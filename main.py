import os, json
from flask import Flask
import telebot
from telebot import types

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# تخزين بسيط بالنقاط
DB_FILE = "/tmp/db.json"
def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}, "pending": {}}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

@bot.message_handler(commands=['start'])
def start(m):
    db = load_db()
    uid = str(m.from_user.id)
    if uid not in db["users"]:
        db["users"][uid] = {"username": "", "points": 0}
        save_db(db)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📤 نشر حسابي", "⭐ نقاطي", "📋 مهام المتابعة")

    bot.send_message(m.chat.id,
        "هلا بيك ببوت تبادل الناصرية 🔥\n\n"
        "1️⃣ دوس 📤 نشر حسابي ودز يوزرك\n"
        "2️⃣ دوس 📋 مهام المتابعة تابع 3 حسابات\n"
        "3️⃣ حسابك ينتشر لـ 100 شخص حقيقي\n\n"
        "بدون باسورد وآمن 100%", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📤 نشر حسابي")
def ask_user(m):
    bot.send_message(m.chat.id, "دز يوزر الانستا مالتك، مثال:\n@ali_nasiriyah")

@bot.message_handler(func=lambda m: m.text and m.text.startswith("@"))
def save_user(m):
    db = load_db()
    uid = str(m.from_user.id)
    username = m.text.strip()
    db["users"][uid]["username"] = username
    db["users"][uid]["points"] += 5
    save_db(db)
    bot.send_message(m.chat.id, f"✅ تم حفظ {username}\nعندك {db['users'][uid]['points']} نقاط\nهسه دوس 📋 مهام المتابعة حتى ينتشر حسابك اكثر")

@bot.message_handler(func=lambda m: m.text == "⭐ نقاطي")
def points(m):
    db = load_db()
    uid = str(m.from_user.id)
    p = db["users"].get(uid, {}).get("points", 0)
    bot.send_message(m.chat.id, f"⭐ نقاطك: {p}\nكل ما تتابع حساب تاخذ 2 نقطة\nنشر حسابك يكلف 10 نقاط")

@bot.message_handler(func=lambda m: m.text == "📋 مهام المتابعة")
def tasks(m):
    db = load_db()
    # نجيب 3 يوزرات عشوائية
    users = [u for uid,u in db["users"].items() if u["username"] and uid!= str(m.from_user.id)]
    if len(users) < 
    bot.send_message(m.chat.id, "⏳ انتظر ناس جدد")
