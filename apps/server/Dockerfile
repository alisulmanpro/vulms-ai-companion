FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    openssl \
    ca-certificates \
    libatomic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY prisma ./prisma
RUN prisma generate

COPY . .

EXPOSE 8000

# Notice app.main:app entrypoint for uvicorn
CMD ["sh", "-c", "prisma db push --accept-data-loss && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"]