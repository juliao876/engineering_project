from pydantic import BaseModel, Field


class RatingSchema(BaseModel):
    value: int = Field(..., ge=1, le=5)