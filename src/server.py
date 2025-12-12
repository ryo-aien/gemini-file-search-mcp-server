"""Gemini File Search MCP Server - Main server implementation"""

import asyncio
import logging
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .gemini_client import GeminiClient
from .config import Settings
from .tools.store_tools import (
    handle_create_store,
    handle_list_stores,
    handle_delete_store,
)
from .tools.document_tools import (
    handle_upload_file,
    handle_list_documents,
    handle_get_document,
    handle_delete_document,
)
from .tools.search_tools import handle_search_documents

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GeminiFileSearchMCPServer:
    """MCP Server for Gemini File Search operations"""

    def __init__(self, settings: Settings):
        """
        Initialize the MCP server

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.server = Server("gemini-file-search")
        self.client = GeminiClient(
            api_key=settings.gemini_api_key,
            max_retries=settings.max_retries
        )

        # Register tool handlers
        self._register_handlers()

        logger.info("Gemini File Search MCP Server initialized")

    def _register_handlers(self):
        """Register all tool handlers"""

        # List tools handler
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """Return list of available tools"""
            return [
                Tool(
                    name="create_file_search_store",
                    description="Create a new File Search Store for document indexing and retrieval",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "display_name": {
                                "type": "string",
                                "description": "Display name for the store",
                                "minLength": 1,
                                "maxLength": 256,
                            },
                            "description": {
                                "type": "string",
                                "description": "Optional description of the store",
                            },
                        },
                        "required": ["display_name"],
                    },
                ),
                Tool(
                    name="list_file_search_stores",
                    description="List all File Search Stores",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "page_size": {
                                "type": "integer",
                                "description": "Number of stores to retrieve (default: 10)",
                                "minimum": 1,
                                "maximum": 100,
                                "default": 10,
                            },
                        },
                    },
                ),
                Tool(
                    name="upload_file_to_store",
                    description="Upload a file to a File Search Store for indexing",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "store_name": {
                                "type": "string",
                                "description": "Name/ID of the target store",
                            },
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file to upload",
                            },
                            "display_name": {
                                "type": "string",
                                "description": "Optional display name for the document",
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Optional metadata for the document",
                            },
                            "chunking_config": {
                                "type": "object",
                                "description": "Optional chunking configuration",
                                "properties": {
                                    "chunk_size": {
                                        "type": "integer",
                                        "description": "Size of each chunk in tokens",
                                        "minimum": 1,
                                        "maximum": 2000,
                                        "default": 200,
                                    },
                                    "chunk_overlap": {
                                        "type": "integer",
                                        "description": "Overlap between chunks",
                                        "minimum": 0,
                                        "default": 20,
                                    },
                                },
                            },
                        },
                        "required": ["store_name", "file_path"],
                    },
                ),
                Tool(
                    name="search_documents",
                    description="Search documents in File Search Stores using semantic search",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "store_names": {
                                "type": "array",
                                "description": "List of store names to search",
                                "items": {"type": "string"},
                                "minItems": 1,
                                "maxItems": 5,
                            },
                            "query": {
                                "type": "string",
                                "description": "Search query",
                                "minLength": 1,
                            },
                            "model": {
                                "type": "string",
                                "description": "Model to use for search",
                                "default": "gemini-2.0-flash-exp",
                            },
                            "metadata_filter": {
                                "type": "string",
                                "description": "Optional metadata filter expression",
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "minimum": 1,
                                "maximum": 50,
                                "default": 10,
                            },
                        },
                        "required": ["store_names", "query"],
                    },
                ),
                Tool(
                    name="list_documents",
                    description="List all documents in a File Search Store",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "store_name": {
                                "type": "string",
                                "description": "Name/ID of the store",
                            },
                            "page_size": {
                                "type": "integer",
                                "description": "Number of documents per page",
                                "minimum": 1,
                                "maximum": 100,
                                "default": 10,
                            },
                        },
                        "required": ["store_name"],
                    },
                ),
                Tool(
                    name="get_document",
                    description="Get information about a specific document",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "document_name": {
                                "type": "string",
                                "description": "Full document name/ID",
                            },
                        },
                        "required": ["document_name"],
                    },
                ),
                Tool(
                    name="delete_document",
                    description="Delete a document from a File Search Store",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "document_name": {
                                "type": "string",
                                "description": "Full document name/ID to delete",
                            },
                        },
                        "required": ["document_name"],
                    },
                ),
                Tool(
                    name="delete_file_search_store",
                    description="Delete an entire File Search Store and all its documents",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "store_name": {
                                "type": "string",
                                "description": "Name/ID of the store to delete",
                            },
                        },
                        "required": ["store_name"],
                    },
                ),
            ]

        # Call tool handler
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """
            Handle tool calls

            Args:
                name: Tool name
                arguments: Tool arguments

            Returns:
                List of text content responses
            """
            logger.info(f"Tool called: {name}")

            try:
                # Route to appropriate handler
                if name == "create_file_search_store":
                    result = handle_create_store(self.client, arguments)
                elif name == "list_file_search_stores":
                    result = handle_list_stores(self.client, arguments)
                elif name == "upload_file_to_store":
                    result = handle_upload_file(self.client, arguments)
                elif name == "search_documents":
                    result = handle_search_documents(self.client, arguments)
                elif name == "list_documents":
                    result = handle_list_documents(self.client, arguments)
                elif name == "get_document":
                    result = handle_get_document(self.client, arguments)
                elif name == "delete_document":
                    result = handle_delete_document(self.client, arguments)
                elif name == "delete_file_search_store":
                    result = handle_delete_store(self.client, arguments)
                else:
                    result = {"error": f"Unknown tool: {name}"}

                # Return formatted response
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, indent=2, ensure_ascii=False)
                    )
                ]

            except Exception as e:
                logger.error(f"Error handling tool {name}: {e}")
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": str(e),
                            "tool": name
                        }, indent=2)
                    )
                ]

    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            logger.info("Starting Gemini File Search MCP Server...")
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point"""
    try:
        # Load settings
        settings = Settings()

        # Create and run server
        server = GeminiFileSearchMCPServer(settings)
        await server.run()

    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
