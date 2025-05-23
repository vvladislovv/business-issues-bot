from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import select, and_
from src.database.settings_data import User, UserSurvey, create_session
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
            day_ago = now - timedelta(days=1)
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)

            # Получаем всех пользователей и опросы
            users_query = await session.execute(select(User))
            surveys_query = await session.execute(select(UserSurvey))

            users = users_query.scalars().all()
            surveys = surveys_query.scalars().all()

            # Подсчитываем статистику
            stats = {
                "total": {
                    "users": len(users),
                    "surveys": len([s for s in surveys if s.survey_completed]),
                },
                "daily": {
                    "users": len([u for u in users if u.first_seen >= day_ago]),
                    "surveys": len(
                        [
                            s
                            for s in surveys
                            if s.created_at >= day_ago and s.survey_completed
                        ]
                    ),
                },
                "weekly": {
                    "users": len([u for u in users if u.first_seen >= week_ago]),
                    "surveys": len(
                        [
                            s
                            for s in surveys
                            if s.created_at >= week_ago and s.survey_completed
                        ]
                    ),
                },
                "monthly": {
                    "users": len([u for u in users if u.first_seen >= month_ago]),
                    "surveys": len(
                        [
                            s
                            for s in surveys
                            if s.created_at >= month_ago and s.survey_completed
                        ]
                    ),
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
                "Новых пользователей:",
                "Пройдено опросов:",
                "",
                "За последний месяц:",
                "Новых пользователей:",
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
