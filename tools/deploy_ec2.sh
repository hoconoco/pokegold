#!/usr/bin/env bash
# Put the web player on the ssafy_schedule EC2 (shared with agent_town) at https://pokemon.3-35-233-70.sslip.io
#   files: web pages + mGBA web core (web/mgba/) + the eight Korean mod ROMs (roms/<game>.gba|gbc:
#   Gold/Silver rebuilt here with tools/kr_patch.py, the GBA ones copied from the REA_repo builds in
#   ../pokefirered/.build/common15) + the first screen's title stills and title music (web/title/, cut from
#   the ROMs by tools/make_titles.py, not in git) + device frame photos if present (web/frames/*.webp,
#   owner's photos, not in git) -> /srv/pokegold/web, tools/web_server.py -> /srv/pokegold/
#   save + backups stay in /srv/pokegold/data (never touched here); files no longer used stay on the server
#   scp to <file>.new -> mv in one go -> restart pokegold-web -> compare sha256 with local
# --setup (first time only): create /srv/pokegold, the pokegold-web systemd unit (127.0.0.1:8789)
#   and append the pokemon. site to /etc/caddy/Caddyfile with the same basicauth line as agent_town
#   (Caddyfile is backed up, validated, and restored if validation fails)
# Run from anywhere: bash tools/deploy_ec2.sh [--setup]
# Key = env SSAFY_SCHEDULE_KEY, host = POKEGOLD_SSH (default ubuntu@3.35.233.70)
set -euo pipefail
cd "$(dirname "$0")/.."
H="${POKEGOLD_SSH:-ubuntu@3.35.233.70}"
: "${SSAFY_SCHEDULE_KEY:?env SSAFY_SCHEDULE_KEY (EC2 SSH key path) is not set}"
O=(-i "$SSAFY_SCHEDULE_KEY" -o BatchMode=yes)
SITE=pokemon.3-35-233-70.sslip.io
PORT=8789

B=../pokefirered/.build/common15
# "local file|path under /srv/pokegold/web"
PAIRS=("web/index.html|index.html" "web/play.html|play.html" "web/favicon.svg|favicon.svg"
       "web/mgba/mgba.js|mgba/mgba.js" "web/mgba/mgba.wasm|mgba/mgba.wasm" "web/mgba/LICENSE.txt|mgba/LICENSE.txt"
       "$B/yellow/pokemon_yellow_kr_0.8.1.gba|roms/yellow.gba"
       ".build/kr/pokegold_kr.gbc|roms/gold.gbc" ".build/kr/pokesilver_kr.gbc|roms/silver.gbc"
       "$B/ruby/ruby_kr_mod_2.1.0.gba|roms/ruby.gba" "$B/sapphire/sapphire_kr_mod_2.1.0.gba|roms/sapphire.gba"
       "$B/fr/firered_kr_mod_2.1.0.gba|roms/firered.gba" "$B/lg/leafgreen_kr_mod_2.1.0.gba|roms/leafgreen.gba"
       "$B/em/emerald_kr_mod_2.2.0.gba|roms/emerald.gba")
for g in yellow gold silver ruby sapphire firered leafgreen emerald; do
  PAIRS+=("web/title/$g.png|title/$g.png" "web/title/$g.m4a|title/$g.m4a")
done
for f in web/frames/*.webp; do [ -f "$f" ] && PAIRS+=("$f|frames/$(basename "$f")"); done
if [ -n "$(git status --porcelain -- web tools/web_server.py tools/kr_patch.py)" ]; then
  echo "uncommitted changes, not deploying:"; git status --short -- web tools/web_server.py tools/kr_patch.py; exit 1
fi
python -X utf8 tools/kr_patch.py --base .build/kr/baserom_kr.gbc --out .build/kr/pokegold_kr.gbc
python -X utf8 tools/kr_patch.py --base .build/kr/baserom_kr_silver.gbc --out .build/kr/pokesilver_kr.gbc

if [ "${1:-}" = "--setup" ]; then
  ssh "${O[@]}" "$H" bash -s -- "$SITE" "$PORT" <<'REMOTE'
set -euo pipefail
SITE=$1; PORT=$2
if ss -ltn | grep -q ":$PORT "; then
  systemctl is-active --quiet pokegold-web || { echo "port $PORT already in use"; exit 1; }
fi
sudo mkdir -p /srv/pokegold/web /srv/pokegold/data
sudo chown -R ubuntu:ubuntu /srv/pokegold
sudo tee /etc/systemd/system/pokegold-web.service >/dev/null <<UNIT
[Unit]
Description=Pokemon Gold mod web player and save store
After=network.target

[Service]
User=ubuntu
ExecStart=/usr/bin/python3 /srv/pokegold/web_server.py --web-dir /srv/pokegold/web --data-dir /srv/pokegold/data --port $PORT
Restart=on-failure

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable pokegold-web
if ! grep -q "^$SITE " /etc/caddy/Caddyfile; then
  BAK=/etc/caddy/Caddyfile.bak-$(date +%Y%m%d%H%M%S)
  sudo cp /etc/caddy/Caddyfile "$BAK"
  AUTH=$(awk '/^[ \t]*basicauth \{/{f=1;next} f&&NF==2{print $1" "$2;exit}' /etc/caddy/Caddyfile)
  case "$AUTH" in *' $2'*) ;; *) echo "basicauth user/hash line not found"; exit 1;; esac
  printf '\n%s {\n\tbasicauth {\n\t\t%s\n\t}\n\treverse_proxy 127.0.0.1:%s\n}\n' "$SITE" "$AUTH" "$PORT" \
    | sudo tee -a /etc/caddy/Caddyfile >/dev/null
  if sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile >/dev/null 2>&1; then
    sudo systemctl reload caddy
    echo "caddy: added $SITE (backup $BAK)"
  else
    sudo cp "$BAK" /etc/caddy/Caddyfile
    echo "caddy validate failed, restored $BAK"; exit 1
  fi
fi
REMOTE
fi

for pr in "${PAIRS[@]}"; do [ -f "${pr%%|*}" ] || { echo "missing: ${pr%%|*} (title files: python -X utf8 tools/make_titles.py)"; exit 1; }; done
ssh "${O[@]}" "$H" "mkdir -p /srv/pokegold/web/mgba /srv/pokegold/web/roms /srv/pokegold/web/frames /srv/pokegold/web/title"
for pr in "${PAIRS[@]}"; do scp "${O[@]}" -q "${pr%%|*}" "$H:/srv/pokegold/web/${pr#*|}.new"; done
scp "${O[@]}" -q tools/web_server.py "$H:/srv/pokegold/web_server.py.new"
R=$(ssh "${O[@]}" "$H" "cd /srv/pokegold && shopt -s nullglob && for f in web/*.new web/*/*.new web_server.py.new; do mv \"\$f\" \"\${f%.new}\"; done \
  && sudo systemctl restart pokegold-web && sleep 2 && systemctl is-active pokegold-web \
  && cd web && sha256sum *.* mgba/* roms/* title/* && { ls frames/* >/dev/null 2>&1 && sha256sum frames/* || true; } && cd .. && sha256sum web_server.py")
echo "$R"
ok=1
for pr in "${PAIRS[@]}" "tools/web_server.py|web_server.py"; do
  f=${pr%%|*}; name=${pr#*|}
  [ "$(sha256sum "$f" | cut -d' ' -f1)" = "$(echo "$R" | grep " $name\$" | cut -d' ' -f1)" ] || { echo "sha256 differs: $f"; ok=0; }
done
[ $ok = 1 ] && echo "deployed: $(git log -1 --format='%h %s') -> https://$SITE" || exit 1
