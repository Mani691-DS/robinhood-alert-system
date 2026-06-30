import os
from dotenv import load_dotenv

load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
SCHEMA_REGISTRY_URL     = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")
TWILIO_ACCOUNT_SID      = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN       = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM    = os.getenv("TWILIO_WHATSAPP_FROM")
