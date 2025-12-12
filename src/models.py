"""Pydantic models for Gemini File Search MCP Server"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


# Configuration Models
class ChunkingConfig(BaseModel):
    """Configuration for document chunking"""
    chunk_size: int = Field(default=200, ge=1, le=2000, description="Size of each chunk in tokens")
    chunk_overlap: int = Field(default=20, ge=0, description="Overlap between chunks")


# Input Models
class CreateStoreInput(BaseModel):
    """Input for creating a File Search Store"""
    display_name: str = Field(..., min_length=1, max_length=256, description="Display name for the store")
    description: Optional[str] = Field(None, description="Optional description of the store")


class ListStoresInput(BaseModel):
    """Input for listing File Search Stores"""
    page_size: int = Field(default=10, ge=1, le=100, description="Number of stores to retrieve per page")


class UploadFileInput(BaseModel):
    """Input for uploading a file to a store"""
    store_name: str = Field(..., description="Name/ID of the target store")
    file_path: str = Field(..., description="Path to the file to upload")
    display_name: Optional[str] = Field(None, description="Display name for the document")
    metadata: Optional[dict[str, Any]] = Field(None, description="Custom metadata for the document")
    chunking_config: Optional[ChunkingConfig] = Field(None, description="Chunking configuration")


class SearchInput(BaseModel):
    """Input for searching documents"""
    store_names: list[str] = Field(..., min_length=1, max_length=5, description="List of store names to search")
    query: str = Field(..., min_length=1, description="Search query")
    model: str = Field(default="gemini-2.0-flash-exp", description="Model to use for search")
    metadata_filter: Optional[str] = Field(None, description="Metadata filter expression")
    max_results: int = Field(default=10, ge=1, le=50, description="Maximum number of results")


class ListDocumentsInput(BaseModel):
    """Input for listing documents in a store"""
    store_name: str = Field(..., description="Name/ID of the store")
    page_size: int = Field(default=10, ge=1, le=100, description="Number of documents per page")


class GetDocumentInput(BaseModel):
    """Input for getting a specific document"""
    document_name: str = Field(..., description="Full document name/ID")


class DeleteDocumentInput(BaseModel):
    """Input for deleting a document"""
    document_name: str = Field(..., description="Full document name/ID to delete")


class DeleteStoreInput(BaseModel):
    """Input for deleting a store"""
    store_name: str = Field(..., description="Name/ID of the store to delete")


# Output Models
class Store(BaseModel):
    """Represents a File Search Store"""
    name: str = Field(..., description="Unique store identifier")
    display_name: str = Field(..., description="Human-readable store name")
    num_documents: int = Field(default=0, description="Total number of documents")
    num_active_documents: int = Field(default=0, description="Number of active documents")
    num_processing_documents: int = Field(default=0, description="Number of documents being processed")
    num_failed_documents: int = Field(default=0, description="Number of failed documents")
    storage_bytes: int = Field(default=0, description="Total storage used in bytes")
    created_at: datetime = Field(..., description="Store creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class Document(BaseModel):
    """Represents a document in a File Search Store"""
    name: str = Field(..., description="Unique document identifier")
    display_name: str = Field(..., description="Human-readable document name")
    metadata: Optional[dict[str, Any]] = Field(None, description="Custom metadata")
    state: str = Field(..., description="Document state: PROCESSING, ACTIVE, or FAILED")
    size_bytes: int = Field(default=0, description="Document size in bytes")
    created_at: datetime = Field(..., description="Document creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class Citation(BaseModel):
    """Represents a citation/reference from search results"""
    source: str = Field(..., description="Source document identifier")
    snippet: str = Field(..., description="Relevant text snippet")
    metadata: Optional[dict[str, Any]] = Field(None, description="Source metadata")


class SearchResult(BaseModel):
    """Represents search results"""
    response: str = Field(..., description="Generated response from the model")
    citations: list[Citation] = Field(default_factory=list, description="List of citations")
    grounding_metadata: dict[str, Any] = Field(default_factory=dict, description="Detailed grounding information")


class UploadResult(BaseModel):
    """Result of a file upload operation"""
    document_name: str = Field(..., description="Created document identifier")
    display_name: str = Field(..., description="Document display name")
    status: str = Field(..., description="Upload status: PROCESSING, ACTIVE, or FAILED")
    operation_name: Optional[str] = Field(None, description="Async operation tracking ID")
    file_size_bytes: int = Field(default=0, description="Uploaded file size")


class ListStoresResult(BaseModel):
    """Result of listing stores"""
    stores: list[Store] = Field(default_factory=list, description="List of stores")
    total_count: int = Field(..., description="Total number of stores")


class ListDocumentsResult(BaseModel):
    """Result of listing documents"""
    documents: list[Document] = Field(default_factory=list, description="List of documents")


class DeleteResult(BaseModel):
    """Result of a delete operation"""
    success: bool = Field(..., description="Whether deletion was successful")
    message: str = Field(..., description="Status message")
