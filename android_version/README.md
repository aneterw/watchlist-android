# yfinance Watchlist Manager — Android 版

## 專案結構

```
android_version/
├── main.py              # 主程式（Kivy UI）
├── common_data.py       # 共用 ticker 索引 + 預設 Watchlist
├── language_data.py     # 6 種語言翻譯
├── requirements.txt     # Python 相依套件
├── buildozer.spec       # Buildozer 打包設定
└── README.md            # 本檔案
```

## 功能特性

- **181+ 個內建 Ticker**：美股、台股、港股、A股、加密貨幣、期貨、匯率
- **6 種語言**：繁體中文、簡體中文、English、日本語、한국어、Español
- **即時價格**：透過 yfinance 抓取 Yahoo Finance 資料
- **搜尋功能**：4 級搜尋策略（精確 → 前綴 → 名稱包含 → 網路）
- **自動儲存**：Watchlist 狀態自動儲存到 JSON
- **背景更新**：可手動更新單一或全部 Watchlist

## 安裝與打包

### 1. 安裝 Buildozer（Linux/Mac）

```bash
pip install buildozer cython
pip install kivy.deps.sdl2 kivy.deps.glew
```

### 2. 安裝 Android SDK/NDK

```bash
# 下載 Android SDK
sdkmanager "platforms;android-33" "build-tools;33.0.0"

# 設定環境變數
export ANDROID_HOME=$HOME/Android/Sdk
export ANDROID_SDK_ROOT=$HOME/Android/Sdk
export ANDROID_NDK_ROOT=$HOME/Android/Sdk/ndk/25.2.9519653
```

### 3. 打包 APK

```bash
cd android_version
buildozer android debug
```

### 4. 安裝到 Android 裝置

```bash
# 透過 USB 連接 Android 手機
buildozer android debug deploy run
```

## 在 PC 上測試 Kivy UI

```bash
cd android_version
py main.py
```

## 使用說明

1. **啟動程式** → 顯示預設 Watchlist 標籤頁
2. **搜尋商品** → 在搜尋框輸入 ticker 或名稱
3. **加入商品** → 點擊搜尋結果旁的「加入」按鈕
4. **更新價格** → 點擊工具列的「更新」按鈕
5. **切換標籤** → 點擊不同 Watchlist 的標籤頁

## 技術架構

| 元件 | 說明 |
|---|---|
| Kivy | Python 跨平台 UI 框架 |
| yfinance | Yahoo Finance API 客戶端 |
| pandas/numpy | 資料處理 |
| Buildozer | Android APK 打包工具 |

## 注意事項

- 需要網路連線才能獲取即時價格
- 首次啟動可能需要較長時間載入相依套件
- Android 版功能較桌面版簡化，核心邏輯保持一致
