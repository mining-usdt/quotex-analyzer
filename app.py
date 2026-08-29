from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
import os
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import random
import time
import asyncio
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# ===== تحميل المتغيرات =====
load_dotenv()

# ===== استيراد الملفات المحلية =====
from data_fetch import get_ohlc_data, get_live_price, get_forex_pairs
from signal_engine import SignalEngine
from risk_manager import RiskManager
from quotex_client import QuotexClient

# ===== تهيئة التطبيق =====
app = FastAPI(
    title="🔥 Quotex OTC Auto Trader ULTIMATE",
    description="نظام تحليل وتنفيذ تلقائي مع إدارة مخاطر صارمة",
    version="6.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== إعدادات من .env =====
QX_EMAIL = os.getenv("QX_EMAIL", "")
QX_PASSWORD = os.getenv("QX_PASSWORD", "")
QX_ACCOUNT = os.getenv("QX_ACCOUNT", "PRACTICE")
QX_RISK_PERCENT = float(os.getenv("QX_RISK_PERCENT", 1.0))
QX_DAILY_LOSS_LIMIT = float(os.getenv("QX_DAILY_LOSS_LIMIT", 10.0))
QX_MIN_CONFIDENCE = int(os.getenv("QX_MIN_CONFIDENCE", 85))

# ===== متغيرات عالمية =====
quotex_client = None
risk_manager = RiskManager(QX_RISK_PERCENT, QX_DAILY_LOSS_LIMIT)
is_trading_enabled = False
trading_log = []
last_signal = None

# ===== ===== ===== ===== ===== ===== ===== =====
# ===== نقاط النهاية API =====
# ===== ===== ===== ===== ===== ===== ===== =====

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except:
        return HTMLResponse(content="<h1>index.html not found</h1>")

@app.get("/style.css", response_class=FileResponse)
async def serve_css():
    return FileResponse("style.css")

@app.get("/script.js", response_class=FileResponse)
async def serve_js():
    return FileResponse("script.js")

# ===== 1. الأزواج =====
@app.get("/api/v1/markets")
async def get_markets():
    return {"status": "success", "data": get_forex_pairs()}

# ===== 2. التحليل =====
@app.get("/api/v2/analyze/{symbol}")
async def analyze_symbol(symbol: str, limit: int = Query(200, ge=30, le=500)):
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
        
        # تخزين الإشارة الأخيرة
        global last_signal
        last_signal = signal
        
        return signal
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== 3. البحث عن إشارة قوية =====
@app.get("/api/v2/strong-signal")
async def get_strong_signal(symbol: str = Query(None)):
    if not symbol:
        return {"status": "error", "message": "الرجاء اختيار زوج"}
    
    try:
        result = await analyze_symbol(symbol)
        if result and result["action"] in ["STRONG_BUY", "STRONG_SELL", "BUY", "SELL"]:
            return {"status": "success", "signal": result}
        return {"status": "no_signal", "message": "لا توجد إشارات قوية"}
    except:
        return {"status": "error", "message": "خطأ في التحليل"}

# ===== 4. حالة النظام =====
@app.get("/api/v2/status")
async def get_status():
    global is_trading_enabled, quotex_client, trading_log
    
    balance = 0
    if quotex_client and quotex_client.is_connected:
        balance = await quotex_client.get_balance()
    
    return {
        "status": "online",
        "trading_enabled": is_trading_enabled,
        "connected": quotex_client.is_connected if quotex_client else False,
        "balance": balance,
        "account_type": QX_ACCOUNT,
        "risk_percent": QX_RISK_PERCENT,
        "daily_loss_limit": QX_DAILY_LOSS_LIMIT,
        "daily_loss": risk_manager.daily_loss if risk_manager else 0,
        "min_confidence": QX_MIN_CONFIDENCE,
        "logs": trading_log[-10:] if trading_log else []
    }

# ===== 5. تفعيل التداول =====
@app.post("/api/v2/enable-trading")
async def enable_trading(background_tasks: BackgroundTasks):
    global is_trading_enabled, quotex_client
    
    if not QX_EMAIL or not QX_PASSWORD:
        return {"status": "error", "message": "بيانات الدخول غير مكتملة في .env"}
    
    try:
        quotex_client = QuotexClient(QX_EMAIL, QX_PASSWORD, QX_ACCOUNT)
        await quotex_client.connect()
        is_trading_enabled = True
        
        # بدء التداول في الخلفية
        background_tasks.add_task(auto_trade_loop)
        
        return {
            "status": "success",
            "message": f"✅ تم تفعيل التداول على حساب {QX_ACCOUNT}",
            "balance": await quotex_client.get_balance()
        }
    except Exception as e:
        return {"status": "error", "message": f"فشل التفعيل: {str(e)}"}

# ===== 6. إيقاف التداول =====
@app.post("/api/v2/disable-trading")
async def disable_trading():
    global is_trading_enabled, quotex_client
    is_trading_enabled = False
    
    if quotex_client:
        await quotex_client.disconnect()
        quotex_client = None
    
    return {"status": "success", "message": "⏹️ تم إيقاف التداول"}

# ===== 7. سجل الصفقات =====
@app.get("/api/v2/logs")
async def get_logs(limit: int = 20):
    global trading_log
    return {"logs": trading_log[-limit:] if trading_log else []}

# ===== 8. إعادة تعيين الإحصائيات اليومية =====
@app.post("/api/v2/reset-daily")
async def reset_daily():
    global risk_manager
    risk_manager.reset_daily_stats()
    return {"status": "success", "message": "✅ تم إعادة تعيين الإحصائيات اليومية"}

# ===== ===== ===== ===== ===== ===== ===== =====
# ===== دالة التداول التلقائي (تعمل في الخلفية) =====
# ===== ===== ===== ===== ===== ===== ===== =====

async def auto_trade_loop():
    global is_trading_enabled, quotex_client, trading_log, last_signal
    
    # قائمة الأزواج التي سيتم مراقبتها
    pairs = [p["symbol"] for p in get_forex_pairs()[:10]]  # أول 10 أزواج
    
    while is_trading_enabled:
        try:
            for symbol in pairs:
                if not is_trading_enabled:
                    break
                
                # 1. تحليل الزوج
                df = get_ohlc_data(symbol, '1min', 200)
                if df is None:
                    continue
                
                signal = SignalEngine.generate_signal(df)
                if "error" in signal:
                    continue
                
                # 2. جلب السعر الحالي
                price = get_live_price(symbol)
                signal["symbol"] = symbol
                signal["current_price"] = price or signal["current_price"]
                signal["timestamp"] = datetime.now().isoformat()
                
                last_signal = signal
                
                # 3. التحقق من قوة الإشارة
                action = signal.get("action", "NEUTRAL")
                confidence = signal.get("confidence", 0)
                
                # 4. التحقق من إمكانية التداول
                if action not in ["STRONG_BUY", "STRONG_SELL", "BUY", "SELL"]:
                    continue
                
                if confidence < QX_MIN_CONFIDENCE:
                    continue
                
                # 5. جلب الرصيد
                balance = await quotex_client.get_balance()
                if balance < 5.0:
                    log_message = f"⚠️ {symbol}: الرصيد منخفض (${balance})"
                    trading_log.append(log_message)
                    continue
                
                # 6. التحقق من إدارة المخاطر
                risk_check = risk_manager.can_trade(balance, confidence, QX_MIN_CONFIDENCE)
                if not risk_check["allowed"]:
                    log_message = f"⛔ {symbol}: {risk_check['reason']}"
                    trading_log.append(log_message)
                    continue
                
                # 7. تنفيذ الصفقة
                position_size = risk_check["position_size"]
                direction = "CALL" if "BUY" in action else "PUT"
                
                log_message = (
                    f"📊 {symbol} | {direction} | ${position_size} | "
                    f"الثقة: {confidence}% | الوقت: {signal.get('time_remaining_minutes', 0)} دقيقة"
                )
                trading_log.append(log_message)
                
                # تنفيذ الصفقة
                trade_result = await quotex_client.execute_trade(
                    symbol=symbol,
                    direction=action,
                    amount=position_size,
                    expiry=60
                )
                
                if trade_result.get("success"):
                    log_message = f"✅ {symbol}: تم تنفيذ {direction} بمبلغ ${position_size}"
                    trading_log.append(log_message)
                    
                    # تسجيل الصفقة
                    risk_manager.record_trade(0)  # سجل الصفقة
                else:
                    log_message = f"❌ {symbol}: فشل التنفيذ - {trade_result.get('error', 'Unknown error')}"
                    trading_log.append(log_message)
                
                # تأخير 5 ثواني بين الصفقات
                await asyncio.sleep(5)
            
            # انتظار 30 ثانية قبل الدورة التالية
            await asyncio.sleep(30)
            
        except Exception as e:
            log_message = f"⚠️ خطأ في التداول: {str(e)}"
            trading_log.append(log_message)
            await asyncio.sleep(10)

# ===== ===== ===== ===== ===== ===== ===== =====
# ===== التشغيل =====
# ===== ===== ===== ===== ===== ===== ===== =====

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "6.0.0",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("API_PORT", 8000)))