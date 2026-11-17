#!/bin/bash
#
# Sus Party Sonos Connector - Setup & Start Script
# ================================================
# This script will:
#   1. Check for Python 3
#   2. Create a virtual environment (if needed)
#   3. Install dependencies (again whenever requirements.txt changes)
#   4. Start the connector
#
# Usage:
#   ./start.sh [room_code] [options]
#
# Examples:
#   ./start.sh
#   ./start.sh ABCD
#   ./start.sh ABCD --volume 50
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/.venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
MAIN_SCRIPT="$SCRIPT_DIR/sonos_connector.py"

# ============ Helper Functions ============

print_banner() {
    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                           ║${NC}"
    echo -e "${BLUE}║     🎮 SUS PARTY - SONOS CONNECTOR 🔊                     ║${NC}"
    echo -e "${BLUE}║                                                           ║${NC}"
    echo -e "${BLUE}║     Setup & Launch Script                                 ║${NC}"
    echo -e "${BLUE}║                                                           ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============ Dependency Checks ============

check_python() {
    log_info "Checking for Python 3..."
    
    # Try different Python commands
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        # Check if 'python' is Python 3
        if python --version 2>&1 | grep -q "Python 3"; then
            PYTHON_CMD="python"
        else
            log_error "Python command found but it's Python 2. Please install Python 3."
            exit 1
        fi
    else
        log_error "Python 3 is not installed!"
        echo ""
        echo "Please install Python 3:"
        echo "  macOS:   brew install python3"
        echo "  Ubuntu:  sudo apt install python3 python3-venv python3-pip"
        echo "  Windows: Download from https://www.python.org/downloads/"
        exit 1
    fi
    
    # Verify Python version is 3.10+
    PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PYTHON_MAJOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.major)')
    PYTHON_MINOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.minor)')
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
        log_error "Python 3.10+ is required. Found Python $PYTHON_VERSION"
        exit 1
    fi
    
    log_info "Found Python $PYTHON_VERSION ✓"
}

# ============ Virtual Environment ============

setup_venv() {
    if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/activate" ]; then
        log_info "Virtual environment found ✓"
    else
        log_info "Creating virtual environment..."
        $PYTHON_CMD -m venv "$VENV_DIR"
        if [ $? -ne 0 ]; then
            log_error "Failed to create virtual environment"
            echo ""
            echo "Try installing venv:"
            echo "  Ubuntu/Debian: sudo apt install python3-venv"
            echo "  macOS: It should be included with Python 3"
            exit 1
        fi
        log_info "Virtual environment created ✓"
    fi
    
    # Activate the virtual environment
    source "$VENV_DIR/bin/activate"
    log_info "Virtual environment activated ✓"
}

# ============ Dependencies ============

install_dependencies() {
    log_info "Checking dependencies..."

    # Install again only when requirements.txt changed since the last install,
    # so updating the connector (git pull) also updates its libraries.
    STAMP="$VENV_DIR/.requirements-installed"
    if [ -f "$STAMP" ] && cmp -s "$REQUIREMENTS_FILE" "$STAMP" && \
       python -c "import socketio, websocket, soco, requests" 2>/dev/null; then
        log_info "All dependencies already installed ✓"
        return 0
    fi

    log_info "Installing dependencies..."
    pip install --upgrade pip --quiet 2>/dev/null || true
    if ! pip install -r "$REQUIREMENTS_FILE" --upgrade --quiet; then
        log_error "Failed to install dependencies"
        exit 1
    fi
    cp "$REQUIREMENTS_FILE" "$STAMP"

    log_info "Dependencies installed ✓"
}

# ============ Network Check ============

check_network() {
    log_info "Checking that the game server is reachable..."

    if command -v curl &> /dev/null && ! curl -fsS -m 5 -o /dev/null https://susparty.com/health 2>/dev/null; then
        log_warn "Cannot reach the game server (susparty.com)"
        log_warn "Make sure this computer is online"
    else
        log_info "Game server reachable ✓"
    fi
}

# ============ Main ============

main() {
    print_banner
    
    # Run setup
    check_python
    setup_venv
    install_dependencies
    check_network
    
    echo ""
    log_info "Setup complete! Starting Sonos Connector..."
    echo ""
    echo "────────────────────────────────────────────────────────────"
    echo ""
    
    # Run the main script with all passed arguments
    python "$MAIN_SCRIPT" "$@"
}

# Run main with all script arguments
main "$@"
