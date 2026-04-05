"""相互情報量分析モジュール

教科間の非線形依存関係を相互情報量で検出する。
Pearson相関では捉えられない非線形的な教科間関係を明らかにする。

Usage:
    python -m discovery.analysis.mutual_info [--data-dir ...] [--output-dir ...]
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_regression


# ── 定数 ────────────────────────────────────────────────

SUBJECTS = ["math", "physics", "chemistry", "english", "japanese"]

SUBJECT_JA = {
    "math": "数学", "physics": "物理", "chemistry": "化学",
    "english": "英語", "japanese": "国語",
}


# ── 相互情報量行列 ─────────────────────────────────────

def compute_mi_matrix(grades_df: pd.DataFrame) -> pd.DataFrame:
    """教科間のペアワイズ相互情報量行列を計算する。

    各教科の平均成績を特徴量とし、sklearn の mutual_info_regression で
    ペアワイズ MI を推定する。
    """
    if grades_df.empty:
        return pd.DataFrame()

    # 生徒ごと教科ごとの平均成績
    pivot = (
        grades_df
        .groupby(["student_id", "subject"])["grade"]
        .mean()
        .unstack(fill_value=0.0)
    )

    # 存在する教科のみ
    available = [s for s in SUBJECTS if s in pivot.columns]
    if len(available) < 2:
        return pd.DataFrame()

    pivot = pivot[available]
    n_subjects = len(available)

    mi_matrix = np.zeros((n_subjects, n_subjects))

    for i in range(n_subjects):
        for j in range(n_subjects):
            if i == j:
                # 自己MI はエントロピーだが、比較用に1に正規化
                mi_matrix[i, j] = np.nan
            else:
                X = pivot.iloc[:, [i]].values
                y = pivot.iloc[:, j].values
                try:
                    mi = mutual_info_regression(
                        X, y, random_state=42, n_neighbors=5
                    )[0]
                    mi_matrix[i, j] = mi
                except Exception:
                    mi_matrix[i, j] = 0.0

    return pd.DataFrame(mi_matrix, index=available, columns=available)


# ── Pearson 相関行列 ───────────────────────────────────

def compute_correlation_matrix(grades_df: pd.DataFrame) -> pd.DataFrame:
    """教科間の Pearson 相関行列を計算する。"""
    if grades_df.empty:
        return pd.DataFrame()

    pivot = (
        grades_df
        .groupby(["student_id", "subject"])["grade"]
        .mean()
        .unstack(fill_value=0.0)
    )

    available = [s for s in SUBJECTS if s in pivot.columns]
    if len(available) < 2:
        return pd.DataFrame()

    return pivot[available].corr()


# ── 非線形依存検出 ─────────────────────────────────────

def find_nonlinear_dependencies(mi_matrix: pd.DataFrame,
                                 corr_matrix: pd.DataFrame,
                                 threshold: float = 0.15) -> list:
    """MI は高いが |相関| が低いペアを非線形依存として検出する。

    判定基準: MI > median(MI) かつ |r| < threshold
    """
    if mi_matrix.empty or corr_matrix.empty:
        return []

    subjects = mi_matrix.index.tolist()
    n = len(subjects)

    # MI の中央値（対角除外）
    mi_values = []
    for i in range(n):
        for j in range(n):
            if i != j:
                v = mi_matrix.iloc[i, j]
                if not np.isnan(v):
                    mi_values.append(v)

    if not mi_values:
        return []

    mi_median = np.median(mi_values)

    dependencies = []
    for i in range(n):
        for j in range(i + 1, n):
            mi_val = mi_matrix.iloc[i, j]
            corr_val = corr_matrix.iloc[i, j]

            if np.isnan(mi_val) or np.isnan(corr_val):
                continue

            # 非線形判定: MI が中央値以上かつ相関が低い
            if mi_val > mi_median and abs(corr_val) < threshold:
                subj_i = subjects[i]
                subj_j = subjects[j]
                dependencies.append({
                    "subject_pair": [subj_i, subj_j],
                    "subject_pair_ja": [SUBJECT_JA.get(subj_i, subj_i),
                                        SUBJECT_JA.get(subj_j, subj_j)],
                    "mutual_information": round(float(mi_val), 4),
                    "pearson_correlation": round(float(corr_val), 4),
                    "nonlinearity_gap": round(float(mi_val - abs(corr_val)), 4),
                    "description": (
                        f"{SUBJECT_JA.get(subj_i, subj_i)}と"
                        f"{SUBJECT_JA.get(subj_j, subj_j)}の間に"
                        f"線形相関(r={corr_val:.3f})では捉えられない"
                        f"非線形的な依存関係(MI={mi_val:.3f})が存在"
                    ),
                })

    dependencies.sort(key=lambda d: d["nonlinearity_gap"], reverse=True)
    return dependencies


# ── メインエントリ ──────────────────────────────────────

def run_mutual_info_analysis(data_dir: Path, output_dir: Path) -> dict:
    """相互情報量分析パイプラインを実行し、mutual_info.json を出力する。"""
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # データ読込
    print("  [相互情報量] データ読込中...", flush=True)
    grades_path = data_dir / "grades.csv"
    if not grades_path.exists():
        raise FileNotFoundError(f"grades.csv が見つかりません: {grades_path}")

    grades_df = pd.read_csv(grades_path)
    print(f"  [相互情報量] {len(grades_df):,}件の成績データを読込", flush=True)

    # 相互情報量行列
    print("  [相互情報量] MI行列計算中...", flush=True)
    mi_matrix = compute_mi_matrix(grades_df)

    if mi_matrix.empty:
        print("  [相互情報量] 警告: MI行列の計算に失敗", flush=True)
        return {}

    # Pearson 相関行列
    print("  [相互情報量] Pearson相関行列計算中...", flush=True)
    corr_matrix = compute_correlation_matrix(grades_df)

    # 非線形依存検出
    print("  [相互情報量] 非線形依存検出中...", flush=True)
    nonlinear = find_nonlinear_dependencies(mi_matrix, corr_matrix, threshold=0.15)

    # 出力構造
    # MI行列をシリアライズ可能な形に変換
    mi_dict = {}
    for subj in mi_matrix.index:
        row = {}
        for col in mi_matrix.columns:
            val = mi_matrix.loc[subj, col]
            row[col] = round(float(val), 4) if not np.isnan(val) else None
        mi_dict[subj] = row

    corr_dict = {}
    for subj in corr_matrix.index:
        row = {}
        for col in corr_matrix.columns:
            val = corr_matrix.loc[subj, col]
            row[col] = round(float(val), 4) if not np.isnan(val) else None
        corr_dict[subj] = row

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mutual_information_matrix": mi_dict,
        "pearson_correlation_matrix": corr_dict,
        "nonlinear_dependencies": nonlinear,
        "summary": {
            "total_pairs": len(mi_matrix) * (len(mi_matrix) - 1) // 2,
            "nonlinear_pairs_detected": len(nonlinear),
        },
    }

    output_path = output_dir / "mutual_info.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  [相互情報量] 完了: {len(nonlinear)}個の非線形依存を検出", flush=True)
    for dep in nonlinear:
        pair = " - ".join(dep["subject_pair_ja"])
        print(f"    {pair}: MI={dep['mutual_information']:.4f}, r={dep['pearson_correlation']:.4f}", flush=True)
    print(f"  [相互情報量] 出力: {output_path}", flush=True)

    # patterns.json への追記（存在する場合）
    patterns_path = output_dir / "patterns.json"
    if patterns_path.exists() and nonlinear:
        _append_to_patterns(patterns_path, nonlinear)

    return result


def _append_to_patterns(patterns_path: Path, nonlinear: list) -> None:
    """既存の patterns.json に非線形依存パターンを追記する。"""
    try:
        with open(patterns_path, "r", encoding="utf-8") as f:
            patterns_data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return

    existing_patterns = patterns_data.get("patterns", [])
    next_id = len(existing_patterns) + 1

    for dep in nonlinear:
        pair_ja = " - ".join(dep["subject_pair_ja"])
        pattern = {
            "id": f"P{next_id:03d}",
            "name": f"非線形依存: {pair_ja}",
            "tags": ["#非線形", "#相互情報量"],
            "context": f"{pair_ja}間の教科成績パターン",
            "problem": (
                f"Pearson相関(r={dep['pearson_correlation']:.3f})は低いが、"
                f"相互情報量(MI={dep['mutual_information']:.3f})は高い"
            ),
            "solution": "成績間に非線形的な関係が存在。条件付き分析や二次元分布の可視化を推奨",
            "metrics": {
                "mutual_information": dep["mutual_information"],
                "pearson_correlation": dep["pearson_correlation"],
                "nonlinearity_gap": dep["nonlinearity_gap"],
            },
            "antecedent_items": [dep["subject_pair"][0]],
            "consequent_items": [dep["subject_pair"][1]],
            "importance_rank": next_id,
        }
        existing_patterns.append(pattern)
        next_id += 1

    patterns_data["patterns"] = existing_patterns
    with open(patterns_path, "w", encoding="utf-8") as f:
        json.dump(patterns_data, f, ensure_ascii=False, indent=2)

    print(f"  [相互情報量] patterns.json に{len(nonlinear)}パターンを追記", flush=True)


# ── CLI ─────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="相互情報量分析")
    parser.add_argument("--data-dir", type=Path, default=Path("discovery/data/sample"))
    parser.add_argument("--output-dir", type=Path, default=Path("discovery/analysis/output"))
    args = parser.parse_args()

    run_mutual_info_analysis(args.data_dir, args.output_dir)
