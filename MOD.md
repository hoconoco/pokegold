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

## 빌드

- Docker 이미지(한 번만): `docker build -t pokegold-build .build` — `.build/Dockerfile`은 git 밖(`.git/info/exclude`)
- 빌드: `MSYS_NO_PATHCONV=1 docker run --rm -v "C:/Users/nojin_ijryw4c/repos/pokegold:/src" pokegold-build make gold`
- 웹에 반영: `cp pokegold.gbc web/`

## 웹에서 실행

- `python -m http.server 8000 --directory C:/Users/nojin_ijryw4c/repos/pokegold/web` 후 http://localhost:8000
- 키: 방향키, X=A, Z=B, Enter=Start, Tab=Select, Backspace=되감기
- 빨리감기(3배)는 켜고 끄는 스위치 — 오른쪽 위 `▶▶` 버튼 또는 왼쪽 Shift
- 화면은 창 크기에 맞춰 10:9 비율로 맞춰진다. 터치 기기는 화면 패드가 나오고, 세로 모드에서는 게임 화면이 패드 위에 놓인다
- 세이브는 브라우저 localStorage(`extram`)에 저장된다
- 에뮬레이터: binjgb 웹 빌드(MIT, `web/LICENSE.binjgb`·`web/LICENSE.gbstudio`)
