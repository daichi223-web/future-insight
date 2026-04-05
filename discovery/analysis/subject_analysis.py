"""教科別深層分析モジュール

教科ごとのスキル定着率・DOKプロファイル・観点別分析・
誤概念頻度・ブルーム梯子を計算する。

Usage:
    python -m discovery.analysis.subject_analysis [--data-dir ...] [--output-dir ...]
"""

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


# ── 定数 ────────────────────────────────────────────────

SUBJECTS = ["math", "physics", "chemistry", "english", "japanese"]

BLOOMS_ORDER = ["remember", "understand", "apply", "analyze", "evaluate", "create"]

DOK_LEVELS = [1, 2, 3, 4]

# DOK ceiling 検出しきい値: 前のレベルからの低下率がこの値以上なら ceiling
DOK_DROP_THRESHOLD = 0.15


# ── Q-matrix ロード ───────────────────────────────────────

def load_q_matrix(schema_dir: Path) -> dict:
    """enhanced_q_matrix.json をロードし items dict を返す。"""
    path = schema_dir / "enhanced_q_matrix.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["items"]


def load_curriculum(schema_dir: Path) -> dict:
    """curriculum.json をロードする。"""
    path = schema_dir / "curriculum.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ── ヘルパー ─────────────────────────────────────────────

def _build_skill_to_unit_map(curriculum: dict) -> dict[str, dict]:
    """skill -> {"unit_id": ..., "unit_name_ja": ..., "course": ...} のマップ。"""
    mapping: dict[str, dict] = {}
    for subj_key, subj_data in curriculum.get("subjects", {}).items():
        for course in subj_data.get("courses", []):
            for unit in course.get("units", []):
                for skill in unit.get("skills", []):
                    mapping[skill] = {
                        "unit_id": unit["id"],
                        "unit_name_ja": unit["name_ja"],
                        "course": course["id"],
                        "course_name_ja": course["name_ja"],
                    }
    return mapping


def _items_for_subject(q_matrix: dict, subject: str) -> dict:
    """指定教科の項目だけを抽出する。"""
    return {k: v for k, v in q_matrix.items() if v.get("subject") == subject}


# ── スキル定着率 ─────────────────────────────────────────

def compute_skill_mastery(
    responses_df: pd.DataFrame,
    q_matrix: dict,
    mastery_threshold: float = 0.60,
) -> dict[str, list[dict]]:
    """教科ごとにスキル別定着率を計算する。

    定着 = そのスキルに紐づく項目群の正答率が mastery_threshold 以上の生徒の割合。
    """
    curriculum_path = None  # curriculum は別途渡される場合もあるが、ここでは q_matrix のみ使用
    result: dict[str, list[dict]] = {}

    for subj in SUBJECTS:
        subj_items = _items_for_subject(q_matrix, subj)
        subj_responses = responses_df[responses_df["subject"] == subj]

        if subj_responses.empty:
            result[subj] = []
            continue

        # skill -> [item_ids]
        skill_items: dict[str, list[str]] = defaultdict(list)
        for item_id, meta in subj_items.items():
            for skill in meta.get("skills", []):
                skill_items[skill].append(item_id)

        skill_rows = []
        for skill, item_ids in sorted(skill_items.items()):
            items_df = subj_responses[subj_responses["item_id"].isin(item_ids)]
            if items_df.empty:
                continue

            # 生徒ごとの当該スキル正答率
            student_rates = items_df.groupby("student_id")["correct"].mean()
            mastery_rate = float((student_rates >= mastery_threshold).mean())
            n_items = len(item_ids)

            # unit 情報 (q_matrix から推定)
            unit_name = ""
            course_name = ""
            for iid in item_ids:
                meta = subj_items.get(iid, {})
                if meta.get("unit"):
                    unit_name = meta["unit"]
                    course_name = meta.get("course", "")
                    break

            skill_rows.append({
                "skill": skill,
                "unit": unit_name,
                "course": course_name,
                "mastery_rate": round(mastery_rate, 4),
                "n_items": n_items,
                "n_students": int(student_rates.shape[0]),
            })

        result[subj] = skill_rows

    return result


# ── DOK パフォーマンスプロファイル ──────────────────────────

def compute_dok_profile(
    responses_df: pd.DataFrame,
    q_matrix: dict,
) -> dict[str, dict]:
    """教科ごとに DOK レベル別平均正答率と DOK ceiling を計算する。"""
    result: dict[str, dict] = {}

    for subj in SUBJECTS:
        subj_items = _items_for_subject(q_matrix, subj)
        subj_responses = responses_df[responses_df["subject"] == subj]

        # DOK レベル -> item_ids
        dok_items: dict[int, list[str]] = defaultdict(list)
        for item_id, meta in subj_items.items():
            dok = meta.get("dok_level")
            if dok is not None:
                dok_items[int(dok)].append(item_id)

        profile: dict[str, dict] = {}
        scores_by_dok: dict[int, float] = {}

        for dok in DOK_LEVELS:
            item_ids = dok_items.get(dok, [])
            if not item_ids:
                profile[str(dok)] = {"mean_score": None, "n_items": 0}
                continue
            items_df = subj_responses[subj_responses["item_id"].isin(item_ids)]
            if items_df.empty:
                profile[str(dok)] = {"mean_score": None, "n_items": len(item_ids)}
                continue
            mean_score = float(items_df["correct"].mean())
            profile[str(dok)] = {
                "mean_score": round(mean_score, 4),
                "n_items": len(item_ids),
            }
            scores_by_dok[dok] = mean_score

        # DOK ceiling の検出: 隣接レベル間で最大の落ち込みがあるレベル
        ceiling = None
        max_drop = 0.0
        sorted_doks = sorted(scores_by_dok.keys())
        for i in range(1, len(sorted_doks)):
            prev_dok = sorted_doks[i - 1]
            curr_dok = sorted_doks[i]
            drop = scores_by_dok[prev_dok] - scores_by_dok[curr_dok]
            if drop > max_drop and drop >= DOK_DROP_THRESHOLD:
                max_drop = drop
                ceiling = curr_dok

        result[subj] = {
            "profile": profile,
            "ceiling": ceiling,
        }

    return result


# ── 観点別パフォーマンス ────────────────────────────────────

def compute_kanten_profile(
    responses_df: pd.DataFrame,
    q_matrix: dict,
) -> dict[str, dict]:
    """教科ごとに観点別（知識・技能 vs 思考・判断・表現）の平均正答率とギャップを計算。"""
    result: dict[str, dict] = {}

    for subj in SUBJECTS:
        subj_items = _items_for_subject(q_matrix, subj)
        subj_responses = responses_df[responses_df["subject"] == subj]

        kanten_items: dict[str, list[str]] = defaultdict(list)
        for item_id, meta in subj_items.items():
            kanten = meta.get("kanten")
            if kanten:
                kanten_items[kanten].append(item_id)

        kanten_scores: dict[str, dict] = {}
        for kanten, item_ids in kanten_items.items():
            items_df = subj_responses[subj_responses["item_id"].isin(item_ids)]
            if items_df.empty:
                kanten_scores[kanten] = {"mean_score": None, "n_items": len(item_ids)}
                continue
            mean_score = float(items_df["correct"].mean())
            kanten_scores[kanten] = {
                "mean_score": round(mean_score, 4),
                "n_items": len(item_ids),
            }

        # ギャップ: 知識・技能 - 思考・判断・表現
        score_chishiki = (kanten_scores.get("知識・技能", {}).get("mean_score") or 0)
        score_shiko = (kanten_scores.get("思考・判断・表現", {}).get("mean_score") or 0)
        gap = round(score_chishiki - score_shiko, 4) if score_chishiki and score_shiko else None

        result[subj] = {
            "profile": kanten_scores,
            "gap": gap,
        }

    return result


# ── 誤概念の有病率 ──────────────────────────────────────

def compute_misconception_prevalence(
    responses_df: pd.DataFrame,
    q_matrix: dict,
) -> dict[str, list[dict]]:
    """教科ごとに誤概念の頻度を計算する。

    Q-matrix に misconceptions が定義された項目について、
    正答率が低い（= 誤答が多い）ほど誤概念の prevalence が高いと推定する。

    prevalence = 1 - 正答率 （当該項目の全受験者について）
    ※ 理想的にはディストラクタ別の選択率を使うが、正誤データのみの場合は
      不正答率で代用する。
    """
    result: dict[str, list[dict]] = {}

    for subj in SUBJECTS:
        subj_items = _items_for_subject(q_matrix, subj)
        subj_responses = responses_df[responses_df["subject"] == subj]
        misconceptions_list: list[dict] = []

        for item_id, meta in subj_items.items():
            miscons = meta.get("misconceptions", {})
            if not miscons:
                continue

            items_df = subj_responses[subj_responses["item_id"] == item_id]
            if items_df.empty:
                continue

            error_rate = float(1.0 - items_df["correct"].mean())

            for distractor, misconception_name in miscons.items():
                # 各ディストラクタの prevalence を誤答率の按分で推定
                # ディストラクタ数で均等按分（正誤データのみの制約）
                n_distractors = len(miscons)
                estimated_prevalence = round(error_rate / n_distractors, 4)

                misconceptions_list.append({
                    "name": misconception_name,
                    "prevalence": estimated_prevalence,
                    "item_id": item_id,
                    "distractor": distractor,
                })

        # prevalence 降順でソート
        misconceptions_list.sort(key=lambda x: x["prevalence"], reverse=True)
        result[subj] = misconceptions_list

    return result


# ── ブルームの梯子 ──────────────────────────────────────

def compute_blooms_ladder(
    responses_df: pd.DataFrame,
    q_matrix: dict,
) -> dict[str, dict]:
    """教科ごとに Bloom's taxonomy レベル別の平均正答率と drop-off ポイントを計算。"""
    result: dict[str, dict] = {}

    for subj in SUBJECTS:
        subj_items = _items_for_subject(q_matrix, subj)
        subj_responses = responses_df[responses_df["subject"] == subj]

        blooms_items: dict[str, list[str]] = defaultdict(list)
        for item_id, meta in subj_items.items():
            level = meta.get("blooms_cognitive")
            if level:
                blooms_items[level].append(item_id)

        ladder: dict[str, float | None] = {}
        scores_ordered: list[tuple[str, float]] = []

        for level in BLOOMS_ORDER:
            item_ids = blooms_items.get(level, [])
            if not item_ids:
                ladder[level] = None
                continue
            items_df = subj_responses[subj_responses["item_id"].isin(item_ids)]
            if items_df.empty:
                ladder[level] = None
                continue
            mean_score = float(items_df["correct"].mean())
            ladder[level] = round(mean_score, 4)
            scores_ordered.append((level, mean_score))

        # Drop-off: 最大落ち込みのレベル
        dropoff = None
        max_drop = 0.0
        for i in range(1, len(scores_ordered)):
            prev_level, prev_score = scores_ordered[i - 1]
            curr_level, curr_score = scores_ordered[i]
            drop = prev_score - curr_score
            if drop > max_drop and drop >= DOK_DROP_THRESHOLD:
                max_drop = drop
                dropoff = curr_level

        result[subj] = {
            "ladder": ladder,
            "dropoff": dropoff,
        }

    return result


# ── メインエントリ ──────────────────────────────────────

def run_subject_analysis(data_dir: Path, output_dir: Path) -> dict:
    """教科別深層分析を実行し、subject_analysis.json を出力する。"""
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # スキーマディレクトリの特定
    schema_dir = data_dir.parent / "schema" if (data_dir.parent / "schema").exists() else data_dir / "schema"
    if not schema_dir.exists():
        # data_dir が sample/ の場合は data/schema を探す
        schema_dir = data_dir.parent / "schema"

    print("  [教科別分析] Q-matrix 読込中...", flush=True)
    q_matrix = load_q_matrix(schema_dir)
    curriculum = load_curriculum(schema_dir)
    skill_unit_map = _build_skill_to_unit_map(curriculum)

    print("  [教科別分析] 回答データ読込中...", flush=True)
    responses_path = data_dir / "item_responses.csv"
    if not responses_path.exists():
        raise FileNotFoundError(f"item_responses.csv が見つかりません: {responses_path}")
    responses_df = pd.read_csv(responses_path)
    n_responses = len(responses_df)
    n_students = responses_df["student_id"].nunique()
    print(f"  [教科別分析] {n_responses:,}件 ({n_students}名) の回答データを読込", flush=True)

    # 各分析の実行
    print("  [教科別分析] スキル定着率計算中...", flush=True)
    skill_mastery = compute_skill_mastery(responses_df, q_matrix)

    print("  [教科別分析] DOKプロファイル計算中...", flush=True)
    dok_profile = compute_dok_profile(responses_df, q_matrix)

    print("  [教科別分析] 観点別プロファイル計算中...", flush=True)
    kanten_profile = compute_kanten_profile(responses_df, q_matrix)

    print("  [教科別分析] 誤概念有病率計算中...", flush=True)
    misconceptions = compute_misconception_prevalence(responses_df, q_matrix)

    print("  [教科別分析] ブルーム梯子計算中...", flush=True)
    blooms = compute_blooms_ladder(responses_df, q_matrix)

    # スキル定着率にカリキュラム情報を付与
    for subj in SUBJECTS:
        for entry in skill_mastery.get(subj, []):
            skill_name = entry["skill"]
            if skill_name in skill_unit_map:
                entry["unit_name_ja"] = skill_unit_map[skill_name]["unit_name_ja"]
                entry["course_name_ja"] = skill_unit_map[skill_name]["course_name_ja"]

    # 出力構造の組み立て
    by_subject: dict[str, dict[str, Any]] = {}
    for subj in SUBJECTS:
        subj_result: dict[str, Any] = {
            "skill_mastery": skill_mastery.get(subj, []),
            "dok_profile": dok_profile.get(subj, {}).get("profile", {}),
            "dok_ceiling": dok_profile.get(subj, {}).get("ceiling"),
            "kanten_profile": kanten_profile.get(subj, {}).get("profile", {}),
            "kanten_gap": kanten_profile.get(subj, {}).get("gap"),
            "misconceptions": misconceptions.get(subj, []),
            "blooms_ladder": blooms.get(subj, {}).get("ladder", {}),
            "blooms_dropoff": blooms.get(subj, {}).get("dropoff"),
        }
        by_subject[subj] = subj_result

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_students": n_students,
        "n_responses": n_responses,
        "by_subject": by_subject,
    }

    output_path = output_dir / "subject_analysis.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  [教科別分析] 完了: {len(SUBJECTS)}教科の分析を出力", flush=True)
    print(f"  [教科別分析] 出力: {output_path}", flush=True)

    return result


# ── CLI ─────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="教科別深層分析")
    parser.add_argument("--data-dir", type=Path, default=Path("discovery/data/sample"))
    parser.add_argument("--output-dir", type=Path, default=Path("discovery/analysis/output"))
    args = parser.parse_args()

    run_subject_analysis(args.data_dir, args.output_dir)
