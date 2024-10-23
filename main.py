import asyncio
import re
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.future import select
from sqlalchemy import Column, Integer, String, Date, Time

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

# Определение уровней пользователей
BAN_LEVEL = -1
ADMIN_LEVEL = 777

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

# Определение модели ивента
class Event(Base):
    __tablename__ = 'ivents'
    id = Column(Integer, primary_key=True, index=True)
    event_date = Column(Date, nullable=False)
    event_time = Column(Time, nullable=False)
    location = Column(String(255), nullable=False)
    event_name = Column(String(255), nullable=False)

# Определение модели билета
class Ticket(Base):
    __tablename__ = 'tickets'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    event_id = Column(Integer, nullable=False)
    code = Column(String(50), nullable=False, unique=True)

# Создание клавиатуры с кнопками
def get_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["/invite", "/buy"]
    keyboard.add(*buttons)
    return keyboard

# Проверка, забанен ли пользователь
async def is_user_banned(telegram_nick):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_nick == telegram_nick))
        user = result.scalars().first()
        return user.level == BAN_LEVEL if user else False

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    telegram_nick = message.from_user.username

    if await is_user_banned(telegram_nick):
        return  # Игнорируем забаненных пользователей

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_nick == telegram_nick))
        user = result.scalars().first()

        keyboard = get_main_keyboard()
        
        if user:
            await message.answer("Добро пожаловать в 0z4r3n13!", reply_markup=keyboard)

            if user.level == ADMIN_LEVEL:
                await message.answer("Приветули Серега, твой ботик на связи, Сосал? Походу сейчас кто-то из пользователей отлетит в бан.", reply_markup=keyboard)

            if not user.full_name:
                await message.answer("Пожалуйста, введите ваше ФИО (например: Иванов Иван Иванович).", reply_markup=keyboard)
                await state.set_state(FullNameState.waiting_for_full_name)
                await state.update_data(user_id=user.id)
            else:
                level_message = LEVEL_MESSAGES.get(user.level, "Привет!")
                await message.answer(level_message, reply_markup=keyboard)
        else:
            await message.answer("Тебя нет в базе данных.", reply_markup=keyboard)

# Обработчик команды /invite
@dp.message(Command("invite"))
async def cmd_invite(message: types.Message, state: FSMContext):
    telegram_nick = message.from_user.username

    if await is_user_banned(telegram_nick):
        return  # Игнорируем забаненных пользователей

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
    telegram_nick = message.from_user.username

    if await is_user_banned(telegram_nick):
        return  # Игнорируем забаненных пользователей

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

# Обработчик команды /buy
@dp.message(Command("buy"))
async def cmd_buy(message: types.Message):
    telegram_nick = message.from_user.username

    if await is_user_banned(telegram_nick):
        return  # Игнорируем забаненных пользователей

    async with async_session() as session:
        current_date = datetime.now().date()
        result = await session.execute(
            select(Event)
            .where(Event.event_date >= current_date)
            .order_by(Event.event_date, Event.event_time)
        )
        event = result.scalars().first()

        if event:
            event_datetime = datetime.combine(event.event_date, event.event_time)
            time_until_event = event_datetime - datetime.now()

            if time_until_event > timedelta(weeks=4):
                await message.answer("Ближайших ивентов нет.")
            else:
                # Поиск первого доступного кода в таблице Ticket
                code_result = await session.execute(
                    select(Ticket)
                    .where(Ticket.user_id == None)  # Проверка, что код не назначен никому
                    .order_by(Ticket.id)
                )
                available_ticket = code_result.scalars().first()

                if available_ticket:
                    # Назначение кода текущему пользователю
                    available_ticket.user_id = message.from_user.id
                    available_ticket.event_id = event.id

                    session.add(available_ticket)
                    await session.commit()

                    # Сообщение с информацией о покупке билета
                    await message.answer(
                        f"До ближайшего ивента {time_until_event.days} дней и {time_until_event.seconds // 3600} часов.\n"
                        f"Ваш уникальный код: {available_ticket.code}"
                    )
                else:
                    await message.answer("Нет доступных кодов для покупки билетов.")
        else:
            await message.answer("Ближайших ивентов нет.")

# Обработчик команды /me
@dp.message(Command("me"))
async def cmd_me(message: types.Message):
    telegram_nick = message.from_user.username

    if await is_user_banned(telegram_nick):
        return  # Игнорируем забаненных пользователей

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_nick == telegram_nick))
        user = result.scalars().first()

        if user:
            user_info = (
                f"Ваш ник: {user.telegram_nick}\n"
                f"ФИО: {user.full_name}\n"
                f"Уровень: {user.level}\n"
                f"Количество посещений: {user.visit_count}\n"
                f"Количество приглашений: {user.invitation_count}\n"
                f"Доступные приглашения: {user.available_invitations}"
            )
            await message.answer(user_info)
        else:
            await message.answer("Вы не зарегистрированы в системе.")

# Обработчик команды help
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    telegram_nick = message.from_user.username

    if await is_user_banned(telegram_nick):
        return  # Игнорируем забаненных пользователей

    help_text = (
        "Если у вас возникили проблемы при работе с ботом, просим выйти с нами на связь любым удобным для вас способом:\n\n"
        "@oz4r3n13supp0rt\n\n"
        "0z4r3n13supp0rt@gmail.com"
    )
    await message.answer(help_text)

# Основная функция
async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
