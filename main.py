import os, time, threading
from datetime import datetime
from flask import Flask
import requests

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "ضع_توكن_البوت_هنا")
CHAT_ID = os.environ.get("CHAT_ID", "ضع_الايدي_هنا")

daily_levels = []
last_price = 4175.0 # سعر افتراضي حتى لو فشل يشتغل
last_15m_slot = ""
touched = {}
last_error = "Starting..."

HEADERS = {"User-Agent": "Mozilla/5.0"}

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except Exception as e:
        print(e)

def get_price():
    global last_error

    urls = [
        ("https://api.gold-api.com/price/XAU", lambda j: float(j.get('price',0))),
        ("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", lambda j: float(j.get('price',0))),
        ("https://api.binance.com/api/v3/ticker/price?symbol=XAUTUSDT", lambda j: float(j.get('price',0))),
        ("https://data-asg.goldprice.org/dbXRates/USD", lambda j: float(j['items'][0]['xauPrice'])),
    ]

    for url, parser in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                j = r.json()
                p = parser(j)
                if p > 1000:
                    last_error = f"OK from {url} = {p}"
                    return p
                else:
                    last_error = f"{url} returned small {p}"
            else:
                last_error = f"{url} status {r.status_code}"
        except Exception as e:
            last_error = f"{url} error {e}"
            continue
    return 0

def build_levels(price):
    base = int(price // 25) * 25
    return [base-75, base-50, base-25, base, base+25, base+50, base+75]

def check_market():
    global daily_levels, last_price, last_15m_slot, touched
    last_day = ""
    time.sleep(3)
    try:
        send(f"✅ البوت اشتغل - السعر الحالي {last_price}")
    except:
        pass

    while True:
        try:
            price = get_price()

            # اذا فشل نبقى على السعر القديم بس نحدث الخطأ بالصفحة
            if price == 0:
                print(f"Failed fetch, keep {last_price} | {last_error}")
                time.sleep(20)
                continue

            now = datetime.utcnow()
            today_str = now.strftime("%Y-%m-%d")
            slot_15m = f"{today_str} {now.hour}:{int(now.minute/15)*15}"

            if today_str!= last_day or len(daily_levels)==0:
                daily_levels = build_levels(price)
                last_day = today_str
                touched = {}
                try:
                    txt = f"مستويات اليوم {today_str}\nسعر {price:.2f}$\n" + "\n".join([f"{lv}$" for lv in daily_levels])
                    send(txt)
                except:
                    pass

            for level in daily_levels:
                if abs(price - level) <= 3:
                    touched[level] = True

            is_new_candle = (slot_15m!= last_15m_slot) and (now.minute % 15 == 0)

            if is_new_candle and last_price!= 0:
                for level in daily_levels:
                    if touched.get(level):
                        if last_price >= level and price < level:
                            send(f"بيع - ارتداد من {level}$ دخول {price:.2f}$")
                            touched[level]=False
                        elif last_price <= level and price > level:
                            send(f"شراء - ارتداد من {level}$ دخول {price:.2f}$")
                            touched[level]=False
                last_15m_slot = slot_15m

            if last_15m_slot=="":
                last_15m_slot=slot_15m

            last_price = price
            print(f"Price OK {price}")

        except Exception as e:
            last_error = str(e)
            print(e)
        time.sleep(20)

threading.Thread(target=check_market, daemon=True).start()

@app.route("/")
def home():
    return f"السعر {last_price} | المستويات {daily_levels} | لمس {touched} | الحالة {last_error}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
