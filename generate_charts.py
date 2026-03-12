"""
generate_charts.py — Phase 2e チャート画像自動生成
==================================================
目的: Yahoo Financeスクショ6〜8枚を、matplotlib自動生成に置換する。
      market_data.py（数値取得）と併用し、毎朝の作業を大幅削減。

使い方:
  1. コマンドプロンプトで以下を実行:
       cd C:\\GitHub
       python generate_charts.py
  2. C:\\GitHub\\charts\\ に日付付きPNGが6枚生成される
  3. GitHub Pagesにpush → NOTEに永続URLで貼付

必要なライブラリ:
  pip install yfinance matplotlib pandas

作成: 2026/03/12
バージョン: v3（Yahoo Finance桁数完全準拠 + レイアウト修正）

桁数設定（Yahoo Finance左上ヘッダーに合わせる）:
  S&P 500:    2桁 (6,775.80)     Y軸: 2桁
  VIX:        2桁 (24.23)        Y軸: 2桁
  10Y Yield:  4桁 (4.2080)       Y軸: 2桁
  USD/JPY:    4桁 (158.9830)     Y軸: 2桁
  DXY:        3桁 (99.255)       Y軸: 1桁
  WTI:        2桁 (91.55)        Y軸: 2桁
"""

import sys
from datetime import datetime, timedelta

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 設定
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OUTPUT_DIR = r"C:\GitHub\charts"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ライブラリ読み込み
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

try:
    import yfinance as yf
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import matplotlib.ticker as mticker
    import pandas as pd
    import os
except ImportError as e:
    print(f"[エラー] ライブラリが見つかりません: {e}")
    print("  pip install yfinance matplotlib pandas")
    sys.exit(1)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# フォント設定
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def setup_font():
    import platform
    if platform.system() == 'Windows':
        for font in ['Meiryo', 'MS Gothic', 'Yu Gothic']:
            try:
                matplotlib.rc('font', family=font)
                return
            except Exception:
                continue

setup_font()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ホワイトテーマ配色
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

THEME = {
    "bg": '#ffffff', "text": '#1a1a1a', "sub_text": '#666666',
    "grid": '#e0e0e0', "spine": '#cccccc',
    "price_line": '#1a73e8', "price_fill": '#1a73e8',
    "up": '#0d7c3f', "down": '#d93025',
    "ma": {21: '#e8710a', 50: '#d93025', 200: '#0d7c3f'},
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# チャート定義（全6枚）
# y_decimals:      ヘッダー終値・MA凡例の小数桁数（Yahoo準拠）
# y_axis_decimals: Y軸目盛りの小数桁数（見やすさ優先）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CHART_CONFIGS = [
    {
        "ticker_symbol": "^GSPC", "name": "S&P 500",
        "filename_prefix": "SP500", "period": "1y",
        "ma_windows": [21, 50, 200],
        "y_format": "comma", "y_decimals": 2, "y_axis_decimals": 2,
    },
    {
        "ticker_symbol": "^VIX", "name": "VIX",
        "filename_prefix": "VIX", "period": "3mo",
        "ma_windows": [21, 50, 200],
        "y_format": "plain", "y_decimals": 2, "y_axis_decimals": 2,
    },
    {
        "ticker_symbol": "^TNX", "name": "10Y Treasury Yield",
        "filename_prefix": "10Y_Yield", "period": "1y",
        "ma_windows": [21, 50, 200],
        "y_format": "plain", "y_decimals": 4, "y_axis_decimals": 2,
    },
    {
        "ticker_symbol": "JPY=X", "name": "USD/JPY",
        "filename_prefix": "USDJPY", "period": "1y",
        "ma_windows": [21, 50, 200],
        "y_format": "plain", "y_decimals": 4, "y_axis_decimals": 2,
    },
    {
        "ticker_symbol": "DX-Y.NYB", "name": "DXY (Dollar Index)",
        "filename_prefix": "DXY", "period": "1y",
        "ma_windows": [21, 50, 200],
        "y_format": "plain", "y_decimals": 3, "y_axis_decimals": 1,
    },
    {
        "ticker_symbol": "CL=F", "name": "WTI Crude Oil",
        "filename_prefix": "WTI", "period": "1y",
        "ma_windows": [21, 50, 200],
        "y_format": "plain", "y_decimals": 2, "y_axis_decimals": 2,
    },
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# データ取得
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def fetch_chart_data(ticker_symbol, period="1y", ma_windows=[21, 50, 200]):
    period_days = {"3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
    display_days = period_days.get(period, 365)
    max_ma = max(ma_windows) if ma_windows else 0
    total_days = display_days + max_ma + 30
    end_date = datetime.now()
    start_date = end_date - timedelta(days=total_days)
    
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(start=start_date, end=end_date)
        if hist is None or hist.empty or len(hist) < max_ma + 10:
            print(f"  [警告] {ticker_symbol}: データ不十分")
            return None
        for w in ma_windows:
            hist[f"MA{w}"] = hist["Close"].rolling(window=w).mean()
        cutoff = end_date - timedelta(days=display_days)
        display_df = hist[hist.index >= pd.Timestamp(cutoff, tz=hist.index.tz)]
        if display_df.empty:
            return None
        return display_df
    except Exception as e:
        print(f"  [エラー] {ticker_symbol}: {e}")
        return None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# チャート描画
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_chart(display_df, name, filename_prefix, period="1y",
                    ma_windows=[21, 50, 200], y_format="comma",
                    y_decimals=2, y_axis_decimals=2, output_dir=OUTPUT_DIR):
    t = THEME
    hd = display_df
    
    latest_close = hd["Close"].iloc[-1]
    prev_close = hd["Close"].iloc[-2] if len(hd) >= 2 else latest_close
    change = latest_close - prev_close
    change_pct = (change / prev_close) * 100
    latest_date = hd.index[-1].strftime("%Y/%m/%d")
    
    ma_values = {}
    for w in ma_windows:
        val = hd[f"MA{w}"].iloc[-1]
        ma_values[w] = val if pd.notna(val) else None
    
    def fmt(val):
        if y_format == "comma":
            return f"{val:,.{y_decimals}f}"
        return f"{val:.{y_decimals}f}"
    
    # ━━━ プロット ━━━
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.set_facecolor(t["bg"])
    ax.set_facecolor(t["bg"])
    
    # 終値ライン
    ax.plot(hd.index, hd["Close"], color=t["price_line"], linewidth=1.8, zorder=5)
    ax.fill_between(hd.index, hd["Close"], hd["Close"].min() * 0.995,
                     alpha=0.06, color=t["price_fill"], zorder=1)
    
    # 移動平均線
    ma_label_text = {21: '21d', 50: '50d', 200: '200d'}
    for w in ma_windows:
        col = f"MA{w}"
        if hd[col].notna().any():
            ax.plot(hd.index, hd[col], color=t["ma"].get(w, '#888'),
                    linewidth=1.0, alpha=0.85, zorder=4)
    
    # ── ヘッダー（左上） ──
    sign = "+" if change >= 0 else ""
    c_color = t["up"] if change >= 0 else t["down"]
    close_str = fmt(latest_close)
    change_str = f"{sign}{fmt(change)}"
    pct_str = f"({sign}{change_pct:.2f}%)"
    
    ax.text(0.01, 1.14, name, transform=ax.transAxes,
            fontsize=15, fontweight='bold', color=t["text"], va='top')
    ax.text(0.01, 1.07, close_str, transform=ax.transAxes,
            fontsize=24, fontweight='bold', color=t["text"], va='top')
    offset = 0.02 + len(close_str) * 0.018
    ax.text(offset + 0.04, 1.07, f"{change_str}  {pct_str}",
            transform=ax.transAxes, fontsize=13, color=c_color, va='top')
    ax.text(0.99, 1.14, latest_date, transform=ax.transAxes,
            fontsize=10, color=t["sub_text"], va='top', ha='right')
    
    # ── MA凡例（右上、チャート領域より上に配置） ──
    ma_start_y = 1.07
    ma_step = 0.055
    
    for i, w in enumerate(ma_windows):
        val = ma_values.get(w)
        color = t["ma"].get(w, '#888')
        if val is not None:
            val_str = fmt(val)
            arrow = "▲" if latest_close >= val else "▼"
            a_color = t["up"] if latest_close >= val else t["down"]
            y_pos = ma_start_y - i * ma_step
            
            ax.text(0.985, y_pos,
                    f"{ma_label_text.get(w, f'{w}d')}MA: {val_str}",
                    transform=ax.transAxes, fontsize=10,
                    color=color, va='top', ha='right')
            ax.text(0.998, y_pos, arrow,
                    transform=ax.transAxes, fontsize=10,
                    color=a_color, va='top', ha='right')
    
    # ── 軸設定 ──
    p_days = {"3mo": 90, "6mo": 180, "1y": 365, "2y": 730}.get(period, 365)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("'%y/%m"))
    ax.xaxis.set_major_locator(
        mdates.MonthLocator(interval=1 if p_days <= 100 else 2))
    
    # Y軸は y_axis_decimals（見やすさ優先）
    if y_format == "comma":
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, p: f"{x:,.{y_axis_decimals}f}"))
    else:
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, p: f"{x:.{y_axis_decimals}f}"))
    
    ax.tick_params(axis='both', colors=t["sub_text"], labelsize=9)
    ax.grid(True, alpha=0.15, color=t["grid"])
    for spine in ax.spines.values():
        spine.set_color(t["spine"])
        spine.set_linewidth(0.5)
    
    # ヘッダー領域を広めに確保
    plt.subplots_adjust(top=0.76, bottom=0.10, left=0.08, right=0.95)
    
    # 保存
    os.makedirs(output_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    filepath = os.path.join(output_dir, f"{filename_prefix}_{date_str}.png")
    fig.savefig(filepath, dpi=150, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close(fig)
    return filepath

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# メイン処理
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    print("=" * 55)
    print("  Phase 2e: チャート画像の自動生成 v3")
    print(f"  テーマ: ホワイト / Yahoo Finance桁数準拠")
    print(f"  出力先: {OUTPUT_DIR}")
    print("=" * 55)
    print()
    
    results = []
    for config in CHART_CONFIGS:
        ticker = config["ticker_symbol"]
        name = config["name"]
        print(f"[取得] {name} ({ticker})...")
        
        display_df = fetch_chart_data(
            ticker, period=config["period"], ma_windows=config["ma_windows"])
        
        if display_df is None:
            print(f"  ❌ {name}: データ取得失敗")
            results.append((name, None))
            continue
        
        filepath = generate_chart(
            display_df, name=name,
            filename_prefix=config["filename_prefix"],
            period=config["period"],
            ma_windows=config["ma_windows"],
            y_format=config["y_format"],
            y_decimals=config["y_decimals"],
            y_axis_decimals=config.get("y_axis_decimals", config["y_decimals"]),
        )
        
        if filepath:
            print(f"  ✅ {name}: {filepath}")
        else:
            print(f"  ❌ {name}: 画像生成失敗")
        results.append((name, filepath))
    
    print()
    print("=" * 55)
    print("  生成結果サマリー")
    print("=" * 55)
    success = 0
    for name, path in results:
        if path:
            success += 1
            print(f"  ✅ {name}")
            print(f"     → {path}")
        else:
            print(f"  ❌ {name}: 失敗")
    print()
    print(f"  {success}/{len(results)} 枚生成完了")
    
    if success > 0:
        print()
        print("  次のステップ:")
        print("  1. GitHub Desktopでchartsフォルダをcommit & push")
        print("  2. NOTEに以下のURLで貼付:")
        date_str = datetime.now().strftime("%Y%m%d")
        print(f"     https://misogai-match.github.io/earnings-insight/charts/SP500_{date_str}.png")

if __name__ == "__main__":
    main()
