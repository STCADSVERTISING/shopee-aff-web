# Deployable Docker image for Shopee Aff Web
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1

# Create app structure
WORKDIR /srv
COPY backend/ /srv/backend/
COPY frontend/ /srv/frontend/

# Install deps
WORKDIR /srv/backend
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8000
ENV PORT=8000

# Run
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
