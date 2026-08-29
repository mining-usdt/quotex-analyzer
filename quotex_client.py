import asyncio
import os
import json
import time
from datetime import datetime
from playwright.async_api import async_playwright
import websockets
import httpx

class QuotexClient:
    def __init__(self, email: str, password: str, account_type: str = "PRACTICE"):
        self.email = email
        self.password = password
        self.account_type = account_type
        self.ssid = None
        self.websocket = None
        self.balance = 0.0
        self.is_connected = False
        self.session_file = "sessions/session.json"

    async def connect(self):
        """تسجيل الدخول إلى كوتكس والحصول على SSID"""
        os.makedirs("sessions", exist_ok=True)

        # محاولة تحميل الجلسة المخزنة
        if os.path.exists(self.session_file):
            with open(self.session_file, 'r') as f:
                data = json.load(f)
                if time.time() - data.get('timestamp', 0) < 3600:  # صلاحية ساعة
                    self.ssid = data.get('ssid')
                    self.is_connected = True
                    return True

        # تسجيل دخول جديد
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto("https://qxbroker.com/en/sign-in")
            await page.fill('input[name="email"]', self.email)
            await page.fill('input[name="password"]', self.password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(3000)

            # استخراج SSID من ملفات تعريف الارتباط
            cookies = await context.cookies()
            for cookie in cookies:
                if cookie['name'] == 'ssid':
                    self.ssid = cookie['value']
                    break

            await browser.close()

        if not self.ssid:
            raise Exception("فشل تسجيل الدخول إلى كوتكس")

        # حفظ الجلسة
        with open(self.session_file, 'w') as f:
            json.dump({
                'ssid': self.ssid,
                'timestamp': time.time()
            }, f)

        self.is_connected = True
        return True

    async def get_balance(self) -> float:
        """جلب الرصيد الحالي"""
        if not self.is_connected:
            await self.connect()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://qxbroker.com/api/v1/balance",
                    cookies={"ssid": self.ssid}
                )
                data = response.json()
                self.balance = float(data.get('balance', 0))
                return self.balance
        except:
            return self.balance

    async def execute_trade(self, symbol: str, direction: str, amount: float, expiry: int = 60) -> dict:
        """تنفيذ صفقة على كوتكس"""
        if not self.is_connected:
            await self.connect()

        # تحويل الاتجاه إلى CALL أو PUT
        trade_direction = 1 if direction in ["BUY", "STRONG_BUY"] else 0

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://qxbroker.com/api/v1/trade",
                    json={
                        "asset": symbol,
                        "direction": trade_direction,
                        "amount": amount,
                        "expiry": expiry,
                        "account_type": self.account_type
                    },
                    cookies={"ssid": self.ssid}
                )
                data = response.json()
                return {
                    "success": True,
                    "trade_id": data.get('trade_id'),
                    "status": "executed",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status": "failed"
            }

    async def disconnect(self):
        """قطع الاتصال"""
        self.is_connected = False
        self.ssid = None