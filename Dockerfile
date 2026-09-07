FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Ensure Python output is sent straight to terminal (no buffering)
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Make the entrypoint script executable
RUN chmod +x entrypoint.sh

# Expose FastAPI (8000) and Streamlit (8501) ports
EXPOSE 8000 8501

# Run the entrypoint script
ENTRYPOINT ["./entrypoint.sh"]
