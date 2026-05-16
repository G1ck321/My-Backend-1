import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # Flutterwave Configuration
    FLW_SECRET_HASH: str
    FW_SECRET_KEY: str  # Added to authenticate outbound API requests

    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: str

    # Automatically look for a .env file in the current working directory
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# Initialize a single settings instance to share across modules
settings = Settings()