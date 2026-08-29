import httpx
import asyncio
from datetime import datetime
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple

class AdvancedSignalEngine:
    def __init__(self, api_base_url="http://127.0.0.1:8000"):
        self.api_base = api_base_url
        
    async def get_asset_analysis(self, symbol: str, limit: int = 200) -> Optional[Dict]:
        """تحليل متقدم مع 7 مؤشرات + أنماط شموع + دعم/مقاومة"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/api/v1/candles",
                    params={"symbol": symbol, "limit": limit}
                )
                
                if response.status_code != 200:
                    return None
                    
                data = response.json()
                candles = data.get('candles', [])
                
                if len(candles) < 50:
                    return None
                    
                # تحويل إلى DataFrame للتحليل السريع
                df = pd.DataFrame(candles)
                closes = df['close'].values
                highs = df['high'].values
                lows = df['low'].values
                opens = df['open'].values
                
                # === 1. المؤشرات الأساسية (المحسنة) ===
                
                # RSI (14) مع إشارات التشبع
                rsi = self._calculate_rsi(closes, 14)
                rsi_signal = self._rsi_signal(rsi)
                
                # MACD (12, 26, 9) مع تقاطع
                macd_line, signal_line, histogram = self._calculate_macd(closes)
                macd_signal = self._macd_signal(macd_line, signal_line, histogram)
                
                # Bollinger Bands (20, 2)
                upper, middle, lower = self._calculate_bollinger(closes)
                bb_signal = self._bb_signal(closes[-1], upper[-1], middle[-1], lower[-1])
                
                # === 2. المؤشرات المتقدمة (الجديدة) ===
                
                # EMA 9 و 21 للاتجاه
                ema9 = self._calculate_ema(closes, 9)
                ema21 = self._calculate_ema(closes, 21)
                trend_signal = self._trend_signal(ema9, ema21, closes)
                
                # Stochastic Oscillator (14, 3, 3)
                stoch_k, stoch_d = self._calculate_stochastic(highs, lows, closes)
                stoch_signal = self._stochastic_signal(stoch_k, stoch_d)
                
                # ATR (Average True Range) للتقلب
                atr = self._calculate_atr(highs, lows, closes, 14)
                volatility = "HIGH" if atr[-1] > atr.mean() * 1.5 else "LOW"
                
                # === 3. أنماط الشموع اليابانية (الاختراقات والارتدادات) ===
                
                # نمط الابتلاع (Engulfing)
                engulfing = self._detect_engulfing(opens, closes)
                
                # نمط المطرقة / الرجل المشنوق (Hammer / Hanging Man)
                hammer = self._detect_hammer(opens, highs, lows, closes)
                
                # نمط النجم (Doji)
                doji = self._detect_doji(opens, closes)
                
                # === 4. الدعم والمقاومة الديناميكية ===
                
                support, resistance = self._find_support_resistance(highs, lows, closes)
                
                # === 5. تحليل الاختراق (Breakout) ===
                
                breakout = self._detect_breakout(closes, upper, lower, support, resistance)
                
                # === 6. تحليل الارتداد (Bounce) ===
                
                bounce = self._detect_bounce(closes, support, resistance, rsi)
                
                # === 7. نظام التسجيل المرجح (Weighted Scoring System) ===
                
                score = 0
                signals_triggered = []
                
                # تجميع الإشارات مع الأوزان
                signal_weights = {
                    'rsi': (rsi_signal, 15),
                    'macd': (macd_signal, 15),
                    'bb': (bb_signal, 10),
                    'trend': (trend_signal, 10),
                    'stoch': (stoch_signal, 10),
                    'engulfing': (engulfing, 20),
                    'hammer': (hammer, 10),
                    'breakout': (breakout, 15),
                    'bounce': (bounce, 15)
                }
                
                for signal_name, (signal_value, weight) in signal_weights.items():
                    if signal_value == 'BUY':
                        score += weight
                        signals_triggered.append(f"{signal_name}:BUY")
                    elif signal_value == 'SELL':
                        score -= weight
                        signals_triggered.append(f"{signal_name}:SELL")
                
                # تحديد الإشارة النهائية
                action = 'NEUTRAL'
                confidence = 0
                
                if score >= 30:
                    action = 'BUY'
                    confidence = min(99, 60 + score)
                elif score <= -30:
                    action = 'SELL'
                    confidence = min(99, 60 + abs(score))
                
                # إشارات قوية جدًا (اختراق + ارتداد + نمط)
                if breakout == 'BUY' and bounce == 'BUY' and engulfing == 'BUY':
                    action = 'BUY'
                    confidence = 95
                elif breakout == 'SELL' and bounce == 'SELL' and engulfing == 'SELL':
                    action = 'SELL'
                    confidence = 95
                
                return {
                    'symbol': symbol,
                    'action': action,
                    'confidence': confidence,
                    'price': closes[-1],
                    'timestamp': datetime.now().isoformat(),
                    'indicators': {
                        'rsi': float(rsi[-1]),
                        'rsi_signal': rsi_signal,
                        'macd': {
                            'macd': float(macd_line[-1]),
                            'signal': float(signal_line[-1]),
                            'histogram': float(histogram[-1])
                        },
                        'macd_signal': macd_signal,
                        'bollinger': {
                            'upper': float(upper[-1]),
                            'middle': float(middle[-1]),
                            'lower': float(lower[-1])
                        },
                        'bb_signal': bb_signal,
                        'ema9': float(ema9[-1]),
                        'ema21': float(ema21[-1]),
                        'trend_signal': trend_signal,
                        'stoch_k': float(stoch_k[-1]),
                        'stoch_d': float(stoch_d[-1]),
                        'stoch_signal': stoch_signal,
                        'atr': float(atr[-1]),
                        'volatility': volatility
                    },
                    'patterns': {
                        'engulfing': engulfing,
                        'hammer': hammer,
                        'doji': doji
                    },
                    'levels': {
                        'support': float(support),
                        'resistance': float(resistance)
                    },
                    'breakout': breakout,
                    'bounce': bounce,
                    'signals_triggered': signals_triggered,
                    'score': score,
                    'payout': candles[-1].get('payout', 0)
                }
                
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")
            return None
    
    # === دوال المؤشرات المتقدمة ===
    
    def _calculate_rsi(self, prices, period=14):
        delta = np.diff(prices)
        gain = (delta > 0) * delta
        loss = (delta < 0) * -delta
        avg_gain = pd.Series(gain).rolling(window=period).mean()
        avg_loss = pd.Series(loss).rolling(window=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return np.append([50], rsi.values)  # padding
    
    def _rsi_signal(self, rsi):
        if rsi[-1] < 30:
            return 'BUY'
        elif rsi[-1] > 70:
            return 'SELL'
        return 'NEUTRAL'
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        exp1 = pd.Series(prices).ewm(span=fast, adjust=False).mean()
        exp2 = pd.Series(prices).ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd.values, signal_line.values, histogram.values
    
    def _macd_signal(self, macd, signal, hist):
        if len(macd) < 2:
            return 'NEUTRAL'
        if macd[-1] > signal[-1] and macd[-2] <= signal[-2] and hist[-1] > 0:
            return 'BUY'
        elif macd[-1] < signal[-1] and macd[-2] >= signal[-2] and hist[-1] < 0:
            return 'SELL'
        return 'NEUTRAL'
    
    def _calculate_bollinger(self, prices, period=20, std_dev=2):
        sma = pd.Series(prices).rolling(window=period).mean()
        std = pd.Series(prices).rolling(window=period).std()
        upper = sma + std * std_dev
        middle = sma
        lower = sma - std * std_dev
        return upper.values, middle.values, lower.values
    
    def _bb_signal(self, price, upper, middle, lower):
        if price <= lower * 1.005:
            return 'BUY'
        elif price >= upper * 0.995:
            return 'SELL'
        return 'NEUTRAL'
    
    def _calculate_ema(self, prices, period):
        return pd.Series(prices).ewm(span=period, adjust=False).mean().values
    
    def _trend_signal(self, ema9, ema21, prices):
        if ema9[-1] > ema21[-1] and prices[-1] > ema9[-1]:
            return 'BUY'
        elif ema9[-1] < ema21[-1] and prices[-1] < ema9[-1]:
            return 'SELL'
        return 'NEUTRAL'
    
    def _calculate_stochastic(self, highs, lows, closes, k_period=14, d_period=3):
        low_min = pd.Series(lows).rolling(window=k_period).min()
        high_max = pd.Series(highs).rolling(window=k_period).max()
        stoch_k = 100 * ((pd.Series(closes) - low_min) / (high_max - low_min))
        stoch_d = stoch_k.rolling(window=d_period).mean()
        return stoch_k.values, stoch_d.values
    
    def _stochastic_signal(self, stoch_k, stoch_d):
        if stoch_k[-1] < 20 and stoch_d[-1] < 20 and stoch_k[-1] > stoch_d[-1]:
            return 'BUY'
        elif stoch_k[-1] > 80 and stoch_d[-1] > 80 and stoch_k[-1] < stoch_d[-1]:
            return 'SELL'
        return 'NEUTRAL'
    
    def _calculate_atr(self, highs, lows, closes, period=14):
        tr1 = highs[1:] - lows[1:]
        tr2 = abs(highs[1:] - closes[:-1])
        tr3 = abs(lows[1:] - closes[:-1])
        tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return np.append([tr.iloc[0]], atr.values)
    
    def _detect_engulfing(self, opens, closes):
        if len(opens) < 3:
            return 'NEUTRAL'
        # Bullish Engulfing: green candle engulfs previous red candle
        if (closes[-1] > opens[-1] and 
            closes[-2] < opens[-2] and
            closes[-1] > opens[-2] and
            opens[-1] < closes[-2]):
            return 'BUY'
        # Bearish Engulfing: red candle engulfs previous green candle
        elif (closes[-1] < opens[-1] and 
              closes[-2] > opens[-2] and
              opens[-1] > closes[-2] and
              closes[-1] < opens[-2]):
            return 'SELL'
        return 'NEUTRAL'
    
    def _detect_hammer(self, opens, highs, lows, closes):
        if len(closes) < 2:
            return 'NEUTRAL'
        body = abs(closes[-1] - opens[-1])
        lower_shadow = min(opens[-1], closes[-1]) - lows[-1]
        upper_shadow = highs[-1] - max(opens[-1], closes[-1])
        # Hammer: small body, long lower shadow (2x body), small upper shadow
        if (lower_shadow > 2 * body and 
            upper_shadow < body * 0.3 and
            closes[-1] > opens[-1]):
            return 'BUY'
        # Hanging Man: same shape but in uptrend (bearish reversal)
        elif (lower_shadow > 2 * body and 
              upper_shadow < body * 0.3 and
              closes[-1] < opens[-1]):
            return 'SELL'
        return 'NEUTRAL'
    
    def _detect_doji(self, opens, closes):
        if abs(closes[-1] - opens[-1]) < (closes[-1] * 0.001):
            return 'DOJI'
        return 'NONE'
    
    def _find_support_resistance(self, highs, lows, closes):
        # Simple method: recent swing points
        if len(highs) < 20:
            return lows[-5:].min(), highs[-5:].max()
        # Support: recent low
        support = min(lows[-20:])
        # Resistance: recent high
        resistance = max(highs[-20:])
        return support, resistance
    
    def _detect_breakout(self, closes, upper, lower, support, resistance):
        if closes[-1] > resistance and closes[-2] <= resistance:
            return 'BUY'
        elif closes[-1] < support and closes[-2] >= support:
            return 'SELL'
        elif closes[-1] > upper[-1] and closes[-2] <= upper[-1]:
            return 'BUY'
        elif closes[-1] < lower[-1] and closes[-2] >= lower[-1]:
            return 'SELL'
        return 'NEUTRAL'
    
    def _detect_bounce(self, closes, support, resistance, rsi):
        if closes[-1] <= support * 1.005 and rsi[-1] < 40:
            return 'BUY'
        elif closes[-1] >= resistance * 0.995 and rsi[-1] > 60:
            return 'SELL'
        return 'NEUTRAL'
    
    async def scan_all_assets(self) -> List[Dict]:
        """مسح جميع الأصول مع تحليل متقدم"""
        try:
            async with httpx.AsyncClient() as client:
                markets = await client.get(f"{self.api_base}/api/v1/markets")
                assets = markets.json().get('data', [])
                
                signals = []
                for asset in assets:
                    if asset.get('is_active', False):
                        signal = await self.get_asset_analysis(asset['symbol'])
                        if signal:
                            signals.append(signal)
                # ترتيب حسب الثقة (الأقوى أولاً)
                signals.sort(key=lambda x: x['confidence'], reverse=True)
                return signals
        except Exception as e:
            print(f"❌ Error scanning assets: {e}")
            return []