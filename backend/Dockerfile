# =============================================================================
# DentalAI Backend Dockerfile — Hugging Face Spaces & Production Ready
# =============================================================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies for OpenCV, Pillow, and PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set up non-root user (Hugging Face Spaces requires UID 1000)
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR /home/user/app

# Install Python dependencies
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code and models
COPY --chown=user:user app/ ./app/
COPY --chown=user:user models/ ./models/
COPY --chown=user:user samples/ ./samples/

# Create writable upload and report directories
RUN mkdir -p /home/user/app/uploads /home/user/app/reports && \
    chown -R user:user /home/user/app

USER user

EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:7860/api/health || exit 1

# Start FastAPI server on port 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "2"]
