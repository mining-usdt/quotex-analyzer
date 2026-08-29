"""
نقطة دخول التطبيق - تشغيل سيرفر FastAPI مع جميع الإعدادات
"""

import os
import sys
import asyncio
import uvicorn
from dotenv import load_dotenv

load_dotenv()

def main():
    """تشغيل السيرفر"""
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    print("=" * 60)
    print("🔥 Quotex Ultimate Bot v10.0")
    print("=" * 60)
    print(f"🌐 السيرفر يعمل على: http://{host}:{port}")
    print(f"📊 وحدة التحليل: http://{host}:{port}/")
    print(f"🔌 حالة النظام: http://{host}:{port}/health")
    print("=" * 60)
    print("⚠️  تأكد من إعدادات .env قبل البدء")
    print("=" * 60)
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()