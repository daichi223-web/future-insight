"""サンプル教育データ生成器

500人の生徒 × 5教科 × 30設問の模擬データを生成する。
データには検証用の「隠れたつながり」が植え込まれている:

1. 教科横断前提チェーン（数学代数→物理力学、数学代数→化学平衡）
2. 4-5種の隠れた生徒タイプ（混合分布）
3. ボトルネックスキル（文章題読解力が3教科に影響）
4. 時間パターン（出欠低下→成績低下シーケンス）

Usage:
    python scripts/generate_sample.py [--output-dir data/sample] [--seed 42] [--n-students 500]
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ── 定数 ──────────────────────────────────────────────

SUBJECTS = ["math", "physics", "chemistry", "english", "japanese"]
SUBJECT_JA = {
    "math": "数学", "physics": "物理", "chemistry": "化学",
    "english": "英語", "japanese": "国語",
}
N_ITEMS = 30
N_TERMS = 6
SCHOOL_DAYS_PER_TERM = 60
MOCK_EXAMS_PER_YEAR = 3  # 6月, 10月, 1月

# 潜在クラス定義
LATENT_CLASSES = {
    0: {
        "name": "balanced_high", "name_ja": "バランス型高達成",
        "proportion": 0.25,
        "abilities": {"math": 0.78, "physics": 0.74, "chemistry": 0.70,
                      "english": 0.80, "japanese": 0.76},
        "attendance_rate": 0.95, "growth_trend": 0.015,
        "reading_skill": 0.8,
    },
    1: {
        "name": "stem_tilted", "name_ja": "STEM傾斜型",
        "proportion": 0.20,
        "abilities": {"math": 0.84, "physics": 0.80, "chemistry": 0.74,
                      "english": 0.44, "japanese": 0.40},
        "attendance_rate": 0.92, "growth_trend": 0.010,
        "reading_skill": 0.55,
    },
    2: {
        "name": "humanities_tilted", "name_ja": "文系傾斜型",
        "proportion": 0.20,
        "abilities": {"math": 0.36, "physics": 0.30, "chemistry": 0.40,
                      "english": 0.80, "japanese": 0.84},
        "attendance_rate": 0.93, "growth_trend": 0.010,
        "reading_skill": 0.75,
    },
    3: {
        "name": "disengaged", "name_ja": "離脱型",
        "proportion": 0.15,
        "abilities": {"math": 0.30, "physics": 0.26, "chemistry": 0.30,
                      "english": 0.34, "japanese": 0.32},
        "attendance_rate": 0.72, "growth_trend": -0.04,
        "reading_skill": 0.30,
    },
    4: {
        "name": "struggling_present", "name_ja": "苦戦努力型",
        "proportion": 0.20,
        "abilities": {"math": 0.42, "physics": 0.36, "chemistry": 0.40,
                      "english": 0.46, "japanese": 0.50},
        "attendance_rate": 0.91, "growth_trend": 0.025,
        "reading_skill": 0.50,
    },
}

# 設問の難易度帯（設問番号→基本難易度）
def item_base_difficulty(item_num: int) -> float:
    if item_num <= 10:
        return np.random.uniform(0.65, 0.90)  # 易
    elif item_num <= 20:
        return np.random.uniform(0.35, 0.65)  # 中
    else:
        return np.random.uniform(0.12, 0.40)  # 難


# ── 生徒生成 ──────────────────────────────────────────

def generate_students(n: int, rng: np.random.Generator) -> pd.DataFrame:
    classes = []
    for cls_id, cls_def in LATENT_CLASSES.items():
        count = int(n * cls_def["proportion"])
        classes.extend([cls_id] * count)
    # 端数調整
    while len(classes) < n:
        classes.append(rng.choice(list(LATENT_CLASSES.keys())))
    rng.shuffle(classes)

    students = pd.DataFrame({
        "student_id": [f"S{i+1:03d}" for i in range(n)],
        "latent_class": classes[:n],
    })

    # コース: STEM型→理系多め、文系型→文系多め
    course_probs = {0: 0.5, 1: 0.85, 2: 0.15, 3: 0.4, 4: 0.45}
    students["course"] = students["latent_class"].apply(
        lambda c: "理系" if rng.random() < course_probs[c] else "文系"
    )
    students["gender"] = rng.choice(["M", "F"], size=n)

    # 個人別の読解力潜在変数
    students["reading_latent"] = students["latent_class"].apply(
        lambda c: LATENT_CLASSES[c]["reading_skill"]
    ) + rng.normal(0, 0.12, n)
    students["reading_latent"] = students["reading_latent"].clip(0, 1)

    return students


# ── 設問応答生成 ──────────────────────────────────────

def generate_item_responses(students: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    n = len(students)

    # 設問難易度を事前生成（再現性のため）
    item_difficulties = {}
    for subj in SUBJECTS:
        item_difficulties[subj] = [item_base_difficulty(i + 1) for i in range(N_ITEMS)]

    for _, stu in students.iterrows():
        sid = stu["student_id"]
        cls = LATENT_CLASSES[stu["latent_class"]]
        reading = stu["reading_latent"]

        for subj in SUBJECTS:
            base_ability = cls["abilities"][subj] + rng.normal(0, 0.08)
            base_ability = np.clip(base_ability, 0.05, 0.98)

            for item_idx in range(N_ITEMS):
                item_id = f"{subj}_q{item_idx+1:02d}"
                difficulty = item_difficulties[subj][item_idx]

                # 基本正答確率
                p = base_ability * difficulty + rng.normal(0, 0.05)

                # ── 植え込み信号1: 教科横断前提チェーン ──
                # 数学の代数操作(q01-q06)が高い→物理の公式適用(q19-q24)にボーナス
                if subj == "physics" and 18 <= item_idx <= 23:
                    math_ability = cls["abilities"]["math"] + rng.normal(0, 0.05)
                    if math_ability > 0.6:
                        p += 0.18
                    else:
                        p -= 0.15

                # 数学の代数操作→化学の平衡計算(q19-q24)
                if subj == "chemistry" and 18 <= item_idx <= 23:
                    math_ability = cls["abilities"]["math"] + rng.normal(0, 0.05)
                    if math_ability > 0.6:
                        p += 0.12
                    else:
                        p -= 0.10

                # 数学の関数理解(q19-q24)→物理の波動(q07-q12)
                if subj == "physics" and 6 <= item_idx <= 11:
                    func_ability = cls["abilities"]["math"] * 0.8 + rng.normal(0, 0.05)
                    if func_ability > 0.5:
                        p += 0.10

                # ── 植え込み信号3: ボトルネックスキル（読解力）──
                # 文章題（各教科q25-q30）は読解力に強く依存
                if item_idx >= 24 and subj in ("math", "physics", "chemistry"):
                    if reading < 0.4:
                        p -= 0.25
                    elif reading > 0.7:
                        p += 0.10

                p = np.clip(p, 0.03, 0.97)
                correct = int(rng.random() < p)
                rows.append({"student_id": sid, "subject": subj,
                             "item_id": item_id, "correct": correct})

    return pd.DataFrame(rows)


# ── 成績生成 ──────────────────────────────────────────

def generate_grades(students: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for _, stu in students.iterrows():
        sid = stu["student_id"]
        cls = LATENT_CLASSES[stu["latent_class"]]
        for subj in SUBJECTS:
            base = cls["abilities"][subj] * 100
            for term in range(1, N_TERMS + 1):
                # 成長トレンド
                growth = cls["growth_trend"] * (term - 1) * 100
                noise = rng.normal(0, 6)

                # ── 植え込み信号4: 出欠→成績低下パターン ──
                # 離脱型は後半で成績急落
                if stu["latent_class"] == 3 and term >= 4:
                    growth -= 8 * (term - 3)

                grade = np.clip(base + growth + noise, 0, 100)
                rows.append({"student_id": sid, "subject": subj,
                             "term": term, "grade": round(grade, 1)})

    return pd.DataFrame(rows)


# ── 出欠生成 ──────────────────────────────────────────

def generate_attendance(students: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    base_dates = pd.date_range("2024-04-08", periods=SCHOOL_DAYS_PER_TERM * N_TERMS, freq="B")
    # 学期ごとに分割
    term_dates = [base_dates[i * SCHOOL_DAYS_PER_TERM:(i + 1) * SCHOOL_DAYS_PER_TERM]
                  for i in range(N_TERMS)]

    for _, stu in students.iterrows():
        sid = stu["student_id"]
        cls = LATENT_CLASSES[stu["latent_class"]]
        base_rate = cls["attendance_rate"]

        for term_idx, dates in enumerate(term_dates):
            # 離脱型: 出欠率が学期ごとに低下
            if stu["latent_class"] == 3:
                rate = base_rate - 0.05 * term_idx
                rate = max(rate, 0.50)
            else:
                rate = base_rate + rng.normal(0, 0.02)
                rate = np.clip(rate, 0.60, 1.0)

            for d in dates:
                present = int(rng.random() < rate)
                rows.append({"student_id": sid,
                             "date": d.strftime("%Y-%m-%d"),
                             "present": present})

    return pd.DataFrame(rows)


# ── 模試生成 ──────────────────────────────────────────

def generate_mock_exams(students: pd.DataFrame, grades: pd.DataFrame,
                        rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    exam_ids = [f"mock_{y}_{m:02d}" for y in (2024, 2025, 2026)
                for m in (6, 10, 1)][:N_TERMS + 3]

    for _, stu in students.iterrows():
        sid = stu["student_id"]
        cls = LATENT_CLASSES[stu["latent_class"]]

        for exam_idx, exam_id in enumerate(exam_ids[:MOCK_EXAMS_PER_YEAR * 2]):
            for subj in SUBJECTS:
                base = cls["abilities"][subj] * 50 + 25  # 25-75レンジ
                noise = rng.normal(0, 5)

                # 離脱型: 模試は定期テストより低い（詰め込み効果の逆）
                if stu["latent_class"] == 3:
                    base -= 5

                dev_score = round(np.clip(base + noise, 25, 75), 1)
                rows.append({"student_id": sid, "exam_id": exam_id,
                             "subject": subj, "deviation_score": dev_score})

    return pd.DataFrame(rows)


# ── 入試成績生成 ──────────────────────────────────────

def generate_entrance_scores(students: pd.DataFrame,
                             rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for _, stu in students.iterrows():
        sid = stu["student_id"]
        cls = LATENT_CLASSES[stu["latent_class"]]
        for subj in SUBJECTS:
            base = cls["abilities"][subj] * 80 + 10
            noise = rng.normal(0, 8)
            score = round(np.clip(base + noise, 0, 100), 1)
            rows.append({"student_id": sid, "subject": subj, "score": score})

    return pd.DataFrame(rows)


# ── グラウンドトゥルース ──────────────────────────────

def generate_ground_truth(students: pd.DataFrame) -> dict:
    class_counts = students["latent_class"].value_counts().to_dict()
    return {
        "description": "検証用: 分析パイプラインが再発見すべき植え込み信号",
        "latent_classes": {
            str(k): {
                "name": v["name"],
                "name_ja": v["name_ja"],
                "target_proportion": v["proportion"],
                "actual_count": class_counts.get(k, 0),
            }
            for k, v in LATENT_CLASSES.items()
        },
        "planted_connections": [
            {
                "type": "cross_subject_prerequisite",
                "from": "math:algebraic_manipulation (q01-q06)",
                "to": "physics:formula_application (q19-q24)",
                "mechanism": "math ability > 0.6 → +0.18 boost on physics items",
                "expected_partial_correlation": "> 0.15",
            },
            {
                "type": "cross_subject_prerequisite",
                "from": "math:algebraic_manipulation",
                "to": "chemistry:equilibrium_calculation (q19-q24)",
                "mechanism": "math ability > 0.6 → +0.12 boost on chemistry items",
                "expected_partial_correlation": "> 0.10",
            },
            {
                "type": "bottleneck_skill",
                "skill": "word_problem_reading",
                "affects": ["math q25-q30", "physics q25-q30", "chemistry q25-q30"],
                "mechanism": "reading_latent < 0.4 → -0.25 penalty",
                "expected_bridge_centrality": "high",
            },
            {
                "type": "temporal_pattern",
                "description": "離脱型の出欠→成績低下シーケンス",
                "mechanism": "class 3: attendance decline term over term, grade crash term 4+",
            },
        ],
        "student_assignments": {
            row["student_id"]: int(row["latent_class"])
            for _, row in students.iterrows()
        },
    }


# ── メイン ────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="サンプル教育データ生成")
    parser.add_argument("--output-dir", default="discovery/data/sample")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-students", type=int, default=500)
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    print(f"生成開始: {args.n_students}人, seed={args.seed}")

    print("  生徒データ...", end=" ", flush=True)
    students = generate_students(args.n_students, rng)
    students.drop(columns=["reading_latent"]).to_csv(out / "students.csv", index=False)
    print(f"OK ({len(students)}人)")

    print("  設問応答データ...", end=" ", flush=True)
    responses = generate_item_responses(students, rng)
    responses.to_csv(out / "item_responses.csv", index=False)
    print(f"OK ({len(responses)}行)")

    print("  成績データ...", end=" ", flush=True)
    grades = generate_grades(students, rng)
    grades.to_csv(out / "grades.csv", index=False)
    print(f"OK ({len(grades)}行)")

    print("  出欠データ...", end=" ", flush=True)
    attendance = generate_attendance(students, rng)
    attendance.to_csv(out / "attendance.csv", index=False)
    print(f"OK ({len(attendance)}行)")

    print("  模試データ...", end=" ", flush=True)
    mock_exams = generate_mock_exams(students, grades, rng)
    mock_exams.to_csv(out / "mock_exams.csv", index=False)
    print(f"OK ({len(mock_exams)}行)")

    print("  入試データ...", end=" ", flush=True)
    entrance = generate_entrance_scores(students, rng)
    entrance.to_csv(out / "entrance_scores.csv", index=False)
    print(f"OK ({len(entrance)}行)")

    print("  グラウンドトゥルース...", end=" ", flush=True)
    gt = generate_ground_truth(students)
    with open(out / "ground_truth.json", "w", encoding="utf-8") as f:
        json.dump(gt, f, ensure_ascii=False, indent=2)
    print("OK")

    print(f"\n完了: {out}/")
    print(f"  生徒: {len(students)}")
    print(f"  クラス分布: {students['latent_class'].value_counts().sort_index().to_dict()}")
    print(f"  応答レコード: {len(responses):,}")


if __name__ == "__main__":
    main()
