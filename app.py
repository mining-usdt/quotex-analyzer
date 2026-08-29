from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import random
import pandas as pd
import numpy as np
import math
from typing import Dict, List, Optional, Tuple

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== قائمة الأزواج =====
AVAILABLE_PAIRS = [
    {"symbol": "EURUSD_otc", "name": "EUR/USD", "payout": 92, "base": 1.0900},
    {"symbol": "GBPUSD_otc", "name": "GBP/USD", "payout": 90, "base": 1.2600},
    {"symbol": "USDJPY_otc", "name": "USD/JPY", "payout": 88, "base": 150.00},
    {"symbol": "AUDUSD_otc", "name": "AUD/USD", "payout": 86, "base": 0.6500},
    {"symbol": "USDCAD_otc", "name": "USD/CAD", "payout": 84, "base": 1.3500},
    {"symbol": "USDCHF_otc", "name": "USD/CHF", "payout": 82, "base": 0.8800},
    {"symbol": "BTCUSD_otc", "name": "BTC/USD", "payout": 78, "base": 65000},
    {"symbol": "ETHUSD_otc", "name": "ETH/USD", "payout": 76, "base": 3500},
]

# ===== توليد شموع محاكاة متطورة =====
def generate_advanced_candles(symbol: str, limit: int = 200) -> List[Dict]:
    """توليد شموع بمحاكاة حركة السوق الحقيقية"""
    np.random.seed(int(datetime.now().timestamp()) % 10000 + hash(symbol) % 1000)
    
    pair = next((p for p in AVAILABLE_PAIRS if p["symbol"] == symbol), AVAILABLE_PAIRS[0])
    base_price = pair["base"]
    
    # توليد اتجاه عشوائي
    trend_direction = random.choice([-1, 1])
    trend_strength = random.uniform(0.0002, 0.002)
    
    candles = []
    current_price = base_price
    volatility = random.uniform(0.0003, 0.001)
    
    for i in range(limit):
        # موجة سعرية
        wave = np.sin(i / random.randint(8, 20)) * random.uniform(0.001, 0.005)
        trend = trend_direction * trend_strength * (i / limit)
        noise = np.random.normal(0, volatility)
        
        change = wave + trend + noise
        open_price = current_price
        close_price = open_price + change
        high_price = max(open_price, close_price) + abs(np.random.normal(0, volatility * 0.5))
        low_price = min(open_price, close_price) - abs(np.random.normal(0, volatility * 0.5))
        
        candles.append({
            "open": round(open_price, 5),
            "high": round(high_price, 5),
            "low": round(low_price, 5),
            "close": round(close_price, 5),
            "volume": random.randint(10, 100)
        })
        current_price = close_price
    
    return candles

# ===== المؤشرات الفنية المتقدمة =====

class AdvancedIndicators:
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50.0
        delta = np.diff(prices)
        gain = (delta > 0) * delta
        loss = (delta < 0) * -delta
        avg_gain = pd.Series(gain).rolling(window=period).mean()
        avg_loss = pd.Series(loss).rolling(window=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1]) if not rsi.empty else 50.0

    @staticmethod
    def calculate_macd(prices: List[float]) -> Dict:
        if len(prices) < 26:
            return {"macd": 0, "signal": 0, "histogram": 0}
        exp1 = pd.Series(prices).ewm(span=12, adjust=False).mean()
        exp2 = pd.Series(prices).ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        hist = macd - signal
        return {
            "macd": float(macd.iloc[-1]),
            "signal": float(signal.iloc[-1]),
            "histogram": float(hist.iloc[-1])
        }

    @staticmethod
    def calculate_bollinger(prices: List[float], period: int = 20) -> Dict:
        if len(prices) < period:
            return {"upper": None, "middle": None, "lower": None}
        sma = pd.Series(prices).rolling(window=period).mean()
        std = pd.Series(prices).rolling(window=period).std()
        return {
            "upper": float((sma + std * 2).iloc[-1]),
            "middle": float(sma.iloc[-1]),
            "lower": float((sma - std * 2).iloc[-1])
        }

    @staticmethod
    def calculate_stochastic(highs: List[float], lows: List[float], closes: List[float]) -> Dict:
        if len(closes) < 14:
            return {"k": 50, "d": 50}
        low_min = pd.Series(lows).rolling(window=14).min()
        high_max = pd.Series(highs).rolling(window=14).max()
        stoch_k = 100 * ((pd.Series(closes) - low_min) / (high_max - low_min))
        stoch_d = stoch_k.rolling(window=3).mean()
        return {"k": float(stoch_k.iloc[-1]), "d": float(stoch_d.iloc[-1])}

    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        if len(prices) < period:
            return prices[-1] if prices else 0
        return float(pd.Series(prices).ewm(span=period, adjust=False).mean().iloc[-1])

    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> float:
        if len(prices) < period:
            return prices[-1] if prices else 0
        return float(pd.Series(prices).rolling(window=period).mean().iloc[-1])

    @staticmethod
    def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        if len(closes) < period + 1:
            return 0.001
        tr1 = np.array(highs[1:]) - np.array(lows[1:])
        tr2 = abs(np.array(highs[1:]) - np.array(closes[:-1]))
        tr3 = abs(np.array(lows[1:]) - np.array(closes[:-1]))
        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        return float(pd.Series(tr).rolling(window=period).mean().iloc[-1])

    @staticmethod
    def calculate_support_resistance(prices: List[float], period: int = 20) -> Dict:
        if len(prices) < period:
            return {"support": min(prices), "resistance": max(prices)}
        recent = prices[-period:]
        return {
            "support": float(min(recent)),
            "resistance": float(max(recent))
        }

    @staticmethod
    def calculate_ichimoku(highs: List[float], lows: List[float], closes: List[float]) -> Dict:
        if len(closes) < 52:
            return {"tenkan": 0, "kijun": 0, "senkou_a": 0, "senkou_b": 0}
        tenkan = (max(highs[-9:]) + min(lows[-9:])) / 2
        kijun = (max(highs[-26:]) + min(lows[-26:])) / 2
        senkou_a = (tenkan + kijun) / 2
        senkou_b = (max(highs[-52:]) + min(lows[-52:])) / 2
        return {
            "tenkan": float(tenkan),
            "kijun": float(kijun),
            "senkou_a": float(senkou_a),
            "senkou_b": float(senkou_b)
        }

    @staticmethod
    def calculate_fibonacci(highs: List[float], lows: List[float]) -> Dict:
        if len(highs) < 20:
            return {"0": 0, "236": 0, "382": 0, "500": 0, "618": 0, "786": 0, "100": 0}
        high = max(highs[-20:])
        low = min(lows[-20:])
        diff = high - low
        return {
            "0": float(high),
            "236": float(high - diff * 0.236),
            "382": float(high - diff * 0.382),
            "500": float(high - diff * 0.5),
            "618": float(high - diff * 0.618),
            "786": float(high - diff * 0.786),
            "100": float(low)
        }

# ===== استراتيجيات التحليل =====

class TradingStrategies:
    @staticmethod
    def analyze_all(candles: List[Dict]) -> Dict:
        if len(candles) < 50:
            return {"error": "Insufficient data"}
        
        df = pd.DataFrame(candles)
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        opens = df['open'].values
        volumes = df['volume'].values
        
        current_price = closes[-1]
        
        # ===== حساب جميع المؤشرات =====
        rsi = AdvancedIndicators.calculate_rsi(closes)
        macd = AdvancedIndicators.calculate_macd(closes)
        bollinger = AdvancedIndicators.calculate_bollinger(closes)
        stoch = AdvancedIndicators.calculate_stochastic(highs, lows, closes)
        ema9 = AdvancedIndicators.calculate_ema(closes, 9)
        ema21 = AdvancedIndicators.calculate_ema(closes, 21)
        ema50 = AdvancedIndicators.calculate_ema(closes, 50)
        sma20 = AdvancedIndicators.calculate_sma(closes, 20)
        atr = AdvancedIndicators.calculate_atr(highs, lows, closes)
        sr = AdvancedIndicators.calculate_support_resistance(closes)
        ichimoku = AdvancedIndicators.calculate_ichimoku(highs, lows, closes)
        fibonacci = AdvancedIndicators.calculate_fibonacci(highs, lows)
        
        # ===== 1. استراتيجية RSI =====
        rsi_signal = "NEUTRAL"
        rsi_score = 0
        if rsi < 25:
            rsi_signal = "STRONG_BUY"
            rsi_score = 25
        elif rsi < 35:
            rsi_signal = "BUY"
            rsi_score = 15
        elif rsi > 75:
            rsi_signal = "STRONG_SELL"
            rsi_score = -25
        elif rsi > 65:
            rsi_signal = "SELL"
            rsi_score = -15
        
        # ===== 2. استراتيجية MACD =====
        macd_signal = "NEUTRAL"
        macd_score = 0
        if macd["histogram"] > 0 and macd["macd"] > macd["signal"]:
            macd_signal = "BUY"
            macd_score = 15
        elif macd["histogram"] < 0 and macd["macd"] < macd["signal"]:
            macd_signal = "SELL"
            macd_score = -15
        
        # ===== 3. استراتيجية بولينجر =====
        bb_signal = "NEUTRAL"
        bb_score = 0
        if bollinger["lower"] and current_price <= bollinger["lower"] * 1.002:
            bb_signal = "BUY"
            bb_score = 12
        elif bollinger["upper"] and current_price >= bollinger["upper"] * 0.998:
            bb_signal = "SELL"
            bb_score = -12
        
        # ===== 4. استراتيجية ستوكاستيك =====
        stoch_signal = "NEUTRAL"
        stoch_score = 0
        if stoch["k"] < 20 and stoch["d"] < 20 and stoch["k"] > stoch["d"]:
            stoch_signal = "BUY"
            stoch_score = 10
        elif stoch["k"] > 80 and stoch["d"] > 80 and stoch["k"] < stoch["d"]:
            stoch_signal = "SELL"
            stoch_score = -10
        
        # ===== 5. استراتيجية الاتجاه (EMA) =====
        trend_signal = "NEUTRAL"
        trend_score = 0
        if ema9 > ema21 and ema21 > ema50 and current_price > ema9:
            trend_signal = "STRONG_BUY"
            trend_score = 20
        elif ema9 > ema21 and current_price > ema9:
            trend_signal = "BUY"
            trend_score = 10
        elif ema9 < ema21 and ema21 < ema50 and current_price < ema9:
            trend_signal = "STRONG_SELL"
            trend_score = -20
        elif ema9 < ema21 and current_price < ema9:
            trend_signal = "SELL"
            trend_score = -10
        
        # ===== 6. استراتيجية إيشيموكو =====
        ichimoku_signal = "NEUTRAL"
        ichimoku_score = 0
        if ichimoku["senkou_a"] > ichimoku["senkou_b"] and current_price > ichimoku["senkou_a"]:
            ichimoku_signal = "BUY"
            ichimoku_score = 8
        elif ichimoku["senkou_a"] < ichimoku["senkou_b"] and current_price < ichimoku["senkou_a"]:
            ichimoku_signal = "SELL"
            ichimoku_score = -8
        
        # ===== 7. استراتيجية فيبوناتشي =====
        fib_signal = "NEUTRAL"
        fib_score = 0
        if current_price <= fibonacci["618"] * 1.002:
            fib_signal = "BUY"
            fib_score = 10
        elif current_price >= fibonacci["382"] * 0.998:
            fib_signal = "SELL"
            fib_score = -10
        
        # ===== 8. استراتيجية الدعم والمقاومة =====
        sr_signal = "NEUTRAL"
        sr_score = 0
        if current_price <= sr["support"] * 1.003:
            sr_signal = "BUY"
            sr_score = 12
        elif current_price >= sr["resistance"] * 0.997:
            sr_signal = "SELL"
            sr_score = -12
        
        # ===== 9. استراتيجية التقلب (ATR) =====
        volatility = "LOW"
        if atr > 0.002:
            volatility = "HIGH"
        elif atr > 0.001:
            volatility = "MEDIUM"
        
        # ===== 10. استراتيجية الحجم =====
        volume_signal = "NEUTRAL"
        volume_score = 0
        avg_volume = np.mean(volumes[-20:])
        if volumes[-1] > avg_volume * 1.5:
            volume_score = 8 if closes[-1] > opens[-1] else -8
            volume_signal = "BUY" if closes[-1] > opens[-1] else "SELL"
        
        # ===== تجميع النتائج =====
        signals = []
        total_score = 0
        
        # تجميع جميع الإشارات
        signal_list = [
            {"name": "RSI", "signal": rsi_signal, "score": rsi_score},
            {"name": "MACD", "signal": macd_signal, "score": macd_score},
            {"name": "Bollinger", "signal": bb_signal, "score": bb_score},
            {"name": "Stochastic", "signal": stoch_signal, "score": stoch_score},
            {"name": "Trend", "signal": trend_signal, "score": trend_score},
            {"name": "Ichimoku", "signal": ichimoku_signal, "score": ichimoku_score},
            {"name": "Fibonacci", "signal": fib_signal, "score": fib_score},
            {"name": "Support/Resistance", "signal": sr_signal, "score": sr_score},
            {"name": "Volume", "signal": volume_signal, "score": volume_score}
        ]
        
        for s in signal_list:
            if s["signal"] != "NEUTRAL":
                signals.append(s)
                total_score += s["score"]
        
        # ===== القرار النهائي =====
        action = "NEUTRAL"
        confidence = 0
        
        if total_score >= 30:
            action = "STRONG_BUY"
            confidence = min(99, 70 + total_score)
        elif total_score >= 15:
            action = "BUY"
            confidence = min(95, 55 + total_score)
        elif total_score <= -30:
            action = "STRONG_SELL"
            confidence = min(99, 70 + abs(total_score))
        elif total_score <= -15:
            action = "SELL"
            confidence = min(95, 55 + abs(total_score))
        else:
            confidence = max(20, 30 + total_score)
        
        # ===== الوقت المتبقي =====
        now = datetime.now()
        seconds_to_next_minute = 60 - now.second
        minutes_remaining = round(seconds_to_next_minute / 60, 2)
        
        return {
            "action": action,
            "confidence": confidence,
            "score": total_score,
            "signals": signals,
            "current_price": float(current_price),
            "rsi": rsi,
            "macd": macd,
            "bollinger": bollinger,
            "stochastic": stoch,
            "ema9": ema9,
            "ema21": ema21,
            "ema50": ema50,
            "sma20": sma20,
            "atr": atr,
            "support_resistance": sr,
            "ichimoku": ichimoku,
            "fibonacci": fibonacci,
            "volatility": volatility,
            "time_remaining_minutes": minutes_remaining
        }

# ===== نقاط النهاية =====

@app.get("/")
async def root():
    return {"message": "🚀 Quotex OTC Analyzer ULTIMATE", "status": "online", "timestamp": datetime.now().isoformat()}

@app.get("/api/v1/markets")
async def get_markets():
    return {"status": "success", "data": AVAILABLE_PAIRS}

@app.get("/api/v2/analyze/{symbol}")
async def analyze_symbol(symbol: str, limit: int = Query(200, ge=50, le=500)):
    for pair in AVAILABLE_PAIRS:
        if pair["symbol"] == symbol:
            candles = generate_advanced_candles(symbol, limit)
            analysis = TradingStrategies.analyze_all(candles)
            if "error" in analysis:
                raise HTTPException(status_code=400, detail=analysis["error"])
            
            analysis["symbol"] = symbol
            analysis["pair_name"] = pair["name"]
            analysis["payout"] = pair["payout"]
            analysis["timestamp"] = datetime.now().isoformat()
            return analysis
    
    raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found")

@app.get("/api/v2/strong-signal")
async def get_strong_signal():
    best = None
    best_confidence = 0
    
    for pair in AVAILABLE_PAIRS:
        try:
            result = await analyze_symbol(pair["symbol"])
            if result and result["action"] in ["STRONG_BUY", "STRONG_SELL"] and result["confidence"] > best_confidence:
                best = result
                best_confidence = result["confidence"]
        except:
            continue
    
    if best:
        return {"status": "success", "signal": best}
    return {"status": "no_strong_signal", "message": "No strong signals found"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}