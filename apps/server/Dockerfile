#docker run -d -p 8000:8000 --name vulms-app vulms-fastapi-server Lightweight Python image
FROM python:3.11-slim

# Working directory set
WORKDIR /app

# System dependencies and requirements installation
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# application code copy
COPY . .

# FastAPI port expose
EXPOSE 8000

# Server run command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]