from flask import Flask, jsonify
import yfinance as yf
from datetime import datetime
import threading, time, requests, os, sys

app = Flask(__name__)
GREEN_LEVELS = {}
last_signal_time = None

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True, file=sys.stdout)

def fix_price(v):
    try:
        if hasattr(v, 'values'): return float(v.values[0])
        if hasattr(v, 'iloc'): return float(v.iloc[0])
        return float(v)
    except: return float(v)

def calc_20_levels():
    global GREEN_LEVELS
    try:
        log("📅 حساب 20 مستوى خضر جديد...")
        data = yf.download("GC=F", period="10d", interval="1d", progress=False, auto_adjust=False)
        high = fix_price(data['High'].iloc[-2])
        low = fix_price(data['Low'].iloc[-2])
        close = fix_price(data['Close'].iloc[-2])
        rng = high - low
        pivot = (high + low + close) / 3

        GREEN_LEVELS = {}
        # 10 مقاومات فوك
        for i in range(1, 11):
            price = pivot + (rng * i * 0.25)
            GREEN_LEVELS[f"R{i}_{price:.2f}"] = round(price, 2)

        # 10 دعوم جوه
        for i in range(1, 11):
            price = pivot - (rng * i * 0.25)
            GREEN_LEVELS[f"S{i}_{price:.2f}"] = round(price, 2)

        GREEN_LEVELS["date"] = datetime.now().strftime("%Y-%m-%d")
        GREEN_LEVELS["pivot"] = round(pivot,2)
        GREEN_LEVELS["high"] = high
        GREEN_LEVELS["low"] = low

        log(f"✅ 20 LEVEL DONE: {GREEN_LEVELS}")

        token = os.getenv("TELEGRAM_TOKEN"); chat = os.getenv("CHAT_ID")
        if token:
            r_levels = "\n".join([f"🔴 {k}: {v}" for k,v in GREEN_LEVELS.items() if k.startswith("R")])
            s_levels = "\n".join([f"🟢 {k}: {v}" for k,v in GREEN_LEVELS.items() if k.startswith("S")])
            msg = f"📅 *20 مستوى جديد - {GREEN_LEVELS['date']}*\nPivot: {pivot:.2f}\n\n*مقاومات:*\n{r_levels}\n\n*دعوم:*\n{s_levels}"
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat, "text": msg, "parse_mode": "Markdown"}, timeout=10)

    except Exception as e:
        import traceback; log(f"❌ {e}"); log(traceback.format_exc())

def send_signal(sig, name, lvl, price):
    token = os.getenv("TELEGRAM_TOKEN"); chat = os.getenv("CHAT_ID")
    if not token: return
    stop = lvl - 2 if sig=="BUY" else lvl + 2
    tp1 = lvl + 5 if sig=="BUY" else lvl - 5
    tp2 = lvl + 10 if sig=="BUY" else lvl - 10
    emoji = "🟢" if sig=="BUY" else "🔴"
    txt = f"""{emoji} *{sig} 15m*
💰 مباشر: {price:.2f}
📍 {name} ({lvl})
🛑 ستوب: {stop:.2f}
🎯 هدف1: {tp1:.2f} | هدف2: {tp2:.2f}
⏰ {datetime.now().strftime('%H:%M')} بغداد
شمعة 15د {"فوك" if sig=="BUY" else "جوه"} الخط"""
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat, "text": txt, "parse_mode": "Markdown"}, timeout=10)

def loop():
    global last_signal_time
    while True:
        try:
            if not GREEN_LEVELS: calc_20_levels()
            df = yf.download("GC=F", period="2d", interval="15m", progress=False, auto_adjust=False)
            if len(df) < 2: time.sleep(30); continue
            last_open = fix_price(df['Open'].iloc[-1])
            prev_close = fix_price(df['Close'].iloc[-2])
            now = datetime.now()
            log(f"Live 15m: {last_open:.2f}")

            if now.minute % 15 <= 1 and now.second < 40 and last_signal_time!= now.strftime("%Y-%m-%d %H:%M"):
                for name, lvl in GREEN_LEVELS.items():
                    if not isinstance(lvl, float): continue
                    if "S" in name and prev_close < lvl and last_open > lvl:
                        send_signal("BUY", name, lvl, last_open)
                        last_signal_time = now.strftime("%Y-%m-%d %H:%M"); break
                    if "R" in name and prev_close > lvl and last_open < lvl:
                        send_signal("SELL", name, lvl, last_open)
                        last_signal_time = now.strftime("%Y-%m-%d %H:%M"); break

            if now.hour == 0 and now.minute == 0:
                calc_20_levels(); time.sleep(70)
        except Exception as e:
            log(f"Loop err {e}")
        time.sleep(30)

@app.route('/')
def home(): return jsonify({"status": "20 LEVELS BOT", "levels": GREEN_LEVELS})

threading.Thread(target=loop, daemon=True).start()
calc_20_levels()
