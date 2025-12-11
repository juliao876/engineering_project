from pydantic import BaseModel
from typing import Dict, Any, List, Optional


class MetricsSchema(BaseModel):
    button_size: Dict[str, Any]
    button_spacing: Dict[str, Any]
    contrast_ratio: Dict[str, Any]
    font_size: Dict[str, Any]
    touch_target: Optional[Dict[str, Any]] = None
    layout_depth: Dict[str, Any]


class AnalysisResponseSchema(BaseModel):
    project_id: int
    device: str

    summary: str
    opinion: str
    recommendations: List[str]

    metrics: MetricsSchema
    issues: List[Dict[str, Any]]
