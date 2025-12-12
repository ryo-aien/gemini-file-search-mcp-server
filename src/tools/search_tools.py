"""Search tool handlers"""

import logging
from typing import Any

from ..gemini_client import GeminiClient
from ..models import SearchInput
from ..exceptions import GeminiFileSearchError

logger = logging.getLogger(__name__)


def handle_search_documents(
    client: GeminiClient,
    arguments: dict[str, Any]
) -> dict[str, Any]:
    """
    Handle search_documents tool call

    Args:
        client: Gemini client instance
        arguments: Tool arguments

    Returns:
        Search results with response and citations
    """
    try:
        # Validate input
        input_data = SearchInput(**arguments)

        # Perform search
        result = client.search(
            store_names=input_data.store_names,
            query=input_data.query,
            model=input_data.model,
            metadata_filter=input_data.metadata_filter,
            max_results=input_data.max_results,
        )

        # Format citations
        citations_list = [
            {
                "source": citation.source,
                "snippet": citation.snippet,
                "metadata": citation.metadata,
            }
            for citation in result.citations
        ]

        return {
            "response": result.response,
            "citations": citations_list,
            "grounding_metadata": result.grounding_metadata,
            "num_citations": len(citations_list),
        }

    except GeminiFileSearchError as e:
        logger.error(f"Search failed: {e}")
        return {
            "error": str(e),
            "response": "",
            "citations": [],
            "grounding_metadata": {},
            "num_citations": 0,
        }
    except Exception as e:
        logger.error(f"Unexpected error in search_documents: {e}")
        return {
            "error": f"Unexpected error: {e}",
            "response": "",
            "citations": [],
            "grounding_metadata": {},
            "num_citations": 0,
        }
