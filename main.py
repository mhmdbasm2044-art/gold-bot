import os, json, asyncio, websockets, requests, time, io
from collections import deque
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# تخزين شموع 1 دقيقة
candles_1m = deque(maxlen=50)
current_candle = {"open": 0, "high": -999999, "low": 999999, "close": 0, "start": 0, "symbol": ""}

def send_1m_chart():
    try:
        if len(candles_1m) < 5: return

        # رسم شموع 1m
        fig, ax = plt.subplots(figsize=(8,4))
        opens = [c["open"] for c in candles_1m]
        highs = [c["high"] for c in candles_1m]
        lows = [c["low"] for c in candles_1m]
        closes = [c["close"] for c in candles_1m]

        # رسم كل شمعة
        for i in range(len(candles_1m)):
            color = 'green' if closes[i] >= opens[i] else 'red'
            ax.plot([i, i], [lows[i], highs[i]], color='black', linewidth=1)
            ax.plot([i, i], [opens[i], closes[i]], color=color, linewidth=4)

        # قمة اخر 20 شمعة 1m
        peak = max(highs[-20:-1]) if len(highs) >= 20 else max(highs)
        bottom = min(lows[-20:-1]) if len(lows) >= 20 else min(lows)
        ax.axhline(y=peak, color='red', linestyle='--', label=f'قمة 1m: {peak:.2f}')
        ax.axhline(y=bottom, color='blue', linestyle='--', label=f'قاع 1m: {bottom:.2f}')

        ax.set_title(f"{current_candle['symbol']} - فريم 1 دقيقة - لحظي")
        ax.legend()
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)

        last = candles_1m[-1]
        caption = f"📊 <b>فريم 1 دقيقة</b>\n{last['symbol']}\n🕯️ O:{last['open']:.2f} H:{last['high']:.2f} L:{last['low']:.2f} C:{last['close']:.2f}\n🔴 قمة: {peak:.2f}\n🔵 قاع: {bottom:.2f}"

        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
            data={"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"},
            files={'photo': ('1m.png', buf)}, timeout=10)

    except Exception as e:
        print(f"chart error {e}")

async def run():
    global current_candle
    uri = "wss://ws.derivws.com/websockets/v3?app_id=1089"
    async with websockets.connect(uri) as ws:
        # نطلب شموع 1 دقيقة مباشرة من Deriv + التيكات اللحظية
        await ws.send(json.dumps({"ticks_history": "BOOM1000", "style": "candles", "granularity": 60, "count": 50, "subscribe": 1}))
        print("📊 يراقب فريم 1 دقيقة لحظة بلحظة")
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": "📊 <b>بوت فريم 1 دقيقة اشتغل</b>\n⏱ يراقب كل شمعة 1m وهي تتكون\n👁️ كسر لحظي", "parse_mode": "HTML"})

        async for raw in ws:
            data = json.loads(raw)
            now = time.time()

            # اذا اجت شمعة تاريخية
            if "candles" in data:
                for c in data["candles"]:
                    candles_1m.append({"open": c["open"], "high": c["high"], "low": c["low"], "close": c["close"], "start": c["epoch"]})
                continue

            # اذا اجت شمعة جديدة لحظية (OHLC)
            if "ohlc" in data:
                o = data["ohlc"]
                candle = {"open": float(o["open"]), "high": float(o["high"]), "low": float(o["low"]), "close": float(o["close"]), "start": o["open_time"], "symbol": o["symbol"]}
                # حدث اخر شمعة
                if candles_1m and candle["start"] == candles_1m[-1]["start"]:
                    candles_1m[-1] = candle
                else:
                    candles_1m.append(candle)
                current_candle = candle

                # تحقق كسر لحظي على فريم 1m
                if len(candles_1m) >= 21:
                    highs = [x["high"] for x in list(candles_1m)[-21:-1]]
                    lows = [x["low"] for x in list(candles_1m)[-21:-1]]
                    peak = max(highs)
                    bottom = min(lows)

                    # كسر قمة بفريم الدقيقة
                    if candle["close"] > peak or candle["high"] > peak:
                        print(f"BREAK 1m HIGH {candle['high']} > {peak}")
                        await asyncio.to_thread(send_1m_chart)
                        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                            json={"chat_id": CHAT_ID, "text": f"🔵 <b>كسر قمة فريم 1m</b>\n💥 {peak:.2f} -> {candle['high']:.2f}\n⏱ الشمعة الحية", "parse_mode": "HTML"})

                    elif candle["close"] < bottom or candle["low"] < bottom:
                        print(f"BREAK 1m LOW {candle['low']} < {bottom}")
                        await asyncio.to_thread(send_1m_chart)

async def main():
    while True:
        try: await run()
        except Exception as e:
            print(f"reconnect {e}")
            await asyncio.sleep(2)

asyncio.run(main())
