from flask import Flask
import threading, time, requests, os

app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")

GOLD_SUP = 4100
GOLD_RES = 4200
BTC_SUP = 108000
BTC_RES = 112000

wg_res = False
wb_res = False

def send(m):
    if not BOT_TOKEN or not CHAT_ID: return
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": m}, timeout=15)
    except: pass

def prices():
    try:
        g = float(requests.get("https://api.gold-api.com/price/XAU", timeout=10).json().get('price',0))
    except: g=0
    try:
        b = float(requests.get("https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=10).json()['data']['amount'])
    except:
        try:
            b = float(requests.get("https://api.kraken.com/0/public/Ticker?pair=XBTUSD", timeout=10).json()['result']['XXBTZUSD']['c'][0])
        except: b=0
    return g,b

def loop():
    global wg_res, wb_res
    g_up = 0; b_up = 0
    while True:
        try:
            gold, btc = prices()
            print(f"Gold {gold} | BTC {btc}", flush=True)
            if GOLD_RES-20 < gold < GOLD_RES and not wg_res:
                send(f"⏳ ذهب ${gold} قرب مقاومة {GOLD_RES}$\nانتظر لا تدخل")
                wg_res=True
            if gold > GOLD_RES+8:
                g_up+=1
                if g_up>=2 and wg_res:
                    send(f"🚀 ذهب كسر {GOLD_RES}$ وصل ${gold}\nاشتري ✅")
                    wg_res=False; g_up=0
            else:
                if gold < GOLD_RES: g_up=0

            if BTC_RES-1500 < btc < BTC_RES and not wb_res:
                send(f"⏳ بتكوين ${btc} قرب مقاومة {BTC_RES}$\nانتظر")
                wb_res=True
            if btc > BTC_RES+500:
                b_up+=1
                if b_up>=2 and wb_res:
                    send(f"🚀 بتكوين كسر {BTC_RES}$ وصل ${btc}\nاشتري ✅")
                    wb_res=False; b_up=0
            else:
                if btc < BTC_RES: b_up=0
        except Exception as e:
            print(f"Error {e}", flush=True)
        time.sleep(300)

@app.route("/")
def home():
    g,b = prices()
    return f"✅ Bot شغال - Gold ${g} | BTC ${b}<br>يفحص كل 5 دقايق"

threading.Thread(target=loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
