from pydantic import BaseModel
from typing import Optional

class CommentSchema(BaseModel):
    content: str
class ReplySchema(BaseModel):
    content: str