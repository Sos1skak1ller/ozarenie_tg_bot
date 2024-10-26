from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    invite_button = KeyboardButton(text='Пригласить')
    buy_button = KeyboardButton(text='Купить билет')
    help_button = KeyboardButton(text='Помощь')
    me_button = KeyboardButton(text='Обо мне')
    info_button = KeyboardButton(text='Об уровнях')
    
    # Создаем клавиатуру с кнопками, используя параметр keyboard
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [invite_button, info_button],
            [help_button, me_button], 
            [buy_button]
        ],
        resize_keyboard=True
    )
    
    return keyboard

