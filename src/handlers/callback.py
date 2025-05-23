from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from src.keyboards.inlinebutton import (
    update_message,
    new_message,
    get_keyboard,
)
from src.utils.localization import MESSAGES
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
        await get_or_create_user(call.from_user.id, call.from_user.username)

        first_question = QUESTIONS.get("region")
        await update_message(
            call.message,
            MESSAGES["ru"]["start_survey"],
            None,
        )

        await new_message(
            call.message,
            first_question.text,
            await get_keyboard(first_question.options),
        )

        await state.set_state(SurveyStates.ANSWERING)
        await state.update_data(current_question="region")

    except Exception as e:
        await write_logs("error", f"Error in general_main_survey: {str(e)}")
        await new_message(
            call.message,
            "Произошла ошибка при начале опроса. Пожалуйста, попробуйте позже.",
            None,
        )
        await call.answer()

