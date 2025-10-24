import requests
from dotenv import load_dotenv
import os

# Load env variables from .env file if needed
load_dotenv()

FARM_EMAIL = os.getenv("FARM_EMAIL")
FARM_PASSWORD = os.getenv("FARM_PASSWORD")

BASE_URL = os.getenv("BASE_URL")

def login_and_get_token(email, password):
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": password
    })
    resp.raise_for_status()
    return resp.json().get("token")


