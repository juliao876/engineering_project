from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Analysis(SQLModel, table=True):
    __tablename__ = "analysis"


    id: Optional[int] = Field(default=None, primary_key=True)

    analysis_id: str = Field(index=True)
    project_id: str = Field(index=True)

    status: str = Field(default="processing")

    results_json: Optional[str] = Field(default=None)
    raw_data: Optional[str] = Field(default=None)

    summary: Optional[str] = Field(default=None)
    opinion: Optional[str] = Field(default=None)
    recomendation: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
