FROM python:3.10-slim

WORKDIR /app/backend
COPY backend/requirements/notification-service.txt requirements/notification-service.txt
RUN pip install --no-cache-dir -r requirements/notification-service.txt

COPY backend/shared/              shared/
COPY backend/schemas/             schemas/
COPY backend/notification-service/ notification-service/

WORKDIR /app/backend/notification-service
CMD ["python", "main.py"]
