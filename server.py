import asyncio
import logging
import os
from typing import Any, Dict, Optional

from fastmcp import FastMCP

from tools import document_tools, search_tools, store_tools, util_tools

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

mcp = FastMCP("Gemini File Search MCP")


@mcp.tool()
def create_store(display_name: Optional[str] = None) -> Dict[str, Any]:
    """Create a new File Search store."""
    return store_tools.create_store(display_name=display_name)


@mcp.tool()
def list_stores(page_size: Optional[int] = None, page_token: Optional[str] = None) -> Dict[str, Any]:
    """List File Search stores."""
    return store_tools.list_stores(page_size=page_size, page_token=page_token)


@mcp.tool()
def get_store(store_name: str) -> Dict[str, Any]:
    """Get information about a File Search store."""
    return store_tools.get_store(store_name)


@mcp.tool()
def delete_store(store_name: str, force: bool = False) -> Dict[str, Any]:
    """Delete a File Search store."""
    return store_tools.delete_store(store_name, force=force)


@mcp.tool()
def upload_file(
    store_name: str,
    file_bytes_base64: str,
    display_name: Optional[str] = None,
    mime_type: Optional[str] = None,
    chunking_config: Optional[Dict[str, Any]] = None,
    custom_metadata: Optional[list] = None,
) -> Dict[str, Any]:
    """Upload a file directly to a File Search store."""
    return document_tools.upload_file(
        store_name,
        file_bytes_base64,
        display_name=display_name,
        mime_type=mime_type,
        chunking_config=chunking_config,
        custom_metadata=custom_metadata,
    )


@mcp.tool()
def import_file(
    store_name: str,
    file_name: str,
    display_name: Optional[str] = None,
    chunking_config: Optional[Dict[str, Any]] = None,
    custom_metadata: Optional[list] = None,
) -> Dict[str, Any]:
    """Import a Files API file into a File Search store."""
    return document_tools.import_file(
        store_name,
        file_name,
        display_name=display_name,
        chunking_config=chunking_config,
        custom_metadata=custom_metadata,
    )


@mcp.tool()
def list_documents(store_name: str, page_size: Optional[int] = None, page_token: Optional[str] = None) -> Dict[str, Any]:
    """List documents inside a File Search store."""
    return document_tools.list_documents(store_name, page_size=page_size, page_token=page_token)


@mcp.tool()
def get_document(document_name: str) -> Dict[str, Any]:
    """Get information about a document."""
    return document_tools.get_document(document_name)


@mcp.tool()
def delete_document(document_name: str, force: bool = False) -> Dict[str, Any]:
    """Delete a document from a store."""
    return document_tools.delete_document(document_name, force=force)


@mcp.tool()
def update_metadata(
    document_name: str,
    new_custom_metadata: list,
    original_file_bytes_base64: Optional[str] = None,
    original_file_name: Optional[str] = None,
    store_name: Optional[str] = None,
    mime_type: Optional[str] = None,
    chunking_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Re-ingest a document to update its metadata."""
    return document_tools.update_metadata(
        document_name=document_name,
        new_custom_metadata=new_custom_metadata,
        original_file_bytes_base64=original_file_bytes_base64,
        original_file_name=original_file_name,
        store_name=store_name,
        mime_type=mime_type,
        chunking_config=chunking_config,
    )


@mcp.tool()
def search_documents(
    store_names: list,
    query: str,
    model: str = "gemini-2.5-flash",
    metadata_filter: Optional[str] = None,
    max_output_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
) -> Dict[str, Any]:
    """Execute a grounded search using the File Search tool."""
    return search_tools.search_documents(
        model=model,
        store_names=store_names,
        query=query,
        metadata_filter=metadata_filter,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
    )


@mcp.tool()
def get_operation_status(operation_name: str) -> Dict[str, Any]:
    """Check the status of a long-running operation."""
    return util_tools.get_operation_status(operation_name)


@mcp.tool()
def list_supported_formats() -> Dict[str, Any]:
    """List supported MIME types for File Search ingestion."""
    return util_tools.list_supported_formats()


@mcp.tool()
def get_store_statistics(store_name: str) -> Dict[str, Any]:
    """Aggregate document statistics for a store."""
    return util_tools.get_store_statistics(store_name)


async def main() -> None:
    port = int(os.getenv("PORT", "8080"))
    logger.info("Starting MCP server on port %s", port)
    await mcp.run_async(transport="streamable-http", host="0.0.0.0", port=port)


if __name__ == "__main__":
    asyncio.run(main())
