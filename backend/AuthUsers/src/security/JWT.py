from jwt import encode
from datetime import datetime, timedelta

SECRET_KEY = "secretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

def create_jwt_token(data: dict):
    to_encode = data.copy()
    expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expires})
    encode_jwt = encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encode_jwt