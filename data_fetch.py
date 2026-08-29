import requests
import pandas as pd
from config import TWELVE_DATA_API_KEY

def get_live_price(symbol="CHF/JPY"):
    """جلب السعر الحالي"""
    try:
        url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={TWELVE_DATA_API_KEY}"
        res = requests.get(url, timeout=10).json()
        return float(res.get('price', 0))
    except:
        return None

def get_ohlc_data(symbol="CHF/JPY", interval='1min', outputsize=100):
    """جلب بيانات الشموع"""
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize={outputsize}&apikey={TWELVE_DATA_API_KEY}"
        res = requests.get(url, timeout=10).json()
        
        values = res.get('values', [])
        if not values:
            return None
        
        df = pd.DataFrame(values)
        df = df.rename(columns={
            'datetime': 'timestamp',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close'
        })
        
        df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(float)
        df = df.sort_values(by='timestamp')
        df.reset_index(drop=True, inplace=True)
        
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def get_forex_pairs():
    """قائمة أزواج العملات المتاحة"""
    return [
        {"symbol": "EUR/USD", "name": "EUR/USD", "payout": 92},
        {"symbol": "GBP/USD", "name": "GBP/USD", "payout": 90},
        {"symbol": "USD/JPY", "name": "USD/JPY", "payout": 88},
        {"symbol": "CHF/JPY", "name": "CHF/JPY", "payout": 86},
        {"symbol": "AUD/USD", "name": "AUD/USD", "payout": 84},
        {"symbol": "USD/CAD", "name": "USD/CAD", "payout": 82},
        {"symbol": "BTC/USD", "name": "BTC/USD", "payout": 78},
        {"symbol": "ETH/USD", "name": "ETH/USD", "payout": 76},
    ]