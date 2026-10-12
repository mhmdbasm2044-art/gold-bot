import os, time, threading
from datetime import datetime
from flask import Flask
import requests

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "ضع_توكن_البوت_هنا")
CHAT_ID = os.environ.get("CHAT_ID", "ضع_الايدي_هنا")

STOP = 4.0
TARGET = 8.0

daily_levels = []
last_price = 0
last_15m_slot = ""
last_day = ""

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def get_gold_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        return float(r['price'])
    except:
        try:
            r = requests.get("https://data-asg.goldprice.org/dbXRates/USD", timeout=10).json()
            return float(r['items'][0]['xauPrice'])
        except:
            return 0

def build_daily_levels(price):
    # 20 مستوى - 10 جوة و 10 فوك - كل 10$
    base = int(price // 10) * 10
    levels = []
    for i in range(-10, 10):
        levels.append(base + (i * 10))
    return sorted(levels)

def check_market():
    global daily_levels, last_price, last_15m_slot, last_day
    send("✅ *بوت الذهب 20 مستوى اشتغل*\n20 مستوى - فريم 15د - مستويات كل 10$")
    while True:
        try:
            price = get_gold_price()
            if price == 0:
                time.sleep(20)
                continue

            now = datetime.utcnow()
            today_str = now.strftime("%Y-%m-%d")
            slot_15m = f"{today_str} {now.hour}:{int(now.minute/15)*15}"

            if today_str != last_day:
                daily_levels = build_daily_levels(price)
                last_day = today_str
                txt = f"📅 *20 مستوى جديد - {today_str}*\nسعر الذهب الان: `{price:.2f}$`\n\n"
                for lv in daily_levels:
                    txt += f"▫️ `{lv}$`\n"
                txt += "\nبانتظار افتتاح شمعة 15د فوق/تحت المستوى"
                send(txt)

            is_new_candle = (slot_15m != last_15m_slot) and (now.minute % 15 == 0) and (now.second < 45)

            if is_new_candle and last_price != 0:
                for level in daily_levels:
                    if last_price < level and price >= level:
                        send(f"🚀 *شراء -
