# Title screen still + title music from the mod ROMs, for the web first screen (tools/make_titles.py)
# libmgba comes from the mgba-headless image (REA_repo tools/mgba-headless — mGBA master, fixed commit)
# build: docker build -t pokegold-title tools/title_capture
FROM mgba-headless AS mgba

FROM debian:trixie-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc libc6-dev liblua5.4-0 zlib1g libpng16-16t64 ffmpeg \
 && rm -rf /var/lib/apt/lists/*
COPY --from=mgba /opt/mgba /opt/mgba
ENV LD_LIBRARY_PATH=/opt/mgba/lib
COPY capture.c /src/capture.c
# libmgba is built with ENABLE_DIRECTORIES but its flags.h leaves it out — without it struct mCore does not match
RUN gcc -O2 -DENABLE_DIRECTORIES -I/opt/mgba/include -o /usr/local/bin/capture /src/capture.c -L/opt/mgba/lib -lmgba
