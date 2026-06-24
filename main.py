import os
import asyncio
from fastapi import FastAPI, Request, Response
from pyrogram import Client
from pyrogram.types import Update

# Inisialisasi FastAPI
app = FastAPI()

# Ambil token dan API dari Environment Variables Railway
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Inisialisasi Pyrogram Client (Tanpa file session untuk Webhook)
bot = Client(
    "my_bot",
    api_id=int(API_ID) if API_ID else None,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

@app.on_event("startup")
async def startup_event():
    """Menjalankan bot saat server FastAPI mulai"""
    if not bot.is_connected:
        await bot.start()
    print("Bot Webhook + Tombol DM Berhasil Dijalankan!")

@app.on_event("shutdown")
async def shutdown_event():
    """Mematikan bot saat server FastAPI mati"""
    if bot.is_connected:
        await bot.stop()

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Menerima kiriman data (Update) dari Telegram"""
    try:
        json_data = await request.json()
        
        # PERBAIKAN DI SINI: Menggunakan de_json bawaan Pyrogram
        update = Update.de_json(bot, json_data)
        
        # Biarkan Pyrogram memproses update (seperti /start, klik tombol, dll)
        if update:
            await bot.feed_update(update)
            
        return Response(status_code=200)
    except Exception as e:
        print(f"Error saat memproses webhook: {e}")
        return Response(status_code=500)

# Contoh handler sederhana untuk merespons /start
@bot.on_message()
async def handle_message(client, message):
    if message.text == "/start":
        await message.reply_text(
            f"Halo {message.from_user.first_name}! Bot Anda berhasil aktif via Webhook Railway! 🚀"
        )
