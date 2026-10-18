import os
import logging
import asyncio
import uuid
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import yt_dlp

# Tokenni koddan emas, serverning maxfiy muhit o'zgaruvchisidan (Environment Variable) olamiz
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("DIQQAT: BOT_TOKEN topilmadi! Server sozlamalaridan tokenni kiriting.")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Salom! 👋\n"
        "Men **YouTube, Instagram, TikTok, Threads va Pinterest** tarmoqlaridan video yuklab beruvchi botman.\n\n"
        "Menga shunchaki video havolasini yuboring!"
    )

@dp.message()
async def download_video(message: types.Message):
    url = message.text.strip()
    
    if not url.startswith("http"):
        await message.answer("⚠️ Iltimos, to'g'ri havola yuboring!")
        return

    processing_msg = await message.answer("⏳ Video yuklab olinmoqda, biroz kuting...")
    
    file_id = str(uuid.uuid4())
    ydl_opts = {
        'format': 'best',
        'outtmpl': f'{DOWNLOAD_DIR}/{file_id}.%(ext)s',
        'noplaylist': True,
    }
    
    file_path = None
    try:
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        loop = asyncio.get_running_loop()
        file_path = await loop.run_in_executor(None, download)

        if file_path and os.path.exists(file_path):
            await message.answer_chat_action("upload_video")
            video_file = types.FSInputFile(file_path)
            await message.answer_video(video=video_file, caption="✅ Marhamat!")
            await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
        else:
            await message.answer("❌ Videoni yuklab olishda xatolik yuz berdi.")
            await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
            
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await message.answer("❌ Kechirasiz, bu havoladan videoni yuklab bo'lmadi.")
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
        except:
            pass
            
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
