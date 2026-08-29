"""
محرك الإشارات المتقدم
10 استراتيجيات تحليل فني مع نظام تسجيل ذكي
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from indicators import AdvancedIndicators

class SignalEngine:
    """محرك توليد الإشارات الفنية"""
    
    @staticmethod
    def generate_signal(df: pd.DataFrame) -> Dict[str, Any]:
        """توليد إشارة متكاملة من بيانات الشموع"""
        
        if df is None or len(df) < 30:
            return {"error": "بيانات غير كافية (تحتاج 30 شمعة على الأقل)"}
        
        # استخراج البيانات
        closes = df['close'].values.astype(float)
        highs = df['high'].values.astype(float)
        lows = df['low'].values.astype(float)
        opens = df['open'].values.astype(float)
        
        # استخدام الحجم إذا كان موجوداً
        volumes = df['volume'].values.astype(float) if 'volume' in df.columns else np.ones(len(closes)) * 50
        
        current_price = closes[-1]
        
        # ===== حساب المؤشرات =====
        rsi = AdvancedIndicators.calculate_rsi(closes)
        macd = AdvancedIndicators.calculate_macd(closes)
        bollinger = AdvancedIndicators.calculate_bollinger(closes)
        stoch = AdvancedIndicators.calculate_stochastic(highs, lows, closes)
        ema9 = AdvancedIndicators.calculate_ema(closes, 9)
        ema21 = AdvancedIndicators.calculate_ema(closes, 21)
        ema50 = AdvancedIndicators.calculate_ema(closes, 50)
        sma20 = AdvancedIndicators.calculate_sma(closes, 20)
        atr = AdvancedIndicators.calculate_atr(highs, lows, closes)
        adx = AdvancedIndicators.calculate_adx(highs, lows, closes)
        ichimoku = AdvancedIndicators.calculate_ichimoku(highs, lows)
        cci = AdvancedIndicators.calculate_cci(highs, lows, closes)
        
        # ===== نظام التسجيل =====
        score = 0
        signals = []
        
        # ------------------------------------------------------------
        # استراتيجية 1: RSI
        # ------------------------------------------------------------
        if rsi < 25:
            score += 25
            signals.append({"name": "RSI تشبع شرائي قوي", "type": "BUY", "score": 25})
        elif rsi < 35:
            score += 15
            signals.append({"name": "RSI تشبع شرائي", "type": "BUY", "score": 15})
        elif rsi > 75:
            score -= 25
            signals.append({"name": "RSI تشبع بيعي قوي", "type": "SELL", "score": -25})
        elif rsi > 65:
            score -= 15
            signals.append({"name": "RSI تشبع بيعي", "type": "SELL", "score": -15})
        
        # ------------------------------------------------------------
        # استراتيجية 2: MACD
        # ------------------------------------------------------------
        if macd["histogram"] > 0 and macd["macd"] > macd["signal"]:
            if macd["histogram"] > 0.0005:
                score += 20
                signals.append({"name": "MACD صعود قوي", "type": "BUY", "score": 20})
            else:
                score += 12
                signals.append({"name": "MACD صعود", "type": "BUY", "score": 12})
        elif macd["histogram"] < 0 and macd["macd"] < macd["signal"]:
            if macd["histogram"] < -0.0005:
                score -= 20
                signals.append({"name": "MACD هبوط قوي", "type": "SELL", "score": -20})
            else:
                score -= 12
                signals.append({"name": "MACD هبوط", "type": "SELL", "score": -12})
        
        # ------------------------------------------------------------
        # استراتيجية 3: بولينجر باند
        # ------------------------------------------------------------
        if bollinger["lower"] and current_price <= bollinger["lower"] * 1.003:
            score += 15
            signals.append({"name": "Bollinger أسفل النطاق", "type": "BUY", "score": 15})
        elif bollinger["upper"] and current_price >= bollinger["upper"] * 0.997:
            score -= 15
            signals.append({"name": "Bollinger أعلى النطاق", "type": "SELL", "score": -15})
        
        # ------------------------------------------------------------
        # استراتيجية 4: ستوكاستيك
        # ------------------------------------------------------------
        if stoch["k"] < 20 and stoch["d"] < 20 and stoch["k"] > stoch["d"]:
            score += 12
            signals.append({"name": "Stochastic تشبع شرائي", "type": "BUY", "score": 12})
        elif stoch["k"] > 80 and stoch["d"] > 80 and stoch["k"] < stoch["d"]:
            score -= 12
            signals.append({"name": "Stochastic تشبع بيعي", "type": "SELL", "score": -12})
        
        # ------------------------------------------------------------
        # استراتيجية 5: الاتجاه (EMAs)
        # ------------------------------------------------------------
        if ema9 > ema21 and ema21 > ema50 and current_price > ema9:
            if ema9 - ema21 > 0.005:
                score += 25
                signals.append({"name": "اتجاه صاعد قوي", "type": "BUY", "score": 25})
            else:
                score += 15
                signals.append({"name": "اتجاه صاعد", "type": "BUY", "score": 15})
        elif ema9 < ema21 and ema21 < ema50 and current_price < ema9:
            if ema21 - ema9 > 0.005:
                score -= 25
                signals.append({"name": "اتجاه هابط قوي", "type": "SELL", "score": -25})
            else:
                score -= 15
                signals.append({"name": "اتجاه هابط", "type": "SELL", "score": -15})
        
        # ------------------------------------------------------------
        # استراتيجية 6: SMA
        # ------------------------------------------------------------
        if current_price > sma20 * 1.005:
            score += 8
            signals.append({"name": "فوق SMA20", "type": "BUY", "score": 8})
        elif current_price < sma20 * 0.995:
            score -= 8
            signals.append({"name": "تحت SMA20", "type": "SELL", "score": -8})
        
        # ------------------------------------------------------------
        # استراتيجية 7: الدعم والمقاومة
        # ------------------------------------------------------------
        support = min(lows[-20:])
        resistance = max(highs[-20:])
        
        if current_price <= support * 1.005:
            score += 10
            signals.append({"name": "ارتداد من الدعم", "type": "BUY", "score": 10})
        elif current_price >= resistance * 0.995:
            score -= 10
            signals.append({"name": "ارتداد من المقاومة", "type": "SELL", "score": -10})
        
        # ------------------------------------------------------------
        # استراتيجية 8: أنماط الشموع
        # ------------------------------------------------------------
        if len(closes) > 3:
            # نمط الابتلاع الصاعد (Bullish Engulfing)
            if (closes[-1] > opens[-1] and closes[-2] < opens[-2] and
                closes[-1] > opens[-2] and opens[-1] < closes[-2]):
                score += 15
                signals.append({"name": "نمط ابتلاع صاعد", "type": "BUY", "score": 15})
            
            # نمط الابتلاع الهابط (Bearish Engulfing)
            elif (closes[-1] < opens[-1] and closes[-2] > opens[-2] and
                  opens[-1] > closes[-2] and closes[-1] < opens[-2]):
                score -= 15
                signals.append({"name": "نمط ابتلاع هابط", "type": "SELL", "score": -15})
            
            # نمط المطرقة (Hammer)
            body = abs(closes[-1] - opens[-1])
            lower_wick = min(opens[-1], closes[-1]) - lows[-1]
            upper_wick = highs[-1] - max(opens[-1], closes[-1])
            
            if lower_wick > body * 2 and upper_wick < body * 0.3 and closes[-1] > opens[-1]:
                score += 10
                signals.append({"name": "نمط مطرقة صاعد", "type": "BUY", "score": 10})
            
            # نمط الرجل المعلق (Hanging Man)
            if lower_wick > body * 2 and upper_wick < body * 0.3 and closes[-1] < opens[-1]:
                score -= 10
                signals.append({"name": "نمط رجل معلق هابط", "type": "SELL", "score": -10})
        
        # ------------------------------------------------------------
        # استراتيجية 9: ADX (قوة الاتجاه)
        # ------------------------------------------------------------
        if adx > 25:
            if ema9 > ema21:
                score += 8
                signals.append({"name": "اتجاه قوي صاعد", "type": "BUY", "score": 8})
            else:
                score -= 8
                signals.append({"name": "اتجاه قوي هابط", "type": "SELL", "score": -8})
        
        # ------------------------------------------------------------
        # استراتيجية 10: إيشيموكو
        # ------------------------------------------------------------
        if current_price > ichimoku["senkou_a"] and current_price > ichimoku["senkou_b"]:
            score += 10
            signals.append({"name": "فوق سحابة إيشيموكو", "type": "BUY", "score": 10})
        elif current_price < ichimoku["senkou_a"] and current_price < ichimoku["senkou_b"]:
            score -= 10
            signals.append({"name": "تحت سحابة إيشيموكو", "type": "SELL", "score": -10})
        
        # ------------------------------------------------------------
        # استراتيجية 11: CCI (مؤشر قناة السلع)
        # ------------------------------------------------------------
        if cci < -100:
            score += 10
            signals.append({"name": "CCI تشبع شرائي", "type": "BUY", "score": 10})
        elif cci > 100:
            score -= 10
            signals.append({"name": "CCI تشبع بيعي", "type": "SELL", "score": -10})
        
        # ------------------------------------------------------------
        # استراتيجية 12: التقلب (ATR)
        # ------------------------------------------------------------
        volatility = "LOW"
        if atr > 0.003:
            volatility = "HIGH"
            # إضافة نقاط إضافية حسب اتجاه السعر
            if closes[-1] > closes[-5]:
                score += 5
            else:
                score -= 5
        elif atr > 0.0015:
            volatility = "MEDIUM"
        
        # ===== القرار النهائي =====
        action = "NEUTRAL"
        confidence = 0
        
        if score >= 40:
            action = "STRONG_BUY"
            confidence = min(99, 80 + score // 2)
        elif score >= 25:
            action = "BUY"
            confidence = min(95, 65 + score // 2)
        elif score <= -40:
            action = "STRONG_SELL"
            confidence = min(99, 80 + abs(score) // 2)
        elif score <= -25:
            action = "SELL"
            confidence = min(95, 65 + abs(score) // 2)
        else:
            confidence = max(20, 35 + score)
        
        # الوقت المتبقي للشمعة
        now = datetime.now()
        seconds_remaining = 60 - now.second
        minutes_remaining = round(seconds_remaining / 60, 2)
        
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
            "sma20": sma20,
            "atr": atr,
            "adx": adx,
            "ichimoku": ichimoku,
            "cci": cci,
            "volatility": volatility,
            "support_resistance": {"support": support, "resistance": resistance},
            "time_remaining_minutes": minutes_remaining
        }