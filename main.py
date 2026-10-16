import os, requests, random
from gtts import gTTS
from moviepy.editor import *
from PIL import Image, ImageDraw
from openai import OpenAI

client = OpenAI(api_key=os.getenv("GROQ_KEY"), base_url="https://api.groq.com/openai/v1")

def gen():
    try:
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":"اكتب قصة قصيرة من الناصرية بالعراقي 25 كلمة مشوقة"}],
            max_tokens=80
        )
        return r.choices[0].message.content
    except Exception as e:
        print(e)
        return "ولد من الناصرية لكه سر بالاهوار غير حياته"

text = gen()
print(text)
gTTS(text, lang='ar').save("v.mp3")
img = Image.new('RGB', (1080,1920), (20,20,20))
ImageDraw.Draw(img).rounded_rectangle([30,600,1050,1300], radius=40, fill=(220,20,20))
ImageDraw.Draw(img).text((50,700), text[:120], fill=(255,255,255))
img.save("b.png")
audio = AudioFileClip("v.mp3")
ImageClip("b.png").set_duration(audio.duration+0.5).set_audio(audio).write_videofile("f.mp4", fps=24, logger=None)
requests.post(f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendVideo", data={'chat_id':os.getenv('CHAT_ID'),'caption':text}, files={'video':open('f.mp4','rb')})
