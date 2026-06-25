import json
import logging
import time
from datetime import datetime

import psycopg2
import psycopg2.extras
import redis
from kafka import KafkaConsumer, KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

from config import DATABASE_URL, KAFKA_BOOTSTRAP_SERVERS, REDIS_HOST, REDIS_PORT, TICKERS

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)


def ensure_alert_topic():
    admin = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    try:
        admin.create_topics([
            NewTopic(name="alert.triggered", num_partitions=3, replication_factor=1)
        ])
        log.info("Created topic: alert.triggered")
    except TopicAlreadyExistsError:
        log.info("Topic alert.triggered already exists.")
    finally:
        admin.close()


def threshold_crossed(alert, current_price):
    threshold = float(alert["threshold_price"])
    if alert["direction"] == "above" and current_price >= threshold:
        return True
    if alert["direction"] == "below" and current_price <= threshold:
        return True
    return False


def main():
    log.info("Waiting for Kafka to be ready...")
    time.sleep(5)

    ensure_alert_topic()

    # ── Kafka consumer: listen to all ticker topics ───────────────────────────
    topics = [f"stock.prices.{t}" for t in TICKERS]
    consumer = KafkaConsumer(
        *topics,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="price-monitor-group",
        auto_offset_reset="latest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    # ── Kafka producer: publish triggered alerts ──────────────────────────────
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    # ── Redis client ──────────────────────────────────────────────────────────
    cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    # ── PostgreSQL connection ─────────────────────────────────────────────────
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True

    log.info(f"Price monitor running. Topics: {topics}")

    for message in consumer:
        data    = message.value
        ticker  = data["ticker"]
        price   = float(data["price"])

        # 1. Cache latest price in Redis
        cache.set(f"price:{ticker}", price)
        log.info(f"[{ticker}]  ${price:.2f}  →  Redis updated")

        # 2. Fetch all active alerts for this ticker
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM alerts WHERE ticker = %s AND is_active = TRUE",
                (ticker,),
            )
            alerts = cur.fetchall()

        # 3. Check each alert against current price
        for alert in alerts:
            if not threshold_crossed(alert, price):
                continue

            # Build the event notification-service will consume
            event = {
                "alert_id":        alert["id"],
                "user_phone":      alert["user_phone"],
                "ticker":          ticker,
                "current_price":   price,
                "threshold_price": float(alert["threshold_price"]),
                "direction":       alert["direction"],
                "triggered_at":    datetime.utcnow().isoformat(),
            }

            # Publish to alert.triggered
            producer.send("alert.triggered", value=event)
            producer.flush()
            log.info(
                f"ALERT TRIGGERED  →  {ticker} ${price:.2f}  "
                f"({alert['direction']} ${alert['threshold_price']})  "
                f"→  {alert['user_phone']}"
            )

            # Deactivate so the same alert doesn't fire repeatedly
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE alerts SET is_active = FALSE WHERE id = %s",
                    (alert["id"],),
                )


if __name__ == "__main__":
    main()
