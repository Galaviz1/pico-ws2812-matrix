# Settings for the 8x8 WS2812B panel. Shared by sign.py and test_matrix.py.

# Pico GPIO wired to the panel's DIN (through a 330 ohm resistor).
# GP2 is physical pin 4.
DATA_PIN = 2

WIDTH = 8
HEIGHT = 8

# How the LED chain snakes through the panel. Run test_matrix.py to find out:
# it lights the LEDs in chain order, then marks the four corners.
#   SERPENTINE  rows alternate direction (true for BTF-LIGHTING 8x8 panels)
#   FLIP_X      mirror left/right
#   FLIP_Y      mirror top/bottom
#   TRANSPOSE   the chain runs in columns instead of rows
# Orientation as mounted on the bench (2026-10-08). LED 0, where the input
# wires attach, is the BOTTOM-LEFT LED and the chain runs right along the
# bottom row, zig-zagging upward: FLIP_Y is the one mapping needed. Measured
# with the board really running no flips (corner test: blue top-left, red
# bottom-left; test "P" photographed as a "b"). Earlier changes here had not
# reached the board: see the module-cache note in run_on_pico.sh.
SERPENTINE = True
FLIP_X = False
FLIP_Y = True
TRANSPOSE = False

# Which edge the scrolling text comes in from: "left" (moves left to right) or
# "right" (moves right to left). Only the motion changes; the letters stay
# upright and unmirrored either way. "right" reads in normal word order.
SCROLL_FROM = "right"

# 0.0 to 1.0. WS2812Bs are very bright; 0.1 is plenty indoors and on camera.
BRIGHTNESS = 0.1

# Current budget in mA. Every frame is scaled down if it would draw more.
# 300 mA is safe when the panel's 5 V comes from the Pico's VBUS (USB).
# With an external 5 V supply, raise it to that supply's rating.
MAX_MA = 300
