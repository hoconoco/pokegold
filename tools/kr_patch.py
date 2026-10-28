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

Usage: python -X utf8 tools/kr_patch.py --base .build/kr/baserom_kr.gbc --out pokegold_kr.gbc
"""

import argparse
import hashlib
import re
from pathlib import Path

BASE_SHA1 = "c0ff3999e1093e1af59ef3eea3f1bfd7c1f18a65"

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


def fix_global_checksum(d):
    s = (sum(d) - d[0x14E] - d[0x14F]) & 0xFFFF
    d[0x14E], d[0x14F] = s >> 8, s & 0xFF


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--log")
    args = ap.parse_args()
    data = Path(args.base).read_bytes()
    assert hashlib.sha1(data).hexdigest() == BASE_SHA1, "not the Korean Gold ROM this patch was made for"
    r = Rom(data)
    patch_shiny(r)
    patch_exp(r)
    fix_global_checksum(r.d)
    Path(args.out).write_bytes(bytes(r.d))
    text = "\n".join(r.log) + "\n"
    if args.log:
        Path(args.log).write_text(text, encoding="utf-8")
    print(f"{len(r.log)} patches -> {args.out}")


if __name__ == "__main__":
    main()
