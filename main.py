from flask import Flask
import threading, time, requests, os

app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# الارقام
GOLD_SUP = 4100
GOLD_RES = 4200
BTC_SUP = 108000
BTC_RES = 112000

wg_res = False
wg_sup = False
wb_res = False
wb_sup = False
g_up = 0
g_down = 0
b_up = 0
b_down = 0

def send(m):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": m}, timeout=15)
    except: pass

def prices():
    try:
        g = float(requests.get("https://api.gold-api.com/price/XAU", timeout=10).json().get('price',0))
    except: g=0
    try:
        b = float(requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10).json()['bitcoin']['usd'])
    except: b=0
    return g,b

def loop():
    global wg_res, wg_sup, wb_res, wb_sup, g_up, g_down, b_up, b_down
    while True:
        gold, btc = prices()
        print(f"Gold {gold} | BTC {btc}")

        # === ذهب مقاومة ===
        if GOLD_RES-20 < gold < GOLD_RES and not wg_res:
            send(f"⏳ ذهب ${gold}\nقرب مقاومة {GOLD_RES}$\nانتظر لا تدخل هسه.. اذا كسر انطيك اشارة شراء")
            wg_res=True
        if gold > GOLD_RES+8:
            g_up+=1
            if g_up>=2 and wg_res:
                send(f"🚀 ذهب كسر المقاومة!\nكان {GOLD_RES}$ هسه ${gold}\nاشتري هسه ✅\nهدف 4250$ - 4300$")
                wg_res=False; g_up=0
        else:
            if gold < GOLD_RES: g_up=0

        # === ذهب دعم ===
        if GOLD_SUP-15 < gold < GOLD_SUP+15 and not wg_sup:
            send(f"⏳ ذهب ${gold}\nقرب دعم {GOLD_SUP}$\nانتظر.. اذا ثبت راح اكلك اشتري")
            wg_sup=True
        if gold < GOLD_SUP-8:
            g_down+=1
            if g_down>=2 and wg_sup:
                send(f"🔴 ذهب كسر الدعم!\nنزل جوة {GOLD_SUP}$ وصل ${gold}\nبيع هسه ❌")
                wg_sup=False; g_down=0
        else:
            if gold > GOLD_SUP: g_down=0

        # === بتكوين مقاومة ===
        if BTC_RES-1500 < btc < BTC_RES and not wb_res:
            send(f"⏳ بتكوين ${btc}\nقرب مقاومة {BTC_RES}$\nانتظر لا تدخل")
            wb_res=True
        if btc > BTC_RES+500:
            b_up+=1
            if b_up>=2 and wb_res:
                send(f"🚀 بتكوين كسر المقاومة!\nكان {BTC_RES}$ هسه ${btc}\nاشتري هسه ✅\nهدف 115k$")
                wb_res=False; b_up=0
        else:
            if btc < BTC_RES: b_up=0

        # === بتكوين دعم ===
        if BTC_SUP-1000 < btc < BTC_SUP+1000 and not wb_sup:
            send(f"⏳ بتكوين ${btc}\nقرب دعم {BTC_SUP}$\nانتظر..")
            wb_sup=True
        if btc < BTC_SUP-500:
            b_down+=1
            if b_down>=2 and wb_sup:
                send(f"🔴 بتكوين كسر الدعم!\nنزل جوة {BTC_SUP}$ وصل ${btc}\nبيع ❌")
                wb_sup=False; b_down=0
        else:
            if btc > BTC_SUP: b_down=0

        time.sleep(300) # 5 دقايق

@app.route("/")
def home():
    g,b = prices()
    return f"✅ شغال كل 5 دقايق<br>Gold: ${g} (دعم {GOLD_SUP} مقاومة {GOLD_RES})<br>BTC: ${b} (دعم {BTC_SUP} مقاومة {BTC_RES})"

threading.Thread(target=loop, daemon=True).start()
