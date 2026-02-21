FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Render uses PORT env var
ENV PORT=8000

# Disable IPv6 to force IPv4 connections (Render doesn't support IPv6)
RUN echo "precedence ::ffff:0:0/96 100" >> /etc/gai.conf

# Run migrations (allow failure) and start server
CMD sh -c "alembic upgrade head || echo 'Migration skipped'; exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"
