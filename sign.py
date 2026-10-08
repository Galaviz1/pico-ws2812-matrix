"""Channel sign for an 8x8 WS2812B panel: Paradox Transistor Lab.

Loop: a rainbow wipe, the YouTube play logo fading in, the channel name
scrolling across in a moving rainbow, then the logo again.

    ./run_on_pico.sh sign.py          run it (Ctrl-C stops and blanks the panel)
    python3 preview.py                render the same frames to docs/sign.gif

frames() only computes colours, with no hardware imports, so preview.py draws
exactly what the panel will show. main() is the part that needs a Pico.
"""

from font import text_columns

TEXT = "Paradox Transistor Lab"
SCROLL_MS = 55            # per 1-column step: ~18 columns per second
W = H = 8

RED = (255, 0, 0)
WHITE = (255, 255, 255)
OFF = (0, 0, 0)

# YouTube play button: red rounded body, white triangle. 'R' red, 'W' white.
LOGO = [
    "........",
    ".RRRRRR.",
    "RRRWRRRR",
    "RRRWWRRR",
    "RRRWWRRR",
    "RRRWRRRR",
    ".RRRRRR.",
    "........",
]


def hsv(h, s=1.0, v=1.0):
    """h in 0..1 -> (r, g, b) 0..255."""
    i = int(h * 6) % 6
    f = h * 6 - int(h * 6)
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    r, g, b = [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][i]
    return (int(r * 255), int(g * 255), int(b * 255))


def blank():
    return [OFF] * (W * H)


def logo_frame(level=1.0):
    px = []
    for row in LOGO:
        for ch in row:
            c = RED if ch == "R" else WHITE if ch == "W" else OFF
            px.append((int(c[0] * level), int(c[1] * level), int(c[2] * level)))
    return px


def wipe():
    """Rainbow diagonal sweeping in, then out."""
    for step in range(W + H):
        px = blank()
        for y in range(H):
            for x in range(W):
                if x + y <= step:
                    px[y * W + x] = hsv((x + y) / (W + H))
        yield px, 30
    for step in range(W + H):
        px = blank()
        for y in range(H):
            for x in range(W):
                if x + y > step:
                    px[y * W + x] = hsv((x + y) / (W + H))
        yield px, 30


def logo(hold_ms=1500):
    for i in range(1, 11):
        yield logo_frame(i / 10), 40
    yield logo_frame(), hold_ms
    for i in range(9, -1, -1):
        yield logo_frame(i / 10), 30


def scroll(text=TEXT, step_ms=SCROLL_MS):
    """Text enters from the right and leaves on the left, in a moving rainbow."""
    strip = [0] * W + text_columns(text) + [0] * W
    for offset in range(len(strip) - W + 1):
        px = blank()
        for x in range(W):
            col = strip[offset + x]
            if col:
                colour = hsv(((offset + x) / 40.0) % 1.0)
                for y in range(H):
                    if col >> y & 1:
                        px[y * W + x] = colour
        yield px, step_ms


def frames():
    """One full cycle of the sign."""
    yield from wipe()
    yield from logo()
    yield from scroll()
    yield from logo(hold_ms=1000)


def main():
    import time
    from matrix import Matrix

    m = Matrix()
    print("Paradox Transistor Lab sign running. Ctrl-C to stop.")
    try:
        while True:
            for px, ms in frames():
                m.frame(px)
                m.show()
                time.sleep_ms(ms)
    except KeyboardInterrupt:
        pass
    finally:
        m.clear()
        m.show()
        print("stopped, panel cleared")


if __name__ == "__main__":
    main()
