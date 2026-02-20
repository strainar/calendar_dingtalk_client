#!/bin/bash
# Docker deployment diagnostic script

echo "=== Docker Deployment Diagnostics ==="
echo "Server: $(hostname)"
echo "Date: $(date)"
echo

# Check Docker status
echo "1. Checking Docker service..."
if systemctl is-active --quiet docker; then
    echo "✅ Docker service is running"
else
    echo "❌ Docker service is not running"
    sudo systemctl start docker
    if [ $? -eq 0 ]; then
        echo "✅ Docker service started"
    else
        echo "❌ Failed to start Docker service"
        exit 1
    fi
fi
echo

# Check Docker version and capabilities
echo "2. Docker information:"
docker --version
docker info | head -10
echo

# Check if buildkit is available
echo "3. Checking BuildKit status..."
docker buildx version || echo "BuildKit not available"
echo

# Create .dockerignore if missing
echo "4. Checking .dockerignore..."
if [ ! -f .dockerignore ]; then
    echo "Creating .dockerignore..."
    cat > .dockerignore << EOF
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
venv
ENV
env/
venv/
.git
.gitignore
README.md
.env
.pytest_cache
.coverage
.mypy_cache
*.log
logs/
EOF
    echo "✅ Created .dockerignore"
else
    echo "✅ .dockerignore exists"
fi
echo

# Check if we can use traditional Docker build instead of buildkit
echo "5. Testing Docker build (traditional)..."
DOCKER_BUILDKIT=0 docker build -t calendar-dingtalk-client:test .
if [ $? -eq 0 ]; then
    echo "✅ Traditional Docker build successful"
    docker rmi calendar-dingtalk-client:test
else
    echo "❌ Traditional Docker build failed, trying BuildKit..."

    # Try with BuildKit enabled
    DOCKER_BUILDKIT=1 docker build -t calendar-dingtalk-client:test .
    if [ $? -eq 0 ]; then
        echo "✅ BuildKit build successful"
        docker rmi calendar-dingtalk-client:test
    else
        echo "❌ Both build methods failed"
        echo "Error details:"
        DOCKER_BUILDKIT=1 docker build -t calendar-dingtalk-client:test . 2>&1
        exit 1
    fi
fi
echo

echo "6. Ready for deployment - testing docker-compose..."
docker-compose config
if [ $? -eq 0 ]; then
    echo "✅ docker-compose configuration is valid"
    echo "You can now run: docker-compose up -d"
else
    echo "❌ docker-compose configuration error"
fi
echo

echo "=== Diagnostics completed ==="