# summary CSV カラム定義（v2 — 2026-03-13 更新）

## 識別情報
| カラム | 型 | 説明 | 例 |
|--------|-----|------|-----|
| ticker | text | ティッカー | NCLH |
| company | text | 会社名 | Norwegian Cruise Line Holdings |
| quarter | text | 決算期 | 2025Q4 |
| earnings_date | date | 発表日 | 2026-03-02 |
| sector | text | セクター | Cruise / Leisure |

## 実績 vs コンセンサス
| カラム | 型 | 説明 | 抽出例 |
|--------|-----|------|--------|
| eps_actual | float | Adjusted EPS（$） | 0.28 |
| eps_consensus | float | コンセンサスEPS（$） | 0.27 |
| eps_beat_pct | float | Beat率（%、負=Miss） | 3.7 |
| revenue_actual_M | float | 売上（$M） | 2244 |
| revenue_consensus_M | float | コンセンサス売上（$M） | 2340 |
| revenue_beat_pct | float | Beat率（%、負=Miss） | -4.1 |
| ebitda_actual_M | float | Adjusted EBITDA（$M） | 564 |
| ebitda_consensus_M | float | コンセンサスEBITDA（$M） | 556 |
| ebitda_beat_pct | float | Beat率（%、負=Miss） | 1.4 |

## 成長率（YoY）
| カラム | 型 | 説明 | 抽出例 |
|--------|-----|------|--------|
| eps_yoy_pct | float | EPS前年同期比（%） | 7.7 |
| revenue_yoy_pct | float | Revenue前年同期比（%） | 6.4 |
| ebitda_yoy_pct | float | EBITDA前年同期比（%） | 11.0 |

## マージン・キャッシュフロー
| カラム | 型 | 説明 | 抽出例 |
|--------|-----|------|--------|
| op_margin_pct | float | Operating Margin（%） | 8.3 |
| op_margin_chg_bps | int | 前年同期比変化（bps） | -190 |
| fcf_margin_pct | float | FCF Margin（%） | 1.0 |
| fcf_margin_chg_bps | int | 前年同期比変化（bps） | -640 |

## ガイダンス
| カラム | 型 | 説明 | 抽出例 |
|--------|-----|------|--------|
| guidance_eps | float | 次期FY EPS ガイダンス（$） | 2.38 |
| guidance_eps_vs_consensus_pct | float | vs コンセンサス（%、負=Miss） | -8.5 |
| guidance_ebitda_M | float | 次期FY EBITDA ガイダンス（$M） | 2950 |
| guidance_ebitda_vs_consensus_pct | float | vs コンセンサス（%、負=Miss） | -3.3 |
| guidance_direction | text | 上方修正 / 据置 / 下方修正 / 新規 | 下方修正 |

## 財務健全性
| カラム | 型 | 説明 | 抽出例 |
|--------|-----|------|--------|
| net_leverage | text | Net Debt / EBITDA | 5.3x |

## バリュエーション（v2 追加）
| カラム | 型 | 説明 | 抽出例 |
|--------|-----|------|--------|
| fwd_pe | float | 決算発表時点のForward P/E（NTM EPS基準） | 22.5 |
| ev_revenue | float | EV/Revenue（直近Q annualized、SaaS・高成長向け） | 12.3 |
| fcf_yield_pct | float | FCF Yield = Annualized FCF ÷ 時価総額 ×100（%） | 4.2 |

## 決算品質スコア（v2 追加）
| カラム | 型 | 説明 | 抽出例 |
|--------|-----|------|--------|
| quality_score | int | 決算品質の総合評価（1〜5） | 4 |

### quality_score 基準

| スコア | 判定 | 条件の目安 |
|--------|------|-----------|
| 5 | 文句なし | EPS & Rev 両方Beat + ガイダンス上方修正 + 成長加速 |
| 4 | 好決算 | EPS & Rev 両方Beat + ガイダンスBeat or In-line |
| 3 | 及第点 | EPS Beat + Rev ≈ In-line、ガイダンス据置 |
| 2 | やや弱い | EPS Beat だが Rev Miss、またはガイダンス下方修正 |
| 1 | 悪い | EPS & Rev Miss、またはガイダンス大幅下方修正 |

### 補正要素（±0.5 → 四捨五入）
- 成長率加速（前Q比でRev YoY上昇）: +0.5
- マージン改善 +200bps以上: +0.5
- FCF Margin 30%超: +0.5
- CEO交代・会計変更等の不確実性: −0.5
- Revenue Miss: −0.5

### 運用ルール
- スコアリングは決算処理完了後にClaudeが提案 → まっちさんが承認
- 主観が入るため、最終判断はまっちさん
- 同一銘柄のスコア推移も重要（改善傾向 / 悪化傾向）

## 定性タグ・評価
| カラム | 型 | 説明 | 抽出例 |
|--------|-----|------|--------|
| tags | text | セミコロン区切りのキーワード | CEO交代;ガイダンス撤回;コスト規律 |
| sentiment | text | Positive / Mixed / Negative | Mixed |
| stock_reaction_pct | float | 発表後の株価変動（%） | -7.3 |
| summary | text | 1〜2文の要約 | EPS小幅Beat... |

---

## 想定クエリ例

```
# 良い決算 × 割安を探す（Extreme Fear時の買い候補フィルタ）
quality_score >= 4 AND fwd_pe < 業種平均

# FCF Yieldが高い好決算銘柄
quality_score >= 4 ORDER BY fcf_yield_pct DESC

# EPS & Revenue 両方Beatの銘柄
eps_beat_pct > 0 AND revenue_beat_pct > 0

# ガイダンス上方修正
guidance_direction = "上方修正"

# マージン改善が顕著（+200bps以上）
op_margin_chg_bps >= 200

# 特定タグで検索
tags CONTAINS "CEO交代"

# 株価反応が良かった順
ORDER BY stock_reaction_pct DESC

# 決算品質スコアが高い順（買い候補の優先順位付け）
ORDER BY quality_score DESC, fcf_yield_pct DESC
```

---

## 変更履歴
| 日付 | 変更内容 |
|------|----------|
| 2026-03-06 | v1 初版作成（26カラム） |
| 2026-03-13 | v2 バリュエーション3列 + quality_score 追加（30カラム） |
