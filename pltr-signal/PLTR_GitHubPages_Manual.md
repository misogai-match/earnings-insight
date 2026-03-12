# PLTR LiveSignal — GitHub Pages 公開マニュアル

**最終更新: 2026-03-01 | v2.1.7**

---

## 概要

ClaudeでPLTR LiveSignalダッシュボード（HTML）を生成し、GitHub Pagesで公開する手順書。
四半期決算や気になるタイミングで随時更新する運用。

**公開URL:** `https://misogai-match.github.io/pltr-signal/PLTR_LiveSignal_v2.1.7_20260225.html`

---

## 全体フロー（所要時間: 約2分）

```
① Claudeで「PLTRシグナル」と入力
    ↓
② HTMLファイルをダウンロード
    ↓
③ GitHubにアップロード（ドラッグ&ドロップ）
    ↓
④ 自動でPages更新（GitHub Actionsが実行）
```

---

## 手順詳細

### ステップ①: Claudeでシグナル生成

1. Claude.aiを開く（PLTRプロジェクト内）
2. **「PLTRシグナル」** と入力
3. Claudeが以下を自動実行:
   - 最新株価・F&G Index・マーケット情報を取得
   - スコア計算・バリュエーション判定
   - JSX / HTML / PNG を生成（バージョン自動+1）
4. 生成された **HTMLファイル** をダウンロード

> ファイル名の形式: `PLTR_LiveSignal_vX.X.X_YYYYMMDD.html`

### ステップ②: GitHubにアップロード

1. GitHubにログイン → `pltr-signal` リポジトリを開く
   - URL: `https://github.com/misogai-match/pltr-signal`
2. **「Add file」** → **「Upload files」** をクリック
3. ダウンロードしたHTMLファイルをドラッグ&ドロップ
4. 下部の **「Commit changes」** をクリック

### ステップ③: 自動公開を確認

- commit後、GitHub Actionsが自動で起動（30秒〜1分）
- 上部タブの **「Actions」** で実行状況を確認可能（緑✓で成功）
- 公開ページにアクセスして表示を確認

---

## リポジトリ構成

```
pltr-signal/
├── .github/
│   └── workflows/
│       └── deploy-pages.yml    ← GitHub Actions設定（変更不要）
├── README.md
└── PLTR_LiveSignal_vX.X.X_YYYYMMDD.html   ← ダッシュボード本体
```

---

## 設定済み項目（初回セットアップ完了済）

以下は既に設定済み。通常の運用で変更する必要なし。

| 項目 | 設定値 |
|------|--------|
| リポジトリ | `misogai-match/pltr-signal`（Public） |
| Pages Source | GitHub Actions |
| Workflow | `.github/workflows/deploy-pages.yml` |
| トリガー | mainブランチへのpush |

---

## トラブルシューティング

### Pagesが更新されない
1. 「Actions」タブを確認 → 赤×ならworkflowエラー
2. Settings → Pages → Sourceが「GitHub Actions」になっているか確認

### 古いファイルが表示される
- ブラウザのキャッシュをクリア（Ctrl+Shift+R / Cmd+Shift+R）

### ファイル名を変えた場合
- URLも変わる: `https://misogai-match.github.io/pltr-signal/新ファイル名.html`
- 古いURLは404になる（履歴は残さない方針なので問題なし）

---

## 更新タイミングの目安

| タイミング | アクション |
|-----------|-----------|
| 四半期決算前（T-7日） | F&G・QoQ確定値でシグナル更新 |
| 四半期決算後（T+1日） | Actual入力 → 最終スコア確定 → 更新 |
| 相場急変時 | 必要に応じて随時更新 |

---

## 備考

- **完全自動化について:** 現時点のClaude.aiからGitHubへの直接pushは不可（ネットワーク制限）。将来Claude Code等で実現可能性あり。
- **履歴:** GitHubのcommit履歴に自動で残る。Pagesには常に最新版のみ表示。
- **費用:** GitHub PagesはPublicリポジトリなら無料。
