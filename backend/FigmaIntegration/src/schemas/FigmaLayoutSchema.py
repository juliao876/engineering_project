from pydantic import BaseModel
from typing import Optional, List

class FigmaLayoutSchema(BaseModel):
    total_frames: Optional[int]
    total_layers: Optional[int]
    layout_models: Optional[List[str]]
    avg_padding: Optional[float]
    avg_item_spacing: Optional[float]
    avg_spacing: Optional[float]
