import os, requests, threading, io, time, json, traceback
from collections import deque
from flask import Flask
import websocket
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

TOKEN=os.getenv("TELEGRAM_TOKEN")
CHAT_ID=os.getenv("TELEGRAM_CHAT_ID")
app=Flask(__name__)
store={"BOOM1000":deque(maxlen=50),"CRASH1000":deque(maxlen=50)}

def send_chart(sym,bp,pk,candles):
    try:
        fig,ax=plt.subplots(figsize=(8,4))
        d=list(candles)[-30:]
        o=[x["open"] for x in d]; h=[x["high"] for x in d]; l=[x["low"] for x in d]; cl=[x["close"] for x in d]
        for i in range(len(d)):
            col='green' if cl[i]>=o[i] else 'red'
            ax.plot([i,i],[l[i],h[i]],color='black',lw=1)
            ax.plot([i,i],[o[i],cl[i]],color=col,lw=4)
        ax.axhline(pk,color='red',ls='--')
        ax.set_title(f"{sym} 1m BREAK {pk:.2f}->{bp:.2f}")
        plt.tight_layout()
        buf=io.BytesIO(); plt.savefig(buf,format='png'); plt.close(); buf.seek(0)
        cap=f"📊 {sym} كسر 1m\n💥 {pk:.2f}->{bp:.2f}\n⏱ {time.strftime('%H:%M:%S')}"
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", data={"chat_id":CHAT_ID,"caption":cap}, files={'photo':(f'{sym}.png',buf)}, timeout=20)
        print(f"sent chart {sym}")
    except Exception as e: print(f"chart err {e}")

def on_message(ws,msg):
    try:
        j=json.loads(msg)
        # تحميل تاريخ
        if "candles" in j and "echo_req" in j:
            sym=j["echo_req"].get("ticks_history")
            if sym in store:
                store[sym].clear()
                for c in j["candles"]:
                    store[sym].append({"high":float(c["high"]),"low":float(c["low"]),"open":float(c["open"]),"close":float(c["close"]),"start":c["epoch"]})
                print(f"{sym} LOADED {len(store[sym])}")
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id":CHAT_ID,"text":f"✅ {sym} {len(store[sym])} شمعة"}, timeout=5)

        # شمعة لايف
        if "ohlc" in j:
            o=j["ohlc"]
            c={"high":float(o["high"]),"low":float(o["low"]),"open":float(o["open"]),"close":float(o["close"]),"start":int(o["open_time"])}
            # Deriv ما يرجع الرمز بالـ ohlc، نعرفه من اخر تحديث وقت
            for sym in ["BOOM1000","CRASH1000"]:
                dq=store[sym]
                if not dq: continue
                if abs(c["start"]-dq[-1]["start"])<120 or c["start"]>=dq[-1]["start"]:
                    if c["start"]==dq[-1]["start"]: dq[-1]=c
                    elif c["start"]>dq[-1]["start"]: dq.append(c)
                    if len(dq)>=21:
                        if sym=="BOOM1000":
                            pk=max([x["high"] for x in list(dq)[-21:-1]])
                            if c["high"]>pk: threading.Thread(target=send_chart,args=(sym,c["high"],pk,dq),daemon=True).start()
                        else:
                            tr=min([x["low"] for x in list(dq)[-21:-1]])
                            if c["low"]<tr: threading.Thread(target=send_chart,args=(sym,c["low"],tr,dq),daemon=True).start()
                    break
    except Exception as e:
        print(f"on_msg err {e} {traceback.format_exc()}")

def on_open(ws):
    print("WS OPEN")
    for sym in ["BOOM1000","CRASH1000"]:
        ws.send(json.dumps({"ticks_history":sym,"count":50,"end":"latest","start":1,"style":"candles","granularity":60}))
        time.sleep(0.5)
    # اشتراك بعد ثانيتين
    def sub():
        time.sleep(2)
        for sym in ["BOOM1000","CRASH1000"]:
            try: ws.send(json.dumps({"ticks_history":sym,"style":"candles","granularity":60,"subscribe":1}))
            except: pass
    threading.Thread(target=sub,daemon=True).start()

def run_ws():
    while True:
        try:
            ws=websocket.WebSocketApp("wss://ws.derivws.com/websockets/v3?app_id=1089", on_open=on_open, on_message=on_message)
            ws.run_forever(ping_interval=20, ping_timeout=10)
        except Exception as e:
            print(f"WS crash {e}")
        time.sleep(5)

@app.route('/')
def home(): return f"OK - BOOM:{len(store['BOOM1000'])} CRASH:{len(store['CRASH1000'])}"

if __name__=="__main__":
    threading.Thread(target=run_ws,daemon=True).start()
    app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
