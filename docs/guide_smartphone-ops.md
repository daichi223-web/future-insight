# スマホからの操作ガイド

future-insight プロジェクトをスマートフォンから操作する3つの方法。

---

## 1. GitHub Copilot Coding Agent — 修正・改善の指示

Issue に Copilot をアサインするだけで、コード変更と PR 作成を自動実行する。
API キー不要。GitHub Copilot の契約に含まれる。

### 初回設定（PC から1回だけ）

1. https://github.com/daichi223-web/future-insight/settings にアクセス
2. 左メニュー → **Copilot** → **Coding agent**
3. **Enable** にする

### スマホからの使い方

1. GitHub アプリまたはブラウザで Issue を作成
   - URL: https://github.com/daichi223-web/future-insight/issues/new
2. タイトルに指示を書く
3. **Assignees に `copilot` を追加**（これがトリガー）
4. Submit

### 何が起きるか

- Copilot がコードを読んで変更を実装
- 新しいブランチで PR を自動作成
- Issue にリンクされる

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

- Assignees に `copilot` を付けないと実行されない
- 処理に数分かかる
- 結果は PR として作成されるので、マージ前に確認可能
- PR のコメントで追加指示もできる

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

### 使い方

1. https://claude.ai/code にスマホブラウザでアクセス
2. Anthropic アカウントでログイン（なければ作成）
3. 対話入力欄が表示される
4. 以下のように入力して作業開始:

```
https://github.com/daichi223-web/future-insight のリポジトリで作業して。
〇〇を修正してください。
```

GitHub のリポジトリ URL を伝えるだけで、Claude Code が自動でクローンして作業を開始する。

### Tips

- 初回はリポジトリ URL を必ず伝える
- 2回目以降も URL を添えると確実
- 変更後は「コミットしてプッシュして」と指示すればデプロイまで完了する
- Safari / Chrome どちらでも動作する

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
| 簡単な修正指示 | GitHub Issue + Copilot アサイン | 数分 |
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
