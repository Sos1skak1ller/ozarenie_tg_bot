import asyncio
import re
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.future import select
from sqlalchemy import Column, Integer, String, Date, Time, Text
from keyboards import get_main_keyboard
from aiogram import F
from aiogram import types
from sqlalchemy.future import select



# Настройки
API_TOKEN = '7050222486:AAHW-e9JU_43Cc3BWwbCewZL3UBFR-MqogQ'
# DATABASE_URL = "postgresql+asyncpg://postgres:pass@localhost:5432/ozarenie_test_db"
# DATABASE_URL = "postgresql+asyncpg://myuser:mypassword@localhost:5432/ozarenie_db"
DATABASE_URL = "postgresql+asyncpg://myuser:mypassword@localhost:5432/mydatabase"



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

LEVEL_MESSAGES = {
    0: "Добро пожаловать в 0z4r3n13, новичок!",
    1: "Добро пожаловать в 0z4r3n13, пользователь 1 уровня!",
    2: "Добро пожаловать в 0z4r3n13, пользователь 2 уровня!",
    3: "Добро пожаловать в 0z4r3n13, пользователь 3 уровня!"
}

class FullNameState(StatesGroup):
    waiting_for_full_name = State()

# Определение состояний для FSM
class InviteState(StatesGroup):
    waiting_for_invite_nickname = State()

# Определение модели пользователя
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    telegram_nick = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(250), nullable=True)
    level = Column(Integer, nullable=False, default=0)
    visit_count = Column(Integer, nullable=False, default=0)
    invitation_count = Column(Integer, nullable=False, default=0)
    available_invitations = Column(Integer, default=None)
    inviter = Column(String(100), default=None)

# Определение модели ивента
class Event(Base):
    __tablename__ = 'ivents'
    id = Column(Integer, primary_key=True, index=True)
    event_date = Column(Date, nullable=False)
    event_time = Column(Time, nullable=False)
    location = Column(String(255), nullable=False)
    event_name = Column(String(255), nullable=False)
    tickets_sale_link = Column(String) 

# Определение модели билета
class Ticket(Base):
    __tablename__ = 'tickets'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=True)
    event_id = Column(Integer, nullable=False)
    code = Column(String, nullable=False, unique=False)

class InviteState(StatesGroup):
    waiting_for_invite_nickname = State()

class FullNameState(StatesGroup):
    waiting_for_full_name = State()

class BanState(StatesGroup):
    waiting_for_ban_name = State()

class UnBanState(StatesGroup):
    waiting_for_unban_name = State()

# Проверка валидности ФИО
def is_valid_full_name(full_name: str) -> bool:
    return bool(re.match(r'^[A-Za-zА-Яа-яёЁ]+\s[A-Za-zА-Яа-яёЁ]+\s[A-Za-zА-Яа-яёЁ]+$', full_name))

# Проверка, забанен ли пользователь
async def is_user_banned(telegram_nick):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_nick == telegram_nick))
        user = result.scalars().first()
        return user.level == BAN_LEVEL if user else False
    
# Метод для получения списка приглашенных пользователей
async def get_invited_users(telegram_nick: str, session) -> str:
    result = await session.execute(select(User).where(User.inviter == telegram_nick))
    invited_users = result.scalars().all()

    if invited_users:
        return "\n".join(user.telegram_nick for user in invited_users)
    else:
        return "Нет приглашенных пользователей."
    

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
            if not user.full_name:
                await message.answer("Пожалуйста, введите ваше ФИО (например: Иванов Иван Иванович).")
                await state.set_state(FullNameState.waiting_for_full_name)
                await state.update_data(user_id=user.id)
                return  # Выход из функции после запроса ФИО

            # Если у пользователя есть полное имя, проверяем уровень
            if user.level == ADMIN_LEVEL:
                await message.answer("Это админка, прошу тебя использовать скрытый функционал с умом. \n\n Спсок закрытых функций:\n /ban - бан пользователя,\n /unban - разбан пользователя,\n /stop - Выключение бота ТОЛЬКО ЭКСТРЕННЫЕ СЛУЧАИ!!! \n ВОЗМОЖНА ПОТЕРЯ НЕКОТОРЫХ ДАННЫХ ДЛЯ БАЗЫ ДАННЫХ!!! \n\n CЁГА ПИШИ МИХАИЛУ )))", reply_markup=keyboard)
            else:
                level_message = LEVEL_MESSAGES.get(user.level)
                await message.answer(level_message, reply_markup=keyboard)
        else:
            await message.answer("Вас нет в базе данных.\nЕсли вы были гостем нашего превого мероприятия «Anniversary 20th», напиши нам: \n\n 0z4r3n13supp0rt@gmail.com \n\n @oz4r3n13support")

@dp.message(FullNameState.waiting_for_full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    full_name = message.text.strip()

    data = await state.get_data()
    user_id = data['user_id']
    keyboard = get_main_keyboard()

    async with async_session() as session:
        user = await session.get(User, user_id)  # Получаем пользователя по ID
        if user:
            user.full_name = full_name  # Обновляем ФИО
            await session.commit()  # Сохраняем изменения
            level_message = LEVEL_MESSAGES.get(user.level)
            await message.answer(f"Ваше ФИО успешно сохранено!\n{level_message}", reply_markup=keyboard)
        else:
            await message.answer("Пользователь не найден.")
    
    await state.clear()  # Убираем состояние после успешного ввода

# Обработчик команды /invite
async def cmd_invite(message: types.Message, state: FSMContext):
    telegram_nick = message.from_user.username

    if await is_user_banned(telegram_nick):
        return  # Игнорируем забаненных пользователей

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_nick == telegram_nick))
        user = result.scalars().first()

        if user:
            if user.available_invitations and user.available_invitations > 0:
                invited_users = await get_invited_users(telegram_nick, session)

                invite_message = (
                    f"Вы посетили {user.visit_count} наше мероприятие.\n"
                    f"Ваш уровень: {user.level}\n"
                    f"Вы уже пригласили: {user.invitation_count}\n"
                    f"Вам доступно {user.available_invitations} приглашение(ий)\n"
                    "Вы пригласили:\n" + invited_users + 
                    "\nВведите никнейм вашего друга в телеграме"
                )
                await state.set_state(InviteState.waiting_for_invite_nickname)
                await message.answer(invite_message)
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
            await message.answer("Вас нет в базе данных.")

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
                    full_name=NULL,
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

# Обработчик команды /level
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

# Обработчик команды /buy
async def cmd_buy(message: types.Message):
    telegram_nick = message.from_user.username

    if await is_user_banned(telegram_nick):
        return  # Игнорируем забаненных пользователей

    async with async_session() as session:
        current_date = datetime.now().date()

        # Проверка, купил ли пользователь уже билет
        ticket_check_result = await session.execute(
            select(Ticket)
            .where(Ticket.user_id == telegram_nick)
        )
        existing_ticket = ticket_check_result.scalars().first()

        if existing_ticket:
            await message.answer(
                "Вы уже купили билет.\n"
                "Один пользователь может купить только один билет.\n"
                "Используйте команду 'Обо мне', чтобы получить информацию о вашем билете."
            )
            return  # Завершаем выполнение функции

        # Поиск ближайшего события
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
                await message.answer("📅 Ближайших ивентов нет.")
            else:
                # Поиск первого доступного кода в таблице Ticket, который не назначен никому
                code_result = await session.execute(
                    select(Ticket)
                    .where(Ticket.user_id == None)  # Проверка, что код не назначен никому
                    .order_by(Ticket.id)
                )
                available_ticket = code_result.scalars().first()

                if available_ticket:
                    available_ticket.user_id = telegram_nick  # Назначаем ник пользователя
                    # available_ticket.event_id = event.id  # Привязываем к текущему событию
                    await session.commit()
                    # Формируем ответное сообщение
                    ticket_link = event.tickets_sale_link
                    await message.answer(
                        f"Вы покупаете билет на событие: {event.event_name}!\n\n"
                        f"Чтобы продолжить покупку билета, перейдите по следующей ссылке:\n"
                        f"{ticket_link}\n\n"
                        f"Введите на сайте код: "
                    )
                    await message.answer(available_ticket.code)
                    await message.answer("И оплатите билет.\n Напоминаем вам, что по одному коду можно купить только один билет!")
                else:
                    await message.answer("Извините, билеты закончились.")
        else:
            await message.answer(
                "Доступных ивентов пока нет.\n"
                "Ждите новости о ближайших релизах в нашем телеграм-канале: @oz4r3n13."
            )

# Обработчик команды /ban
async def cmd_ban(message: types.Message, state: FSMContext):
    telegram_nick = message.from_user.username

    # Проверяем, является ли пользователь администратором
    async with async_session() as session:
        admin_result = await session.execute(select(User).where(User.telegram_nick == telegram_nick))
        admin_user = admin_result.scalars().first()

        if admin_user and admin_user.level == 777:  # Проверяем уровень администратора
            parts = message.text.split()
            if len(parts) < 2:
                # Если никнейм не указан, запрашиваем его
                await state.set_state(BanState.waiting_for_ban_name) # Устанавливаем состояние ожидания никнейма
                await message.answer("Пожалуйста, укажите никнейм пользователя, которого хотите забанить.")
                return

            user_to_ban_nick = parts[1].lstrip('@')
            await ban_user(user_to_ban_nick, message)
        else:
            await message.answer("❌ У вас недостаточно прав для выполнения этой команды. ❌")

# Обработчик для получения никнейма после запроса
async def process_ban_username(message: types.Message, state: FSMContext):
    user_to_ban_nick = message.text.lstrip('@')
    await ban_user(user_to_ban_nick, message)
    await state.clear()  # Завершаем состояние

# Функция для выполнения бана
async def ban_user(user_to_ban_nick, message):
    async with async_session() as session:
        user_result = await session.execute(select(User).where(User.telegram_nick == user_to_ban_nick))
        user_to_ban = user_result.scalars().first()

        if user_to_ban:
            user_to_ban.level = -1  # Устанавливаем уровень -1 для забаненного
            await session.commit()
            await message.answer(f"Пользователь @{user_to_ban_nick} был забанен.")
        else:
            await message.answer("Пользователь не найден.")

# Обработчик команды /unban
async def cmd_unban(message: types.Message, state: FSMContext):
    telegram_nick = message.from_user.username

    # Проверяем, является ли пользователь администратором
    async with async_session() as session:
        admin_result = await session.execute(select(User).where(User.telegram_nick == telegram_nick))
        admin_user = admin_result.scalars().first()

        if admin_user and admin_user.level == 777:  # Проверяем уровень администратора
            parts = message.text.split()
            if len(parts) < 2:
                # Если никнейм не указан, запрашиваем его
                await message.answer("Пожалуйста, укажите никнейм пользователя, которого хотите разбанить.")
                await state.set_state(UnBanState.waiting_for_unban_name)  # Устанавливаем состояние ожидания никнейма
                return

            user_to_unban_nick = parts[1].lstrip('@')
            await unban_user(user_to_unban_nick, message)
        else:
            await message.answer("❌ У вас недостаточно прав для выполнения этой команды. ❌")

# Обработчик для получения никнейма после запроса
async def process_unban_username(message: types.Message, state: FSMContext):
    user_to_unban_nick = message.text.lstrip('@')
    await unban_user(user_to_unban_nick, message)
    await state.clear()  # Завершаем состояние

# Функция для выполнения разбана
async def unban_user(user_to_unban_nick, message):
    async with async_session() as session:
        user_result = await session.execute(select(User).where(User.telegram_nick == user_to_unban_nick))
        user_to_unban = user_result.scalars().first()

        if user_to_unban:
            user_to_unban.level = 1  # Снимаем бан, устанавливая уровень на 1
            await session.commit()
            await message.answer(f"Пользователь @{user_to_unban_nick} был разбанен.")
        else:
            await message.answer("Пользователь не найден.")

# Обработчик команды /stop
@dp.message(Command("stop"))
async def cmd_stop(message: types.Message):
    telegram_nick = message.from_user.username

    # Проверяем, является ли пользователь администратором
    async with async_session() as session:
        admin_result = await session.execute(select(User).where(User.telegram_nick == telegram_nick))
        admin_user = admin_result.scalars().first()

        if admin_user and admin_user.level == ADMIN_LEVEL:  # Проверяем, что уровень администратора
            await message.answer("Бот остановлен, что-бы его заново запустить пиши Михаилу ))")
            # Остановка бота
            await bot.session.close()  # Закрытие сессии бота
            await dp.storage.close()  # Закрытие хранилища состояний
            await dp.storage.wait_closed()
            await asyncio.get_event_loop().stop()  # Остановка event loop
        else:
            await message.answer("❌ У вас недостаточно прав для выполнения этой команды. ❌")

# Обработчик команды /me
async def cmd_me(message: types.Message):
    telegram_nick = message.from_user.username

    async with async_session() as session:
        # Проверка наличия пользователя в базе данных
        result = await session.execute(select(User).where(User.telegram_nick == telegram_nick))
        user = result.scalars().first()

        if user:
            # Формируем основную информацию о пользователе
            user_info = (
                f"ФИО: {user.full_name or 'Не указано'}\n"
                f"Уровень: {user.level}\n"
                f"Количество посещений: {user.visit_count}\n"
                f"Количество приглашений: {user.invitation_count}\n"
                f"Доступные приглашения: {user.available_invitations or 'Нет'}\n"
                f"Пригласивший: @{user.inviter or 'Нет'}"
            )

            # Проверка, купил ли пользователь билет
            ticket_result = await session.execute(
                select(Ticket)
                .where(Ticket.user_id == telegram_nick)
            )
            ticket = ticket_result.scalars().first()

            if ticket:
                # Получаем информацию о событии
                event_result = await session.execute(
                    select(Event)
                    .where(Event.id == ticket.event_id)
                )
                event = event_result.scalars().first()

                if event:
                    tiket_info = (
                        f"\n\nВы купили билет на событие: {event.event_name}\n"
                        f"Код билета: {ticket.code}\n"
                        f"Дата и время: {event.event_date} {event.event_time}\n"
                        f"Ссылка на строницу события в Qtikets где ты покупал билет: {event.tickets_sale_link}"
                    )
                    await message.answer(tiket_info)
            else:
                tiket_info = "\n\nКак вы купите билет здесь появится информаиця о событии."
                await message.answer(tiket_info)
        
            await message.answer(user_info)
        else:
            await message.answer("Тебя нет в базе данных.")

# Обработчик команды /help
async def cmd_help(message: types.Message):
    help_text = (
        "У вас появился вопрос на который не может ответить бот?\n"
        "Напиши нам на почту потдержки: 0z4r3n13supp0rt@gmail.com \n"
        "Или в телеграмм аккаунт потдержки: @oz4r3n13support"
    )
    await message.answer(help_text)

# Обработчик нажатия на кнопку "Пригласить"
async def handle_invite_button(message: types.Message, state: FSMContext):
    if message.text == "Пригласить":
        await cmd_invite(message, state)  # Передаем state

# Обработчик нажатия на кнопку "Купить билет"
async def handle_buy_button(message: types.Message):
    if message.text == "Купить билет":
        await cmd_buy(message)

# Обработчик нажатия на кнопку "Помощь"
async def handle_help_button(message: types.Message):
    if message.text == "Помощь":
        await cmd_help(message)

# Обработчик нажатия на кнопку "Обо мне"
async def handle_me_button(message: types.Message):
    if message.text == "Обо мне":
        await cmd_me(message)

# Обработчик нажатия на кнопку "Информация об уровнях"
async def handle_level_info_button(message: types.Message):
    if message.text == "Об уровнях":
        await cmd_level(message)


def register_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command(commands=["start"]))
    dp.message.register(cmd_invite, Command(commands=["invite"]))
    dp.message.register(process_invite_nickname, StateFilter(InviteState.waiting_for_invite_nickname))
    dp.message.register(cmd_me, Command(commands=["me"]))
    dp.message.register(cmd_buy, Command(commands=["buy"]))
    dp.message.register(cmd_ban, Command(commands=["ban"]))
    dp.message.register(process_ban_username, StateFilter(BanState.waiting_for_ban_name))
    dp.message.register(cmd_unban, Command(commands=["unban"]))
    dp.message.register(process_unban_username, StateFilter(UnBanState.waiting_for_unban_name))
    dp.message.register(cmd_level, Command(commands=["level"]))
    dp.message.register(cmd_help, Command(commands=["help"]))

    # Регистрация обработчиков кнопок
    dp.message.register(handle_invite_button, F.text == "Пригласить")
    dp.message.register(handle_buy_button, F.text == "Купить билет")
    dp.message.register(handle_help_button, F.text == "Помощь")
    dp.message.register(handle_me_button, F.text == "Обо мне")
    dp.message.register(handle_level_info_button, F.text == "Об уровнях")

async def main():
    register_handlers(dp)
    await bot.delete_webhook()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
