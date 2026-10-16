import os, json, asyncio, websockets, requests, threading, io, time
from collections import deque
from flask import Flask
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
app = Flask(__name__)
candles = deque(maxlen=50)

def send_chart_with_break(break_price, peak):
    try:
        if len(candles) < 10: return
        fig, ax = plt.subplots(figsize=(8,4))

        # اخر 30 شمعة 1m
        data = list(candles)[-30:]
        opens = [c["open"] for c in data]
        highs = [c["high"] for c in data]
        lows = [c["low"] for c in data]
        closes = [c["close"] for c in data]

        for i in range(len(data)):
            color = 'green' if closes[i] >= opens[i] else 'red'
            ax.plot([i, i], [lows[i], highs[i]], color='black', linewidth=1)
            ax.plot([i, i], [opens[i], closes[i]], color=color, linewidth=4)
            # نقطة الكسر
            if highs[i] == break_price:
                ax.scatter(i, highs[i], color='blue', s=120, zorder=5)

        ax.axhline(y=peak, color='red', linestyle='--', linewidth=1.2, label=f'قمة مكسورة {peak:.2f}')

        ax.set_title(f"BOOM1000 - 1m BREAK - {peak:.2f} -> {break_price:.2f}")
        ax.legend()
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)

        caption = f"📊 كسر فريم 1 دقيقة\n💥 قمة: {peak:.2f}\n🔵 كسر: {break_price:.2f}\n🕯️ اخر اغلاق: {closes[-1]:.2f}\n⏱ {time.strftime('%H:%M:%S')}"

        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
            data={"chat_id": CHAT_ID, "caption": caption},
            files={'photo': ('break_1m.png', buf)}, timeout=15)
        print("تم ارسال شارت الكسر")
    except Exception as e:
        print(f"Chart error: {e}")

def log(msg):
    try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg}, timeout=5)
    except: pass

async def run():
    uri = "wss://ws.derivws.com/websockets/v3?app_id=1089"
    while True:
        try:
            async with websockets.connect(uri) as ws:
                await ws.send(json.dumps({"ticks_history": "BOOM1000", "adjust_start_time": 1, "count": 50, "end": "latest", "start": 1, "style": "candles", "granularity": 60}))
                print("طلبت تاريخ 1m...")
                async for raw in ws:
                    data = json.loads(raw)
                    if "candles" in data:
                        candles.clear()
                        for c in data["candles"]:
                            candles.append({"high": float(c["high"]), "low": float(c["low"]), "open": float(c["open"]), "close": float(c["close"]), "start": c["epoch"]})
                        log(f"✅ تم تحميل {len(candles)} شمعة 1m - بانتظار كسر مع شارت")
                        await ws.send(json.dumps({"ticks_history": "BOOM1000", "style": "candles", "granularity": 60, "subscribe": 1}))

                    if "ohlc" in data:
                        o = data["ohlc"]
                        c = {"high": float(o["high"]), "low": float(o["low"]), "open": float(o["open"]), "close": float(o["close"]), "start": int(o["open_time"])}
                        if candles and c["start"] == candles[-1]["start"]:
                            candles[-1] = c
                        else:
                            candles.append(c)

                        if len(candles) >= 21:
                            peak = max([x["high"] for x in list(candles)[-21:-1]])
                            if c["high"] > peak:
                                print(f"BREAK 1m {peak} -> {c['high']}")
                                # دز صورة + نص
                                await asyncio.to_thread(send_chart_with_break, c["high"], peak)
                                log(f"🔵 كسر قمة 1m\n💥 {peak:.2f} -> {c['high']:.2f}")
        except Exception as e:
            print(f"Reconnect {e}")
            await asyncio.sleep(3)

def start_ws(): asyncio.run(run())
@app.route('/')
def home(): return f"OK - {len(candles)} candles"

if __name__ == "__main__":
    threading.Thread(target=start_ws, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
