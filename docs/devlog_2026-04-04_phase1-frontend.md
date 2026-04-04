# Devlog: Phase 1 フロントエンド実装

**日付**: 2026-04-04
**タスク**: 未来洞察支援アプリ Phase 1（フロントエンドHTML + モックデータ）

## 判断ログ

### 実装アプローチ
- 3並列エージェント（モックデータ、HTML+CSS、app.js）で初回実装
- エージェント間の調整不足により HTML が静的構造、app.js が動的レンダリング（`#app` に `buildShell()` で全生成）という不整合が発生
- **対応**: HTML を `<div id="app"></div>` のみに簡素化、CSS を app.js のクラス名に合わせて全面書き直し
- **教訓**: 並列エージェントには共通インターフェース仕様を明示的に渡すべき

### CLA index.json の修正
- 初期生成では 1990-2026 の 37 年分を index.json に記載したが、実データは 2020.json のみ
- **決定**: index.json を実データのある年のみ（2020）に縮小
- **理由**: 存在しない年を選択可能にするのは UX として不適切。Phase 3 で年次データ生成時に拡張する

### KNOWN_SOURCES の修正
- app.js が生成したソース名（NHK News, Reuters Japan 等）が latest.json の実ソース名（NHK, Google News 等）と不一致
- **対応**: app.js の KNOWN_SOURCES を実データに合わせて修正

## 検証結果

| 検証項目 | 結果 |
|---------|------|
| `node --check app.js` | PASS |
| latest.json 構文 | PASS |
| cla/index.json 構文 | PASS |
| cla/2020.json 構文 | PASS |
| scenarios.json 構文 | PASS |
| HTML/CSS/JS クラス名整合性 | PASS（Explore エージェントによる全数確認） |
| 全 element ID 参照整合性 | PASS |
| シナリオ signal ID 参照整合性 | PASS（14件全て latest.json に存在確認） |

## 制約

- **Google Drive パス**: ローカル HTTP サーバー起動が不安定。ブラウザ直接表示ではCORS制約あり
- **ビルドステップなし**: 仕様どおり静的 HTML + vanilla JS。テストフレームワーク未導入
- **Chart.js CDN依存**: オフライン動作不可

## 成果物

| ファイル | 行数 | 内容 |
|---------|------|------|
| docs/index.html | 14 | SPA シェル |
| docs/assets/app.js | 1136 | 全7タブ動的レンダリング |
| docs/assets/style.css | 1045 | レスポンシブデザイン |
| data/latest.json | 471 | モック記事31件 |
| data/cla/index.json | 4 | CLA年一覧 |
| data/cla/2020.json | 91 | CLA 2020年データ |
| data/scenarios/scenarios.json | 41 | シナリオ4象限 |

## 次フェーズへの申し送り

### Phase 2（GitHub リポジトリ作成）
- `docs/` を GitHub Pages ルートに設定
- `.gitignore` 作成（node_modules 等）
- data/ パスは `../data/` の相対パスで動作確認済み

### Phase 3（CLA 一括生成）
- `data/cla/2020.json` をテンプレートとして使用
- `data-generator` エージェント（haiku）でバッチ生成推奨
- 生成後 `index.json` の years 配列を更新すること
- 各年ファイルは `fields` に 7 分野 × 4 層が必須

### Phase 4（collect.js）
- `collect/` ディレクトリは空の状態（sources/, processors/）
- RSS ソース: Google News, Yahoo!ニュース, NHK, はてなブックマーク, Hacker News
- 論文: arXiv API（3秒 sleep 必須）
