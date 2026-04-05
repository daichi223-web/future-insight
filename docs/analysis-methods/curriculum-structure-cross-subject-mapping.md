# 日本の高等学校カリキュラム構造と教科横断マッピング

> 教育データ分析のための学習指導要領詳細分解・教科横断前提関係・観点別評価・ナレッジグラフ設計
> 作成日: 2026-04-05

---

## 目次

1. [高等学校カリキュラム構造（学習指導要領 2022年改訂）](#1-高等学校カリキュラム構造)
2. [教科横断コンセプトマッピング](#2-教科横断コンセプトマッピング)
3. [観点別評価（3観点）の詳細構造](#3-観点別評価の詳細構造)
4. [教育評価用語体系](#4-教育評価用語体系)
5. [教科横断前提チェーン（具体例）](#5-教科横断前提チェーン)
6. [ナレッジグラフデータ構造設計](#6-ナレッジグラフデータ構造設計)

---

## 1. 高等学校カリキュラム構造

### 1.1 数学（Mathematics）

2022年改訂（平成30年告示）で「数学C」が復活し、6科目体制に戻った。**必履修は数学Iのみ**。他は選択だが、履修順序に制約がある。

#### 科目間の依存関係（履修順序）

```
数学I（必履修）──→ 数学II ──→ 数学III
  │                   │
  └──→ 数学A          └──→ 数学B ──→ 数学C
      （並行可）         （並行可）    （並行可）
```

- 数学I → 数学II → 数学III: 連続的積み上げ（数Iなしに数IIは不可、数IIなしに数IIIは不可）
- 数学A: 数学Iと並行履修可能（ただし多くの学校では数学Iの後または同時）
- 数学B: 数学IIを履修後（または並行）
- 数学C: 数学IIを履修後（または並行）

#### 科目別 単元詳細

**数学I（2単位 / 必履修）**

| 単元 | 主要内容 | 中学からの接続 |
|------|---------|--------------|
| (1) 数と式 | 数の拡張（実数）、整式の加減乗除、因数分解、一次不等式、集合と命題 | 中3・式の展開と因数分解の発展 |
| (2) 図形と計量 | 三角比（sin, cos, tan）、正弦定理、余弦定理、三角形の面積 | 中3・三平方の定理の拡張 |
| (3) 二次関数 | 二次関数のグラフ、最大・最小、二次方程式・不等式 | 中3・二次方程式の視覚化 |
| (4) データの分析 | 四分位数、分散、標準偏差、相関係数、散布図、仮説検定の考え方 | 中1-3・統計の発展 |

**数学II（4単位 / 数学I履修後）**

| 単元 | 主要内容 |
|------|---------|
| (1) いろいろな式 | 二項定理、整式の除法、分数式、恒等式、等式・不等式の証明、複素数と二次方程式、高次方程式 |
| (2) 図形と方程式 | 直線の方程式、円の方程式、軌跡と領域 |
| (3) 指数関数・対数関数 | 指数の拡張、指数関数、対数、対数関数、常用対数 |
| (4) 三角関数 | 一般角と弧度法、三角関数のグラフ、加法定理、三角関数の合成 |
| (5) 微分・積分の考え | 微分係数、導関数、接線、関数の増減・極値、不定積分・定積分、面積 |

**数学III（3単位 / 数学II履修後 / 主に理系）**

| 単元 | 主要内容 |
|------|---------|
| (1) 極限 | 数列の極限、無限級数、関数の極限、連続性 |
| (2) 微分法 | 三角・指数・対数関数の導関数、合成関数・逆関数の微分、高次導関数、媒介変数表示 |
| (3) 積分法 | 不定積分（置換・部分積分）、定積分、面積・体積・曲線の長さ |

**数学A（2単位 / 数学Iと並行可能）**

| 単元 | 主要内容 |
|------|---------|
| (1) 図形の性質 | 三角形の性質（重心・内心・外心）、円の性質、空間図形 |
| (2) 場合の数と確率 | 順列・組合せ、確率の基本性質、条件付き確率、**期待値**（新課程で数Bから移動） |
| (3) 整数の性質 | 約数と倍数、ユークリッドの互除法、整数の性質の活用 |

**数学B（2単位 / 数学IIと並行可能）** ※内容(1)-(3)から選択履修

| 単元 | 主要内容 | 備考 |
|------|---------|------|
| (1) 数列 | 等差数列、等比数列、漸化式、数学的帰納法 | 多くの学校で必修的に選択 |
| (2) 統計的な推測 | 確率変数と確率分布、二項分布、正規分布、母集団と標本、推定、仮説検定 | **新課程で事実上必須化** |
| (3) 数学と社会生活 | 数学的モデリング | 選択する学校は少数 |

**数学C（2単位 / 数学IIと並行可能 / 新設復活）** ※内容(1)-(3)から選択履修

| 単元 | 主要内容 | 備考 |
|------|---------|------|
| (1) ベクトル | 平面・空間ベクトル、内積、位置ベクトル | **旧課程の数学Bから移動** |
| (2) 平面上の曲線と複素数平面 | 二次曲線、媒介変数表示、極座標、複素数平面 | **旧課程の数学IIIから移動** |
| (3) 数学的な表現の工夫 | 行列を含む離散数学的な表現 | 選択する学校は少数 |

#### 文系 vs 理系の典型的履修パターン

| 学年 | 文系 | 理系 |
|------|------|------|
| 高1 | 数学I + 数学A | 数学I + 数学A |
| 高2 | 数学II + 数学B | 数学II + 数学B + 数学C（ベクトル） |
| 高3 | — (数学なし、または演習) | 数学III + 数学C（複素数平面・曲線） |

共通テスト:
- 文系: 数学I・A + 数学II・B・C（数列 + 統計的推測 + ベクトルから3つ選択）
- 理系: 数学I・A + 数学II・B・C（数列 + ベクトル + 複素数平面が典型）

---

### 1.2 物理（Physics）

理科は「基礎科目（2単位）」と「発展科目（4単位）」の二層構造。**基礎科目は全員に3科目以上**の履修が求められ、発展科目は選択。

#### 物理基礎（2単位 / 基礎科目）

| 大項目 | 中項目 | 主要内容 |
|--------|--------|---------|
| (1) 物体の運動とエネルギー | ア 運動の表し方 | 速度、加速度、等加速度直線運動、v-tグラフ、落体の運動 |
| | イ 様々な力とその働き | 力の表し方、重力、弾性力、摩擦力、力のつりあい、作用反作用 |
| | ウ 力学的エネルギー | 運動エネルギー、位置エネルギー、力学的エネルギー保存 |
| (2) 熱 | ア 熱とエネルギー | 熱と温度、熱量、比熱、熱量保存、熱と仕事、不可逆変化 |
| (3) 波 | ア 波の性質 | 波の表し方、横波・縦波、重ね合わせ、定常波 |
| | イ 音 | 音の性質、音速、共鳴、うなり |
| (4) 電気 | ア 物質と電気抵抗 | 電流、電圧、抵抗、オームの法則、直列・並列回路 |
| | イ 電気の利用 | 電力、ジュール熱、交流の概要 |
| (5) 物理学が拓く世界 | | エネルギーとその変換、放射線 |

#### 物理（4単位 / 発展科目 / 物理基礎の後）

| 大項目 | 中項目 | 主要内容 |
|--------|--------|---------|
| (1) 様々な運動 | ア 平面内の運動 | 斜方投射、放物運動、相対運動 |
| | イ 運動量 | 運動量と力積、運動量保存則、反発係数 |
| | ウ 円運動と単振動 | 等速円運動、向心力、単振動、ばね振り子、単振り子 |
| | エ 万有引力 | ケプラーの法則、万有引力、万有引力による位置エネルギー |
| | オ 気体分子の運動 | 気体の法則、気体の分子運動論、気体の内部エネルギー、熱力学第一法則 |
| (2) 波 | ア 波の伝わり方 | ホイヘンスの原理、反射・屈折、回折・干渉 |
| | イ 音 | ドップラー効果 |
| | ウ 光 | 光の反射・屈折、全反射、レンズ、光の干渉・回折 |
| (3) 電気と磁気 | ア 電場 | クーロンの法則、電場、電位、コンデンサー |
| | イ 電流 | 電流と抵抗、キルヒホッフの法則、半導体 |
| | ウ 電流と磁場 | 磁場、電磁力、ローレンツ力 |
| | エ 電磁誘導と電磁波 | 電磁誘導、自己誘導、相互誘導、交流、電磁波 |
| (4) 原子 | ア 電子と光 | 光電効果、光の粒子性、X線、粒子の波動性 |
| | イ 原子と原子核 | 原子の構造、水素原子のスペクトル、放射線、核反応、素粒子 |

#### 物理の内部前提関係マップ

```
物理基礎:力学 ──→ 物理:力学（平面運動、運動量、円運動）
物理基礎:熱 ──→ 物理:気体分子運動論・熱力学
物理基礎:波 ──→ 物理:波（ホイヘンス、干渉、光）
物理基礎:電気 ──→ 物理:電気と磁気（電場、磁場、電磁誘導）
                    └──→ 物理:原子（電子と光、原子構造）
```

---

### 1.3 化学（Chemistry）

#### 化学基礎（2単位 / 基礎科目）

| 大項目 | 中項目 | 主要内容 |
|--------|--------|---------|
| (1) 化学と人間生活 | | 化学と日常生活、化学が拓く世界 |
| (2) 物質の構成 | ア 物質の探究 | 純物質と混合物、分離・精製、単体と化合物、元素 |
| | イ 物質の構成粒子 | 原子の構造、電子配置、イオンの生成、周期表 |
| | ウ 粒子の結合 | イオン結合、共有結合、金属結合、分子間力、結晶の分類 |
| (3) 物質の変化 | ア 物質量と化学反応式 | 原子量・分子量・式量、物質量（mol）、化学反応式と量的関係 |
| | イ 酸と塩基の反応 | 酸・塩基の定義、pH、中和反応、中和滴定 |
| | ウ 酸化還元反応 | 酸化・還元、酸化数、イオン化傾向、電池、電気分解 |

#### 化学（4単位 / 発展科目 / 化学基礎の後）

| 大項目 | 中項目 | 主要内容 |
|--------|--------|---------|
| (1) 物質の状態と平衡 | ア 物質の状態 | 状態変化、気体の法則、蒸気圧、溶解度 |
| | イ 溶液と平衡 | 希薄溶液の性質（沸点上昇・凝固点降下・浸透圧）、コロイド |
| | ウ 化学反応とエネルギー | **エンタルピー**（新課程で導入）、ヘスの法則、格子エネルギー |
| (2) 物質の変化と平衡 | ア 化学反応の速さ | 反応速度、活性化エネルギー、触媒 |
| | イ 化学平衡 | 平衡定数、ルシャトリエの原理、電離平衡、緩衝液、溶解度積 |
| (3) 無機物質 | ア 非金属元素 | ハロゲン、酸素・硫黄、窒素・リン、炭素・ケイ素、気体の製法 |
| | イ 金属元素 | アルカリ金属、2族元素、アルミニウム・亜鉛・スズ・鉛、遷移元素、錯イオン |
| | ウ 無機物質と人間生活 | セラミックス、金属材料 |
| (4) 有機化合物 | ア 有機化合物の構造 | 構造式、異性体、官能基 |
| | イ 炭化水素 | アルカン、アルケン、アルキン、芳香族炭化水素 |
| | ウ 官能基を含む化合物 | アルコール、アルデヒド、カルボン酸、エステル、芳香族化合物 |
| (5) 高分子化合物 | ア 天然高分子 | 糖類（単糖・二糖・多糖）、アミノ酸、タンパク質、核酸 |
| | イ 合成高分子 | 合成繊維、合成樹脂、ゴム |

#### 化学の内部前提関係マップ

```
化学基礎:物質の構成（原子・イオン・結合）
  ├──→ 化学:物質の状態と平衡
  ├──→ 化学:無機物質
  └──→ 化学:有機化合物
化学基礎:物質の変化（mol・反応式・酸塩基・酸化還元）
  ├──→ 化学:化学反応とエネルギー（エンタルピー）
  ├──→ 化学:反応速度と化学平衡
  └──→ 化学:高分子化合物
```

---

### 1.4 英語（English）

2022年改訂で「コミュニケーション英語」が「英語コミュニケーション」に、「英語表現」が「論理・表現」に再編。5領域（聞く・読む・話す[やり取り]・話す[発表]・書く）を統合的に扱う。

#### 科目構成

| 科目 | 単位数 | 必修/選択 | 主な目標 |
|------|--------|----------|---------|
| 英語コミュニケーションI | 3 | **必履修** | 5領域の総合的育成。日常的・社会的話題 |
| 英語コミュニケーションII | 4 | 選択 | 5領域の発展。社会的・学術的話題 |
| 英語コミュニケーションIII | 4 | 選択 | 5領域の高度化。専門的・抽象的話題 |
| 論理・表現I | 2 | 選択 | 発信力（話す・書く）の基礎。スピーチ、プレゼン |
| 論理・表現II | 2 | 選択 | 発信力の発展。ディベート、ディスカッション |
| 論理・表現III | 2 | 選択 | 発信力の高度化。学術的論述、批判的議論 |

#### スキル進行と語彙

- 語彙目標: 小学校600-700語 + 中学校1,600-1,800語 + 高校最大2,500語 = 卒業時4,000-5,000語
- 旧課程（1,800語）から大幅増加
- I → II → III は順次履修が原則（前段階の履修が前提）
- 論理・表現は英語コミュニケーションと並行可能

---

### 1.5 国語（Japanese Language）

#### 科目構成

| 科目 | 単位数 | 必修/選択 | 主な目標 |
|------|--------|----------|---------|
| 現代の国語 | 2 | **必履修** | 実社会における国語活動。論理的文章、実用的文章 |
| 言語文化 | 2 | **必履修** | 上代～近現代の言語文化。古文・漢文の入門、近現代文学 |
| 論理国語 | 4 | 選択 | 創造的・論理的思考力の育成。論説、評論、学術的文章 |
| 文学国語 | 4 | 選択 | 感性・情緒の育成。小説、詩歌、随筆 |
| 国語表現 | 4 | 選択 | 表現力の育成。スピーチ、レポート、小論文 |
| 古典探究 | 4 | 選択 | 古典の読解力深化。古文、漢文の精読・解釈 |

#### 実際の選択パターン

- 多くの学校: 高1で「現代の国語」+「言語文化」（必履修）、高2-3で「論理国語」+「古典探究」（大学受験対応）
- 「文学国語」と「論理国語」の同時履修は時間割上困難（ともに4単位）
- 文系は「論理国語」+「古典探究」、理系は「論理国語」のみが典型

---

### 1.6 学年別の典型的カリキュラム配置

| 学年 | 文系 | 理系 |
|------|------|------|
| 高1 | 数学I+A、英語CI+論理表現I、現代の国語+言語文化、物理基礎 or 化学基礎、生物基礎 or 地学基礎 | 同左 |
| 高2 | 数学II+B、英語CII+論理表現II、論理国語+古典探究、化学基礎 or 地学基礎、歴史/地理/公民 | 数学II+B+C、英語CII+論理表現II、物理（発展）+化学（発展）、論理国語 |
| 高3 | 英語CIII+論理表現III、論理国語+古典探究、歴史/地理/公民（選択）、数学演習(任意) | 数学III+C、英語CIII、物理+化学（演習）、論理国語 |

**重要**: 各学校でカリキュラムは異なるが、上記が進学校の典型パターン。この配置タイミングが教科横断の前提関係に直接影響する。

---

## 2. 教科横断コンセプトマッピング

### 2.1 数学→物理の前提関係（最重要）

数学と物理の前提関係は最も密接かつ体系的である。以下に単元レベルの対応を示す。

#### 数学I → 物理基礎

| 数学I単元 | 物理での利用場面 | 関係の強度 | 詳細 |
|-----------|----------------|-----------|------|
| 二次関数 | 等加速度運動（x = v₀t + ½at²）、放物運動の軌跡 | **必須前提** | 二次関数のグラフ理解なしに放物運動は理解不能 |
| 三角比（sin, cos, tan） | 力の分解、斜面上の運動、投射角の分解 | **必須前提** | 力の斜面方向・垂直方向への分解に三角比が不可欠 |
| 一次不等式 | 力のつりあい条件の判定 | 有用 | 条件の成立判定 |
| データの分析 | 実験データ処理 | 有用 | 標準偏差、相関の理解が実験評価に有用 |

#### 数学II → 物理

| 数学II単元 | 物理での利用場面 | 関係の強度 | 詳細 |
|-----------|----------------|-----------|------|
| 微分 | 速度 = 位置の微分、加速度 = 速度の微分 | **必須前提** | v = dx/dt, a = dv/dt という関係が物理の根幹 |
| 積分 | v-tグラフの面積 = 変位、力積の計算 | **必須前提** | x = ∫v dt の理解が運動分析に必須 |
| 三角関数 | 単振動 (x = A sin ωt)、交流 | **必須前提** | 弧度法・加法定理が波動・振動の記述に不可欠 |
| 指数・対数関数 | 減衰振動、放射性崩壊 | 有用 | N = N₀e^(-λt) の理解に指数関数が必要 |
| 図形と方程式 | 円運動の記述、電場・磁場の可視化 | 有用 | 座標系でのベクトル場の理解 |

#### 数学B/C → 物理

| 数学単元 | 物理での利用場面 | 関係の強度 | 詳細 |
|---------|----------------|-----------|------|
| ベクトル（数学C） | 力の合成・分解、電場・磁場、ローレンツ力 | **必須前提** | 物理量の大半がベクトル量。力学・電磁気の基盤 |
| 数列（数学B） | 等差・等比数列モデル、近似計算 | 有用 | 直接使用は限定的だが、概念理解に貢献 |
| 統計的な推測（数学B） | 実験誤差の評価、有意差検定 | 有用 | 探究活動での実験データ評価に直結 |

#### タイミング問題（致命的なカリキュラム上のミスマッチ）

**問題**: 物理で力の分解（三角比が必要）を学ぶ時期と、数学Iで三角比を学ぶ時期がずれる場合がある。同様に、物理で微分的概念（速度・加速度の関係）を扱うのが、数学IIで微分を正式に学ぶ前になることが多い。

**対策**: 多くの学校では、物理基礎で「v-tグラフの傾き = 加速度」「面積 = 変位」を直感的に教え、数学IIで微分を学んだ後に物理で正式に微積分を使う、という二段階アプローチをとる。

---

### 2.2 数学→化学の前提関係

| 数学単元 | 化学での利用場面 | 関係の強度 | 詳細 |
|---------|----------------|-----------|------|
| **対数関数（数学II）** | **pH = -log₁₀[H⁺]** の計算 | **必須前提** | 対数の理解なしにpH計算は不可能。化学基礎で学ぶが数学IIの対数が前提 |
| 指数関数（数学II） | 放射性崩壊 N=N₀(1/2)^(t/T)、反応速度 | 必須前提 | 半減期の概念に指数関数が不可欠 |
| 比例計算（数学I以前） | 物質量(mol)計算、化学量論 | 必須前提 | n = m/M, PV=nRT など比例関係が基盤 |
| 一次関数（中学→数学I） | 反応速度のグラフ解析 | 有用 | 濃度-時間グラフの傾き = 反応速度 |
| 二次方程式（数学I） | 弱酸・弱塩基の電離平衡計算 | 有用 | Ka = [H⁺][A⁻]/[HA] の二次方程式 |

#### タイミング問題

**問題**: 化学基礎でpHを学ぶのは通常高1後半～高2前半だが、対数関数は数学IIで高2に学ぶ。多くの場合、化学の方が先に来るため、「対数の意味がわからないままpHを暗記する」状態が生じる。

---

### 2.3 数学→他教科の前提関係

| 数学単元 | 他教科での利用 | 詳細 |
|---------|--------------|------|
| 統計（数学I/B） | 全教科の探究活動 | データの分析、仮説検定は探究学習の基盤スキル |
| 数列（数学B） | 生物: 個体群動態（指数増殖 → ロジスティック曲線） | 生物の個体数変化モデルに数列・指数関数が必要 |
| ベクトル（数学C） | 化学: 分子の構造（sp混成軌道の配置角度） | 分子の三次元構造理解にベクトル的思考が有用 |
| 確率（数学A） | 生物: 遺伝の法則（メンデル遺伝の分離比） | 遺伝確率の計算に順列・組合せが必要 |

### 2.4 国語・英語→全教科の前提関係

| 言語スキル | 全教科での利用 | 関係の性質 |
|-----------|--------------|-----------|
| 論理的読解（現代の国語/論理国語） | 数学・理科の文章題解釈、問題文の構造理解 | **暗黙の前提**: 問題文を正確に読めなければ全教科の成績に影響 |
| 論理的記述（現代の国語/国語表現） | 全教科の記述問題、実験レポート | 「思考・判断・表現」観点の評価に直結 |
| 英語読解（英語コミュニケーション） | 理系科目の英語論文・用語、入試の英語出題 | 大学進学後の学術活動の基盤 |
| 語彙力（国語/英語共通） | 全教科の専門用語理解 | 語彙力は全教科の理解度を規定する「ゲートウェイスキル」 |

### 2.5 物理⇔化学の相互前提関係

| 物理概念 | 化学での利用 | 方向 |
|---------|------------|------|
| エネルギー保存則 | エンタルピー、ヘスの法則 | 物理→化学 |
| 電場・クーロンの法則 | イオン結合のエネルギー、格子エネルギー | 物理→化学 |
| 波動（光の性質） | 原子のスペクトル、分子の色 | 物理→化学 |
| 気体の分子運動論 | 気体の法則（ボイル・シャルル） | 物理⇔化学（相互） |
| 電子の波動性 | 電子軌道、量子数 | 物理→化学 |

---

## 3. 観点別評価の詳細構造

### 3.1 三観点の定義と評価法

2022年度より高等学校でも観点別学習状況の評価が本格導入された。

#### (1) 知識・技能（Knowledge and Skills）

**定義**: 各教科の学習内容に関する個別の知識を身に付けているか。また、既有の知識と関連付けて理解しているか。技能についても同様。

**評価方法**:
- ペーパーテスト（用語の記憶、公式の適用、基本的な計算問題）
- 実技テスト（理科の実験操作、英語の音読・発話）
- 小テスト・確認テスト

**テスト問題の特徴**:
- 知識の再生・再認を問う（「～とは何か」「～の公式を書け」）
- 手続きの正確な実行を問う（「次の方程式を解け」「次の化学反応式を完成させよ」）
- 単一のスキルの適用を問う（基本～標準レベル）

**Bloom's Taxonomyとの対応**: Remember（記憶）、Understand（理解）、Apply（適用）の下位レベル

#### (2) 思考・判断・表現（Thinking, Judgment, Expression）

**定義**: 各教科の知識・技能を活用して課題を解決するために必要な思考力・判断力・表現力等を身に付けているか。

**評価方法**:
- ペーパーテスト（応用問題、複合問題、記述問題）
- レポート・小論文
- プレゼンテーション、ディスカッション
- パフォーマンス課題（実験の計画・考察、データの解釈）

**テスト問題の特徴**:
- 複数の知識・スキルの統合を要求（「～の場合、どのような結果が予想されるか理由を含めて説明せよ」）
- 未知の状況への適用を要求（初見の問題設定）
- 論理的な推論過程の記述を要求
- グラフ・図表の読解と解釈
- 日常場面・社会的場面への知識の適用

**Bloom's Taxonomyとの対応**: Apply（適用）の上位、Analyze（分析）、Evaluate（評価）、Create（創造）

#### (3) 主体的に学習に取り組む態度（Attitude toward Independent Learning）

**定義**: 知識・技能を獲得したり、思考力・判断力・表現力等を身に付けたりすることに向けた粘り強い取組を行おうとしているか。また、自らの学習を調整しようとしているか。

**評価方法**:
- ノート・ワークシートの記述分析
- 授業中の発言・参加態度の観察
- 振り返りシート
- ポートフォリオ
- 学習計画の策定と実行

**テスト問題では直接測定困難**: ペーパーテストだけでは評価できない。行動観察と自己省察の記録が主な評価材料。

**Bloom's Taxonomyとの対応**: 情意領域（Affective Domain）の全レベルに対応。Krathwohlの情意分類（Receiving → Responding → Valuing → Organization → Characterization）との対応が適切。

### 3.2 観点別評価からの評定への換算

```
各単元 → 観点別にA/B/C判定
  ↓
学期末 → 各観点の最頻値 or 数値化平均
  ↓
3観点 → 5段階評定に総括

換算例:
AAA → 5
AAB, ABA, BAA → 4
BBB, ABB, BAB, BBA → 3
BBC, BCB, CBB → 2
CCC, BCC, CBC, CCB → 1
```

### 3.3 Bloom's Taxonomy と 3観点の対応マッピング

```
Bloom's Taxonomy (認知領域)          日本の3観点
┌──────────────────┐
│ Create (創造)     │ ──→ 思考・判断・表現
│ Evaluate (評価)   │ ──→ 思考・判断・表現
│ Analyze (分析)    │ ──→ 思考・判断・表現
│ Apply (適用)      │ ──→ 知識・技能 / 思考・判断・表現（境界領域）
│ Understand (理解) │ ──→ 知識・技能
│ Remember (記憶)   │ ──→ 知識・技能
└──────────────────┘

Bloom's Taxonomy (情意領域)          日本の3観点
┌──────────────────────────┐
│ Characterization (人格化) │ ──→ 主体的に学習に取り組む態度
│ Organization (組織化)     │ ──→ 主体的に学習に取り組む態度
│ Valuing (価値づけ)        │ ──→ 主体的に学習に取り組む態度
│ Responding (反応)         │ ──→ 主体的に学習に取り組む態度
│ Receiving (受容)          │ ──→ 主体的に学習に取り組む態度
└──────────────────────────┘
```

**重要な注意**: 対応は厳密な1対1ではない。特に「Apply（適用）」レベルは、単純な公式適用なら「知識・技能」、未知の場面への適用なら「思考・判断・表現」と判定される。この境界の曖昧さがテスト問題のタグ付けを困難にする。

### 3.4 テスト問題の観点自動タグ付けの手がかり

テスト問題から観点を自動推定するためのヒューリスティクス:

| 特徴 | 推定される観点 | 信頼度 |
|------|-------------|--------|
| 「～とは何か」「～を答えよ」「計算せよ」 | 知識・技能 | 高 |
| 基本的な公式適用（単一ステップ） | 知識・技能 | 高 |
| 選択肢問題（単純再認） | 知識・技能 | 高 |
| 「理由を述べよ」「説明せよ」 | 思考・判断・表現 | 高 |
| 「予想せよ」「考察せよ」 | 思考・判断・表現 | 高 |
| 複数の知識を組み合わせる複合問題 | 思考・判断・表現 | 中 |
| グラフ・表の読解と解釈 | 思考・判断・表現 | 中 |
| 実験計画の立案 | 思考・判断・表現 | 高 |
| 日常場面への適用 | 思考・判断・表現 | 中 |
| ノート・振り返りの内容 | 主体的態度 | 高 |

**自動分類のアプローチ**:
1. 問題文のキーワード抽出（「説明せよ」「理由」「考察」→ 思考・判断・表現）
2. 解答形式の判定（選択 vs 記述 vs 論述）
3. 要求される認知操作の段数（単一 vs 複合）
4. 文科省「思考力・判断力・表現力を評価する問題作成手順」の7分類（Tr, Tc, Td, Ti, Ju, Ex, Ms）との照合

---

## 4. 教育評価用語体系

### 4.1 評価方法の分類

| 日本語用語 | 英語対応 | 定義 | 実施時期 |
|-----------|---------|------|---------|
| **到達度評価** | Criterion-referenced assessment | あらかじめ設定した到達基準に対する達成度を評価 | 常時 |
| **相対評価** | Norm-referenced assessment | 集団内での相対的位置（偏差値等）で評価 | 模試等 |
| **診断的評価** | Diagnostic assessment | 学習前の既有知識・準備状態を把握 | 単元開始前 |
| **形成的評価** | Formative assessment | 学習過程中の理解度を把握し指導に反映 | 学習過程中 |
| **総括的評価** | Summative assessment | 学習の最終的な達成度を判定 | 単元・学期末 |

### 4.2 評価技法

| 日本語用語 | 英語対応 | 内容 |
|-----------|---------|------|
| **ルーブリック** | Rubric | 尺度（段階）と記述語（descriptor）からなる評価基準表 |
| **パフォーマンス評価** | Performance assessment | レポート作成、発表、実験等の実際のパフォーマンスを評価 |
| **パフォーマンス課題** | Performance task | パフォーマンス評価のために設計された課題 |
| **ポートフォリオ評価** | Portfolio assessment | 学習成果物の蓄積と省察に基づく評価 |
| **自己評価** | Self-assessment | 生徒自身による学習の振り返り |
| **相互評価** | Peer assessment | 生徒同士による評価 |

### 4.3 日本固有の評価制度

| 用語 | 説明 |
|------|------|
| **指導要録** | 学校が法的に作成義務を持つ公簿。観点別学習状況と評定を記載 |
| **通知表（通信簿）** | 保護者への連絡文書。法的義務はないが慣行として発行。形式は学校裁量 |
| **調査書（内申書）** | 入学選抜に使用。観点別評価・評定・特別活動等を記載 |
| **観点別学習状況** | A/B/Cの3段階。2022年度から高校でも記載義務化 |
| **評定** | 5段階（5が最高）。観点別評価を総括して算出 |

---

## 5. 教科横断前提チェーン（具体例）

### 5.1 チェーン1: 二次関数 → 放物運動 → 反応速度

```
数学I: 二次関数
│ y = ax² + bx + c のグラフ理解
│ 頂点・軸・最大最小
│
├──→ 物理基礎: 等加速度運動
│     x = v₀t + ½at² （二次関数の物理的意味）
│     放物運動の軌跡 = 放物線
│
├──→ 物理: 斜方投射
│     x = v₀cosθ·t, y = v₀sinθ·t - ½gt²
│     二次関数 + 三角比の合成
│
└──→ 化学: 反応速度
      [A] = [A]₀ - kt （一次反応）
      [A] = 1/(1/[A]₀ + kt) （二次反応）
      濃度-時間グラフの形状判断に関数理解が必要
```

### 5.2 チェーン2: 三角比 → 力の分解 → 分子構造

```
数学I: 三角比（sin, cos, tan）
│ 直角三角形の辺の比
│ 正弦定理・余弦定理
│
├──→ 物理基礎: 力の分解
│     F_x = F cosθ, F_y = F sinθ
│     斜面上の運動: mg sinθ, mg cosθ
│
├──→ 物理: ベクトルの成分（数学Cのベクトルと融合）
│     力の合成・分解のベクトル表現
│     モーメントの計算: M = rF sinθ
│
└──→ 化学: 分子の構造
      結合角の理解（水分子 104.5°等）
      VSEPR理論での分子形状の幾何学的理解
```

### 5.3 チェーン3: ベクトル → 力学全般 → 電磁気学

```
数学C: ベクトル
│ 平面・空間ベクトルの演算
│ 内積 a·b = |a||b|cosθ
│ 位置ベクトル
│
├──→ 物理: 力学
│     力の合成・分解（ベクトルの加法）
│     運動量ベクトル p = mv
│     仕事 W = F·d = Fd cosθ（内積の物理的意味）
│
├──→ 物理: 電磁気学
│     電場ベクトル E
│     磁場ベクトル B
│     ローレンツ力 F = qv × B（外積の概念への拡張）
│
└──→ 化学: 結晶構造
      格子ベクトル、単位格子の記述
      面間距離の計算（X線結晶構造解析の基礎）
```

### 5.4 チェーン4: 微分 → 速度・加速度 → 反応速度論

```
数学II: 微分・積分の考え
│ 導関数 f'(x) = lim[h→0] (f(x+h)-f(x))/h
│ 関数の増減・極値
│
├──→ 物理: 速度と加速度
│     v = dx/dt（位置の時間微分 = 速度）
│     a = dv/dt = d²x/dt²（速度の時間微分 = 加速度）
│     F = ma（ニュートンの運動方程式）
│
├──→ 物理: 電磁気
│     V = -dΦ/dt（ファラデーの電磁誘導の法則）
│     電磁波の記述に微分方程式
│
└──→ 化学: 反応速度論
      v = -d[A]/dt（反応速度の微分的定義）
      速度定数kとアレニウスの式
      反応次数の決定（微分法）
```

### 5.5 チェーン5: 対数 → pH → 個体群動態

```
数学II: 指数関数・対数関数
│ a^x, log_a(x) の定義と性質
│ 常用対数 log₁₀
│ 対数法則: log(ab) = log a + log b
│
├──→ 化学基礎: pH計算
│     pH = -log₁₀[H⁺]
│     pOH, Kw = [H⁺][OH⁻] = 10⁻¹⁴
│     緩衝液のpH計算
│
├──→ 化学: 反応速度
│     アレニウスの式: k = Ae^(-Ea/RT)
│     ln k vs 1/T のグラフ（対数変換で直線化）
│
├──→ 生物: 個体群動態
│     指数増殖: N = N₀e^(rt)
│     対数目盛のグラフ解析
│
└──→ 物理: 放射性崩壊
      N = N₀(1/2)^(t/T₁/₂)
      半減期の対数計算
```

### 5.6 チェーン6: 読解力 → 全教科の文章題

```
国語: 論理的読解力
│ 現代の国語: 実用的文章の読解
│ 論理国語: 論理的文章の構造分析
│
├──→ 数学: 文章題の読解
│     問題条件の抽出、数学的モデリング
│     「何を求めるか」の正確な同定
│
├──→ 理科: 実験・考察問題
│     長文の実験手順の理解
│     グラフ・データからの結論導出
│     記述問題での論理的な文章構成
│
├──→ 英語: 長文読解
│     文構造の把握（母語の文法理解力が転移）
│     論理展開パターンの認識
│
└──→ 全教科: 共通テストの傾向
      長文化・資料読解重視の傾向
      「読む力」がすべての教科の得点の基盤
```

### 5.7 探究活動（総合的な探究の時間）としての統合ポイント

```
探究活動 = 全教科スキルの統合実践

必要スキル:
├── 国語: 論理的な論文・レポート執筆
├── 英語: 英語文献の読解
├── 数学: データ収集・統計分析（数学I: データの分析, 数学B: 統計的推測）
├── 理科: 仮説設定・実験計画・考察
└── 情報: ICT活用、プログラミングによるデータ処理

評価される3観点:
├── 知識・技能: 各教科の知識を探究に適用できるか
├── 思考・判断・表現: 課題設定・仮説構築・考察の質
└── 主体的態度: 粘り強さ、自己調整、振り返り
```

---

## 6. ナレッジグラフデータ構造設計

### 6.1 ノードタイプの定義

教育カリキュラムと評価をナレッジグラフとして表現するためのスキーマ設計。

```typescript
// === ノードタイプ ===

interface SubjectNode {
  id: string;                    // e.g., "math", "physics", "chemistry"
  type: "subject";
  name_ja: string;               // e.g., "数学"
  name_en: string;               // e.g., "Mathematics"
}

interface CourseNode {
  id: string;                    // e.g., "math_1", "physics_basic"
  type: "course";
  subject_id: string;            // 所属教科
  name_ja: string;               // e.g., "数学I", "物理基礎"
  name_en: string;
  credits: number;               // 単位数
  is_required: boolean;          // 必履修か
  typical_grade: number[];       // 典型的な履修学年 [1], [2], [1,2] 等
  track: "common" | "bunrei" | "rikei" | "both";
}

interface UnitNode {
  id: string;                    // e.g., "math1_quadratic_func"
  type: "unit";
  course_id: string;             // 所属科目
  name_ja: string;               // e.g., "二次関数"
  name_en: string;
  order_in_course: number;       // 科目内の順序
  typical_hours: number;         // 標準授業時数
}

interface ConceptNode {
  id: string;                    // e.g., "quadratic_graph"
  type: "concept";
  unit_id: string;               // 所属単元
  name_ja: string;               // e.g., "二次関数のグラフ"
  name_en: string;
  bloom_level: "remember" | "understand" | "apply" | "analyze" | "evaluate" | "create";
  kanten_primary: "knowledge_skill" | "thinking_judgment_expression" | "independent_attitude";
}

interface TestItemNode {
  id: string;                    // e.g., "test_2026_math1_q3"
  type: "test_item";
  test_id: string;               // 所属テスト
  course_id: string;             // 対応科目
  item_text: string;             // 問題文
  item_format: "multiple_choice" | "short_answer" | "essay" | "calculation";
  difficulty: number;            // 難易度 (0-1)
  kanten_tag: "knowledge_skill" | "thinking_judgment_expression";
  bloom_level: string;
  max_score: number;
}

interface StudentNode {
  id: string;
  type: "student";
  grade: number;                 // 学年
  track: "bunrei" | "rikei";    // 文理
  cohort_year: number;           // 入学年度
}
```

### 6.2 エッジタイプの定義

```typescript
// === エッジタイプ ===

interface PrerequisiteEdge {
  type: "prerequisite";          // A is prerequisite for B
  source: string;                // 前提となるノードID
  target: string;                // 前提を必要とするノードID
  strength: "required" | "recommended" | "helpful";
  cross_subject: boolean;        // 教科横断か
  description: string;           // e.g., "二次関数の理解が放物運動の理解に必須"
}

interface ContainsEdge {
  type: "contains";              // 階層関係
  source: string;                // 親ノード (subject → course → unit → concept)
  target: string;                // 子ノード
}

interface MeasuresEdge {
  type: "measures";              // テスト項目が概念を測定
  source: string;                // test_item ID
  target: string;                // concept ID
  kanten: "knowledge_skill" | "thinking_judgment_expression";
}

interface TransferEdge {
  type: "transfer";              // 学習転移の関係
  source: string;                // 転移元の概念
  target: string;                // 転移先の概念
  transfer_type: "positive" | "negative";  // 正の転移 or 負の転移
  mechanism: string;             // e.g., "同一のベクトル概念を異なる文脈で使用"
}

interface SameConceptEdge {
  type: "same_concept";          // 異なる教科で同一の概念
  source: string;                // 教科Aの概念
  target: string;                // 教科Bの概念
  similarity: number;            // 0-1 の類似度
  description: string;           // e.g., "数学のベクトルと物理のベクトルは同一概念だが文脈が異なる"
}

interface TemporalEdge {
  type: "temporal_sequence";     // 時間的な順序関係
  source: string;                // 先に学ぶノード
  target: string;                // 後に学ぶノード
  typical_gap_months: number;    // 典型的な時間間隔（月）
  gap_issue: boolean;            // タイミングの問題があるか
  issue_description?: string;    // e.g., "物理で力の分解を学ぶ前に数学Iの三角比が未履修の場合がある"
}
```

### 6.3 観点別評価のデータ構造

```typescript
// === 観点別評価のデータモデル ===

interface KantenAssessment {
  student_id: string;
  course_id: string;
  term: string;                  // "2026_1" (年度_学期)
  unit_id: string;

  // 3観点の評価
  knowledge_skill: "A" | "B" | "C";
  thinking_judgment_expression: "A" | "B" | "C";
  independent_attitude: "A" | "B" | "C";

  // 数値化 (A=3, B=2, C=1 として保持)
  knowledge_skill_numeric: number;
  thinking_judgment_expression_numeric: number;
  independent_attitude_numeric: number;

  // 評定 (学期末に3観点を総括)
  overall_rating?: 1 | 2 | 3 | 4 | 5;
}

interface ItemResponse {
  student_id: string;
  test_item_id: string;
  response: string;              // 生徒の回答（選択肢記号、記述テキスト等）
  score: number;                 // 得点
  max_score: number;
  is_correct: boolean;
  response_time_sec?: number;    // 回答時間（利用可能な場合）

  // 誤答分析用
  error_type?: string;           // "procedural_bug" | "misconception" | "careless" | "blank"
  misconception_id?: string;     // 対応する誤概念ID

  // 観点タグ
  kanten_tag: "knowledge_skill" | "thinking_judgment_expression";
  bloom_level: string;
}

interface CrossSubjectProfile {
  student_id: string;
  term: string;

  // 教科別の観点別スコア（数値化済み）
  subjects: {
    [course_id: string]: {
      knowledge_skill: number;
      thinking_judgment_expression: number;
      independent_attitude: number;
      overall_rating: number;
    }
  };

  // 教科横断的な集約指標
  cross_subject_metrics: {
    // 観点間の教科横断相関
    knowledge_consistency: number;    // 知識・技能の教科間一貫性
    thinking_consistency: number;     // 思考・判断・表現の教科間一貫性
    attitude_consistency: number;     // 主体的態度の教科間一貫性

    // 教科横断の前提チェーンの充足度
    prerequisite_chain_scores: {
      chain_id: string;              // e.g., "quadratic_to_projectile"
      source_mastery: number;        // 前提科目の習得度
      target_mastery: number;        // 依存科目の習得度
      transfer_efficiency: number;   // 転移効率 = target / source
    }[];
  };
}
```

### 6.4 グラフデータベースでの実装例（JSONL形式）

#### nodes.jsonl

```json
{"id":"math","type":"subject","name_ja":"数学","name_en":"Mathematics"}
{"id":"physics","type":"subject","name_ja":"物理","name_en":"Physics"}
{"id":"chemistry","type":"subject","name_ja":"化学","name_en":"Chemistry"}
{"id":"math_1","type":"course","subject_id":"math","name_ja":"数学I","credits":2,"is_required":true,"typical_grade":[1],"track":"common"}
{"id":"math_2","type":"course","subject_id":"math","name_ja":"数学II","credits":4,"is_required":false,"typical_grade":[2],"track":"both"}
{"id":"math_3","type":"course","subject_id":"math","name_ja":"数学III","credits":3,"is_required":false,"typical_grade":[3],"track":"rikei"}
{"id":"math_a","type":"course","subject_id":"math","name_ja":"数学A","credits":2,"is_required":false,"typical_grade":[1],"track":"common"}
{"id":"math_b","type":"course","subject_id":"math","name_ja":"数学B","credits":2,"is_required":false,"typical_grade":[2],"track":"both"}
{"id":"math_c","type":"course","subject_id":"math","name_ja":"数学C","credits":2,"is_required":false,"typical_grade":[2,3],"track":"both"}
{"id":"physics_basic","type":"course","subject_id":"physics","name_ja":"物理基礎","credits":2,"is_required":false,"typical_grade":[1],"track":"common"}
{"id":"physics_adv","type":"course","subject_id":"physics","name_ja":"物理","credits":4,"is_required":false,"typical_grade":[2,3],"track":"rikei"}
{"id":"chem_basic","type":"course","subject_id":"chemistry","name_ja":"化学基礎","credits":2,"is_required":false,"typical_grade":[1],"track":"common"}
{"id":"chem_adv","type":"course","subject_id":"chemistry","name_ja":"化学","credits":4,"is_required":false,"typical_grade":[2,3],"track":"rikei"}
{"id":"math1_quadratic","type":"unit","course_id":"math_1","name_ja":"二次関数","order_in_course":3,"typical_hours":20}
{"id":"math1_trigonometric","type":"unit","course_id":"math_1","name_ja":"図形と計量","order_in_course":2,"typical_hours":18}
{"id":"math2_differential","type":"unit","course_id":"math_2","name_ja":"微分・積分の考え","order_in_course":5,"typical_hours":25}
{"id":"math2_logarithm","type":"unit","course_id":"math_2","name_ja":"指数関数・対数関数","order_in_course":3,"typical_hours":18}
{"id":"mathc_vector","type":"unit","course_id":"math_c","name_ja":"ベクトル","order_in_course":1,"typical_hours":20}
{"id":"phys_basic_motion","type":"unit","course_id":"physics_basic","name_ja":"物体の運動とエネルギー","order_in_course":1,"typical_hours":30}
{"id":"phys_adv_projectile","type":"unit","course_id":"physics_adv","name_ja":"平面内の運動","order_in_course":1,"typical_hours":12}
{"id":"phys_adv_electromagnetic","type":"unit","course_id":"physics_adv","name_ja":"電気と磁気","order_in_course":3,"typical_hours":35}
{"id":"chem_basic_ph","type":"unit","course_id":"chem_basic","name_ja":"酸と塩基の反応","order_in_course":5,"typical_hours":12}
{"id":"chem_adv_rate","type":"unit","course_id":"chem_adv","name_ja":"化学反応の速さ","order_in_course":3,"typical_hours":10}
```

#### relationships.jsonl

```json
{"type":"prerequisite","source":"math_1","target":"math_2","strength":"required","cross_subject":false}
{"type":"prerequisite","source":"math_2","target":"math_3","strength":"required","cross_subject":false}
{"type":"prerequisite","source":"math1_quadratic","target":"phys_basic_motion","strength":"required","cross_subject":true,"description":"二次関数y=ax²+bx+cの理解が等加速度運動x=v₀t+½at²の理解に必須"}
{"type":"prerequisite","source":"math1_trigonometric","target":"phys_basic_motion","strength":"required","cross_subject":true,"description":"三角比(sin,cos)が力の分解に必須"}
{"type":"prerequisite","source":"math2_differential","target":"phys_adv_projectile","strength":"required","cross_subject":true,"description":"微分がv=dx/dt,a=dv/dtの関係理解に必須"}
{"type":"prerequisite","source":"mathc_vector","target":"phys_adv_electromagnetic","strength":"required","cross_subject":true,"description":"ベクトルが力の合成・電場・磁場の記述に必須"}
{"type":"prerequisite","source":"math2_logarithm","target":"chem_basic_ph","strength":"required","cross_subject":true,"description":"対数がpH=-log[H⁺]の計算に必須"}
{"type":"prerequisite","source":"math2_differential","target":"chem_adv_rate","strength":"recommended","cross_subject":true,"description":"微分がv=-d[A]/dtの反応速度の定義に有用"}
{"type":"same_concept","source":"mathc_vector","target":"phys_adv_electromagnetic","similarity":0.85,"description":"数学のベクトルと物理のベクトルは同一概念。物理では物理量としてのベクトルの意味解釈が加わる"}
{"type":"temporal_sequence","source":"math1_trigonometric","target":"phys_basic_motion","typical_gap_months":2,"gap_issue":true,"issue_description":"物理基礎の力の分解を学ぶ時期に数学Iの三角比が未履修の場合がある"}
{"type":"temporal_sequence","source":"math2_logarithm","target":"chem_basic_ph","typical_gap_months":-3,"gap_issue":true,"issue_description":"化学基礎のpHを学ぶ時期が数学IIの対数より前になることが多い。タイミングのミスマッチ"}
{"type":"transfer","source":"math1_quadratic","target":"phys_adv_projectile","transfer_type":"positive","mechanism":"二次関数のグラフ形状の理解が放物軌道の直感的理解を促進"}
{"type":"transfer","source":"chem_basic_ph","target":"math2_logarithm","transfer_type":"positive","mechanism":"化学でpHを先に学ぶことで対数の具体的応用例を持った状態で数学IIに入れる場合もある（逆方向の正の転移）"}
```

### 6.5 クエリ例

このナレッジグラフで可能になる分析クエリ:

1. **前提チェーン充足チェック**: 「生徒Xが物理の電磁気学で苦戦している。その前提となる数学Cのベクトルの観点別評価はどうか？」
2. **タイミングミスマッチ検出**: 「化学基礎のpH単元の成績が低い生徒群は、数学IIの対数関数の履修状況と関連があるか？」
3. **教科横断の橋渡し概念検出**: 「Bridge Centralityが高いconceptノードはどれか？」→ ベクトル、対数、二次関数が候補
4. **観点別の教科横断パターン**: 「思考・判断・表現がA/Bの教科とCの教科のパターンに、教科横断前提関係の未充足が関与しているか？」
5. **転移効率分析**: 「数学Iの二次関数でAの生徒は、物理基礎の力学でも高い成績を取る傾向があるか？転移効率はいくつか？」

---

## 参考資料・典拠

### 学習指導要領・公式文書
- [文部科学省 高等学校学習指導要領解説](https://www.mext.go.jp/a_menu/shotou/new-cs/1407074.htm)
- [文部科学省 高等学校学習指導要領（平成30年告示）全文PDF](https://www.mext.go.jp/content/20230120-mxt_kyoiku02-100002604_03.pdf)
- [文部科学省 高等学校学習指導要領解説 外国語編・英語編](https://www.mext.go.jp/content/1407073_09_1_2.pdf)
- [文部科学省 国語に関するQ&A](https://www.mext.go.jp/content/1422366_001.pdf)
- [文部科学省 学習評価に関するQ&A](https://www.mext.go.jp/a_menu/shotou/new-cs/qa/1299415.htm)

### 教科書出版社のカリキュラム分析
- [数研出版 新学習指導要領 数学の科目構成](https://www.chart.co.jp/subject/sugaku/suken_tsushin/91/91-1-2.pdf)
- [啓林館 新教育課程と学習指導要領 理科](https://www.shinko-keirin.co.jp/keirinkan/kou/science/pdf/science_sidou.pdf)
- [啓林館 新教育課程と学習指導要領 英語](https://www.shinko-keirin.co.jp/keirinkan/kou/kou_wp/wp-content/uploads/2025/02/english_sidou_r03.pdf)
- [数研出版 新学習指導要領 国語](https://www.chart.co.jp/subject/kokugo/kokugo_tsushinshi/33/33-2.pdf)
- [河合塾 化学基礎・化学 学習指導要領分析](https://www.kawai-juku.ac.jp/highschool/analysis/science/chemistry/)

### 教科横断・STEAM教育
- [J-STAGE: 数学との教科等横断的な学習を促す理科授業の試み](https://www.jstage.jst.go.jp/article/sjst/62/2/62_20082/_article/-char/ja/)
- [Brill: Trends in STEM/STEAM Education and Students' Perceptions in Japan](https://brill.com/view/journals/apse/7/1/article-p7_2.xml)
- [JapanGov: Combining STEAM Education with Playful Exploration](https://www.japan.go.jp/kizuna/2022/07/combining_steam_education.html)

### 観点別評価・学習評価
- [すらら: 高校の観点別評価を徹底解説](https://surala.jp/school/column/3627/)
- [NITS: 新学習指導要領に対応した学習評価（高等学校編）](https://www.nits.go.jp/materials/youryou/files/034_001.pdf)
- [NIER: 学習評価のQ&A](https://www.nier.go.jp/kaihatsu/pdf/gakushuhyouka_R010613-01.pdf)
- [文科省: 思考力・判断力・表現力を評価する問題作成手順](https://www.mext.go.jp/content/1412881_4_1.pdf)

### ナレッジグラフ・教育データ
- [JEDM: ACE: AI-Assisted Construction of Educational Knowledge Graphs with Prerequisite Relations](https://jedm.educationaldatamining.org/index.php/JEDM/article/view/737)
- [GitHub: learning-commons-org/knowledge-graph](https://github.com/learning-commons-org/knowledge-graph)
- [ArXiv: Design and Implementation of Curriculum System Based on Knowledge Graph](https://arxiv.org/pdf/2012.12522)

### Bloom's Taxonomy
- [熊本大学: ブルームのタキソノミー](https://www.gsis.kumamoto-u.ac.jp/opencourses/pf/2Block/04/04-1_text.html)
- [Wikipedia: Bloom's taxonomy](https://en.wikipedia.org/wiki/Bloom's_taxonomy)

---

Last Updated: 2026-04-05
