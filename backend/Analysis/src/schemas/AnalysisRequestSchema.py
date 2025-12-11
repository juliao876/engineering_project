from pydantic import BaseModel, Field
from typing import Literal, Dict, Any, Optional


class AnalysisRequestSchema(BaseModel):
    device: Literal["desktop", "mobile"] = Field(..., description="Device type used for analysis")
    figma_url: Optional[str] = Field(
        default=None,
        description="Link to Figma file, e.g. https://www.figma.com/file/ABC123"
    )
    figma_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional raw Figma JSON payload (skips import from Figma service)"
    )
    token: Optional[str] = Field(
        default=None,
        description="User JWT token — required when using figma_url"
    )
