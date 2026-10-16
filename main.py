import os, json, asyncio, websockets, requests, threading
from collections import deque
from flask import Flask

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
app = Flask(__name__)
candles = deque(maxlen=50)

async def run():
    uri = "wss://ws.derivws.com/websockets/v3?app_id=1089"
    while True:
        try:
            async with websockets.connect(uri) as ws:
                await ws.send(json.dumps({"ticks_history": "BOOM1000", "style": "candles", "granularity": 60, "count": 50, "subscribe": 1}))
                print("BOT 1m ON")
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": "✅ بوت 1m اشتغل على Render المجاني"})
                async for raw in ws:
                    data = json.loads(raw)
                    if "ohlc" in data:
                        o = data["ohlc"]
                        c = {"high": float(o["high"]), "low": float(o["low"]), "start": o["open_time"]}
                        if candles and c["start"] == candles[-1]["start"]:
                            candles[-1] = c
                        else:
                            candles.append(c)
                        if len(candles) >= 21:
                            peak = max([x["high"] for x in list(candles)[-21:-1]])
                            if c["high"] > peak:
                                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": f"🔵 كسر قمة 1m: {peak:.2f} -> {c['high']:.2f}"})
        except Exception as e:
            print(f"reconnect {e}")
            await asyncio.sleep(2)

def start_ws(): asyncio.run(run())
@app.route('/')
def home(): return f"OK - {len(candles)} candles"
if __name__ == "__main__":
    threading.Thread(target=start_ws, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
