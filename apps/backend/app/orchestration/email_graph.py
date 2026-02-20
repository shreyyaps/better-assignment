from typing import TypedDict

from langgraph.graph import StateGraph

from app.llm.gemini_client import GeminiClient
from app.models.email import ImportanceEnum
from app.models.user import User


class EmailState(TypedDict):
    user: User
    emails: list[dict]


def _fetch_emails(state: EmailState) -> EmailState:
    """Fetch emails from Gmail API.

    TODO: Replace stub with Gmail API calls (inbox + spam).
    """
    _ = state["user"]
    emails = [
        {
            "gmail_message_id": "stub-1",
            "subject": "Welcome to our newsletter",
            "sender": "news@example.com",
            "snippet": "Thanks for joining...",
            "body": "Thanks for joining our newsletter.",
            "is_spam": False,
        }
    ]
    return {"user": state["user"], "emails": emails}


def _classify_importance(state: EmailState) -> EmailState:
    client = GeminiClient()
    for email in state["emails"]:
        email_text = email.get("body") or ""
        email["importance"] = client.classify_email_importance(email_text)
    return state


def _store_emails(state: EmailState) -> EmailState:
    # Storage handled in service layer for now.
    return state


def _generate_reply(state: EmailState) -> EmailState:
    # Optional step for future automation.
    return state


def build_email_graph() -> StateGraph:
    graph = StateGraph(EmailState)
    graph.add_node("fetch_emails", _fetch_emails)
    graph.add_node("classify_importance", _classify_importance)
    graph.add_node("store_emails", _store_emails)
    graph.add_node("generate_reply", _generate_reply)

    graph.set_entry_point("fetch_emails")
    graph.add_edge("fetch_emails", "classify_importance")
    graph.add_edge("classify_importance", "store_emails")
    graph.add_edge("store_emails", "generate_reply")
    graph.set_finish_point("generate_reply")

    return graph


def run_email_graph(user: User) -> EmailState:
    graph = build_email_graph().compile()
    result = graph.invoke({"user": user, "emails": []})

    for email in result["emails"]:
        if "importance" not in email:
            email["importance"] = ImportanceEnum.MEDIUM

    return result
