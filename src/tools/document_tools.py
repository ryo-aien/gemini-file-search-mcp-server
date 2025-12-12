"""Document management tool handlers"""

import logging
from typing import Any

from ..gemini_client import GeminiClient
from ..models import (
    UploadFileInput,
    ListDocumentsInput,
    GetDocumentInput,
    DeleteDocumentInput,
)
from ..exceptions import GeminiFileSearchError

logger = logging.getLogger(__name__)


def handle_upload_file(
    client: GeminiClient,
    arguments: dict[str, Any]
) -> dict[str, Any]:
    """
    Handle upload_file_to_store tool call

    Args:
        client: Gemini client instance
        arguments: Tool arguments

    Returns:
        Upload result
    """
    try:
        # Validate input
        input_data = UploadFileInput(**arguments)

        # Upload file
        result = client.upload_file(
            store_name=input_data.store_name,
            file_path=input_data.file_path,
            display_name=input_data.display_name,
            metadata=input_data.metadata,
            chunking_config=input_data.chunking_config,
        )

        return {
            "document_name": result.document_name,
            "display_name": result.display_name,
            "status": result.status,
            "operation_name": result.operation_name,
            "file_size_bytes": result.file_size_bytes,
        }

    except GeminiFileSearchError as e:
        logger.error(f"File upload failed: {e}")
        return {
            "error": str(e),
            "status": "FAILED"
        }
    except Exception as e:
        logger.error(f"Unexpected error in upload_file: {e}")
        return {
            "error": f"Unexpected error: {e}",
            "status": "FAILED"
        }


def handle_list_documents(
    client: GeminiClient,
    arguments: dict[str, Any]
) -> dict[str, Any]:
    """
    Handle list_documents tool call

    Args:
        client: Gemini client instance
        arguments: Tool arguments

    Returns:
        List of documents
    """
    try:
        # Validate input
        input_data = ListDocumentsInput(**arguments)

        # List documents
        documents = client.list_documents(
            store_name=input_data.store_name,
            page_size=input_data.page_size
        )

        documents_list = [
            {
                "name": doc.name,
                "display_name": doc.display_name,
                "metadata": doc.metadata,
                "state": doc.state,
                "size_bytes": doc.size_bytes,
                "created_at": doc.created_at.isoformat(),
                "updated_at": doc.updated_at.isoformat(),
            }
            for doc in documents
        ]

        return {
            "documents": documents_list,
        }

    except GeminiFileSearchError as e:
        logger.error(f"List documents failed: {e}")
        return {
            "error": str(e),
            "documents": [],
        }
    except Exception as e:
        logger.error(f"Unexpected error in list_documents: {e}")
        return {
            "error": f"Unexpected error: {e}",
            "documents": [],
        }


def handle_get_document(
    client: GeminiClient,
    arguments: dict[str, Any]
) -> dict[str, Any]:
    """
    Handle get_document tool call

    Args:
        client: Gemini client instance
        arguments: Tool arguments

    Returns:
        Document information
    """
    try:
        # Validate input
        input_data = GetDocumentInput(**arguments)

        # Get document
        doc = client.get_document(input_data.document_name)

        return {
            "name": doc.name,
            "display_name": doc.display_name,
            "metadata": doc.metadata,
            "state": doc.state,
            "size_bytes": doc.size_bytes,
            "created_at": doc.created_at.isoformat(),
            "updated_at": doc.updated_at.isoformat(),
        }

    except GeminiFileSearchError as e:
        logger.error(f"Get document failed: {e}")
        return {
            "error": str(e),
        }
    except Exception as e:
        logger.error(f"Unexpected error in get_document: {e}")
        return {
            "error": f"Unexpected error: {e}",
        }


def handle_delete_document(
    client: GeminiClient,
    arguments: dict[str, Any]
) -> dict[str, Any]:
    """
    Handle delete_document tool call

    Args:
        client: Gemini client instance
        arguments: Tool arguments

    Returns:
        Deletion result
    """
    try:
        # Validate input
        input_data = DeleteDocumentInput(**arguments)

        # Delete document
        success = client.delete_document(input_data.document_name)

        return {
            "success": success,
            "message": f"Document {input_data.document_name} deleted successfully"
        }

    except GeminiFileSearchError as e:
        logger.error(f"Document deletion failed: {e}")
        return {
            "success": False,
            "message": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error in delete_document: {e}")
        return {
            "success": False,
            "message": f"Unexpected error: {e}"
        }
