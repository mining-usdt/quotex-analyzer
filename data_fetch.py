"""
جلب البيانات الحقيقية من Twelve Data API
مع بيانات احتياطية ذكية في حال فشل API
"""

import os
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# ===== مفتاح API =====
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "")

# ===== الأسعار الأساسية (احتياطية) =====
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

# ===== ذاكرة مؤقتة للبيانات =====
_cache = {}
_cache_time = {}

def _is_cache_valid(key: str, max_age: int = 30) -> bool:
    """التحقق من صلاحية الذاكرة المؤقتة"""
    if key not in _cache_time:
        return False
    return (time.time() - _cache_time[key]) < max_age

def get_live_price(symbol: str) -> float:
    """جلب السعر الحي من Twelve Data"""
    cache_key = f"price_{symbol}"
    
    # استخدام الذاكرة المؤقتة
    if _is_cache_valid(cache_key, 5):
        return _cache[cache_key]
    
    try:
        if TWELVE_DATA_API_KEY:
            url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={TWELVE_DATA_API_KEY}"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if "price" in data:
                    price = float(data["price"])
                    _cache[cache_key] = price
                    _cache_time[cache_key] = time.time()
                    return price
    except Exception as e:
        print(f"⚠️ فشل جلب السعر الحي لـ {symbol}: {e}")
    
    # الرجوع إلى السعر المخزن
    return BASE_PRICES.get(symbol, 1.0)

def get_ohlc_data(symbol: str, interval: str = "1min", outputsize: int = 200) -> Optional[pd.DataFrame]:
    """جلب شموع حقيقية من Twelve Data"""
    cache_key = f"ohlc_{symbol}_{interval}_{outputsize}"
    
    # استخدام الذاكرة المؤقتة (30 ثانية)
    if _is_cache_valid(cache_key, 30):
        return _cache[cache_key].copy()
    
    try:
        if TWELVE_DATA_API_KEY:
            url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize={outputsize}&apikey={TWELVE_DATA_API_KEY}"
            resp = requests.get(url, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                if "values" in data and len(data["values"]) > 0:
                    df = pd.DataFrame(data["values"])
                    df["datetime"] = pd.to_datetime(df["datetime"])
                    df = df.rename(columns={
                        "open": "open",
                        "high": "high",
                        "low": "low",
                        "close": "close"
                    })
                    df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].astype(float)
                    df = df.sort_values("datetime")
                    
                    _cache[cache_key] = df.copy()
                    _cache_time[cache_key] = time.time()
                    return df
    except Exception as e:
        print(f"⚠️ فشل جلب البيانات لـ {symbol}: {e}")
    
    # بيانات احتياطية ذكية
    df = _generate_fallback_data(symbol, outputsize)
    _cache[cache_key] = df.copy()
    _cache_time[cache_key] = time.time()
    return df

def _generate_fallback_data(symbol: str, outputsize: int) -> pd.DataFrame:
    """توليد بيانات احتياطية تشبه السوق الحقيقي (ذكية)"""
    base = BASE_PRICES.get(symbol, 1.0)
    seed = int(time.time() * 1000) % 100000 + hash(symbol) % 1000
    np.random.seed(seed)
    
    candles = []
    price = base
    trend_direction = np.random.choice([-1, 1])
    trend_strength = np.random.uniform(0.0001, 0.001)
    volatility = np.random.uniform(0.0003, 0.002)
    
    # توليد موجات سعرية
    for i in range(outputsize):
        # موجات سعرية طبيعية
        wave1 = np.sin(i / np.random.uniform(6, 15)) * np.random.uniform(0.001, 0.008)
        wave2 = np.cos(i / np.random.uniform(10, 25)) * np.random.uniform(0.0005, 0.003)
        noise = np.random.normal(0, volatility)
        trend = trend_direction * trend_strength * (i / outputsize)
        
        change = wave1 + wave2 + trend + noise
        
        open_price = price
        close_price = open_price + change
        high_price = max(open_price, close_price) + abs(np.random.normal(0, volatility * 0.6))
        low_price = min(open_price, close_price) - abs(np.random.normal(0, volatility * 0.6))
        
        candles.append({
            "datetime": (datetime.now() - timedelta(minutes=outputsize - i)).isoformat(),
            "open": round(open_price, 5),
            "high": round(high_price, 5),
            "low": round(low_price, 5),
            "close": round(close_price, 5)
        })
        price = close_price
    
    df = pd.DataFrame(candles)
    df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].astype(float)
    return df

def get_forex_pairs() -> List[Dict[str, Any]]:
    """قائمة الأزواج المتاحة للتداول"""
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
        # العملات الهندية
        {"symbol": "USDINR", "name": "USD/INR", "payout": 74},
        {"symbol": "EURINR", "name": "EUR/INR", "payout": 72},
        {"symbol": "GBPINR", "name": "GBP/INR", "payout": 70},
        # المعادن الثمينة
        {"symbol": "XAUUSD", "name": "الذهب XAU/USD", "payout": 68},
        {"symbol": "XAGUSD", "name": "الفضة XAG/USD", "payout": 66},
        # العملات المشفرة
        {"symbol": "BTCUSD", "name": "Bitcoin BTC/USD", "payout": 64},
        {"symbol": "ETHUSD", "name": "Ethereum ETH/USD", "payout": 62},
        # العملات البنغلاديشية
        {"symbol": "USDBDT", "name": "USD/BDT", "payout": 60},
        {"symbol": "EURBDT", "name": "EUR/BDT", "payout": 58},
    ]

def clear_cache():
    """مسح الذاكرة المؤقتة"""
    global _cache, _cache_time
    _cache = {}
    _cache_time = {}