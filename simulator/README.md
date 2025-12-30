# Jacket Simulator

Desktop simulator for testing jacket LED patterns without flashing to the ESP32.

## Requirements

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- A terminal with 24-bit color support (most modern terminals)

## Setup

Configure `../config.py` with your server details:

```python
SERVER_URL = 'http://192.168.1.100:5000'
API_KEY = 'your_api_key_here'
```

## Running

```bash
uv run simulator.py
```

Or without uv:

```bash
pip install requests
python simulator.py
```

## Display

The simulator renders a 6x14 grid matching the physical jacket layout:

```
  ██  ██  ██  ██  ██  ██
  ██  ██  ██  ██  ██  ██
  ██  ██  ██  ██  ██  ██
  ...
```

Each column represents one LED strip (6 total), each row represents one LED position (14 per strip).

## LED Mapping

Strips are wired top-to-bottom:
- Strip 0: LEDs 0-13
- Strip 1: LEDs 14-27
- Strip 2: LEDs 28-41
- Strip 3: LEDs 42-55
- Strip 4: LEDs 56-69
- Strip 5: LEDs 70-83

## Status Colors

- Blue flash on startup
- Red: Network/WiFi error
- Orange: Server error

Press `Ctrl+C` to exit.
