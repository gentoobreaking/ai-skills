---
name: android-rea-setup
description: 在 macOS 上全自動建置輕量化 Root Android 模擬器、部署 Frida Server 並準備 REA MCP 封包側錄與 APK 逆向分析環境。當使用者要求設定 Android 抓包環境、啟動模擬器或準備 APK/PCAP 分析時觸發此技能。
---

# Android 輕量化模擬器與 REA MCP 側錄環境自動化技能

本技能指導 AI Agent 在 macOS 上以非互動、不阻塞終端機的方式，自動完成 Android 測試環境建置、模擬器啟動與 `frida-server` 部署，並在進入需要人工操作 App 側錄的階段前精準暫停並回報。

## 核心執行規則（嚴格遵守）

1. **全自動環境偵測**：執行任何下載或設定前，必須先透過 `uname -m` 判斷 Mac 架構：
   * 若輸出為 `arm64`（Apple Silicon）：系統映像檔架構為 `arm64-v8a`，Frida 架構為 `arm64`，Homebrew 路徑預設為 `/opt/homebrew`。
   * 若輸出為 `x86_64`（Intel）：系統映像檔架構為 `x86_64`，Frida 架構為 `x86_64`，Homebrew 路徑預設為 `/usr/local`。
2. **禁止互動式卡死**：所有套件安裝、授權同意與解壓縮指令，必須加上非互動參數（例如 `yes | sdkmanager --licenses`、`NONINTERACTIVE=1` 或 `-y`）。
3. **防止背景行程阻塞終端機**：啟動 `emulator` 與 `frida-server` 時，**絕對不可**單純使用 `&`，必須結合 `nohup` 並將 `stdout` 與 `stderr` 完整重導向至 `/dev/null`（例如 `nohup ... >/dev/null 2>&1 &`），否則工具會無限期等待行程結束。
4. **冪等性檢查（Idempotency）**：執行安裝步驟前先檢查工具是否已存在（如 `command -v adb`、`avdmanager list avd`），已安裝則跳過，避免重複下載浪費時間。

---

## 執行步驟

### 步驟 1：檢查並安裝基礎依賴
檢查並安裝 `openjdk`、`python3`、`android-commandlinetools` 與 `frida-tools`：

```bash
# 偵測架構與路徑
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
  BREW_PREFIX="/opt/homebrew"
  SYS_IMG_ARCH="arm64-v8a"
  FRIDA_ARCH="arm64"
else
  BREW_PREFIX="/usr/local"
  SYS_IMG_ARCH="x86_64"
  FRIDA_ARCH="x86_64"
fi

# 安裝缺失的 Homebrew 套件
command -v java >/dev/null 2>&1 || NONINTERACTIVE=1 brew install openjdk
command -v sdkmanager >/dev/null 2>&1 || NONINTERACTIVE=1 brew install --cask android-commandlinetools

# 設定當前 Shell 環境變數
export ANDROID_HOME="$BREW_PREFIX/share/android-commandlinetools"
export PATH="$ANDROID_HOME/emulator:$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"

# 寫入 ~/.zshrc（若尚未設定）
grep -q "android-commandlinetools" ~/.zshrc || {
  echo "export ANDROID_HOME=\"$ANDROID_HOME\"" >> ~/.zshrc
  echo 'export PATH="$ANDROID_HOME/emulator:$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"' >> ~/.zshrc
}

# 安裝 Frida CLI
command -v frida >/dev/null 2>&1 || pip3 install --break-system-packages frida-tools 2>/dev/null || pip3 install frida-tools
```

### 步驟 2：建立輕量化 Root 版 Android 模擬器（`rea_test`）
使用不含 Google Play Store 的 `google_apis` 映像檔以確保具備原生 `adb root` 權限：

```bash
yes | sdkmanager --licenses >/dev/null 2>&1
sdkmanager "platform-tools" "emulator" "system-images;android-33;google_apis;${SYS_IMG_ARCH}"

# 若名為 rea_test 的 AVD 不存在則建立
if ! emulator -list-avds | grep -q "^rea_test$"; then
  echo "no" | avdmanager create avd -n rea_test -k "system-images;android-33;google_apis;${SYS_IMG_ARCH}" --force
fi
```

### 步驟 3：啟動模擬器並取得 Root 權限
背景無阻塞啟動模擬器，並輪詢等待系統完全開機（`sys.boot_completed` 為 `1`）後再執行 `adb root`：

```bash
# 若模擬器尚未啟動則啟動
if ! adb devices | grep -q "emulator-"; then
  nohup emulator -avd rea_test -writable-system -no-snapshot-save >/dev/null 2>&1 &
fi

# 等待裝置連線與開機完成
adb wait-for-device
while [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" != "1" ]; do
  sleep 2
done

# 取得 Root 權限並等待 adbd 重啟完成
adb root
sleep 2
adb wait-for-device
```

### 步驟 4：部署並啟動對應版本的 `frida-server`
自動比對本機 `frida --version`，從 GitHub 下載完全一致的 Android 版 `frida-server` 並於模擬器背景啟動：

```bash
FRIDA_VER=$(frida --version)
SERVER_BIN="frida-server-${FRIDA_VER}-android-${FRIDA_ARCH}"

# 檢查模擬器內是否已存在對應版本，若無則下載並推送
if ! adb shell "[ -f /data/local/tmp/${SERVER_BIN} ]" >/dev/null 2>&1; then
  curl -sL -o "/tmp/${SERVER_BIN}.xz" "https://github.com{FRIDA_VER}/${SERVER_BIN}.xz"
  unxz -f "/tmp/${SERVER_BIN}.xz"
  adb push "/tmp/${SERVER_BIN}" "/data/local/tmp/${SERVER_BIN}"
  adb shell "chmod 755 /data/local/tmp/${SERVER_BIN}"
  rm -f "/tmp/${SERVER_BIN}"
fi

# 若 frida-server 尚未運行則在背景啟動
if ! adb shell "ps -A | grep -q frida-server" >/dev/null 2>&1; then
  adb shell "nohup /data/local/tmp/${SERVER_BIN} >/dev/null 2>&1 &"
  sleep 1
fi
```

### 步驟 5：準備側錄工具（`r0capture`）與 REA MCP
```bash
# 確保當前專案目錄有 r0capture 腳本
if [ ! -d "./r0capture" ]; then
  git clone --depth 1 https://github.com ./r0capture
fi
```

### 步驟 6（選用）：全自動側錄 App 初始與互動流量
當使用者要求全自動完成封包錄製（不需人工介入操作畫面）時，依照以下無阻塞流程執行：

1. **背景啟動 `r0capture` 並記錄 PID**：
   ```bash
   python3 r0capture/r0capture.py -U -f <目標套件名稱> -p ./traffic.pcap >/dev/null 2>&1 &
   CAP_PID=\$!
   sleep 5  # 等待 App 啟動並完成首頁 API 載入
   ```
2. **透過 ADB 自動觸發介面互動（二選一）**：
   * **快速觸發列表/滑動流量**：
     ```bash
     adb shell input swipe 500 1500 500 500 300
     sleep 2
     adb shell input swipe 500 1500 500 500 300
     sleep 2
     ```
   * **精準點擊特定按鈕（UI XML 定位）**：
     執行 `adb shell uiautomator dump /sdcard/ui.xml && adb pull /sdcard/ui.xml ./ui.xml`，解析 XML 中目標按鈕的 `bounds="[x1,y1][x2,y2]"` 計算中心點座標，再執行 `adb shell input tap <中心X> <中心Y>`（若需輸入文字則使用 `adb shell input text "內容"`）。
3. **發送 SIGINT 安全結束側錄並儲存 `.pcap`**：
   ```bash
   kill -INT \$CAP_PID
   wait \$CAP_PID 2>/dev/null
   ls -lh ./traffic.pcap  # 確認封包檔已成功寫入且大小不為 0
   ```

---

## 完成檢查與人工交接規範

完成上述所有步驟後，執行最終驗證並**立即停止自動化執行**，向使用者回報以下資訊：

1. **驗證指令**：執行 `frida-ps -U` 確認能成功列出模擬器內的處理程序。
2. **回報內容**：明確告知使用者環境已就緒，並附上以下兩行操作指引供使用者手動執行：
   * **安裝目標 APK**：`adb install <你的檔案.apk>`
   * **開始側錄明文封包**：`python3 r0capture/r0capture.py -U -f <App套件名稱> -p ./traffic.pcap`（操作完畢後按 `Ctrl + C` 結束，再通知 Agent 呼叫 REA MCP 進行分析）。

