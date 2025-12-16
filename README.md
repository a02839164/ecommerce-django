# Django 生產級電商平台 (Production-Ready E-Commerce Platform)

[![Live Demo](https://img.shields.io/badge/線上-Demo-brightgreen?style=for-the-badge)](https://buyriastore.com)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.x-blue?style=for-the-badge)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Cloud_SQL-blue?style=for-the-badge)](https://www.postgresql.org/)
[![GCP](https://img.shields.io/badge/GCP-Compute_Engine-blue?style=for-the-badge)](https://cloud.google.com/)

## 專案概述 (Project Overview)

這是一個完整、可實際營運的電商後端系統，功能涵蓋商品瀏覽、購物車、金流結帳、物流追蹤、庫存管理、會員與客服工單。

開發目標 **「打造可實際營運的生產級後端系統」**。專注於真實情境下的核心：
* **資料一致性 (Data Consistency)：** 確保交易、庫存與金流狀態的絕對同步。
* **高併發控制 (Concurrency Control)：** 預防超賣、搶貨等問題。
* **系統可維護性 (Maintainability)：** 透過清晰架構降低技術債。

---

##  核心設計決策與工程亮點 (Key Design Decisions & Engineering Highlights)

### 1. 商品搜尋效能優化：從 2.6 秒到 30 毫秒

**挑戰 (The Challenge)：**
當商品資料量達到百萬級別時，單純使用 Django ORM 的模糊搜尋 (`icontains`) 會觸發全表掃描（Full Table Scan），導致查詢延遲嚴重（約 2.6 秒）。

**解決方案 (The Solution)：**
我在資料庫層級實現了混合索引策略：
* **B-tree Index：** 用於處理分類、價格排序及精準的前綴比對。
* **GIN Trigram Index (`pg_trgm`)：** 專門用於高效處理模糊搜尋 (`ILIKE %keyword%`)。

**成果 (The Result)：**
在壓力測試中，模糊搜尋的查詢時間由約 2.6 秒大幅降低至 **約 30 毫秒**，**效能提升超過 80 倍**，確保了使用者體驗的流暢度。

### 2. 結帳流程控制與顯式流程 (CheckoutService & Explicit Flow)

**權衡與取捨 (Trade-off)：**
雖然 Django Signals 可以「自動」觸發訂單後續行為，但在涉及金流與庫存的關鍵流程中，我選擇**顯式 (Explicit) 流程控制**。

**設計決策 (Design Decision)：**
* **流程協調者：** `CheckoutService` 集中負責串接付款、訂單建立、庫存預扣與通知觸發的執行順序。
* **優勢：** 這種作法能讓流程執行順序一目瞭然，不僅除錯效率高，也大幅降低了維護時的隱性風險。

### 3. 金流狀態管理：PayPal Webhook 作為最終可信來源 (Source of Truth)

不依賴前端或即時 API 回傳的結果，而是將 **PayPal Webhook** 視為最終可信來源。

* **安全性：**  Webhook 請求皆需通過官方**簽章驗證**，防止偽造。
* **狀態一致性：** 系統狀態嚴格以 Webhook 的 `event_type` 為準，使交易狀態（成功、失敗、退款）與金流端完全同步。

### 4. 庫存異動與冪等性 (Idempotency) 設計

**併發控制 (Concurrency Control)：**
* **原子操作：** 庫存變動在 **Database Atomic Transaction** 中執行，結帳搭配預扣機制，防止在高併發結帳時發生超賣或負庫存；
    提供管理者介面進行單一、批量庫存調整，透過 CSV 匯入/匯出功能進行大規模數據同步。所有異動皆記錄操作日誌。

**冪等性處理 (Idempotency)：**
* **防重複：** 事件處理層會檢查訂單當前狀態，即使 PayPal 重複發送 Webhook，庫存也不會被錯誤地重複扣減或回補，保障資料的絕對一致性。

### 5. 事件導向的非同步通知 (Event-Driven Asynchronous Notifications)

為了不影響核心交易流程的效能，通知系統採事件導向設計：

* **延遲觸發：** 使用 `transaction.on_commit` 確保只有在資料庫資料成功寫入後，才會觸發通知，避免「信寄出了但訂單失敗」的尷尬情況。
* **職責分離：** 寄信邏輯與核心業務徹底解耦，即使第三方信件服務異常，核心交易功能仍能正常運作。

---

## 安全與風控 (Security & Risk Mitigation)

針對電商常見的濫用風險，在關鍵節點加入防護機制：
* **帳號驗證：** 強制 Email 驗證流程。
* **機器人防禦：** 整合 Cloudflare Turnstile 於登入與註冊、客服表單。
* **暴力破解防護：** 在結帳等高風險流程實作失敗次數統計、暫時鎖定與限流（Rate limiting）機制。

---

## 技術棧與生產部署 (Tech Stack & Production Deployment)

### 核心技術棧
* **後端框架：** Django 5.x, Python 3.10+
* **資料庫：** PostgreSQL（Google Cloud SQL）
* **非同步任務：** Celery + Redis
* **金流服務：** PayPal REST API（含 Webhook 驗證）
* **物流服務：** Shippo API
* **Email 服務：** SendGrid API
* **身份驗證與安全：** Google OAuth 2.0、Cloudflare Turnstile（Bot / Abuse Protection）

### 部署架構 (GCP)
* **雲端環境：** Google Cloud Platform VM（Ubuntu）
* **應用服務：** Gunicorn 作為 WSGI Server
* **反向代理 / HTTPS：** Nginx + Let’s Encrypt
* **靜態與媒體檔案：** Google Cloud Storage
* **敏感資訊管理：** 透過環境變數（`.env`）管理敏感資訊，並以 `.env.example` 作為設定範例（未納入版本控制）

---

## 使用說明與聯絡方式

**Live Demo (線上展示):** [https://buyriastore.com](https://buyriastore.com)
> 本專案為實際上線的作品集，重點在於系統設計與後端實作，並非快速啟動模板。

### 本地開發環境需求
- Python 3.10+
- Django 5.x
- PostgreSQL
- Redis（Celery Broker）
- 設定 `.env` 環境變數（請參考 `.env.example`）


如果您對此專案的後台架構、程式碼細節有興趣，**歡迎透過 Email 聯繫。我可以提供後台測試帳號，讓您進一步檢視管理流程與資料結構設計。**

* **Email:** a02839164@gmail.com

For English summary, see README.en.md