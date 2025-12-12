"""Configuration management for Gemini File Search MCP Server"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Gemini API Configuration
    gemini_api_key: str

    # Model Configuration
    default_model: str = "gemini-2.0-flash-exp"

    # Chunking Configuration
    default_chunk_size: int = 200
    default_chunk_overlap: int = 20

    # File Upload Limits
    max_file_size_mb: int = 100
    max_stores_per_query: int = 5

    # Logging
    log_level: str = "INFO"

    # Cache Configuration
    cache_ttl_minutes: int = 5

    # Retry Configuration
    max_retries: int = 3
    retry_min_wait: int = 2
    retry_max_wait: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Allowed file extensions for upload
ALLOWED_EXTENSIONS = {
    # Text files
    '.txt', '.md', '.html', '.htm', '.xml', '.json', '.yaml', '.yml',
    # Documents
    '.pdf', '.doc', '.docx', '.odt', '.rtf',
    # Spreadsheets
    '.csv', '.xlsx', '.xls', '.ods',
    # Presentations
    '.pptx', '.ppt', '.odp',
    # Code files
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
    '.hpp', '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
    '.sh', '.bash', '.sql', '.r', '.m', '.mat',
}
