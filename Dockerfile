# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv for dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

# Copy project files
COPY pyproject.toml ./
COPY server.py ./
COPY gemini_client.py ./
COPY tools/ ./tools/

# Install dependencies using uv
RUN uv pip install --no-cache -e .

# Expose port (Cloud Run uses PORT environment variable)
EXPOSE 8080

# Run the server
CMD ["python", "server.py"]
