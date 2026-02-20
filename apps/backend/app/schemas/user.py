from datetime import datetime
from pydantic import BaseModel


class UserRead(BaseModel):
    id: int
    clerk_user_id: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}
