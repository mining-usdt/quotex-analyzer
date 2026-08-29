import pandas as pd
import numpy as np

class TechnicalIndicators:
    @staticmethod
    def calculate_rsi(prices, period=14):
        """حساب مؤشر القوة النسبية RSI"""
        delta = np.diff(prices)
        gain = (delta > 0) * delta
        loss = (delta < 0) * -delta
        
        avg_gain = pd.Series(gain).rolling(window=period).mean()
        avg_loss = pd.Series(loss).rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not rsi.empty else 50

    @staticmethod
    def calculate_macd(prices, fast=12, slow=26, signal=9):
        """حساب مؤشر MACD"""
        exp1 = pd.Series(prices).ewm(span=fast, adjust=False).mean()
        exp2 = pd.Series(prices).ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return {
            'macd': macd.iloc[-1],
            'signal': signal_line.iloc[-1],
            'histogram': histogram.iloc[-1]
        }

    @staticmethod
    def calculate_bollinger_bands(prices, period=20, std_dev=2):
        """حساب نطاقات بولينجر"""
        sma = pd.Series(prices).rolling(window=period).mean()
        std = pd.Series(prices).rolling(window=period).std()
        return {
            'upper': (sma + std * std_dev).iloc[-1],
            'middle': sma.iloc[-1],
            'lower': (sma - std * std_dev).iloc[-1]
        }

    @staticmethod
    def generate_signal(candles):
        """توليد إشارة تداول متكاملة"""
        closes = [c['close'] for c in candles]
        
        rsi = TechnicalIndicators.calculate_rsi(closes)
        macd_data = TechnicalIndicators.calculate_macd(closes)
        bb = TechnicalIndicators.calculate_bollinger_bands(closes)
        
        signal = {
            'action': 'NEUTRAL',
            'confidence': 0,
            'rsi': rsi,
            'macd': macd_data,
            'bollinger': bb,
            'price': closes[-1]
        }
        
        # منطق توليد الإشارة
        if rsi < 30 and macd_data['histogram'] > 0:
            signal['action'] = 'BUY'
            signal['confidence'] = 85
        elif rsi > 70 and macd_data['histogram'] < 0:
            signal['action'] = 'SELL'
            signal['confidence'] = 85
        elif closes[-1] <= bb['lower'] and macd_data['histogram'] > 0:
            signal['action'] = 'BUY'
            signal['confidence'] = 70
        elif closes[-1] >= bb['upper'] and macd_data['histogram'] < 0:
            signal['action'] = 'SELL'
            signal['confidence'] = 70
            
        return signal