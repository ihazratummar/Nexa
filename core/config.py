from loguru import logger
from pydantic_settings import BaseSettings
from dotenv import  load_dotenv

load_dotenv()

class Settings(BaseSettings):
    discord_token: str
    pixabay_api: str
    api_ninja: str
    giphy_api: str
    cat_api_key: str
    dog_api_key:str
    mongo_connection: str
    database_name: str
    perspective_api_key: str
    sightengine_api_user: str
    sightengine_api_secret: str
    openai_api_key: str

    class Config:
        env_file = ".env"
        case_sensitive = False

try:
    settings = Settings()
except Exception as e:
    logger.error(f"Failed to load settings: {e}")









