FROM python:3.10-slim

WORKDIR /app/backend
COPY backend/requirements/price-monitor.txt requirements/price-monitor.txt
RUN pip install --no-cache-dir -r requirements/price-monitor.txt

COPY backend/shared/        shared/
COPY backend/schemas/       schemas/
COPY backend/price-monitor/ price-monitor/

WORKDIR /app/backend/price-monitor
CMD ["python", "main.py"]
