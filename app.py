"""
السيرفر الرئيسي لنظام Quotex Ultimate Bot
النسخة النهائية للـ Render - v10.0
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
    title="🔥 Quotex Ultimate Auto Trader",
    description="نظام تحليل وتداول تلقائي مع إدارة مخاطر صارمة",
    version="10.0.0"
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
QX_AUTO_START = os.getenv("QX_AUTO_START", "true").lower() == "true"
QX_DEFAULT_SYMBOL = os.getenv("QX_DEFAULT_SYMBOL", "EURUSD")

# ===== متغيرات عالمية =====
quotex_client: Optional[QuotexClient] = None
risk_manager = RiskManager(QX_RISK_PERCENT, QX_DAILY_LOSS_LIMIT)
is_trading_enabled = False
trading_log: List[str] = []
last_analysis: Optional[Dict] = None
last_trade_result: Optional[Dict] = None
connection_status = {
    "connected": False,
    "account_type": "demo",
    "balance": 0.0,
    "last_update": None
}
auto_trade_task: Optional[asyncio.Task] = None
trading_symbol: str = QX_DEFAULT_SYMBOL
is_auto_connecting = False

# ============================================================
# ===== نقاط النهاية API =====
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """تقديم الصفحة الرئيسية"""
    try:
        # محاولة قراءة index.html
        html_path = os.path.join(os.path.dirname(__file__), "index.html")
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        else:
            # صفحة HTML مدمجة في حال عدم وجود الملف
            return HTMLResponse(content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Quotex Bot</title>
                <style>
                    body { font-family: Arial; background: #0a0a0f; color: white; text-align: center; padding: 50px; }
                    .status { color: #00ff88; }
                    .error { color: #ff4444; }
                </style>
            </head>
            <body>
                <h1>🔥 Quotex Ultimate Bot</h1>
                <p class="status">✅ السيرفر يعمل بنجاح</p>
                <p>API متاحة على: <code>/api/v2/</code></p>
                <p>حالة النظام: <a href="/health">/health</a></p>
            </body>
            </html>
            """)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error: {str(e)}</h1>")

@app.get("/style.css", response_class=FileResponse)
async def serve_css():
    """تقديم ملف CSS"""
    css_path = os.path.join(os.path.dirname(__file__), "style.css")
    if os.path.exists(css_path):
        return FileResponse(css_path)
    return JSONResponse({"error": "style.css not found"}, status_code=404)

@app.get("/script.js", response_class=FileResponse)
async def serve_js():
    """تقديم ملف JavaScript"""
    js_path = os.path.join(os.path.dirname(__file__), "script.js")
    if os.path.exists(js_path):
        return FileResponse(js_path)
    return JSONResponse({"error": "script.js not found"}, status_code=404)

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
    global last_analysis
    
    try:
        df = get_ohlc_data(symbol, '1min', limit)
        if df is None or len(df) < 30:
            return {"error": f"لا يمكن جلب البيانات لـ {symbol}"}
        
        signal = SignalEngine.generate_signal(df)
        if "error" in signal:
            raise HTTPException(status_code=400, detail=signal["error"])
        
        price = get_live_price(symbol)
        
        signal["symbol"] = symbol
        signal["current_price"] = price or signal["current_price"]
        signal["timestamp"] = datetime.now().isoformat()
        
        # إضافة اسم الزوج
        pairs = get_forex_pairs()
        for p in pairs:
            if p["symbol"] == symbol:
                signal["pair_name"] = p["name"]
                signal["payout"] = p["payout"]
                break
        
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
    global last_analysis
    
    if not symbol:
        # البحث في جميع الأزواج
        pairs = get_forex_pairs()
        best_signal = None
        best_confidence = 0
        
        for p in pairs:
            try:
                df = get_ohlc_data(p["symbol"], '1min', 200)
                if df is None:
                    continue
                signal = SignalEngine.generate_signal(df)
                if "error" in signal:
                    continue
                if signal.get("confidence", 0) > best_confidence and signal.get("action") in ["STRONG_BUY", "STRONG_SELL", "BUY", "SELL"]:
                    signal["symbol"] = p["symbol"]
                    signal["pair_name"] = p["name"]
                    signal["payout"] = p["payout"]
                    best_signal = signal
                    best_confidence = signal.get("confidence", 0)
            except:
                continue
        
        if best_signal and best_confidence >= QX_MIN_CONFIDENCE:
            last_analysis = best_signal
            return {"status": "success", "signal": best_signal}
        return {"status": "no_signal", "message": "لا توجد إشارات قوية"}
    
    # تحليل زوج محدد
    try:
        result = await analyze_symbol(symbol)
        if isinstance(result, dict) and result.get("action") in ["STRONG_BUY", "STRONG_SELL", "BUY", "SELL"]:
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
    global connection_status, is_trading_enabled, trading_log, last_trade_result
    
    balance = 0.0
    if quotex_client and quotex_client.is_connected:
        try:
            balance = await quotex_client.get_balance()
            connection_status["balance"] = balance
            connection_status["last_update"] = datetime.now().isoformat()
        except:
            pass
    
    # الحصول على حالة إدارة المخاطر
    risk_status = risk_manager.get_status() if risk_manager else {}
    
    return {
        "status": "online",
        "trading_enabled": is_trading_enabled,
        "connected": quotex_client.is_connected if quotex_client else False,
        "account_type": connection_status["account_type"],
        "balance": balance,
        "risk_percent": QX_RISK_PERCENT,
        "daily_loss_limit": QX_DAILY_LOSS_LIMIT,
        "daily_loss": risk_manager.daily_loss if risk_manager else 0,
        "min_confidence": QX_MIN_CONFIDENCE,
        "logs": trading_log[-20:] if trading_log else [],
        "last_trade": last_trade_result,
        "trading_symbol": trading_symbol,
        "risk_status": risk_status
    }

# ============================================================
# ===== 5. الاتصال بـ Quotex =====
# ============================================================

@app.post("/api/v2/connect")
async def connect_to_quotex(
    account_type: str = Query("demo", description="نوع الحساب: demo أو real")
):
    """الاتصال بـ Quotex"""
    global quotex_client, connection_status, is_auto_connecting
    
    if quotex_client and quotex_client.is_connected:
        return {"status": "already_connected", "message": "✅ تم الاتصال بالفعل"}
    
    if is_auto_connecting:
        return {"status": "connecting", "message": "⏳ جاري الاتصال..."}
    
    is_auto_connecting = True
    
    try:
        is_demo = account_type.lower() == "demo"
        quotex_client = QuotexClient(
            email=QX_EMAIL,
            password=QX_PASSWORD,
            is_demo=is_demo
        )
        
        connected = await quotex_client.connect()
        
        if connected:
            connection_status["connected"] = True
            connection_status["account_type"] = "demo" if is_demo else "real"
            balance = await quotex_client.get_balance()
            connection_status["balance"] = balance
            connection_status["last_update"] = datetime.now().isoformat()
            
            is_auto_connecting = False
            
            # بدء التداول التلقائي فوراً
            if QX_AUTO_START and not is_trading_enabled:
                await start_auto_trading()
            
            return {
                "status": "success",
                "message": f"✅ تم الاتصال بحساب {connection_status['account_type']}",
                "balance": balance
            }
        else:
            is_auto_connecting = False
            return {
                "status": "error",
                "message": f"❌ فشل الاتصال بـ Quotex: {quotex_client.last_error}"
            }
            
    except Exception as e:
        is_auto_connecting = False
        return {"status": "error", "message": f"❌ خطأ: {str(e)}"}

# ============================================================
# ===== 6. قطع الاتصال =====
# ============================================================

@app.post("/api/v2/disconnect")
async def disconnect_from_quotex():
    """قطع الاتصال بـ Quotex"""
    global quotex_client, connection_status, is_trading_enabled, auto_trade_task
    
    is_trading_enabled = False
    if auto_trade_task:
        auto_trade_task.cancel()
        auto_trade_task = None
    
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
    symbol: str = Query(..., description="رمز الزوج")
):
    """تفعيل التداول التلقائي لزوج معين"""
    global is_trading_enabled, auto_trade_task, trading_symbol
    
    if not quotex_client or not quotex_client.is_connected:
        return {"status": "error", "message": "❌ غير متصل بـ Quotex"}
    
    if is_trading_enabled:
        return {"status": "already_running", "message": "⏳ التداول مفعل بالفعل"}
    
    is_trading_enabled = True
    trading_symbol = symbol
    auto_trade_task = asyncio.create_task(auto_trade_loop(symbol))
    
    trading_log.append(f"🚀 بدء التداول التلقائي على {symbol}")
    
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
    global is_trading_enabled, auto_trade_task
    
    is_trading_enabled = False
    if auto_trade_task:
        auto_trade_task.cancel()
        auto_trade_task = None
    
    trading_log.append("⏹️ تم إيقاف التداول التلقائي")
    
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
# ===== 13. صحة النظام =====
# ============================================================

@app.get("/health")
async def health_check():
    """فحص صحة النظام"""
    return {
        "status": "healthy",
        "version": "10.0.0",
        "timestamp": datetime.now().isoformat(),
        "connected": connection_status["connected"],
        "trading_enabled": is_trading_enabled,
        "uptime": "running"
    }

# ============================================================
# ===== دالة بدء التداول التلقائي =====
# ============================================================

async def start_auto_trading():
    """بدء التداول التلقائي مع الزوج الافتراضي"""
    global is_trading_enabled, auto_trade_task, trading_symbol
    
    if is_trading_enabled:
        return
    
    if not quotex_client or not quotex_client.is_connected:
        print("⚠️ لا يمكن بدء التداول - غير متصل")
        return
    
    is_trading_enabled = True
    trading_symbol = QX_DEFAULT_SYMBOL
    auto_trade_task = asyncio.create_task(auto_trade_loop(QX_DEFAULT_SYMBOL))
    
    print(f"🚀 بدء التداول التلقائي على {QX_DEFAULT_SYMBOL}")
    trading_log.append(f"🚀 بدء التداول التلقائي على {QX_DEFAULT_SYMBOL}")

# ============================================================
# ===== حلقة التداول التلقائي =====
# ============================================================

async def auto_trade_loop(symbol: str):
    """حلقة التداول التلقائي"""
    global is_trading_enabled, trading_log, last_trade_result, last_analysis, trading_symbol
    
    print(f"🚀 بدء التداول التلقائي على {symbol}")
    trading_log.append(f"🚀 بدء التداول التلقائي على {symbol}")
    
    scan_interval = 10
    expiry_seconds = QX_DEFAULT_EXPIRY
    consecutive_failures = 0
    max_failures = 5
    trades_today = 0
    max_trades_per_day = 30
    
    while is_trading_enabled:
        try:
            # 1. التحقق من الاتصال
            if not quotex_client or not quotex_client.is_connected:
                print("⚠️ فقدان الاتصال، محاولة إعادة الاتصال...")
                trading_log.append("⚠️ فقدان الاتصال، محاولة إعادة الاتصال...")
                
                if quotex_client:
                    connected = await quotex_client.connect()
                    if not connected:
                        await asyncio.sleep(30)
                        continue
                else:
                    is_demo = QX_ACCOUNT.lower() == "practice"
                    quotex_client = QuotexClient(QX_EMAIL, QX_PASSWORD, is_demo)
                    connected = await quotex_client.connect()
                    if not connected:
                        await asyncio.sleep(30)
                        continue
            
            # 2. جلب البيانات وتحليلها
            df = get_ohlc_data(symbol, '1min', 200)
            
            if df is None or len(df) < 30:
                await asyncio.sleep(scan_interval)
                consecutive_failures += 1
                if consecutive_failures >= max_failures:
                    trading_log.append(f"⚠️ {symbol}: فشل جلب البيانات {max_failures} مرات")
                    consecutive_failures = 0
                    await asyncio.sleep(60)
                continue
            
            analysis = SignalEngine.generate_signal(df)
            if "error" in analysis:
                await asyncio.sleep(scan_interval)
                continue
            
            last_analysis = analysis
            consecutive_failures = 0
            
            action = analysis.get("action", "NEUTRAL")
            confidence = analysis.get("confidence", 0)
            price = analysis.get("current_price", 0)
            time_remaining = analysis.get("time_remaining_minutes", 0)
            
            print(f"📊 الإشارة: {action} (الثقة: {confidence}%) | {symbol} | السعر: {price}")
            
            # 3. التحقق من قوة الإشارة
            if action not in ["STRONG_BUY", "STRONG_SELL", "BUY", "SELL"]:
                await asyncio.sleep(scan_interval)
                continue
            
            if confidence < QX_MIN_CONFIDENCE:
                await asyncio.sleep(scan_interval)
                continue
            
            # 4. التحقق من الحد الأقصى للصفقات اليومية
            if trades_today >= max_trades_per_day:
                print(f"⏳ تم الوصول للحد الأقصى للصفقات اليومية ({max_trades_per_day})")
                await asyncio.sleep(60)
                continue
            
            # 5. التحقق من الرصيد والمخاطر
            balance = await quotex_client.get_balance()
            print(f"💰 الرصيد الحالي: ${balance:.2f}")
            
            risk_check = risk_manager.can_trade(balance, confidence, QX_MIN_CONFIDENCE)
            
            if not risk_check["allowed"]:
                print(f"⛔ {risk_check['reason']}")
                await asyncio.sleep(scan_interval)
                continue
            
            # 6. تنفيذ الصفقة
            position_size = risk_check["position_size"]
            direction = "CALL" if "BUY" in action else "PUT"
            
            trade_executed = False
            for retry in range(3):
                try:
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
                        trade_executed = True
                        trade_id = trade_result.get("trade_id")
                        print(f"✅ تم تنفيذ {direction} بمبلغ ${position_size:.2f} (ID: {trade_id})")
                        trading_log.append(f"✅ {symbol}: تم تنفيذ {direction} بمبلغ ${position_size:.2f}")
                        
                        print(f"⏳ انتظار نتيجة الصفقة {trade_id}...")
                        result = await quotex_client.get_trade_result(trade_id, timeout=expiry_seconds + 15)
                        
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
                            trades_today += 1
                            
                            profit_str = f"+${profit:.2f}" if profit > 0 else f"${profit:.2f}"
                            print(f"💰 نتيجة الصفقة: {trade_result_status} | {profit_str}")
                            trading_log.append(f"💰 {symbol}: {trade_result_status} | {profit_str}")
                        else:
                            print(f"⚠️ فشل الحصول على نتيجة الصفقة: {result.get('error')}")
                            trading_log.append(f"⚠️ {symbol}: فشل الحصول على نتيجة")
                        break
                    else:
                        error = trade_result.get("error", "خطأ غير معروف")
                        print(f"❌ فشل تنفيذ الصفقة (محاولة {retry + 1}): {error}")
                        trading_log.append(f"❌ {symbol}: فشل التنفيذ - {error}")
                        await asyncio.sleep(5)
                        
                except Exception as e:
                    print(f"⚠️ خطأ في التنفيذ (محاولة {retry + 1}): {e}")
                    await asyncio.sleep(5)
            
            if not trade_executed:
                trading_log.append(f"⚠️ {symbol}: فشل تنفيذ الصفقة بعد 3 محاولات")
            
            # 7. انتظار قبل الدورة التالية
            wait_time = max(5, expiry_seconds / 2)
            print(f"⏳ انتظار {wait_time} ثواني قبل الدورة التالية...")
            await asyncio.sleep(wait_time)
            
        except asyncio.CancelledError:
            print("⏹️ تم إلغاء مهمة التداول التلقائي")
            trading_log.append("⏹️ تم إلغاء مهمة التداول التلقائي")
            break
        except Exception as e:
            error_msg = f"⚠️ خطأ في حلقة التداول: {str(e)}"
            print(error_msg)
            trading_log.append(error_msg)
            await asyncio.sleep(15)
    
    print("⏹️ تم إيقاف التداول التلقائي")
    trading_log.append("⏹️ تم إيقاف التداول التلقائي")

# ============================================================
# ===== التشغيل التلقائي عند بدء السيرفر =====
# ============================================================

@app.on_event("startup")
async def startup_event():
    """تشغيل التداول التلقائي عند بدء السيرفر"""
    print("=" * 60)
    print("🔥 Quotex Ultimate Bot v10.0 - التشغيل التلقائي")
    print("=" * 60)
    
    if QX_AUTO_START:
        print("🔧 تفعيل وضع التشغيل التلقائي...")
        asyncio.create_task(auto_connect_and_start())
    else:
        print("⏸️ وضع التشغيل التلقائي معطل (QX_AUTO_START=false)")

async def auto_connect_and_start():
    """الاتصال التلقائي وبدء التداول"""
    global quotex_client, connection_status
    
    try:
        await asyncio.sleep(3)
        
        print("🔌 محاولة الاتصال التلقائي بـ Quotex...")
        
        is_demo = QX_ACCOUNT.lower() == "practice"
        quotex_client = QuotexClient(QX_EMAIL, QX_PASSWORD, is_demo)
        
        connected = await quotex_client.connect()
        
        if connected:
            connection_status["connected"] = True
            connection_status["account_type"] = "demo" if is_demo else "real"
            balance = await quotex_client.get_balance()
            connection_status["balance"] = balance
            connection_status["last_update"] = datetime.now().isoformat()
            
            print(f"✅ تم الاتصال التلقائي (الرصيد: ${balance:.2f})")
            trading_log.append(f"✅ تم الاتصال التلقائي (الرصيد: ${balance:.2f})")
            
            await start_auto_trading()
        else:
            print(f"❌ فشل الاتصال التلقائي: {quotex_client.last_error}")
            trading_log.append(f"❌ فشل الاتصال التلقائي: {quotex_client.last_error}")
            
            await asyncio.sleep(30)
            asyncio.create_task(auto_connect_and_start())
            
    except Exception as e:
        print(f"❌ خطأ في التشغيل التلقائي: {e}")
        trading_log.append(f"❌ خطأ في التشغيل التلقائي: {e}")
        await asyncio.sleep(30)
        asyncio.create_task(auto_connect_and_start())

# ============================================================
# ===== التشغيل =====
# ============================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)