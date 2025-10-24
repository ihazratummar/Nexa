import os
import pytz
import openai
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

token = os.getenv("DISCORD_TOKEN")

TIMEZONE = pytz.timezone("Asia/Kolkata")

# Load environment variables
WEATHER_API = os.getenv("WEATHER_API")
API_NINJA = os.getenv("API_NINJA")
GIPHY_API = os.getenv("GIPHY_API")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CAT_API_KEY = os.getenv("CAT_API_KEY")
DOG_API_KEY = os.getenv("DOG_API_KEY")
PIXABAY_API = os.getenv("PIXABAY_API")

mongo_uri = os.getenv("MONGO_CONNECTION")

# Create clients
mongo_client = AsyncIOMotorClient(mongo_uri)
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Export these
__all__ = ["mongo_client",
           "openai_client",
           "WEATHER_API",
           "API_NINJA",
           "GIPHY_API",
           "CAT_API_KEY",
           "PIXABAY_API",
           "token",
           "DOG_API_KEY",
           TIMEZONE
           ]
