#!/usr/bin/env python3
"""
Jacket LED Simulator

Desktop simulator for the jacket-client that displays a 2D representation
of the LED strips in the terminal using ANSI colors.

Usage:
    uv run simulator.py                     # Default fade effect
    uv run simulator.py --effect chase_down # Specific effect
    uv run simulator.py --list              # List available effects
"""

import sys
from pathlib import Path

# Add parent directory to path to import shared config
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import requests
import time
import config
from effects import get_effect, list_effects, is_buffer_effect, DEFAULT_BUFFER_SIZE

# Transition settings
TRANSITION_DURATION = 1.0  # seconds
FRAME_RATE = 30  # fps
BUFFER_FRAME_RATE = 10  # fps for buffer effect animation
EFFECT_CHANGE_INTERVAL = 30  # Only allow effect change every N polls


class NeoPixelSimulator:
    """Simulates NeoPixel LED strip with terminal visualization."""

    def __init__(self, num_leds):
        self.num_leds = num_leds
        self.pixels = [(0, 0, 0)] * num_leds
        self.effect_name = None

    def __setitem__(self, index, color):
        if 0 <= index < self.num_leds:
            self.pixels[index] = color

    def __getitem__(self, index):
        return self.pixels[index]

    def write(self):
        """Render LEDs to terminal as 2D grid."""
        # Clear screen and move cursor to top
        sys.stdout.write('\033[2J\033[H')

        header = "Jacket Simulator - Press Ctrl+C to exit"
        if self.effect_name:
            header += f"  [Effect: {self.effect_name}]"
        print(header)
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


def run_transition(np, effect, old_color, new_color):
    """Run a transition animation from old_color to new_color."""
    frame_time = 1.0 / FRAME_RATE
    frames = int(TRANSITION_DURATION * FRAME_RATE)

    for frame in range(frames + 1):
        progress = frame / frames
        effect.transition(np, old_color, new_color, progress)
        np.write()
        time.sleep(frame_time)


def set_solid_color(np, color):
    """Set all LEDs to a solid color."""
    for i in range(config.LED_COUNT):
        np[i] = color


def fetch_color_and_effect(url, headers):
    """Fetch color and optional effect from server.

    Returns (color_tuple, effect_name) or (None, None) on error.
    Effect may be None if not specified by server.

    Expected API response format:
    {
        "color": {"rgb": [r, g, b]},
        "effect": "chase_down"  // optional
    }
    """
    try:
        response = requests.get(url, headers=headers, timeout=config.HTTP_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            color = None
            effect = None

            if 'color' in data and 'rgb' in data['color']:
                rgb = data['color']['rgb']
                if len(rgb) == 3:
                    color = tuple(rgb)

            if 'effect' in data:
                effect = data['effect']

            return color, effect
    except requests.exceptions.RequestException:
        pass
    return None, None


def run(effect_name='fade'):
    """Run simulator with dynamic effect switching from API."""
    print("Starting Jacket Simulator...")

    np = NeoPixelSimulator(config.LED_COUNT)
    effect = get_effect(effect_name)
    current_effect_name = effect.name
    np.effect_name = current_effect_name

    color_buffer = []  # List of colors, newest first (for buffer effects)
    current_color = (0, 0, 0)

    url = f"{config.SERVER_URL}/api/v1/color"
    headers = {'X-API-Key': config.API_KEY}

    # Counters
    frame_count = 0
    poll_count = 0
    last_effect_change_poll = 0

    frame_time = 1.0 / BUFFER_FRAME_RATE
    poll_interval_frames = int(config.POLL_INTERVAL * BUFFER_FRAME_RATE)

    # Startup indication
    set_solid_color(np, config.COLOR_STARTUP)
    np.write()
    time.sleep(0.5)

    try:
        while True:
            # Poll server periodically
            if frame_count % poll_interval_frames == 0:
                new_color, new_effect = fetch_color_and_effect(url, headers)
                poll_count += 1

                # Handle color
                if new_color is None:
                    new_color = config.COLOR_ERROR_NETWORK

                if new_color != current_color:
                    # For buffer effects, add to buffer
                    if is_buffer_effect(current_effect_name):
                        color_buffer.insert(0, new_color)
                        if len(color_buffer) > DEFAULT_BUFFER_SIZE:
                            color_buffer = color_buffer[:DEFAULT_BUFFER_SIZE]
                    else:
                        # For transition effects, run the transition
                        run_transition(np, effect, current_color, new_color)

                    current_color = new_color

                # Handle effect change (rate limited)
                if new_effect and new_effect in list_effects():
                    polls_since_change = poll_count - last_effect_change_poll
                    if new_effect != current_effect_name and polls_since_change >= EFFECT_CHANGE_INTERVAL:
                        print(f"Switching effect: {current_effect_name} -> {new_effect}")
                        current_effect_name = new_effect
                        effect = get_effect(new_effect)
                        np.effect_name = current_effect_name
                        last_effect_change_poll = poll_count

                        # Reset buffer for new effect
                        if is_buffer_effect(current_effect_name):
                            color_buffer = [current_color] if current_color else []

            # Update display
            if is_buffer_effect(current_effect_name):
                # Buffer effects animate continuously
                if color_buffer:
                    effect.update_from_buffer(np, color_buffer, frame_count)
                    np.write()
            # Transition effects only update on color change (handled above)

            frame_count += 1
            time.sleep(frame_time)

    except KeyboardInterrupt:
        sys.stdout.write('\033[2J\033[H')
        print("Simulator stopped.")


def main():
    parser = argparse.ArgumentParser(
        description='Jacket LED Simulator with transition effects'
    )
    parser.add_argument(
        '--effect', '-e',
        default='fade',
        help=f'Transition effect to use (default: fade)'
    )
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List available effects and exit'
    )

    args = parser.parse_args()

    if args.list:
        print("Available effects:")
        for name in list_effects():
            print(f"  {name}")
        return

    if args.effect not in list_effects():
        print(f"Unknown effect: {args.effect}")
        print(f"Available: {', '.join(list_effects())}")
        sys.exit(1)

    run(args.effect)


if __name__ == '__main__':
    main()
