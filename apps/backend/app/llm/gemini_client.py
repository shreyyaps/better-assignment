from app.core.config import Settings
from app.models.email import ImportanceEnum


class GeminiClient:
    def __init__(self) -> None:
        settings = Settings()
        self.api_key = settings.gemini_api_key

    def classify_email_importance(self, email_text: str) -> ImportanceEnum:
        """Classify email importance using Gemini.

        TODO: Call Gemini API with a structured prompt.
        """
        _ = email_text
        return ImportanceEnum.MEDIUM

    def generate_reply(self, email_text: str) -> str:
        """Generate a reply using Gemini.

        TODO: Call Gemini API with a reply-generation prompt.
        """
        _ = email_text
        return "Thanks for reaching out. I'll get back to you soon."
