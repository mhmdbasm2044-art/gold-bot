from flask import Flask
import threading, time, requests, os
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# اعدادات الذهب - تكدر تغيرها
BUY_PRICE = 3900   # اذا نزل جوة هذا يشتري
SELL_PRICE = 4100  # اذا صعد فوك هذا يبيع

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(e)

def get_gold_price():
    try:
        # مصدرين حتى اذا واحد وكع
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        return float(r.get('price', 0))
    except:
        return 0

def check_gold():
    last_signal = ""
    while True:
        price = get_gold_price()
        now = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        print(f"[{now}] Gold: {price}")
        
        if price == 0:
            time.sleep(60)
            continue

        if price <= BUY_PRICE and last_signal != "BUY":
            msg = f"""
🟢 *فرصة شراء - الذهب نزل*

💰 *السعر الحالي:* `{price:.2f}$`
📉 *سعر الشراء المحدد:* `{BUY_PRICE}$`
⏰ *الوقت:* {now}

📊 *التحليل:* الذهب نازل وجاهز للصعود، وقت مناسب للشراء.

#ذهب #شراء
"""
            send(msg)
            last_signal = "BUY"
        
        elif price >= SELL_PRICE and last_signal != "SELL":
            msg = f"""
🔴 *فرصة بيع - الذهب صعد*

💰 *السعر الحالي:* `{price:.2f}$`
📈 *سعر البيع المحدد:* `{SELL_PRICE}$`
⏰ *الوقت:* {now}

📊 *التحليل:* الذهب صاعد بقوة، وقت مناسب لجني الارباح.

#ذهب #بيع
"""
            send(msg)
            last_signal = "SELL"
        
        # كل 5 دقايق يفحص
        time.sleep(300)

@app.route('/')
def home():
    price = get_gold_price()
    return f"Gold Bot شغال ✅ السعر هسه {price}$ - يفحص كل 5 دقايق"

threading.Thread(target=check_gold, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
