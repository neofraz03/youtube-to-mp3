FROM python:3.11-slim

# Install ffmpeg system dependencies
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

EXPOSE 8080

# Combines the pip upgrade and app launch smoothly into one command string
CMD ["sh", "-c", "pip install --no-cache-dir --upgrade yt-dlp && python app.py"]
