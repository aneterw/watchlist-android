"""
yfinance Watchlist Manager
功能：
  - 預設各大主要指數 Watchlist
  - 可新增/刪除自訂 Watchlist
  - 可搜尋 ticker 並加入 Watchlist（輸入即篩選）
  - 一鍵更新所有 / 目前 Watchlist 商品價格
  - 閒置 10 分鐘自動更新
  - JSON 自動儲存，重啟不遺失
  - 雙擊商品顯示 K 線圖（日/週/月）+ 成交量 + KD
  - 多語言（繁中/簡中/英/日/韓/西）+ 主題（日間/暗黑/系統）
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import yfinance as yf
import threading
import math
import datetime
import json
import os

SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watchlist_data.json")

DEFAULT_WATCHLISTS = {
    "全球主要指數": [
        ("SPX", "^GSPC", "S&P 500"), ("NASDAQ", "^IXIC", "NASDAQ Composite"),
        ("DOW", "^DJI", "Dow Jones"), ("FTSE100", "^FTSE", "UK FTSE 100"),
        ("DAX", "^GDAXI", "Germany DAX"), ("日經225", "^N225", "Nikkei 225"),
        ("上證綜指", "000001.SS", "SSE Composite"), ("恒生指數", "^HSI", "Hang Seng"),
        ("KOSPI", "^KS11", "Korea KOSPI"), ("ASX200", "^AXJO", "Australia ASX 200"),
    ],
    "科技股 ETF": [
        ("QQQ", "QQQ", "Invesco QQQ Trust"), ("VGT", "VGT", "Vanguard Info Tech"),
    ],
}

COMMON_TICKERS = [
    ("AAPL","AAPL","Apple"),("MSFT","MSFT","Microsoft"),("GOOGL","GOOGL","Alphabet"),
    ("AMZN","AMZN","Amazon"),("NVDA","NVDA","NVIDIA"),("META","META","Meta"),
    ("TSLA","TSLA","Tesla"),("BRK-B","BRK-B","Berkshire"),("LLY","LLY","Eli Lilly"),
    ("AVGO","AVGO","Broadcom"),("JPM","JPM","JPMorgan"),("V","V","Visa"),
    ("JNJ","JNJ","J&J"),("WMT","WMT","Walmart"),("XOM","XOM","Exxon"),
    ("PG","PG","P&G"),("MA","MA","Mastercard"),("HD","HD","Home Depot"),
    ("CVX","CVX","Chevron"),("MRK","MRK","Merck"),("KO","KO","Coca-Cola"),
    ("PEP","PEP","PepsiCo"),("COST","COST","Costco"),("ADBE","ADBE","Adobe"),
    ("MCD","MCD","McDonald's"),("CSCO","CSCO","Cisco"),("ACN","ACN","Accenture"),
    ("NKE","NKE","Nike"),("TMO","TMO","Thermo Fisher"),("LIN","LIN","Linde"),
    ("TMUS","TMUS","T-Mobile"),("VZ","VZ","Verizon"),("INTC","INTC","Intel"),
    ("QCOM","QCOM","Qualcomm"),("TXN","TXN","Texas Inst"),("HON","HON","Honeywell"),
    ("2330.TW","2330.TW","台積電"),("2317.TW","2317.TW","鴻海"),("2454.TW","2454.TW","聯發科"),
    ("2382.TW","2382.TW","廣達"),("2881.TW","2881.TW","富邦金"),("2882.TW","2882.TW","國泰金"),
    ("3711.TW","3711.TW","日月光"),("2409.TW","2409.TW","友達"),("3481.TW","3481.TW","群創"),
    ("0700.HK","0700.HK","騰訊"),("9988.HK","9988.HK","阿里巴巴"),
    ("00941.HK","00941.HK","中國移動"),("00939.HK","00939.HK","建設銀行"),
    ("601318.SS","601318.SS","中國平安"),("600519.SS","600519.SS","貴州茅台"),
    ("000858.SZ","000858.SZ","五糧液"),("002594.SZ","002594.SZ","比亞迪"),
    ("601398.SS","601398.SS","工商銀行"),("601899.SS","601899.SS","紫金礦業"),
    ("03690.HK","03690.HK","美團"),("01810.HK","01810.HK","小米"),
    ("09618.HK","09618.HK","京東"),("00388.HK","00388.HK","港交所"),
    ("00005.HK","00005.HK","匯豐"),("601857.SS","601857.SS","中石油"),
    ("GC=F","GC=F","Gold"),("SI=F","SI=F","Silver"),("CL=F","CL=F","Crude Oil"),
    ("NG=F","NG=F","NatGas"),("HG=F","HG=F","Copper"),("GLD","GLD","GLD ETF"),
    ("SLV","SLV","SLV ETF"),("USO","USO","USO ETF"),
    ("EURUSD=X","EURUSD=X","EUR/USD"),("USDJPY=X","USDJPY=X","USD/JPY"),
    ("USDCNY=X","USDCNY=X","USD/CNY"),("USDHKD=X","USDHKD=X","USD/HKD"),
    ("USDTWD=X","USDTWD=X","USD/TWD"),("USDKRW=X","USDKRW=X","USD/KRW"),
    ("BTC-USD","BTC-USD","Bitcoin"),("ETH-USD","ETH-USD","Ethereum"),
    ("^TNX","^TNX","US 10Y"),("^VIX","^VIX","VIX"),
]

LANG = {
    "app_title":    {"zh-TW":"yfinance 自選股管理器","zh-CN":"yfinance 自选股管理器","en":"yfinance Watchlist Manager","ja":"yfinance ウォッチリスト マネージャー","ko":"yfinance 관심종목 관리자","es":"yfinance Gestor de Lista"},
    "status_ready": {"zh-TW":"就緒 — 請點選 Watchlist 並按更新價格","zh-CN":"就绪 — 请点选 Watchlist 并按更新价格","en":"Ready — select a Watchlist and press Refresh","ja":"準備完了 — Watchlist を選択して更新を押してください","ko":"준비 — 관심종목을 선택하고 새로고침을 누르세요","es":"Listo — selecciona una Watchlist y pulsa Actualizar"},
    "btn_new_wl":{"zh-TW":"＋ 新增 Watchlist","zh-CN":"＋ 新增 Watchlist","en":"+ New Watchlist","ja":"＋ 新しい Watchlist","ko":"＋ 새 Watchlist","es":"+ Nueva Watchlist"},
    "btn_del_wl":{"zh-TW":"－ 刪除 Watchlist","zh-CN":"－ 删除 Watchlist","en":"- Del Watchlist","ja":"－ Watchlist 削除","ko":"－ Watchlist 삭제","es":"- Eliminar Watchlist"},
    "btn_add_item":{"zh-TW":"＋ 加入商品","zh-CN":"＋ 加入商品","en":"+ Add Item","ja":"＋ 商品追加","ko":"＋ 종목 추가","es":"+ Agregar"},
    "btn_del_item":{"zh-TW":"－ 移除商品","zh-CN":"－ 移除商品","en":"- Remove","ja":"－ 商品削除","ko":"－ 종목 제거","es":"- Eliminar"},
    "btn_refresh_cur":{"zh-TW":"更新目前 WL","zh-CN":"更新目前 WL","en":"Refresh WL","ja":"WL 更新","ko":"WL 새로고침","es":"Actualizar WL"},
    "btn_refresh_all":{"zh-TW":"更新所有價格","zh-CN":"更新所有价格","en":"Refresh All","ja":"全て更新","ko":"전체 새로고침","es":"Actualizar Todo"},
    "col_name":{"zh-TW":"名稱","zh-CN":"名称","en":"Name","ja":"名称","ko":"이름","es":"Nombre"},
    "col_ticker":{"zh-TW":"Ticker","zh-CN":"Ticker","en":"Ticker","ja":"ティッカー","ko":"티커","es":"Ticker"},
    "col_price":{"zh-TW":"現價 (報價延遲15~20分鐘)","zh-CN":"现价 (报价延迟15~20分钟)","en":"Price (Delayed 15-20 min)","ja":"現在値 (気配延期15~20分)","ko":"현재가 (시세 지연 15~20분)","es":"Precio (Retraso 15-20 min)"},
    "col_change":{"zh-TW":"漲跌","zh-CN":"涨跌","en":"Change","ja":"前日比","ko":"등락","es":"Cambio"},
    "col_pct":{"zh-TW":"漲跌幅","zh-CN":"涨跌幅","en":"% Chg","ja":"騰落率","ko":"등락률","es":"% Var"},
    "col_vol":{"zh-TW":"成交量","zh-CN":"成交量","en":"Volume","ja":"出来高","ko":"거래량","es":"Volumen"},
    "col_count":{"zh-TW":"#","zh-CN":"#","en":"#","ja":"#","ko":"#","es":"#"},
    "frame_watchlists":{"zh-TW":"  Watchlists  ","zh-CN":"  Watchlists  ","en":"  Watchlists  ","ja":"  ウォッチリスト  ","ko":"   관심종목  ","es":"   Listas  "},
    "frame_prices":{"zh-TW":"  商品價格  ","zh-CN":"  商品价格  ","en":"  Prices  ","ja":"  価格一覧  ","ko":"   가격  ","es":"   Precios  "},
    "frame_search":{"zh-TW":"  加入商品 - 輸入 ticker 或名稱即搜尋（雙擊結果直接加入）  ","zh-CN":"  加入商品 - 输入 ticker 或名称即搜寻（双击结果直接加入）  ","en":"  Add Item - type ticker or name (double-click result to add)  ","ja":"  商品追加 - ティッカーまたは名称を入力（ダブルクリックで追加）  ","ko":"  종목추가 - 티커 또는 이름 입력 (더블클릭으로 추가)  ","es":"  Agregar - escribe ticker o nombre (doble clic para agregar)  "},
    "lbl_search":{"zh-TW":"搜尋 / Ticker：","zh-CN":"搜寻 / Ticker：","en":"Search / Ticker:","ja":"検索 / ティッカー：","ko":"검색 / 티커:","es":"Buscar / Ticker:"},
    "lbl_result":{"zh-TW":"搜尋結果（雙擊加入目前 Watchlist）：","zh-CN":"搜寻结果（双击加入目前 Watchlist）：","en":"Results (double-click to add):","ja":"検索結果（ダブルクリックで追加）：","ko":"검색결과 (더블클릭으로 추가):","es":"Resultados (doble clic para agregar):"},
    "lbl_custom_name":{"zh-TW":"顯示名稱(選填)：","zh-CN":"显示名称(选填)：","en":"Label (optional):","ja":"表示名（任意）：","ko":"표시명 (선택사항):","es":"Etiqueta (opcional):"},
    "btn_add_selected":{"zh-TW":"＋ 加入所選","zh-CN":"＋ 加入所选","en":"+ Add Selected","ja":"＋ 選択を追加","ko":"＋ 선택 추가","es":"+ Agregar Seleccionado"},
    "btn_direct_input":{"zh-TW":"直接輸入 Ticker","zh-CN":"直接输入 Ticker","en":"Direct Input","ja":"ティッカー直接入力","ko":"티커 직접 입력","es":"Entrada Directa"},
    "dlg_add_title":{"zh-TW":"新增商品","zh-CN":"新增商品","en":"Add Item","ja":"商品追加","ko":"종목 추가","es":"Agregar"},
    "dlg_ticker_hint":{"zh-TW":"Ticker（例 AAPL、BTC-USD、005930.KS、EURUSD=X）：","zh-CN":"Ticker（例 AAPL、BTC-USD、005930.KS、EURUSD=X）：","en":"Ticker (e.g. AAPL, BTC-USD):","ja":"ティッカー（例 AAPL、BTC-USD）：","ko":"티커 (예 AAPL, BTC-USD):","es":"Ticker (ej. AAPL, BTC-USD):"},
    "dlg_label_hint":{"zh-TW":"顯示名稱（可空白）：","zh-CN":"显示名称（可空白）：","en":"Label (optional):","ja":"表示名（空白可）：","ko":"표시명 (공백 가능):","es":"Etiqueta (opcional):"},
    "btn_ok":{"zh-TW":"加入","zh-CN":"加入","en":"Add","ja":"追加","ko":"추가","es":"Agregar"},
    "chart_day":{"zh-TW":"日線","zh-CN":"日线","en":"Day","ja":"日足","ko":"일봉","es":"Día"},
    "chart_week":{"zh-TW":"週線","zh-CN":"周线","en":"Week","ja":"週足","ko":"주봉","es":"Semana"},
    "chart_month":{"zh-TW":"月線","zh-CN":"月线","en":"Month","ja":"月足","ko":"월봉","es":"Mes"},
    "theme_menu":{"zh-TW":"主題","zh-CN":"主题","en":"Theme","ja":"テーマ","ko":"테마","es":"Tema"},
    "lang_menu":{"zh-TW":"語言","zh-CN":"语言","en":"Language","ja":"言語","ko":"언어","es":"Idioma"},
    "err_no_wl":{"zh-TW":"請先選擇一個 Watchlist","zh-CN":"请先选择一个 Watchlist","en":"Please select a Watchlist","ja":"Watchlist を選択してください","ko":"관심종목을 선택하세요","es":"Selecciona una Watchlist primero"},
    "err_no_select":{"zh-TW":"請先在列表中點選一個項目","zh-CN":"请先在列表中点选一个项目","en":"Please select an item in the list","ja":"リストから項目を選択してください","ko":"목록에서 항목을 선택하세요","es":"Selecciona un elemento en la lista"},
}

def _init_lang():
    global LANG
    pass  # already defined above

def t(key):
    global LANG
    return LANG.get(key, {}).get(CURRENT_LANG, key)

CURRENT_LANG = "zh-TW"
CURRENT_THEME = "system"

def _fmt_price(val):
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return "N/A"
    if isinstance(val, (int, float)):
        return f"{val:,.2f}"
    return str(val)

def _fmt_pct(val):
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return "N/A"
    if isinstance(val, (int, float)):
        return f"{val:,.2f}%"
    return str(val)

def _fmt_vol(val):
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return "N/A"
    if isinstance(val, (int, float)):
        return f"{int(val):,}"
    return str(val)

def _now_str():
    return datetime.datetime.now().strftime("%H:%M:%S")

def search_yfinance(query, limit=12):
    if not query or not query.strip():
        return []
    q = query.strip().upper()
    results = []
    for _, tk_sym, nm in COMMON_TICKERS:
        if q == tk_sym.upper() or q == nm.upper():
            results.append((f"{tk_sym} - {nm}", tk_sym, nm))
    if results:
        return results[:limit]
    for _, tk_sym, nm in COMMON_TICKERS:
        if tk_sym.upper().startswith(q):
            results.append((f"{tk_sym} - {nm}", tk_sym, nm))
    if len(results) >= limit:
        return results[:limit]
    for _, tk_sym, nm in COMMON_TICKERS:
        if q in nm.upper():
            results.append((f"{tk_sym} - {nm}", tk_sym, nm))
    if len(results) >= limit:
        return results[:limit]
    try:
        srch = yf.search(q, max_results=limit)
        if srch and "quotes" in srch and srch["quotes"]:
            for item in srch["quotes"]:
                sym = item.get("symbol", "")
                nm = item.get("shortname") or item.get("longname") or sym
                results.append((f"{sym} - {nm}", sym, nm))
    except Exception as e:
        print("yfinance search error:", e)
    seen = set()
    uniq = []
    for r in results:
        if r[1] not in seen:
            seen.add(r[1])
            uniq.append(r)
    return uniq[:limit]

def fetch_price(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.info
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        prev  = info.get("previousClose") or info.get("regularMarketPreviousClose")
        change = pct = vol = None
        if price is not None and prev is not None and prev != 0:
            change = price - prev
            pct = (change / prev) * 100
        vol = info.get("volume") or info.get("regularMarketVolume")
        return {
            "ticker": ticker,
            "name": info.get("shortName") or info.get("longName") or ticker,
            "price": price, "change": change, "pct_change": pct,
            "volume": vol, "market_cap": info.get("marketCap"),
        }
    except Exception as e:
        print("fetch_price error:", ticker, e)
        return {"ticker": ticker, "name": ticker, "price": None, "change": None,
                "pct_change": None, "volume": None, "market_cap": None}

def save_watchlists(watchlists, active_wl):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump({"active_wl": active_wl,
                        "watchlists": {n: list(v) for n, v in watchlists.items()},
                        "lang": CURRENT_LANG, "theme": CURRENT_THEME},
                       f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("save error:", e)

def load_watchlists():
    if not os.path.exists(SAVE_FILE):
        return None, None, None, None
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        wl = data.get("watchlists", {})
        restored = {n: [tuple(it) for it in v] for n, v in wl.items()}
        return restored, data.get("active_wl"), data.get("lang"), data.get("theme")
    except Exception as e:
        print("load error:", e)
        return None, None, None, None

def detect_system_theme():
    try:
        import ctypes, struct
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        attr = ctypes.c_int(20)
        ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, attr, ctypes.byref(ctypes.c_int()), 4)
        val = ctypes.c_int()
        ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 20, ctypes.byref(val), 4)
        return "dark" if val.value else "light"
    except Exception:
        return "light"

def _get_effective_theme():
    if CURRENT_THEME == "system":
        return detect_system_theme()
    return CURRENT_THEME

def apply_theme(root, style):
    theme = _get_effective_theme()
    is_dark = (theme == "dark")
    bg = "#1a1a1a" if is_dark else "#f0f0f0"
    fg = "#929292" if is_dark else "#333333"
    panel = "#252525" if is_dark else "#e8e8e8"
    entry_bg = "#1a1a1a" if is_dark else "#ffffff"
    field_fg = "#929292" if is_dark else "#000000"
    tree_bg = "#1a1a1a" if is_dark else "#ffffff"
    tree_fg = "#929292" if is_dark else "#000000"
    grid_c = "#333333" if is_dark else "#cccccc"
    sel_c = "#2a5a8a" if is_dark else "#0078d4"
    sel_fg = "#ffffff"

    root.configure(bg=bg)
    style.theme_use("clam")
    style.configure(".", background=bg, foreground=fg)
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton")
    style.configure("TCheckbutton", background=bg, foreground=fg)
    style.configure("TRadiobutton", background=bg, foreground=fg)
    style.map("TButton", background=[("active", "#3a3a3a" if is_dark else "#d0d0d0")])
    style.configure("TLabelframe", background=panel, foreground=fg)
    style.configure("TLabelframe.Label", background=panel, foreground=fg)
    style.configure("TEntry", fieldbackground=entry_bg, foreground=field_fg,
                    bordercolor="#444444" if is_dark else "#aaa")
    style.configure("Treeview", background=tree_bg, foreground=tree_fg,
                    fieldbackground=tree_bg, bordercolor=grid_c)
    style.configure("Treeview.Heading", background=panel, foreground=fg)
    style.map("Treeview", background=[("selected", sel_c)], foreground=[("selected", sel_fg)])
    # menubar（Windows 由系統渲染，盡量套色）
    try:
        root.option_add("*Menu.background", panel)
        root.option_add("*Menu.foreground", fg)
        root.option_add("*Menu.activeBackground", sel_c)
        root.option_add("*Menu.activeForeground", sel_fg)
    except Exception:
        pass


class ChartWindow:
    """K 線圖視窗：K 線 + 成交量(中) + KD(下)"""
    def __init__(self, parent, ticker, name, theme_mode="light"):
        self.ticker = ticker
        self.name = name
        self.theme_mode = theme_mode
        self.period = "day"

        self.win = tk.Toplevel(parent)
        self.win.title(f"{ticker} - {name}")
        self.win.geometry("1200x700")
        self.win.transient(parent)
        self.win.minsize(900, 540)

        try:
            import matplotlib
            matplotlib.use("TkAgg")
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
            import pandas as pd
            import numpy as np
            self._plt = plt
            self._FigureCanvasTkAgg = FigureCanvasTkAgg
            self._Figure = Figure
            self._pd = pd
            self._np = np
        except Exception as e:
            ttk.Label(self.win, text=f"Chart library error: {e}").pack(padx=20, pady=20)
            return

        tab_frame = ttk.Frame(self.win)
        tab_frame.pack(fill=tk.X, padx=8, pady=4)
        self.period_var = tk.StringVar(value="day")
        for p, lbl in [("day", t("chart_day")), ("week", t("chart_week")), ("month", t("chart_month"))]:
            ttk.Radiobutton(tab_frame, text=lbl, variable=self.period_var, value=p,
                            command=self._draw).pack(side=tk.LEFT, padx=6)

        self.fig_frame = ttk.Frame(self.win)
        self.fig_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
        self._draw()

    def _params(self):
        p = self.period_var.get()
        if p == "day":
            return "1d", "2y"
        elif p == "week":
            return "1wk", "10y"
        else:
            return "1mo", "30y"

    def _draw(self):
        for w in self.fig_frame.winfo_children():
            w.destroy()
        try:
            interval, period = self._params()
            raw = yf.Ticker(self.ticker).history(period=period, interval=interval)
            if raw is None or raw.empty:
                ttk.Label(self.fig_frame, text=f"{self.ticker}: 無資料").pack(padx=20, pady=20)
                return
            raw = raw.tail(200)

            def _to_date(x):
                if hasattr(x, "strftime"):
                    return x.strftime("%Y-%m-%d")
                return str(x)
            dates = [_to_date(x) for x in raw.index]
            n = len(raw)
            xpos = list(range(n))

            def _safe(series):
                try:
                    s = self._pd.to_numeric(series, errors="coerce")
                    return s.fillna(0).values
                except Exception:
                    return [0.0] * n

            o = _safe(raw["Open"]); h = _safe(raw["High"]); l = _safe(raw["Low"])
            c = _safe(raw["Close"]); v = _safe(raw["Volume"])
            eps = 1e-9

            is_dark = (self.theme_mode == "dark")
            bg = "#1a1a1a" if is_dark else "#ffffff"
            grid_c = "#333333" if is_dark else "#cccccc"
            txt_c = "#929292" if is_dark else "#333333"
            up_c = "#ff6666" if is_dark else "#cc0000"
            dn_c = "#66ff66" if is_dark else "#006600"

            fig = self._Figure(figsize=(11, 6.5), dpi=100)
            fig.patch.set_facecolor(bg)

            # 3 子圖：K線(上) / 成交量(中) / KD(下+X軸)
            ax_k = fig.add_axes([0.07, 0.40, 0.90, 0.36])
            ax_v = fig.add_axes([0.07, 0.29, 0.90, 0.10], sharex=ax_k)
            ax_kd = fig.add_axes([0.07, 0.08, 0.90, 0.19], sharex=ax_k)

            for ax in (ax_k, ax_v, ax_kd):
               ax.set_facecolor(bg)
               ax.grid(True, color=grid_c, linestyle="--", linewidth=0.4)
               for sp in ax.spines.values():
                   sp.set_edgecolor(grid_c)

            title = f"{self.ticker}  {self.name}  [{self.period_var.get().upper()} CHART]"
            ax_k.set_title(title, color=txt_c, fontsize=11, fontweight="bold", loc="left")
            ax_k.set_ylabel("Price", color=txt_c, fontsize=8)
            ax_k.tick_params(colors=txt_c, labelsize=7, left=True, bottom=False, labelbottom=False)
            ax_k.set_xlim(-0.5, n - 0.5)

            # K 線
            for i in range(n):
                oi, hi, li, ci = o[i], h[i], l[i], c[i]
                col = up_c if ci >= oi else dn_c
                if hi <= li:
                    hi = max(oi, ci) + eps
                    li = min(oi, ci) - eps
                ax_k.plot([i, i], [li, hi], color=col, linewidth=0.9, solid_capstyle="butt")
                bot, top = min(oi, ci), max(oi, ci)
                if abs(top - bot) < eps:
                    d = max(abs(oi) * 0.005, eps)
                    bot -= d / 2; top += d / 2
                ax_k.bar(i, top - bot, bottom=bot, width=0.52, color=col, edgecolor=col, linewidth=0.4)

            # 成交量（np.array 確保永遠有 .max）
            try:
                v_arr = self._pd.to_numeric(v, errors="coerce")
                if hasattr(v_arr, "values"):
                    v_arr = v_arr.values
                v_arr = v_arr.astype(float)
                vmax = float(v_arr.max()) if v_arr.size else 1.0
            except Exception:
                v_arr = self._np.zeros(n)
                vmax = 1.0
            vnorm = v_arr / max(vmax, 1.0)
            colors_v = [up_c if c[i] >= o[i] else dn_c for i in range(n)]
            ax_v.bar(xpos, vnorm, color=colors_v, width=0.6)
            ax_v.set_ylabel("Vol", color=txt_c, fontsize=6)
            ax_v.tick_params(colors=txt_c, labelsize=6, left=True, bottom=False, labelbottom=False)

            # KD
            low9 = self._pd.Series(l).rolling(9, min_periods=1).min().values
            hi9  = self._pd.Series(h).rolling(9, min_periods=1).max().values
            denom = hi9 - low9
            rsv = self._pd.Series([50.0] * n)
            mask = denom != 0
            rsv[mask] = (self._pd.Series(c)[mask] - low9[mask]) / denom[mask] * 100
            k_arr = rsv.ewm(com=2, adjust=False).mean().values
            d_arr = self._pd.Series(k_arr).ewm(com=2, adjust=False).mean().values

            ax_kd.set_ylabel("KD", color=txt_c, fontsize=8)
            ax_kd.tick_params(colors=txt_c, labelsize=7)
            ax_kd.set_ylim(-10, 110)
            ax_kd.axhline(80, color="#ff8800", linestyle=":", linewidth=0.8)
            ax_kd.axhline(20, color="#0088ff", linestyle=":", linewidth=0.8)
            ax_kd.plot(xpos, k_arr, color="#ff9900", linewidth=1.0, label="K")
            ax_kd.plot(xpos, d_arr, color="#3399ff", linewidth=1.0, label="D")
            ax_kd.legend(loc="upper left", fontsize=7, facecolor=bg, edgecolor=grid_c, labelcolor=txt_c)

            # X 軸：最下層、橫列、不斜
            step = max(1, n // 8)
            xt = list(range(0, n, step))
            if not xt or xt[-1] != n - 1:
                xt.append(n - 1)
            ax_kd.set_xticks(xt)
            ax_kd.set_xticklabels([dates[i] for i in xt], rotation=0, ha="center",
                                  fontsize=7, color=txt_c)

            canvas = self._FigureCanvasTkAgg(fig, master=self.fig_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            ttk.Label(self.fig_frame, text=f"繪圖失敗: {e}").pack(padx=20, pady=20)


class WatchlistApp:
    def __init__(self, root):
        self.root = root
        self.root.title("yfinance Watchlist Manager")
        self._apply_zoom()

        self.watchlists = {}
        self.active_wl = None
        self.price_data = {}
        self._selected_res = None
        self._search_job = None
        self._search_enabled = False
        self._auto_job = None

        saved, saved_active, saved_lang, saved_theme = load_watchlists()
        if saved is not None:
            self.watchlists = saved
            self.active_wl = saved_active
        else:
            for name, items in DEFAULT_WATCHLISTS.items():
                self.watchlists[name] = list(items)
        if saved_lang:
            global CURRENT_LANG
            CURRENT_LANG = saved_lang
        if saved_theme:
            global CURRENT_THEME
            CURRENT_THEME = saved_theme

        try:
            self._style = ttk.Style()
        except Exception:
            self._style = None

        self._build_ui()
        self._apply_theme()
        self._refresh_wl_list()
        self._refresh_items()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(100, self._enable_search)
        self._schedule_auto_refresh()

    def _apply_zoom(self):
        w, h = 960, 600
        zw, zh = int(w * 1.5), int(h * 1.5)
        self.root.geometry(f"{zw}x{zh}")
        self.root.minsize(int(820 * 1.5), int(500 * 1.5))

    def _save(self):
        save_watchlists(self.watchlists, self.active_wl)

    def _on_close(self):
        self._save()
        self.root.destroy()

    def _schedule_auto_refresh(self):
        if self._auto_job:
            self.root.after_cancel(self._auto_job)
        self._auto_job = self.root.after(600000, self._auto_refresh)

    def _auto_refresh(self):
        try:
            self._refresh_all()
        except Exception:
            pass
        self._schedule_auto_refresh()

    def _enable_search(self):
        self._search_enabled = True
        self.search_var.trace_add("write", lambda *_: self._schedule_search())

    def _apply_theme(self):
        if self._style:
            apply_theme(self.root, self._style)

    def _build_ui(self):
        root = self.root

        # 上方工具列
        top = ttk.Frame(root, padding=6)
        top.pack(fill=tk.X, side=tk.TOP)

        self.btn_add_wl = ttk.Button(top, text=t("btn_new_wl"), command=self._add_watchlist)
        self.btn_add_wl.pack(side=tk.LEFT, padx=(0, 3))
        self.btn_del_wl = ttk.Button(top, text=t("btn_del_wl"), command=self._del_watchlist)
        self.btn_del_wl.pack(side=tk.LEFT, padx=(0, 3))
        self.btn_add_item = ttk.Button(top, text=t("btn_add_item"), command=self._open_add_dialog)
        self.btn_add_item.pack(side=tk.LEFT, padx=(0, 3))
        self.btn_del_item = ttk.Button(top, text=t("btn_del_item"), command=self._del_item)
        self.btn_del_item.pack(side=tk.LEFT, padx=(0, 3))
        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)

        self.btn_refresh_current = ttk.Button(top, text=t("btn_refresh_cur"), command=self._refresh_current_watchlist)
        self.btn_refresh_current.pack(side=tk.LEFT, padx=(0, 3))
        self.btn_refresh = ttk.Button(top, text=t("btn_refresh_all"), command=self._refresh_all)
        self.btn_refresh.pack(side=tk.LEFT, padx=(0, 3))

        self.status_var = tk.StringVar(value=t("status_ready"))
        self.status_label = ttk.Label(top, textvariable=self.status_var)
        self.status_label.pack(side=tk.RIGHT, padx=(8, 0))

        self._build_menu()

        # 主分割區域
        paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        left = ttk.LabelFrame(paned, text=t("frame_watchlists"), padding=4)
        paned.add(left, weight=1)

        self.wl_tree = ttk.Treeview(left, columns=("cnt",), show="tree headings", height=18)
        self.wl_tree.heading("#0", text=t("col_name"))
        self.wl_tree.heading("#1", text=t("col_count"))
        self.wl_tree.column("#0", width=150, stretch=True)
        self.wl_tree.column("#1", width=30, anchor=tk.CENTER)
        self.wl_tree.bind("<<TreeviewSelect>>", self._on_wl_select)
        self.wl_tree.pack(fill=tk.BOTH, expand=True)

        right = ttk.PanedWindow(paned, orient=tk.VERTICAL)
        paned.add(right, weight=3)

        item_frame = ttk.LabelFrame(right, text=t("frame_prices"), padding=4)
        right.add(item_frame, weight=3)

        cols = ("label", "ticker", "price", "change", "pct", "vol")
        self.item_tree = ttk.Treeview(item_frame, columns=cols, show="headings", height=10)
        self.item_tree.heading("label", text=t("col_name"))
        self.item_tree.heading("ticker", text=t("col_ticker"))
        self.item_tree.heading("price", text=t("col_price"))
        self.item_tree.heading("change", text=t("col_change"))
        self.item_tree.heading("pct", text=t("col_pct"))
        self.item_tree.heading("vol", text=t("col_vol"))
        for col_id, w in [("label",150),("ticker",90),("price",170),
                           ("change",80),("pct",75),("vol",90)]:
            anchor = tk.W if col_id == "label" else tk.E if col_id != "ticker" else tk.CENTER
            self.item_tree.column(col_id, width=w, anchor=anchor)
        self.item_tree.pack(fill=tk.BOTH, expand=True)
        self.item_tree.bind("<Double-1>", self._on_item_double_click)

        search_frame = ttk.LabelFrame(right, text=t("frame_search"), padding=6)
        right.add(search_frame, weight=2)

        row1 = ttk.Frame(search_frame)
        row1.pack(fill=tk.X, pady=(0, 4))
        ttk.Label(row1, text=t("lbl_search")).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(row1, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))

        ttk.Label(search_frame, text=t("lbl_result")).pack(anchor=tk.W)
        self.result_tree = ttk.Treeview(search_frame, columns=("lbl","tk","nm"),
                                        show="headings", height=5)
        self.result_tree.heading("lbl", text=t("col_name"))
        self.result_tree.heading("tk", text=t("col_ticker"))
        self.result_tree.heading("nm", text=t("col_name"))
        self.result_tree.column("lbl", width=200, anchor=tk.W)
        self.result_tree.column("tk", width=90, anchor=tk.CENTER)
        self.result_tree.column("nm", width=180, anchor=tk.W)
        self.result_tree.pack(fill=tk.BOTH, expand=True, pady=(2, 4))
        self.result_tree.bind("<Double-1>", lambda e: self._add_selected())
        self.result_tree.bind("<<TreeviewSelect>>", self._on_res_select)

        row2 = ttk.Frame(search_frame)
        row2.pack(fill=tk.X, pady=(4, 0))
        ttk.Label(row2, text=t("lbl_custom_name")).pack(side=tk.LEFT)
        self.label_var = tk.StringVar()
        self.label_entry = ttk.Entry(row2, textvariable=self.label_var, width=16)
        self.label_entry.pack(side=tk.LEFT, padx=(4, 4))
        self.btn_add_res = ttk.Button(row2, text=t("btn_add_selected"),
                                      command=self._add_selected, state=tk.DISABLED)
        self.btn_add_res.pack(side=tk.LEFT)
        ttk.Button(row2, text=t("btn_direct_input"), command=self._open_add_dialog).pack(side=tk.LEFT, padx=(6, 0))

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        lang_menu = tk.Menu(menubar, tearoff=0)
        for code, label in [("zh-TW","繁體中文"),("zh-CN","简体中文"),("en","English"),
                             ("ja","日本語"),("ko","한국어"),("es","Español")]:
            lang_menu.add_command(label=label, command=lambda c=code: self._switch_lang(c))
        menubar.add_cascade(label=t("lang_menu"), menu=lang_menu)
        theme_menu = tk.Menu(menubar, tearoff=0)
        for val, label in [("system","🌓 System"),("light","☀ Light"),("dark","🌙 Dark")]:
            theme_menu.add_command(label=label, command=lambda v=val: self._switch_theme(v))
        menubar.add_cascade(label=t("theme_menu"), menu=theme_menu)
        self.root.config(menu=menubar)

    def _switch_lang(self, code):
        global CURRENT_LANG
        CURRENT_LANG = code
        self._save()
        for w in self.root.winfo_children():
            w.destroy()
        self._build_ui()
        self._apply_theme()
        self._refresh_wl_list()
        self._refresh_items()

    def _switch_theme(self, val):
        global CURRENT_THEME
        CURRENT_THEME = val
        self._save()
        self._apply_theme()
        # 更新價格表 tag 顔色
        self._refresh_items()

    def _refresh_wl_list(self):
        for i in self.wl_tree.get_children():
            self.wl_tree.delete(i)
        for name in self.watchlists:
            cnt = len(self.watchlists[name])
            self.wl_tree.insert("", tk.END, iid=name, text=name, values=(cnt,))
        if self.active_wl and self.active_wl in self.watchlists:
            self.wl_tree.selection_set(self.active_wl)
        elif self.watchlists:
            first = next(iter(self.watchlists))
            self.wl_tree.selection_set(first)
            self.active_wl = first

    def _refresh_items(self):
        for i in self.item_tree.get_children():
            self.item_tree.delete(i)
        if not self.active_wl:
            return
        is_dark = (_get_effective_theme() == "dark")
        up_c   = "#ff6666" if is_dark else "#cc0000"
        dn_c   = "#66ff66" if is_dark else "#006600"
        neu_c  = "#cccccc" if is_dark else "#333333"
        for local_label, ticker, _ in self.watchlists.get(self.active_wl, []):
            pd2 = self.price_data.get(ticker, {})
            price_str = _fmt_price(pd2.get("price"))
            change_str = _fmt_price(pd2.get("change"))
            pct_str = _fmt_pct(pd2.get("pct_change"))
            vol_str = _fmt_vol(pd2.get("volume"))
            pct_val = pd2.get("pct_change")
            tag = ("up" if (pct_val is not None and pct_val > 0) else
                   "down" if (pct_val is not None and pct_val < 0) else "neutral")
            self.item_tree.insert("", tk.END, iid=ticker,
                values=(local_label, ticker, price_str, change_str, pct_str, vol_str),
                tags=(tag,))
        self.item_tree.tag_configure("up", foreground=up_c)
        self.item_tree.tag_configure("down", foreground=dn_c)
        self.item_tree.tag_configure("neutral", foreground=neu_c)

    def _on_wl_select(self, event):
        sel = self.wl_tree.selection()
        self.active_wl = sel[0] if sel else None
        self._refresh_items()

    def _add_watchlist(self):
        name = simpledialog.askstring("新增 Watchlist", "請輸入名稱：")
        if not name:
            return
        name = name.strip()
        if name in self.watchlists:
            messagebox.showwarning("錯誤", "此名稱已存在")
            return
        self.watchlists[name] = []
        self.active_wl = name
        self._refresh_wl_list()
        self._save()
        self.status_var.set(f"已新增 Watchlist「{name}」")

    def _del_watchlist(self):
        if not self.active_wl:
            messagebox.showinfo("提示", t("err_no_wl"))
            return
        if not messagebox.askyesno("確認", f"確定刪除「{self.active_wl}」？\n（裡面所有商品也會移除）"):
            return
        del self.watchlists[self.active_wl]
        self.active_wl = next(iter(self.watchlists)) if self.watchlists else None
        self._refresh_wl_list()
        self._refresh_items()
        self._save()

    def _schedule_search(self):
        if not self._search_enabled:
            return
        if self._search_job:
            self.root.after_cancel(self._search_job)
        self._search_job = self.root.after(200, self._do_search)

    def _do_search(self):
        q = self.search_var.get().strip()
        for i in self.result_tree.get_children():
            self.result_tree.delete(i)
        self._selected_res = None
        self.btn_add_res.config(state=tk.DISABLED)
        if not q:
            return
        results = search_yfinance(q)
        if not results:
            self.result_tree.insert("", tk.END, values=(f"（找不到 {q}）", "", ""))
            return
        for lbl, tk_sym, nm in results:
            self.result_tree.insert("", tk.END, values=(lbl, tk_sym, nm))
        self.status_var.set(f"找到 {len(results)} 筆結果")

    def _on_res_select(self, event):
        sel = self.result_tree.selection()
        self._selected_res = None
        if sel:
            vals = self.result_tree.item(sel[0], "values")
            if vals[1]:
                self._selected_res = (vals[0], vals[1], vals[2])
        self.btn_add_res.config(state=tk.NORMAL if (self._selected_res and self.active_wl) else tk.DISABLED)

    def _add_selected(self):
        if not self._selected_res:
            messagebox.showinfo("提示", "請先在搜尋結果中點選一個項目")
            return
        if not self.active_wl:
            messagebox.showinfo("提示", t("err_no_wl"))
            return
        label, ticker, name = self._selected_res
        self._insert_item(label, ticker, name)

    def _insert_item(self, label, ticker, full_name):
        if not self.active_wl:
            messagebox.showinfo("提示", t("err_no_wl"))
            return
        items = self.watchlists[self.active_wl]
        if any(it[1] == ticker for it in items):
            messagebox.showwarning("重複", f"{ticker} 已在 Watchlist 中")
            return
        final_label = label if label else ticker
        items.append((final_label, ticker, full_name))
        self.search_var.set("")
        self._refresh_wl_list()
        self._refresh_items()
        self._save()
        self.status_var.set(f"已加入 {ticker} ({full_name}) 到 {self.active_wl}")

    def _center_dialog(self, dlg):
        dlg.update_idletasks()
        dlg.geometry(f"+{self.root.winfo_x() + (self.root.winfo_width()-dlg.winfo_reqwidth())//2}"
                     f"+{self.root.winfo_y() + (self.root.winfo_height()-dlg.winfo_reqheight())//2}")

    def _open_add_dialog(self):
        if not self.active_wl:
            messagebox.showinfo("提示", t("err_no_wl"))
            return
        dlg = tk.Toplevel(self.root)
        dlg.title(t("dlg_add_title"))
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.geometry("420x150")
        self._center_dialog(dlg)
        ttk.Label(dlg, text=t("dlg_ticker_hint")).pack(anchor=tk.W, padx=12, pady=(12, 2))
        tk_var = tk.StringVar()
        lb_var = tk.StringVar()
        ttk.Entry(dlg, textvariable=tk_var, width=42).pack(padx=12, fill=tk.X)
        ttk.Label(dlg, text=t("dlg_label_hint")).pack(anchor=tk.W, padx=12, pady=(8, 2))
        ttk.Entry(dlg, textvariable=lb_var, width=42).pack(padx=12, fill=tk.X)
        def _ok():
            sym = tk_var.get().strip()
            lbl = lb_var.get().strip() or sym
            if not sym:
                messagebox.showwarning("提示", "請輸入 Ticker")
                return
            self._insert_item(lbl, sym, sym)
            tk_var.set(""); lb_var.set("")
            dlg.focus_force()
        ttk.Button(dlg, text=f"{t('btn_ok')} (Enter 繼續新增)", command=_ok).pack(pady=8)
        dlg.bind("<Return>", lambda e: _ok())
        dlg.bind("<Escape>", lambda e: dlg.destroy())

    def _del_item(self):
        if not self.active_wl:
            return
        sel = self.item_tree.selection()
        if not sel:
            messagebox.showinfo("提示", t("err_no_select"))
            return
        ticker = sel[0]
        if not messagebox.askyesno("確認", f"確定從「{self.active_wl}」移除 {ticker}？"):
            return
        self.watchlists[self.active_wl] = [it for it in self.watchlists[self.active_wl] if it[1] != ticker]
        self._refresh_wl_list()
        self._refresh_items()
        self._save()
        self.status_var.set(f"已移除 {ticker}")

    def _on_item_double_click(self, event):
        sel = self.item_tree.selection()
        if not sel:
            return
        ticker = sel[0]
        wl_items = self.watchlists.get(self.active_wl, [])
        name = next((it[2] for it in wl_items if it[1] == ticker), ticker)
        ChartWindow(self.root, ticker, name, theme_mode=_get_effective_theme())

    def _refresh_all(self):
        self.btn_refresh.config(state=tk.DISABLED)
        self.btn_refresh_current.config(state=tk.DISABLED)
        self.status_var.set("正在更新（所有 WL）…請稍候")
        threading.Thread(target=self._worker_fetch, args=(None,), daemon=True).start()

    def _refresh_current_watchlist(self):
        if not self.active_wl:
            messagebox.showinfo("提示", t("err_no_wl"))
            return
        self.btn_refresh.config(state=tk.DISABLED)
        self.btn_refresh_current.config(state=tk.DISABLED)
        self.status_var.set(f"正在更新（{self.active_wl}）…請稍候")
        threading.Thread(target=self._worker_fetch, args=(self.active_wl,), daemon=True).start()

    def _worker_fetch(self, target_wl):
        if target_wl is None:
            tickers = {it[1] for items in self.watchlists.values() for it in items}
        else:
            tickers = {it[1] for it in self.watchlists.get(target_wl, [])}
        data = {tk_sym: fetch_price(tk_sym) for tk_sym in sorted(tickers)}
        def _apply():
            self.price_data = {**self.price_data, **data}
            self._refresh_items()
            self.btn_refresh.config(state=tk.NORMAL)
            self.btn_refresh_current.config(state=tk.NORMAL)
            self.status_var.set(f"更新完成 ({len(tickers)} 個標的，{_now_str()})")
        self.root.after(0, _apply)

def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        style.theme_use("clam")
    except Exception:
        pass
    app = WatchlistApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
