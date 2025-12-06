from pydantic import BaseModel


class FigmaConnectSchema(BaseModel):
    code: str
    state: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    redirect_uri: str | None = None

    class Config:
        from_attributes = True