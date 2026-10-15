import os, time, requests, json, websocket
import matplotlib.pyplot as plt

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SYMBOLS = ["BOOM1000", "CRASH1000", "BOOM500", "CRASH500"]

def send_msg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    except: pass

def send_chart(symbol, candles, rsi):
    try:
        closes = [float(c['close']) for c in candles]
        plt.figure(figsize=(8,4))
        plt.plot(closes, color='blue', linewidth=2)
        plt.title(f"{symbol} - RSI: {rsi:.1f}")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig("chart.png")
        plt.close()

        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        caption = f"📊 *{symbol}*\nRSI: {rsi:.1f}\nالسعر: {closes[-1]}"
        with open("chart.png", "rb") as f:
            requests.post(url, data={"chat_id": CHAT_ID, "caption": caption, "parse_mode": "Markdown"}, files={"photo": f})
    except Exception as e:
        print(f"Chart error: {e}")

def get_data(symbol):
    try:
        ws = websocket.create_connection("wss://ws.derivws.com/websockets/v3?app_id=1089", timeout=10)
        ws.send(json.dumps({"ticks_history": symbol, "count": 50, "end": "latest", "style": "candles", "granularity": 60}))
        candles = json.loads(ws.recv()).get('candles', [])
        ws.close()
        return candles
    except: return []

def calc_rsi(candles):
    if len(candles) < 15: return 50
    closes = [float(c['close']) for c in candles]
    g=l=0
    for i in range(1,15):
        d=closes[-i]-closes[-i-1]
        if d>0: g+=d
        else: l+=abs(d)
    if l==0: return 75
    return 100 - (100/(1+(g/14)/(l/14)))

send_msg("🚀 *بوت BOOM & CRASH مع شارت اشتغل*\nراح يدز صورة شارت مع كل اشارة")

while True:
    for sym in SYMBOLS:
        try:
            candles = get_data(sym)
            if not candles: continue
            rsi = calc_rsi(candles)
            price = candles[-1]['close']
            print(f"{sym} RSI {rsi:.1f}")

            if "BOOM" in sym and rsi < 25:
                send_msg(f"💥 *{sym} شراء قوي*\nRSI: {rsi:.1f}")
                send_chart(sym, candles, rsi)

            if "CRASH" in sym and rsi > 75:
                send_msg(f"📉 *{sym} بيع قوي*\nRSI: {rsi:.1f}")
                send_chart(sym, candles, rsi)

            time.sleep(3)
        except Exception as e:
            print(e)
    time.sleep(60)
