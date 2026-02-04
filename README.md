# Django 實作的電商後端系統

[![Live Demo](https://img.shields.io/badge/線上-Demo-brightgreen?style=for-the-badge)](https://buyriastore.com)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.x-blue?style=for-the-badge)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Cloud_SQL-blue?style=for-the-badge)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-blue?style=for-the-badge&logo=docker)](https://www.docker.com/)
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
當引入商品資料量至百萬級別時，傳統 ORM 的`icontains`會觸發全表掃描，導致搜尋延遲高達 2.6 秒以上，造成明顯的網頁卡頓與使用者流失。

**我的做法：**
* **B-tree Index：** 針對分類篩選與排序欄位建立 B-tree 複合索引，優化查詢路徑。
* **GIN Trigram Index (pg_trgm)：** 捨棄效能低下的傳統模糊搜尋，大幅提升 `ILIKE %keyword%` 的匹配速度。
* **Raw SQL 優化：** 改寫查詢邏輯為 Raw SQL，並採用 ID 延遲關聯，快速篩選出目標 ID 列表，再回補詳細資料，極小化記憶體與 I/O 消耗

**具體成果：**
  在壓力測試中，模糊搜尋從「明顯卡頓」變成秒開(2.6秒降至30毫秒)，效能提升**80倍**，解決搜尋延遲問題


### 2. Docker 容器化與服務編排
透過 Docker 與 docker-compose 統一開發與執行環境，Python版本、套件與系統相依性一致，避免因環境差異導致的部署問題，一鍵指令完成所有服務的啟動與串接。

**我的做法：**
* **多服務架構編排：** 使用 docker-compose 整合 Django、PostgreSQL、Redis 與 Celery 於獨立容器中運作，實現環境隔離，利於未來水平擴展。
* **多階段建置優化：** Python image 換成 Slim ，搭配 multi-stage build，把 build-time 依賴和 runtime 拆開，在實測環境下將 Docker image 體積減少約 70～75%（約由 2GB 降至 486MB），並降低執行環境的攻擊面。
* **容器內溝通實務：** 使用 service name 作為主機名稱進行跨容器通訊，避免硬編碼 IP。
* **應用案例-自動化備份：**利用 Celery 容器定期執行腳本，跨容器連線至資料庫執行 `pg_dump` 使用 `gzip` 進行壓縮備份。


### 3. Redis 實務應用 & 配置
為了提升系統回應速度，引入 Redis 作為記憶體資料庫。將原本放在資料庫或檔案系統的 Session 與常用資料快取 Cache 移至 Redis，減少磁碟 I/O，讓系統在高流量下保持低延遲。

**我的做法：**
* **資料庫區隔：**配置不同的資料庫編號，讓 Session 儲存與快取資料分開。
* **非同步任務寫入：**針對商品瀏覽紀錄高頻率的寫入需求，利用 Redis List 作為暫存隊列，把造成資料庫負擔的 I/O 動作轉交給 Celery 批量回寫，提升系統吞吐量。
* **多級快取：**結合 cache_page 與 Redis Mutex Lock，防止在極端流量下出現 快取擊穿 ，確保資料庫僅承受必要的查詢壓力。


### 4. 金流 Webhook 與狀態一致性
**設計初衷：**
串接金流選擇將 PayPal Webhook 異步回傳視為系統狀態更新的最終可信來源，規避網路環境影響或人為竄改的風險。

**我的做法：**
* **嚴謹驗證：** 每筆 Webhook 請求經過官方簽章驗證，確保訊息由 PayPal 官方發出，防止惡意偽造請求。
* **防重複處理：** 實作冪等性檢查。在處理訂單狀態變更前，會先比對該事件 ID 與訂單當前狀態。

**帶來的保障：**
  不依賴前端防止惡意串改、系統異常；冪等性檢查確保即使 PayPal 因為網路波動重複發送了相同的 Webhook 事件，系統也不會觸發重複扣庫存或更新訂單，保證金流與庫存資料絕對精確。


### 5. 安全防禦、風控
**設計考量：**
電商平台最怕遇到惡意攻擊（如 DDoS）。我除了在程式碼層級做防護，也在網路基礎架構防線。

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
* **資料庫：** PostgreSQL
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
#### 1.備份
系統整合 Celery Beat，每日 03:00 自動執行 `local_backup.sh` 並將壓縮檔存至 `./db_backups/`。

#### 2.還原
執行後可從清單中選擇備份檔進行手動還原。注意：執行將會重置現有資料庫
```bash
./local_restore.sh
```

## 聯絡方式
如果您欲瞭解專案的後台架構，歡迎透過 Email 聯繫。可提供後台測試帳號，進一步檢視管理流程、庫存異動日誌( csv設計 )與結構設計。

* **Email:** a02839164@gmail.com

