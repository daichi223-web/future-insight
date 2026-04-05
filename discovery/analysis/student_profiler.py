"""多次元生徒プロファイリングモジュール

IB Learner Profile にインスパイアされた多次元プロファイルを生成する。

Usage:
    python -m discovery.analysis.student_profiler [--data-dir ...] [--output-dir ...]
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


SUBJECTS = ["math", "physics", "chemistry", "english", "japanese"]
SUBJECT_JA = {
    "math": "数学", "physics": "物理", "chemistry": "化学",
    "english": "英語", "japanese": "国語",
}


def _load_q_matrix(data_dir: Path) -> dict:
    schema_dir = data_dir.parent / "schema"
    for name in ("enhanced_q_matrix.json", "q_matrix.json"):
        path = schema_dir / name
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    return {}


# ── 教科プロファイル ─────────────────────────────────

def compute_subject_profile(grades_df: pd.DataFrame) -> pd.DataFrame:
    """生徒ごとの教科別平均成績を計算。"""
    return (
        grades_df.groupby(["student_id", "subject"])["grade"]
        .mean()
        .reset_index()
        .pivot_table(index="student_id", columns="subject", values="grade")
        .reset_index()
    )


# ── IB Learner Profile プロキシ ──────────────────────

def compute_learner_profile_proxies(
    responses_df: pd.DataFrame,
    grades_df: pd.DataFrame,
    attendance_df: pd.DataFrame,
    q_matrix: dict,
) -> pd.DataFrame:
    """IB Learner Profile の6属性をプロキシスコアで計算。"""
    students = grades_df["student_id"].unique()
    items = q_matrix.get("items", {})

    records = []
    for sid in students:
        stu_grades = grades_df[grades_df["student_id"] == sid]
        stu_resp = responses_df[responses_df["student_id"] == sid]
        stu_att = attendance_df[attendance_df["student_id"] == sid]

        # Balanced: 教科間分散の逆数（正規化）
        subj_means = stu_grades.groupby("subject")["grade"].mean()
        if len(subj_means) > 1:
            variance = subj_means.var()
            balanced = max(0, 100 - variance * 0.3)  # スケーリング
        else:
            balanced = 50.0

        # Risk-taker: 難問（DOK3+）への挑戦率
        if not stu_resp.empty and items:
            hard_items = [
                iid for iid, meta in items.items()
                if meta.get("dok_level", 1) >= 3
            ]
            hard_resp = stu_resp[stu_resp["item_id"].isin(hard_items)]
            risk_taker = (hard_resp["correct"].mean() * 100) if not hard_resp.empty else 50.0
        else:
            risk_taker = 50.0

        # Reflective: 成績低下後の回復率
        term_grades = stu_grades.groupby("term")["grade"].mean().sort_index()
        recoveries = []
        for i in range(1, len(term_grades) - 1):
            if term_grades.iloc[i] < term_grades.iloc[i - 1] - 3:  # 3点以上低下
                recovery = term_grades.iloc[i + 1] - term_grades.iloc[i]
                recoveries.append(recovery)
        reflective = (np.mean(recoveries) + 20) * 2.5 if recoveries else 50.0  # 正規化

        # Knowledgeable: 全教科加重平均
        knowledgeable = subj_means.mean() if not subj_means.empty else 50.0

        # Thinker: 高次思考問題（Bloom's analyze以上）のスコア
        if not stu_resp.empty and items:
            think_items = [
                iid for iid, meta in items.items()
                if meta.get("blooms_cognitive", "") in ("analyze", "evaluate", "create")
            ]
            think_resp = stu_resp[stu_resp["item_id"].isin(think_items)]
            thinker = (think_resp["correct"].mean() * 100) if not think_resp.empty else 50.0
        else:
            thinker = 50.0

        # Communicator: 言語系スキルのスコア
        if not stu_resp.empty:
            lang_resp = stu_resp[stu_resp["subject"].isin(["japanese", "english"])]
            communicator = (lang_resp["correct"].mean() * 100) if not lang_resp.empty else 50.0
        else:
            communicator = 50.0

        records.append({
            "student_id": sid,
            "lp_balanced": round(float(np.clip(balanced, 0, 100)), 1),
            "lp_risk_taker": round(float(np.clip(risk_taker, 0, 100)), 1),
            "lp_reflective": round(float(np.clip(reflective, 0, 100)), 1),
            "lp_knowledgeable": round(float(np.clip(knowledgeable, 0, 100)), 1),
            "lp_thinker": round(float(np.clip(thinker, 0, 100)), 1),
            "lp_communicator": round(float(np.clip(communicator, 0, 100)), 1),
        })

    return pd.DataFrame(records)


# ── WOK プロファイル ─────────────────────────────────

def compute_wok_profile(responses_df: pd.DataFrame, q_matrix: dict) -> pd.DataFrame:
    """WOK（知る方法）ごとのプロファイルを計算。"""
    items = q_matrix.get("items", {})
    if not items:
        return pd.DataFrame()

    # WOK分類ヒューリスティック
    wok_items = {"reason": [], "language": [], "imagination": []}
    for item_id, meta in items.items():
        dok = meta.get("dok_level", 1)
        blooms = meta.get("blooms_cognitive", "")
        subj = meta.get("subject", "")
        skills_str = str(meta.get("skills", []))

        if (dok >= 3 or blooms in ("analyze", "evaluate")) and subj in ("math", "physics", "chemistry"):
            wok_items["reason"].append(item_id)
        if (blooms in ("understand", "evaluate") and subj in ("japanese", "english")) or "reading" in skills_str or "word_problem" in skills_str:
            wok_items["language"].append(item_id)
        if any(k in skills_str for k in ("geometric", "graph", "wave", "spatial", "model")):
            wok_items["imagination"].append(item_id)

    records = []
    students = responses_df["student_id"].unique()
    for sid in students:
        stu_resp = responses_df[responses_df["student_id"] == sid]
        row = {"student_id": sid}
        for wok, iids in wok_items.items():
            wok_resp = stu_resp[stu_resp["item_id"].isin(iids)]
            row[f"wok_{wok}"] = round(float(wok_resp["correct"].mean() * 100), 1) if not wok_resp.empty else 50.0
        records.append(row)

    return pd.DataFrame(records)


# ── 動機診断 ─────────────────────────────────────────

def compute_motivation_diagnostic(
    responses_df: pd.DataFrame,
    grades_df: pd.DataFrame,
    attendance_df: pd.DataFrame,
) -> pd.DataFrame:
    """「やらない」vs「できない」の診断指標を計算。"""
    students = grades_df["student_id"].unique()
    records = []

    for sid in students:
        stu_resp = responses_df[responses_df["student_id"] == sid]
        stu_grades = grades_df[grades_df["student_id"] == sid]
        stu_att = attendance_df[attendance_df["student_id"] == sid]

        # 1. 簡単な問題の正答率（DOK1相当 = q01-q10）
        easy_resp = stu_resp[stu_resp["item_id"].str.extract(r"_q(\d+)$")[0].astype(float) <= 10]
        easy_accuracy = easy_resp["correct"].mean() if not easy_resp.empty else 0.5

        # 2. 無回答率のプロキシ（後半問題の連続0）
        blank_proxy = 0.0
        for subj in SUBJECTS:
            subj_resp = stu_resp[stu_resp["subject"] == subj].sort_values("item_id")
            if len(subj_resp) >= 5:
                last5 = subj_resp.tail(5)["correct"]
                if last5.sum() == 0:
                    blank_proxy += 0.2

        # 3. 出席率
        att_rate = stu_att["present"].mean() if not stu_att.empty else 0.9

        # 4. 教科間分散
        subj_means = stu_grades.groupby("subject")["grade"].mean()
        cross_var = float(subj_means.std()) if len(subj_means) > 1 else 0.0

        # 診断: 「できない」= easy_accuracy低い、「やらない」= easy_accuracy高いが全体低い
        overall = stu_resp["correct"].mean() if not stu_resp.empty else 0.5
        if easy_accuracy > 0.7 and overall < 0.5:
            diagnosis = "動機的課題の可能性"
        elif easy_accuracy < 0.5:
            diagnosis = "スキル的課題の可能性"
        else:
            diagnosis = "混合型または該当なし"

        records.append({
            "student_id": sid,
            "easy_accuracy": round(float(easy_accuracy), 3),
            "blank_proxy": round(float(blank_proxy), 3),
            "attendance_rate": round(float(att_rate), 3),
            "cross_subject_variance": round(cross_var, 1),
            "diagnosis": diagnosis,
        })

    return pd.DataFrame(records)


# ── メインエントリ ────────────────────────────────────

def run_student_profiler(data_dir: Path, output_dir: Path) -> dict:
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("  [生徒プロファイル] データ読込中...", flush=True)
    responses_df = pd.read_csv(data_dir / "item_responses.csv")
    grades_df = pd.read_csv(data_dir / "grades.csv")
    attendance_df = pd.read_csv(data_dir / "attendance.csv")
    q_matrix = _load_q_matrix(data_dir)
    print(f"  [生徒プロファイル] {responses_df['student_id'].nunique()}人", flush=True)

    print("  [生徒プロファイル] 教科プロファイル計算中...", flush=True)
    subject_profile = compute_subject_profile(grades_df)

    print("  [生徒プロファイル] IB Learner Profile プロキシ計算中...", flush=True)
    lp_profile = compute_learner_profile_proxies(
        responses_df, grades_df, attendance_df, q_matrix
    )

    print("  [生徒プロファイル] WOKプロファイル計算中...", flush=True)
    wok_profile = compute_wok_profile(responses_df, q_matrix)

    print("  [生徒プロファイル] 動機診断中...", flush=True)
    motivation = compute_motivation_diagnostic(responses_df, grades_df, attendance_df)

    # 統合
    print("  [生徒プロファイル] 統合中...", flush=True)
    merged = subject_profile.copy()
    for df in [lp_profile, wok_profile, motivation]:
        if not df.empty:
            merged = merged.merge(df, on="student_id", how="left")

    student_list = []
    for _, row in merged.iterrows():
        entry = {"student_id": row["student_id"]}

        # 教科スコア
        entry["subjects"] = {}
        for subj in SUBJECTS:
            if subj in row.index and not pd.isna(row.get(subj)):
                entry["subjects"][subj] = round(float(row[subj]), 1)

        # Learner Profile
        entry["learner_profile"] = {}
        for col in ["lp_balanced", "lp_risk_taker", "lp_reflective",
                     "lp_knowledgeable", "lp_thinker", "lp_communicator"]:
            if col in row.index and not pd.isna(row.get(col)):
                entry["learner_profile"][col.replace("lp_", "")] = float(row[col])

        # WOK
        entry["wok_profile"] = {}
        for col in ["wok_reason", "wok_language", "wok_imagination"]:
            if col in row.index and not pd.isna(row.get(col)):
                entry["wok_profile"][col.replace("wok_", "")] = float(row[col])

        # 動機診断
        entry["motivation"] = {}
        for col in ["easy_accuracy", "blank_proxy", "attendance_rate",
                     "cross_subject_variance", "diagnosis"]:
            if col in row.index:
                val = row.get(col)
                if not pd.isna(val) if isinstance(val, (int, float)) else val:
                    entry["motivation"][col] = val if isinstance(val, str) else float(val)

        student_list.append(entry)

    # 診断サマリー
    diag_counts = motivation["diagnosis"].value_counts().to_dict() if not motivation.empty else {}

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_students": len(student_list),
        "dimensions": [
            "subjects (5教科スコア)",
            "learner_profile (IB LP 6属性プロキシ)",
            "wok_profile (知る方法 3次元)",
            "motivation (動機/スキル診断)",
        ],
        "diagnosis_summary": diag_counts,
        "students": student_list,
    }

    out_path = output_dir / "student_profiles_enhanced.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  [生徒プロファイル] 完了: {len(student_list)}人", flush=True)
    print(f"  [生徒プロファイル] 診断: {diag_counts}", flush=True)
    print(f"  [生徒プロファイル] 出力: {out_path}", flush=True)

    return result


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    run_student_profiler(
        Path("discovery/data/sample"),
        Path("discovery/analysis/output"),
    )
