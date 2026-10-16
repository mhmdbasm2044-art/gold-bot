import os
import time
import threading
from flask import Flask
import requests

# --- الاعدادات ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

app = Flask(__name__)

@app.route('/')
def home():
    return "BOOM & CRASH Bot is Live - troej60"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
        requests.post(url, data=data)
    except Exception as e:
        print(f"Error sending: {e}")

def bot_logic():
    print("بوت BOOM & CRASH اشتغل...")
    send_telegram("✅ البوت اشتغل بنجاح بقناة troej60 و مربوط بـ UptimeRobot")
    while True:
        # هنا تخلي منطق الاشارات مال BOOM و CRASH
        # مثال تجريبي كل 5 دقايق
        time.sleep(300)
        # send_telegram("🔥 اشارة BOOM قادمة...")
        print("Bot loop running...")

# شغل البوت بثريد منفصل
threading.Thread(target=bot_logic, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
