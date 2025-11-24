from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session
import json
from src.schemas.AnalysisChecklistSchema import AnalysisChecklistSchema
from src.schemas.AnalysisResponseSchema import AnalysisResponseSchema
from src.services.Services import Services
from src.database.db_connection import get_db

analysis_router = APIRouter(prefix="/analysis", tags=["Analysis"])

@cbv(analysis_router)
class AnalysisEndpoints:

    @analysis_router.post("/{project_id}", response_model=AnalysisResponseSchema)
    def run_analysis(self, project_id: int):
        service = Services(self.db)
        result = service.run_analysis(project_id)
        return result

    @analysis_router.get("/{project_id}", response_model=AnalysisResponseSchema)
    def get_analysis(self, project_id: int):
        service = Services(self.db)
        result = service.get_analysis(project_id)

        if not result:
            raise HTTPException(status_code=404, detail="No analysis found for this project")

        return result

    @analysis_router.get("/checklist", response_model=AnalysisChecklistSchema)
    def get_checklist(self):
        service = Services(self.db)
        return service.get_checklist()