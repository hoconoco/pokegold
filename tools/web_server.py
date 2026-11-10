"""Serve the web player and keep the game save on the server.

- GET  /            files from --web-dir (index.html, emulator, ROMs), with the cross-origin isolation
                     headers the threaded mGBA web core needs (COOP same-origin, COEP require-corp)
- GET  /api/save?slot=<slot>    current save of that game (404 if none yet)
- PUT  /api/save?slot=<slot>    replace it; the previous one is kept in backups/
                               (newest BACKUP_KEEP files per slot)
  Slots and files: SLOTS below. Gold/Silver Korean keep their first names (kr, kr_silver), the
  English ones stay readable but the site no longer offers them.

No login here: it listens on 127.0.0.1 only and Caddy puts basicauth in front.

Usage: python3 tools/web_server.py --web-dir DIR --data-dir DIR [--port 8789]
"""

import argparse
import shutil
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

MAX_SAVE_BYTES = 256 * 1024  # GBA flash saves are 128 KiB (+ mGBA footer); Gold uses 32 KiB
BACKUP_KEEP = 30
# slot -> (save file, backup name prefix)
SLOTS = {
    "en": ("save.sav", "save-2"),
    "kr": ("save-kr.sav", "save-kr-"),
    "en_silver": ("save-silver.sav", "save-silver-"),
    "kr_silver": ("save-kr-silver.sav", "save-kr-silver-"),
    "yellow": ("save-yellow.sav", "save-yellow-"),
    "ruby": ("save-ruby.sav", "save-ruby-"),
    "sapphire": ("save-sapphire.sav", "save-sapphire-"),
    "firered": ("save-firered.sav", "save-firered-"),
    "leafgreen": ("save-leafgreen.sav", "save-leafgreen-"),
    "emerald": ("save-emerald.sav", "save-emerald-"),
}


class Handler(SimpleHTTPRequestHandler):
    data_dir: Path

    extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
                      ".wasm": "application/wasm", ".js": "text/javascript", ".webp": "image/webp"}

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        super().end_headers()

    def _slot(self):
        """(save file, backup name prefix) for ?slot=, or None for an unknown slot."""
        query = parse_qs(urlsplit(self.path).query)
        slot = query.get("slot", ["en"])[0]
        if slot not in SLOTS:
            return None
        name, prefix = SLOTS[slot]
        return self.data_dir / name, prefix

    def do_GET(self):
        if self.path.split("?")[0] != "/api/save":
            return super().do_GET()
        if not self._slot():
            return self.send_error(400, "unknown slot")
        save = self._slot()[0]
        if not save.exists():
            return self.send_error(404, "no save yet")
        body = save.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_PUT(self):
        if self.path.split("?")[0] != "/api/save":
            return self.send_error(405)
        length = int(self.headers.get("Content-Length", 0))
        if not 0 < length <= MAX_SAVE_BYTES:
            return self.send_error(400, "bad save size")
        body = self.rfile.read(length)
        if not self._slot():
            return self.send_error(400, "unknown slot")
        save, prefix = self._slot()
        backups = self.data_dir / "backups"
        backups.mkdir(exist_ok=True)
        if save.exists():
            if save.read_bytes() == body:
                return self._ok()
            stamp = time.strftime("%Y%m%d-%H%M%S")
            shutil.copy2(save, backups / f"{prefix}{stamp[1:] if prefix == 'save-2' else stamp}.sav")
            for old in sorted(backups.glob(f"{prefix}*.sav"))[:-BACKUP_KEEP]:
                old.unlink()
        tmp = save.with_suffix(".tmp")
        tmp.write_bytes(body)
        tmp.replace(save)
        self._ok()

    def _ok(self):
        self.send_response(204)
        self.end_headers()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--web-dir", required=True)
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--port", type=int, default=8789)
    args = ap.parse_args()
    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    Handler.data_dir = data_dir
    handler = partial(Handler, directory=args.web_dir)
    ThreadingHTTPServer(("127.0.0.1", args.port), handler).serve_forever()


if __name__ == "__main__":
    main()
