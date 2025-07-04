#!/bin/bash

# Docker test script for TeamSpeak MCP
set -e

echo "🐳 Docker build and startup test for TeamSpeak MCP"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    error "Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose is not installed"
    exit 1
fi

success "Docker and Docker Compose are installed"

# Check if .env file exists
if [ ! -f .env ]; then
    warning ".env file missing, creating from config.docker.env"
    cp config.docker.env .env
    warning "Modify .env with your TeamSpeak parameters before continuing"
    echo "Press Enter to continue or Ctrl+C to stop..."
    read -r
fi

# Build image
echo "🔧 Building Docker image..."
if docker build -t teamspeak-mcp:test .; then
    success "Image built successfully"
else
    error "Image build failed"
    exit 1
fi

# Test different modes
echo "🧪 Testing container modes..."

# Test help mode
echo "📖 Testing help mode..."
if docker run --rm teamspeak-mcp:test help; then
    success "Help mode works"
else
    error "Help mode failed"
fi

# Test config mode
echo "⚙️ Testing config mode..."
if docker run --rm --env-file .env teamspeak-mcp:test config; then
    success "Config mode works"
else
    error "Config mode failed"
fi

# Test docker-compose (build only)
echo "🚢 Testing docker-compose..."
if docker-compose config > /dev/null; then
    success "docker-compose configuration is valid"
else
    error "docker-compose configuration is invalid"
    exit 1
fi

# Cleanup
echo "🧹 Cleaning up..."
docker rmi teamspeak-mcp:test 2>/dev/null || true

success "All Docker tests passed!"
echo ""
echo "🎯 Next steps:"
echo "1. Modify .env with your TeamSpeak parameters"
echo "2. Run: make setup"
echo "3. Then: make run" 