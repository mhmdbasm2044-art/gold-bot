import requests, threading, time, os
from flask import Flask
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
gold_hist = []
btc_hist = []

def send(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print(f"ERROR: BOT_TOKEN or CHAT_ID missing! BOT={bool(BOT_TOKEN)} CHAT={bool(CHAT_ID)}")
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=15)
        print(f"SEND {r.status_code}: {r.text[:300]}")
    except Exception as e:
        print(f"SEND ERR {e}")

def calc(h,l,c):
    p=(h+l+c)/3
    return {"R3":h+2*(p-l),"R2":p+(h-l),"R1":2*p-l,"P":p,"S1":2*p-h,"S2":p-(h-l),"S3":l-2*(h-p)}

def rsi(prices, period=14):
    if len(prices) < period+1: return 50
    gains=[]; losses=[]
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        gains.append(diff if diff>0 else 0)
        losses.append(abs(diff) if diff<0 else 0)
    avg_gain = sum(gains[-period:])/period
    avg_loss = sum(losses[-period:])/period
    if avg_loss == 0: return 100
    rs = avg_gain/avg_loss
    return 100 - (100/(1+rs))

def get_levels():
    global gold_hist, btc_hist
    try:
        # --- BTC ---
        k = requests.get("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=3m&limit=30", timeout=10).json()
        closes = [float(x[4]) for x in k]
        highs = [float(x[2]) for x in k]
        lows = [float(x[3]) for x in k]
        btc_h = max(highs[-20:])
        btc_l = min(lows[-20:])
        btc_c = closes[-1]
        btc_hist = closes
        btc_lv = calc(btc_h, btc_l, btc_c)
        btc_rsi = rsi(closes)

        # --- GOLD مع حماية ---
        g = None
        try:
            g = float(requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()['price'])
        except Exception as e:
            print(f"GOLD API ERR {e}")

        if g is None:
            g = gold_hist[-1] if gold_hist else 4200.0

        gold_hist.append(g)
        if len(gold_hist) > 50: gold_hist.pop(0)

        g_h = max(gold_hist[-20:]) if len(gold_hist) >= 5 else g
        g_l = min(gold_hist[-20:]) if len(gold_hist) >= 5 else g
        gold_lv = calc(g_h, g_l, g)
        gold_rsi = rsi(gold_hist)

        print(f"LEVELS OK: Gold {g:.2f} RSI {gold_rsi:.0f} | BTC {btc_c:.0f} RSI {btc_rsi:.0f}")
        return gold_lv, btc_lv, g, btc_c, gold_rsi, btc_rsi

    except Exception as e:
        print(f"LEVEL ERR {e}")
        return None

def job():
    last_hour = -1
    print("JOB started, waiting for full hour")
    while True:
        now = datetime.now()
        if now.minute == 0 and now.hour!= last_hour:
            d = get_levels()
            if d:
                gl, bl, gp, bp, grsi, brsi = d
                last_hour = now.hour

                gold_signal = "⚪ انتظر"
                if grsi > 70 and gp >= gl['R1']: gold_signal = "🔴 بيع قوي عند R1"
                elif grsi < 30 and gp <= gl['S1']: gold_signal = "🟢 شراء قوي عند S1"

                btc_signal = "⚪ انتظر"
                if brsi > 70 and bp >= bl['R1']: btc_signal = "🔴 بيع قوي"
                elif brsi < 30 and bp <= bl['S1']: btc_signal = "🟢 شراء قوي"

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
        time.sleep(20)

@app.route("/")
def home():
    return "✅ شغال - لستة + RSI - /test للفحص"

@app.route("/test")
def test():
    print("TEST called")
    d = get_levels()
    if not d:
        return "❌ fail get_levels - شوف Logs"
    gl, bl, gp, bp, grsi, brsi = d
    send(f"🧪 <b>تيست فوري</b>\n🥇 ذهب ${gp:.2f} RSI {grsi:.0f}\nR1 {gl['R1']:.2f} S1 {gl['S1']:.2f}\n₿ ${bp:,.0f} RSI {brsi:.0f}")
    return "✅ sent! check telegram & logs"

threading.Thread(target=job, daemon=True).start()

if __name__ == "__main__":
    print(f"START: BOT_TOKEN exists={bool(BOT_TOKEN)} CHAT_ID exists={bool(CHAT_ID)}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
