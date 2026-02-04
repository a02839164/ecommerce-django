# --- 第一階段：Builder (編譯專用) ---
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 1. 補上 libpq-dev，這是編譯 psycopg2 的關鍵
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --user --no-cache-dir -r requirements.txt


# --- 第二階段：Final (運行環境) ---
FROM python:3.13-slim AS final

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Taipei

WORKDIR /code

# 2. 安裝 libpq5 (運行必備) 與 postgresql-client (備份腳本必備)
RUN apt-get update && apt-get install -y \
    libpq5 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 從 builder 拷貝編譯好的套件
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 拷貝程式碼與腳本
COPY . /code/
RUN chmod +x /code/local_backup.sh /code/local_restore.sh /code/run_web.sh