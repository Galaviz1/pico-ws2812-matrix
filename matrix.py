"""Driver for an 8x8 WS2812B panel on a Raspberry Pi Pico (MicroPython).

Draw in panel coordinates, x left to right and y top to bottom, and this maps
each (x, y) to its position on the LED chain, so the code that draws never has
to know how the strip snakes through the panel.

Every show() also does two things the raw neopixel module doesn't:
  * scales by BRIGHTNESS, so colours can be written at full range (0-255)
  * estimates the current the frame will draw and scales it down to fit
    MAX_MA. A full-white 8x8 frame asks for ~3.8 A, enough to brown out
    a USB port. The estimate uses ~20 mA per colour channel at 255 and
    ~0.6 mA idle per LED, typical WS2812B figures.
"""

import machine
import neopixel

import config

MA_PER_CHANNEL = 20.0     # mA for one channel at 255
MA_IDLE_PER_LED = 0.6     # mA drawn by each LED even when dark


class Matrix:
    def __init__(self, pin=config.DATA_PIN, width=config.WIDTH, height=config.HEIGHT,
                 brightness=config.BRIGHTNESS, max_ma=config.MAX_MA):
        self.width = width
        self.height = height
        self.n = width * height
        self.brightness = brightness
        self.max_ma = max_ma
        self.np = neopixel.NeoPixel(machine.Pin(pin), self.n)
        self.fb = [(0, 0, 0)] * self.n          # logical, row-major: y * width + x
        self.last_ma = 0                         # estimate for the last frame shown
        # Panel tiling: map each grid cell -> (chain position, rotated 180?).
        # Falls back to a single full-size panel for older configs.
        panels = getattr(config, "PANELS", [(0, 0, False)])
        self._pw = getattr(config, "PANEL_W", width)
        self._ph = getattr(config, "PANEL_H", height)
        self._panels = {(gc, gr): (k, rot) for k, (gc, gr, rot) in enumerate(panels)}

    def index(self, x, y):
        """Chain position of the LED at display (x, y), across tiled panels."""
        pw, ph = self._pw, self._ph
        k, rot = self._panels.get((x // pw, y // ph), (0, False))
        lx, ly = x % pw, y % ph
        if rot:                                  # panel mounted turned 180
            lx, ly = pw - 1 - lx, ph - 1 - ly
        return k * pw * ph + self._panel_index(lx, ly, pw, ph)

    def _panel_index(self, x, y, w, h):
        """Chain position within one panel: its internal snake/flip mapping."""
        if config.FLIP_X:
            x = w - 1 - x
        if config.FLIP_Y:
            y = h - 1 - y
        if config.TRANSPOSE:
            x, y = y, x
        if config.SERPENTINE and (y & 1):
            x = w - 1 - x
        return y * w + x

    def set(self, x, y, rgb):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.fb[y * self.width + x] = rgb

    def fill(self, rgb):
        self.fb = [rgb] * self.n

    def clear(self):
        self.fill((0, 0, 0))

    def frame(self, pixels):
        """Load a whole frame: a list of width*height (r, g, b), row-major."""
        self.fb = list(pixels)

    def show(self):
        scale = self.brightness
        lit = 0
        for r, g, b in self.fb:
            lit += r + g + b
        idle = self.n * MA_IDLE_PER_LED
        want = lit * scale * MA_PER_CHANNEL / 255 + idle
        if want > self.max_ma and lit:
            scale *= max(0.0, (self.max_ma - idle)) / (want - idle)
        self.last_ma = lit * scale * MA_PER_CHANNEL / 255 + idle
        for y in range(self.height):
            for x in range(self.width):
                r, g, b = self.fb[y * self.width + x]
                self.np[self.index(x, y)] = (int(r * scale), int(g * scale), int(b * scale))
        self.np.write()

    def raw(self, i, rgb):
        """Set LED i on the chain directly, ignoring the mapping (for tests)."""
        s = self.brightness
        self.np[i] = (int(rgb[0] * s), int(rgb[1] * s), int(rgb[2] * s))
