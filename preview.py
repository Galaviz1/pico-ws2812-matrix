"""Render the sign to docs/sign.gif on your computer (no Pico needed).

    python3 preview.py

Uses the same frames() as the panel, so the GIF is exactly what the LEDs show,
one cycle. Needs Pillow:  python3 -m pip install --user pillow
"""

import os

from PIL import Image, ImageDraw, ImageFilter

import sign

PITCH = 22           # pixels between LED centres
LED = 14             # LED dot diameter
PAD = 10


def render(px):
    size = PAD * 2 + PITCH * sign.W
    glow = Image.new("RGB", (size, size), (10, 10, 12))
    d = ImageDraw.Draw(glow)
    for y in range(sign.H):
        for x in range(sign.W):
            r, g, b = px[y * sign.W + x]
            cx, cy = PAD + x * PITCH + PITCH // 2, PAD + y * PITCH + PITCH // 2
            if r or g or b:
                d.ellipse([cx - LED, cy - LED, cx + LED, cy + LED], fill=(r // 3, g // 3, b // 3))
    img = glow.filter(ImageFilter.GaussianBlur(7))
    d = ImageDraw.Draw(img)
    for y in range(sign.H):
        for x in range(sign.W):
            r, g, b = px[y * sign.W + x]
            cx, cy = PAD + x * PITCH + PITCH // 2, PAD + y * PITCH + PITCH // 2
            colour = (r, g, b) if (r or g or b) else (32, 32, 36)
            d.ellipse([cx - LED // 2, cy - LED // 2, cx + LED // 2, cy + LED // 2], fill=colour)
    return img


def main():
    images, durations = [], []
    for px, ms in sign.frames():
        images.append(render(px))
        durations.append(ms)
    os.makedirs("docs", exist_ok=True)
    out = os.path.join("docs", "sign.gif")
    # 64 colours per frame keeps the README GIF ~1.4 MB instead of ~3 MB.
    pal = [im.quantize(colors=64, method=Image.MEDIANCUT) for im in images]
    pal[0].save(out, save_all=True, append_images=pal[1:], duration=durations, loop=0, optimize=True)
    print("wrote %s: %d frames, %.1f s per cycle" % (out, len(images), sum(durations) / 1000))


if __name__ == "__main__":
    main()
