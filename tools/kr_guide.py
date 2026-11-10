"""Guide menu ('공략') for the Korean Gold/Silver mod — called by tools/kr_patch.py after the other patches.

- Korean ROM addresses are found from code patterns (each must match once, or all matches must agree):
  the options screen (Textbox, PlaceString, palettes, joypad), the START menu (item table, list builder,
  FadeToMenu/CloseSubmenu like the trainer card item) and the wild code (wMapGroup/wMapNumber, wTimeOfDay).
- Texts are Korean, encoded with tools/kr_charset.py (the ROM's own text encoding); Pokémon names are
  copied from the ROM's name table, so they are exactly the game's names.
- 이 맵 출현: lists made from the (already patched) wild tables of this ROM — grass per time of day, water.
- 전설과 환상: the legends met in map scripts (mod statics, 칠색조, 루기아) with their place and '끝' once their
  object's event flag is set (caught or defeated), and the three roaming beasts' current place (their map ->
  the place name of this ROM's landmark table), '불탄 탑 사건 뒤' before EVENT_RELEASED_THE_BEASTS.
- 다음 목표: GOALS below in story order — the first one whose event flag / badge bit is not set is shown.
- 도감 안내: species not caught yet with where to get them (tools/kr_guide_data.py docstring).
- Other facts (Korean RAM, constants, places, sources): tools/kr_guide_data.py.
- tools/kr_guide/guide.asm is assembled with rgbasm/rgblink in the pokegold-build Docker image; its two
  sections are copied into the free tail of bank 4 and into GUIDE_BANK, then three START menu spots are
  patched (item table pointer, the '가방' append, the '닫다' append).
"""
import re
import subprocess
import tempfile
from pathlib import Path

import kr_guide_data as D

HERE = Path(__file__).resolve().parent
GUIDE_BANK = 0x7D
SCGB_DIPLOMA = 8
LINE_TILES = 17                     # list column 2 .. 18 inside the frame
NEXT = 0x59                         # line break of the Korean text engine (the START menu descriptions use it; $4E is not one)
MAX_GRASS_LINES, MAX_WATER_LINES = 3, 1
GOAL_LINES = 6
DONE_COL = 16                       # guide.asm DONE_COL ('끝' on the legend page)
LEGEND_ORDER = ["ARTICUNO", "ZAPDOS", "MOLTRES", "MEWTWO", "MEW", "CELEBI", "HO_OH", "LUGIA"]

# (condition, text): event flag or badge, in story order (leader and item names as the Korean ROM writes them)
GOALS = [
    (("event", "EVENT_GOT_A_POKEMON_FROM_ELM"), "연두마을 공박사의\n연구소에서\n포켓몬을 받자"),
    (("event", "EVENT_GOT_MYSTERY_EGG_FROM_MR_POKEMON"), "30번 도로 북쪽 끝\n집에 심부름을 가자"),
    (("event", "EVENT_GAVE_MYSTERY_EGG_TO_ELM"), "받은 알을 연두마을\n공박사에게\n가져가자"),
    (("johto", "ZEPHYRBADGE"), "도라지시티 체육관\n관장 비상을 이기자"),
    (("event", "EVENT_CLEARED_SLOWPOKE_WELL"), "고동마을 야돈 우물의\n로켓단을 쫓아내자"),
    (("johto", "HIVEBADGE"), "고동마을 체육관\n관장 호일을 이기자"),
    (("event", "EVENT_GOT_HM01_CUT"), "너도밤나무 숲에서\n파오리를 찾아 주고\n풀베기를 받자"),
    (("johto", "PLAINBADGE"), "금빛시티 체육관\n관장 꼭두를 이기자"),
    (("event", "EVENT_FOUGHT_SUDOWOODO"), "금빛시티 꽃집에서\n꼬부기 물뿌리개를\n받아 36번 도로의\n나무에 뿌리자"),
    (("event", "EVENT_RELEASED_THE_BEASTS"), "인주시티 불탄 탑\n지하에 가 보자"),
    (("johto", "FOGBADGE"), "인주시티 체육관\n관장 유빈을 이기자"),
    (("event", "EVENT_GOT_HM03_SURF"), "인주시티 전통 무용수\n다섯을 모두 이기고\n파도타기를 받자"),
    (("johto", "STORMBADGE"), "41번 도로 바다를\n건너 진청시티\n체육관 관장 사도를\n이기자"),
    (("event", "EVENT_JASMINE_RETURNED_TO_GYM"), "진청시티 약국에서\n비전 신약을 받아\n담청등대 꼭대기의\n규리에게 주자"),
    (("johto", "MINERALBADGE"), "담청시티 체육관\n관장 규리를 이기자"),
    (("event", "EVENT_CLEARED_ROCKET_HIDEOUT"), "분노의 호수에서\n목호를 만나고\n황토마을 로켓단\n아지트를 무찌르자"),
    (("johto", "GLACIERBADGE"), "황토마을 체육관\n관장 류옹을 이기자"),
    (("event", "EVENT_CLEARED_RADIO_TOWER"), "금빛시티 라디오타워의\n로켓단을 쫓아내자"),
    (("johto", "RISINGBADGE"), "검은먹시티 체육관\n관장 이향을 이기고\n용의 굴 시험을\n마치자"),
    (("event", "EVENT_BEAT_ELITE_FOUR"), "연두마을 동쪽\n27번 도로로 가서\n석영고원 사천왕과\n챔피언을 이기자"),
    (("event", "EVENT_GOT_SS_TICKET_FROM_ELM"), "연두마을 공박사에게\n승선 티켓을 받자"),
    (("kanto", "THUNDERBADGE"), "담청시티 항구에서\n쾌속선을 타고\n갈색시티 체육관\n관장 마티스를 이기자"),
    (("event", "EVENT_RETURNED_MACHINE_PART"), "발전소에 가 보고\n잃어버린 기계부품을\n찾아 주자\n(블루시티 체육관)"),
    (("kanto", "MARSHBADGE"), "노랑시티 체육관\n관장 초련을 이기자"),
    (("kanto", "RAINBOWBADGE"), "무지개시티 체육관\n관장 민화를 이기자"),
    (("kanto", "SOULBADGE"), "연분홍시티 체육관\n관장 도희를 이기자"),
    (("kanto", "CASCADEBADGE"), "블루시티 체육관\n관장 이슬을 이기자"),
    (("kanto", "BOULDERBADGE"), "회색시티 체육관\n관장 웅을 이기자"),
    (("kanto", "VOLCANOBADGE"), "쌍둥이섬 체육관\n관장 강연을 이기자"),
    (("kanto", "EARTHBADGE"), "상록시티 체육관\n관장 그린을 이기자"),
    (("event", "EVENT_RED_IN_MT_SILVER"), "28번 도로 끝\n은빛 산 꼭대기의\n레드를 이기자"),
]
GOAL_DONE = "모든 목표를 마쳤다!\n전설과 환상, 도감\n안내를 보자"
# wRoamMon1 comes from wRoamMon1MapGroup (struct: species, level, group, number, HP, DVs) — the species address
# alone also matches unrelated Korean code
RAM = ["wEventFlags", "wJohtoBadges", "wKantoBadges", "wPokedexCaught", "wRoamMon1MapGroup", "wStringBuffer1",
       "wMapGroup", "wTimeOfDay"]
ROAM_STRUCT = 7


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


def width(raw):
    w, k = 0, 0
    while k < len(raw):
        k += 2 if 1 <= raw[k] <= 0x0B else 1
        w += 1
    return w


def check_lines(name, raw, most_lines, tiles=LINE_TILES):
    lines = raw.split(bytes([NEXT]))
    assert len(lines) <= most_lines and all(width(x) <= tiles for x in lines), f"{name}: too long for the page"


class Facts:
    """everything the pages need, from the source, the English build and this Korean ROM"""

    def __init__(self, d, wild_start, en_rom, en_sym, repo):
        self.repo, self.d = Path(repo), d
        self.en = Path(en_rom).read_bytes()
        self.sym = D.en_symbols(en_sym)
        self.ram = {k: D.find_ram(self.en, bytes(d), self.sym[k][1]) for k in RAM}
        self.species = D.species_names(self.repo)
        self.maps = D.map_table(self.repo)
        self.trees, self.tree_sets = D.tree_species(self.repo)
        names = set(self.species) | {lm for _, _, lm, _ in self.maps.values()} | {f for *_, f in self.maps.values()}
        names |= {f"GROUP_{m}" for m, _ in self.trees} | {f"MAP_{m}" for m, _ in self.trees}
        names |= {c for (k, c), _ in GOALS} | {"EVENT_RELEASED_THE_BEASTS", "NUM_LANDMARKS"}
        self.legends = D.legends(self.repo, LEGEND_ORDER)
        names |= {f for *_, f in self.legends}
        self.C = D.consts(self.repo, names)
        self.place = D.landmark_names(self.en, self.sym, d, self.C["NUM_LANDMARKS"])
        self.landmark_of = {(g, n): self.C[lm] for g, n, lm, _ in self.maps.values()}
        self.fishgroup_of = {(g, n): self.C[f] for g, n, _, f in self.maps.values()}
        self.grass, self.water = wild_tables(d, wild_start)

    def flag(self, kind, name):
        """(RAM address, mask) of an event flag or a badge"""
        if kind == "event":
            n = self.C[name]
            return self.ram["wEventFlags"] + n // 8, 1 << (n % 8)
        n = self.C[name] - (self.C["BOULDERBADGE"] if kind == "kanto" else 0)
        return self.ram["wJohtoBadges" if kind == "johto" else "wKantoBadges"], 1 << n


def dex_strings(f, names, enc):
    """species id -> raw string 'name where' (the earliest place among the location sources)"""
    sid = {s: i + 1 for i, s in enumerate(f.species)}
    best = {}                       # species id -> (landmark, priority, method)

    def offer(sp, mapid, prio, method):
        lm = f.landmark_of.get(mapid)
        if lm is None:
            return
        key = (lm, prio)
        if sp not in best or key < best[sp][:2]:
            best[sp] = (lm, prio, method)
    for g, n, *times in f.grass:
        for t in times:
            for sp in t:
                offer(sp, (g, n), 0, "")
    fish = D.fish_species(f.repo)
    for g, n, sl in f.water:
        for sp in sl:
            offer(sp, (g, n), 0, "")
        for s in fish.get(f.fishgroup_of.get((g, n)), ()):
            offer(sid[s], (g, n), 1, "낚시")
    for mc, sps in f.trees:
        for s in sps:
            offer(sid[s], (f.C[f"GROUP_{mc}"], f.C[f"MAP_{mc}"]), 2, "박치기")
    for mname, cmd, s, _ in D.map_scripts(f.repo):
        if mname in D.NOT_A_SOURCE or s in D.ROAMERS or s not in sid:
            continue
        g, n, _, _ = f.maps[mname]
        offer(sid[s], (g, n), 3, {"loadwildmon": "만남", "givepoke": "선물", "giveegg": "알 선물"}[cmd])
    for mname, s in D.trades(f.repo):
        g, n, _, _ = f.maps[mname]
        offer(sid[s], (g, n), 4, "교환")
    g, n, _, _ = f.maps["NationalParkBugContest"]
    for s in D.contest_species(f.repo):
        offer(sid[s], (g, n), 2, "곤충채집")
    evos = D.evolutions(f.en, f.sym)
    pre = {}
    for a, outs in evos.items():
        for b in outs:
            pre.setdefault(b, a)
    rock = {sid[s] for s in f.tree_sets.get("TREEMON_SET_ROCK", ())}
    roam = {sid[s] for s in D.ROAMERS}
    # obtainable in this game: a direct source, or evolve an obtainable one, or breed an obtainable evolution
    can = set(best) | rock | roam
    while True:
        more = {sp for sp in range(1, 252) if sp not in can and (pre.get(sp) in can or any(e in can for e in evos[sp]))}
        if not more:
            break
        can |= more
    out = {}
    for sp in range(1, 252):
        name = names[sp][0]
        if sp in roam:
            parts = [name, enc("배회")]
        elif sp in best:
            lm, _, method = best[sp]
            parts = [name, f.place[lm]] + ([enc(method)] if method else [])
        elif sp in rock:
            parts = [name, enc("바위깨기")]
        elif pre.get(sp) in can:
            parts = [name, names[pre[sp]][0], enc("진화")]
        elif any(e in can for e in evos[sp]):
            parts = [name, names[next(e for e in evos[sp] if e in can)][0], enc("알")]
        else:
            parts = [name, enc("통신 교환")]
        raw = b"\x7f".join(parts)
        if width(raw) > LINE_TILES:
            raw = b"\x7f".join([parts[0], parts[1].replace(b"\x7f", b"")] + parts[2:])
        assert width(raw) <= LINE_TILES, f"dex line too long: {sp}"
        out[sp] = raw
    return out


def build_data(f, enc):
    names = mon_names(f.d)
    water_of = {(g, n): sp for g, n, sp in f.water}
    maps = [(g, n) for g, n, *_ in f.grass] + [(g, n) for g, n, _ in f.water if (g, n) not in {(a, b) for a, b, *_ in f.grass}]
    grass_of = {(g, n): (m, dy, nt) for g, n, m, dy, nt in f.grass}
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
        ptrs.append(label(f.place[f.landmark_of[(g, n)]]))
        lines.append(f"\tdb ${g:02X}, ${n:02X}\n\tdw {', '.join(ptrs)}")
    assert most[0] <= MAX_GRASS_LINES and most[1] <= MAX_WATER_LINES, f"wild lists too long for the page: {most}"
    lines.append("\tdb $FF")
    # 전설과 환상
    sid = {s: i + 1 for i, s in enumerate(f.species)}
    lines.append("LegendTable:")
    for sp, mname, flag in f.legends:
        g, n, _, _ = f.maps[mname]
        text = names[sid[sp]][0] + b"\x7f" + f.place[f.landmark_of[(g, n)]]
        check_lines(sp, text, 1, DONE_COL - 3)
        addr, mask = f.flag("event", flag)
        lines.append(f"\tdb 0\n\tdw {label(text)}, ${addr:04X}\n\tdb ${mask:02X}")
    for k, sp in enumerate(D.ROAMERS):
        struct = f.ram["wRoamMon1MapGroup"] - 2 + ROAM_STRUCT * k
        lines.append(f"\tdb 1\n\tdw {label(names[sid[sp]][0])}, ${struct:04X}\n\tdb 0")
    lines.append("\tdb $FF")
    # 다음 목표
    lines.append("GoalTable:")
    for (kind, name), text in GOALS:
        raw = enc(text)
        check_lines(name, raw, GOAL_LINES)
        addr, mask = f.flag(kind, name)
        lines.append(f"\tdw ${addr:04X}\n\tdb ${mask:02X}\n\tdw {label(raw)}")
    check_lines("GOAL_DONE", enc(GOAL_DONE), GOAL_LINES)
    lines.append(f"\tdw 0, {label(enc(GOAL_DONE))}")
    # 도감 안내
    dex = dex_strings(f, names, enc)
    lines.append("DexStrings:\n" + "\n".join(f"\tdw {label(dex[sp])}" for sp in range(1, 252)))
    texts = {
        "TxtGuideTitle": "공략",
        "TxtMenuItems": "이 맵 출현\n전설과 환상\n다음 목표\n도감 안내",
        "TxtWildTitle": "이 맵 출현",
        "TxtNoWild": "야생 포켓몬이 없다",
        "TxtMorn": "풀숲 (아침)",
        "TxtDay": "풀숲 (낮)",
        "TxtNite": "풀숲 (밤)",
        "TxtWater": "물 위",
        "TxtLegendTitle": "전설과 환상",
        "TxtDone": "끝",
        "TxtNotYet": "불탄 탑 사건 뒤",
        "TxtGoalTitle": "다음 목표",
        "TxtDexTitle": "도감 안내 (못 잡은 종)",
        "TxtDexAll": "모두 잡았다!",
    }
    released = f.flag("event", "EVENT_RELEASED_THE_BEASTS")
    out = ["DEF NUM_PAGES EQU 4", f"DEF RELEASED_ADDR EQU ${released[0]:04X}", f"DEF RELEASED_MASK EQU ${released[1]:02X}"]
    out += [f"{k}:\n{db(enc(v) + bytes([0x50]))}" for k, v in texts.items()]
    out.append("TimeLabels:\n\tdw TxtMorn, TxtDay, TxtNite")
    out += lines + strings
    dex_where = {sp: dex[sp] for sp in range(1, 252)}
    return "\n".join(out) + "\n", len(maps), dex_where


def patch_guide(r, wild_start, en_rom, en_sym, repo):
    d = r.d
    syms, spots = find_symbols(d)
    enc = charmap(d)
    facts = Facts(d, wild_start, en_rom, en_sym, repo)
    for k in ("wMapGroup", "wTimeOfDay"):
        assert facts.ram[k] == syms[k], f"{k}: {facts.ram[k]:04X} != {syms[k]:04X}"
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
    inc += [f"DEF {k} EQU ${facts.ram[k]:04X}" for k in ("wStringBuffer1", "wPokedexCaught")]
    inc += [f"DEF FarCall EQU $08", f"DEF SCGB_DIPLOMA EQU {SCGB_DIPLOMA}", f"DEF GUIDE_BANK EQU ${GUIDE_BANK:02X}",
            f"DEF BANK4_FREE EQU ${0x4000 + free4 - 0x10000:04X}",
            "MACRO ORIGINAL_START_MENU_ITEMS", "\tdw " + ", ".join(f"${v:04X}" for v in orig), "ENDM",
            "MACRO GUIDE_ITEM_STRING", db(enc("공략") + b"\x50"), "ENDM",
            "MACRO GUIDE_ITEM_DESC", db(enc("출현 전설\n목표 안내") + b"\x50"), "ENDM"]
    data, nmaps, dex = build_data(facts, enc)
    import kr_charset
    dec = kr_charset.decoder({**kr_charset.hangul(), **kr_charset.SYMBOLS}, kr_charset.single_bytes(HERE.parent))
    end = bytes([0x50])
    r.log += [f"guide dex {sp:3}: " + dec(raw + end)[0].replace("　", " ") for sp, raw in dex.items()]
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "kr_syms.inc").write_text("\n".join(inc) + "\n", encoding="utf-8")
        (t / "guide_data.inc").write_text(data, encoding="utf-8")
        (t / "guide.asm").write_text((HERE / "kr_guide" / "guide.asm").read_text(encoding="utf-8"), encoding="utf-8")
        res = subprocess.run(["docker", "run", "--rm", "-v", f"{t}:/w", "-w", "/w", "pokegold-build", "sh", "-c",
                              "rgbasm -o guide.o guide.asm && rgblink -m guide.map -n guide.sym -o guide.gbc guide.o"],
                             capture_output=True, encoding="utf-8")
        assert res.returncode == 0, res.stderr[-3000:]
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
                 f"({nmaps} maps) — " + ", ".join(f"{k} {v:04X}" for k, v in {**syms, **facts.ram}.items()))
    lo_hi = lambda v: [v & 0xFF, v >> 8]
    r.put("guide: START menu item table", spots["items_ref"], d[spots["items_ref"]:spots["items_ref"] + 2], lo_hi(sym["GuideMenuItems"]))
    r.put("guide: after 가방", spots["pack_site"], [0x3E, 0x02, 0xCD, *lo_hi(syms["AppendMenuList"])], [0xCD, *lo_hi(sym["GuidePackHook"])])
    r.put("guide: 닫다 only below 8 items", spots["exit_site"], [0x3E, 0x06, 0xCD, *lo_hi(syms["AppendMenuList"])], [0xCD, *lo_hi(sym["GuideExitHook"])])
