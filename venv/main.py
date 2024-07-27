# import logging
# import asyncio
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy import text  # Import the text function
# from aiogram import Bot, Dispatcher, types
# from aiogram.filters import Command
# from aiogram.types import Message

# # Database settings
# DATABASE_URL = "postgresql+asyncpg://postgres:pass@localhost:5432/ozarenie_test_db"

# # Bot settings
# API_TOKEN = '7050222486:AAHW-e9JU_43Cc3BWwbCewZL3UBFR-MqogQ'

# # Logging
# logging.basicConfig(level=logging.INFO)

# # Initialize bot and dispatcher
# bot = Bot(token=API_TOKEN)
# dp = Dispatcher()

# # Create engine and session factory
# engine = create_async_engine(DATABASE_URL, echo=True)
# async_session = sessionmaker(
#     bind=engine,
#     class_=AsyncSession,
#     expire_on_commit=False
# )

# # Command handler for /start
# @dp.message(Command(commands=['start']))
# async def send_welcome(message: Message):
#     username = message.from_user.username
    
#     async with async_session() as session:
#         result = await session.execute(
#             text('SELECT level FROM users WHERE telegram_nick = :username'),  # Wrap the query with text
#             {'username': username}
#         )
#         user_level = result.fetchone()

#     if user_level:
#         level = user_level['level']
#         if level == 1:
#             await message.reply('Welcome back, active user!')
#         elif level == 0:
#             await message.reply('Your account is inactive. Please contact support.')
#         else:
#             await message.reply('Unknown level. Please contact support.')
#     else:
#         await message.reply('You are not in the database.')

# async def main():
#     await dp.start_polling(bot)

# if __name__ == '__main__':
#     asyncio.run(main())


# import asyncio
# from aiogram import Bot, Dispatcher, types
# from aiogram.filters import Command
# from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.future import select
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy import Column, Integer, BigInteger

# # Настройки
# API_TOKEN = '7050222486:AAHW-e9JU_43Cc3BWwbCewZL3UBFR-MqogQ'
# DATABASE_URL = "postgresql+asyncpg://postgres:pass@localhost:5432/ozarenie_test_db"

# # Инициализация бота и диспетчера
# bot = Bot(token = API_TOKEN)
# dp = Dispatcher()

# # Настройка базы данных
# Base = declarative_base()
# engine = create_async_engine(DATABASE_URL, echo = True)
# async_session = sessionmaker(
#     engine, expire_on_commit = False, class_ = AsyncSession
# )

# # Определение модели пользователя
# class User(Base):
#     __tablename__ = 'users'
#     id = Column(Integer, primary_key = True, index = True)
#     user_id = Column(BigInteger, unique = True, index = True)
#     level = Column(Integer)

# # Сообщения в зависимости от уровня пользователя
# LEVEL_MESSAGES = {
#     0: "Привет, новичок!",
#     1: "Привет, опытный пользователь!",
#     2: "Привет, профессионал!",
#     3: "Привет, мастер!"
# }

# # Обработчик команды /start
# @dp.message(Command("start"))
# async def cmd_start(message: types.Message):
#     username = message.from_user.username

#     # Создание сессии и запрос к базе данных
#     async with async_session() as session:
#         result = await session.execute(select(User).where(User.user_id == username))
#         user = result.scalars().first()

#         if user:
#             # Пользователь найден в базе данных
#             level_message = LEVEL_MESSAGES.get(user.level, "Привет!")
#             await message.answer(level_message)
#         else:
#             # Пользователь не найден в базе данных
#             await message.answer("Тебя нет в базе данных.")

# async def main():
#     await dp.start_polling(bot)

# if __name__ == '__main__':
#     asyncio.run(main())

import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String

# Настройки
API_TOKEN = '7050222486:AAHW-e9JU_43Cc3BWwbCewZL3UBFR-MqogQ'
DATABASE_URL = "postgresql+asyncpg://postgres:pass@localhost:5432/ozarenie_test_db"

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Настройка базы данных
Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

# Определение модели пользователя
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    telegram_nick = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    level = Column(Integer, nullable=False, default=0)
    visit_count = Column(Integer, nullable=False, default=0)
    invitation_count = Column(Integer, nullable=False, default=0)
    available_invitations = Column(Integer, default=None)
    inviter = Column(String(50), default=None)

# Сообщения в зависимости от уровня пользователя
LEVEL_MESSAGES = {
    0: "Привет, новичок!",
    1: "Привет, опытный пользователь!",
    2: "Привет, профессионал!",
    3: "Привет, мастер!"
}

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    telegram_nick = message.from_user.username

    # Создание сессии и запрос к базе данных
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_nick == telegram_nick))
        user = result.scalars().first()

        if user:
            # Пользователь найден в базе данных
            level_message = LEVEL_MESSAGES.get(user.level, "Привет!")
            await message.answer(level_message)
        else:
            # Пользователь не найден в базе данных
            await message.answer("Тебя нет в базе данных.")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
