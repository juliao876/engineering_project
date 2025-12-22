from pydantic import BaseModel

class RoleSchema(BaseModel):
    role: str