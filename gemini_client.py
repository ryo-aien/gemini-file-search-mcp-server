"""Gemini API クライアントのシングルトン管理."""
import os
import logging
from typing import Optional
from google import genai

logger = logging.getLogger(__name__)

_client: Optional[genai.Client] = None


def get_client() -> genai.Client:
    """
    Gemini API クライアントのシングルトンインスタンスを取得する.

    環境変数 GEMINI_API_KEY が必須.

    Returns:
        genai.Client: Gemini API クライアント

    Raises:
        ValueError: GEMINI_API_KEY が設定されていない場合
    """
    global _client

    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        _client = genai.Client(api_key=api_key)
        logger.info("Gemini API client initialized")

    return _client


def reset_client() -> None:
    """
    クライアントをリセットする（テスト用）.
    """
    global _client
    _client = None
