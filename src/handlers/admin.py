from src.config.config import settings
from aiogram import Router, types, F
from aiogram.filters import Command
from src.utils.logging import write_logs
from src.keyboards.inlinebutton import (
    new_message,
    get_admin_keyboard,
)
from src.utils.localization import get_message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import os
from aiogram.types import (
    FSInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    MessageEntity,
)
from src.utils.statistics import (
    get_time_based_statistics,
    generate_time_statistics_excel,
)
from src.utils.user_statistics import (
    get_user_statistics,
    generate_user_statistics_excel,
)
from src.database.using_data import get_all_users

router = Router(name=__name__)


class AdminStates(StatesGroup):
    WAITING_PASSWORD = State()
    WAITING_MAILING_TEXT = State()
    WAITING_MAILING_MEDIA = State()
    WAITING_MAILING_BUTTONS = State()
    WAITING_BUTTON_TEXT = State()
    WAITING_BUTTON_URL = State()


@router.message(Command("admin"))
async def handle_admin_command(message: types.Message, state: FSMContext):
    """
    Обрабатывает команду администратора.
    
    Args:
        message (types.Message): Сообщение, содержащее команду от пользователя.
        state (FSMContext): Контекст состояния для управления состоянием.
    """
    user_id = message.from_user.id
    await write_logs("info", f"Admin command received from user {user_id}")

    if user_id not in settings.config.admins.admins:
        await write_logs("warning", f"Unauthorized access attempt by {user_id}")
        # await new_message(message, MESSAGES["ru"]["access_denied"], None)
        return

    await state.set_state(AdminStates.WAITING_PASSWORD)
    await new_message(message,  await get_message("enter_password"), None)


@router.message(AdminStates.WAITING_PASSWORD)
async def handle_password_input(message: types.Message, state: FSMContext):
    """
    Обрабатывает ввод пароля от администратора.
    
    Args:
        message (types.Message): Сообщение, содержащее введенный пароль.
        state (FSMContext): Контекст состояния для управления состоянием.
    """
    user_id = message.from_user.id
    input_password = message.text

    if input_password == settings.config.ADMIN_PASSWORD:
        await write_logs("info", f"Admin access granted for {user_id}")
        await new_message(
            message, await get_message("admin_msg"), await get_admin_keyboard()
        )
        await state.clear()
    else:
        await write_logs("warning", f"Wrong password attempt by {user_id}")
        await new_message(message, await get_message("wrong_password"), None)


@router.callback_query(lambda c: c.data == "admin_activity_stats")
async def process_activity_stats_button(callback_query: types.CallbackQuery):
    """
    Обрабатывает нажатие кнопки статистики активности.
    
    Args:
        callback_query (types.CallbackQuery): Запрос обратного вызова от пользователя.
    """
    user_id = callback_query.from_user.id

    try:
        if user_id not in settings.config.admins.admins:
            await write_logs(
                "warning", f"Unauthorized stats access attempt by {user_id}"
            )
            await callback_query.answer("У вас нет прав администратора")
            return

        await write_logs("info", f"Activity stats request from admin {user_id}")
        await callback_query.answer("⏳ Подготовка статистики активности...")

        # Получаем статистику
        stats = await get_time_based_statistics()

        if stats:
            stats_text = (
                "📊 Статистика активности бота:\n\n"
                f"За последние 24 часа:\n"
                f"👤 Новых пользователей: {stats['daily']['users']}\n"
                f"📝 Пройдено опросов: {stats['daily']['surveys']}\n\n"
                f"За последнюю неделю:\n"
                f"👤 Новых пользователей: {stats['weekly']['users']}\n"
                f"📝 Пройдено опросов: {stats['weekly']['surveys']}\n\n"
                f"За последний месяц:\n"
                f"👤 Новых пользователей: {stats['monthly']['users']}\n"
                f"📝 Пройдено опросов: {stats['monthly']['surveys']}\n\n"
                f"Всего:\n"
                f"👤 Пользователей: {stats['total']['users']}\n"
                f"📝 Пройдено опросов: {stats['total']['surveys']}"
            )

            try:
                # Генерируем Excel отчет
                excel_path = await generate_time_statistics_excel()
                if excel_path:
                    # Отправляем статистику
                    await callback_query.message.edit_text(
                        stats_text, reply_markup=await get_admin_keyboard()
                    )

                    try:
                        # Отправляем Excel файл
                        doc = FSInputFile(excel_path)
                        await callback_query.message.answer_document(
                            doc, caption="📊 Статистика активности бота"
                        )
                        await write_logs(
                            "info",
                            f"Activity statistics Excel report sent to admin {user_id}",
                        )
                    except Exception as e:
                        await write_logs("error", f"Error sending Excel file: {str(e)}")
                        await callback_query.message.answer(
                            "❌ Ошибка при отправке Excel файла"
                        )
                    finally:
                        # Удаляем временный файл
                        try:
                            if os.path.exists(excel_path):
                                os.remove(excel_path)
                                await write_logs(
                                    "info",
                                    f"Temporary Excel file removed: {excel_path}",
                                )
                        except Exception as e:
                            await write_logs(
                                "error",
                                f"Error removing temporary Excel file: {str(e)}",
                            )
                else:
                    await callback_query.message.edit_text(
                        stats_text + "\n\n⚠️ Ошибка при создании Excel отчета",
                        reply_markup=await get_admin_keyboard(),
                    )
            except Exception as e:
                await write_logs("error", f"Error in Excel report generation: {str(e)}")
                await callback_query.message.edit_text(
                    stats_text + "\n\n❌ Ошибка при создании Excel отчета",
                    reply_markup=await get_admin_keyboard(),
                )
        else:
            await write_logs("warning", "No activity statistics data available")
            await callback_query.message.edit_text(
                "📊 Статистика активности\n\n"
                "На данный момент статистика недоступна.\n"
                "Возможные причины:\n"
                "- Бот только запущен\n"
                "- Нет зарегистрированных пользователей\n"
                "- Ошибка доступа к базе данных",
                reply_markup=await get_admin_keyboard(),
            )

    except Exception as e:
        await write_logs(
            "error", f"Critical error in activity stats processing: {str(e)}"
        )
        await callback_query.message.edit_text(
            "❌ Произошла критическая ошибка при обработке статистики",
            reply_markup=await get_admin_keyboard(),
        )


@router.callback_query(lambda c: c.data == "admin_user_stats")
async def process_user_stats_button(callback_query: types.CallbackQuery):
    """
    Обрабатывает нажатие кнопки статистики пользователей.
    
    Args:
        callback_query (types.CallbackQuery): Запрос обратного вызова от пользователя.
    """
    user_id = callback_query.from_user.id

    try:
        if user_id not in settings.config.admins.admins:
            await write_logs(
                "warning", f"Unauthorized user stats access attempt by {user_id}"
            )
            await callback_query.answer("У вас нет прав администратора")
            return

        await write_logs("info", f"User stats request from admin {user_id}")
        await callback_query.answer("⏳ Подготовка статистики пользователей...")

        # Генерируем Excel отчет
        excel_path = await generate_user_statistics_excel()
        if excel_path:
            try:
                # Отправляем Excel файл
                doc = FSInputFile(excel_path)
                await callback_query.message.answer_document(
                    doc, caption="👥 Статистика пользователей бота"
                )
                await write_logs(
                    "info",
                    f"User statistics Excel report sent to admin {user_id}",
                )

                # Удаляем временный файл
                try:
                    if os.path.exists(excel_path):
                        os.remove(excel_path)
                        await write_logs(
                            "info",
                            f"Temporary Excel file removed: {excel_path}",
                        )
                except Exception as e:
                    await write_logs(
                        "error",
                        f"Error removing temporary Excel file: {str(e)}",
                    )
            except Exception as e:
                await write_logs("error", f"Error sending Excel file: {str(e)}")
                await callback_query.message.answer(
                    "❌ Ошибка при отправке Excel файла"
                )
        else:
            await write_logs("warning", "No user statistics data available")
            await callback_query.message.edit_text(
                "👥 Статистика пользователей\n\n"
                "На данный момент статистика недоступна.\n"
                "Возможные причины:\n"
                "- Бот только запущен\n"
                "- Нет зарегистрированных пользователей\n"
                "- Ошибка доступа к базе данных",
                reply_markup=await get_admin_keyboard(),
            )

    except Exception as e:
        await write_logs("error", f"Critical error in user stats processing: {str(e)}")
        await callback_query.message.edit_text(
            "❌ Произошла критическая ошибка при обработке статистики",
            reply_markup=await get_admin_keyboard(),
        )


@router.callback_query(lambda c: c.data == "admin_mailing")
async def process_mailing_button(
    callback_query: types.CallbackQuery, state: FSMContext
):
    """
    Обрабатывает нажатие кнопки рассылки.
    
    Args:
        callback_query (types.CallbackQuery): Запрос обратного вызова от пользователя.
        state (FSMContext): Контекст состояния для управления состоянием.
    """
    user_id = callback_query.from_user.id

    if user_id not in settings.config.admins.admins:
        await write_logs("warning", f"Unauthorized mailing attempt by {user_id}")
        await callback_query.answer("У вас нет прав администратора")
        return

    await write_logs("info", f"Mailing request from admin {user_id}")

    # Check if already in mailing state to prevent multiple triggers
    current_state = await state.get_state()
    if current_state == AdminStates.WAITING_MAILING_MEDIA.state:
        await callback_query.answer("❌ Вы уже находитесь в процессе рассылки.")
        return

    await state.set_state(AdminStates.WAITING_MAILING_MEDIA)
    await callback_query.message.edit_text(
        "📨 Отправьте сообщение для рассылки.\n"
        "Это может быть:\n"
        "- Текст\n"
        "- Фото\n"
        "- Видео\n"
        "- Голосовое сообщение",
        reply_markup=await get_admin_keyboard(),
    )
    await callback_query.answer()


@router.message(AdminStates.WAITING_MAILING_MEDIA)
async def handle_mailing_content(message: types.Message, state: FSMContext):
    """
    Обрабатывает контент для рассылки.
    
    Args:
        message (types.Message): Сообщение, содержащее контент для рассылки.
        state (FSMContext): Контекст состояния для управления состоянием.
    """
    try:
        # Сохраняем информацию о сообщении
        mailing_data = {}

        if message.text:
            mailing_data["type"] = "text"
            mailing_data["content"] = message.text
            # Сохраняем entities как список словарей
            if message.entities:
                mailing_data["entities"] = [
                    {
                        "type": entity.type,
                        "offset": entity.offset,
                        "length": entity.length,
                        "url": entity.url,
                        "user": entity.user,
                        "language": entity.language,
                        "custom_emoji_id": entity.custom_emoji_id,
                    }
                    for entity in message.entities
                ]
        elif message.photo:
            mailing_data["type"] = "photo"
            mailing_data["content"] = message.photo[-1].file_id
            mailing_data["caption"] = message.caption
            if message.caption_entities:
                mailing_data["caption_entities"] = [
                    {
                        "type": entity.type,
                        "offset": entity.offset,
                        "length": entity.length,
                        "url": entity.url,
                        "user": entity.user,
                        "language": entity.language,
                        "custom_emoji_id": entity.custom_emoji_id,
                    }
                    for entity in message.caption_entities
                ]
        elif message.video:
            mailing_data["type"] = "video"
            mailing_data["content"] = message.video.file_id
            mailing_data["caption"] = message.caption
            if message.caption_entities:
                mailing_data["caption_entities"] = [
                    {
                        "type": entity.type,
                        "offset": entity.offset,
                        "length": entity.length,
                        "url": entity.url,
                        "user": entity.user,
                        "language": entity.language,
                        "custom_emoji_id": entity.custom_emoji_id,
                    }
                    for entity in message.caption_entities
                ]
        elif message.voice:
            mailing_data["type"] = "voice"
            mailing_data["content"] = message.voice.file_id
            mailing_data["caption"] = message.caption
            if message.caption_entities:
                mailing_data["caption_entities"] = [
                    {
                        "type": entity.type,
                        "offset": entity.offset,
                        "length": entity.length,
                        "url": entity.url,
                        "user": entity.user,
                        "language": entity.language,
                        "custom_emoji_id": entity.custom_emoji_id,
                    }
                    for entity in message.caption_entities
                ]
        else:
            await message.answer(
                "❌ Неподдерживаемый тип сообщения. Пожалуйста, отправьте текст, фото, видео или голосовое сообщение."
            )
            return

        # Сохраняем данные в состояние
        await state.update_data(mailing=mailing_data)

        # Спрашиваем про кнопки
        await state.set_state(AdminStates.WAITING_MAILING_BUTTONS)
        await message.answer(
            "Хотите добавить кнопки к сообщению?",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ Да", callback_data="add_buttons"),
                        InlineKeyboardButton(text="❌ Нет", callback_data="no_buttons"),
                    ]
                ]
            ),
        )

    except Exception as e:
        await write_logs("error", f"Error processing mailing content: {str(e)}")
        await message.answer("❌ Произошла ошибка при обработке сообщения")
        await state.clear()


@router.callback_query(lambda c: c.data == "add_buttons")
async def process_add_buttons(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обрабатывает добавление кнопок.
    
    Args:
        callback_query (types.CallbackQuery): Запрос обратного вызова от пользователя.
        state (FSMContext): Контекст состояния для управления состоянием.
    """
    await state.set_state(AdminStates.WAITING_BUTTON_TEXT)
    await callback_query.message.edit_text(
        "Введите текст для кнопки:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_buttons")]
            ]
        ),
    )


@router.callback_query(lambda c: c.data == "no_buttons")
async def process_no_buttons(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обрабатывает отказ от добавления кнопок.
    
    Args:
        callback_query (types.CallbackQuery): Запрос обратного вызова от пользователя.
        state (FSMContext): Контекст состояния для управления состоянием.
    """
    await send_mailing(callback_query.message, state)


@router.callback_query(lambda c: c.data == "cancel_buttons")
async def process_cancel_buttons(
    callback_query: types.CallbackQuery, state: FSMContext
):
    """
    Обрабатывает отмену добавления кнопок.
    
    Args:
        callback_query (types.CallbackQuery): Запрос обратного вызова от пользователя.
        state (FSMContext): Контекст состояния для управления состоянием.
    """
    await send_mailing(callback_query.message, state)


@router.message(AdminStates.WAITING_BUTTON_TEXT)
async def handle_button_text(message: types.Message, state: FSMContext):
    """
    Обрабатывает текст кнопки.
    
    Args:
        message (types.Message): Сообщение, содержащее текст кнопки.
        state (FSMContext): Контекст состояния для управления состоянием.
    """
    await state.update_data(button_text=message.text)
    await state.set_state(AdminStates.WAITING_BUTTON_URL)
    await message.answer("Теперь введите ссылку для кнопки:")


@router.message(AdminStates.WAITING_BUTTON_URL)
async def handle_button_url(message: types.Message, state: FSMContext):
    """
    Обрабатывает URL кнопки.
    
    Args:
        message (types.Message): Сообщение, содержащее URL кнопки.
        state (FSMContext): Контекст состояния для управления состоянием.
    """
    if not message.text.startswith(("http://", "https://")):
        await message.answer(
            "❌ Некорректная ссылка. Ссылка должна начинаться с http:// или https://"
        )
        return

    state_data = await state.get_data()
    mailing_data = state_data["mailing"]
    button_text = state_data["button_text"]

    # Добавляем информацию о кнопке
    mailing_data["button"] = {"text": button_text, "url": message.text}

    await state.update_data(mailing=mailing_data)
    await send_mailing(message, state)


async def send_mailing(message: types.Message, state: FSMContext):
    """
    Отправляет рассылку всем пользователям.
    
    Args:
        message (types.Message): Сообщение, содержащее контент для рассылки.
        state (FSMContext): Контекст состояния для управления состоянием.
    """
    try:
        state_data = await state.get_data()
        mailing_data = state_data["mailing"]

        # Получаем всех пользователей
        users = await get_all_users()

        # Создаем клавиатуру, если есть кнопка
        keyboard = None
        if "button" in mailing_data:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=mailing_data["button"]["text"],
                            url=mailing_data["button"]["url"],
                        )
                    ]
                ]
            )

        # Счетчики для статистики
        successful = 0
        failed = 0

        # Преобразуем entities в объекты MessageEntity
        entities = None
        caption_entities = None

        if "entities" in mailing_data:
            entities = [
                MessageEntity(
                    type=e["type"],
                    offset=e["offset"],
                    length=e["length"],
                    url=e.get("url"),
                    user=e.get("user"),
                    language=e.get("language"),
                    custom_emoji_id=e.get("custom_emoji_id"),
                )
                for e in mailing_data["entities"]
            ]

        if "caption_entities" in mailing_data:
            caption_entities = [
                MessageEntity(
                    type=e["type"],
                    offset=e["offset"],
                    length=e["length"],
                    url=e.get("url"),
                    user=e.get("user"),
                    language=e.get("language"),
                    custom_emoji_id=e.get("custom_emoji_id"),
                )
                for e in mailing_data["caption_entities"]
            ]

        # Отправляем сообщения
        for user in users:
            try:
                if mailing_data["type"] == "text":
                    await message.bot.send_message(
                        user.user_id,
                        mailing_data["content"],
                        entities=entities,
                        reply_markup=keyboard,
                    )
                elif mailing_data["type"] == "photo":
                    await message.bot.send_photo(
                        user.user_id,
                        mailing_data["content"],
                        caption=mailing_data.get("caption"),
                        caption_entities=caption_entities,
                        reply_markup=keyboard,
                    )
                elif mailing_data["type"] == "video":
                    await message.bot.send_video(
                        user.user_id,
                        mailing_data["content"],
                        caption=mailing_data.get("caption"),
                        caption_entities=caption_entities,
                        reply_markup=keyboard,
                    )
                elif mailing_data["type"] == "voice":
                    await message.bot.send_voice(
                        user.user_id,
                        mailing_data["content"],
                        caption=mailing_data.get("caption"),
                        caption_entities=caption_entities,
                        reply_markup=keyboard,
                    )
                successful += 1
            except Exception as e:
                await write_logs(
                    "error", f"Error sending mailing to user {user.user_id}: {str(e)}"
                )
                failed += 1

        # Отправляем статистику
        await message.answer(
            f"📊 Рассылка завершена\n\n"
            f"✅ Успешно отправлено: {successful}\n"
            f"❌ Ошибок отправки: {failed}",
            reply_markup=await get_admin_keyboard(),
        )

    except Exception as e:
        await write_logs("error", f"Error in mailing: {str(e)}")
        await message.answer("❌ Произошла ошибка при рассылке")
    finally:
        await state.clear()