"""教科間つながりネットワークの可視化コンポーネント.

pyvis を使ってインタラクティブなネットワークグラフを生成し、
Streamlit に HTML として埋め込む。
"""

from __future__ import annotations

from pyvis.network import Network
import streamlit.components.v1 as components

# 教科カラーマップ
SUBJECT_COLORS: dict[str, str] = {
    "math": "#4C78A8",
    "physics": "#F58518",
    "chemistry": "#E45756",
    "english": "#72B7B2",
    "japanese": "#54A24B",
}

_DEFAULT_COLOR = "#999999"


def render_network(
    nodes: list[dict],
    edges: list[dict],
    height: str = "600px",
    highlight_bridges: bool = True,
) -> str:
    """pyvis でネットワークを描画し、HTML 文字列を返す。

    Parameters
    ----------
    nodes : list[dict]
        各ノードは id, label, subject, color, centrality を持つ。
    edges : list[dict]
        各エッジは source, target, weight, is_cross_subject を持つ。
    height : str
        描画領域の高さ (CSS 値)。
    highlight_bridges : bool
        ブリッジノードを星形 + グロー強調するかどうか。

    Returns
    -------
    str
        描画済みの HTML 文字列。
    """
    net = Network(
        height=height,
        width="100%",
        bgcolor="#0E1117",
        font_color="white",
        directed=False,
        notebook=False,
    )

    # 物理シミュレーション設定
    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -80,
          "centralGravity": 0.01,
          "springLength": 120,
          "springConstant": 0.04,
          "damping": 0.4
        },
        "solver": "forceAtlas2Based",
        "stabilization": {"iterations": 150}
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100
      }
    }
    """)

    # ブリッジノード ID を収集
    bridge_ids: set[str] = set()
    if highlight_bridges:
        for node in nodes:
            centrality = node.get("centrality", {})
            if centrality.get("bridge_score", 0) >= 0.5:
                bridge_ids.add(node["id"])

    # ノード追加
    for node in nodes:
        color = node.get("color") or SUBJECT_COLORS.get(node.get("subject", ""), _DEFAULT_COLOR)
        centrality = node.get("centrality", {})
        degree = centrality.get("degree", 0.3)
        size = 15 + degree * 40  # 中心性に応じたサイズ

        bridge_score = centrality.get("bridge_score", 0)
        title = (
            f"{node['label']}\n"
            f"次数中心性: {degree:.2f}\n"
            f"媒介中心性: {centrality.get('betweenness', 0):.2f}\n"
            f"ブリッジスコア: {bridge_score:.2f}"
        )

        is_bridge = node["id"] in bridge_ids
        shape = "star" if is_bridge else "dot"

        border_width = 3 if is_bridge else 1
        border_color = "#FFD700" if is_bridge else color

        net.add_node(
            node["id"],
            label=node["label"],
            title=title,
            color={
                "background": color,
                "border": border_color,
                "highlight": {"background": color, "border": "#FFFFFF"},
            },
            size=size,
            shape=shape,
            borderWidth=border_width,
            shadow=is_bridge,
        )

    # エッジ追加
    for edge in edges:
        weight = edge.get("weight", 0.1)
        is_cross = edge.get("is_cross_subject", False)
        width = 1 + weight * 8
        edge_color = "#FF6B6B" if is_cross else "#555555"
        dashes = False

        net.add_edge(
            edge["source"],
            edge["target"],
            value=weight,
            width=width,
            color={"color": edge_color, "opacity": 0.6},
            title=f"重み: {weight:.3f}" + (" (教科横断)" if is_cross else ""),
            dashes=dashes,
        )

    html = net.generate_html()
    return html


def display_network(
    nodes: list[dict],
    edges: list[dict],
    height: str = "600px",
    highlight_bridges: bool = True,
) -> None:
    """ネットワークを Streamlit 上にレンダリングする。"""
    html = render_network(nodes, edges, height=height, highlight_bridges=highlight_bridges)
    # pyvis の HTML 高さをピクセル数値に変換
    height_px = int(height.replace("px", "")) + 50
    components.html(html, height=height_px, scrolling=True)
