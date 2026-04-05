"""偏相関ネットワーク分析モジュール

スキルレベルの偏相関ネットワークを構築し、
教科横断的なブリッジノードやコミュニティを検出する。

Usage:
    python -m discovery.analysis.network [--data-dir ...] [--output-dir ...]
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import networkx as nx
from scipy import linalg

try:
    from community import community_louvain
except ImportError:
    community_louvain = None


# ── 定数 ────────────────────────────────────────────────

SUBJECTS = ["math", "physics", "chemistry", "english", "japanese"]

SUBJECT_COLORS = {
    "math": "#4C78A8",
    "physics": "#F58518",
    "chemistry": "#E45756",
    "english": "#72B7B2",
    "japanese": "#54A24B",
}

# Q-matrix に基づくスキル名（q_matrix.json と同期）
SKILL_NAMES = {
    "math": ["algebraic_manipulation", "geometric_reasoning", "statistical_thinking",
             "function_understanding", "word_problem_reading"],
    "physics": ["mechanics_concepts", "wave_understanding", "energy_conservation",
                "formula_application", "word_problem_reading"],
    "chemistry": ["stoichiometry", "periodic_table", "reaction_mechanisms",
                  "equilibrium_calculation", "word_problem_reading"],
    "english": ["grammar", "vocabulary", "reading_comprehension",
                "listening", "writing"],
    "japanese": ["kanji_knowledge", "grammar_classical", "reading_comprehension",
                 "essay_writing", "critical_reading"],
}

SKILL_LABELS_JA = {
    "math_algebraic_manipulation": "数学:代数操作",
    "math_geometric_reasoning": "数学:幾何推論",
    "math_statistical_thinking": "数学:統計的思考",
    "math_function_understanding": "数学:関数理解",
    "math_word_problem_reading": "数学:文章題読解",
    "physics_mechanics_concepts": "物理:力学概念",
    "physics_wave_understanding": "物理:波動理解",
    "physics_energy_conservation": "物理:エネルギー保存",
    "physics_formula_application": "物理:公式適用",
    "physics_word_problem_reading": "物理:文章題読解",
    "chemistry_stoichiometry": "化学:化学量論",
    "chemistry_periodic_table": "化学:周期表",
    "chemistry_reaction_mechanisms": "化学:反応機構",
    "chemistry_equilibrium_calculation": "化学:平衡計算",
    "chemistry_word_problem_reading": "化学:文章題読解",
    "english_grammar": "英語:文法",
    "english_vocabulary": "英語:語彙",
    "english_reading_comprehension": "英語:読解",
    "english_listening": "英語:リスニング",
    "english_writing": "英語:ライティング",
    "japanese_kanji_knowledge": "国語:漢字知識",
    "japanese_grammar_classical": "国語:古典文法",
    "japanese_reading_comprehension": "国語:読解",
    "japanese_essay_writing": "国語:小論文",
    "japanese_critical_reading": "国語:批評的読解",
}

# 設問番号→スキルインデックス
SKILL_RANGES = [(1, 6), (7, 12), (13, 18), (19, 24), (25, 30)]


# ── スキルスコア計算 ────────────────────────────────────

def compute_subject_scores(responses_df: pd.DataFrame) -> pd.DataFrame:
    """設問応答からスキルレベルスコア（正答率）を集計する。

    Returns:
        student_id をインデックスとし、各列がスキル名 (e.g. math_algebraic_manipulation)
        の DataFrame。値はスキルごとの正答率 (0-1)。
    """
    if responses_df.empty:
        return pd.DataFrame()

    # 設問番号を抽出
    responses_df = responses_df.copy()
    responses_df["q_num"] = (
        responses_df["item_id"]
        .str.extract(r"_q(\d+)$")[0]
        .astype(int)
    )

    records = []
    for _, row in responses_df.iterrows():
        subj = row["subject"]
        q_num = row["q_num"]

        # スキルインデックスを特定
        skill_idx = None
        for idx, (lo, hi) in enumerate(SKILL_RANGES):
            if lo <= q_num <= hi:
                skill_idx = idx
                break

        if skill_idx is None:
            continue

        skill_name = f"{subj}_{SKILL_NAMES[subj][skill_idx]}"
        records.append({
            "student_id": row["student_id"],
            "skill": skill_name,
            "correct": row["correct"],
        })

    if not records:
        return pd.DataFrame()

    rec_df = pd.DataFrame(records)
    score_matrix = (
        rec_df
        .groupby(["student_id", "skill"])["correct"]
        .mean()
        .unstack(fill_value=0.0)
    )

    return score_matrix


# ── 偏相関行列 ─────────────────────────────────────────

def compute_partial_correlations(score_matrix: pd.DataFrame,
                                  ridge: float = 0.01) -> pd.DataFrame:
    """偏相関行列を精度行列（相関行列の逆行列）から計算する。

    特異行列対策として正則化パラメータ ridge * I を加算する。
    """
    if score_matrix.empty or score_matrix.shape[1] < 2:
        return pd.DataFrame()

    corr = score_matrix.corr().values
    labels = score_matrix.columns.tolist()
    n = corr.shape[0]

    # 正則化
    corr_reg = corr + ridge * np.eye(n)

    try:
        precision = linalg.inv(corr_reg)
    except linalg.LinAlgError:
        print("  [ネットワーク] 警告: 逆行列計算に失敗、より強い正則化を適用", flush=True)
        precision = linalg.inv(corr_reg + 0.1 * np.eye(n))

    # 偏相関 = -P_ij / sqrt(P_ii * P_jj)
    diag = np.sqrt(np.diag(precision))
    diag[diag == 0] = 1e-10  # ゼロ除算回避
    partial = -precision / np.outer(diag, diag)
    np.fill_diagonal(partial, 1.0)

    return pd.DataFrame(partial, index=labels, columns=labels)


# ── ネットワーク構築 ───────────────────────────────────

def build_network(partial_corr: pd.DataFrame, labels: list,
                  threshold: float = 0.08) -> nx.Graph:
    """偏相関行列からネットワークグラフを構築する。

    閾値以上の偏相関をエッジとして追加し、
    ノード属性として教科・中心性指標を付与する。
    """
    G = nx.Graph()

    # ノード追加
    for label in labels:
        subj = label.split("_")[0]
        G.add_node(
            label,
            subject=subj,
            color=SUBJECT_COLORS.get(subj, "#999999"),
            label_ja=SKILL_LABELS_JA.get(label, label),
        )

    # エッジ追加
    n = len(labels)
    for i in range(n):
        for j in range(i + 1, n):
            w = partial_corr.iloc[i, j]
            if abs(w) >= threshold:
                src_subj = labels[i].split("_")[0]
                tgt_subj = labels[j].split("_")[0]
                G.add_edge(
                    labels[i], labels[j],
                    weight=round(float(w), 4),
                    is_cross_subject=(src_subj != tgt_subj),
                )

    # 中心性指標
    if G.number_of_nodes() > 0:
        degree_cent = nx.degree_centrality(G)
        between_cent = nx.betweenness_centrality(G, weight="weight")
        for node in G.nodes:
            G.nodes[node]["degree_centrality"] = round(degree_cent.get(node, 0.0), 4)
            G.nodes[node]["betweenness_centrality"] = round(between_cent.get(node, 0.0), 4)

    return G


# ── ブリッジ中心性 ─────────────────────────────────────

def compute_bridge_centrality(G: nx.Graph) -> list:
    """各ノードのブリッジスコアを計算する。

    ブリッジスコア = 媒介中心性 x 教科横断エッジ数
    """
    if G.number_of_nodes() == 0:
        return []

    between = nx.betweenness_centrality(G, weight="weight")
    bridge_nodes = []

    for node in G.nodes:
        node_subj = G.nodes[node].get("subject", "")
        cross_edges = 0
        connected_subjects = set()

        for neighbor in G.neighbors(node):
            neighbor_subj = G.nodes[neighbor].get("subject", "")
            if neighbor_subj != node_subj:
                cross_edges += 1
                connected_subjects.add(neighbor_subj)

        bridge_score = between.get(node, 0.0) * max(cross_edges, 1)
        G.nodes[node]["bridge_score"] = round(bridge_score, 4)

        if cross_edges > 0:
            bridge_nodes.append({
                "id": node,
                "bridge_score": round(bridge_score, 4),
                "betweenness": round(between.get(node, 0.0), 4),
                "cross_subject_edges": cross_edges,
                "connected_subjects": sorted(connected_subjects),
                "description": _describe_bridge(node, connected_subjects),
            })

    bridge_nodes.sort(key=lambda x: x["bridge_score"], reverse=True)
    return bridge_nodes


def _describe_bridge(node_id: str, connected_subjects: set) -> str:
    """ブリッジノードの説明文を生成する。"""
    label_ja = SKILL_LABELS_JA.get(node_id, node_id)
    subjects_ja = {
        "math": "数学", "physics": "物理", "chemistry": "化学",
        "english": "英語", "japanese": "国語",
    }
    connected_ja = [subjects_ja.get(s, s) for s in sorted(connected_subjects)]
    return f"{label_ja}は{', '.join(connected_ja)}と教科横断的に結合"


# ── コミュニティ検出 ───────────────────────────────────

def detect_communities(G: nx.Graph) -> list:
    """Louvain 法によるコミュニティ検出を行う。

    検出されたコミュニティと教科境界の一致度も評価する。
    """
    if G.number_of_nodes() == 0:
        return []

    if community_louvain is None:
        print("  [ネットワーク] 警告: python-louvain 未インストール、スキップ", flush=True)
        return []

    try:
        partition = community_louvain.best_partition(G, random_state=42)
    except Exception as e:
        print(f"  [ネットワーク] 警告: コミュニティ検出失敗: {e}", flush=True)
        return []

    # コミュニティ別に集約
    communities_map: dict[int, list] = {}
    for node, comm_id in partition.items():
        communities_map.setdefault(comm_id, []).append(node)

    result = []
    for comm_id, nodes in sorted(communities_map.items()):
        subject_counts: dict[str, int] = {}
        for node in nodes:
            subj = G.nodes[node].get("subject", "unknown")
            subject_counts[subj] = subject_counts.get(subj, 0) + 1

        dominant_subject = max(subject_counts, key=subject_counts.get)
        crosses = len(subject_counts) > 1

        result.append({
            "id": comm_id,
            "nodes": sorted(nodes),
            "size": len(nodes),
            "subject_composition": subject_counts,
            "dominant_subject": dominant_subject,
            "crosses_subjects": crosses,
        })

    return result


# ── メインエントリ ──────────────────────────────────────

def run_network_analysis(data_dir: Path, output_dir: Path) -> dict:
    """ネットワーク分析パイプラインを実行し、network_graph.json を出力する。"""
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("  [ネットワーク] データ読込中...", flush=True)
    responses_path = data_dir / "item_responses.csv"
    if not responses_path.exists():
        raise FileNotFoundError(f"item_responses.csv が見つかりません: {responses_path}")

    responses_df = pd.read_csv(responses_path)

    # スキルスコア計算
    print("  [ネットワーク] スキルスコア集計中...", flush=True)
    score_matrix = compute_subject_scores(responses_df)

    if score_matrix.empty:
        print("  [ネットワーク] 警告: スコアデータが空です", flush=True)
        return {}

    labels = score_matrix.columns.tolist()
    print(f"  [ネットワーク] {len(labels)}スキル x {len(score_matrix)}人", flush=True)

    # 偏相関行列
    print("  [ネットワーク] 偏相関行列計算中...", flush=True)
    partial_corr = compute_partial_correlations(score_matrix)

    if partial_corr.empty:
        print("  [ネットワーク] 警告: 偏相関計算に失敗", flush=True)
        return {}

    # ネットワーク構築
    print("  [ネットワーク] グラフ構築中...", flush=True)
    G = build_network(partial_corr, labels, threshold=0.08)
    print(f"  [ネットワーク] ノード: {G.number_of_nodes()}, エッジ: {G.number_of_edges()}", flush=True)

    # ブリッジ中心性
    print("  [ネットワーク] ブリッジ中心性計算中...", flush=True)
    bridge_nodes = compute_bridge_centrality(G)

    # コミュニティ検出
    print("  [ネットワーク] コミュニティ検出中...", flush=True)
    communities = detect_communities(G)

    # 出力構造
    nodes_out = []
    for node in sorted(G.nodes):
        data = G.nodes[node]
        nodes_out.append({
            "id": node,
            "label": data.get("label_ja", node),
            "subject": data.get("subject", ""),
            "color": data.get("color", "#999999"),
            "centrality": {
                "degree": data.get("degree_centrality", 0.0),
                "betweenness": data.get("betweenness_centrality", 0.0),
                "bridge_score": data.get("bridge_score", 0.0),
            },
        })

    edges_out = []
    for u, v, data in G.edges(data=True):
        edges_out.append({
            "source": u,
            "target": v,
            "weight": data.get("weight", 0.0),
            "is_cross_subject": data.get("is_cross_subject", False),
        })
    edges_out.sort(key=lambda e: abs(e["weight"]), reverse=True)

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "subject_network": {
            "nodes": nodes_out,
            "edges": edges_out,
        },
        "communities": communities,
        "bridge_nodes": bridge_nodes[:10],  # 上位10
    }

    output_path = output_dir / "network_graph.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    cross_edges = sum(1 for e in edges_out if e["is_cross_subject"])
    print(f"  [ネットワーク] 完了: {G.number_of_edges()}エッジ (うち教科横断: {cross_edges})", flush=True)
    print(f"  [ネットワーク] ブリッジノード: {len(bridge_nodes)}個", flush=True)
    print(f"  [ネットワーク] コミュニティ: {len(communities)}個", flush=True)
    print(f"  [ネットワーク] 出力: {output_path}", flush=True)

    return result


# ── CLI ─────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="偏相関ネットワーク分析")
    parser.add_argument("--data-dir", type=Path, default=Path("discovery/data/sample"))
    parser.add_argument("--output-dir", type=Path, default=Path("discovery/analysis/output"))
    args = parser.parse_args()

    run_network_analysis(args.data_dir, args.output_dir)
