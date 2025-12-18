"""Gemini File Search MCP サーバー."""
import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

from tools.store_tools import create_store, delete_store, get_store, list_stores
from tools.document_tools import (
    delete_document,
    get_document,
    import_file,
    list_documents,
    update_metadata,
    upload_file,
)
from tools.search_tools import search_documents
from tools.util_tools import (
    get_operation_status,
    get_store_statistics,
    list_supported_formats,
)

# 環境変数をロード
load_dotenv()

# ロギング設定
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 認証プロバイダーの設定
AUTH_TOKENS_STR = os.getenv("MCP_AUTH_TOKENS")
auth_provider = None

if AUTH_TOKENS_STR:
    # カンマ区切りのトークンリストをパース
    # 形式: "token1:client_id1,token2:client_id2"
    tokens = {}
    for token_pair in AUTH_TOKENS_STR.split(","):
        token_pair = token_pair.strip()
        if ":" in token_pair:
            token, client_id = token_pair.split(":", 1)
            tokens[token.strip()] = {
                "client_id": client_id.strip(),
                "scopes": ["mcp:access"],
            }

    if tokens:
        auth_provider = StaticTokenVerifier(tokens=tokens)
        logger.info(f"Bearer token authentication enabled with {len(tokens)} token(s)")
else:
    logger.warning("MCP_AUTH_TOKENS not set - authentication is DISABLED")

# FastMCP サーバーの初期化
mcp = FastMCP("Gemini File Search MCP", auth=auth_provider)


# ============================================================
# Store 管理ツール
# ============================================================


@mcp.tool()
async def mcp_create_store(display_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new File Search Store.

    Args:
        display_name: Display name for the store (max 512 characters, optional)

    Returns:
        Store information including store_name, display_name, and create_time
    """
    return await create_store(display_name=display_name)


@mcp.tool()
async def mcp_list_stores(
    page_size: Optional[int] = None, page_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    List all File Search Stores.

    Args:
        page_size: Maximum number of stores per page
        page_token: Pagination token

    Returns:
        List of stores and next_page_token
    """
    return await list_stores(page_size=page_size, page_token=page_token)


@mcp.tool()
async def mcp_get_store(store_name: str) -> Dict[str, Any]:
    """
    Get details of a specific File Search Store.

    Args:
        store_name: Store resource name (e.g., fileSearchStores/...)

    Returns:
        Store details
    """
    return await get_store(store_name=store_name)


@mcp.tool()
async def mcp_delete_store(store_name: str, force: bool = False) -> Dict[str, bool]:
    """
    Delete a File Search Store.

    Args:
        store_name: Store resource name (e.g., fileSearchStores/...)
        force: Force deletion even if documents exist (default: False)

    Returns:
        Deletion confirmation
    """
    return await delete_store(store_name=store_name, force=force)


# ============================================================
# Document 管理ツール
# ============================================================


@mcp.tool()
async def mcp_upload_file(
    store_name: str,
    file_bytes_base64: str,
    display_name: Optional[str] = None,
    mime_type: Optional[str] = None,
    chunking_config: Optional[Dict[str, Any]] = None,
    custom_metadata: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Upload a file directly to File Search Store.

    Args:
        store_name: Store resource name
        file_bytes_base64: Base64-encoded file bytes
        display_name: Document display name (optional)
        mime_type: MIME type (optional, will be inferred if not provided)
        chunking_config: Chunking configuration (optional)
        custom_metadata: Custom metadata (optional, max 20 entries)

    Returns:
        operation_name and document_name (if available)
    """
    return await upload_file(
        store_name=store_name,
        file_bytes_base64=file_bytes_base64,
        display_name=display_name,
        mime_type=mime_type,
        chunking_config=chunking_config,
        custom_metadata=custom_metadata,
    )


@mcp.tool()
async def mcp_import_file(
    store_name: str,
    file_name: str,
    display_name: Optional[str] = None,
    chunking_config: Optional[Dict[str, Any]] = None,
    custom_metadata: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, str]:
    """
    Import a file from Files API to File Search Store.

    Args:
        store_name: Store resource name
        file_name: Files API file resource name (e.g., files/...)
        display_name: Document display name (optional)
        chunking_config: Chunking configuration (optional)
        custom_metadata: Custom metadata (optional)

    Returns:
        operation_name
    """
    return await import_file(
        store_name=store_name,
        file_name=file_name,
        display_name=display_name,
        chunking_config=chunking_config,
        custom_metadata=custom_metadata,
    )


@mcp.tool()
async def mcp_list_documents(
    store_name: str,
    page_size: Optional[int] = None,
    page_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List documents in a File Search Store.

    Args:
        store_name: Store resource name
        page_size: Maximum number of documents per page
        page_token: Pagination token

    Returns:
        List of documents and next_page_token
    """
    return await list_documents(
        store_name=store_name, page_size=page_size, page_token=page_token
    )


@mcp.tool()
async def mcp_get_document(document_name: str) -> Dict[str, Any]:
    """
    Get details of a specific document.

    Args:
        document_name: Document resource name (e.g., fileSearchStores/.../documents/...)

    Returns:
        Document details
    """
    return await get_document(document_name=document_name)


@mcp.tool()
async def mcp_delete_document(
    document_name: str, force: bool = False
) -> Dict[str, bool]:
    """
    Delete a document.

    Args:
        document_name: Document resource name
        force: Force deletion flag (optional)

    Returns:
        Deletion confirmation
    """
    return await delete_document(document_name=document_name, force=force)


@mcp.tool()
async def mcp_update_metadata(
    document_name: str,
    new_custom_metadata: List[Dict[str, Any]],
    original_file_bytes_base64: str,
    display_name: Optional[str] = None,
    mime_type: Optional[str] = None,
    chunking_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Update document metadata by deleting and re-uploading.

    Note: Document name may change.

    Args:
        document_name: Existing document resource name
        new_custom_metadata: New custom metadata
        original_file_bytes_base64: Original file bytes (Base64)
        display_name: Document display name (optional)
        mime_type: MIME type (optional)
        chunking_config: Chunking configuration (optional)

    Returns:
        new_document_name and operation_name
    """
    return await update_metadata(
        document_name=document_name,
        new_custom_metadata=new_custom_metadata,
        original_file_bytes_base64=original_file_bytes_base64,
        display_name=display_name,
        mime_type=mime_type,
        chunking_config=chunking_config,
    )


# ============================================================
# 検索ツール
# ============================================================


@mcp.tool()
async def mcp_search_documents(
    store_names: List[str],
    query: str,
    model: str = "gemini-2.5-flash",
    metadata_filter: Optional[str] = None,
    max_output_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Search documents using File Search and generate an answer.

    Args:
        store_names: List of store resource names to search
        query: Search query
        model: Model to use (default: gemini-2.5-flash)
        metadata_filter: Metadata filter expression (optional)
        max_output_tokens: Maximum output tokens (optional)
        temperature: Temperature parameter (optional)

    Returns:
        answer_text, grounding_metadata, used_stores, model
    """
    return await search_documents(
        store_names=store_names,
        query=query,
        model=model,
        metadata_filter=metadata_filter,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
    )


# ============================================================
# ユーティリティツール
# ============================================================


@mcp.tool()
async def mcp_get_operation_status(operation_name: str) -> Dict[str, Any]:
    """
    Get the status of a long-running operation (LRO).

    Args:
        operation_name: Operation resource name

    Returns:
        done (completion flag), error (if any), response (if completed)
    """
    return await get_operation_status(operation_name=operation_name)


@mcp.tool()
async def mcp_list_supported_formats() -> Dict[str, Any]:
    """
    List supported file formats (MIME types) for File Search.

    Returns:
        supported_mime_types (categorized by application and text)
    """
    return await list_supported_formats()


@mcp.tool()
async def mcp_get_store_statistics(store_name: str) -> Dict[str, Any]:
    """
    Get statistics for a File Search Store.

    Args:
        store_name: Store resource name

    Returns:
        document_count, total_size_bytes, states_breakdown
    """
    return await get_store_statistics(store_name=store_name)


# ============================================================
# サーバー起動
# ============================================================


async def main():
    """サーバーを起動する."""
    # API キーの確認
    if not os.getenv("GEMINI_API_KEY"):
        logger.error("GEMINI_API_KEY environment variable is not set")
        raise ValueError("GEMINI_API_KEY is required")

    # トランスポートモードを環境変数で切り替え（デフォルトは stdio）
    transport_mode = os.getenv("MCP_TRANSPORT", "stdio")

    if transport_mode == "http":
        # HTTP トランスポートで起動（Cloud Run、Docker等）
        port = int(os.getenv("PORT", "8080"))
        logger.info(f"Starting Gemini File Search MCP server on port {port} (HTTP mode)")
        await mcp.run_async(
            transport="streamable-http", host="0.0.0.0", port=port, path="/mcp"
        )
    else:
        # stdio トランスポートで起動（Claude Desktop等）
        logger.info("Starting Gemini File Search MCP server (stdio mode)")
        await mcp.run_async(transport="stdio")


if __name__ == "__main__":
    asyncio.run(main())
