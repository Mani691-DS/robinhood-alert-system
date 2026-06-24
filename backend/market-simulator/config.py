import os
from dotenv import load_dotenv

load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TICKERS = os.getenv("TICKERS", "AAPL,GOOGL,TSLA,MSFT,AMZN").split(",")
