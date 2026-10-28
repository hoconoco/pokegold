"""Print a map's collision as text, one character per step tile.

Used to pick walkable spots for new object_events. Read-only.

  .  floor        #  wall/other blocked     ~  water
  "  grass        D  door/warp tile         ?  other collision
  O  object_event W  warp_event             S  bg_event

Usage: python -X utf8 tools/map_ascii.py MapName [MapName ...] --out FILE
"""

import argparse
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CHARS = {
    "FLOOR": ".", "WALL": "#", "WATER": "~", "TALL_GRASS": '"', "LONG_GRASS": '"',
    "CUT_TREE": "#", "HEADBUTT_TREE": "#", "COUNTER": "#",
}


def snake(name):
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z0-9])", "_", name).upper()


def render(mapname):
    maps = (REPO / "data/maps/maps.asm").read_text(encoding="utf-8")
    tileset = re.search(rf"^\tmap {mapname}, TILESET_(\w+),", maps, re.M).group(1).lower()
    consts = (REPO / "constants/map_constants.asm").read_text(encoding="utf-8")
    w, h = map(int, re.search(rf"map_const {snake(mapname)},\s+(\d+),\s+(\d+)", consts).groups())
    blk = (REPO / f"maps/{mapname}.blk").read_bytes()
    coll = re.findall(r"tilecoll (\w+), (\w+), (\w+), (\w+)",
                      (REPO / f"data/tilesets/{tileset}_collision.asm").read_text(encoding="utf-8"))
    grid = [["?"] * (w * 2) for _ in range(h * 2)]
    for by in range(h):
        for bx in range(w):
            quads = coll[blk[by * w + bx]]
            for i, c in enumerate(quads):
                ch = CHARS.get(c, "D" if "DOOR" in c or "WARP" in c or "CAVE" in c or "LADDER" in c else "?")
                grid[by * 2 + i // 2][bx * 2 + i % 2] = ch
    src = (REPO / f"maps/{mapname}.asm").read_text(encoding="utf-8")
    for mark, kind in (("W", "warp_event"), ("S", "bg_event"), ("O", "object_event")):
        for x, y in re.findall(rf"\t{kind}\s+(\d+),\s*(\d+)", src):
            x, y = int(x), int(y)
            if 0 <= y < h * 2 and 0 <= x < w * 2:
                grid[y][x] = mark
    head = "    " + "".join(str(x // 10) for x in range(w * 2)) + "\n    " + "".join(str(x % 10) for x in range(w * 2))
    rows = [f"{y:3d} " + "".join(r) for y, r in enumerate(grid)]
    return f"== {mapname} ({tileset}, {w*2}x{h*2})\n{head}\n" + "\n".join(rows) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("maps", nargs="+")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    Path(args.out).write_text("\n".join(render(m) for m in args.maps), encoding="utf-8")


if __name__ == "__main__":
    main()
