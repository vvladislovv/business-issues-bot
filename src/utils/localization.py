from src.database.settings_data import create_session, Localization
from sqlalchemy import select
from typing import Dict, Optional
from src.utils.logging import write_logs
import time

# Cache for storing messages
_message_cache: Dict[str, Dict[str, Dict[str, str]]] = {}
_last_cache_update = 0
CACHE_TTL = 60  # 1 minute in seconds


async def _init_messages():
    """Initialize messages from the database into cache."""
    if not _message_cache:
        async with create_session() as session:
            result = await session.execute(select(Localization))
            messages = result.scalars().all()

            for msg in messages:
                if msg.language not in _message_cache:
                    _message_cache[msg.language] = {}
                if msg.category not in _message_cache[msg.language]:
                    _message_cache[msg.language][msg.category] = {}
                _message_cache[msg.language][msg.category][msg.key] = msg.message


async def _refresh_cache():
    """Refresh the message cache from database."""
    global _last_cache_update
    _message_cache.clear()
    await _init_messages()
    _last_cache_update = time.time()


async def _should_refresh_cache() -> bool:
    """Check if cache should be refreshed based on TTL."""
    return time.time() - _last_cache_update > CACHE_TTL


async def get_message(key: str, language: str = "ru", category: str = "system") -> str:
    """Get a localized message by key and language.

    Args:
        key (str): Message key
        language (str, optional): Language code. Defaults to 'ru'.
        category (str, optional): Message category. Defaults to 'system'.

    Returns:
        str: Localized message or key if not found
    """
    if not _message_cache or await _should_refresh_cache():
        await _refresh_cache()

    return _message_cache.get(language, {}).get(category, {}).get(key, key)


async def set_message(
    key: str, language: str, message: str, category: str = "system"
) -> None:
    """Set a localized message.

    Args:
        key (str): Message key
        language (str): Language code
        message (str): Message text
        category (str, optional): Message category. Defaults to 'system'.
    """
    async with create_session() as session:
        # Check if message exists
        stmt = select(Localization).where(
            Localization.key == key,
            Localization.language == language,
            Localization.category == category,
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.message = message
        else:
            new_message = Localization(
                key=key, language=language, message=message, category=category
            )
            session.add(new_message)

        await session.commit()

        # Update cache
        if language not in _message_cache:
            _message_cache[language] = {}
        if category not in _message_cache[language]:
            _message_cache[language][category] = {}
        _message_cache[language][category][key] = message


# Initialize default messages if they don't exist
async def init_default_messages():
    """Initialize default messages in the database."""
    try:
        # System messages
        system_messages = {
            "start": "👋 Добро пожаловать! Выберите действие:",
            "invalid_password": "Неверный пароль!",
            "access_denied": "У вас нет доступа!",
            "admin_msg": "Вы вошли в админ панель:",
            "enter_password": "Введите пароль:",
            "wrong_password": "Неверный пароль!",
            "error_survey": "Произошла ошибка с состоянием опроса. Пожалуйста, начните заново.",
            "error_processing": "Произошла ошибка при обработке ответа. Пожалуйста, попробуйте позже.",
        }

        # Survey messages
        survey_messages = {
            "start_survey": "Привет! Давайте пройдем небольшой опрос, чтобы определить ваши возможности получения субсидии.",
            "select_answer": "Пожалуйста, выберите один из предложенных вариантов ответа:",
            "start_preparation": "Отлично! Сейчас мы начнем подготовку вашей заявки.",
            "get_guide": "Сейчас отправлю вам гайд по получению субсидии.",
            "contact_expert": "Сейчас подключим эксперта для консультации.",
            "faq": "Вот ответы на часто задаваемые вопросы:",
            "survey_final_base": """Отлично!
По этим данным у тебя очень высокие шансы на выдачу. С подобными ответами мои клиенты получают субсидию с первой попытки в 90%+ случаев

📌 В зависимости от вашего возраста вам доступны следующие варианты:""",
            "survey_final_under_25": """
— Социальный контракт — до 350.000 ₽
— Грант для предпринимателей — до 500.000 ₽""",
            "survey_final_over_25": """
— Социальный контракт — до 350.000 ₽""",
            "survey_final_steps": """

Что дальше? Выбери, с чего хочешь начать:

👇 Твои следующие шаги:

1️⃣ Начать подготовку заявки — включаемся в работу и идем к субсидии вместе
2️⃣ Забрать гайд «Как получить до 500.000₽ от государства» - полезный PDF с алгоритмом, примерами и лайфхаками
3️⃣ Связаться с экспертом — обсудить вашу ситуацию и задать вопросы
4️⃣ Посмотреть ответы на частые вопросы (FAQ) — коротко и по делу""",
            "survey_result_header": "📋 Новый пройденный опрос",
            "survey_result_user_info": "👤 Пользователь: @{username}\n👤 Идентификатор: {user_id}",
            "survey_result_answers_header": "📝 Ответы на вопросы:",
        }

        # Questions
        question_messages = {
            "question_has_business": "Есть ли у тебя ИП/Самозанятость?",
            "question_is_under_25": "Ты младше 25 лет?",
            "question_has_experience": "Есть ли у тебя опыт или навыки в сфере будущего бизнеса?",
            "question_region": "В каком ты регионе?",
            "question_official_income": "Какой у тебя сейчас официальный доход? (переводы на карту не считаются)",
            "question_work_plan": "Планируешь ли ты работать один или нанимать сотрудников?",
            "question_micro_result": "Можно какой-то микрорезультат дать, чтобы проще было дойти до конца вопросов",
            "question_subsidy_interest": "Насколько серьёзно вы настроены получить субсидию в ближайшие 2 месяца?",
            "question_desired_outcome": "Что вы хотели бы получить?",
            "question_importance_level": "Насколько важно для вас увеличить шансы на одобрение и сократить сроки?",
            "question_investment_readiness": "Вы готовы инвестировать в подготовку, чтобы получить субсидию в 350–500 тыс. руб?",
        }

        # Initialize all messages
        for key, message in system_messages.items():
            await set_message(key, "ru", message, "system")
            await write_logs("info", f"Initialized system message: {key}")

        for key, message in survey_messages.items():
            await set_message(key, "ru", message, "survey")
            await write_logs("info", f"Initialized survey message: {key}")

        for key, message in question_messages.items():
            await set_message(key, "ru", message, "questions")
            await write_logs("info", f"Initialized question message: {key}")

        await write_logs("info", "All messages initialized successfully")

    except Exception as e:
        await write_logs("error", f"Error initializing messages: {str(e)}")
        raise
