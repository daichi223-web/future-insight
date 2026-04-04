# Devlog: Phase 2-4 構造修正 + CLA生成 + collect.js

**日付**: 2026-04-04
**タスク**: 未来洞察支援アプリ Phase 2-4

## 判断ログ

### Phase 2: data/ パス移動
- GitHub Pages は `docs/` のみ配信するため、`data/` を `docs/data/` に移動
- app.js の DATA_PATHS を `../data/` → `./data/` に変更（4箇所）
- **決定理由**: 最小変更で GitHub Pages 対応を実現

### Phase 3: CLA 一括生成
- data-generator エージェント（haiku）を4バッチ並列で起動
- Batch 1: 2015-2017、Batch 2: 2018-2019、Batch 3: 2021-2022、Batch 4: 2023-2025
- **手戻り**: 2018, 2019 の一部エントリが50文字未満と短すぎたため手動で加筆修正
- **教訓**: haiku は layer3/layer4 のような抽象的分析で短文に逃げがち。テンプレートに最低文字数を明示すべきだった

### Phase 4: collect.js 実装
- fast-xml-parser v4.5.6 を使用
- **手戻り1**: `toNumber is not a function` エラー — XMLParser に `parseTagValue: false` を追加して解決
- **手戻り2**: `Entity expansion limit exceeded` エラー — `processEntities: false` で解決
- **決定**: Google Drive 上で npm install が極端に遅いため、ローカル /tmp にインストールしてからコピー。実行時は `NODE_PATH` 環境変数で対応
- **教訓**: Google Drive 上での node_modules は非推奨。将来的には git リポジトリ化して通常のローカルパスで開発すべき

## 検証結果

| 検証項目 | 結果 |
|---------|------|
| app.js 構文チェック | PASS |
| collect/*.js 全14ファイル構文チェック | PASS |
| CLA 10ファイル JSON構文 | PASS |
| CLA スキーマ検証（7分野×4層×10年=280エントリ） | PASS（修正後） |
| collect.js 実行テスト | PASS（351記事取得） |
| latest.json スキーマ検証 | PASS（エラー0） |

## collect.js 実行結果

| ソース | 取得件数 |
|--------|---------|
| Google News | 30 |
| Yahoo!ニュース | 24 |
| NHK | 260 |
| はてなブックマーク | 90（重複除去後18） |
| Hacker News | 26（重複除去後25） |
| arXiv | 20（重複除去後9） |
| **合計（重複除去後）** | **351** |

## 制約

- **Google Drive**: npm install が極端に遅い。NODE_PATH 経由での実行が必要
- **PESTLE分類**: キーワードベースのため精度に限界あり。将来的にLLMベース分類を検討
- **シグナルスコア**: ヒューリスティックベース。チューニングが必要

## 成果物

### Phase 2
| ファイル | 内容 |
|---------|------|
| docs/assets/app.js | DATA_PATHS 修正（4箇所） |
| .gitignore | 新規作成 |

### Phase 3
| ファイル | 内容 |
|---------|------|
| docs/data/cla/{2015..2025}.json | CLA 11年分（2020既存+10新規） |
| docs/data/cla/index.json | years 配列更新 |

### Phase 4
| ファイル | 内容 |
|---------|------|
| package.json | fast-xml-parser 依存 |
| collect/main.js | エントリポイント |
| collect/config.js | URL定数・設定 |
| collect/sources/*.js | 6ソースモジュール |
| collect/processors/*.js | 4処理モジュール |
| collect/utils/*.js | 2ユーティリティ |

## 次フェーズへの申し送り

### GitHub リポジトリ化
- git init → GitHub push → Pages 設定（branch: main, folder: /docs）
- node_modules は .gitignore に含まれている

### GitHub Actions 自動化
- `.github/workflows/collect.yml` でデイリー実行（JST 15:00）
- 実行後に latest.json を自動コミット

### PESTLE分類精度向上
- Claude API を使った分類の検討（コスト vs 精度のトレードオフ）

### シナリオデータ自動更新
- collect.js の出力を使ってシナリオの signals 参照を更新するスクリプト
