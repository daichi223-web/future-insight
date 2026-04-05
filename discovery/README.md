# 教育データ発見エンジン

> 「見えないつながりを見えるようにする」

教科・テスト・時間の壁を超えて、教育データに隠れた「つながり」を発見し、
教員が理解・活用できる形で可視化するシステム。

## セットアップ

```bash
cd discovery
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 使い方

### 1. サンプルデータ生成

```bash
python scripts/generate_sample.py
```

500人 × 5教科 × 30設問のサンプルデータを `data/sample/` に生成。
データには検証用の「隠れたつながり」が植え込まれている。

### 2. 分析パイプライン実行

```bash
python scripts/run_pipeline.py
```

5つの分析モジュールを実行し、結果を `analysis/output/` にJSON出力。

| モジュール | 出力 | 内容 |
|-----------|------|------|
| item_analysis | item_analysis.json | CTT項目分析（難易度・識別力） |
| network | network_graph.json | 偏相関ネットワーク（つながりマップ） |
| association | patterns.json | アソシエーションルール（パターンカタログ） |
| student_types | student_profiles.json | 潜在クラス分析（生徒タイプ） |
| mutual_info | mutual_info.json | 相互情報量（非線形依存） |

### 3. ダッシュボード起動

```bash
streamlit run app/app.py
```

4つの画面:
1. **つながりマップ** — 教科間・設問間のネットワーク可視化
2. **パターンカタログ** — 発見されたパターン（Context-Problem-Solution形式）
3. **個別診断プロファイル** — 生徒別のスキルプロファイル
4. **テスト品質レポート** — 設問の品質分析

## ディレクトリ構造

```
discovery/
├── data/
│   ├── sample/          # 生成されたサンプルデータ（CSV）
│   └── schema/          # データ辞書、Q-matrix
├── analysis/
│   ├── pipeline.py      # 分析オーケストレータ
│   ├── item_analysis.py # CTT項目分析
│   ├── network.py       # 偏相関ネットワーク
│   ├── association.py   # アソシエーションルール
│   ├── student_types.py # 潜在クラス分析（GMM）
│   ├── mutual_info.py   # 相互情報量
│   └── output/          # 分析結果（JSON）
├── app/
│   ├── app.py           # Streamlitメイン
│   ├── pages/           # 4画面
│   └── components/      # 再利用可能UIコンポーネント
├── scripts/
│   ├── generate_sample.py
│   └── run_pipeline.py
└── requirements.txt
```

## 理論的基盤

本システムは22学問領域にわたるディープリサーチに基づく。
詳細は `docs/workplans/2026-04-05_discovery-engine-requirements.md` を参照。

主要手法:
- **Network Psychometrics** (偏相関ネットワーク) — 一般能力を除去した後のスキル間直接依存
- **Association Rule Mining** (Apriori) — 教科横断の設問レベルルール
- **Gaussian Mixture Model** (LCA近似) — 隠れた生徒タイプの発見
- **Mutual Information** — 相関では見えない非線形依存の検出
- **パターンランゲージ** — 発見を「コンテクスト-問題-解決」形式で命名
