from flask import Flask, jsonify
import yfinance as yf
import pandas as pd
from datetime import datetime
import threading
import time
import requests
import os

app = Flask(__name__)

# ============ الاعدادات ============
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "حط_التوكن_مالك_هنا")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID", "حط_الايدي_مالك_هنا")
SYMBOL = "GC=F"  # الذهب

levels = {}

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def calc_daily_levels():
    global levels
    # يجيب بيانات امس
    data = yf.download(SYMBOL, period="2d", interval="1d")
    if len(data) < 1:
        return
    
    high = float(data['High'].iloc[-1])
    low = float(data['Low'].iloc[-1])
    close = float(data['Close'].iloc[-1])
    
    pivot = (high + low + close) / 3
    
    # 24 مستوى لليوم الجديد - على طريقة 15د
    levels = {
        "R12": pivot + (high - low) * 1.5,
        "R11": pivot + (high - low) * 1.2,
        "R10": high + (high - low) * 0.5,
        "R9": high + (high - low) * 0.2,
        "R8": high,
        "R7": pivot + (high - low) * 0.5,
        "R6": pivot + (high - low) * 0.2,
        "S1": pivot,
        "S2": pivot - (high - low) * 0.2,
        "S3": pivot - (high - low) * 0.5,
        "S4": low,
        "S5": low - (high - low) * 0.2,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "pivot": pivot
    }
    
    msg = f"""📅 *مستويات اليوم الجديدة - 15د*
🗓️ التاريخ: {levels['date']}
💰 اغلاق امس: {close:.2f}

*مقاومات (SELL):*
🔴 {levels['R12']:.2f}
🔴 {levels['R8']:.2f} - هاي اليوم
🔴 {levels['R7']:.2f}

*دعوم (BUY):*
🟢 {levels['S1']:.2f} - بيفوت اليوم
🟢 {levels['S4']:.2f} - لو امس
🟢 {levels['S5']:.2f}

البوت بدا يراقب فريم 15د
"""
    send_telegram(msg)
    print("Levels Updated", levels)

def check_15m_candle():
    while True:
        try:
            if not levels:
                calc_daily_levels()
            
            # يجيب اخر شمعتين 15د
            df = yf.download(SYMBOL, period="1d", interval="15m")
            if len(df) < 2:
                time.sleep(60)
                continue
            
            last_close = float(df['Close'].iloc[-1])
            last_open = float(df['Open'].iloc[-1])
            prev_close = float(df['Close'].iloc[-2])
            
            # شمعة جديدة فاتحة؟
            is_new_candle = datetime.now().minute % 15 == 0
            
            if is_new_candle:
                signal = None
                entry = last_open
                stop = 0
                tp = 0
                
                # BUY اذا فتحت فوك دعم
                for name, lvl in levels.items():
                    if not isinstance(lvl, float):
                        continue
                    if prev_close < lvl and last_open > lvl and "S" in name:
                        signal = "BUY"
                        stop = lvl - 2.0
                        tp = lvl + 5.0
                        level_name = f"{name} ({lvl:.2f})"
                        break
                    if prev_close > lvl and last_open < lvl and "R" in name:
                        signal = "SELL"
                        stop = lvl + 2.0
                        tp = lvl - 5.0
                        level_name = f"{name} ({lvl:.2f})"
                        break
                
                if signal:
                    msg = f"""🚨 *اشارة جديدة - 15 دقيقة*
⏰ الوقت: {datetime.now().strftime('%H:%M')} بتوقيت بغداد
📊 الفريم: 15m

*النوع:* {signal} { '🟢' if signal=='BUY' else '🔴'}
*السعر المباشر:* {entry:.2f}
*المستوى:* {level_name}
*الستوب:* {stop:.2f} (قريب 2$)
*الهدف:* {tp:.2f} (قريب 5$)

*الحالة:* شمعة جديدة فتحت {"فوك" if signal=="BUY" else "جوه"} الخط
"""
                    send_telegram(msg)
                
                time.sleep(60) # حتى ما يكرر الاشارة بنفس الشمعة
            
            # كل يوم ساعة 00:00 يحسب مستويات جديدة
            if datetime.now().hour == 0 and datetime.now().minute == 0:
                calc_daily_levels()
                time.sleep(60)
                
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(30) # يفحص كل 30 ثانية

# ============ Flask Routes for Render ============
@app.route('/')
def home():
    return jsonify({"status": "running", "levels": levels, "time": datetime.now().isoformat()})

@app.route('/levels')
def get_levels():
    return jsonify(levels)

# تشغيل المراقبة بالخلفية
threading.Thread(target=check_15m_candle, daemon=True).start()
calc_daily_levels()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
