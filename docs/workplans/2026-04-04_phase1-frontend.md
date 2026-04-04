# Phase 1: フロントエンドHTML完成（モックデータ）

**日付**: 2026-04-04
**仕様書**: spec-v1.0.md
**ステータス**: 完了

## 目的
未来洞察支援アプリのフロントエンドを完成させる。モックデータで全7タブが動作する状態。

## 対象ファイル
- `docs/index.html` — メインアプリ（SPA シェル）
- `docs/assets/style.css` — スタイル（1045行、レスポンシブ）
- `docs/assets/app.js` — アプリロジック（1136行、全7タブ動的レンダリング）
- `data/latest.json` — モックニュース＋論文データ（31記事）
- `data/cla/index.json` — CLA年一覧（実データのある年のみ）
- `data/cla/2020.json` — CLAサンプルデータ（7分野×4層）
- `data/scenarios/scenarios.json` — シナリオデータ（4象限）

## チェックリスト
- [x] モックデータJSON作成
- [x] 概要タブ（収集件数・カテゴリグラフ）
- [x] PESTLEニュースタブ（カード・フィルタ・検索・スコアソート）
- [x] 学術論文タブ（論文一覧・分野フィルタ・arXivリンク）
- [x] CLA分析タブ（年代別横スクロール・4層表示）
- [x] シナリオタブ（2×2マトリクス・自動命名）
- [x] ウィークシグナルタブ（HIGH/Medium/Lowカード）
- [x] 設定タブ（ソース確認・JSONエクスポート）
- [x] モバイル対応（レスポンシブ）
- [x] ライトテーマ

## 検証結果
| Gate | Status | 詳細 |
|------|--------|------|
| JS構文 | PASS | `node --check docs/assets/app.js` |
| JSON検証 | PASS | 4ファイル全て構文エラーなし |
| コード品質 | PASS | escapeHtml一貫使用、IIFE、イベント委譲 |
| スコープ | PASS | Phase 1 範囲内のみ |

## 方針
- 外部ライブラリ最小（Chart.js のみ CDN 使用）
- 静的HTML + vanilla JS
- GitHub Pages でそのまま動作する構成
