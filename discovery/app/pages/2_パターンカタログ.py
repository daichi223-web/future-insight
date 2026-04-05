"""画面2: パターンカタログ — 発見パターンの一覧表示."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# コンポーネントのインポートパス追加
_APP_DIR = Path(__file__).resolve().parent.parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

from components.pattern_card import render_pattern_card  # noqa: E402
from app import load_json  # noqa: E402

# ---------------------------------------------------------------------------
# データ読み込み
# ---------------------------------------------------------------------------
patterns_data = load_json("patterns.json")

if patterns_data is None:
    st.warning("パターンデータが見つかりません。分析を実行してください。")
    st.stop()

all_patterns: list[dict] = patterns_data.get("patterns", [])

if not all_patterns:
    st.info("発見されたパターンはありません。")
    st.stop()

# ---------------------------------------------------------------------------
# タグ一覧を収集
# ---------------------------------------------------------------------------
all_tags: set[str] = set()
for p in all_patterns:
    all_tags.update(p.get("tags", []))
all_tags_sorted = sorted(all_tags)

# ---------------------------------------------------------------------------
# サイドバー
# ---------------------------------------------------------------------------
st.sidebar.header("フィルタ設定")

# タグフィルタ
selected_tags = st.sidebar.multiselect(
    "タグで絞り込み",
    options=all_tags_sorted,
    default=[],
    help="選択したタグを含むパターンのみ表示します（未選択=全て表示）",
)

# ソート順
sort_options = {
    "リフト値（高い順）": ("lift", False),
    "確信度（高い順）": ("confidence", False),
    "支持度（高い順）": ("support", False),
    "重要度ランク": ("importance_rank", True),
}
sort_choice = st.sidebar.selectbox("並び替え", options=list(sort_options.keys()))
sort_key, sort_ascending = sort_options[sort_choice]

# ---------------------------------------------------------------------------
# フィルタリングとソート
# ---------------------------------------------------------------------------
filtered_patterns = all_patterns
if selected_tags:
    filtered_patterns = [
        p
        for p in filtered_patterns
        if any(t in p.get("tags", []) for t in selected_tags)
    ]

# ソート
def _get_sort_value(pattern: dict) -> float:
    if sort_key == "importance_rank":
        return pattern.get(sort_key, 9999)
    return pattern.get("metrics", {}).get(sort_key, 0)

filtered_patterns = sorted(filtered_patterns, key=_get_sort_value, reverse=not sort_ascending)

# ---------------------------------------------------------------------------
# メインコンテンツ
# ---------------------------------------------------------------------------
st.header("パターンカタログ")
st.caption("相関ルールマイニングで発見された教科間パターンを一覧表示します。")

# サマリー
total_count = len(all_patterns)
cross_subject_count = sum(
    1
    for p in all_patterns
    if "#教科横断" in p.get("tags", [])
)
filtered_count = len(filtered_patterns)

col1, col2, col3 = st.columns(3)
col1.metric("全パターン数", total_count)
col2.metric("教科横断パターン", cross_subject_count)
col3.metric("表示中", filtered_count)

st.divider()

# カード表示（2カラムグリッド）
if filtered_patterns:
    for i in range(0, len(filtered_patterns), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(filtered_patterns):
                with col:
                    render_pattern_card(filtered_patterns[idx])
else:
    st.info("条件に一致するパターンがありません。フィルタを調整してください。")
