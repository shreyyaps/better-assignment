from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/ai_email"
    clerk_jwt_public_key: str = ""
    gemini_api_key: str = ""
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_redirect_uri: str = ""

    scheduler_timezone: str = "UTC"
    scheduler_interval_minutes: int = 5
