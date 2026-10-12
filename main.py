import os, time, threading
from datetime import datetime
from flask import Flask
import requests

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "ضع_توكن_البوت_هنا")
CHAT_ID = os.environ.get("CHAT_ID", "ضع_الايدي_هنا")

daily_levels = []
last_price = 0
last_15m_slot = ""
touched = {} # نتذكر يا مستوى انلمس

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(e)

def get_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        return float(r.get('price', 0))
    except:
        return 0

def build_levels(price):
    # مستويات حقيقية - Pivot + نفسية
    base = int(price // 50) * 50
    # 7 مستويات قوية قريبة
    levels = [base-100, base-50, base-25, base, base+25, base+50, base+100]
    return sorted(levels)

def check_market():
    global daily_levels, last_price, last_15m_slot, touched
    last_day = ""
    send("✅ بوت اللمس والارتداد اشتغل - 15د")
    
    while True:
        try:
            price = get_price()
            if price == 0:
                time.sleep(20)
                continue

            now = datetime.utcnow()
            today_str = now.strftime("%Y-%m-%d")
            slot_15m = f"{today_str} {now.hour}:{int(now.minute/15)*15}"

            # كل يوم مستويات جديدة
            if today_str != last_day:
                daily_levels = build_levels(price)
                last_day = today_str
                touched = {}
                txt = f"📊 مستويات اليوم {today_str}\nسعر: {price:.2f}$\n\n"
                for lv in daily_levels:
                    txt += f"{lv}$\n"
                txt += "\nبانتظار لمس + ارتداد"
                send(txt)

            # هل لمس اي مستوى؟ (قريب 2$)
            for level in daily_levels:
                if abs(price - level) <= 2.5:
                    touched[level] = True
                    print(f"Touched {level}")

            # هل انفتحت شمعة 15د جديدة؟
            is_new_candle = (slot_15m != last_15m_slot) and (now.minute % 15 == 0) and (now.second < 50)

            if is_new_candle and last_price != 0:
                for level in daily_levels:
                    # اذا انلمس قبل شوية وهسه رجع جوه
                    if touched.get(level):
                        # لمس مقاومة ورجع جوه = بيع
                        if last_price >= level and price < level:
                            send(f"🔻 *بيع - ارتداد من مقاومة*\n\nالمستوى: `{level}$`\nلمس {level}$ ورجع يفتح شمعة جديدة جوه\n\nدخول: `{price:.2f}$`\n🔴 ستوب: `{price+4:.2f}$`\n🟢 هدف: `{price-8:.2f}$`\n⏰ 15د - {now.strftime('%H:%M UTC')}")
                            touched[level] = False
                        
                        # لمس دعم ورجع جوه = شراء
                        elif last_price <= level and price > level:
                            send(f"🚀 *شراء - ارتداد من دعم*\n\nالمستوى: `{level}$`\nلمس {level}$ ورجع يفتح شمعة جديدة جوه\n\nدخول: `{price:.2f}$`\n🔴 ستوب: `{price-4:.2f}$`\n🟢 هدف: `{price+8:.2f}$`\n⏰ 15د - {now.strftime('%H:%M UTC')}")
                            touched[level] = False

                last_15m_slot = slot_15m

            if last_15m_slot == "":
                last_15m_slot = slot_15m

            last_price = price

        except Exception as e:
            print(e)
        time.sleep(20)

threading.Thread(target=check_market, daemon=True).start()

@app.route("/")
def home():
    return f"Touch & Rebound Bot | Price {last_price} | Levels {daily_levels} | Touched {touched}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
