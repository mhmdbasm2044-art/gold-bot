import os, time, threading
from datetime import datetime
from flask import Flask
import requests

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "ضع_توكن_البوت_هنا")
CHAT_ID = os.environ.get("CHAT_ID", "ضع_الايدي_هنا")

daily_levels = []
last_price = 0
last_15m_slot = ""
touched = {}
last_error = ""

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Send Error {e}")

def get_price():
    global last_error
    # مصدر 1
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        p = float(r.get('price', 0))
        if p > 1000:
            last_error = "OK gold-api"
            return p
    except Exception as e:
        last_error = f"gold-api fail {e}"

    # مصدر 2 - PAXG هو ذهب حقيقي على بينانس سعره نفس الذهب
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", timeout=10).json()
        p = float(r.get('price', 0))
        if p > 1000:
            last_error = "OK binance PAXG"
            return p
    except Exception as e:
        last_error = f"binance fail {e}"

    # مصدر 3
    try:
        r = requests.get("https://data-asg.goldprice.org/dbXRates/USD", timeout=10).json()
        p = float(r['items'][0]['xauPrice'])
        if p > 1000:
            last_error = "OK goldprice.org"
            return p
    except Exception as e:
        last_error = f"all fail {e}"

    return 0

def build_levels(price):
    base = int(price // 25) * 25
    levels = [base-75, base-50, base-25, base, base+25, base+50, base+75]
    return sorted(levels)

def check_market():
    global daily_levels, last_price, last_15m_slot, touched
    last_day = ""
    time.sleep(5)
    send("✅ البوت اشتغل - جاري جلب السعر...")

    while True:
        try:
            price = get_price()

            if price == 0:
                print(f"Price 0 - Error {last_error}")
                time.sleep(15)
                continue

            now = datetime.utcnow()
            today_str = now.strftime("%Y-%m-%d")
            slot_15m = f"{today_str} {now.hour}:{int(now.minute/15)*15}"

            if today_str!= last_day or len(daily_levels)==0:
                daily_levels = build_levels(price)
                last_day = today_str
                touched = {}
                txt = f"📊 مستويات اليوم {today_str}\nسعر: {price:.2f}$\n\n"
                for lv in daily_levels:
                    txt += f"{lv}$\n"
                txt += "\nبانتظار لمس + ارتداد 15د"
                send(txt)

            # لمس
            for level in daily_levels:
                if abs(price - level) <= 3:
                    touched[level] = True

            is_new_candle = (slot_15m!= last_15m_slot) and (now.minute % 15 == 0) and (now.second < 60)

            if is_new_candle and last_price!= 0:
                for level in daily_levels:
                    if touched.get(level):
                        if last_price >= level and price < level:
                            send(f"🔻 بيع - ارتداد من {level}$\nدخول {price:.2f}$\nستوب {price+4:.2f}$\nهدف {price-8:.2f}$\n15د {now.strftime('%H:%M UTC')}")
                            touched[level] = False
                        elif last_price <= level and price > level:
                            send(f"🚀 شراء - ارتداد من {level}$\nدخول {price:.2f}$\nستوب {price-4:.2f}$\nهدف {price+8:.2f}$\n15د {now.strftime('%H:%M UTC')}")
                            touched[level] = False
                last_15m_slot = slot_15m

            if last_15m_slot == "":
                last_15m_slot = slot_15m

            last_price = price
            print(f"OK Price {price}")

        except Exception as e:
            print(f"Loop Error {e}")
        time.sleep(20)

threading.Thread(target=check_market, daemon=True).start()

@app.route("/")
def home():
    return f"بوت اللمس والارتداد | السعر {last_price} | المستويات {daily_levels} | تم لمسه {touched} | حالة {last_error}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
