from dataclasses import dataclass
from environs import Env


@dataclass
class Admins:
    admins: list[int]


@dataclass
class Config:
    bot_token: str
    channel_id: int
    admins: Admins
    DATABASE_URL: str
    ADMIN_PASSWORD: str  # Изменено с List[int] на str
    # db_user: str
    # db_password: str
    # db_name: str
    # db_host: str
    # db_port: int
    # admin_id: int
    start_preparation_url: str
    contact_expert_url: str
    faq_url: str


@dataclass
class Settings:
    bot_token: str
    config: Config


def get_settings(path: str = None) -> Settings:
    """
    Загружает настройки из переменных окружения.

    Args:
        path (str, optional): Путь к файлу .env. Если не указан, будет использован файл по умолчанию.

    Returns:
        Settings: Объект Settings, содержащий конфигурацию бота и другие параметры.
    """
    env = Env()
    env.read_env(path)

    def parse_ids(v: str) -> list[int]:
        """
        Преобразует строку с идентификаторами в список целых чисел.

        Args:
            v (str): Строка, содержащая идентификаторы, разделенные запятыми.

        Returns:
            list[int]: Список целых чисел, представляющих идентификаторы.
        """
        # Remove any surrounding brackets and quotes before splitting
        cleaned_ids = v.strip("[]'\"")
        return [int(id.strip()) for id in cleaned_ids.split(",")]

    return Settings(
        bot_token=env.str("TOKEN_BOT"),
        config=Config(
            bot_token=env.str("TOKEN_BOT"),
            channel_id=env.int("CHANNEL_ID"),
            admins=Admins(
                admins=parse_ids(env.str("ADMINS_ID"))  # Преобразуем строки в числа
            ),
            ADMIN_PASSWORD=env.str("ADMIN_PASSWORD"),
            DATABASE_URL=env.str("DATABASE_URL"),
            # db_user=env.str("DB_USER"),
            # db_password=env.str("DB_PASSWORD"),
            # db_name=env.str("DB_NAME"),
            # db_host=env.str("DB_HOST"),
            # db_port=env.int("DB_PORT"),
            # admin_id=env.int("ADMIN_ID"),
            start_preparation_url=env.str("START_PREPARATION_URL"),
            contact_expert_url=env.str("CONTACT_EXPERT_URL"),
            faq_url=env.str("FAQ_URL"),
        ),
    )


settings = get_settings()
