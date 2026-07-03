"""
yfinance Watchlist Manager — Android (Kivy)
================================================
Run on Android via Buildozer:
    pip install buildozer
    cd android_version
    buildozer android debug deploy run
"""

import os
import sys
import json
import threading
import time
import yfinance as yf
import pandas as pd
import numpy as np
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.metrics import dp

# Local imports
from common_data import COMMON_TICKERS, DEFAULT_WATCHLISTS
from language_data import LANG

# ─── Globals ─────────────────────────────────────────────────────
CURRENT_LANG = "zh-TW"
CURRENT_THEME = "system"  # system | light | dark

def t(key):
    return LANG.get(key, {}).get(CURRENT_LANG, key)

def _fmt_price(val):
    if val is None or val == "N/A":
        return "N/A"
    try:
        return f"{float(val):,.2f}"
    except:
        return "N/A"

def _fmt_pct(val):
    if val is None or val == "N/A":
        return "N/A"
    try:
        return f"{float(val):,.2f}%"
    except:
        return "N/A"

def _fmt_vol(val):
    if val is None or val == "N/A":
        return "N/A"
    try:
        return f"{int(val):,}"
    except:
        return "N/A"

# ─── Search ──────────────────────────────────────────────────────
def search_tickers(query, limit=12):
    q = query.strip().lower()
    if not q:
        return []
    results = []
    seen = set()
    for name, ticker, full in COMMON_TICKERS:
        if ticker.lower() == q or ticker.lower().startswith(q):
            if ticker not in seen:
                results.append((name, ticker, full))
                seen.add(ticker)
        elif q in name.lower() or q in full.lower():
            if ticker not in seen:
                results.append((name, ticker, full))
                seen.add(ticker)
    if len(results) >= limit:
        return results[:limit]
    # Fallback: yfinance search
    try:
        data = yf.search(q, quotes_count=limit - len(results))
        if data and "quotes" in data and data["quotes"]:
            for q_item in data["quotes"]:
                tk = q_item.get("symbol", "")
                nm = q_item.get("shortname", tk)
                if tk not in seen:
                    results.append((nm, tk, nm))
                    seen.add(tk)
    except:
        pass
    return results[:limit]

# ─── Fetch Price ─────────────────────────────────────────────────
def fetch_price(ticker):
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1d", interval="1m")
        if hist is not None and not hist.empty:
            info = tk.info
            price = info.get("regularMarketPrice") or info.get("currentPrice")
            prev = info.get("regularMarketPreviousClose") or info.get("previousClose")
            vol = info.get("regularMarketVolume") or info.get("volume")
            if price is not None and prev is not None:
                chg = price - prev
                pct = (chg / prev) * 100 if prev else 0
                return {"price": price, "change": chg, "pct": pct, "volume": vol}
            return {"price": price, "change": 0, "pct": 0, "volume": vol}
        # Fallback to info only
        info = tk.info
        price = info.get("regularMarketPrice") or info.get("currentPrice")
        prev = info.get("regularMarketPreviousClose") or info.get("previousClose")
        vol = info.get("regularMarketVolume") or info.get("volume")
        if price and prev:
            chg = price - prev
            pct = (chg / prev) * 100 if prev else 0
            return {"price": price, "change": chg, "pct": pct, "volume": vol}
        return {"price": price, "change": 0, "pct": 0, "volume": vol}
    except:
        return {"price": None, "change": None, "pct": None, "volume": None}

# ─── Persistence ─────────────────────────────────────────────────
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watchlist_data.json")

def save_watchlists(watchlists, active_wl, lang, theme):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"watchlists": watchlists, "active_wl": active_wl,
                       "lang": lang, "theme": theme}, f, ensure_ascii=False)
    except:
        pass

def load_watchlists():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d.get("watchlists", {}), d.get("active_wl", ""), d.get("lang", "zh-TW"), d.get("theme", "system")
    except:
        return {}, "", "zh-TW", "system"


# ─── Price Row Widget ───────────────────────────────────────────
class PriceRow(GridLayout):
    """Single row showing one stock/index price."""
    def __init__(self, name, ticker, price_info, **kwargs):
        super().__init__(cols=5, size_hint_y=None, height=44, **kwargs)
        self.name = name
        self.ticker = ticker
        self.price_info = price_info or {"price": None, "change": None, "pct": None, "volume": None}
        
        self.lbl_name = Label(text=name, size_hint_x=0.25, halign="left", valign="middle",
                              font_size="12sp", color=get_color_from_hex("#333333"))
        self.lbl_ticker = Label(text=ticker, size_hint_x=0.2, halign="left", valign="middle",
                                font_size="11sp", color=get_color_from_hex("#666666"))
        self.lbl_price = Label(text=_fmt_price(self.price_info.get("price")), size_hint_x=0.15,
                               halign="right", valign="middle", font_size="12sp",
                               color=get_color_from_hex("#333333"))
        self.lbl_change = Label(text=_fmt_price(self.price_info.get("change")), size_hint_x=0.15,
                                halign="right", valign="middle", font_size="12sp",
                                color=get_color_from_hex("#333333"))
        self.lbl_pct = Label(text=_fmt_pct(self.price_info.get("pct")), size_hint_x=0.1,
                             halign="right", valign="middle", font_size="12sp",
                             color=get_color_from_hex("#333333"))
        self.lbl_vol = Label(text=_fmt_vol(self.price_info.get("volume")), size_hint_x=0.1,
                             halign="right", valign="middle", font_size="11sp",
                             color=get_color_from_hex("#666666"))
        
        self.add_widget(self.lbl_name)
        self.add_widget(self.lbl_ticker)
        self.add_widget(self.lbl_price)
        self.add_widget(self.lbl_change)
        self.add_widget(self.lbl_pct)
        self.add_widget(self.lbl_vol)
    
    def update(self, price_info):
        self.price_info = price_info or {"price": None, "change": None, "pct": None, "volume": None}
        self.lbl_price.text = _fmt_price(self.price_info.get("price"))
        self.lbl_change.text = _fmt_price(self.price_info.get("change"))
        self.lbl_pct.text = _fmt_pct(self.price_info.get("pct"))
        self.lbl_vol.text = _fmt_vol(self.price_info.get("volume"))
        
        # Color coding
        chg = self.price_info.get("change", 0)
        if chg is not None:
            try:
                cv = float(chg)
                if cv > 0:
                    self.lbl_change.color = get_color_from_hex("#cc0000")
                    self.lbl_pct.color = get_color_from_hex("#cc0000")
                elif cv < 0:
                    self.lbl_change.color = get_color_from_hex("#006600")
                    self.lbl_pct.color = get_color_from_hex("#006600")
                else:
                    self.lbl_change.color = get_color_from_hex("#333333")
                    self.lbl_pct.color = get_color_from_hex("#333333")
            except:
                pass


# ─── Search Result Row ──────────────────────────────────────────
class SearchRow(BoxLayout):
    """Single row in search results, tap to add."""
    def __init__(self, name, ticker, full_name, on_add_callback, **kwargs):
        super().__init__(orientation="vertical", size_hint_y=None, height=40, **kwargs)
        self.name = name
        self.ticker = ticker
        self.on_add = on_add_callback
        
        row = BoxLayout(size_hint_y=None, height=20)
        lbl = Label(text=f"{name} ({ticker})", font_size="11sp", color=get_color_from_hex("#333333"))
        row.add_widget(lbl)
        self.add_widget(row)
        
        btn = Button(text=t+"btn_add_selected", size_hint_y=None, height=20, font_size="10sp",
                     background_color=get_color_from_hex("#4CAF50"))
        btn.bind(on_release=lambda *_: self.on_add(name, ticker, full_name))
        self.add_widget(btn)


# ─── Watchlist Tab Widget ────────────────────────────────────────
class WatchlistTab(TabbedPanelItem):
    """A single watchlist tab showing its items."""
    def __init__(self, name, items, on_remove=None, **kwargs):
        super().__init__(text=name, **kwargs)
        self.items = list(items)  # [(name, ticker, full), ...]
        self.price_info_map = {}  # ticker -> price dict
        self.on_remove = on_remove
        
        self.layout = BoxLayout(orientation="vertical", padding=5, spacing=5)
        
        # Header row
        hdr = BoxLayout(size_hint_y=None, height=30, spacing=2)
        for col_name in [t("col_name"), t("col_ticker"), t("col_price"), t("col_change"), 
                         t("col_pct"), t("col_vol")]:
            lbl = Label(text=col_name, font_size="11sp", bold=True,
                       color=get_color_from_hex("#555555"), size_hint_x=1)
            hdr.add_widget(lbl)
        self.layout.add_widget(hdr)
        
        # Scrollable price rows
        self.scroll = ScrollView(size_hint=(1, 0.9))
        self.rows_layout = BoxLayout(orientation="vertical", size_hint_y=None)
        self.rows_layout.bind(minimum_height=self.rows_layout.setter("height"))
        self.scroll.add_widget(self.rows_layout)
        self.layout.add_widget(self.scroll)
        
        self._render_rows()
        self.add_widget(self.layout)
    
    def _render_rows(self):
        self.rows_layout.clear_widgets()
        for name, ticker, full in self.items:
            pi = self.price_info_map.get(ticker)
            row = PriceRow(name, ticker, pi)
            row.bind(on_press=lambda *_: self._show_detail(row, ticker))
            self.rows_layout.add_widget(row)
    
    def _show_detail(self, row, ticker):
        """Show detail popup on tap."""
        pi = self.price_info_map.get(ticker, {})
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        
        info_items = [
            (t("col_name"), row.name),
            (t("col_ticker"), ticker),
            (t("col_price"), _fmt_price(pi.get("price"))),
            (t("col_change"), _fmt_price(pi.get("change"))),
            (t("col_pct"), _fmt_pct(pi.get("pct"))),
            (t("col_vol"), _fmt_vol(pi.get("volume"))),
        ]
        
        for label, value in info_items:
            row = BoxLayout(size_hint_y=None, height=30, spacing=5)
            lbl = Label(text=label + ":", font_size="12sp", size_hint_x=0.3)
            val = Label(text=value, font_size="12sp", size_hint_x=0.7, halign="right")
            row.add_widget(lbl)
            row.add_widget(val)
            content.add_widget(row)
        
        if self.on_remove:
            del_btn = Button(text=t("btn_del_item"), size_hint_y=None, height=40,
                            background_color=get_color_from_hex("#f44336"))
            del_btn.bind(on_release=lambda *_: self._remove_item(ticker))
            content.add_widget(del_btn)
        
        popup = Popup(title=row.name, content=content, size_hint=(0.8, 0.5))
        popup.open()
    
    def _remove_item(self, ticker):
        if self.on_remove:
            self.on_remove(ticker)
    
    def update_prices(self, ticker_to_info):
        for row in self.rows_layout.children:
            if isinstance(row, PriceRow):
                pi = ticker_to_info.get(row.ticker)
                row.update(pi)


# ─── Main App ────────────────────────────────────────────────────
class WatchlistApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.watchlists = {}
        self.active_wl = ""
        self.search_results = []
        self._auto_job = None
    
    def build(self):
        # Load saved data
        self.watchlists, self.active_wl, lang, theme = load_watchlists()
        global CURRENT_LANG, CURRENT_THEME
        CURRENT_LANG = lang
        CURRENT_THEME = theme
        
        # Set window background
        Window.clearcolor = get_color_from_hex("#f0f0f0")
        
        # Main layout
        self.main_layout = BoxLayout(orientation="vertical", padding=5, spacing=5)
        
        # Toolbar
        toolbar = self._build_toolbar()
        self.main_layout.add_widget(toolbar)
        
        # Content area
        content = self._build_content()
        self.main_layout.add_widget(content)
        
        # Status bar
        status = Label(text=t("status_ready"), font_size="11sp",
                      color=get_color_from_hex("#888888"), size_hint_y=None, height=25)
        self.status_label = status
        self.main_layout.add_widget(status)
        
        # Apply zoom
        self._apply_zoom()
        
        # Schedule auto refresh
        self._schedule_auto_refresh()
        
        return self.main_layout
    
    def _apply_zoom(self):
        """Enlarge window for tablet/large screens."""
        Window.size = (int(Window.size[0] * 1.5), int(Window.size[1] * 1.5))
    
    def _schedule_auto_refresh(self):
        if self._auto_job:
            Clock.unschedule(self._auto_job)
        self._auto_job = Clock.schedule_interval(self._auto_refresh_once, 600)  # 10 min
    
    def _auto_refresh_once(self, dt):
        try:
            self._refresh_all_prices_threaded()
        except:
            pass
    
    def _build_toolbar(self):
        toolbar = BoxLayout(size_hint_y=None, height=50, spacing=5)
        
        # New Watchlist
        btn_new = Button(text=t("btn_new_wl"), font_size="12sp", size_hint_x=0.2)
        btn_new.bind(on_press=lambda *_: self._new_watchlist())
        toolbar.add_widget(btn_new)
        
        # Del Watchlist
        btn_del = Button(text=t("btn_del_wl"), font_size="12sp", size_hint_x=0.2)
        btn_del.bind(on_press=lambda *_: self._del_watchlist())
        toolbar.add_widget(btn_del)
        
        # Add Item
        btn_add = Button(text=t("btn_add_item"), font_size="12sp", size_hint_x=0.2)
        btn_add.bind(on_press=lambda *_: self._show_add_dialog())
        toolbar.add_widget(btn_add)
        
        # Refresh Current
        btn_ref = Button(text=t("btn_refresh_cur"), font_size="12sp", size_hint_x=0.2)
        btn_ref.bind(on_press=lambda *_: self._refresh_current_wl())
        toolbar.add_widget(btn_ref)
        
        # Refresh All
        btn_ref_all = Button(text=t("btn_refresh_all"), font_size="12sp", size_hint_x=0.2)
        btn_ref_all.bind(on_press=lambda *_: self._refresh_all_prices_threaded())
        toolbar.add_widget(btn_ref_all)
        
        return toolbar
    
    def _build_content(self):
        # Tabbed panel for watchlists
        self.tabs = TabbedPanel(default_tab_text="")
        self.tabs.do_default_tab = False
        
        # Add default tabs if none loaded
        if not self.watchlists:
            self.watchlists = dict(DEFAULT_WATCHLISTS)
            self.active_wl = list(DEFAULT_WATCHLISTS.keys())[0]
        
        for wl_name, items in self.watchlists.items():
            tab = WatchlistTab(wl_name, items, on_remove=lambda t: self._remove_item_from_wl(wl_name, t))
            self.tabs.add_widget(tab)
        
        self.current_tab = self.tabs.default_tab
        
        # Search panel below tabs
        search_panel = self._build_search_panel()
        
        container = BoxLayout(orientation="vertical", spacing=5)
        container.add_widget(self.tabs)
        container.add_widget(search_panel)
        return container

    
    def _build_search_panel(self):
        panel = BoxLayout(orientation="vertical", size_hint_y=None, height=200, spacing=5)
        
        # Search input
        search_row = BoxLayout(size_hint_y=None, height=40, spacing=5)
        self.search_input = TextInput(hint_text=t("lbl_search"), font_size="12sp",
                                      multiline=False, size_hint_x=0.6)
        self.search_input.bind(text=self._on_search_changed)
        search_row.add_widget(self.search_input)
        
        # Direct input button
        btn_direct = Button(text=t("btn_direct_input"), font_size="11sp", size_hint_x=0.4)
        btn_direct.bind(on_press=lambda *_: self._direct_input_dialog())
        search_row.add_widget(btn_direct)
        
        panel.add_widget(search_row)
        
        # Search results
        results_scroll = ScrollView()
        self.results_layout = BoxLayout(orientation="vertical", size_hint_y=None, padding=5)
        self.results_layout.bind(minimum_height=self.results_layout.setter("height"))
        results_scroll.add_widget(self.results_layout)
        panel.add_widget(results_scroll)
        
        return panel
    
    def _on_search_changed(self, instance, value):
        query = value.strip()
        self.results_layout.clear_widgets()
        if not query:
            self.search_results = []
            return
        
        self.search_results = search_tickers(query, limit=12)
        for name, ticker, full in self.search_results:
            row = SearchRow(name, ticker, full, 
                          lambda n, tk, fn: self._add_to_wl(n, tk, fn),
                          size_hint_y=None, height=40)
            self.results_layout.add_widget(row)
    
    def _add_to_wl(self, name, ticker, full):
        if not self.active_wl:
            self.active_wl = list(self.watchlists.keys())[0] if self.watchlists else "My Watchlist"
        
        if self.active_wl not in self.watchlists:
            self.watchlists[self.active_wl] = []
        
        # Check duplicate
        existing = [item[1] for item in self.watchlists[self.active_wl]]
        if ticker in existing:
            return
        
        self.watchlists[self.active_wl].append((name, ticker, full))
        self._save_and_refresh()
        
        # Update status
        self.status_label.text = f"Added {name} ({ticker}) to {self.active_wl}"
        Clock.schedule_once(lambda dt: setattr(self.status_label, "text", t("status_ready")), 3)
    
    def _remove_item_from_wl(self, ticker):
        if not self.active_wl or self.active_wl not in self.watchlists:
            return
        self.watchlists[self.active_wl] = [
            item for item in self.watchlists[self.active_wl] if item[1] != ticker
        ]
        self._save_and_refresh()
    
    def _save_and_refresh(self):
        save_watchlists(self.watchlists, self.active_wl, CURRENT_LANG, CURRENT_THEME)
        # Rebuild tabs
        self.tabs.clear_widgets()
        for wl_name, items in self.watchlists.items():
            tab = WatchlistTab(wl_name, items, on_remove=lambda t: self._remove_item_from_wl(t))
            self.tabs.add_widget(tab)
        self.current_tab = self.tabs.default_tab
    
    def _refresh_current_wl(self):
        if not self.active_wl or self.active_wl not in self.watchlists:
            return
        ticker_list = [item[1] for item in self.watchlists[self.active_wl]]
        self._fetch_and_update_prices(ticker_list)
    
    def _refresh_all_prices_threaded(self):
        all_tickers = []
        for items in self.watchlists.values():
            all_tickers.extend([item[1] for item in items])
        all_tickers = list(set(all_tickers))
        self._fetch_and_update_prices(all_tickers)
    
    def _fetch_and_update_prices(self, tickers):
        """Fetch prices in background thread."""
        def fetch_worker():
            results = {}
            for ticker in tickers:
                results[ticker] = fetch_price(ticker)
            Clock.schedule_once(lambda dt: self._apply_price_updates(results))
        
        threading.Thread(target=fetch_worker, daemon=True).start()
    
    def _apply_price_updates(self, results):
        for tab in self.tabs.tab_list:
            if isinstance(tab, WatchlistTab):
                tab.update_prices(results)
        self.status_label.text = "Prices updated"
        Clock.schedule_once(lambda dt: setattr(self.status_label, "text", t("status_ready")), 3)

    
    def _new_watchlist(self):
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        input_field = TextInput(hint_text="Watchlist name...", font_size="14sp",
                               size_hint_y=None, height=40)
        content.add_widget(input_field)
        
        def on_confirm(*_):
            name = input_field.text.strip()
            if name:
                self.watchlists[name] = []
                self.active_wl = name
                self._save_and_refresh()
                popup.dismiss()
        
        btn = Button(text=t("btn_ok"), size_hint_y=None, height=40,
                    background_color=get_color_from_hex("#4CAF50"))
        btn.bind(on_press=on_confirm)
        content.add_widget(btn)
        
        popup = Popup(title=t("btn_new_wl"), content=content, size_hint=(0.8, 0.4))
        popup.open()
    
    def _del_watchlist(self):
        if not self.active_wl:
            return
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        content.add_widget(Label(text=f"Delete {self.active_wl}?", font_size="14sp"))
        
        def on_yes(*_):
            if self.active_wl in self.watchlists:
                del self.watchlists[self.active_wl]
            if self.watchlists:
                self.active_wl = list(self.watchlists.keys())[0]
            else:
                self.active_wl = ""
            self._save_and_refresh()
            popup.dismiss()
        
        def on_no(*_):
            popup.dismiss()
        
        row = BoxLayout(size_hint_y=None, height=40, spacing=10)
        btn_yes = Button(text="Yes", size_hint_x=0.5, background_color=get_color_from_hex("#f44336"))
        btn_yes.bind(on_press=on_yes)
        btn_no = Button(text="No", size_hint_x=0.5, background_color=get_color_from_hex("#999999"))
        btn_no.bind(on_press=on_no)
        row.add_widget(btn_yes)
        row.add_widget(btn_no)
        content.add_widget(row)
        
        popup = Popup(title=t("btn_del_wl"), content=content, size_hint=(0.8, 0.4))
        popup.open()
    
    def _show_add_dialog(self):
        """Show add item popup with search."""
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        
        search_input = TextInput(hint_text=t("lbl_search"), font_size="14sp",
                                size_hint_y=None, height=40)
        content.add_widget(search_input)
        
        results_scroll = ScrollView(size_hint_y=0.6)
        results_layout = BoxLayout(orientation="vertical", size_hint_y=None, padding=5)
        results_layout.bind(minimum_height=results_layout.setter("height"))
        results_scroll.add_widget(results_layout)
        content.add_widget(results_scroll)
        
        def on_search(*_):
            query = search_input.text.strip()
            results_layout.clear_widgets()
            if not query:
                return
            results = search_tickers(query, limit=12)
            for name, ticker, full in results:
                row = SearchRow(name, ticker, full,
                              lambda n, tk, fn: (self._add_to_wl(n, tk, fn), search_input.clear()),
                              size_hint_y=None, height=40)
                results_layout.add_widget(row)
        
        search_input.bind(text=on_search)
        
        popup = Popup(title=t("dlg_add_title"), content=content, size_hint=(0.9, 0.7))
        popup.open()
    
    def _direct_input_dialog(self):
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        
        ticker_input = TextInput(hint_text=t("dlg_ticker_hint"), font_size="14sp",
                                size_hint_y=None, height=40)
        content.add_widget(ticker_input)
        
        name_input = TextInput(hint_text=t("dlg_label_hint"), font_size="14sp",
                              size_hint_y=None, height=40)
        content.add_widget(name_input)
        
        def on_confirm(*_):
            ticker = ticker_input.text.strip()
            name = name_input.text.strip() or ticker
            if ticker:
                self._add_to_wl(name, ticker, name)
                popup.dismiss()
        
        btn = Button(text=t("btn_ok"), size_hint_y=None, height=40,
                    background_color=get_color_from_hex("#4CAF50"))
        btn.bind(on_press=on_confirm)
        content.add_widget(btn)
        
        popup = Popup(title=t("dlg_add_title"), content=content, size_hint=(0.8, 0.5))
        popup.open()


# ─── Entry Point ─────────────────────────────────────────────────
if __name__ == "__main__":
    WatchlistApp().run()
