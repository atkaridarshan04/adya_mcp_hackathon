#!/bin/bash
set -e

# Docker entrypoint script for TeamSpeak MCP
# Allows different execution modes

# Colors for logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" >&2
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" >&2
}

# Debug function to show all environment variables
debug_env() {
    log "🔍 Environment Variables Debug:"
    echo "All TEAMSPEAK_* variables:" >&2
    env | grep "^TEAMSPEAK_" | while read -r line; do
        key=$(echo "$line" | cut -d'=' -f1)
        if [[ "$key" == "TEAMSPEAK_PASSWORD" ]]; then
            echo "  $key=[REDACTED]" >&2
        else
            echo "  $line" >&2
        fi
    done
    echo "" >&2
    echo "All environment variables count: $(env | wc -l)" >&2
    echo "Docker-related variables:" >&2
    env | grep -E "^(PATH|HOME|USER|HOSTNAME)" | head -5 >&2
}

# Check required environment variables
check_env() {
    log "Checking configuration..."
    
    if [ -z "$TEAMSPEAK_HOST" ]; then
        error "TEAMSPEAK_HOST is required"
        exit 1
    fi
    
    if [ -z "$TEAMSPEAK_PASSWORD" ]; then
        error "TEAMSPEAK_PASSWORD is required"
        exit 1
    fi
    
    success "Configuration validated"
}

# Test TeamSpeak connection
test_connection() {
    log "Testing TeamSpeak server connection..."
    
    if python test_mcp.py; then
        success "TeamSpeak connection successful"
    else
        error "TeamSpeak connection failed"
        exit 1
    fi
}

# Display configuration (without secrets)
show_config() {
    log "TeamSpeak MCP Configuration:"
    echo "  Host: $TEAMSPEAK_HOST" >&2
    echo "  Port: ${TEAMSPEAK_PORT:-10011}" >&2
    echo "  User: ${TEAMSPEAK_USER:-serveradmin}" >&2
    echo "  Server ID: ${TEAMSPEAK_SERVER_ID:-1}" >&2
    echo "  Password: [REDACTED]" >&2
}

# Main mode handler
case "${1:-server}" in
    "server")
        log "🚀 Starting TeamSpeak MCP server..."
        debug_env
        show_config
        check_env
        
        # Optional connection test
        if [ "${SKIP_CONNECTION_TEST:-false}" != "true" ]; then
            test_connection
        fi
        
        log "Launching MCP server..."
        exec python -m teamspeak_mcp.server
        ;;
        
    "server-cli")
        log "🚀 Starting TeamSpeak MCP server with CLI args..."
        # Pass all arguments except the first one to the Python server
        shift
        exec python -m teamspeak_mcp.server "$@"
        ;;
        
    "test")
        log "🧪 Test mode - Checking configuration..."
        show_config
        check_env
        test_connection
        success "All tests passed!"
        ;;
        
    "integration-test")
        log "🧪 Running comprehensive integration tests..."
        
        # Vérifier que le fichier de test existe
        if [ ! -f "/app/tests/test_integration.py" ]; then
            error "Integration test file not found at /app/tests/test_integration.py"
            exit 1
        fi
        
        # Attendre que le serveur TeamSpeak soit prêt
        if [ "$TEAMSPEAK_HOST" != "localhost" ] && [ "$TEAMSPEAK_HOST" != "127.0.0.1" ]; then
            log "⏳ Waiting for TeamSpeak server to be ready..."
            log "🔍 Connection target: $TEAMSPEAK_HOST:${TEAMSPEAK_PORT:-10011}"
            
            # Debug network connectivity
            log "🌐 Network debugging:"
            echo "  DNS resolution test:" >&2
            nslookup "$TEAMSPEAK_HOST" 2>/dev/null || echo "  DNS resolution failed" >&2
            echo "  Network interfaces:" >&2
            ip addr show 2>/dev/null || ifconfig 2>/dev/null || echo "  No network info available" >&2
            echo "  Routing table:" >&2
            ip route 2>/dev/null || route -n 2>/dev/null || echo "  No routing info available" >&2
            
            # Check if nc is available
            if ! command -v nc >/dev/null 2>&1; then
                error "netcat (nc) not available in container"
                log "Available network tools:"
                command -v wget >/dev/null 2>&1 && echo "  wget: available" >&2
                command -v curl >/dev/null 2>&1 && echo "  curl: available" >&2
                command -v telnet >/dev/null 2>&1 && echo "  telnet: available" >&2
                command -v python3 >/dev/null 2>&1 && echo "  python3: available" >&2
            fi
            
            for i in {1..180}; do
                # Try multiple connection methods
                connected=false
                
                # Method 1: netcat
                if command -v nc >/dev/null 2>&1; then
                    if nc -z "$TEAMSPEAK_HOST" "${TEAMSPEAK_PORT:-10011}" 2>/dev/null; then
                        connected=true
                        method="netcat"
                    fi
                fi
                
                # Method 2: Python socket (fallback)
                if [ "$connected" = false ] && command -v python3 >/dev/null 2>&1; then
                    if python3 -c "
import socket
import sys
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex(('$TEAMSPEAK_HOST', ${TEAMSPEAK_PORT:-10011}))
    sock.close()
    sys.exit(0 if result == 0 else 1)
except Exception as e:
    sys.exit(1)
" 2>/dev/null; then
                        connected=true
                        method="python"
                    fi
                fi
                
                # Method 3: wget (fallback)
                if [ "$connected" = false ] && command -v wget >/dev/null 2>&1; then
                    if wget --spider --timeout=5 "http://$TEAMSPEAK_HOST:${TEAMSPEAK_PORT:-10011}" 2>/dev/null; then
                        connected=true
                        method="wget"
                    fi
                fi
                
                if [ "$connected" = true ]; then
                    success "TeamSpeak server is ready after ${i}s (via $method)"
                    break
                fi
                
                # Log progress every 30 seconds with detailed info
                if [ $((i % 30)) -eq 0 ]; then
                    log "⏳ Still waiting... (${i}s elapsed)"
                    echo "  Connection attempts:" >&2
                    echo "    Target: $TEAMSPEAK_HOST:${TEAMSPEAK_PORT:-10011}" >&2
                    echo "    Container hostname: $(hostname)" >&2
                    echo "    Container IP: $(hostname -i 2>/dev/null || echo 'unknown')" >&2
                    
                    # Test alternative connection methods
                    if command -v ping >/dev/null 2>&1; then
                        echo "  Ping test:" >&2
                        ping -c 1 "$TEAMSPEAK_HOST" 2>&1 | head -3 >&2 || echo "    Ping failed" >&2
                    fi
                fi
                
                if [ $i -eq 180 ]; then
                    error "TeamSpeak server not ready after 180 seconds"
                    log "🔧 Final diagnostics:"
                    echo "  Environment:" >&2
                    echo "    TEAMSPEAK_HOST=$TEAMSPEAK_HOST" >&2
                    echo "    TEAMSPEAK_PORT=${TEAMSPEAK_PORT:-10011}" >&2
                    echo "  Network tools available:" >&2
                    command -v nc >/dev/null 2>&1 && echo "    nc: yes" >&2 || echo "    nc: no" >&2
                    command -v python3 >/dev/null 2>&1 && echo "    python3: yes" >&2 || echo "    python3: no" >&2
                    command -v wget >/dev/null 2>&1 && echo "    wget: yes" >&2 || echo "    wget: no" >&2
                    exit 1
                fi
                sleep 1
            done
        fi
        
        log "🚀 Starting integration tests..."
        show_config
        
        # Créer le dossier de résultats
        mkdir -p /app/test_results
        
        # Lancer les tests d'intégration
        exec python3 /app/tests/test_integration.py
        ;;
        
    "debug")
        log "🔍 Debug mode - Full environment analysis..."
        debug_env
        show_config
        echo "" >&2
        echo "Current working directory: $(pwd)" >&2
        echo "Python version: $(python --version)" >&2
        echo "Available Python packages:" >&2
        pip list | grep -E "(mcp|ts3|pydantic)" >&2 || echo "  No relevant packages found" >&2
        ;;
        
    "shell"|"bash")
        log "🐚 Shell mode - Opening interactive shell..."
        exec /bin/bash
        ;;
        
    "config")
        log "⚙️ Displaying configuration:"
        show_config
        ;;
        
    "help"|"--help"|"-h")
        echo "TeamSpeak MCP Docker - Available modes:" >&2
        echo "" >&2
        echo "  server (default)     - Launch MCP server with env vars" >&2
        echo "  server-cli           - Launch MCP server with CLI args" >&2
        echo "  test                 - Basic connection tests" >&2
        echo "  integration-test     - Comprehensive tool testing" >&2
        echo "  debug                - Full environment analysis" >&2
        echo "  shell|bash           - Interactive shell" >&2
        echo "  config               - Display configuration" >&2
        echo "  help                 - This help" >&2
        echo "" >&2
        echo "Required environment variables (server mode):" >&2
        echo "  TEAMSPEAK_HOST       - TeamSpeak server address" >&2
        echo "  TEAMSPEAK_PASSWORD   - ServerQuery password" >&2
        echo "" >&2
        echo "CLI arguments (server-cli mode):" >&2
        echo "  --host HOST          - TeamSpeak server address" >&2
        echo "  --port PORT          - ServerQuery port (default: 10011)" >&2
        echo "  --user USER          - ServerQuery user (default: serveradmin)" >&2
        echo "  --password PASS      - ServerQuery password" >&2
        echo "  --server-id ID       - Virtual server ID (default: 1)" >&2
        echo "" >&2
        echo "Optional variables:" >&2
        echo "  TEAMSPEAK_PORT       - ServerQuery port (default: 10011)" >&2
        echo "  TEAMSPEAK_USER       - ServerQuery user (default: serveradmin)" >&2
        echo "  TEAMSPEAK_SERVER_ID  - Virtual server ID (default: 1)" >&2
        echo "  SKIP_CONNECTION_TEST - Skip connection tests (default: false)" >&2
        echo "" >&2
        echo "🧪 Integration Test Mode:" >&2
        echo "  integration-test     - Test all 20 MCP tools with real TS3 server" >&2
        echo "  Results saved in: /app/test_results/integration_results.json" >&2
        ;;
        
    *)
        # If command doesn't match any mode, execute it directly
        log "🔧 Executing custom command: $*"
        exec "$@"
        ;;
esac 