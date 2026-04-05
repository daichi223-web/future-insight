"""教育データ発見エンジン — メインダッシュボード.

Streamlit のエントリーポイント。概要画面と KPI を表示する。
起動: streamlit run discovery/app/app.py
"""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Page config (ここでのみ set_page_config を呼ぶ)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="教育データ発見エンジン",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# データディレクトリ
# ---------------------------------------------------------------------------
_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "analysis" / "output"


# ---------------------------------------------------------------------------
# JSON 読み込みユーティリティ
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_json(filename: str) -> dict | None:
    """analysis/output/ 配下の JSON ファイルを読み込む。見つからなければ None。"""
    path = _OUTPUT_DIR / filename
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_all() -> dict[str, dict | None]:
    """全 JSON ファイルをまとめて読み込む。"""
    return {
        "network": load_json("network_graph.json"),
        "patterns": load_json("patterns.json"),
        "profiles": load_json("student_profiles.json"),
        "items": load_json("item_analysis.json"),
        "metadata": load_json("metadata.json"),
    }


# ---------------------------------------------------------------------------
# メイン画面
# ---------------------------------------------------------------------------
def main() -> None:
    data = load_all()

    # ヘッダー
    st.markdown(
        '<h1 style="text-align:center;">教育データ発見エンジン</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="text-align:center;color:#888;">教科間のつながり・学習パターン・生徒プロファイルを探索的に可視化するダッシュボード</p>',
        unsafe_allow_html=True,
    )

    st.divider()

    # データ未生成チェック
    if all(v is None for v in data.values()):
        st.warning("分析結果が見つかりません。先に分析パイプラインを実行してください。")
        st.info("実行方法: `python -m discovery.scripts.run_pipeline`")
        return

    # ----- KPI カード -----
    metadata = data.get("metadata") or {}
    patterns_data = data.get("patterns") or {}
    profiles_data = data.get("profiles") or {}
    items_data = data.get("items") or {}

    n_students = metadata.get("n_students", "—")
    n_patterns = len(patterns_data.get("patterns", []))
    n_classes = profiles_data.get("optimal_k", "—")
    n_flagged = (items_data.get("summary") or {}).get("flagged_items", "—")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="対象生徒数", value=n_students)
    col2.metric(label="発見パターン数", value=n_patterns)
    col3.metric(label="生徒タイプ数", value=n_classes)
    col4.metric(label="要注意項目数", value=n_flagged)

    st.divider()

    # ----- 各画面の説明 -----
    st.subheader("画面ガイド")

    guide_cols = st.columns(4)

    with guide_cols[0]:
        st.markdown("##### つながりマップ")
        st.caption(
            "教科・スキル間の関連をネットワークで可視化。"
            "教科をまたぐブリッジノードを特定し、"
            "つまずきの連鎖経路を発見します。"
        )

    with guide_cols[1]:
        st.markdown("##### パターンカタログ")
        st.caption(
            "相関ルールマイニングで発見されたパターンを "
            "Context-Problem-Solution 形式で閲覧。"
            "教科横断の示唆を一覧できます。"
        )

    with guide_cols[2]:
        st.markdown("##### 個別診断プロファイル")
        st.caption(
            "潜在クラス分析に基づく生徒タイプの可視化。"
            "個々の生徒がどのタイプに属するか、"
            "レーダーチャートで確認できます。"
        )

    with guide_cols[3]:
        st.markdown("##### テスト品質レポート")
        st.caption(
            "テスト項目の難易度と識別力を散布図で確認。"
            "改善が必要な問題をフラグ付きで一覧表示します。"
        )

    # ----- 最終分析タイムスタンプ -----
    st.divider()
    timestamp = metadata.get("analysis_timestamp", "不明")
    st.caption(f"最終分析実行: {timestamp}")


if __name__ == "__main__":
    main()
