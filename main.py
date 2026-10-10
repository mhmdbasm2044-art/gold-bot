import requests, time, os, threading
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, timezone
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

app = Flask(__name__)
@app.route('/')
def home(): return "Bot GOLD+BTC TP/SL running"
def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
threading.Thread(target=run_web, daemon=True).start()

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      data={"chat_id": CHAT_ID, "text": msg}, timeout=15)
    except: pass

def get_30m(symbol):
    try:
        df = yf.download(symbol, period="2d", interval="30m", progress=False, auto_adjust=True)
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

send("✅ بوت GOLD+BTC TP/SL اشتغل\n🥇 ذهب + ₿ بتكوين\n📊 وقف واهداف مفعلة")

t_gold = 0; t_btc = 0; t_levels = 0; t_heart = 0
last_day = None

while True:
    try:
        now = datetime.now(timezone.utc) + timedelta(hours=3)

        if time.time() - t_levels > 60:
            if now.hour == 22 and now.minute < 10 and last_day!= now.date():
                r = get_levels()
                if r:
                    b,c,h,l = r
                    txt = f"📊 مستويات ذهب باجر {now.date() + timedelta(days=1)}\n💰 ${c:.2f} عالي ${h:.2f} واطي ${l:.2f}\n\n"
                    for x in b: txt+=f"{x}\n"
                    send(txt)
                    last_day = now.date()
            t_levels = time.time()

        if time.time() - t_gold > 1800:
            g,rsi = get_30m("GC=F")
            if g:
                if rsi <= 22:
                    sl = g - 25; tp1 = g + 15; tp2 = g + 35
                    send(f"💎💎💎 [ذهب 30د الماس] شراء\n💰 دخول ${g:.1f}\nRSI {rsi:.0f}\n🛑 وقف ${sl:.1f} (-25$)\n✅ هدف1 ${tp1:.1f}\n✅ هدف2 ${tp2:.1f}\n📦 0.02 لوت")
                elif rsi <= 30:
                    sl = g - 20; tp1 = g + 12; tp2 = g + 28
                    send(f"🔥 [ذهب 30د] شراء\n💰 دخول ${g:.1f}\nRSI {rsi:.0f}\n🛑 وقف ${sl:.1f} (-20$)\n✅ هدف1 ${tp1:.1f}\n✅ هدف2 ${tp2:.1f}\n📦 0.01")
                elif rsi >= 82:
                    sl = g + 25; tp1 = g - 15; tp2 = g - 35
                    send(f"💎💎💎 [ذهب 30د الماس] بيع\n💰 دخول ${g:.1f}\nRSI {rsi:.0f}\n🛑 وقف ${sl:.1f} (+25$)\n✅ هدف1 ${tp1:.1f}\n✅ هدف2 ${tp2:.1f}\n📦 0.02")
                elif rsi >= 70:
                    sl = g + 20; tp1 = g - 12; tp2 = g - 28
                    send(f"🔻 [ذهب 30د] بيع\n💰 دخول ${g:.1f}\nRSI {rsi:.0f}\n🛑 وقف ${sl:.1f} (+20$)\n✅ هدف1 ${tp1:.1f}\n✅ هدف2 ${tp2:.1f}\n📦 0.01")
            t_gold = time.time()

        if time.time() - t_btc > 1800:
            btc,rsi = get_30m("BTC-USD")
            if btc:
                if rsi <= 22:
                    sl = btc * 0.985; tp1 = btc * 1.015; tp2 = btc * 1.035
                    send(f"💎💎💎 [بتكوين 30د الماس] شراء\n💰 دخول ${btc:.0f}\nRSI {rsi:.0f}\n🛑 وقف ${sl:.0f} (-1.5%)\n✅ هدف1 ${tp1:.0f}\n✅ هدف2 ${tp2:.0f}\n📦 0.02")
                elif rsi <= 30:
                    sl = btc * 0.988; tp1 = btc * 1.012; tp2 = btc * 1.025
                    send(f"🔥 [بتكوين 30د] شراء\n💰 دخول ${btc:.0f}\nRSI {rsi:.0f}\n🛑 وقف ${sl:.0f} (-1.2%)\n✅ هدف1 ${tp1:.0f}\n✅ هدف2 ${tp2:.0f}\n📦 0.01")
                elif rsi >= 82:
                    sl = btc * 1.015; tp1 = btc * 0.985; tp2 = btc * 0.965
                    send(f"💎💎💎 [بتكوين 30د الماس] بيع\n💰 دخول ${btc:.0f}\nRSI {rsi:.0f}\n🛑 وقف ${sl:.0f} (+1.5%)\n✅ هدف1 ${tp1:.0f}\n✅ هدف2 ${tp2:.0f}\n📦 0.02")
                elif rsi >= 70:
                    sl = btc * 1.012; tp1 = btc * 0.988; tp2 = btc * 0.975
                    send(f"🔻 [بتكوين 30د] بيع\n💰 دخول ${btc:.0f}\nRSI {rsi:.0f}\n🛑 وقف ${sl:.0f} (+1.2%)\n✅ هدف1 ${tp1:.0f}\n✅ هدف2 ${tp2:.0f}\n📦 0.01")
            t_btc = time.time() + 90

        if time.time() - t_heart > 3600:
            g,rsi = get_30m("GC=F")
            btc,rsi2 = get_30m("BTC-USD")
            if g and btc:
                send(f"💓 حي GOLD ${g:.0f} RSI {rsi:.0f} | BTC ${btc:.0f} RSI {rsi2:.0f} - {now.strftime('%H:%M')}")
            t_heart = time.time()

        time.sleep(20)
    except: time.sleep(30)
