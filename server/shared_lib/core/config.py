from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    REDIS_HOST:str
    REDIS_PORT:str

    QDRANT_URL:str
    QDRANT_API_KEY:str | None = None
    QDRANT_COLLECTION:str
    LLM_API:str
    LLM_MODEL:str

    class Config:
        env_file = ".env"


settings = Settings()