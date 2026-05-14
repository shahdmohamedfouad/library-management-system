# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60   # 1 ساعة

    class Config:
        env_file = ".env"   # لو هتستخدمي .env file بعدين

settings = Settings()
