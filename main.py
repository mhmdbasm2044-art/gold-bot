from flask import Flask, jsonify
import threading, time, requests, os
from datetime import datetime
import pytz

app = Flask(__name__)

LEVELS = {}
LAST_CANDLE = ""  # لمنع تكرار الاشارة بنفس الشمعة
BAGHDAD = pytz.timezone('Asia/Baghdad')

def log(m):
    print(f"[{datetime.now(BAGHDAD).strftime('%H:%M:%S')}] {m}", flush=True)

def get_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=8).json()
        return float(r['price'])
    except:
        return 4185.0  # سعر احتياط اذا فشل النت

def calc_daily_levels():
    global LEVELS
    price = get_price()
    # كل يوم مستوى جديد حول سعر السوق الحالي - المسافة 4$
    LEVELS = {}
    for i in range(1, 11):
        LEVELS[f"R{i}"] = round(price + i*4, 2)  # مقاومات فوك
    for i in range(1, 11):
        LEVELS[f"S{i}"] = round(price - i*4, 2)  # دعوم جوه
    
    LEVELS["date"] = datetime.now(BAGHDAD).strftime("%Y-%m-%d")
    LEVELS["base_price"] = price
    log(f"✅ 20 مستوى جديد ليوم {LEVELS['date']} من سعر {price}")

    # دز المستويات الجديدة تليكرام
    send_daily_levels(price)

def send_daily_levels(price):
    token = os.getenv("TELEGRAM_TOKEN")
    chat = os.getenv("CHAT_ID")
    if not token or not chat: return
    try:
        r_txt = "\n".join([f"🔴 {k}: {v}" for k,v in LEVELS.items() if k.startswith("R")])
        s_txt = "\n".join([f"🟢 {k}: {v}" for k,v in LEVELS.items() if k.startswith("S")])
        msg = f"📅 *مستويات خضرة جديدة - {LEVELS['date']}*\n💰 سعر الارتكاز: {price:.2f}\n\n*r_txt*\n\n*s_txt*\n\n⏰ يراقب فريم 15د"
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        log(f"Telegram daily error {e}")

def send_signal(signal, lvl_name, lvl_price, live_price, prev_price):
    token = os.getenv("TELEGRAM_TOKEN")
    chat = os.getenv("CHAT_ID")
    if not token or not chat: return
    try:
        stop = lvl_price - 2.5 if signal == "BUY" else lvl_price + 2.5
        tp1 = lvl_price + 5 if signal == "BUY" else lvl_price - 5
        tp2 = lvl_price + 10 if signal == "BUY" else lvl_price - 10
        emoji = "🟢" if signal == "BUY" else "🔴"
        direct = "سكرت فوك الخط" if signal == "BUY" else "سكرت جوه الخط"

        msg = f"""{emoji} *{signal} 15M - كسر مستوى*

📍 المستوى: {lvl_name} ({lvl_price})
💰 سعر مباشر: {live_price:.2f}
📊 شمعة 15د: {direct}
الاغلاق السابق: {prev_price:.2f}

🛑 ستوب: {stop:.2f} (2.5$)
🎯 هدف1: {tp1:.2f} (5$)
🎯 هدف2: {tp2:.2f} (10$)

⏰ {datetime.now(BAGHDAD).strftime('%Y-%m-%d %H:%M')} بتوقيت بغداد
"""
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        log(f"🚀 اشارة {signal} {lvl_name}")
    except Exception as e:
        log(f"Signal error {e}")

def bot_loop():
    global LAST_CANDLE
    prev_price = get_price()
    time.sleep(10) # انتظار حتى يربط السيرفر
    calc_daily_levels() # اول حساب

    while True:
        try:
            now = datetime.now(BAGHDAD)
            live_price = get_price()

            # 1. كل يوم 00:00 حدث المستويات
            if now.hour == 0 and now.minute == 0 and now.second < 50:
                calc_daily_levels()
                time.sleep(70)
                continue

            # 2. فحص شمعة 15د جديدة - كل 00,15,30,45 دقيقة
            is_new_candle = (now.minute % 15 == 0 and now.second < 50)
            candle_id = now.strftime("%Y-%m-%d %H:%M")

            if is_new_candle and candle_id != LAST_CANDLE:
                log(f"شمعة 15د جديدة: {live_price:.2f}")
                for name, lvl in list(LEVELS.items()):
                    if not isinstance(lvl, float): continue
                    # شروط الكسر الحقيقي
                    if "S" in name and prev_price < lvl and live_price > lvl:
                        send_signal("BUY", name, lvl, live_price, prev_price)
                        LAST_CANDLE = candle_id
                        break
                    if "R" in name and prev_price > lvl and live_price < lvl:
                        send_signal("SELL", name, lvl, live_price, prev_price)
                        LAST_CANDLE = candle_id
                        break
                
                if candle_id != LAST_CANDLE:
                    LAST_CANDLE = candle_id # حتى لو ماكو كسر

            prev_price = live_price
            log(f"Live {live_price:.2f} | Candle {now.strftime('%H:%M')}")

        except Exception as e:
            log(f"Loop err {e}")
        time.sleep(30)

@app.route('/')
def home():
    price = get_price()
    return jsonify({
        "status": "✅ BOT WORKING 20 LEVELS",
        "live_price": price,
        "levels_date": LEVELS.get("date", "not yet"),
        "levels": LEVELS,
        "time_baghdad": datetime.now(BAGHDAD).isoformat()
    })

# شغل البوت بالخلفية بعد ما يشتغل Flask
threading.Thread(target=bot_loop, daemon=True).start()
