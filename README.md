# Django Production-Ready E-Commerce Platform

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen?style=for-the-badge)](https://buyriastore.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.x-092E20?style=for-the-badge&logo=django)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Cloud_SQL-336791?style=for-the-badge&logo=postgresql)](https://www.postgresql.org/)
[![GCP](https://img.shields.io/badge/GCP-Compute_Engine-4285F4?style=for-the-badge&logo=google-cloud)](https://cloud.google.com/)


## Project Overview

This is a fully functional, production-grade e-commerce platform designed to simulate real-world operational challenges. Unlike typical CRUD applications, this project focuses on **data consistency**, **concurrency control**, and **system maintainability** under high-traffic scenarios.

The system features a complete shopping lifecycle: product browsing, cart management, secure checkout, shipping tracking, inventory management, and a customer support ticketing system.

**Core Philosophy:**
To build a backend system capable of handling real business logic, ensuring transaction integrity, and minimizing technical debt through clean architecture.

---

## Architecture & Design Patterns

The system is built on **Django**, utilizing a **multi-app architecture** to separate business concerns. 

### The Service Layer Pattern
To avoid "Fat Models" or "Logic-Heavy Views," I implemented a distinct **Service Layer**.
* **Decoupling:** Business logic is isolated from the HTTP request/response cycle.
* **Maintainability:** Complex flows (like checkout) are easier to test and modify without affecting the API interface.

### Key Modules
* **Store:** Optimized search engine and automated slug generation.
* **Payment:** Centralized payment processing (PayPal) with strict error handling.
* **Shipping:** Integration with **Shippo** for label generation and tracking simulation.
* **Inventory:** Atomic inventory adjustments with audit logging.
* **Support:** Event-driven notification system and independent ticketing models.

---

## Key Design Decisions (Engineering Highlights)

### 1. Search Performance Optimization: 2.6s to 30ms
**The Challenge:**
As the dataset grew to millions of records, standard Django ORM queries (`icontains`) resulted in Full Table Scans, causing unacceptable latency (~2.6 seconds).

**The Solution:**
I implemented a hybrid indexing strategy at the database level:
* **B-tree Index:** For filtering by category, price, and prefix matching.
* **GIN Trigram Index (`pg_trgm`):** Specifically for fuzzy searching (`ILIKE %keyword%`).

**The Result:**
Query time dropped to approx. **30ms**, achieving an **80x performance improvement** and ensuring a smooth user experience.

### 2. Explicit Flow Control in CheckoutService
**The Trade-off:**
While Django Signals offer an "automatic" way to trigger actions, they can lead to implicit, hard-to-debug logic chains.

**The Decision:**
I chose an **Explicit Service Layer** approach for the checkout process. The `CheckoutService` acts as an orchestrator, handling Validation -> Payment -> Inventory Reservation -> Notification strictly in order. This improves readability and reduces the risk of race conditions in critical financial flows.

### 3. Payment Integrity & Webhooks as Source of Truth
Instead of relying on frontend confirmations, the system treats **PayPal Webhooks** as the single source of truth.
* **Security:** All webhooks are verified using cryptographic signatures to prevent spoofing.
* **State Management:** Strict mapping of `event_type` ensures the local order status (Paid, Failed, Refunded) always matches the payment gateway.

### 4. Concurrency Control & Idempotency
**Inventory Management:**
* **Atomicity:** All inventory changes occur within `atomic` database transactions to prevent race conditions during high-concurrency sales.
* **Idempotency:** The event handler checks the current order state before processing updates. This ensures that even if a Webhook is delivered multiple times (a common occurrence), inventory is never deducted twice.

### 5. Event-Driven Notifications
To decouple the notification logic (emailing) from the core transaction loop:
* **`transaction.on_commit`:** Emails are only triggered *after* the database transaction successfully commits. This prevents the "Phantom Email" scenario where a user receives a confirmation for a failed order.
* **Third-Party Integration:** Uses **SendGrid** via a dedicated Email Service.

---

## Security & Risk Mitigation

* **Bot Protection:** Integrated **Cloudflare Turnstile** on Login/Register pages to block automated attacks.
* **Rate Limiting:** Implemented failure counting on the checkout flow to lock out users after repeated failed attempts (Brute-force protection).
* **Account Verification:** Mandatory email verification to prevent spam accounts.

---

## Tech Stack & Deployment

### Backend Core
* **Framework:** Django 5.x, Python 3.10+
* **Database:** PostgreSQL (Cloud SQL)
* **Async Tasks:** Celery + Redis (Task Queue)

### Infrastructure (GCP)
* **Compute:** Google Compute Engine (VM) running Gunicorn & Nginx.
* **Storage:** Google Cloud Storage for media assets.
* **Proxy:** Nginx (Reverse Proxy, Static Files, HTTPS).

### Third-Party Services
* **Payment:** PayPal API
* **Logistics:** Shippo API
* **Email:** SendGrid

---

## Getting Started

**Live Demo:** [https://buyriastore.com](https://buyriastore.com)

*Note: This project is designed as a portfolio showcase rather than a quick-start template.*

**Local Development Prerequisites:**
* Python 3.10+
* PostgreSQL & Redis
* Configuration of `.env` file (API Keys for PayPal, Shippo, SendGrid, etc.)

---

## Contact

I am open to discussing the architecture, code quality, or backend challenges solved in this project. I can provide **Admin Access** upon request for a deeper review of the management dashboard and data structures.

* **Email:** a02839164@gmail.com