"""スキルレーダーチャート コンポーネント.

plotly の Scatterpolar でプロファイルをレーダー表示する。
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

# 教科キー → 日本語ラベル
SUBJECT_LABELS: dict[str, str] = {
    "math": "数学",
    "physics": "物理",
    "chemistry": "化学",
    "english": "英語",
    "japanese": "国語",
}

# 教科カラー
SUBJECT_COLORS: dict[str, str] = {
    "math": "#4C78A8",
    "physics": "#F58518",
    "chemistry": "#E45756",
    "english": "#72B7B2",
    "japanese": "#54A24B",
}


def render_skill_radar(
    profile_dict: dict,
    title: str = "",
    fill_color: str = "rgba(76, 120, 168, 0.3)",
    line_color: str = "#4C78A8",
) -> go.Figure:
    """レーダーチャートの Figure を生成して返す。

    Parameters
    ----------
    profile_dict : dict
        教科キーをキー、スコアを値とする辞書。
        例: {"math": 78.2, "physics": 74.5, ...}
    title : str
        チャートタイトル。
    fill_color : str
        塗りつぶし色 (RGBA)。
    line_color : str
        線の色。

    Returns
    -------
    go.Figure
        plotly Figure オブジェクト。
    """
    # 教科の順序を固定
    subject_order = ["math", "physics", "chemistry", "english", "japanese"]
    categories = []
    values = []

    for subj in subject_order:
        if subj in profile_dict:
            categories.append(SUBJECT_LABELS.get(subj, subj))
            values.append(profile_dict[subj])

    # レーダーを閉じるために先頭を末尾にも追加
    if categories:
        categories_closed = categories + [categories[0]]
        values_closed = values + [values[0]]
    else:
        categories_closed = []
        values_closed = []

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill="toself",
            fillcolor=fill_color,
            line=dict(color=line_color, width=2),
            marker=dict(size=6, color=line_color),
            name=title or "プロファイル",
        )
    )

    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[20, 40, 60, 80, 100],
                ticktext=["20", "40", "60", "80", "100"],
                gridcolor="rgba(255,255,255,0.1)",
                linecolor="rgba(255,255,255,0.1)",
                tickfont=dict(color="#888888", size=10),
            ),
            angularaxis=dict(
                gridcolor="rgba(255,255,255,0.15)",
                linecolor="rgba(255,255,255,0.15)",
                tickfont=dict(color="#e0e0e0", size=13),
            ),
        ),
        showlegend=False,
        title=dict(text=title, font=dict(color="#e0e0e0", size=16)) if title else None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, r=60, t=60 if title else 30, b=30),
        height=400,
    )

    return fig


def display_skill_radar(
    profile_dict: dict,
    title: str = "",
    fill_color: str = "rgba(76, 120, 168, 0.3)",
    line_color: str = "#4C78A8",
) -> None:
    """レーダーチャートを Streamlit 上に表示する。"""
    fig = render_skill_radar(profile_dict, title=title, fill_color=fill_color, line_color=line_color)
    st.plotly_chart(fig, use_container_width=True)
