FROM python:3.11-slim

# Install OS dependencies (if needed for crawling/parsing)
RUN apt-get update && apt-get install -y \
    build-essential curl libpq-dev gcc \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source
COPY app/ ./app
COPY config/ ./config

# Avoid storing secrets in image
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Expose port
EXPOSE 8000

# Command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
