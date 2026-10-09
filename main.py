from flask import Flask
import threading, time, requests, os
from collections import deque

app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")

GOLD_SUP = 4100
GOLD_RES = 4200
BTC_SUP = 108000
BTC_RES = 112000
WHALE_LIMIT = 50

wg_res = False
wb_res = False
wg_sup = False
wb_sup = False
seen_tx = deque(maxlen=100)

def send(m):
    if not BOT_TOKEN or not CHAT_ID: return
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": m, "parse_mode": "Markdown"}, timeout=15)
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

def check_whales(btc_price):
    try:
        r = requests.get("https://api.blockchair.com/bitcoin/mempool?limit=20", timeout=15).json()
        for tx in r.get('data', []):
            txid = tx.get('transaction_hash')
            val_btc = tx.get('output_total', 0) / 100_000_000
            if val_btc >= WHALE_LIMIT and txid not in seen_tx:
                seen_tx.append(txid)
                usd = val_btc * btc_price
                send(f"🐳 *حوت تحرك!*\nالحجم: {val_btc:.1f} BTC (${usd/1000000:.1f}M)\n⚠️ احتمال تذبذب قوي - لا تدخل سريع")
                break
    except: pass

def loop():
    global wg_res, wb_res, wg_sup, wb_sup
    while True:
        try:
            gold, btc = prices()
            print(f"Gold {gold} | BTC {btc}", flush=True)

            if btc > 0:
                check_whales(btc)

            if GOLD_RES-20 < gold < GOLD_RES and not wg_res:
                send(f"⏳ *ذهب قرب مقاومة*\nالسعر: ${gold:.1f} / مقاومة {GOLD_RES}$\nالحالة: انتظر لا تشتري")
                wg_res=True
            if gold > GOLD_RES+10 and wg_res:
                send(f"🚀 *ذهب اشتري الان*\nدخول: ${gold:.1f}\nهدف: ${GOLD_RES+35:.0f}\nوقف: ${GOLD_RES-15:.0f}\nالسبب: كسر 4200 بقوة")
                wg_res=False

            if gold < GOLD_SUP+20 and gold > GOLD_SUP-10 and not wg_sup:
                send(f"⏳ *ذهب قرب دعم*\nالسعر: ${gold:.1f} / دعم {GOLD_SUP}$\nاستعد للشراء")
                wg_sup=True
            if gold < GOLD_SUP-10 and wg_sup:
                send(f"🔻 *ذهب بيع الان*\nدخول: ${gold:.1f}\nهدف: ${GOLD_SUP-40:.0f}\nوقف: ${GOLD_SUP+15:.0f}")
                wg_sup=False

            if BTC_RES-1500 < btc < BTC_RES and not wb_res:
                send(f"⏳ *بتكوين قرب مقاومة*\nالسعر: ${btc:.0f} / مقاومة {BTC_RES}$\nانتظر")
                wb_res=True
            if btc > BTC_RES+800 and wb_res:
                send(f"🚀 *بتكوين اشتري الان*\nدخول: ${btc:.0f}\nهدف: ${btc+2500:.0f}\nوقف: ${BTC_RES-1200:.0f}\nالسبب: كسر 112k")
                wb_res=False

            if btc < BTC_SUP+1000 and btc > BTC_SUP-500 and not wb_sup:
                send(f"⏳ *بتكوين قرب دعم*\nالسعر: ${btc:.0f} / دعم {BTC_SUP}$")
                wb_sup=True
            if btc < BTC_SUP-800 and wb_sup:
                send(f"🔻 *بتكوين بيع الان*\nدخول: ${btc:.0f}\nهدف: ${btc-2000:.0f}\nوقف: ${BTC_SUP+1000:.0f}")
                wb_sup=False

            if gold < GOLD_RES-40: wg_res=False
            if gold > GOLD_SUP+40: wg_sup=False
            if btc < BTC_RES-2500: wb_res=False
            if btc > BTC_SUP+2500: wb_sup=False

        except Exception as e:
            print(f"Error {e}", flush=True)
        time.sleep(300)

@app.route("/")
def home():
    g,b = prices()
    return f"✅ Bot PRO شغال - Gold ${g:.2f} | BTC ${b:.0f}<br>🐳 Whale Radar ON | يفحص كل 5 دقايق"

threading.Thread(target=loop, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
