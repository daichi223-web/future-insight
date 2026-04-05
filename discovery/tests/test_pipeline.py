"""分析パイプラインのテスト

サンプルデータ生成 → 全モジュール実行 → 出力検証 の統合テスト。
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

DISCOVERY = Path(__file__).parent.parent
SAMPLE_DIR = DISCOVERY / "data" / "sample"
OUTPUT_DIR = DISCOVERY / "analysis" / "output"
SCHEMA_DIR = DISCOVERY / "data" / "schema"


# ── サンプルデータ検証 ────────────────────────────────

class TestSampleData:
    """生成済みサンプルデータの検証。"""

    def test_students_exist(self):
        df = pd.read_csv(SAMPLE_DIR / "students.csv")
        assert len(df) > 0, "生徒データが空"
        assert "student_id" in df.columns

    def test_students_count(self):
        df = pd.read_csv(SAMPLE_DIR / "students.csv")
        assert 300 <= len(df) <= 500, f"生徒数が想定外: {len(df)}"

    def test_item_responses_shape(self):
        df = pd.read_csv(SAMPLE_DIR / "item_responses.csv")
        students = pd.read_csv(SAMPLE_DIR / "students.csv")
        n = len(students)
        assert len(df) == n * 150, f"応答数が想定外: {len(df)} (期待: {n*150})"

    def test_item_responses_binary(self):
        df = pd.read_csv(SAMPLE_DIR / "item_responses.csv")
        assert set(df["correct"].unique()).issubset({0, 1}), "正誤が0/1でない"

    def test_five_subjects(self):
        df = pd.read_csv(SAMPLE_DIR / "item_responses.csv")
        subjects = set(df["subject"].unique())
        expected = {"math", "physics", "chemistry", "english", "japanese"}
        assert subjects == expected, f"教科が不正: {subjects}"

    def test_grades_exist(self):
        df = pd.read_csv(SAMPLE_DIR / "grades.csv")
        assert len(df) > 0
        assert all(c in df.columns for c in ["student_id", "subject", "term", "grade"])

    def test_attendance_exist(self):
        df = pd.read_csv(SAMPLE_DIR / "attendance.csv")
        assert len(df) > 0
        assert all(c in df.columns for c in ["student_id", "date", "present"])

    def test_ground_truth_planted_signals(self):
        with open(SAMPLE_DIR / "ground_truth.json", encoding="utf-8") as f:
            gt = json.load(f)
        assert "planted_connections" in gt
        assert len(gt["planted_connections"]) >= 4, "植え込み信号が不足"
        assert "latent_classes" in gt
        assert len(gt["latent_classes"]) == 5, "潜在クラスが5でない"


# ── スキーマ検証 ──────────────────────────────────────

class TestSchema:
    """スキーマファイルの整合性検証。"""

    def test_q_matrix_items_count(self):
        with open(SCHEMA_DIR / "enhanced_q_matrix.json", encoding="utf-8") as f:
            qm = json.load(f)
        assert len(qm["items"]) == 150, f"Q-matrix設問数: {len(qm['items'])}"

    def test_q_matrix_items_match_data(self):
        with open(SCHEMA_DIR / "enhanced_q_matrix.json", encoding="utf-8") as f:
            qm = json.load(f)
        df = pd.read_csv(SAMPLE_DIR / "item_responses.csv")
        qm_ids = set(qm["items"].keys())
        data_ids = set(df["item_id"].unique())
        assert data_ids.issubset(qm_ids), f"データにQ-matrix未定義の設問: {data_ids - qm_ids}"

    def test_q_matrix_has_dok(self):
        with open(SCHEMA_DIR / "enhanced_q_matrix.json", encoding="utf-8") as f:
            qm = json.load(f)
        dok_items = [iid for iid, m in qm["items"].items() if "dok_level" in m]
        assert len(dok_items) >= 100, f"DOKタグ付き設問が少ない: {len(dok_items)}"

    def test_curriculum_has_prerequisites(self):
        with open(SCHEMA_DIR / "curriculum.json", encoding="utf-8") as f:
            cur = json.load(f)
        prereqs = cur.get("cross_subject_prerequisites", [])
        assert len(prereqs) >= 15, f"教科横断前提が少ない: {len(prereqs)}"

    def test_glossary_terms(self):
        with open(SCHEMA_DIR / "glossary.json", encoding="utf-8") as f:
            g = json.load(f)
        terms = g.get("terms", {})
        assert len(terms) >= 30, f"用語数が少ない: {len(terms)}"
        for name, entry in terms.items():
            assert "short" in entry, f"用語 '{name}' にshort定義がない"
            assert "long" in entry, f"用語 '{name}' にlong定義がない"


# ── 分析出力検証 ──────────────────────────────────────

class TestAnalysisOutput:
    """分析パイプライン出力の検証。"""

    def test_item_analysis_output(self):
        path = OUTPUT_DIR / "item_analysis.json"
        if not path.exists():
            pytest.skip("item_analysis.json未生成")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert "summary" in data
        assert data["summary"]["total_items"] == 150
        assert data["summary"]["flagged_items"] >= 0

    def test_network_output(self):
        path = OUTPUT_DIR / "network_graph.json"
        if not path.exists():
            pytest.skip("network_graph.json未生成")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        nodes = data.get("subject_network", {}).get("nodes", [])
        edges = data.get("subject_network", {}).get("edges", [])
        assert len(nodes) >= 20, f"ノード数が少ない: {len(nodes)}"
        assert len(edges) >= 30, f"エッジ数が少ない: {len(edges)}"
        cross = [e for e in edges if e.get("is_cross_subject")]
        assert len(cross) >= 10, f"教科横断エッジが少ない: {len(cross)}"

    def test_patterns_output(self):
        path = OUTPUT_DIR / "patterns.json"
        if not path.exists():
            pytest.skip("patterns.json未生成")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        patterns = data.get("patterns", [])
        assert len(patterns) >= 5, f"パターン数が少ない: {len(patterns)}"
        for p in patterns:
            assert "name" in p
            assert "context" in p
            assert "metrics" in p

    def test_student_types_recovers_classes(self):
        path = OUTPUT_DIR / "student_profiles.json"
        if not path.exists():
            pytest.skip("student_profiles.json未生成")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        k = data.get("optimal_k", 0)
        assert 3 <= k <= 7, f"最適クラス数が想定外: {k}"

    def test_subject_analysis_output(self):
        path = OUTPUT_DIR / "subject_analysis.json"
        if not path.exists():
            pytest.skip("subject_analysis.json未生成")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        subjects = data.get("by_subject", {})
        assert len(subjects) == 5, f"教科数: {len(subjects)}"
        for subj, info in subjects.items():
            assert "dok_profile" in info, f"{subj}にDOKプロファイルがない"
            assert "skill_mastery" in info, f"{subj}にスキル習得データがない"

    def test_cross_subject_output(self):
        path = OUTPUT_DIR / "cross_subject.json"
        if not path.exists():
            pytest.skip("cross_subject.json未生成")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        confirmed = data.get("summary", {}).get("prerequisites_confirmed", 0)
        assert confirmed >= 3, f"確認された前提チェーンが少ない: {confirmed}"

    def test_student_profiles_enhanced(self):
        path = OUTPUT_DIR / "student_profiles_enhanced.json"
        if not path.exists():
            pytest.skip("student_profiles_enhanced.json未生成")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        students = data.get("students", [])
        assert len(students) >= 300, f"プロファイル数が少ない: {len(students)}"
        s0 = students[0]
        assert "learner_profile" in s0, "IB Learner Profileがない"
        assert "wok_profile" in s0, "WOKプロファイルがない"
        assert "motivation" in s0, "動機診断がない"

    def test_irt_output(self):
        path = OUTPUT_DIR / "irt_analysis.json"
        if not path.exists():
            pytest.skip("irt_analysis.json未生成")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert data.get("model") == "2PL"
        subjects = data.get("by_subject", {})
        assert len(subjects) >= 3, f"IRT教科数が少ない: {len(subjects)}"
        for subj, info in subjects.items():
            assert "item_parameters" in info
            assert "student_abilities" in info
            assert "test_information" in info

    def test_metadata(self):
        path = OUTPUT_DIR / "metadata.json"
        if not path.exists():
            pytest.skip("metadata.json未生成")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert "n_students" in data
        assert "n_items" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
