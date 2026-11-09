"""Fit a cartridge or box photo for the web shelf: web/carts/ or web/boxes/<gold|silver>_<kr|en>.png.

The photo is the owner's own file (kept out of git, see .gitignore). This trims the background
around the cartridge and resizes it to 764x870 (the shelf's cartridge outline); the page cuts it to
the outline (stepped top-right corner), so a little leftover background at the edges is fine.

Background trim: pixels that differ from the photo's corner color by more than --tol count as
cartridge; the bounding box of those (ignoring thin specks) is the crop. Use --box L,T,R,B to crop by
hand when the background is busy.

Box photos: --size WxH with the crop's aspect (e.g. 440x440 for a square crop), --clear-bg makes the near-white
background connected to the edges transparent (flood fill), so a box photographed at an angle sits on
the dark page.

Usage: python -X utf8 tools/cart_photo.py PHOTO --out web/carts/gold_kr.png [--tol 60] [--box L,T,R,B]
       python -X utf8 tools/cart_photo.py PHOTO --out web/boxes/gold_kr.png --box L,T,R,B --size 440x440 --clear-bg
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

W, H = 764, 870


def find_box(im: Image.Image, tol: int):
    rgb = im.convert("RGB")
    w, h = rgb.size
    corners = [rgb.getpixel(p) for p in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]]
    bg = tuple(sorted(c[i] for c in corners)[1] for i in range(3))  # robust-ish corner color
    diff = ImageChops.difference(rgb, Image.new("RGB", rgb.size, bg)).convert("L")
    mask = diff.point(lambda v: 255 if v > tol else 0).filter(ImageFilter.MedianFilter(9))
    return mask.getbbox()


def clear_background(im: Image.Image, white: int = 232) -> Image.Image:
    """Near-white pixels reachable from the image edge become transparent."""
    rgba = im.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()
    seen = bytearray(w * h)
    stack = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while stack:
        x, y = stack.pop()
        i = y * w + x
        if seen[i]:
            continue
        seen[i] = 1
        r, g, b, _ = px[x, y]
        if min(r, g, b) < white:
            continue
        px[x, y] = (r, g, b, 0)
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx]:
                stack.append((nx, ny))
    return rgba


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--out", required=True)
    ap.add_argument("--tol", type=int, default=60)
    ap.add_argument("--box")
    ap.add_argument("--size", default=f"{W}x{H}")
    ap.add_argument("--clear-bg", action="store_true")
    a = ap.parse_args()
    im = Image.open(a.photo)
    im.load()
    box = tuple(int(v) for v in a.box.split(",")) if a.box else find_box(im, a.tol)
    if not box:
        sys.exit("cartridge not found — pass --box L,T,R,B")
    w, h = (int(v) for v in a.size.lower().split("x"))
    out = im.convert("RGB").crop(box).resize((w, h), Image.LANCZOS)
    if a.clear_bg:
        out = clear_background(out)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    out.save(a.out)
    print(f"{a.photo} box={box} -> {a.out} {w}x{h}")


if __name__ == "__main__":
    main()
