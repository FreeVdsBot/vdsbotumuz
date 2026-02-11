import os
import subprocess
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ====== AYARLAR ======
BOT_TOKEN = "8486391588:AAEuBbgpmwnMwB6IW_Zlg6oUTxfE0X44fac"
ADMIN_ID = 8352226813  # Admin Telegram ID
# =====================

app = Flask(__name__)

@app.route("/")
def home():
    return "VDS Bot Aktif!"

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

threading.Thread(target=run_web).start()

# ===== GLOBAL =====
current_process = None
current_file = None
log_file = "bot_logs.txt"

# ===== ADMIN KONTROL =====
def is_admin(user_id):
    return user_id == ADMIN_ID

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("VDS Bot Hazır.")

# ===== DOSYA YÜKLEME =====
async def upload_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_file
    if not is_admin(update.effective_user.id):
        return

    if update.message.document:
        file = await update.message.document.get_file()
        file_path = update.message.document.file_name
        await file.download_to_drive(file_path)
        current_file = file_path
        await update.message.reply_text(f"{file_path} yüklendi.")

# ===== DOSYA BAŞLAT =====
async def run_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_process, current_file
    if not is_admin(update.effective_user.id):
        return

    if not current_file:
        await update.message.reply_text("Önce dosya yükle.")
        return

    if current_process:
        await update.message.reply_text("Zaten çalışıyor.")
        return

    with open(log_file, "w") as f:
        pass

    current_process = subprocess.Popen(
        ["python", current_file],
        stdout=open(log_file, "a"),
        stderr=subprocess.STDOUT
    )

    keyboard = [
        [
            InlineKeyboardButton("Durdur", callback_data="stop"),
            InlineKeyboardButton("Sil", callback_data="delete")
        ]
    ]

    await update.message.reply_text(
        f"{current_file} başlatıldı.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== DURDUR / SİL =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_process, current_file
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    if query.data == "stop":
        if current_process:
            current_process.terminate()
            current_process = None
            await query.edit_message_text("Durduruldu.")
        else:
            await query.edit_message_text("Çalışan dosya yok.")

    elif query.data == "delete":
        if current_file:
            try:
                os.remove(current_file)
                current_file = None
                await query.edit_message_text("Dosya silindi.")
            except:
                await query.edit_message_text("Silinemedi.")
        else:
            await query.edit_message_text("Dosya yok.")

# ===== LOG GÖSTER =====
async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not os.path.exists(log_file):
        await update.message.reply_text("Log yok.")
        return

    with open(log_file, "r") as f:
        data = f.read()

    if not data:
        data = "Boş log."

    await update.message.reply_text(data[:4000])

# ===== PIP YÜKLE =====
async def pip_install(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if len(context.args) == 0:
        await update.message.reply_text("Kullanım: /pip paketadı")
        return

    package = context.args[0]

    process = subprocess.Popen(
        ["pip", "install", package],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    output = process.communicate()[0]

    await update.message.reply_text(output[:4000])

# ===== BOT BAŞLAT =====
def main():
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("calistir", run_file))
    app_bot.add_handler(CommandHandler("loglar", logs))
    app_bot.add_handler(CommandHandler("pip", pip_install))
    app_bot.add_handler(MessageHandler(filters.Document.ALL, upload_file))
    app_bot.add_handler(telegram.ext.CallbackQueryHandler(button_handler))

    app_bot.run_polling()

if __name__ == "__main__":
    main()
