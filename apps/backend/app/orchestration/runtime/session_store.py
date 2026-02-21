from dataclasses import dataclass
from typing import Any


@dataclass
class SessionState:
    playwright: Any
    browser: Any
    page: Any
    plan: Any
    step_index: int
    step_results: list[dict]
    last_screenshot: str | None
    last_error: str
    logs: list[str]
    dom_snapshot: str
    stop_requested: bool = False


ACTIVE_SESSIONS: dict[int, SessionState] = {}
