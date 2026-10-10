import requests, time, os, threading
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# هذا حتى Render يشوف بورت مفتوح
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running 30m + levels"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      data={"chat_id": CHAT_ID, "text": msg}, timeout=15)
        print(f"Sent {msg[:20]}")
    except Exception as e:
        print(f"Send error {e}")

def get_30m():
    try:
        df = yf.download("GC=F", period="2d", interval="30m", progress=False, auto_adjust=True)
        if len(df) < 20: return None, None
        close = df['Close']
        if isinstance(close, pd.DataFrame): close = close.iloc[:,0]
        delta = close.diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rs = gain/loss
        rsi = 100 - (100/(1+rs))
        return float(close.iloc[-1]), float(rsi.iloc[-1])
    except: return None, None

def get_levels():
    try:
        df = yf.download("GC=F", period="1mo", interval="1h", progress=False, auto_adjust=True)
        close = df['Close']; high = df['High']; low = df['Low']
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:,0]; high = high.iloc[:,0]; low = low.iloc[:,0]
        lvls = []
        for i in range(2, len(df)-2):
            if high.iloc[i] > high.iloc[i-1] and high.iloc[i] > high.iloc[i-2] and high.iloc[i] > high.iloc[i+1] and high.iloc[i] > high.iloc[i+2]:
                lvls.append(float(high.iloc[i]))
            if low.iloc[i] < low.iloc[i-1] and low.iloc[i] < low.iloc[i-2] and low.iloc[i] < low.iloc[i+1] and low.iloc[i] < low.iloc[i+2]:
                lvls.append(float(low.iloc[i]))
        d = yf.download("GC=F", period="5d", interval="1d", progress=False, auto_adjust=True)
        dh = float(d['High'].iloc[-1]); dl = float(d['Low'].iloc[-1]); dc = float(d['Close'].iloc[-1])
        lvls.extend([dh, dl, dc])
        cur = float(close.iloc[-1])
        filt = sorted(set([round(x,2) for x in lvls if cur*0.9 < x < cur*1.1]), reverse=True)[:12]
        final = []
        for x in filt:
            final.append(x); final.append(round(x - x*0.00045,2))
        return final[:24], dc, dh, dl
    except: return None

send("✅ البوت النهائي اشتغل\n🔹 30د كل 30 دقيقة\n🔹 24 رقم 10 بليل\n🔹 هجين 22=0.02 30=0.01")

t1 = 0; t2 = 0; t3 = 0
last_day = None

while True:
    try:
        now = datetime.utcnow() + timedelta(hours=3)
        if time.time() - t1 > 60:
            if now.hour == 22 and now.minute < 10 and last_day!= now.date():
                r = get_levels()
                if r:
                    b,c,h,l = r
                    txt = f"📊 مستويات باجر {now.date() + timedelta(days=1)}\n💰 ${c:.2f} عالي ${h:.2f} واطي ${l:.2f}\n\n"
                    for x in b: txt+=f"{x}\n"
                    send(txt)
                    last_day = now.date()
            t1 = time.time()
        if time.time() - t2 > 1800:
            g,rsi = get_30m()
            if g:
                if rsi <= 22: send(f"💎💎💎 [30د الماس] شراء ${g:.1f} RSI {rsi:.0f} 0.02 لوت")
                elif rsi <= 30: send(f"🔥 [30د] شراء ${g:.1f} RSI {rsi:.0f} 0.01 لوت")
                elif rsi >= 82: send(f"💎💎💎 [30د الماس] بيع ${g:.1f} RSI {rsi:.0f} 0.02")
                elif rsi >= 70: send(f"🔻 [30د] بيع ${g:.1f} RSI {rsi:.0f} 0.01")
            t2 = time.time()
        if time.time() - t3 > 3600:
            g,rsi = get_30m()
            if g: send(f"💓 حي 30د ${g:.1f} RSI {rsi:.0f} - {now.strftime('%H:%M')}")
            t3 = time.time()
        time.sleep(20)
    except: time.sleep(30)
