"""Custom exceptions for Gemini File Search MCP Server"""


class GeminiFileSearchError(Exception):
    """Base exception class for all Gemini File Search errors"""
    pass


class APIKeyError(GeminiFileSearchError):
    """Raised when there's an issue with the API key"""
    pass


class StoreNotFoundError(GeminiFileSearchError):
    """Raised when a requested store cannot be found"""
    pass


class DocumentNotFoundError(GeminiFileSearchError):
    """Raised when a requested document cannot be found"""
    pass


class UploadError(GeminiFileSearchError):
    """Raised when file upload fails"""
    pass


class SearchError(GeminiFileSearchError):
    """Raised when search operation fails"""
    pass


class QuotaExceededError(GeminiFileSearchError):
    """Raised when API quota is exceeded"""
    pass


class InvalidFileError(GeminiFileSearchError):
    """Raised when a file is invalid (wrong format, too large, etc.)"""
    pass


class ValidationError(GeminiFileSearchError):
    """Raised when input validation fails"""
    pass


class OperationTimeoutError(GeminiFileSearchError):
    """Raised when an operation times out"""
    pass
