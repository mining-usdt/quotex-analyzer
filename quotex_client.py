"""
عميل Quotex - وضع المحاكاة المتقدم
يعمل بدون اتصال حقيقي - مثالي لـ Render
"""

import asyncio
import random
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

class QuotexClient:
    """
    عميل محاكاة متقدم - يعمل دائماً بدون اتصال حقيقي
    جميع الإشارات والتحليلات حقيقية، فقط التنفيذ محاكى
    """
    
    def __init__(self, email: str = "", password: str = "", is_demo: bool = True):
        self.email = email
        self.password = password
        self.is_demo = is_demo
        self.is_connected = False
        self.balance = 10000.0
        self.last_error = ""
        self._trades = []
        self._trade_id_counter = 0
        self._win_rate = 0.78  # 78% نسبة نجاح (واقعية)
        self._profit_factor = 0.85  # 85% عائد
        
    async def connect(self) -> bool:
        """محاكاة الاتصال - تنجح دائماً"""
        print(f"🔌 [محاكاة] جاري الاتصال بـ Quotex... (حساب: {'تجريبي' if self.is_demo else 'حقيقي'})")
        await asyncio.sleep(0.5)
        self.is_connected = True
        self.balance = 10000.0
        print("✅ [محاكاة] تم الاتصال بنجاح")
        print(f"💰 [محاكاة] الرصيد التجريبي: ${self.balance:.2f}")
        return True
    
    async def disconnect(self) -> None:
        """قطع الاتصال"""
        self.is_connected = False
        print("🔌 [محاكاة] تم قطع الاتصال")
    
    async def get_balance(self) -> float:
        """الحصول على الرصيد"""
        await asyncio.sleep(0.1)
        return self.balance
    
    async def execute_trade(self, symbol: str, direction: str, amount: float, expiry: int = 60) -> Dict[str, Any]:
        """محاكاة تنفيذ صفقة"""
        if not self.is_connected:
            return {"success": False, "error": "غير متصل"}
        
        self._trade_id_counter += 1
        trade_id = f"sim_{int(time.time())}_{self._trade_id_counter}"
        
        # محاكاة واقعية
        win = random.random() < self._win_rate
        profit = round(amount * self._profit_factor if win else -amount, 2)
        
        trade_data = {
            "id": trade_id,
            "symbol": symbol,
            "direction": direction,
            "amount": amount,
            "profit": profit,
            "win": win,
            "expiry": expiry,
            "timestamp": datetime.now().isoformat()
        }
        self._trades.append(trade_data)
        self.balance += profit
        
        print(f"📈 [محاكاة] {direction} {symbol} | ${amount:.2f} | {'✅ WIN' if win else '❌ LOSS'} | ${profit:+.2f}")
        
        return {
            "success": True,
            "trade_id": trade_id,
            "asset": symbol,
            "direction": direction,
            "amount": amount,
            "expiry": expiry,
            "timestamp": trade_data["timestamp"]
        }
    
    async def get_trade_result(self, trade_id: str, timeout: int = 60) -> Dict[str, Any]:
        """محاكاة الحصول على نتيجة الصفقة"""
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        for trade in self._trades:
            if trade["id"] == trade_id:
                return {
                    "success": True,
                    "trade_id": trade_id,
                    "result": "win" if trade["win"] else "loss",
                    "profit": trade["profit"]
                }
        
        return {"success": False, "error": "الصفقة غير موجودة"}
    
    async def get_open_trades(self) -> List[Dict]:
        """الصفقات المفتوحة"""
        return [t for t in self._trades if t.get("status") != "closed"]
    
    async def get_history(self, limit: int = 50) -> List[Dict]:
        """سجل الصفقات"""
        return self._trades[-limit:]
    
    def get_status(self) -> Dict:
        """حالة العميل"""
        wins = sum(1 for t in self._trades if t.get("win", False))
        total = len(self._trades)
        win_rate = round((wins / total * 100) if total > 0 else 0, 1)
        
        return {
            "connected": self.is_connected,
            "account_type": "demo" if self.is_demo else "real",
            "balance": self.balance,
            "last_error": self.last_error,
            "trades_count": total,
            "win_rate": win_rate,
            "profit": round(self.balance - 10000.0, 2)
        }