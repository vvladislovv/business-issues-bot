from aiogram import Router, types
from aiogram.filters import CommandStart
from src.keyboards.inlinebutton import new_message
from src.utils.localization import get_message
from src.keyboards.inlinebutton import get_general_menu
from src.database.using_data import add_user_if_not_exists
from aiogram.types import FSInputFile

router = Router(name=__name__)


@router.message(CommandStart())
async def command_start(message: types.Message) -> None:
    """
    Обрабатывает команду старта и отправляет приветственное сообщение пользователю.

    Args:
        message (types.Message): Сообщение, полученное от пользователя, содержащие информацию о пользователе.

    Returns:
        None: Функция ничего не возвращает, но отправляет сообщение пользователю и добавляет его в базу данных, если он новый.
    """
    # Отправляем фото с приветственным сообщением
    await message.answer_photo(
        photo=FSInputFile("/app/content/welcome.JPG"),
        caption=await get_message("start"),
        reply_markup=await get_general_menu(),
    )

    user_data = {
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "first_name": message.from_user.first_name,
        "last_name": message.from_user.last_name,
    }

    await add_user_if_not_exists(user_data)
