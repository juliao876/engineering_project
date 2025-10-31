import jwt
from fastapi import APIRouter, Depends, Response, Request, HTTPException
from fastapi_utils.cbv import cbv
from sqlalchemy.sql.coercions import expect

project_router = APIRouter(prefix="/project", tags=["Projects"])