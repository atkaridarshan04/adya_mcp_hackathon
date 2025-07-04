#!/bin/bash

# Script de tests d'intégration TeamSpeak MCP
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect architecture and set appropriate TeamSpeak image
ARCH=$(uname -m)
echo "🏗️  Detected architecture: $ARCH"

if [[ "$ARCH" == "arm64" || "$ARCH" == "aarch64" ]]; then
    echo "🍎 ARM64 detected - Using official TeamSpeak image with emulation"
    export TEAMSPEAK_IMAGE="teamspeak:latest"
    export TEAMSPEAK_PLATFORM="linux/amd64"
    echo "⚠️  Note: Running AMD64 image on ARM64 via emulation (slower but compatible)"
elif [[ "$ARCH" == "x86_64" || "$ARCH" == "amd64" ]]; then
    echo "💻 AMD64 detected - Using official TeamSpeak image"
    export TEAMSPEAK_IMAGE="teamspeak:latest"
    export TEAMSPEAK_PLATFORM=""
else
    echo "❌ Unsupported architecture: $ARCH"
    exit 1
fi

echo "📦 Using TeamSpeak image: $TEAMSPEAK_IMAGE"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Cleanup function
cleanup() {
    print_status "🧹 Cleaning up..."
    if command -v docker-compose >/dev/null 2>&1; then
        docker-compose -f docker-compose.test.yml down --volumes --remove-orphans >/dev/null 2>&1 || true
    else
        docker compose -f docker-compose.test.yml down --volumes --remove-orphans >/dev/null 2>&1 || true
    fi
}

# Trap cleanup on exit
trap cleanup EXIT

# Main script
print_status "🧪 Starting TeamSpeak MCP Integration Tests"
print_status "🏗️  Architecture: $ARCH"
print_status "📦 TeamSpeak Image: $TEAMSPEAK_IMAGE"

# Ensure directories exist
mkdir -p test_results scripts

# Clean up any existing containers
cleanup

# Start the integration test
print_status "🚀 Starting TeamSpeak 3 server..."

# Use the detected Docker Compose command
if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# Start TeamSpeak server with platform-specific image
$COMPOSE_CMD -f docker-compose.test.yml up -d teamspeak3-server

# Wait for server to be ready
print_status "⏳ Waiting for TeamSpeak server to be ready..."
timeout=180
counter=0

while [ $counter -lt $timeout ]; do
    if $COMPOSE_CMD -f docker-compose.test.yml exec -T teamspeak3-server nc -z localhost 10011 2>/dev/null; then
        print_success "TeamSpeak server is ready after ${counter}s"
        break
    fi
    
    if [ $((counter % 30)) -eq 0 ] && [ $counter -gt 0 ]; then
        print_status "⏳ Still waiting... (${counter}s elapsed)"
    fi
    
    if [ $counter -eq $timeout ]; then
        print_error "TeamSpeak server failed to start after ${timeout}s"
        print_status "📋 Server logs:"
        $COMPOSE_CMD -f docker-compose.test.yml logs teamspeak3-server
        exit 1
    fi
    
    sleep 1
    counter=$((counter + 1))
done

# Extract admin token if needed
print_status "🔑 Extracting admin token..."
$COMPOSE_CMD -f docker-compose.test.yml up token-extractor

# Run integration tests
print_status "🧪 Running integration tests..."

# Set environment variables
export TEAMSPEAK_HOST=teamspeak3-server
export TEAMSPEAK_PORT=10011
export TEAMSPEAK_USER=serveradmin
export TEAMSPEAK_SERVER_ID=1

if [ -f scripts/admin_token.txt ]; then
    export TEAMSPEAK_PASSWORD=$(cat scripts/admin_token.txt)
    print_status "🔑 Using extracted admin token"
else
    export TEAMSPEAK_PASSWORD=""
    print_warning "No admin token found, using empty password"
fi

# Run the actual integration tests
$COMPOSE_CMD -f docker-compose.test.yml run --rm \
    -e TEAMSPEAK_HOST=$TEAMSPEAK_HOST \
    -e TEAMSPEAK_PORT=$TEAMSPEAK_PORT \
    -e TEAMSPEAK_USER=$TEAMSPEAK_USER \
    -e TEAMSPEAK_PASSWORD="$TEAMSPEAK_PASSWORD" \
    -e TEAMSPEAK_SERVER_ID=$TEAMSPEAK_SERVER_ID \
    teamspeak-mcp-test integration-test

# Check results
if [ -f test_results/integration_results.json ]; then
    print_success "Integration tests completed!"
    
    # Display summary if jq is available
    if command -v jq >/dev/null 2>&1; then
        successes=$(jq '[.[] | select(.status == "SUCCESS")] | length' test_results/integration_results.json)
        failures=$(jq '[.[] | select(.status == "FAILURE")] | length' test_results/integration_results.json)
        total=$(jq 'length' test_results/integration_results.json)
        
        print_status "📊 Test Results Summary:"
        echo "  ✅ Successes: $successes"
        echo "  ❌ Failures: $failures"
        echo "  📊 Total: $total"
        echo "  🎯 Success rate: $(echo "scale=1; $successes * 100 / $total" | bc)%"
        
        if [ $failures -gt 0 ]; then
            echo ""
            print_warning "Failed tests:"
            jq -r '.[] | select(.status == "FAILURE") | "  • \(.tool): \(.message)"' test_results/integration_results.json
        fi
    else
        print_status "📄 Raw test results:"
        cat test_results/integration_results.json
    fi
else
    print_error "No test results found!"
    exit 1
fi

print_success "Integration tests completed successfully!" 