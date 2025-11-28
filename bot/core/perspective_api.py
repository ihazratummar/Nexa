import logging
from typing import Any, Coroutine

import aiohttp
import os
import dotenv


dotenv.load_dotenv()

PERSPECTIVE_API_KEY = os.getenv("PERSPECTIVE_API_KEY")
PERSPECTIVE_API_URL = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"
SIGHTENGINE_API_USER = os.getenv("SIGHTENGINE_API_USER")
SIGHTENGINE_API_SECRET = os.getenv("SIGHTENGINE_API_SECRET")

SIGHTENGINE_MODELS = 'nudity-2.1,alcohol,recreational_drug,medical,text-content,face-attributes,gore-2.0,violence,self-harm'

async def analyze_comment(comment: str) -> float | Any:
    payload = {
        "comment":{"text": comment},
        "languages": ["en"],
        "requestedAttributes": {
            "TOXICITY": {}, "SEXUALLY_EXPLICIT": {}, "PROFANITY": {},  "FLIRTATION": {}, "INSULT": {},  "IDENTITY_ATTACK": {}, "THREAT": {}
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{PERSPECTIVE_API_URL}?key={PERSPECTIVE_API_KEY}", json= payload) as response:
            if response.status != 200:
                logging.error(f"[PERSPECTIVE ERROR STATUS] : {response.status}")
                return 0.0
            data = await response.json()
            return data["attributeScores"]["TOXICITY"]["summaryScore"]["value"]
        return None
    return None


async def check_image_content(image_url: str) -> Any:
    """
    Sends the image to Sightengine and returns a dictionary of key risks and their scores.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.sightengine.com/1.0/check.json",
            params={
                "url": image_url,
                "models": 'nudity-2.1,weapon,alcohol,recreational_drug,medical,gore-2.0,face-attributes,qr-content,text-content,offensive-2.0,tobacco,gambling,self-harm',
                "api_user": SIGHTENGINE_API_USER,
                "api_secret": SIGHTENGINE_API_SECRET,
            },
        ) as resp:
            return await resp.json()
        return None
    return None


async def check_video_content(video_url: str) -> Any:
    """
    Sends the video to Sightengine and returns a dictionary of key risks and their scores.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.sightengine.com/1.0/video/check.json",
            params={
                "callback_url": video_url,
                "models": SIGHTENGINE_MODELS,
                "api_user": SIGHTENGINE_API_USER,
                "api_secret": SIGHTENGINE_API_SECRET,
            },
        ) as resp:
            return await resp.json()
        return None
    return None


def extract_scores(data):
    flagged = []

    # Only check these top-level keys from the response
    relevant_keys = ["nudity", "gore", "violence", "self-harm", "medical", "alcohol", "recreational_drug"]

    def deep_check(d, path=""):
        for k, v in d.items():
            if k in ["none", "safe", "context", "suggestive_classes", "cleavage_categories", "male_chest_categories"]:
                continue
            current_path = f"{path}.{k}" if path else k
            if isinstance(v, dict):
                deep_check(v, current_path)
            elif isinstance(v, (int, float)) and v > 0.45:
                flagged.append((current_path, v))

    for key in relevant_keys:
        section = data.get(key)
        if section:
            deep_check(section, key)

    return flagged
