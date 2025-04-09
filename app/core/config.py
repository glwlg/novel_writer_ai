import os

from pydantic import computed_field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件


class Settings(BaseSettings):
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "")
    POSTGRES_HOST_PORT: str = os.getenv("POSTGRES_HOST_PORT", "")
    LLM_API_BASE: str = os.getenv("LLM_API_BASE", "")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "")
    EMBED_API_BASE: str = os.getenv("EMBED_API_BASE", LLM_API_BASE)
    EMBED_API_KEY: str = os.getenv("EMBED_API_KEY", LLM_API_KEY)
    EMBED_MODEL: str = os.getenv("EMBED_MODEL", "")
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:3333")

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_HOST_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


settings = Settings()
