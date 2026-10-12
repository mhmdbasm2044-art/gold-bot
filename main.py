from flask import Flask, jsonify
import threading, time, requests, os, sys
from datetime import datetime

app = Flask(__name__)
LEVELS = {}
LAST_SIGNAL = None

def log(m):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {m}", flush=True, file=sys.stdout)

def get_gold_price():
    # يحاول 3 مصادر
    try:
        import yfinance as yf
        df = yf.download("GC=F", period="1d", interval="15m", progress=False, auto_adjust=False)
        if len(df) > 0:
            v = df['Close'].iloc[-1]
            price = float(v.values[0] if hasattr(v, 'values') else v)
            log(f"Gold from yfinance: {price}")
            return price
    except Exception as e:
        log(f"yfinance fail: {e}")

    try:
        # مصدر ثاني
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        price = float(r['price'])
        log(f"Gold from gold-api: {price}")
        return price
    except Exception as e:
        log(f"gold-api fail: {e}")

    log("Using fallback price 4180")
    return 4180.0

def calc_20_levels():
    global LEVELS
    try:
        price = get_gold_price()
        # نحسب 20 مستوى حول السعر الحالي - كل مستوى 5$
        LEVELS = {}
        for i in range(1, 11):
            LEVELS[f"R{i}"] = round(price + (i * 5), 2)
        for i in range(1, 11):
            LEVELS[f"S{i}"] = round(price - (i * 5), 2)

        LEVELS["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        LEVELS["current"] = price
        log(f"✅ 20 LEVEL READY: {LEVELS}")

        # دز تليكرام اذا اكو توكن
        token = os.getenv("TELEGRAM_TOKEN")
        chat = os.getenv("CHAT_ID")
        if token and chat:
            r_txt = "\n".join([f"🔴 {k}: {v}" for k,v in LEVELS.items() if k.startswith("R")])
            s_txt = "\n".join([f"🟢 {k}: {v}" for k,v in LEVELS.items() if k.startswith("S")])
            msg = f"📅 *20 مستوى جديد*\n💰 السعر: {price}\n\n{r_txt}\n\n{s_txt}"
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat, "text": msg, "parse_mode": "Markdown"}, timeout=10)
            log("Telegram levels sent")

    except Exception as e:
        import traceback
        log(f"❌ calc error: {e}")
        log(traceback.format_exc())
        # مستويات طوارئ
        LEVELS = {f"R{i}": 4180 + i*5 for i in range(1,11)}
        LEVELS.update({f"S{i}": 4180 - i*5 for i in range(1,11)})

def check_loop():
    global LAST_SIGNAL
    while True:
        try:
            price = get_gold_price()
            now = datetime.now()
            log(f"Live Check: {price:.2f} | Levels: {LEVELS.get('date','none')}")

            # يحدث كل يوم مرة
            if now.hour == 0 and now.minute == 0:
                calc_20_levels()
                time.sleep(70)

            # هنا الاشارة - اذا السعر لمس مستوى
            for name, lvl in LEVELS.items():
                if not isinstance(lvl, (int,float)): continue
                if name.startswith("S") and abs(price - lvl) < 0.8: # لمس الدعم
                    if LAST_SIGNAL!= f"{name}_{now.strftime('%H:%M')}":
                        log(f"🚨 BUY SIGNAL {name} {lvl} price {price}")
                        LAST_SIGNAL = f"{name}_{now.strftime('%H:%M')}"
                if name.startswith("R") and abs(price - lvl) < 0.8: # لمس المقاومة
                    if LAST_SIGNAL!= f"{name}_{now.strftime('%H:%M')}":
                        log(f"🚨 SELL SIGNAL {name} {lvl} price {price}")
                        LAST_SIGNAL = f"{name}_{now.strftime('%H:%M')}"

        except Exception as e:
            log(f"Loop error: {e}")
        time.sleep(60)

@app.route('/')
def home():
    return jsonify({"status": "WORKING - 20 LEVELS", "levels": LEVELS, "time": datetime.now().isoformat()})

@app.route('/test')
def test():
    calc_20_levels()
    return jsonify(LEVELS)

# شغل
threading.Thread(target=check_loop, daemon=True).start()
calc_20_levels()
log("=== BOT STARTED ===")
