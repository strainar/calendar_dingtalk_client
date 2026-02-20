#!/bin/bash
# Calendar DingTalk Client Docker Version Deployment Script
echo "=== Calendar DingTalk Client Docker Deployment ==="

# Configuration
SERVER="192.168.1.204"
USERNAME="sunzhen"
REMOTE_DIR="/home/$USERNAME/calendar-dingtalk-client"
PROJECT_ROOT="$(pwd)"

echo "Local project root: $PROJECT_ROOT"
echo "Remote server: $USERNAME@$SERVER"
echo "Remote directory: $REMOTE_DIR"

# Copy files to server
echo "Step 1: Copying docker.version to server..."
scp -r docker.version "$USERNAME@$SERVER:$REMOTE_DIR"

# Connect to server and diagnose + build
echo "Step 2: Running diagnostics and building Docker image..."
ssh "$USERNAME@$SERVER" << 'EOF'
cd calendar-dingtalk-client/docker.version

# Run diagnostics first
echo "Running Docker diagnostics..."
chmod +x diagnose.sh
./diagnose.sh

if [ $? -ne 0 ]; then
    echo "Diagnostics failed. Attempting with fallback Docker build..."
    # Try manual Docker build with disabled BuildKit
    DOCKER_BUILDKIT=0 docker build -t calendar-dingtalk-client:latest .
fi

# Build the Docker image
echo "Building Docker image..."
docker build -t calendar-dingtalk-client:latest .

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully"
    docker images calendar-dingtalk-client
else
    echo "❌ Docker build failed"
    exit 1
fi

# Start the service using docker-compose
echo "Starting the service..."
docker-compose down 2>/dev/null || true
docker-compose up -d

# Wait a moment for startup
sleep 3

# Check if service is running
echo "Checking service status..."
docker-compose ps

# Test health endpoint
echo "Testing health check..."
if curl -f http://localhost:8000/health 2>/dev/null; then
    echo "✅ Health check passed"
else
    echo "⚠️ Health check failed or not ready yet"
fi

EOF

echo "Deployment completed. Service should be running on server."
echo "Access the application at: http://192.168.1.204:8000"