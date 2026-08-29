"""
المؤشرات الفنية المتقدمة
15 مؤشراً مختلفاً للتحليل الفني
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

class AdvancedIndicators:
    """فئة تحتوي على جميع المؤشرات الفنية"""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
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
    def calculate_rsi_array(prices: List[float], period: int = 14) -> List[float]:
        """مؤشر القوة النسبية RSI كقائمة"""
        if len(prices) < period + 1:
            return [50.0] * len(prices)
        
        delta = np.diff(prices)
        gain = (delta > 0) * delta
        loss = (delta < 0) * -delta
        
        avg_gain = pd.Series(gain).rolling(window=period).mean()
        avg_loss = pd.Series(loss).rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return [float(x) if not pd.isna(x) else 50.0 for x in rsi]
    
    @staticmethod
    def calculate_macd(prices: List[float]) -> Dict[str, float]:
        """مؤشر MACD"""
        if len(prices) < 26:
            return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}
        
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
    def calculate_bollinger(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, Optional[float]]:
        """مؤشر بولينجر باند"""
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
    def calculate_ema(prices: List[float], period: int) -> float:
        """المتوسط المتحرك الأسي EMA"""
        if len(prices) < period:
            return prices[-1] if len(prices) > 0 else 0.0
        return float(pd.Series(prices).ewm(span=period, adjust=False).mean().iloc[-1])
    
    @staticmethod
    def calculate_ema_array(prices: List[float], period: int) -> List[float]:
        """المتوسط المتحرك الأسي EMA كقائمة"""
        if len(prices) < period:
            return [prices[-1]] * len(prices) if prices else []
        
        ema = pd.Series(prices).ewm(span=period, adjust=False).mean()
        return [float(x) for x in ema]
    
    @staticmethod
    def calculate_sma(prices: List[float], period: int = 20) -> float:
        """المتوسط المتحرك البسيط SMA"""
        if len(prices) < period:
            return prices[-1] if len(prices) > 0 else 0.0
        return float(pd.Series(prices).rolling(window=period).mean().iloc[-1])
    
    @staticmethod
    def calculate_sma_array(prices: List[float], period: int = 20) -> List[float]:
        """المتوسط المتحرك البسيط SMA كقائمة"""
        if len(prices) < period:
            return [prices[-1]] * len(prices) if prices else []
        
        sma = pd.Series(prices).rolling(window=period).mean()
        return [float(x) if not pd.isna(x) else prices[i] for i, x in enumerate(sma)]
    
    @staticmethod
    def calculate_stochastic(highs: List[float], lows: List[float], closes: List[float]) -> Dict[str, float]:
        """مؤشر ستوكاستيك"""
        if len(closes) < 14:
            return {"k": 50.0, "d": 50.0}
        
        low_min = pd.Series(lows).rolling(window=14).min()
        high_max = pd.Series(highs).rolling(window=14).max()
        stoch_k = 100 * ((pd.Series(closes) - low_min) / (high_max - low_min))
        stoch_d = stoch_k.rolling(window=3).mean()
        
        return {
            "k": float(stoch_k.iloc[-1]) if not stoch_k.empty else 50.0,
            "d": float(stoch_d.iloc[-1]) if not stoch_d.empty else 50.0
        }
    
    @staticmethod
    def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        """مؤشر متوسط المدى الحقيقي ATR"""
        if len(closes) < period + 1:
            return 0.001
        
        tr1 = np.array(highs[1:]) - np.array(lows[1:])
        tr2 = abs(np.array(highs[1:]) - np.array(closes[:-1]))
        tr3 = abs(np.array(lows[1:]) - np.array(closes[:-1]))
        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        
        return float(pd.Series(tr).rolling(window=period).mean().iloc[-1]) if len(tr) >= period else 0.001
    
    @staticmethod
    def calculate_adx(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        """مؤشر متوسط الاتجاه ADX"""
        if len(closes) < period + 1:
            return 0.0
        
        # حساب True Range
        tr1 = np.array(highs[1:]) - np.array(lows[1:])
        tr2 = abs(np.array(highs[1:]) - np.array(closes[:-1]))
        tr3 = abs(np.array(lows[1:]) - np.array(closes[:-1]))
        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        
        # حساب Directional Movements
        up_move = np.array(highs[1:]) - np.array(highs[:-1])
        down_move = np.array(lows[:-1]) - np.array(lows[1:])
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        # حساب Smoothing
        atr = pd.Series(tr).rolling(window=period).mean()
        plus_di = 100 * (pd.Series(plus_dm).rolling(window=period).mean() / atr)
        minus_di = 100 * (pd.Series(minus_dm).rolling(window=period).mean() / atr)
        
        # حساب DX و ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return float(adx.iloc[-1]) if not adx.empty else 0.0
    
    @staticmethod
    def calculate_ichimoku(highs: List[float], lows: List[float]) -> Dict[str, float]:
        """مؤشر إيشيموكو"""
        if len(highs) < 52:
            return {"tenkan": 0.0, "kijun": 0.0, "senkou_a": 0.0, "senkou_b": 0.0}
        
        # Tenkan-sen (Conversion Line)
        tenkan_high = max(highs[-9:])
        tenkan_low = min(lows[-9:])
        tenkan = (tenkan_high + tenkan_low) / 2
        
        # Kijun-sen (Base Line)
        kijun_high = max(highs[-26:])
        kijun_low = min(lows[-26:])
        kijun = (kijun_high + kijun_low) / 2
        
        # Senkou Span A
        senkou_a = (tenkan + kijun) / 2
        
        # Senkou Span B
        senkou_b_high = max(highs[-52:])
        senkou_b_low = min(lows[-52:])
        senkou_b = (senkou_b_high + senkou_b_low) / 2
        
        return {
            "tenkan": tenkan,
            "kijun": kijun,
            "senkou_a": senkou_a,
            "senkou_b": senkou_b
        }
    
    @staticmethod
    def calculate_mfi(highs: List[float], lows: List[float], closes: List[float], volumes: List[float], period: int = 14) -> float:
        """مؤشر التدفق النقدي MFI"""
        if len(closes) < period + 1:
            return 50.0
        
        # Typical Price
        typical = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
        
        # Money Flow
        money_flow = [t * v for t, v in zip(typical, volumes)]
        
        positive_flow = []
        negative_flow = []
        
        for i in range(1, len(typical)):
            if typical[i] > typical[i-1]:
                positive_flow.append(money_flow[i])
                negative_flow.append(0)
            else:
                positive_flow.append(0)
                negative_flow.append(money_flow[i])
        
        # حساب MFI
        if len(positive_flow) < period:
            return 50.0
        
        pos_sum = sum(positive_flow[-period:])
        neg_sum = sum(negative_flow[-period:])
        
        if neg_sum == 0:
            return 100.0
        
        mfi = 100 - (100 / (1 + pos_sum / neg_sum))
        return float(mfi)
    
    @staticmethod
    def calculate_cci(highs: List[float], lows: List[float], closes: List[float], period: int = 20) -> float:
        """مؤشر قناة السلع CCI"""
        if len(closes) < period + 1:
            return 0.0
        
        # Typical Price
        typical = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
        
        # SMA of Typical Price
        sma = sum(typical[-period:]) / period
        
        # Mean Deviation
        deviations = [abs(t - sma) for t in typical[-period:]]
        mean_dev = sum(deviations) / period
        
        if mean_dev == 0:
            return 0.0
        
        cci = (typical[-1] - sma) / (0.015 * mean_dev)
        return float(cci)
    
    @staticmethod
    def calculate_obv(closes: List[float], volumes: List[float]) -> float:
        """مؤشر توازن الحجم OBV"""
        if len(closes) < 2:
            return 0.0
        
        obv = 0
        for i in range(1, len(closes)):
            if closes[i] > closes[i-1]:
                obv += volumes[i]
            elif closes[i] < closes[i-1]:
                obv -= volumes[i]
        
        return float(obv)