"""Channel sign for a WS2812B display: Paradox Transistor Lab.

Sized from config (one 8x8 panel, or two chained side by side as 16x8). The
8x8 logo and tree are drawn centred on whatever width the display is.

Loop: a rainbow wipe, the play-button logo fading in, then the logo sliding
out to the left with the channel name right behind it, in a rainbow, as one
continuous ticker, and finally the channel's tree icon scanning in.

    ./run_on_pico.sh sign.py          run it (Ctrl-C stops and blanks the panel)
    python3 preview.py                render the same frames to docs/sign.gif

frames() only computes colours, with no hardware imports, so preview.py draws
exactly what the panel will show. main() is the part that needs a Pico.
"""

import config
from font import text_columns

TEXT = "Paradox Transistor Lab"
SCROLL_MS = 55            # per 1-column step: ~18 columns per second
LOGO_GAP = 2              # blank columns between the logo and the first letter
LOGO_HOLD_MS = 1500       # how long the logo stays still before sliding out
W = config.WIDTH          # 8 for one panel, 16 for two side by side
H = config.HEIGHT

RED = (255, 0, 0)
WHITE = (255, 255, 255)
OFF = (0, 0, 0)

# YouTube play button: red rounded body, white triangle pointing RIGHT.
# 'R' red, 'W' white. For a left-pointing triangle, move the single 'W' in
# rows 2 and 5 one column right of the 'WW' pair.
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


# Channel icon: a minimalist tree, drawn in mint green with a CRT scan-line
# look (alternate rows brighter and dimmer). '#' lit, '.' off. Original
# artwork for the channel; the style nods to 80s scan-line logos.
TREE = [
    "..####..",
    ".######.",
    "########",
    "########",
    ".######.",
    "...##...",
    "..####..",
    "########",
]
MINT = (40, 230, 140)
TREE_HOLD_STEPS = 24      # x TREE_STEP_MS: how long the tree shimmers (~3 s)
TREE_STEP_MS = 120


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
    px = blank()
    xoff = (W - len(LOGO[0])) // 2        # centre the 8-wide logo on the display
    for yy, row in enumerate(LOGO):
        for xx, ch in enumerate(row):
            if ch == "R":
                c = RED
            elif ch == "W":
                c = WHITE
            else:
                continue
            px[yy * W + xoff + xx] = (int(c[0] * level), int(c[1] * level), int(c[2] * level))
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


def _logo_columns():
    """The logo as columns, each a list of colours top to bottom (its own size)."""
    cols = []
    for x in range(len(LOGO[0])):
        col = []
        for y in range(len(LOGO)):
            ch = LOGO[y][x]
            col.append(RED if ch == "R" else WHITE if ch == "W" else OFF)
        cols.append(col)
    return cols


def _text_columns(text):
    """The text as coloured columns, each column a rainbow step along the text."""
    cols = []
    for i, mask in enumerate(text_columns(text)):
        colour = hsv((i / 40.0) % 1.0)
        cols.append([colour if mask >> y & 1 else OFF for y in range(H)])
    return cols


def scroll(text=TEXT, step_ms=SCROLL_MS):
    """The logo slides out and the text follows right behind it, as one ticker.

    SCROLL_FROM "right": the logo leaves on the left and the first letter (P)
    comes in from the right, so the name reads in order. "left" runs the same
    ticker the other way round. The letters stay upright either way.
    """
    blank_col = [OFF] * H
    logo, words = _logo_columns(), _text_columns(text)
    gap = [blank_col] * LOGO_GAP
    xoff = (W - len(logo)) // 2           # so the ticker starts where the held
    pad = [blank_col] * xoff              # (centred) logo was, with no jump
    if getattr(config, "SCROLL_FROM", "right") == "left":
        # Mirror image of the ticker's motion, not of the letters: the logo
        # sits at the right end and leaves to the right, the text follows.
        strip = [blank_col] * W + words + gap + logo + pad
        offsets = range(len(strip) - W, -1, -1)
    else:
        strip = pad + logo + gap + words + [blank_col] * W
        offsets = range(len(strip) - W + 1)
    for offset in offsets:
        px = blank()
        for x in range(W):
            col = strip[offset + x]
            for y in range(H):
                px[y * W + x] = col[y]
        yield px, step_ms


def tree_frame(rows_shown=8, phase=0, level=1.0):
    """The tree with only its bottom `rows_shown` rows, scan-line shaded.

    Rows alternate full and ~55 % brightness; `phase` swaps which rows are
    bright, so stepping it makes the stripes shimmer.
    """
    px = blank()
    xoff = (W - len(TREE[0])) // 2        # centre the 8-wide tree on the display
    for y in range(H):
        if y < H - rows_shown:
            continue
        shade = level * (1.0 if (y + phase) % 2 == 0 else 0.55)
        colour = (int(MINT[0] * shade), int(MINT[1] * shade), int(MINT[2] * shade))
        for x in range(len(TREE[y])):
            if TREE[y][x] == "#":
                px[y * W + xoff + x] = colour
    return px


def tree():
    """Scan in from the ground up, shimmer, fade out."""
    for rows in range(1, H + 1):
        yield tree_frame(rows), 70
    for step in range(TREE_HOLD_STEPS):
        yield tree_frame(phase=step % 2), TREE_STEP_MS
    for i in range(9, -1, -1):
        yield tree_frame(level=i / 10), 40


def frames():
    """One full cycle: rainbow wipe, logo fades in and holds, then the ticker."""
    yield from wipe()
    for i in range(1, 11):
        yield logo_frame(i / 10), 40
    yield logo_frame(), LOGO_HOLD_MS
    yield from scroll()
    yield from tree()


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
