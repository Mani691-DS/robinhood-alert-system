import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
TICKERS    = os.getenv("TICKERS", "AAPL,GOOGL,TSLA,MSFT,AMZN").split(",")
