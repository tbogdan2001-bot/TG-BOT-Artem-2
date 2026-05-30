# keyboards.py
# Клавиатуры клубной воронки (club3-сценарий).

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

import config


def get_subscribe_keyboard(channel_link: str | None = None) -> InlineKeyboardMarkup:
    """Кнопка-ссылка на канал (показывается на /start, когда нужна заявка)."""
    link = channel_link or config.CHANNEL_LINK
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=config.SUBSCRIBE_BUTTON_TEXT, url=link)]
        ]
    )


def get_not_robot_keyboard() -> ReplyKeyboardMarkup:
    """Reply-кнопка «Я не робот» под стартовым фото."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=config.NOT_ROBOT_BUTTON_TEXT)]],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder=config.NOT_ROBOT_BUTTON_TEXT,
    )


def get_step3_keyboard() -> InlineKeyboardMarkup:
    """Кнопки шага 3: «ГОЛОС КЛУБА» (ссылка) + «СМОТРЕТЬ ОТЗЫВЫ» (callback)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=config.VOICE_BUTTON_TEXT, url=config.CLUB_MANAGER_URL)],
            [InlineKeyboardButton(text=config.REVIEWS_BUTTON_TEXT, callback_data="club3:reviews")],
        ]
    )


def get_manager_keyboard() -> InlineKeyboardMarkup:
    """Запасная кнопка «Написать менеджеру»."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=config.VOICE_BUTTON_TEXT, url=config.CLUB_MANAGER_URL)]
        ]
    )
