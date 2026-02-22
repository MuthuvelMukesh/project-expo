FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for ML libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Generate synthetic data + train ML model at build time
RUN python -m app.ml.seed_data && python -m app.ml.train

EXPOSE 8000

# Startup: seed database + run server
CMD ["sh", "-c", "python -m app.seed_db && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
