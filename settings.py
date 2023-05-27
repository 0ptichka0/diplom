
import aiogram
import logging

from aiogram.bot import api
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from psycopg2 import OperationalError
import psycopg2

token = ""
url = "https://api.telegram.org/bot"
channel_id = "@SBDRPO_bot"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PATCHED_URL = "https://telegg.ru/orig/bot{token}/{method}"
setattr(api, 'API_URL', PATCHED_URL)

bot = Bot(token = token)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)

def create_connection(db_name, db_user, db_password, db_host, db_port):
    connection = None
    try:
        connection = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        pass
        print(f"The error '{e}' occurred")
    connection.autocommit = True
    return connection

connection = create_connection("postgres", "postgres", "1234", "127.0.0.1", "5432")
