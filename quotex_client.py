"""
عميل Quotex المتقدم باستخدام PyQuotex
اتصال حقيقي وتنفيذ صفقات
"""

import os
import asyncio
import json
import time
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from pyquotex.stable_api import Quotex
from pyquotex.utils.account_type import AccountType

class QuotexClient:
    """
    عميل Quotex للاتصال والتداول
    """
    
    def __init__(self, email: str, password: str, is_demo: bool = True):
        """
        تهيئة عميل Quotex
        
        Args:
            email: البريد الإلكتروني
            password: كلمة المرور
            is_demo: True للحساب التجريبي، False للحقيقي
        """
        self.email = email
        self.password = password
        self.is_demo = is_demo
        self.client: Optional[Quotex] = None
        self.is_connected = False
        self.balance = 0.0
        self.balances = {"demo": 0.0, "real": 0.0}
        self.account_type = "demo" if is_demo else "real"
        self.last_error = ""
        self._callbacks = []
        
    async def connect(self) -> bool:
        """
        الاتصال بـ Quotex عبر WebSocket
        
        Returns:
            bool: True إذا تم الاتصال بنجاح
        """
        try:
            print(f"🔌 جاري الاتصال بـ Quotex... (حساب: {self.account_type})")
            
            # إنشاء عميل Quotex
            self.client = Quotex(
                email=self.email,
                password=self.password,
                lang="ar"
            )
            
            # تعيين نوع الحساب
            mode = "PRACTICE" if self.is_demo else "REAL"
            self.client.set_account_mode(mode)
            
            # الاتصال
            connected, reason = await self.client.connect()
            
            if connected:
                self.is_connected = True
                await self._update_balance()
                print(f"✅ تم الاتصال بـ Quotex (حساب: {mode})")
                print(f"💰 الرصيد: ${self.balance:.2f}")
                return True
            else:
                self.last_error = reason
                print(f"❌ فشل الاتصال: {reason}")
                return False
                
        except Exception as e:
            self.last_error = str(e)
            print(f"❌ خطأ في الاتصال: {e}")
            return False
    
    async def disconnect(self) -> None:
        """قطع الاتصال بـ Quotex"""
        if self.client:
            try:
                await self.client.close()
            except:
                pass
        self.is_connected = False
        print("🔌 تم قطع الاتصال")
    
    async def _update_balance(self) -> None:
        """تحديث الرصيد"""
        if self.client and self.is_connected:
            try:
                balance = await self.client.get_balance()
                self.balance = balance if balance else 0.0
            except Exception as e:
                print(f"⚠️ فشل تحديث الرصيد: {e}")
    
    async def get_balance(self) -> float:
        """الحصول على الرصيد الحالي"""
        if not self.is_connected:
            return 0.0
        await self._update_balance()
        return self.balance
    
    async def switch_account(self, is_demo: bool) -> bool:
        """
        التبديل بين الحساب التجريبي والحقيقي
        
        Args:
            is_demo: True للحساب التجريبي، False للحقيقي
            
        Returns:
            bool: True إذا تم التبديل بنجاح
        """
        if not self.client or not self.is_connected:
            return False
        
        try:
            mode = "PRACTICE" if is_demo else "REAL"
            await self.client.change_account(mode)
            self.is_demo = is_demo
            self.account_type = "demo" if is_demo else "real"
            await self._update_balance()
            print(f"✅ تم التبديل إلى حساب {self.account_type}")
            return True
        except Exception as e:
            print(f"❌ فشل التبديل: {e}")
            return False
    
    async def execute_trade(self, symbol: str, direction: str, amount: float, expiry: int = 60) -> Dict[str, Any]:
        """
        تنفيذ صفقة على Quotex
        
        Args:
            symbol: رمز الزوج
            direction: الاتجاه (CALL أو PUT)
            amount: المبلغ
            expiry: المدة بالثواني
            
        Returns:
            Dict: نتيجة الصفقة
        """
        if not self.client or not self.is_connected:
            return {"success": False, "error": "غير متصل بـ Quotex"}
        
        try:
            # تحويل الاتجاه إلى صيغة PyQuotex
            dir_map = {"CALL": "call", "PUT": "put"}
            dir_key = dir_map.get(direction.upper(), "call")
            
            # التأكد من أن الزوج مفتوح
            asset_name, asset_data = await self.client.get_available_asset(symbol, force_open=True)
            if not asset_data or not asset_data[2]:
                return {"success": False, "error": f"الزوج {symbol} مغلق"}
            
            # تنفيذ الصفقة
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
                    "open_price": result.get("openPrice"),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": str(result)}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_trade_result(self, trade_id: str, timeout: int = 60) -> Dict[str, Any]:
        """
        انتظار نتيجة الصفقة
        
        Args:
            trade_id: معرف الصفقة
            timeout: مدة الانتظار بالثواني
            
        Returns:
            Dict: نتيجة الصفقة
        """
        if not self.client or not self.is_connected:
            return {"success": False, "error": "غير متصل بـ Quotex"}
        
        try:
            # انتظار النتيجة
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
    
    async def get_open_trades(self) -> List[Dict]:
        """الحصول على الصفقات المفتوحة"""
        if not self.client or not self.is_connected:
            return []
        
        try:
            # استخدام get_history للحصول على الصفقات
            history = await self.client.get_history()
            return history if history else []
        except Exception as e:
            print(f"⚠️ فشل جلب الصفقات المفتوحة: {e}")
            return []
    
    async def get_history(self, limit: int = 50) -> List[Dict]:
        """الحصول على سجل الصفقات"""
        if not self.client or not self.is_connected:
            return []
        
        try:
            history = await self.client.get_history()
            if history and len(history) > limit:
                return history[:limit]
            return history if history else []
        except Exception as e:
            print(f"⚠️ فشل جلب السجل: {e}")
            return []
    
    def get_status(self) -> Dict:
        """الحصول على حالة العميل"""
        return {
            "connected": self.is_connected,
            "account_type": self.account_type,
            "balance": self.balance,
            "last_error": self.last_error
        }