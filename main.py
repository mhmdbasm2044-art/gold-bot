import requests, threading, time, os
from flask import Flask

app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

gold_history = []
TIMEFRAME = 48 # 4 ساعات = 48 قراءة (كل 5 دقايق)

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except: pass

def get_data():
    global gold_history
    try:
        g = float(requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()['price'])
        b_data = requests.get("https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT", timeout=10).json()
        btc = float(b_data['lastPrice'])
        # نجيب شمعات 4 ساعات للبتكوين حقيقية
        klines = requests.get("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=4h&limit=1", timeout=10).json()
        btc_h = float(klines[0][2])
        btc_l = float(klines[0][3])

        gold_history.append(g)
        if len(gold_history) > TIMEFRAME:
            gold_history.pop(0)

        gold_h = max(gold_history) if len(gold_history) > 5 else g * 1.005
        gold_l = min(gold_history) if len(gold_history) > 5 else g * 0.995

        return g, gold_h, gold_l, btc, btc_h, btc_l
    except Exception as e:
        print(e)
        return None

last_alert = 0
def check():
    global last_alert
    while True:
        d = get_data()
        if d:
            g, g_h, g_l, btc, btc_h, btc_l = d
            print(f"4H | Gold {g} H:{g_h} L:{g_l} | BTC {btc} H:{btc_h} L:{btc_l}")
            if time.time() - last_alert > 1800:
                if g >= g_h * 0.999 and len(gold_history) > 10:
                    send(f"🚀 <b>ذهب كسر مقاومة 4 ساعات</b>\n${g}\nاعلى 4س: ${g_h}\nاقل 4س: ${g_l}")
                    last_alert = time.time()
                elif g <= g_l * 1.001 and len(gold_history) > 10:
                    send(f"🔻 <b>ذهب كسر دعم 4 ساعات</b>\n${g}\nاعلى 4س: ${g_h}\nاقل 4س: ${g_l}")
                    last_alert = time.time()
                elif btc >= btc_h * 0.998:
                    send(f"🚀 <b>بتكوين مقاومة 4 ساعات</b>\n${btc:,.0f}\nاعلى: ${btc_h:,.0f} | اقل: ${btc_l:,.0f}")
                    last_alert = time.time()
                elif btc <= btc_l * 1.002:
                    send(f"🔻 <b>بتكوين دعم 4 ساعات</b>\n${btc:,.0f}\nاعلى: ${btc_h:,.0f} | اقل: ${btc_l:,.0f}")
                    last_alert = time.time()
        time.sleep(300)

@app.route("/")
def home():
    d = get_data()
    if not d: return "⏳ يجمع بيانات 4 ساعات..."
    g, g_h, g_l, btc, btc_h, btc_l = d
    return f"✅ افضل نظام - 4 ساعات<br>Gold: ${g} | H:{g_h:.1f} L:{g_l:.1f}<br>BTC: ${btc:,.0f} | H:{btc_h:,.0f} L:{btc_l:,.0f}<br>فحص كل 5 دقايق"

threading.Thread(target=check, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
