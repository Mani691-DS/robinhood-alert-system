import json
import os
import random
import sys
import time
from datetime import datetime

from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.schema_utils import register_schema, serialize

from config import KAFKA_BOOTSTRAP_SERVERS, SCHEMA_REGISTRY_URL, TICKERS

STOCK_PRICE_SCHEMA = json.load(
    open(os.path.join(os.path.dirname(__file__), '..', 'schemas', 'stock_price.avsc'))
)

BASE_PRICES = {
    "AAPL":  180.00,
    "GOOGL": 140.00,
    "TSLA":  250.00,
    "MSFT":  380.00,
    "AMZN":  185.00,
}


def ensure_topics():
    admin = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    topics = [
        NewTopic(name=f"stock.prices.{t}", num_partitions=1, replication_factor=1)
        for t in TICKERS
    ]
    try:
        admin.create_topics(topics)
        print(f"Created topics: {[t.name for t in topics]}")
    except TopicAlreadyExistsError:
        print("Topics already exist, skipping creation.")
    finally:
        admin.close()


def simulate(producer):
    prices = {t: BASE_PRICES.get(t, 100.00) for t in TICKERS}

    print(f"Streaming prices for: {TICKERS}  (Ctrl+C to stop)\n")

    while True:
        for ticker in TICKERS:
            change         = random.uniform(-0.005, 0.005)   # ±0.5% per tick
            prices[ticker] = round(prices[ticker] * (1 + change), 2)

            message = {
                "ticker":    ticker,
                "price":     prices[ticker],
                "timestamp": datetime.utcnow().isoformat(),
            }

            producer.send(
                topic=f"stock.prices.{ticker}",
                key=ticker.encode(),
                value=message,
            )
            print(f"  {ticker:<6} ${prices[ticker]:.2f}")

        producer.flush()
        print()
        time.sleep(1)


if __name__ == "__main__":
    ensure_topics()

    # Register schema once at startup — returns schema ID used in every message
    schema_id = register_schema(
        SCHEMA_REGISTRY_URL,
        subject="stock.prices-value",
        schema=STOCK_PRICE_SCHEMA,
    )
    print(f"Schema registered. ID: {schema_id}")

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: serialize(v, STOCK_PRICE_SCHEMA, schema_id),
    )

    try:
        simulate(producer)
    except KeyboardInterrupt:
        print("\nStopping market simulator.")
    finally:
        producer.close()
