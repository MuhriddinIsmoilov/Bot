import os
import logging
import asyncio
import uuid
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("DIQQAT: BOT_TOKEN topilmadi!")

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
        'noplaylist': `True`,
        # YouTube bot sifatida aniqlab qolmasligi uchun qo'shimcha user-agent sozlamalari
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
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
            # Xatolik to'g'irlandi: bot orqali chat action yuboriladi
            await bot.send_chat_action(chat_id=message.chat.id, action="upload_video")
            
            video_file = types.FSInputFile(file_path)
            await message.answer_video(video=video_file, caption="✅ Marhamat!")
            
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
            except:
                pass
        else:
            await message.answer("❌ Videoni yuklab olishda xatolik yuz berdi.")
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
            except:
                pass
            
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await message.answer("❌ Kechirasiz, bu havoladan videoni yuklab bo'lmadi (YouTube himoyasi yoki yaroqsiz havola).")
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

# --- RENDER WEB SERVICE UCHUN PORT OCHISH (No open ports xatosini yo'qotish uchun) ---
async def handle(request):
    return web.Response(text="Bot ishlayapti!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    # Veb server va Telegram botni bir vaqtda ishga tushiramiz
    await asyncio.gather(
        web_server(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
