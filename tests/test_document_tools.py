"""Tests for document management tools"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.gemini_client import GeminiClient
from src.tools.document_tools import (
    handle_upload_file,
    handle_list_documents,
    handle_get_document,
    handle_delete_document,
)
from src.models import Document, UploadResult


@pytest.fixture
def mock_client():
    """Create a mock Gemini client"""
    client = MagicMock(spec=GeminiClient)
    return client


@pytest.mark.asyncio
async def test_handle_upload_file_success(mock_client):
    """Test successful file upload"""
    # Mock the upload_file method
    mock_result = UploadResult(
        document_name="fileSearchStores/store1/documents/doc1",
        display_name="test.pdf",
        status="PROCESSING",
        operation_name="operations/op123",
        file_size_bytes=1024000,
    )
    mock_client.upload_file = AsyncMock(return_value=mock_result)

    # Call handler
    result = await handle_upload_file(
        mock_client,
        {
            "store_name": "fileSearchStores/store1",
            "file_path": "/path/to/test.pdf",
            "display_name": "test.pdf",
        }
    )

    # Verify result
    assert result["document_name"] == "fileSearchStores/store1/documents/doc1"
    assert result["display_name"] == "test.pdf"
    assert result["status"] == "PROCESSING"
    assert "error" not in result


@pytest.mark.asyncio
async def test_handle_list_documents_success(mock_client):
    """Test successful document listing"""
    # Mock the list_documents method
    mock_documents = [
        Document(
            name="fileSearchStores/store1/documents/doc1",
            display_name="Document 1",
            metadata={"category": "test"},
            state="ACTIVE",
            size_bytes=1024000,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        Document(
            name="fileSearchStores/store1/documents/doc2",
            display_name="Document 2",
            metadata={"category": "test"},
            state="ACTIVE",
            size_bytes=512000,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]
    mock_client.list_documents = AsyncMock(return_value=mock_documents)

    # Call handler
    result = await handle_list_documents(
        mock_client,
        {"store_name": "fileSearchStores/store1", "page_size": 10}
    )

    # Verify result
    assert len(result["documents"]) == 2
    assert result["documents"][0]["display_name"] == "Document 1"
    assert result["documents"][1]["display_name"] == "Document 2"
    assert "error" not in result


@pytest.mark.asyncio
async def test_handle_get_document_success(mock_client):
    """Test successful document retrieval"""
    # Mock the get_document method
    mock_document = Document(
        name="fileSearchStores/store1/documents/doc1",
        display_name="Test Document",
        metadata={"category": "test", "version": "1.0"},
        state="ACTIVE",
        size_bytes=1024000,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    mock_client.get_document = AsyncMock(return_value=mock_document)

    # Call handler
    result = await handle_get_document(
        mock_client,
        {"document_name": "fileSearchStores/store1/documents/doc1"}
    )

    # Verify result
    assert result["name"] == "fileSearchStores/store1/documents/doc1"
    assert result["display_name"] == "Test Document"
    assert result["state"] == "ACTIVE"
    assert result["metadata"]["category"] == "test"
    assert "error" not in result


@pytest.mark.asyncio
async def test_handle_delete_document_success(mock_client):
    """Test successful document deletion"""
    # Mock the delete_document method
    mock_client.delete_document = AsyncMock(return_value=True)

    # Call handler
    result = await handle_delete_document(
        mock_client,
        {"document_name": "fileSearchStores/store1/documents/doc1"}
    )

    # Verify result
    assert result["success"] is True
    assert "deleted successfully" in result["message"]

    # Verify client was called correctly
    mock_client.delete_document.assert_called_once_with(
        "fileSearchStores/store1/documents/doc1"
    )
