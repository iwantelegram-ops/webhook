import os
import asyncio
from fastapi import FastAPI, Request, Response
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Inisialisasi FastAPI
app = FastAPI()

# Ambil token dan API dari Environment Variables Railway
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Inisialisasi Pyrogram Client
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
    print("Bot Webhook + Fitur Lengkap Berhasil Dijalankan!")

@app.on_event("shutdown")
async def shutdown_event():
    """Mematikan bot saat server FastAPI mati"""
    if bot.is_connected:
        await bot.stop()

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Menerima data dari Telegram dan diteruskan ke Pyrogram"""
    try:
        json_data = await request.json()
        await bot.feed_update(json_data)
        return Response(status_code=200)
    except Exception as e:
        print(f"Error saat memproses webhook: {e}")
        return Response(status_code=500)

# ==================== FUNGSI & HANDLER BOT ====================

# 1. Fungsi /start (Menampilkan pesan selamat datang dan Tombol Menu)
@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    nama_user = message.from_user.first_name
    teks = (
        f"👋 Halo **{nama_user}**!\n\n"
        "Selamat datang di Bot Webhook yang berjalan di Railway.\n"
        "Silakan pilih menu di bawah ini untuk mencoba fungsi bot:"
    )
    
    # Membuat susunan tombol (Inline Keyboard)
    tombol = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📱 Menu Utama", callback_data="menu_utama"),
            InlineKeyboardButton("ℹ️ Bantuan", callback_data="bantuan")
        ],
        [
            InlineKeyboardButton("🌐 Cek Server", callback_data="cek_server")
        ]
    ])
    
    await message.reply_text(text=teks, reply_markup=tombol)

# 2. Fungsi /help (Perintah teks biasa)
@bot.on_message(filters.command("help") & filters.private)
async def help_command(client, message):
    teks_bantuan = (
        "🤖 **Panduan Penggunaan Bot:**\n\n"
        "/start - Memulai bot dan membuka menu\n"
        "/help - Melihat bantuan ini\n\n"
        "Hubungi admin jika ada kendala sistem."
    )
    await message.reply_text(teks_bantuan)

# 3. Fungsi Menangani Klik Tombol (Callback Query Handler)
@bot.on_callback_query()
async def handle_callbacks(client, callback_query: CallbackQuery):
    data = callback_query.data
    
    if data == "menu_utama":
        await callback_query.answer("Anda menekan Menu Utama", show_alert=False)
        await callback_query.edit_message_text(
            "🔥 **Ini adalah halaman Menu Utama.**\n\n"
            "Anda bisa mengembangkan fungsi database, integrasi API, atau fitur lainnya di sini.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_start")]])
        )
        
    elif data == "bantuan":
        await callback_query.answer()
        await callback_query.edit_message_text(
            "ℹ️ **Halaman Bantuan**\n\n"
            "Bot ini merespons menggunakan sistem Webhook FastAPI sehingga responnya instan.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_start")]])
        )
        
    elif data == "cek_server":
        # Efek loading notifikasi di atas layar Telegram
        await callback_query.answer("Memeriksa kestabilan server...", show_alert=False)
        await callback_query.edit_message_text(
            "✅ **Status Server: ONLINE**\n"
            "⚡ **Sistem:** FastAPI + Pyrogram\n"
            "🌐 **Hosting:** Railway Cloud",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_start")]])
        )
        
    elif data == "back_to_start":
        await callback_query.answer()
        # Mengembalikan ke tampilan awal /start
        nama_user = callback_query.from_user.first_name
        teks = (
            f"👋 Halo **{nama_user}**!\n\n"
            "Selamat datang di Bot Webhook yang berjalan di Railway.\n"
            "Silakan pilih menu di bawah ini untuk mencoba fungsi bot:"
        )
        tombol = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📱 Menu Utama", callback_data="menu_utama"),
                InlineKeyboardButton("ℹ️ Bantuan", callback_data="bantuan")
            ],
            [
                InlineKeyboardButton("🌐 Cek Server", callback_data="cek_server")
            ]
        ])
        await callback_query.edit_message_text(text=teks, reply_markup=tombol)
