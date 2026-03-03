# summary-2025Q4.csv カラム定義

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
```
