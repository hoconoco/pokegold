# 골드 개조판 (mod/rea-gold)

## 바뀐 것

- 파티 전원 경험치 — 전투 참가 포켓몬은 100%, 기절하지 않은 나머지 파티(알 제외)는 50% (`engine/battle/core.asm` `GetExpAllMons`)
- 야생 전부 이로치 — 배회 3마리·고정 심볼 포함. 공격 개체값은 이로치 허용값 중 무작위라 성별이 섞인다
  - 안농은 이로치 모양이 I·V뿐이라, 그 글자가 안 풀렸으면 일반 색으로 나온다
- 출현 — 각 맵의 드문 칸에 반대 지역 포켓몬(관동 맵 ← 성도 152~251번, 성도 맵 ← 관동 1~151번)
  - 풀숲 10%·5%·4% 칸, 물 10% 칸. 생성: `python -X utf8 tools/mix_wild.py`
- 전설·환상 고정 심볼 — 도망치면 남고, 잡거나 쓰러뜨리면 사라진다(전투 전 저장 권장)
  - 프리져 Lv50 쌍둥이섬 체육관 (3,4)
  - 썬더 Lv50 무인발전소 (18,2)
  - 파이어 Lv50 챔피언로드 (10,54)
  - 뮤츠 Lv70 블루시티 서쪽 옛 동굴 자리 (2,10)
  - 뮤 Lv30 갈색시티 부두 (29,24)
  - 세레비 Lv30 너도밤나무숲 사당 옆 (9,22)

## 한국어판

- 정식 한국어판 ROM(`POKEMON_GLD` `AAUK`, sha1 `c0ff3999…`)에 같은 개조를 바이너리 패치로 옮긴다 — `tools/kr_patch.py`
  - 원본 ROM은 `.build/kr/baserom_kr.gbc`(git 밖). 패치 위치는 바이트 패턴(주소 부분 제외)이 한 곳에만 맞아야 하고, 원래 바이트를 확인한 뒤 쓴다
  - 옮긴 것: 이로치(야생·배회·선물·박스 선물·알), 파티 전원 경험치, 반대 지역 출현(영어판에서 섞은 칸의 포켓몬만 복사 — 한국어판 출현 데이터는 레벨 등 33바이트가 원래 달라 나머지는 한국어판 것을 유지)
  - 전설 6마리: 영어판과 같은 자리·레벨. 한국어판은 글자 인코딩이 달라 말 걸 때 대사 없이 울음소리 후 바로 전투. 한국어판 스크립트 명령은 opentext 이후 번호가 1씩 크다(루기아 스크립트로 확인)
- 웹은 개조판 여덟 판(옐로·골드·실버·루비·사파이어·파이어레드·리프그린·에메랄드, 한국어)을 mGBA 웹판으로 돌린다 — 아래 '웹에서 실행'

## 빌드

- Docker 이미지(한 번만): `docker build -t pokegold-build .build` — `.build/Dockerfile`은 git 밖(`.git/info/exclude`)
- 빌드: `MSYS_NO_PATHCONV=1 docker run --rm -v "C:/Users/nojin_ijryw4c/repos/pokegold:/src" pokegold-build make gold`

## 웹에서 실행

- 접속: https://pokemon.3-35-233-70.sslip.io — 에이전트 타운과 같은 아이디·비밀번호, 스마트폰 세로 화면 기준
  - ssafy_schedule EC2(에이전트 타운과 공용)의 Caddy `pokemon.` 블록(예전 `gold.` 주소는 새 주소로 넘김) → 서비스 `pokegold-web`(127.0.0.1:8789, `tools/web_server.py`)
- 첫 화면(`web/index.html`): 여덟 판 발매순 슬라이드
  - 가운데 판은 그 ROM을 실제로 돌린다(`play.html?game=<판>&preview=1` — 세이브 없음, 인트로는 빨리감기 뒤 판별 프레임 수에 START로 건너뜀 `PREVIEW_SKIP`) — 시작 화면과 BGM, 소리는 첫 터치 뒤부터
  - 양옆은 그 판 시작 화면의 정지 화면(가운데 왔을 때 떠서 그 브라우저 localStorage에), 아직 없으면 판 이름
  - 밀기·방향키·옆 판 누르기로 넘기고, 가운데를 누르면 'OO 버전을 시작하시겠습니까?' → 예면 `play.html?game=<판>`
- 플레이 화면(`web/play.html`)
  - 틀 사진(`web/frames/<gbc|gba>.webp`, 사용자 사진, git 밖)이 있는 판은 사진 위에 게임 화면·누르는 자리·전원 등(세이브 상태)을 겹친다 — 지금 골드·실버는 틀 없이(사용자 결정), GBA 판은 사진 대기
  - 틀이 없으면 게임 화면 아래 예전 웹 플레이어 모양 버튼(회색 십자키, 자주색 A·B, 회색 SELECT·START, GBA는 L·R)
  - 오른쪽 위: `판 선택`(세이브 올리고 첫 화면으로), 속도 `×1 → ×2 → ×3`(왼쪽 Shift도) — 빨라져도 소리는 그대로 나온다(mGBA)
  - 키: 방향키, X=A, Z=B, Enter=Start, Tab=Select, A=L, S=R
- 세이브: 판마다 서버 칸 하나(`api/save?slot=` — 골드 `kr`, 실버 `kr_silver`, 나머지는 판 이름), 게임이 저장하면 1초 뒤 올린다, 덮어쓸 때마다 이전 것을 `backups/`에 30개까지
  - 서버에 닿지 않으면 그 브라우저(IndexedDB)에만 남고 전원 등이 빨강
- 배포: `bash C:/Users/nojin_ijryw4c/repos/pokegold/tools/deploy_ec2.sh` — 페이지·mGBA·여덟 ROM(골드·실버는 여기서 `kr_patch.py`로 다시 만들고, GBA 판은 `../pokefirered/.build/common15`의 보낸 빌드)·틀 사진을 올리고 sha256을 맞춘다(세이브는 건드리지 않음). `--setup`은 처음 한 번(폴더·서비스·Caddy 블록)
- 로컬 시험: ROM을 `web/roms/<판>.gba|gbc`에 두고 `python -X utf8 tools/web_server.py --web-dir web --data-dir <임시폴더> --port 8790`
- 에뮬레이터: mGBA 2.6.0 웹판(`@thenick775/mgba-wasm`, MPL-2.0, `web/mgba/LICENSE.txt`) — 스레드를 써서 서버가 COOP·COEP 헤더를 붙인다(`web_server.py`)
