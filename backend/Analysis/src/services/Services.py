from fastapi import HTTPException, Response, requests
from pip._internal.network.auth import Credentials
from sqlalchemy.orm import Session
import os


FIGMA_SERVICE_URL = os.getenv("FIGMA_SERVICE_URL", "http://localhost:6702/api/v1")

class Services:
    def __init__(self, db: Session):
        self.db = db

