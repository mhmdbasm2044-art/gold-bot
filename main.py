import os, time, threading
from datetime import datetime
from flask import Flask
import requests
app = Flask(__name__)
BOT_TOKEN=os.environ.get("BOT_TOKEN","")
CHAT_ID=os.environ.get("CHAT_ID","")
last_price=0
zones=[]
touched={}
last_error="Init"
last_3m=""

def send(m):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",data={"chat_id":CHAT_ID,"text":m},timeout=10)
    except: pass

def get_market():
    global last_error
    try:
        r=requests.get("https://data-api.binance.vision/api/v3/ticker/24hr?symbol=PAXGUSDT",timeout=10).json()
        p=float(r['lastPrice']);h=float(r['highPrice']);l=float(r['lowPrice']);c=float(r['prevClosePrice'])
        last_error=f"OK {p}";return p,h,l,c
    except Exception as e:
        last_error=str(e);return 0,0,0,0

def build_zones(h,l,c):
    rng=h-l
    if rng<20: rng=224.6
    raw=[("R4",c+rng*1.1/2),("R3",c+rng*1.1/4),("R2",c+rng*1.1/6),("R1",c+rng*1.1/12),("PP",c),("S1",c-rng*1.1/12),("S2",c-rng*1.1/6),("S3",c-rng*1.1/4),("S4",c-rng*1.1/2)]
    res=[]
    for name,mid in raw:
        res.append((round(mid+1.25,2),round(mid-1.25,2),name,round(mid,2)))
    return sorted(res,key=lambda x:x[3],reverse=True)

def worker():
    global last_price,zones,last_3m
    for _ in range(20):
        p,h,l,c=get_market()
        if p!=0:
            last_price=p;zones=build_zones(h,l,c)
            txt=f"✅ 3د + يومي\nسعر {p:.2f}$ H {h:.0f} L {l:.0f}\n"
            for up,lo,n,_ in zones: txt+=f"{n}: {up},{lo}\n"
            send(txt);break
        time.sleep(3)
    while True:
        try:
            p,h,l,c=get_market()
            if p!=0:
                old=last_price;last_price=p
                now=datetime.utcnow()
                slot=f"{now.hour}:{now.minute//3}"
                # تحديث يومي الساعة 00:00
                if now.hour==0 and now.minute<2:
                    zones=build_zones(h,l,c)
                    send(f"📊 مستويات جديدة {now.date()}\n"+ "\n".join([f"{n}: {u},{lo}" for u,lo,n,_ in zones]))

                for up,lo,name,_ in zones:
                    if lo-1 <= p <= up+1:
                        touched[name]=True

                is_new = (slot!=last_3m) and (now.minute%3==0)
                if is_new and last_3m!="":
                    for up,lo,name,mid in zones:
                        if touched.get(name):
                            if old>=up and p<lo:
                                send(f"🔻 بيع 3د {name} {up}-{lo} دخول {p:.2f}$")
                            elif old<=lo and p>up:
                                send(f"🚀 شراء 3د {name} {up}-{lo} دخول {p:.2f}$")
                            touched[name]=False
                    last_3m=slot
                if last_3m=="": last_3m=slot
        except: pass
        time.sleep(10)

threading.Thread(target=worker,daemon=True).start()
@app.route("/")
def home():
    t=f"3د يومي | {last_price}$ | {last_error}<br>"
    for up,lo,n,mid in zones: t+=f"{n}: {up},{lo} mid {mid}<br>"
    return t
if __name__=="__main__":
    app.run(host="0.0.0.0",port=10000)
