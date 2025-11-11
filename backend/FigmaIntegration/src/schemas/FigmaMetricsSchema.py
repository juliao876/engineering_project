from pydantic import BaseModel
from typing import Optional, List
from src.schemas.FigmaLayoutSchema import FigmaLayoutSchema
from src.schemas.FigmaTypographySchema import FigmaTypographySchema

class FigmaMetricsSchema(FigmaLayoutSchema, FigmaTypographySchema):
    total_buttons: Optional[int]
    avg_buttons_size: Optional[int]