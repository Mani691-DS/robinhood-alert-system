import asyncio
import json
import os
import time

import redis.asyncio as aioredis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from config import REDIS_HOST, REDIS_PORT, TICKERS

app = FastAPI(title="Dashboard Service")

FRONTEND_HTML = os.path.join(
    os.path.dirname(__file__), "..", "..", "frontend", "index.html"
)


@app.get("/")
async def index():
    with open(FRONTEND_HTML, encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/history/{ticker}")
async def price_history(ticker: str, since: int = 0):
    """Return all price ticks for a ticker since a given Unix ms timestamp.
    Used by the frontend to build historical candlestick candles on load."""
    cache = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    try:
        members = await cache.zrangebyscore(
            f"ticks:{ticker}", since, "+inf", withscores=True
        )
        return [
            {"time": int(score), "price": float(member.split(":", 1)[1])}
            for member, score in members
        ]
    finally:
        await cache.aclose()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    cache = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    try:
        while True:
            prices = {}
            for ticker in TICKERS:
                value = await cache.get(f"price:{ticker}")
                if value:
                    prices[ticker] = float(value)

            if prices:
                await websocket.send_text(json.dumps({
                    "prices": prices,
                    "ts": int(time.time() * 1000),
                }))

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass
    finally:
        await cache.aclose()
