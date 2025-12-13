from typing import Any, Dict, Optional

import httpx

from gemini_client import get_api_key, get_base_url

API_BASE = f"{get_base_url()}/v1beta"


def _with_key(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = params or {}
    params["key"] = get_api_key()
    return params


def create_store(display_name: Optional[str] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    if display_name:
        payload["displayName"] = display_name

    with httpx.Client(timeout=60) as client:
        response = client.post(
            f"{API_BASE}/fileSearchStores",
            params=_with_key(),
            json=payload,
        )
        response.raise_for_status()
        return response.json()


def list_stores(page_size: Optional[int] = None, page_token: Optional[str] = None) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    if page_size:
        params["pageSize"] = page_size
    if page_token:
        params["pageToken"] = page_token

    with httpx.Client(timeout=60) as client:
        response = client.get(f"{API_BASE}/fileSearchStores", params=_with_key(params))
        response.raise_for_status()
        return response.json()


def get_store(store_name: str) -> Dict[str, Any]:
    with httpx.Client(timeout=60) as client:
        response = client.get(f"{API_BASE}/{store_name}", params=_with_key())
        response.raise_for_status()
        return response.json()


def delete_store(store_name: str, force: bool = False) -> Dict[str, Any]:
    params = {"force": str(force).lower()}
    with httpx.Client(timeout=60) as client:
        response = client.delete(f"{API_BASE}/{store_name}", params=_with_key(params))
        response.raise_for_status()
        return {"deleted": True, "response": response.json() if response.content else None}
