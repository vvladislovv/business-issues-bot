import json
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from typing import List, Optional
from src.utils.formater import format_user_survey_results
from src.utils.logging import write_logs
from .settings_data import User, create_session, UserSurvey, UserActivity


async def get_all_users() -> List[User]:
    """Получает всех пользователей из базы данных.

    Returns:
        List[User]: Список всех пользователей
    """
    async with create_session() as session:
        try:
            result = await session.execute(select(User))
            return result.scalars().all()
        except Exception as e:
            await write_logs("error", f"Error getting all users: {str(e)}")
            return []


async def get_user_by_id(json_data: str) -> Optional[User]:
    """Получает пользователя по его идентификатору.

    Args:
        json_data (str): JSON-строка, содержащая идентификатор пользователя.

    Returns:
        Optional[User]: Объект User, если пользователь найден, иначе None.
    """
    async with create_session() as session:
        try:
            params = json.loads(json_data)
            user_id = params.get("user_id")
            stmt = select(User).where(User.user_id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            await write_logs("error", f"Error getting user: {str(e)}")
            return None


async def check_existing_user(user_id: int) -> Optional[User]:
    """Проверяет, существует ли пользователь с данным идентификатором.

    Args:
        user_id (int): Идентификатор пользователя.

    Returns:
        Optional[User]: Объект User, если пользователь существует, иначе None.
    """
    async with create_session() as session:
        try:
            stmt = select(User).where(User.user_id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            await write_logs("error", f"Error checking existing user: {str(e)}")
            return None


async def add_user_if_not_exists(user_data: dict):
    """Добавляет пользователя в базу данных, если он не существует.

    Args:
        user_data (dict): Словарь с данными пользователя, включая user_id, username, first_name и last_name.
    """
    async with create_session() as session:
        try:
            user_id = user_data["user_id"]
            existing_user = await check_existing_user(user_id)
            if existing_user is None:
                new_user = User(
                    user_id=user_id,
                    username=user_data.get("username"),
                    first_name=user_data.get("first_name"),
                    last_name=user_data.get("last_name"),
                )
                session.add(new_user)
                await session.commit()
                await write_logs(
                    "info", f"User with ID {user_id} added to the database."
                )
            else:
                await write_logs(
                    "info", f"User with ID {user_id} already exists in the database."
                )
        except Exception as e:
            await write_logs("error", f"Error adding user: {str(e)}")


async def save_survey_answer(user_id: int, field_name: str, answer: str):
    """Сохраняет ответ пользователя на вопрос опроса.

    Args:
        user_id (int): Идентификатор пользователя.
        field_name (str): Имя поля, в которое будет сохранен ответ.
        answer (str): Ответ пользователя.
    """
    async with create_session() as session:
        try:
            # Get or create survey for user
            stmt = (
                select(UserSurvey)
                .where(
                    UserSurvey.user_id == user_id, UserSurvey.survey_completed == False
                )
                .order_by(UserSurvey.created_at.desc())
            )
            result = await session.execute(stmt)
            survey = result.scalar_one_or_none()

            if not survey:
                survey = UserSurvey(user_id=user_id)
                session.add(survey)

            # Update the specific field
            setattr(survey, field_name, answer)
            await session.commit()

        except Exception as e:
            await write_logs("error", f"Error saving survey answer: {str(e)}")


async def update_user_activity(user_id: int):
    """Обновляет статистику активности пользователя.

    Args:
        user_id (int): Идентификатор пользователя.
    """
    async with create_session() as session:
        try:
            # Получаем пользователя
            user_stmt = select(User).where(User.user_id == user_id)
            user = (await session.execute(user_stmt)).scalar_one_or_none()

            if not user:
                return

            now = datetime.utcnow()
            today = now.date()

            # Проверяем, был ли пользователь активен сегодня
            if user.last_active_date.date() != today:
                user.active_days += 1
                user.last_active_date = now

            user.last_activity = now

            # Получаем или создаем запись активности за сегодня
            activity_stmt = select(UserActivity).where(
                func.date(UserActivity.date) == today
            )
            activity = (await session.execute(activity_stmt)).scalar_one_or_none()

            if not activity:
                activity = UserActivity(date=now)
                session.add(activity)

            # Обновляем статистику
            # Получаем количество активных пользователей
            day_ago = now - timedelta(days=1)
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)

            daily_users = await session.execute(
                select(func.count(User.user_id)).where(User.last_activity >= day_ago)
            )
            weekly_users = await session.execute(
                select(func.count(User.user_id)).where(User.last_activity >= week_ago)
            )
            monthly_users = await session.execute(
                select(func.count(User.user_id)).where(User.last_activity >= month_ago)
            )

            # Получаем количество завершенных опросов
            daily_surveys = await session.execute(
                select(func.count(UserSurvey.id)).where(
                    and_(
                        UserSurvey.created_at >= day_ago,
                        UserSurvey.survey_completed == True,
                    )
                )
            )
            weekly_surveys = await session.execute(
                select(func.count(UserSurvey.id)).where(
                    and_(
                        UserSurvey.created_at >= week_ago,
                        UserSurvey.survey_completed == True,
                    )
                )
            )
            monthly_surveys = await session.execute(
                select(func.count(UserSurvey.id)).where(
                    and_(
                        UserSurvey.created_at >= month_ago,
                        UserSurvey.survey_completed == True,
                    )
                )
            )

            # Обновляем статистику
            activity.daily_active_users = daily_users.scalar()
            activity.weekly_active_users = weekly_users.scalar()
            activity.monthly_active_users = monthly_users.scalar()
            activity.daily_surveys = daily_surveys.scalar()
            activity.weekly_surveys = weekly_surveys.scalar()
            activity.monthly_surveys = monthly_surveys.scalar()

            await session.commit()
            await write_logs("info", f"Updated activity statistics for user {user_id}")

        except Exception as e:
            await write_logs("error", f"Error updating user activity: {str(e)}")


async def get_or_create_user(user_id: int, username: str) -> User:
    """Получает существующего пользователя или создает нового.

    Args:
        user_id (int): Идентификатор пользователя.
        username (str): Имя пользователя.

    Returns:
        User: Объект User, представляющий существующего или нового пользователя.
    """
    async with create_session() as session:
        try:
            # Try to get existing user
            stmt = select(User).where(User.user_id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if user is None:
                # Create new user if not exists
                user = User(
                    user_id=user_id,
                    username=username,
                    last_active_date=datetime.utcnow(),
                )
                session.add(user)
                await session.commit()
                await write_logs("info", f"Created new user with ID {user_id}")

            # Обновляем активность пользователя
            await update_user_activity(user_id)

            return user
        except Exception as e:
            await write_logs("error", f"Error in get_or_create_user: {str(e)}")
            raise


async def finalize_survey(user_id: int, username: str) -> Optional[str]:
    """Завершает опрос пользователя и отправляет результаты в канал.

    Args:
        user_id (int): Идентификатор пользователя.
        username (str): Имя пользователя.

    Returns:
        Optional[str]: Форматированные результаты опроса, если опрос завершен, иначе None.
    """
    async with create_session() as session:
        try:
            # Получаем данные опроса пользователя
            stmt = (
                select(UserSurvey)
                .where(
                    UserSurvey.user_id == user_id, UserSurvey.survey_completed == False
                )
                .order_by(UserSurvey.created_at.desc())
            )
            result = await session.execute(stmt)
            survey = result.scalar_one_or_none()

            if survey:
                # Отмечаем опрос как завершенный
                survey.survey_completed = True

                # Получаем и обновляем пользователя
                user_stmt = select(User).where(User.user_id == user_id)
                user = (await session.execute(user_stmt)).scalar_one_or_none()
                if user:
                    user.survey_completed = True
                    user.last_activity = datetime.utcnow()

                    # Обновляем счетчик дней активности
                    if (datetime.utcnow() - user.last_activity).days >= 1:
                        user.active_days += 1

                await session.commit()

                # Форматируем результаты опроса
                user_results = await format_user_survey_results(
                    user_id, username or "Без username", survey
                )
                return user_results

            return None  # Если опрос не найден

        except Exception as e:
            await write_logs("error", f"Error finalizing survey: {str(e)}")
            return None
