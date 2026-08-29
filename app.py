"""
السيرفر الرئيسي لنظام التحليل والتنفيذ التلقائي على Quotex
النسخة النهائية - لا تعدل فيها
"""

import os
import json
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# ===== تحميل المتغيرات =====
load_dotenv()

# ===== استيراد الملفات المحلية =====
from data_fetch import get_ohlc_data, get_live_price, get_forex_pairs
from signal_engine import SignalEngine
from indicators import AdvancedIndicators
from risk_manager import RiskManager
from quotex_client import QuotexClient

# ===== تهيئة التطبيق =====
app = FastAPI(
    title="🔥 Quotex OTC Auto Trader ULTIMATE",
    description="نظام تحليل وتنفيذ تلقائي مع إدارة مخاطر صارمة",
    version="7.0.0"
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
QX_SSID = os.getenv("QX_SSID", "")
QX_ACCOUNT = os.getenv("QX_ACCOUNT", "PRACTICE")
QX_RISK_PERCENT = float(os.getenv("QX_RISK_PERCENT", 1.0))
QX_DAILY_LOSS_LIMIT = float(os.getenv("QX_DAILY_LOSS_LIMIT", 10.0))
QX_MIN_CONFIDENCE = int(os.getenv("QX_MIN_CONFIDENCE", 85))
QX_DEFAULT_EXPIRY = int(os.getenv("QX_DEFAULT_EXPIRY", 60))

# ===== متغيرات عالمية =====
quotex_client = None
risk_manager = RiskManager(QX_RISK_PERCENT, QX_DAILY_LOSS_LIMIT)
is_trading_enabled = False
trading_log = []
last_analysis = None
last_trade_result = None
connection_status = {
    "connected": False,
    "account_type": "demo",
    "balance": 0.0,
    "last_update": None
}
auto_trade_task = None

# ============================================================
# ===== نقاط النهاية API =====
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """تقديم الصفحة الرئيسية"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>index.html not found</h1>")

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

# ============================================================
# ===== 1. الأزواج =====
# ============================================================

@app.get("/api/v1/markets")
async def get_markets():
    """قائمة الأزواج المتاحة"""
    return {"status": "success", "data": get_forex_pairs()}

# ============================================================
# ===== 2. التحليل =====
# ============================================================

@app.get("/api/v2/analyze/{symbol}")
async def analyze_symbol(
    symbol: str,
    limit: int = Query(200, ge=30, le=500)
):
    """تحليل متقدم لزوج معين"""
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
        
        global last_analysis
        last_analysis = signal
        
        return signal
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# ===== 3. البحث عن إشارة قوية =====
# ============================================================

@app.get("/api/v2/strong-signal")
async def get_strong_signal(
    symbol: str = Query(None, description="رمز الزوج")
):
    """البحث عن إشارة قوية في زوج محدد"""
    if not symbol:
        return {"status": "error", "message": "الرجاء اختيار زوج"}
    
    try:
        result = await analyze_symbol(symbol)
        if result and result.get("action") in ["STRONG_BUY", "STRONG_SELL", "BUY", "SELL"]:
            if result.get("confidence", 0) >= QX_MIN_CONFIDENCE:
                return {"status": "success", "signal": result}
        return {"status": "no_signal", "message": "لا توجد إشارات قوية"}
    except:
        return {"status": "error", "message": "خطأ في التحليل"}

# ============================================================
# ===== 4. حالة النظام =====
# ============================================================

@app.get("/api/v2/status")
async def get_status():
    """حالة النظام الكاملة"""
    global connection_status, is_trading_enabled, trading_log
    
    if quotex_client and quotex_client.is_connected:
        try:
            balance = await quotex_client.get_balance()
            connection_status["balance"] = balance
            connection_status["last_update"] = datetime.now().isoformat()
        except:
            pass
    
    return {
        "status": "online",
        "trading_enabled": is_trading_enabled,
        "connected": quotex_client.is_connected if quotex_client else False,
        "account_type": connection_status["account_type"],
        "balance": connection_status["balance"],
        "risk_percent": QX_RISK_PERCENT,
        "daily_loss_limit": QX_DAILY_LOSS_LIMIT,
        "daily_loss": risk_manager.daily_loss if risk_manager else 0,
        "min_confidence": QX_MIN_CONFIDENCE,
        "logs": trading_log[-20:] if trading_log else [],
        "last_trade": last_trade_result
    }

# ============================================================
# ===== 5. الاتصال بـ Quotex =====
# ============================================================

@app.post("/api/v2/connect")
async def connect_to_quotex(
    account_type: str = Query("demo", description="نوع الحساب: demo أو real")
):
    """الاتصال بـ Quotex"""
    global quotex_client, connection_status
    
    if quotex_client and quotex_client.is_connected:
        return {"status": "already_connected", "message": "✅ تم الاتصال بالفعل"}
    
    try:
        is_demo = account_type.lower() == "demo"
        quotex_client = QuotexClient(
            email=QX_EMAIL,
            password=QX_PASSWORD,
            ssid=QX_SSID,
            is_demo=is_demo
        )
        
        connected = await quotex_client.connect()
        
        if connected:
            connection_status["connected"] = True
            connection_status["account_type"] = "demo" if is_demo else "real"
            connection_status["balance"] = await quotex_client.get_balance()
            connection_status["last_update"] = datetime.now().isoformat()
            
            return {
                "status": "success",
                "message": f"✅ تم الاتصال بحساب {connection_status['account_type']}",
                "balance": connection_status["balance"]
            }
        else:
            return {
                "status": "error",
                "message": f"❌ فشل الاتصال: {quotex_client.last_error}"
            }
            
    except Exception as e:
        return {"status": "error", "message": f"❌ خطأ: {str(e)}"}

# ============================================================
# ===== 6. قطع الاتصال =====
# ============================================================

@app.post("/api/v2/disconnect")
async def disconnect_from_quotex():
    """قطع الاتصال بـ Quotex"""
    global quotex_client, connection_status, is_trading_enabled
    
    is_trading_enabled = False
    connection_status["connected"] = False
    
    if quotex_client:
        await quotex_client.disconnect()
        quotex_client = None
    
    return {"status": "success", "message": "⏹️ تم قطع الاتصال"}

# ============================================================
# ===== 7. تفعيل التداول التلقائي =====
# ============================================================

@app.post("/api/v2/enable-trading")
async def enable_trading(
    bg_tasks: BackgroundTasks,
    symbol: str = Query(..., description="رمز الزوج")
):
    """تفعيل التداول التلقائي لزوج معين"""
    global is_trading_enabled, auto_trade_task, last_trade_result
    
    if not quotex_client or not quotex_client.is_connected:
        return {"status": "error", "message": "❌ غير متصل بـ Quotex"}
    
    if is_trading_enabled:
        return {"status": "already_running", "message": "⏳ التداول مفعل بالفعل"}
    
    is_trading_enabled = True
    bg_tasks.add_task(auto_trade_loop, symbol)
    
    return {
        "status": "success",
        "message": f"✅ تم تفعيل التداول التلقائي على {symbol}",
        "symbol": symbol
    }
# ============================================================
# ===== 8. إيقاف التداول التلقائي =====
# ============================================================

@app.post("/api/v2/disable-trading")
async def disable_trading():
    """إيقاف التداول التلقائي"""
    global is_trading_enabled
    is_trading_enabled = False
    return {"status": "success", "message": "⏹️ تم إيقاف التداول التلقائي"}

# ============================================================
# ===== 9. تنفيذ صفقة يدوية =====
# ============================================================

@app.post("/api/v2/execute-trade")
async def execute_manual_trade(
    symbol: str = Query(..., description="رمز الزوج"),
    direction: str = Query(..., description="الاتجاه: CALL أو PUT"),
    amount: float = Query(..., description="المبلغ"),
    expiry: int = Query(60, description="المدة بالثواني")
):
    """تنفيذ صفقة يدوية"""
    global last_trade_result
    
    if not quotex_client or not quotex_client.is_connected:
        return {"status": "error", "message": "❌ غير متصل بـ Quotex"}
    
    try:
        result = await quotex_client.execute_trade(symbol, direction, amount, expiry)
        last_trade_result = result
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ============================================================
# ===== 10. سجل الصفقات =====
# ============================================================

@app.get("/api/v2/logs")
async def get_logs(limit: int = 50):
    """الحصول على سجل الصفقات"""
    global trading_log
    return {"logs": trading_log[-limit:] if trading_log else []}

# ============================================================
# ===== 11. إعادة تعيين الإحصائيات اليومية =====
# ============================================================

@app.post("/api/v2/reset-daily")
async def reset_daily():
    """إعادة تعيين الإحصائيات اليومية"""
    global risk_manager
    if risk_manager:
        risk_manager.reset_daily_stats()
    return {"status": "success", "message": "✅ تم إعادة تعيين الإحصائيات اليومية"}

# ============================================================
# ===== 12. تحديث السعر الحي =====
# ============================================================

@app.get("/api/v2/live-price/{symbol}")
async def get_live_price_endpoint(symbol: str):
    """الحصول على السعر الحي لزوج"""
    price = get_live_price(symbol)
    return {
        "symbol": symbol,
        "price": price,
        "timestamp": datetime.now().isoformat()
    }

# ============================================================
# ===== 13. صحية النظام =====
# ============================================================

@app.get("/health")
async def health_check():
    """فحص صحة النظام"""
    return {
        "status": "healthy",
        "version": "7.0.0",
        "timestamp": datetime.now().isoformat(),
        "connected": connection_status["connected"],
        "trading_enabled": is_trading_enabled
    }

# ============================================================
# ===== دالة التداول التلقائي (تعمل في الخلفية) =====
# ============================================================

async def auto_trade_loop(symbol: str):
    """حلقة التداول التلقائي"""
    global is_trading_enabled, trading_log, last_trade_result, last_analysis
    
    print(f"🚀 بدء التداول التلقائي على {symbol}")
    trading_log.append(f"🚀 بدء التداول التلقائي على {symbol}")
    
    scan_interval = 10
    expiry_seconds = QX_DEFAULT_EXPIRY
    
    while is_trading_enabled:
        try:
            # 1. التحليل
            print(f"🔍 تحليل {symbol}...")
            analysis = await analyze_symbol(symbol, 200)
            
            if "error" in analysis:
                print(f"⚠️ خطأ في التحليل: {analysis['error']}")
                await asyncio.sleep(scan_interval)
                continue
            
            last_analysis = analysis
            
            action = analysis.get("action", "NEUTRAL")
            confidence = analysis.get("confidence", 0)
            price = analysis.get("current_price", 0)
            time_remaining = analysis.get("time_remaining_minutes", 0)
            
            print(f"📊 الإشارة: {action} (الثقة: {confidence}%)")
            
            if action not in ["STRONG_BUY", "STRONG_SELL", "BUY", "SELL"]:
                print(f"⏳ إشارة ضعيفة ({action})، انتظار...")
                await asyncio.sleep(scan_interval)
                continue
            
            if confidence < QX_MIN_CONFIDENCE:
                print(f"⏳ الثقة منخفضة ({confidence}% < {QX_MIN_CONFIDENCE}%)، انتظار...")
                await asyncio.sleep(scan_interval)
                continue
            
            if not quotex_client or not quotex_client.is_connected:
                print("⚠️ فقدان الاتصال بـ Quotex، محاولة إعادة الاتصال...")
                await quotex_client.connect()
                if not quotex_client.is_connected:
                    trading_log.append("❌ فشل إعادة الاتصال بـ Quotex")
                    await asyncio.sleep(30)
                    continue
            
            balance = await quotex_client.get_balance()
            print(f"💰 الرصيد الحالي: ${balance:.2f}")
            
            risk_check = risk_manager.can_trade(balance, confidence, QX_MIN_CONFIDENCE)
            
            if not risk_check["allowed"]:
                print(f"⛔ {risk_check['reason']}")
                trading_log.append(f"⛔ {risk_check['reason']}")
                await asyncio.sleep(scan_interval)
                continue
            
            position_size = risk_check["position_size"]
            direction = "CALL" if "BUY" in action else "PUT"
            
            print(f"📈 تنفيذ {direction} بمبلغ ${position_size:.2f} (الثقة: {confidence}%)")
            trading_log.append(
                f"📈 {symbol} | {direction} | ${position_size:.2f} | "
                f"الثقة: {confidence}% | الوقت: {time_remaining:.1f} دقيقة"
            )
            
            trade_result = await quotex_client.execute_trade(
                symbol=symbol,
                direction=direction,
                amount=position_size,
                expiry=expiry_seconds
            )
            
            if trade_result.get("success"):
                trade_id = trade_result.get("trade_id")
                print(f"✅ تم تنفيذ {direction} بمبلغ ${position_size:.2f} (ID: {trade_id})")
                trading_log.append(f"✅ {symbol}: تم تنفيذ {direction} بمبلغ ${position_size:.2f}")
                
                print(f"⏳ انتظار نتيجة الصفقة {trade_id}...")
                result = await quotex_client.get_trade_result(trade_id, timeout=expiry_seconds + 10)
                
                if result.get("success"):
                    profit = result.get("profit", 0)
                    trade_result_status = result.get("result", "unknown")
                    
                    risk_manager.record_trade(profit, {
                        "symbol": symbol,
                        "direction": direction,
                        "amount": position_size,
                        "profit": profit,
                        "result": trade_result_status
                    })
                    
                    last_trade_result = result
                    
                    profit_str = f"+${profit:.2f}" if profit > 0 else f"${profit:.2f}"
                    print(f"💰 نتيجة الصفقة: {trade_result_status} | {profit_str}")
                    trading_log.append(f"💰 {symbol}: {trade_result_status} | {profit_str}")
                else:
                    print(f"⚠️ فشل الحصول على نتيجة الصفقة: {result.get('error')}")
                    trading_log.append(f"⚠️ {symbol}: فشل الحصول على نتيجة")
            else:
                error = trade_result.get("error", "خطأ غير معروف")
                print(f"❌ فشل تنفيذ الصفقة: {error}")
                trading_log.append(f"❌ {symbol}: فشل التنفيذ - {error}")
            
            wait_time = max(5, expiry_seconds / 2)
            print(f"⏳ انتظار {wait_time} ثواني قبل الدورة التالية...")
            await asyncio.sleep(wait_time)
            
        except Exception as e:
            error_msg = f"⚠️ خطأ في حلقة التداول: {str(e)}"
            print(error_msg)
            trading_log.append(error_msg)
            await asyncio.sleep(10)
    
    print("⏹️ تم إيقاف التداول التلقائي")
    trading_log.append("⏹️ تم إيقاف التداول التلقائي")

# ============================================================
# ===== التشغيل =====
# ============================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)