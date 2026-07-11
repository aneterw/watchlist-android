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
import pandas as pd
import re
import webbrowser
from typing import Any, List, Tuple, Dict, Optional

from tkinter import ttk, messagebox, simpledialog
import yfinance as yf
import math
import datetime
import json
import os
import threading
import subprocess

# === Windows 系統通知 ===
def _send_windows_notification(title: str, message: str):
    """發送 Windows 系統通知"""
    # 使用 PowerShell System.Windows.Forms.NotifyIcon（BalloonTip）
    try:
        ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms
$notify = New-Object System.Windows.Forms.NotifyIcon
$notify.Icon = [System.Drawing.SystemIcons]::Information
$notify.Visible = $true
$notify.ShowBalloonTip(10000, "{title}", "{message}", [System.Windows.Forms.ToolTipIcon]::Info)
Start-Sleep -Seconds 12
$notify.Dispose()
'''
        subprocess.Popen(
            ["powershell", "-Command", ps_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        # 後備：使用音效
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass

SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watchlist_data.json")

# 價格提醒設置：key=ticker, value={"high": float, "low": float, "high_triggered": bool, "low_triggered": bool}
PRICE_ALERTS = {}

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
    # US Large‑Cap equities
    ("AAPL","AAPL","Apple"),("MSFT","MSFT","Microsoft"),("GOOGL","GOOGL","Alphabet"),("GOOG","GOOG","Alphabet C"),("AMZN","AMZN","Amazon"),("NVDA","NVDA","NVIDIA"),("META","META","Meta"),("TSLA","TSLA","Tesla"),("BRK-A","BRK-A","Berkshire A"),("BRK-B","BRK-B","Berkshire B"),("LLY","LLY","Eli Lilly"),("AVGO","AVGO","Broadcom"),("JPM","JPM","JPMorgan"),("V","V","Visa"),("JNJ","JNJ","J&J"),("WMT","WMT","Walmart"),("XOM","XOM","Exxon"),("PG","PG","P&G"),("MA","MA","Mastercard"),("HD","HD","Home Depot"),("CVX","CVX","Chevron"),("MRK","MRK","Merck"),("KO","KO","Coca-Cola"),("PEP","PEP","PepsiCo"),("COST","COST","Costco"),("ADBE","ADBE","Adobe"),("MCD","MCD","McDonald's"),("CSCO","CSCO","Cisco"),("ACN","ACN","Accenture"),("NKE","NKE","Nike"),("TMO","TMO","Thermo Fisher"),("LIN","LIN","Linde"),("TMUS","TMUS","T-Mobile"),("VZ","VZ","Verizon"),("INTC","INTC","Intel"),("QCOM","QCOM","Qualcomm"),("TXN","TXN","Texas Instruments"),("HON","HON","Honeywell"),
    # US ETFs & indices
    ("SPY","SPY","SPDR S&P 500"),("QQQ","QQQ","Invesco QQQ"),("VGT","VGT","Vanguard Info Tech"),("IWM","IWM","iShares Russell 2000"),("EFA","EFA","iShares MSCI EAFE"),("EEM","EEM","iShares MSCI Emerging Markets"),("XLK","XLK","Technology Select SPDR"),("XLF","XLF","Financial Select SPDR"),
    # Asian equities
    ("2330.TW","2330.TW","台積電"),("2317.TW","2317.TW","鴻海"),("2454.TW","2454.TW","聯發科"),("2382.TW","2382.TW","廣達"),("2881.TW","2881.TW","富邦金"),("2882.TW","2882.TW","國泰金"),("3711.TW","3711.TW","日月光"),("2409.TW","2409.TW","友達"),("3481.TW","3481.TW","群創"),("2456.TW","2456.TW","台泥"),("2303.TW","2303.TW","聯電"),("1301.TW","1301.TW","台塑"),
    ("0700.HK","0700.HK","騰訊"),("9988.HK","9988.HK","阿里巴巴"),("00941.HK","00941.HK","中國移動"),("00939.HK","00939.HK","建設銀行"),("03690.HK","03690.HK","美團"),("01810.HK","01810.HK","小米"),("09618.HK","09618.HK","京東"),("00388.HK","00388.HK","港交所"),("00005.HK","00005.HK","匯豐"),
    # Chinese A‑shares
    ("601318.SS","601318.SS","中國平安"),("600519.SS","600519.SS","貴州茅台"),("000858.SZ","000858.SZ","五糧液"),("002594.SZ","002594.SZ","比亞迪"),("601398.SS","601398.SS","工商銀行"),("601899.SS","601899.SS","紫金礦業"),("601857.SS","601857.SS","中石油"),
    # Commodities & energy
    ("GC=F","GC=F","Gold"),("SI=F","SI=F","Silver"),("CL=F","CL=F","Crude Oil"),("NG=F","NG=F","Natural Gas"),("HG=F","HG=F","Copper"),("BZ=F","BZ=F","Brent Crude"),("PL=F","PL=F","Platinum"),("GLD","GLD","GLD ETF"),("SLV","SLV","SLV ETF"),("USO","USO","USO ETF"),
    # Forex pairs
    ("EURUSD=X","EURUSD=X","EUR/USD"),("USDJPY=X","USDJPY=X","USD/JPY"),("GBPUSD=X","GBPUSD=X","GBP/USD"),("AUDUSD=X","AUDUSD=X","AUD/USD"),("USDCNY=X","USDCNY=X","USD/CNY"),("USDHKD=X","USDHKD=X","USD/HKD"),("USDTWD=X","USDTWD=X","USD/TWD"),("USDKRW=X","USDKRW=X","USD/KRW"),
    # Cryptocurrencies
    ("BTC-USD","BTC-USD","Bitcoin"),("ETH-USD","ETH-USD","Ethereum"),("ADA-USD","ADA-USD","Cardano"),("DOGE-USD","DOGE-USD","Dogecoin"),
    # Fixed‑income & indices
    ("^TNX","^TNX","US 10Y"),("^VIX","^VIX","VIX"),("^GSPC","^GSPC","S&P 500 Index"),("^FTSE","^FTSE","FTSE 100"),("^DAX","^DAX","DAX"),("^N225","^N225","Nikkei 225"),("^HSI","^HSI","Hang Seng Index"),
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
    "btn_set_alert":{"zh-TW":"⚙ 設定提醒","zh-CN":"⚙ 设定提醒","en":"⚙ Set Alert","ja":"⚙ アラート設定","ko":"⚙ 알림 설정","es":"⚙ Configurar Alerta"},
    "dlg_add_title":{"zh-TW":"新增商品","zh-CN":"新增商品","en":"Add Item","ja":"商品追加","ko":"종목 추가","es":"Agregar"},
    "dlg_ticker_hint":{"zh-TW":"Ticker（例 AAPL、BTC-USD、005930.KS、EURUSD=X）：","zh-CN":"Ticker（例 AAPL、BTC-USD、005930.KS、EURUSD=X）：","en":"Ticker (e.g. AAPL, BTC-USD):","ja":"ティッカー（例 AAPL、BTC-USD）：","ko":"티커 (예 AAPL, BTC-USD):","es":"Ticker (ej. AAPL, BTC-USD):"},
    "dlg_label_hint":{"zh-TW":"顯示名稱（可空白）：","zh-CN":"显示名称（可空白）：","en":"Label (optional):","ja":"表示名（空白可）：","ko":"표시명 (공백 가능):","es":"Etiqueta (opcional):"},
    "btn_ok":{"zh-TW":"加入","zh-CN":"加入","en":"Add","ja":"追加","ko":"추가","es":"Agregar"},
    "chart_day":{"zh-TW":"日線","zh-CN":"日线","en":"Day","ja":"日足","ko":"일봉","es":"Día"},
    "chart_week":{"zh-TW":"週線","zh-CN":"周线","en":"Week","ja":"週足","ko":"주봉","es":"Semana"},
    "chart_month":{"zh-TW":"月線","zh-CN":"月线","en":"Month","ja":"月足","ko":"월봉","es":"Mes"},
    "ctx_fundamental":{"zh-TW":"基本面分析","zh-CN":"基本面分析","en":"Fundamental Analysis","ja":"ファンダメンタル分析","ko":"펀더멘탈 분석","es":"Análisis Fundamental"},
    "ctx_technical":{"zh-TW":"技術面分析","zh-CN":"技术面分析","en":"Technical Analysis","ja":"テクニカル分析","ko":"기술적 분석","es":"Análisis Técnico"},
    "ctx_news":{"zh-TW":"相關新聞","zh-CN":"相关新闻","en":"Related News","ja":"関連ニュース","ko":"관련 뉴스","es":"Noticias Relacionadas"},
    "fundamental_title":{"zh-TW":"基本面分析","zh-CN":"基本面分析","en":"Fundamental Analysis","ja":"ファンダメンタル分析","ko":"펀더멘탈 분석","es":"Análisis Fundamental"},
    "tab_fundamental":{"zh-TW":"基本面","zh-CN":"基本面","en":"Fundamental","ja":"ファンダ","ko":"펀더","es":"Fundamental"},
    "tab_technical":{"zh-TW":"技術面","zh-CN":"技术面","en":"Technical","ja":"テクニカル","ko":"기술","es":"Técnico"},
    "metric_company_name":{"zh-TW":"公司名稱","zh-CN":"公司名称","en":"Company","ja":"会社名","ko":"회사명","es":"Empresa"},
    "metric_market_cap":{"zh-TW":"市值","zh-CN":"市值","en":"Market Cap","ja":"時価総額","ko":"시가총액","es":"Cap. Mercado"},
    "metric_eps":{"zh-TW":"每股盈餘","zh-CN":"每股收益","en":"EPS","ja":"EPS","ko":"EPS","es":"EPS"},
    "metric_beta":{"zh-TW":"貝他值","zh-CN":"贝他值","en":"Beta","ja":"ベータ","ko":"베타","es":"Beta"},
    "metric_trailing_pe":{"zh-TW":"目前本益比","zh-CN":"当前市盈率","en":"Trailing PE","ja":"予想PER","ko":"추정PER","es":"PER TTM"},
    "metric_forward_pe":{"zh-TW":"預期本益比","zh-CN":"预期市盈率","en":"Forward PE","ja":"先行PER","ko":"선행PER","es":"PER Adelantado"},
    "metric_peg":{"zh-TW":"本益成長比","zh-CN":"市盈率增长比","en":"PEG","ja":"PEG","ko":"PEG","es":"PEG"},
    "metric_price_book":{"zh-TW":"股價淨值比","zh-CN":"市净率","en":"Price/Book","ja":"PBR","ko":"PBR","es":"Precio/Valor"},
    "metric_roe":{"zh-TW":"股東權益報酬率","zh-CN":"净资产收益率","en":"ROE","ja":"ROE","ko":"ROE","es":"ROE"},
    "metric_roa":{"zh-TW":"資產報酬率","zh-CN":"资产收益率","en":"ROA","ja":"ROA","ko":"ROA","es":"ROA"},
    "metric_op_margin":{"zh-TW":"營業利潤率","zh-CN":"营业利润率","en":"Op. Margin","ja":"営業利益率","ko":"영업이익률","es":"Margen Op."},
    "metric_profit_margin":{"zh-TW":"利潤率","zh-CN":"利润率","en":"Profit Margin","ja":"利益率","ko":"이익률","es":"Margen Benef."},
    "metric_fcf":{"zh-TW":"自由現金流","zh-CN":"自由现金流","en":"FCF","ja":"FCF","ko":"FCF","es":"FCF"},
    "metric_quick_ratio":{"zh-TW":"速動比率","zh-CN":"速动比率","en":"Quick Ratio","ja":"当座比率","ko":"당좌비율","es":"Ratio Rápido"},
    "metric_debt_equity":{"zh-TW":"債務權益比","zh-CN":"负债权益比","en":"Debt/Equity","ja":"DE比","ko":"부채비율","es":"Deuda/Capital"},
    "metric_target_mean":{"zh-TW":"分析師平均目標價","zh-CN":"分析师平均目标价","en":"Analyst Target (Avg)","ja":"アナリスト目標(平均)","ko":"애널리스트 목표(평균)","es":"Objetivo Analista (Prom)"},
    "metric_target_median":{"zh-TW":"分析師中位數目標價","zh-CN":"分析师中位数目标价","en":"Analyst Target (Med)","ja":"アナリスト目標(中央)","ko":"애널리스트 목표(중앙)","es":"Objetivo Analista (Med)"},
    "metric_analyst_count":{"zh-TW":"評估分析師人數","zh-CN":"评估分析师人数","en":"Analyst Count","ja":"アナリスト数","ko":"애널리스트 수","es":"Nº Analistas"},
    "metric_insider_pct":{"zh-TW":"內部人持股","zh-CN":"内部人持股","en":"Insider %","ja":"内部者保有率","ko":"인사이드 보유율","es":"% Insiders"},
    "metric_inst_pct":{"zh-TW":"機構持股","zh-CN":"机构持股","en":"Institutional %","ja":"機関投資家保有率","ko":"기관 보유율","es":"% Instituc."},
    "metric_ev_ebitda":{"zh-TW":"企業價值/EBITDA","zh-CN":"企业价值/EBITDA","en":"EV/EBITDA","ja":"EV/EBITDA","ko":"EV/EBITDA","es":"EV/EBITDA"},
    "metric_dividend_yield":{"zh-TW":"殖利率","zh-CN":"股息率","en":"Div. Yield","ja":"配当利回り","ko":"배당수익률","es":"Rend. Divid."},
    "theme_menu":{"zh-TW":"主題","zh-CN":"主题","en":"Theme","ja":"テーマ","ko":"테마","es":"Tema"},
    "lang_menu":{"zh-TW":"語言","zh-CN":"语言","en":"Language","ja":"言語","ko":"언어","es":"Idioma"},
    "font_menu":{"zh-TW":"字體","zh-CN":"字体","en":"Font","ja":"フォント","ko":"글꼴","es":"Fuente"},
    "font_family":{"zh-TW":"字體：","zh-CN":"字体：","en":"Font:","ja":"フォント：","ko":"글꼴:","es":"Fuente:"},
    "font_size":{"zh-TW":"大小：","zh-CN":"大小：","en":"Size:","ja":"サイズ：","ko":"크기:","es":"Tamaño:"},
    "err_no_wl":{"zh-TW":"請先選擇一個 Watchlist","zh-CN":"请先选择一个 Watchlist","en":"Please select a Watchlist","ja":"Watchlist を選択してください","ko":"관심종목을 선택하세요","es":"Selecciona una Watchlist primero"},
    "err_no_select":{"zh-TW":"請先在列表中點選一個項目","zh-CN":"请先在列表中点选一个项目","en":"Please select an item in the list","ja":"リストから項目を選択してください","ko":"목록에서 항목을 선택하세요","es":"Selecciona un elemento en la lista"},
    "alert_title":{"zh-TW":"價格提醒設定","zh-CN":"价格提醒设定","en":"Price Alert Settings","ja":"価格アラート設定","ko":"가격 알림 설정","es":"Configuración de Alerta"},
    "alert_high":{"zh-TW":"高價提醒（高於此價格拉通知）：","zh-CN":"高价提醒（高于此价格通知）：","en":"High Price Alert (notify when above):","ja":"高値アラート（この値以上で通知）：","ko":"고가 알림 (이 가격 이상일 때):","es":"Alerta Alta (notificar cuando esté arriba de):"},
    "alert_low":{"zh-TW":"低價提醒（低於此價格拉通知）：","zh-CN":"低价提醒（低于此价格通知）：","en":"Low Price Alert (notify when below):","ja":"安値アラート（この値以下で通知）：","ko":"저가 알림 (이 가격 이하일 때):","es":"Alerta Baja (notificar cuando esté debajo de):"},
    "alert_clear":{"zh-TW":"清除提醒","zh-CN":"清除提醒","en":"Clear Alerts","ja":"アラートをクリア","ko":"알림 지우기","es":"Borrar Alertas"},
    "alert_none":{"zh-TW":"（不設定）","zh-CN":"（不设定）","en":"(no alert)","ja":"（設定なし）","ko":"（설정 안함）","es":"(sin alerta)"},
    "alert_saved":{"zh-TW":"提醒已設定","zh-CN":"提醒已设定","en":"Alert saved","ja":"アラート設定完了","ko":"알림 설정됨","es":"Alerta guardada"},
    "alert_high_triggered":{"zh-TW":"🚨 高價提醒：{ticker} 已漲至 {price}（提醒價：{target}）","zh-CN":"🚨 高价提醒：{ticker} 已涨至 {price}（提醒价：{target}）","en":"🚨 High Alert: {ticker} rose to {price} (alert at {target})","ja":"🚨 高値アラート：{ticker} が {price} に上昇（設定値：{target}）","ko":"🚨 고가 알림：{ticker} 이(가) {price} 로 상승（설정가：{target}）","es":"🚨 Alerta Alta: {ticker} subió a {price} (alerta en {target})"},
    "alert_low_triggered":{"zh-TW":"📉 低價提醒：{ticker} 已跌至 {price}（提醒價：{target}）","zh-CN":"📉 低价提醒：{ticker} 已跌至 {price}（提醒价：{target}）","en":"📉 Low Alert: {ticker} dropped to {price} (alert at {target})","ja":"📉 安値アラート：{ticker} が {price} に下落（設定値：{target}）","ko":"📉 저가 알림：{ticker} 이(가) {price} 로 하락（설정가：{target}）","es":"📉 Alerta Baja: {ticker} bajó a {price} (alerta en {target})"},
    "btn_save_alert":{"zh-TW":"儲存","zh-CN":"储存","en":"Save","ja":"保存","ko":"저장","es":"Guardar"},
    "alert_set_title":{"zh-TW":"設定「{ticker}」的提醒","zh-CN":"设定「{ticker}」的提醒","en":"Set alerts for {ticker}","ja":"「{ticker}」のアラート設定","ko":"{ticker} 알림 설정","es":"Configurar alertas para {ticker}"},
    "alert_list_label":{"zh-TW":"已設定的提醒：","zh-CN":"已设定的提醒：","en":"Current Alerts:","ja":"設定されたアラート：","ko":"설정된 알림:","es":"Alertas Configuradas:"},
    "btn_delete_selected":{"zh-TW":"刪除所選","zh-CN":"删除所选","en":"Delete Selected","ja":"選択を削除","ko":"선택 삭제","es":"Eliminar Seleccionado"},
    "btn_reset_triggered":{"zh-TW":"重置已觸發","zh-CN":"重置已触发","en":"Reset Triggered","ja":"トリガー解除","ko":"트리거 초기화","es":"Restablecer Disparados"},
    "alert_high_label":{"zh-TW":"高","zh-CN":"高","en":"High","ja":"高","ko":"고","es":"Alto"},
    "alert_low_label":{"zh-TW":"低","zh-CN":"低","en":"Low","ja":"低","ko":"저","es":"Bajo"},
    "alert_triggered":{"zh-TW":"已觸發","zh-CN":"已触发","en":"triggered","ja":"トリガー済み","ko":"트리거됨","es":"disparado"},
    "btn_add_continue":{"zh-TW":"加入（Enter 繼續新增）","zh-CN":"加入（Enter 继续新增）","en":"Add (Enter to continue adding)","ja":"追加（Enter で追加継続）","ko":"추가 (Enter로 추가 계속)","es":"Agregar (Enter para seguir agregando)"},
    "btn_cancel_zh":{"zh-TW":"取消","zh-CN":"取消","en":"Cancel","ja":"キャンセル","ko":"취소","es":"Cancelar"},
    "err_wl_name":{"zh-TW":"請輸入名稱","zh-CN":"请输入名称","en":"Enter name","ja":"名前を入力","ko":"이름 입력","es":"Ingrese nombre"},
    "err_search_select":{"zh-TW":"請先在搜尋結果中點選一個項目","zh-CN":"请先在搜寻结果中点选一个项目","en":"Select an item from search results","ja":"検索結果から項目を選択","ko":"검색 결과에서 항목 선택","es":"Seleccione un elemento de los resultados"},
    "err_ticker_input":{"zh-TW":"請輸入 Ticker","zh-CN":"请输入 Ticker","en":"Enter Ticker","ja":"ティッカーを入力","ko":"티커 입력","es":"Ingrese Ticker"},
    "err_alert_high_num":{"zh-TW":"高價提醒請輸入數字","zh-CN":"高价提醒请输入数字","en":"Enter a valid number for high alert","ja":"高値アラートに数値を入力","ko":"고가 알림에 숫자 입력","es":"Ingrese un número válido para alerta alta"},
    "err_alert_low_num":{"zh-TW":"低價提醒請輸入數字","zh-CN":"低价提醒请输入数字","en":"Enter a valid number for low alert","ja":"安値アラートに数値を入力","ko":"저가 알림에 숫자 입력","es":"Ingrese un número válido para alerta baja"},
    "dialog_new_wl":{"zh-TW":"新增 Watchlist","zh-CN":"新增 Watchlist","en":"New Watchlist","ja":"新規 Watchlist","ko":"새 관심종목","es":"Nueva Watchlist"},
}

def _init_lang() -> None:
    """Initialize language dict if needed – currently a no‑op because LANG defined earlier."""
    global LANG
    # No additional init required

def t(key: str) -> str:
    global LANG
    return LANG.get(key, {}).get(CURRENT_LANG, key)

CURRENT_LANG = "zh-TW"
CURRENT_THEME = "system"
CURRENT_FONT_FAMILY = ["微軟正黑體"]
CURRENT_FONT_SIZE = [13]

def get_font(size: int = None) -> tuple:
    """Return font tuple using current font family and size."""
    return (CURRENT_FONT_FAMILY[0], size or CURRENT_FONT_SIZE[0])

def get_installed_fonts() -> list[str]:
    """Get list of commonly available Chinese/Unicode fonts on Windows."""
    import tkinter.font as tkfont
    try:
        families = set(tkfont.families())
    except Exception:
        families = set()
    # Common fonts to prioritize
    priority = ["微軟正黑體", "Microsoft JhengHei", "新細明體", "PMingLiU",
                "標楷體", "DFKai-SB", "細明體", "SimHei", "SimSun",
                "Arial", "Tahoma", "Times New Roman", "Courier New"]
    result = []
    for f in priority:
        if f in families:
            result.append(f)
    for f in sorted(families):
        if f not in result and not f.startswith("@"):
            result.append(f)
    return result

# Font list will be populated dynamically
INSTALLED_FONTS = []

def _fmt_price(val: Any) -> str:
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

def _load_dynamic_tickers() -> list[tuple[str, str, str]]:
    """Load ticker symbols from a local static file.
    The file ``top250_tickers.json`` (placed next to this script) should contain a
    JSON object with a ``"tickers"`` list of ``[display, ticker, name]`` entries.
    If the file is missing or malformed, a minimal fallback from
    ``fallback_tickers.json`` is used. No network access is performed.
    Returns a list of ``(display, ticker, name)`` tuples.
    """
    import json, os
    base_dir = os.path.dirname(__file__)
    primary_path = os.path.join(base_dir, "top250_tickers.json")
    # Try primary static file (expected to contain the full top‑250 lists)
    if os.path.exists(primary_path):
        try:
            with open(primary_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            tickers = data.get("tickers", [])
            if tickers:
                print(f"[Dynamic] 使用本地 top250 檔案 ({len(tickers)} 條)")
                return tickers
        except Exception as e:
            print("[Dynamic] 讀取 top250_tickers.json 失敗:", e)
    # Fallback to tiny hard‑coded set stored in fallback_tickers.json
    fallback_path = os.path.join(base_dir, "fallback_tickers.json")
    try:
        with open(fallback_path, "r", encoding="utf-8") as f:
            fb = json.load(f)
        tickers = fb.get("tickers", [])
        print(f"[Dynamic] 使用備援檔案 ({len(tickers)} 條)")
        return tickers
    except Exception as e:
        print("[Dynamic] 讀取備援檔案失敗:", e)
        return []

# Merge static COMMON_TICKERS with dynamic list (dynamic may contain duplicates)
# Load dynamic tickers and report count
DYNAMIC_TICKERS = _load_dynamic_tickers()
print(f"Loaded {len(DYNAMIC_TICKERS)} dynamic tickers")
ALL_TICKERS = COMMON_TICKERS + DYNAMIC_TICKERS

def search_yfinance(query, limit=12):
    if not query or not query.strip():
        return []
    q = query.strip().upper()
    results = []
    # Search combined static + dynamic list
    for _, tk_sym, nm in ALL_TICKERS:
        if q == tk_sym.upper() or q == nm.upper():
            results.append((f"{tk_sym} - {nm}", tk_sym, nm))
    if results:
        return results[:limit]
    for _, tk_sym, nm in ALL_TICKERS:
        if tk_sym.upper().startswith(q):
            results.append((f"{tk_sym} - {nm}", tk_sym, nm))
    if len(results) >= limit:
        return results[:limit]
    for _, tk_sym, nm in ALL_TICKERS:
        if q in nm.upper():
            results.append((f"{tk_sym} - {nm}", tk_sym, nm))
    if len(results) >= limit:
        return results[:limit]
    # Removed yfinance.search fallback because it raises 'module' object is not callable
    # If needed, a proper API call can be added here.
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
                        "lang": CURRENT_LANG, "theme": CURRENT_THEME,
                        "font_family": CURRENT_FONT_FAMILY[0],
                        "font_size": CURRENT_FONT_SIZE[0],
                        "alerts": PRICE_ALERTS},
                       f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("save error:", e)

def load_watchlists():
    global PRICE_ALERTS, CURRENT_FONT_FAMILY, CURRENT_FONT_SIZE
    if not os.path.exists(SAVE_FILE):
        return None, None, None, None, None, None
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        wl = data.get("watchlists", {})
        restored = {n: [tuple(it) if isinstance(it, list) else it for it in v] for n, v in wl.items()}
        PRICE_ALERTS = data.get("alerts", {})
        font_family = data.get("font_family", "微軟正黑體")
        font_size = data.get("font_size", 13)
        CURRENT_FONT_FAMILY[0] = font_family
        CURRENT_FONT_SIZE[0] = font_size
        return restored, data.get("active_wl"), data.get("lang"), data.get("theme"), font_family, font_size
    except Exception as e:
        print("load error:", e)
        return None, None, None, None, None, None

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
    # 统一灰色系 - 日间模式用淡一点的灰色
    main_gray = "#1a1a1a" if is_dark else "#c0c0c0"
    text_gray = "#cccccc" if is_dark else "#1a1a1a"
    btn_gray = "#2a2a2a" if is_dark else "#b5b5b5"
    btn_text = "#cccccc" if is_dark else "#000000"
    sel_gray = "#2a5a8a" if is_dark else "#8090a8"

    root.configure(bg=main_gray)
    style.theme_use("clam")
    style.configure(".", background=main_gray, foreground=text_gray)
    style.configure("TFrame", background=main_gray)
    style.configure("TLabel", background=main_gray, foreground=text_gray)
    style.configure("TButton", background=btn_gray, foreground=btn_text)
    style.configure("TCheckbutton", background=main_gray, foreground=text_gray)
    style.configure("TRadiobutton", background=main_gray, foreground=text_gray)
    style.map("TButton", background=[("active", btn_gray)])
    style.configure("TLabelframe", background=main_gray, foreground=text_gray)
    style.configure("TLabelframe.Label", background=main_gray, foreground=text_gray)
    style.configure("TEntry", fieldbackground=main_gray, foreground=text_gray,
                    bordercolor=text_gray)
    style.configure("Treeview", background=main_gray, foreground=text_gray,
                    fieldbackground=main_gray, bordercolor=text_gray, font=get_font())
    style.configure("Treeview.Heading", background=btn_gray, foreground=btn_text, font=get_font())
    style.map("Treeview", background=[("selected", sel_gray)], foreground=[("selected", btn_text)])
    try:
        root.option_add("*Menu.background", main_gray)
        root.option_add("*Menu.foreground", text_gray)
        root.option_add("*Menu.activeBackground", sel_gray)
        root.option_add("*Menu.activeForeground", btn_text)
    except Exception:
        pass

    # 存储统一颜色供所有组件使用
    # 暗黑模式下输入框背景更浅以便与按钮区分
    entry_bg = "#3a3a3a" if is_dark else main_gray
    entry_border = "#666666" if is_dark else "#808080"
    root._theme_colors = {
        "bg": main_gray, "fg": text_gray, "panel": main_gray,
        "entry_bg": entry_bg, "entry_fg": text_gray, "entry_border": entry_border,
        "btn_bg": btn_gray, "btn_fg": btn_text, "btn_active": btn_gray,
        "list_bg": main_gray, "list_fg": text_gray, "list_sel": sel_gray
    }


class FundamentalAnalysisWindow:
    """基本面分析視窗：顯示估值與財務指標"""
    def __init__(self, parent, ticker, name, theme_mode="light"):
        self.ticker = ticker
        self.name = name
        self.theme_mode = theme_mode

        self.win = tk.Toplevel(parent)
        self.win.title(f"{ticker} - {name} - {t('fundamental_title')}")
        # 長寬高分別增加
        self.win.geometry("1400x680")
        self.win.transient(parent)
        self.win.minsize(1000, 550)

        # Center window on screen
        self.win.update_idletasks()
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        w, h = 1400, 680
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        # Notebook for tabs
        nb = ttk.Notebook(self.win)
        nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # === Fundamental Tab ===
        fund_frame = ttk.Frame(nb)
        nb.add(fund_frame, text=t("tab_fundamental"))

        # Canvas with scrollbar
        canvas = tk.Canvas(fund_frame, bg=self._bg(), highlightthickness=0)
        scrollbar = ttk.Scrollbar(fund_frame, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self._bg())

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add mousewheel scrolling
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                pass
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self._canvas = canvas
        self._scroll_frame = scroll_frame

        # === Technical Tab (K-line chart - same as double-click) ===
        tech_frame = ttk.Frame(nb)
        nb.add(tech_frame, text=t("tab_technical"))

        self._tech_frame = tech_frame
        self._period_var = tk.StringVar(value="day")
        tab_frame = ttk.Frame(tech_frame)
        tab_frame.pack(fill=tk.X, padx=8, pady=4)
        for p, lbl in [("day", t("chart_day")), ("week", t("chart_week")), ("month", t("chart_month"))]:
            ttk.Radiobutton(tab_frame, text=lbl, variable=self._period_var, value=p,
                            command=self._draw_tech).pack(side=tk.LEFT, padx=6)

        self._fig_frame = ttk.Frame(tech_frame)
        self._fig_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        # Load fundamental data
        self._load_fundamental()

        # Draw initial tech chart
        self._init_tech_chart()

    def _bg(self):
        return "#1a1a1a" if self.theme_mode == "dark" else "#ffffff"

    def _fg(self):
        return "#cccccc" if self.theme_mode == "dark" else "#1a1a1a"

    def _label_bg(self):
        return "#2a2a2a" if self.theme_mode == "dark" else "#e0e0e0"

    def _value_bg(self):
        return "#3a3a3a" if self.theme_mode == "dark" else "#ffffff"

    def _positive_color(self):
        return "#66ff66" if self.theme_mode == "dark" else "#006600"

    def _negative_color(self):
        return "#ff6666" if self.theme_mode == "dark" else "#cc0000"

    def _init_tech_chart(self):
        """Initialize matplotlib for technical chart"""
        try:
            import matplotlib
            matplotlib.use("TkAgg")
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
            import pandas as pd
            import numpy as np
            self._FigureCanvasTkAgg = FigureCanvasTkAgg
            self._Figure = Figure
            self._pd = pd
            self._np = np
            self._draw_tech()
        except Exception as e:
            ttk.Label(self._fig_frame, text=f"Chart library error: {e}").pack(padx=20, pady=20)

    def _draw_tech(self):
        """Draw K-line chart in technical tab"""
        for w in self._fig_frame.winfo_children():
            w.destroy()

        interval, period = self._params()
        try:
            raw = yf.Ticker(self.ticker).history(period=period, interval=interval)
        except Exception as e:
            ttk.Label(self._fig_frame, text=f"{self.ticker}: fetch error {e}").pack(padx=20, pady=20)
            return
        if raw is None or raw.empty:
            ttk.Label(self._fig_frame, text=f"{self.ticker}: 無資料").pack(padx=20, pady=20)
            return

        raw = raw.tail(200)
        dates = [d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d) for d in raw.index]
        n = len(raw)

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

        fig = self._Figure(figsize=(8, 6), dpi=100)
        fig.patch.set_facecolor(bg)
        ax_k = fig.add_axes([0.07, 0.40, 0.90, 0.36])
        ax_v = fig.add_axes([0.07, 0.29, 0.90, 0.10], sharex=ax_k)
        ax_kd = fig.add_axes([0.07, 0.08, 0.90, 0.19], sharex=ax_k)

        for ax in (ax_k, ax_v, ax_kd):
            ax.set_facecolor(bg)
            ax.grid(True, color=grid_c, linestyle="--", linewidth=0.4)
            for sp in ax.spines.values():
                sp.set_edgecolor(grid_c)

        title = f"{self.ticker}  {self.name}  [{self._period_var.get().upper()} CHART]"
        ax_k.set_title(title, color=txt_c, fontsize=10, fontweight="bold", loc="left")
        ax_k.set_ylabel("Price", color=txt_c, fontsize=8)
        ax_k.tick_params(colors=txt_c, labelsize=7, left=True, bottom=False, labelbottom=False)
        ax_k.set_xlim(-0.5, n - 0.5)

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

        # Volume
        v_arr = self._pd.to_numeric(self._pd.Series(v), errors="coerce").values
        v_arr = self._np.nan_to_num(v_arr, nan=0.0)
        vmax = float(v_arr.max()) if v_arr.size and v_arr.max() > 0 else 1.0
        vnorm = v_arr / max(vmax, 1.0)
        xpos = list(range(n))
        colors_v = [up_c if c[i] >= o[i] else dn_c for i in range(n)]
        ax_v.bar(xpos, vnorm, color=colors_v, width=0.6)
        ax_v.set_ylabel("Vol", color=txt_c, fontsize=6)
        ax_v.tick_params(colors=txt_c, labelsize=6, left=True, bottom=False, labelbottom=False)

        # KD
        low9 = self._pd.Series(l).rolling(9, min_periods=1).min().values
        hi9 = self._pd.Series(h).rolling(9, min_periods=1).max().values
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

        step = max(1, n // 8)
        xt = list(range(0, n, step))
        if xt and xt[-1] != n - 1:
            xt.append(n - 1)
        ax_kd.set_xticks(xt)
        ax_kd.set_xticklabels([dates[i] for i in xt], rotation=0, ha="center",
                             fontsize=7, color=txt_c)

        canvas = self._FigureCanvasTkAgg(fig, master=self._fig_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _params(self):
        p = self._period_var.get()
        if p == "day":
            return "1d", "2y"
        elif p == "week":
            return "1wk", "10y"
        else:
            return "1mo", "30y"

    def _load_fundamental(self):
        """Load and display fundamental analysis data"""
        def worker():
            try:
                ticker_obj = yf.Ticker(self.ticker)
                info = ticker_obj.info

                metrics = {
                    t("metric_company_name"): info.get("longName") or info.get("shortName") or self.ticker,
                    t("metric_market_cap"): self._fmt_market_cap(info.get("marketCap")),
                    t("metric_eps"): self._fmt_eps(info.get("trailingEps")),
                    t("metric_beta"): self._fmt_number(info.get("beta")),
                    t("metric_trailing_pe"): self._fmt_number(info.get("trailingPE")),
                    t("metric_forward_pe"): self._fmt_number(info.get("forwardPE")),
                    t("metric_peg"): self._fmt_number(info.get("pegRatio")),
                    t("metric_price_book"): self._fmt_number(info.get("priceToBook")),
                    t("metric_roe"): self._fmt_pct(info.get("returnOnEquity")),
                    t("metric_roa"): self._fmt_pct(info.get("returnOnAssets")),
                    t("metric_op_margin"): self._fmt_pct(info.get("operatingMargins")),
                    t("metric_profit_margin"): self._fmt_pct(info.get("profitMargins")),
                    t("metric_fcf"): self._fmt_money(info.get("freeCashflow")),
                    t("metric_quick_ratio"): self._fmt_number(info.get("quickRatio")),
                    t("metric_target_mean"): self._fmt_price(info.get("targetMeanPrice")),
                    t("metric_target_median"): self._fmt_price(info.get("targetMedianPrice")),
                    t("metric_analyst_count"): self._fmt_number(info.get("numberOfAnalystOpinions")),
                    t("metric_insider_pct"): self._fmt_pct(info.get("heldPercentInsiders")),
                    t("metric_inst_pct"): self._fmt_pct(info.get("heldPercentInstitutions")),
                    t("metric_ev_ebitda"): self._fmt_number(info.get("enterpriseToEbitda")),
                    t("metric_dividend_yield"): self._fmt_yield(info.get("dividendYield")),
                }

                self.win.after(0, lambda: self._display_metrics(metrics))
            except Exception as e:
                self.win.after(0, lambda: self._show_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _fmt_market_cap(self, val):
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return "N/A"
        if isinstance(val, (int, float)):
            if val >= 1e12:
                return f"${val/1e12:.2f}T"
            elif val >= 1e9:
                return f"${val/1e9:.2f}B"
            elif val >= 1e6:
                return f"${val/1e6:.2f}M"
            else:
                return f"${val:,.0f}"
        return str(val)

    def _fmt_pct(self, val):
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return "N/A"
        if isinstance(val, (int, float)):
            return f"{val*100:.2f}%"
        return str(val)

    def _fmt_eps(self, val):
        """EPS - not percentage, show as decimal currency"""
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return "N/A"
        if isinstance(val, (int, float)):
            return f"${val:.2f}"
        return str(val)

    def _fmt_number(self, val):
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return "N/A"
        if isinstance(val, (int, float)):
            return f"{val:.2f}"
        return str(val)

    def _fmt_money(self, val):
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return "N/A"
        if isinstance(val, (int, float)):
            if val >= 1e12:
                return f"${val/1e12:.2f}T"
            elif val >= 1e9:
                return f"${val/1e9:.2f}B"
            elif val >= 1e6:
                return f"${val/1e6:.2f}M"
            else:
                return f"${val:,.0f}"
        return str(val)

    def _fmt_yield(self, val):
        if val is None:
            return "N/A"
        if isinstance(val, (int, float)):
            return f"{val:.2f}%"
        return str(val)

    def _fmt_price(self, val):
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return "N/A"
        if isinstance(val, (int, float)):
            return f"${val:.2f}"
        return str(val)

    def _display_metrics(self, metrics: dict):
        """Display metrics in scroll frame - horizontal layout"""
        label_bg = self._label_bg()
        value_bg = self._value_bg()
        fg = self._fg()
        pos_color = self._positive_color()
        neg_color = self._negative_color()

        # Company name header - 18pt
        company_name = metrics.get(t("metric_company_name"), self.ticker)
        header = tk.Label(self._scroll_frame, text=company_name, font=get_font(18),
                         bg=self._bg(), fg=fg, anchor=tk.W)
        header.pack(fill=tk.X, padx=10, pady=(10, 5))

        # Separator
        sep = tk.Frame(self._scroll_frame, height=2, bg=fg)
        sep.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Collect metrics (skip company name)
        items = [(k, v) for k, v in metrics.items() if k != t("metric_company_name")]

        # Number of columns
        num_cols = 2
        # Split items into columns
        col_size = (len(items) + num_cols - 1) // num_cols
        columns = [items[i:i + col_size] for i in range(0, len(items), col_size)]

        # Create horizontal container
        h_frame = tk.Frame(self._scroll_frame, bg=self._bg())
        h_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        for col_items in columns:
            # Column frame
            col_frame = tk.Frame(h_frame, bg=self._bg())
            col_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            for key, value in col_items:
                # Determine value color
                val_color = fg
                if key in [t("metric_roe"), t("metric_roa"), t("metric_op_margin"),
                           t("metric_profit_margin")] and value != "N/A":
                    try:
                        num_val = float(value.rstrip("%")) / 100
                        val_color = pos_color if num_val > 0 else neg_color
                    except (ValueError, AttributeError):
                        pass

                row_frame = tk.Frame(col_frame, bg=self._bg())
                row_frame.pack(fill=tk.X, padx=5, pady=2)

                # Metrics font size 14pt
                lbl = tk.Label(row_frame, text=key, width=20, font=get_font(14),
                              bg=label_bg, fg=fg, anchor=tk.W, padx=5)
                lbl.pack(side=tk.LEFT, padx=(0, 2))

                val_lbl = tk.Label(row_frame, text=value, width=18, font=get_font(14),
                                  bg=value_bg, fg=val_color, anchor=tk.E, padx=5)
                val_lbl.pack(side=tk.LEFT)

        # Update scroll region
        self._scroll_frame.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _show_error(self, msg: str):
        error_lbl = tk.Label(self._scroll_frame, text=f"載入失敗: {msg}",
                            font=get_font(), bg=self._bg(), fg="#ff6666")
        error_lbl.pack(padx=20, pady=20)


class NewsWindow:
    """新聞視窗：顯示個股相關新聞"""
    def __init__(self, parent, ticker, name, theme_mode="light"):
        self.ticker = ticker
        self.name = name
        self.theme_mode = theme_mode

        self.win = tk.Toplevel(parent)
        self.win.title(f"{ticker} - {name} - {t('ctx_news')}")
        self.win.geometry("1200x800")
        self.win.transient(parent)
        self.win.minsize(800, 400)

        # Center window on screen
        self.win.update_idletasks()
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        w, h = 1200, 800
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        # Main frame
        main_frame = tk.Frame(self.win, bg=self._bg())
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas with scrollbar
        canvas = tk.Canvas(main_frame, bg=self._bg(), highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self._bg())

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Mousewheel scrolling
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                pass
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self._canvas = canvas
        self._scroll_frame = scroll_frame

        # Load news
        self._load_news()

        # Cleanup on close
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

    def _bg(self):
        return "#1a1a1a" if self.theme_mode == "dark" else "#ffffff"

    def _fg(self):
        return "#cccccc" if self.theme_mode == "dark" else "#1a1a1a"

    def _label_bg(self):
        return "#2a2a2a" if self.theme_mode == "dark" else "#e0e0e0"

    def _on_close(self):
        if self._canvas and self._canvas.winfo_exists():
            self._canvas.unbind_all("<MouseWheel>")
        self.win.destroy()

    def _open_link(self, url):
        """Open URL in default browser"""
        if url and url != "（無連結）":
            webbrowser.open(url)

    def _load_news(self):
        """Load and display news"""
        def worker():
            try:
                stock = yf.Ticker(self.ticker)
                news_list = stock.news or []

                if not news_list:
                    self.win.after(0, lambda: self._display_empty())
                    return

                # Extract news data (up to 10)
                news_data = []
                for news in news_list[:10]:
                    content = news.get("content", {})
                    title = content.get("title", "（無標題）")
                    link_dict = content.get("clickThroughUrl", {})
                    link = link_dict.get("url", "") if isinstance(link_dict, dict) else ""
                    provider_dict = content.get("provider", {})
                    publisher = provider_dict.get("displayName", "未知來源") if isinstance(provider_dict, dict) else "未知來源"
                    pub_date = content.get("pubDate", "")
                    # Format time
                    if "T" in pub_date:
                        pub_date = pub_date.replace("T", " ").replace("Z", " UTC")

                    news_data.append({
                        "title": title,
                        "link": link,
                        "publisher": publisher,
                        "pub_date": pub_date or "未知時間"
                    })

                self.win.after(0, lambda: self._display_news(news_data))
            except Exception as e:
                self.win.after(0, lambda: self._show_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _display_news(self, news_data: list):
        """Display news in scroll frame"""
        bg = self._bg()
        fg = self._fg()
        label_bg = self._label_bg()

        # Header
        header = tk.Label(self._scroll_frame, text=f"{self.ticker} {t('ctx_news')}",
                         font=get_font(20), bg=bg, fg=fg, anchor=tk.W)
        header.pack(fill=tk.X, padx=10, pady=(10, 5))

        # Separator
        sep = tk.Frame(self._scroll_frame, height=2, bg=fg)
        sep.pack(fill=tk.X, padx=10, pady=(0, 10))

        for idx, news in enumerate(news_data):
            # News item frame
            item_frame = tk.Frame(self._scroll_frame, bg=label_bg)
            item_frame.pack(fill=tk.X, padx=10, pady=5)

            # Source and time
            meta_text = f"[{news['publisher']}] - {news['pub_date']}"
            meta_lbl = tk.Label(item_frame, text=meta_text, font=get_font(12),
                               bg=label_bg, fg="#888888", anchor=tk.W)
            meta_lbl.pack(fill=tk.X, padx=5, pady=(5, 2))

            # Title (clickable)
            title_lbl = tk.Label(item_frame, text=news["title"], font=get_font(14),
                                bg=label_bg, fg="#5588ff" if news["link"] else fg,
                                anchor=tk.W, cursor="hand2")
            title_lbl.pack(fill=tk.X, padx=5, pady=(0, 2))

            if news["link"]:
                title_lbl.bind("<Button-1>", lambda e, url=news["link"]: self._open_link(url))
                title_lbl.bind("<Enter>", lambda e, l=title_lbl: l.config(fg="#ffaa00"))
                title_lbl.bind("<Leave>", lambda e, l=title_lbl: l.config(fg="#5588ff"))

            # Link text
            if news["link"]:
                link_lbl = tk.Label(item_frame, text=f"🔗 {news['link']}",
                                   font=get_font(12), bg=label_bg, fg="#666666",
                                   anchor=tk.W, cursor="hand2")
                link_lbl.pack(fill=tk.X, padx=5, pady=(0, 5))
                link_lbl.bind("<Button-1>", lambda e, url=news["link"]: self._open_link(url))
                link_lbl.bind("<Enter>", lambda e, l=link_lbl: l.config(fg="#ffaa00"))
                link_lbl.bind("<Leave>", lambda e, l=link_lbl: l.config(fg="#666666"))

        # Update scroll region
        self._scroll_frame.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _display_empty(self):
        """Display when no news found"""
        bg = self._bg()
        fg = self._fg()
        empty_lbl = tk.Label(self._scroll_frame, text=f"{self.ticker} 無相關新聞",
                            font=get_font(14), bg=bg, fg=fg, padx=20, pady=20)
        empty_lbl.pack()

    def _show_error(self, msg: str):
        """Display error message"""
        bg = self._bg()
        error_lbl = tk.Label(self._scroll_frame, text=f"載入失敗: {msg}",
                            font=get_font(), bg=bg, fg="#ff6666", padx=20, pady=20)
        error_lbl.pack()


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
        # Clear previous figure
        for w in self.fig_frame.winfo_children():
            w.destroy()
        # Run fetch in background thread to avoid UI freeze
        def worker():
            interval, period = self._params()
            try:
                raw = yf.Ticker(self.ticker).history(period=period, interval=interval)
            except Exception as e:
                self.fig_frame.after(0, lambda: ttk.Label(self.fig_frame, text=f"{self.ticker}: fetch error {e}").pack(padx=20, pady=20))
                return
            if raw is None or raw.empty:
                self.fig_frame.after(0, lambda: ttk.Label(self.fig_frame, text=f"{self.ticker}: 無資料").pack(padx=20, pady=20))
                return
            raw = raw.tail(200)
            dates = [d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d) for d in raw.index]
            n = len(raw)
            xpos = list(range(n))
            # Convert series safely
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
            # Volume
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
            hi9 = self._pd.Series(h).rolling(9, min_periods=1).max().values
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
        threading.Thread(target=worker, daemon=True).start()

    def _params(self):
        p = self.period_var.get()
        if p == "day":
            return "1d", "2y"
        elif p == "week":
            return "1wk", "10y"
        else:
            return "1mo", "30y"


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

        saved, saved_active, saved_lang, saved_theme, _, _ = load_watchlists()
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

        # 字体列表在菜单构建时动态获取
        if CURRENT_FONT_FAMILY[0] not in get_installed_fonts() and get_installed_fonts():
            CURRENT_FONT_FAMILY[0] = get_installed_fonts()[0]

        try:
            self._style = ttk.Style()
        except Exception:
            self._style = None

        self._build_ui()
        self._apply_theme()
        self._apply_search_style()
        self._refresh_wl_list()
        self._refresh_items()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(100, self._enable_search)
        self._schedule_auto_refresh()

    def _apply_zoom(self):
        w, h = 960, 600
        zh = int(h * 1.5 * 1.12)  # 高度增加12%
        zw = int(w * 1.5 * 1.05)  # 寬度也稍微增加保持比例
        self.root.geometry(f"{zw}x{zh}")
        self.root.minsize(int(820 * 1.5 * 1.05), int(500 * 1.5 * 1.12))

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
        colors = self._get_dialog_colors()

        # 上方工具列 - 使用 tk.Frame + tk.Button 实现主题色
        top = tk.Frame(root, bg=colors["bg"], padx=6, pady=6)
        top.pack(fill=tk.X, side=tk.TOP)

        self.btn_add_wl = tk.Button(top, text=t("btn_new_wl"), command=self._add_watchlist,
                                     bg=colors["btn_bg"], fg=colors["btn_fg"], relief=tk.RAISED, bd=1,
                                     font=get_font())
        self.btn_add_wl.pack(side=tk.LEFT, padx=(0, 3))
        self.btn_del_wl = tk.Button(top, text=t("btn_del_wl"), command=self._del_watchlist,
                                     bg=colors["btn_bg"], fg=colors["btn_fg"], relief=tk.RAISED, bd=1,
                                     font=get_font())
        self.btn_del_wl.pack(side=tk.LEFT, padx=(0, 3))
        self.btn_add_item = tk.Button(top, text=t("btn_add_item"), command=self._open_add_dialog,
                                       bg=colors["btn_bg"], fg=colors["btn_fg"], relief=tk.RAISED, bd=1,
                                       font=get_font())
        self.btn_add_item.pack(side=tk.LEFT, padx=(0, 3))
        self.btn_del_item = tk.Button(top, text=t("btn_del_item"), command=self._del_item,
                                       bg=colors["btn_bg"], fg=colors["btn_fg"], relief=tk.RAISED, bd=1,
                                       font=get_font())
        self.btn_del_item.pack(side=tk.LEFT, padx=(0, 3))
        self.btn_set_alert = tk.Button(top, text=t("btn_set_alert"), command=self._open_alert_dialog,
                                       bg=colors["btn_bg"], fg=colors["btn_fg"], relief=tk.RAISED, bd=1,
                                       font=get_font())
        self.btn_set_alert.pack(side=tk.LEFT, padx=(0, 3))

        # 分隔线
        sep = tk.Frame(top, width=2, bg=colors["fg"])
        sep.pack(side=tk.LEFT, fill=tk.Y, padx=6)

        self.btn_refresh_current = tk.Button(top, text=t("btn_refresh_cur"),
                                             command=self._refresh_current_watchlist,
                                             bg=colors["btn_bg"], fg=colors["btn_fg"], relief=tk.RAISED, bd=1,
                                             font=get_font())
        self.btn_refresh_current.pack(side=tk.LEFT, padx=(0, 3))
        self.btn_refresh = tk.Button(top, text=t("btn_refresh_all"), command=self._refresh_all,
                                      bg=colors["btn_bg"], fg=colors["btn_fg"], relief=tk.RAISED, bd=1,
                                      font=get_font())
        self.btn_refresh.pack(side=tk.LEFT, padx=(0, 3))

        self.status_var = tk.StringVar(value=t("status_ready"))
        self.status_label = tk.Label(top, textvariable=self.status_var,
                                      bg=colors["bg"], fg=colors["fg"], font=get_font())
        self.status_label.pack(side=tk.RIGHT, padx=(8, 0))

        self._build_menu()

        # 主分割區域 - 使用 tk.PanedWindow
        paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        # 左侧 Watchlists 区域
        left = tk.Frame(paned, bg=colors["bg"])
        paned.add(left, weight=1)
        tk.Label(left, text=t("frame_watchlists"), font=get_font(),
                 bg=colors["bg"], fg=colors["fg"], anchor=tk.W).pack(fill=tk.X, padx=8, pady=(4, 2))

        self.wl_tree = ttk.Treeview(left, columns=("cnt",), show="tree headings", height=18)
        self.wl_tree.heading("#0", text=t("col_name"))
        self.wl_tree.heading("#1", text=t("col_count"))
        self.wl_tree.column("#0", width=150, stretch=True)
        self.wl_tree.column("#1", width=30, anchor=tk.CENTER)
        self.wl_tree.bind("<<TreeviewSelect>>", self._on_wl_select)
        self.wl_tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        # 右侧区域
        right = ttk.PanedWindow(paned, orient=tk.VERTICAL)
        paned.add(right, weight=3)

        # 商品價格區域
        price_frame = tk.Frame(right, bg=colors["bg"])
        right.add(price_frame, weight=7)
        tk.Label(price_frame, text=t("frame_prices"), font=get_font(),
                 bg=colors["bg"], fg=colors["fg"], anchor=tk.W).pack(fill=tk.X, padx=8, pady=(4, 2))

        cols = ("label", "ticker", "price", "change", "pct", "vol")
        self.item_tree = ttk.Treeview(price_frame, columns=cols, show="headings", height=12)
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
        self.item_tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
        self.item_tree.bind("<Double-1>", self._on_item_double_click)
        self.item_tree.bind("<Button-3>", self._on_item_right_click)

        # 設定 Treeview 行高和字體（根據字體大小動態調整）
        try:
            style = ttk.Style()
            rowheight = max(27, CURRENT_FONT_SIZE[0] + 14)
            style.configure("Treeview", rowheight=rowheight, font=get_font())
            style.configure("Treeview.Heading", font=get_font())
        except Exception:
            pass

        # 搜尋區域
        search_frame = tk.Frame(right, bg=colors["bg"], relief=tk.FLAT, bd=0)
        right.add(search_frame, weight=3)
        tk.Label(search_frame, text=t("frame_search"), font=get_font(),
                 bg=colors["bg"], fg=colors["fg"]).pack(anchor=tk.W, padx=8, pady=(4, 2))

        row1 = tk.Frame(search_frame, bg=colors["bg"])
        row1.pack(fill=tk.X, pady=(0, 4))
        tk.Label(row1, text=t("lbl_search"), bg=colors["bg"], fg=colors["fg"], font=get_font()).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(row1, textvariable=self.search_var,
                                     bg=colors["entry_bg"], fg=colors["entry_fg"],
                                     insertbackground=colors["entry_fg"],
                                     relief=tk.SOLID, bd=1,
                                     highlightbackground=colors["entry_border"],
                                     highlightcolor=colors["entry_border"],
                                     highlightthickness=1,
                                     font=get_font())
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))

        tk.Label(search_frame, text=t("lbl_result"), bg=colors["bg"], fg=colors["fg"], font=get_font()).pack(anchor=tk.W, padx=8)

        self.result_tree = ttk.Treeview(search_frame, columns=("lbl","tk","nm"),
                                        show="headings", height=6)
        self.result_tree.heading("lbl", text=t("col_name"))
        self.result_tree.heading("tk", text=t("col_ticker"))
        self.result_tree.heading("nm", text=t("col_name"))
        self.result_tree.column("lbl", width=200, anchor=tk.W)
        self.result_tree.column("tk", width=90, anchor=tk.CENTER)
        self.result_tree.column("nm", width=180, anchor=tk.W)
        self.result_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=(2, 4))
        self.result_tree.bind("<Double-1>", lambda e: self._add_selected())
        self.result_tree.bind("<<TreeviewSelect>>", self._on_res_select)

        row2 = tk.Frame(search_frame, bg=colors["bg"])
        row2.pack(fill=tk.X, pady=(4, 0))
        tk.Label(row2, text=t("lbl_custom_name"), bg=colors["bg"], fg=colors["fg"], font=get_font()).pack(side=tk.LEFT)
        self.label_var = tk.StringVar()
        self.label_entry = tk.Entry(row2, textvariable=self.label_var, width=16,
                                    bg=colors["entry_bg"], fg=colors["entry_fg"],
                                    insertbackground=colors["entry_fg"],
                                    relief=tk.SOLID, bd=1,
                                    highlightbackground=colors["entry_border"],
                                    highlightcolor=colors["entry_border"],
                                    highlightthickness=1,
                                    font=get_font())
        self.label_entry.pack(side=tk.LEFT, padx=(4, 4))
        self.btn_add_res = tk.Button(row2, text=t("btn_add_selected"), command=self._add_selected,
                                     state=tk.DISABLED, bg=colors["btn_bg"], fg=colors["btn_fg"],
                                     relief=tk.RAISED, bd=1, font=get_font())
        self.btn_add_res.pack(side=tk.LEFT)
        tk.Button(row2, text=t("btn_direct_input"), command=self._open_add_dialog,
                  bg=colors["btn_bg"], fg=colors["btn_fg"], relief=tk.RAISED, bd=1,
                  font=get_font()).pack(side=tk.LEFT, padx=(6, 0))

    def _build_menu(self):
        colors = self._get_dialog_colors()
        font_used = get_font()
        menubar = tk.Menu(self.root, bg=colors["bg"], fg=colors["fg"],
                          activebackground=colors["list_sel"], activeforeground=colors["fg"],
                          font=font_used)
        lang_menu = tk.Menu(menubar, tearoff=0, bg=colors["bg"], fg=colors["fg"],
                            activebackground=colors["list_sel"], activeforeground=colors["fg"],
                            font=font_used)
        for code, label in [("zh-TW","繁體中文"),("zh-CN","簡體中文"),("en","English"),
                             ("ja","日本語"),("ko","한국어"),("es","Español")]:
            lang_menu.add_command(label=label, command=lambda c=code: self._switch_lang(c))
        menubar.add_cascade(label=t("lang_menu"), menu=lang_menu)
        theme_menu = tk.Menu(menubar, tearoff=0, bg=colors["bg"], fg=colors["fg"],
                            activebackground=colors["list_sel"], activeforeground=colors["fg"],
                            font=font_used)
        for val, label in [("system","🌓 System"),("light","☀ Light"),("dark","🌙 Dark")]:
            theme_menu.add_command(label=label, command=lambda v=val: self._switch_theme(v))
        menubar.add_cascade(label=t("theme_menu"), menu=theme_menu)
        font_menu = tk.Menu(menubar, tearoff=0, bg=colors["bg"], fg=colors["fg"],
                           activebackground=colors["list_sel"], activeforeground=colors["fg"],
                           font=font_used)
        # Font family submenu - dynamically get fonts
        family_submenu = tk.Menu(font_menu, tearoff=0, bg=colors["bg"], fg=colors["fg"],
                                  activebackground=colors["list_sel"], activeforeground=colors["fg"],
                                  font=font_used)
        current_family = CURRENT_FONT_FAMILY[0]
        font_families = get_installed_fonts()
        for family in font_families:
            cmd = lambda f=family: self._switch_font_family(f)
            family_submenu.add_command(label=family, command=cmd)
        if not font_families:
            family_submenu.add_command(label="(無字體)", state=tk.DISABLED)
        font_menu.add_cascade(label=t("font_family"), menu=family_submenu)
        # Font size submenu
        size_submenu = tk.Menu(font_menu, tearoff=0, bg=colors["bg"], fg=colors["fg"],
                                activebackground=colors["list_sel"], activeforeground=colors["fg"],
                                font=font_used)
        for size in range(8, 17):
            cmd = lambda s=size: self._switch_font_size(s)
            size_submenu.add_command(label=str(size), command=cmd)
        font_menu.add_cascade(label=t("font_size"), menu=size_submenu)
        menubar.add_cascade(label=t("font_menu"), menu=font_menu)
        self.root.config(menu=menubar)

    def _switch_lang(self, code):
        global CURRENT_LANG
        CURRENT_LANG = code
        self._save()
        for w in self.root.winfo_children():
            w.destroy()
        self._build_ui()
        self._apply_theme()
        self._apply_search_style()
        self._refresh_wl_list()
        self._refresh_items()

    def _switch_font_family(self, family: str):
        global CURRENT_FONT_FAMILY
        CURRENT_FONT_FAMILY[0] = family
        self._save()
        for w in self.root.winfo_children():
            w.destroy()
        self._build_ui()
        self._apply_theme()
        self._apply_search_style()
        self._refresh_wl_list()
        self._refresh_items()

    def _switch_font_size(self, size: int):
        global CURRENT_FONT_SIZE
        CURRENT_FONT_SIZE[0] = size
        self._save()
        for w in self.root.winfo_children():
            w.destroy()
        self._build_ui()
        self._apply_theme()
        self._apply_search_style()
        self._refresh_wl_list()
        self._refresh_items()

    def _apply_search_style(self):
        """Apply theme-aware style to search Entry"""
        colors = self._get_dialog_colors()
        try:
            self.search_entry.configure(
                background=colors["entry_bg"],
                foreground=colors["entry_fg"],
                insertbackground=colors["entry_fg"],
                relief=tk.SOLID,
                highlightbackground=colors["entry_border"],
                highlightcolor=colors["entry_border"],
                highlightthickness=1
            )
            self.label_entry.configure(
                background=colors["entry_bg"],
                foreground=colors["entry_fg"],
                insertbackground=colors["entry_fg"],
                relief=tk.SOLID,
                highlightbackground=colors["entry_border"],
                highlightcolor=colors["entry_border"],
                highlightthickness=1
            )
        except Exception:
            pass

    def _switch_theme(self, val):
        global CURRENT_THEME
        CURRENT_THEME = val
        self._save()
        self._apply_theme()
        self._apply_search_style()
        # 重新构建整个 UI 以更新所有组件颜色
        for w in self.root.winfo_children():
            w.destroy()
        self._build_ui()
        self._refresh_wl_list()
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
        name = simpledialog.askstring(t("dialog_new_wl"), t("err_wl_name"))
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

    def _del_item(self):
        """Remove selected ticker from current watchlist."""
        if not self.active_wl:
            return
        sel = self.item_tree.selection()
        if not sel:
            messagebox.showinfo("提示", t("err_no_select"))
            return
        ticker = sel[0]
        if not messagebox.askyesno("確認", f"確定從「{self.active_wl}」移除 {ticker}？"):
            return
        # filter out ticker
        self.watchlists[self.active_wl] = [it for it in self.watchlists[self.active_wl] if it[1] != ticker]
        self._refresh_wl_list()
        self._refresh_items()
        self._save()
        self.status_var.set(f"已移除 {ticker}")

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
            messagebox.showinfo("提示", t("err_search_select"))
            return
        if not self.active_wl:
            messagebox.showinfo("提示", t("err_no_wl"))
            return
        label, ticker, name = self._selected_res
        if not self._valid_ticker(ticker):
            messagebox.showwarning("錯誤", f"Ticker '{ticker}' 格式不正確")
            return
        self._insert_item(label, ticker, name)

    def _insert_item(self, label, ticker, full_name):
        if not self.active_wl:
            messagebox.showinfo("提示", t("err_no_wl"))
            return
        if not self._valid_ticker(ticker):
            messagebox.showwarning("錯誤", f"Ticker '{ticker}' 格式不正確")
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

    def _get_dialog_colors(self):
        """Get unified gray colors for all components"""
        is_dark = (_get_effective_theme() == "dark")
        main_gray = "#1a1a1a" if is_dark else "#c0c0c0"
        text_gray = "#cccccc" if is_dark else "#1a1a1a"
        btn_gray = "#2a2a2a" if is_dark else "#b5b5b5"
        btn_text = "#cccccc" if is_dark else "#000000"
        sel_gray = "#2a5a8a" if is_dark else "#8090a8"
        # 暗黑模式下输入框背景更浅 + 添加对比边框
        entry_bg = "#3a3a3a" if is_dark else main_gray
        entry_border = "#666666" if is_dark else "#808080"
        return {
            "bg": main_gray, "fg": text_gray, "panel": main_gray,
            "entry_bg": entry_bg, "entry_fg": text_gray, "entry_border": entry_border,
            "btn_bg": btn_gray, "btn_fg": btn_text, "btn_active": btn_gray,
            "list_bg": main_gray, "list_fg": text_gray, "list_sel": sel_gray
        }

    def _apply_entry_style(self, entry):
        """Apply theme-aware style to an Entry widget"""
        colors = self._get_dialog_colors()
        try:
            entry.configure(
                background=colors["entry_bg"],
                foreground=colors["entry_fg"],
                insertcolor=colors["entry_fg"],
                relief=tk.SOLID,
                bd=1
            )
        except Exception:
            pass

    def _open_add_dialog(self):
        if not self.active_wl:
            messagebox.showinfo("提示", t("err_no_wl"))
            return
        colors = self._get_dialog_colors()

        dlg = tk.Toplevel(self.root)
        dlg.title(t("dlg_add_title"))
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.geometry("420x224")
        dlg.configure(bg=colors["bg"])
        self._center_dialog(dlg)

        # 使用 Frame 代替 ttk.Frame 以便控制背景色
        content = tk.Frame(dlg, bg=colors["bg"])
        content.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        ttk.Label(content, text=t("dlg_ticker_hint"), font=get_font()).pack(anchor=tk.W)
        tk_var = tk.StringVar()
        entry1 = tk.Entry(content, textvariable=tk_var, width=42,
                         bg=colors["entry_bg"], fg=colors["entry_fg"],
                         insertbackground=colors["entry_fg"], relief=tk.SOLID, bd=1,
                         highlightbackground=colors["entry_border"],
                         highlightcolor=colors["entry_border"],
                         highlightthickness=1,
                         font=get_font())
        entry1.pack(pady=(2, 8))

        ttk.Label(content, text=t("dlg_label_hint"), font=get_font()).pack(anchor=tk.W)
        lb_var = tk.StringVar()
        entry2 = tk.Entry(content, textvariable=lb_var, width=42,
                         bg=colors["entry_bg"], fg=colors["entry_fg"],
                         insertbackground=colors["entry_fg"], relief=tk.SOLID, bd=1,
                         highlightbackground=colors["entry_border"],
                         highlightcolor=colors["entry_border"],
                         highlightthickness=1,
                         font=get_font())
        entry2.pack(pady=(2, 8))

        def _ok():
            sym = tk_var.get().strip()
            lbl = lb_var.get().strip() or sym
            if not sym:
                messagebox.showwarning("提示", t("err_ticker_input"))
                return
            self._insert_item(lbl, sym, sym)
            tk_var.set(""); lb_var.set("")
            dlg.focus_force()

        btn_frame = tk.Frame(dlg, bg=colors["bg"])
        btn_frame.pack(pady=4)
        btn_ok = tk.Button(btn_frame, text=t("btn_add_continue"), command=_ok,
                          bg=colors["btn_bg"], fg=colors["btn_fg"], relief=tk.RAISED, bd=1,
                          font=get_font())
        btn_ok.pack(side=tk.LEFT, padx=5)
        btn_cancel = tk.Button(btn_frame, text=t("btn_cancel_zh"), command=dlg.destroy,
                               bg=colors["btn_bg"], fg=colors["btn_fg"], relief=tk.RAISED, bd=1,
                               font=get_font())
        btn_cancel.pack(side=tk.LEFT, padx=5)

        dlg.bind("<Return>", lambda e: _ok())
        dlg.bind("<Escape>", lambda e: dlg.destroy())
        entry1.focus_set()

    def _open_alert_dialog(self):
        """打開價格提醒設置對話框"""
        sel = self.item_tree.selection()
        if not sel:
            messagebox.showinfo("提示", t("err_no_select"))
            return
        ticker = sel[0]

        colors = self._get_dialog_colors()

        dlg = tk.Toplevel(self.root)
        dlg.title(t("alert_title"))
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.geometry("420x550")
        dlg.configure(bg=colors["bg"])
        self._center_dialog(dlg)

        # 使用 Frame 控制背景
        content = tk.Frame(dlg, bg=colors["bg"])
        content.pack(fill=tk.BOTH, expand=True)

        # 當前提醒設置
        current = PRICE_ALERTS.get(ticker, {})
        current_high = current.get("high")
        current_low = current.get("low")

        tk.Label(content, text=t("alert_list_label"), font=get_font(),
                 bg=colors["bg"], fg=colors["fg"]).pack(anchor=tk.W, padx=20, pady=(15, 4))

        list_frame = tk.Frame(content, bg=colors["bg"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        alert_listbox = tk.Listbox(list_frame, height=6, font=get_font(),
                                   bg=colors["list_bg"], fg=colors["list_fg"],
                                   selectbackground=colors["list_sel"],
                                   relief=tk.SOLID, bd=1)
        alert_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        alert_scroll = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=alert_listbox.yview)
        alert_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        alert_listbox.config(yscrollcommand=alert_scroll.set)

        # 填充已有提醒（顯示觸發狀態）
        alert_items = []  # 儲存 (ticker_key, alert_type, display_str)
        if PRICE_ALERTS:
            for tk_key, alert in sorted(PRICE_ALERTS.items()):
                high_val = alert.get("high")
                low_val = alert.get("low")
                high_triggered = alert.get("high_triggered", False)
                low_triggered = alert.get("low_triggered", False)
                info = []
                triggered_markers = []
                if high_val:
                    marker = "⚠️" if high_triggered else "↑"
                    info.append(f"{marker}{t('alert_high_label')}={high_val}")
                    if high_triggered:
                        triggered_markers.append(t("alert_high_label"))
                if low_val:
                    marker = "⚠️" if low_triggered else "↓"
                    info.append(f"{marker}{t('alert_low_label')}={low_val}")
                    if low_triggered:
                        triggered_markers.append(t("alert_low_label"))
                if info:
                    status = f" ({t('alert_triggered')})" if triggered_markers else ""
                    display = f"{tk_key}: {', '.join(info)}{status}"
                    alert_listbox.insert(tk.END, display)
                    if high_val:
                        alert_items.append((tk_key, "high", f"↑{t('alert_high_label')}={high_val}", high_triggered))
                    if low_val:
                        alert_items.append((tk_key, "low", f"↓{t('alert_low_label')}={low_val}", low_triggered))

        def _delete_selected_alert():
            sel_idx = alert_listbox.curselection()
            if not sel_idx:
                return
            idx = sel_idx[0]
            tk_key, alert_type, _, _ = alert_items[idx]
            if tk_key in PRICE_ALERTS:
                if alert_type == "high":
                    PRICE_ALERTS[tk_key]["high"] = None
                elif alert_type == "low":
                    PRICE_ALERTS[tk_key]["low"] = None
                # 如果兩個都沒了，刪除這個 ticker
                if PRICE_ALERTS[tk_key]["high"] is None and PRICE_ALERTS[tk_key]["low"] is None:
                    del PRICE_ALERTS[tk_key]
                self._save()
            # 重新載入列表
            alert_listbox.delete(0, tk.END)
            alert_items.clear()
            for tk_key2, alert2 in sorted(PRICE_ALERTS.items()):
                high_val = alert2.get("high")
                low_val = alert2.get("low")
                high_triggered = alert2.get("high_triggered", False)
                low_triggered = alert2.get("low_triggered", False)
                info = []
                triggered_markers = []
                if high_val:
                    marker = "⚠️" if high_triggered else "↑"
                    info.append(f"{marker}{t('alert_high_label')}={high_val}")
                    if high_triggered:
                        triggered_markers.append(t("alert_high_label"))
                if low_val:
                    marker = "⚠️" if low_triggered else "↓"
                    info.append(f"{marker}{t('alert_low_label')}={low_val}")
                    if low_triggered:
                        triggered_markers.append(t("alert_low_label"))
                if info:
                    status = f" ({t('alert_triggered')})" if triggered_markers else ""
                    display = f"{tk_key2}: {', '.join(info)}{status}"
                    alert_listbox.insert(tk.END, display)
                    if high_val:
                        alert_items.append((tk_key2, "high", f"↑{t('alert_high_label')}={high_val}", high_triggered))
                    if low_val:
                        alert_items.append((tk_key2, "low", f"↓{t('alert_low_label')}={low_val}", low_triggered))

        def _reset_all_triggered():
            """重置所有已觸發的提醒狀態"""
            reset_count = 0
            for tk_key, alert in PRICE_ALERTS.items():
                if alert.get("high_triggered"):
                    alert["high_triggered"] = False
                    reset_count += 1
                if alert.get("low_triggered"):
                    alert["low_triggered"] = False
                    reset_count += 1
            if reset_count > 0:
                self._save()
                self.status_var.set(f"{t('btn_reset_triggered')} {reset_count}")
                # 重新載入列表
                alert_listbox.delete(0, tk.END)
                alert_items.clear()
                for tk_key2, alert2 in sorted(PRICE_ALERTS.items()):
                    high_val = alert2.get("high")
                    low_val = alert2.get("low")
                    high_triggered = alert2.get("high_triggered", False)
                    low_triggered = alert2.get("low_triggered", False)
                    info = []
                    triggered_markers = []
                    if high_val:
                        marker = "⚠️" if high_triggered else "↑"
                        info.append(f"{marker}{t('alert_high_label')}={high_val}")
                        if high_triggered:
                            triggered_markers.append(t("alert_high_label"))
                    if low_val:
                        marker = "⚠️" if low_triggered else "↓"
                        info.append(f"{marker}{t('alert_low_label')}={low_val}")
                        if low_triggered:
                            triggered_markers.append(t("alert_low_label"))
                    if info:
                        status = f" ({t('alert_triggered')})" if triggered_markers else ""
                        display = f"{tk_key2}: {', '.join(info)}{status}"
                        alert_listbox.insert(tk.END, display)
                        if high_val:
                            alert_items.append((tk_key2, "high", f"↑{t('alert_high_label')}={high_val}", high_triggered))
                        if low_val:
                            alert_items.append((tk_key2, "low", f"↓{t('alert_low_label')}={low_val}", low_triggered))

        btn_frame = tk.Frame(content, bg=colors["bg"])
        btn_frame.pack(pady=(4, 0))
        tk.Button(btn_frame, text=t("btn_delete_selected"), command=_delete_selected_alert,
                  bg=colors["btn_bg"], fg=colors["btn_fg"], relief=tk.RAISED, bd=1).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text=t("btn_reset_triggered"), command=_reset_all_triggered,
                  bg=colors["btn_bg"], fg=colors["btn_fg"], relief=tk.RAISED, bd=1).pack(side=tk.LEFT, padx=5)

        # === 新增/編輯當前 Ticker 的提醒 ===
        sep_canvas = tk.Canvas(content, height=4, bg=colors["bg"], highlightthickness=0)
        sep_canvas.pack(fill=tk.X, padx=15, pady=8)
        sep_canvas.create_line(0, 2, sep_canvas.winfo_reqwidth(), 2, fill=colors["fg"], width=1)

        tk.Label(content, text=t("alert_set_title").format(ticker=ticker), font=get_font(),
                 bg=colors["bg"], fg=colors["fg"]).pack(anchor=tk.W, padx=20, pady=(5, 4))

        # 高價提醒
        high_frame = tk.Frame(content, bg=colors["bg"])
        high_frame.pack(fill=tk.X, padx=20, pady=2)
        tk.Label(high_frame, text=t("alert_high"), bg=colors["bg"], fg=colors["fg"]).pack(anchor=tk.W)
        high_var = tk.StringVar(value=str(current_high) if current_high else "")
        high_entry = tk.Entry(high_frame, textvariable=high_var, width=20,
                             bg=colors["entry_bg"], fg=colors["entry_fg"],
                             insertbackground=colors["entry_fg"], relief=tk.SOLID, bd=1,
                             highlightbackground=colors["entry_border"],
                             highlightcolor=colors["entry_border"],
                             highlightthickness=1)
        high_entry.pack(anchor=tk.W, pady=(2, 0))

        # 低價提醒
        low_frame = tk.Frame(content, bg=colors["bg"])
        low_frame.pack(fill=tk.X, padx=20, pady=2)
        tk.Label(low_frame, text=t("alert_low"), bg=colors["bg"], fg=colors["fg"]).pack(anchor=tk.W)
        low_var = tk.StringVar(value=str(current_low) if current_low else "")
        low_entry = tk.Entry(low_frame, textvariable=low_var, width=20,
                            bg=colors["entry_bg"], fg=colors["entry_fg"],
                            insertbackground=colors["entry_fg"], relief=tk.SOLID, bd=1,
                            highlightbackground=colors["entry_border"],
                            highlightcolor=colors["entry_border"],
                            highlightthickness=1)
        low_entry.pack(anchor=tk.W, pady=(2, 0))

        def _save_alert():
            try:
                high_val = float(high_var.get()) if high_var.get().strip() else None
            except ValueError:
                messagebox.showwarning("提示", t("err_alert_high_num"))
                return
            try:
                low_val = float(low_var.get()) if low_var.get().strip() else None
            except ValueError:
                messagebox.showwarning("提示", t("err_alert_low_num"))
                return
            if high_val is None and low_val is None:
                # 清除這個 ticker 的提醒
                if ticker in PRICE_ALERTS:
                    del PRICE_ALERTS[ticker]
                self.status_var.set(f"{ticker} 提醒已清除")
            else:
                # 保存提醒設置，重置觸發狀態
                PRICE_ALERTS[ticker] = {
                    "high": high_val,
                    "low": low_val,
                    "high_triggered": False,
                    "low_triggered": False
                }
                self.status_var.set(t("alert_saved"))
            self._save()
            # 顯示成功訊息後關閉
            messagebox.showinfo("提示", t("alert_saved"))
            dlg.destroy()

        btn_frame = tk.Frame(content, bg=colors["bg"])
        btn_frame.pack(pady=12)
        tk.Button(btn_frame, text=t("btn_save_alert"), command=_save_alert,
                  bg=colors["btn_bg"], fg=colors["btn_fg"], relief=tk.RAISED, bd=1).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text=t("btn_cancel_zh"), command=dlg.destroy,
                  bg=colors["btn_bg"], fg=colors["btn_fg"], relief=tk.RAISED, bd=1).pack(side=tk.LEFT, padx=5)

        dlg.bind("<Return>", lambda e: _save_alert())
        dlg.bind("<Escape>", lambda e: dlg.destroy())

    def _valid_ticker(self, ticker: str) -> bool:
        """Basic validation: allow alphanumerics, dot, dash, underscore, up to 20 chars."""
        return bool(re.fullmatch(r"[A-Za-z0-9._\-]{1,20}", ticker))
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

    def _on_item_right_click(self, event):
        """Show right-click context menu for fundamental/technical analysis"""
        # Get item under cursor
        item_id = self.item_tree.identify_row(event.y)
        if not item_id:
            return
        # Select the item
        self.item_tree.selection_set(item_id)
        self.item_tree.focus(item_id)

        # Get ticker and name
        ticker = item_id
        wl_items = self.watchlists.get(self.active_wl, [])
        name = next((it[2] for it in wl_items if it[1] == ticker), ticker)

        # Create context menu
        colors = self._get_dialog_colors()
        menu = tk.Menu(self.root, tearoff=0,
                      bg=colors["bg"], fg=colors["fg"],
                      activebackground=colors["list_sel"],
                      activeforeground=colors["fg"],
                      font=get_font())

        menu.add_command(label=t("ctx_fundamental"),
                        command=lambda: FundamentalAnalysisWindow(self.root, ticker, name, theme_mode=_get_effective_theme()))
        menu.add_command(label=t("ctx_technical"),
                        command=lambda: ChartWindow(self.root, ticker, name, theme_mode=_get_effective_theme()))
        menu.add_command(label=t("ctx_news"),
                        command=lambda: NewsWindow(self.root, ticker, name, theme_mode=_get_effective_theme()))

        menu.tk_popup(event.x_root, event.y_root)

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
            self._check_price_alerts(data)
            self._refresh_items()
            self.btn_refresh.config(state=tk.NORMAL)
            self.btn_refresh_current.config(state=tk.NORMAL)
            self.status_var.set(f"更新完成 ({len(tickers)} 個標的，{_now_str()})")
        self.root.after(0, _apply)

    def _check_price_alerts(self, price_data: dict):
        """檢查價格是否觸發提醒"""
        for ticker, pd_data in price_data.items():
            if ticker not in PRICE_ALERTS:
                continue
            price = pd_data.get("price")
            if price is None:
                continue
            alert = PRICE_ALERTS.get(ticker)
            if not alert:
                continue
            # 檢查高價提醒（價格 >= 目標價時觸發）
            high_target = alert.get("high")
            if high_target and price >= high_target:
                if not alert.get("high_triggered"):  # 未觸發過才通知
                    alert["high_triggered"] = True
                    self._send_alert_notification(ticker, price, high_target, "high")
                    self._save()
            # 檢查低價提醒（價格 <= 目標價時觸發）
            low_target = alert.get("low")
            if low_target and price <= low_target:
                if not alert.get("low_triggered"):
                    alert["low_triggered"] = True
                    self._send_alert_notification(ticker, price, low_target, "low")
                    self._save()

    def _send_alert_notification(self, ticker: str, current_price: float, target_price: float, alert_type: str):
        """發送價格提醒通知"""
        price_str = _fmt_price(current_price)
        target_str = _fmt_price(target_price)
        name = next((it[2] for wl in self.watchlists.values() for it in wl if it[1] == ticker), ticker)
        if alert_type == "high":
            msg = t("alert_high_triggered").format(ticker=f"{ticker} ({name})", price=price_str, target=target_str)
            title = "High Price Alert"
        else:
            msg = t("alert_low_triggered").format(ticker=f"{ticker} ({name})", price=price_str, target=target_str)
            title = "Low Price Alert"
        _send_windows_notification(title, msg)
        self.root.after(0, lambda: self.status_var.set(msg))

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
