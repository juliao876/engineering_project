from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class AnalysisResponseSchema(BaseModel):
    project_id: int
    summary: str
    issues: List[Dict[str, Any]]
    opinion: str
    recommendations: List[str]
