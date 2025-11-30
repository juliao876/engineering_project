from pydantic import BaseModel
from datetime import datetime

class NotificationSchema(BaseModel):
    id: int
    type: str
    message: str
    is_read: bool
    created_at: datetime
