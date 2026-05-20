import os
from pydantic import field_validator
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
    RESEND_API_KEY: str

    @field_validator("TELEGRAM_BOT_TOKEN", mode="before")
    @classmethod
    def clean_telegram_token(cls, v: str) -> str:
        if not isinstance(v, str):
            return v
        v = v.strip()
        # Remove surrounding quotes
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        v = v.strip()
        # Remove leading "bot" case-insensitive
        if v.lower().startswith("bot"):
            v = v[3:]
        return v.strip()

    @field_validator("TELEGRAM_CHAT_ID", mode="before")
    @classmethod
    def clean_chat_id(cls, v: str) -> str:
        if not isinstance(v, str):
            return str(v)
        v = v.strip()
        # Remove surrounding quotes
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        return v.strip()

    # Automatically look for a .env file in the current working directory
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# Initialize a single settings instance to share across modules
settings = Settings()