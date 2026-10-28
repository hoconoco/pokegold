"""Serve the web player and keep the game save on the server.

- GET  /            files from --web-dir (index.html, emulator, ROM)
- GET  /api/save?slot=kr|en    current save of that ROM (404 if none yet)
- PUT  /api/save?slot=kr|en    replace it; the previous one is kept in backups/
                               (newest BACKUP_KEEP files per slot)
  The English save keeps its first name save.sav; the Korean one is save-kr.sav.

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

MAX_SAVE_BYTES = 64 * 1024  # Gold uses 32 KiB of cartridge RAM
BACKUP_KEEP = 30


class Handler(SimpleHTTPRequestHandler):
    data_dir: Path

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def _slot(self):
        """(save file, backup name prefix) for ?slot=, or None for an unknown slot."""
        query = parse_qs(urlsplit(self.path).query)
        slot = query.get("slot", ["en"])[0]
        if slot == "en":
            return self.data_dir / "save.sav", "save-2"
        if slot == "kr":
            return self.data_dir / "save-kr.sav", "save-kr-"
        return None

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
