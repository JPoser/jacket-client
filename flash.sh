#!/bin/bash
#
# Jacket Client Flash Tool
# Usage:
#   ./flash.sh upload          - Upload config.py and client.py to ESP32
#   ./flash.sh flash <firmware> - Full flash: erase, install MicroPython, upload scripts
#   ./flash.sh monitor         - Open serial monitor
#
# Options:
#   -p, --port <port>  Specify serial port (default: auto-detect)
#   -b, --baud <baud>  Specify baud rate (default: 115200 for ampy, 460800 for esptool)
#
# Dependencies managed by uv (installed automatically on first run)
#

set -e

# Default values
PORT=""
BAUD_AMPY=115200
BAUD_ESPTOOL=460800

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Colour

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Check for uv
check_uv() {
    if ! command -v uv &> /dev/null; then
        error "uv is required but not installed.\nInstall from: https://docs.astral.sh/uv/getting-started/installation/"
    fi
}

# Auto-detect serial port
detect_port() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        PORT=$(ls /dev/tty.usbserial-* /dev/tty.SLAB_USBtoUART 2>/dev/null | head -n 1)
    elif [[ "$OSTYPE" == "linux"* ]]; then
        # Linux
        PORT=$(ls /dev/ttyUSB* 2>/dev/null | head -n 1)
    fi

    if [[ -z "$PORT" ]]; then
        error "No serial port detected. Connect ESP32 or specify port with -p"
    fi
    info "Detected port: $PORT"
}

# Run esptool via uv (using new 'esptool' command, not deprecated 'esptool.py')
run_esptool() {
    uv run --with esptool esptool "$@"
}

# Run ampy via uv
ampy() {
    uv run --with adafruit-ampy ampy "$@"
}

# Upload scripts to ESP32
cmd_upload() {
    check_uv
    [[ -z "$PORT" ]] && detect_port

    info "Uploading config.py..."
    ampy --port "$PORT" --baud "$BAUD_AMPY" put config.py

    info "Uploading client.py as main.py (auto-start on boot)..."
    ampy --port "$PORT" --baud "$BAUD_AMPY" put client.py main.py

    info "Upload complete! Reset ESP32 to start."
}

# Full flash: erase, install firmware, upload scripts
cmd_flash() {
    local firmware="$1"

    if [[ -z "$firmware" ]]; then
        error "Usage: $0 flash <firmware.bin>\nDownload firmware from https://micropython.org/download/esp32/"
    fi

    if [[ ! -f "$firmware" ]]; then
        error "Firmware file not found: $firmware"
    fi

    check_uv
    [[ -z "$PORT" ]] && detect_port

    info "Erasing flash..."
    run_esptool --chip esp32 --port "$PORT" erase-flash

    info "Flashing MicroPython firmware..."
    run_esptool --chip esp32 --port "$PORT" --baud "$BAUD_ESPTOOL" \
        write-flash -z 0x1000 "$firmware"

    info "Waiting for ESP32 to restart..."
    sleep 3

    cmd_upload
}

# Open serial monitor
cmd_monitor() {
    [[ -z "$PORT" ]] && detect_port

    info "Opening serial monitor (Ctrl+A then K to exit)..."
    screen "$PORT" 115200
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -b|--baud)
            BAUD_AMPY="$2"
            shift 2
            ;;
        upload)
            shift
            cmd_upload
            exit 0
            ;;
        flash)
            shift
            cmd_flash "$1"
            exit 0
            ;;
        monitor)
            shift
            cmd_monitor
            exit 0
            ;;
        -h|--help|*)
            echo "Jacket Client Flash Tool"
            echo ""
            echo "Usage:"
            echo "  $0 upload              Upload config.py and client.py to ESP32"
            echo "  $0 flash <firmware>    Full flash: erase, install MicroPython, upload"
            echo "  $0 monitor             Open serial monitor"
            echo ""
            echo "Options:"
            echo "  -p, --port <port>      Specify serial port (default: auto-detect)"
            echo "  -b, --baud <baud>      Specify baud rate for ampy (default: 115200)"
            echo ""
            echo "Examples:"
            echo "  $0 upload"
            echo "  $0 -p /dev/ttyUSB0 upload"
            echo "  $0 flash esp32-20231005-v1.21.0.bin"
            echo ""
            echo "Dependencies (esptool, ampy) are managed automatically by uv."
            exit 0
            ;;
    esac
done

# No command specified
echo "Usage: $0 [options] <command>"
echo "Run '$0 --help' for more information."
exit 1
