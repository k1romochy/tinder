from datetime import datetime, timedelta

import bcrypt
import jwt
from core.config import settings


def get_private_key() -> str:
    return settings.auth_jwt.private_key_path.read_text()


def get_public_key() -> str:
    return settings.auth_jwt.public_key_path.read_text()


def encode_jwt(
    payload: dict,
    private_key: str = None,
    algorithm: str = None,
    expire_minutes: int = None
):
    algorithm = algorithm or settings.auth_jwt.algorithm
    expire_minutes = expire_minutes or settings.auth_jwt.access_token_expire_minutes

    if private_key is None:
        private_key = get_private_key()

    to_encode = payload.copy()
    now = datetime.utcnow()
    expire = now + timedelta(minutes=expire_minutes)
    to_encode.update(exp=expire, iat=now)

    encoded = jwt.encode(to_encode, private_key, algorithm=algorithm)

    return encoded


def decode_jwt(
    token: str | bytes,
    public_key: str = None,
    algorithm: str = None
):
    algorithm = algorithm or settings.auth_jwt.algorithm

    if public_key is None:
        public_key = get_public_key()

    decoded = jwt.decode(token, public_key, algorithms=[algorithm])

    return decoded


def hash_password(password: str) -> bytes:
    salt = bcrypt.gensalt()
    pwd_bytes: bytes = password.encode()

    return bcrypt.hashpw(pwd_bytes, salt)


def validate_password(password: str, hashed_password: bytes) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password=hashed_password)