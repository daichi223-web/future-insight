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

360人 x 5教科 x 30設問のサンプルデータを `data/sample/` に生成。
データには検証用の「隠れたつながり」が植え込まれている。

### 2. 分析パイプライン実行

```bash
python scripts/run_pipeline.py
```

8つの分析モジュールを実行し、結果を `analysis/output/` にJSON出力。

| モジュール | 出力 | 内容 |
|-----------|------|------|
| item_analysis | item_analysis.json | CTT項目分析（難易度・識別力） |
| network | network_graph.json | 偏相関ネットワーク（つながりマップ） |
| association | patterns.json | アソシエーションルール（パターンカタログ） |
| student_types | student_profiles.json | 潜在クラス分析（生徒タイプ） |
| mutual_info | mutual_info.json | 相互情報量（非線形依存） |
| subject_analysis | subject_analysis.json | 教科別深掘り（DOK天井・観点別・誤概念） |
| cross_subject | cross_subject.json | 教科横断（前提チェーン・WOK・ボトルネック） |
| student_profiler | student_profiles_enhanced.json | 多次元プロファイル（IB LP・WOK・動機診断） |

### 3. ダッシュボード起動

```bash
streamlit run app/app.py
```

7つの画面:

**分析ビュー（4画面）**
1. **つながりマップ** - 教科間・設問間のネットワーク可視化
2. **パターンカタログ** - 発見されたパターン（Context-Problem-Solution形式）
3. **個別診断プロファイル** - 生徒別のスキルプロファイル
4. **テスト品質レポート** - 設問の品質分析

**ロール別ビュー（3画面）**
5. **学級担任ビュー** - クラスの生徒を全教科横断で把握
6. **教科担当ビュー** - 担当教科を設問レベルで深掘り（DOK・Bloom's・観点別・誤概念）
7. **学年主任ビュー** - 学年全体の傾向と教科横断パターンを俯瞰

## パラメータ設定

分析の閾値パラメータは `analysis/config.py` に集約。チューニング時はこのファイルのみ変更。

## ディレクトリ構造

```
discovery/
├── data/
│   ├── sample/          # 生成されたサンプルデータ（CSV）
│   └── schema/          # データ辞書、Q-matrix、カリキュラム、用語辞書
├── analysis/
│   ├── config.py        # 全パラメータ設定
│   ├── pipeline.py      # 分析オーケストレーター（8モジュール）
│   ├── item_analysis.py # CTT項目分析
│   ├── network.py       # 偏相関ネットワーク
│   ├── association.py   # アソシエーションルール
│   ├── student_types.py # 潜在クラス分析（GMM）
│   ├── mutual_info.py   # 相互情報量
│   ├── subject_analysis.py  # 教科別深掘り
│   ├── cross_subject.py     # 教科横断分析
│   ├── student_profiler.py  # 多次元プロファイル
│   └── output/          # 分析結果（JSON）
├── app/
│   ├── app.py           # Streamlitメイン
│   ├── pages/           # 7画面
│   └── components/      # UIコンポーネント（ネットワーク可視化・パターンカード・レーダー・用語解説）
├── scripts/
│   ├── generate_sample.py
│   └── run_pipeline.py
└── requirements.txt
```

## 理論的基盤

22学問領域にわたるディープリサーチに基づく。IB/TOK、Bloom's Taxonomy、Webb's DOK、
観点別評価、パターンランゲージ等の国際的フレームワークを統合。

主要手法:
- **Network Psychometrics** - 偏相関ネットワークで一般能力を除去した直接依存を検出
- **Association Rule Mining** - 教科横断の設問レベルルールを自動発見
- **Gaussian Mixture Model** - 隠れた生徒タイプの発見（LCA近似）
- **IB Learner Profile** - 6属性プロキシ（Balanced, Risk-taker, Reflective, Thinker等）
- **WOK Profile** - 「知る方法」（理性・言語・想像力）ごとの教科横断パフォーマンス
- **パターンランゲージ** - 発見を「コンテクスト-問題-解決」形式で命名
