"""画面1: つながりマップ — 教科間ネットワーク可視化."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# コンポーネントのインポートパス追加
_APP_DIR = Path(__file__).resolve().parent.parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

from components.network_viz import display_network  # noqa: E402

# app.py からデータローダーを再利用
sys.path.insert(0, str(_APP_DIR))
from app import load_json  # noqa: E402

# ---------------------------------------------------------------------------
# 教科設定
# ---------------------------------------------------------------------------
SUBJECT_NAMES: dict[str, str] = {
    "math": "数学",
    "physics": "物理",
    "chemistry": "化学",
    "english": "英語",
    "japanese": "国語",
}

SUBJECT_COLORS: dict[str, str] = {
    "math": "#4C78A8",
    "physics": "#F58518",
    "chemistry": "#E45756",
    "english": "#72B7B2",
    "japanese": "#54A24B",
}

# ---------------------------------------------------------------------------
# データ読み込み
# ---------------------------------------------------------------------------
network_data = load_json("network_graph.json")

if network_data is None:
    st.warning("ネットワークデータが見つかりません。分析を実行してください。")
    st.stop()

subject_network = network_data.get("subject_network", {})
all_nodes: list[dict] = subject_network.get("nodes", [])
all_edges: list[dict] = subject_network.get("edges", [])
communities: list[dict] = network_data.get("communities", [])
bridge_nodes: list[dict] = network_data.get("bridge_nodes", [])

# ---------------------------------------------------------------------------
# サイドバー
# ---------------------------------------------------------------------------
st.sidebar.header("フィルタ設定")

# 教科フィルタ
st.sidebar.subheader("表示教科")
selected_subjects: list[str] = []
for key, label in SUBJECT_NAMES.items():
    if st.sidebar.checkbox(label, value=True, key=f"subj_{key}"):
        selected_subjects.append(key)

# エッジ重みしきい値
weight_threshold: float = st.sidebar.slider(
    "エッジ重みしきい値",
    min_value=0.0,
    max_value=0.5,
    value=0.08,
    step=0.01,
    help="この値以上の重みを持つエッジのみ表示します",
)

# ブリッジ強調
highlight_bridges: bool = st.sidebar.toggle("ブリッジノードを強調", value=True)

# ---------------------------------------------------------------------------
# フィルタリング
# ---------------------------------------------------------------------------
filtered_nodes = [n for n in all_nodes if n.get("subject", "") in selected_subjects]
filtered_node_ids = {n["id"] for n in filtered_nodes}
filtered_edges = [
    e
    for e in all_edges
    if e["source"] in filtered_node_ids
    and e["target"] in filtered_node_ids
    and e.get("weight", 0) >= weight_threshold
]

# ---------------------------------------------------------------------------
# メインコンテンツ
# ---------------------------------------------------------------------------
st.header("つながりマップ")
st.caption("教科・スキル間の関連をネットワークで可視化します。ノードをドラッグして探索できます。")

# 凡例
legend_cols = st.columns(len(SUBJECT_NAMES))
for col, (key, label) in zip(legend_cols, SUBJECT_NAMES.items()):
    color = SUBJECT_COLORS[key]
    col.markdown(
        f'<span style="color:{color};font-size:1.2em;">●</span> {label}',
        unsafe_allow_html=True,
    )

# ネットワーク描画
if filtered_nodes:
    display_network(
        filtered_nodes,
        filtered_edges,
        height="600px",
        highlight_bridges=highlight_bridges,
    )
else:
    st.info("表示するノードがありません。教科フィルタを確認してください。")

st.divider()

# ---------------------------------------------------------------------------
# ブリッジノード一覧
# ---------------------------------------------------------------------------
st.subheader("ブリッジノード")
st.caption("複数教科を橋渡しするノード。ブリッジスコアが高いほど教科横断的な影響が大きいことを示します。")

if bridge_nodes:
    bridge_df = pd.DataFrame(bridge_nodes)
    bridge_df = bridge_df.sort_values("bridge_score", ascending=False)

    display_cols = {
        "id": "ノードID",
        "bridge_score": "ブリッジスコア",
        "connected_subjects": "接続教科",
        "description": "説明",
    }
    available_cols = [c for c in display_cols if c in bridge_df.columns]
    bridge_display = bridge_df[available_cols].rename(
        columns={c: display_cols[c] for c in available_cols}
    )

    # 接続教科を日本語に変換
    if "接続教科" in bridge_display.columns:
        bridge_display["接続教科"] = bridge_display["接続教科"].apply(
            lambda subjects: ", ".join(SUBJECT_NAMES.get(s, s) for s in subjects)
            if isinstance(subjects, list)
            else str(subjects)
        )

    st.dataframe(bridge_display, use_container_width=True, hide_index=True)
else:
    st.info("ブリッジノードは検出されませんでした。")

st.divider()

# ---------------------------------------------------------------------------
# コミュニティ
# ---------------------------------------------------------------------------
st.subheader("検出されたコミュニティ")
st.caption("ネットワーク内で密に接続されたノード群。教科境界との一致・不一致を確認できます。")

if communities:
    for comm in communities:
        comm_id = comm.get("id", "?")
        dominant = SUBJECT_NAMES.get(comm.get("dominant_subject", ""), comm.get("dominant_subject", "不明"))
        crosses = comm.get("crosses_subjects", False)
        node_list = comm.get("nodes", [])
        cross_label = "教科横断" if crosses else "単一教科内"
        cross_color = "#FF6B6B" if crosses else "#54A24B"

        with st.expander(
            f"コミュニティ {comm_id} — {dominant}中心 ({cross_label})",
            expanded=False,
        ):
            st.markdown(
                f'<span style="color:{cross_color};font-weight:600;">{cross_label}</span>',
                unsafe_allow_html=True,
            )
            st.write(f"主要教科: {dominant}")
            st.write(f"含まれるノード数: {len(node_list)}")
            if node_list:
                st.code(", ".join(node_list))
else:
    st.info("コミュニティは検出されませんでした。")
