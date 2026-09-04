# Multi-stage production and development Dockerfile for AgentCart Backend
FROM python:3.11-slim AS backend-runtime

WORKDIR /app

# Install system dependencies (curl for healthchecks, build tools if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source code
COPY backend/ ./backend/
COPY tests/ ./tests/
COPY alembic.ini .

# Expose backend port
EXPOSE 8000

# Environment defaults
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=development

# Run FastAPI server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
