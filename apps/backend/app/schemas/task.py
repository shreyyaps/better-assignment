from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    prompt: str


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt: str
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
