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
