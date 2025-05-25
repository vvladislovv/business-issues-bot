from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class Question:
    text: str
    field_name: str
    options: Optional[List[str]] = None
    next_question: Optional[str] = None
    is_last: bool = False


QUESTIONS: Dict[str, Question] = {
    # Block 1: Diagnostics
    "region": Question(
        text="В каком ты регионе?", field_name="region", next_question="has_business"
    ),
    "has_business": Question(
        text="Есть ли у тебя ИП/Самозанятость?",
        field_name="has_business",
        options=["Да", "Нет, но планирую", "Нет и не планирую"],
        next_question="is_under_25",
    ),
    "is_under_25": Question(
        text="Ты младше 25 лет?",
        field_name="is_under_25",
        options=["Да", "Нет"],
        next_question="has_experience",
    ),
    "has_experience": Question(
        text="Есть ли у тебя опыт или навыки в сфере будущего бизнеса?",
        field_name="has_experience",
        options=["Да", "Нет"],
        next_question="official_income",
    ),
    "official_income": Question(
        text="Какой у тебя сейчас официальный доход? (переводы на карту не считаются)",
        field_name="official_income",
        next_question="work_plan",
    ),
    "work_plan": Question(
        text="Планируешь ли ты работать один или нанимать сотрудников?",
        field_name="work_plan",
        options=["Один", "Нанимать сотрудников"],
        next_question="micro_result",
    ),
    "micro_result": Question(
        text="Можно какой-то микрорезультат дать, чтобы проще было дойти до конца вопросов",
        field_name="micro_result",
        next_question="subsidy_interest",
    ),
    # Block 2: Qualification
    "subsidy_interest": Question(
        text="Насколько серьёзно вы настроены получить субсидию в ближайшие 2 месяца?",
        field_name="subsidy_interest",
        options=["Готов начинать", "Думаю пока", "Просто интересуюсь"],
        next_question="desired_outcome",
    ),
    "desired_outcome": Question(
        text="Что вы хотели бы получить?",
        field_name="desired_outcome",
        options=["Пошаговый план", "Готовый бизнес-план", "Сопровождение под ключ"],
        next_question="importance_level",
    ),
    "importance_level": Question(
        text="Насколько важно для вас увеличить шансы на одобрение и сократить сроки?",
        field_name="importance_level",
        options=["Очень важно", "Не очень", "Пока не уверен"],
        next_question="investment_readiness",
    ),
    "investment_readiness": Question(
        text="Вы готовы инвестировать в подготовку, чтобы получить субсидию в 350–500 тыс. руб?",
        field_name="investment_readiness",
        options=[
            "Да, если шансы высоки",
            "Готов частично",
            "Нет, хочу только бесплатно",
        ],
        is_last=True,
    ),
}


def get_final_message(is_under_25: bool) -> str:
    """Генерирует финальное сообщение в зависимости от возраста пользователя.

    Args:
        is_under_25 (bool): True если пользователь младше 25 лет.

    Returns:
        str: Финальное сообщение с доступными вариантами поддержки.
    """
    base_message = """Отлично!
По этим данным у тебя очень высокие шансы на выдачу. С подобными ответами мои клиенты получают субсидию с первой попытки в 90%+ случаев

📌 В зависимости от вашего возраста вам доступны следующие варианты:"""

    if is_under_25:
        support_options = """
— Социальный контракт — до 350.000 ₽
— Грант для предпринимателей — до 500.000 ₽"""
    else:
        support_options = """
— Социальный контракт — до 350.000 ₽"""

    final_part = """

Что дальше? Выбери, с чего хочешь начать:

👇 Твои следующие шаги:

1️⃣ Начать подготовку заявки — включаемся в работу и идем к субсидии вместе
2️⃣ Забрать гайд «Как получить до 500.000₽ от государства» - полезный PDF с алгоритмом, примерами и лайфхаками
3️⃣ Связаться с экспертом — обсудить вашу ситуацию и задать вопросы
4️⃣ Посмотреть ответы на частые вопросы (FAQ) — коротко и по делу"""

    return base_message + support_options + final_part
