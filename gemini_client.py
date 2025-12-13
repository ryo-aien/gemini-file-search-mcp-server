import os
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from google import genai

load_dotenv()


class MissingApiKeyError(RuntimeError):
    """Raised when GEMINI_API_KEY is not configured."""


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise MissingApiKeyError(
            "GEMINI_API_KEY is not set. Please provide an API key to use the Gemini client."
        )
    return genai.Client(api_key=api_key)


def get_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise MissingApiKeyError(
            "GEMINI_API_KEY is not set. Please provide an API key to reach Gemini APIs."
        )
    return api_key


def get_base_url() -> str:
    return os.getenv("GENAI_BASE_URL", "https://generativelanguage.googleapis.com")
