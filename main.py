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
    if down==0: return 85
    return 100-(100/(1+(up/14)/(down/14)))

def job():
    global last_min
    while True:
        now = datetime.now()
        # كل 30 دقيقة: 00 و 30
        if now.minute % 30 == 0 and now.minute!= last_min:
            last_min = now.minute
            try:
                try: gold = float(requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()['price'])
                except: gold = gold_hist[-1] if gold_hist else 4195
                try: btc = float(requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10).json()['bitcoin']['usd'])
                except: btc = btc_hist[-1] if btc_hist else 82000

                gold_hist.append(gold); btc_hist.append(btc)
                if len(gold_hist)>200: gold_hist.pop(0)
                if len(btc_hist)>200: btc_hist.pop(0)
                if len(gold_hist) < 16: time.sleep(60); continue

                g_rsi = rsi(gold_hist)
                b_rsi = rsi(btc_hist)
                g_change = (gold_hist[-1]-gold_hist[-2])/gold_hist[-2]*100 if len(gold_hist)>=2 else 0
                b_change = (btc_hist[-1]-btc_hist[-2])/btc_hist[-2]*100 if len(btc_hist)>=2 else 0

                # ===== ذهب =====
                g_msg = f"⏰ {now.strftime('%H:%M')} | 🥇 ذهب 30m\n💰 ${gold:.2f} ({g_change:+.2f}%)\n📊 RSI {g_rsi:.0f}"
                if g_rsi <= 22:
                    g_msg += f"\n\n🔥🔥 شراء نادر جدا\n⛔ وقف {gold*0.995:.2f} (-0.5%)\n🎯 TP1 {gold*1.006:.2f} (+0.6%)\n🎯 TP2 {gold*1.015:.2f} (+1.5%)\n🎯 TP3 {gold*1.02:.2f} (+2%)\n💡 مخاطرة 1:3"
                elif g_rsi >= 82:
                    g_msg += f"\n\n🔥🔥 بيع نادر جدا\n⛔ وقف {gold*1.005:.2f} (+0.5%)\n🎯 TP1 {gold*0.994:.2f} (-0.6%)\n🎯 TP2 {gold*0.985:.2f} (-1.5%)\n🎯 TP3 {gold*0.98:.2f} (-2%)\n💡 مخاطرة 1:3"
                elif g_rsi <= 32 and g_change >= 0.6:
                    g_msg += f"\n\n🐋 حوت شراء قوي {g_change:.2f}%\n⛔ وقف {gold*0.995:.2f}\n🎯 TP1 {gold*1.008:.2f} (+0.8%)\n🎯 TP2 {gold*1.015:.2f} (+1.5%)"
                elif g_rsi >= 72 and g_change <= -0.6:
                    g_msg += f"\n\n🐋 حوت بيع قوي {g_change:.2f}%\n⛔ وقف {gold*1.005:.2f}\n🎯 TP1 {gold*0.992:.2f} (-0.8%)\n🎯 TP2 {gold*0.985:.2f} (-1.5%)"
                else:
                    g_msg += f"\n⚪ انتظار - ماكو اشارة"

                # ===== بتكوين =====
                b_msg = f"⏰ {now.strftime('%H:%M')} | ₿ بتكوين 30m\n💰 ${btc:,.0f} ({b_change:+.2f}%)\n📊 RSI {b_rsi:.0f}"
                if b_rsi <= 22:
                    b_msg += f"\n\n🔥🔥 شراء نادر جدا\n⛔ وقف {btc*0.99:,.0f} (-1%)\n🎯 TP1 {btc*1.012:,.0f} (+1.2%)\n🎯 TP2 {btc*1.025:,.0f} (+2.5%)\n🎯 TP3 {btc*1.04:,.0f} (+4%)"
                elif b_rsi >= 82:
                    b_msg += f"\n\n🔥🔥 بيع نادر جدا\n⛔ وقف {btc*1.01:,.0f} (+1%)\n🎯 TP1 {btc*0.988:,.0f} (-1.2%)\n🎯 TP2 {btc*0.975:,.0f} (-2.5%)\n🎯 TP3 {btc*0.96:,.0f} (-4%)"
                elif b_rsi <= 32 and b_change >= 1.2:
                    b_msg += f"\n\n🐋 حوت شراء قوي {b_change:.2f}%\n⛔ وقف {btc*0.99:,.0f}\n🎯 TP1 {btc*1.015:,.0f} (+1.5%)\n🎯 TP2 {btc*1.025:,.0f} (+2.5%)"
                elif b_rsi >= 72 and b_change <= -1.2:
                    b_msg += f"\n\n🐋 حوت بيع قوي {b_change:.2f}%\n⛔ وقف {btc*1.01:,.0f}\n🎯 TP1 {btc*0.985:,.0f} (-1.5%)\n🎯 TP2 {btc*0.975:,.0f} (-2.5%)"
                else:
                    b_msg += f"\n⚪ انتظار - ماكو اشارة"

                send(g_msg)
                time.sleep(2)
                send(b_msg)

                time.sleep(60)
            except Exception as e: print(f"Error: {e}"); time.sleep(10)
        time.sleep(5)

@app.route("/")
def home(): return "30m final ok"
@app.route("/test")
def test():
    send("⏰ 10:30 | 🥇 ذهب 30m\n💰 $4195.60 (+0.30%)\n📊 RSI 55\n⚪ انتظار - ماكو اشارة")
    time.sleep(1)
    send("⏰ 10:30 | ₿ بتكوين 30m\n💰 $82,774 (+0.50%)\n📊 RSI 58\n⚪ انتظار - ماكو اشارة")
    return "sent 30m test"

threading.Thread(target=job, daemon=True).start()
if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
