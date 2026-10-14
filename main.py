# ملف main.py - انسخه كامل
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip
import os

TOKEN = "حط توكنك من BotFather هنا"
CHANNEL = "@اسم قناتك هنا"  # اذا ما عندك قناة امسح هذا السطر

قصص = {
    "ارنب": "كان يا ما كان ارنب صغير اسمه بوبو يحب الجزر، كان يشارك اصحابه واصبح محبوبا",
    "اسد": "الاسد سيمبا ملك الغابة الطيب يحمي الحيوانات",
    "فيل": "الفيل فلفول ساعد الحيوانات تعبر النهر",
    "قرد": "القرد شاطر وزع الموز على الجميع",
    "ببغاء": "الببغاء لولو تنقل اخبار الغابة",
    "سلحفاة": "السلحفاة توتا فازت بالسباق لانها لم تستسلم"
}

async def رد(update: Update, context: ContextTypes.DEFAULT_TYPE):
    حيوان = update.message.text.strip().lower()
    if حيوان not in قصص:
        await update.message.reply_text("اكتب: ارنب / اسد / فيل / قرد / ببغاء / سلحفاة")
        return
    
    قصة = قصص[حيوان]
    await update.message.reply_text(f"⏳ جاري صنع فيديو {حيوان}...")

    tts = gTTS(text=قصة, lang='ar')
    tts.save("صوت.mp3")
    
    صوت = AudioFileClip("صوت.mp3")
    # استخدم صورة افتراضية اذا ما عندك
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (1280,720), color=(135,206,235))
    d = ImageDraw.Draw(img)
    d.text((400,350), f"قصة {حيوان}", fill=(0,0,0))
    img.save("صورة.jpg")
    
    صورة = ImageClip("صورة.jpg").set_duration(صوت.duration)
    صورة = صورة.resize(lambda t: 1 + 0.03*t).set_audio(صوت)
    صورة.write_videofile(f"{حيوان}.mp4", fps=24, logger=None)
    
    await update.message.reply_video(video=open(f"{حيوان}.mp4", 'rb'), caption=f"✅ فيديو {حيوان} جاهز للرفع!")
    os.remove("صوت.mp3")
    os.remove(f"{حيوان}.mp4")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, رد))
app.run_polling()
