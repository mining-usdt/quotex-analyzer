from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
import json
import httpx
from typing import List, Dict, Optional
import os

app = FastAPI()

# تفعيل CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== قائمة الأزواج المتاحة في Quotex OTC =====
AVAILABLE_PAIRS = [
    {"symbol": "EURUSD_otc", "name": "EUR/USD OTC", "payout": 92},
    {"symbol": "GBPUSD_otc", "name": "GBP/USD OTC", "payout": 90},
    {"symbol": "USDJPY_otc", "name": "USD/JPY OTC", "payout": 88},
    {"symbol": "AUDUSD_otc", "name": "AUD/USD OTC", "payout": 86},
    {"symbol": "USDCAD_otc", "name": "USD/CAD OTC", "payout": 84},
    {"symbol": "USDCHF_otc", "name": "USD/CHF OTC", "payout": 82},
    {"symbol": "BTCUSD_otc", "name": "BTC/USD OTC", "payout": 78},
    {"symbol": "ETHUSD_otc", "name": "ETH/USD OTC", "payout": 76},
]

# ===== محرك التحليل الخارق =====

class UltimateAnalyzer:
    @staticmethod
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
    
    @staticmethod
    def calculate_macd(prices):
        if len(prices) < 26:
            return 0, 0, 0
        exp1 = pd.Series(prices).ewm(span=12, adjust=False).mean()
        exp2 = pd.Series(prices).ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        hist = macd - signal
        return float(macd.iloc[-1]), float(signal.iloc[-1]), float(hist.iloc[-1])
    
    @staticmethod
    def calculate_bollinger(prices, period=20, std_dev=2):
        if len(prices) < period:
            return None, None, None
        sma = pd.Series(prices).rolling(window=period).mean()
        std = pd.Series(prices).rolling(window=period).std()
        upper = sma + std * std_dev
        lower = sma - std * std_dev
        return float(upper.iloc[-1]), float(sma.iloc[-1]), float(lower.iloc[-1])
    
    @staticmethod
    def calculate_stochastic(highs, lows, closes):
        if len(closes) < 14:
            return 50, 50
        low_min = pd.Series(lows).rolling(window=14).min()
        high_max = pd.Series(highs).rolling(window=14).max()
        stoch_k = 100 * ((pd.Series(closes) - low_min) / (high_max - low_min))
        stoch_d = stoch_k.rolling(window=3).mean()
        return float(stoch_k.iloc[-1]), float(stoch_d.iloc[-1])
    
    @staticmethod
    def detect_pattern(opens, highs, lows, closes):
        if len(closes) < 3:
            return "NONE", 0
        
        body1 = abs(closes[-2] - opens[-2])
        body2 = abs(closes[-1] - opens[-1])
        
        # Bullish Engulfing
        if (closes[-1] > opens[-1] and closes[-2] < opens[-2] and
            closes[-1] > opens[-2] and opens[-1] < closes[-2]):
            return "BULLISH_ENGULFING", 85
        
        # Bearish Engulfing
        if (closes[-1] < opens[-1] and closes[-2] > opens[-2] and
            opens[-1] > closes[-2] and closes[-1] < opens[-2]):
            return "BEARISH_ENGULFING", 85
        
        # Hammer
        body = abs(closes[-1] - opens[-1])
        lower_shadow = min(opens[-1], closes[-1]) - lows[-1]
        upper_shadow = highs[-1] - max(opens[-1], closes[-1])
        
        if lower_shadow > 2 * body and upper_shadow < body * 0.3:
            if closes[-1] > opens[-1]:
                return "HAMMER", 80
            else:
                return "HANGING_MAN", 80
        
        # Doji
        if abs(closes[-1] - opens[-1]) < (closes[-1] * 0.001):
            return "DOJI", 60
        
        return "NONE", 0
    
    @staticmethod
    def find_support_resistance(highs, lows, closes):
        if len(closes) < 20:
            return float(min(lows[-10:])), float(max(highs[-10:]))
        support = float(min(lows[-20:]))
        resistance = float(max(highs[-20:]))
        return support, resistance
    
    @staticmethod
    def detect_breakout(price, support, resistance, upper_bb, lower_bb):
        if price > resistance:
            return "RESISTANCE_BREAKOUT", 90
        elif price < support:
            return "SUPPORT_BREAKOUT", 90
        elif upper_bb and price > upper_bb:
            return "BB_UPPER_BREAKOUT", 75
        elif lower_bb and price < lower_bb:
            return "BB_LOWER_BREAKOUT", 75
        return "NONE", 0
    
    @staticmethod
    def detect_bounce(price, support, resistance, rsi):
        if support and price <= support * 1.005 and rsi < 40:
            return "SUPPORT_BOUNCE", 85
        elif resistance and price >= resistance * 0.995 and rsi > 60:
            return "RESISTANCE_BOUNCE", 85
        return "NONE", 0
    
    @staticmethod
    def analyze_candles(candles):
        if len(candles) < 30:
            return None
        
        df = pd.DataFrame(candles)
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        opens = df['open'].values
        
        # حساب المؤشرات
        rsi = UltimateAnalyzer.calculate_rsi(closes)
        macd, macd_signal, macd_hist = UltimateAnalyzer.calculate_macd(closes)
        upper_bb, middle_bb, lower_bb = UltimateAnalyzer.calculate_bollinger(closes)
        stoch_k, stoch_d = UltimateAnalyzer.calculate_stochastic(highs, lows, closes)
        pattern, pattern_score = UltimateAnalyzer.detect_pattern(opens, highs, lows, closes)
        support, resistance = UltimateAnalyzer.find_support_resistance(highs, lows, closes)
        breakout, breakout_score = UltimateAnalyzer.detect_breakout(closes[-1], support, resistance, upper_bb, lower_bb)
        bounce, bounce_score = UltimateAnalyzer.detect_bounce(closes[-1], support, resistance, rsi)
        
        # نظام التسجيل المتقدم
        score = 0
        signals = []
        
        # 1. RSI
        if rsi < 30:
            score += 20
            signals.append({"name": "RSI Oversold", "type": "BUY", "score": 20})
        elif rsi > 70:
            score -= 20
            signals.append({"name": "RSI Overbought", "type": "SELL", "score": 20})
        
        # 2. MACD
        if macd_hist > 0 and macd > macd_signal:
            score += 15
            signals.append({"name": "MACD Bullish", "type": "BUY", "score": 15})
        elif macd_hist < 0 and macd < macd_signal:
            score -= 15
            signals.append({"name": "MACD Bearish", "type": "SELL", "score": 15})
        
        # 3. Bollinger Bands
        if lower_bb and closes[-1] <= lower_bb * 1.005:
            score += 10
            signals.append({"name": "BB Oversold", "type": "BUY", "score": 10})
        elif upper_bb and closes[-1] >= upper_bb * 0.995:
            score -= 10
            signals.append({"name": "BB Overbought", "type": "SELL", "score": 10})
        
        # 4. Stochastic
        if stoch_k < 20 and stoch_d < 20 and stoch_k > stoch_d:
            score += 10
            signals.append({"name": "Stoch Oversold", "type": "BUY", "score": 10})
        elif stoch_k > 80 and stoch_d > 80 and stoch_k < stoch_d:
            score -= 10
            signals.append({"name": "Stoch Overbought", "type": "SELL", "score": 10})
        
        # 5. الأنماط
        if pattern == "BULLISH_ENGULFING" or pattern == "HAMMER":
            score += pattern_score
            signals.append({"name": pattern, "type": "BUY", "score": pattern_score})
        elif pattern == "BEARISH_ENGULFING" or pattern == "HANGING_MAN":
            score -= pattern_score
            signals.append({"name": pattern, "type": "SELL", "score": pattern_score})
        
        # 6. الاختراقات
        if breakout != "NONE":
            if "RESISTANCE" in breakout or "BB_UPPER" in breakout:
                score -= breakout_score
                signals.append({"name": breakout, "type": "SELL", "score": breakout_score})
            else:
                score += breakout_score
                signals.append({"name": breakout, "type": "BUY", "score": breakout_score})
        
        # 7. الارتدادات
        if bounce != "NONE":
            if "RESISTANCE" in bounce:
                score -= bounce_score
                signals.append({"name": bounce, "type": "SELL", "score": bounce_score})
            else:
                score += bounce_score
                signals.append({"name": bounce, "type": "BUY", "score": bounce_score})
        
        # 8. الاتجاه (EMA 9 & 21)
        if len(closes) > 21:
            ema9 = float(pd.Series(closes).ewm(span=9, adjust=False).mean().iloc[-1])
            ema21 = float(pd.Series(closes).ewm(span=21, adjust=False).mean().iloc[-1])
            if ema9 > ema21 and closes[-1] > ema9:
                score += 10
                signals.append({"name": "Uptrend", "type": "BUY", "score": 10})
            elif ema9 < ema21 and closes[-1] < ema9:
                score -= 10
                signals.append({"name": "Downtrend", "type": "SELL", "score": 10})
        
        # القرار النهائي
        action = "NEUTRAL"
        confidence = 0
        
        if score >= 50:
            action = "STRONG_BUY"
            confidence = min(99, 70 + abs(score) // 2)
        elif score >= 30:
            action = "BUY"
            confidence = min(95, 55 + abs(score) // 2)
        elif score <= -50:
            action = "STRONG_SELL"
            confidence = min(99, 70 + abs(score) // 2)
        elif score <= -30:
            action = "SELL"
            confidence = min(95, 55 + abs(score) // 2)
        
        # حساب الوقت المتبقي من الشمعة
        now = datetime.now()
        seconds_to_next_minute = 60 - now.second
        minutes_remaining = seconds_to_next_minute / 60
        
        # حساب الأهداف (Stop Loss / Take Profit)
        atr = abs(highs[-1] - lows[-1])
        if atr == 0 and len(highs) > 1:
            atr = abs(highs[-1] - lows[-1]) if abs(highs[-1] - lows[-1]) > 0 else 0.001
        
        return {
            "action": action,
            "confidence": confidence,
            "score": score,
            "signals": signals,
            "rsi": float(rsi),
            "macd": {
                "macd": float(macd),
                "signal": float(macd_signal),
                "histogram": float(macd_hist)
            },
            "bollinger": {
                "upper": float(upper_bb) if upper_bb else None,
                "middle": float(middle_bb) if middle_bb else None,
                "lower": float(lower_bb) if lower_bb else None
            },
            "stochastic": {"k": float(stoch_k), "d": float(stoch_d)},
            "pattern": {"name": pattern, "score": pattern_score},
            "support_resistance": {"support": float(support), "resistance": float(resistance)},
            "breakout": {"name": breakout, "score": breakout_score},
            "bounce": {"name": bounce, "score": bounce_score},
            "time_remaining_minutes": round(minutes_remaining, 2),
            "current_price": float(closes[-1]),
            "atr": float(atr),
            "suggestion": self.get_suggestion(action, confidence, support, resistance, closes[-1]),
            "timestamp": now.isoformat()
        }
    
    @staticmethod
    def get_suggestion(action, confidence, support, resistance, price):
        if action == "STRONG_BUY" or action == "BUY":
            entry = price
            take_profit = resistance if resistance > price else price * 1.0015
            stop_loss = support if support < price else price * 0.9985
            risk_reward = abs((take_profit - entry) / (entry - stop_loss)) if (entry - stop_loss) != 0 else 0
            return {
                "direction": "شراء (BUY)",
                "entry": round(entry, 5),
                "take_profit": round(take_profit, 5),
                "stop_loss": round(stop_loss, 5),
                "risk_reward": round(risk_reward, 2)
            }
        elif action == "STRONG_SELL" or action == "SELL":
            entry = price
            take_profit = support if support < price else price * 0.9985
            stop_loss = resistance if resistance > price else price * 1.0015
            risk_reward = abs((entry - take_profit) / (stop_loss - entry)) if (stop_loss - entry) != 0 else 0
            return {
                "direction": "بيع (SELL)",
                "entry": round(entry, 5),
                "take_profit": round(take_profit, 5),
                "stop_loss": round(stop_loss, 5),
                "risk_reward": round(risk_reward, 2)
            }
        else:
            return {
                "direction": "انتظار (NEUTRAL)",
                "entry": round(price, 5),
                "take_profit": None,
                "stop_loss": None,
                "risk_reward": 0
            }

# ===== نقاط النهاية API =====

@app.get("/api/v1/markets")
async def get_markets():
    """الحصول على قائمة الأزواج المتاحة"""
    return {
        "status": "success",
        "total_assets": len(AVAILABLE_PAIRS),
        "data": AVAILABLE_PAIRS
    }

@app.get("/api/v1/candles")
async def get_candles(
    symbol: str = Query(..., description="رمز الأصل"),
    limit: int = Query(100, ge=10, le=500)
):
    """محاكاة شموع (لتجربة النظام بدون اتصال حقيقي)"""
    # هذه شموع محاكاة للتجربة
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
    elif "AUD" in symbol:
        base_price = 0.6500
    elif "CAD" in symbol:
        base_price = 1.3500
    elif "CHF" in symbol:
        base_price = 0.8800
    
    candles = []
    current_time = datetime.now().replace(second=0, microsecond=0)
    
    for i in range(limit):
        # توليد حركة سعرية عشوائية لكن مع اتجاه
        trend = np.sin(i / 20) * 0.002
        noise = np.random.normal(0, 0.0008)
        change = trend + noise
        
        open_price = base_price
        close_price = open_price + change
        high_price = max(open_price, close_price) + abs(np.random.normal(0, 0.0003))
        low_price = min(open_price, close_price) - abs(np.random.normal(0, 0.0003))
        
        candles.append({
            "time": (current_time - pd.Timedelta(minutes=limit - i)).isoformat(),
            "open": round(open_price, 5),
            "high": round(high_price, 5),
            "low": round(low_price, 5),
            "close": round(close_price, 5),
            "volume": np.random.randint(10, 100),
            "payout": 92
        })
        
        base_price = close_price
    
    return {
        "symbol": symbol,
        "timeframe": "1m",
        "timezone": "UTC",
        "candle_count": len(candles),
        "candles": candles
    }

@app.get("/api/v2/analyze/{symbol}")
async def analyze_symbol(symbol: str, limit: int = Query(100, ge=10, le=500)):
    """تحليل متقدم لزوج معين"""
    try:
        # التحقق من وجود الزوج
        if symbol not in [p["symbol"] for p in AVAILABLE_PAIRS]:
            raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found")
        
        # جلب الشموع
        candles_response = await get_candles(symbol, limit)
        candles = candles_response.get("candles", [])
        
        if len(candles) < 30:
            raise HTTPException(status_code=400, detail="Insufficient data (need at least 30 candles)")
        
        # التحليل
        result = UltimateAnalyzer.analyze_candles(candles)
        if not result:
            raise HTTPException(status_code=400, detail="Analysis failed")
        
        # إضافة معلومات الزوج
        pair_info = next((p for p in AVAILABLE_PAIRS if p["symbol"] == symbol), None)
        result["symbol"] = symbol
        result["pair_name"] = pair_info["name"] if pair_info else symbol
        result["payout"] = pair_info["payout"] if pair_info else 92
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

@app.get("/api/v2/strong-signal")
async def get_strong_signal():
    """البحث عن إشارة قوية في جميع الأزواج"""
    strong_signals = []
    
    for pair in AVAILABLE_PAIRS:
        try:
            result = await analyze_symbol(pair["symbol"], 100)
            if result and (result["action"] == "STRONG_BUY" or result["action"] == "STRONG_SELL"):
                strong_signals.append(result)
        except:
            continue
    
    # ترتيب حسب الثقة
    strong_signals.sort(key=lambda x: x["confidence"], reverse=True)
    
    return {
        "status": "success",
        "count": len(strong_signals),
        "signals": strong_signals
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "ULTIMATE v5.0"
    }