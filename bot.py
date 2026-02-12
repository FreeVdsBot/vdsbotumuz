import os
import json
import subprocess
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = "8587429954:AAEaVLl4lpHTc9Wf8wc4IZGSzhiXiTLNPns"

DATA_FILE = "data.json"
LOG_FILE = "logs.txt"

# ================== WEB SERVER ==================
app = Flask(__name__)

@app.route("/")
def home():
    return "VDS Bot Aktif!"

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

threading.Thread(target=run_web).start()

# ================== DATA ==================
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"current_file": None}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

current_process = None

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("VDS Panel Hazır.\nDosya gönder, sonra /calistir")

# ================== DOSYA YÜKLE ==================
async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        file = await update.message.document.get_file()
        filename = update.message.document.file_name
        await file.download_to_drive(filename)

        data = load_data()
        data["current_file"] = filename
        save_data(data)

        await update.message.reply_text(f"{filename} yüklendi.")

# ================== ÇALIŞTIR ==================
async def run_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_process
    data = load_data()

    if not data["current_file"]:
        await update.message.reply_text("Önce dosya yükle.")
        return

    if current_process:
        await update.message.reply_text("Zaten çalışıyor.")
        return

    current_process = subprocess.Popen(
        ["python", data["current_file"]],
        stdout=open(LOG_FILE, "a"),
        stderr=subprocess.STDOUT
    )

    keyboard = [
        [
            InlineKeyboardButton("Durdur", callback_data="stop"),
            InlineKeyboardButton("Sil", callback_data="delete"),
        ]
    ]

    await update.message.reply_text(
        "Başlatıldı.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================== DURDUR/SİL ==================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_process
    query = update.callback_query
    await query.answer()

    data = load_data()

    if query.data == "stop":
        if current_process:
            current_process.terminate()
            current_process = None
            await query.edit_message_text("Durduruldu.")
        else:
            await query.edit_message_text("Çalışan yok.")

    elif query.data == "delete":
        if data["current_file"]:
            try:
                os.remove(data["current_file"])
                data["current_file"] = None
                save_data(data)
                await query.edit_message_text("Silindi.")
            except:
                await query.edit_message_text("Silinemedi.")

# ================== LOGLAR ==================
async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(LOG_FILE):
        await update.message.reply_text("Log yok.")
        return

    with open(LOG_FILE, "r") as f:
        content = f.read()

    if not content:
        content = "Boş log."

    await update.message.reply_text(content[:4000])

# ================== PIP ==================
async def pip_install(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Kullanım: /pip paket")
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

# ================== MAIN ==================
def main():
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("calistir", run_file))
    app_bot.add_handler(CommandHandler("loglar", logs))
    app_bot.add_handler(CommandHandler("pip", pip_install))
    app_bot.add_handler(MessageHandler(filters.Document.ALL, upload))
    app_bot.add_handler(CallbackQueryHandler(buttons))

    app_bot.run_polling()

if __name__ == "__main__":
    main()
