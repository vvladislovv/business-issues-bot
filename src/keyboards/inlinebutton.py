from aiogram.utils.keyboard import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
)
from src.utils.logging import write_logs
from aiogram.types import InlineKeyboardButton as TypesInlineKeyboardButton
from aiogram.types import Message


async def get_general_menu() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру общего меню с кнопками для прохождения опроса и доступа к FAQ.

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками.
    """
    keyboard = [
        [
            TypesInlineKeyboardButton(text="📝 Пройти опрос", callback_data="Survey"),
            TypesInlineKeyboardButton(
                text="❓ FAQ", url="https://telegra.ph/test-bot-05-23-2"
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def get_mailing_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для рассылки."""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text="✅ Подтвердить рассылку", callback_data="confirm_mailing"),
        InlineKeyboardButton(text="❌ Отменить рассылку", callback_data="cancel_mailing"),
    )
    return keyboard

async def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для администратора.

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками администратора.
    """
    keyboard = [
        [
            TypesInlineKeyboardButton(
                text="📊 Статистика активности", callback_data="admin_activity_stats"
            )
        ],
        [
            TypesInlineKeyboardButton(
                text="👥 Статистика пользователей", callback_data="admin_user_stats"
            )
        ],
        [TypesInlineKeyboardButton(text="📨 Рассылка", callback_data="admin_mailing")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def get_keyboard(options: list[str] | None = None) -> InlineKeyboardMarkup | None:
    """
    Создает клавиатуру с кнопками на основе предоставленных вариантов ответов.

    Args:
        options (list[str] | None): Список вариантов ответов. Если None, возвращает None.

    Returns:
        InlineKeyboardMarkup | None: Клавиатура с кнопками или None, если вариантов нет.
    """
    if not options:
        return None  # Возвращаем None для вопросов без вариантов ответа

    buttons = [
        [InlineKeyboardButton(text=option, callback_data=option)] for option in options
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_final_keyboard() -> InlineKeyboardMarkup:
    """
    Создает финальную клавиатуру с кнопками для завершения опроса.

    Returns:
        InlineKeyboardMarkup: Клавиатура с финальными кнопками.
    """
    buttons = [
        [
            InlineKeyboardButton(
                text="1️⃣ Начать подготовку заявки", callback_data="start_preparation"
            )
        ],
        [InlineKeyboardButton(text="2️⃣ Забрать гайд", callback_data="get_guide")],
        [
            InlineKeyboardButton(
                text="3️⃣ Связаться с экспертом", callback_data="contact_expert"
            )
        ],
        [InlineKeyboardButton(text="4️⃣ FAQ", url="https://telegra.ph/test-bot-05-23-2")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def new_message(
    message: Message,
    text: str,
    keyboard: ReplyKeyboardMarkup | InlineKeyboardMarkup | None = None,
) -> Message:
    """
    Отправляет новое сообщение с текстом и клавиатурой.

    Args:
        message (Message): Сообщение, к которому будет отправлено новое сообщение.
        text (str): Текст нового сообщения.
        keyboard (ReplyKeyboardMarkup | InlineKeyboardMarkup | None): Клавиатура для нового сообщения.

    Returns:
        Message: Отправленное сообщение.
    """
    try:
        markup = None
        if keyboard:
            if isinstance(keyboard, (InlineKeyboardMarkup, ReplyKeyboardMarkup)):
                markup = keyboard
            elif isinstance(keyboard, list):
                markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            else:
                markup = keyboard.as_markup()

        return await message.answer(
            text=text, reply_markup=markup, parse_mode="Markdown"
        )

    except Exception as e:
        await write_logs("error", f"Error in new_message: {e}")


async def update_message(
    message: Message,
    text: str,
    keyboard: ReplyKeyboardMarkup | InlineKeyboardMarkup | None = None,
) -> None:
    """
    Обновляет существующее сообщение, удаляя предыдущую клавиатуру и добавляя новую.

    Args:
        message (Message): Сообщение, которое будет обновлено.
        text (str): Новый текст сообщения.
        keyboard (ReplyKeyboardMarkup | InlineKeyboardMarkup | None): Новая клавиатура для сообщения.
    """
    try:
        # Сначала удаляем клавиатуру у предыдущего сообщения
        try:
            await message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass  # Игнорируем ошибки при удалении клавиатуры

        # Отправляем новое сообщение с новой клавиатурой
        await message.answer(text=text, reply_markup=keyboard, parse_mode="Markdown")
    except Exception as error:
        await write_logs("error", f"Error in update_message: {error}")
