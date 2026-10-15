import os
import time
import requests
import yfinance as yf

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_msg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

def check_gold():
    # يفحص الذهب كل دقيقة
    data = yf.download("GC=F", period="1d", interval="1m")
    price = data['Close'].iloc[-1]
    return price

send_msg("✅ بوت الذهب اشتغل على Render")

while True:
    try:
        price = check_gold()
        print(f"Gold: {price}")
        # هنا تكدر تضيف شرط الاشارة مالك
        # مثال: اذا السعر نزل هواي
        # if price < 2650:
        #    send_msg(f"🚨 تنبيه هبوط ذهب: {price}")
        time.sleep(60)
    except Exception as e:
        print(e)
        time.sleep(10)
