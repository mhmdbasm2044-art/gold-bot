from flask import Flask, jsonify
import threading, time, requests, os
from datetime import datetime, timedelta

app = Flask(__name__)
LEVELS = {}
LAST_CANDLE = ""
STARTED = False

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
    print(f"✅ 20 LEVELS {p}", flush=True)
    # دز يومية
    token = os.getenv("TELEGRAM_TOKEN")
    chat = os.getenv("CHAT_ID")
    if token and chat:
        try:
            txt = "\n".join([f"{k}: {v}" for k,v in LEVELS.items() if isinstance(v,float)])
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                data={"chat_id": chat, "text": f"📅 مستويات جديدة {LEVELS['date']}\nBase {p}\n\n{txt}"}, timeout=10)
        except: pass

def send_signal(sig, name, lvl, live, prev):
    token = os.getenv("TELEGRAM_TOKEN")
    chat = os.getenv("CHAT_ID")
    if not token or not chat: return
    stop = lvl - 2.5 if sig=="BUY" else lvl + 2.5
    tp1 = lvl + 5 if sig=="BUY" else lvl - 5
    tp2 = lvl + 10 if sig=="BUY" else lvl - 10
    em = "🟢" if sig=="BUY" else "🔴"
    d = "فوك الخط" if sig=="BUY" else "جوه الخط"
    msg = f"""{em} {sig} 15M
📍 {name} {lvl}
💰 مباشر: {live:.2f} | سابق: {prev:.2f}
📊 شمعة 15د: {d}
🛑 ستوب: {stop:.2f} (2.5$)
🎯 هدف1: {tp1:.2f}
🎯 هدف2: {tp2:.2f}
⏰ {(datetime.now()+timedelta(hours=3)).strftime('%H:%M')} بغداد"""
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat, "text": msg}, timeout=10)
    except: pass

def loop():
    global LAST_CANDLE
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
            print(f"Live {live} {now.strftime('%H:%M')}", flush=True)
        except Exception as e:
            print(f"err {e}", flush=True)
        time.sleep(30)

def start_bot():
    time.sleep(5)
    threading.Thread(target=loop, daemon=True).start()

@app.route('/')
def home():
    global STARTED
    if not STARTED:
        STARTED = True
        threading.Thread(target=start_bot, daemon=True).start()
    return jsonify({"status":"✅ BOT WORKING 20 LEVELS","live":get_price(),"levels":LEVELS,"time": (datetime.now()+timedelta(hours=3)).strftime('%Y-%m-%d %H:%M')})

@app.route('/levels')
def levels():
    return jsonify(LEVELS)
