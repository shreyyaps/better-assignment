from sqlalchemy.orm import Session

from app.models.task import Task


class TaskService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_task(self, user_id: int, prompt: str) -> Task:
        task = Task(user_id=user_id, prompt=prompt, status="running")
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def complete_task(self, task_id: int, result: dict) -> Task:
        task = self.session.get(Task, task_id)
        if task is None:
            raise ValueError("Task not found")
        task.status = "completed"
        task.result = result
        task.error = None
        self.session.commit()
        self.session.refresh(task)
        return task

    def fail_task(self, task_id: int, error: str) -> Task:
        task = self.session.get(Task, task_id)
        if task is None:
            raise ValueError("Task not found")
        task.status = "failed"
        task.error = error
        self.session.commit()
        self.session.refresh(task)
        return task

    def list_tasks(self, user_id: int) -> list[Task]:
        return (
            self.session.query(Task)
            .filter(Task.user_id == user_id)
            .order_by(Task.created_at.desc())
            .all()
        )

    def get_task(self, task_id: int, user_id: int) -> Task | None:
        return (
            self.session.query(Task)
            .filter(Task.id == task_id, Task.user_id == user_id)
            .first()
        )
