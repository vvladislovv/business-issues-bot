from dataclasses import dataclass
from typing import List, Optional, Dict
from src.utils.localization import get_message


@dataclass
class Question:
    key: str  # Ключ для получения текста из БД
    field_name: str
    options: Optional[List[str]] = None
    next_question: Optional[str] = None
    is_last: bool = False

    async def get_text(self) -> str:
        """Получает текст вопроса из базы данных."""
        return await get_message(self.key, category="questions")


# Удаляем класс MicroResultQuestion
# class MicroResultQuestion(Question):
#     def __init__(self):
#         super().__init__(
#             key="question_micro_result",
#             field_name="micro_result",
#             next_question="region",
#             options=["Да", "Нет"],
#             is_last=False,
#         )

#     async def get_text(self) -> str:
#         return (
#             "✨ Отлично! Судя по твоим ответам, у тебя есть все шансы получить субсидию!\n\n"
#             "Осталось всего 2 вопроса, и ты узнаешь точный результат. Продолжаем? 😊"
#         )


QUESTIONS: Dict[str, Question] = {
    # Block 1: Diagnostics
    "has_business": Question(
        key="question_has_business",
        field_name="has_business",
        options=["Да", "Нет, но планирую", "Нет и не планирую"],
        next_question="is_under_25",
    ),
    "is_under_25": Question(
        key="question_is_under_25",
        field_name="is_under_25",
        options=["Да", "Нет"],
        next_question="has_experience",
    ),
    "has_experience": Question(
        key="question_has_experience",
        field_name="has_experience",
        options=["Да", "Нет"],
        next_question="region",
    ),
    "region": Question(
        key="question_region", field_name="region", next_question="official_income"
    ),
    "official_income": Question(
        key="question_official_income",
        field_name="official_income",
        options=[
            "Меньше 50.000",
            "50.000-100.000",
            "100.000-250.000",
            "250.000+",
        ],
        next_question="work_plan",
    ),
    "work_plan": Question(
        key="question_work_plan",
        field_name="work_plan",
        options=["Один", "Нанимать сотрудников"],
        next_question="subsidy_interest",  # Изменено с "micro_result" на "subsidy_interest"
    ),
    # Удаляем запись "micro_result"
    # "micro_result": MicroResultQuestion(),
    # Block 2: Qualification
    "subsidy_interest": Question(
        key="question_subsidy_interest",
        field_name="subsidy_interest",
        options=["Готов начинать", "Думаю пока", "Просто интересуюсь"],
        next_question="desired_outcome",
    ),
    "desired_outcome": Question(
        key="question_desired_outcome",
        field_name="desired_outcome",
        options=["Пошаговый план", "Готовый бизнес-план", "Сопровождение под ключ"],
        next_question="importance_level",
    ),
    "importance_level": Question(
        key="question_importance_level",
        field_name="importance_level",
        options=["Очень важно", "Не очень", "Пока не уверен"],
        next_question="investment_readiness",
    ),
    "investment_readiness": Question(
        key="question_investment_readiness",
        field_name="investment_readiness",
        options=[
            "Да, если шансы высоки",
            "Готов частично",
            "Нет, хочу только бесплатно",
        ],
        is_last=True,
    ),
}


async def get_final_message(is_under_25: bool) -> str:
    """Генерирует финальное сообщение в зависимости от возраста пользователя."""
    base_message = await get_message("survey_final_base", category="survey")

    if is_under_25:
        support_options = await get_message("survey_final_under_25", category="survey")
    else:
        support_options = await get_message("survey_final_over_25", category="survey")

    final_part = await get_message("survey_final_steps", category="survey")

    return base_message + support_options + final_part
