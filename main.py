import requests, threading, time, os
from flask import Flask
from datetime import datetime
app=Flask(__name__)
BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
gold_hist=[]
def send(msg):
    try:
        r=requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHAT_ID,"text":msg,"parse_mode":"HTML"}, timeout=15)
        print(f"SEND {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"SEND ERR {e}")
def calc(h,l,c):
    p=(h+l+c)/3
    return {"R3":h+2*(p-l),"R2":p+(h-l),"R1":2*p-l,"P":p,"S1":2*p-h,"S2":p-(h-l),"S3":l-2*(h-p)}
def rsi(prices, period=14):
    if len(prices) < period+1: return 50
    gains=[]; losses=[]
    for i in range(1, len(prices)):
        diff=prices[i]-prices[i-1]
        gains.append(diff if diff>0 else 0)
        losses.append(abs(diff) if diff<0 else 0)
    avg_gain=sum(gains[-period:])/period
    avg_loss=sum(losses[-period:])/period
    if avg_loss==0: return 100
    return 100-(100/(1+avg_gain/avg_loss))
def get_levels():
    global gold_hist
    try:
        k=requests.get("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=3m&limit=30", timeout=10).json()
        closes=[float(x[4]) for x in k]
        btc_h=max([float(x[2]) for x in k[-20:]]); btc_l=min([float(x[3]) for x in k[-20:]]); btc_c=closes[-1]
        btc_lv=calc(btc_h,btc_l,btc_c); btc_rsi=rsi(closes)
        g=float(requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()['price'])
        gold_hist.append(g)
        if len(gold_hist)>30: gold_hist.pop(0)
        g_h=max(gold_hist[-20:]) if len(gold_hist)>=5 else g
        g_l=min(gold_hist[-20:]) if len(gold_hist)>=5 else g
        gold_lv=calc(g_h,g_l,g); gold_rsi=rsi(gold_hist)
        return gold_lv, btc_lv, g, btc_c, gold_rsi, btc_rsi
    except Exception as e:
        print(f"LEVEL ERR {e}"); return None
def job():
    last_hour=-1
    while True:
        now=datetime.now()
        if now.minute==0 and now.hour!=last_hour:
            d=get_levels()
            if d:
                gl,bl,gp,bp,grsi,brsi=d; last_hour=now.hour
                send(f"⏰ <b>{now.strftime('%H:00')}</b> 🥇 ${gp:.2f} RSI {grsi:.0f} | ₿ ${bp:,.0f} RSI {brsi:.0f}\nR1 Gold {gl['R1']:.2f} S1 {gl['S1']:.2f}")
        time.sleep(180)
@app.route("/")
def home(): return "✅ شغال - لستة + RSI"
@app.route("/test")
def test():
    d=get_levels()
    if not d: return "fail get_levels"
    gl,bl,gp,bp,grsi,brsi=d
    send(f"🧪 <b>تيست فوري</b>\n🥇 ذهب ${gp:.2f} RSI {grsi:.0f}\nR1 {gl['R1']:.2f} S1 {gl['S1']:.2f}\n₿ ${bp:,.0f} RSI {brsi:.0f}")
    return "sent check telegram"
threading.Thread(target=job, daemon=True).start()
if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
