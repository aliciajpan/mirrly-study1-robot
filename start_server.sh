#!/bin/bash

# Robot Server Startup Script
# Simple script to start the robot control server on Raspberry Pi

set -e  # Exit on error

# Ensure GUI apps (e.g., video/image display) can open when launched over SSH
export DISPLAY=:0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check Python version
check_python() {
    print_info "Checking Python version..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 not found. Install with: sudo apt-get install python3"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -V 2>&1 | awk '{print $2}')
    print_success "Python $PYTHON_VERSION found"
}

# Check/install dependencies
check_dependencies() {
    print_info "Checking dependencies..."
    
    if ! python3 -c "import websockets" 2>/dev/null; then
        print_warning "websockets not installed"
        print_info "Installing: pip install websockets"
        pip install websockets
    else
        print_success "websockets installed"
    fi
    
    if ! python3 -c "from dynamixel_sdk import *" 2>/dev/null; then
        print_warning "dynamixel_sdk not installed"
        print_info "Installing: pip install dynamixel_sdk"
        pip install dynamixel_sdk
    else
        print_success "dynamixel_sdk installed"
    fi
    
    if ! python3 -c "import gpiozero" 2>/dev/null; then
        print_warning "gpiozero not installed"
        print_info "Installing: pip install gpiozero"
        pip install gpiozero
    else
        print_success "gpiozero installed"
    fi
}

# Check pigpiod (Raspberry Pi only)
check_pigpiod() {
    if [[ ! -f /proc/version ]] || ! grep -qi "raspberry" /proc/version; then
        return  # Not on Raspberry Pi
    fi
    
    print_info "Checking pigpiod daemon (Raspberry Pi)..."
    
    if ! pgrep -x "pigpiod" > /dev/null; then
        print_warning "pigpiod daemon not running"
        print_info "Starting pigpiod: sudo pigpiod"
        
        if sudo -n pigpiod 2>/dev/null; then
            sleep 1
            print_success "pigpiod daemon started"
        else
            print_error "Failed to start pigpiod (requires sudo)"
            print_info "Start manually with: sudo pigpiod"
            read -p "Continue without pigpiod? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    else
        print_success "pigpiod daemon already running"
    fi
}

# Check USB connection for head servos
check_usb() {
    print_info "Checking USB Dynamixel connection..."
    
    if [ -e /dev/ttyUSB0 ]; then
        print_success "USB serial device found: /dev/ttyUSB0"
    elif [ -e /dev/ttyUSB1 ]; then
        print_success "USB serial device found: /dev/ttyUSB1"
    else
        print_warning "No USB serial device found (/dev/ttyUSB*)"
        print_info "Head servos may not be available"
    fi
}

# Show help
show_help() {
    cat << EOF
${BLUE}Robot Server Startup Script${NC}

Usage: $0 [OPTIONS]

Options:
    --local         Listen on localhost only (for testing)
    --port PORT     Custom port (default: 8765)
    --host HOST     Custom host (default: 0.0.0.0)
    --no-check      Skip dependency checks
    --help          Show this help message

Examples:
    $0                      # Production mode on all interfaces
    $0 --local              # Development mode on localhost only
    $0 --port 9000          # Custom port
    $0 --host 192.168.1.100 # Specific host

EOF
}

# Parse arguments
SKIP_CHECK=false
LOCAL_MODE=false
PORT="8765"
HOST="0.0.0.0"

while [[ $# -gt 0 ]]; do
    case $1 in
        --local)
            LOCAL_MODE=true
            HOST="localhost"
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --no-check)
            SKIP_CHECK=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main execution
echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Mirrly Robot Server Startup Script    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Run checks
if [ "$SKIP_CHECK" = false ]; then
    check_python
    echo ""
    check_dependencies
    echo ""
    check_pigpiod
    echo ""
    check_usb
    echo ""
else
    print_warning "Skipping dependency checks (--no-check)"
fi

# Show startup info
print_info "Starting server..."
echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Server Configuration           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo -e "  Host:     ${YELLOW}$HOST${NC}"
echo -e "  Port:     ${YELLOW}$PORT${NC}"
echo -e "  Mode:     ${YELLOW}$([ "$LOCAL_MODE" = true ] && echo "Development" || echo "Production")${NC}"
echo -e "  WebSocket: ${YELLOW}ws://$HOST:$PORT${NC}"
echo ""
echo -e "${GREEN}Ready for connections!${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Start server
if [ "$LOCAL_MODE" = true ]; then
    python3 robot_server.py --local --port "$PORT"
else
    python3 robot_server.py --host "$HOST" --port "$PORT"
fi
