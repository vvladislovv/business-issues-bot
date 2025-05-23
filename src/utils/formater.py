from src.database.settings_data import UserSurvey

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
        str: Строка, содержащая отформатированные результаты опроса, включая 
              имя пользователя и их ответы на вопросы.
    """
    message = f"📋 Новый пройденный опрос\n"
    message += f"👤 Пользователь: @{username}\n\n"
    message += f"👤 Идентификатор: {user_id}\n\n"
    message += "📝 Ответы на вопросы:\n\n"

    # Создаем словарь с вопросами и ответами
    answers = {
        "region": ("В каком регионе?", survey.region),
        "has_business": ("Есть ли ИП/Самозанятость?", survey.has_business),
        "is_under_25": ("Младше 25 лет?", survey.is_under_25),
        "has_experience": ("Есть опыт или навыки?", survey.has_experience),
        "official_income": ("Официальный доход", survey.official_income),
        "work_plan": ("План работы", survey.work_plan),
        "micro_result": ("Микрорезультат", survey.micro_result),
        "subsidy_interest": ("Интерес к субсидии", survey.subsidy_interest),
        "desired_outcome": ("Желаемый результат", survey.desired_outcome),
        "importance_level": ("Важность шансов", survey.importance_level),
        "investment_readiness": (
            "Готовность инвестировать",
            survey.investment_readiness,
        ),
    }


    for (question_text, answer) in answers.items():
        if answer:  
            message += f"❓ {question_text}\n"
            message += f"✅ {answer}\n\n"

    return message.replace("_", "\\_").replace(
        "*", "\\*"
    )  
