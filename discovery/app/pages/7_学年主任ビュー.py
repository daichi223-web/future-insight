"""学年主任ビュー - 学年全体の傾向と教科横断パターンを俯瞰する"""

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
SUBJECT_JA = {"math": "数学", "physics": "物理", "chemistry": "化学",
              "english": "英語", "japanese": "国語"}


def load_json(name):
    p = OUTPUT_DIR / name
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return None


st.header("学年主任ビュー")
st.caption("学年全体の傾向と教科横断パターンを俯瞰する")

# サイドバー
with st.sidebar:
    glossary_sidebar(["偏相関", "Bridge Centrality", "教科横断前提チェーン",
                      "ボトルネックスキル", "パターンランゲージ", "アソシエーションルール",
                      "TOK", "ATLスキル"])

# データ読込
metadata = load_json("metadata.json")
network = load_json("network_graph.json")
patterns = load_json("patterns.json")
profiles = load_json("student_profiles.json")
cross_subj = load_json("cross_subject.json")
subject_data = load_json("subject_analysis.json")

if not metadata:
    st.warning("分析を実行してください: `python scripts/run_pipeline.py`")
    st.stop()

# ── セクション1: 学年概要 ──
st.subheader("学年概要")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("生徒数", metadata.get("n_students", "N/A"))

n_edges = 0
n_cross = 0
if network:
    edges = network.get("subject_network", {}).get("edges", [])
    n_edges = len(edges)
    n_cross = sum(1 for e in edges if e.get("is_cross_subject"))
col2.metric("教科横断つながり", n_cross)

n_patterns = len(patterns.get("patterns", [])) if patterns else 0
col3.metric("発見パターン", n_patterns)

n_types = profiles.get("optimal_k", 0) if profiles else 0
col4.metric("生徒タイプ", n_types)

n_bridge = 0
if network:
    bridges = network.get("bridge_nodes", [])
    n_bridge = sum(1 for b in bridges if b.get("bridge_score", 0) > 0.05)
col5.metric("ブリッジノード", n_bridge)

# ── セクション2: 教科横断つながり（簡易版）──
st.subheader("教科横断つながりマップ（上位10）")
if network:
    edges = network.get("subject_network", {}).get("edges", [])
    cross_edges = [e for e in edges if e.get("is_cross_subject")]
    cross_edges.sort(key=lambda e: abs(e.get("weight", 0)), reverse=True)
    top10 = cross_edges[:10]

    if top10:
        edge_df = pd.DataFrame([{
            "From": e["source"],
            "To": e["target"],
            "強度": round(e.get("weight", 0), 3),
        } for e in top10])
        st.dataframe(edge_df, use_container_width=True, hide_index=True)
        st.caption("詳細は「つながりマップ」ページを参照")
    else:
        st.info("教科横断エッジがありません。")
    term_expander("偏相関")
else:
    st.info("ネットワーク分析データがありません。")

# ── セクション3: 教科横断前提チェーン検証 ──
st.subheader("教科横断前提チェーン検証")
if cross_subj:
    prereqs = cross_subj.get("prerequisite_validation", [])
    if prereqs:
        prereq_df = pd.DataFrame(prereqs)
        # ステータスに色を付ける
        def status_icon(s):
            if s == "確認":
                return "✓ 確認"
            elif s == "弱い関連":
                return "△ 弱い関連"
            elif s == "未確認":
                return "✗ 未確認"
            return s

        display_df = prereq_df[["from", "to", "expected_strength",
                                "actual_correlation", "status", "description_ja"]].copy()
        display_df.columns = ["前提スキル", "依存スキル", "想定強度",
                              "実測相関", "ステータス", "説明"]
        display_df["ステータス"] = display_df["ステータス"].apply(status_icon)
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        summary = cross_subj.get("summary", {})
        confirmed = summary.get("prerequisites_confirmed", 0)
        total = summary.get("prerequisites_total", 0)
        st.caption(f"{total}件中 {confirmed}件が確認済み")
    term_expander("教科横断前提チェーン")

    # タイミングミスマッチ
    mismatches = cross_subj.get("timing_mismatches", [])
    if mismatches:
        st.markdown("**タイミングミスマッチ（前提が依存先より後に教えられるケース）**")
        for m in mismatches:
            st.warning(m.get("issue", ""))
else:
    st.info("教科横断分析を実行してください。")

# ── セクション4: ボトルネックスキル ──
st.subheader("ボトルネックスキル")
if cross_subj:
    bottlenecks = cross_subj.get("bottleneck_skills", [])
    if bottlenecks:
        for b in bottlenecks[:5]:
            subjects = ", ".join(b.get("affected_subjects", []))
            st.markdown(
                f"**{b['skill']}** — 影響教科: {subjects} | "
                f"習得率: {b.get('mean_mastery', 0):.0%} | "
                f"影響度: {b.get('impact', '')}"
            )
    else:
        st.info("明示的なボトルネックスキルは検出されませんでした。ネットワーク分析のBridge Centralityを確認してください。")
    term_expander("ボトルネックスキル")

# ── セクション5: 生徒タイプ分布 ──
st.subheader("生徒タイプ分布（学年全体）")
if profiles:
    classes = profiles.get("classes", [])
    if classes:
        type_df = pd.DataFrame([{
            "タイプ": c["label"],
            "人数": c["size"],
            "割合": f"{c['proportion']:.1%}",
        } for c in classes])

        col_pie, col_bar = st.columns(2)
        with col_pie:
            fig_pie = px.pie(
                names=[c["label"] for c in classes],
                values=[c["size"] for c in classes],
                title="タイプ分布",
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_bar:
            bar_data = []
            for c in classes:
                profile = c.get("profile", {})
                for subj, score in profile.items():
                    if subj in SUBJECT_JA:
                        bar_data.append({
                            "タイプ": c["label"],
                            "教科": SUBJECT_JA[subj],
                            "平均点": score,
                        })
            if bar_data:
                fig_bar = px.bar(
                    pd.DataFrame(bar_data),
                    x="教科", y="平均点", color="タイプ",
                    barmode="group", title="タイプ別教科平均",
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        st.dataframe(type_df, use_container_width=True, hide_index=True)

# ── セクション6: 教科別DOK天井比較 ──
st.subheader("教科別DOK天井比較")
if subject_data:
    by_subj = subject_data.get("by_subject", {})
    dok_comparison = []
    for subj_key, subj_val in by_subj.items():
        dok = subj_val.get("dok_profile", {})
        for level, data in dok.items():
            dok_comparison.append({
                "教科": SUBJECT_JA.get(subj_key, subj_key),
                "DOKレベル": f"DOK {level}",
                "平均正答率": data.get("mean_score", 0),
            })

    if dok_comparison:
        fig_dok = px.bar(
            pd.DataFrame(dok_comparison),
            x="教科", y="平均正答率", color="DOKレベル",
            barmode="group", title="教科別 DOKレベルパフォーマンス",
        )
        fig_dok.update_yaxes(range=[0, 1], tickformat=".0%")
        st.plotly_chart(fig_dok, use_container_width=True)

        # 全教科DOK3天井チェック
        ceilings = [v.get("dok_ceiling") for v in by_subj.values() if v.get("dok_ceiling")]
        if ceilings and all(c >= 3 for c in ceilings):
            st.info("全教科でDOK3に天井があります。メタ認知的なボトルネックの可能性を検討してください。")
        term_expander("DOK")

# ── セクション7: 発見パターン サマリー ──
st.subheader("発見パターン（上位5件）")
if patterns:
    for p in patterns.get("patterns", [])[:5]:
        with st.expander(f"**{p.get('name', 'パターン')}** (lift={p.get('metrics', {}).get('lift', 0):.1f})"):
            st.markdown(f"**コンテクスト**: {p.get('context', '')}")
            st.markdown(f"**問題**: {p.get('problem', '')}")
            st.markdown(f"**解決**: {p.get('solution', '')}")
            tags = p.get("tags", [])
            if tags:
                st.caption(" ".join(tags))
    if n_patterns > 5:
        st.caption(f"他 {n_patterns - 5} 件は「パターンカタログ」ページを参照")

# WOK分析
if cross_subj:
    wok = cross_subj.get("wok_connections", {})
    if wok:
        st.subheader("WOK（知る方法）媒介相関")
        for wok_name, wok_data in wok.items():
            with st.expander(f"WOK: {wok_name} ({wok_data.get('n_items', 0)}設問)"):
                corrs = wok_data.get("cross_subject_correlations", [])
                if corrs:
                    corr_df = pd.DataFrame(corrs[:5])
                    st.dataframe(corr_df, use_container_width=True, hide_index=True)
        term_expander("TOK")

# フッター
st.divider()
if metadata:
    st.caption(f"最終分析: {metadata.get('analysis_timestamp', 'N/A')}")
