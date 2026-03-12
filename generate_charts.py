"""
generate_charts.py — Phase 2e チャート画像自動生成
==================================================
目的: Yahoo Financeスクショ＋FRED系スクショを、matplotlib自動生成に置換する。
      market_data.py（数値取得）と併用し、毎朝の作業を大幅削減。

使い方:
  1. コマンドプロンプトで以下を実行:
       cd C:\\GitHub
       python generate_charts.py
  2. C:\\GitHub\\charts\\ に日付付きPNGが8枚生成される
  3. GitHub Pagesにpush → NOTEに永続URLで貼付

必要なライブラリ:
  pip install yfinance matplotlib pandas fredapi

作成: 2026/03/12
バージョン: v4（FRED API統合 — 実質金利＋10-2スプレッド追加）

桁数設定（Yahoo Finance左上ヘッダー / FRED準拠）:
  S&P 500:       2桁 (6,775.80)
  VIX:           2桁 (24.23)
  10Y Yield:     4桁 (4.2080)
  USD/JPY:       4桁 (158.9830)
  DXY:           3桁 (99.255)
  WTI:           2桁 (91.55)
  Real Yield:    2桁 (1.85)     ← NEW
  10-2 Spread:   2桁 (0.35)     ← NEW
"""

import sys
from datetime import datetime, timedelta

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 設定
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# チャート画像の保存先
OUTPUT_DIR = r"C:\GitHub\charts"

# FRED APIキー（market_data.pyと同じキーを使用）
FRED_API_KEY = "87f44968a8c6fc424e9c5ec8f5e2831c"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ライブラリ読み込み
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

try:
    import yfinance as yf
    import matplotlib
    matplotlib.use('Agg')  # GUIなしで画像出力
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import matplotlib.ticker as mticker
    import pandas as pd
    import os
except ImportError as e:
    print(f"[エラー] ライブラリが見つかりません: {e}")
    print("以下のコマンドでインストールしてください:")
    print("  pip install yfinance matplotlib pandas fredapi")
    sys.exit(1)

# FRED APIはオプション（未設定でもyfinanceチャートは生成可能）
try:
    from fredapi import Fred
    FRED_AVAILABLE = True
except ImportError:
    FRED_AVAILABLE = False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# フォント設定（Windows日本語対応）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def setup_font():
    """Windows環境でMeiryoフォントを使用する設定"""
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
    "bg":         '#ffffff',
    "text":       '#1a1a1a',
    "sub_text":   '#666666',
    "grid":       '#e0e0e0',
    "spine":      '#cccccc',
    "price_line": '#1a73e8',   # Google Blue
    "price_fill": '#1a73e8',
    "up":         '#0d7c3f',   # 緑
    "down":       '#d93025',   # 赤
    "zero_line":  '#999999',   # ゼロライン（10-2スプレッド用）
    "ma": {
        21: '#e8710a',         # オレンジ
        50: '#d93025',         # 赤
        200: '#0d7c3f',        # 緑
    },
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# チャート定義（yfinance: 6枚 + FRED: 2枚 = 計8枚）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# --- yfinanceチャート（既存6枚） ---
YFINANCE_CHART_CONFIGS = [
    {
        "ticker_symbol": "^GSPC",
        "name": "S&P 500",
        "filename_prefix": "SP500",
        "period": "1y",
        "ma_windows": [21, 50, 200],
        "y_format": "comma",
        "y_decimals": 2,
    },
    {
        "ticker_symbol": "^VIX",
        "name": "VIX",
        "filename_prefix": "VIX",
        "period": "3mo",
        "ma_windows": [21, 50, 200],
        "y_format": "plain",
        "y_decimals": 2,
    },
    {
        "ticker_symbol": "^TNX",
        "name": "10Y Treasury Yield",
        "filename_prefix": "10Y_Yield",
        "period": "1y",
        "ma_windows": [21, 50, 200],
        "y_format": "plain",
        "y_decimals": 4,
    },
    {
        "ticker_symbol": "JPY=X",
        "name": "USD/JPY",
        "filename_prefix": "USDJPY",
        "period": "1y",
        "ma_windows": [21, 50, 200],
        "y_format": "plain",
        "y_decimals": 4,
    },
    {
        "ticker_symbol": "DX-Y.NYB",
        "name": "DXY (Dollar Index)",
        "filename_prefix": "DXY",
        "period": "1y",
        "ma_windows": [21, 50, 200],
        "y_format": "plain",
        "y_decimals": 3,
    },
    {
        "ticker_symbol": "CL=F",
        "name": "WTI Crude Oil",
        "filename_prefix": "WTI",
        "period": "1y",
        "ma_windows": [21, 50, 200],
        "y_format": "plain",
        "y_decimals": 2,
    },
]

# --- FREDチャート（新規2枚） ---
FRED_CHART_CONFIGS = [
    {
        "series_id": "DFII10",
        "name": "Real Yield (10Y TIPS)",
        "filename_prefix": "RealYield",
        "period": "1y",
        "ma_windows": [21, 50, 200],
        "y_format": "plain",
        "y_decimals": 2,
        "y_suffix": "%",
        "has_zero_line": False,
    },
    {
        "series_id": "T10Y2Y",
        "name": "10Y-2Y Spread",
        "filename_prefix": "Spread10Y2Y",
        "period": "1y",
        "ma_windows": [21, 50, 200],
        "y_format": "plain",
        "y_decimals": 2,
        "y_suffix": "%",
        "has_zero_line": True,     # ゼロラインを描画し、正負で色分け
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# データ取得（yfinance）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def fetch_yfinance_data(ticker_symbol: str, period: str = "1y", ma_windows: list = [21, 50, 200]):
    """yfinanceから株価データを取得し、移動平均線を計算する。"""
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
            print(f"  [警告] {ticker_symbol}: データ不十分（{len(hist) if hist is not None else 0}行）")
            return None

        for w in ma_windows:
            hist[f"MA{w}"] = hist["Close"].rolling(window=w).mean()

        cutoff = end_date - timedelta(days=display_days)
        display_df = hist[hist.index >= pd.Timestamp(cutoff, tz=hist.index.tz)]

        if display_df.empty:
            print(f"  [警告] {ticker_symbol}: 表示期間のデータがありません")
            return None

        return display_df

    except Exception as e:
        print(f"  [エラー] {ticker_symbol}: {e}")
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# データ取得（FRED API）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def fetch_fred_chart_data(fred: Fred, series_id: str, period: str = "1y", ma_windows: list = [21, 50, 200]):
    """
    FRED APIから時系列データを取得し、yfinanceと同じ形式のDataFrameに変換する。
    Close列 + MA列を持つDataFrameを返す。
    """
    period_days = {"3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
    display_days = period_days.get(period, 365)
    max_ma = max(ma_windows) if ma_windows else 0

    total_days = display_days + max_ma + 60  # FREDは休日欠損が多いので余裕を持つ
    end_date = datetime.now()
    start_date = end_date - timedelta(days=total_days)

    try:
        data = fred.get_series(series_id, start_date, end_date)

        if data is None or data.empty:
            print(f"  [警告] FRED {series_id}: データが見つかりません")
            return None

        # NaN除去してDataFrame化
        data = data.dropna()
        df = pd.DataFrame({"Close": data})
        df.index.name = "Date"

        if len(df) < max_ma + 10:
            print(f"  [警告] FRED {series_id}: データ不十分（{len(df)}行）")
            return None

        # 移動平均線の計算
        for w in ma_windows:
            df[f"MA{w}"] = df["Close"].rolling(window=w).mean()

        # 表示期間にトリム
        cutoff = end_date - timedelta(days=display_days)
        display_df = df[df.index >= pd.Timestamp(cutoff)]

        if display_df.empty:
            print(f"  [警告] FRED {series_id}: 表示期間のデータがありません")
            return None

        return display_df

    except Exception as e:
        print(f"  [エラー] FRED {series_id}: {e}")
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# チャート描画（共通）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_chart(
    display_df: pd.DataFrame,
    name: str,
    filename_prefix: str,
    period: str = "1y",
    ma_windows: list = [21, 50, 200],
    y_format: str = "comma",
    y_decimals: int = 2,
    y_suffix: str = "",
    has_zero_line: bool = False,
    output_dir: str = OUTPUT_DIR,
):
    """データフレームからチャート画像を生成・保存する。"""
    t = THEME
    hd = display_df

    # ── 最新値の取得 ──
    latest_close = hd["Close"].iloc[-1]
    prev_close = hd["Close"].iloc[-2] if len(hd) >= 2 else latest_close
    change = latest_close - prev_close
    change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
    latest_date = hd.index[-1].strftime("%Y/%m/%d")

    ma_values = {}
    for w in ma_windows:
        col = f"MA{w}"
        if col in hd.columns:
            val = hd[col].iloc[-1]
            ma_values[w] = val if pd.notna(val) else None
        else:
            ma_values[w] = None

    # フォーマッタ
    def fmt(val):
        if y_format == "comma":
            return f"{val:,.{y_decimals}f}"
        return f"{val:.{y_decimals}f}"

    # ━━━━━━━━━━━━ プロット ━━━━━━━━━━━━
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.set_facecolor(t["bg"])
    ax.set_facecolor(t["bg"])

    # ── ゼロライン（10-2スプレッド用） ──
    if has_zero_line:
        ax.axhline(y=0, color=t["zero_line"], linewidth=1.0, linestyle='--', zorder=3)
        # 正負で色分けフィル
        ax.fill_between(hd.index, hd["Close"], 0,
                         where=(hd["Close"] >= 0),
                         alpha=0.08, color=t["up"], zorder=1)
        ax.fill_between(hd.index, hd["Close"], 0,
                         where=(hd["Close"] < 0),
                         alpha=0.08, color=t["down"], zorder=1)
    else:
        # 通常のフィル（下端まで）
        ax.fill_between(hd.index, hd["Close"], hd["Close"].min() * 0.995,
                         alpha=0.06, color=t["price_fill"], zorder=1)

    # ── 終値ライン ──
    ax.plot(hd.index, hd["Close"], color=t["price_line"], linewidth=1.8, zorder=5)

    # ── 移動平均線 ──
    ma_labels = {21: '21d', 50: '50d', 200: '200d'}
    for w in ma_windows:
        col = f"MA{w}"
        if col in hd.columns and hd[col].notna().any():
            ax.plot(hd.index, hd[col], color=t["ma"].get(w, '#888'),
                    linewidth=1.0, alpha=0.85, zorder=4)

    # ── ヘッダー（左上） ──
    sign = "+" if change >= 0 else ""
    c_color = t["up"] if change >= 0 else t["down"]

    close_str = fmt(latest_close)
    change_str = f"{sign}{fmt(change)}"
    pct_str = f"({sign}{change_pct:.2f}%)"

    # サフィックス付きの表示（%など）
    display_close = f"{close_str}{y_suffix}"
    display_change = f"{change_str}{y_suffix}"

    # タイトル
    ax.text(0.01, 1.10, name, transform=ax.transAxes,
            fontsize=15, fontweight='bold', color=t["text"], va='top')
    # 終値（大きく）
    ax.text(0.01, 1.03, display_close, transform=ax.transAxes,
            fontsize=24, fontweight='bold', color=t["text"], va='top')
    # 前日比
    offset = 0.02 + len(display_close) * 0.018
    ax.text(offset + 0.04, 1.03, f"{display_change}  {pct_str}",
            transform=ax.transAxes, fontsize=13, color=c_color, va='top')
    # 日付（右上）
    ax.text(0.99, 1.10, latest_date, transform=ax.transAxes,
            fontsize=10, color=t["sub_text"], va='top', ha='right')

    # ── MA凡例（右上） ──
    for i, w in enumerate(ma_windows):
        val = ma_values.get(w)
        color = t["ma"].get(w, '#888')
        if val is not None:
            val_str = f"{fmt(val)}{y_suffix}"
            arrow = "▲" if latest_close >= val else "▼"
            a_color = t["up"] if latest_close >= val else t["down"]

            ax.text(0.985, 1.03 - i * 0.06,
                    f"{ma_labels.get(w, f'{w}d')}MA: {val_str}",
                    transform=ax.transAxes, fontsize=10,
                    color=color, va='top', ha='right')
            ax.text(0.998, 1.03 - i * 0.06, arrow,
                    transform=ax.transAxes, fontsize=10,
                    color=a_color, va='top', ha='right')

    # ── 軸の設定 ──
    period_days_map = {"3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
    p_days = period_days_map.get(period, 365)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("'%y/%m"))
    if p_days <= 100:
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    else:
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))

    # Y軸フォーマッタ（サフィックス対応）
    if y_format == "comma":
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, p: f"{x:,.{y_decimals}f}{y_suffix}"))
    else:
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, p: f"{x:.{y_decimals}f}{y_suffix}"))

    ax.tick_params(axis='both', colors=t["sub_text"], labelsize=9)
    ax.grid(True, alpha=0.15, color=t["grid"])

    for spine in ax.spines.values():
        spine.set_color(t["spine"])
        spine.set_linewidth(0.5)

    plt.subplots_adjust(top=0.80, bottom=0.10, left=0.08, right=0.95)

    # ── 保存 ──
    os.makedirs(output_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"{filename_prefix}_{date_str}.png"
    filepath = os.path.join(output_dir, filename)

    fig.savefig(filepath, dpi=150, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close(fig)

    return filepath


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# メイン処理
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    print("=" * 55)
    print("  Phase 2e: チャート画像の自動生成 v4")
    print("  テーマ: ホワイト / Yahoo Finance桁数準拠")
    print("  新規: FRED API統合（実質金利＋10-2スプレッド）")
    print(f"  出力先: {OUTPUT_DIR}")
    print("=" * 55)
    print()

    results = []

    # ━━━ yfinanceチャート（6枚） ━━━
    print("─── yfinance チャート（6枚）───")
    print()

    for config in YFINANCE_CHART_CONFIGS:
        ticker = config["ticker_symbol"]
        name = config["name"]
        print(f"[取得] {name} ({ticker})...")

        display_df = fetch_yfinance_data(
            ticker,
            period=config["period"],
            ma_windows=config["ma_windows"],
        )

        if display_df is None:
            print(f"  ❌ {name}: データ取得失敗")
            results.append((name, None))
            continue

        filepath = generate_chart(
            display_df,
            name=name,
            filename_prefix=config["filename_prefix"],
            period=config["period"],
            ma_windows=config["ma_windows"],
            y_format=config["y_format"],
            y_decimals=config["y_decimals"],
        )

        if filepath:
            print(f"  ✅ {name}: {filepath}")
        else:
            print(f"  ❌ {name}: 画像生成失敗")

        results.append((name, filepath))

    print()

    # ━━━ FREDチャート（2枚） ━━━
    print("─── FRED チャート（2枚）───")
    print()

    if not FRED_AVAILABLE:
        print("[スキップ] fredapiライブラリが未インストールです。")
        print("  → pip install fredapi でインストールしてください。")
        for config in FRED_CHART_CONFIGS:
            results.append((config["name"], None))
    elif FRED_API_KEY == "ここにAPIキーを貼り付けてください":
        print("[スキップ] FRED APIキーが未設定です。")
        print("  → スクリプト冒頭の FRED_API_KEY を書き換えてください。")
        print("  → market_data.py と同じキーを使えます。")
        for config in FRED_CHART_CONFIGS:
            results.append((config["name"], None))
    else:
        try:
            fred = Fred(api_key=FRED_API_KEY)
            for config in FRED_CHART_CONFIGS:
                series_id = config["series_id"]
                name = config["name"]
                print(f"[取得] {name} (FRED: {series_id})...")

                display_df = fetch_fred_chart_data(
                    fred,
                    series_id,
                    period=config["period"],
                    ma_windows=config["ma_windows"],
                )

                if display_df is None:
                    print(f"  ❌ {name}: データ取得失敗")
                    results.append((name, None))
                    continue

                filepath = generate_chart(
                    display_df,
                    name=name,
                    filename_prefix=config["filename_prefix"],
                    period=config["period"],
                    ma_windows=config["ma_windows"],
                    y_format=config["y_format"],
                    y_decimals=config["y_decimals"],
                    y_suffix=config.get("y_suffix", ""),
                    has_zero_line=config.get("has_zero_line", False),
                )

                if filepath:
                    print(f"  ✅ {name}: {filepath}")
                else:
                    print(f"  ❌ {name}: 画像生成失敗")

                results.append((name, filepath))

        except Exception as e:
            print(f"[エラー] FRED API接続失敗: {e}")
            for config in FRED_CHART_CONFIGS:
                results.append((config["name"], None))

    # ── サマリー ──
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
        print(f"     （他のチャートも同様にファイル名を変更）")
        print()
        print("  新規チャートURL:")
        print(f"     .../charts/RealYield_{date_str}.png")
        print(f"     .../charts/Spread10Y2Y_{date_str}.png")


if __name__ == "__main__":
    main()
