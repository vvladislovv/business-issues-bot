from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.config.config import settings
from src.database.using_data import (
    save_survey_answer,
    finalize_survey,
    get_user_survey,
)
from .questions import QUESTIONS, get_final_message
from src.utils.logging import write_logs
from src.keyboards.inlinebutton import (
    get_final_keyboard,
    new_message,
    get_keyboard,
    get_general_menu,
    get_continue_keyboard,
)
from src.utils.localization import get_message
import os


router = Router()


class SurveyStates(StatesGroup):
    ANSWERING = State()
    MID_SURVEY = State()


async def get_final_survey_message(user_id: int) -> str:
    """Получает финальное сообщение на основе ответов пользователя.

    Args:
        user_id (int): ID пользователя.

    Returns:
        str: Финальное сообщение.
    """
    survey = await get_user_survey(user_id)
    if not survey:
        return await get_final_message(False)

    is_under_25 = survey.is_under_25 == "Да"
    return await get_final_message(is_under_25)


@router.message(SurveyStates.ANSWERING)
async def process_text_answer(message: Message, state: FSMContext):
    """Обрабатывает текстовые ответы на вопросы опроса."""
    try:
        data = await state.get_data()
        current_question_id = data.get("current_question")

        if not current_question_id:
            await state.clear()
            await message.answer(await get_message("error_survey"))
            return

        current_question = QUESTIONS[current_question_id]

        if current_question.options:
            # Повторно отправляем текущий вопрос вместо select_answer
            question_text = await current_question.get_text()
            await message.answer(
                question_text,
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
            if user_results and settings.config.channel_id:
                await message.chat.bot.send_message(
                    settings.config.channel_id, user_results
                )

            final_message = await get_final_survey_message(message.from_user.id)
            await message.answer(final_message, reply_markup=await get_final_keyboard())
            await state.clear()
            return

        next_question = QUESTIONS[current_question.next_question]
        await state.update_data(current_question=current_question.next_question)

        question_text = await next_question.get_text()
        await message.answer(
            question_text, reply_markup=await get_keyboard(next_question.options)
        )

    except Exception as e:
        await write_logs("error", f"Error in process_text_answer: {str(e)}")
        await message.answer(await get_message("error_survey"))


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
            await write_logs("error", "No current question ID found in state")
            await state.clear()
            await callback.message.answer(await get_message("error_survey"))
            return

        current_question = QUESTIONS[current_question_id]

        await save_survey_answer(
            callback.from_user.id, current_question.field_name, callback.data
        )

        await callback.message.edit_reply_markup(reply_markup=None)

        # Check if we're at the mid-point of the survey
        if current_question_id == "work_plan":  # This is the mid-point question
            await state.set_state(SurveyStates.MID_SURVEY)
            await callback.message.answer(
                await get_message("mid_survey", category="survey"),
                reply_markup=await get_continue_keyboard(),
            )
            return

        if current_question.is_last:
            try:
                user_results = await finalize_survey(
                    callback.from_user.id, callback.from_user.username
                )
                if user_results and settings.config.channel_id:
                    await callback.message.chat.bot.send_message(
                        settings.config.channel_id, user_results
                    )

                final_message = await get_final_survey_message(callback.from_user.id)

                # Check if the final image exists
                final_image_path = "./content/final.JPG"
                if not os.path.exists(final_image_path):
                    await write_logs(
                        "error", f"Final image not found at {final_image_path}"
                    )
                    # Send message without image if image is missing
                    await callback.message.answer(
                        "final_message",
                        reply_markup=await get_final_keyboard(),
                    )
                else:
                    # Send message with image
                    await callback.message.answer_photo(
                        photo=FSInputFile(final_image_path),
                        caption=final_message,
                        reply_markup=await get_final_keyboard(),
                    )

                await state.clear()
                await write_logs(
                    "info",
                    f"Survey completed successfully for user {callback.from_user.id}",
                )
            except Exception as e:
                await write_logs("error", f"Error in survey completion: {str(e)}")
                await callback.message.answer(await get_message("error_survey"))
        else:
            next_question = QUESTIONS[current_question.next_question]
            await state.update_data(current_question=current_question.next_question)

            question_text = await next_question.get_text()
            await callback.message.answer(
                question_text, reply_markup=await get_keyboard(next_question.options)
            )

        await callback.answer()

    except Exception as e:
        await write_logs("error", f"Error in process_survey_answer: {str(e)}")
        await callback.message.answer(await get_message("error_survey"))
        await callback.answer()


@router.callback_query(SurveyStates.MID_SURVEY, F.data == "continue_survey")
async def continue_survey(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает продолжение опроса после mid-survey сообщения."""
    try:
        # Устанавливаем состояние обратно в ANSWERING
        await state.set_state(SurveyStates.ANSWERING)

        # Получаем следующий вопрос после work_plan (который вызвал mid-survey)
        # Следующий вопрос после work_plan теперь subsidy_interest
        next_question_id = QUESTIONS["work_plan"].next_question

        if next_question_id not in QUESTIONS:
            await write_logs(
                "error",
                f"Next question ID {next_question_id} not found in QUESTIONS after mid-survey.",
            )
            await callback.message.answer(await get_message("error_survey"))
            await callback.answer()
            return

        next_question = QUESTIONS[next_question_id]

        # Обновляем текущий вопрос в состоянии
        await state.update_data(current_question=next_question_id)

        # Отправляем следующий вопрос
        question_text = await next_question.get_text()
        await callback.message.answer(
            question_text, reply_markup=await get_keyboard(next_question.options)
        )

        await callback.answer()

    except Exception as e:
        await write_logs("error", f"Error in continue_survey: {str(e)}")
        await callback.message.answer(await get_message("error_survey"))
        await callback.answer()


@router.callback_query(F.data.in_(["start_preparation", "contact_expert", "faq"]))
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
            "start_preparation": await get_message("start_preparation"),
            "contact_expert": await get_message("contact_expert"),
            "faq": await get_message("faq"),
        }

        if callback.data in responses:
            await new_message(
                callback.message, responses[callback.data], await get_general_menu()
            )
        else:
            await write_logs(
                "warning",
                f"Unexpected callback data in process_final_choice: {callback.data}",
            )
            await callback.answer()

    except Exception as e:
        await write_logs("error", f"Error in process_final_choice: {str(e)}")
        await callback.message.answer(await get_message("error_survey"))


@router.callback_query(F.data == "get_guide")
async def send_guide(callback: CallbackQuery):
    """Отправляет PDF гайд пользователю."""
    try:
        await write_logs(
            "info",
            f"Attempting to send guide to user {callback.from_user.id} from send_guide handler.",
        )

        # Проверяем существование файла
        file_path = "./content/guide.pdf"
        if not os.path.exists(file_path):
            await write_logs("error", f"Guide file not found at {file_path}")
            await callback.message.answer("Извините, файл гайда временно недоступен.")
            await callback.answer()
            return

        # Отправляем PDF файл
        await callback.message.answer_document(
            document=FSInputFile(file_path),
            caption="📚 Ваш гайд по получению субсидии",
        )
        await write_logs(
            "info", f"Guide successfully sent to user {callback.from_user.id}"
        )
        await callback.answer()

    except Exception as e:
        error_msg = f"Error sending guide to user {callback.from_user.id}: {str(e)}"
        await write_logs("error", error_msg)
        await callback.message.answer(
            "Произошла ошибка при отправке гайда. Пожалуйста, попробуйте позже."
        )
        await callback.answer()
