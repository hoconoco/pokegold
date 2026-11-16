#!/bin/bash
# ro_reports.sh --out <폴더>: 웹 게임기 '버그 신고'(서버 /srv/pokegold/data/reports/<시각>_<판>/ report.json·screen.png·save.sav)를 받아 온다 — 읽기만
#   bash C:/Users/nojin_ijryw4c/repos/pokegold/tools/ro_reports.sh --out C:/Users/nojin_ijryw4c/repos/pokegold/.build/reports
# 키 = env SSAFY_SCHEDULE_KEY, 호스트 = POKEGOLD_SSH(기본 ubuntu@3.35.233.70). 이미 받은 신고 폴더는 다시 받지 않는다
set -e
[ "$1" = "--out" ] && OUT="$2" || { echo "usage: ro_reports.sh --out <folder>"; exit 2; }
H="${POKEGOLD_SSH:-ubuntu@3.35.233.70}"
: "${SSAFY_SCHEDULE_KEY:?env SSAFY_SCHEDULE_KEY (EC2 SSH key path) is not set}"
O=(-i "$SSAFY_SCHEDULE_KEY" -o BatchMode=yes)
mkdir -p "$OUT"
for d in $(ssh "${O[@]}" "$H" "ls /srv/pokegold/data/reports 2>/dev/null"); do
  [ -d "$OUT/$d" ] && continue
  scp -q -r "${O[@]}" "$H:/srv/pokegold/data/reports/$d" "$OUT/"
  echo "new: $d"
done
ls "$OUT" | tail -20
