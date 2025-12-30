#!/usr/bin/env python3
"""
Jacket LED Simulator

Desktop simulator for the jacket-client that displays a 2D representation
of the LED strips in the terminal using ANSI colors.

Usage: uv run simulator.py
"""

import sys
from pathlib import Path

# Add parent directory to path to import shared config
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import time
import config


class NeoPixelSimulator:
    """Simulates NeoPixel LED strip with terminal visualization."""

    def __init__(self, num_leds):
        self.num_leds = num_leds
        self.pixels = [(0, 0, 0)] * num_leds

    def __setitem__(self, index, color):
        if 0 <= index < self.num_leds:
            self.pixels[index] = color

    def __getitem__(self, index):
        return self.pixels[index]

    def write(self):
        """Render LEDs to terminal as 2D grid."""
        # Clear screen and move cursor to top
        sys.stdout.write('\033[2J\033[H')

        print("Jacket Simulator - Press Ctrl+C to exit")
        print(f"Server: {config.SERVER_URL}/api/v1/color\n")

        # Render as 2D grid (rows x columns)
        for row in range(config.LEDS_PER_STRIP):
            line = "  "
            for strip in range(config.STRIP_COUNT):
                led_index = strip * config.LEDS_PER_STRIP + row
                r, g, b = self.pixels[led_index]
                # ANSI 24-bit color: \033[48;2;R;G;Bm for background
                line += f"\033[48;2;{r};{g};{b}m  \033[0m  "
            print(line)

        # Show current color value
        if all(p == self.pixels[0] for p in self.pixels):
            print(f"\nColor: {self.pixels[0]}")
        else:
            print("\nColor: (mixed)")

        sys.stdout.flush()


def update_leds(np, target_color, current_color):
    """Update LEDs only if color has changed."""
    if current_color != target_color:
        for i in range(config.LED_COUNT):
            np[i] = target_color
        np.write()
        return target_color
    return current_color


def run():
    print("Starting Jacket Simulator...")

    np = NeoPixelSimulator(config.LED_COUNT)
    current_color = (0, 0, 0)

    # Startup indication
    current_color = update_leds(np, config.COLOR_STARTUP, current_color)
    time.sleep(0.5)
    current_color = update_leds(np, config.COLOR_OFF, current_color)

    url = f"{config.SERVER_URL}/api/v1/color"
    headers = {'X-API-Key': config.API_KEY}

    try:
        while True:
            try:
                response = requests.get(url, headers=headers, timeout=config.HTTP_TIMEOUT)

                if response.status_code == 200:
                    data = response.json()
                    if 'color' in data and 'rgb' in data['color']:
                        rgb = data['color']['rgb']
                        if len(rgb) == 3:
                            new_color = tuple(rgb)
                            current_color = update_leds(np, new_color, current_color)
                else:
                    current_color = update_leds(np, config.COLOR_ERROR_SERVER, current_color)

            except requests.exceptions.RequestException as e:
                current_color = update_leds(np, config.COLOR_ERROR_NETWORK, current_color)
                # Re-render to show error message
                np.write()
                print(f"Network error: {e}")

            time.sleep(config.POLL_INTERVAL)

    except KeyboardInterrupt:
        # Clear screen and show exit message
        sys.stdout.write('\033[2J\033[H')
        print("Simulator stopped.")


if __name__ == '__main__':
    run()
