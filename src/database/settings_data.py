from contextlib import asynccontextmanager
from typing import AsyncGenerator
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    String,
    DateTime,
    ForeignKey,
    Integer,
    Boolean,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, mapped_column, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from src.utils.logging import write_logs
from src.config.config import settings

Base = declarative_base()

# Устанавливаем URL базы данных на файл в текущем каталоге
# db_file_path = os.path.join(os.path.dirname(__file__), "database.db")
engine = create_async_engine(
    settings.config.DATABASE_URL, echo=True, pool_pre_ping=True
)


class UserActivity(Base):
    """Модель для хранения статистики активности пользователей.

    Атрибуты:
        id (int): Уникальный идентификатор записи.
        date (datetime): Дата активности.
        daily_active_users (int): Количество активных пользователей за день.
        weekly_active_users (int): Количество активных пользователей за неделю.
        monthly_active_users (int): Количество активных пользователей за месяц.
        daily_surveys (int): Количество пройденных опросов за день.
        weekly_surveys (int): Количество пройденных опросов за неделю.
        monthly_surveys (int): Количество пройденных опросов за месяц.
    """

    __tablename__ = "user_activity"

    id = mapped_column(Integer, primary_key=True)
    date = mapped_column(DateTime, default=datetime.utcnow, index=True)
    daily_active_users = mapped_column(Integer, default=0)
    weekly_active_users = mapped_column(Integer, default=0)
    monthly_active_users = mapped_column(Integer, default=0)
    daily_surveys = mapped_column(Integer, default=0)
    weekly_surveys = mapped_column(Integer, default=0)
    monthly_surveys = mapped_column(Integer, default=0)


class User(Base):
    """Модель для хранения информации о пользователе и ответах на опросы.

    Атрибуты:
        user_id (int): Уникальный идентификатор пользователя.
        username (str): Имя пользователя.
        first_name (str): Имя пользователя.
        last_name (str): Фамилия пользователя.
        first_seen (datetime): Когда пользователь впервые использовал бота.
        last_activity (datetime): Последняя активность пользователя.
        survey_completed (bool): Завершил ли пользователь опрос.
        active_days (int): Количество дней активности.
        last_active_date (datetime): Дата последней активности для подсчета дней.
    """

    __tablename__ = "users"

    user_id = mapped_column(BigInteger, primary_key=True)
    username = mapped_column(String(255))
    first_name = mapped_column(String(255))
    last_name = mapped_column(String(255))
    first_seen = mapped_column(DateTime, default=datetime.utcnow)
    last_activity = mapped_column(DateTime, default=datetime.utcnow)
    survey_completed = mapped_column(Boolean, default=False)
    active_days = mapped_column(Integer, default=1)
    last_active_date = mapped_column(DateTime, default=datetime.utcnow)


class UserSurvey(Base):
    """Модель для хранения ответов пользователей на опросы.

    Атрибуты:
        id (int): Уникальный идентификатор ответа на опрос.
        user_id (int): Внешний ключ, ссылающийся на пользователя.
        has_business (str): Указывает, есть ли у пользователя бизнес.
        region (str): Регион пользователя.
        is_under_25 (str): Указывает, младше ли пользователь 25 лет.
        has_experience (str): Указывает, есть ли у пользователя опыт в бизнесе.
        official_income (str): Официальный доход пользователя.
        work_plan (str): План работы пользователя.
        micro_result (str): Микрорезультат, предоставленный пользователем.
        subsidy_interest (str): Интерес пользователя к субсидиям.
        desired_outcome (str): Желаемый результат от опроса.
        importance_level (str): Уровень важности для пользователя.
        investment_readiness (str): Готовность пользователя инвестировать.
        survey_completed (bool): Указывает, завершен ли опрос.
        created_at (datetime): Временная метка, когда был создан опрос.
    """

    __tablename__ = "user_surveys"

    id = mapped_column(Integer, primary_key=True)
    user_id = mapped_column(BigInteger, ForeignKey("users.user_id"))
    has_business = mapped_column(String(255), nullable=True)
    region = mapped_column(String(255), nullable=True)
    is_under_25 = mapped_column(String(255), nullable=True)
    has_experience = mapped_column(String(255), nullable=True)
    official_income = mapped_column(String(255), nullable=True)
    work_plan = mapped_column(String(255), nullable=True)
    micro_result = mapped_column(String(255), nullable=True)
    subsidy_interest = mapped_column(String(255), nullable=True)
    desired_outcome = mapped_column(String(255), nullable=True)
    importance_level = mapped_column(String(255), nullable=True)
    investment_readiness = mapped_column(String(255), nullable=True)
    survey_completed = mapped_column(Boolean, default=False)
    created_at = mapped_column(DateTime, default=datetime.utcnow)

    # Связь с пользователем
    user = relationship("User", backref="surveys")


class Localization(Base):
    """Модель для хранения локализованных сообщений.

    Атрибуты:
        id (int): Уникальный идентификатор сообщения
        key (str): Ключ сообщения
        category (str): Категория сообщения (system, survey, questions, etc.)
        language (str): Код языка (например, 'ru')
        message (str): Текст сообщения
    """

    __tablename__ = "localizations"

    id = mapped_column(Integer, primary_key=True)
    key = mapped_column(String(255), index=True)
    category = mapped_column(String(50), index=True, default="system")
    language = mapped_column(String(10), index=True)
    message = mapped_column(String(1000))


async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Инициализирует базу данных и создает все таблицы.

    Эта функция удаляет все существующие таблицы и создает новые.
    Она записывает успех или неудачу операции.

    Raises:
        Exception: Если произошла ошибка во время инициализации.
    """
    try:
        async with engine.begin() as conn:
            # Удалить все таблицы
            # await conn.run_sync(Base.metadata.drop_all)
            # Создать все таблицы
            await conn.run_sync(Base.metadata.create_all)
            await write_logs("info", "Таблицы базы данных успешно созданы")
    except Exception as e:
        await write_logs("error", f"Ошибка инициализации базы данных: {str(e)}")
        raise


@asynccontextmanager
async def create_session() -> AsyncGenerator[AsyncSession, None]:
    """Создает новую сессию базы данных.

    Эта функция предоставляет асинхронный контекстный менеджер для сессий базы данных.
    Она фиксирует сессию, если все прошло успешно, откатывает в случае ошибки и закрывает сессию.

    Yields:
        AsyncSession: Сессия базы данных.

    Raises:
        Exception: Если произошла ошибка во время управления сессией.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            await write_logs("error", f"Ошибка сессии базы данных: {str(e)}")
            raise
        finally:
            await session.close()
