from dotenv import load_dotenv
import os
from pathlib import Path

from pydantic_settings import BaseSettings

load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent


class AuthJWT:
    private_key_path = BASE_DIR / 'auth' / 'jwt-private.pem'
    public_key_path = BASE_DIR / 'auth' / 'jwt-public.pem'
    algorithm: str = 'RS256'
    access_token_expire_minutes: int = 15


class Settings(BaseSettings):
    db_url: str = os.getenv('POSTGRES_URL')
    SECRET_KEY: str = os.getenv('SECRET_KEY')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    auth_jwt: AuthJWT = AuthJWT()


settings = Settings()
