import os, time, threading
from datetime import datetime
from flask import Flask
import requests

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")

last_price = 0
daily_levels = []
touched = {}
last_error = "Starting..."
last_15m_slot = ""

def send(msg):
    if not BOT_TOKEN or not CHAT_ID: return
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except: pass

def get_price_real():
    global last_error
    # 1 - Binance Vision (هذا ما ينحجب بـ Render)
    try:
        r = requests.get("https://data-api.binance.vision/api/v3/ticker/24hr?symbol=PAXGUSDT", timeout=10).json()
        p = float(r['lastPrice'])
        h = float(r['highPrice'])
        l = float(r['lowPrice'])
        if p>1000:
            last_error=f"OK Binance Vision {p}"
            return p,h,l,float(r['prevClosePrice'])
    except Exception as e:
        last_error=f"Vision fail {e}"

    # 2 - CoinGecko (يشتغل دائما)
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=pax-gold&vs_currencies=usd", timeout=10).json()
        p = float(r['pax-gold']['usd'])
        if p>1000:
            last_error=f"OK CoinGecko {p}"
            # هاي وليو تقديرية
            return p, p+20, p-20, p
    except Exception as e:
        last_error=f"Gecko fail {e}"

    # 3 - Gold-API
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        p = float(r['price'])
        if p>1000:
            last_error=f"OK GoldAPI {p}"
            return p, p+20, p-20, p
    except Exception as e:
        last_error=f"All fail {e}"

    return 0,0,0,0

def build_levels(price, high, low, close):
    pp = (high+low+close)/3
    r1 = (2*pp)-low
    s1 = (2*pp)-high
    levels=[]
    for lv in [s1, pp, r1]:
        if abs(lv-price)<50 and lv>1000:
            levels.append(round(lv,1))
    # اضيف اقرب مستوى نفسي حقيقي بس واحد
    for psy in [4150,4170,4180,4200]:
        if abs(psy-price)<25:
            levels.append(psy)
    return sorted(list(set(levels))), pp

def worker():
    global last_price, daily_levels, touched, last_15m_slot
    # حاول تجيب السعر فورا
    for _ in range(10):
        p,h,l,c = get_price_real()
        if p!=0:
            last_price=p
            daily_levels, pp = build_levels(p,h,l,c)
            try:
                send(f"✅ اشتغل\nسعر {p:.2f}$\nمستويات {daily_levels}\nPivot {pp:.1f}")
            except: pass
            break
        time.sleep(3)

    while True:
        try:
            p,h,l,c = get_price_real()
            if p!=0:
                old=last_price
                last_price=p
                now=datetime.utcnow()
                slot=f"{now.hour}:{int(now.minute/15)*15}"
                for lv in daily_levels:
                    if abs(p-lv)<=2:
                        touched[lv]=True
                is_new=(slot!=last_15m_slot) and (now.minute%15==0)
                if is_new and last_15m_slot!="":
                    for lv in daily_levels:
                        if touched.get(lv):
                            if old>=lv and p<lv:
                                send(f"🔻 بيع من {lv}$ دخول {p:.1f}$")
                            elif old<=lv and p>lv:
                                send(f"🚀 شراء من {lv}$ دخول {p:.1f}$")
                            touched[lv]=False
                    last_15m_slot=slot
                if last_15m_slot=="":
                    last_15m_slot=slot
        except Exception as e:
            last_error=str(e)
        time.sleep(20)

threading.Thread(target=worker, daemon=True).start()

@app.route("/")
def home():
    return f"سعر حقيقي {last_price}$ | مستويات حقيقية {daily_levels} | {last_error}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
