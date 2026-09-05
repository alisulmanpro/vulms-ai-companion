FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PATH="/root/.cargo/bin:/root/.local/bin:$PATH" \
    TZ=Asia/Karachi

WORKDIR /app

# 1. System Dependencies, Node.js & UV Package Manager
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssl \
    ca-certificates \
    libatomic1 \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
    && apt-get install -y tzdata

# 2. Copy dependency lockfiles and install via uv
COPY pyproject.toml uv.lock ./
RUN uv pip install --system -r pyproject.toml || uv pip install --system cachetools diskcache httpx fastapi uvicorn pydantic pydantic-settings prisma cryptography playwright apscheduler

# 3. Playwright OS Dependencies & Chromium Browser
RUN playwright install-deps chromium && playwright install chromium

# 4. Prisma Setup & Client Generation
COPY prisma ./prisma
RUN prisma generate

# 5. Copy Application Source Code
COPY . .

EXPOSE 8000

# 6. Container Entrypoint
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
