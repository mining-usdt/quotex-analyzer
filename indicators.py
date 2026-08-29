import pandas as pd
import numpy as np

class AdvancedIndicators:
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
    def calculate_bollinger(prices, period=20):
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
    def calculate_ema(prices, period):
        if len(prices) < period:
            return prices[-1] if len(prices) > 0 else 0
        return float(pd.Series(prices).ewm(span=period, adjust=False).mean().iloc[-1])

    @staticmethod
    def calculate_sma(prices, period=20):
        if len(prices) < period:
            return prices[-1] if len(prices) > 0 else 0
        return float(pd.Series(prices).rolling(window=period).mean().iloc[-1])

    @staticmethod
    def calculate_stochastic(highs, lows, closes):
        if len(closes) < 14:
            return {"k": 50, "d": 50}
        low_min = pd.Series(lows).rolling(window=14).min()
        high_max = pd.Series(highs).rolling(window=14).max()
        stoch_k = 100 * ((pd.Series(closes) - low_min) / (high_max - low_min))
        stoch_d = stoch_k.rolling(window=3).mean()
        return {
            "k": float(stoch_k.iloc[-1]),
            "d": float(stoch_d.iloc[-1])
        }

    @staticmethod
    def calculate_atr(highs, lows, closes, period=14):
        if len(closes) < period + 1:
            return 0.001
        tr1 = np.array(highs[1:]) - np.array(lows[1:])
        tr2 = abs(np.array(highs[1:]) - np.array(closes[:-1]))
        tr3 = abs(np.array(lows[1:]) - np.array(closes[:-1]))
        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        return float(pd.Series(tr).rolling(window=period).mean().iloc[-1])