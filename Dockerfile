# Use a clean Python base image
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Install system build tools if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY src/ ./src/
COPY app.py .
COPY main.py .
COPY README.md .

# Create outputs folder
RUN mkdir -p output

# Expose port for Streamlit
EXPOSE 8501

# Streamlit headless server configurations
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

# Command to run the Streamlit dashboard
CMD ["streamlit", "run", "app.py"]
