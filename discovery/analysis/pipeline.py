"""分析パイプライン オーケストレーター

全8分析モジュールを順次実行し、メタデータを出力する。

Usage:
    python -m discovery.analysis.pipeline [--data-dir ...] [--output-dir ...]
"""

import argparse
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


# ── モジュールインポート ────────────────────────────────

from discovery.analysis.item_analysis import run_item_analysis
from discovery.analysis.network import run_network_analysis
from discovery.analysis.association import run_association_analysis
from discovery.analysis.student_types import run_student_types_analysis
from discovery.analysis.mutual_info import run_mutual_info_analysis
from discovery.analysis.subject_analysis import run_subject_analysis
from discovery.analysis.cross_subject import run_cross_subject_analysis
from discovery.analysis.student_profiler import run_student_profiler
from discovery.analysis.irt_analysis import run_irt_analysis


# ── データバリデーション ─────────────────────────────────

def validate_data(data_dir: Path) -> list:
    """入力データの整合性を検証。問題があればエラーメッセージのリストを返す。"""
    errors = []

    required_files = [
        "students.csv", "item_responses.csv", "grades.csv", "attendance.csv",
    ]
    for f in required_files:
        if not (data_dir / f).exists():
            errors.append(f"必須ファイル不足: {f}")

    if errors:
        return errors

    students = pd.read_csv(data_dir / "students.csv")
    responses = pd.read_csv(data_dir / "item_responses.csv")
    grades = pd.read_csv(data_dir / "grades.csv")

    n_students = len(students)
    n_items = responses["item_id"].nunique()
    n_subjects = responses["subject"].nunique()

    if n_students == 0:
        errors.append("生徒数が0です")
    if n_items == 0:
        errors.append("設問数が0です")

    # 生徒IDの整合性チェック
    stu_ids = set(students["student_id"])
    resp_ids = set(responses["student_id"])
    if not resp_ids.issubset(stu_ids):
        missing = resp_ids - stu_ids
        errors.append(f"item_responses.csvに未定義の生徒ID: {len(missing)}件")

    grade_ids = set(grades["student_id"])
    if not grade_ids.issubset(stu_ids):
        missing = grade_ids - stu_ids
        errors.append(f"grades.csvに未定義の生徒ID: {len(missing)}件")

    # Q-matrixとの整合チェック
    schema_dir = data_dir.parent / "schema"
    for qm_name in ("enhanced_q_matrix.json", "q_matrix.json"):
        qm_path = schema_dir / qm_name
        if qm_path.exists():
            with open(qm_path, encoding="utf-8") as f:
                qm = json.load(f)
            qm_items = set(qm.get("items", {}).keys())
            data_items = set(responses["item_id"])
            if qm_items and not data_items.issubset(qm_items):
                extra = data_items - qm_items
                if len(extra) > 5:
                    errors.append(f"Q-matrix ({qm_name})に未定義の設問ID: {len(extra)}件")
            break

    if not errors:
        print(f"  [検証] OK: {n_students}人, {n_items}設問, {n_subjects}教科", flush=True)

    return errors


# ── パイプライン定義 ───────────────────────────────────

PIPELINE_STEPS = [
    {
        "name": "item_analysis",
        "label": "項目分析 (CTT)",
        "func": run_item_analysis,
        "output_file": "item_analysis.json",
    },
    {
        "name": "network",
        "label": "偏相関ネットワーク分析",
        "func": run_network_analysis,
        "output_file": "network_graph.json",
    },
    {
        "name": "association",
        "label": "相関ルールマイニング",
        "func": run_association_analysis,
        "output_file": "patterns.json",
    },
    {
        "name": "student_types",
        "label": "生徒タイプ分類 (GMM)",
        "func": run_student_types_analysis,
        "output_file": "student_profiles.json",
    },
    {
        "name": "mutual_info",
        "label": "相互情報量分析",
        "func": run_mutual_info_analysis,
        "output_file": "mutual_info.json",
    },
    {
        "name": "subject_analysis",
        "label": "教科別深掘り分析",
        "func": run_subject_analysis,
        "output_file": "subject_analysis.json",
    },
    {
        "name": "cross_subject",
        "label": "教科横断分析",
        "func": run_cross_subject_analysis,
        "output_file": "cross_subject.json",
    },
    {
        "name": "student_profiler",
        "label": "多次元生徒プロファイル",
        "func": run_student_profiler,
        "output_file": "student_profiles_enhanced.json",
    },
    {
        "name": "irt_analysis",
        "label": "IRT分析 (2PL)",
        "func": run_irt_analysis,
        "output_file": "irt_analysis.json",
    },
]


# ── メインエントリ ──────────────────────────────────────

def run_all(data_dir: Path, output_dir: Path) -> dict:
    """全分析モジュールを順次実行する。"""
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    start_time = datetime.now(timezone.utc)
    print("=" * 60)
    print("教育データ発見エンジン - 分析パイプライン")
    print(f"開始: {start_time.isoformat()}")
    print(f"データ: {data_dir}")
    print(f"出力先: {output_dir}")
    print("=" * 60)

    # データバリデーション
    print("\n[0] データ検証", flush=True)
    print("-" * 40, flush=True)
    validation_errors = validate_data(data_dir)
    if validation_errors:
        print("  [検証] エラー:", flush=True)
        for err in validation_errors:
            print(f"    - {err}", flush=True)
        print("  パイプラインを中断します。", flush=True)
        return {"status": "validation_failed", "errors": validation_errors}

    results = []
    success_count = 0
    error_count = 0

    for i, step in enumerate(PIPELINE_STEPS, 1):
        step_name = step["name"]
        step_label = step["label"]

        print(f"\n[{i}/{len(PIPELINE_STEPS)}] {step_label}", flush=True)
        print("-" * 40, flush=True)

        step_start = datetime.now(timezone.utc)
        step_result = {
            "name": step_name,
            "label": step_label,
            "output_file": step["output_file"],
            "status": "pending",
        }

        try:
            step["func"](data_dir, output_dir)
            step_result["status"] = "success"
            success_count += 1
        except Exception as e:
            step_result["status"] = "error"
            step_result["error"] = str(e)
            step_result["traceback"] = traceback.format_exc()
            error_count += 1
            print(f"  エラー: {e}", flush=True)

        step_end = datetime.now(timezone.utc)
        step_result["duration_seconds"] = round(
            (step_end - step_start).total_seconds(), 2
        )
        results.append(step_result)

    end_time = datetime.now(timezone.utc)
    total_duration = round((end_time - start_time).total_seconds(), 2)

    # メタデータ出力
    n_students = 0
    n_items = 0
    try:
        students = pd.read_csv(data_dir / "students.csv")
        responses = pd.read_csv(data_dir / "item_responses.csv")
        n_students = len(students)
        n_items = responses["item_id"].nunique()
    except Exception:
        pass

    metadata = {
        "analysis_timestamp": end_time.isoformat(),
        "pipeline_version": "2.0.0",
        "data_dir": str(data_dir),
        "output_dir": str(output_dir),
        "n_students": n_students,
        "n_items": n_items,
        "duration_seconds": total_duration,
        "summary": {
            "total_steps": len(PIPELINE_STEPS),
            "success": success_count,
            "errors": error_count,
        },
        "steps": results,
    }

    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("パイプライン完了")
    print(f"  実行時間: {total_duration:.1f}秒")
    print(f"  成功: {success_count}/{len(PIPELINE_STEPS)}")
    if error_count > 0:
        print(f"  エラー: {error_count}/{len(PIPELINE_STEPS)}")
        for r in results:
            if r["status"] == "error":
                print(f"    - {r['label']}: {r.get('error', '不明')}")
    print(f"  メタデータ: {metadata_path}")
    print("=" * 60)

    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="分析パイプライン")
    parser.add_argument("--data-dir", type=Path, default=Path("discovery/data/sample"))
    parser.add_argument("--output-dir", type=Path, default=Path("discovery/analysis/output"))
    args = parser.parse_args()

    run_all(args.data_dir, args.output_dir)
