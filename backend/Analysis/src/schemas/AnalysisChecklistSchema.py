from pydantic import BaseModel
from typing import List, Dict, Any

class AnalysisChecklistSchema(BaseModel):
    categories: List[Dict[str, Any]]
