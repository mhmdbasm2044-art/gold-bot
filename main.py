import requests, threading, time, os
from flask import Flask
from datetime import datetime

app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
gold_hist = []
btc_hist = []
last_min = -1

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=15)
    except: pass

def rsi(prices):
    if len(prices) < 15: return 50
    up = sum(max(0, prices[i]-prices[i-1]) for i in range(-14,0))
    down = sum(max(0, prices[i-1]-prices[i]) for i in range(-14,0))
    if down==0: return 80
    return 100-(100/(1+(up/14)/(down/14)))

def job():
    global last_min
    while True:
        now = datetime.now()
        if now.minute % 5 == 0 and now.minute!= last_min:
            last_min = now.minute
            try:
                try: gold = float(requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()['price'])
                except: gold = gold_hist[-1] if gold_hist else 4195
                try: btc = float(requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10).json()['bitcoin']['usd'])
                except: btc = btc_hist[-1] if btc_hist else 82000

                gold_hist.append(gold); btc_hist.append(btc)
                if len(gold_hist)>200: gold_hist.pop(0)
                if len(btc_hist)>200: btc_hist.pop(0)

                if len(gold_hist) < 16:
                    time.sleep(60)
                    continue

                g_change = (gold_hist[-1]-gold_hist[-2])/gold_hist[-2]*100
                b_change = (btc_hist[-1]-btc_hist[-2])/btc_hist[-2]*100
                g_rsi = rsi(gold_hist)
                b_rsi = rsi(btc_hist)

                msgs = []

                # ذهب
                if g_rsi <= 25:
                    sl=gold*0.997; tp=gold*1.008
                    msgs.append(f"🥇 <b>ذهب ${gold:.2f}</b>\n🟢🟢 شراء قوي جدا RSI {g_rsi:.0f}\n👉 ادخل فورا\n⛔ وقف {sl:.2f} | 🎯 هدف {tp:.2f}")
                elif g_rsi <= 35 and g_change > 0.35:
                    sl=gold*0.997; tp=gold*1.008
                    msgs.append(f"🥇 <b>ذهب ${gold:.2f} ({g_change:+.2f}%)</b>\n🟢🟢 شراء قوي + 🐋 حوت\n👉 ادخل ويا الحوت\n⛔ وقف {sl:.2f} | 🎯 {tp:.2f}")
                elif g_rsi >= 80:
                    sl=gold*1.003; tp=gold*0.992
                    msgs.append(f"🥇 <b>ذهب ${gold:.2f}</b>\n🔴🔴 بيع قوي جدا RSI {g_rsi:.0f}\n👉 بيع فورا\n⛔ وقف {sl:.2f} | 🎯 هدف {tp:.2f}")
                elif g_rsi >= 68 and g_change < -0.35:
                    sl=gold*1.003; tp=gold*0.992
                    msgs.append(f"🥇 <b>ذهب ${gold:.2f} ({g_change:+.2f}%)</b>\n🔴🔴 بيع قوي + 🐋 حوت\n👉 بيع ويا الحوت\n⛔ وقف {sl:.2f} | 🎯 {tp:.2f}")

                # بتكوين
                if b_rsi <= 25:
                    sl=btc*0.993; tp=btc*1.015
                    msgs.append(f"₿ <b>بتكوين ${btc:,.0f}</b>\n🟢🟢 شراء قوي جدا RSI {b_rsi:.0f}\n👉 ادخل فورا\n⛔ وقف {sl:,.0f} | 🎯 {tp:,.0f}")
                elif b_rsi <= 35 and b_change > 0.8:
                    sl=btc*0.993; tp=btc*1.015
                    msgs.append(f"₿ <b>بتكوين ${btc:,.0f} ({b_change:+.2f}%)</b>\n🟢🟢 شراء قوي + 🐋 حوت\n👉 ادخل ويا الحوت\n⛔ وقف {sl:,.0f} | 🎯 {tp:,.0f}")
                elif b_rsi >= 80:
                    sl=btc*1.007; tp=btc*0.985
                    msgs.append(f"₿ <b>بتكوين ${btc:,.0f}</b>\n🔴🔴 بيع قوي جدا RSI {b_rsi:.0f}\n👉 بيع فورا\n⛔ وقف {sl:,.0f} | 🎯 {tp:,.0f}")
                elif b_rsi >= 68 and b_change < -0.8:
                    sl=btc*1.007; tp=btc*0.985
                    msgs.append(f"₿ <b>بتكوين ${btc:,.0f} ({b_change:+.2f}%)</b>\n🔴🔴 بيع قوي + 🐋 حوت\n👉 بيع ويا الحوت\n⛔ وقف {sl:,.0f} | 🎯 {tp:,.0f}")

                if msgs:
                    send(f"⏰ <b>{now.strftime('%H:%M')} - 5m اشارة قوية فقط</b>\n\n" + "\n\n---\n\n".join(msgs))

                time.sleep(60)
            except Exception as e:
                print(e); time.sleep(10)
        time.sleep(5)

@app.route("/")
def home(): return "5m strong only ok"

@app.route("/test")
def test():
    send("🧪 <b>البوت المصغر شغال</b>\nفريم 5 دقايق\nراح تجيك رسالة بس اذا:\n🟢🟢 شراء قوي جدا\n🔴🔴 بيع قوي جدا\n🐋 حوت دخل\n\nاذا السوق هادئ ما راح يزعجك برسائل")
    return "sent mini"

threading.Thread(target=job, daemon=True).start()
if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
