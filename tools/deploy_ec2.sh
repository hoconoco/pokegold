#!/usr/bin/env bash
# Put the web player on the ssafy_schedule EC2 (shared with agent_town) at https://gold.3-35-233-70.sslip.io
#   files: web/* + pokegold.gbc -> /srv/pokegold/web, tools/web_server.py -> /srv/pokegold/
#   save + backups stay in /srv/pokegold/data (never touched here)
#   scp to <file>.new -> mv in one go -> restart pokegold-web -> compare sha256 with local
# --setup (first time only): create /srv/pokegold, the pokegold-web systemd unit (127.0.0.1:8789)
#   and append the gold. site to /etc/caddy/Caddyfile with the same basicauth line as agent_town
#   (Caddyfile is backed up, validated, and restored if validation fails)
# Run from anywhere: bash tools/deploy_ec2.sh [--setup]
# Key = env SSAFY_SCHEDULE_KEY, host = POKEGOLD_SSH (default ubuntu@3.35.233.70)
set -euo pipefail
cd "$(dirname "$0")/.."
H="${POKEGOLD_SSH:-ubuntu@3.35.233.70}"
: "${SSAFY_SCHEDULE_KEY:?env SSAFY_SCHEDULE_KEY (EC2 SSH key path) is not set}"
O=(-i "$SSAFY_SCHEDULE_KEY" -o BatchMode=yes)
SITE=gold.3-35-233-70.sslip.io
PORT=8789

WEB=(web/index.html web/simple.js web/simple.css web/reset.css web/binjgb.js web/binjgb.wasm
     web/favicon.svg web/LICENSE.binjgb web/LICENSE.gbstudio)
[ -f pokegold.gbc ] || { echo "pokegold.gbc not built"; exit 1; }
if [ -n "$(git status --porcelain -- web tools/web_server.py)" ]; then
  echo "uncommitted changes, not deploying:"; git status --short -- web tools/web_server.py; exit 1
fi

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

FILES=("${WEB[@]}" pokegold.gbc tools/web_server.py)
for f in "${WEB[@]}"; do scp "${O[@]}" -q "$f" "$H:/srv/pokegold/web/$(basename "$f").new"; done
scp "${O[@]}" -q pokegold.gbc "$H:/srv/pokegold/web/pokegold.gbc.new"
scp "${O[@]}" -q tools/web_server.py "$H:/srv/pokegold/web_server.py.new"
R=$(ssh "${O[@]}" "$H" "cd /srv/pokegold && for f in web/*.new web_server.py.new; do mv \"\$f\" \"\${f%.new}\"; done \
  && sudo systemctl restart pokegold-web && sleep 2 && systemctl is-active pokegold-web \
  && cd web && sha256sum * && cd .. && sha256sum web_server.py")
echo "$R"
ok=1
for f in "${FILES[@]}"; do
  name=$(basename "$f")
  [ "$(sha256sum "$f" | cut -d' ' -f1)" = "$(echo "$R" | grep " $name\$" | cut -d' ' -f1)" ] || { echo "sha256 differs: $f"; ok=0; }
done
[ $ok = 1 ] && echo "deployed: $(git log -1 --format='%h %s') -> https://$SITE" || exit 1
