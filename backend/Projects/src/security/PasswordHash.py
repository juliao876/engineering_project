from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

def hash_password(password: str) -> str:
    return PasswordHasher().hash(password)

def password_verify(password: str, hashed_password: str) -> bool:
    try:
        return PasswordHasher().verify(hashed_password, password)
    except (VerifyMismatchError, InvalidHashError):
        return False