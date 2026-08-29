"""
عميل Quotex مع دعم الـ Proxy
"""

import os
import asyncio
import json
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    from pyquotex.stable_api import Quotex
except ImportError:
    print("⚠️ pyquotex غير مثبت")
    # استخدم وضع المحاكاة كبديل
    from quotex_sim import QuotexClient as SimClient
    Quotex = None

class QuotexClient:
    def __init__(self, email: str, password: str, is_demo: bool = True):
        self.email = email
        self.password = password
        self.is_demo = is_demo
        self.client = None
        self.is_connected = False
        self.balance = 0.0
        self.last_error = ""
        self._use_sim = Quotex is None
        
    async def connect(self) -> bool:
        if self._use_sim:
            # استخدام المحاكاة
            self.client = SimClient(self.email, self.password, self.is_demo)
            return await self.client.connect()
        
        try:
            print(f"🔌 جاري الاتصال بـ Quotex... (حساب: {'تجريبي' if self.is_demo else 'حقيقي'})")
            
            self.client = Quotex(
                email=self.email,
                password=self.password,
                lang="en"
            )
            
            mode = "PRACTICE" if self.is_demo else "REAL"
            self.client.set_account_mode(mode)
            
            # محاولة الاتصال مع بروكسي
            connected, reason = await self.client.connect()
            
            if connected:
                self.is_connected = True
                await self._update_balance()
                print(f"✅ تم الاتصال بـ Quotex (حساب: {mode})")
                print(f"💰 الرصيد: ${self.balance:.2f}")
                return True
            else:
                self.last_error = reason
                print(f"⚠️ فشل الاتصال: {reason}")
                return False
                
        except Exception as e:
            self.last_error = str(e)
            print(f"❌ خطأ في الاتصال: {e}")
            return False
    
    async def _update_balance(self):
        if self.client and self.is_connected:
            try:
                self.balance = await self.client.get_balance()
            except:
                pass
    
    async def disconnect(self):
        if self.client:
            try:
                await self.client.close()
            except:
                pass
        self.is_connected = False
    
    async def get_balance(self) -> float:
        if self._use_sim:
            return await self.client.get_balance()
        await self._update_balance()
        return self.balance
    
    async def execute_trade(self, symbol: str, direction: str, amount: float, expiry: int = 60) -> Dict[str, Any]:
        if self._use_sim:
            return await self.client.execute_trade(symbol, direction, amount, expiry)
        
        if not self.client or not self.is_connected:
            return {"success": False, "error": "غير متصل"}
        
        try:
            dir_map = {"CALL": "call", "PUT": "put"}
            dir_key = dir_map.get(direction.upper(), "call")
            
            status, result = await self.client.buy(
                amount=amount,
                asset=symbol,
                direction=dir_key,
                duration=expiry
            )
            
            if status:
                await self._update_balance()
                return {
                    "success": True,
                    "trade_id": result.get("id"),
                    "asset": symbol,
                    "direction": direction,
                    "amount": amount,
                    "expiry": expiry,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": str(result)}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_trade_result(self, trade_id: str, timeout: int = 60) -> Dict[str, Any]:
        if self._use_sim:
            return await self.client.get_trade_result(trade_id, timeout)
        
        if not self.client or not self.is_connected:
            return {"success": False, "error": "غير متصل"}
        
        try:
            win, profit = await self.client.check_win(trade_id, timeout=timeout)
            await self._update_balance()
            return {
                "success": True,
                "trade_id": trade_id,
                "result": "win" if win == "win" else "loss",
                "profit": profit
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_history(self, limit: int = 50) -> List[Dict]:
        if self._use_sim:
            return await self.client.get_history(limit)
        
        if not self.client or not self.is_connected:
            return []
        
        try:
            history = await self.client.get_history()
            return history[:limit] if history else []
        except:
            return []
    
    def get_status(self) -> Dict:
        return {
            "connected": self.is_connected,
            "account_type": "demo" if self.is_demo else "real",
            "balance": self.balance,
            "last_error": self.last_error
        }