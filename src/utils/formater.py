from src.database.settings_data import UserSurvey
from src.utils.localization import get_message
import re
from aiogram import types


async def format_user_survey_results(
    user_id: int, username: str, survey: UserSurvey
) -> str:
    """
    Форматирует результаты опроса конкретного пользователя.

    Args:
        user_id (int): Идентификатор пользователя, который прошел опрос.
        username (str): Имя пользователя в формате @username.
        survey (UserSurvey): Объект, содержащий результаты опроса пользователя.

    Returns:
        str: Строка, содержащая отформатированные результаты опроса.
    """
    header = await get_message("survey_result_header", category="survey")
    user_info = await get_message("survey_result_user_info", category="survey")
    answers_header = await get_message(
        "survey_result_answers_header", category="survey"
    )

    message = f"{header}\n"
    message += user_info.format(username=username, user_id=user_id) + "\n\n"
    message += f"{answers_header}\n\n"

    # Создаем словарь с вопросами и ответами
    answers = {
        "region": ("question_region", survey.region),
        "has_business": ("question_has_business", survey.has_business),
        "is_under_25": ("question_is_under_25", survey.is_under_25),
        "has_experience": ("question_has_experience", survey.has_experience),
        "official_income": ("question_official_income", survey.official_income),
        "work_plan": ("question_work_plan", survey.work_plan),
        "micro_result": ("question_micro_result", survey.micro_result),
        "subsidy_interest": ("question_subsidy_interest", survey.subsidy_interest),
        "desired_outcome": ("question_desired_outcome", survey.desired_outcome),
        "importance_level": ("question_importance_level", survey.importance_level),
        "investment_readiness": (
            "question_investment_readiness",
            survey.investment_readiness,
        ),
    }

    for question_key, (question_msg_key, answer) in answers.items():
        if answer:
            question_text = await get_message(question_msg_key, category="questions")
            message += f"❓ {question_text}\n"
            message += f"✅ {answer}\n\n"

    return message.replace(
        "*", "\\*"
    )  # Оставляем только экранирование звездочек для markdown
