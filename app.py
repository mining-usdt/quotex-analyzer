from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
import os
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import random
import asyncio
from typing import Dict, List, Optional, Tuple, Any
import math
import time
import hashlib
import requests
from functools import lru_cache

# ===== تهيئة التطبيق =====
app = FastAPI(
    title="🔥 Quotex OTC Analyzer ULTIMATE",
    description="نظام تحليل أسطوري متكامل مع 15 مؤشراً و 12 استراتيجية",
    version="6.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== قائمة الأزواج الأسطورية =====
FOREX_PAIRS = [
    # العملات الرئيسية
    {"symbol": "EURUSD", "name": "EUR/USD", "payout": 92, "base": 1.0900, "type": "forex"},
    {"symbol": "GBPUSD", "name": "GBP/USD", "payout": 90, "base": 1.2600, "type": "forex"},
    {"symbol": "USDJPY", "name": "USD/JPY", "payout": 88, "base": 150.00, "type": "forex"},
    {"symbol": "AUDUSD", "name": "AUD/USD", "payout": 86, "base": 0.6500, "type": "forex"},
    {"symbol": "USDCAD", "name": "USD/CAD", "payout": 84, "base": 1.3500, "type": "forex"},
    {"symbol": "USDCHF", "name": "USD/CHF", "payout": 82, "base": 0.8800, "type": "forex"},
    {"symbol": "NZDUSD", "name": "NZD/USD", "payout": 80, "base": 0.5900, "type": "forex"},
    {"symbol": "EURGBP", "name": "EUR/GBP", "payout": 78, "base": 0.8600, "type": "forex"},
    {"symbol": "EURJPY", "name": "EUR/JPY", "payout": 76, "base": 160.00, "type": "forex"},
    {"symbol": "GBPJPY", "name": "GBP/JPY", "payout": 74, "base": 190.00, "type": "forex"},
    # العملات التركية
    {"symbol": "USDTRY", "name": "USD/TRY", "payout": 72, "base": 34.50, "type": "exotic"},
    {"symbol": "EURTRY", "name": "EUR/TRY", "payout": 70, "base": 38.00, "type": "exotic"},
    {"symbol": "GBPTRY", "name": "GBP/TRY", "payout": 68, "base": 44.00, "type": "exotic"},
    # العملات البنغلاديشية
    {"symbol": "USDBDT", "name": "USD/BDT", "payout": 66, "base": 120.00, "type": "exotic"},
    {"symbol": "EURBDT", "name": "EUR/BDT", "payout": 64, "base": 130.00, "type": "exotic"},
    # العملات الهندية
    {"symbol": "USDINR", "name": "USD/INR", "payout": 62, "base": 83.50, "type": "exotic"},
    {"symbol": "EURINR", "name": "EUR/INR", "payout": 60, "base": 90.00, "type": "exotic"},
    {"symbol": "GBPINR", "name": "GBP/INR", "payout": 58, "base": 105.00, "type": "exotic"},
    # المعادن الثمينة
    {"symbol": "XAUUSD", "name": "الذهب XAU/USD", "payout": 56, "base": 2400.00, "type": "commodity"},
    {"symbol": "XAGUSD", "name": "الفضة XAG/USD", "payout": 54, "base": 28.50, "type": "commodity"},
    # العملات المشفرة
    {"symbol": "BTCUSD", "name": "Bitcoin BTC/USD", "payout": 52, "base": 65000, "type": "crypto"},
    {"symbol": "ETHUSD", "name": "Ethereum ETH/USD", "payout": 50, "base": 3500, "type": "crypto"},
    {"symbol": "SOLUSD", "name": "Solana SOL/USD", "payout": 48, "base": 180, "type": "crypto"},
    {"symbol": "ADAUSD", "name": "Cardano ADA/USD", "payout": 46, "base": 0.60, "type": "crypto"},
]

# ===== ===== ===== ===== ===== ===== ===== =====
# ===== القسم 1: توليد البيانات =====
# ===== ===== ===== ===== ===== ===== ===== =====

def generate_market_wave(seed: int, step: int, base: float, volatility: float, trend: float) -> float:
    """توليد موجة سعرية واقعية"""
    wave1 = math.sin(step / 7 + seed) * volatility * 0.8
    wave2 = math.cos(step / 13 + seed * 2) * volatility * 0.5
    wave3 = math.sin(step / 23 + seed * 3) * volatility * 0.3
    noise = np.random.normal(0, volatility * 0.2)
    trend_effect = trend * (step / 100)
    return wave1 + wave2 + wave3 + noise + trend_effect

def generate_candles(symbol: str, count: int = 200) -> List[Dict]:
    """توليد شموع واقعية مع مستويات دعم ومقاومة"""
    pair = next((p for p in FOREX_PAIRS if p["symbol"] == symbol), FOREX_PAIRS[0])
    base = pair["base"]
    
    # تحديد خصائص السوق
    seed = hash(symbol) % 10000
    volatility = random.uniform(0.0005, 0.003)
    trend = random.uniform(-0.005, 0.005)
    if pair["type"] == "crypto":
        volatility *= 3
    elif pair["type"] == "commodity":
        volatility *= 1.5
    
    candles = []
    current_price = base
    
    for i in range(count):
        step = i
        change = generate_market_wave(seed, step, base, volatility, trend)
        
        open_price = current_price
        close_price = open_price + change
        high_price = max(open_price, close_price) + abs(np.random.normal(0, volatility * 0.4))
        low_price = min(open_price, close_price) - abs(np.random.normal(0, volatility * 0.4))
        
        # تأكد من أن high و low منطقيان
        high_price = max(high_price, open_price, close_price)
        low_price = min(low_price, open_price, close_price)
        
        # إضافة انعكاسات عرضية
        if i > 10 and i % random.randint(8, 15) == 0:
            close_price = open_price + (close_price - open_price) * (-0.5)
            high_price = max(high_price, close_price)
            low_price = min(low_price, close_price)
        
        candle_time = datetime.now() - timedelta(minutes=count - i)
        
        candles.append({
            "timestamp": candle_time.isoformat(),
            "open": round(open_price, 5),
            "high": round(high_price, 5),
            "low": round(low_price, 5),
            "close": round(close_price, 5),
            "volume": random.randint(10, 200)
        })
        current_price = close_price
    
    return candles

def get_live_price(symbol: str) -> float:
    """جلب السعر الحالي مع حركة حية"""
    pair = next((p for p in FOREX_PAIRS if p["symbol"] == symbol), FOREX_PAIRS[0])
    base_price = pair["base"]
    
    # محاكاة حركة حية باستخدام الوقت الحقيقي
    timestamp = time.time()
    seed = hash(symbol) % 10000
    
    wave1 = math.sin(timestamp / 5 + seed) * 0.002
    wave2 = math.cos(timestamp / 12 + seed * 2) * 0.001
    wave3 = math.sin(timestamp / 30 + seed * 3) * 0.0005
    noise = np.random.normal(0, 0.0003)
    
    change = wave1 + wave2 + wave3 + noise
    return round(base_price + change, 5)

# ===== ===== ===== ===== ===== ===== ===== =====
# ===== القسم 2: المؤشرات الفنية =====
# ===== ===== ===== ===== ===== ===== ===== =====

class TechnicalIndicators:
    """فئة تحتوي على جميع المؤشرات الفنية"""
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> float:
        """مؤشر القوة النسبية RSI"""
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
    def macd(prices: List[float]) -> Dict:
        """مؤشر MACD"""
        if len(prices) < 26:
            return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}
        exp1 = pd.Series(prices).ewm(span=12, adjust=False).mean()
        exp2 = pd.Series(prices).ewm(span=26, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        return {
            "macd": float(macd_line.iloc[-1]),
            "signal": float(signal_line.iloc[-1]),
            "histogram": float(histogram.iloc[-1])
        }
    
    @staticmethod
    def bollinger(prices: List[float], period: int = 20, std_dev: float = 2) -> Dict:
        """نطاقات بولينجر"""
        if len(prices) < period:
            return {"upper": None, "middle": None, "lower": None}
        sma = pd.Series(prices).rolling(window=period).mean()
        std = pd.Series(prices).rolling(window=period).std()
        return {
            "upper": float((sma + std * std_dev).iloc[-1]),
            "middle": float(sma.iloc[-1]),
            "lower": float((sma - std * std_dev).iloc[-1])
        }
    
    @staticmethod
    def stochastic(highs: List[float], lows: List[float], closes: List[float]) -> Dict:
        """مؤشر ستوكاستيك"""
        if len(closes) < 14:
            return {"k": 50.0, "d": 50.0}
        low_min = pd.Series(lows).rolling(window=14).min()
        high_max = pd.Series(highs).rolling(window=14).max()
        stoch_k = 100 * ((pd.Series(closes) - low_min) / (high_max - low_min))
        stoch_d = stoch_k.rolling(window=3).mean()
        return {
            "k": float(stoch_k.iloc[-1]),
            "d": float(stoch_d.iloc[-1])
        }
    
    @staticmethod
    def ema(prices: List[float], period: int) -> float:
        """المتوسط المتحرك الأسي"""
        if len(prices) < period:
            return prices[-1] if prices else 0.0
        return float(pd.Series(prices).ewm(span=period, adjust=False).mean().iloc[-1])
    
    @staticmethod
    def sma(prices: List[float], period: int) -> float:
        """المتوسط المتحرك البسيط"""
        if len(prices) < period:
            return prices[-1] if prices else 0.0
        return float(pd.Series(prices).rolling(window=period).mean().iloc[-1])
    
    @staticmethod
    def atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        """متوسط المدى الحقيقي ATR"""
        if len(closes) < period + 1:
            return 0.001
        tr1 = np.array(highs[1:]) - np.array(lows[1:])
        tr2 = abs(np.array(highs[1:]) - np.array(closes[:-1]))
        tr3 = abs(np.array(lows[1:]) - np.array(closes[:-1]))
        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        return float(pd.Series(tr).rolling(window=period).mean().iloc[-1])
    
    @staticmethod
    def ichimoku(highs: List[float], lows: List[float]) -> Dict:
        """مؤشر إيشيموكو"""
        if len(highs) < 52:
            return {"tenkan": 0, "kijun": 0, "senkou_a": 0, "senkou_b": 0, "chikou": 0}
        tenkan = (max(highs[-9:]) + min(lows[-9:])) / 2
        kijun = (max(highs[-26:]) + min(lows[-26:])) / 2
        senkou_a = (tenkan + kijun) / 2
        senkou_b = (max(highs[-52:]) + min(lows[-52:])) / 2
        chikou = highs[-26] if len(highs) > 26 else highs[-1]
        return {
            "tenkan": float(tenkan),
            "kijun": float(kijun),
            "senkou_a": float(senkou_a),
            "senkou_b": float(senkou_b),
            "chikou": float(chikou)
        }
    
    @staticmethod
    def fibonacci(highs: List[float], lows: List[float]) -> Dict:
        """مستويات فيبوناتشي"""
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
    
    @staticmethod
    def support_resistance(highs: List[float], lows: List[float]) -> Dict:
        """مستويات الدعم والمقاومة"""
        if len(highs) < 20:
            return {"support": min(lows), "resistance": max(highs)}
        support = min(lows[-20:])
        resistance = max(highs[-20:])
        # إضافة مستويات ثانوية
        support2 = min(lows[-10:]) if len(lows) >= 10 else support
        resistance2 = max(highs[-10:]) if len(highs) >= 10 else resistance
        return {
            "support": float(support),
            "support2": float(support2),
            "resistance": float(resistance),
            "resistance2": float(resistance2)
        }
    
    @staticmethod
    def adx(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        """مؤشر اتجاه السوق ADX"""
        if len(closes) < period + 1:
            return 25.0
        df = pd.DataFrame({
            'high': highs,
            'low': lows,
            'close': closes
        })
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift()),
                abs(df['low'] - df['close'].shift())
            )
        )
        df['atr'] = df['tr'].rolling(window=period).mean()
        df['dm_plus'] = np.where(
            (df['high'] - df['high'].shift()) > (df['low'].shift() - df['low']),
            np.maximum(df['high'] - df['high'].shift(), 0),
            0
        )
        df['dm_minus'] = np.where(
            (df['low'].shift() - df['low']) > (df['high'] - df['high'].shift()),
            np.maximum(df['low'].shift() - df['low'], 0),
            0
        )
        df['di_plus'] = 100 * df['dm_plus'].rolling(window=period).mean() / df['atr']
        df['di_minus'] = 100 * df['dm_minus'].rolling(window=period).mean() / df['atr']
        df['dx'] = 100 * abs(df['di_plus'] - df['di_minus']) / (df['di_plus'] + df['di_minus'])
        adx = df['dx'].rolling(window=period).mean()
        return float(adx.iloc[-1]) if not adx.empty else 25.0
    
    @staticmethod
    def volume_profile(volumes: List[float]) -> Dict:
        """تحليل حجم التداول"""
        if len(volumes) < 20:
            return {"avg": 50, "current": 50, "ratio": 1.0, "signal": "NEUTRAL"}
        avg = np.mean(volumes[-20:])
        current = volumes[-1]
        ratio = current / avg if avg > 0 else 1.0
        signal = "NEUTRAL"
        if ratio > 1.5:
            signal = "HIGH"
        elif ratio < 0.5:
            signal = "LOW"
        return {
            "avg": float(avg),
            "current": float(current),
            "ratio": float(ratio),
            "signal": signal
        }
    
    @staticmethod
    def candlestick_pattern(opens: List[float], highs: List[float], lows: List[float], closes: List[float]) -> Dict:
        """كشف أنماط الشموع اليابانية"""
        if len(closes) < 3:
            return {"pattern": "NONE", "strength": 0, "direction": "NEUTRAL"}
        
        patterns = []
        strength = 0
        direction = "NEUTRAL"
        
        # 1. Engulfing (ابتلاع)
        body1 = abs(closes[-2] - opens[-2])
        body2 = abs(closes[-1] - opens[-1])
        if closes[-1] > opens[-1] and closes[-2] < opens[-2] and closes[-1] > opens[-2] and opens[-1] < closes[-2]:
            patterns.append("BULLISH_ENGULFING")
            strength += 20
            direction = "BUY"
        elif closes[-1] < opens[-1] and closes[-2] > opens[-2] and opens[-1] > closes[-2] and closes[-1] < opens[-2]:
            patterns.append("BEARISH_ENGULFING")
            strength -= 20
            direction = "SELL"
        
        # 2. Hammer (مطرقة)
        body = abs(closes[-1] - opens[-1])
        lower_shadow = min(opens[-1], closes[-1]) - lows[-1]
        upper_shadow = highs[-1] - max(opens[-1], closes[-1])
        if lower_shadow > 2 * body and upper_shadow < body * 0.3:
            if closes[-1] > opens[-1]:
                patterns.append("HAMMER")
                strength += 15
                if direction == "NEUTRAL":
                    direction = "BUY"
            else:
                patterns.append("HANGING_MAN")
                strength -= 15
                if direction == "NEUTRAL":
                    direction = "SELL"
        
        # 3. Doji (نجمة)
        if abs(closes[-1] - opens[-1]) < (closes[-1] * 0.001):
            patterns.append("DOJI")
            strength += 5
        
        # 4. Morning Star / Evening Star
        if len(closes) >= 3:
            body1_prev = abs(closes[-3] - opens[-3])
            body2_prev = abs(closes[-2] - opens[-2])
            if (closes[-3] < opens[-3] and 
                closes[-2] < opens[-2] and 
                closes[-1] > opens[-1] and
                abs(closes[-2] - opens[-2]) < body1_prev * 0.5 and
                closes[-1] > (opens[-2] + closes[-2]) / 2):
                patterns.append("MORNING_STAR")
                strength += 25
                if direction == "NEUTRAL":
                    direction = "BUY"
            elif (closes[-3] > opens[-3] and 
                  closes[-2] > opens[-2] and 
                  closes[-1] < opens[-1] and
                  abs(closes[-2] - opens[-2]) < body1_prev * 0.5 and
                  closes[-1] < (opens[-2] + closes[-2]) / 2):
                patterns.append("EVENING_STAR")
                strength -= 25
                if direction == "NEUTRAL":
                    direction = "SELL"
        
        return {
            "patterns": patterns,
            "strength": strength,
            "direction": direction,
            "primary": patterns[0] if patterns else "NONE"
        }

# ===== ===== ===== ===== ===== ===== ===== =====
# ===== القسم 3: محرك الإشارات الأسطوري =====
# ===== ===== ===== ===== ===== ===== ===== =====

class SignalEngine:
    """محرك الإشارات المتقدم مع 12 استراتيجية"""
    
    @staticmethod
    def generate_signal(df: pd.DataFrame) -> Dict:
        """توليد إشارة متكاملة"""
        if df is None or len(df) < 30:
            return {"error": "Insufficient data"}
        
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        opens = df['open'].values
        volumes = df.get('volume', np.ones(len(closes)) * 50).values
        
        current_price = closes[-1]
        
        # ===== حساب جميع المؤشرات =====
        indicators = {
            "rsi": TechnicalIndicators.rsi(closes),
            "macd": TechnicalIndicators.macd(closes),
            "bollinger": TechnicalIndicators.bollinger(closes),
            "stochastic": TechnicalIndicators.stochastic(highs, lows, closes),
            "ema9": TechnicalIndicators.ema(closes, 9),
            "ema21": TechnicalIndicators.ema(closes, 21),
            "ema50": TechnicalIndicators.ema(closes, 50),
            "sma20": TechnicalIndicators.sma(closes, 20),
            "atr": TechnicalIndicators.atr(highs, lows, closes),
            "ichimoku": TechnicalIndicators.ichimoku(highs, lows),
            "fibonacci": TechnicalIndicators.fibonacci(highs, lows),
            "sr": TechnicalIndicators.support_resistance(highs, lows),
            "adx": TechnicalIndicators.adx(highs, lows, closes),
            "volume": TechnicalIndicators.volume_profile(volumes),
            "pattern": TechnicalIndicators.candlestick_pattern(opens, highs, lows, closes)
        }
        
        # ===== نظام التسجيل المتقدم =====
        score = 0
        signals = []
        
        # ===== استراتيجية 1: RSI =====
        rsi = indicators["rsi"]
        if rsi < 25:
            score += 30
            signals.append({"name": "RSI تشبع شرائي قوي جداً", "type": "BUY", "score": 30})
        elif rsi < 35:
            score += 20
            signals.append({"name": "RSI تشبع شرائي", "type": "BUY", "score": 20})
        elif rsi < 45:
            score += 8
            signals.append({"name": "RSI قريب من التشبع الشرائي", "type": "BUY", "score": 8})
        elif rsi > 75:
            score -= 30
            signals.append({"name": "RSI تشبع بيعي قوي جداً", "type": "SELL", "score": -30})
        elif rsi > 65:
            score -= 20
            signals.append({"name": "RSI تشبع بيعي", "type": "SELL", "score": -20})
        elif rsi > 55:
            score -= 8
            signals.append({"name": "RSI قريب من التشبع البيعي", "type": "SELL", "score": -8})
        
        # ===== استراتيجية 2: MACD =====
        macd = indicators["macd"]
        if macd["histogram"] > 0.0005 and macd["macd"] > macd["signal"]:
            score += 25
            signals.append({"name": "MACD صعود قوي جداً", "type": "BUY", "score": 25})
        elif macd["histogram"] > 0 and macd["macd"] > macd["signal"]:
            score += 15
            signals.append({"name": "MACD صعود", "type": "BUY", "score": 15})
        elif macd["histogram"] < -0.0005 and macd["macd"] < macd["signal"]:
            score -= 25
            signals.append({"name": "MACD هبوط قوي جداً", "type": "SELL", "score": -25})
        elif macd["histogram"] < 0 and macd["macd"] < macd["signal"]:
            score -= 15
            signals.append({"name": "MACD هبوط", "type": "SELL", "score": -15})
        
        # ===== استراتيجية 3: Bollinger Bands =====
        bb = indicators["bollinger"]
        if bb["lower"] and current_price <= bb["lower"] * 1.005:
            score += 20
            signals.append({"name": "Bollinger أسفل النطاق", "type": "BUY", "score": 20})
        elif bb["upper"] and current_price >= bb["upper"] * 0.995:
            score -= 20
            signals.append({"name": "Bollinger أعلى النطاق", "type": "SELL", "score": -20})
        
        # ===== استراتيجية 4: Stochastic =====
        stoch = indicators["stochastic"]
        if stoch["k"] < 20 and stoch["d"] < 20 and stoch["k"] > stoch["d"]:
            score += 15
            signals.append({"name": "Stochastic تشبع شرائي", "type": "BUY", "score": 15})
        elif stoch["k"] > 80 and stoch["d"] > 80 and stoch["k"] < stoch["d"]:
            score -= 15
            signals.append({"name": "Stochastic تشبع بيعي", "type": "SELL", "score": -15})
        
        # ===== استراتيجية 5: الاتجاه (EMA) =====
        ema9 = indicators["ema9"]
        ema21 = indicators["ema21"]
        ema50 = indicators["ema50"]
        if ema9 > ema21 and ema21 > ema50 and current_price > ema9:
            if ema9 - ema21 > 0.005:
                score += 30
                signals.append({"name": "اتجاه صاعد قوي جداً", "type": "BUY", "score": 30})
            else:
                score += 15
                signals.append({"name": "اتجاه صاعد", "type": "BUY", "score": 15})
        elif ema9 < ema21 and ema21 < ema50 and current_price < ema9:
            if ema21 - ema9 > 0.005:
                score -= 30
                signals.append({"name": "اتجاه هابط قوي جداً", "type": "SELL", "score": -30})
            else:
                score -= 15
                signals.append({"name": "اتجاه هابط", "type": "SELL", "score": -15})
        
        # ===== استراتيجية 6: SMA =====
        sma20 = indicators["sma20"]
        if current_price > sma20 * 1.01:
            score += 10
            signals.append({"name": "فوق SMA20", "type": "BUY", "score": 10})
        elif current_price < sma20 * 0.99:
            score -= 10
            signals.append({"name": "تحت SMA20", "type": "SELL", "score": -10})
        
        # ===== استراتيجية 7: ATR والتقلب =====
        atr = indicators["atr"]
        volatility = "LOW"
        if atr > 0.003:
            volatility = "HIGH"
            if rsi < 50:
                score += 8
                signals.append({"name": "تقلب عالي مع ميل صاعد", "type": "BUY", "score": 8})
            else:
                score -= 8
                signals.append({"name": "تقلب عالي مع ميل هابط", "type": "SELL", "score": -8})
        elif atr > 0.0015:
            volatility = "MEDIUM"
        
        # ===== استراتيجية 8: ADX =====
        adx = indicators["adx"]
        if adx > 40:
            if ema9 > ema21:
                score += 15
                signals.append({"name": "اتجاه قوي صاعد", "type": "BUY", "score": 15})
            else:
                score -= 15
                signals.append({"name": "اتجاه قوي هابط", "type": "SELL", "score": -15})
        elif adx > 25:
            if ema9 > ema21:
                score += 8
                signals.append({"name": "اتجاه متوسط صاعد", "type": "BUY", "score": 8})
            else:
                score -= 8
                signals.append({"name": "اتجاه متوسط هابط", "type": "SELL", "score": -8})
        
        # ===== استراتيجية 9: إيشيموكو =====
        ichi = indicators["ichimoku"]
        if ichi["senkou_a"] > ichi["senkou_b"] and current_price > ichi["senkou_a"]:
            score += 10
            signals.append({"name": "Ichimoku صاعد", "type": "BUY", "score": 10})
        elif ichi["senkou_a"] < ichi["senkou_b"] and current_price < ichi["senkou_a"]:
            score -= 10
            signals.append({"name": "Ichimoku هابط", "type": "SELL", "score": -10})
        
        # ===== استراتيجية 10: فيبوناتشي =====
        fib = indicators["fibonacci"]
        if current_price <= fib["618"] * 1.005:
            score += 12
            signals.append({"name": "Fibonacci 61.8% دعم", "type": "BUY", "score": 12})
        elif current_price >= fib["382"] * 0.995:
            score -= 12
            signals.append({"name": "Fibonacci 38.2% مقاومة", "type": "SELL", "score": -12})
        
        # ===== استراتيجية 11: الدعم والمقاومة =====
        sr = indicators["sr"]
        if current_price <= sr["support"] * 1.005:
            score += 15
            signals.append({"name": "ارتداد من الدعم الرئيسي", "type": "BUY", "score": 15})
        elif current_price <= sr["support2"] * 1.005:
            score += 8
            signals.append({"name": "ارتداد من الدعم الثانوي", "type": "BUY", "score": 8})
        elif current_price >= sr["resistance"] * 0.995:
            score -= 15
            signals.append({"name": "ارتداد من المقاومة الرئيسية", "type": "SELL", "score": -15})
        elif current_price >= sr["resistance2"] * 0.995:
            score -= 8
            signals.append({"name": "ارتداد من المقاومة الثانوية", "type": "SELL", "score": -8})
        
        # ===== استراتيجية 12: أنماط الشموع =====
        pattern = indicators["pattern"]
        if pattern["direction"] == "BUY":
            score += pattern["strength"]
            for p in pattern["patterns"]:
                signals.append({"name": f"نمط {p}", "type": "BUY", "score": pattern["strength"]})
        elif pattern["direction"] == "SELL":
            score += pattern["strength"]
            for p in pattern["patterns"]:
                signals.append({"name": f"نمط {p}", "type": "SELL", "score": pattern["strength"]})
        
        # ===== استراتيجية 13: الحجم =====
        vol = indicators["volume"]
        if vol["signal"] == "HIGH":
            if closes[-1] > opens[-1]:
                score += 10
                signals.append({"name": "حجم مرتفع مع صعود", "type": "BUY", "score": 10})
            else:
                score -= 10
                signals.append({"name": "حجم مرتفع مع هبوط", "type": "SELL", "score": -10})
        
        # ===== القرار النهائي =====
        action = "NEUTRAL"
        confidence = 0
        
        if score >= 50:
            action = "STRONG_BUY"
            confidence = min(99, 80 + score // 2)
        elif score >= 30:
            action = "BUY"
            confidence = min(95, 65 + score // 2)
        elif score >= 15:
            action = "WEAK_BUY"
            confidence = min(90, 50 + score // 2)
        elif score <= -50:
            action = "STRONG_SELL"
            confidence = min(99, 80 + abs(score) // 2)
        elif score <= -30:
            action = "SELL"
            confidence = min(95, 65 + abs(score) // 2)
        elif score <= -15:
            action = "WEAK_SELL"
            confidence = min(90, 50 + abs(score) // 2)
        else:
            confidence = max(20, 35 + score)
        
        # ===== حساب الوقت المتبقي للشمعة =====
        now = datetime.now()
        seconds = 60 - now.second
        minutes_remaining = round(seconds / 60, 2)
        
        # ===== تحديد وقت الدخول المقترح =====
        entry_suggestion = ""
        if action in ["STRONG_BUY", "BUY", "WEAK_BUY"]:
            if minutes_remaining > 0.5:
                entry_suggestion = f"⏱️ دخول الآن ({minutes_remaining:.1f} دقيقة متبقية)"
            else:
                entry_suggestion = f"⏱️ انتظر الشمعة القادمة ({minutes_remaining:.1f} دقيقة متبقية)"
        elif action in ["STRONG_SELL", "SELL", "WEAK_SELL"]:
            if minutes_remaining > 0.5:
                entry_suggestion = f"⏱️ دخول الآن ({minutes_remaining:.1f} دقيقة متبقية)"
            else:
                entry_suggestion = f"⏱️ انتظر الشمعة القادمة ({minutes_remaining:.1f} دقيقة متبقية)"
        
        return {
            "action": action,
            "confidence": confidence,
            "score": score,
            "signals": signals,
            "current_price": float(current_price),
            "rsi": rsi,
            "macd": indicators["macd"],
            "bollinger": indicators["bollinger"],
            "stochastic": indicators["stochastic"],
            "ema9": ema9,
            "ema21": ema21,
            "ema50": ema50,
            "sma20": sma20,
            "atr": atr,
            "volatility": volatility,
            "support_resistance": sr,
            "ichimoku": indicators["ichimoku"],
            "fibonacci": indicators["fibonacci"],
            "adx": adx,
            "volume": indicators["volume"],
            "pattern": indicators["pattern"],
            "time_remaining_minutes": minutes_remaining,
            "entry_suggestion": entry_suggestion
        }

# ===== ===== ===== ===== ===== ===== ===== =====
# ===== القسم 4: نقاط النهاية API =====
# ===== ===== ===== ===== ===== ===== ===== =====

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """تقديم الصفحة الرئيسية"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>index.html not found</h1>")

@app.get("/style.css", response_class=FileResponse)
async def serve_css():
    """تقديم ملف CSS"""
    return FileResponse("style.css")

@app.get("/script.js", response_class=FileResponse)
async def serve_js():
    """تقديم ملف JavaScript"""
    return FileResponse("script.js")

@app.get("/api/v1/markets")
async def get_markets():
    """قائمة جميع الأزواج المتاحة"""
    return {
        "status": "success",
        "count": len(FOREX_PAIRS),
        "data": FOREX_PAIRS
    }

@app.get("/api/v1/candles/{symbol}")
async def get_candles(symbol: str, limit: int = Query(200, ge=10, le=500)):
    """جلب بيانات الشموع لزوج معين"""
    pair = next((p for p in FOREX_PAIRS if p["symbol"] == symbol), None)
    if not pair:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found")
    
    candles = generate_candles(symbol, limit)
    return {
        "symbol": symbol,
        "count": len(candles),
        "candles": candles
    }

@app.get("/api/v2/analyze/{symbol}")
async def analyze_symbol(
    symbol: str,
    limit: int = Query(200, ge=30, le=500),
    include_raw: bool = Query(False, description="تضمين البيانات الخام")
):
    """تحليل متقدم لزوج معين مع جميع المؤشرات"""
    pair = next((p for p in FOREX_PAIRS if p["symbol"] == symbol), None)
    if not pair:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found")
    
    try:
        # جلب الشموع
        candles = generate_candles(symbol, limit)
        df = pd.DataFrame(candles)
        
        # توليد الإشارة
        signal = SignalEngine.generate_signal(df)
        if "error" in signal:
            raise HTTPException(status_code=400, detail=signal["error"])
        
        # جلب السعر الحالي
        price = get_live_price(symbol)
        
        # إضافة معلومات الزوج
        signal["symbol"] = symbol
        signal["pair_name"] = pair["name"]
        signal["payout"] = pair["payout"]
        signal["current_price"] = price or signal["current_price"]
        signal["timestamp"] = datetime.now().isoformat()
        
        # إضافة البيانات الخام إذا طلب
        if include_raw:
            signal["raw_candles"] = candles[-30:]
        
        return signal
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v2/strong-signal")
async def get_strong_signal(
    symbol: str = Query(None, description="رمز الزوج للبحث"),
    scan_all: bool = Query(False, description="مسح جميع الأزواج")
):
    """البحث عن إشارة قوية في زوج محدد أو جميع الأزواج"""
    if symbol:
        # بحث في زوج محدد
        try:
            result = await analyze_symbol(symbol)
            if result and result["action"] in ["STRONG_BUY", "STRONG_SELL"] and result["confidence"] >= 70:
                return {"status": "success", "signal": result}
            return {"status": "no_signal", "message": f"لا توجد إشارات قوية في {symbol}"}
        except:
            return {"status": "error", "message": "خطأ في تحليل الزوج"}
    
    if scan_all:
        # مسح جميع الأزواج
        best = None
        best_score = -999
        
        for pair in FOREX_PAIRS:
            try:
                result = await analyze_symbol(pair["symbol"])
                if result and result["action"] in ["STRONG_BUY", "STRONG_SELL", "BUY", "SELL"]:
                    if result["score"] > best_score:
                        best = result
                        best_score = result["score"]
            except:
                continue
        
        if best:
            return {"status": "success", "signal": best, "scanned": len(FOREX_PAIRS)}
        return {"status": "no_signal", "message": "لا توجد إشارات قوية في جميع الأزواج"}
    
    return {"status": "error", "message": "الرجاء تحديد زوج أو تفعيل المسح الشامل"}

@app.get("/api/v2/multi-analyze")
async def multi_analyze(
    symbols: str = Query(None, description="قائمة الأزواج مفصولة بفاصلة"),
    limit: int = Query(200, ge=30, le=500)
):
    """تحليل عدة أزواج في وقت واحد"""
    if not symbols:
        return {"status": "error", "message": "الرجاء تحديد الأزواج"}
    
    symbol_list = [s.strip() for s in symbols.split(",")]
    results = {}
    
    for symbol in symbol_list:
        try:
            result = await analyze_symbol(symbol, limit)
            results[symbol] = {
                "action": result.get("action", "ERROR"),
                "confidence": result.get("confidence", 0),
                "score": result.get("score", 0),
                "price": result.get("current_price", 0)
            }
        except:
            results[symbol] = {"error": "فشل التحليل"}
    
    return {
        "status": "success",
        "results": results
    }

@app.get("/api/v2/market-summary")
async def market_summary():
    """ملخص عام للسوق مع أفضل التوصيات"""
    recommendations = []
    
    for pair in FOREX_PAIRS[:10]:  # حد أقصى 10 أزواج للتلخيص
        try:
            result = await analyze_symbol(pair["symbol"])
            if result and result["action"] != "NEUTRAL":
                recommendations.append({
                    "symbol": pair["symbol"],
                    "name": pair["name"],
                    "action": result["action"],
                    "confidence": result["confidence"],
                    "price": result["current_price"]
                })
        except:
            continue
    
    # ترتيب حسب الثقة
    recommendations.sort(key=lambda x: x["confidence"], reverse=True)
    
    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "total_analyzed": len(recommendations),
        "recommendations": recommendations[:5]  # أفضل 5 توصيات
    }

@app.get("/health")
async def health_check():
    """فحص صحة النظام"""
    return {
        "status": "healthy",
        "version": "6.0.0",
        "timestamp": datetime.now().isoformat(),
        "pairs_count": len(FOREX_PAIRS)
    }

@app.get("/api/v1/pairs")
async def get_pairs():
    """الحصول على قائمة الأزواج (نسخة مبسطة)"""
    return {"pairs": [p["symbol"] for p in FOREX_PAIRS]}

@app.get("/api/v1/pair/{symbol}/price")
async def get_pair_price(symbol: str):
    """الحصول على السعر الحالي لزوج"""
    pair = next((p for p in FOREX_PAIRS if p["symbol"] == symbol), None)
    if not pair:
        raise HTTPException(status_code=404, detail="Symbol not found")
    return {
        "symbol": symbol,
        "price": get_live_price(symbol),
        "timestamp": datetime.now().isoformat()
    }

# ===== ===== ===== ===== ===== ===== ===== =====
# ===== القسم 5: تشغيل التطبيق =====
# ===== ===== ===== ===== ===== ===== ===== =====

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)