import json
import os
from datetime import datetime, date

class RiskManager:
    def __init__(self, risk_percent: float = 1.0, daily_loss_limit: float = 10.0):
        self.risk_percent = risk_percent
        self.daily_loss_limit = daily_loss_limit
        self.trades_file = "trades_history.json"
        self.daily_loss = 0.0
        self.load_daily_stats()

    def load_daily_stats(self):
        """تحميل إحصائيات اليوم"""
        today = date.today().isoformat()
        if os.path.exists(self.trades_file):
            with open(self.trades_file, 'r') as f:
                data = json.load(f)
                if data.get('date') == today:
                    self.daily_loss = data.get('daily_loss', 0.0)
                else:
                    self.daily_loss = 0.0
        else:
            self.daily_loss = 0.0

    def save_daily_stats(self):
        """حفظ إحصائيات اليوم"""
        with open(self.trades_file, 'w') as f:
            json.dump({
                'date': date.today().isoformat(),
                'daily_loss': self.daily_loss
            }, f)

    def calculate_position_size(self, balance: float) -> float:
        """حساب حجم الصفقة بناءً على الرصيد ونسبة المخاطرة"""
        return round(balance * (self.risk_percent / 100), 2)

    def can_trade(self, balance: float, confidence: int, min_confidence: int = 85) -> dict:
        """التحقق من إمكانية التداول"""
        # 1. التحقق من الثقة
        if confidence < min_confidence:
            return {"allowed": False, "reason": f"الثقة منخفضة ({confidence}% < {min_confidence}%)"}

        # 2. التحقق من حد الخسارة اليومي
        if self.daily_loss >= self.daily_loss_limit:
            return {"allowed": False, "reason": f"تم تجاوز حد الخسارة اليومي (${self.daily_loss_limit})"}

        # 3. التحقق من الرصيد
        if balance < 5.0:
            return {"allowed": False, "reason": f"الرصيد منخفض (${balance})"}

        # 4. حساب حجم الصفقة
        position_size = self.calculate_position_size(balance)
        if position_size < 0.5:
            return {"allowed": False, "reason": f"حجم الصفقة صغير جداً (${position_size})"}

        return {
            "allowed": True,
            "position_size": position_size,
            "daily_loss": self.daily_loss,
            "remaining_daily_limit": self.daily_loss_limit - self.daily_loss
        }

    def record_trade(self, profit: float):
        """تسجيل نتيجة الصفقة"""
        if profit < 0:
            self.daily_loss += abs(profit)
        self.save_daily_stats()

    def reset_daily_stats(self):
        """إعادة تعيين الإحصائيات اليومية"""
        self.daily_loss = 0.0
        self.save_daily_stats()