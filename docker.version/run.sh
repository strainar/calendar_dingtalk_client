#!/bin/bash
# Run the Docker version locally

echo "Starting DingTalk CalDAV Calendar Client (Docker version)..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your DingTalk CALDAV credentials!"
fi

# Start the application
cd src
uvicorn calendar_dingtalk_client.http_server:app --host 0.0.0.0 --port 8080 --reload
