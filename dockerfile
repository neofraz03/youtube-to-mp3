# Stage 1: Build FFmpeg dependencies
FROM ffmpeg:latest AS build-ffmpeg
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Stage 2: Build the Python application with dependencies
FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
COPY app.py .

# Define environment variables and commands
ENV YOUTUBE_API_KEY=YOUR_API_KEY_HERE (replace with your API key)
CMD ["python", "app.py"]