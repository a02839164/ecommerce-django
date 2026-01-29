# Django 實作的電商後端系統

[![Live Demo](https://img.shields.io/badge/線上-Demo-brightgreen?style=for-the-badge)](https://buyriastore.com)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.x-blue?style=for-the-badge)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Cloud_SQL-blue?style=for-the-badge)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-Session_%26_Cache-red?style=for-the-badge)](https://redis.io/)
[![Cloudflare](https://img.shields.io/badge/Cloudflare-DNS_%26_CDN-orange?style=for-the-badge)](https://www.cloudflare.com/)
[![GCP](https://img.shields.io/badge/GCP-Compute_Engine-blue?style=for-the-badge)](https://cloud.google.com/)

## 概述

「這是我模擬真實電商營運環境所開發的專案。除了基礎功能，花了些心思在處理『庫存超賣』、『金流異步回傳』以及『系統架構重構』等實際開發中會遇到的難題。」

開發過程中，特別著重以下挑戰：
* **確保資料一致性：** 處理交易與金流 Webhook 的同步，保證訂單狀態絕對準確。
* **高併發下的庫存控制：** 透過資料庫事務 (Transaction) 與預扣機制，預防搶購時發生超賣問題。
* **系統的長期維護性：** 實作 Service Layer 模式來封裝商業邏輯，避免代碼變得臃腫難以維護。

---

##  設計決策

### 1. 搜尋效能優化：從 2.6 秒到 30 毫秒
**遇到的問題：**
當引入商品資料量至百萬級別時，傳統 ORM 的`icontains`會觸發全表掃描，導致搜尋延遲高達 2.6 秒以上，造成明顯的網頁卡頓與使用者流失。

**我的做法：**
* **B-tree Index：** 針對分類篩選與排序欄位建立 B-tree 複合索引，優化查詢路徑。
* **GIN Trigram Index (pg_trgm)：** 捨棄效能低下的傳統模糊搜尋，大幅提升 `ILIKE %keyword%` 的匹配速度。
* **Raw SQL 優化：** 改寫查詢邏輯為 Raw SQL，並採用 ID 延遲關聯，快速篩選出目標 ID 列表，再回補詳細資料，極小化記憶體與 I/O 消耗

**具體成果：**
  在壓力測試中，模糊搜尋從「明顯卡頓」變成秒開(2.6秒降至30毫秒)，效能提升**80倍**，解決搜尋延遲問題


### 2. Redis 實務應用 & 配置
**為什麼使用 Redis：** 
為了提升系統回應速度，引入 Redis 作為記憶體資料庫。將原本放在資料庫或檔案系統的 Session 與常用資料快取 Cache 移至 Redis，大幅減少磁碟 I/O，讓系統在高流量下保持低延遲。但如果 Redis 沒有分別配置，會導致 Session 與 Cache 功能錯亂混淆(如:線上的使用者被強制登出)。

**我的做法：**
* **資料庫區隔：**在 Redis 配置了不同的資料庫編號，讓 Session 儲存與快取資料徹底分開。
* **帶來的價值：**使用 Redis 與配置確保穩定性。不僅可以放心執行快取維護或清理，不會影響到使用者的登入狀態，更符合真實環境的運作標準。


### 3. 金流 Webhook 與狀態一致性
**設計初衷：**
串接金流選擇將 PayPal Webhook 異步回傳視為系統狀態更新的最終可信來源，規避網路環境影響或人為竄改的風險。

**我的做法：**
* **嚴謹驗證：** 每筆 Webhook 請求經過官方簽章驗證，確保訊息由 PayPal 官方發出，防止惡意偽造請求。
* **防重複處理：** 實作冪等性檢查。在處理訂單狀態變更前，會先比對該事件 ID 與訂單當前狀態。

**帶來的保障：**
  不依賴前端防止惡意串改、系統異常；冪等性檢查確保即使 PayPal 因為網路波動重複發送了相同的 Webhook 事件，系統也不會觸發重複扣庫存或更新訂單，保證金流與庫存資料絕對精確。


### 4. 架構重構：引入 Service Layer
**為什麼要重構：**
原本的開發方式會讓 Model 或 View 變得很肥大，像「庫存預扣」或「購物車金額計算」混在一起，不但難以維護，要寫測試時也發現邏輯太散，很難精準測試。

**我的做法：**
* **模組化設計：** 透過 Service Layer 封裝外部 API（如 PayPal、Shippo）。
* **獨立業務邏輯：** 實作 `PaypalService` 與 `InventoryService`，將核心邏輯抽離，View 只單純負責資料結構，「怎麼算錢」、「怎麼扣庫存」由專門的 Service 負責。

**帶來的改變：**
* **更容易測試：** 可以針對這些 Service 編寫單元測試，不用再擔心改 A 功能卻壞 B 功能。
* **依賴解耦：** View 只跟 Service 對接，未來如果公司決定更換 API 服務，只需要修改或新增 Service 實作即可，完全不需要更動到 View 流程，大大降低維護成本。


### 5. 安全防禦、風控
**設計考量：**
電商平台最怕遇到惡意攻擊（如 DDoS）或爬蟲濫用。我除了在程式碼層級做防護，也在網路基礎架構防線。

**我的做法：**
* **隱藏源站 IP：** 透過 GCP VPC 防火牆設定白名單，僅允許來自 Cloudflare 的流量。能徹底防止攻擊者繞過 CDN 直接攻擊伺服器真實 IP。
* **流量清洗與過濾：** 整合 Cloudflare WAF 與 Turnstile (驗證碼)，在登入、註冊及客服表單阻擋自動化腳本與惡意 Web 攻擊。
* **帳號與交易防護：** 實作 Email 驗證機制，確保帳號真實性。

**帶來的保障：**
  系統在面對真實網路環境時更具彈性，提升了使用者的帳號安全性，也大幅降低了伺服器被惡意流量灌爆的風險。

---

## 技術棧與佈署

### 核心技術棧
* **後端框架：** Django 5.2.6, Python 3.10+
* **資料庫：** PostgreSQL（Google Cloud SQL）
* **記憶體資料庫：** Redis 
* **非同步任務：** Celery + Redis Broker
* **容器化技術：** Docker & Docker Compose
* **第三方API服務：** 
  * **金流與物流：** PayPal REST API, Shippo API
  * **驗證與通訊：** Google OAuth 2.0, SendGrid (Email)
  * **安全防護：** Cloudflare WAF, Turnstile

### 生產環境架構
**本專案部署於 Google Cloud Platform (GCP)，並採用標準化生產配置：**
* **伺服器：** GCP Compute Engine (Ubuntu) 搭配 Gunicorn 作為 WSGI 伺服器。
* **反向代理：** Nginx 處理靜態資源與 HTTPS (Let's Encrypt) 憑證加密。
* **雲端儲存：** 靜態檔案與使用者上傳圖片託管於 Google Cloud Storage (GCS)，達成動靜分離。
* **環境管理：** 透過環境變數（`.env`）管理敏感資訊，並提供`.env.example`供開發者參考。

---

## Quick Start
### Docker 快速啟動
專案整合 Django、PostgreSQL、Redis 及 Celery，一行指令即可完成建置。
* **環境配置：** 參考 `.env.example` 建立 `.env` 檔案。
* **啟動指令：** 
```bash
docker-compose up --build -d
```
### Unit Testing
專案包含 18 項自動化測試案例，包含購物車、庫存管理、郵件服務、客服工單。
```bash
# 全域測試 (可針對特定模組進行測試；如: cart, inventory)
docker exec -it buyria_web python manage.py test
```

### 資料庫維護
專案提供自動化腳本，用於 Docker 環境下的 PostgreSQL 備份與還原。
#### 1.賦予執行權限
在執行腳本前，請先確保腳本具備執行權限：
```bash
chmod +x local_backup.sh local_restore.sh
```
#### 2.備份
讀取 .env 配置，產生壓縮備份檔於 ./db_backups/
```bash
./local_backup.sh
```
#### 3.還原
執行後可從清單中選擇備份檔進行還原。注意：執行將會重置現有資料庫
```bash
./local_restore.sh
```

## 聯絡方式
如果您欲瞭解專案的後台架構，歡迎透過 Email 聯繫。可提供後台測試帳號，進一步檢視管理流程、庫存異動日誌( csv設計 )與結構設計。

* **Email:** a02839164@gmail.com

