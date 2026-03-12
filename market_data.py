"""
market_data.py — Phase 2a+2b 統合マーケットデータ取得スクリプト
==============================================================
目的: 毎朝のNOTEレポート制作で使う数値データを自動取得し、
      Claudeに貼付できるMarkdown表として出力する。

使い方:
  1. コマンドプロンプトで以下を実行:
       python market_data.py
  2. 出力されたMarkdown表をコピーしてClaudeに貼付

必要なライブラリ:
  pip install yfinance fredapi pandas

作成: 2026/03/12
"""

import sys
from datetime import datetime, timedelta

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 設定（ここを編集）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# FRED APIキー（https://fred.stlouisfed.org/docs/api/api_key.html で取得）
FRED_API_KEY = "87f44968a8c6fc424e9c5ec8f5e2831c"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ライブラリの読み込み
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

try:
    import yfinance as yf
    import pandas as pd
    from fredapi import Fred
except ImportError as e:
    print(f"[エラー] ライブラリが見つかりません: {e}")
    print("以下のコマンドでインストールしてください:")
    print("  pip install yfinance fredapi pandas")
    sys.exit(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# yfinance ティッカー定義
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 主要指数（騰落率テーブル用）
INDEX_TICKERS = {
    "S&P500":      "^GSPC",
    "Dow":         "^DJI",
    "Nasdaq":      "^IXIC",
    "Russell2000":  "^RUT",
}

# 移動平均線テーブル用（指数 + VIX + 為替 + 原油）
MA_TICKERS = {
    "S&P500":  "^GSPC",
    "VIX":     "^VIX",
    "ドル円":   "JPY=X",
    "DXY":     "DX-Y.NYB",
    "原油":     "CL=F",
}

# FRED シリーズID
FRED_SERIES = {
    "10年債利回り":   "DGS10",
    "2年債利回り":    "DGS2",
    "10-2スプレッド": "T10Y2Y",
    "実質金利(10年)": "DFII10",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# データ取得関数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def fetch_yfinance_data(ticker_symbol: str, period: str = "1y") -> dict | None:
    """
    yfinanceから株価データを取得し、終値・前日比・移動平均線を計算する。
    
    戻り値の例:
    {
        "close": 5800.50,
        "prev_close": 5810.20,
        "change": -9.70,
        "change_pct": -0.17,
        "ma21": 5750.00,
        "ma50": 5700.00,
        "ma200": 5500.00,
        "vs_ma21": "上",
        "vs_ma50": "上",
        "vs_ma200": "上",
    }
    """
    try:
        # 1年分のデータを取得（200日MA計算に必要）
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period)
        
        if hist is None or hist.empty or len(hist) < 2:
            print(f"  [警告] {ticker_symbol}: データが不十分です")
            return None
        
        # 最新の終値と前日の終値
        close = hist["Close"].iloc[-1]
        prev_close = hist["Close"].iloc[-2]
        change = close - prev_close
        change_pct = (change / prev_close) * 100
        
        # 移動平均線の計算
        ma21 = hist["Close"].rolling(window=21).mean().iloc[-1] if len(hist) >= 21 else None
        ma50 = hist["Close"].rolling(window=50).mean().iloc[-1] if len(hist) >= 50 else None
        ma200 = hist["Close"].rolling(window=200).mean().iloc[-1] if len(hist) >= 200 else None
        
        # 終値とMAの位置関係
        def position(close_val, ma_val):
            if ma_val is None:
                return "—"
            return "上" if close_val >= ma_val else "下"
        
        return {
            "close": close,
            "prev_close": prev_close,
            "change": change,
            "change_pct": change_pct,
            "ma21": ma21,
            "ma50": ma50,
            "ma200": ma200,
            "vs_ma21": position(close, ma21),
            "vs_ma50": position(close, ma50),
            "vs_ma200": position(close, ma200),
        }
    
    except Exception as e:
        print(f"  [エラー] {ticker_symbol}: {e}")
        return None


def fetch_fred_data(fred: Fred, series_id: str, lookback_days: int = 10) -> dict | None:
    """
    FRED APIから金利データを取得する。
    直近の有効なデータポイントを返す（土日・祝日はデータなしのため）。
    
    戻り値の例:
    {
        "value": 4.28,
        "prev_value": 4.30,
        "change": -0.02,
        "date": "2026-03-11",
    }
    """
    try:
        # 直近のデータを取得（土日祝を考慮して10日分）
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        data = fred.get_series(series_id, start_date, end_date)
        
        # NaN（休場日）を除去
        data = data.dropna()
        
        if len(data) < 1:
            print(f"  [警告] FRED {series_id}: データが見つかりません")
            return None
        
        value = data.iloc[-1]
        prev_value = data.iloc[-2] if len(data) >= 2 else None
        change = (value - prev_value) if prev_value is not None else None
        date_str = data.index[-1].strftime("%Y-%m-%d")
        
        return {
            "value": value,
            "prev_value": prev_value,
            "change": change,
            "date": date_str,
        }
    
    except Exception as e:
        print(f"  [エラー] FRED {series_id}: {e}")
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# フォーマット関数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def fmt_num(val, decimals=2, comma=True):
    """数値をフォーマット。Noneの場合は '—' を返す"""
    if val is None:
        return "—"
    if comma:
        return f"{val:,.{decimals}f}"
    return f"{val:.{decimals}f}"


def fmt_change(val, decimals=2):
    """前日比をフォーマット（+/-符号付き）"""
    if val is None:
        return "—"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.{decimals}f}"


def fmt_pct(val, decimals=2):
    """変化率をフォーマット（+/-符号付き、%付き）"""
    if val is None:
        return "—"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.{decimals}f}%"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Markdown表の生成
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_markdown(index_data: dict, ma_data: dict, fred_data: dict, tnx_data: dict | None) -> str:
    """全データを統合してMarkdown表を生成する"""
    
    today = datetime.now().strftime("%Y/%m/%d")
    lines = []
    lines.append(f"## 市場データ（自動取得 {today}）")
    lines.append("")
    
    # ── 主要指数 ──
    lines.append("### 主要指数")
    lines.append("| 指標 | 終値 | 前日比 | 変化率 |")
    lines.append("|------|------|--------|--------|")
    
    for name, data in index_data.items():
        if data is None:
            lines.append(f"| {name} | 取得失敗 | — | — |")
        else:
            lines.append(
                f"| {name} "
                f"| {fmt_num(data['close'])} "
                f"| {fmt_change(data['change'])} "
                f"| {fmt_pct(data['change_pct'])} |"
            )
    
    # VIXも主要指数テーブルに追加
    vix_data = ma_data.get("VIX")
    if vix_data is None:
        lines.append("| VIX | 取得失敗 | — | — |")
    else:
        lines.append(
            f"| VIX "
            f"| {fmt_num(vix_data['close'])} "
            f"| {fmt_change(vix_data['change'])} "
            f"| {fmt_pct(vix_data['change_pct'])} |"
        )
    
    lines.append("")
    
    # ── 移動平均線 ──
    lines.append("### 移動平均線")
    lines.append("| 指標 | 終値 | 21日MA | 50日MA | 200日MA | vs 21MA | vs 50MA | vs 200MA |")
    lines.append("|------|------|--------|--------|---------|---------|---------|----------|")
    
    for name, data in ma_data.items():
        if data is None:
            lines.append(f"| {name} | 取得失敗 | — | — | — | — | — | — |")
        else:
            lines.append(
                f"| {name} "
                f"| {fmt_num(data['close'])} "
                f"| {fmt_num(data['ma21'])} "
                f"| {fmt_num(data['ma50'])} "
                f"| {fmt_num(data['ma200'])} "
                f"| {data['vs_ma21']} "
                f"| {data['vs_ma50']} "
                f"| {data['vs_ma200']} |"
            )
    
    # 10年債もMA表に追加（yfinanceの^TNXを使用）
    if tnx_data:
        lines.append(
            f"| 10年債 "
            f"| {fmt_num(tnx_data['close'])} "
            f"| {fmt_num(tnx_data['ma21'])} "
            f"| {fmt_num(tnx_data['ma50'])} "
            f"| {fmt_num(tnx_data['ma200'])} "
            f"| {tnx_data['vs_ma21']} "
            f"| {tnx_data['vs_ma50']} "
            f"| {tnx_data['vs_ma200']} |"
        )
    
    lines.append("")
    
    # ── 金利（FRED） ──
    lines.append("### 金利（FRED）")
    lines.append("| 指標 | 値 | 前日比 | 日付 |")
    lines.append("|------|-----|--------|------|")
    
    for name, data in fred_data.items():
        if data is None:
            lines.append(f"| {name} | 取得失敗 | — | — |")
        else:
            lines.append(
                f"| {name} "
                f"| {fmt_num(data['value'])} "
                f"| {fmt_change(data['change'])} "
                f"| {data['date']} |"
            )
    
    lines.append("")
    lines.append("---")
    lines.append("*自動取得 by market_data.py*")
    
    return "\n".join(lines)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# メイン処理
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    print("=" * 50)
    print("Phase 2: マーケットデータ自動取得")
    print("=" * 50)
    print()
    
    # ── Phase 2a: yfinance ──
    print("[Phase 2a] yfinanceでデータ取得中...")
    
    # 主要指数
    index_data = {}
    for name, ticker in INDEX_TICKERS.items():
        print(f"  取得中: {name} ({ticker})")
        index_data[name] = fetch_yfinance_data(ticker)
    
    # MA用ティッカー
    ma_data = {}
    for name, ticker in MA_TICKERS.items():
        print(f"  取得中: {name} ({ticker})")
        ma_data[name] = fetch_yfinance_data(ticker)
    
    # 10年債（移動平均線テーブル用）
    print(f"  取得中: 10年債 (^TNX)")
    tnx_data = fetch_yfinance_data("^TNX")
    
    print()
    
    # ── Phase 2b: FRED API ──
    print("[Phase 2b] FRED APIでデータ取得中...")
    
    fred_data = {}
    if FRED_API_KEY == "ここにAPIキーを貼り付けてください":
        print("  [スキップ] FRED APIキーが未設定です。")
        print("  → スクリプト冒頭の FRED_API_KEY を書き換えてください。")
        for name in FRED_SERIES:
            fred_data[name] = None
    else:
        try:
            fred = Fred(api_key=FRED_API_KEY)
            for name, series_id in FRED_SERIES.items():
                print(f"  取得中: {name} ({series_id})")
                fred_data[name] = fetch_fred_data(fred, series_id)
        except Exception as e:
            print(f"  [エラー] FRED API接続失敗: {e}")
            for name in FRED_SERIES:
                fred_data[name] = None
    
    print()
    
    # ── Markdown表の生成 ──
    print("[Phase 2c] Markdown表を生成中...")
    markdown = build_markdown(index_data, ma_data, fred_data, tnx_data)
    
    print()
    print("=" * 50)
    print("以下をコピーしてClaudeに貼り付けてください:")
    print("=" * 50)
    print()
    print(markdown)
    
    # ファイルにも保存（オプション）
    output_file = f"market_data_{datetime.now().strftime('%Y%m%d')}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown)
    print()
    print(f"[保存完了] {output_file}")


if __name__ == "__main__":
    main()
