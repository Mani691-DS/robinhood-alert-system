FROM python:3.10-slim

# Use /app as root so ../../frontend/ in main.py resolves to /app/frontend/
WORKDIR /app
COPY backend/requirements/dashboard-service.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/dashboard-service/ backend/dashboard-service/
COPY frontend/                  frontend/

WORKDIR /app/backend/dashboard-service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
