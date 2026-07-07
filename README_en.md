### English | [中文](https://github.com/aneterw/yfinance-Watchlist-Manager/blob/main/README.md)

# yfinance Watchlist Manager — User Guide

## 1. Installation & Startup

### 1.1 Install Dependencies

Open Command Prompt (CMD) or PowerShell and run:

```bash
pip install yfinance
```

Python version requirement: Python 3.8 or higher.

### 1.2 Launch the Application

```bash
python watchlist_app.py
```

After launching, you will see the graphical user interface (GUI).

---

## 2. Interface Overview

After launching, you will see three main sections:

```
┌──────────────────┬─────────────────────────────────────────────┐
│  Watchlists       │  Asset Prices                               │
│  (Left Panel)     │  (Top Right)                                 │
│                   │                                               │
│  - Global Indices │  Name     Ticker    Price   Change  % Change │
│  - Tech ETFs       │  SPX    ^GSPC    ...                        │
│                   │                                               │
│                   ├─────────────────────────────────────────────┤
│                   │  Add Asset to Watchlist                       │
│                   │  (Bottom Right)                              │
└──────────────────┴─────────────────────────────────────────────┘

Top Toolbar: [+ New WL] [- Delete WL] [+ Add Asset] [- Remove Asset] [Refresh Current WL] [Refresh All Prices]
```

---

## 3. Feature Details

### 3.1 Default Watchlists

When the program starts, two default Watchlists are automatically created on the left panel:

| Watchlist Name | Contents                                                                            |
| -------------- | ----------------------------------------------------------------------------------- |
| Global Indices | S&P 500, NASDAQ, Dow Jones, FTSE100, DAX, Nikkei 225, SSE, Hang Seng, KOSPI, ASX200 |
| Tech ETFs      | QQQ, VGT                                                                            |
| TAIWAN         | TSMC, Foxconn, MediaTek, etc.                                                       |
| USA            | Apple, Microsoft, Google, etc.                                                      |

Click on a Watchlist name on the left panel, and the right panel will display all assets in that list.

---

### 3.2 Add / Delete Watchlist

**Add:**

1. Click **"+ New Watchlist"** in the toolbar
2. Enter the new list name (e.g., "My Favorites")
3. Press Enter or click OK

**Delete:**

1. Click on the Watchlist you want to delete on the left panel
2. Click **"- Delete Watchlist"**
3. Confirm in the dialog, select Yes

---

### 3.3 Add Assets to Watchlist (3 Methods)

#### Method A: Search & Add (Recommended)

1. First, select a Watchlist on the left panel
2. In the search box at the bottom right, enter a ticker or company name (e.g., `AAPL`, `Tesla`, `Bitcoin`)
3. Search results display in real-time (auto-filtered as you type)
4. **Double-click** any item in the search results to add it to the currently selected Watchlist

#### Method B: Button Add Selected

1. After searching, click to select an item in the search results
2. Enter your desired display name in the "Display Name" field (can be left blank)
3. Click **"+ Add Selected"**

#### Method C: Direct Ticker Input

1. Click the **"Direct Ticker Input"** button
2. In the popup dialog, enter the ticker (e.g., `BTC-USD`, `005930.KS`)
3. Display name is optional
4. Press Enter or click "Add"

> Common tickers reference:
> 
> ```
> AAPL       Apple Inc.
> MSFT       Microsoft Corp.
> NVDA       NVIDIA Corp.
> TSLA       Tesla Inc.
> BTC-USD    Bitcoin USD
> ETH-USD    Ethereum USD
> GC=F       Gold Futures
> CL=F       Crude Oil Futures
> EURUSD=X   EUR/USD Exchange Rate
> USDJPY=X   USD/JPY Exchange Rate
> USDCNY=X   USD/CNY Exchange Rate
> 2330.TW    TSMC (Taiwan)
> 005930.KS  Samsung Electronics (Korea)
> 0700.HK    Tencent Holdings (Hong Kong)
> ```

---

### 3.4 Remove Asset

1. In the "Asset Prices" list (top right), click on the asset you want to remove
2. Click **"- Remove Asset"** in the toolbar
3. Confirm in the dialog, select Yes

---

### 3.5 Update Prices

#### Update Current Watchlist

**Method:** Click **"Refresh Current WL"** in the toolbar

- Only updates assets in the currently selected Watchlist
- Does not affect prices in other Watchlists

#### Update All Prices

**Method:** Click **"Refresh All Prices"** in the toolbar

- Updates all assets across all Watchlists
- Runs in **background threading** so the UI won't freeze
- Status bar displays "Updating... Please wait"
- After completion, the right panel updates in real-time:
  - Up: Red
  - Down: Green
  - Unchanged: Dark gray

Price field descriptions:

| Field    | Description                   |
| -------- | ----------------------------- |
| Price    | Current market price          |
| Change   | Today's price change amount   |
| % Change | Today's percentage change (%) |
| Volume   | Today's trading volume        |

> Note: Some indices (starting with `^`) or forex pairs don't have volume data, showing N/A.

---

### 3.6 Auto-Update

The program **automatically updates all prices every 10 minutes** when idle. No manual action required.

---

### 3.7 Candlestick Chart (Double-click Asset)

**How to use:** In the "Asset Prices" list, **double-click** any asset row to open the candlestick chart window.

The candlestick chart window contains three subplots:

1. **Candlestick Chart** (top): Red for up, green for down, showing OHLC price movement
2. **Volume** (middle): Bar chart showing trading volume
3. **KD Indicator** (bottom): K line (orange) and D line (blue) for buy/sell signals

Period switching:

- **Daily**: Last 2 years of daily data
- **Weekly**: Last 10 years of weekly data
- **Monthly**: Last 30 years of monthly data

---

### 3.8 Theme & Language Settings

#### Theme

Menu bar **Theme** → Options:

- 🌓 System: Follows Windows system settings
- ☀ Light: Light mode (white background, dark text)
- 🌙 Dark: Dark mode (dark background, light text)

#### Language

Menu bar **Language** → Options:

- 繁體中文 (Traditional Chinese)
- 简体中文 (Simplified Chinese)
- English
- 日本語 (Japanese)
- 한국어 (Korean)
- Español (Spanish)

Language and theme settings are automatically saved and restored on next launch.

---

### 3.9 Data Storage

The program automatically saves Watchlist contents, language, and theme settings to `watchlist_data.json` (in the same directory as the program).

- **Saves immediately on every Watchlist modification**
- **Forces save again when closing the program**
- **Automatically loads previous state on next launch**

---

## 4. FAQ

### Q: Can I update a single Watchlist at a time?

A: Yes. Click **"Refresh Current WL"** to update only the currently selected Watchlist; click **"Refresh All Prices"** to update all.

### Q: Is data persisted permanently?

A: Yes. The program automatically saves Watchlists, language, and theme settings to `watchlist_data.json`, and restores automatically on next launch.

---

### Q: Can't find the ticker I'm looking for?

A:

1. Use **Method C (Direct Ticker Input)** and manually enter the official ticker
2. Common formats:
   - US stocks: `AAPL`, `GOOGL`
   - Crypto: `BTC-USD`, `ETH-USD`
   - Futures: `GC=F` (Gold), `CL=F` (Crude Oil)
   - Taiwan stocks: `2330.TW` on Yahoo Finance
   - Hong Kong stocks: `0700.HK`
   - Forex: `EURUSD=X`

### Q: Price updates are slow or failing?

A:

- yfinance requires internet connection; please verify your network
- Yahoo Finance occasionally rate-limits; if blocked due to heavy requests, wait and try again later
- The program has a built-in common ticker index; search function works offline

### Q: Candlestick chart won't display?

A:

- Make sure `matplotlib` and `mplfinance` are installed (`pip install matplotlib mplfinance`)
- Some cryptocurrencies or forex pairs have limited data; candlestick chart may appear empty

### Q: Some text is hard to read in dark mode?

A: Dark mode has been optimized for contrast; if issues persist, try switching to System or Light theme.

---

## 6. Technical Architecture (For Developers)

| Component           | Description                                                              |
| ------------------- | ------------------------------------------------------------------------ |
| `yfinance`          | Fetches real-time stock prices from Yahoo Finance API                    |
| `tkinter` / `ttk`   | Built-in GUI framework                                                   |
| `threading`         | Background fetching to prevent UI freezing                               |
| `watchlists` dict   | Core data structure; Key=name, Value=[(display name, ticker, full name)] |
| `fetch_price()`     | Single ticker price fetching function, returns full price dict           |
| `search_yfinance()` | Search function using yfinance native search + fallback index            |

---

## 7. Quick Start Guide (5 Minutes)

```
1. Launch the program
   > python watchlist_app.py

2. Click "Global Indices" on the left panel

3. The top-right table is pre-filled with major indices; click "Refresh Current WL" to view real-time data

4. Create a new Watchlist:
   > Click "+ New Watchlist" → Enter "My Favorites" → OK

5. Add a stock (example: TSMC):
   > Select "My Favorites" on the left
   > Enter "2330" in the bottom-right search box
   > Double-click "2330.TW - TSMC" in the results
   > (Or directly input "2330.TW" and click "Direct Ticker Input")

6. Click "Refresh Current WL" to see the results

7. Double-click any asset → Opens candlestick chart (Daily/Weekly/Monthly toggle)
```

Enjoy! 🎉