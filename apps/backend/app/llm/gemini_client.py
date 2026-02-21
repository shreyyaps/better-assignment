from typing import Literal

from google import genai
from pydantic import BaseModel, Field

from app.core.config import Settings


class BrowserStep(BaseModel):
    action: Literal[
        "goto",
        "click",
        "type",
        "wait_for",
        "screenshot",
        "extract_text",
        "scroll",
    ]
    url: str | None = None
    selector: str | None = None
    text: str | None = None
    wait_ms: int | None = None
    description: str | None = None


class BrowserPlan(BaseModel):
    goal: str = Field(default="")
    steps: list[BrowserStep]


class GeminiClient:
    def __init__(self) -> None:
        settings = Settings()
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        if not self.api_key or not self.model:
            raise ValueError("GEMINI_API_KEY and GEMINI_MODEL must be set")
        self.client = genai.Client(api_key=self.api_key)

    def plan_browser_task(self, prompt: str) -> BrowserPlan:
        """Plan a multi-step browser task using Gemini structured output."""
        system = (
            "You are a browser automation planner. "
            "Return a JSON plan with an ordered list of steps. "
            "Use actions: goto, click, type, wait_for, screenshot, extract_text, scroll. "
            "Each step may include url, selector, text, wait_ms, description. "
            "Keep selectors stable and prefer data-testid when possible. "
            "Ensure the first step is goto with a URL if provided in the prompt. "
            "Prefer DuckDuckGo over Google for search. "
            "If a CAPTCHA or 'I'm not a robot' checkbox appears, include a click step for it. "
            "Use the selector iframe[title*='reCAPTCHA'] and then click the checkbox "
            "within the iframe (div.recaptcha-checkbox-border or #recaptcha-anchor). "
            "Assume a human will complete any remaining challenge."
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                {"role": "user", "parts": [{"text": system}]},
                {"role": "user", "parts": [{"text": prompt}]},
            ],
            config={
                "response_mime_type": "application/json",
                "response_schema": BrowserPlan,
            },
        )

        return BrowserPlan.model_validate(response.parsed)

    def replan_browser_task(
        self,
        prompt: str,
        previous_plan: BrowserPlan,
        error: str,
        page_url: str,
        page_title: str,
        step_results: list[dict],
        dom_snapshot: str,
    ) -> BrowserPlan:
        """Replan after a failed step using error context."""
        system = (
            "You are a browser automation planner. The previous plan failed. "
            "Return a revised JSON plan with an ordered list of steps. "
            "Use actions: goto, click, type, wait_for, screenshot, extract_text, scroll. "
            "Fix the failed step by choosing a better selector or adding waits. "
            "Prefer DuckDuckGo over Google for search. "
            "If a CAPTCHA or 'I'm not a robot' checkbox appears, include a click step for it. "
            "Use the selector iframe[title*='reCAPTCHA'] and then click the checkbox "
            "within the iframe (div.recaptcha-checkbox-border or #recaptcha-anchor). "
            "Assume a human will complete any remaining challenge. "
            "If the page is already at the correct URL, you may omit goto."
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                {"role": "user", "parts": [{"text": system}]},
                {"role": "user", "parts": [{"text": f"Prompt: {prompt}"}]},
                {
                    "role": "user",
                    "parts": [{"text": f"Previous plan: {previous_plan.model_dump()}"}],
                },
                {"role": "user", "parts": [{"text": f"Error: {error}"}]},
                {"role": "user", "parts": [{"text": f"Page URL: {page_url}"}]},
                {"role": "user", "parts": [{"text": f"Page title: {page_title}"}]},
                {"role": "user", "parts": [{"text": f"Step results: {step_results}"}]},
                {"role": "user", "parts": [{"text": f"DOM snapshot: {dom_snapshot}"}]},
            ],
            config={
                "response_mime_type": "application/json",
                "response_schema": BrowserPlan,
            },
        )

        return BrowserPlan.model_validate(response.parsed)

    def diagnose_failure(
        self,
        prompt: str,
        previous_plan: BrowserPlan,
        error: str,
        page_url: str,
        page_title: str,
        step_results: list[dict],
        dom_snapshot: str,
    ) -> str:
        """Explain why a step likely failed and suggest a fix in 1-2 sentences."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                "Explain briefly why the automation failed and suggest a fix. "
                                "Keep it to 1-2 sentences."
                            )
                        }
                    ],
                },
                {"role": "user", "parts": [{"text": f"Prompt: {prompt}"}]},
                {
                    "role": "user",
                    "parts": [{"text": f"Previous plan: {previous_plan.model_dump()}"}],
                },
                {"role": "user", "parts": [{"text": f"Error: {error}"}]},
                {"role": "user", "parts": [{"text": f"Page URL: {page_url}"}]},
                {"role": "user", "parts": [{"text": f"Page title: {page_title}"}]},
                {"role": "user", "parts": [{"text": f"Step results: {step_results}"}]},
                {"role": "user", "parts": [{"text": f"DOM snapshot: {dom_snapshot}"}]},
            ],
        )
        return response.text or ""

    def summarize_execution(self, prompt: str, result: dict) -> str:
        """Generate short feedback for the executed plan."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                "Summarize the execution in 2-3 sentences. "
                                "Mention success/failure and key extracted info."
                            )
                        }
                    ],
                },
                {"role": "user", "parts": [{"text": f"Prompt: {prompt}"}]},
                {"role": "user", "parts": [{"text": f"Result JSON: {result}"}]},
            ],
        )
        return response.text or ""

    def summarize_plan(self, prompt: str, plan: BrowserPlan) -> str:
        """Summarize the plan in 1-2 sentences for UI."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                "Summarize the planned steps in 1-2 short sentences. "
                                "Do not include JSON."
                            )
                        }
                    ],
                },
                {"role": "user", "parts": [{"text": f"Prompt: {prompt}"}]},
                {"role": "user", "parts": [{"text": f"Plan: {plan.model_dump()}"}]},
            ],
        )
        return response.text or ""
