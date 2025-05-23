from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import select, and_
from src.database.settings_data import User, UserSurvey, create_session
from src.utils.logging import write_logs
from typing import Optional, Dict
from openpyxl.styles import Font


async def get_user_statistics() -> Optional[Dict]:
    """Получает статистику пользователей.

    Returns:
        Optional[Dict]: Словарь со статистикой или None при ошибке
    """
    async with create_session() as session:
        try:
            # Получаем всех пользователей
            users_query = await session.execute(select(User))
            users = users_query.scalars().all()

            # Формируем данные пользователей
            users_data = []
            for user in users:
                users_data.append(
                    {
                        "ID пользователя": user.user_id,
                        "Username": user.username or "Не указан",
                        "Имя": user.first_name or "Не указано",
                        "Фамилия": user.last_name or "Не указана",
                        "Первое использование": user.first_seen.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "Последняя активность": user.last_activity.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "Опрос пройден": "Да" if user.survey_completed else "Нет",
                        "Дней активности": user.active_days,
                    }
                )

            # Подсчитываем статистику
            now = datetime.utcnow()
            day_ago = now - timedelta(days=1)

            stats = {
                "total_users": len(users),
                "active_today": sum(
                    1 for user in users if user.last_activity >= day_ago
                ),
                "completed_surveys": sum(1 for user in users if user.survey_completed),
                "activity_stats": {
                    "daily": sum(1 for user in users if user.active_days == 1),
                    "weekly": sum(1 for user in users if 1 < user.active_days <= 7),
                    "monthly": sum(1 for user in users if 7 < user.active_days <= 30),
                },
                "users_data": users_data,
            }

            return stats

        except Exception as e:
            await write_logs("error", f"Error getting user statistics: {str(e)}")
            return None


async def generate_user_statistics_excel() -> Optional[str]:
    """Генерирует Excel отчет со статистикой пользователей.

    Returns:
        Optional[str]: Путь к сгенерированному файлу или None при ошибке
    """
    try:
        stats = await get_user_statistics()
        if not stats:
            return None

        # Создаем DataFrame с данными пользователей
        df_users = pd.DataFrame(stats["users_data"])

        # Добавляем итоговую информацию
        summary_data = {
            "ID пользователя": [
                "ИТОГО:",
                "",
                "Активны сегодня:",
                "Прошли опрос:",
                "",
                "По дням активности:",
                "1 день:",
                "До недели:",
                "До месяца:",
            ],
            "Username": [
                f"{stats['total_users']} пользователей",
                "",
                f"{stats['active_today']}",
                f"{stats['completed_surveys']}",
                "",
                "",
                f"{stats['activity_stats']['daily']}",
                f"{stats['activity_stats']['weekly']}",
                f"{stats['activity_stats']['monthly']}",
            ],
        }

        # Создаем DataFrame для итогов
        df_summary = pd.DataFrame(summary_data)

        # Объединяем данные, добавляя пустую строку между ними
        empty_row = pd.DataFrame(
            [["" for _ in df_users.columns]], columns=df_users.columns
        )
        df_final = pd.concat([df_summary, empty_row, df_users], ignore_index=True)

        # Сохраняем в Excel
        filename = f"user_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            df_final.to_excel(
                writer, index=False, sheet_name="Статистика пользователей"
            )

            # Получаем рабочий лист
            worksheet = writer.sheets["Статистика пользователей"]

            # Настраиваем ширину столбцов
            for idx, col in enumerate(df_final.columns):
                max_length = (
                    max(df_final[col].astype(str).apply(len).max(), len(col)) + 2
                )
                worksheet.column_dimensions[chr(65 + idx)].width = max_length

            # Применяем форматирование
            header_font = Font(name="Arial", size=11, bold=True)
            regular_font = Font(name="Arial", size=11)

            for row in worksheet.iter_rows():
                for cell in row:
                    if (
                        cell.row == 1 or cell.row <= 10
                    ):  # Заголовок и итоговая информация
                        cell.font = header_font
                    else:
                        cell.font = regular_font

        await write_logs(
            "info", f"Successfully generated user statistics Excel report: {filename}"
        )
        return filename

    except Exception as e:
        await write_logs("error", f"Error generating user statistics Excel: {str(e)}")
        return None
