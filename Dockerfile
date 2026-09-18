FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy repo
COPY . .

# Sync dependencies
RUN uv sync

# Default command
CMD ["uv", "run", "pytest"]
