from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

AVAILABLE_PAIRS = [
    {"symbol": "EURUSD_otc", "name": "EUR/USD OTC", "payout": 92},
    {"symbol": "GBPUSD_otc", "name": "GBP/USD OTC", "payout": 90},
    {"symbol": "USDJPY_otc", "name": "USD/JPY OTC", "payout": 88},
    {"symbol": "BTCUSD_otc", "name": "BTC/USD OTC", "payout": 78},
]

@app.get("/")
async def root():
    return {"message": "🚀 Quotex OTC Analyzer", "status": "online", "timestamp": datetime.now().isoformat()}

@app.get("/api/v1/markets")
async def get_markets():
    return {"status": "success", "data": AVAILABLE_PAIRS}

@app.get("/api/v2/analyze/{symbol}")
async def analyze(symbol: str):
    for pair in AVAILABLE_PAIRS:
        if pair["symbol"] == symbol:
            action = random.choice(["BUY", "SELL", "NEUTRAL"])
            confidence = random.randint(50, 95)
            return {
                "symbol": symbol,
                "pair_name": pair["name"],
                "action": action,
                "confidence": confidence,
                "payout": pair["payout"],
                "timestamp": datetime.now().isoformat()
            }
    return {"error": "Symbol not found"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}