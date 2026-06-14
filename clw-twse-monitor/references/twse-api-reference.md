# TWSE OpenAPI 完整參考手冊

## 概述

**臺灣證券交易所 OpenAPI** 提供免費、無需 API Key 的市場資料存取。

- **Base URL**：`https://openapi.twse.com.tw/v1`
- **Swagger**：`https://openapi.twse.com.tw/v1/swagger.json`
- **格式**：JSON（`Accept: application/json`）或 CSV
- **認證**：無
- **端點總數**：143 個

### 與 gold-monitor 的差異

| 項目 | gold-monitor | twse-monitor |
|------|-------------|--------------|
| 資料來源 | 台灣銀行（牌告匯率） | 證交所（OpenAPI） |
| 資料類型 | 黃金存摺買賣價 | 股票/ETF/指數/ESG |
| 即時性 | 每 10 分鐘 | 每日收盤後更新 |
| API Key | 不需要 | 不需要 |

---

## 已實作的端點（twse_monitor.py）

| 模組 | 端點 | 用途 |
|------|------|------|
| `--check-messages` | `/opendata/t187ap04_L` | 重大訊息 |
| `--check-dividend` | `/exchangeReport/TWT48U_ALL` | 除權除息預告 |
| `--check-valuation` | `/exchangeReport/BWIBBU_ALL` | 殖利率/本益比/淨值比 |
| `--check-price` | `/exchangeReport/STOCK_DAY_ALL` | 個股日成交 |
| `--check-threshold` | `/exchangeReport/STOCK_DAY_ALL` | 閾值監控（同上） |
| `--check-alert` | `/announcement/notice` | 注意股票 |
| `--check-alert` | `/announcement/punish` | 處置股票 |
| `--check-alert` | `/exchangeReport/TWT85U` | 變更交易 |
| `--check-alert` | `/exchangeReport/TWTAWU` | 暫停交易 |
| `--check-insider` | `/opendata/t187ap12_L` | 持股轉讓申報 |
| `--check-insider` | `/opendata/t187ap11_L` | 董監事持股餘額 |
| `--check-revenue` | `/opendata/t187ap05_L` | 月營收 |
| `--check-revenue` | `/opendata/t187ap14_L` | EPS 產業統計 |
| `--check-revenue` | `/opendata/t187ap16_L` | 財測差異 10%+ |
| `--check-governance` | `/opendata/t187ap22_L` | 裁罰案件 |
| `--check-governance` | `/opendata/t187ap23_L` | 違反資訊申報 |
| `--check-governance` | `/opendata/t187ap24_L` | 經營權異動 |
| `--check-governance` | `/opendata/t187ap27_L` | 經營權+變更交易 |
| `--check-governance` | `/opendata/t187ap46_L_16` | ESG 資訊安全 |
| `--check-governance` | `/opendata/t187ap46_L_21` | ESG 職業安全衛生 |
| `--check-market` | `/exchangeReport/MI_INDEX` | 大盤統計 |
| `--check-market` | `/indicesReport/TAI50I` | 台灣50指數 |
| `--check-market` | `/indicesReport/MI_5MINS_HIST` | 加權指數歷史 |

**已實作**：23 個端點（佔 143 個的 16%）

---

## 完整端點清單（143 個）

### 證券交易（36 個）

| # | Endpoint | 說明 |
|---|----------|------|
| 1 | `/Announcement/BFZFZU_T` | 投資理財節目異常推介個股 |
| 2 | `/SBL/TWT96U` | 上市上櫃股票當日可借券賣出股數 |
| 3 | `/announcement/notetrans` | 集中市場公布注意累計次數異常資訊 |
| 4 | `/announcement/notice` | 集中市場當日公布注意股票 |
| 5 | `/block/BFIAUU_d` | 集中市場鉅額交易日成交量值統計 |
| 6 | `/block/BFIAUU_m` | 集中市場鉅額交易月成交量值統計 |
| 7 | `/block/BFIAUU_y` | 集中市場鉅額交易年成交量值統計 |
| 8 | `/exchangeReport/BFI84U` | 集中市場停資停券預告表 |
| 9 | `/exchangeReport/BFT41U` | 集中市場盤後定價交易 |
| 10 | `/exchangeReport/BWIBBU_ALL` | 上市個股日本益比、殖利率及股價淨值比（依代碼查詢） |
| 11 | `/exchangeReport/BWIBBU_d` | 上市個股日本益比、殖利率及股價淨值比（依日期查詢） |
| 12 | `/exchangeReport/FMNPTK_ALL` | 上市個股年成交資訊 |
| 13 | `/exchangeReport/FMSRFK_ALL` | 上市個股月成交資訊 |
| 14 | `/exchangeReport/FMTQIK` | 集中市場每日市場成交資訊 |
| 15 | `/exchangeReport/MI_5MINS` | 每 5 秒委託成交統計 |
| 16 | `/exchangeReport/MI_INDEX` | 每日收盤行情-大盤統計資訊 |
| 17 | `/exchangeReport/MI_INDEX20` | 集中市場每日成交量前二十名證券 |
| 18 | `/exchangeReport/MI_MARGN` | 集中市場融資融券餘額 |
| 19 | `/exchangeReport/STOCK_DAY_ALL` | 上市個股日成交資訊 |
| 20 | `/exchangeReport/STOCK_DAY_AVG_ALL` | 上市個股日收盤價及月平均價 |
| 21 | `/exchangeReport/STOCK_FIRST` | 每日第一上市外國股票成交量值 |
| 22 | `/exchangeReport/TWT48U_ALL` | 上市股票除權除息預告表 |
| 23 | `/exchangeReport/TWT53U` | 集中市場零股交易行情單 |
| 24 | `/exchangeReport/TWT84U` | 上市個股股價升降幅度 |
| 25 | `/exchangeReport/TWT85U` | 集中市場證券變更交易 |
| 26 | `/exchangeReport/TWT88U` | 上市個股首五日無漲跌幅 |
| 27 | `/exchangeReport/TWTAWU` | 集中市場暫停交易證券 |
| 28 | `/exchangeReport/TWTB4U` | 上市股票每日當日沖銷交易標的及統計 |
| 29 | `/exchangeReport/TWTBAU1` | 集中市場暫停先賣後買當日沖銷交易標的預告表 |
| 30 | `/exchangeReport/TWTBAU2` | 集中市場暫停先賣後買當日沖銷交易歷史查詢 |
| 31 | `/fund/MI_QFIIS_cat` | 集中市場外資及陸資投資類股持股比率表 |
| 32 | `/fund/MI_QFIIS_sort_20` | 集中市場外資及陸資持股前 20 名彙總表 |
| 33 | `/holidaySchedule/holidaySchedule` | 有價證券集中交易市場開（休）市日期 |
| 34 | `/opendata/t187ap19` | 電子式交易統計資訊 |
| 35 | `/opendata/t187ap37_L` | 上市權證基本資料彙總表 |
| 36 | `/opendata/twtazu_od` | 集中市場漲跌證券數統計表 |

### 指數（5 個）

| # | Endpoint | 說明 |
|---|----------|------|
| 1 | `/exchangeReport/MI_INDEX4` | 每日上市上櫃跨市場成交資訊 |
| 2 | `/indicesReport/FRMSA` | 寶島股價指數歷史資料 |
| 3 | `/indicesReport/MFI94U` | 發行量加權股價報酬指數 |
| 4 | `/indicesReport/MI_5MINS_HIST` | 發行量加權股價指數歷史資料 |
| 5 | `/indicesReport/TAI50I` | 臺灣 50 指數歷史資料 |

### 財務報表（30 個）

| # | Endpoint | 說明 |
|---|----------|------|
| 1 | `/opendata/t187ap05_L` | 上市公司每月營業收入彙總表 |
| 2 | `/opendata/t187ap06_L_basi` | 上市公司綜合損益表(金融業) |
| 3 | `/opendata/t187ap06_L_bd` | 上市公司綜合損益表(證券期貨業) |
| 4 | `/opendata/t187ap06_L_ci` | 上市公司綜合損益表(一般業) |
| 5 | `/opendata/t187ap06_L_fh` | 上市公司綜合損益表(金控業) |
| 6 | `/opendata/t187ap06_L_ins` | 上市公司綜合損益表(保險業) |
| 7 | `/opendata/t187ap06_L_mim` | 上市公司綜合損益表(異業) |
| 8 | `/opendata/t187ap06_X_basi` | 公發公司綜合損益表-金融業 |
| 9 | `/opendata/t187ap06_X_bd` | 公發公司綜合損益表-證券期貨業 |
| 10 | `/opendata/t187ap06_X_ci` | 公發公司綜合損益表-一般業 |
| 11 | `/opendata/t187ap06_X_fh` | 公發公司綜合損益表-金控業 |
| 12 | `/opendata/t187ap06_X_ins` | 公發公司綜合損益表-保險業 |
| 13 | `/opendata/t187ap06_X_mim` | 公發公司綜合損益表-異業 |
| 14 | `/opendata/t187ap07_L_basi` | 上市公司資產負債表(金融業) |
| 15 | `/opendata/t187ap07_L_bd` | 上市公司資產負債表(證券期貨業) |
| 16 | `/opendata/t187ap07_L_ci` | 上市公司資產負債表(一般業) |
| 17 | `/opendata/t187ap07_L_fh` | 上市公司資產負債表(金控業) |
| 18 | `/opendata/t187ap07_L_ins` | 上市公司資產負債表(保險業) |
| 19 | `/opendata/t187ap07_L_mim` | 上市公司資產負債表(異業) |
| 20 | `/opendata/t187ap07_X_basi` | 公發公司資產負債表-金融業 |
| 21 | `/opendata/t187ap07_X_bd` | 公發公司資產負債表-證券期貨業 |
| 22 | `/opendata/t187ap07_X_ci` | 公發公司資產負債表-一般業 |
| 23 | `/opendata/t187ap07_X_fh` | 公發公司資產負債表-金控業 |
| 24 | `/opendata/t187ap07_X_ins` | 公發公司資產負債表-保險業 |
| 25 | `/opendata/t187ap07_X_mim` | 公發公司資產負債表-異業 |
| 26 | `/opendata/t187ap11_P` | 公發公司董監事持股餘額明細 |
| 27 | `/opendata/t187ap15_L` | 上市公司截至各季綜合損益財測達成情形(簡式) |
| 28 | `/opendata/t187ap16_L` | 上市公司當季綜合損益經會計師查核(核閱)數與當季預測數差異達百分之十以上者，或截至當季累計差異達百分之二十以上者(簡式) |
| 29 | `/opendata/t187ap17_L` | 上市公司營益分析查詢彙總表(全體公司彙總報表) |
| 30 | `/opendata/t187ap31_L` | 上市公司財務報告經監察人承認情形 |

### 公司治理（56 個）

| # | Endpoint | 說明 |
|---|----------|------|
| 1 | `/announcement/punish` | 集中市場公布處置股票 |
| 2 | `/company/applylistingForeign` | 外國公司向證交所申請第一上市之公司 |
| 3 | `/company/applylistingLocal` | 申請上市之本國公司 |
| 4 | `/company/newlisting` | 最近上市公司 |
| 5 | `/company/suspendListingCsvAndHtml` | 終止上市公司 |
| 6 | `/opendata/t187ap02_L` | 上市公司持股逾 10% 大股東名單 |
| 7 | `/opendata/t187ap03_L` | 上市公司基本資料 |
| 8 | `/opendata/t187ap03_P` | 公開發行公司基本資料 |
| 9 | `/opendata/t187ap04_L` | 上市公司每日重大訊息 |
| 10 | `/opendata/t187ap05_P` | 公開發行公司每月營業收入彙總表 |
| 11 | `/opendata/t187ap08_L` | 上市公司董事、監察人持股不足法定成數彙總表 |
| 12 | `/opendata/t187ap09_L` | 上市公司董事、監察人質權設定占董事及監察人實際持有股數彙總表 |
| 13 | `/opendata/t187ap10_L` | 上市公司董事、監察人持股不足法定成數連續達3個月以上彙總表 |
| 14 | `/opendata/t187ap11_L` | 上市公司董監事持股餘額明細資料 |
| 15 | `/opendata/t187ap12_L` | 上市公司每日內部人持股轉讓事前申報表-持股轉讓日報表 |
| 16 | `/opendata/t187ap13_L` | 上市公司每日內部人持股轉讓事前申報表-持股未轉讓日報表 |
| 17 | `/opendata/t187ap14_L` | 上市公司各產業EPS統計資訊 |
| 18 | `/opendata/t187ap22_L` | 上市公司金管會證券期貨局裁罰案件專區 |
| 19 | `/opendata/t187ap23_L` | 上市公司違反資訊申報、重大訊息及說明記者會規定專區 |
| 20 | `/opendata/t187ap24_L` | 上市公司經營權及營業範圍異(變)動專區-經營權異動公司 |
| 21 | `/opendata/t187ap25_L` | 上市公司經營權及營業範圍異(變)動專區-營業範圍重大變更公司 |
| 22 | `/opendata/t187ap26_L` | 上市公司經營權及營業範圍異(變)動專區-經營權異動且營業範圍重大變更停止買賣公司 |
| 23 | `/opendata/t187ap27_L` | 上市公司經營權及營業範圍異(變)動專區-經營權異動且營業範圍重大變更列為變更交易公司 |
| 24 | `/opendata/t187ap29_A_L` | 上市公司董事酬金相關資訊 |
| 25 | `/opendata/t187ap29_B_L` | 上市公司監察人酬金相關資訊 |
| 26 | `/opendata/t187ap29_C_L` | 上市公司合併報表董事酬金相關資訊 |
| 27 | `/opendata/t187ap29_D_L` | 上市公司合併報表監察人酬金相關資訊 |
| 28 | `/opendata/t187ap30_L` | 上市公司獨立董監事兼任情形彙總表 |
| 29 | `/opendata/t187ap32_L` | 上市公司公司治理之相關規程規則 |
| 30 | `/opendata/t187ap33_L` | 上市公司董事長是否兼任總經理 |
| 31 | `/opendata/t187ap34_L` | 上市公司採累積投票制、全額連記法、候選人提名制選任董監事及當選資料彙總表 |
| 32 | `/opendata/t187ap35_L` | 上市公司股東行使提案權情形彙總表 |
| 33 | `/opendata/t187ap38_L` | 上市公司股東會公告-召集股東常(臨時)會公告資料彙總表(95年度起適用) |
| 34 | `/opendata/t187ap41_L` | 上市公司召開股東常(臨時)會日期、地點及採用電子投票情形等資料彙總表 |
| 35 | `/opendata/t187ap45_L` | 上市公司股利分派情形 |
| 36 | `/opendata/t187ap46_L_1` | ESG-溫室氣體排放 |
| 37 | `/opendata/t187ap46_L_10` | ESG-燃料管理 |
| 38 | `/opendata/t187ap46_L_11` | ESG-產品生命週期 |
| 39 | `/opendata/t187ap46_L_12` | ESG-食品安全 |
| 40 | `/opendata/t187ap46_L_13` | ESG-供應鏈管理 |
| 41 | `/opendata/t187ap46_L_14` | ESG-產品品質與安全 |
| 42 | `/opendata/t187ap46_L_15` | ESG-社區關係 |
| 43 | `/opendata/t187ap46_L_16` | ESG-資訊安全 |
| 44 | `/opendata/t187ap46_L_17` | ESG-普惠金融 |
| 45 | `/opendata/t187ap46_L_18` | ESG-持股及控制力 |
| 46 | `/opendata/t187ap46_L_19` | ESG-風險管理政策 |
| 47 | `/opendata/t187ap46_L_2` | ESG-能源管理 |
| 48 | `/opendata/t187ap46_L_20` | ESG-反競爭行為法律訴訟 |
| 49 | `/opendata/t187ap46_L_21` | ESG-職業安全衛生 |
| 50 | `/opendata/t187ap46_L_3` | ESG-水資源管理 |
| 51 | `/opendata/t187ap46_L_4` | ESG-廢棄物管理 |
| 52 | `/opendata/t187ap46_L_5` | ESG-人力發展 |
| 53 | `/opendata/t187ap46_L_6` | ESG-董事會 |
| 54 | `/opendata/t187ap46_L_7` | ESG-投資人溝通 |
| 55 | `/opendata/t187ap46_L_8` | ESG-氣候相關議題管理 |
| 56 | `/opendata/t187ap46_L_9` | ESG-功能性委員會 |

### 權證（3 個）

| # | Endpoint | 說明 |
|---|----------|------|
| 1 | `/opendata/t187ap36_L` | 上市認購(售)權證年度發行量概況統計表 |
| 2 | `/opendata/t187ap42_L` | 上市認購(售)權證每日成交資料檔 |
| 3 | `/opendata/t187ap43_L` | 上市認購(售)權證交易人數檔 |

### 券商資料（9 個）

| # | Endpoint | 說明 |
|---|----------|------|
| 1 | `/ETFReport/ETFRank` | 定期定額交易戶數統計排行月報表 |
| 2 | `/brokerService/brokerList` | 證券商總公司基本資料 |
| 3 | `/brokerService/secRegData` | 開辦定期定額業務證券商名單 |
| 4 | `/opendata/OpenData_BRK01` | 證券商營業員男女人數統計資料 |
| 5 | `/opendata/OpenData_BRK02` | 證券商分公司基本資料 |
| 6 | `/opendata/t187ap01` | 券商業務別人員數 |
| 7 | `/opendata/t187ap18` | 證券商基本資料 |
| 8 | `/opendata/t187ap20` | 各券商每月月計表 |
| 9 | `/opendata/t187ap21` | 各券商收支概況表資料 |

### 其他（4 個）

| # | Endpoint | 說明 |
|---|----------|------|
| 1 | `/exchangeReport/BFI61U` | 中央登錄公債補息資料表 |
| 2 | `/news/eventList` | 證交所活動訊息 |
| 3 | `/news/newsList` | 證交所新聞 |
| 4 | `/opendata/t187ap47_L` | 基金基本資料彙總表 |

---

## 資料限制與注意事項

### 即時性
- 大部分端點為**每日收盤後更新**，非即時行情
- `MI_5MINS`（每 5 秒委託成交統計）是唯一接近即時的端點
- 建議在 **14:00 後**執行監控，確保資料已更新

### 資料量
- `t187ap11_L`（董監事持股餘額）：27,000+ 筆，首次執行較慢
- `STOCK_DAY_ALL`（個股日成交）：1,300+ 筆，篩選後僅 3 筆
- `BWIBBU_ALL`（殖利率）：1,000+ 筆，篩選後僅少數

### ETF 限制
- `t187ap05_L`（月營收）僅限上市公司，**ETF 無月營收**
- `BWIBBU_ALL` 不一定包含 ETF 資料（0050 有，但殖利率可能為空）
- `STOCK_DAY_ALL` 和 `TWT48U_ALL` 包含 ETF

### 回應格式
- 所有端點支援 JSON（`Accept: application/json`）和 CSV
- 日期格式為**民國年**（如 `1150505` = 2026/05/05）
- 數字欄位為字串型態，需 `float()` / `int()` 轉換

---

## 擴展方向

### 如何新增監控標的
1. 在 `~/.twse_monitor_config.json` 的 `watchlist` 加入股票代碼
2. 在 `thresholds` 加入對應閾值（可選，有動態預設值）
3. 用 `--cost CODE VALUE` 設定持有成本
4. 下次 cron 執行時自動納入監控

### 如何新增監控模組
1. 在 `twse_monitor.py` 新增 `check_xxx()` 函式
2. 在 `MODES` dict 加入對應參數
3. 在 `HELP_TEXT` 加入說明
4. 更新 howto 文件

### 尚未實作但可考慮的端點
| 端點 | 用途 | 優先級 |
|------|------|--------|
| `/exchangeReport/MI_MARGN` | 融資融券餘額 | 中 |
| `/exchangeReport/TWT84U` | 個股股價升降幅度 | 低 |
| `/exchangeReport/TWTB4U` | 當日沖銷交易統計 | 中 |
| `/fund/MI_QFIIS_sort_20` | 外資持股前20名 | 中 |
| `/opendata/t187ap45_L` | 股利分派情形 | 高（已排入 T002） |
| `/opendata/t187ap02_L` | 大股東名單 | 低 |
| `/opendata/t187ap46_L_1~7` | ESG 其餘項目 | 低 |
| `/news/newsList` | 證交所新聞 | 低 |
