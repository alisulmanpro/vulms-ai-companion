FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# 1. System Dependencies & Official Node.js Setup
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssl \
    ca-certificates \
    libatomic1 \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. Python Packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Playwright OS Dependencies & Chromium Browser
RUN playwright install-deps chromium && playwright install chromium

# 4. Prisma Setup
COPY prisma ./prisma
RUN python -m prisma generate

# 5. Source Code Copy
COPY . .

EXPOSE 8000

# 6. Entrypoint
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"]