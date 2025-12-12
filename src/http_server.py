"""HTTP/SSE server for Gemini File Search MCP Server (Cloud Run deployment)"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from mcp.server import Server
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


# Global server instance
mcp_server: Server = None
gemini_client: GeminiClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    global mcp_server, gemini_client

    # Startup
    logger.info("Starting Gemini File Search MCP Server (HTTP mode)")
    settings = Settings()
    gemini_client = GeminiClient(api_key=settings.gemini_api_key)
    mcp_server = Server("gemini-file-search")

    # Register tools
    register_tools(mcp_server, gemini_client)

    logger.info("Server initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down server")


app = FastAPI(
    title="Gemini File Search MCP Server",
    description="MCP Server for Gemini File Search API",
    version="0.1.0",
    lifespan=lifespan
)


def register_tools(server: Server, client: GeminiClient):
    """Register all MCP tools"""

    @server.list_tools()
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
                            "description": "Number of stores to retrieve",
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
                        "store_name": {"type": "string"},
                        "file_path": {"type": "string"},
                        "display_name": {"type": "string"},
                        "metadata": {"type": "object"},
                    },
                    "required": ["store_name", "file_path"],
                },
            ),
            Tool(
                name="search_documents",
                description="Search documents in File Search Stores",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "store_names": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "query": {"type": "string"},
                        "model": {"type": "string", "default": "gemini-2.0-flash-exp"},
                        "max_results": {"type": "integer", "default": 10},
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
                        "store_name": {"type": "string"},
                        "page_size": {"type": "integer", "default": 10},
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
                        "document_name": {"type": "string"},
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
                        "document_name": {"type": "string"},
                    },
                    "required": ["document_name"],
                },
            ),
            Tool(
                name="delete_file_search_store",
                description="Delete an entire File Search Store",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "store_name": {"type": "string"},
                    },
                    "required": ["store_name"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: Any) -> list[TextContent]:
        """Handle tool calls"""
        logger.info(f"Tool called: {name}")

        try:
            # Route to appropriate handler
            if name == "create_file_search_store":
                result = handle_create_store(client, arguments)
            elif name == "list_file_search_stores":
                result = handle_list_stores(client, arguments)
            elif name == "upload_file_to_store":
                result = handle_upload_file(client, arguments)
            elif name == "search_documents":
                result = handle_search_documents(client, arguments)
            elif name == "list_documents":
                result = handle_list_documents(client, arguments)
            elif name == "get_document":
                result = handle_get_document(client, arguments)
            elif name == "delete_document":
                result = handle_delete_document(client, arguments)
            elif name == "delete_file_search_store":
                result = handle_delete_store(client, arguments)
            else:
                result = {"error": f"Unknown tool: {name}"}

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


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Gemini File Search MCP Server",
        "version": "0.1.0",
        "transport": "HTTP/SSE"
    }


@app.get("/health")
async def health():
    """Health check for Cloud Run"""
    return {"status": "healthy"}


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """MCP endpoint for tool calls"""
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})

        if method == "tools/list":
            # List available tools
            tools_list = await mcp_server.request_handler.handle_list_tools()
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": {"tools": [t.model_dump() for t in tools_list]}
            })

        elif method == "tools/call":
            # Call a tool
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            result = await mcp_server.request_handler.handle_call_tool(
                tool_name, arguments
            )

            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": {"content": [c.model_dump() for c in result]}
            })

        else:
            return JSONResponse(
                status_code=400,
                content={"error": f"Unknown method: {method}"}
            )

    except Exception as e:
        logger.error(f"Error processing MCP request: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/sse")
async def sse_endpoint(request: Request):
    """SSE endpoint for MCP communication"""

    async def event_generator():
        """Generate SSE events"""
        try:
            # Send initial connection event
            yield {
                "event": "connected",
                "data": json.dumps({
                    "status": "connected",
                    "server": "gemini-file-search"
                })
            }

            # Keep connection alive
            while True:
                # In a real implementation, you would handle MCP messages here
                # For now, just send periodic heartbeats
                await asyncio.sleep(30)
                yield {
                    "event": "heartbeat",
                    "data": json.dumps({"timestamp": datetime.now().isoformat()})
                }

        except Exception as e:
            logger.error(f"SSE error: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }

    return EventSourceResponse(event_generator())


if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.getenv("PORT", 8080))

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
