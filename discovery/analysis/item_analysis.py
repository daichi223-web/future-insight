"""CTT (Classical Test Theory) 項目分析モジュール

設問ごとの難易度・識別力・点双列相関を計算し、
問題のある設問をフラグ付けする。

Usage:
    python -m discovery.analysis.item_analysis [--data-dir ...] [--output-dir ...]
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from discovery.analysis.config import ITEM_ANALYSIS as CFG


# ── スキルマッピング定数 ─────────────────────────────────

SUBJECTS = ["math", "physics", "chemistry", "english", "japanese"]


# ── 難易度（正答率） ─────────────────────────────────────

def compute_difficulty(responses_df: pd.DataFrame) -> pd.DataFrame:
    """設問ごとの難易度（正答率 p）を計算する。"""
    if responses_df.empty:
        return pd.DataFrame(columns=["item_id", "subject", "difficulty"])

    result = (
        responses_df
        .groupby(["item_id", "subject"])["correct"]
        .mean()
        .reset_index()
        .rename(columns={"correct": "difficulty"})
    )
    return result


# ── 識別力（D-index） ───────────────────────────────────

def compute_discrimination(responses_df: pd.DataFrame) -> pd.DataFrame:
    """D-index を計算する。

    教科ごとの合計点で上位27%・下位27%に分割し、
    各設問の正答率差を識別力とする。
    """
    if responses_df.empty:
        return pd.DataFrame(columns=["item_id", "subject", "discrimination"])

    rows = []
    for subj, subj_df in responses_df.groupby("subject"):
        # 受験者ごとの教科合計点
        totals = subj_df.groupby("student_id")["correct"].sum()
        n = len(totals)
        cutoff_low = totals.quantile(CFG["percentile_cutoff"])
        cutoff_high = totals.quantile(1 - CFG["percentile_cutoff"])

        top_students = set(totals[totals >= cutoff_high].index)
        bottom_students = set(totals[totals <= cutoff_low].index)

        if not top_students or not bottom_students:
            # データ不足の場合は全設問 0
            for item_id in subj_df["item_id"].unique():
                rows.append({"item_id": item_id, "subject": subj, "discrimination": 0.0})
            continue

        for item_id, item_df in subj_df.groupby("item_id"):
            top_rate = item_df[item_df["student_id"].isin(top_students)]["correct"].mean()
            bottom_rate = item_df[item_df["student_id"].isin(bottom_students)]["correct"].mean()
            d_index = top_rate - bottom_rate
            rows.append({"item_id": item_id, "subject": subj, "discrimination": round(d_index, 4)})

    return pd.DataFrame(rows)


# ── 点双列相関 ──────────────────────────────────────────

def compute_point_biserial(responses_df: pd.DataFrame) -> pd.DataFrame:
    """各設問の正答 (0/1) と教科合計点の点双列相関を計算する。"""
    if responses_df.empty:
        return pd.DataFrame(columns=["item_id", "subject", "point_biserial"])

    rows = []
    for subj, subj_df in responses_df.groupby("subject"):
        totals = subj_df.groupby("student_id")["correct"].sum()

        # 設問ごとのピボット
        pivot = subj_df.pivot(index="student_id", columns="item_id", values="correct")
        for item_id in pivot.columns:
            item_scores = pivot[item_id].dropna()
            matched_totals = totals.loc[item_scores.index]

            # 分散ゼロチェック
            if item_scores.std() == 0 or matched_totals.std() == 0:
                rpb = 0.0
            else:
                rpb = item_scores.corr(matched_totals)
                if np.isnan(rpb):
                    rpb = 0.0

            rows.append({"item_id": item_id, "subject": subj, "point_biserial": round(rpb, 4)})

    return pd.DataFrame(rows)


# ── フラグ判定 ──────────────────────────────────────────

def flag_problematic_items(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """問題のある設問にフラグを付ける。

    フラグ条件:
    - difficulty < 0.10 (難しすぎ)
    - difficulty > 0.90 (易しすぎ)
    - discrimination < 0.20 (識別力不足)
    """
    if metrics_df.empty:
        metrics_df["flags"] = []
        return metrics_df

    flags_list = []
    for _, row in metrics_df.iterrows():
        flags = []
        d = row.get("difficulty", 0.5)
        disc = row.get("discrimination", 0.3)

        if d < CFG["flag_difficulty_low"]:
            flags.append("too_hard")
        if d > CFG["flag_difficulty_high"]:
            flags.append("too_easy")
        if disc < CFG["flag_discrimination_low"]:
            flags.append("low_discrimination")

        flags_list.append(flags)

    metrics_df = metrics_df.copy()
    metrics_df["flags"] = flags_list
    return metrics_df


# ── メインエントリ ──────────────────────────────────────

def run_item_analysis(data_dir: Path, output_dir: Path) -> dict:
    """項目分析パイプラインを実行し、item_analysis.json を出力する。"""
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("  [項目分析] データ読込中...", flush=True)
    responses_path = data_dir / "item_responses.csv"
    if not responses_path.exists():
        raise FileNotFoundError(f"item_responses.csv が見つかりません: {responses_path}")

    responses_df = pd.read_csv(responses_path)
    print(f"  [項目分析] {len(responses_df):,}件のレスポンスを読込", flush=True)

    # 各指標の計算
    print("  [項目分析] 難易度計算中...", flush=True)
    difficulty = compute_difficulty(responses_df)

    print("  [項目分析] 識別力計算中...", flush=True)
    discrimination = compute_discrimination(responses_df)

    print("  [項目分析] 点双列相関計算中...", flush=True)
    pbis = compute_point_biserial(responses_df)

    # 統合
    metrics = difficulty.merge(discrimination, on=["item_id", "subject"], how="outer")
    metrics = metrics.merge(pbis, on=["item_id", "subject"], how="outer")
    metrics = metrics.fillna(0.0)

    # フラグ付け
    print("  [項目分析] フラグ判定中...", flush=True)
    metrics = flag_problematic_items(metrics)

    # 出力構造の組み立て
    total_items = len(metrics)
    flagged_count = metrics["flags"].apply(len).gt(0).sum()

    summary = {
        "total_items": int(total_items),
        "flagged_items": int(flagged_count),
        "mean_difficulty": round(float(metrics["difficulty"].mean()), 4),
        "mean_discrimination": round(float(metrics["discrimination"].mean()), 4),
    }

    by_subject = {}
    for subj in SUBJECTS:
        subj_metrics = metrics[metrics["subject"] == subj].sort_values("item_id")
        items = []
        for _, row in subj_metrics.iterrows():
            items.append({
                "item_id": row["item_id"],
                "difficulty": round(float(row["difficulty"]), 4),
                "discrimination": round(float(row["discrimination"]), 4),
                "point_biserial": round(float(row["point_biserial"]), 4),
                "flags": row["flags"],
            })
        by_subject[subj] = {"items": items}

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "by_subject": by_subject,
    }

    output_path = output_dir / "item_analysis.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  [項目分析] 完了: {total_items}問, うち{flagged_count}問にフラグ", flush=True)
    print(f"  [項目分析] 出力: {output_path}", flush=True)

    return result


# ── CLI ─────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CTT 項目分析")
    parser.add_argument("--data-dir", type=Path, default=Path("discovery/data/sample"))
    parser.add_argument("--output-dir", type=Path, default=Path("discovery/analysis/output"))
    args = parser.parse_args()

    run_item_analysis(args.data_dir, args.output_dir)
