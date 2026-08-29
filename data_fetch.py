import pandas as pd
import numpy as np
from datetime import datetime

def get_live_price(symbol="EURUSD"):
    """محاكاة سعر حي"""
    base_prices = {
        "EURUSD": 1.0900,
        "GBPUSD": 1.2600,
        "USDJPY": 150.00,
        "CHFJPY": 165.00,
        "AUDUSD": 0.6500,
        "USDCAD": 1.3500,
        "BTCUSD": 65000,
        "ETHUSD": 3500
    }
    base = base_prices.get(symbol, 1.0000)
    change = np.random.normal(0, 0.0005)
    return round(base + change, 5)

def get_ohlc_data(symbol="EURUSD", interval='1min', outputsize=100):
    """توليد شموع محاكاة ذكية"""
    # تعيين بذرة عشوائية ثابتة لكل رمز
    np.random.seed(int(datetime.now().timestamp()) % 10000 + hash(symbol) % 1000)
    
    base_prices = {
        "EURUSD": 1.0900,
        "GBPUSD": 1.2600,
        "USDJPY": 150.00,
        "CHFJPY": 165.00,
        "AUDUSD": 0.6500,
        "USDCAD": 1.3500,
        "BTCUSD": 65000,
        "ETHUSD": 3500
    }
    
    base = base_prices.get(symbol, 1.0000)
    
    candles = []
    current_price = base
    trend = np.random.choice([-1, 1]) * np.random.uniform(0.0002, 0.001)
    volatility = np.random.uniform(0.0003, 0.001)
    
    for i in range(outputsize):
        wave = np.sin(i / np.random.randint(8, 20)) * np.random.uniform(0.001, 0.005)
        noise = np.random.normal(0, volatility)
        change = wave + trend * (i / outputsize) + noise
        
        open_price = current_price
        close_price = open_price + change
        high_price = max(open_price, close_price) + abs(np.random.normal(0, volatility * 0.5))
        low_price = min(open_price, close_price) - abs(np.random.normal(0, volatility * 0.5))
        
        candles.append({
            'timestamp': datetime.now().isoformat(),
            'open': round(open_price, 5),
            'high': round(high_price, 5),
            'low': round(low_price, 5),
            'close': round(close_price, 5)
        })
        current_price = close_price
    
    df = pd.DataFrame(candles)
    df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(float)
    return df

def get_forex_pairs():
    """قائمة الأزواج المتاحة"""
    return [
        {"symbol": "EURUSD", "name": "EUR/USD", "payout": 92},
        {"symbol": "GBPUSD", "name": "GBP/USD", "payout": 90},
        {"symbol": "USDJPY", "name": "USD/JPY", "payout": 88},
        {"symbol": "CHFJPY", "name": "CHF/JPY", "payout": 86},
        {"symbol": "AUDUSD", "name": "AUD/USD", "payout": 84},
        {"symbol": "USDCAD", "name": "USD/CAD", "payout": 82},
        {"symbol": "BTCUSD", "name": "BTC/USD", "payout": 78},
        {"symbol": "ETHUSD", "name": "ETH/USD", "payout": 76},
    ]