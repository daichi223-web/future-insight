"""パターンカード コンポーネント.

Context-Problem-Solution 形式で発見パターンを表示する。
"""

from __future__ import annotations

import streamlit as st

# タグ別の色マッピング
_TAG_COLORS: dict[str, str] = {
    "#教科横断": "#FF6B6B",
    "#前提条件": "#4ECDC4",
    "#つまずき連鎖": "#FFE66D",
    "#読解力": "#A8E6CF",
    "#計算力": "#FFD3B6",
    "#高達成": "#95E1D3",
    "#低達成": "#F38181",
}

_DEFAULT_TAG_COLOR = "#888888"


def _tag_badge(tag: str) -> str:
    """タグをカラー付きバッジ HTML として返す。"""
    color = _TAG_COLORS.get(tag, _DEFAULT_TAG_COLOR)
    return (
        f'<span style="background-color:{color};color:#1a1a2e;'
        f"padding:2px 8px;border-radius:12px;font-size:0.8em;"
        f'font-weight:600;margin-right:4px;">{tag}</span>'
    )


def _metric_badge(label: str, value: float, color: str) -> str:
    """メトリクスを小さなバッジ HTML として返す。"""
    return (
        f'<span style="background-color:{color};color:white;'
        f"padding:2px 8px;border-radius:8px;font-size:0.75em;"
        f'margin-right:6px;">{label}: {value:.2f}</span>'
    )


def render_pattern_card(pattern: dict) -> None:
    """パターンカードを Streamlit 上に描画する。

    Parameters
    ----------
    pattern : dict
        パターン辞書。name, tags, context, problem, solution, metrics を含む。
    """
    with st.container():
        # カード全体のスタイル
        card_html = []

        # ヘッダー: パターン名
        name = pattern.get("name", "不明なパターン")
        rank = pattern.get("importance_rank", "")
        rank_str = f"#{rank} " if rank else ""
        card_html.append(
            f'<div style="background-color:#1a1a2e;border:1px solid #333;'
            f'border-radius:12px;padding:20px;margin-bottom:16px;">'
        )
        card_html.append(
            f'<h4 style="margin:0 0 8px 0;color:#e0e0e0;">'
            f"{rank_str}{name}</h4>"
        )

        # タグ
        tags = pattern.get("tags", [])
        if tags:
            tags_html = " ".join(_tag_badge(t) for t in tags)
            card_html.append(f'<div style="margin-bottom:12px;">{tags_html}</div>')

        # Context-Problem-Solution セクション
        sections = [
            ("観察された文脈", pattern.get("context", "")),
            ("発見された関連", pattern.get("problem", "")),
            ("示唆されるアクション", pattern.get("solution", "")),
        ]
        section_icons = ["eye", "link", "lightbulb"]
        section_colors = ["#4C78A8", "#F58518", "#54A24B"]

        for (label, text), color in zip(sections, section_colors):
            if text:
                card_html.append(
                    f'<div style="margin-bottom:8px;">'
                    f'<span style="color:{color};font-weight:600;font-size:0.9em;">'
                    f"{label}</span>"
                    f'<p style="color:#c0c0c0;margin:4px 0 0 0;font-size:0.9em;'
                    f'line-height:1.5;">{text}</p></div>'
                )

        # メトリクス
        metrics = pattern.get("metrics", {})
        if metrics:
            badges = []
            if "support" in metrics:
                badges.append(_metric_badge("支持度", metrics["support"], "#4C78A8"))
            if "confidence" in metrics:
                badges.append(_metric_badge("確信度", metrics["confidence"], "#F58518"))
            if "lift" in metrics:
                badges.append(_metric_badge("リフト", metrics["lift"], "#E45756"))
            card_html.append(
                f'<div style="margin-top:12px;padding-top:8px;'
                f'border-top:1px solid #333;">{"".join(badges)}</div>'
            )

        card_html.append("</div>")
        st.markdown("".join(card_html), unsafe_allow_html=True)
