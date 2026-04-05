# Devlog: 教育データ発見エンジン 実装 Phase 0+1

**日付**: 2026-04-05
**タスク**: 要件定義に基づく発見エンジンMVP実装

---

## 実施内容

### 構築したもの

`discovery/` ディレクトリに23ファイルのPythonアプリケーションを新規構築。

#### サンプルデータ生成器
- 500人 × 5教科 × 30設問のリアルなサンプルデータ
- 4つの「隠れたつながり」を植え込み:
  1. 数学代数→物理力学/化学平衡の教科横断前提チェーン
  2. 5種の潜在的生徒タイプ（混合分布）
  3. 文章題読解力のボトルネックスキル（3教科に影響）
  4. 出欠低下→成績低下の時間パターン（離脱型）

#### 分析パイプライン（5モジュール）
| モジュール | 結果 |
|-----------|------|
| item_analysis | 150問中28問にフラグ（品質問題） |
| network | 25スキル、69エッジ（40教科横断）、3コミュニティ |
| association | 365ルール発見、192教科横断、15パターン出力 |
| student_types | BIC基準で5クラス最適（植え込み通り回収） |
| mutual_info | 非線形依存0件（線形設計のため想定通り） |

#### Streamlitダッシュボード（4画面）
1. つなが��マップ（pyvisネットワーク可視化）
2. パターンカタログ（Context-Problem-Solution カード）
3. 個別診断プロファイル（レーダーチャート + クラス所属）
4. テスト品質レポート（難易度×識別力散布図）

### 検証結果

| 検証項目 | 結果 |
|---------|------|
| サンプルデータ生成 | PASS（500人、75,000応答レコード） |
| 5分析モジュール個別実行 | PASS（全モジュール成功�� |
| 全Pythonファイル構文チェック | PASS |
| Streamlit起動（HTTP 200） | PASS |
| 植え込み信号の回収（GMM 5クラス） | PASS |
| 教���横断ルール発見 | PASS（192ルール） |

---

## 判断ログ

### Python-only（Rなし）の判断
Phase 0+1は概念実証。Python equivalents（sklearn GMM, mlxtend Apriori, networkx）で十分な結果が得られた。R (mirt, GDINA, bootnet)はPhase 2で導入。

### Aprioriメモリ問題の解決
- 初回: 50特徴（25スキル×2(mastered/unmastered)）でmin_support=0.05 → 10.7GiB要求でOOM
- 修正: 25特徴（mastered列のみ）+ min_support=0.15 → 正常動作、365ルール発見

### 個別モジュール実行の採用
パイプライン一括実行（pipeline.py）はscikit-learnのインポート時にMemoryErrorを起こした（Python 3.14 + Windows環境の制約の可能性）。個別実行では全モジュール成功。

---

## 成果物

| ファイル | 種別 |
|---------|------|
| `discovery/scripts/generate_sample.py` | データ生成器 |
| `discovery/analysis/item_analysis.py` | CTT項目分析 |
| `discovery/analysis/network.py` | 偏相関ネットワーク |
| `discovery/analysis/association.py` | アソシエーションルール |
| `discovery/analysis/student_types.py` | 潜在クラス分析 |
| `discovery/analysis/mutual_info.py` | 相互情報量 |
| `discovery/analysis/pipeline.py` | オーケストレータ |
| `discovery/scripts/run_pipeline.py` | CLIラッパー |
| `discovery/app/app.py` | Streamlitメイン |
| `discovery/app/pages/1_つながりマップ.py` | 画面1 |
| `discovery/app/pages/2_パターンカタログ.py` | 画面2 |
| `discovery/app/pages/3_個別診断プロファイル.py` | 画面3 |
| `discovery/app/pages/4_テスト品質レポート.py` | 画面4 |
| `discovery/app/components/network_viz.py` | ネットワーク可視化 |
| `discovery/app/components/pattern_card.py` | パターンカード |
| `discovery/app/components/skill_radar.py` | レーダーチャート |
| `discovery/data/schema/q_matrix.json` | Q-matrix定義 |
| `discovery/data/schema/data_dictionary.md` | データ辞書 |
| `discovery/requirements.txt` | Python依存 |
| `discovery/.gitignore` | Git除外 |
| `discovery/README.md` | 使い方 |

---

## 次フェーズへの申し送り

### 改善点
- パイプライン一括実行のメモリ問題を解決（Python 3.14互換性調査）
- ネットワーク可視化のブラウザ上での動作確認・微調整
- パターンカタログの命名をより教育的に洗練

### Phase 2に向けて
- R環境構築（mirt, GDINA, bootnet）
- 実データの入手可能性調査
- Q-matrix教員ワークショップの設計
- IRT分析（Rasch/2PL）の追加
- CDM（DINA）の追加
