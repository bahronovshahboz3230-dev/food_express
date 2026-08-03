from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_ID: int
    DATABASE_URL: str = "sqlite+aiosqlite:///food_express.db"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
