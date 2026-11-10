"""Guide menu ('공략') for the Korean Gold/Silver mod — called by tools/kr_patch.py after the other patches.

- Korean ROM addresses are found from code patterns (each must match once, or all matches must agree):
  the options screen (Textbox, PlaceString, palettes, joypad), the START menu (item table, list builder,
  FadeToMenu/CloseSubmenu like the trainer card item) and the wild code (wMapGroup/wMapNumber, wTimeOfDay).
- Texts are Korean, encoded with tools/kr_charset.py (the ROM's own text encoding); Pokémon names are
  copied from the ROM's name table, so they are exactly the game's names.
- 이 맵 출현: lists made from the (already patched) wild tables of this ROM — grass per time of day, water.
- tools/kr_guide/guide.asm is assembled with rgbasm/rgblink in the pokegold-build Docker image; its two
  sections are copied into the free tail of bank 4 and into GUIDE_BANK, then three START menu spots are
  patched (item table pointer, the '가방' append, the '닫다' append).
"""
import re
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GUIDE_BANK = 0x7D
SCGB_DIPLOMA = 8
LINE_TILES = 17                     # list column 2 .. 18 inside the frame
NEXT = 0x59                         # line break of the Korean text engine (the START menu descriptions use it; $4E is not one)
MAX_GRASS_LINES, MAX_WATER_LINES = 3, 1


def _ops(d, at, *offs):
    return [d[at + o] | d[at + o + 1] << 8 for o in offs]


def _find_all(d, pattern):
    rx = re.compile(b"".join(b"." if t == "??" else re.escape(bytes([int(t, 16)])) for t in pattern.split()), re.S)
    return [m.start() for m in rx.finditer(bytes(d))]


def _one(d, name, pattern):
    hits = _find_all(d, pattern)
    assert len(hits) == 1, f"{name}: {len(hits)} matches"
    return hits[0]


def find_symbols(d):
    s = {}
    o = _one(d, "options screen", "21 ac ff 7e f5 36 01 cd ?? ?? 21 ?? ?? 06 10 0e 12 cd ?? ?? 21 ?? ?? 11 ?? ?? cd ?? ??")
    s["ClearBGPalettes"], s["wTilemap"], s["Textbox"], s["PlaceString"] = _ops(d, o, 8, 11, 18, 27)
    o2 = _one(d, "options screen end", "3c e0 ?? cd ?? ?? 06 08 cd ?? ?? cd ?? ?? cd ?? ?? f0 ?? e6 0a")
    s["hBGMapMode"] = 0xFF00 | d[o2 + 2]
    s["WaitBGMap"], s["GetSGBLayout"], s["SetDefaultBGPAndOBP"], s["JoyTextDelay"] = _ops(d, o2, 4, 9, 12, 15)
    s["hJoyPressed"] = 0xFF00 | d[o2 + 18]
    s["hInMenu"] = 0xFFAC
    st = _find_all(d[0x10000:0x14000], "cd ?? ?? 3e ?? 21 ?? ?? cf cd ?? ?? 3e 00 c9")
    pairs = {tuple(_ops(d, 0x10000 + k, 1, 10)) for k in st}
    assert len(pairs) == 1, f"FadeToMenu/CloseSubmenu: {pairs}"
    s["FadeToMenu"], s["CloseSubmenu"] = pairs.pop()
    status = 0x4000 + st[0]                                   # first one = StartMenu_Status (item 3)
    tail = 0x10000 + _one(d[0x10000:0x14000], "menu list tail", "3e 05 cd ?? ?? 3e 06 cd ?? ?? 79 ea ?? ?? c9")
    s["AppendMenuList"] = _ops(d, tail, 3)[0]
    pack = 0x10000 + _one(d[0x10000:0x14000], "menu list pack", "20 05 3e 02 cd ?? ?? 21") + 2
    items = next(k for k in range(0x10000, 0x14000 - 54, 1) if _ops(d, k, 18)[0] == status
                 and all(0x4000 <= v < 0x8000 for v in _ops(d, k, *range(0, 54, 2))))
    items_gb = 0x4000 + items - 0x10000
    ref = [k for k in range(0x10000, 0x14000) if _ops(d, k, 0)[0] == items_gb]
    assert len(ref) == 1, f"START menu item table pointer: {len(ref)}"
    from collections import Counter
    mg = Counter()
    for m in re.finditer(rb"\xfa(.)(.)\x47\xfa(.)(.)\x4f", bytes(d), re.S):
        a1, a2 = m.group(1)[0] | m.group(2)[0] << 8, m.group(3)[0] | m.group(4)[0] << 8
        if a2 == a1 + 1 and 0xC000 <= a1 < 0xE000:
            mg[a1] += 1
    (s["wMapGroup"], n1), (_, n2) = mg.most_common(2)
    assert n1 >= 2 * n2, f"wMapGroup not clear: {mg.most_common(3)}"
    s["wMapNumber"] = s["wMapGroup"] + 1
    tods = {_ops(d, k, 1)[0] for k in _find_all(d, "fa ?? ?? 01 0e 00 cd")}
    assert len(tods) == 1, f"wTimeOfDay: {tods}"
    s["wTimeOfDay"] = tods.pop()
    return s, {"items": items, "items_ref": ref[0], "pack_site": pack, "exit_site": tail + 5}


def charmap(rom_bytes):
    import kr_charset
    double = kr_charset.hangul()
    double.update(kr_charset.SYMBOLS)
    single = kr_charset.single_bytes(HERE.parent)

    def enc(text):
        out = bytearray()
        for ch in text:
            if ch == "\n":
                out.append(NEXT)
            elif ch == " ":
                out.append(0x7F)
            elif ch in double and ch not in ("댜", "돐"):
                out += bytes([double[ch] >> 8, double[ch] & 0xFF])
            else:
                out.append(single[ch])
        return bytes(out)
    return enc


def mon_names(d):
    nb, na = d[0x35C3], d[0x35C4] | d[0x35C5] << 8
    o = nb * 0x4000 + na - 0x4000
    names = {}
    for i in range(1, 252):
        raw = bytes(d[o + 10 * (i - 1):o + 10 * i]).split(b"\x50")[0]
        width, k = 0, 0
        while k < len(raw):
            k += 2 if 1 <= raw[k] <= 0x0B else 1
            width += 1
        names[i] = (raw, width)
    return names


def wild_tables(d, start):
    """[(group, num, [morn], [day], [nite]) ...], [(group, num, [water])] — Johto grass, water, Kanto grass, water"""
    grass, water, o = [], [], start
    for kind in ("grass", "water", "grass", "water"):
        while d[o] != 0xFF:
            g, n = d[o], d[o + 1]
            if kind == "grass":
                sl = [d[o + 5 + 2 * k + 1] for k in range(21)]
                grass.append((g, n, sl[0:7], sl[7:14], sl[14:21]))
                o += 47
            else:
                water.append((g, n, [d[o + 3 + 2 * k + 1] for k in range(3)]))
                o += 9
        o += 1
    return grass, water


def name_list(species, names, enc):
    """distinct species in order -> (lines of at most LINE_TILES tiles joined by NEXT, number of lines)"""
    seen, lines, cur, w = [], [], bytearray(), 0
    for sp in species:
        if sp in seen or sp == 0:
            continue
        seen.append(sp)
        raw, width = names[sp]
        need = width + (1 if w else 0)
        if w and w + need > LINE_TILES:
            lines.append(bytes(cur)); cur, w = bytearray(), 0
            need = width
        if w:
            cur.append(0x7F)
        cur += raw
        w += need
    if cur:
        lines.append(bytes(cur))
    return (bytes([NEXT]).join(lines), len(lines)) if lines else (enc("없음"), 1)


def db(b):
    return "\tdb " + ", ".join(f"${x:02X}" for x in b)


def build_data(d, wild_start, enc):
    names = mon_names(d)
    grass, water = wild_tables(d, wild_start)
    water_of = {(g, n): sp for g, n, sp in water}
    maps = [(g, n) for g, n, *_ in grass] + [(g, n) for g, n, _ in water if (g, n) not in {(a, b) for a, b, *_ in grass}]
    grass_of = {(g, n): (m, dy, nt) for g, n, m, dy, nt in grass}
    strings, label_of = [], {}

    def label(blob):
        if blob not in label_of:
            label_of[blob] = f"GuideStr{len(label_of)}"
            strings.append(f"{label_of[blob]}:\n{db(blob + bytes([0x50]))}")
        return label_of[blob]
    lines, most = ["WildIndex:"], [0, 0]
    for g, n in maps:
        m, dy, nt = grass_of.get((g, n), ([], [], []))
        ptrs = []
        for k, sp in enumerate((m, dy, nt, water_of.get((g, n), []))):
            blob, count = name_list(sp, names, enc)
            most[k == 3] = max(most[k == 3], count)
            ptrs.append(label(blob))
        lines.append(f"\tdb ${g:02X}, ${n:02X}\n\tdw {', '.join(ptrs)}")
    assert most[0] <= MAX_GRASS_LINES and most[1] <= MAX_WATER_LINES, f"wild lists too long for the page: {most}"
    lines.append("\tdb $FF")
    texts = {
        "TxtGuideTitle": "공략",
        "TxtMenuItems": "이 맵 출현\n전설과 환상\n다음 목표\n도감 안내",
        "TxtSoon": "준비 중입니다",
        "TxtWildTitle": "이 맵 출현",
        "TxtNoWild": "야생 포켓몬이 없다",
        "TxtMorn": "풀숲 (아침)",
        "TxtDay": "풀숲 (낮)",
        "TxtNite": "풀숲 (밤)",
        "TxtWater": "물 위",
    }
    out = ["DEF NUM_PAGES EQU 4"]
    out += [f"{k}:\n{db(enc(v) + bytes([0x50]))}" for k, v in texts.items()]
    out.append("TimeLabels:\n\tdw TxtMorn, TxtDay, TxtNite")
    out += lines + strings
    return "\n".join(out) + "\n", len(maps)


def patch_guide(r, wild_start):
    d = r.d
    syms, spots = find_symbols(d)
    enc = charmap(d)
    free4 = 0x14000
    while d[free4 - 1] == 0:
        free4 -= 1
    free4 = (free4 + 0xF) & ~0xF
    assert 0x14000 - free4 >= 0x100, "bank 4: not enough free space"
    gb = GUIDE_BANK * 0x4000
    assert len(set(d[gb:gb + 0x4000])) == 1, f"bank {GUIDE_BANK:02X} is not free"
    items = spots["items"]
    orig = [d[items + k] | d[items + k + 1] << 8 for k in range(0, 54, 2)]
    inc = [f"DEF {k} EQU ${v:04X}" for k, v in syms.items()]
    inc += [f"DEF FarCall EQU $08", f"DEF SCGB_DIPLOMA EQU {SCGB_DIPLOMA}", f"DEF GUIDE_BANK EQU ${GUIDE_BANK:02X}",
            f"DEF BANK4_FREE EQU ${0x4000 + free4 - 0x10000:04X}",
            "MACRO ORIGINAL_START_MENU_ITEMS", "\tdw " + ", ".join(f"${v:04X}" for v in orig), "ENDM",
            "MACRO GUIDE_ITEM_STRING", db(enc("공략") + b"\x50"), "ENDM",
            "MACRO GUIDE_ITEM_DESC", db(enc("출현 전설\n목표 안내") + b"\x50"), "ENDM"]
    data, nmaps = build_data(d, wild_start, enc)
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "kr_syms.inc").write_text("\n".join(inc) + "\n", encoding="utf-8")
        (t / "guide_data.inc").write_text(data, encoding="utf-8")
        (t / "guide.asm").write_text((HERE / "kr_guide" / "guide.asm").read_text(encoding="utf-8"), encoding="utf-8")
        subprocess.run(["docker", "run", "--rm", "-v", f"{t}:/w", "-w", "/w", "pokegold-build", "sh", "-c",
                        "rgbasm -o guide.o guide.asm && rgblink -m guide.map -n guide.sym -o guide.gbc guide.o"],
                       check=True, capture_output=True)
        out = (t / "guide.gbc").read_bytes()
        sym = {l.split()[1]: int(l.split()[0].split(":")[1], 16) for l in (t / "guide.sym").read_text().splitlines()
               if l and not l.startswith(";")}
    b4 = out[free4:0x14000]
    b4 = b4[:len(b4.rstrip(b"\x00")) or 1]
    assert all(x == 0 for x in d[free4:free4 + len(b4)])
    d[free4:free4 + len(b4)] = b4
    code = out[gb:gb + 0x4000].rstrip(b"\x00")
    d[gb:gb + len(code)] = code
    r.log.append(f"guide: bank 04:{0x4000 + free4 - 0x10000:04X} {len(b4)} bytes (items + hooks), bank {GUIDE_BANK:02X} {len(code)} bytes "
                 f"({nmaps} maps) — " + ", ".join(f"{k} {v:04X}" for k, v in syms.items()))
    lo_hi = lambda v: [v & 0xFF, v >> 8]
    r.put("guide: START menu item table", spots["items_ref"], d[spots["items_ref"]:spots["items_ref"] + 2], lo_hi(sym["GuideMenuItems"]))
    r.put("guide: after 가방", spots["pack_site"], [0x3E, 0x02, 0xCD, *lo_hi(syms["AppendMenuList"])], [0xCD, *lo_hi(sym["GuidePackHook"])])
    r.put("guide: 닫다 only below 8 items", spots["exit_site"], [0x3E, 0x06, 0xCD, *lo_hi(syms["AppendMenuList"])], [0xCD, *lo_hi(sym["GuideExitHook"])])
