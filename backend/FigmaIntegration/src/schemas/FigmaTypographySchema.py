from pydantic import BaseModel
from typing import Optional, List

class FigmaTypographySchema(BaseModel):
    total_text_nodes: Optional[int]
    avg_font_size: Optional[int]
    avg_line_height: Optional[float]
    dominant_colors: Optional[List[str]]
    color_contrast_ratio: Optional[float]