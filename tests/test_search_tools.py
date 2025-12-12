"""Tests for search tools"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.gemini_client import GeminiClient
from src.tools.search_tools import handle_search_documents
from src.models import SearchResult, Citation


@pytest.fixture
def mock_client():
    """Create a mock Gemini client"""
    client = MagicMock(spec=GeminiClient)
    return client


@pytest.mark.asyncio
async def test_handle_search_documents_success(mock_client):
    """Test successful document search"""
    # Mock the search method
    mock_citations = [
        Citation(
            source="fileSearchStores/store1/documents/doc1",
            snippet="This is a relevant snippet from the document.",
            metadata={"category": "documentation"},
        ),
        Citation(
            source="fileSearchStores/store1/documents/doc2",
            snippet="Another relevant snippet.",
            metadata={"category": "guide"},
        ),
    ]

    mock_result = SearchResult(
        response="Based on the documents, here is the answer to your question...",
        citations=mock_citations,
        grounding_metadata={"search_quality": "high"},
    )

    mock_client.search = AsyncMock(return_value=mock_result)

    # Call handler
    result = await handle_search_documents(
        mock_client,
        {
            "store_names": ["fileSearchStores/store1"],
            "query": "What is the answer?",
            "model": "gemini-2.0-flash-exp",
            "max_results": 10,
        }
    )

    # Verify result
    assert result["response"] == "Based on the documents, here is the answer to your question..."
    assert result["num_citations"] == 2
    assert len(result["citations"]) == 2
    assert result["citations"][0]["source"] == "fileSearchStores/store1/documents/doc1"
    assert "error" not in result

    # Verify client was called correctly
    mock_client.search.assert_called_once()


@pytest.mark.asyncio
async def test_handle_search_documents_no_results(mock_client):
    """Test search with no results"""
    # Mock the search method with empty results
    mock_result = SearchResult(
        response="No relevant information found.",
        citations=[],
        grounding_metadata={},
    )

    mock_client.search = AsyncMock(return_value=mock_result)

    # Call handler
    result = await handle_search_documents(
        mock_client,
        {
            "store_names": ["fileSearchStores/store1"],
            "query": "Non-existent topic",
        }
    )

    # Verify result
    assert result["response"] == "No relevant information found."
    assert result["num_citations"] == 0
    assert len(result["citations"]) == 0
    assert "error" not in result


@pytest.mark.asyncio
async def test_handle_search_documents_error(mock_client):
    """Test search with error"""
    # Mock an error
    mock_client.search = AsyncMock(side_effect=Exception("Search API Error"))

    # Call handler
    result = await handle_search_documents(
        mock_client,
        {
            "store_names": ["fileSearchStores/store1"],
            "query": "Test query",
        }
    )

    # Verify error handling
    assert "error" in result
    assert result["num_citations"] == 0
    assert result["response"] == ""


@pytest.mark.asyncio
async def test_handle_search_documents_with_metadata_filter(mock_client):
    """Test search with metadata filter"""
    # Mock the search method
    mock_result = SearchResult(
        response="Filtered results",
        citations=[
            Citation(
                source="fileSearchStores/store1/documents/doc1",
                snippet="Filtered content",
                metadata={"category": "documentation"},
            )
        ],
        grounding_metadata={},
    )

    mock_client.search = AsyncMock(return_value=mock_result)

    # Call handler with metadata filter
    result = await handle_search_documents(
        mock_client,
        {
            "store_names": ["fileSearchStores/store1"],
            "query": "Test query",
            "metadata_filter": 'category="documentation"',
        }
    )

    # Verify result
    assert result["num_citations"] == 1
    assert result["citations"][0]["metadata"]["category"] == "documentation"

    # Verify client was called with metadata filter
    call_args = mock_client.search.call_args
    assert call_args.kwargs["metadata_filter"] == 'category="documentation"'
