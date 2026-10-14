import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont
import io
import random

TOKEN = os.environ.get("TOKEN") or "8871511463:AAHptY0mk4Ecn7BTsZH1NDDT7gwUs06eVu8"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔔 اهلا Mohammed BASIM\n"
        "بوت الفيديو الذهبي جاهز 🎥✨\n\n"
        "دزلي اسم حيوان (اسد، نمر، ذئب) وانا اسويلك فيديو ذهبي يلمع!"
    )

async def make_gold_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    animal = update.message.text.strip()[:20]
    await update.message.reply_text(f"🎥 جاري تصنيع فيديو {animal} الذهبي... انتظر 5 ثواني")

    W, H = 600, 600
    frames = []

    try:
        font_big = ImageFont.truetype("DejaVuSans.ttf", 70)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 30)
    except:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # نسوي 25 فريم - كل فريم يلمع شكل
    for i in range(25):
        img = Image.new('RGB', (W, H), (10, 8, 0))
        draw = ImageDraw.Draw(img)

        # خلفية تلمع
        glow = int(50 + 50 * abs((i % 10) - 5) / 5) # يصعد وينزل
        for y in range(H):
            draw.line([(0, y), (W, y)], fill=(glow//2, glow//3, 0))

        # دائرة ذهبية تكبر وتصغر
        size = 200 + int(20 * (i % 10))
        x0 = W//2 - size
        y0 = H//2 - size
        x1 = W//2 + size
        y1 = H//2 + size

        gold = (255, 215 + random.randint(-20,20), 0)
        draw.ellipse([(x0, y0), (x1, y1)], outline=gold, width=6)
        draw.ellipse([(x0+20, y0+20), (x1-20, y1-20)], outline=(255,255,255), width=2)

        # اسم الحيوان
        draw.text((W//2+2, H//2+2), animal, font=font_big, fill=(0,0,0), anchor="mm")
        draw.text((W//2, H//2), animal, font=font_big, fill=gold, anchor="mm")
        draw.text((W//2, 550), "GOLD VIDEO", font=font_small, fill=(255,255,200), anchor="mm")

        frames.append(img)

    # نحفظ كـ GIF متحرك (يشتغل كفيديو بتليكرام)
    bio = io.BytesIO()
    bio.name = f"{animal}_gold.mp4"
    frames[0].save(
        bio, format='GIF',
        save_all=True, append_images=frames[1:],
        duration=80, loop=0, optimize=False
    )
    bio.seek(0)

    await update.message.reply_animation(
        animation=bio,
        caption=f"✨ فيديو {animal} الذهبي جاهز!\n🔔 تكوين او الذهب بادارة محمد باسم"
    )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, make_gold_video))
    print("Gold Video Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
