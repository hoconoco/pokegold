"""ui_check.py --out <folder>: the web player's screen layout check before a deploy (user request 2026-11-17: UI overlaps).

Serves web/ locally (tools/web_server.py) and opens play.html for one game of each kind (GB gold, GBA firered,
DS diamond) as a phone browser and as the Android app would (window.PokeApp stub; the app's GB/GBA WebView has no
cross-origin isolation, so those run on EmulatorJS), upright and sideways, on two phone sizes. For each it checks:
- the bug key, the note line (filled with a sample text), every button, the screen box: inside the viewport
- the bug key and the note line do not overlap each other or any button
- the bug report dialog (with a tall full-screen capture in the app) fits the viewport and its send key is visible,
  also with the keyboard up (viewport height cut to 520)
- app0: the app's WebView can still be 0×0 when the page first lays out (HeartGold report 2026-11-18: white screen,
  screen box 0×0) — the page starts with innerWidth/innerHeight 0, then gets its real size and a resize
Writes <out>/ui_check.txt (FAIL lines first) and <out>/ui_check.png (all screens). Exit code 1 if anything failed.

python -X utf8 tools/ui_check.py --out .build/ui_check
"""
import argparse
import base64
import io
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

GAMES = ["gold", "firered", "diamond"]
SIZES = {"s23": (412, 915), "small": (360, 740)}
TALL_PNG = None


def tall_png():
    buf = io.BytesIO()
    Image.new("RGB", (540, 1158), (200, 160, 40)).save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


APP_STUB = """window.PokeApp = { appVersion(){return 99}, captureScreen(){ return '%s'; }, romOk(){}, update(){},
  screens(){}, key(){}, touch(){}, release(){}, speed(){}, home(){}, capture(){return ''}, save(){return ''}, log(){}, diag(){return ''} };"""

BLIND = """(() => { window.__blind = true;
  for (const k of ['innerWidth', 'innerHeight']) {
    const d = Object.getOwnPropertyDescriptor(window, k) || Object.getOwnPropertyDescriptor(Window.prototype, k);
    Object.defineProperty(window, k, { configurable: true, get() { return window.__blind ? 0 : d.get.call(window); } });
  } })();"""

RECT = "e => { const r = e.getBoundingClientRect(); return r.width && r.height ? [r.left, r.top, r.right, r.bottom] : null; }"


def inside(r, w, h):
    return r[0] >= -1 and r[1] >= -1 and r[2] <= w + 1 and r[3] <= h + 1


def overlap(a, b):
    return a[0] < b[2] - 1 and b[0] < a[2] - 1 and a[1] < b[3] - 1 and b[1] < a[3] - 1


def check(pg, w, h, name, out):
    fails = []
    bug = pg.eval_on_selector("#bugBtn", RECT)
    pg.evaluate("document.querySelector('#msg').textContent = '서버에 연결되지 않아 이 기기에만 저장했어요'")
    msg = pg.eval_on_selector("#msg", RECT)
    keys = pg.eval_on_selector_all("#dev [data-k], #homeKey, #speedKey", f"es => es.map({RECT})")
    screen = pg.eval_on_selector("#screenbox", RECT) if pg.query_selector("#screenbox") else None
    for label, r in [("bug key", bug), ("note", msg), ("screen", screen)] + [(f"button {i}", k) for i, k in enumerate(keys)]:
        if r and not inside(r, w, h):
            fails.append(f"{label} outside the screen {[round(x) for x in r]}")
    if bug and msg and overlap(bug, msg):
        fails.append("bug key and note overlap")
    for i, k in enumerate(keys):
        if k and bug and overlap(bug, k):
            fails.append(f"bug key on button {i}")
        if k and msg and overlap(msg, k):
            fails.append(f"note on button {i}")
    pg.evaluate("document.querySelector('#msg').textContent = ''")
    pg.screenshot(path=str(out / f"{name}.png"))
    return fails


def check_dialog(pg, w, h):
    fails = []
    pg.click("#bugBtn")
    pg.wait_for_timeout(500)
    box = pg.eval_on_selector("#bugDlg .box", RECT)
    send = pg.eval_on_selector("#bugSend", RECT)
    if not box or not inside(box, w, h):
        fails.append(f"bug dialog outside the screen {box}")
    if not send or not inside(send, w, h):
        fails.append(f"bug dialog send key not visible {send}")
    pg.click("#bugCancel")
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--port", type=int, default=8798)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[1]
    srv = subprocess.Popen([sys.executable, str(root / "tools/web_server.py"), "--web-dir", str(root / "web"),
                            "--data-dir", str(out / "data"), "--port", str(a.port)], stderr=subprocess.DEVNULL)
    time.sleep(4)
    stub = APP_STUB % tall_png()
    lines, shots = [], []
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            for game in GAMES:
                for mode in ("web", "app", "app0"):
                    for size, (w0, h0) in SIZES.items():
                        for orient in ("port", "land"):
                            if mode == "app0" and (size, orient) != ("s23", "port"):
                                continue
                            w, h = (w0, h0) if orient == "port" else (h0, w0)
                            name = f"{game}_{mode}_{size}_{orient}"
                            pg = b.new_page(viewport={"width": w, "height": h})
                            if mode in ("app", "app0"):
                                pg.add_init_script(stub)
                                if game != "diamond":
                                    pg.add_init_script("Object.defineProperty(self, 'crossOriginIsolated', {get: () => false});")
                            if mode == "app0":
                                pg.add_init_script(BLIND)
                            pg.goto(f"http://127.0.0.1:{a.port}/play.html?game={game}")
                            pg.wait_for_timeout(2500)
                            if mode == "app0":
                                pg.evaluate("() => { window.__blind = false; dispatchEvent(new Event('resize')); }")
                                pg.wait_for_timeout(800)
                            fails = check(pg, w, h, name, out)
                            fails += check_dialog(pg, w, h)
                            pg.set_viewport_size({"width": w, "height": min(h, 520)})
                            pg.wait_for_timeout(400)
                            fails += [f + " (keyboard up)" for f in check_dialog(pg, w, min(h, 520))]
                            shots.append(out / f"{name}.png")
                            lines.append(("FAIL " if fails else "ok   ") + name + (": " + "; ".join(fails) if fails else ""))
                            pg.close()
            b.close()
    finally:
        srv.terminate()
    lines.sort(key=lambda l: not l.startswith("FAIL"))
    (out / "ui_check.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    ims = [Image.open(s) for s in shots]
    cell = 200
    sheet = Image.new("RGB", (cell * 8, cell * ((len(ims) + 7) // 8)), "white")
    for i, im in enumerate(ims):
        im.thumbnail((cell, cell))
        sheet.paste(im, ((i % 8) * cell, (i // 8) * cell))
    sheet.save(out / "ui_check.png")
    print("\n".join(lines))
    sys.exit(1 if any(l.startswith("FAIL") for l in lines) else 0)


if __name__ == "__main__":
    main()
