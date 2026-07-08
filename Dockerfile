FROM python:3.10-slim

WORKDIR /app

# Install system ffmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create output folder if it does not exist
RUN mkdir -p OUTPUT

CMD ["python", "check_streams.py"]