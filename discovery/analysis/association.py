"""相関ルールマイニングモジュール

設問の正答/誤答パターンから教科横断的な関連ルールを抽出し、
パターン言語形式 (Context-Problem-Solution) で出力する。

Usage:
    python -m discovery.analysis.association [--data-dir ...] [--output-dir ...]
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from mlxtend.frequent_patterns import apriori, association_rules
except ImportError:
    apriori = None
    association_rules = None


# ── 定数 ────────────────────────────────────────────────

SUBJECTS = ["math", "physics", "chemistry", "english", "japanese"]

# スキル名（日本語）
SKILL_RANGES = {
    (1, 6): 0,
    (7, 12): 1,
    (13, 18): 2,
    (19, 24): 3,
    (25, 30): 4,
}

SKILL_NAMES_JA = {
    "math": {0: "代数操作", 1: "幾何推論", 2: "統計的思考", 3: "関数理解", 4: "文章題読解"},
    "physics": {0: "力学概念", 1: "波動理解", 2: "エネルギー保存", 3: "公式適用", 4: "文章題読解"},
    "chemistry": {0: "化学量論", 1: "周期表", 2: "反応機構", 3: "平衡計算", 4: "文章題読解"},
    "english": {0: "文法", 1: "語彙", 2: "読解", 3: "リスニング", 4: "ライティング"},
    "japanese": {0: "漢字知識", 1: "古典文法", 2: "読解", 3: "小論文", 4: "批評的読解"},
}

SUBJECT_JA = {
    "math": "数学", "physics": "物理", "chemistry": "化学",
    "english": "英語", "japanese": "国語",
}


def _get_skill_index(q_num: int) -> int:
    """設問番号からスキルインデックスを返す。"""
    for (lo, hi), idx in SKILL_RANGES.items():
        if lo <= q_num <= hi:
            return idx
    return -1


def _get_subject(item_id: str) -> str:
    """item_id (e.g. 'math_q01') から教科を抽出する。"""
    for subj in SUBJECTS:
        if item_id.startswith(subj):
            return subj
    # '_wrong' サフィックスの場合
    clean = item_id.replace("_wrong", "")
    for subj in SUBJECTS:
        if clean.startswith(subj):
            return subj
    return ""


def _get_skill_label(item_id: str) -> str:
    """item_id からスキルの日本語ラベルを返す。"""
    clean = item_id.replace("_wrong", "")
    subj = _get_subject(clean)
    if not subj:
        return item_id

    try:
        q_num = int(clean.split("_q")[1])
    except (IndexError, ValueError):
        return item_id

    skill_idx = _get_skill_index(q_num)
    if skill_idx < 0:
        return item_id

    skill_ja = SKILL_NAMES_JA.get(subj, {}).get(skill_idx, "")
    subj_ja = SUBJECT_JA.get(subj, subj)
    is_wrong = "_wrong" in item_id
    suffix = "（誤答）" if is_wrong else "（正答）"
    return f"{subj_ja}:{skill_ja}{suffix}"


# ── バイナリ行列の準備 ─────────────────────────────────

def prepare_binary_matrix(responses_df: pd.DataFrame) -> pd.DataFrame:
    """設問応答を学生 x 設問のバイナリ行列に変換する。

    正答列と誤答列（_wrong サフィックス）の両方を生成。
    """
    if responses_df.empty:
        return pd.DataFrame()

    # ピボット: 学生 x 設問
    pivot = responses_df.pivot_table(
        index="student_id",
        columns="item_id",
        values="correct",
        aggfunc="first",
    ).fillna(0).astype(int)

    # 誤答列を追加
    wrong_cols = {}
    for col in pivot.columns:
        wrong_cols[f"{col}_wrong"] = (1 - pivot[col]).astype(int)

    wrong_df = pd.DataFrame(wrong_cols, index=pivot.index)
    binary_df = pd.concat([pivot, wrong_df], axis=1)

    # bool 型に変換（mlxtend 要件）
    binary_df = binary_df.astype(bool)

    return binary_df


# ── ルールマイニング ───────────────────────────────────

def mine_rules(binary_df: pd.DataFrame,
               min_support: float = 0.05,
               min_confidence: float = 0.5,
               min_lift: float = 1.2) -> pd.DataFrame:
    """Apriori + 相関ルール抽出を実行する。"""
    if binary_df.empty:
        return pd.DataFrame()

    if apriori is None or association_rules is None:
        print("  [相関ルール] 警告: mlxtend 未インストール", flush=True)
        return pd.DataFrame()

    try:
        frequent = apriori(binary_df, min_support=min_support, use_colnames=True)
    except Exception as e:
        print(f"  [相関ルール] 警告: Apriori 実行失敗: {e}", flush=True)
        return pd.DataFrame()

    if frequent.empty:
        print("  [相関ルール] 頻出パターンが見つかりません", flush=True)
        return pd.DataFrame()

    try:
        rules = association_rules(frequent, metric="lift", min_threshold=min_lift)
    except Exception as e:
        print(f"  [相関ルール] 警告: ルール抽出失敗: {e}", flush=True)
        return pd.DataFrame()

    if rules.empty:
        return pd.DataFrame()

    # confidence フィルタ
    rules = rules[rules["confidence"] >= min_confidence].copy()
    rules = rules.sort_values("lift", ascending=False).reset_index(drop=True)

    return rules


# ── 教科横断フィルタ ──────────────────────────────────

def filter_cross_subject(rules_df: pd.DataFrame) -> pd.DataFrame:
    """前件と後件が異なる教科のルールのみを残す。"""
    if rules_df.empty:
        return rules_df

    def _is_cross(row):
        ant_subjects = {_get_subject(item) for item in row["antecedents"]}
        con_subjects = {_get_subject(item) for item in row["consequents"]}
        ant_subjects.discard("")
        con_subjects.discard("")
        return not ant_subjects.intersection(con_subjects)

    mask = rules_df.apply(_is_cross, axis=1)
    return rules_df[mask].reset_index(drop=True)


# ── パターン言語変換 ──────────────────────────────────

def format_as_patterns(rules_df: pd.DataFrame, top_n: int = 20) -> list:
    """ルールをパターン言語形式 (Context-Problem-Solution) に変換する。"""
    if rules_df.empty:
        return []

    patterns = []
    for rank, (_, rule) in enumerate(rules_df.head(top_n).iterrows(), 1):
        ant_items = sorted(rule["antecedents"])
        con_items = sorted(rule["consequents"])

        ant_labels = [_get_skill_label(item) for item in ant_items]
        con_labels = [_get_skill_label(item) for item in con_items]

        # ルール方向の判定
        ant_has_wrong = any("_wrong" in item for item in ant_items)
        con_has_wrong = any("_wrong" in item for item in con_items)

        # タグ生成
        tags = []
        ant_subjects = {_get_subject(item) for item in ant_items}
        con_subjects = {_get_subject(item) for item in con_items}
        ant_subjects.discard("")
        con_subjects.discard("")

        if not ant_subjects.intersection(con_subjects):
            tags.append("#教科横断")

        if ant_has_wrong or con_has_wrong:
            tags.append("#つまずき連鎖")
        else:
            tags.append("#前提条件")

        if any("word_problem" in item or "reading" in item for item in ant_items + con_items):
            tags.append("#読解力ボトルネック")

        # パターン名の生成
        ant_subj_ja = "/".join(SUBJECT_JA.get(s, s) for s in sorted(ant_subjects))
        con_subj_ja = "/".join(SUBJECT_JA.get(s, s) for s in sorted(con_subjects))

        if ant_has_wrong and con_has_wrong:
            name = f"つまずきの連鎖: {ant_subj_ja}→{con_subj_ja}"
        elif ant_has_wrong:
            name = f"弱点の波及: {ant_subj_ja}→{con_subj_ja}"
        else:
            name = f"強みの転移: {ant_subj_ja}→{con_subj_ja}"

        # Context / Problem / Solution
        context = f"{', '.join(ant_labels)}のパターン"
        problem = f"{', '.join(con_labels)}と強い連動（lift={rule['lift']:.2f}）"

        if ant_has_wrong:
            solution = (
                f"{ant_subj_ja}の該当スキル補強が"
                f"{con_subj_ja}の改善に波及する可能性"
            )
        else:
            solution = (
                f"{ant_subj_ja}の学習成功パターンを"
                f"{con_subj_ja}指導に活用可能"
            )

        patterns.append({
            "id": f"P{rank:03d}",
            "name": name,
            "tags": tags,
            "context": context,
            "problem": problem,
            "solution": solution,
            "metrics": {
                "support": round(float(rule["support"]), 4),
                "confidence": round(float(rule["confidence"]), 4),
                "lift": round(float(rule["lift"]), 4),
            },
            "antecedent_items": ant_items,
            "consequent_items": con_items,
            "importance_rank": rank,
        })

    return patterns


# ── メインエントリ ──────────────────────────────────────

def run_association_analysis(data_dir: Path, output_dir: Path) -> dict:
    """相関ルール分析パイプラインを実行し、patterns.json を出力する。"""
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("  [相関ルール] データ読込中...", flush=True)
    responses_path = data_dir / "item_responses.csv"
    if not responses_path.exists():
        raise FileNotFoundError(f"item_responses.csv が見つかりません: {responses_path}")

    responses_df = pd.read_csv(responses_path)
    print(f"  [相関ルール] {len(responses_df):,}件のレスポンスを読込", flush=True)

    # スキルレベルに集約（設問単位だとパターンが多すぎる）
    print("  [相関ルール] スキルレベルに集約中...", flush=True)
    responses_df = responses_df.copy()
    responses_df["q_num"] = (
        responses_df["item_id"]
        .str.extract(r"_q(\d+)$")[0]
        .astype(int)
    )
    responses_df["skill_idx"] = responses_df["q_num"].apply(_get_skill_index)

    # スキルごとの正答率が 0.5 以上なら 1（習得）、未満なら 0（未習得）
    skill_scores = (
        responses_df
        .groupby(["student_id", "subject", "skill_idx"])["correct"]
        .mean()
        .reset_index()
    )
    skill_scores["mastered"] = (skill_scores["correct"] >= 0.5).astype(int)
    skill_scores["skill_item"] = (
        skill_scores["subject"] + "_skill" + skill_scores["skill_idx"].astype(str)
    )

    # バイナリ行列
    print("  [相関ルール] バイナリ行列構築中...", flush=True)
    pivot = skill_scores.pivot_table(
        index="student_id",
        columns="skill_item",
        values="mastered",
        aggfunc="first",
    ).fillna(0).astype(int)

    # 習得列のみ使用（未習得列を含めると組合せ爆発するため）
    binary_df = pivot.astype(bool)

    print(f"  [相関ルール] バイナリ行列: {binary_df.shape[0]}人 x {binary_df.shape[1]}特徴", flush=True)

    # ルールマイニング
    print("  [相関ルール] Apriori 実行中...", flush=True)
    rules = mine_rules(binary_df, min_support=0.15, min_confidence=0.5, min_lift=1.2)

    if rules.empty:
        print("  [相関ルール] ルールが見つかりませんでした（閾値を緩和して再試行）", flush=True)
        rules = mine_rules(binary_df, min_support=0.10, min_confidence=0.4, min_lift=1.1)

    total_rules = len(rules)
    print(f"  [相関ルール] 抽出ルール数: {total_rules}", flush=True)

    # 教科横断フィルタ
    print("  [相関ルール] 教科横断フィルタリング中...", flush=True)
    cross_rules = filter_cross_subject(rules)
    print(f"  [相関ルール] 教科横断ルール: {len(cross_rules)}", flush=True)

    # パターン変換（教科横断優先、全ルールも含む）
    print("  [相関ルール] パターン言語変換中...", flush=True)
    cross_patterns = format_as_patterns(cross_rules, top_n=15)
    all_patterns = format_as_patterns(rules, top_n=10)

    # 重複排除して結合
    seen_ids = {p["id"] for p in cross_patterns}
    for p in all_patterns:
        if p["id"] not in seen_ids:
            p["id"] = f"P{len(cross_patterns) + len(seen_ids) + 1:03d}"
            cross_patterns.append(p)

    # 再番号付け
    for i, p in enumerate(cross_patterns, 1):
        p["id"] = f"P{i:03d}"
        p["importance_rank"] = i

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_rules_found": total_rules,
            "cross_subject_rules": len(filter_cross_subject(rules)) if not rules.empty else 0,
            "patterns_output": len(cross_patterns),
        },
        "patterns": cross_patterns,
    }

    output_path = output_dir / "patterns.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  [相関ルール] 完了: {len(cross_patterns)}パターンを出力", flush=True)
    print(f"  [相関ルール] 出力: {output_path}", flush=True)

    return result


# ── CLI ─────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="相関ルールマイニング")
    parser.add_argument("--data-dir", type=Path, default=Path("discovery/data/sample"))
    parser.add_argument("--output-dir", type=Path, default=Path("discovery/analysis/output"))
    args = parser.parse_args()

    run_association_analysis(args.data_dir, args.output_dir)
