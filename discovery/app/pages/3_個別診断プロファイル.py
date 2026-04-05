"""画面3: 個別診断プロファイル — 生徒タイプの可視化."""

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

from components.skill_radar import render_skill_radar, SUBJECT_LABELS  # noqa: E402
from app import load_json  # noqa: E402

# ---------------------------------------------------------------------------
# クラス別カラー
# ---------------------------------------------------------------------------
_CLASS_COLORS = [
    ("rgba(76, 120, 168, 0.3)", "#4C78A8"),
    ("rgba(245, 133, 24, 0.3)", "#F58518"),
    ("rgba(228, 87, 86, 0.3)", "#E45756"),
    ("rgba(114, 183, 178, 0.3)", "#72B7B2"),
    ("rgba(84, 162, 75, 0.3)", "#54A24B"),
    ("rgba(255, 215, 0, 0.3)", "#FFD700"),
]

# ---------------------------------------------------------------------------
# データ読み込み
# ---------------------------------------------------------------------------
profiles_data = load_json("student_profiles.json")

if profiles_data is None:
    st.warning("プロファイルデータが見つかりません。分析を実行してください。")
    st.stop()

classes: list[dict] = profiles_data.get("classes", [])
student_assignments: list[dict] = profiles_data.get("student_assignments", [])
optimal_k: int = profiles_data.get("optimal_k", 0)
bic_values: dict = profiles_data.get("bic_values", {})

if not classes or not student_assignments:
    st.info("プロファイルデータが不完全です。")
    st.stop()

# クラスIDからラベルへのマッピング
class_label_map = {c["class_id"]: c.get("label", f"タイプ {c['class_id']}") for c in classes}

# ---------------------------------------------------------------------------
# メインコンテンツ
# ---------------------------------------------------------------------------
st.header("個別診断プロファイル")
st.caption("潜在クラス分析に基づく生徒タイプと個別プロファイルを表示します。")

st.divider()

# ---------------------------------------------------------------------------
# 生徒セレクタ
# ---------------------------------------------------------------------------
student_ids = [s["student_id"] for s in student_assignments]
selected_student_id = st.selectbox(
    "生徒を選択",
    options=student_ids,
    index=0,
    help="プロファイルを表示する生徒を選んでください",
)

# 選択された生徒の情報
selected_student = next(
    (s for s in student_assignments if s["student_id"] == selected_student_id),
    None,
)

if selected_student is None:
    st.error("生徒データが見つかりません。")
    st.stop()

assigned_class_id = selected_student["class_id"]
probabilities = selected_student.get("probabilities", [])
assigned_class = next((c for c in classes if c["class_id"] == assigned_class_id), None)

# ---------------------------------------------------------------------------
# 2カラム: レーダー + 所属情報
# ---------------------------------------------------------------------------
col_radar, col_info = st.columns([1, 1])

with col_radar:
    st.subheader("教科別スコア")
    if assigned_class and "profile" in assigned_class:
        profile = assigned_class["profile"]
        # 教科スコアのみ抽出（attendance_rate 等を除外）
        subject_profile = {k: v for k, v in profile.items() if k in SUBJECT_LABELS}
        fill_c, line_c = _CLASS_COLORS[assigned_class_id % len(_CLASS_COLORS)]
        fig = render_skill_radar(
            subject_profile,
            title=f"{selected_student_id} — {class_label_map.get(assigned_class_id, '')}",
            fill_color=fill_c,
            line_color=line_c,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("プロファイルデータがありません。")

with col_info:
    st.subheader("クラス所属情報")

    # 所属クラス
    class_label = class_label_map.get(assigned_class_id, f"タイプ {assigned_class_id}")
    st.markdown(f"**所属タイプ:** {class_label}")

    if assigned_class:
        st.markdown(f"**説明:** {assigned_class.get('description', '—')}")
        size = assigned_class.get("size", "—")
        proportion = assigned_class.get("proportion", 0)
        st.markdown(f"**タイプ人数:** {size}人 ({proportion:.1%})")

        # 出席率があれば表示
        attendance = assigned_class.get("profile", {}).get("attendance_rate")
        if attendance is not None:
            st.markdown(f"**平均出席率:** {attendance:.0%}")

    # 所属確率バーチャート
    st.markdown("**所属確率分布:**")
    if probabilities:
        prob_labels = [class_label_map.get(i, f"タイプ {i}") for i in range(len(probabilities))]
        colors = [
            _CLASS_COLORS[i % len(_CLASS_COLORS)][1] for i in range(len(probabilities))
        ]

        fig_prob = go.Figure()
        fig_prob.add_trace(
            go.Bar(
                x=probabilities,
                y=prob_labels,
                orientation="h",
                marker=dict(color=colors),
                text=[f"{p:.1%}" for p in probabilities],
                textposition="auto",
            )
        )
        fig_prob.update_layout(
            xaxis=dict(
                title="確率",
                range=[0, 1],
                tickformat=".0%",
                gridcolor="rgba(255,255,255,0.1)",
            ),
            yaxis=dict(autorange="reversed"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=30),
            height=250,
            font=dict(color="#e0e0e0"),
        )
        st.plotly_chart(fig_prob, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# BIC エルボーチャート
# ---------------------------------------------------------------------------
st.subheader("モデル選択 (BIC エルボーチャート)")
st.caption("ベイズ情報量基準 (BIC) によるクラス数の最適化。値が最小となるクラス数を採用しています。")

if bic_values:
    ks = sorted(bic_values.keys(), key=lambda x: int(x))
    bic_vals = [bic_values[k] for k in ks]
    k_ints = [int(k) for k in ks]

    fig_bic = go.Figure()
    fig_bic.add_trace(
        go.Scatter(
            x=k_ints,
            y=bic_vals,
            mode="lines+markers",
            line=dict(color="#4C78A8", width=2),
            marker=dict(size=8, color="#4C78A8"),
            name="BIC",
        )
    )

    # 最適 K をマーク
    if optimal_k and str(optimal_k) in bic_values:
        fig_bic.add_trace(
            go.Scatter(
                x=[optimal_k],
                y=[bic_values[str(optimal_k)]],
                mode="markers",
                marker=dict(size=14, color="#E45756", symbol="star"),
                name=f"最適 K={optimal_k}",
            )
        )

    fig_bic.update_layout(
        xaxis=dict(title="クラス数 (K)", dtick=1, gridcolor="rgba(255,255,255,0.1)"),
        yaxis=dict(title="BIC", gridcolor="rgba(255,255,255,0.1)"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10),
        height=300,
        font=dict(color="#e0e0e0"),
        legend=dict(font=dict(color="#e0e0e0")),
    )
    st.plotly_chart(fig_bic, use_container_width=True)
else:
    st.info("BIC データがありません。")

# ---------------------------------------------------------------------------
# 全タイプ一覧
# ---------------------------------------------------------------------------
st.divider()
st.subheader("生徒タイプ一覧")

for cls in classes:
    cid = cls["class_id"]
    label = cls.get("label", f"タイプ {cid}")
    desc = cls.get("description", "")
    size = cls.get("size", 0)
    proportion = cls.get("proportion", 0)
    fill_c, line_c = _CLASS_COLORS[cid % len(_CLASS_COLORS)]

    with st.expander(f"{label} — {size}人 ({proportion:.1%})", expanded=False):
        st.write(desc)
        profile = cls.get("profile", {})
        subject_profile = {k: v for k, v in profile.items() if k in SUBJECT_LABELS}
        if subject_profile:
            fig = render_skill_radar(subject_profile, title=label, fill_color=fill_c, line_color=line_c)
            st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# 倫理的注意事項 (NFR-E3)
# ---------------------------------------------------------------------------
st.divider()
st.info(
    "**倫理的注意事項:** "
    "本プロファイルは観察されたパターンの記述であり、"
    "固定的な特性を表すものではありません。"
    "生徒の可能性を限定する目的で使用しないでください。"
)
