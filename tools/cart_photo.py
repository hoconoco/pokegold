"""Fit a cartridge front photo for the web shelf: web/carts/<gold|silver>_<kr|en>.png.

The photo is the owner's own file (kept out of git, see .gitignore). This trims the background
around the cartridge and resizes it to 764x870 (the shelf's cartridge outline); the page cuts it to
the outline (stepped top-right corner), so a little leftover background at the edges is fine.

Background trim: pixels that differ from the photo's corner color by more than --tol count as
cartridge; the bounding box of those (ignoring thin specks) is the crop. Use --box L,T,R,B to crop by
hand when the background is busy.

Usage: python -X utf8 tools/cart_photo.py PHOTO --out web/carts/gold_kr.png [--tol 60] [--box L,T,R,B]
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


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--out", required=True)
    ap.add_argument("--tol", type=int, default=60)
    ap.add_argument("--box")
    a = ap.parse_args()
    im = Image.open(a.photo)
    im.load()
    box = tuple(int(v) for v in a.box.split(",")) if a.box else find_box(im, a.tol)
    if not box:
        sys.exit("cartridge not found — pass --box L,T,R,B")
    out = im.convert("RGB").crop(box).resize((W, H), Image.LANCZOS)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    out.save(a.out)
    print(f"{a.photo} box={box} -> {a.out} {W}x{H}")


if __name__ == "__main__":
    main()
