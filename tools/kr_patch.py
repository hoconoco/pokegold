"""Port the mod (mod/rea-gold) to the official Korean Gold ROM (POKEMON_GLD AAUK) as binary patches.

The Korean ROM shares the English engine but every address moved, so each patch point is
found by a wildcard byte pattern (operands of calls/loads masked) that must match exactly once,
and the original bytes are checked before writing. RAM/ROM addresses used in new code are read
from the matched bytes or listed in KR below (all taken from the Korean ROM itself).

Patches:
- shiny: wild (forced-shiny branch for every wild battle; Unown retries stay normal so a locked
  I/V letter cannot loop forever), roaming init, gift mons (party and box), day-care eggs.
  Shiny DVs = random Atk with the shiny bit, Def/Spd/Spc 10 (genders stay mixed).
- exp all: participants get full exp (no even split), alive non-egg non-participants get half.

New routines go into the zero-filled tail of the bank that calls them.

- 2nd stage: 5x exp and prize money, every ball catches, even species odds in grass/water, the other
  version's exclusives in spare wild slots, Prof. Elm trade evolution after the 8th badge (no new text —
  the Korean text encoding is not mapped yet). Korean Silver (AAXK) uses the same code addresses.
- guide menu: START menu '공략' (tools/kr_guide.py, Korean text with tools/kr_charset.py).

Usage: python -X utf8 tools/kr_patch.py --base .build/kr/baserom_kr.gbc --out pokegold_kr.gbc
       python -X utf8 tools/kr_patch.py --base .build/kr/baserom_kr_silver.gbc --out pokesilver_kr.gbc
"""

import argparse
import hashlib
import re
import subprocess
from pathlib import Path

from kr_guide import patch_guide

BASE_SHA1 = {"c0ff3999e1093e1af59ef3eea3f1bfd7c1f18a65": "GOLD",     # POKEMON_GLD AAUK
             "cb22d7e03a74dc3a563fde6be8626626b2b392e7": "SILVER"}   # POKEMON_SLV AAXK (user-provided 2026-11-09)

# Korean ROM addresses (read from the code at the matched patch points)
KR = dict(
    Random=0x313B, BattleRandom=0x314E, CopyBytes=0x31C2,
    GiveExperiencePoints=0x6CC5,
    wPartyCount=0xDB1F, wPartySpecies=0xDB20, wPartyMon1HP=0xDB27 + 0x22,
    wBattleParticipantsNotFainted=0xCB4A, wGivingExperienceToExpShareHolders=0xCC05,
    wBackupEnemyMonBaseStats=0xCC06, wEnemyMonBaseStats=0xD1CC, wEnemyMonDVs=0xD1B2,
    wEggMonDVs=0xDDD8, wStringBuffer1=0xD036,
)
PARTYMON_STRUCT_LENGTH = 0x30
EGG = 0xFD
SHINY_SPDSPC = 0xAA
BASESTATS_LEN = 7

# free space: (file offset of first usable byte, end) at the zero tail of each bank
FREE = {0x03: 0xFA00, 0x05: 0x17800, 0x0F: 0x3FF10}


def lo_hi(v):
    return [v & 0xFF, v >> 8]


def asm(items, origin):
    """Tiny assembler: items are ints (bytes), 'label:' strings, ('jr', op, label) or ('abs', label)."""
    labels, size = {}, 0
    for it in items:
        if isinstance(it, str):
            labels[it.rstrip(":")] = origin + size
        elif isinstance(it, tuple):
            size += 2
        else:
            size += 1
    out = []
    for it in items:
        if isinstance(it, str):
            continue
        if isinstance(it, tuple) and it[0] == "jr":
            rel = labels[it[2]] - (origin + len(out) + 2)
            assert -128 <= rel <= 127, it
            out += [it[1], rel & 0xFF]
        elif isinstance(it, tuple):
            out += lo_hi(labels[it[1]])
        else:
            out.append(it)
    return bytes(out)


def gb_addr(off):
    return off if off < 0x4000 else 0x4000 + off % 0x4000


class Rom:
    def __init__(self, data):
        self.d = bytearray(data)
        self.log = []
        self.free = dict(FREE)

    def find(self, name, pattern):
        rx = re.compile(b"".join(b"." if t == "??" else re.escape(bytes([int(t, 16)]))
                                 for t in pattern.split()), re.S)
        hits = [m.start() for m in rx.finditer(bytes(self.d))]
        assert len(hits) == 1, f"{name}: {len(hits)} matches"
        return hits[0]

    def put(self, name, off, expect, new):
        expect, new = bytes(expect), bytes(new)
        assert self.d[off:off + len(expect)] == expect, f"{name}: unexpected bytes at {off:06x}"
        assert len(new) <= len(expect), f"{name}: new code longer than original"
        new = new + bytes(len(expect) - len(new))  # pad with nop
        self.d[off:off + len(new)] = new
        self.log.append(f"{name}: {off:06x} {expect.hex()} -> {new.hex()}")

    def alloc(self, name, bank, code_fn):
        off = self.free[bank]
        code = code_fn(gb_addr(off))
        assert all(b == 0 for b in self.d[off:off + len(code)]), f"{name}: free space not empty"
        assert (off + len(code)) // 0x4000 == bank, f"{name}: bank {bank:02x} full"
        self.d[off:off + len(code)] = code
        self.free[bank] = off + len(code)
        self.log.append(f"{name}: new code {len(code)} bytes at {bank:02x}:{gb_addr(off):04x}")
        return gb_addr(off)


def shiny_bc(random):
    # call Random/BattleRandom / and $f0 / or $2a / ld b,a / ld c,$aa / ret
    return lambda org: bytes([0xCD, *lo_hi(random), 0xE6, 0xF0, 0xF6, 0x2A, 0x47, 0x0E, SHINY_SPDSPC, 0xC9])


def patch_shiny(r):
    battle_shiny = r.alloc("ShinyDVs (battle)", 0x0F, shiny_bc(KR["BattleRandom"]))
    call_bs = [0xCD, *lo_hi(battle_shiny)]

    # wild: make the forced-shiny branch unconditional and give it a random shiny Atk DV
    off = r.find("wild", "FE 07 20 06 06 EA 0E AA 18 08 CD 4E 31 47 CD 4E 31 4F")
    r.put("wild: always shiny", off + 2, [0x20, 0x06], [])
    r.put("wild: random shiny atk", off + 4, [0x06, 0xEA, 0x0E, 0xAA], call_bs)
    # Magikarp size retries jump back to the shiny entry (Unown retry stays on normal DVs)
    gen, shiny_entry = off + 10, off + 4
    for jr_off, op in ((0x3E897, 0x30), (0x3E8A5, 0x30), (0x3E8C1, 0x38)):
        old = r.d[jr_off + 1] - 256
        assert r.d[jr_off] == op and jr_off + 2 + old == gen, f"magikarp retry {jr_off:06x}"
        r.put("wild: magikarp retry shiny", jr_off, [op, old & 0xFF], [op, (shiny_entry - jr_off - 2) & 0xFF])

    # roaming: first DV init
    off = r.find("roam", "CD ?? ?? 23 CD 4E 31 32 4F CD 4E 31 77 47 18 ??")
    r.put("roam: shiny", off + 4, r.d[off + 4:off + 14],
          call_bs + [0x71, 0x2B, 0x70])  # ld [hl],c / dec hl / ld [hl],b

    # gift mons into the party (TryAddMonToParty, not in battle)
    gift_shiny = r.alloc("ShinyDVs (gift)", 0x03, shiny_bc(KR["Random"]))
    off = r.find("gift", "FA D3 D1 A7 20 ?? CD 3B 31 47 CD 3B 31 4F 78 12")
    r.put("gift: shiny", off + 6, r.d[off + 6:off + 14], [0xCD, *lo_hi(gift_shiny)])

    # gift mons sent to the box (GivePoke when the party is full): callfar LoadEnemyMon / call SendMonIntoBox
    off = r.find("gift box", "EA ?? ?? 21 ?? ?? 3E 0F CF CD ?? ?? D2 ?? ??")
    send = r.d[off + 10] | r.d[off + 11] << 8
    box_shiny = r.alloc("ShinyBoxGift", 0x03, lambda org: bytes([
        0xCD, *lo_hi(KR["Random"]), 0xE6, 0xF0, 0xF6, 0x2A, 0xEA, *lo_hi(KR["wEnemyMonDVs"]),
        0x3E, SHINY_SPDSPC, 0xEA, *lo_hi(KR["wEnemyMonDVs"] + 1),
        0xC3, *lo_hi(send)]))
    r.put("gift box: shiny", off + 9, r.d[off + 9:off + 12], [0xCD, *lo_hi(box_shiny)])

    # day-care eggs: at .SkipDVs (ld hl,wStringBuffer1) force shiny egg DVs first
    off = r.find("egg", "1A E6 07 47 7E E6 F8 80 77 21 36 D0 11 ?? ?? 01 0B 00")
    egg_shiny = r.alloc("ShinyEgg", 0x05, lambda org: bytes([
        0x21, *lo_hi(KR["wEggMonDVs"]), 0x7E, 0xE6, 0xF0, 0xF6, 0x2A, 0x22, 0x36, SHINY_SPDSPC,
        0x21, *lo_hi(KR["wStringBuffer1"]), 0xC9]))
    r.put("egg: shiny", off + 9, [0x21, 0x36, 0xD0], [0xCD, *lo_hi(egg_shiny)])


def patch_exp(r):
    k = KR
    get_mons = r.alloc("GetExpAllMons", 0x0F, lambda org: asm([
        0xFA, *lo_hi(k["wPartyCount"]), 0x47,
        0x21, *lo_hi(k["wPartyMon1HP"]), 0x0E, 0x01, 0x16, 0x00,
        "loop:", 0x2A, 0xB6, 0x2B, ("jr", 0x28, "next"), 0x7A, 0xB1, 0x57,
        "next:", 0xCB, 0x21, 0xD5, 0x11, PARTYMON_STRUCT_LENGTH, 0x00, 0x19, 0xD1, 0x05, ("jr", 0x20, "loop"),
        0x21, *lo_hi(k["wPartySpecies"]), 0x0E, 0x01,
        "egg:", 0x2A, 0xFE, 0xFF, ("jr", 0x28, "done"), 0xFE, EGG, ("jr", 0x20, "not_egg"),
        0x79, 0x2F, 0xA2, 0x57,
        "not_egg:", 0xCB, 0x21, ("jr", 0x18, "egg"),
        "done:", 0xFA, *lo_hi(k["wBattleParticipantsNotFainted"]), 0x2F, 0xA2, 0x57, 0xC9,
    ], org))

    off = r.find("exp", "CD ?? ?? 28 0B 21 CC D1 06 07 CB 3E 23 05 20 FA")
    end = r.find("exp end", "CD C5 6C F1 EA 4A CB C9") + 8
    copy = lambda src, dst: [0x21, *lo_hi(src), 0x11, *lo_hi(dst), 0x01, BASESTATS_LEN, 0x00,
                             0xCD, *lo_hi(k["CopyBytes"])]
    new = asm([
        0xCD, *lo_hi(get_mons), 0xD5,
        *copy(k["wEnemyMonBaseStats"], k["wBackupEnemyMonBaseStats"]),
        0xAF, 0xEA, *lo_hi(k["wGivingExperienceToExpShareHolders"]),
        0xCD, *lo_hi(k["GiveExperiencePoints"]),
        0xD1, 0x7A, 0xA7, 0xC8,
        0xFA, *lo_hi(k["wBattleParticipantsNotFainted"]), 0xF5, 0x7A,
        0xEA, *lo_hi(k["wBattleParticipantsNotFainted"]),
        *copy(k["wBackupEnemyMonBaseStats"], k["wEnemyMonBaseStats"]),
        0x21, *lo_hi(k["wEnemyMonBaseStats"]), 0x06, BASESTATS_LEN,
        "halve:", 0xCB, 0x3E, 0x23, 0x05, ("jr", 0x20, "halve"),
        0x3E, 0x01, 0xEA, *lo_hi(k["wGivingExperienceToExpShareHolders"]),
        0xCD, *lo_hi(k["GiveExperiencePoints"]),
        0xF1, 0xEA, *lo_hi(k["wBattleParticipantsNotFainted"]), 0xC9,
    ], gb_addr(off))
    r.put("exp all", off, r.d[off:end], new)

    off = r.find("exp split", "FA ?? ?? A7 C0 CD 4E 6F AF EA")
    r.put("exp: no even split", off + 5, [0xCD, 0x4E, 0x6F], [])


def wild_slots(data, start):
    """Walk Johto grass/water and Kanto grass/water tables from start.
    Returns (end offset, offsets of the species bytes mix_wild.py may change)."""
    off, mixable = start, []
    for kind in ("grass", "water", "grass", "water"):
        while data[off] != 0xFF:
            if kind == "grass":
                slots = [off + 5 + t * 14 + s * 2 + 1 for t in range(3) for s in range(7)]
                mixable += [slots[t * 7 + s] for t in range(3) for s in (3, 4, 5)]
                off += 5 + 42
            else:
                mixable.append(off + 3 + 2 * 2 + 1)
                off += 3 + 6
        off += 1
    return off, set(mixable)


def patch_wild(r, en_rom, en_sym):
    """Copy the species that tools/mix_wild.py put into the rarer slots of the English build
    into the same slots of the Korean tables. Species and map ids are the same in both ROMs and
    the tables have the same maps in the same order, but the Korean data differs in 33 other bytes
    (some levels and version species), so only the mixed species bytes are copied and the rest of
    the Korean data is kept."""
    en = Path(en_rom).read_bytes()
    addr = next(int(l.split()[0][3:], 16) for l in open(en_sym, encoding="utf-8")
                if l.split()[1:] == ["JohtoGrassWildMons"])
    bank = next(int(l.split()[0][:2], 16) for l in open(en_sym, encoding="utf-8")
                if l.split()[1:] == ["JohtoGrassWildMons"])
    en_start = bank * 0x4000 + addr - 0x4000
    en_end, mixable = wild_slots(en, en_start)
    # first entry: map, rates and the first three morning slots are never mixed
    head = en[en_start:en_start + 5 + 6]
    kr_start = r.find("wild tables", " ".join(f"{b:02X}" for b in head))
    kr_end, _ = wild_slots(r.d, kr_start)
    assert kr_end - kr_start == en_end - en_start, "wild tables differ in size"
    shift = kr_start - en_start
    # same maps in the same order: compare each entry's map group/number
    maps_en = wild_maps(en, en_start)
    maps_kr = wild_maps(r.d, kr_start)
    assert maps_en == maps_kr, "wild tables list different maps"
    changed = 0
    for o in sorted(mixable):
        if r.d[o + shift] != en[o]:
            r.d[o + shift] = en[o]
            changed += 1
    r.log.append(f"wild: {kr_start:06x}-{kr_end:06x} {changed} mixed species copied from English build")


def wild_maps(data, start):
    off, maps = start, []
    for size in (47, 9, 47, 9):
        while data[off] != 0xFF:
            maps.append((data[off], data[off + 1]))
            off += size
        off += 1
    return maps


MAP_GROUP_POINTERS = (0x25, 0x40ED)  # same place in both ROMs
LEGEND_MAPS = {  # map: (group, number), as in constants/map_constants.asm
    "SeafoamGym": (6, 4), "PowerPlant": (7, 10), "VictoryRoad": (3, 82),
    "CeruleanCity": (7, 17), "VermilionCity": (12, 3), "IlexForest": (3, 44),
}


def map_events(d, group, number):
    """(file offset of the attributes, script bank, events offset, events size, object count)."""
    bank, ptrs = MAP_GROUP_POINTERS
    gp = d[bank * 0x4000 + ptrs - 0x4000 + 2 * (group - 1):][:2]
    hdr = bank * 0x4000 + (gp[0] | gp[1] << 8) - 0x4000 + 9 * (number - 1)
    at = d[hdr] * 0x4000 + (d[hdr + 3] | d[hdr + 4] << 8) - 0x4000
    sbank = d[at + 6]
    ev = sbank * 0x4000 + (d[at + 9] | d[at + 10] << 8) - 0x4000
    e = ev + 2
    e += 1 + 5 * d[e]
    e += 1 + 8 * d[e]
    e += 1 + 5 * d[e]
    objs = d[e]
    e += 1 + 13 * objs
    return at, sbank, ev, e - ev, objs


def patch_legends(r, en_rom):
    """Add the six legendary static encounters of the English build to the Korean maps.

    Map headers, script banks and event flag numbers are the same in both ROMs. For each map the
    Korean event list is copied to free space in the map's script bank with the English legend
    object (last object_event: position, sprite, palette, flag) appended, and the map attributes
    point to the new list. The legend script is the English one without its text box (the Korean
    ROM uses another text encoding): cry, wild battle, and the object disappears unless the
    player fled."""
    en = Path(en_rom).read_bytes()
    # The Korean script engine has one extra command, so commands from opentext ($47 in English)
    # up are numbered one higher. Checked on the Lugia script, whose English bytes are
    # 6a 47 4c .. .. 83 f9 00 8a 0f 49 33 18 03 18 09 (readvar $1c / ifequal $06 are unchanged).
    lugia_kr = r.find("script commands", "6B 48 4D ?? ?? 84 F9 00 8B 0F 4A 33 18 03 18 09")
    assert lugia_kr // 0x4000 == 0x47, "Lugia script not where expected"
    for name, (group, number) in LEGEND_MAPS.items():
        _, en_bank, en_ev, en_size, en_objs = map_events(en, group, number)
        at, bank, ev, size, objs = map_events(r.d, group, number)
        assert en_bank == bank and en_objs == objs + 1, f"{name}: maps differ"
        legend = bytearray(en[en_ev + en_size - 13:en_ev + en_size])
        script_en = en[bank * 0x4000 + (legend[9] | legend[10] << 8) - 0x4000:][:24]
        assert script_en[:3] == b"\x6a\x47\x4c" and script_en[5] == 0x83, f"{name}: legend script"
        species, level = script_en[6], script_en[13]
        obj = objs + 2  # object_const_def starts at 2
        r.free.setdefault(bank, bank * 0x4000 + 0x4000 - free_tail(r.d, bank) + 16)
        script = r.alloc(f"{name}: legend script", bank, lambda org: asm([
            0x6B,                         # faceplayer
            0x84, species, 0x00,          # cry
            0x8B, 0x0F,                   # pause 15
            0x5D, species, level,         # loadwildmon
            0x5F,                         # startbattle
            0x1C, 0x02,                   # readvar VAR_BATTLERESULT
            0x06, 0x02, ("abs", "fled"),  # ifequal DRAW, .fled
            0x6E, obj,                    # disappear
            "fled:", 0x60, 0x91,          # reloadmapafterbattle / end
        ], org))
        legend[9:11] = bytes(lo_hi(script))
        events = bytearray(r.d[ev:ev + size])
        events[size - 13 * objs - 1] += 1
        new_ev = r.alloc(f"{name}: events + legend", bank, lambda org: bytes(events + legend))
        r.put(f"{name}: events pointer", at + 9, r.d[at + 9:at + 11], lo_hi(new_ev))


def free_tail(d, bank):
    blk = d[bank * 0x4000:(bank + 1) * 0x4000]
    return len(blk) - len(bytes(blk).rstrip(b"\x00"))


# ---- mod 2nd stage (user request 2026-11-09): 5x exp / prize money, always-catch, even species odds,
# both versions' exclusives, Prof. Elm trade evolution. Korean Gold and Silver share every code address below
# (found by wildcard patterns, each matching exactly once in both ROMs).
KR2 = dict(
    Multiply=0x325C, Random=0x313B, hProduct=0xFFB5, hMultiplier=0xFFB9, wBattleReward=0xCB6C,
    GetFarByte=0x31D0, GetFarWord=0x31E4, GetPartyParamLocation=0x3B07, PlaySFX=0x3DEF, WaitSFX=0x3E21,
    SelectMonFromParty=(0x14, 0x4000), EvolvePokemon=(0x10, 0x5E0B), EvosAttacksPointers=(0x10, 0x63ED),
    wCurPartySpecies=0xD0C0, wScriptVar=0xD230, wLinkMode=0xD0FD,
)
EVOLVE_TRADE, EVOLVE_STAT, MON_ITEM, SFX_WRONG, LINK_TRADECENTER = 3, 5, 1, 0x19, 2
ENGINE_RISINGBADGE = 0x21


def alloc_tail(r, name, bank, code_fn, margin=4):
    """New code in the zero tail of any bank (keeps a small margin after the last non-zero byte)."""
    r.free.setdefault(bank, bank * 0x4000 + 0x4000 - free_tail(r.d, bank) + margin)
    return r.alloc(name, bank, code_fn)


def patch_exp5(r):
    m, k = KR2["Multiply"], KR2
    off = r.find("exp x5", "FA ?? ?? E0 ?? CD 5C 32 3E 07 E0 ?? 06 04 CD ?? ??")
    new = r.alloc("Exp x5", 0x0F, lambda org: bytes([0xCD, *lo_hi(m), 0x3E, 0x05, 0xE0, k["hMultiplier"] & 0xFF,
                                                     0xC3, *lo_hi(m)]))
    r.put("exp x5", off + 5, [0xCD, *lo_hi(m)], [0xCD, *lo_hi(new)])


def patch_money5(r):
    m, k = KR2["Multiply"], KR2
    off = r.find("prize x5", "21 ?? FF AF 22 22 22 FA ?? ?? 22 FA ?? ?? 77 CD 5C 32 21 ?? ?? AF 22 F0 ?? 22 F0 ?? 77 C9")
    p = k["hProduct"] & 0xFF
    new = alloc_tail(r, "Prize x5", off // 0x4000, lambda org: bytes([
        0xCD, *lo_hi(m), 0x3E, 0x05, 0xE0, k["hMultiplier"] & 0xFF, 0xCD, *lo_hi(m),
        0x21, *lo_hi(k["wBattleReward"]), 0xF0, p + 1, 0x22, 0xF0, p + 2, 0x22, 0xF0, p + 3, 0x77, 0xC9]))
    r.put("prize x5", off + 15, r.d[off + 15:off + 30], [0xC3, *lo_hi(new)])


def patch_catch(r):
    off = r.find("catch", "FA ?? ?? FE 01 CA ?? ?? FA ?? ?? 4F 21")
    r.put("catch: always", off + 3, r.d[off + 3:off + 8], [0xC3, r.d[off + 6], r.d[off + 7]])


def patch_even_odds(r):
    """ChooseWildEncounter: the probability bracket loop is replaced by an even species pick
    (same logic as the English engine/overworld/wildmons.asm). Bank $0A has only 56 free bytes,
    so the first part stays in place of the old loop (21 bytes) and jumps to the rest in the tail.
    Water tables start with 60 (grass with 30) — that tells the slot count without CheckOnWater."""
    off = r.find("even odds", "E5 CD ?? ?? FE 64 30 F9 3C 47 62 6B 2A B8 30 03 23 18 F9 4E 06 00 E1")
    site, back, rnd = gb_addr(off + 1), gb_addr(off + 22), KR2["Random"]
    tail = {}

    def rest(org):
        return asm([
            0xF8, 0x00, 0x2A, 0x66, 0x6F,                    # ld hl,sp+0 (wild data pushed) / ld a,[hli] / ld h,[hl] / ld l,a
            0xE5, 0x16, 0x00, 0x19, 0x19, 0x23, 0x7E, 0xE1,  # push hl / ld d,0 / add hl,de x2 / inc hl / ld a,[hl] / pop hl
            0xD5, 0x5F, 0x16, 0x00, 0x48, 0x23,              # push de / ld e,a / ld d,0 / ld c,b / inc hl
            "cnt:", 0x2A, 0xBB, ("jr", 0x20, "nx"), 0x14,
            "nx:", 0x23, 0x0D, ("jr", 0x20, "cnt"),
            0xCD, *lo_hi(rnd),
            "mod:", 0xBA, ("jr", 0x38, "md"), 0x92, ("jr", 0x18, "mod"),
            "md:", 0xA7, 0xD1, 0xC2, *lo_hi(site + 9),       # and a / pop de / jp nz, .rand
            0x7B, 0x87, 0x4F, 0x06, 0x00, 0xC3, *lo_hi(back),
        ], org)
    t = alloc_tail(r, "even odds (rest)", off // 0x4000, rest)
    first = asm([
        0x1A, 0xFE, 60, 0x06, 0x03, ("jr", 0x28, "go"), 0x06, 0x07,
        "go:", 0xCD, *lo_hi(rnd), 0xE6, 0x07, 0xB8, ("jr", 0x30, "go"),
        0x5F, 0xC3, *lo_hi(t),
    ], site)
    assert len(first) == 21 and first[9] == 0xCD, "even odds: .rand must be at site+9"
    r.put("even odds", off + 1, r.d[off + 1:off + 22], first)


def patch_elm_trade_evo(r):
    k = KR2
    bank = 0x60
    elm = r.find("Elm script", "91 6B 48 31 24 00 09 ?? ?? 31 44 00 09 ?? ?? 31 7C 00 09 ?? ?? 34 21 00 09") + 1
    assert elm // 0x4000 == bank
    sel_b, sel = k["SelectMonFromParty"]
    evo_b, evo = k["EvolvePokemon"]
    ptr_b, ptrs = k["EvosAttacksPointers"]
    routine = alloc_tail(r, "ElmTradeEvolution", bank, lambda org: asm([
        0xAF, 0xEA, *lo_hi(k["wScriptVar"]),
        0x3E, sel_b, 0x21, *lo_hi(sel), 0xCF, 0xD8,                  # farcall SelectMonFromParty / ret c
        0xFA, *lo_hi(k["wCurPartySpecies"]), 0xFE, EGG, ("jr", 0x28, "cannot"),
        0x3D, 0x4F, 0x06, 0x00, 0x21, *lo_hi(ptrs), 0x09, 0x09, 0x3E, ptr_b, 0xCD, *lo_hi(k["GetFarWord"]),
        "loop:", 0x3E, ptr_b, 0xCD, *lo_hi(k["GetFarByte"]), 0x23, 0xA7, ("jr", 0x28, "cannot"),
        0xFE, EVOLVE_TRADE, ("jr", 0x28, "trade"), 0xFE, EVOLVE_STAT, ("jr", 0x20, "next"), 0x23,
        "next:", 0x23, 0x23, ("jr", 0x18, "loop"),
        "trade:", 0x3E, ptr_b, 0xCD, *lo_hi(k["GetFarByte"]), 0xFE, 0xFF, ("jr", 0x28, "evolve"),
        0x47, 0xC5, 0x3E, MON_ITEM, 0xCD, *lo_hi(k["GetPartyParamLocation"]), 0xC1, 0x7E, 0xB8, ("jr", 0x20, "cannot"),
        "evolve:", 0x3E, LINK_TRADECENTER, 0xEA, *lo_hi(k["wLinkMode"]),
        0x3E, evo_b, 0x21, *lo_hi(evo), 0xCF,                       # farcall EvolvePokemon
        0xAF, 0xEA, *lo_hi(k["wLinkMode"]), 0x3E, 0x01, 0xEA, *lo_hi(k["wScriptVar"]), 0xC9,
        "cannot:", 0x11, SFX_WRONG, 0x00, 0xCD, *lo_hi(k["PlaySFX"]), 0xC3, *lo_hi(k["WaitSFX"]),
    ], org))
    back = gb_addr(elm) + 5
    script = alloc_tail(r, "ProfElmScript (trade evolution)", bank, lambda org: asm([
        0x6B,                                        # faceplayer
        0x34, ENGINE_RISINGBADGE, 0x00,              # checkflag ENGINE_RISINGBADGE
        0x08, ("abs", "no"),                         # iffalse .no
        0x0E, bank, *lo_hi(routine),                 # callasm ElmTradeEvolution
        0x09, ("abs", "yes"),                        # iftrue .yes
        "no:", 0x48, 0x31, 0x24, 0x00,               # opentext / checkevent EVENT_GOT_SS_TICKET_FROM_ELM
        0x04, bank, *lo_hi(back),                    # farsjump back to the original iftrue
        "yes:", 0x7B, 0x91,                          # reloadmap / end
    ], org))
    r.put("Elm: trade evolution", elm, r.d[elm:elm + 5], [0x04, bank, *lo_hi(script)])


def wild_species_offsets(data, start):
    """All species bytes of Johto grass/water and Kanto grass/water tables, in table order."""
    off, out = start, []
    for kind in ("grass", "water", "grass", "water"):
        while data[off] != 0xFF:
            if kind == "grass":
                out += [off + 5 + t * 14 + s * 2 + 1 for t in range(3) for s in range(7)]
                off += 5 + 42
            else:
                out += [off + 3 + s * 2 + 1 for s in range(3)]
                off += 3 + 6
        off += 1
    return off, out


def asm_species(text, version):
    """Species of every wild slot in an asm table file, for one version (IF DEF(_GOLD) / ELIF DEF(_SILVER))."""
    out, stack = [], []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("IF DEF(_"):
            stack.append(s == f"IF DEF(_{version})"); continue
        if s.startswith("ELIF DEF(_"):
            stack[-1] = s == f"ELIF DEF(_{version})"; continue
        if s == "ENDC":
            stack.pop(); continue
        if stack and not stack[-1]:
            continue
        m = re.match(r"db (\d+), (\w+)", s)
        if m:
            out.append(m.group(2))
    return out


WILD_FILES = ["data/wild/johto_grass.asm", "data/wild/johto_water.asm", "data/wild/kanto_grass.asm", "data/wild/kanto_water.asm"]


def patch_wild_src(r, en_rom, en_sym, version, repo, base_ref="origin/master"):
    """Copy every wild species the mod changed (tools/mix_wild.py: the other version's exclusives in spare
    slots) from the English build to the same slots of the Korean tables. Changed slots come from
    comparing the original tables at base_ref with the current ones (for this version), so the Korean
    data's own differences (33 bytes: some levels and version species) stay where nothing was changed."""
    en = Path(en_rom).read_bytes()
    line = next(l.split() for l in open(en_sym, encoding="utf-8") if l.split()[1:] == ["JohtoGrassWildMons"])
    bank, addr = (int(x, 16) for x in line[0].split(":"))
    en_start = bank * 0x4000 + addr - 0x4000
    en_end, en_offs = wild_species_offsets(en, en_start)
    head = en[en_start:en_start + 5 + 6]
    kr_start = r.find("wild tables", " ".join(f"{b:02X}" for b in head))
    kr_end, kr_offs = wild_species_offsets(r.d, kr_start)
    assert kr_end - kr_start == en_end - en_start and wild_maps(en, en_start) == wild_maps(r.d, kr_start)
    orig, cur = [], []
    for f in WILD_FILES:
        old = subprocess.run(["git", "-C", str(repo), "show", f"{base_ref}:{f}"], capture_output=True,
                             encoding="utf-8", check=True).stdout
        orig += asm_species(old, version)
        cur += asm_species((Path(repo) / f).read_text(encoding="utf-8"), version)
    assert len(orig) == len(cur) == len(en_offs), (len(orig), len(cur), len(en_offs))
    changed = 0
    for i, (a, b) in enumerate(zip(orig, cur)):
        if a != b:
            r.d[kr_offs[i]] = en[en_offs[i]]
            changed += 1
    r.log.append(f"wild: {kr_start:06x}-{kr_end:06x} {changed} changed species copied from the English build")
    return kr_start


def fix_global_checksum(d):
    s = (sum(d) - d[0x14E] - d[0x14F]) & 0xFFFF
    d[0x14E], d[0x14F] = s >> 8, s & 0xFF


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--en-rom", help="English mod build of the same version (default pokegold.gbc / pokesilver.gbc)")
    ap.add_argument("--en-sym")
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--log")
    args = ap.parse_args()
    data = Path(args.base).read_bytes()
    version = BASE_SHA1.get(hashlib.sha1(data).hexdigest())
    assert version, "not the Korean Gold/Silver ROM this patch was made for"
    stem = "pokegold" if version == "GOLD" else "pokesilver"
    en_rom, en_sym = args.en_rom or f"{stem}.gbc", args.en_sym or f"{stem}.sym"
    r = Rom(data)
    patch_shiny(r)
    patch_exp(r)
    wild_start = patch_wild_src(r, en_rom, en_sym, version, args.repo)
    patch_legends(r, en_rom)
    patch_exp5(r)
    patch_money5(r)
    patch_catch(r)
    patch_even_odds(r)
    patch_elm_trade_evo(r)
    patch_guide(r, wild_start)
    fix_global_checksum(r.d)
    Path(args.out).write_bytes(bytes(r.d))
    text = "\n".join(r.log) + "\n"
    if args.log:
        Path(args.log).write_text(text, encoding="utf-8")
    print(f"{len(r.log)} patches -> {args.out}")


if __name__ == "__main__":
    main()
