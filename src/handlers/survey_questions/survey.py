from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.config.config import settings
from src.database.using_data import (
    save_survey_answer,
    finalize_survey,
)
from .questions import QUESTIONS, FINAL_MESSAGE
from src.utils.logging import write_logs
from src.keyboards.inlinebutton import (
    get_final_keyboard,
    new_message,
    get_keyboard,
    get_general_menu,
)
from src.utils.localization import MESSAGES


router = Router()


class SurveyStates(StatesGroup):
    ANSWERING = State()


# ! это для текстового ответа
@router.message(SurveyStates.ANSWERING)
async def process_text_answer(message: Message, state: FSMContext):
    """
    Обрабатывает текстовые ответы на вопросы опроса.

    Args:
        message (Message): Сообщение, содержащее текстовый ответ от пользователя.
        state (FSMContext): Контекст состояния для управления состоянием опроса.

    Returns:
        None: Функция ничего не возвращает, но обновляет состояние и отправляет сообщения.
    """
    try:
        data = await state.get_data()
        current_question_id = data.get("current_question")

        if not current_question_id:
            await state.clear()
            await message.answer(MESSAGES["ru"]["error_survey"])
            return

        current_question = QUESTIONS[current_question_id]

        if current_question.options:
            await message.answer(
                "Пожалуйста, выберите один из предложенных вариантов ответа:",
                reply_markup=await get_keyboard(current_question.options),
            )
            return

        await save_survey_answer(
            message.from_user.id, current_question.field_name, message.text
        )

        if current_question.is_last:
            user_results = await finalize_survey(
                message.from_user.id, message.from_user.username
            )
            print(user_results)
            if user_results and settings.config.channel_id:
                await message.chat.bot.send_message(
                    settings.config.channel_id, user_results
                )

            await message.answer(FINAL_MESSAGE, reply_markup=await get_final_keyboard())
            await state.clear()
            return

        next_question = QUESTIONS[current_question.next_question]
        await state.update_data(current_question=current_question.next_question)

        await message.answer(
            next_question.text, reply_markup=await get_keyboard(next_question.options)
        )

    except Exception as e:
        await write_logs("error", f"Error in process_text_answer: {str(e)}")
        await message.answer(MESSAGES["ru"]["error_survey"])


# ! это для ответов на вопросы
@router.callback_query(SurveyStates.ANSWERING)
async def process_survey_answer(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает ответы на вопросы опроса, полученные через кнопки.

    Args:
        callback (CallbackQuery): Объект CallbackQuery, содержащий информацию о нажатой кнопке и пользователе.
        state (FSMContext): Контекст состояния для управления состоянием опроса.

    Returns:
        None: Функция ничего не возвращает, но обновляет состояние и отправляет сообщения.
    """
    try:
        data = await state.get_data()
        current_question_id = data.get("current_question")

        if not current_question_id:
            await state.clear()
            await callback.message.answer(MESSAGES["ru"]["error_survey"])
            return

        current_question = QUESTIONS[current_question_id]

        await save_survey_answer(
            callback.from_user.id, current_question.field_name, callback.data
        )

        await callback.message.edit_reply_markup(reply_markup=None)

        if current_question.is_last:
            user_results = await finalize_survey(
                callback.from_user.id, callback.from_user.username
            )
            print(user_results)
            if user_results and settings.config.channel_id:
                await callback.message.chat.bot.send_message(
                    settings.config.channel_id, user_results
                )

            await callback.message.answer(
                FINAL_MESSAGE, reply_markup=await get_final_keyboard()
            )
            await state.clear()
        else:
            next_question = QUESTIONS[current_question.next_question]
            await state.update_data(current_question=current_question.next_question)

            await callback.message.answer(
                next_question.text,
                reply_markup=await get_keyboard(next_question.options),
            )

        await callback.answer()

    except Exception as e:
        await write_logs("error", f"Error in process_survey_answer: {str(e)}")
        await callback.message.answer(MESSAGES["ru"]["error_survey"])
        await callback.answer()


@router.callback_query(
    F.data.in_(["start_preparation", "get_guide", "contact_expert", "faq"])
)
async def process_final_choice(callback: CallbackQuery):
    """
    Обрабатывает выбор финальных действий после завершения опроса.

    Args:
        callback (CallbackQuery): Объект CallbackQuery, содержащий информацию о нажатой кнопке и пользователе.

    Returns:
        None: Функция ничего не возвращает, но обновляет сообщение и отправляет финальные действия.
    """
    try:
        responses = {
            "start_preparation": MESSAGES["ru"]["start_preparation"],
            "get_guide": MESSAGES["ru"]["get_guide"],
            "contact_expert": MESSAGES["ru"]["contact_expert"],
            "faq": MESSAGES["ru"]["faq"],
        }

        await new_message(
            callback.message,
            responses[callback.data],
            await get_general_menu()
        )
        await callback.answer()

    except Exception as e:
        await write_logs("error", f"Error in process_final_choice: {str(e)}")
        await callback.message.answer(MESSAGES["ru"]["error_survey"])
        await callback.answer()
