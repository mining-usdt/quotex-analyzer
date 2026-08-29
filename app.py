from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import random
import pandas as pd
import numpy as np

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

# ===== المؤشرات الفنية الحقيقية =====

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    delta = np.diff(prices)
    gain = (delta > 0) * delta
    loss = (delta < 0) * -delta
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1]) if not rsi.empty else 50

def calculate_macd(prices):
    if len(prices) < 26:
        return 0, 0, 0
    exp1 = pd.Series(prices).ewm(span=12, adjust=False).mean()
    exp2 = pd.Series(prices).ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    return float(macd.iloc[-1]), float(signal.iloc[-1]), float(hist.iloc[-1])

def calculate_bollinger(prices, period=20, std_dev=2):
    if len(prices) < period:
        return None, None, None
    sma = pd.Series(prices).rolling(window=period).mean()
    std = pd.Series(prices).rolling(window=period).std()
    upper = sma + std * std_dev
    lower = sma - std * std_dev
    return float(upper.iloc[-1]), float(sma.iloc[-1]), float(lower.iloc[-1])

def generate_real_candles(symbol, limit=100):
    """توليد شموع محاكاة واقعية"""
    np.random.seed(int(datetime.now().timestamp()) % 10000 + hash(symbol) % 1000)
    
    base_price = 1.0900
    if "GBP" in symbol:
        base_price = 1.2600
    elif "JPY" in symbol:
        base_price = 150.00
    elif "BTC" in symbol:
        base_price = 65000
    elif "ETH" in symbol:
        base_price = 3500
    
    candles = []
    current_price = base_price
    
    for i in range(limit):
        trend = np.sin(i / 15) * 0.002
        noise = np.random.normal(0, 0.0006)
        change = trend + noise
        
        open_price = current_price
        close_price = open_price + change
        high_price = max(open_price, close_price) + abs(np.random.normal(0, 0.0003))
        low_price = min(open_price, close_price) - abs(np.random.normal(0, 0.0003))
        
        candles.append({
            "open": round(open_price, 5),
            "high": round(high_price, 5),
            "low": round(low_price, 5),
            "close": round(close_price, 5),
        })
        current_price = close_price
    
    return candles

@app.get("/")
async def root():
    return {"message": "🚀 Quotex OTC Analyzer PRO", "status": "online", "timestamp": datetime.now().isoformat()}

@app.get("/api/v1/markets")
async def get_markets():
    return {"status": "success", "data": AVAILABLE_PAIRS}

@app.get("/api/v2/analyze/{symbol}")
async def analyze_symbol(symbol: str, limit: int = 100):
    """تحليل حقيقي مع RSI, MACD, Bollinger Bands"""
    for pair in AVAILABLE_PAIRS:
        if pair["symbol"] == symbol:
            # توليد شموع
            candles = generate_real_candles(symbol, limit)
            closes = [c["close"] for c in candles]
            current_price = closes[-1]
            
            # حساب المؤشرات الحقيقية
            rsi = calculate_rsi(closes)
            macd, macd_signal, macd_hist = calculate_macd(closes)
            upper_bb, middle_bb, lower_bb = calculate_bollinger(closes)
            
            # توليد الإشارة بناءً على المؤشرات الحقيقية
            score = 0
            
            # RSI
            if rsi < 30:
                score += 20
            elif rsi > 70:
                score -= 20
            
            # MACD
            if macd_hist > 0 and macd > macd_signal:
                score += 15
            elif macd_hist < 0 and macd < macd_signal:
                score -= 15
            
            # Bollinger Bands
            if lower_bb and current_price <= lower_bb * 1.005:
                score += 10
            elif upper_bb and current_price >= upper_bb * 0.995:
                score -= 10
            
            # القرار النهائي
            if score >= 30:
                action = "STRONG_BUY"
                confidence = min(99, 70 + score)
            elif score >= 15:
                action = "BUY"
                confidence = min(95, 55 + score)
            elif score <= -30:
                action = "STRONG_SELL"
                confidence = min(99, 70 + abs(score))
            elif score <= -15:
                action = "SELL"
                confidence = min(95, 55 + abs(score))
            else:
                action = "NEUTRAL"
                confidence = 30

            # حساب الوقت المتبقي من الشمعة
            now = datetime.now()
            seconds_to_next_minute = 60 - now.second
            minutes_remaining = round(seconds_to_next_minute / 60, 2)

            return {
                "symbol": symbol,
                "pair_name": pair["name"],
                "action": action,
                "confidence": confidence,
                "score": score,
                "current_price": current_price,
                "rsi": rsi,
                "macd": {
                    "macd": macd,
                    "signal": macd_signal,
                    "histogram": macd_hist
                },
                "bollinger": {
                    "upper": upper_bb,
                    "middle": middle_bb,
                    "lower": lower_bb
                },
                "time_remaining_minutes": minutes_remaining,
                "payout": pair["payout"],
                "timestamp": datetime.now().isoformat()
            }
    
    return {"error": "Symbol not found"}

@app.get("/api/v2/strong-signal")
async def get_strong_signal():
    """البحث عن أقوى إشارة في جميع الأزواج"""
    best_signal = None
    best_confidence = 0
    
    for pair in AVAILABLE_PAIRS:
        try:
            result = await analyze_symbol(pair["symbol"])
            if result and result["action"] in ["STRONG_BUY", "STRONG_SELL"] and result["confidence"] > best_confidence:
                best_signal = result
                best_confidence = result["confidence"]
        except:
            continue
    
    if best_signal:
        return {"status": "success", "signal": best_signal}
    return {"status": "no_strong_signal", "message": "لا توجد إشارات قوية حالياً"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}