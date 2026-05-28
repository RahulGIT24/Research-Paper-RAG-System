from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    NOTION_CLIENT_ID: str
    NOTION_CLIENT_SECRET: str
    NOTION_REDIRECT_URI: str

    class Config:
        env_file = ".env"


settings = Settings()