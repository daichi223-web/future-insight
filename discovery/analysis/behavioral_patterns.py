"""行動経済学・システム思考パターン検出モジュール

ディープリサーチで特定された18の検出可能パターンのうち、
既存データ（正誤・成績・出欠）から検出可能なものを実装する。

検出パターン:
1. ティッピングポイント（出欠率の臨界閾値）
2. 詰め込みスコア（スペーシング効果の欠如）
3. 損失回避プロキシ（後半問題の放棄率）
4. 成功が成功を呼ぶ（成績分散の時間的拡大）
5. 茹でガエル（緩慢な出欠低下の検出）

Usage:
    python -m discovery.analysis.behavioral_patterns [--data-dir ...] [--output-dir ...]
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


# ── 1. ティッピングポイント検出 ────────────────────────

def detect_tipping_points(grades_df: pd.DataFrame, attendance_df: pd.DataFrame) -> dict:
    """出欠率の臨界閾値を区分回帰で検出する。

    出欠率がある閾値を下回ると成績が急落するポイントを特定する。
    """
    # 学期ごとの出欠率と成績を集計
    att_by_term = []
    students = grades_df["student_id"].unique()
    dates = pd.to_datetime(attendance_df["date"])
    attendance_df = attendance_df.copy()
    attendance_df["month"] = dates.dt.month
    attendance_df["year"] = dates.dt.year

    # 生徒ごとの全期間出欠率
    att_rates = (
        attendance_df.groupby("student_id")["present"]
        .mean()
        .reset_index()
        .rename(columns={"present": "attendance_rate"})
    )

    # 生徒ごとの全教科平均成績
    mean_grades = (
        grades_df.groupby("student_id")["grade"]
        .mean()
        .reset_index()
        .rename(columns={"grade": "mean_grade"})
    )

    merged = att_rates.merge(mean_grades, on="student_id")
    if len(merged) < 50:
        return {"tipping_point": None, "message": "サンプル不足"}

    # 区分回帰: 出欠率を0.60-0.95の範囲で分割し、残差平方和が最小の点を探す
    best_threshold = None
    best_rss = np.inf
    att_vals = merged["attendance_rate"].values
    grade_vals = merged["mean_grade"].values

    for threshold in np.arange(0.65, 0.95, 0.01):
        below = grade_vals[att_vals < threshold]
        above = grade_vals[att_vals >= threshold]
        if len(below) < 10 or len(above) < 10:
            continue
        rss = np.sum((below - below.mean()) ** 2) + np.sum((above - above.mean()) ** 2)
        if rss < best_rss:
            best_rss = rss
            best_threshold = threshold

    if best_threshold is None:
        return {"tipping_point": None, "message": "閾値を検出できませんでした"}

    below = merged[merged["attendance_rate"] < best_threshold]
    above = merged[merged["attendance_rate"] >= best_threshold]
    grade_drop = above["mean_grade"].mean() - below["mean_grade"].mean()

    return {
        "tipping_point": round(float(best_threshold), 2),
        "grade_drop": round(float(grade_drop), 1),
        "n_below": len(below),
        "n_above": len(above),
        "mean_grade_below": round(float(below["mean_grade"].mean()), 1),
        "mean_grade_above": round(float(above["mean_grade"].mean()), 1),
        "description": f"出欠率{best_threshold:.0%}を下回ると平均成績が{grade_drop:.1f}点低下",
    }


# ── 2. 詰め込みスコア ────────────────────────────────

def detect_cramming(grades_df: pd.DataFrame, mock_df: pd.DataFrame) -> list:
    """定期テスト成績と模試成績の乖離からスペーシング効果の欠如を検出。

    定期テスト成績 >> 模試成績 の生徒 = 短期記憶依存（詰め込み型）。
    """
    if mock_df.empty:
        return []

    # 教科別の定期テスト平均 vs 模試偏差値（50基準に正規化）
    grade_means = (
        grades_df.groupby(["student_id", "subject"])["grade"]
        .mean()
        .reset_index()
        .rename(columns={"grade": "regular_grade"})
    )
    mock_means = (
        mock_df.groupby(["student_id", "subject"])["deviation_score"]
        .mean()
        .reset_index()
        .rename(columns={"deviation_score": "mock_score"})
    )

    merged = grade_means.merge(mock_means, on=["student_id", "subject"])
    if merged.empty:
        return []

    # 正規化: regular_gradeを偏差値スケールに変換
    for subj in merged["subject"].unique():
        mask = merged["subject"] == subj
        grades = merged.loc[mask, "regular_grade"]
        if grades.std() > 0:
            merged.loc[mask, "regular_normalized"] = (
                50 + (grades - grades.mean()) / grades.std() * 10
            )
        else:
            merged.loc[mask, "regular_normalized"] = 50

    merged["cramming_score"] = merged["regular_normalized"] - merged["mock_score"]

    # 教科別の詰め込みスコア上位
    results = []
    for subj in SUBJECTS:
        subj_data = merged[merged["subject"] == subj]
        if subj_data.empty:
            continue
        mean_cram = subj_data["cramming_score"].mean()
        high_crammers = subj_data[subj_data["cramming_score"] > 5]
        results.append({
            "subject": subj,
            "subject_ja": SUBJECT_JA.get(subj, subj),
            "mean_cramming_score": round(float(mean_cram), 2),
            "n_high_crammers": len(high_crammers),
            "pct_high_crammers": round(float(len(high_crammers) / len(subj_data) * 100), 1) if len(subj_data) > 0 else 0,
        })

    return results


# ── 3. 損失回避プロキシ ──────────────────────────────

def detect_loss_aversion(responses_df: pd.DataFrame) -> dict:
    """後半の難問での放棄パターンから損失回避傾向を検出。

    テスト後半（q21-q30）の連続不正解 = 放棄（損失回避的行動）と推定。
    """
    students = responses_df["student_id"].unique()
    abandonment_rates = {}

    for subj in SUBJECTS:
        subj_resp = responses_df[responses_df["subject"] == subj]
        abandon_count = 0
        total = 0

        for sid in students:
            stu_resp = subj_resp[subj_resp["student_id"] == sid].sort_values("item_id")
            if len(stu_resp) < 25:
                continue
            total += 1
            # 最後5問が全て不正解 = 放棄と推定
            last5 = stu_resp.tail(5)["correct"].values
            if last5.sum() == 0:
                abandon_count += 1

        if total > 0:
            abandonment_rates[subj] = {
                "subject_ja": SUBJECT_JA.get(subj, subj),
                "abandonment_rate": round(abandon_count / total, 3),
                "n_abandoned": abandon_count,
                "n_total": total,
            }

    overall_rate = np.mean([v["abandonment_rate"] for v in abandonment_rates.values()]) if abandonment_rates else 0

    return {
        "overall_abandonment_rate": round(float(overall_rate), 3),
        "by_subject": abandonment_rates,
        "description": "テスト後半（最後5問）の全問不正解率。高い値は損失回避的な放棄傾向を示唆",
    }


# ── 4. 成功が成功を呼ぶ（成績分散拡大）──────────────

def detect_matthew_effect(grades_df: pd.DataFrame) -> dict:
    """学期ごとの成績分散を追跡し、「成功が成功を呼ぶ」パターンを検出。

    分散が時間とともに拡大 = 上位と下位の差が広がっている（マタイ効果）。
    """
    terms = sorted(grades_df["term"].unique())
    if len(terms) < 3:
        return {"detected": False, "message": "学期数不足（3学期以上必要）"}

    variance_by_term = []
    gini_by_term = []
    for t in terms:
        term_grades = grades_df[grades_df["term"] == t]
        student_means = term_grades.groupby("student_id")["grade"].mean()

        variance_by_term.append({
            "term": int(t),
            "variance": round(float(student_means.var()), 2),
            "std": round(float(student_means.std()), 2),
        })

        # ジニ係数
        vals = np.sort(student_means.values)
        n = len(vals)
        if n > 1 and vals.sum() > 0:
            index = np.arange(1, n + 1)
            gini = (2 * np.sum(index * vals) - (n + 1) * np.sum(vals)) / (n * np.sum(vals))
            gini_by_term.append({"term": int(t), "gini": round(float(gini), 4)})

    # 分散のトレンド: 正の傾き = 拡大
    variances = [v["variance"] for v in variance_by_term]
    if len(variances) >= 3:
        slope = np.polyfit(range(len(variances)), variances, 1)[0]
        detected = slope > 0.5
    else:
        slope = 0
        detected = False

    return {
        "detected": detected,
        "variance_trend_slope": round(float(slope), 3),
        "variance_by_term": variance_by_term,
        "gini_by_term": gini_by_term,
        "description": "成績分散が学期ごとに拡大している場合、上位・下位の二極化が進行中" if detected
                       else "成績分散は安定しており、顕著な二極化は検出されず",
    }


# ── 5. 茹でガエル（緩慢な出欠低下）──────────────────

def detect_boiling_frog(attendance_df: pd.DataFrame) -> list:
    """出欠率が緩やかに低下し続ける生徒を検出。

    急激な変化ではなく、毎月少しずつ低下するパターン。
    """
    dates = pd.to_datetime(attendance_df["date"])
    attendance_df = attendance_df.copy()
    attendance_df["yearmonth"] = dates.dt.to_period("M").astype(str)

    monthly = (
        attendance_df.groupby(["student_id", "yearmonth"])["present"]
        .mean()
        .reset_index()
        .rename(columns={"present": "monthly_rate"})
    )

    flagged = []
    for sid in monthly["student_id"].unique():
        stu = monthly[monthly["student_id"] == sid].sort_values("yearmonth")
        if len(stu) < 4:
            continue
        rates = stu["monthly_rate"].values

        # 3ヶ月以上連続で低下しているか
        consecutive_drops = 0
        max_consecutive = 0
        for i in range(1, len(rates)):
            if rates[i] < rates[i - 1] - 0.01:  # 1%以上の低下
                consecutive_drops += 1
                max_consecutive = max(max_consecutive, consecutive_drops)
            else:
                consecutive_drops = 0

        # 全体の傾き
        if len(rates) >= 3:
            slope = np.polyfit(range(len(rates)), rates, 1)[0]
        else:
            slope = 0

        if max_consecutive >= 3 or (slope < -0.02 and rates[-1] < 0.85):
            flagged.append({
                "student_id": sid,
                "initial_rate": round(float(rates[0]), 3),
                "final_rate": round(float(rates[-1]), 3),
                "decline": round(float(rates[0] - rates[-1]), 3),
                "slope": round(float(slope), 4),
                "max_consecutive_drops": max_consecutive,
                "description": f"出欠率が{rates[0]:.0%}から{rates[-1]:.0%}に緩やかに低下",
            })

    return sorted(flagged, key=lambda x: x["decline"], reverse=True)


# ── メインエントリ ────────────────────────────────────

def run_behavioral_patterns(data_dir: Path, output_dir: Path) -> dict:
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("  [行動パターン] データ読込中...", flush=True)
    responses = pd.read_csv(data_dir / "item_responses.csv")
    grades = pd.read_csv(data_dir / "grades.csv")
    attendance = pd.read_csv(data_dir / "attendance.csv")

    mock_path = data_dir / "mock_exams.csv"
    mock = pd.read_csv(mock_path) if mock_path.exists() else pd.DataFrame()

    print("  [行動パターン] ティッピングポイント検出中...", flush=True)
    tipping = detect_tipping_points(grades, attendance)
    tp = tipping.get("tipping_point")
    print(f"    出欠率閾値: {tp}" if tp else "    閾値未検出", flush=True)

    print("  [行動パターン] 詰め込みスコア計算中...", flush=True)
    cramming = detect_cramming(grades, mock)
    if cramming:
        avg_cram = np.mean([c["mean_cramming_score"] for c in cramming])
        print(f"    平均詰め込みスコア: {avg_cram:.2f}", flush=True)

    print("  [行動パターン] 損失回避プロキシ計算中...", flush=True)
    loss_aversion = detect_loss_aversion(responses)
    print(f"    全体放棄率: {loss_aversion['overall_abandonment_rate']:.1%}", flush=True)

    print("  [行動パターン] マタイ効果検出中...", flush=True)
    matthew = detect_matthew_effect(grades)
    print(f"    二極化: {'検出' if matthew['detected'] else '未検出'}", flush=True)

    print("  [行動パターン] 茹でガエル検出中...", flush=True)
    boiling_frog = detect_boiling_frog(attendance)
    print(f"    緩慢低下: {len(boiling_frog)}人", flush=True)

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "patterns": {
            "tipping_point": tipping,
            "cramming_effect": cramming,
            "loss_aversion": loss_aversion,
            "matthew_effect": matthew,
            "boiling_frog": boiling_frog,
        },
        "summary": {
            "tipping_point_detected": tp is not None,
            "tipping_point_value": tp,
            "cramming_subjects": len([c for c in cramming if c["n_high_crammers"] > 0]),
            "abandonment_rate": loss_aversion["overall_abandonment_rate"],
            "matthew_effect_detected": matthew["detected"],
            "boiling_frog_count": len(boiling_frog),
        },
    }

    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.bool_, np.integer)):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return super().default(obj)

    out_path = output_dir / "behavioral_patterns.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
    print(f"  [行動パターン] 出力: {out_path}", flush=True)

    return result


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    run_behavioral_patterns(
        Path("discovery/data/sample"),
        Path("discovery/analysis/output"),
    )
