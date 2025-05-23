from typing import Dict
from datetime import datetime
from pydantic import BaseModel


class LogsJson(BaseModel):
    data: Dict[str, str]
    created_at: str = datetime.now().strftime("%H:%M %d-%m-%Y")


async def write_logs(TypeLog: str, message: str) -> None:
    """
    Записывает лог-сообщение с указанным уровнем.

    Args:
        TypeLog (str): Уровень лога, который может быть 'error', 'warning', 'info' или 'debug'.
        message (str): Сообщение, которое будет записано в лог.

    Returns:
        None: Функция ничего не возвращает, но выводит запись лога в консоль.
    """
    try:
        valid_log_types = ["error", "warning", "info", "debug"]
        if TypeLog.lower() not in valid_log_types:
            TypeLog = "warning"  

        # Создаем запись лога
        log_data = {"level": TypeLog, "message": message}
        log_entry = LogsJson(data=log_data)
        print(f"{log_entry.data['level']}  {log_entry.data['message']} {log_entry.created_at}")
        
    except Exception as e:
        print(f"Ошибка логирования: {str(e)}")
