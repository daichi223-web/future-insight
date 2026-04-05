"""分析パイプライン CLI ラッパー

プロジェクトルートから実行:
    python discovery/scripts/run_pipeline.py
    python discovery/scripts/run_pipeline.py --data-dir discovery/data/sample --output-dir discovery/analysis/output
"""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="教育データ発見エンジン - 分析パイプライン実行",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python discovery/scripts/run_pipeline.py
  python discovery/scripts/run_pipeline.py --data-dir path/to/data --output-dir path/to/output
  python discovery/scripts/run_pipeline.py --module item_analysis
        """,
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("discovery/data/sample"),
        help="入力データディレクトリ (default: discovery/data/sample)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("discovery/analysis/output"),
        help="出力ディレクトリ (default: discovery/analysis/output)",
    )
    parser.add_argument(
        "--module",
        type=str,
        choices=["item_analysis", "network", "association", "student_types", "mutual_info", "all"],
        default="all",
        help="実行するモジュール (default: all)",
    )
    args = parser.parse_args()

    # プロジェクトルートを sys.path に追加
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    data_dir = args.data_dir
    output_dir = args.output_dir

    # データディレクトリの存在確認
    if not data_dir.exists():
        print(f"エラー: データディレクトリが見つかりません: {data_dir}", file=sys.stderr)
        print("先にサンプルデータを生成してください:", file=sys.stderr)
        print("  python discovery/scripts/generate_sample.py", file=sys.stderr)
        sys.exit(1)

    if args.module == "all":
        from discovery.analysis.pipeline import run_all
        result = run_all(data_dir, output_dir)
        errors = result.get("summary", {}).get("errors", 0)
        sys.exit(1 if errors > 0 else 0)
    else:
        _run_single_module(args.module, data_dir, output_dir)


def _run_single_module(module_name: str, data_dir: Path, output_dir: Path) -> None:
    """単一モジュールを実行する。"""
    output_dir.mkdir(parents=True, exist_ok=True)

    module_map = {
        "item_analysis": ("discovery.analysis.item_analysis", "run_item_analysis"),
        "network": ("discovery.analysis.network", "run_network_analysis"),
        "association": ("discovery.analysis.association", "run_association_analysis"),
        "student_types": ("discovery.analysis.student_types", "run_student_types_analysis"),
        "mutual_info": ("discovery.analysis.mutual_info", "run_mutual_info_analysis"),
    }

    if module_name not in module_map:
        print(f"エラー: 不明なモジュール: {module_name}", file=sys.stderr)
        sys.exit(1)

    mod_path, func_name = module_map[module_name]

    try:
        import importlib
        mod = importlib.import_module(mod_path)
        func = getattr(mod, func_name)
    except (ImportError, AttributeError) as e:
        print(f"エラー: モジュール読込失敗: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"モジュール実行: {module_name}")
    print(f"データ: {data_dir}")
    print(f"出力先: {output_dir}")
    print("-" * 40)

    try:
        func(data_dir, output_dir)
        print(f"\n完了: {module_name}")
    except Exception as e:
        print(f"\nエラー: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
