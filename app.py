from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime
import pandas as pd
import numpy as np
from data_fetch import get_ohlc_data, get_live_price, get_forex_pairs
from signal_engine import SignalEngine

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== خدمة الملفات الثابتة =====

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """تقديم الصفحة الرئيسية"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return {"error": "index.html not found"}

@app.get("/style.css", response_class=FileResponse)
async def serve_css():
    """تقديم ملف CSS"""
    try:
        return FileResponse("style.css")
    except FileNotFoundError:
        return {"error": "style.css not found"}

@app.get("/script.js", response_class=FileResponse)
async def serve_js():
    """تقديم ملف JavaScript"""
    try:
        return FileResponse("script.js")
    except FileNotFoundError:
        return {"error": "script.js not found"}

# ===== نقاط النهاية API =====

@app.get("/api/v1/markets")
async def get_markets():
    """قائمة الأزواج المتاحة"""
    return {"status": "success", "data": get_forex_pairs()}

@app.get("/api/v2/analyze/{symbol}")
async def analyze_symbol(symbol: str, limit: int = Query(100, ge=30, le=500)):
    """تحليل حقيقي باستخدام Twelve Data API"""
    try:
        df = get_ohlc_data(symbol, '1min', limit)
        if df is None:
            return {"error": f"Could not fetch data for {symbol}"}
        
        signal = SignalEngine.generate_signal(df)
        if "error" in signal:
            raise HTTPException(status_code=400, detail=signal["error"])
        
        price = get_live_price(symbol)
        
        signal["symbol"] = symbol
        signal["current_price"] = price or signal["current_price"]
        signal["timestamp"] = datetime.now().isoformat()
        
        return signal
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v2/strong-signal")
async def get_strong_signal():
    """البحث عن أقوى إشارة في جميع الأزواج"""
    pairs = get_forex_pairs()
    best = None
    best_confidence = 0
    
    for pair in pairs:
        try:
            result = await analyze_symbol(pair["symbol"].replace("/", ""))
            if result and result["action"] in ["STRONG_BUY", "STRONG_SELL"] and result["confidence"] > best_confidence:
                best = result
                best_confidence = result["confidence"]
        except:
            continue
    
    if best:
        return {"status": "success", "signal": best}
    return {"status": "no_strong_signal", "message": "No strong signals found"}

@app.get("/health")
async def health():
    """فحص صحة السيرفر"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}