"""教科横断分析モジュール

カリキュラム上の前提チェーン検証、WOK媒介相関、ボトルネック検出を行う。

Usage:
    python -m discovery.analysis.cross_subject [--data-dir ...] [--output-dir ...]
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from discovery.analysis.config import CROSS_SUBJECT as CFG

SUBJECTS = ["math", "physics", "chemistry", "english", "japanese"]
SUBJECT_JA = {
    "math": "数学", "physics": "物理", "chemistry": "化学",
    "english": "英語", "japanese": "国語",
}

# WOK ヒューリスティックマッピング
WOK_HEURISTICS = {
    "reason": {
        "conditions": lambda item: (
            item.get("dok_level", 1) >= 3
            or item.get("blooms_cognitive", "") in ("analyze", "evaluate")
        ) and item.get("subject", "") in ("math", "physics", "chemistry"),
    },
    "language": {
        "conditions": lambda item: (
            item.get("blooms_cognitive", "") in ("understand", "evaluate")
            and item.get("subject", "") in ("japanese", "english")
        ) or (
            "word_problem" in str(item.get("skills", []))
            or "reading" in str(item.get("skills", []))
        ),
    },
    "imagination": {
        "conditions": lambda item: (
            any(k in str(item.get("skills", []))
                for k in ("geometric", "graph", "wave", "model", "spatial"))
        ),
    },
}


def _load_q_matrix(data_dir: Path) -> dict:
    schema_dir = data_dir.parent / "schema"
    enhanced = schema_dir / "enhanced_q_matrix.json"
    basic = schema_dir / "q_matrix.json"
    path = enhanced if enhanced.exists() else basic
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_curriculum(data_dir: Path) -> dict:
    path = data_dir.parent / "schema" / "curriculum.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _get_skill_scores(responses_df: pd.DataFrame, q_matrix: dict) -> pd.DataFrame:
    """生徒×スキルの正答率マトリクスを構築。"""
    items = q_matrix.get("items", {})
    if not items:
        return pd.DataFrame()

    rows = []
    for _, row in responses_df.iterrows():
        item_id = row["item_id"]
        meta = items.get(item_id, {})
        skills = meta.get("skills", [])
        for skill in skills:
            rows.append({
                "student_id": row["student_id"],
                "skill": skill,
                "subject": meta.get("subject", row.get("subject", "")),
                "correct": row["correct"],
            })

    if not rows:
        return pd.DataFrame()

    skill_df = pd.DataFrame(rows)
    scores = (
        skill_df.groupby(["student_id", "skill"])["correct"]
        .mean()
        .reset_index()
        .rename(columns={"correct": "score"})
    )
    return scores


# ── 前提チェーン検証 ─────────────────────────────────

def validate_prerequisites(responses_df: pd.DataFrame, q_matrix: dict,
                           curriculum: dict) -> list:
    """カリキュラム上の教科横断前提チェーンをデータで検証。"""
    prereqs = curriculum.get("cross_subject_prerequisites", [])
    if not prereqs:
        return []

    skill_scores = _get_skill_scores(responses_df, q_matrix)
    if skill_scores.empty:
        return []

    pivot = skill_scores.pivot_table(
        index="student_id", columns="skill", values="score", aggfunc="mean"
    )

    results = []
    for prereq in prereqs:
        from_raw = prereq.get("from_skill", "")
        to_raw = prereq.get("to_skill", "")
        # "math:algebraic_manipulation" -> "algebraic_manipulation"
        from_skill = from_raw.split(":")[-1] if ":" in from_raw else from_raw
        to_skill = to_raw.split(":")[-1] if ":" in to_raw else to_raw

        if from_skill not in pivot.columns or to_skill not in pivot.columns:
            results.append({
                "from": from_raw, "to": to_raw,
                "expected_strength": prereq.get("strength", ""),
                "actual_correlation": None,
                "status": "データ不足",
                "description_ja": prereq.get("description_ja", prereq.get("description", "")),
            })
            continue

        valid = pivot[[from_skill, to_skill]].dropna()
        if len(valid) < CFG["min_sample_size"]:
            results.append({
                "from": from_raw, "to": to_raw,
                "expected_strength": prereq.get("strength", ""),
                "actual_correlation": None,
                "status": "サンプル不足",
                "description_ja": prereq.get("description_ja", prereq.get("description", "")),
            })
            continue

        corr = valid[from_skill].corr(valid[to_skill])
        status = ("確認" if corr > CFG["prerequisite_confirmed"]
                  else ("弱い関連" if corr > CFG["prerequisite_weak"] else "未確認"))

        results.append({
            "from": from_raw, "to": to_raw,
            "expected_strength": prereq.get("strength", ""),
            "actual_correlation": round(float(corr), 3),
            "status": status,
            "description_ja": prereq.get("description_ja", prereq.get("description", "")),
        })

    return results


# ── WOK媒介相関 ──────────────────────────────────────

def analyze_wok_connections(responses_df: pd.DataFrame, q_matrix: dict) -> dict:
    """WOK（知る方法）ごとにグループ化し、教科横断相関を計算。"""
    items = q_matrix.get("items", {})
    if not items:
        return {}

    # 各設問にWOKタグを付与
    wok_items = {wok: [] for wok in WOK_HEURISTICS}
    for item_id, meta in items.items():
        for wok, rule in WOK_HEURISTICS.items():
            if rule["conditions"](meta):
                wok_items[wok].append(item_id)

    # WOKごとに教科別スコアを計算
    results = {}
    for wok, item_ids in wok_items.items():
        if len(item_ids) < 5:
            continue

        wok_responses = responses_df[responses_df["item_id"].isin(item_ids)].copy()
        if wok_responses.empty:
            continue

        # 教科別平均
        subj_scores = (
            wok_responses.groupby(["student_id", "subject"])["correct"]
            .mean()
            .reset_index()
        )
        pivot = subj_scores.pivot_table(
            index="student_id", columns="subject", values="correct"
        )

        if pivot.shape[1] < 2:
            continue

        corr_matrix = pivot.corr()
        cross_pairs = []
        cols = list(corr_matrix.columns)
        for i, s1 in enumerate(cols):
            for s2 in cols[i + 1:]:
                val = corr_matrix.loc[s1, s2]
                if not np.isnan(val):
                    cross_pairs.append({
                        "subject_1": SUBJECT_JA.get(s1, s1),
                        "subject_2": SUBJECT_JA.get(s2, s2),
                        "correlation": round(float(val), 3),
                    })

        results[wok] = {
            "n_items": len(item_ids),
            "cross_subject_correlations": sorted(
                cross_pairs, key=lambda x: abs(x["correlation"]), reverse=True
            ),
        }

    return results


# ── ボトルネック検出 ─────────────────────────────────

def find_bottlenecks(responses_df: pd.DataFrame, q_matrix: dict) -> list:
    """複数教科に影響するボトルネックスキルを検出。"""
    items = q_matrix.get("items", {})
    if not items:
        return []

    # スキル → 教科マッピング
    skill_subjects = {}
    for item_id, meta in items.items():
        subj = meta.get("subject", "")
        for skill in meta.get("skills", []):
            skill_subjects.setdefault(skill, set()).add(subj)

    # 複数教科にまたがるスキル
    cross_skills = {
        skill: subjects
        for skill, subjects in skill_subjects.items()
        if len(subjects) >= 2
    }

    if not cross_skills:
        # 同名スキルがなくても、相関から間接的ボトルネックを検出
        return []

    skill_scores = _get_skill_scores(responses_df, q_matrix)
    if skill_scores.empty:
        return []

    results = []
    for skill, subjects in cross_skills.items():
        skill_data = skill_scores[skill_scores["skill"] == skill]
        if skill_data.empty:
            continue

        mean_score = skill_data["score"].mean()
        n_students = skill_data["student_id"].nunique()

        results.append({
            "skill": skill,
            "affected_subjects": sorted(SUBJECT_JA.get(s, s) for s in subjects),
            "n_subjects": len(subjects),
            "mean_mastery": round(float(mean_score), 3),
            "n_students": n_students,
            "impact": "高" if len(subjects) >= 3 else "中",
        })

    return sorted(results, key=lambda x: x["n_subjects"], reverse=True)


# ── タイミングミスマッチ ─────────────────────────────

def detect_timing_mismatches(curriculum: dict) -> list:
    """前提スキルが依存スキルより後に教えられるケースを検出。"""
    prereqs = curriculum.get("cross_subject_prerequisites", [])
    subjects = curriculum.get("subjects", {})

    # コースの典型学年をマップ
    course_grades = {}
    for subj_key, subj_data in subjects.items():
        for course in subj_data.get("courses", []):
            course_grades[course["id"]] = course.get("typical_grade", 0)

    # スキル → コース → 学年をマップ
    skill_grade = {}
    for subj_key, subj_data in subjects.items():
        for course in subj_data.get("courses", []):
            grade = course.get("typical_grade", 0)
            for unit in course.get("units", []):
                for skill in unit.get("skills", []):
                    skill_grade[skill] = grade

    mismatches = []
    for prereq in prereqs:
        from_raw = prereq.get("from_skill", "")
        to_raw = prereq.get("to_skill", "")
        from_skill = from_raw.split(":")[-1] if ":" in from_raw else from_raw
        to_skill = to_raw.split(":")[-1] if ":" in to_raw else to_raw

        from_grade = skill_grade.get(from_skill, 0)
        to_grade = skill_grade.get(to_skill, 0)

        if from_grade > 0 and to_grade > 0 and from_grade > to_grade:
            mismatches.append({
                "prerequisite": from_raw,
                "dependent": to_raw,
                "prereq_taught_grade": from_grade,
                "dependent_taught_grade": to_grade,
                "issue": f"前提({from_raw})が{from_grade}年で教えられるが、依存先({to_raw})は{to_grade}年で教えられる",
                "description_ja": prereq.get("description_ja", ""),
            })

    return mismatches


# ── メインエントリ ────────────────────────────────────

def run_cross_subject_analysis(data_dir: Path, output_dir: Path) -> dict:
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("  [教科横断] データ読込中...", flush=True)
    responses_df = pd.read_csv(data_dir / "item_responses.csv")
    q_matrix = _load_q_matrix(data_dir)
    curriculum = _load_curriculum(data_dir)

    print("  [教科横断] 前提チェーン検証中...", flush=True)
    prereq_results = validate_prerequisites(responses_df, q_matrix, curriculum)
    confirmed = sum(1 for r in prereq_results if r["status"] == "確認")
    print(f"  [教科横断] 前提チェーン: {len(prereq_results)}件中{confirmed}件確認", flush=True)

    print("  [教科横断] WOK媒介相関分析中...", flush=True)
    wok_results = analyze_wok_connections(responses_df, q_matrix)
    print(f"  [教科横断] WOK分析: {len(wok_results)}種類のWOK", flush=True)

    print("  [教科横断] ボトルネック検出中...", flush=True)
    bottlenecks = find_bottlenecks(responses_df, q_matrix)
    print(f"  [教科横断] ボトルネック: {len(bottlenecks)}件", flush=True)

    print("  [教科横断] タイミングミスマッチ検出中...", flush=True)
    mismatches = detect_timing_mismatches(curriculum)
    print(f"  [教科横断] タイミングミスマッチ: {len(mismatches)}件", flush=True)

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "prerequisite_validation": prereq_results,
        "wok_connections": wok_results,
        "bottleneck_skills": bottlenecks,
        "timing_mismatches": mismatches,
        "summary": {
            "prerequisites_total": len(prereq_results),
            "prerequisites_confirmed": confirmed,
            "wok_types_analyzed": len(wok_results),
            "bottlenecks_found": len(bottlenecks),
            "timing_mismatches_found": len(mismatches),
        },
    }

    out_path = output_dir / "cross_subject.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  [教科横断] 出力: {out_path}", flush=True)

    return result


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    run_cross_subject_analysis(
        Path("discovery/data/sample"),
        Path("discovery/analysis/output"),
    )
