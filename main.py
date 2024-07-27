import asyncio
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.future import select
from sqlalchemy import Column, Integer, String

# Настройки
API_TOKEN = '7050222486:AAHW-e9JU_43Cc3BWwbCewZL3UBFR-MqogQ'
DATABASE_URL = "postgresql+asyncpg://postgres:pass@localhost:5432/ozarenie_test_db"

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

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

# Определение состояний для FSM
class InviteState(StatesGroup):
    waiting_for_invite_nickname = State()

class FullNameState(StatesGroup):
    waiting_for_full_name = State()

# Проверка валидности ФИО
def is_valid_full_name(full_name: str) -> bool:
    return bool(re.match(r'^[A-Za-zА-Яа-яёЁ]+\s[A-Za-zА-Яа-яёЁ]+\s[A-Za-zА-Яа-яёЁ]+$', full_name))

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    telegram_nick = message.from_user.username

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_nick == telegram_nick))
        user = result.scalars().first()

        if user:
            if not user.full_name:
                await message.answer("Пожалуйста, введите ваше ФИО (например: Иванов Иван Иванович).")
                await state.set_state(FullNameState.waiting_for_full_name)
                await state.update_data(user_id=user.id)
            else:
                level_message = LEVEL_MESSAGES.get(user.level, "Привет!")
                await message.answer(level_message)
        else:
            await message.answer("Тебя нет в базе данных.")

@dp.message(FullNameState.waiting_for_full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    full_name = message.text.strip()
    
    if not is_valid_full_name(full_name):
        await message.answer("Некорректный формат ФИО. Пожалуйста, введите ваше ФИО в формате 'Фамилия Имя Отчество'.")
        return
    
    data = await state.get_data()
    user_id = data['user_id']

    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if user:
            user.full_name = full_name
            session.add(user)
            await session.commit()
            await message.answer("Ваше ФИО успешно сохранено!")
    
    await state.clear()

# Обработчик команды /me
@dp.message(Command("me"))
async def cmd_me(message: types.Message):
    telegram_nick = message.from_user.username

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_nick == telegram_nick))
        user = result.scalars().first()

        if user:
            invitees_result = await session.execute(select(User).where(User.inviter == telegram_nick))
            invitees = invitees_result.scalars().all()
            invitees_list = "\n".join([invitee.telegram_nick for invitee in invitees]) or "Нет приглашенных пользователей"

            user_info = (
                f"Имя пользователя: {user.full_name}\n"
                f"Уровень: {user.level}\n"
                f"Количество посещений: {user.visit_count}\n"
                f"Количество приглашений: {user.invitation_count}\n"
                f"Доступно приглашений: {user.available_invitations if user.available_invitations is not None else 'Нет данных'}\n"
                f"Вас пригласил: {user.inviter if user.inviter else 'Никто'}\n"
                f"Вы пригласили:\n{invitees_list}"
            )
            await message.answer(user_info)
        else:
            await message.answer("Тебя нет в базе данных.")

# Обработчик команды /level
@dp.message(Command("level"))
async def cmd_level(message: types.Message):
    answer = (
        "Существует три уровня участника. Уровень повышается засчет посещения наших мероприятий. "
        "На каждом уровне доступно ограниченное количество приглашений (они обновляются каждое мероприятие).\n\n"
        "1 посещение - 1й уровень - 1 приглашение\n"
        "3 посещения - 2й уровень - 2 приглашения\n"
        "5 посещений - 3й уровень - 3 приглашения\n\n"
        "Вы можете использовать свои приглашения, чтобы пригласить на мероприятие своих друзей, не являющихся участниками нашего общества. "
        "После этого они также будут внесены в список наших участников."
    )
    await message.answer(answer)

# Обработчик команды /invite
@dp.message(Command("invite"))
async def cmd_invite(message: types.Message, state: FSMContext):
    telegram_nick = message.from_user.username

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_nick == telegram_nick))
        user = result.scalars().first()

        if user:
            if user.available_invitations and user.available_invitations > 0:
                invite_message = (
                    f"Вы посетили {user.visit_count} наше мероприятие.\n"
                    f"Ваш уровень: {user.level}\n"
                    f"Вы уже пригласили: {user.invitation_count}\n"
                    f"Вам доступно {user.available_invitations} приглашение(ий)\n"
                    "Введите никнейм вашего друга в телеграме"
                )
                await message.answer(invite_message)
                await state.set_state(InviteState.waiting_for_invite_nickname)
                await state.update_data(inviter=telegram_nick)
            else:
                invite_message = (
                    f"Вы посетили {user.visit_count} наше мероприятие.\n"
                    f"Ваш уровень: {user.level}\n"
                    f"Вы уже пригласили: {user.invitation_count}\n"
                    "Вам не доступны приглашения"
                )
                await message.answer(invite_message)
        else:
            await message.answer("Тебя нет в базе данных.")

@dp.message(InviteState.waiting_for_invite_nickname)
async def process_invite_nickname(message: types.Message, state: FSMContext):
    invitee_nick = message.text.strip().lstrip('@')
    data = await state.get_data()
    inviter_nick = data['inviter']

    async with async_session() as session:
        existing_user_result = await session.execute(select(User).where(User.telegram_nick == invitee_nick))
        existing_user = existing_user_result.scalars().first()

        if existing_user:
            await message.answer("Пользователь с таким никнеймом уже существует в базе данных.")
        else:
            inviter_result = await session.execute(select(User).where(User.telegram_nick == inviter_nick))
            inviter = inviter_result.scalars().first()

            if inviter and inviter.available_invitations and inviter.available_invitations > 0:
                inviter.available_invitations -= 1
                inviter.invitation_count += 1
                session.add(inviter)

                new_user = User(
                    telegram_nick=invitee_nick,
                    full_name="",
                    level=0,
                    visit_count=0,
                    invitation_count=0,
                    available_invitations=0,
                    inviter=inviter_nick
                )
                session.add(new_user)
                await session.commit()

                await message.answer(f"Пользователь @{invitee_nick} успешно приглашен!")
            else:
                await message.answer("У вас недостаточно приглашений для этого действия.")

    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
