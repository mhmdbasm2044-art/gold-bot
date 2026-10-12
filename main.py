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
last_error = "Init"
last_15m_slot = ""

def send(msg):
    if not BOT_TOKEN or not CHAT_ID: return
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except: pass

def get_real_market():
    global last_error
    try:
        # 24hr high low حقيقي من Binance (نفس تريدنج فيو)
        r = requests.get("https://api.binance.com/api/v3/ticker/24hr?symbol=PAXGUSDT", timeout=10).json()
        price = float(r['lastPrice'])
        high = float(r['highPrice'])
        low = float(r['lowPrice'])
        close = float(r['prevClosePrice'])
        last_error = f"LIVE {price}$ H:{high} L:{low}"
        return price, high, low, close
    except Exception as e:
        last_error = f"Error {e}"
        return 0,0,0,0

def build_real_levels(price, high, low, close):
    # Pivot Point حقيقي مثل تريدنج فيو
    pp = (high + low + close) / 3
    r1 = (2*pp) - low
    s1 = (2*pp) - high
    r2 = pp + (high - low)
    s2 = pp - (high - low)
    
    # بس المستويات القريبة من السعر الحالي +-40$
    levels = [s2, s1, pp, r1, r2]
    real = []
    for lv in levels:
        if abs(lv - price) < 60:
            real.append(round(lv,1))
    
    # اضيف مستوى نفسي واحد قوي بس اذا قريب
    for psy in [4150, 4170, 4200, 4220]:
        if abs(psy - price) < 40:
            real.append(psy)
            
    real = sorted(list(set(real)))
    return real, pp

def check():
    global last_price, daily_levels, touched, last_15m_slot
    price, high, low, close = get_real_market()
    while price==0:
        time.sleep(10)
        price, high, low, close = get_real_market()
    
    last_price = price
    daily_levels, pp = build_real_levels(price, high, low, close)
    
    try:
        txt = f"📊 تحليل حقيقي {price:.2f}$\nH:{high:.1f} L:{low:.1f}\nPivot:{pp:.1f}\n\n"
        for lv in daily_levels:
            txt += f"{'🔴 مقاومة' if lv>price else '🟢 دعم'} {lv}$\n"
        send(txt)
    except: pass

    while True:
        try:
            p,h,l,c = get_real_market()
            if p!=0:
                old = last_price
                last_price = p
                
                now = datetime.utcnow()
                slot = f"{now.hour}:{int(now.minute/15)*15}"

                for lv in daily_levels:
                    if abs(last_price - lv) <= 2:
                        touched[lv]=True

                is_new = (slot!=last_15m_slot) and (now.minute % 15 == 0)
                if is_new and last_15m_slot!="":
                    for lv in daily_levels:
                        if touched.get(lv):
                            if old >= lv and last_price < lv:
                                send(f"🔻 بيع ارتداد حقيقي من {lv}$\nدخول {last_price}$")
                            elif old <= lv and last_price > lv:
                                send(f"🚀 شراء ارتداد حقيقي من {lv}$\nدخول {last_price}$")
                            touched[lv]=False
                    last_15m_slot=slot

                if last_15m_slot=="":
                    last_15m_slot=slot
        except Exception as e:
            last_error=str(e)
        time.sleep(15)

threading.Thread(target=check, daemon=True).start()

@app.route("/")
def home():
    return f"سعر حقيقي {last_price}$ | مستويات حقيقية {daily_levels} | {last_error}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
