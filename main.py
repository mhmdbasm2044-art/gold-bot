from flask import Flask, jsonify
import threading, time, requests, os
from datetime import datetime, timedelta
app = Flask(__name__)
LEVELS = {}
LAST_CANDLE = ""
def get_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        return float(r['price'])
    except:
        return 4185.0
def calc_levels():
    global LEVELS
    p = get_price()
    LEVELS = {}
    for i in range(1, 11):
        LEVELS[f"R{i}"] = round(p + i*4, 2)
        LEVELS[f"S{i}"] = round(p - i*4, 2)
    LEVELS["date"] = datetime.now().strftime("%Y-%m-%d")
    LEVELS["base"] = p
    print(f"NEW LEVELS {p}", flush=True)
def send_signal(sig, name, lvl, live, prev):
    token = os.getenv("TELEGRAM_TOKEN")
    chat = os.getenv("CHAT_ID")
    if not token or not chat: return
    stop = lvl - 2.5 if sig=="BUY" else lvl + 2.5
    tp1 = lvl + 5 if sig=="BUY" else lvl - 5
    tp2 = lvl + 10 if sig=="BUY" else lvl - 10
    em = "🟢" if sig=="BUY" else "🔴"
    msg = f"{em} {sig} 15M\n📍 {name} {lvl}\n💰 مباشر: {live:.2f}\n🛑 {stop:.2f} 🎯 {tp1:.2f}/{tp2:.2f}"
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat, "text": msg}, timeout=10)
    except: pass
def loop():
    global LAST_CANDLE
    time.sleep(15)
    calc_levels()
    prev = get_price()
    while True:
        try:
            now = datetime.now() + timedelta(hours=3)
            live = get_price()
            if now.hour == 0 and now.minute < 2:
                calc_levels()
                time.sleep(70)
            is_new = (now.minute % 15 == 0 and now.second < 50)
            cid = now.strftime("%d %H:%M")
            if is_new and cid != LAST_CANDLE:
                for n,l in list(LEVELS.items()):
                    if not isinstance(l,float): continue
                    if "S" in n and prev < l and live > l:
                        send_signal("BUY", n, l, live, prev)
                        break
                    if "R" in n and prev > l and live < l:
                        send_signal("SELL", n, l, live, prev)
                        break
                LAST_CANDLE = cid
            prev = live
        except: pass
        time.sleep(30)
@app.route('/')
def home():
    return jsonify({"status":"WORKING 20 LEVELS","live":get_price(),"levels":LEVELS})
threading.Thread(target=loop, daemon=True).start()
