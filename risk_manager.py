"""
إدارة المخاطر الصارمة لنظام التداول الآلي
"""

import json
import os
from datetime import datetime, date
from typing import Dict, Optional, Any

class RiskManager:
    """
    إدارة المخاطر مع حد خسارة يومي ونسبة مخاطرة ثابتة
    """
    
    def __init__(self, risk_percent: float = 1.0, daily_loss_limit: float = 10.0):
        """
        تهيئة مدير المخاطر
        
        Args:
            risk_percent: نسبة المخاطرة من الرصيد (مثال: 1.0 = 1%)
            daily_loss_limit: حد الخسارة اليومي بالدولار
        """
        self.risk_percent = risk_percent
        self.daily_loss_limit = daily_loss_limit
        self.trades_file = "trades_history.json"
        self.log_file = "trades_log.json"
        self.daily_loss = 0.0
        self.today = date.today().isoformat()
        self.total_trades = 0
        self.win_count = 0
        self.loss_count = 0
        self.total_profit = 0.0
        self.consecutive_losses = 0
        self.max_consecutive_losses = 0
        self.load_daily_stats()
    
    def load_daily_stats(self) -> None:
        """تحميل إحصائيات اليوم من الملف"""
        if os.path.exists(self.trades_file):
            try:
                with open(self.trades_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('date') == self.today:
                        self.daily_loss = data.get('daily_loss', 0.0)
                        self.total_trades = data.get('total_trades', 0)
                        self.win_count = data.get('win_count', 0)
                        self.loss_count = data.get('loss_count', 0)
                        self.total_profit = data.get('total_profit', 0.0)
                        self.consecutive_losses = data.get('consecutive_losses', 0)
                        self.max_consecutive_losses = data.get('max_consecutive_losses', 0)
                    else:
                        # يوم جديد - إعادة تعيين الإحصائيات
                        self.daily_loss = 0.0
                        self.total_trades = 0
                        self.win_count = 0
                        self.loss_count = 0
                        self.total_profit = 0.0
                        self.consecutive_losses = 0
                        self.max_consecutive_losses = 0
            except:
                self.daily_loss = 0.0
        else:
            self.daily_loss = 0.0
    
    def save_daily_stats(self) -> None:
        """حفظ إحصائيات اليوم إلى الملف"""
        try:
            with open(self.trades_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'date': self.today,
                    'daily_loss': self.daily_loss,
                    'total_trades': self.total_trades,
                    'win_count': self.win_count,
                    'loss_count': self.loss_count,
                    'total_profit': self.total_profit,
                    'consecutive_losses': self.consecutive_losses,
                    'max_consecutive_losses': self.max_consecutive_losses
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ فشل حفظ الإحصائيات: {e}")
    
    def calculate_position_size(self, balance: float) -> float:
        """
        حساب حجم الصفقة بناءً على الرصيد ونسبة المخاطرة
        
        Args:
            balance: الرصيد الحالي
            
        Returns:
            float: حجم الصفقة المقترح
        """
        position_size = balance * (self.risk_percent / 100)
        return round(position_size, 2)
    
    def can_trade(self, balance: float, confidence: int, min_confidence: int = 85) -> Dict:
        """
        التحقق من إمكانية التداول بناءً على عدة شروط
        
        Args:
            balance: الرصيد الحالي
            confidence: نسبة الثقة في الإشارة (0-100)
            min_confidence: أقل ثقة مسموح بها للتنفيذ
            
        Returns:
            Dict: {
                'allowed': bool,
                'reason': str,
                'position_size': float
            }
        """
        # 1. التحقق من الثقة
        if confidence < min_confidence:
            return {
                "allowed": False,
                "reason": f"الثقة منخفضة ({confidence}% < {min_confidence}%)",
                "position_size": 0.0
            }
        
        # 2. التحقق من حد الخسارة اليومي
        if self.daily_loss >= self.daily_loss_limit:
            return {
                "allowed": False,
                "reason": f"تم تجاوز حد الخسارة اليومي (${self.daily_loss_limit})",
                "position_size": 0.0
            }
        
        # 3. التحقق من الرصيد
        if balance < 5.0:
            return {
                "allowed": False,
                "reason": f"الرصيد منخفض جداً (${balance}) - الحد الأدنى 5$",
                "position_size": 0.0
            }
        
        # 4. التحقق من الخسائر المتتالية (توقف مؤقت)
        if self.consecutive_losses >= 3:
            return {
                "allowed": False,
                "reason": f"خسائر متتالية ({self.consecutive_losses}) - توقف مؤقت",
                "position_size": 0.0
            }
        
        # 5. حساب حجم الصفقة
        position_size = self.calculate_position_size(balance)
        if position_size < 0.5:
            return {
                "allowed": False,
                "reason": f"حجم الصفقة صغير جداً (${position_size}) - الحد الأدنى 0.5$",
                "position_size": 0.0
            }
        
        # 6. كل الشروط مستوفاة
        return {
            "allowed": True,
            "reason": "✅ جميع الشروط مستوفاة",
            "position_size": position_size
        }
    
    def record_trade(self, profit: float, trade_data: Optional[Dict] = None) -> None:
        """
        تسجيل نتيجة الصفقة
        
        Args:
            profit: الربح أو الخسارة من الصفقة
            trade_data: بيانات الصفقة (اختياري)
        """
        self.total_trades += 1
        
        if profit > 0:
            self.win_count += 1
            self.consecutive_losses = 0
        else:
            self.loss_count += 1
            self.consecutive_losses += 1
            if self.consecutive_losses > self.max_consecutive_losses:
                self.max_consecutive_losses = self.consecutive_losses
        
        self.total_profit += profit
        
        if profit < 0:
            self.daily_loss += abs(profit)
        
        # حفظ الإحصائيات
        self.save_daily_stats()
        
        # تسجيل الصفقة في ملف التدقيق
        self._log_trade(profit, trade_data)
    
    def _log_trade(self, profit: float, trade_data: Optional[Dict] = None) -> None:
        """تسجيل الصفقة في سجل التدقيق"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "profit": profit,
            "daily_loss": self.daily_loss,
            "total_profit": self.total_profit,
            "win_rate": round((self.win_count / self.total_trades * 100) if self.total_trades > 0 else 0, 2),
            "trade_data": trade_data or {}
        }
        
        try:
            logs = []
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            
            logs.append(log_entry)
            
            # الاحتفاظ بآخر 1000 صفقة فقط
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ فشل تسجيل الصفقة: {e}")
    
    def reset_daily_stats(self) -> None:
        """إعادة تعيين الإحصائيات اليومية"""
        self.daily_loss = 0.0
        self.total_trades = 0
        self.win_count = 0
        self.loss_count = 0
        self.total_profit = 0.0
        self.consecutive_losses = 0
        self.max_consecutive_losses = 0
        self.today = date.today().isoformat()
        self.save_daily_stats()
        print(f"✅ تم إعادة تعيين الإحصائيات اليومية ({self.today})")
    
    def get_status(self) -> Dict:
        """الحصول على حالة إدارة المخاطر الحالية"""
        win_rate = round((self.win_count / self.total_trades * 100) if self.total_trades > 0 else 0, 2)
        return {
            "daily_loss": self.daily_loss,
            "daily_limit": self.daily_loss_limit,
            "remaining": round(self.daily_loss_limit - self.daily_loss, 2),
            "risk_percent": self.risk_percent,
            "date": self.today,
            "total_trades": self.total_trades,
            "win_count": self.win_count,
            "loss_count": self.loss_count,
            "win_rate": win_rate,
            "total_profit": round(self.total_profit, 2),
            "consecutive_losses": self.consecutive_losses,
            "max_consecutive_losses": self.max_consecutive_losses
        }