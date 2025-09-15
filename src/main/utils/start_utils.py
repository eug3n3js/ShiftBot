import os
import logging
import signal
import sys
import asyncio
import threading

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from src.main.utils.db_helper import DatabaseHelper
from src.main.dao import UserDAO, FilterDAO
from src.main.handlers import base_router, filter_router, admin_router
from src.main.services import UserService, MessageService, ShiftService
from src.main.clients import SeleniumClient

bot_instance = None
shift_service_instance = None
shutdown_requested = False


def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    global shutdown_requested
    signal_name = signal.Signals(signum).name
    logging.warning(f"Received signal {signal_name} ({signum})")
    logging.info(f"Signal received in frame: {frame}")
    logging.info(f"Current thread: {threading.current_thread().name}")
    logging.info(f"Active tasks: {len(asyncio.all_tasks())}")
    
    shutdown_requested = True
    
    if bot_instance:
        logging.info("Bot instance found, initiating graceful shutdown...")
        # Создаем задачу для graceful shutdown
        asyncio.create_task(graceful_shutdown())
    else:
        logging.warning("Bot instance not found, forcing exit...")
        sys.exit(0)


async def graceful_shutdown():
    """Graceful shutdown процедура"""
    global bot_instance, shift_service_instance
    
    logging.info("Starting graceful shutdown...")
    
    try:
        # Останавливаем ShiftService
        if shift_service_instance:
            logging.info("Stopping ShiftService...")
            # Здесь можно добавить логику остановки ShiftService
            logging.info("ShiftService stopped")
        
        # Останавливаем бота
        if bot_instance:
            logging.info("Stopping bot...")
            await bot_instance.session.close()
            logging.info("Bot stopped")
            
    except Exception as e:
        logging.error(f"Error during graceful shutdown: {e}")
    finally:
        logging.info("Graceful shutdown completed")
        sys.exit(0)


class ServiceInitializer:

    @staticmethod
    async def initialize_database() -> DatabaseHelper:
        load_dotenv()
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise RuntimeError("DATABASE_URL is not set in environment")
        db_helper = DatabaseHelper(db_url, async_mode=True)
        # await db_helper.del_schema()
        await db_helper.create_schema()
        logging.info("Database initialized successfully")
        return db_helper

    @staticmethod
    async def initialize_selenium_client() -> SeleniumClient:
        login = os.getenv("SELENIUM_LOGIN")
        password = os.getenv("SELENIUM_PASSWORD")
        if not login or not password:
            raise RuntimeError("SELENIUM_LOGIN and SELENIUM_PASSWORD must be set in environment")
        selenium_client = SeleniumClient(login, password)
        return selenium_client

    @staticmethod
    async def initialize_all() -> None:
        db_helper = await ServiceInitializer.initialize_database()
        selenium_client = await ServiceInitializer.initialize_selenium_client()
        user_dao = UserDAO(db_helper)
        filter_dao = FilterDAO(db_helper)
        UserService.initialize(user_dao, filter_dao)
        MessageService.initialize(user_dao)
        ShiftService.initialize(user_dao, filter_dao, selenium_client)
        
        # Initialize MuteService
        from src.main.services.mute_service import MuteService
        MuteService.initialize(db_helper)


def create_dispatcher() -> Dispatcher:
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(base_router)
    dp.include_router(filter_router)
    dp.include_router(admin_router)
    return dp


async def run_bot() -> None:
    global bot_instance, shift_service_instance
    
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in environment")

    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Регистрация обработчиков сигналов
    # signal.signal(signal.SIGTERM, signal_handler)
    # signal.signal(signal.SIGINT, signal_handler)
    # signal.signal(signal.SIGHUP, signal_handler)
    #
    # logging.info("Signal handlers registered")
    # logging.info(f"Process ID: {os.getpid()}")
    # logging.info(f"Main thread: {threading.current_thread().name}")

    try:
        bot = Bot(token=token)
        bot_instance = bot
        
        dp = create_dispatcher()
        await ServiceInitializer.initialize_all()
        
        shift_service = ShiftService.get_instance()
        shift_service_instance = shift_service
        
        logging.info("Starting ShiftService...")
        await shift_service.run()
        
        logging.info("Starting bot polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except Exception as e:
        logging.error(f"Error in run_bot: {e}")
        raise
    finally:
        logging.info("run_bot() completed")


def get_required_env_vars() -> dict:
    """Получение всех необходимых переменных окружения"""
    load_dotenv()
    
    required_vars = {
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
        "DATABASE_URL": os.getenv("DATABASE_URL"),
        "SELENIUM_LOGIN": os.getenv("SELENIUM_LOGIN"),
        "SELENIUM_PASSWORD": os.getenv("SELENIUM_PASSWORD"),
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return required_vars

# Раскомментируйте для тестирования
# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(example_async_selenium_usage())
