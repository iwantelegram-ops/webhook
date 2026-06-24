import os
import asyncio
from fastapi import FastAPI
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Inisialisasi FastAPI agar Railway tetap mendeteksi port aktif
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
    bot_token=BOT_TOKEN
)

@app.on_event("startup")
async def startup_event():
    """Menjalankan bot secara otomatis saat FastAPI dimulai"""
    # PERBAIKAN: Cukup panggil bot.start() saja, Pyrogram otomatis menghandle loop-nya
    if not bot.is_connected:
        await bot.start()
    print("Bot Berhasil Dijalankan Menggunakan Mode Polling!")

@app.on_event("shutdown")
async def shutdown_event():
    """Mematikan bot saat server FastAPI mati"""
    if bot.is_connected:
        await bot.stop()

@app.get("/")
async def root():
    return {"status": "Bot berjalan dengan aman via Polling!"}

# ==================== FUNGSI & HANDLER BOT ====================

# 1. Perintah /start
@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    nama_user = message.from_user.first_name
    teks = (
        f"👋 Halo **{nama_user}**!\n\n"
        "Selamat datang di Bot yang berjalan di Railway.\n"
        "Silakan pilih menu di bawah ini:"
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
    await message.reply_text(text=teks, reply_markup=tombol)

# 2. Perintah /help
@bot.on_message(filters.command("help") & filters.private)
async def help_command(client, message):
    await message.reply_text(
        "🤖 **Panduan Penggunaan Bot:**\n\n"
        "/start - Memulai menu utama\n"
        "/help - Melihat panduan ini"
    )

# 3. Menangani Klik Tombol
@bot.on_callback_query()
async def handle_callbacks(client, callback_query: CallbackQuery):
    data = callback_query.data
    
    if data == "menu_utama":
        await callback_query.edit_message_text(
            "🔥 **Ini adalah halaman Menu Utama.**\n\nFitur Anda sudah siap dikembangkan di sini.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_start")]])
        )
    elif data == "bantuan":
        await callback_query.edit_message_text(
            "ℹ️ **Halaman Bantuan**\n\nBot ini merespons dengan sangat cepat dan stabil di Railway.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_start")]])
        )
    elif data == "cek_server":
        await callback_query.edit_message_text(
            "✅ **Status Server: ONLINE**\n⚡ **Hosting:** Railway Cloud",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_start")]])
        )
    elif data == "back_to_start":
        nama_user = callback_query.from_user.first_name
        teks = f"👋 Halo **{nama_user}**!\n\nSelamat datang di Bot yang berjalan di Railway."
        tombol = InlineKeyboardMarkup([
            [InlineKeyboardButton("📱 Menu Utama", callback_data="menu_utama"), InlineKeyboardButton("ℹ️ Bantuan", callback_data="bantuan")],
            [InlineKeyboardButton("🌐 Cek Server", callback_data="cek_server")]
        ])
        await callback_query.edit_message_text(text=teks, reply_markup=tombol)
