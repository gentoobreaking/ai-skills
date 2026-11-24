---
name: rea-apk-pcap-analysis
description: 使用 REA MCP 工具對 Android APK 與已側錄的 PCAP/HAR 封包檔進行聯合逆向與 API 參數追蹤分析。當使用者要求分析 traffic.pcap、比對 API 簽章生成邏輯、或從封包反推 APK 程式碼時觸發此技能。
---

# REA MCP 封包與 Android APK 聯合分析技能

本技能指導 AI Agent 在取得明文封包（`.pcap` / `.har`）與目標 `.apk` 後，利用 **REA (Reverse Engineer Anything) MCP** 系統化地拆解網路請求、定位關鍵 API，並在反編譯程式碼中追蹤參數生成與加密邏輯。

> **合規與安全邊界**：本技能僅限用於使用者擁有所有權或已取得明確合法授權之應用程式進行安全評估、除錯與協定分析。嚴禁生成自動化攻擊腳本、憑證竊取工具或未授權存取指令。

---

## 核心分析原則

1. **證據驅動（Evidence-First）**：所有關於 API 結構、加密演算法或程式碼路徑的結論，必須嚴格對應到 REA 工具回傳的實際封包內容與反編譯類別/函式名稱，禁止猜測或腦補未驗證的邏輯。
2. **由外而內追蹤（Traffic-to-Code）**：先從封包（`.pcap`）鎖定目標網域、URL 路徑與特殊 Header/Payload 欄位（如 `Sign`、`Signature`、`Token`、`X-Timestamp`、`Nonce`），再以這些特徵字串作為關鍵字去搜尋 APK 反編譯程式碼，避免盲目翻找整個 APK。
3. **漸進式深入（Progressive Disclosure）**：先產出高層次的 API 端點總覽，確認目標端點後再針對單一加密或簽章參數進行深度呼叫鏈（Call Graph）追蹤。

---

## 標準分析工作流（SOP）

### 階段一：確認輸入檔案與 REA MCP 狀態
1. 檢查當前工作目錄中是否存在目標 `.apk` 檔案與封包檔案（`.pcap` 或 `.har`）。若缺少任一檔案或檔名不明確，先向使用者確認路徑。
2. 確認 REA MCP 工具可正常呼叫；若尚未初始化，引導使用者執行 `npx rea-agents@latest setup` 完成註冊。

### 階段二：封包流量結構化解析（PCAP / HAR）
呼叫 REA 的封包分析工具解析目標封包檔，並整理出以下資訊：
1. **網域與端點清單**：過濾掉第三方統計、廣告或系統背景連線（如 Google/Firebase 遙測），列出核心業務 API 的 `Method`、`Host`、`Path` 與 `Status Code`。
2. **特徵參數標記**：識別請求中包含動態計算或看似經過編碼/加密的欄位：
   * **Header 關鍵欄位**：如 `Authorization`、`X-Sign`、`X-Token`、`X-Timestamp`、`X-Nonce` 等。
   * **Query / Body 關鍵欄位**：如 `sign`、`sig`、`hash`、`encrypted_data` 等。
3. **展示摘要**：以簡潔表格向使用者呈現找到的主要 API 端點與疑難參數，若使用者未指定特定 API，主動詢問或優先挑選最核心的業務請求進入階段三。

### 階段三：APK 靜態反編譯與關鍵字定位（JADX）
針對鎖定的 API 端點與特徵參數，呼叫 REA 的 Android/JADX 工具執行以下追蹤：
1. **定位網路層定義**：
   * 搜尋 API 的 URL 路徑字串（例如 `/api/v1/login`），找出定義該端點的 Retrofit Interface、OkHttp Interceptor 或自訂網路封裝類別。
2. **追蹤簽章與加密邏輯**：
   * 搜尋特徵 Header 或參數名稱（例如 `"X-Sign"` 或 `"sign"`）。
   * 沿著變數賦值與函式呼叫關係（Cross-References / Xrefs）往上回溯，找出計算該數值的核心函式。
3. **辨識演算法與加鹽（Salt）結構**：
   * 確認該函式使用的雜湊或加密方式（如 MD5、SHA-256、HMAC、AES/RSA）。
   * 記錄參與運算的參數組合順序（例如：`參數排序拼接 + Timestamp + 固定 Salt`）。
   * **原生函式庫處理**：若追蹤到 `native` 宣告（JNI 呼叫 `.so` 檔），明確指出對應的 `.so` 函式庫名稱與 JNI 方法簽章；若環境已配置 Ghidra/Hopper MCP，則進一步對該 `.so` 函式進行反編譯分析。

### 階段三（補充）：React Native 架構專屬處理流程
若在 JADX 反編譯結果中發現 `com.facebook.react` 套件，且找不到業務 API 路徑，代表目標為 **React Native** 應用，必須改從 JS Bundle 追蹤業務邏輯：

1. **解壓並檢查 Bundle 格式**：
   * 使用 `unzip -q target_app.apk -d ./unpacked_apk` 解開 APK。
   * 檢查 `./unpacked_apk/assets/index.android.bundle` 的檔案類型（執行 `file ./unpacked_apk/assets/index.android.bundle`）。
2. **還原 JavaScript / Hermes 位元組碼**：
   * **若為純文字 JS**：安裝並執行 `npx js-beautify ./unpacked_apk/assets/index.android.bundle -o ./recovered_bundle.js` 進行格式化排版。
   * **若為 Hermes Bytecode**：確認並使用 `hermes-dec`（若未安裝則透過 `pip3 install git+https://github.com` 安裝）執行 `hbc-decompiler ./unpacked_apk/assets/index.android.bundle ./recovered_bundle.js` 還原程式碼。
3. **在還原後的 Bundle 中追蹤 API 與簽章**：
   * 直接在 `./recovered_bundle.js` 中搜尋 `traffic.pcap` 裡發現的 API 路徑或特殊 Header 名稱（如 `X-Sign`）。
   * 追蹤 `fetch`、`axios` 攔截器（Interceptors）或加密函式庫（如 `CryptoJS`、`hmac`）的調用上下文，還原參數生成規則。
   * 若 JS 透過 `NativeModules` 呼叫底層原生模組，再回到 JADX 或 `.so` 檔中追蹤對應的原生方法。

---

## 輸出報告格式規範

完成分析後，請以結構化 Markdown 輸出分析報告，包含以下四個區塊：

1. **API 流量總覽表**：列出關鍵端點、HTTP 方法與核心驗證欄位。
2. **目標請求詳解**：展示選定 API 的完整 Request Header 與 Body 結構（敏感個人憑證如真實密碼或 Session Token 請自動遮罩）。
3. **程式碼追蹤路徑（Call Chain）**：以 `類別名稱.方法名稱()` 的階層方式，清晰列出從網路請求發起到參數生成的完整呼叫鏈。
4. **參數生成規則總結**：用虛擬碼（Pseudocode）或條列式公式說明簽章/加密參數的輸入來源、拼接順序與演算法邏輯。

