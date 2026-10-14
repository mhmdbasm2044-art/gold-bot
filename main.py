from flask import Flask
import os, json, threading, time, random
import telebot

# --- Flask حتى Render ما يطفي ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Gold Bot is Live - Fixed"

# --- اعدادات البوت ---
TOKEN = os.environ.get("BOT_TOKEN", "ضع_التوكن_هنا")
bot = telebot.TeleBot(TOKEN)

DB_FILE = "db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": {}}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

# /start
@bot.message_handler(commands=['start'])
def start(m):
    db = load_db()
    uid = str(m.from_user.id)
    if uid not in db["users"]:
        db["users"][uid] = {"points": 0, "name": m.from_user.first_name}
        save_db(db)
    bot.send_message(m.chat.id, f"اهلا {m.from_user.first_name} 👋\nاستخدم الازرار")

# ⭐ نقاطي
@bot.message_handler(func=lambda m: m.text == "⭐ نقاطي")
def points(m):
    db = load_db()
    uid = str(m.from_user.id)
    p = db["users"].get(uid, {}).get("points", 0)
    bot.send_message(m.chat.id, f"⭐ نقاطك: {p}")

# 📋 المهام
@bot.message_handler(func=lambda m: m.text == "📋 المهام")
def tasks(m):
    db = load_db()
    # نجيب 3 يوزرات عشوائية
    users = [u for uid, u in db["users"].items()]
    if len(users) < 3:
        bot.send_message(m.chat.id, "⏳ انتظر ناس جدد")
        return
    # اذا اكو ناس
    selected = random.sample(users, 3)
    text = "📋 مهام اليوم:\n"
    for u in selected:
        text += f"- {u.get('name','مستخدم')}\n"
    bot.send_message(m.chat.id, text)

# تشغيل البوت
def run_bot():
    print("Bot polling started...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Bot error: {e}")
            time.sleep(5)

# شغل البوت بثريد منفصل
threading.Thread(target=run_bot, daemon=True).start()

# شغل Flask
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
