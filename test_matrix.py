"""Bring-up test for the display. Run this before anything else.

    ./run_on_pico.sh test_matrix.py

Works for one 8x8 panel or two chained side by side (16x8) — it uses the size
and tiling from config.py.

1. Chain order: lights the LEDs one at a time in the order the data reaches
   them (raw index 0..n-1, no mapping). Watch where #0 is and which way the
   chain snakes. With two panels, note which physical panel lights FIRST and
   which lights SECOND — that is the chain order. If the right panel lights
   first, swap the two rows in config.PANELS.
2. Corners, through the mapping in config.py — on the WHOLE display:
       top-left RED     top-right GREEN
       bottom-left BLUE bottom-right WHITE
   If they land elsewhere on a single panel, adjust FLIP_X / FLIP_Y /
   TRANSPOSE / SERPENTINE. If one panel is correct but the other is
   upside-down/mirrored, set that panel's rotate180 to True in config.PANELS.
3. Colour order: the whole panel red, then green, then blue. If red shows
   as green, the panel isn't the usual GRB WS2812B.
4. A diagonal: should run from top-left to bottom-right.
"""

import time

import config
from matrix import Matrix

m = Matrix()
n = m.n


def pause(ms):
    time.sleep_ms(ms)


try:
    print("1/4 chain order: LED 0 to %d, one at a time" % (n - 1))
    for i in range(n):
        for j in range(n):
            m.raw(j, (0, 0, 0))
        m.raw(i, (255, 255, 255))
        m.np.write()
        if i % 8 == 0:
            print("   LED %d" % i)
        pause(80)

    print("2/4 corners: TL red, TR green, BL blue, BR white")
    m.clear()
    m.set(0, 0, (255, 0, 0))
    m.set(config.WIDTH - 1, 0, (0, 255, 0))
    m.set(0, config.HEIGHT - 1, (0, 0, 255))
    m.set(config.WIDTH - 1, config.HEIGHT - 1, (255, 255, 255))
    m.show()
    pause(4000)

    for name, rgb in (("red", (255, 0, 0)), ("green", (0, 255, 0)), ("blue", (0, 0, 255))):
        m.fill(rgb)
        m.show()
        print("3/4 colour: whole panel %s  (estimated %d mA)" % (name, m.last_ma))
        pause(1200)

    print("4/4 diagonal: top-left to bottom-right")
    m.clear()
    for k in range(min(config.WIDTH, config.HEIGHT)):
        m.set(k, k, (255, 160, 0))
        m.show()
        pause(150)
    pause(1500)
    print("done")
finally:
    m.clear()
    m.show()
