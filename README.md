# Jacket Client

MicroPython client for ESP32 that controls NeoPixel LED strips on a jacket. Polls a jacket-server for color data and updates the LEDs accordingly.

## Features

- WiFi connectivity with automatic reconnection
- Polls server every 5 seconds for color updates
- 30-second watchdog timer for reliability
- Visual error indication (red = network error, orange = server error)
- Desktop simulator for testing without hardware

## Hardware

- ESP32 microcontroller
- 6 vertical NeoPixel strips × 14 LEDs = 84 total
- Strips wired top-to-bottom on GPIO pin 2

## Quick Start

### 1. Install uv

[uv](https://docs.astral.sh/uv/) manages Python dependencies automatically.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Configure

Copy the example config and fill in your values:

```bash
cp config.example.py config.py
```

Edit `config.py` with your settings:

```python
WIFI_SSID = 'your_wifi'
WIFI_PASSWORD = 'your_password'
SERVER_URL = 'http://192.168.1.100:5000'
API_KEY = 'your_api_key'
```

`config.py` is gitignored to keep your secrets safe.

### 3. Flash and upload

```bash
# First time: full flash with MicroPython firmware
./flash.sh flash esp32-v1.21.0.bin

# After that: just upload code changes
./flash.sh upload

# Monitor serial output
./flash.sh monitor
```

Download MicroPython firmware from https://micropython.org/download/esp32/

## flash.sh Commands

| Command | Description |
|---------|-------------|
| `./flash.sh upload` | Upload config.py and client.py to ESP32 |
| `./flash.sh flash <firmware>` | Full flash: erase, install firmware, upload |
| `./flash.sh monitor` | Open serial monitor (Ctrl+A, K to exit) |
| `./flash.sh -p /dev/ttyUSB0 upload` | Specify serial port manually |

Dependencies (esptool, ampy) are installed automatically by uv on first run.

## Simulator

Test LED patterns without hardware:

```bash
cd simulator
uv run simulator.py
```

Renders a 6×14 grid in your terminal matching the physical jacket layout. Connects to your configured server for live color updates.

See [simulator/README.md](simulator/README.md) for details.

## API

The client expects the server to return JSON in this format:

```json
{"color": {"rgb": [255, 100, 50]}}
```

## Troubleshooting

- **Permission denied on serial port (Linux)**: `sudo usermod -a -G dialout $USER`
- **ampy timeout errors**: Try `./flash.sh -b 115200 upload` or replug the ESP32
- **Can't find serial port**: Install USB drivers (CP210x or CH340 depending on board)
