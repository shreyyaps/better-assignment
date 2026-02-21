import base64
from typing import TypedDict

from langgraph.graph import StateGraph
from playwright.sync_api import sync_playwright

from app.core.config import Settings
from app.llm.gemini_client import BrowserPlan, GeminiClient
from app.orchestration.runtime.artifacts import truncate_text
from app.orchestration.runtime.session_store import ACTIVE_SESSIONS, SessionState


class BrowserState(TypedDict):
    prompt: str
    plan: BrowserPlan
    result: dict
    feedback: str


def _plan_task(state: BrowserState) -> BrowserState:
    client = GeminiClient()
    plan = client.plan_browser_task(state["prompt"])
    return {"prompt": state["prompt"], "plan": plan, "result": {}, "feedback": ""}


def _capture_dom_snapshot(page, settings: Settings) -> str:
    if not settings.playwright_capture_dom_snapshot:
        return ""
    try:
        return truncate_text(page.content())
    except Exception:  # noqa: BLE001
        return ""


def _execute_step(
    page,
    step,
    settings: Settings,
    logs: list[str],
    step_results: list[dict],
    step_artifacts: list[dict],
):
    last_screenshot = None
    failure_screenshot = None
    try:
        if step.action == "goto":
            if not step.url:
                raise ValueError("goto requires url")
            logs.append(f"[goto] {step.url}")
            page.goto(step.url, wait_until="domcontentloaded")
            step_results.append({"action": "goto", "url": step.url, "ok": True})
        elif step.action == "click":
            if not step.selector:
                raise ValueError("click requires selector")
            logs.append(f"[click] {step.selector}")
            locator = page.locator(step.selector).first
            box = locator.bounding_box()
            if box:
                import random

                x = box["x"] + box["width"] / 2
                y = box["y"] + box["height"] / 2
                jitter = random.uniform(2, 6)
                page.mouse.move(x - jitter, y - jitter, steps=8)
                page.mouse.move(x + jitter, y + jitter, steps=6)
                page.mouse.move(x, y, steps=4)
                page.mouse.click(x, y, delay=random.randint(30, 120))
            else:
                locator.click()
            step_results.append({"action": "click", "selector": step.selector, "ok": True})
        elif step.action == "type":
            if not step.selector:
                raise ValueError("type requires selector")
            logs.append(f"[type] {step.selector}")
            page.fill(step.selector, step.text or "")
            step_results.append(
                {
                    "action": "type",
                    "selector": step.selector,
                    "text": step.text or "",
                    "ok": True,
                }
            )
        elif step.action == "wait_for":
            if step.selector:
                logs.append(f"[wait_for] selector {step.selector}")
                page.wait_for_selector(
                    step.selector, timeout=step.wait_ms or settings.playwright_default_timeout_ms
                )
            elif step.wait_ms:
                logs.append(f"[wait_for] {step.wait_ms}ms")
                page.wait_for_timeout(step.wait_ms)
            else:
                logs.append(f"[wait_for] {settings.playwright_default_timeout_ms}ms")
                page.wait_for_timeout(settings.playwright_default_timeout_ms)
            step_results.append(
                {
                    "action": "wait_for",
                    "selector": step.selector,
                    "wait_ms": step.wait_ms,
                    "ok": True,
                }
            )
        elif step.action == "scroll":
            logs.append("[scroll]")
            page.evaluate("window.scrollBy(0, window.innerHeight)")
            step_results.append({"action": "scroll", "ok": True})
        elif step.action == "extract_text":
            if not step.selector:
                raise ValueError("extract_text requires selector")
            logs.append(f"[extract_text] {step.selector}")
            text = page.inner_text(step.selector)
            step_results.append(
                {
                    "action": "extract_text",
                    "selector": step.selector,
                    "text": text,
                    "ok": True,
                }
            )
        elif step.action == "screenshot":
            logs.append("[screenshot]")
            screenshot_bytes = page.screenshot(full_page=True)
            last_screenshot = base64.b64encode(screenshot_bytes).decode("ascii")
            step_results.append({"action": "screenshot", "ok": True})
        else:
            step_results.append({"action": step.action, "ok": False, "error": "Unknown action"})
            return False, "Unknown action", last_screenshot
    except Exception as exc:  # noqa: BLE001
        error = str(exc)
        logs.append(f"[error] {error}")
        step_results.append(
            {
                "action": step.action,
                "ok": False,
                "error": error,
                "selector": step.selector,
                "url": step.url,
            }
        )
        if settings.playwright_capture_step_screenshots:
            try:
                step_shot = page.screenshot(full_page=True)
                failure_screenshot = base64.b64encode(step_shot).decode("ascii")
            except Exception:  # noqa: BLE001
                pass
        return False, error, last_screenshot, failure_screenshot

    return True, "", last_screenshot, failure_screenshot


def _run_playwright(state: BrowserState) -> BrowserState:
    plan = state["plan"]
    settings = Settings()
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=not settings.playwright_headed, slow_mo=settings.playwright_slow_mo_ms
        )
        page = browser.new_page()
        page.set_default_timeout(settings.playwright_default_timeout_ms)
        page.set_default_timeout(settings.playwright_default_timeout_ms)
        step_results: list[dict] = []
        step_artifacts: list[dict] = []
        last_screenshot: str | None = None
        step_artifacts: list[dict] = []
        attempts = 0
        last_error = ""
        planner = GeminiClient()
        logs: list[str] = []
        diagnosis = ""
        dom_snapshot = ""

        while attempts < settings.planner_max_attempts:
            attempts += 1
            step_results.clear()
            last_error = ""
            logs.append(f"[attempt {attempts}] executing {len(plan.steps)} steps")
            for step in plan.steps:
                ok, error, shot, _failure_shot = _execute_step(
                    page, step, settings, logs, step_results, step_artifacts
                )
                if shot:
                    last_screenshot = shot
                if not ok:
                    last_error = error
                    break

            if not last_error:
                break

            if attempts < settings.planner_max_attempts:
                dom_snapshot = _capture_dom_snapshot(page, settings)
                diagnosis = planner.diagnose_failure(
                    prompt=state["prompt"],
                    previous_plan=plan,
                    error=last_error,
                    page_url=page.url,
                    page_title=page.title(),
                    step_results=step_results,
                    dom_snapshot=dom_snapshot,
                )
                logs.append(f"[diagnosis] {diagnosis}")
                plan = planner.replan_browser_task(
                    prompt=state["prompt"],
                    previous_plan=plan,
                    error=last_error,
                    page_url=page.url,
                    page_title=page.title(),
                    step_results=step_results,
                    dom_snapshot=dom_snapshot,
                )

        title = page.title()
        result: dict = {
            "goal": plan.goal,
            "title": title,
            "steps": [step.model_dump() for step in plan.steps],
            "step_results": step_results,
            "attempts": attempts,
            "logs": logs,
        }
        if last_error:
            result["error"] = last_error
        if diagnosis:
            result["diagnosis"] = diagnosis
        if dom_snapshot:
            result["dom_snapshot"] = dom_snapshot
        if step_artifacts:
            result["step_artifacts"] = step_artifacts
        if last_screenshot:
            result["screenshot_base64"] = last_screenshot

        browser.close()

    return {"prompt": state["prompt"], "plan": plan, "result": result, "feedback": ""}


def _summarize(state: BrowserState) -> BrowserState:
    client = GeminiClient()
    feedback = client.summarize_execution(state["prompt"], state["result"])
    return {
        "prompt": state["prompt"],
        "plan": state["plan"],
        "result": state["result"],
        "feedback": feedback,
    }


def build_browser_graph() -> StateGraph:
    graph = StateGraph(BrowserState)
    graph.add_node("plan_task", _plan_task)
    graph.add_node("run_playwright", _run_playwright)
    graph.add_node("summarize", _summarize)

    graph.set_entry_point("plan_task")
    graph.add_edge("plan_task", "run_playwright")
    graph.add_edge("run_playwright", "summarize")
    graph.set_finish_point("summarize")
    return graph


def run_browser_graph(prompt: str) -> dict:
    graph = build_browser_graph().compile()
    result = graph.invoke(
        {"prompt": prompt, "plan": BrowserPlan(steps=[]), "result": {}, "feedback": ""}
    )
    response = result["result"]
    if result["feedback"]:
        response["feedback"] = result["feedback"]
    return response


def run_browser_graph_stream(prompt: str, task_id: int):
    settings = Settings()
    planner = GeminiClient()
    plan = planner.plan_browser_task(prompt)
    attempt = 1

    plan_summary = planner.summarize_plan(prompt, plan)
    yield {"event": "plan", "data": {"summary": plan_summary}}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=not settings.playwright_headed, slow_mo=settings.playwright_slow_mo_ms
        )
        page = browser.new_page()

        step_results: list[dict] = []
        step_artifacts: list[dict] = []
        last_screenshot: str | None = None
        last_error = ""
        diagnosis = ""
        dom_snapshot = ""

        ACTIVE_SESSIONS[task_id] = SessionState(
            playwright=p,
            browser=browser,
            page=page,
            plan=plan,
            step_index=0,
            step_results=step_results,
            last_screenshot=last_screenshot,
            last_error=last_error,
            logs=[],
            dom_snapshot=dom_snapshot,
            stop_requested=False,
        )

        while attempt <= settings.planner_max_attempts:
            if ACTIVE_SESSIONS.get(task_id) and ACTIVE_SESSIONS[task_id].stop_requested:
                yield {"event": "stopped", "data": {"reason": "user_requested"}}
                break
            yield {"event": "attempt_start", "data": {"attempt": attempt}}
            for idx, step in enumerate(plan.steps):
                if ACTIVE_SESSIONS.get(task_id) and ACTIVE_SESSIONS[task_id].stop_requested:
                    yield {"event": "stopped", "data": {"reason": "user_requested"}}
                    break
                yield {"event": "step_start", "data": {"index": idx, "step": step.model_dump()}}
                ok, error, shot, failure_shot = _execute_step(
                    page, step, settings, [], step_results, step_artifacts
                )
                if shot:
                    last_screenshot = shot
                if not ok:
                    last_error = error
                    dom_snapshot = _capture_dom_snapshot(page, settings)
                    diagnosis = planner.diagnose_failure(
                        prompt=prompt,
                        previous_plan=plan,
                        error=last_error,
                        page_url=page.url,
                        page_title=page.title(),
                        step_results=step_results,
                        dom_snapshot=dom_snapshot,
                    )
                    yield {
                        "event": "step_error",
                        "data": {
                            "index": idx,
                            "error": last_error,
                            "diagnosis": diagnosis,
                            "dom_snapshot": dom_snapshot,
                            "step_results": step_results,
                            "failure_screenshot_base64": failure_shot,
                        },
                    }

                    if attempt < settings.planner_max_attempts:
                        plan = planner.replan_browser_task(
                            prompt=prompt,
                            previous_plan=plan,
                            error=last_error,
                            page_url=page.url,
                            page_title=page.title(),
                            step_results=step_results,
                            dom_snapshot=dom_snapshot,
                        )
                        attempt += 1
                        yield {"event": "replan", "data": plan.model_dump()}
                        break
                else:
                    yield {"event": "step_result", "data": {"index": idx}}
            else:
                # completed all steps
                title = page.title()
                result = {
                    "goal": plan.goal,
                    "title": title,
                }
                if last_screenshot:
                    result["screenshot_base64"] = last_screenshot
                if plan_summary:
                    result["plan_summary"] = plan_summary
                feedback = planner.summarize_execution(prompt, result)
                if feedback:
                    result["feedback"] = feedback
                yield {"event": "complete", "data": result}
                break

            if attempt > settings.planner_max_attempts:
                break

        if last_error:
            yield {
                "event": "error",
                "data": {
                    "error": last_error,
                    "diagnosis": diagnosis,
                    "plan_summary": plan_summary,
                },
            }

        browser.close()
        ACTIVE_SESSIONS.pop(task_id, None)
