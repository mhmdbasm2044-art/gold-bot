import requests, time, os, datetime
import yfinance as yf
import pandas as pd
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TZ_BAGHDAD = pytz.timezone('Asia/Baghdad')

def send(msg):
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}", timeout=10)
    except: pass

def get_data_30m(symbol):
    try:
        df = yf.download(symbol, period="2d", interval="30m", progress=False, auto_adjust=True)
        if len(df) < 30: return None, None, None
        close = df['Close']
        if isinstance(close, pd.DataFrame): close = close.iloc[:,0]
        delta = close.diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rs = gain/loss
        rsi = 100 - (100/(1+rs))
        last_rsi = float(rsi.iloc[-1])
        last_price = float(close.iloc[-1])
        prev_price = float(close.iloc[-2])
        ch = ((last_price-prev_price)/prev_price)*100
        return last_price, last_rsi, ch
    except:
        return None, None, None

def get_daily_levels():
    try:
        df = yf.download("GC=F", period="1mo", interval="1h", progress=False, auto_adjust=True)
        if len(df) < 50: return None
        close = df['Close']; high = df['High']; low = df['Low']
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:,0]; high = high.iloc[:,0]; low = low.iloc[:,0]

        levels = []
        for i in range(2, len(df)-2):
            if high.iloc[i] > high.iloc[i-1] and high.iloc[i] > high.iloc[i-2] and high.iloc[i] > high.iloc[i+1] and high.iloc[i] > high.iloc[i+2]:
                levels.append(float(high.iloc[i]))
            if low.iloc[i] < low.iloc[i-1] and low.iloc[i] < low.iloc[i-2] and low.iloc[i] < low.iloc[i+1] and low.iloc[i] < low.iloc[i+2]:
                levels.append(float(low.iloc[i]))

        daily = yf.download("GC=F", period="5d", interval="1d", progress=False, auto_adjust=True)
        d_high = float(daily['High'].iloc[-1]); d_low = float(daily['Low'].iloc[-1]); d_close = float(daily['Close'].iloc[-1])
        levels.extend([d_high, d_low, d_close, daily['High'].iloc[-2], daily['Low'].iloc[-2]])

        current = float(close.iloc[-1])
        filtered = [x for x in set([round(v,2) for v in levels]) if current*0.90 < x < current*1.10]
        filtered = sorted(filtered, reverse=True)[:12]

        final = []
        for lvl in filtered:
            final.append(lvl)
            final.append(round(lvl - lvl*0.00045,2))

        return final[:24], d_close, d_high, d_low
    except Exception as e:
        print(f"Levels error {e}")
        return None

send("✅ بوت 30د + مستويات 10 بليل اشتغل\n💎 RSI 22 نادر 0.02 لوت\n🔥 RSI 30 عادي 0.01 لوت\n⏰ 24 رقم كل يوم 10 بليل\n💰 $50")

last_heart = 0
last_sig = 0
last_levels_day = None

while True:
    try:
        now_baghdad = datetime.datetime.now(TZ_BAGHDAD)

        # مستويات كل يوم 10 بليل
        if now_baghdad.hour == 22 and now_baghdad.minute < 5 and last_levels_day!= now_baghdad.date():
            res = get_daily_levels()
            if res:
                blocks, d_close, d_high, d_low = res
                msg = f"📊 مستويات ذهب باجر {now_baghdad.date() + datetime.timedelta(days=1)}\n"
                msg += f"💰 اغلاق اليوم ${d_close:.2f}\n"
                msg += f"📈 عالي ${d_high:.2f} واطي ${d_low:.2f}\n"
                msg += f"⏰ فريم 30د\n\n"
                for b in blocks:
                    msg += f"{b}\n"
                msg += f"\n💡 بيع يم الفوك، شراء يم الجوه"
                send(msg)
                last_levels_day = now_baghdad.date()

        gold, rg, cg = get_data_30m("GC=F")
        btc, rb, cb = get_data_30m("BTC-USD")

        # فحص حي كل ساعة
        if time.time() - last_heart > 3600:
            if gold and btc:
                send(f"💓 30د شغال\n🥇 ${gold:.1f} RSI {rg:.0f} {cg:+.2f}%\n₿ ${btc:.0f} RSI {rb:.0f} {cb:+.2f}%")
            last_heart = time.time()

        # اشارات 30د - كل 30 دقيقة
        if time.time() - last_sig > 1800:
            if gold:
                if rg <= 22 and cg < -0.3:
                    send(f"💎💎💎 شراء ذهب 30د الماس نادر\n💰 ${gold:.1f} RSI {rg:.0f}\n⛔ وقف ${gold*0.995:.1f}\n🎯 ${gold*1.015:.1f}\n📦 $50 = 0.02 لوت بقوة!\n💵 ربح $12.6")
                    last_sig = time.time()
                elif rg <= 30 and cg < -0.3:
                    send(f"🔥 شراء ذهب 30د عادي\n💰 ${gold:.1f} RSI {rg:.0f}\n⛔ ${gold*0.995:.1f}\n🎯 ${gold*1.015:.1f}\n📦 0.01 لوت\n💵 $6.3")
                    last_sig = time.time()
                elif rg >= 82 and cg > 0.3:
                    send(f"💎💎💎 بيع ذهب 30د الماس RSI {rg:.0f} ${gold:.1f}\n📦 0.02 لوت")
                    last_sig = time.time()
                elif rg >= 70 and cg > 0.3:
                    send(f"🔻 بيع ذهب 30د RSI {rg:.0f} ${gold:.1f}\n📦 0.01 لوت")
                    last_sig = time.time()

            if btc and time.time() - last_sig > 1800:
                if rb <= 30 and cb < -0.5:
                    send(f"🥇 شراء بتكوين 30د ${btc:.0f} RSI {rb:.0f}\n📦 0.01 لوت")
                    last_sig = time.time()

        time.sleep(120)
    except Exception as e:
        send(f"⚠️ {e}")
        time.sleep(60)
