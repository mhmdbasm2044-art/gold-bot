import os, json, asyncio, websockets, requests, threading, io, time
from collections import deque
from flask import Flask
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
app = Flask(__name__)

store = {"BOOM1000": deque(maxlen=50), "CRASH1000": deque(maxlen=50)}

def send_chart(symbol, bp, pk, candles):
    try:
        fig, ax = plt.subplots(figsize=(8,4))
        d = list(candles)[-30:]
        if len(d) < 5: return
        o=[x["open"] for x in d]; h=[x["high"] for x in d]; l=[x["low"] for x in d]; cl=[x["close"] for x in d]
        for i in range(len(d)):
            col='green' if cl[i]>=o[i] else 'red'
            ax.plot([i,i],[l[i],h[i]],color='black',lw=1)
            ax.plot([i,i],[o[i],cl[i]],color=col,lw=4)
        ax.axhline(pk,color='red',ls='--',label=f'{pk:.2f}')
        ax.set_title(f"{symbol} 1m {pk:.2f}->{bp:.2f}")
        ax.legend(); plt.tight_layout()
        buf=io.BytesIO(); plt.savefig(buf,format='png'); plt.close(); buf.seek(0)
        cap=f"📊 {symbol} كسر 1m\n💥 {pk:.2f} -> {bp:.2f}\n⏱ {time.strftime('%H:%M:%S')}"
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", data={"chat_id":CHAT_ID,"caption":cap}, files={'photo':(f'{symbol}.png',buf)}, timeout=15)
        print(f"Chart sent {symbol}")
    except Exception as e:
        print(f"Chart err {e}")

def log(m):
    try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id":CHAT_ID,"text":m}, timeout=5)
    except: pass

async def run_all():
    uri="wss://ws.derivws.com/websockets/v3?app_id=1089"
    while True:
        try:
            async with websockets.connect(uri) as ws:
                print("Connected Deriv")
                # نطلب الثنين ورا بعض بنفس الاتصال
                for sym in ["BOOM1000","CRASH1000"]:
                    await ws.send(json.dumps({"ticks_history": sym, "count": 50, "end": "latest", "start": 1, "style": "candles", "granularity": 60}))
                    print(f"طلبت {sym}")

                async for raw in ws:
                    j=json.loads(raw)
                    if "echo_req" in j and "ticks_history" in j["echo_req"]:
                        sym=j["echo_req"]["ticks_history"]
                        if "candles" in j:
                            store[sym].clear()
                            for c in j["candles"]:
                                store[sym].append({"high":float(c["high"]),"low":float(c["low"]),"open":float(c["open"]),"close":float(c["close"]),"start":c["epoch"]})
                            print(f"{sym} loaded {len(store[sym])}")
                            log(f"✅ {sym} {len(store[sym])} شمعة")
                            # اشترك بعد التحميل
                            await ws.send(json.dumps({"ticks_history": sym, "style": "candles", "granularity": 60, "subscribe": 1}))

                    if "ohlc" in j:
                        o=j["ohlc"]
                        sym=j["ohlc"]["symbol"] if "symbol" in j["ohlc"] else j.get("echo_req",{}).get("ticks_history","BOOM1000")
                        # نحدد الرمز من الـ tick
                        # Deriv ما يدز symbol بالـ ohlc، فنحدده من الـ subscription id - نستخدم اخر طلب
                        # حل بسيط: نجرب الثنين
                        for s in ["BOOM1000","CRASH1000"]:
                            candles=store[s]
                            if not candles: continue
                            # اذا الوقت قريب من اخر شمعة، هاي الها
                            if abs(int(o["open_time"]) - candles[-1]["start"]) < 120:
                                c={"high":float(o["high"]),"low":float(o["low"]),"open":float(o["open"]),"close":float(o["close"]),"start":int(o["open_time"])}
                                if c["start"]==candles[-1]["start"]: candles[-1]=c
                                else: candles.append(c)
                                if len(candles)>=21:
                                    if s=="BOOM1000":
                                        pk=max([x["high"] for x in list(candles)[-21:-1]])
                                        if c["high"]>pk:
                                            await asyncio.to_thread(send_chart,s,c["high"],pk,candles)
                                    else:
                                        tr=min([x["low"] for x in list(candles)[-21:-1]])
                                        if c["low"]<tr:
                                            await asyncio.to_thread(send_chart,s,c["low"],tr,candles)
                                break
        except Exception as e:
            print(f"Reconnect all {e}")
            await asyncio.sleep(3)

def start_ws(): asyncio.run(run_all())
@app.route('/')
def home(): return f"OK - BOOM:{len(store['BOOM1000'])} CRASH:{len(store['CRASH1000'])}"

if __name__=="__main__":
    threading.Thread(target=start_ws,daemon=True).start()
    app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
