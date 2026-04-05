"""学級担任ビュー - クラスの生徒を全教科横断で把握する"""

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


st.header("学級担任ビュー")
st.caption("クラスの生徒を全教科横断で把握する")

# サイドバー
with st.sidebar:
    st.subheader("フィルタ")
    # クラス疑似フィルタ（student_id 範囲で分割）
    class_options = {"全員": (1, 999), "1組 (S001-S120)": (1, 120),
                     "2組 (S121-S240)": (121, 240), "3組 (S241-S360)": (241, 360),
                     "4組 (S361-S500)": (361, 500)}
    selected_class = st.selectbox("クラス選択", list(class_options.keys()))
    lo, hi = class_options[selected_class]

    glossary_sidebar(["観点別評価", "偏差値", "潜在クラス分析", "ボトルネックスキル", "DOK"])

# データ読込
profiles = load_json("student_profiles.json")
enhanced = load_json("student_profiles_enhanced.json")
grades_data = load_json("metadata.json")

if not profiles:
    st.warning("分析を実行してください: `python scripts/run_pipeline.py`")
    st.stop()

# フィルタ適用
assignments = profiles.get("student_assignments", [])
filtered = [a for a in assignments
            if lo <= int(a["student_id"][1:]) <= hi]

if not filtered:
    st.info("該当する生徒がいません。")
    st.stop()

student_ids = {a["student_id"] for a in filtered}

# ── セクション1: クラス概要 ──
st.subheader("クラス概要")

classes = profiles.get("classes", [])
class_map = {a["student_id"]: a["class_id"] for a in filtered}

# 拡張プロファイルから教科スコア取得
students_enhanced = []
if enhanced:
    students_enhanced = [s for s in enhanced.get("students", [])
                         if s["student_id"] in student_ids]

col1, col2, col3, col4 = st.columns(4)
col1.metric("生徒数", len(filtered))

# 出席率
att_rates = [s.get("motivation", {}).get("attendance_rate", 0.9)
             for s in students_enhanced] if students_enhanced else []
col2.metric("平均出席率", f"{sum(att_rates)/len(att_rates)*100:.1f}%" if att_rates else "N/A")

# サポート候補
support_count = sum(1 for s in students_enhanced
                    if s.get("motivation", {}).get("diagnosis", "") == "動機的課題の可能性"
                    or s.get("motivation", {}).get("attendance_rate", 1) < 0.85)
col3.metric("サポート検討候補", support_count)

# 全教科平均
all_scores = []
for s in students_enhanced:
    for subj, score in s.get("subjects", {}).items():
        all_scores.append(score)
col4.metric("全教科平均", f"{sum(all_scores)/len(all_scores):.1f}" if all_scores else "N/A")

# ── ヒートマップ ──
if students_enhanced:
    heat_data = []
    for s in students_enhanced:
        row = {"生徒ID": s["student_id"]}
        for subj in SUBJECT_JA:
            row[SUBJECT_JA[subj]] = s.get("subjects", {}).get(subj, None)
        heat_data.append(row)

    heat_df = pd.DataFrame(heat_data).set_index("生徒ID")
    heat_df = heat_df.sort_values(list(heat_df.columns), ascending=False)

    fig = px.imshow(
        heat_df.head(50).values,
        labels=dict(x="教科", y="生徒", color="成績"),
        x=list(heat_df.columns),
        y=list(heat_df.head(50).index),
        color_continuous_scale="RdYlGn",
        aspect="auto",
    )
    fig.update_layout(height=max(400, len(heat_df.head(50)) * 12))
    st.plotly_chart(fig, use_container_width=True)
    if len(heat_df) > 50:
        st.caption(f"上位50人を表示（全{len(heat_df)}人）")

# ── セクション2: 生徒タイプ分布 ──
st.subheader("生徒タイプ分布")
if classes and filtered:
    type_counts = {}
    for a in filtered:
        cid = a["class_id"]
        label = next((c["label"] for c in classes if c["class_id"] == cid), f"タイプ{cid}")
        type_counts[label] = type_counts.get(label, 0) + 1

    fig_pie = px.pie(
        names=list(type_counts.keys()),
        values=list(type_counts.values()),
        title="クラス内の生徒タイプ分布",
    )
    st.plotly_chart(fig_pie, use_container_width=True)
    term_expander("潜在クラス分析")

# ── セクション3: 注目すべき生徒 ──
st.subheader("サポート検討候補")
st.caption("※ 本データは支援の参考情報であり、個人の固定的な特性を表すものではありません。")

alerts = []
for s in students_enhanced:
    sid = s["student_id"]
    motivation = s.get("motivation", {})
    att = motivation.get("attendance_rate", 1.0)
    diag = motivation.get("diagnosis", "")

    reasons = []
    if att < 0.85:
        reasons.append(f"出席率 {att*100:.0f}%")
    if diag == "動機的課題の可能性":
        reasons.append("動機的課題の兆候")

    subjects = s.get("subjects", {})
    if subjects:
        vals = list(subjects.values())
        if len(vals) > 1 and max(vals) - min(vals) > 30:
            reasons.append(f"教科間ギャップ {max(vals)-min(vals):.0f}点")

    if reasons:
        alerts.append({"生徒ID": sid, "状況": "、".join(reasons)})

if alerts:
    st.dataframe(pd.DataFrame(alerts), use_container_width=True, hide_index=True)
else:
    st.success("現在、特に注目すべき生徒はいません。")

# ── セクション4: 生徒個別カード ──
st.subheader("生徒個別カード")
for s in students_enhanced[:20]:  # 最初の20人
    sid = s["student_id"]
    with st.expander(f"{sid}"):
        cols = st.columns([1, 1])
        with cols[0]:
            subjects = s.get("subjects", {})
            if subjects:
                fig_radar = go.Figure(go.Scatterpolar(
                    r=[subjects.get(k, 0) for k in SUBJECT_JA],
                    theta=[SUBJECT_JA[k] for k in SUBJECT_JA],
                    fill="toself",
                    name=sid,
                ))
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    height=300, margin=dict(l=40, r=40, t=20, b=20),
                )
                st.plotly_chart(fig_radar, use_container_width=True)

        with cols[1]:
            lp = s.get("learner_profile", {})
            if lp:
                st.markdown("**Learner Profile プロキシ**")
                for attr, val in lp.items():
                    st.progress(val / 100, text=f"{attr}: {val:.0f}")

            motivation = s.get("motivation", {})
            if motivation.get("diagnosis"):
                st.markdown(f"**診断**: {motivation['diagnosis']}")
            st.markdown(f"**出席率**: {motivation.get('attendance_rate', 0)*100:.1f}%")

# 倫理的注意
st.divider()
st.caption("本データは生徒支援の参考情報です。個人の固定的な特性を表すものではありません。")
