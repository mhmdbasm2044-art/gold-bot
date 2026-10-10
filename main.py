import requests, threading, time, os
from flask import Flask
from datetime import datetime

app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
gold_hist = []
btc_hist = []

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=15)
        print(f"SEND {r.status_code}")
    except Exception as e:
        print(f"SEND ERR {e}")

def calc(h,l,c):
    p=(h+l+c)/3
    return {"R3":h+2*(p-l),"R2":p+(h-l),"R1":2*p-l,"P":p,"S1":2*p-h,"S2":p-(h-l),"S3":l-2*(h-p)}

def rsi(prices, period=14):
    if len(prices) < period+1: return 55
    gains=[]; losses=[]
    for i in range(1, len(prices)):
        d=prices[i]-prices[i-1]
        gains.append(d if d>0 else 0)
        losses.append(abs(d) if d<0 else 0)
    ag=sum(gains[-period:])/period
    al=sum(losses[-period:])/period
    if al==0: return 80
    return 100-(100/(1+ag/al))

def get_levels():
    global gold_hist, btc_hist
    try:
        # BTC من CoinGecko - شغال بكل مكان
        btc_c = 115000.0
        try:
            j = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10).json()
            btc_c = float(j['bitcoin']['usd'])
        except Exception as e:
            print(f"COINGECKO ERR {e}")

        btc_hist.append(btc_c)
        if len(btc_hist)>50: btc_hist.pop(0)
        btc_h = max(btc_hist[-20:]) if len(btc_hist)>=5 else btc_c*1.005
        btc_l = min(btc_hist[-20:]) if len(btc_hist)>=5 else btc_c*0.995

        # Gold
        g = 4200.0
        try:
            g = float(requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()['price'])
        except:
            g = gold_hist[-1] if gold_hist else 4200.0

        gold_hist.append(g)
        if len(gold_hist)>50: gold_hist.pop(0)
        g_h = max(gold_hist[-20:]) if len(gold_hist)>=5 else g*1.003
        g_l = min(gold_hist[-20:]) if len(gold_hist)>=5 else g*0.997

        print(f"OK Gold {g} BTC {btc_c}")
        return calc(g_h,g_l,g), calc(btc_h,btc_l,btc_c), g, btc_c, rsi(gold_hist), rsi(btc_hist)
    except Exception as e:
        print(f"LEVEL ERR {e}")
        import traceback; traceback.print_exc()
        return None

def job():
    last_hour=-1
    while True:
        now=datetime.now()
        if now.minute==0 and now.hour!=last_hour:
            d=get_levels()
            if d:
                last_hour=now.hour
                gl,bl,gp,bp,grsi,brsi=d
                send(f"⏰ <b>{now.strftime('%H:00')}</b> 🥇 ${gp:.2f} RSI {grsi:.0f} | ₿ ${bp:,.0f} RSI {brsi:.0f}\nR1 Gold {gl['R1']:.2f} S1 {gl['S1']:.2f} | R1 BTC {bl['R1']:,.0f} S1 {bl['S1']:,.0f}")
        time.sleep(20)

@app.route("/")
def home(): return "✅ شغال"

@app.route("/test")
def test():
    d=get_levels()
    if not d: return "❌ fail get_levels - شوف Logs"
    gl,bl,gp,bp,grsi,brsi=d
    send(f"🧪 <b>تيست فوري</b>\n🥇 ${gp:.2f} RSI {grsi:.0f}\nR1 {gl['R1']:.2f} S1 {gl['S1']:.2f}\n₿ ${bp:,.0f} RSI {brsi:.0f}")
    return "✅ sent!"

threading.Thread(target=job, daemon=True).start()
if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
