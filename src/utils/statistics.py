from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import select, and_, func
from src.database.settings_data import User, UserSurvey, UserActivity, create_session
from src.utils.logging import write_logs
from typing import Optional, Dict
from openpyxl.styles import Font


async def get_time_based_statistics() -> Optional[Dict]:
    """Получает статистику использования бота по времени.

    Returns:
        Optional[Dict]: Словарь со статистикой или None при ошибке
    """
    async with create_session() as session:
        try:
            now = datetime.utcnow()
            today = now.date()

            # Получаем статистику за сегодня
            activity_stmt = select(UserActivity).where(
                func.date(UserActivity.date) == today
            )
            activity = (await session.execute(activity_stmt)).scalar_one_or_none()

            if not activity:
                # Если статистики нет, возвращаем нулевые значения
                return {
                    "total": {"users": 0, "surveys": 0},
                    "daily": {"users": 0, "surveys": 0},
                    "weekly": {"users": 0, "surveys": 0},
                    "monthly": {"users": 0, "surveys": 0},
                }

            # Получаем общее количество пользователей и опросов
            total_users = await session.execute(select(func.count(User.user_id)))
            total_surveys = await session.execute(
                select(func.count(UserSurvey.id)).where(
                    UserSurvey.survey_completed == True
                )
            )

            stats = {
                "total": {
                    "users": total_users.scalar(),
                    "surveys": total_surveys.scalar(),
                },
                "daily": {
                    "users": activity.daily_active_users,
                    "surveys": activity.daily_surveys,
                },
                "weekly": {
                    "users": activity.weekly_active_users,
                    "surveys": activity.weekly_surveys,
                },
                "monthly": {
                    "users": activity.monthly_active_users,
                    "surveys": activity.monthly_surveys,
                },
            }

            return stats

        except Exception as e:
            await write_logs("error", f"Error getting time-based statistics: {str(e)}")
            return None


async def generate_time_statistics_excel() -> Optional[str]:
    """Генерирует Excel отчет со статистикой использования бота.

    Returns:
        Optional[str]: Путь к сгенерированному файлу или None при ошибке
    """
    try:
        stats = await get_time_based_statistics()
        if not stats:
            return None

        # Создаем данные для сводной информации
        summary_data = {
            "Показатель": [
                "ИТОГО:",
                "",
                "Активны сегодня:",
                "Прошли опрос сегодня:",
                "",
                "За последнюю неделю:",
                "Активных пользователей:",
                "Пройдено опросов:",
                "",
                "За последний месяц:",
                "Активных пользователей:",
                "Пройдено опросов:",
                "",
                "Всего:",
                "Пользователей:",
                "Пройдено опросов:",
            ],
            "Количество": [
                f"{stats['total']['users']} пользователей",
                "",
                f"{stats['daily']['users']}",
                f"{stats['daily']['surveys']}",
                "",
                "",
                f"{stats['weekly']['users']}",
                f"{stats['weekly']['surveys']}",
                "",
                "",
                f"{stats['monthly']['users']}",
                f"{stats['monthly']['surveys']}",
                "",
                "",
                f"{stats['total']['users']}",
                f"{stats['total']['surveys']}",
            ],
        }

        # Создаем DataFrame
        df = pd.DataFrame(summary_data)

        # Сохраняем в Excel
        filename = f"bot_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Статистика бота")

            # Получаем рабочий лист
            worksheet = writer.sheets["Статистика бота"]

            # Настраиваем ширину столбцов
            for idx, col in enumerate(df.columns):
                max_length = max(df[col].astype(str).apply(len).max(), len(col)) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = max_length

            # Применяем форматирование
            header_font = Font(name="Arial", size=11, bold=True)
            regular_font = Font(name="Arial", size=11)

            for row in worksheet.iter_rows():
                for cell in row:
                    if cell.row == 1 or ":" in str(cell.value):  # Заголовок и категории
                        cell.font = header_font
                    else:
                        cell.font = regular_font

        await write_logs(
            "info", f"Successfully generated time statistics Excel report: {filename}"
        )
        return filename

    except Exception as e:
        await write_logs("error", f"Error generating time statistics Excel: {str(e)}")
        return None
