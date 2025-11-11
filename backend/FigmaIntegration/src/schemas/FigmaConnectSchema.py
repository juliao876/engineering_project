from pydantic import BaseModel

class FigmaConnectSchema(BaseModel):
    code:str

    class Config:
        from_attributes = True