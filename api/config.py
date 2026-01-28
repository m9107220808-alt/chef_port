from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Настройки приложения из .env"""
    
    # База данных
    database_url: str
    
    # Telegram Bot
    bot_token: str
    
    # FastAPI
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str
    
    # ЮКасса
    yookassa_shop_id: str = ""
    yookassa_secret_key: str = ""
    
    # Мой Склад
    moysklad_login: str = ""
    moysklad_password: str = ""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

# Создаём экземпляр настроек
settings = Settings()
