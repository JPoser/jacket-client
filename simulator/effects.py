"""
Reactive LED Effects Library

All effects animate transitions between colors when the server sends a new color.

Two types of effects:
1. Transition effects: transition(np, old_color, new_color, progress)
   - Animate from old to new color, progress 0.0 to 1.0

2. Buffer effects: update_from_buffer(np, color_buffer, progress)
   - Use history of recent colors for multi-color trails/stacks
   - color_buffer is list of (color, age) tuples, newest first
"""

import random
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

# Buffer settings
DEFAULT_BUFFER_SIZE = config.LEDS_PER_STRIP  # One color per row


# Color utilities

def lerp_color(c1, c2, t):
    """Linear interpolation between two RGB colors."""
    t = max(0, min(1, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def dim_color(color, factor):
    """Reduce brightness of a color."""
    factor = max(0, min(1, factor))
    return (
        int(color[0] * factor),
        int(color[1] * factor),
        int(color[2] * factor),
    )


def get_led_position(index):
    """Convert LED index to (strip, row) position."""
    strip = index // config.LEDS_PER_STRIP
    row = index % config.LEDS_PER_STRIP
    return strip, row


def get_led_index(strip, row):
    """Convert (strip, row) position to LED index."""
    return strip * config.LEDS_PER_STRIP + row


# Base effect class

class Effect:
    name = "base"

    def transition(self, np, old_color, new_color, progress):
        """Override this method to implement the effect."""
        raise NotImplementedError


# Fade effect

class Fade(Effect):
    name = "fade"

    def transition(self, np, old_color, new_color, progress):
        color = lerp_color(old_color, new_color, progress)
        for i in range(config.LED_COUNT):
            np[i] = color


# Wipe effects

class WipeDown(Effect):
    name = "wipe_down"

    def transition(self, np, old_color, new_color, progress):
        wipe_row = int(progress * (config.LEDS_PER_STRIP + 1))
        for i in range(config.LED_COUNT):
            strip, row = get_led_position(i)
            np[i] = new_color if row < wipe_row else old_color


class WipeUp(Effect):
    name = "wipe_up"

    def transition(self, np, old_color, new_color, progress):
        wipe_row = config.LEDS_PER_STRIP - int(progress * (config.LEDS_PER_STRIP + 1))
        for i in range(config.LED_COUNT):
            strip, row = get_led_position(i)
            np[i] = new_color if row >= wipe_row else old_color


class WipeLeft(Effect):
    name = "wipe_left"

    def transition(self, np, old_color, new_color, progress):
        wipe_strip = int(progress * (config.STRIP_COUNT + 1))
        for i in range(config.LED_COUNT):
            strip, row = get_led_position(i)
            np[i] = new_color if strip < wipe_strip else old_color


class WipeRight(Effect):
    name = "wipe_right"

    def transition(self, np, old_color, new_color, progress):
        wipe_strip = config.STRIP_COUNT - int(progress * (config.STRIP_COUNT + 1))
        for i in range(config.LED_COUNT):
            strip, row = get_led_position(i)
            np[i] = new_color if strip >= wipe_strip else old_color


# Chase effects with trails

class ChaseDown(Effect):
    name = "chase_down"
    trail_length = 6
    decay = 0.6

    def transition(self, np, old_color, new_color, progress):
        head_row = int(progress * (config.LEDS_PER_STRIP + self.trail_length))

        for i in range(config.LED_COUNT):
            strip, row = get_led_position(i)
            distance = head_row - row

            if distance < 0:
                # Ahead of the chase - still old color
                np[i] = old_color
            elif distance >= self.trail_length:
                # Behind the trail - fully new color
                np[i] = new_color
            else:
                # In the trail - blend with decay
                trail_factor = self.decay ** distance
                blended = lerp_color(new_color, old_color, trail_factor)
                np[i] = blended


class ChaseUp(Effect):
    name = "chase_up"
    trail_length = 6
    decay = 0.6

    def transition(self, np, old_color, new_color, progress):
        head_row = config.LEDS_PER_STRIP - 1 - int(progress * (config.LEDS_PER_STRIP + self.trail_length))

        for i in range(config.LED_COUNT):
            strip, row = get_led_position(i)
            distance = row - head_row

            if distance < 0:
                np[i] = old_color
            elif distance >= self.trail_length:
                np[i] = new_color
            else:
                trail_factor = self.decay ** distance
                blended = lerp_color(new_color, old_color, trail_factor)
                np[i] = blended


class ChaseSpiral(Effect):
    name = "chase_spiral"
    trail_length = 8
    decay = 0.65

    def transition(self, np, old_color, new_color, progress):
        total_leds = config.LED_COUNT
        head_pos = int(progress * (total_leds + self.trail_length))

        for i in range(config.LED_COUNT):
            strip, row = get_led_position(i)
            # Spiral order: go down each strip in sequence
            spiral_pos = strip * config.LEDS_PER_STRIP + row
            distance = head_pos - spiral_pos

            if distance < 0:
                np[i] = old_color
            elif distance >= self.trail_length:
                np[i] = new_color
            else:
                trail_factor = self.decay ** distance
                blended = lerp_color(new_color, old_color, trail_factor)
                np[i] = blended


# Other effects

class Dissolve(Effect):
    name = "dissolve"

    def __init__(self):
        self._order = None
        self._last_transition = None

    def transition(self, np, old_color, new_color, progress):
        # Generate random order once per transition
        transition_id = (old_color, new_color)
        if self._last_transition != transition_id:
            self._order = list(range(config.LED_COUNT))
            random.shuffle(self._order)
            self._last_transition = transition_id

        pixels_to_change = int(progress * config.LED_COUNT)

        for i in range(config.LED_COUNT):
            np[i] = old_color

        for i in range(pixels_to_change):
            np[self._order[i]] = new_color


class Expand(Effect):
    name = "expand"

    def transition(self, np, old_color, new_color, progress):
        center_strip = config.STRIP_COUNT / 2
        center_row = config.LEDS_PER_STRIP / 2
        max_dist = math.sqrt(center_strip**2 + center_row**2)

        expand_radius = progress * max_dist * 1.2  # Slight overshoot to ensure full coverage

        for i in range(config.LED_COUNT):
            strip, row = get_led_position(i)
            dist = math.sqrt((strip - center_strip + 0.5)**2 + (row - center_row + 0.5)**2)
            np[i] = new_color if dist <= expand_radius else old_color


# Buffer-based effects (use color history)

class BufferEffect(Effect):
    """Base class for effects that use color history buffer."""
    uses_buffer = True

    def transition(self, np, old_color, new_color, progress):
        """Fallback for non-buffer mode."""
        color = lerp_color(old_color, new_color, progress)
        for i in range(config.LED_COUNT):
            np[i] = color

    def update_from_buffer(self, np, color_buffer, frame):
        """Override this. frame is continuous integer counter for animation."""
        raise NotImplementedError


class ColourStack(BufferEffect):
    """Colours stack as rows with pulsing brightness animation."""
    name = "colour_stack"

    def update_from_buffer(self, np, color_buffer, frame):
        # Pulsing brightness based on frame
        pulse = 0.7 + 0.3 * math.sin(frame * 0.2)

        for i in range(config.LED_COUNT):
            strip, row = get_led_position(i)
            if row < len(color_buffer):
                # Newest color pulses more
                row_pulse = pulse if row == 0 else 1.0
                np[i] = dim_color(color_buffer[row], row_pulse)
            else:
                np[i] = (0, 0, 0)


class ColourRain(BufferEffect):
    """Colours continuously rain downward through the strips."""
    name = "colour_rain"

    def update_from_buffer(self, np, color_buffer, frame):
        if not color_buffer:
            return

        # Continuous downward movement
        offset = frame % (config.LEDS_PER_STRIP * 2)

        for i in range(config.LED_COUNT):
            strip, row = get_led_position(i)
            # Calculate which buffer color to show, scrolling down
            buffer_idx = (row + offset) % len(color_buffer)
            np[i] = color_buffer[buffer_idx]


class ColourTrail(BufferEffect):
    """Single bright LED trails down each strip with colour history."""
    name = "colour_trail"

    def update_from_buffer(self, np, color_buffer, frame):
        if not color_buffer:
            return

        # Trail head position cycles through rows
        head_pos = frame % config.LEDS_PER_STRIP
        trail_length = min(6, len(color_buffer))

        for i in range(config.LED_COUNT):
            strip, row = get_led_position(i)

            # Distance behind the head (wrapping)
            distance = (head_pos - row) % config.LEDS_PER_STRIP

            if distance < trail_length:
                # In the trail - use buffered color with fade
                color_idx = distance % len(color_buffer)
                fade = 0.9 ** distance
                np[i] = dim_color(color_buffer[color_idx], fade)
            else:
                np[i] = (0, 0, 0)


class ColourWaterfall(BufferEffect):
    """Colours cascade down with flowing animation and fading trails."""
    name = "colour_waterfall"
    trail_decay = 0.85

    def update_from_buffer(self, np, color_buffer, frame):
        if not color_buffer:
            return

        # Flowing offset
        flow_offset = frame % len(color_buffer)

        for i in range(config.LED_COUNT):
            strip, row = get_led_position(i)

            # Stagger strips for waterfall effect
            strip_offset = strip * 2
            buffer_idx = (row + flow_offset + strip_offset) % len(color_buffer)

            base_color = color_buffer[buffer_idx]
            # Fade based on row position
            fade = self.trail_decay ** (row % 8)
            np[i] = dim_color(base_color, fade)


class ColourWave(BufferEffect):
    """Colours flow in continuous sine wave pattern across strips."""
    name = "colour_wave"

    def update_from_buffer(self, np, color_buffer, frame):
        if not color_buffer:
            return

        for i in range(config.LED_COUNT):
            strip, row = get_led_position(i)

            # Sine wave offset per strip, animated by frame
            wave = math.sin(strip * 0.8 + frame * 0.15) * 3
            buffer_idx = int(row + wave + frame * 0.5) % len(color_buffer)

            np[i] = color_buffer[buffer_idx]


class ColourSpiral(BufferEffect):
    """Colours spiral continuously through the grid."""
    name = "colour_spiral"

    def update_from_buffer(self, np, color_buffer, frame):
        if not color_buffer:
            return

        for i in range(config.LED_COUNT):
            strip, row = get_led_position(i)

            # Spiral pattern animated by frame
            spiral_offset = strip * 3 + row + frame
            buffer_idx = spiral_offset % len(color_buffer)

            np[i] = color_buffer[buffer_idx]


# Effect registry

EFFECTS = {
    'fade': Fade(),
    'wipe_down': WipeDown(),
    'wipe_up': WipeUp(),
    'wipe_left': WipeLeft(),
    'wipe_right': WipeRight(),
    'chase_down': ChaseDown(),
    'chase_up': ChaseUp(),
    'chase_spiral': ChaseSpiral(),
    'dissolve': Dissolve(),
    'expand': Expand(),
    # Buffer-based effects
    'colour_stack': ColourStack(),
    'colour_rain': ColourRain(),
    'colour_trail': ColourTrail(),
    'colour_waterfall': ColourWaterfall(),
    'colour_wave': ColourWave(),
    'colour_spiral': ColourSpiral(),
}

BUFFER_EFFECTS = {name for name, eff in EFFECTS.items() if getattr(eff, 'uses_buffer', False)}


def get_effect(name):
    """Get an effect by name, default to fade."""
    return EFFECTS.get(name, EFFECTS['fade'])


def list_effects():
    """Return list of available effect names."""
    return list(EFFECTS.keys())


def is_buffer_effect(name):
    """Check if an effect uses the color buffer."""
    return name in BUFFER_EFFECTS
