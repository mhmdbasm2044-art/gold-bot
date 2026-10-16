import os, json, asyncio, websockets, requests, threading, io, time
from collections import deque
from flask import Flask
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
app = Flask(__name__)

# شموع لكل رمز
data_store = {
    "BOOM1000": deque(maxlen=50),
    "CRASH1000": deque(maxlen=50)
}

def send_chart(symbol, break_price, peak, candles):
    try:
        fig, ax = plt.subplots(figsize=(8,4))
        d = list(candles)[-30:]
        opens = [c["open"] for c in d]
        highs = [c["high"] for c in d]
        lows = [c["low"] for c in d]
        closes = [c["close"] for c in d]

        for i in range(len(d)):
            color = 'green' if closes[i] >= opens[i] else 'red'
            ax.plot([i, i], [lows[i], highs[i]], color='black', linewidth=1)
            ax.plot([i, i], [opens[i], closes[i]], color=color, linewidth=4)
            if highs[i] == break_price and symbol == "BOOM1000":
                ax.scatter(i, highs[i], color='blue', s=120)
            if lows[i] == break_price and symbol == "CRASH1000":
                ax.scatter(i, lows[i], color='blue', s=120)

        if symbol == "BOOM1000":
            ax.axhline(y=peak, color='red', linestyle='--', label=f'قمة {peak:.2f}')
            title = f"{symbol} - 1m BREAK UP {peak:.2f}->{break_price:.2f}"
            caption = f"📊 BOOM كسر قمة 1m\n💥 {peak:.2f} -> {break_price:.2f}\n⏱ {time.strftime('%H:%M:%S')}"
        else:
            ax.axhline(y=peak, color='red', linestyle='--', label=f'قاع {peak:.2f}')
            title = f"{symbol} - 1m BREAK DOWN {peak:.2f}->{break_price:.2f}"
            caption = f"📊 CRASH كسر قاع 1m\n🔻 {peak:.2f} -> {break_price:.2f}\n⏱ {time.strftime('%H:%M:%S')}"

        ax.set_title(title)
        ax.legend()
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)

        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
            data={"chat_id": CHAT_ID, "caption": caption},
            files={'photo': (f'{symbol}.png', buf)}, timeout=15)
    except Exception as e:
        print(f"Chart {symbol} error: {e}")

def log(msg):
    try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg}, timeout=5)
    except: pass

async def handle_symbol(symbol):
    uri = "wss://ws.derivws.com/websockets/v3?app_id=1089"
    while True:
        try:
            async with websockets.connect(uri) as ws:
                await ws.send(json.dumps({"ticks_history": symbol, "adjust_start_time": 1, "count": 50, "end": "latest", "start": 1, "style": "candles", "granularity": 60}))
                print(f"طلبت تاريخ {symbol}")
                async for raw in ws:
                    data = json.loads(raw)
                    candles = data_store[symbol]

                    if "candles" in data:
                        candles.clear()
                        for c in data["candles"]:
                            candles.append({"high": float(c["high"]), "low": float(c["low"]), "open": float(c["open"]), "close": float(c["close"]), "start": c["epoch"]})
                        log(f"✅ {symbol} تم تحميل {len(candles)} شمعة 1m")
                        await ws.send(json.dumps({"ticks_history": symbol, "style": "candles", "granularity": 60, "subscribe": 1}))

                    if "ohlc" in data:
                        o = data["ohlc"]
                        c = {"high": float(o["high"]), "low": float(o["low"]), "open": float(o["open"]), "close": float(o["close"]), "start": int(o["open_time"])}
                        if candles and c["start"] == candles[-1]["start"]:
                            candles[-1] = c
                        else:
                            candles.append(c)

                        if len(candles) >= 21:
                            if symbol == "BOOM1000":
                                peak = max([x["high"] for x in list(candles)[-21:-1]])
                                if c["high"] > peak:
                                    await asyncio.to_thread(send_chart, symbol, c["high"], peak, candles)
                            else: # CRASH1000 يكسر قاع
                                trough = min([x["low"] for x in list(candles)[-21:-1]])
                                if c["low"] < trough:
                                    await asyncio.to_thread(send_chart, symbol, c["low"], trough, candles)
        except Exception as e:
            print(f"{symbol} reconnect {e}")
            await asyncio.sleep(3)

async def main_loop():
    await asyncio.gather(handle_symbol("BOOM1000"), handle_symbol("CRASH1000"))

def start_ws(): asyncio.run(main_loop())

@app.route('/')
def home():
    b = len(data_store["BOOM1000"])
    cr = len(data_store["CRASH1000"])
    return f"OK - BOOM:{b} CRASH:{cr}"

if __name__ == "__main__":
    threading.Thread(target=start_ws, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
