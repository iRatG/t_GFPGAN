import logging
from telegram.ext import Updater, CommandHandler
from bot.config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

def start(update, context):
    """Обработчик команды /start."""
    update.message.reply_text('Привет! Я тестовый бот!')
    logger.info(f"Пользователь {update.effective_user.id} запустил бота")

def main():
    """Запуск бота."""
    logger.info("Запуск бота...")
    
    # Создаём объект updater
    updater = Updater(BOT_TOKEN, use_context=True)
    
    # Получаем диспетчер
    dp = updater.dispatcher
    
    # Добавляем обработчик команды /start
    dp.add_handler(CommandHandler("start", start))
    
    # Запускаем бота
    logger.info("Бот начинает работу...")
    updater.start_polling()
    
    # Держим бота запущенным до прерывания
    updater.idle()

if __name__ == '__main__':
    main()