"""IRT (Item Response Theory) 2PLモデル分析モジュール

各設問の難易度(b)・識別力(a)パラメータと、各生徒の能力(theta)を推定する。
scipy.optimizeによる実装で外部IRTパッケージ不要。

Usage:
    python -m discovery.analysis.irt_analysis [--data-dir ...] [--output-dir ...]
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit  # logistic function


SUBJECTS = ["math", "physics", "chemistry", "english", "japanese"]
SUBJECT_JA = {
    "math": "数学", "physics": "物理", "chemistry": "化学",
    "english": "英語", "japanese": "国語",
}


def _irf_2pl(theta: np.ndarray, a: float, b: float) -> np.ndarray:
    """2PL IRFモデル: P(correct | theta, a, b) = 1 / (1 + exp(-a*(theta-b)))"""
    return expit(a * (theta - b))


def estimate_2pl(response_matrix: np.ndarray, max_iter: int = 50) -> dict:
    """2PLパラメータ推定（Joint MLE風の交互推定）。

    Args:
        response_matrix: N(生徒) x J(設問) の二値行列 (0/1)
        max_iter: 交互推定の最大反復数

    Returns:
        dict with keys: theta (N,), a (J,), b (J,), converged (bool)
    """
    N, J = response_matrix.shape

    # 初期値: thetaは標準化得点、aは1.0、bはlogit(正答率)
    p_obs = response_matrix.mean(axis=0)
    p_obs = np.clip(p_obs, 0.01, 0.99)

    theta = np.zeros(N)
    a = np.ones(J)
    b = -np.log(p_obs / (1 - p_obs))  # logit(p)の符号反転

    # 生徒の合計点で初期theta推定
    raw_scores = response_matrix.sum(axis=1)
    raw_scores_std = (raw_scores - raw_scores.mean()) / (raw_scores.std() + 1e-8)
    theta = np.clip(raw_scores_std, -3, 3)

    prev_ll = -np.inf

    for iteration in range(max_iter):
        # === E-step: thetaを固定してa, bを推定 ===
        for j in range(J):
            resp_j = response_matrix[:, j]
            valid = ~np.isnan(resp_j)
            if valid.sum() < 10:
                continue

            def neg_ll_item(params):
                a_j, b_j = params
                if a_j < 0.1:
                    return 1e10
                p = _irf_2pl(theta[valid], a_j, b_j)
                p = np.clip(p, 1e-8, 1 - 1e-8)
                ll = resp_j[valid] * np.log(p) + (1 - resp_j[valid]) * np.log(1 - p)
                return -ll.sum()

            result = minimize(neg_ll_item, [a[j], b[j]], method="Nelder-Mead",
                              options={"maxiter": 100, "xatol": 0.01})
            if result.success or result.fun < neg_ll_item([a[j], b[j]]):
                a[j] = max(0.2, min(result.x[0], 3.0))  # a を [0.2, 3.0] に制約
                b[j] = max(-4.0, min(result.x[1], 4.0))  # b を [-4, 4] に制約

        # === M-step: a, bを固定してthetaを推定 ===
        for i in range(N):
            resp_i = response_matrix[i, :]
            valid = ~np.isnan(resp_i)
            if valid.sum() < 5:
                continue

            def neg_ll_person(params):
                th = params[0]
                p = _irf_2pl(np.array([th]), a[valid], b[valid]).flatten()
                p = np.clip(p, 1e-8, 1 - 1e-8)
                ll = resp_i[valid] * np.log(p) + (1 - resp_i[valid]) * np.log(1 - p)
                # 正規事前分布（MAP推定）
                prior = -0.5 * th ** 2
                return -(ll.sum() + prior)

            result = minimize(neg_ll_person, [theta[i]], method="Nelder-Mead",
                              options={"maxiter": 50})
            if result.success:
                theta[i] = max(-4.0, min(result.x[0], 4.0))

        # 収束判定
        p_pred = np.zeros_like(response_matrix, dtype=float)
        for j in range(J):
            p_pred[:, j] = _irf_2pl(theta, a[j], b[j])
        p_pred = np.clip(p_pred, 1e-8, 1 - 1e-8)
        ll = np.nansum(
            response_matrix * np.log(p_pred) + (1 - response_matrix) * np.log(1 - p_pred)
        )

        if abs(ll - prev_ll) < 0.1:
            return {"theta": theta, "a": a, "b": b, "converged": True, "iterations": iteration + 1, "log_likelihood": ll}
        prev_ll = ll

    return {"theta": theta, "a": a, "b": b, "converged": False, "iterations": max_iter, "log_likelihood": ll}


def compute_test_information(theta_range: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """テスト情報関数を計算。"""
    info = np.zeros_like(theta_range)
    for j in range(len(a)):
        p = _irf_2pl(theta_range, a[j], b[j])
        q = 1 - p
        info += a[j] ** 2 * p * q
    return info


def run_irt_analysis(data_dir: Path, output_dir: Path) -> dict:
    """教科別に2PL IRTを実行し、結果をJSONで出力する。"""
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("  [IRT] データ読込中...", flush=True)
    responses = pd.read_csv(data_dir / "item_responses.csv")
    n_students = responses["student_id"].nunique()
    print(f"  [IRT] {n_students}人, {responses['item_id'].nunique()}設問", flush=True)

    results_by_subject = {}

    for subj in SUBJECTS:
        subj_resp = responses[responses["subject"] == subj]
        if subj_resp.empty:
            continue

        print(f"  [IRT] {SUBJECT_JA.get(subj, subj)} 推定中...", end=" ", flush=True)

        # 応答マトリクス構築
        pivot = subj_resp.pivot_table(
            index="student_id", columns="item_id", values="correct", aggfunc="first"
        )
        matrix = pivot.values.astype(float)
        student_ids = list(pivot.index)
        item_ids = list(pivot.columns)

        # 2PL推定
        irt = estimate_2pl(matrix, max_iter=30)
        converged = irt["converged"]
        print(f"{'収束' if converged else '未収束'} ({irt['iterations']}回)", flush=True)

        # テスト情報関数
        theta_range = np.linspace(-3, 3, 61)
        test_info = compute_test_information(theta_range, irt["a"], irt["b"])

        # 結果格納
        item_params = []
        for j, item_id in enumerate(item_ids):
            item_params.append({
                "item_id": item_id,
                "difficulty_b": round(float(irt["b"][j]), 3),
                "discrimination_a": round(float(irt["a"][j]), 3),
            })

        student_abilities = []
        for i, sid in enumerate(student_ids):
            student_abilities.append({
                "student_id": sid,
                "theta": round(float(irt["theta"][i]), 3),
            })

        results_by_subject[subj] = {
            "converged": converged,
            "iterations": irt["iterations"],
            "log_likelihood": round(float(irt["log_likelihood"]), 1),
            "n_students": len(student_ids),
            "n_items": len(item_ids),
            "item_parameters": item_params,
            "student_abilities": student_abilities,
            "test_information": {
                "theta_range": [round(float(t), 2) for t in theta_range],
                "information": [round(float(i), 3) for i in test_info],
                "peak_theta": round(float(theta_range[np.argmax(test_info)]), 2),
                "peak_info": round(float(test_info.max()), 3),
            },
            "summary": {
                "mean_difficulty": round(float(np.mean(irt["b"])), 3),
                "std_difficulty": round(float(np.std(irt["b"])), 3),
                "mean_discrimination": round(float(np.mean(irt["a"])), 3),
                "mean_theta": round(float(np.mean(irt["theta"])), 3),
                "std_theta": round(float(np.std(irt["theta"])), 3),
            },
        }

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": "2PL",
        "by_subject": results_by_subject,
    }

    out_path = output_dir / "irt_analysis.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  [IRT] 出力: {out_path}", flush=True)

    return result


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    run_irt_analysis(
        Path("discovery/data/sample"),
        Path("discovery/analysis/output"),
    )
