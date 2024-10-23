from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    # Create a ReplyKeyboardMarkup instance with resize_keyboard set to True
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    # Create buttons explicitly with their text parameter
    invite_button = KeyboardButton(text="/invite")
    buy_button = KeyboardButton(text="/buy")
    help_button = KeyboardButton(text="/help")
    me_button = KeyboardButton(text="/me")

    # Add buttons to the keyboard
    keyboard.add(invite_button, buy_button)
    keyboard.add(help_button, me_button)

    return keyboard
