"""画面4: テスト品質レポート — 項目分析の可視化."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# コンポーネントのインポートパス追加
_APP_DIR = Path(__file__).resolve().parent.parent
if str(_APP_DIR) not in sys.path:
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

# ---------------------------------------------------------------------------
# データ読み込み
# ---------------------------------------------------------------------------
items_data = load_json("item_analysis.json")

if items_data is None:
    st.warning("項目分析データが見つかりません。分析を実行してください。")
    st.stop()

summary = items_data.get("summary", {})
by_subject: dict[str, dict] = items_data.get("by_subject", {})

if not by_subject:
    st.info("教科別の項目データがありません。")
    st.stop()

# ---------------------------------------------------------------------------
# メインコンテンツ
# ---------------------------------------------------------------------------
st.header("テスト品質レポート")
st.caption("テスト項目の難易度と識別力を分析し、改善が必要な問題を特定します。")

# ---------------------------------------------------------------------------
# サマリーメトリクス
# ---------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("総項目数", summary.get("total_items", "—"))
col2.metric("要注意項目数", summary.get("flagged_items", "—"))
col3.metric("平均難易度", f"{summary.get('mean_difficulty', 0):.2f}")
col4.metric("平均識別力", f"{summary.get('mean_discrimination', 0):.2f}")

st.divider()

# ---------------------------------------------------------------------------
# 教科セレクタ
# ---------------------------------------------------------------------------
available_subjects = list(by_subject.keys())
subject_options = {SUBJECT_NAMES.get(s, s): s for s in available_subjects}
selected_label = st.selectbox(
    "教科を選択",
    options=list(subject_options.keys()),
    index=0,
)
selected_subject = subject_options[selected_label]

# 選択教科の項目データ
subject_data = by_subject[selected_subject]
items: list[dict] = subject_data.get("items", [])

if not items:
    st.info(f"{selected_label}の項目データがありません。")
    st.stop()

# DataFrame に変換
df = pd.DataFrame(items)

# フラグ状態の判定
df["フラグあり"] = df["flags"].apply(lambda f: len(f) > 0 if isinstance(f, list) else False)

# ---------------------------------------------------------------------------
# 散布図: 難易度 vs 識別力
# ---------------------------------------------------------------------------
st.subheader(f"{selected_label} — 難易度 vs 識別力")
st.caption("理想ゾーン (難易度 0.3-0.7、識別力 0.3以上) を緑枠で表示。赤点は要注意項目。")

fig = go.Figure()

# 理想ゾーンの矩形
fig.add_shape(
    type="rect",
    x0=0.3,
    y0=0.3,
    x1=0.7,
    y1=df["discrimination"].max() * 1.1 if len(df) > 0 else 1.0,
    line=dict(color="#54A24B", width=2, dash="dash"),
    fillcolor="rgba(84, 162, 75, 0.08)",
    layer="below",
)

# 正常項目
ok_items = df[~df["フラグあり"]]
if len(ok_items) > 0:
    fig.add_trace(
        go.Scatter(
            x=ok_items["difficulty"],
            y=ok_items["discrimination"],
            mode="markers",
            marker=dict(color="#4C78A8", size=8, opacity=0.7),
            text=ok_items["item_id"],
            hovertemplate=(
                "項目ID: %{text}<br>"
                "難易度: %{x:.2f}<br>"
                "識別力: %{y:.2f}<extra></extra>"
            ),
            name="正常",
        )
    )

# フラグ付き項目
flagged_items = df[df["フラグあり"]]
if len(flagged_items) > 0:
    fig.add_trace(
        go.Scatter(
            x=flagged_items["difficulty"],
            y=flagged_items["discrimination"],
            mode="markers",
            marker=dict(
                color="#E45756",
                size=10,
                opacity=0.9,
                symbol="diamond",
                line=dict(color="white", width=1),
            ),
            text=flagged_items["item_id"],
            hovertemplate=(
                "項目ID: %{text}<br>"
                "難易度: %{x:.2f}<br>"
                "識別力: %{y:.2f}<br>"
                "(要注意)<extra></extra>"
            ),
            name="要注意",
        )
    )

# 理想ゾーンのラベル
fig.add_annotation(
    x=0.5,
    y=0.32,
    text="理想ゾーン",
    showarrow=False,
    font=dict(color="#54A24B", size=11),
)

fig.update_layout(
    xaxis=dict(
        title="難易度 (p値)",
        range=[-0.05, 1.05],
        gridcolor="rgba(255,255,255,0.1)",
        zeroline=False,
    ),
    yaxis=dict(
        title="識別力 (D値)",
        range=[
            min(-0.1, df["discrimination"].min() - 0.05) if len(df) > 0 else -0.1,
            max(1.0, df["discrimination"].max() + 0.1) if len(df) > 0 else 1.0,
        ],
        gridcolor="rgba(255,255,255,0.1)",
        zeroline=False,
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=10, b=10),
    height=500,
    font=dict(color="#e0e0e0"),
    legend=dict(
        font=dict(color="#e0e0e0"),
        bgcolor="rgba(0,0,0,0.3)",
    ),
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# 要注意項目一覧
# ---------------------------------------------------------------------------
st.subheader("要注意項目一覧")

flagged_df = df[df["フラグあり"]].copy()

if len(flagged_df) > 0:
    # 表示用に整形
    display_df = flagged_df[["item_id", "difficulty", "discrimination", "point_biserial", "flags"]].copy()
    display_df = display_df.rename(
        columns={
            "item_id": "項目ID",
            "difficulty": "難易度",
            "discrimination": "識別力",
            "point_biserial": "点双列相関",
            "flags": "フラグ",
        }
    )
    # flags リストを文字列に変換
    display_df["フラグ"] = display_df["フラグ"].apply(
        lambda f: ", ".join(f) if isinstance(f, list) else str(f)
    )

    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.success(f"{selected_label}に要注意項目はありません。全項目が基準を満たしています。")

# ---------------------------------------------------------------------------
# 全項目一覧（折りたたみ）
# ---------------------------------------------------------------------------
with st.expander("全項目データを表示", expanded=False):
    all_display = df[["item_id", "difficulty", "discrimination", "point_biserial", "flags", "フラグあり"]].copy()
    all_display = all_display.rename(
        columns={
            "item_id": "項目ID",
            "difficulty": "難易度",
            "discrimination": "識別力",
            "point_biserial": "点双列相関",
            "flags": "フラグ",
            "フラグあり": "要注意",
        }
    )
    all_display["フラグ"] = all_display["フラグ"].apply(
        lambda f: ", ".join(f) if isinstance(f, list) else str(f)
    )
    st.dataframe(all_display, use_container_width=True, hide_index=True)
