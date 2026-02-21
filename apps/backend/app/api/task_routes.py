from flask import Blueprint, g, request

from app.auth.clerk_middleware import clerk_required
from app.db.session import get_session
import json

from flask import Response, stream_with_context

from app.orchestration.browser_graph import run_browser_graph, run_browser_graph_stream
from app.orchestration.runtime.session_store import ACTIVE_SESSIONS
from app.schemas.task import TaskCreate, TaskRead
from app.services.task_service import TaskService

task_bp = Blueprint("tasks", __name__)


@task_bp.get("")
@clerk_required
def list_tasks():
    session = next(get_session())
    try:
        service = TaskService(session)
        tasks = service.list_tasks(g.current_user.id)
        return [TaskRead.model_validate(task).model_dump() for task in tasks]
    finally:
        session.close()


@task_bp.get("/<int:task_id>")
@clerk_required
def get_task(task_id: int):
    session = next(get_session())
    try:
        service = TaskService(session)
        task = service.get_task(task_id, g.current_user.id)
        if not task:
            return {"error": "Task not found"}, 404
        return TaskRead.model_validate(task).model_dump()
    finally:
        session.close()


@task_bp.post("/run")
@clerk_required
def run_task():
    payload = TaskCreate(**request.get_json(force=True))
    session = next(get_session())
    try:
        service = TaskService(session)
        task = service.create_task(g.current_user.id, payload.prompt)
        try:
            result = run_browser_graph(payload.prompt)
            if isinstance(result, dict) and result.get("error"):
                task = service.fail_task(task.id, str(result.get("error")))
                return TaskRead.model_validate(task).model_dump(), 400
            task = service.complete_task(task.id, result)
        except Exception as exc:  # noqa: BLE001
            task = service.fail_task(task.id, str(exc))
            return TaskRead.model_validate(task).model_dump(), 500
        return TaskRead.model_validate(task).model_dump()
    finally:
        session.close()

@task_bp.post("/stream")
@clerk_required
def stream_task():
    payload = TaskCreate(**request.get_json(force=True))
    session = next(get_session())
    service = TaskService(session)
    task = service.create_task(g.current_user.id, payload.prompt)

    def generate():
        try:
            yield "event: task\n"
            yield f"data: {json.dumps({'task_id': task.id})}\n\n"
            for event in run_browser_graph_stream(payload.prompt, task.id):
                if event["event"] == "complete":
                    service.complete_task(task.id, event["data"])
                if event["event"] == "error":
                    service.fail_task(task.id, event["data"].get("error", "Unknown error"))
                yield f"event: {event['event']}\n"
                yield f"data: {json.dumps(event['data'])}\n\n"
        finally:
            session.close()

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@task_bp.post("/stop/<int:task_id>")
@clerk_required
def stop_task(task_id: int):
    session_state = ACTIVE_SESSIONS.get(task_id)
    if not session_state:
        return {"error": "Task session not found"}, 404
    session_state.stop_requested = True
    return {"status": "stopping"}
