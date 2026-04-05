"""教科担当ビュー - 担当教科を設問レベルで深掘りする"""

import json
import sys
from pathlib import Path

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from components.glossary import glossary_sidebar, term_expander

OUTPUT_DIR = Path(__file__).parent.parent.parent / "analysis" / "output"
SUBJECT_OPTIONS = {"数学": "math", "物理": "physics", "化学": "chemistry",
                   "英語": "english", "国語": "japanese"}


def load_json(name):
    p = OUTPUT_DIR / name
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return None


st.header("教科担当ビュー")
st.caption("担当教科を設問レベルで深掘りする")

# サイドバー
with st.sidebar:
    selected_ja = st.selectbox("教科選択", list(SUBJECT_OPTIONS.keys()))
    subject_key = SUBJECT_OPTIONS[selected_ja]
    glossary_sidebar(["CTT", "難易度指数", "識別力指数", "DOK", "Bloom's Taxonomy",
                      "観点別評価", "誤概念", "Q-matrix"])

# データ読込
subject_data = load_json("subject_analysis.json")
item_data = load_json("item_analysis.json")

if not subject_data:
    st.warning("教科別分析を実行してください。")
    st.stop()

subj = subject_data.get("by_subject", {}).get(subject_key, {})
if not subj:
    st.info(f"{selected_ja}のデータがありません。")
    st.stop()

# ── セクション1: 教科サマリー ──
st.subheader(f"{selected_ja} サマリー")

col1, col2, col3 = st.columns(3)

# 平均正答率
all_dok = subj.get("dok_profile", {})
total_items = sum(d.get("n_items", 0) for d in all_dok.values())
weighted_score = sum(d.get("mean_score", 0) * d.get("n_items", 0) for d in all_dok.values())
avg_score = weighted_score / total_items if total_items > 0 else 0
col1.metric("平均正答率", f"{avg_score:.0%}")

col2.metric("DOK天井レベル", subj.get("dok_ceiling", "N/A"))

gap = subj.get("kanten_gap", 0)
col3.metric("観点別ギャップ", f"{gap:.2f}")

# ── セクション2: スキル習得マップ ──
st.subheader("スキル習得マップ")
skills = subj.get("skill_mastery", [])
if skills:
    skill_df = pd.DataFrame(skills)
    skill_df["color"] = skill_df["mastery_rate"].apply(
        lambda x: "高 (>70%)" if x > 0.7 else ("中 (50-70%)" if x >= 0.5 else "低 (<50%)")
    )
    color_map = {"高 (>70%)": "#2ecc71", "中 (50-70%)": "#f39c12", "低 (<50%)": "#e74c3c"}

    fig = px.bar(
        skill_df, y="skill", x="mastery_rate", color="color",
        color_discrete_map=color_map,
        orientation="h",
        labels={"mastery_rate": "習得率", "skill": "スキル"},
        title="スキル別習得率",
    )
    fig.update_layout(yaxis=dict(autorange="reversed"), showlegend=True, height=max(300, len(skills) * 30))
    fig.update_xaxes(tickformat=".0%", range=[0, 1])
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("スキル習得データがありません。")

# ── セクション3: DOK × Bloom's パフォーマンス ──
st.subheader("DOK × Bloom's パフォーマンス")
col_dok, col_blooms = st.columns(2)

with col_dok:
    dok = subj.get("dok_profile", {})
    if dok:
        dok_df = pd.DataFrame([
            {"DOKレベル": f"DOK {k}", "平均正答率": v.get("mean_score", 0),
             "設問数": v.get("n_items", 0)}
            for k, v in sorted(dok.items())
        ])
        ceiling = subj.get("dok_ceiling", None)
        colors = ["#e74c3c" if f"DOK {ceiling}" == row["DOKレベル"] else "#4C78A8"
                  for _, row in dok_df.iterrows()] if ceiling else None

        fig_dok = px.bar(
            dok_df, x="DOKレベル", y="平均正答率",
            title="DOKレベル別パフォーマンス",
            text_auto=".0%",
        )
        if colors:
            fig_dok.update_traces(marker_color=colors)
        fig_dok.update_yaxes(range=[0, 1], tickformat=".0%")
        st.plotly_chart(fig_dok, use_container_width=True)
    term_expander("DOK")

with col_blooms:
    blooms = subj.get("blooms_ladder", {})
    if blooms:
        order = ["remember", "understand", "apply", "analyze", "evaluate", "create"]
        blooms_ja = {"remember": "記憶", "understand": "理解", "apply": "応用",
                     "analyze": "分析", "evaluate": "評価", "create": "創造"}
        dropoff = subj.get("blooms_dropoff", "")

        blooms_df = pd.DataFrame([
            {"レベル": blooms_ja.get(k, k), "平均正答率": blooms.get(k, 0)}
            for k in order if k in blooms
        ])
        colors_b = ["#e74c3c" if blooms_ja.get(dropoff, "") == row["レベル"] else "#54A24B"
                    for _, row in blooms_df.iterrows()]

        fig_b = px.bar(
            blooms_df, x="レベル", y="平均正答率",
            title="Bloom's 分類別パフォーマンス",
            text_auto=".0%",
        )
        fig_b.update_traces(marker_color=colors_b)
        fig_b.update_yaxes(range=[0, 1], tickformat=".0%")
        st.plotly_chart(fig_b, use_container_width=True)
    term_expander("Bloom's Taxonomy")

# ── セクション4: 観点別評価分析 ──
st.subheader("観点別評価分析")
kanten = subj.get("kanten_profile", {})
if kanten:
    col_k1, col_k2 = st.columns(2)
    for i, (k, v) in enumerate(kanten.items()):
        col = col_k1 if i == 0 else col_k2
        with col:
            score = v.get("mean_score", 0)
            st.metric(k, f"{score:.0%}", delta=f"設問数: {v.get('n_items', 0)}")

    if gap > 0.1:
        st.warning(f"観点間ギャップ: {gap:.2f} — 知識・技能と思考・判断・表現の間に差があります。")
    term_expander("観点別評価")
else:
    st.info("観点別データがありません。")

# ── セクション5: 誤概念ランキング ──
st.subheader("誤概念ランキング")
misconceptions = subj.get("misconceptions", [])
if misconceptions:
    mis_df = pd.DataFrame(misconceptions)
    display_cols = ["name", "prevalence", "item_id"]
    available = [c for c in display_cols if c in mis_df.columns]
    if available:
        mis_df_display = mis_df[available].copy()
        mis_df_display.columns = ["誤概念名", "該当率", "対象設問"][:len(available)]
        if "該当率" in mis_df_display.columns:
            mis_df_display["該当率"] = mis_df_display["該当率"].apply(lambda x: f"{x:.0%}")
        st.dataframe(mis_df_display, use_container_width=True, hide_index=True)
    term_expander("誤概念")
else:
    st.info("誤概念データは今後追加予定です。enhanced_q_matrix.json に誤概念タグを設定してください。")

# ── セクション6: 設問品質 ──
st.subheader("設問品質")
if item_data:
    subj_items = item_data.get("by_subject", {}).get(subject_key, {}).get("items", [])
    if subj_items:
        items_df = pd.DataFrame(subj_items)

        fig_scatter = go.Figure()
        flagged = items_df[items_df["flags"].apply(len) > 0]
        ok = items_df[items_df["flags"].apply(len) == 0]

        fig_scatter.add_trace(go.Scatter(
            x=ok["difficulty"], y=ok["discrimination"],
            mode="markers", name="正常",
            marker=dict(color="#4C78A8", size=8),
            text=ok["item_id"], hovertemplate="%{text}<br>難易度: %{x:.2f}<br>識別力: %{y:.2f}",
        ))
        if not flagged.empty:
            fig_scatter.add_trace(go.Scatter(
                x=flagged["difficulty"], y=flagged["discrimination"],
                mode="markers", name="フラグ付き",
                marker=dict(color="#E45756", size=10, symbol="diamond"),
                text=flagged["item_id"],
                hovertemplate="%{text}<br>難易度: %{x:.2f}<br>識別力: %{y:.2f}",
            ))

        # 理想ゾーン
        fig_scatter.add_shape(type="rect", x0=0.3, x1=0.7, y0=0.3, y1=1.0,
                              fillcolor="rgba(46,204,113,0.1)", line=dict(color="green", dash="dash"))
        fig_scatter.update_layout(
            xaxis_title="難易度 (p値)", yaxis_title="識別力 (D指数)",
            title="難易度 × 識別力", height=400,
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

        if not flagged.empty:
            st.markdown(f"**フラグ付き設問: {len(flagged)}問**")
            flag_display = flagged[["item_id", "difficulty", "discrimination", "flags"]].copy()
            flag_display.columns = ["設問ID", "難易度", "識別力", "フラグ"]
            flag_display["フラグ"] = flag_display["フラグ"].apply(lambda x: ", ".join(x))
            st.dataframe(flag_display, use_container_width=True, hide_index=True)
