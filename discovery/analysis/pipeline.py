"""分析パイプライン オーケストレーター

全5分析モジュールを順次実行し、メタデータを出力する。

Usage:
    python -m discovery.analysis.pipeline [--data-dir ...] [--output-dir ...]
"""

import argparse
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path


# ── モジュールインポート ────────────────────────────────

from discovery.analysis.item_analysis import run_item_analysis
from discovery.analysis.network import run_network_analysis
from discovery.analysis.association import run_association_analysis
from discovery.analysis.student_types import run_student_types_analysis
from discovery.analysis.mutual_info import run_mutual_info_analysis


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
]


# ── メインエントリ ──────────────────────────────────────

def run_all(data_dir: Path, output_dir: Path) -> dict:
    """全分析モジュールを順次実行する。

    各モジュールの実行結果とメタデータを metadata.json に記録する。
    """
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
    metadata = {
        "generated_at": end_time.isoformat(),
        "pipeline_version": "1.0.0",
        "data_dir": str(data_dir),
        "output_dir": str(output_dir),
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

    # 完了サマリ
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


# ── CLI ─────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="分析パイプライン オーケストレーター")
    parser.add_argument("--data-dir", type=Path, default=Path("discovery/data/sample"))
    parser.add_argument("--output-dir", type=Path, default=Path("discovery/analysis/output"))
    args = parser.parse_args()

    run_all(args.data_dir, args.output_dir)
