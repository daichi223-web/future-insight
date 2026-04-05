"""生徒タイプ分類モジュール（GMM による潜在クラス近似）

成績・出欠データから生徒特徴量を構築し、
混合ガウスモデル（GMM）でクラスタリングを行う。

Usage:
    python -m discovery.analysis.student_types [--data-dir ...] [--output-dir ...]
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler


# ── 定数 ────────────────────────────────────────────────

SUBJECTS = ["math", "physics", "chemistry", "english", "japanese"]

SUBJECT_JA = {
    "math": "数学", "physics": "物理", "chemistry": "化学",
    "english": "英語", "japanese": "国語",
}

# プロファイルパターンに基づく自動ラベリング
CLASS_LABEL_RULES = [
    {
        "check": lambda p: all(p.get(s, 0) >= 65 for s in SUBJECTS),
        "label": "バランス型高達成",
        "desc": "全教科で安定した高成績を維持。出席率も高い。",
    },
    {
        "check": lambda p: (
            p.get("math", 0) >= 60 and p.get("physics", 0) >= 55
            and p.get("english", 0) < 50
        ),
        "label": "STEM傾斜型",
        "desc": "理系科目（数学・物理）が強く、文系科目に弱みがある。",
    },
    {
        "check": lambda p: (
            p.get("english", 0) >= 60 and p.get("japanese", 0) >= 60
            and p.get("math", 0) < 45
        ),
        "label": "文系傾斜型",
        "desc": "英語・国語が強く、数学・理科に弱みがある。",
    },
    {
        "check": lambda p: (
            all(p.get(s, 0) < 45 for s in SUBJECTS)
            and p.get("attendance", 1.0) < 0.80
        ),
        "label": "離脱型",
        "desc": "全教科低成績かつ出席率が低い。早期介入が必要。",
    },
    {
        "check": lambda p: (
            all(p.get(s, 0) < 55 for s in SUBJECTS)
            and p.get("attendance", 0) >= 0.85
        ),
        "label": "苦戦努力型",
        "desc": "出席率は高いが成績に反映されていない。学習方法の改善が鍵。",
    },
]


# ── 特徴量準備 ─────────────────────────────────────────

def prepare_features(grades_df: pd.DataFrame,
                     attendance_df: pd.DataFrame) -> pd.DataFrame:
    """成績・出欠データから生徒ごとの特徴量を構築する。

    特徴量:
    - 教科ごとの平均成績 (math_mean, physics_mean, ...)
    - 全体出席率 (attendance_rate)

    Returns:
        student_id をインデックスとした特徴量 DataFrame。
    """
    # 教科ごとの平均成績
    if grades_df.empty:
        raise ValueError("grades_df が空です")

    grade_means = (
        grades_df
        .groupby(["student_id", "subject"])["grade"]
        .mean()
        .unstack(fill_value=0.0)
    )
    # 列名を統一
    grade_means.columns = [f"{col}_mean" for col in grade_means.columns]

    # 出席率
    if not attendance_df.empty:
        att_rate = (
            attendance_df
            .groupby("student_id")["present"]
            .mean()
            .rename("attendance_rate")
        )
    else:
        # 出欠データがない場合はデフォルト
        att_rate = pd.Series(
            1.0, index=grade_means.index, name="attendance_rate"
        )

    features = grade_means.join(att_rate, how="left").fillna(0.0)
    return features


# ── GMM フィッティング ─────────────────────────────────

def fit_gmm(features: pd.DataFrame,
            max_k: int = 8) -> tuple:
    """GMM を k=2..max_k で適合し、BIC 最小のモデルを選択する。

    Returns:
        (best_model, labels, bic_values)
    """
    if features.empty or len(features) < max_k:
        raise ValueError(f"データ不足: {len(features)}行 (最低 {max_k} 行必要)")

    # 標準化
    scaler = StandardScaler()
    X = scaler.fit_transform(features.values)

    bic_values = {}
    best_bic = np.inf
    best_model = None
    best_labels = None

    for k in range(2, max_k + 1):
        try:
            gmm = GaussianMixture(
                n_components=k,
                covariance_type="full",
                n_init=5,
                max_iter=300,
                random_state=42,
            )
            gmm.fit(X)
            bic = gmm.bic(X)
            bic_values[str(k)] = round(float(bic), 2)

            if bic < best_bic:
                best_bic = bic
                best_model = gmm
                best_labels = gmm.predict(X)
        except Exception as e:
            print(f"  [生徒タイプ] 警告: k={k} で適合失敗: {e}", flush=True)
            bic_values[str(k)] = None

    if best_model is None:
        raise RuntimeError("GMM の適合に失敗しました")

    return best_model, best_labels, bic_values


# ── クラスプロファイリング ─────────────────────────────

def profile_classes(features_df: pd.DataFrame,
                    labels: np.ndarray) -> list:
    """各クラスのプロファイルを計算し、日本語ラベルを付与する。"""
    features_with_labels = features_df.copy()
    features_with_labels["class_id"] = labels

    classes = []
    for class_id in sorted(features_with_labels["class_id"].unique()):
        class_data = features_with_labels[features_with_labels["class_id"] == class_id]
        size = len(class_data)
        proportion = size / len(features_with_labels)

        # プロファイル: 各特徴量の平均
        profile = {}
        for col in features_df.columns:
            mean_val = float(class_data[col].mean())
            # 列名の _mean サフィックスを除去
            clean_name = col.replace("_mean", "").replace("_rate", "")
            profile[clean_name] = round(mean_val, 2)

        # 出席率は0-1スケールなのでそのまま保持
        attendance = profile.pop("attendance", None)
        if attendance is not None:
            profile["attendance"] = attendance

        # 日本語ラベルの自動付与
        label_ja = _assign_label(profile)

        classes.append({
            "class_id": int(class_id),
            "label": label_ja["label"],
            "size": size,
            "proportion": round(proportion, 4),
            "profile": {k: round(v, 2) for k, v in profile.items()},
            "description": label_ja["desc"],
        })

    return classes


def _assign_label(profile: dict) -> dict:
    """プロファイルに基づいて日本語ラベルを自動付与する。"""
    for rule in CLASS_LABEL_RULES:
        try:
            if rule["check"](profile):
                return {"label": rule["label"], "desc": rule["desc"]}
        except (KeyError, TypeError):
            continue

    # デフォルト
    # 最高教科と最低教科を特定
    subj_scores = {s: profile.get(s, 0) for s in SUBJECTS}
    if subj_scores:
        best = max(subj_scores, key=subj_scores.get)
        worst = min(subj_scores, key=subj_scores.get)
        best_ja = SUBJECT_JA.get(best, best)
        worst_ja = SUBJECT_JA.get(worst, worst)
        mean_score = np.mean(list(subj_scores.values()))

        if mean_score >= 60:
            return {
                "label": f"{best_ja}優位型",
                "desc": f"{best_ja}が最も高く、全体的に平均以上。",
            }
        else:
            return {
                "label": f"混合型（{best_ja}寄り）",
                "desc": f"{best_ja}が相対的に高いが、{worst_ja}に弱みがある。",
            }

    return {"label": "未分類", "desc": "プロファイルが不明確。"}


# ── メインエントリ ──────────────────────────────────────

def run_student_types_analysis(data_dir: Path, output_dir: Path) -> dict:
    """生徒タイプ分析パイプラインを実行し、student_profiles.json を出力する。"""
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # データ読込
    print("  [生徒タイプ] データ読込中...", flush=True)
    grades_path = data_dir / "grades.csv"
    attendance_path = data_dir / "attendance.csv"

    if not grades_path.exists():
        raise FileNotFoundError(f"grades.csv が見つかりません: {grades_path}")

    grades_df = pd.read_csv(grades_path)
    attendance_df = (
        pd.read_csv(attendance_path) if attendance_path.exists()
        else pd.DataFrame()
    )

    print(f"  [生徒タイプ] 成績: {len(grades_df):,}件, 出欠: {len(attendance_df):,}件", flush=True)

    # 特徴量構築
    print("  [生徒タイプ] 特徴量構築中...", flush=True)
    features = prepare_features(grades_df, attendance_df)
    print(f"  [生徒タイプ] {len(features)}人 x {len(features.columns)}特徴量", flush=True)

    # GMM フィッティング
    print("  [生徒タイプ] GMM フィッティング中 (k=2..8)...", flush=True)
    model, labels, bic_values = fit_gmm(features, max_k=8)
    optimal_k = model.n_components
    print(f"  [生徒タイプ] 最適クラス数: {optimal_k} (BIC基準)", flush=True)

    # クラスプロファイリング
    print("  [生徒タイプ] クラスプロファイリング中...", flush=True)
    classes = profile_classes(features, labels)

    # 生徒割り当て
    probabilities = model.predict_proba(
        StandardScaler().fit_transform(features.values)
    )
    student_assignments = []
    for i, student_id in enumerate(features.index):
        student_assignments.append({
            "student_id": student_id,
            "class_id": int(labels[i]),
            "probabilities": [round(float(p), 4) for p in probabilities[i]],
        })

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "optimal_k": optimal_k,
        "bic_values": bic_values,
        "classes": classes,
        "student_assignments": student_assignments,
    }

    output_path = output_dir / "student_profiles.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  [生徒タイプ] 完了: {optimal_k}クラスを検出", flush=True)
    for cls in classes:
        print(f"    クラス{cls['class_id']}: {cls['label']} (n={cls['size']}, {cls['proportion']:.1%})", flush=True)
    print(f"  [生徒タイプ] 出力: {output_path}", flush=True)

    return result


# ── CLI ─────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生徒タイプ分類 (GMM)")
    parser.add_argument("--data-dir", type=Path, default=Path("discovery/data/sample"))
    parser.add_argument("--output-dir", type=Path, default=Path("discovery/analysis/output"))
    args = parser.parse_args()

    run_student_types_analysis(args.data_dir, args.output_dir)
