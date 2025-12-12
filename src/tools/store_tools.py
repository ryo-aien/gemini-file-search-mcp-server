"""Store management tool handlers"""

import logging
from typing import Any

from ..gemini_client import GeminiClient
from ..models import (
    CreateStoreInput,
    ListStoresInput,
    DeleteStoreInput,
    ListStoresResult,
    DeleteResult,
)
from ..exceptions import GeminiFileSearchError

logger = logging.getLogger(__name__)


def handle_create_store(
    client: GeminiClient,
    arguments: dict[str, Any]
) -> dict[str, Any]:
    """
    Handle create_file_search_store tool call

    Args:
        client: Gemini client instance
        arguments: Tool arguments

    Returns:
        Store creation result
    """
    try:
        # Validate input
        input_data = CreateStoreInput(**arguments)

        # Create store
        store = client.create_store(
            display_name=input_data.display_name,
            description=input_data.description
        )

        return {
            "store_name": store.name,
            "display_name": store.display_name,
            "status": "ACTIVE",
            "created_at": store.created_at.isoformat(),
            "num_documents": store.num_documents,
            "storage_bytes": store.storage_bytes,
        }

    except GeminiFileSearchError as e:
        logger.error(f"Store creation failed: {e}")
        return {
            "error": str(e),
            "status": "FAILED"
        }
    except Exception as e:
        logger.error(f"Unexpected error in create_store: {e}")
        return {
            "error": f"Unexpected error: {e}",
            "status": "FAILED"
        }


def handle_list_stores(
    client: GeminiClient,
    arguments: dict[str, Any]
) -> dict[str, Any]:
    """
    Handle list_file_search_stores tool call

    Args:
        client: Gemini client instance
        arguments: Tool arguments

    Returns:
        List of stores
    """
    try:
        # Validate input
        input_data = ListStoresInput(**arguments)

        # List stores
        stores = client.list_stores(page_size=input_data.page_size)

        stores_list = [
            {
                "name": store.name,
                "display_name": store.display_name,
                "num_documents": store.num_documents,
                "num_active_documents": store.num_active_documents,
                "num_processing_documents": store.num_processing_documents,
                "num_failed_documents": store.num_failed_documents,
                "storage_bytes": store.storage_bytes,
                "created_at": store.created_at.isoformat(),
                "updated_at": store.updated_at.isoformat(),
            }
            for store in stores
        ]

        return {
            "stores": stores_list,
            "total_count": len(stores_list),
        }

    except GeminiFileSearchError as e:
        logger.error(f"List stores failed: {e}")
        return {
            "error": str(e),
            "stores": [],
            "total_count": 0,
        }
    except Exception as e:
        logger.error(f"Unexpected error in list_stores: {e}")
        return {
            "error": f"Unexpected error: {e}",
            "stores": [],
            "total_count": 0,
        }


def handle_delete_store(
    client: GeminiClient,
    arguments: dict[str, Any]
) -> dict[str, Any]:
    """
    Handle delete_file_search_store tool call

    Args:
        client: Gemini client instance
        arguments: Tool arguments

    Returns:
        Deletion result
    """
    try:
        # Validate input
        input_data = DeleteStoreInput(**arguments)

        # Delete store
        success = client.delete_store(input_data.store_name)

        return {
            "success": success,
            "message": f"Store {input_data.store_name} deleted successfully"
        }

    except GeminiFileSearchError as e:
        logger.error(f"Store deletion failed: {e}")
        return {
            "success": False,
            "message": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error in delete_store: {e}")
        return {
            "success": False,
            "message": f"Unexpected error: {e}"
        }
