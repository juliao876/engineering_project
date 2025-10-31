from fastapi import HTTPException, Response
from pip._internal.network.auth import Credentials
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from starlette import status




class Services:
    def __init__(self, db: Session):
        self.db = db
