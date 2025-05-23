from src.config.config import settings
from aiogram import Router, types
from aiogram.filters import Command
from src.utils.logging import write_logs
from src.keyboards.inlinebutton import new_message, get_admin_keyboard
from src.utils.localization import MESSAGES
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

router = Router(name=__name__)


class AdminStates(StatesGroup):
    WAITING_PASSWORD = State()

@router.message(Command("admin"))
async def handle_admin_command(message: types.Message, state: FSMContext):
    """
    Обрабатывает команду администратора.

    Args:
        message (types.Message): Сообщение, содержащее команду от пользователя.
        state (FSMContext): Контекст состояния для управления состоянием.

    Returns:
        None: Функция ничего не возвращает, но обновляет состояние и отправляет сообщение.
    """
    user_id = message.from_user.id
    
    if user_id not in settings.config.admins.admins:
        await write_logs("warning", f"Unauthorized access attempt by {user_id}")
        await new_message(message, MESSAGES['ru']['access_denied'], None)
        return
    
    await state.set_state(AdminStates.WAITING_PASSWORD)
    await new_message(message, MESSAGES['ru']['enter_password'], None)

@router.message(AdminStates.WAITING_PASSWORD)
async def handle_password_input(message: types.Message, state: FSMContext):
    """
    Обрабатывает ввод пароля от администратора.

    Args:
        message (types.Message): Сообщение, содержащее введенный пароль.
        state (FSMContext): Контекст состояния для управления состоянием.

    Returns:
        None: Функция ничего не возвращает, но обновляет состояние и отправляет сообщение.
    """
    user_id = message.from_user.id
    input_password = message.text
    
    if input_password == settings.config.ADMIN_PASSWORD:
        await write_logs("info", f"Admin access granted for {user_id}")
        await new_message(
            message,
            MESSAGES['ru']['admin_msg'],
            await get_admin_keyboard()
        )
        await state.clear()
    else:
        await write_logs("warning", f"Wrong password attempt by {user_id}")
        await new_message(message, MESSAGES['ru']['wrong_password'], None)


@router.callback_query(lambda c: c.data == "admin_stats")
async def process_stats_button(callback_query: types.CallbackQuery):
    """
    Обрабатывает нажатие кнопки статистики.

    Args:
        callback_query (types.CallbackQuery): Объект CallbackQuery, содержащий информацию о нажатой кнопке и пользователе.

    Returns:
        None: Функция ничего не возвращает, но обновляет сообщение с статистикой.
    """
    user_id = callback_query.from_user.id
    if user_id in settings.config.admins.admins:
        # Здесь добавьте вашу логику для показа статистики
        await callback_query.message.edit_text(
            "📊 Статистика:\n" +
            "Здесь будет ваша статистика",
            reply_markup=await get_admin_keyboard()
        )
    await callback_query.answer()