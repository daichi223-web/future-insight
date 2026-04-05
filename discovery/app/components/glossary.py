"""用語解説コンポーネント

専門用語にクリックで解説を表示する機能を提供する。

Usage:
    from components.glossary import term, load_glossary

    # テキスト内で用語を使う
    st.markdown(f"この分析では{term('偏相関')}ネットワークを使用します。")

    # 用語解説パネルを表示
    glossary_panel()
"""

import json
from pathlib import Path
from functools import lru_cache

import streamlit as st


GLOSSARY_PATH = Path(__file__).parent.parent.parent / "data" / "schema" / "glossary.json"


@lru_cache(maxsize=1)
def load_glossary() -> dict:
    """用語辞書を読み込む（キャッシュ付き）。"""
    if not GLOSSARY_PATH.exists():
        return {}
    with open(GLOSSARY_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("terms", {})


def term(word: str, show_icon: bool = True) -> str:
    """用語をクリック可能なスタイルで返す。

    Streamlit の st.markdown() 内で使用する。
    クリックすると expander が開いて解説が表示される仕組みは
    term_expander() で実現する。

    Args:
        word: 辞書に登録された用語
        show_icon: True なら用語の後に ? アイコンを付ける

    Returns:
        HTML装飾された用語文字列
    """
    glossary = load_glossary()
    if word not in glossary:
        return f"**{word}**"

    entry = glossary[word]
    tooltip = entry.get("short", "")
    icon = ' <span style="color: #4C78A8; font-size: 0.75em; cursor: help;" title="クリックで詳細表示">&#9432;</span>' if show_icon else ""

    return (
        f'<span style="border-bottom: 1px dashed #4C78A8; cursor: help;" '
        f'title="{tooltip}">'
        f'**{word}**</span>{icon}'
    )


def term_tooltip(word: str) -> None:
    """用語のツールチップをStreamlitで表示する。

    st.markdown() では HTML title 属性のツールチップが使えるため、
    この関数はより詳細な解説が必要な場合に使う。
    """
    glossary = load_glossary()
    if word not in glossary:
        return

    entry = glossary[word]
    st.markdown(
        f'<div style="background: #f0f2f6; border-left: 3px solid #4C78A8; '
        f'padding: 8px 12px; margin: 4px 0; border-radius: 0 4px 4px 0; '
        f'font-size: 0.85em;">'
        f'<strong>{word}</strong>'
        f'<br>{entry.get("short", "")}'
        f'</div>',
        unsafe_allow_html=True,
    )


def term_expander(word: str, expanded: bool = False) -> None:
    """用語の詳細解説を expander で表示する。"""
    glossary = load_glossary()
    if word not in glossary:
        return

    entry = glossary[word]
    reading = ""
    category = entry.get("category", "")
    category_badge = f"  `{category}`" if category else ""

    with st.expander(f"{word}{reading}{category_badge}", expanded=expanded):
        st.markdown(entry.get("long", entry.get("short", "")))


def glossary_sidebar(terms_to_show: list[str] | None = None) -> None:
    """サイドバーに用語解説セクションを表示する。

    Args:
        terms_to_show: 表示する用語のリスト。None なら全用語。
    """
    glossary = load_glossary()
    if not glossary:
        return

    if terms_to_show is None:
        terms_to_show = list(glossary.keys())

    available = [t for t in terms_to_show if t in glossary]
    if not available:
        return

    with st.sidebar.expander("用語解説", expanded=False):
        for word in available:
            entry = glossary[word]
            reading = ""
            st.markdown(
                f"**{word}**{reading}",
                help=entry.get("long", entry.get("short", "")),
            )


def glossary_panel(category_filter: str | None = None) -> None:
    """ページ内に全用語の解説パネルを表示する。

    Args:
        category_filter: 特定カテゴリの用語のみ表示する場合に指定
    """
    glossary = load_glossary()
    if not glossary:
        st.info("用語辞書が見つかりません。")
        return

    # カテゴリ別にグループ化
    by_category: dict[str, list[tuple[str, dict]]] = {}
    for word, entry in glossary.items():
        cat = entry.get("category", "その他")
        if category_filter and cat != category_filter:
            continue
        by_category.setdefault(cat, []).append((word, entry))

    for cat, entries in sorted(by_category.items()):
        st.markdown(f"#### {cat}")
        for word, entry in entries:
            reading = ""
            with st.expander(f"{word}{reading}"):
                st.markdown(entry.get("long", entry.get("short", "")))


def inline_help(word: str) -> None:
    """テキスト直後に小さな ? ボタンを配置し、クリックで解説を表示する。

    Usage:
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            st.metric("Bridge Centrality", "0.78")
        with col2:
            inline_help("Bridge Centrality")
    """
    glossary = load_glossary()
    if word not in glossary:
        return

    entry = glossary[word]
    st.markdown(
        f'<div style="text-align: center; margin-top: 12px;">'
        f'<span style="background: #4C78A8; color: white; border-radius: 50%; '
        f'width: 20px; height: 20px; display: inline-flex; align-items: center; '
        f'justify-content: center; font-size: 0.7em; cursor: help;" '
        f'title="{entry.get("long", entry.get("short", ""))}">'
        f'?</span></div>',
        unsafe_allow_html=True,
    )
