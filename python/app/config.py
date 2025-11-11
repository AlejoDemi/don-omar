import os
from dotenv import load_dotenv

# Load environment variables once at startup
load_dotenv()


def get_google_model_name() -> str:
    return os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")


def get_google_api_key() -> str:
    return os.getenv("GOOGLE_API_KEY", "")


