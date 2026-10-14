import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont
import io, random

TOKEN = os.environ.get("TOKEN") or "8871511463:AAHptY0mk4Ecn7BTsZH1NDDT7gwUs06eVu8"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔔 اهلا محمد باسم\nبوت الفيديو الذهبي جاهز 🎥\nدزلي اسم حيوان")

async def make_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    animal = update.message.text.strip()[:20]
    await update.message.reply_text(f"🎥 جاري صنع فيديو {animal} الذهبي...")

    W, H = 600, 600
    frames = []
    try:
        font_big = ImageFont.truetype("DejaVuSans.ttf", 70)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 30)
    except:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    for i in range(20):
        img = Image.new('RGB', (W, H), (15, 10, 0))
        draw = ImageDraw.Draw(img)
        glow = 40 + (i % 10) * 8
        for y in range(H):
            draw.line([(0, y), (W, y)], fill=(glow, glow//2, 0))
        size = 180 + (i % 10) * 5
        draw.ellipse([(W//2-size, H//2-size), (W//2+size, H//2+size)], outline=(255,215,0), width=6)
        draw.text((W//2+2, H//2+2), animal, font=font_big, fill=(0,0,0), anchor="mm")
        draw.text((W//2, H//2), animal, font=font_big, fill=(255,215,0), anchor="mm")
        draw.text((W//2, 550), "GOLD VIDEO", font=font_small, fill=(255,255,200), anchor="mm")
        frames.append(img)

    bio = io.BytesIO()
    frames[0].save(bio, format='GIF', save_all=True, append_images=frames[1:], duration=100, loop=0)
    bio.seek(0)
    await update.message.reply_animation(bio, caption=f"✨ فيديو {animal} الذهبي\n🔔 بادارة محمد باسم")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, make_video))
    app.run_polling()

if __name__ == "__main__":
    main()
