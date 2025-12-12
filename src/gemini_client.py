"""Gemini API client for File Search operations"""

import os
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from .models import (
    Store,
    Document,
    SearchResult,
    Citation,
    UploadResult,
    ChunkingConfig,
)
from .exceptions import (
    APIKeyError,
    StoreNotFoundError,
    DocumentNotFoundError,
    UploadError,
    SearchError,
    QuotaExceededError,
    InvalidFileError,
)
from .config import ALLOWED_EXTENSIONS

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for interacting with Gemini File Search API"""

    def __init__(self, api_key: str, max_retries: int = 3):
        """
        Initialize Gemini client

        Args:
            api_key: Gemini API key
            max_retries: Maximum number of retry attempts
        """
        if not api_key:
            raise APIKeyError("Gemini API key is required")

        self.api_key = api_key
        self.max_retries = max_retries

        # Initialize Gemini client
        try:
            self.client = genai.Client(api_key=api_key)
            logger.info("Gemini client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise APIKeyError(f"Failed to initialize Gemini client: {e}")

    def _validate_file(self, file_path: str, max_size_mb: int = 100) -> None:
        """
        Validate file before upload

        Args:
            file_path: Path to file
            max_size_mb: Maximum file size in MB

        Raises:
            InvalidFileError: If file is invalid
        """
        path = Path(file_path)

        # Check if file exists
        if not path.exists():
            raise InvalidFileError(f"File not found: {file_path}")

        if not path.is_file():
            raise InvalidFileError(f"Path is not a file: {file_path}")

        # Check file extension
        ext = path.suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise InvalidFileError(
                f"Unsupported file type: {ext}. "
                f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        # Check file size
        size_bytes = path.stat().st_size
        max_size_bytes = max_size_mb * 1024 * 1024

        if size_bytes > max_size_bytes:
            raise InvalidFileError(
                f"File too large: {size_bytes / 1024 / 1024:.2f}MB "
                f"(max: {max_size_mb}MB)"
            )

        logger.info(f"File validation passed: {file_path} ({size_bytes} bytes)")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def create_store(
        self,
        display_name: str,
        description: Optional[str] = None
    ) -> Store:
        """
        Create a new File Search Store

        Args:
            display_name: Display name for the store
            description: Optional description

        Returns:
            Created Store object
        """
        try:
            logger.info(f"Creating store: {display_name}")

            # Use the correct API method
            response = self.client.file_search_stores.create(
                config={'display_name': display_name}
            )

            # Convert response to Store model
            store = Store(
                name=response.name,
                display_name=response.display_name,
                num_documents=getattr(response, 'num_documents', 0),
                num_active_documents=getattr(response, 'num_active_documents', 0),
                num_processing_documents=getattr(response, 'num_processing_documents', 0),
                num_failed_documents=getattr(response, 'num_failed_documents', 0),
                storage_bytes=getattr(response, 'storage_bytes', 0),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            logger.info(f"Store created successfully: {store.name}")
            return store

        except Exception as e:
            logger.error(f"Failed to create store: {e}")
            raise UploadError(f"Failed to create store: {e}")

    def list_stores(self, page_size: int = 10) -> list[Store]:
        """
        List all File Search Stores

        Args:
            page_size: Number of stores per page

        Returns:
            List of Store objects
        """
        try:
            logger.info(f"Listing stores (page_size={page_size})")

            # Use the correct API method
            response = self.client.file_search_stores.list(
                config={'page_size': page_size}
            )

            stores = []
            for store_data in response:
                store = Store(
                    name=store_data.name,
                    display_name=store_data.display_name,
                    num_documents=getattr(store_data, 'num_documents', 0),
                    num_active_documents=getattr(store_data, 'num_active_documents', 0),
                    num_processing_documents=getattr(store_data, 'num_processing_documents', 0),
                    num_failed_documents=getattr(store_data, 'num_failed_documents', 0),
                    storage_bytes=getattr(store_data, 'storage_bytes', 0),
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                stores.append(store)

            logger.info(f"Found {len(stores)} stores")
            return stores

        except Exception as e:
            logger.error(f"Failed to list stores: {e}")
            raise SearchError(f"Failed to list stores: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def upload_file(
        self,
        store_name: str,
        file_path: str,
        display_name: Optional[str] = None,
        metadata: Optional[dict] = None,
        chunking_config: Optional[ChunkingConfig] = None,
        max_size_mb: int = 100,
    ) -> UploadResult:
        """
        Upload a file to a File Search Store

        Args:
            store_name: Target store name/ID
            file_path: Path to file to upload
            display_name: Optional display name
            metadata: Optional metadata
            chunking_config: Optional chunking configuration
            max_size_mb: Maximum file size in MB

        Returns:
            UploadResult object
        """
        try:
            # Validate file
            self._validate_file(file_path, max_size_mb)

            logger.info(f"Uploading file to store {store_name}: {file_path}")

            # Use filename as display name if not provided
            if not display_name:
                display_name = Path(file_path).name

            # Upload file first
            with open(file_path, 'rb') as f:
                upload_response = self.client.files.upload(file=f)

            logger.info(f"File uploaded with URI: {upload_response.uri}")

            # Create document in store
            doc_metadata = metadata or {}

            create_request = types.CreateFileSearchDocumentRequest(
                parent=store_name,
                file_search_document=types.FileSearchDocument(
                    display_name=display_name,
                    file_uri=upload_response.uri,
                    metadata=doc_metadata,
                )
            )

            doc_response = self.client.file_search_documents.create(create_request)

            file_size = Path(file_path).stat().st_size

            result = UploadResult(
                document_name=doc_response.name,
                display_name=display_name,
                status="PROCESSING",
                operation_name=getattr(doc_response, 'operation_name', None),
                file_size_bytes=file_size,
            )

            logger.info(f"Document created successfully: {result.document_name}")
            return result

        except InvalidFileError:
            raise
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise UploadError(f"Failed to upload file: {e}")

    def search(
        self,
        store_names: list[str],
        query: str,
        model: str = "gemini-2.0-flash-exp",
        metadata_filter: Optional[str] = None,
        max_results: int = 10,
    ) -> SearchResult:
        """
        Search documents in File Search Stores

        Args:
            store_names: List of store names to search
            query: Search query
            model: Model name to use
            metadata_filter: Optional metadata filter expression
            max_results: Maximum number of results

        Returns:
            SearchResult object
        """
        try:
            logger.info(f"Searching in stores {store_names}: {query}")

            # Create tools configuration
            file_search_tool = types.Tool(
                file_search=types.FileSearchToolConfig(
                    file_search_stores=store_names,
                )
            )

            # Generate content with file search
            response = self.client.models.generate_content(
                model=model,
                contents=query,
                config=types.GenerateContentConfig(
                    tools=[file_search_tool],
                )
            )

            # Extract response text
            response_text = response.text if hasattr(response, 'text') else str(response)

            # Extract citations
            citations = []
            grounding_metadata = {}

            if hasattr(response, 'grounding_metadata'):
                grounding_metadata = response.grounding_metadata

                if hasattr(grounding_metadata, 'grounding_chunks'):
                    for chunk in grounding_metadata.grounding_chunks:
                        citation = Citation(
                            source=getattr(chunk, 'document_name', 'unknown'),
                            snippet=getattr(chunk, 'content', ''),
                            metadata=getattr(chunk, 'metadata', {}),
                        )
                        citations.append(citation)

            result = SearchResult(
                response=response_text,
                citations=citations,
                grounding_metadata=grounding_metadata.__dict__ if hasattr(grounding_metadata, '__dict__') else {},
            )

            logger.info(f"Search completed with {len(citations)} citations")
            return result

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise SearchError(f"Search failed: {e}")

    def list_documents(
        self,
        store_name: str,
        page_size: int = 10
    ) -> list[Document]:
        """
        List documents in a store

        Args:
            store_name: Store name/ID
            page_size: Number of documents per page

        Returns:
            List of Document objects
        """
        try:
            logger.info(f"Listing documents in store: {store_name}")

            request = types.ListFileSearchDocumentsRequest(
                parent=store_name,
                page_size=page_size
            )

            response = self.client.file_search_documents.list(request)

            documents = []
            for doc_data in response:
                doc = Document(
                    name=doc_data.name,
                    display_name=doc_data.display_name,
                    metadata=getattr(doc_data, 'metadata', {}),
                    state=getattr(doc_data, 'state', 'UNKNOWN'),
                    size_bytes=getattr(doc_data, 'size_bytes', 0),
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                documents.append(doc)

            logger.info(f"Found {len(documents)} documents")
            return documents

        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            raise SearchError(f"Failed to list documents: {e}")

    def get_document(self, document_name: str) -> Document:
        """
        Get a specific document

        Args:
            document_name: Full document name/ID

        Returns:
            Document object
        """
        try:
            logger.info(f"Getting document: {document_name}")

            request = types.GetFileSearchDocumentRequest(name=document_name)
            doc_data = self.client.file_search_documents.get(request)

            doc = Document(
                name=doc_data.name,
                display_name=doc_data.display_name,
                metadata=getattr(doc_data, 'metadata', {}),
                state=getattr(doc_data, 'state', 'UNKNOWN'),
                size_bytes=getattr(doc_data, 'size_bytes', 0),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            logger.info(f"Document retrieved: {doc.name}")
            return doc

        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            raise DocumentNotFoundError(f"Document not found: {document_name}")

    def delete_document(self, document_name: str) -> bool:
        """
        Delete a document

        Args:
            document_name: Full document name/ID

        Returns:
            True if successful
        """
        try:
            logger.info(f"Deleting document: {document_name}")

            request = types.DeleteFileSearchDocumentRequest(name=document_name)
            self.client.file_search_documents.delete(request)

            logger.info(f"Document deleted: {document_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise DocumentNotFoundError(f"Failed to delete document: {document_name}")

    def delete_store(self, store_name: str) -> bool:
        """
        Delete a File Search Store

        Args:
            store_name: Store name/ID to delete

        Returns:
            True if successful
        """
        try:
            logger.info(f"Deleting store: {store_name}")

            # Use the correct API method
            self.client.file_search_stores.delete(
                name=store_name,
                config={'force': True}
            )

            logger.info(f"Store deleted: {store_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete store: {e}")
            raise StoreNotFoundError(f"Failed to delete store: {store_name}")
