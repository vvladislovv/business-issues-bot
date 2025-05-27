from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from src.keyboards.inlinebutton import (
    update_message,
    new_message,
    get_keyboard,
)
from src.utils.localization import get_message
from src.database.using_data import get_or_create_user
from src.handlers.survey_questions.questions import QUESTIONS
from src.handlers.survey_questions.survey import SurveyStates
from src.utils.logging import write_logs

router = Router(name=__name__)


@router.callback_query(F.data == "Survey")
async def general_main_survey(call: CallbackQuery, state: FSMContext) -> None:
    """
    Обрабатывает запрос на начало опроса.

    Args:
        call (CallbackQuery): Объект CallbackQuery, содержащий информацию о нажатой кнопке и пользователе.
        state (FSMContext): Контекст состояния для управления состоянием опроса.

    Returns:
        None: Функция ничего не возвращает, но обновляет сообщение и управляет состоянием опроса.
    """
    try:
        # Получаем первый вопрос
        first_question = QUESTIONS.get("has_business")
        if not first_question:
            raise ValueError("First question not found")

        # Устанавливаем состояние опроса
        await state.set_state(SurveyStates.ANSWERING)
        await state.update_data(current_question="has_business")

        # Получаем текст вопроса
        question_text = await first_question.get_text()

        # Обновляем сообщение с началом опроса
        await update_message(
            call.message,
            await get_message("start_survey"),
            None,
        )

        # Отправляем первый вопрос
        await new_message(
            call.message,
            question_text,
            await get_keyboard(first_question.options),
        )

        await call.answer()

    except Exception as e:
        await write_logs("error", f"Error in general_main_survey: {str(e)}")
        await new_message(
            call.message,
            "Произошла ошибка при начале опроса. Пожалуйста, попробуйте позже.",
            None,
        )
        await call.answer()
