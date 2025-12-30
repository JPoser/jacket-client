# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a MicroPython client designed to run on an ESP32 microcontroller. It polls a jacket-server for color data and controls a strip of NeoPixel LEDs accordingly.

## Architecture

- **client.py**: Main application loop that:
  - Manages WiFi connectivity with automatic reconnection
  - Polls the server's `/api/v1/color` endpoint every 5 seconds
  - Updates NeoPixel LEDs when color changes
  - Uses a 30-second watchdog timer for reliability
  - Shows error states via LED colors (red for network issues, orange for server errors)

- **config.py**: Configuration file containing WiFi credentials, server URL, API key, and LED settings (pin number, LED count)

## Development Notes

- This is MicroPython, not standard Python. Use MicroPython-specific modules:
  - `urequests` instead of `requests`
  - `ujson` instead of `json`
  - `machine` for hardware access (Pin, WDT)
  - `neopixel` for LED control
  - `network` for WiFi

- The client expects a server API returning JSON in format: `{"color": {"rgb": [r, g, b]}}`

- Default LED configuration: 21 LEDs on GPIO pin 2

## Deployment

### Prerequisites

1. **Install esptool** (for flashing MicroPython firmware):
   ```bash
   pip install esptool
   ```

2. **Install ampy** (for uploading files):
   ```bash
   pip install adafruit-ampy
   ```

3. **Download MicroPython firmware** for ESP32 from https://micropython.org/download/esp32/

### Step 1: Flash MicroPython Firmware

Find your ESP32's serial port:
- macOS: `/dev/tty.usbserial-*` or `/dev/tty.SLAB_USBtoUART`
- Linux: `/dev/ttyUSB0`
- Windows: `COM3` (check Device Manager)

Erase the flash and install MicroPython:
```bash
# Erase existing firmware
esptool.py --chip esp32 --port /dev/tty.usbserial-0001 erase_flash

# Flash MicroPython (replace with your firmware file)
esptool.py --chip esp32 --port /dev/tty.usbserial-0001 --baud 460800 write_flash -z 0x1000 esp32-20231005-v1.21.0.bin
```

### Step 2: Configure the Client

Edit `config.py` with your settings:
- `WIFI_SSID`: Your WiFi network name
- `WIFI_PASSWORD`: Your WiFi password
- `SERVER_URL`: jacket-server address (e.g., `http://192.168.1.100:5000`)
- `API_KEY`: API key matching your server configuration
- `LED_PIN`: GPIO pin connected to NeoPixel data line (default: 2)
- `LED_COUNT`: Number of LEDs in your strip (default: 21)

### Step 3: Upload Files

```bash
# Upload configuration
ampy --port /dev/tty.usbserial-0001 put config.py

# Upload main client code
ampy --port /dev/tty.usbserial-0001 put client.py

# Optional: rename client.py to main.py for auto-start on boot
ampy --port /dev/tty.usbserial-0001 put client.py main.py
```

### Step 4: Run the Client

Connect via serial to start manually or verify operation:
```bash
screen /dev/tty.usbserial-0001 115200
```

Then in the REPL:
```python
import client
client.run()
```

To exit screen: `Ctrl-A` then `K`, then `Y`

### Auto-Start on Boot

To run automatically when the ESP32 powers on, upload `client.py` as `main.py`:
```bash
ampy --port /dev/tty.usbserial-0001 put client.py main.py
```

### Troubleshooting

- **Permission denied on serial port (Linux)**: Add user to dialout group: `sudo usermod -a -G dialout $USER`
- **ampy timeout errors**: Try adding `--baud 115200` or unplugging/replugging the ESP32
- **Can't find serial port**: Ensure USB drivers are installed (CP210x or CH340 depending on your board)
