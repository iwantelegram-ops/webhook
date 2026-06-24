import os
import hashlib
import time
import asyncio
from fastapi import FastAPI, Request
from pyrogram import Client, filters
from pyrogram.types import Update, InlineKeyboardMarkup, InlineKeyboardButton

# 1. Inisialisasi FastAPI
app = FastAPI()

# 2. Inisialisasi Pyrogram Client
API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH", "your_api_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token")

bot = Client("antispam_webhook", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ── DATABASE/CONFIG SIMULASI (Menggunakan RAM untuk contoh) ──
# Di bot asli, bagian ini biasanya terhubung ke MongoDB/SQL
group_settings = {}  # Format: {chat_id: {"global": True, "local": True}}

# ── CACHE RAM ANTISPAM ──
_local_flood_cache = {}
_global_text_tracker = {}
_global_text_blacklist = {}

_FLOOD_WINDOW = 5.0
_MAX_DUPLICATE = 2
_MASS_BURST_WINDOW = 1.5
_MASS_BURST_LIMIT = 3
_LOCK_DURATION = 10.0


# ── TAMBAHAN: HANDLER UNTUK DM BOT (MENU PENGATURAN) ──
@bot.on_message(filters.private & filters.command("start"))
async def start_private(client, message):
    # Membuat tombol-tombol indah di DM
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Proteksi Global", callback_data="toggle_global"),
            InlineKeyboardButton("Proteksi Lokal", callback_data="toggle_local")
        ],
        [
            InlineKeyboardButton("Lihat Status Fitur", callback_data="view_status")
        ],
        [
            InlineKeyboardButton("Tutup Menu ❌", callback_data="close_menu")
        ]
    ])
    
    await message.reply_text(
        "👋 **Halo! Selamat datang di Menu Pengaturan Bot.**\n\n"
        "Silakan klik tombol di bawah ini untuk mengatur fitur antispam Anda:",
        reply_markup=keyboard
    )


# ── TAMBAHAN: HANDLER TOMBOL DIKLIK (CALLBACK QUERY) ──
@bot.on_callback_query()
async def handle_buttons(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    # Inisialisasi config default jika belum ada
    if user_id not in group_settings:
        group_settings[user_id] = {"global": True, "local": True}
        
    if data == "toggle_global":
        # Balikkan nilai True jadi False, atau False jadi True
        group_settings[user_id]["global"] = not group_settings[user_id]["global"]
        status = "AKTIF ✅" if group_settings[user_id]["global"] else "NON-AKTIF ❌"
        await callback_query.answer(f"Proteksi Global sekarang {status}", show_alert=True)
        
    elif data == "toggle_local":
        group_settings[user_id]["local"] = not group_settings[user_id]["local"]
        status = "AKTIF ✅" if group_settings[user_id]["local"] else "NON-AKTIF ❌"
        await callback_query.answer(f"Proteksi Lokal sekarang {status}", show_alert=True)
        
    elif data == "view_status":
        g_status = "✅ AKTIF" if group_settings[user_id]["global"] else "❌ NON-AKTIF"
        l_status = "✅ AKTIF" if group_settings[user_id]["local"] else "❌ NON-AKTIF"
        
        await callback_query.edit_message_text(
            f"📊 **Status Pengaturan Anda saat ini:**\n\n"
            f"🌐 Anti-Spam Global: {g_status}\n"
            f"🏠 Anti-Spam Lokal: {l_status}\n\n"
            "Klik tombol di bawah untuk mengubah kembali:",
            reply_markup=callback_query.message.reply_markup # Tetap tampilkan tombol yang sama
        )
        return
        
    elif data == "close_menu":
        await callback_query.message.delete()
        return

    # Setelah tombol diklik, kita perbarui teks atau status tombolnya jika diperlukan
    await callback_query.answer()


# ── HANDLER UNTUK ANTISPAM DI GRUP (Modifikasi dengan pengecekan toggle) ──
@bot.on_message(filters.group & ~filters.service)
async def handle_group_message(client, message):
    if not message.from_user:
        return
    
    cid, uid, mid = message.chat.id, message.from_user.id, message.id
    content = (message.text or message.caption or "").strip()
    
    if not content or content.startswith("/"):
        return

    # Ambil pengaturan grup (jika tidak ada, anggap True secara bawaan)
    # Catatan: Di real bot, Anda harus mencocokkan pengaturan berdasarkan `cid` (ID Grup) bukan `uid`
    cfg = group_settings.get(cid, {"global": True, "local": True})
    global_on = cfg.get("global", True)
    local_on = cfg.get("local", True)

    content_hash = hashlib.md5(content.encode("utf-8", errors="ignore")).hexdigest()
    now_ts = time.time()

    # ── PROTEKSI A & B (Hanya jalan jika global_on == True) ──
    if global_on:
        if cid in _global_text_blacklist and content_hash in _global_text_blacklist[cid]:
            if now_ts < _global_text_blacklist[cid][content_hash]:
                await message.delete()
                return
            else:
                _global_text_blacklist[cid].pop(content_hash, None)

        if cid not in _global_text_tracker:
            _global_text_tracker[cid] = {}
        if content_hash not in _global_text_tracker[cid]:
            _global_text_tracker[cid][content_hash] = []

        _global_text_tracker[cid][content_hash].append(now_ts)
        _global_text_tracker[cid][content_hash] = [
            ts for ts in _global_text_tracker[cid][content_hash] if (now_ts - ts) <= _MASS_BURST_WINDOW
        ]

        if len(_global_text_tracker[cid][content_hash]) >= _MASS_BURST_LIMIT:
            if cid not in _global_text_blacklist:
                _global_text_blacklist[cid] = {}
            _global_text_blacklist[cid][content_hash] = now_ts + _LOCK_DURATION
            await message.delete()
            return

    # ── PROTEKSI C (Hanya jalan jika local_on == True) ──
    if local_on:
        if cid not in _local_flood_cache:
            _local_flood_cache[cid] = {}
        
        user_flood_data = _local_flood_cache[cid].get(uid)
        if user_flood_data:
            last_hash, last_time, duplicate_count = user_flood_data
            if last_hash == content_hash and (now_ts - last_time) < _FLOOD_WINDOW:
                duplicate_count += 1
                _local_flood_cache[cid][uid] = (content_hash, now_ts, duplicate_count)
                if duplicate_count >= _MAX_DUPLICATE:
                    await message.delete()
                    return
            else:
                _local_flood_cache[cid][uid] = (content_hash, now_ts, 1)
        else:
            _local_flood_cache[cid][uid] = (content_hash, now_ts, 1)


# 4. Lifespan/Startup FastAPI
@app.on_event("startup")
async def startup_event():
    await bot.start()
    print("Bot Webhook + Tombol DM Berhasil Dijalankan!")

@app.on_event("shutdown")
async def shutdown_event():
    await bot.stop()

# 5. Jalur Terima Setoran Webhook dari Telegram
@app.post("/webhook")
async def telegram_webhook(request: Request):
    json_data = await request.json()
    update = Update.into_object(bot, json_data)
    asyncio.create_task(bot.feed_update(update))
    return {"status": "ok"}

@app.get("/")
def index():
    return {"message": "Bot is Online with Settings Panel!"}
