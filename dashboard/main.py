import os
import uvicorn
from fastapi import FastAPI, Request
from starlette.responses import RedirectResponse
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
import subprocess
from starlette.middleware.sessions import SessionMiddleware

load_dotenv()

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/callback"
API_BASE_URL = "https://discord.com/api"
AUTHORIZATION_BASE_URL = API_BASE_URL + "/oauth2/authorize"
TOKEN_URL = API_BASE_URL + "/oauth2/token"
SCOPE = ["identify", "email", "guilds"]

app = FastAPI()

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key="some-random-secret")

@app.on_event("startup")
async def startup_event():
    subprocess.Popen(["streamlit", "run", "/Volumes/External SSD/Coding/python/discord bot/Nexa/dashboard/pages/home.py"])

@app.get("/")
async def root(request: Request):
    if 'user' in request.session:
        return {"message": f"Welcome {request.session['user']['username']}"}
    return {"message": "Dashboard is running. Please login."}

@app.get("/login")
async def login():
    discord = OAuth2Session(DISCORD_CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE)
    authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
    return RedirectResponse(authorization_url)

@app.get("/callback")
async def callback(request: Request):
    discord = OAuth2Session(DISCORD_CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE, state=request.query_params.get("state"))
    token = discord.fetch_token(
        TOKEN_URL,
        client_secret=DISCORD_CLIENT_SECRET,
        authorization_response=str(request.url)
    )
    user_response = discord.get(API_BASE_URL + "/users/@me")
    user_data = user_response.json()
    request.session['user'] = user_data
    request.session['oauth2_token'] = token
    # Redirect to the streamlit app
    return RedirectResponse(url="http://localhost:8501")


@app.get("/logout")
async def logout(request: Request):
    request.session.pop('user', None)
    request.session.pop('oauth2_token', None)
    return RedirectResponse(url="/")

# This is the new dashboard page that will be shown after login
@app.get("/dashboard")
async def dashboard_page(request: Request):
    if 'user' not in request.session:
        return RedirectResponse(url="/login")
    # This will be handled by streamlit, but we need a placeholder
    return {"message": "Welcome to the dashboard"}


def run_dashboard():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    run_dashboard()