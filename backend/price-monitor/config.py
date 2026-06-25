import os
from dotenv import load_dotenv

load_dotenv()

# Strip +asyncpg driver so psycopg2 can use the same URL
DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
REDIS_HOST               = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT               = int(os.getenv("REDIS_PORT", 6379))
TICKERS                  = os.getenv("TICKERS", "AAPL,GOOGL,TSLA,MSFT,AMZN").split(",")
