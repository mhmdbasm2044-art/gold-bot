import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# جرب استيراد moviepy بطريقتين
try:
    from moviepy.editor import ImageClip, AudioFileClip
except:
    from moviepy import ImageClip, AudioFileClip

from gtts import gTTS
import tempfile

TOKEN = "8871511463:AAHptY0mk4Ecn7BTsZHlNDDT7gwUsO6eVu8"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("هلا! دزلي كلمة مثل: ارنب، اسد، فيل")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"جاري عمل فيديو لـ: {text} ...")

    # هنا الكود مالتك مال انشاء الفيديو
    # مثال بسيط:
    try:
        tts = gTTS(text=text, lang='ar')
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            tts.save(fp.name)
            audio = AudioFileClip(fp.name)
            clip = ImageClip("image.jpg", duration=audio.duration) # حط صورتك
            clip = clip.with_audio(audio)
            clip.write_videofile("output.mp4", fps=24)
        
        await update.message.reply_video(video=open("output.mp4", "rb"))
    except Exception as e:
        await update.message.reply_text(f"صار خطأ: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
