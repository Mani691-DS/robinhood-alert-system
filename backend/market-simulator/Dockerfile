FROM python:3.10-slim

WORKDIR /app/backend
COPY backend/requirements/market-simulator.txt requirements/market-simulator.txt
RUN pip install --no-cache-dir -r requirements/market-simulator.txt

COPY backend/shared/   shared/
COPY backend/schemas/  schemas/
COPY backend/market-simulator/ market-simulator/

WORKDIR /app/backend/market-simulator
CMD ["python", "main.py"]
