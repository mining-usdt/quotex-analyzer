import pandas as pd
import numpy as np
from indicators import AdvancedIndicators

class SignalEngine:
    @staticmethod
    def generate_signal(df):
        """توليد إشارة متكاملة من DataFrame"""
        if df is None or len(df) < 30:
            return {"error": "Insufficient data"}
        
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        
        current_price = closes[-1]
        
        # حساب المؤشرات
        rsi = AdvancedIndicators.calculate_rsi(closes)
        macd = AdvancedIndicators.calculate_macd(closes)
        bollinger = AdvancedIndicators.calculate_bollinger(closes)
        stoch = AdvancedIndicators.calculate_stochastic(highs, lows, closes)
        ema9 = AdvancedIndicators.calculate_ema(closes, 9)
        ema21 = AdvancedIndicators.calculate_ema(closes, 21)
        ema50 = AdvancedIndicators.calculate_ema(closes, 50)
        atr = AdvancedIndicators.calculate_atr(highs, lows, closes)
        
        # نظام التسجيل
        score = 0
        signals = []
        
        # 1. RSI
        if rsi < 30:
            score += 20
            signals.append({"name": "RSI Oversold", "type": "BUY", "score": 20})
        elif rsi > 70:
            score -= 20
            signals.append({"name": "RSI Overbought", "type": "SELL", "score": -20})
        
        # 2. MACD
        if macd["histogram"] > 0 and macd["macd"] > macd["signal"]:
            score += 15
            signals.append({"name": "MACD Bullish", "type": "BUY", "score": 15})
        elif macd["histogram"] < 0 and macd["macd"] < macd["signal"]:
            score -= 15
            signals.append({"name": "MACD Bearish", "type": "SELL", "score": -15})
        
        # 3. Bollinger
        if bollinger["lower"] and current_price <= bollinger["lower"] * 1.005:
            score += 10
            signals.append({"name": "BB Oversold", "type": "BUY", "score": 10})
        elif bollinger["upper"] and current_price >= bollinger["upper"] * 0.995:
            score -= 10
            signals.append({"name": "BB Overbought", "type": "SELL", "score": -10})
        
        # 4. Stochastic
        if stoch["k"] < 20 and stoch["d"] < 20:
            score += 10
            signals.append({"name": "Stoch Oversold", "type": "BUY", "score": 10})
        elif stoch["k"] > 80 and stoch["d"] > 80:
            score -= 10
            signals.append({"name": "Stoch Overbought", "type": "SELL", "score": -10})
        
        # 5. Trend (EMA)
        if ema9 > ema21 and ema21 > ema50 and current_price > ema9:
            score += 15
            signals.append({"name": "Uptrend", "type": "BUY", "score": 15})
        elif ema9 < ema21 and ema21 < ema50 and current_price < ema9:
            score -= 15
            signals.append({"name": "Downtrend", "type": "SELL", "score": -15})
        
        # القرار النهائي
        action = "NEUTRAL"
        confidence = 0
        
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
            confidence = max(20, 30 + score)
        
        # التقلب
        volatility = "LOW"
        if atr > 0.002:
            volatility = "HIGH"
        elif atr > 0.001:
            volatility = "MEDIUM"
        
        return {
            "action": action,
            "confidence": confidence,
            "score": score,
            "signals": signals,
            "current_price": current_price,
            "rsi": rsi,
            "macd": macd,
            "bollinger": bollinger,
            "stochastic": stoch,
            "ema9": ema9,
            "ema21": ema21,
            "ema50": ema50,
            "atr": atr,
            "volatility": volatility
        }