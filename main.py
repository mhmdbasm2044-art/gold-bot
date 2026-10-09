from flask import Flask
import threading, time, requests, os
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# اعدادات احترافية
SUPPORT = 4100
RESISTANCE = 4200
BREAKOUT_BUFFER = 8
last_price = 0
above_count = 0

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg}
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(e)

def get_gold_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        return float(r.get('price', 0))
    except:
        return 0

def check_gold():
    global last_price, above_count
    while True:
        price = get_gold_price()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        print(f"[{now}] Gold: {price}")

        if price == 0:
            time.sleep(60)
            continue

        # 1- قرب المقاومة
        if RESISTANCE-15 < price < RESISTANCE:
            if last_price < RESISTANCE-15:
                send(f"⚠️ الذهب عند المقاومة\nالسعر: ${price}\nالمقاومة: {RESISTANCE}$ قوية\nالقرار: لا تشتري - انتظر كسر")

        # 2- كسر مقاومة حقيقي - شراء مو بيع
        elif price > RESISTANCE + BREAKOUT_BUFFER:
            above_count += 1
            if above_count >= 2:
                send(f"🚀 كسر مقاومة مؤكد!\nكسر {RESISTANCE}$ ووصل ${price}\nالقرار: شراء - الهدف 4250$ ثم 4300$\nستوب: {RESISTANCE}$")
                above_count = 0
        else:
            above_count = 0

        # 3- عند الدعم - شراء
        if SUPPORT-10 < price < SUPPORT+15 and last_price > SUPPORT+20:
            send(f"🟢 الذهب عند الدعم\nالسعر: ${price}\nالدعم {SUPPORT}$ صمد اسبوع\nالقرار: شراء - هدف {RESISTANCE}$")

        last_price = price
        time.sleep(300)

@app.route("/")
def home():
    price = get_gold_price()
    return f"✅ Gold Bot Pro شغال - السعر هسه ${price} - دعم {SUPPORT} مقاومة {RESISTANCE}"

threading.Thread(target=check_gold, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
