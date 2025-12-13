from collections import Counter
from typing import Any, Dict, List, Optional

import httpx

from gemini_client import get_api_key, get_base_url
from tools import document_tools

API_BASE = f"{get_base_url()}/v1beta"

SUPPORTED_MIME_TYPES: Dict[str, List[str]] = {
    "application": [
        "application/pdf",
        "application/json",
        "application/msword",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/zip",
        "application/x-tar",
    ],
    "text": [
        "text/plain",
        "text/markdown",
        "text/csv",
        "text/html",
        "text/yaml",
        "text/x-python",
        "text/x-go",
        "text/x-java",
    ],
}


def _with_key(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = params or {}
    params["key"] = get_api_key()
    return params


def get_operation_status(operation_name: str) -> Dict[str, Any]:
    with httpx.Client(timeout=60) as client:
        response = client.get(f"{API_BASE}/{operation_name}", params=_with_key())
        response.raise_for_status()
        return response.json()


def list_supported_formats() -> Dict[str, Any]:
    return {"supported_mime_types": SUPPORTED_MIME_TYPES}


def get_store_statistics(store_name: str) -> Dict[str, Any]:
    page_token: Optional[str] = None
    document_count = 0
    total_size_bytes = 0
    states_counter: Counter[str] = Counter()

    while True:
        page = document_tools.list_documents(store_name, page_size=100, page_token=page_token)
        documents = page.get("documents", [])
        document_count += len(documents)
        for doc in documents:
            size_bytes = doc.get("sizeBytes")
            if isinstance(size_bytes, int):
                total_size_bytes += size_bytes
            state = doc.get("state")
            if state:
                states_counter[state] += 1
        page_token = page.get("nextPageToken")
        if not page_token:
            break

    return {
        "document_count": document_count,
        "total_size_bytes": total_size_bytes,
        "states_breakdown": dict(states_counter),
    }
