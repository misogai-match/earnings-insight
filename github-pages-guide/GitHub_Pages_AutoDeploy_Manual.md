# GitHub Pages 自動デプロイ マニュアル

**最終更新: 2026-03-01**

---

## GitHub Pagesとは？

GitHubのリポジトリにHTMLファイルを置くだけで、無料でWebページを公開できるサービス。
公開URL: `https://ユーザー名.github.io/リポジトリ名/ファイル名.html`

---

## 初回セットアップ（1回だけ）

### 1. リポジトリを作成

1. GitHub.com にログイン
2. 左上の緑の **「New」** ボタンをクリック
3. 以下を設定:
   - **Repository name:** 好きな名前（例: `my-site`）
   - **Public** を選択（Pagesで公開するため必須）
   - **「Add a README file」** にチェック
4. **「Create repository」** をクリック

### 2. GitHub Actions 設定ファイルを追加

1. リポジトリ画面で **「Add file」** → **「Create new file」**
2. ファイル名欄に `.github/workflows/deploy-pages.yml` と入力
   - スラッシュ `/` を打つとフォルダが自動で分かれる
3. 以下をコピペ:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: ["main"]

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v4
      - uses: actions/upload-pages-artifact@v3
        with:
          path: "."
      - id: deployment
        uses: actions/deploy-pages@v4
```

4. **「Commit changes」** → もう一度 **「Commit changes」** で保存

### 3. Pages のソースを変更

1. 上のタブから **「Settings」** をクリック
2. 左メニューの **「Pages」** をクリック
3. Source を **「GitHub Actions」** に変更

これでセットアップ完了！

---

## 日常の更新作業（毎回これだけ）

```
① HTMLファイルを用意（Claudeで生成、自分で作成、など）
    ↓
② GitHubのリポジトリを開く
    ↓
③ 「Add file」→「Upload files」→ ファイルをドラッグ&ドロップ
    ↓
④ 「Commit changes」をクリック
    ↓
⑤ 30秒〜1分で自動公開！
```

公開URL: `https://ユーザー名.github.io/リポジトリ名/ファイル名.html`

---

## 仕組み

```
ファイルをアップロード（push）
    ↓
GitHub Actionsが自動起動（deploy-pages.yml の設定）
    ↓
リポジトリの中身をそのままGitHub Pagesに公開
    ↓
URLでアクセス可能に
```

- **静的HTMLのみ対応**: サーバー側の処理は不要。HTML/CSS/JSがそのまま配信される
- **毎回上書き**: 同じファイル名でアップロードすれば自動で更新される
- **複数ファイルOK**: リポジトリ内の全HTMLが公開対象になる

---

## トラブルシューティング

| 症状 | 対処法 |
|------|--------|
| ページが更新されない | 「Actions」タブで実行状況を確認。赤×ならエラー |
| 404エラーが出る | URLのファイル名が正しいか確認。大文字小文字も区別される |
| 古い内容が表示される | ブラウザキャッシュをクリア（Ctrl+Shift+R / Cmd+Shift+R） |
| Actionsが動かない | Settings → Pages → Sourceが「GitHub Actions」になっているか確認 |

---

## 知っておくと便利なこと

- **費用**: Publicリポジトリなら完全無料
- **独自ドメイン**: Settings → Pages → Custom domain で設定可能
- **履歴**: GitHubのcommit履歴にアップロード記録が自動で残る
- **複数サイト**: リポジトリごとに別サイトを作れる（同じ手順を繰り返すだけ）
- **index.html**: このファイル名にすると `https://ユーザー名.github.io/リポジトリ名/` だけでアクセス可能

---

## 活用例

| 用途 | やり方 |
|------|--------|
| ダッシュボード公開 | Claudeで生成したHTMLをアップロード |
| プレゼン資料の共有 | HTMLスライドをアップロード → URLを共有 |
| ポートフォリオ | 自己紹介ページを公開 |
| 社内ツール | 簡易的なWebツールを公開 |
