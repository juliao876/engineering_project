from pydantic import BaseModel

class RatingSchema(BaseModel):
    project_id: int
    average_rating: float
    total_ratings: int
