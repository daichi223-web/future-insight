"""実データ取り込みスクリプト

data/import/ に配置されたCSV/Excelファイルを読み込み、
分析パイプラインが処理できる標準形式に変換して data/real/ に出力する。

Usage:
    python scripts/import_data.py
    python scripts/import_data.py --import-dir data/import --output-dir data/real
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


# ── ファイル検出 ──────────────────────────────────────

def find_files(directory: Path, extensions: list[str]) -> list[Path]:
    """指定拡張子のファイルを再帰的に検出。"""
    files = []
    for ext in extensions:
        files.extend(directory.glob(f"**/*{ext}"))
    return sorted(files)


def read_tabular(path: Path) -> pd.DataFrame:
    """CSV/Excelファイルを自動判別して読み込む。文字コードも自動検出。"""
    suffix = path.suffix.lower()

    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(path)

    # CSV: 文字コード自動検出
    for encoding in ("utf-8", "utf-8-sig", "shift_jis", "cp932"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError(f"文字コードを検出できません: {path}")


# ── テスト結果の取り込み ─────────────────────────────────

def import_results(results_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """results/ フォルダからテスト結果を取り込む。

    Returns:
        item_responses: 設問単位正誤データ（形式A検出時）
        grades: 教科別合計点データ（形式B検出時）
    """
    files = find_files(results_dir, [".csv", ".xlsx", ".xls"])
    if not files:
        print("  [取込] results/ にファイルがありません", flush=True)
        return pd.DataFrame(), pd.DataFrame()

    all_item_responses = []
    all_grades = []

    for f in files:
        print(f"  [取込] 読込: {f.name}", flush=True)
        df = read_tabular(f)

        if df.empty:
            print(f"    空ファイル: {f.name}", flush=True)
            continue

        # ファイル名から教科・テスト情報を抽出
        fname = f.stem.lower()
        subject = _detect_subject(fname)
        test_id = _make_test_id(fname)

        # 形式判定: Q1, Q2... のような列名があれば形式A（設問単位）
        q_cols = [c for c in df.columns if re.match(r"^[Qq]\d+$", str(c))]

        if q_cols:
            # 形式A: 設問単位正誤
            id_col = _find_id_column(df)
            if id_col is None:
                print(f"    警告: 生徒番号列が見つかりません: {f.name}", flush=True)
                continue

            for _, row in df.iterrows():
                sid = str(row[id_col])
                for q_col in q_cols:
                    q_num = re.search(r"\d+", str(q_col)).group()
                    item_id = f"{subject}_q{int(q_num):02d}" if subject else f"q{int(q_num):02d}"
                    correct = int(row[q_col]) if pd.notna(row[q_col]) else 0
                    all_item_responses.append({
                        "student_id": f"S{sid}",
                        "subject": subject or "unknown",
                        "item_id": item_id,
                        "correct": min(max(correct, 0), 1),
                        "test_id": test_id,
                    })
            print(f"    形式A（設問単位）: {len(q_cols)}設問 x {len(df)}人", flush=True)

        else:
            # 形式B: 教科別合計点 or 形式C: 観点別
            id_col = _find_id_column(df)
            if id_col is None:
                print(f"    警告: 生徒番号列が見つかりません: {f.name}", flush=True)
                continue

            # 教科列を検出
            subj_map = {
                "数学": "math", "math": "math",
                "物理": "physics", "physics": "physics",
                "化学": "chemistry", "chemistry": "chemistry",
                "英語": "english", "english": "english",
                "国語": "japanese", "japanese": "japanese",
                "理科": "science", "社会": "social",
            }
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if col_lower in subj_map or col in subj_map:
                    subj_code = subj_map.get(col_lower, subj_map.get(col, ""))
                    if subj_code:
                        for _, row in df.iterrows():
                            val = row[col]
                            if pd.notna(val):
                                all_grades.append({
                                    "student_id": f"S{row[id_col]}",
                                    "subject": subj_code,
                                    "grade": float(val),
                                    "test_id": test_id,
                                })
            if all_grades:
                print(f"    形式B（合計点）: {len(df)}人", flush=True)

    item_responses = pd.DataFrame(all_item_responses) if all_item_responses else pd.DataFrame()
    grades = pd.DataFrame(all_grades) if all_grades else pd.DataFrame()

    return item_responses, grades


# ── 出欠データの取り込み ─────────────────────────────────

def import_attendance(att_dir: Path) -> pd.DataFrame:
    """attendance/ フォルダから出欠データを取り込む。"""
    files = find_files(att_dir, [".csv", ".xlsx", ".xls"])
    if not files:
        return pd.DataFrame()

    all_rows = []
    for f in files:
        print(f"  [取込] 出欠: {f.name}", flush=True)
        df = read_tabular(f)
        id_col = _find_id_column(df)
        if id_col is None:
            continue

        # 日付列 or 月次集計列を検出
        date_cols = [c for c in df.columns if re.search(r"\d{4}[-/]\d{2}", str(c)) or "月" in str(c)]
        if date_cols:
            # 月次集計の場合はそのまま保存
            for _, row in df.iterrows():
                all_rows.append({
                    "student_id": f"S{row[id_col]}",
                    "data": {str(c): row[c] for c in date_cols if pd.notna(row[c])},
                })
        else:
            # 日単位の場合
            for col in ["日付", "date", "Date"]:
                if col in df.columns:
                    for _, row in df.iterrows():
                        present = 1 if str(row.get("出欠", row.get("status", "出席"))) in ("出席", "1", 1) else 0
                        all_rows.append({
                            "student_id": f"S{row[id_col]}",
                            "date": str(row[col]),
                            "present": present,
                        })
                    break

    return pd.DataFrame(all_rows) if all_rows else pd.DataFrame()


# ── ヘルパー ─────────────────────────────────────────

def _find_id_column(df: pd.DataFrame) -> str | None:
    """生徒番号列を検出。"""
    candidates = ["生徒番号", "番号", "出席番号", "student_id", "id", "ID", "No", "no"]
    for c in candidates:
        if c in df.columns:
            return c
    # 最初の列が数値なら番号と推定
    first_col = df.columns[0]
    if df[first_col].dtype in (int, float, np.int64, np.float64):
        return first_col
    return None


def _detect_subject(filename: str) -> str:
    """ファイル名から教科を推定。"""
    mapping = {
        "math": "math", "suugaku": "math", "数学": "math",
        "physics": "physics", "butsuri": "physics", "物理": "physics",
        "chemistry": "chemistry", "kagaku": "chemistry", "化学": "chemistry",
        "english": "english", "eigo": "english", "英語": "english",
        "japanese": "japanese", "kokugo": "japanese", "国語": "japanese",
        "science": "science", "rika": "science", "理科": "science",
        "social": "social", "shakai": "social", "社会": "social",
    }
    for key, subj in mapping.items():
        if key in filename:
            return subj
    return ""


def _make_test_id(filename: str) -> str:
    """ファイル名からテストIDを生成。"""
    # _results サフィックスを除去
    clean = re.sub(r"_results?$", "", filename)
    return clean


# ── 出力 ─────────────────────────────────────────────

def save_imported(item_responses: pd.DataFrame, grades: pd.DataFrame,
                  attendance: pd.DataFrame, output_dir: Path) -> dict:
    """取り込み結果を標準形式で保存。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {}

    if not item_responses.empty:
        item_responses.to_csv(output_dir / "item_responses.csv", index=False)
        summary["item_responses"] = len(item_responses)
        print(f"  [出力] item_responses.csv: {len(item_responses)}行", flush=True)

    if not grades.empty:
        grades.to_csv(output_dir / "grades.csv", index=False)
        summary["grades"] = len(grades)
        print(f"  [出力] grades.csv: {len(grades)}行", flush=True)

    if not attendance.empty:
        attendance.to_csv(output_dir / "attendance.csv", index=False)
        summary["attendance"] = len(attendance)
        print(f"  [出力] attendance.csv: {len(attendance)}行", flush=True)

    # 生徒マスタ生成（検出された全生徒ID）
    all_ids = set()
    for df in [item_responses, grades, attendance]:
        if not df.empty and "student_id" in df.columns:
            all_ids.update(df["student_id"].unique())

    if all_ids:
        students = pd.DataFrame({"student_id": sorted(all_ids)})
        students["course"] = ""
        students["gender"] = ""
        students.to_csv(output_dir / "students.csv", index=False)
        summary["students"] = len(students)
        print(f"  [出力] students.csv: {len(students)}人", flush=True)

    # メタデータ
    meta = {
        "imported_at": datetime.now().isoformat(),
        "summary": summary,
    }
    with open(output_dir / "import_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return summary


# ── メイン ────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="実データ取り込み")
    parser.add_argument("--import-dir", default="discovery/data/import")
    parser.add_argument("--output-dir", default="discovery/data/real")
    args = parser.parse_args()

    import_dir = Path(args.import_dir)
    output_dir = Path(args.output_dir)

    print("=" * 50)
    print("データ取り込み")
    print(f"入力: {import_dir}")
    print(f"出力: {output_dir}")
    print("=" * 50)

    # テスト結果
    results_dir = import_dir / "results"
    if results_dir.exists():
        print("\n[テスト結果]", flush=True)
        item_responses, grades = import_results(results_dir)
    else:
        print("\n[テスト結果] results/ フォルダがありません", flush=True)
        item_responses, grades = pd.DataFrame(), pd.DataFrame()

    # 出欠
    att_dir = import_dir / "attendance"
    if att_dir.exists():
        print("\n[出欠データ]", flush=True)
        attendance = import_attendance(att_dir)
    else:
        print("\n[出欠データ] attendance/ フォルダがありません", flush=True)
        attendance = pd.DataFrame()

    # 保存
    print("\n[出力]", flush=True)
    summary = save_imported(item_responses, grades, attendance, output_dir)

    if not summary:
        print("\n取り込めるデータがありませんでした。")
        print("data/import/ にファイルを配置してから再実行してください。")
        print("詳細は data/import/README.md を参照。")
    else:
        print(f"\n完了: {output_dir}/")
        print(f"分析実行: python scripts/run_pipeline.py --data-dir {output_dir}")


if __name__ == "__main__":
    main()
