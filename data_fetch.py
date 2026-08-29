import pandas as pd
import numpy as np
from datetime import datetime
import random

# سعر الافتتاح لكل زوج
BASE_PRICES = {
    "EURUSD": 1.0900,
    "GBPUSD": 1.2600,
    "USDJPY": 150.00,
    "CHFJPY": 165.00,
    "AUDUSD": 0.6500,
    "USDCAD": 1.3500,
    "BTCUSD": 65000,
    "ETHUSD": 3500,
    "USDTRY": 34.50,
    "EURTRY": 38.00,
    "GBPTRY": 44.00,
    "USDBDT": 120.00,
    "EURBDT": 130.00,
    "USDINR": 83.50,
    "EURINR": 90.00,
    "GBPINR": 105.00,
    "XAUUSD": 2400.00,
    "XAGUSD": 28.50,
}

def get_live_price(symbol="EURUSD"):
    """سعر حي يتحرك بشكل طبيعي"""
    base = BASE_PRICES.get(symbol, 1.0000)
    # حركة عشوائية طبيعية تشبه السوق الحقيقي
    change = np.random.normal(0, base * 0.0003)
    # إضافة موجات صغيرة
    wave = np.sin(datetime.now().timestamp() / 10 + hash(symbol)) * base * 0.0001
    return round(base + change + wave, 5)

def get_ohlc_data(symbol="EURUSD", interval='1min', outputsize=100):
    """توليد شموع محاكاة ذكية تشبه السوق الحقيقي"""
    np.random.seed(int(datetime.now().timestamp()) % 10000 + hash(symbol) % 1000)
    
    base = BASE_PRICES.get(symbol, 1.0000)
    
    candles = []
    current_price = base
    trend = np.random.choice([-1, 1]) * np.random.uniform(0.0002, 0.0015)
    volatility = np.random.uniform(0.0003, 0.002)
    
    for i in range(outputsize):
        # موجات سعرية واقعية
        wave1 = np.sin(i / np.random.randint(6, 15)) * np.random.uniform(0.001, 0.008)
        wave2 = np.cos(i / np.random.randint(10, 25)) * np.random.uniform(0.0005, 0.003)
        noise = np.random.normal(0, volatility)
        
        change = wave1 + wave2 + trend * (i / outputsize) + noise
        
        open_price = current_price
        close_price = open_price + change
        high_price = max(open_price, close_price) + abs(np.random.normal(0, volatility * 0.6))
        low_price = min(open_price, close_price) - abs(np.random.normal(0, volatility * 0.6))
        
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
    """قائمة الأزواج المتاحة (موسعة)"""
    return [
        # العملات الرئيسية
        {"symbol": "EURUSD", "name": "EUR/USD", "payout": 92},
        {"symbol": "GBPUSD", "name": "GBP/USD", "payout": 90},
        {"symbol": "USDJPY", "name": "USD/JPY", "payout": 88},
        {"symbol": "CHFJPY", "name": "CHF/JPY", "payout": 86},
        {"symbol": "AUDUSD", "name": "AUD/USD", "payout": 84},
        {"symbol": "USDCAD", "name": "USD/CAD", "payout": 82},
        # العملات التركية
        {"symbol": "USDTRY", "name": "USD/TRY", "payout": 80},
        {"symbol": "EURTRY", "name": "EUR/TRY", "payout": 78},
        {"symbol": "GBPTRY", "name": "GBP/TRY", "payout": 76},
        # العملات البنغلاديشية
        {"symbol": "USDBDT", "name": "USD/BDT", "payout": 74},
        {"symbol": "EURBDT", "name": "EUR/BDT", "payout": 72},
        # العملات الهندية
        {"symbol": "USDINR", "name": "USD/INR", "payout": 70},
        {"symbol": "EURINR", "name": "EUR/INR", "payout": 68},
        {"symbol": "GBPINR", "name": "GBP/INR", "payout": 66},
        # المعادن الثمينة
        {"symbol": "XAUUSD", "name": "الذهب XAU/USD", "payout": 64},
        {"symbol": "XAGUSD", "name": "الفضة XAG/USD", "payout": 62},
        # العملات المشفرة
        {"symbol": "BTCUSD", "name": "Bitcoin BTC/USD", "payout": 60},
        {"symbol": "ETHUSD", "name": "Ethereum ETH/USD", "payout": 58},
    ]