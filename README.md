Django 生產級電商平台 (Ecommerce Project)

## 專案簡介 (Project Overview)

這是一個正式上線的完整電商平台，功能涵蓋商品瀏覽、購物車、結帳金流、物流追蹤、庫存管理、會員系統以及客服工單流程。
開發此專案是以「打造可實際營運的生產級後端系統」為目標。過程中著重於解決真實商業場景會遇到的痛點：
交易流程的真實性、正確性、高併發下的資料一致性以及系統的可維護性。



## 架構概述 (Architecture Overview)

本系統以 Django 為核心，採多 app 架構劃分不同業務職責，並透過明確的 service layer 協調跨模組流程，
避免業務邏輯分散於 view 或 signals 中，以提升可讀性與可維護性。

本系統以 Django 為核心，採用多 App 架構劃分業務職責，並透過明確定義的 Service Layer 來協調跨模組流程，
避免將複雜邏輯寫在 Views 或 Signals 中，確保程式碼在專案擴大後，依然易讀且好維護。


### 商品瀏覽與搜尋 Store/
1.Slug 自動化：商品建立時自動生成唯一 Slug。
2.高效搜尋設計：考量到資料量成長後的效能問題，針對百萬筆資料級別的模糊搜尋進行了優化。
透過混合使用 B-tree 與 GIN trigram 索引，避免全表掃描（Full Table Scan），大幅降低資料庫負擔。


### 付款與退款處理 Payment/
1.整合 PayPal 金流，並由 Service Layer 統一管理訂單建立、驗證與狀態更新。
2.設計了嚴謹的錯誤處理機制，一旦流程出現異常會即時中斷並回傳明確錯誤。
3.Source of Truth：付款與退款狀態一律以 Webhook 驗證結果為準，確保最終交易狀態的正確性。


### 物流與出貨追蹤 shipping/
1.封裝 Shippo 第三方物流服務，自動依訂單資訊購買運送標籤並取得追蹤碼。
2.透過模擬事件回拋機制更新出貨狀態，讓使用者的訂單狀態與物流端保持同步。


### 庫存管理 inventory/
1.使用者端支援預扣、釋放、出貨扣減與退貨回補；管理者端提供單筆與批次（CSV）庫存調整。
2.原子性操作：所有庫存變動皆在 Database Transaction 中執行，並完整記錄異動 Log，確保資料絕對一致且可追蹤。


### 通知與客服 Notifications/ & Support/
1.採事件導向 (Event-Driven) 設計，將通知邏輯與核心業務解耦。
2.客服系統擁有獨立的工單與對話模型，並保留完整歷史紀錄，支援問題追蹤與回覆。



## 核心設計決策 (Key Design Decisions) 

### 商品搜尋效能優化策略：從 2.6 秒到 30 毫秒
在設計搜尋功能時，我將「效能的可預期性」列為首要考量。當資料量達到百萬筆時，單純使用 Django ORM 的 icontains 進行全表掃描會導致嚴重的延遲。
為了解決這個問題，我在資料庫層級採用了分工策略：

- **B-tree index** 
  處理分類、價格排序與 Prefix match，維持低成本且精準的查詢。

- **GIN trigram index（pg_trgm）**  
  專門處理 ILIKE %keyword% 類型的模糊搜尋。

成果：在壓力測試中，模糊搜尋的查詢時間由約 2.6 秒大幅降低至約 30 毫秒，效能提升超過 80 倍，確保了使用者體驗的流暢。


### CheckoutService 與 Service Layer 流程控制
結帳是電商最關鍵的環節。為了避免業務邏輯隨著功能迭代而失控，我拒絕將邏輯分散在 View 或 Model 中，而是集中於 CheckoutService。

- **流程協調者**
  CheckoutService 負責串接付款、訂單、庫存預扣與通知觸發。

- **權衡 (Trade-off)**
  雖然使用 Django Signals 可以「自動」觸發後續行為，但我選擇顯式 (Explicit) 撰寫流程。
  在涉及金流與庫存的情境下，這種作法能讓執行順序一目瞭然，不僅除錯效率高，也大幅降低
  維護時的隱性風險。


### PayPal Webhook 驅動的狀態管理
不依賴前端或即時 API 回傳的結果來判斷交易成敗，而是將 PayPal Webhook 視為最終可信來源 (Source of Truth)。

- **安全性**
  所有 Webhook 皆需通過官方簽章驗證，防止偽造請求。

- **狀態明確**
  依據 Webhook 的 event_type 嚴格區分付款成功、失敗、過期與退款，確保系統狀態與金流端完全一致。


### 庫存異動與冪等性 (Idempotency) 設計
庫存更新由 InventoryService 負責，並與 PayPal Webhook 事件緊密連動：

- **併發控制**
  在高併發結帳時，利用原子交易 (Atomic Transaction) 與預扣機制，防止超賣或搶貨。

- **冪等性處理**
  事件處理層會檢查訂單當前狀態，確保即使 Webhook 重複發送，庫存也不會被錯誤地重複扣減或回補。


### Notifications 事件導向的非同步通知
為了不影響核心交易流程的效能，通知系統採事件導向設計。

- **交易後發送**
  使用 transaction.on_commit 確保只有在資料庫資料成功寫入後，才會觸發通知，避免「信寄出了但訂單失敗」的尷尬情況。

- **職責分離**
  寄信邏輯封裝於 Email Service (SendGrid)，並透過 Template 產生內容，讓業務邏輯與通知管道徹底解耦。

  通知系統涵蓋的事件包含：
  - 帳號相關通知（註冊驗證、密碼變更）
  - 訂單狀態通知（付款完成、取消、退款）
  - 出貨狀態更新通知
  - 客服回覆提醒


### 客服工單與對話系統 Support System
為了有效追蹤使用者問題，我將客服系統設計為獨立的工單與訊息模型，完整記錄每筆對話歷史與回覆狀態，方便後續查詢與管理。

- **通知機制**
  採用了解耦設計，當管理員回覆訊息時，雖然會觸發 Email 通知，但訊息的儲存不依賴Email 的發送成功。
  即使第三方信件服務暫時異常，客服對話功能仍能正常運作，確保使用者的求助管道不會因此中斷。



## 技術實作摘要（Optional）

- 結帳流程集中於 service layer，明確控制付款、庫存與物流的執行順序
- 使用交易與預扣機制避免超賣、搶貨與負庫存問題
- PayPal webhook 具備簽章驗證與冪等處理，防止重複扣款或退款
- 通知系統以事件導向設計，並於交易提交後才發送信件
- 透過 Celery 與 Redis處理非同步任務，模擬物流 webhook 與出貨狀態更新
- 關鍵操作加入限流與機器人防護機制



## 安全與風控 (Security & Risk Mitigation)
針對電商常見的濫用風險，我在關鍵節點加入了防護：

- 帳號驗證：強制 Email 驗證流程，防止無效帳號消耗資源。
- 暴力破解防護：在結帳流程實作失敗次數統計，連續失敗超過閾值即暫時鎖定。
- 機器人防禦：整合 Cloudflare Turnstile 於登入與註冊介面，有效阻擋自動化攻擊。



## 部署與實際上線（Deployment & Production Experience）

本專案實際部署於 Google Cloud Platform 虛擬機（VM）雲端環境。
後端服務使用 Gunicorn 作為 WSGI server，並由 Nginx 負責反向代理、靜態檔案服務與 HTTPS 終端處理。
整體架構可支援多 worker 並行請求，符合實際上線環境的基本需求。

資料庫採用 PostgreSQL，並部署於 Google Cloud SQL（Managed Database）。
媒體檔案整合至 Google Cloud Storage，避免檔案儲存在本機造成擴充上的限制。

透過實際部署與上線經驗，專案涵蓋從本地開發、環境變數管理，到雲端部署與基本維運的完整流程。



## Getting Started

Live demo: https://buyriastore.com

專案並非以「快速 clone 執行」為主要目標。

本地開發所需之基礎環境版本：
- Python 3.10+
- Django 5.x
- PostgreSQL
- Redis (for Celery)
- 需設定 .env 環境變數（參考 .env.example）及相關第三方服務 API Keys。



## Contact 

如果您對此專案的後台架構、程式碼細節有興趣，歡迎透過 Email 聯繫。我可以提供後台測試帳號，讓您進一步檢視管理流程與資料結構設計。

- Email: a02839164@gmail.com