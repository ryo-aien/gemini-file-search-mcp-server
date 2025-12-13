import base64
import json
import os
import tempfile
from typing import Any, Dict, List, Optional

import httpx

from gemini_client import get_api_key, get_base_url

API_BASE = f"{get_base_url()}/v1beta"
UPLOAD_BASE = f"{get_base_url()}/upload/v1beta"


class MissingFileContentError(RuntimeError):
    """Raised when file content is unavailable for re-import."""


def _with_key(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = params or {}
    params["key"] = get_api_key()
    return params


def upload_file(
    store_name: str,
    file_bytes_base64: str,
    *,
    display_name: Optional[str] = None,
    mime_type: Optional[str] = None,
    chunking_config: Optional[Dict[str, Any]] = None,
    custom_metadata: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    file_bytes = base64.b64decode(file_bytes_base64)
    metadata: Dict[str, Any] = {}
    if display_name:
        metadata["displayName"] = display_name
    if mime_type:
        metadata["mimeType"] = mime_type
    if chunking_config:
        metadata["chunkingConfig"] = chunking_config
    if custom_metadata:
        metadata["customMetadata"] = custom_metadata

    params = {"uploadType": "multipart"}
    with httpx.Client(timeout=300) as client:
        files = {
            "metadata": ("metadata.json", json.dumps(metadata), "application/json"),
            "file": (display_name or "document", file_bytes, mime_type or "application/octet-stream"),
        }
        response = client.post(
            f"{UPLOAD_BASE}/{store_name}:uploadToFileSearchStore",
            params=_with_key(params),
            files=files,
        )
        response.raise_for_status()
        return response.json()


def import_file(
    store_name: str,
    file_name: str,
    *,
    display_name: Optional[str] = None,
    chunking_config: Optional[Dict[str, Any]] = None,
    custom_metadata: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"file": file_name}
    if display_name:
        payload["displayName"] = display_name
    if chunking_config:
        payload["chunkingConfig"] = chunking_config
    if custom_metadata:
        payload["customMetadata"] = custom_metadata

    with httpx.Client(timeout=60) as client:
        response = client.post(
            f"{API_BASE}/{store_name}:importFile",
            params=_with_key(),
            json=payload,
        )
        response.raise_for_status()
        return response.json()


def list_documents(store_name: str, page_size: Optional[int] = None, page_token: Optional[str] = None) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    if page_size:
        params["pageSize"] = page_size
    if page_token:
        params["pageToken"] = page_token

    with httpx.Client(timeout=60) as client:
        response = client.get(f"{API_BASE}/{store_name}/documents", params=_with_key(params))
        response.raise_for_status()
        return response.json()


def get_document(document_name: str) -> Dict[str, Any]:
    with httpx.Client(timeout=60) as client:
        response = client.get(f"{API_BASE}/{document_name}", params=_with_key())
        response.raise_for_status()
        return response.json()


def delete_document(document_name: str, force: bool = False) -> Dict[str, Any]:
    params = {"force": str(force).lower()}
    with httpx.Client(timeout=60) as client:
        response = client.delete(f"{API_BASE}/{document_name}", params=_with_key(params))
        response.raise_for_status()
        return {"deleted": True, "response": response.json() if response.content else None}


def update_metadata(
    document_name: str,
    *,
    new_custom_metadata: List[Dict[str, Any]],
    original_file_bytes_base64: Optional[str] = None,
    original_file_name: Optional[str] = None,
    store_name: Optional[str] = None,
    mime_type: Optional[str] = None,
    chunking_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    # Delete existing document
    delete_document(document_name, force=True)

    if not store_name:
        store_parts = document_name.split("/documents/")
        if len(store_parts) == 2:
            store_name = store_parts[0]

    if not store_name:
        raise MissingFileContentError("store_name could not be derived from document_name.")

    if original_file_bytes_base64:
        return upload_file(
            store_name=store_name,
            file_bytes_base64=original_file_bytes_base64,
            display_name=original_file_name,
            mime_type=mime_type,
            chunking_config=chunking_config,
            custom_metadata=new_custom_metadata,
        )

    raise MissingFileContentError(
        "original_file_bytes_base64 is required to re-import the document with new metadata."
    )
