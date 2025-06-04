import os
from dotenv import load_dotenv
from pymongo import MongoClient
import openai

load_dotenv()

token = os.getenv("DISCORD_TOKEN")

# Load environment variables
WEATHER_API = os.getenv("WEATHER_API")
API_NINJA = os.getenv("API_NINJA")
GIPHY_API = os.getenv("GIPHY_API")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CAT_API_KEY = os.getenv("CAT_API_KEY")
DOG_API_KEY = os.getenv("DOG_API_KEY")
PIXABAY_API = os.getenv("PIXABAY_API")
DEV_API_KEY = os.getenv("DEV_API_KEY")

mongo_uri = os.getenv("MONGO_CONNECTION")

# Create clients
mongo_client = MongoClient(mongo_uri)
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Export these
__all__ = ["mongo_client",
           "openai_client",
           "WEATHER_API",
           "API_NINJA",
           "GIPHY_API",
           "CAT_API_KEY",
           "PIXABAY_API",
           "DEV_API_KEY",
           "token",
           "DOG_API_KEY"
           ]
