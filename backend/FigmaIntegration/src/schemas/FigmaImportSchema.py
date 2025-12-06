from pydantic import BaseModel


class FigmaImportSchema(BaseModel):
    file_url: str

    class Config:
        from_attributes = True