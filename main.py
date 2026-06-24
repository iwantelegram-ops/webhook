import os
from fastapi import FastAPI, Request, Response
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# Inisialisasi FastAPI
app = FastAPI()

# Ambil data dari Environment Variables Railway
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Inisialisasi Pyrogram Client (in_memory=True agar tidak buat file session)
bot = Client(
    "my_bot",
    api_id=int(API_ID) if API_ID else None,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

@app.on_event("startup")
async def startup_event():
    """Menyalakan bot saat FastAPI mulai"""
    if not bot.is_connected:
        await bot.start()
    print("FastAPI Webhook Server Starter!")

@app.on_event("shutdown")
async def shutdown_event():
    """Mematikan bot saat FastAPI mati"""
    if bot.is_connected:
        await bot.stop()

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Menerima data JSON dari Telegram Webhook"""
    try:
        json_data = await request.json()
        
        # JIKA YANG MASUK ADALAH PESAN TEKS (MESSAGE)
        if "message" in json_data:
            # Saring data mentah menjadi objek Message Pyrogram
            message = await Message.parse(bot, json_data["message"])
            # Tembakkan langsung ke fungsi handler pesan kita
            await handle_message(bot, message)
            
        return Response(status_code=200)
    except Exception as e:
        print(f"Eror Webhook: {e}")
        return Response(status_code=500)

# ==================== HANDLER BOT LENGKAP ====================

async def handle_message(client, message: Message):
    """Fungsi manual untuk memproses pesan teks"""
    if not message.text:
        return
        
    if message.text.startswith("/start"):
        nama_user = message.from_user.first_name if message.from_user else "User"
        teks = f"👋 Halo **{nama_user}**!\n\nBot Webhook FastAPI Anda Berhasil Merespons! 🚀"
        
        tombol = InlineKeyboardMarkup([
            [InlineKeyboardButton("📱 Menu Utama", callback_data="menu")]
        ])
        await message.reply_text(text=teks, reply_markup=tombol)
