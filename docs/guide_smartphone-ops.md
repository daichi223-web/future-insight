# スマホからの操作ガイド

future-insight プロジェクトをスマートフォンから操作する3つの方法。

---

## 1. GitHub Issues — 修正・改善の指示

コードの修正や機能追加を指示すると、Claude Code が自動で実行して PR を作成する。

### 手順

1. GitHub アプリまたはブラウザで Issue を作成
   - URL: https://github.com/daichi223-web/future-insight/issues/new
2. タイトルに指示を書く
3. **ラベルに `claude` を付ける**（これがトリガー）
4. Submit

### 何が起きるか

- GitHub Actions が起動し、Claude Code がコードを読んで変更を実行
- 完了すると PR を作成
- Issue にコメントで完了通知

### 指示の書き方（例）

```
タイトル: PESTLE分類にセキュリティ関連キーワードを追加
本文:
サイバー攻撃、情報漏洩、ランサムウェアなどのキーワードを
Legal または Technological に追加してください。
```

```
タイトル: 概要タブにPESTLEカテゴリ別の記事数テーブルを追加
本文:
ドーナツチャートの下に、カテゴリ名と記事数の一覧テーブルを表示してください。
```

### 注意

- `claude` ラベルを付けないと実行されない
- 処理に数分〜最大30分かかる
- 結果は PR として作成されるので、マージ前に確認可能

---

## 2. Remote Trigger — データ収集の手動実行

通常は毎日 15:00 (JST) に自動実行されるが、今すぐデータを更新したいときに使う。

### 手順

**GitHub アプリの場合:**
1. リポジトリを開く
2. Actions タブ → **Daily Collect** を選択
3. **Run workflow** → **Run workflow** ボタン

**ブラウザの場合:**
1. https://github.com/daichi223-web/future-insight/actions/workflows/collect.yml を開く
2. 右上の **Run workflow** → **Run workflow**

### 何が起きるか

- 9つのソースからデータ収集（Google News, Yahoo, NHK, はてな, HN, arXiv, Zenn, Qiita, GitHub Trending）
- PESTLE-A 分類 + シグナルスコア算出
- `latest.json` と `sns-blogs.json` を自動コミット
- GitHub Pages に自動反映（数分後）

### 実行結果の確認

- Actions タブで実行ログを確認
- https://daichi223-web.github.io/future-insight/ でデータ更新を確認

---

## 3. claude.ai/code — 対話しながら開発

本格的な開発作業をスマホから対話形式で行う。

### 初回セットアップ

1. https://claude.ai/code にスマホブラウザでアクセス
2. Anthropic アカウントでログイン（なければ作成）
3. 「Connect to GitHub」または「GitHub リポジトリを接続」を選択
4. GitHub の OAuth 認証画面が出る → **Authorize** をタップ
5. リポジトリ一覧から `daichi223-web/future-insight` を選択
6. 対話画面が開く

### GitHub 認証がうまくいかない場合

- GitHub アプリで先にログインしておく
- ブラウザの「デスクトップ用サイトを表示」を使う（モバイル表示で崩れる場合）
- Safari / Chrome どちらでも動作する

### 2回目以降

- claude.ai/code にアクセスすると、前回のリポジトリが記憶されている
- 別リポジトリに切り替えたい場合は設定から変更

### できること

- コードの閲覧・編集・実行
- ファイルの作成・削除
- git 操作（コミット、プッシュ、ブランチ作成）
- テスト実行
- 複雑な変更の対話的な設計・実装

### 向いている作業

- 複数ステップの設計判断が必要な作業
- エラーの調査・デバッグ
- 新機能の対話的な開発

---

## 使い分け早見表

| やりたいこと | 方法 | 所要時間 |
|-------------|------|---------|
| 簡単な修正指示 | GitHub Issue + `claude` ラベル | 数分〜30分 |
| データを今すぐ更新 | Actions → Run workflow | 約1分 |
| じっくり開発 | claude.ai/code | リアルタイム |
| 結果を見るだけ | ブラウザでサイトを開く | 即時 |

---

## 必要なアプリ・アカウント

- **GitHub アプリ**（iOS / Android）— Issue 作成と Actions 実行が楽
- **ブラウザ** — 上記全てブラウザでも可能
- **Anthropic アカウント** — claude.ai/code 用

## URL 一覧

| 用途 | URL |
|------|-----|
| サイト | https://daichi223-web.github.io/future-insight/ |
| リポジトリ | https://github.com/daichi223-web/future-insight |
| Issue 作成 | https://github.com/daichi223-web/future-insight/issues/new |
| データ収集実行 | https://github.com/daichi223-web/future-insight/actions/workflows/collect.yml |
| 対話開発 | https://claude.ai/code |
