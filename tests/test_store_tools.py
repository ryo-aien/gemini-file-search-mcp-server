"""Tests for store management tools"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.gemini_client import GeminiClient
from src.tools.store_tools import (
    handle_create_store,
    handle_list_stores,
    handle_delete_store,
)
from src.models import Store


@pytest.fixture
def mock_client():
    """Create a mock Gemini client"""
    client = MagicMock(spec=GeminiClient)
    return client


@pytest.mark.asyncio
async def test_handle_create_store_success(mock_client):
    """Test successful store creation"""
    # Mock the create_store method
    mock_store = Store(
        name="fileSearchStores/test123",
        display_name="Test Store",
        num_documents=0,
        num_active_documents=0,
        num_processing_documents=0,
        num_failed_documents=0,
        storage_bytes=0,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    mock_client.create_store = AsyncMock(return_value=mock_store)

    # Call handler
    result = await handle_create_store(
        mock_client,
        {"display_name": "Test Store", "description": "Test description"}
    )

    # Verify result
    assert result["store_name"] == "fileSearchStores/test123"
    assert result["display_name"] == "Test Store"
    assert result["status"] == "ACTIVE"
    assert "error" not in result

    # Verify client was called correctly
    mock_client.create_store.assert_called_once_with(
        display_name="Test Store",
        description="Test description"
    )


@pytest.mark.asyncio
async def test_handle_create_store_error(mock_client):
    """Test store creation with error"""
    # Mock an error
    mock_client.create_store = AsyncMock(side_effect=Exception("API Error"))

    # Call handler
    result = await handle_create_store(
        mock_client,
        {"display_name": "Test Store"}
    )

    # Verify error handling
    assert "error" in result
    assert result["status"] == "FAILED"


@pytest.mark.asyncio
async def test_handle_list_stores_success(mock_client):
    """Test successful store listing"""
    # Mock the list_stores method
    mock_stores = [
        Store(
            name="fileSearchStores/store1",
            display_name="Store 1",
            num_documents=5,
            num_active_documents=5,
            num_processing_documents=0,
            num_failed_documents=0,
            storage_bytes=1024000,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        Store(
            name="fileSearchStores/store2",
            display_name="Store 2",
            num_documents=3,
            num_active_documents=3,
            num_processing_documents=0,
            num_failed_documents=0,
            storage_bytes=512000,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]
    mock_client.list_stores = AsyncMock(return_value=mock_stores)

    # Call handler
    result = await handle_list_stores(mock_client, {"page_size": 10})

    # Verify result
    assert result["total_count"] == 2
    assert len(result["stores"]) == 2
    assert result["stores"][0]["display_name"] == "Store 1"
    assert result["stores"][1]["display_name"] == "Store 2"
    assert "error" not in result


@pytest.mark.asyncio
async def test_handle_delete_store_success(mock_client):
    """Test successful store deletion"""
    # Mock the delete_store method
    mock_client.delete_store = AsyncMock(return_value=True)

    # Call handler
    result = await handle_delete_store(
        mock_client,
        {"store_name": "fileSearchStores/test123"}
    )

    # Verify result
    assert result["success"] is True
    assert "deleted successfully" in result["message"]

    # Verify client was called correctly
    mock_client.delete_store.assert_called_once_with("fileSearchStores/test123")


@pytest.mark.asyncio
async def test_handle_delete_store_error(mock_client):
    """Test store deletion with error"""
    # Mock an error
    mock_client.delete_store = AsyncMock(side_effect=Exception("Store not found"))

    # Call handler
    result = await handle_delete_store(
        mock_client,
        {"store_name": "fileSearchStores/invalid"}
    )

    # Verify error handling
    assert result["success"] is False
    assert "error" in result["message"].lower() or "not found" in result["message"].lower()
