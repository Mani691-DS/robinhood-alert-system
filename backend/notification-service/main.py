import logging
import os
import sys
import time

from kafka import KafkaConsumer
from twilio.rest import Client

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.schema_utils import deserialize

from config import (
    KAFKA_BOOTSTRAP_SERVERS,
    SCHEMA_REGISTRY_URL,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_WHATSAPP_FROM,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)


def to_whatsapp(phone: str) -> str:
    return phone if phone.startswith("whatsapp:") else f"whatsapp:{phone}"


def build_message(event: dict) -> str:
    timestamp = event["triggered_at"].replace("T", " ")[:19]
    return (
        f"🚨 Stock Alert Triggered!\n"
        f"Ticker: {event['ticker']}\n"
        f"Current Price: ${event['current_price']:.2f}\n"
        f"Your Alert: {event['direction']} ${event['threshold_price']:.2f}\n"
        f"Time: {timestamp}"
    )


def send_whatsapp(client: Client, to_phone: str, body: str) -> str:
    msg = client.messages.create(
        from_=TWILIO_WHATSAPP_FROM,
        to=to_whatsapp(to_phone),
        body=body,
    )
    return msg.sid


def main():
    log.info("Waiting for Kafka to be ready...")
    time.sleep(5)

    consumer = KafkaConsumer(
        "alert.triggered",
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="notification-group",
        auto_offset_reset="earliest",   # don't miss alerts fired before this service started
        value_deserializer=lambda v: deserialize(v, SCHEMA_REGISTRY_URL),
    )

    twilio = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    log.info("Notification service ready. Listening on alert.triggered...")

    for message in consumer:
        event = message.value
        log.info(f"Alert received → {event['ticker']} ${event['current_price']:.2f} ({event['direction']} ${event['threshold_price']:.2f})")

        body = build_message(event)

        try:
            sid = send_whatsapp(twilio, event["user_phone"], body)
            log.info(f"WhatsApp sent → {event['user_phone']}  SID: {sid}")
        except Exception as e:
            log.error(f"WhatsApp failed → {e}")


if __name__ == "__main__":
    main()
