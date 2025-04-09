import logging
import os
from datetime import datetime
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
import threading
from bot.config import BOT_TOKEN
from bot.database import Database
from bot.gfpgan_processor import process_image

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создаем семафор для ограничения одновременных подключений
MAX_CONCURRENT_USERS = 10
connection_semaphore = threading.Semaphore(MAX_CONCURRENT_USERS)

# Инициализируем базу данных
db = Database()

def start(update, context):
    """Обработчик команды /start."""
    message = (
        "👋 Привет! Я бот для улучшения качества фотографий лиц.\n\n"
        "📸 Отправь мне фотографию, и я улучшу её качество.\n"
        "⚠️ Лимит: 5 фотографий в день на пользователя.\n\n"
        "Команды:\n"
        "/start - Показать это сообщение\n"
        "/limits - Проверить оставшиеся лимиты\n"
        "/help - Получить помощь"
    )
    update.message.reply_text(message, parse_mode=ParseMode.HTML)

def help_command(update, context):
    """Обработчик команды /help."""
    help_text = (
        "🔍 <b>Как пользоваться ботом:</b>\n\n"
        "1. Отправьте фотографию с лицом\n"
        "2. Дождитесь обработки (обычно 10-30 секунд)\n"
        "3. Получите улучшенную версию\n\n"
        "⚠️ <b>Ограничения:</b>\n"
        "• Максимум 5 фото в день\n"
        "• Размер фото до 5MB\n"
        "• Фото должно содержать лицо\n\n"
        "❓ По всем вопросам: @ваш_username"
    )
    update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

def check_limits(update, context):
    """Обработчик команды /limits."""
    user_id = update.effective_user.id
    count = db.get_user_count(user_id)
    remaining = 5 - count
    message = f"📊 <b>Ваши лимиты:</b>\n\nОсталось фотографий на сегодня: {remaining}"
    update.message.reply_text(message, parse_mode=ParseMode.HTML)

def handle_photo(update, context):
    """Обработчик получения фотографий."""
    user_id = update.effective_user.id
    
    # Проверяем лимиты пользователя
    if db.get_user_count(user_id) >= 5:
        update.message.reply_text(
            "⚠️ Вы достигли дневного лимита (5 фото).\n"
            "Попробуйте завтра!"
        )
        return
    
    # Пробуем получить семафор
    if not connection_semaphore.acquire(blocking=False):
        update.message.reply_text(
            "🔄 Сервер сейчас перегружен.\n"
            "Пожалуйста, попробуйте через несколько минут."
        )
        return
    
    try:
        # Сообщаем о начале обработки
        processing_message = update.message.reply_text(
            "🔄 Обрабатываю фотографию...\n"
            "Это может занять 10-30 секунд."
        )
        
        # Получаем файл
        photo_file = update.message.photo[-1].get_file()
        
        # Создаем временные директории если их нет
        os.makedirs("temp_inputs", exist_ok=True)
        os.makedirs("temp_outputs", exist_ok=True)
        
        # Формируем пути для файлов
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_path = f"temp_inputs/{user_id}_{timestamp}.jpg"
        output_path = f"temp_outputs/{user_id}_{timestamp}_restored.jpg"
        
        # Скачиваем фото
        photo_file.download(input_path)
        
        # Обрабатываем фото
        try:
            process_image(input_path, output_path)
            
            # Отправляем обработанное фото
            with open(output_path, 'rb') as photo:
                update.message.reply_photo(
                    photo,
                    caption="✨ Фото успешно обработано!"
                )
            
            # Увеличиваем счетчик
            db.increment_user_count(user_id)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке фото: {e}")
            update.message.reply_text(
                "❌ Произошла ошибка при обработке фотографии.\n"
                "Убедитесь, что на фото есть лицо и попробуйте снова."
            )
        
        # Удаляем временные файлы
        try:
            os.remove(input_path)
            os.remove(output_path)
        except:
            pass
        
        # Удаляем сообщение о процессе обработки
        processing_message.delete()
        
    finally:
        # Освобождаем семафор
        connection_semaphore.release()

def error_handler(update, context):
    """Обработчик ошибок."""
    logger.error(f"Update {update} caused error {context.error}")
    try:
        update.message.reply_text(
            "❌ Произошла ошибка при обработке запроса.\n"
            "Пожалуйста, попробуйте позже."
        )
    except:
        pass

def main():
    """Запуск бота."""
    logger.info("Запуск бота...")
    
    # Инициализируем базу данных
    db.init()
    
    # Создаём updater
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Добавляем обработчики
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("limits", check_limits))
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))
    dp.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("Бот начинает работу...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()