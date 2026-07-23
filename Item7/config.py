import os
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed environment settings loaded from the local .env file."""

    # Supabase connection details used by the database client.
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # Flutterwave configuration for payment creation and webhook verification.
    FLW_SECRET_HASH: str
    FW_SECRET_KEY: str

    # Telegram and email settings for admin notifications.
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: str
    RESEND_API_KEY: str
    OWNER_EMAIL_ADDRESS: str

    @field_validator("TELEGRAM_BOT_TOKEN", mode="before")
    @classmethod
    def clean_telegram_token(cls, v: str) -> str:
        if not isinstance(v, str):
            return v
        v = v.strip()
        # Allow values copied from shells or editors that wrap the token in quotes.
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        v = v.strip()
        # Telegram sometimes gets pasted with the "bot" prefix included.
        if v.lower().startswith("bot"):
            v = v[3:]
        return v.strip()

    @field_validator("TELEGRAM_CHAT_ID", mode="before")
    @classmethod
    def clean_chat_id(cls, v: str) -> str:
        if not isinstance(v, str):
            return str(v)
        v = v.strip()
        # Keep chat IDs clean even if they were copied with surrounding quotes.
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        return v.strip()

    # Load variables from the project-local .env file.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# Create one shared settings object so every module reads the same configuration.
settings = Settings()