from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = ""
    clerk_jwt_public_key: str = ""
    clerk_jwks_url: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    playwright_headed: bool = True
    playwright_slow_mo_ms: int = 0
    playwright_capture_step_screenshots: bool = False
    playwright_capture_dom_snapshot: bool = True
    playwright_default_timeout_ms: int = 3000
    planner_max_attempts: int = 2
