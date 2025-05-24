from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import select
from src.database.settings_data import User, create_session
from src.utils.logging import write_logs
from typing import Optional, Dict
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter


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
                        "id": user.user_id,
                        "username": user.username or "",
                        "first_name": user.first_name or "",
                        "last_name": user.last_name or "",
                        "fist_seen": user.first_seen.strftime("%Y-%m-%d %H:%M:%S.%f")[
                            :-4
                        ],
                        "last_activity": user.last_activity.strftime(
                            "%Y-%m-%d %H:%M:%S.%f"
                        )[:-4],
                        "survey_completed": user.survey_completed,
                        "active_days": user.active_days,
                    }
                )

            return {"users_data": users_data}

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
        df = pd.DataFrame(stats["users_data"])

        # Устанавливаем порядок колонок как на фотографии
        columns = [
            "id",
            "username",
            "first_name",
            "last_name",
            "fist_seen",
            "last_activity",
            "survey_completed",
            "active_days",
        ]
        df = df[columns]

        # Сохраняем в Excel
        filename = "users_data.xlsx"

        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="J17")

            # Получаем рабочий лист
            worksheet = writer.sheets["J17"]

            # Настраиваем форматирование
            for idx, col in enumerate(df.columns, 1):
                # Получаем букву колонки
                column_letter = get_column_letter(idx)

                # Устанавливаем ширину колонки
                max_length = max(df[col].astype(str).apply(len).max(), len(str(col)))
                adjusted_width = max_length + 2
                worksheet.column_dimensions[column_letter].width = adjusted_width

                # Форматируем заголовок
                header_cell = worksheet[f"{column_letter}1"]
                header_cell.font = Font(name="Arial", size=11)
                header_cell.alignment = Alignment(horizontal="left")

                # Форматируем все ячейки в колонке
                for row in range(2, len(df) + 2):
                    cell = worksheet[f"{column_letter}{row}"]
                    cell.font = Font(name="Arial", size=11)
                    cell.alignment = Alignment(horizontal="left")

                    # Форматируем числовые значения для survey_completed
                    if col == "survey_completed":
                        cell.value = 1 if cell.value else 0

        await write_logs(
            "info", f"Successfully generated user statistics Excel report: {filename}"
        )
        return filename

    except Exception as e:
        await write_logs("error", f"Error generating user statistics Excel: {str(e)}")
        return None
