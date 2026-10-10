import requests, threading, time, os
from flask import Flask
from datetime import datetime

app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
gold_hist = []

def send(msg):
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=15)
    except: pass

def calc(h,l,c):
    p=(h+l+c)/3
    return {"R3":h+2*(p-l),"R2":p+(h-l),"R1":2*p-l,"P":p,"S1":2*p-h,"S2":p-(h-l),"S3":l-2*(h-p)}

def rsi(prices, period=14):
    if len(prices) < period+1: return 50
    gains=[]; losses=[]
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        if diff>0: gains.append(diff); losses.append(0)
        else: gains.append(0); losses.append(abs(diff))
    avg_gain = sum(gains[-period:])/period
    avg_loss = sum(losses[-period:])/period
    if avg_loss==0: return 100
    rs = avg_gain/avg_loss
    return 100 - (100/(1+rs))

def get_levels():
    global gold_hist
    try:
        k=requests.get("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=3m&limit=30", timeout=10).json()
        closes=[float(x[4]) for x in k]
        btc_h=max([float(x[2]) for x in k[-20:]]); btc_l=min([float(x[3]) for x in k[-20:]]); btc_c=closes[-1]
        btc_lv=calc(btc_h,btc_l,btc_c)
        btc_rsi=rsi(closes)

        g=float(requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()['price'])
        gold_hist.append(g)
        if len(gold_hist)>30: gold_hist.pop(0)
        g_h=max(gold_hist[-20:]); g_l=min(gold_hist[-20:])
        gold_lv=calc(g_h,g_l,g)
        gold_rsi=rsi(gold_hist)

        return gold_lv, btc_lv, g, btc_c, gold_rsi, btc_rsi
    except: return None

def job():
    last_hour=-1
    while True:
        now=datetime.now()
        if now.minute==0 and now.hour!=last_hour:
            d=get_levels()
            if d:
                gl,bl,gp,bp,grsi,brsi=d
                last_hour=now.hour

                # تحليل الدخول
                gold_signal = ""
                if grsi>70 and gp>=gl['R1']: gold_signal="🔴 بيع قوي عند R1 (RSI متشبع)"
                elif grsi<30 and gp<=gl['S1']: gold_signal="🟢 شراء قوي عند S1 (RSI هابط)"
                else: gold_signal="⚪ انتظر كسر واضح"

                btc_signal = ""
                if brsi>70 and bp>=bl['R1']: btc_signal="🔴 بيع قوي عند R1"
                elif brsi<30 and bp<=bl['S1']: btc_signal="🟢 شراء قوي عند S1"
                else: btc_signal="⚪ انتظر كسر"

                send(f"""⏰ <b>لستة {now.strftime('%H:00')} - 3د + RSI</b>

🥇 <b>ذهب ${gp:.2f} | RSI {grsi:.0f}</b>
R3 {gl['R3']:.2f} | R2 {gl['R2']:.2f} | R1 {gl['R1']:.2f}
P {gl['P']:.2f}
S1 {gl['S1']:.2f} | S2 {gl['S2']:.2f} | S3 {gl['S3']:.2f}
{gold_signal}

₿ <b>بتكوين ${bp:,.0f} | RSI {brsi:.0f}</b>
R3 {bl['R3']:,.0f} | R2 {bl['R2']:,.0f} | R1 {bl['R1']:,.0f}
P {bl['P']:,.0f}
S1 {bl['S1']:,.0f} | S2 {bl['S2']:,.0f} | S3 {bl['S3']:,.0f}
{btc_signal}
""")
        get_levels()
        time.sleep(180)

@app.route("/")
def home(): return "✅ شغال - لستة + RSI"

threading.Thread(target=job, daemon=True).start()
if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
