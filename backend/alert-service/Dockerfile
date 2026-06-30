FROM python:3.10-slim

WORKDIR /app/backend
COPY backend/requirements/alert-service.txt requirements/alert-service.txt
RUN pip install --no-cache-dir -r requirements/alert-service.txt

COPY backend/shared/        shared/
COPY backend/alembic/       alembic/
COPY backend/alembic.ini    alembic.ini
COPY backend/alert-service/ alert-service/

WORKDIR /app/backend/alert-service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
