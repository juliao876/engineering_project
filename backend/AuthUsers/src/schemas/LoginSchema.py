from typing import Optional, Union
from pydantic import BaseModel, EmailStr


# class LoginType(BaseModel):
#     username: Optional[str] = None
#     email: Optional[EmailStr] = None
#
#
# class LoginSchema(BaseModel):
#     login: LoginType
#     password: str
class LoginSchema(BaseModel):
    login: Union[str, EmailStr]
    password: str