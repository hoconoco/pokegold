"""Korean Gold/Silver text encoding (charmap) read from the ROM itself — for new Korean text (guide menu).

How the Korean ROM writes text (found 2026-11-10, Gold AAUK = Silver AAXK here):
- CheckDict sends bytes < $0C to the two-byte handler (00:1229): lead byte $01-$0B + trail byte.
  Trail bytes $50-$5F are never used (they are control codes), so a code's slot is
  L = (lead - 1) * 240 + rank of the trail among $00-$FF without $50-$5F.
- Hangul = the 2350 syllables of KS X 1001 rows $B0-$C8, each row 96 slots (94 syllables + 2 empty pads,
  like EUC-KR $A1-$FE): row r, column k -> L = 1 + 96 r + k. All 245 distinct syllables of the 251 Pokémon
  names (6C:4C4A) match their official Korean names.
- Glyphs: 8x16, 1bpp, 16 bytes per code at ROM $1E0000 + code * 16 (glyph cache routine 7F:4225 —
  bank $78 + code / $400). The same bytes in Gold and Silver.
- $0B00-: jamo ㄱ-ㅉ ($B00-$B12), ㅏ-ㅢ ($B20-$B34), bars ($B3E-$B3F), 「」『』()!?-~…,. ($B60-$B6C), bold 0-9 ($BF0-$BF9).
- Left out: 댜 ($2F4) and 돐 ($31B) have empty glyphs; the 5 extra syllables in pad slots ($3D0 $62F $630 $6A0
  $830 — non-KS, read as 뢔 쌰 썌 쓔 쮸 from the glyphs, not confirmed by any text).
- Single bytes are the English charmap (constants/charmap.asm): digits $F6-$FF, ♂ $EF, ♀ $F5, space $7F, end $50.

Check: decodes the Pokémon, move and item name tables (NamesPointers types 1, 2, 4); with --ko-names
(PokéAPI pokemon_species_names.csv) the Pokémon names are compared with the official Korean names.

Usage: python -X utf8 tools/kr_charset.py --rom .build/kr/baserom_kr.gbc --out .build/kr/charmap_kr.json [--ko-names <csv>]
"""
import argparse
import csv
import json
import re
from pathlib import Path

FONT = 0x1E0000
TRAILS = [t for t in range(256) if not 0x50 <= t <= 0x5F]          # 240 usable trail bytes
SYMBOLS = {**{c: 0x0B00 + i for i, c in enumerate("ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎㄲㄸㅃㅆㅉ")},
           **{c: 0x0B20 + i for i, c in enumerate("ㅏㅑㅓㅕㅗㅛㅜㅠㅡㅣㅐㅒㅔㅖㅘㅙㅚㅝㅞㅟㅢ")},
           **{c: 0x0B60 + i for i, c in enumerate("「」『』()!?-~…,.")}}
EMPTY_GLYPH = {0x02F4, 0x031B}
NAMES_POINTERS = 0x35C3          # bank 0 table of (bank, address) per name type — found from GetName's code


def code_of_slot(slot):
    return (slot // 240 + 1) << 8 | TRAILS[slot % 240]


def hangul():
    out = {}
    for row, hi in enumerate(range(0xB0, 0xC9)):
        for col, lo in enumerate(range(0xA1, 0xFF)):
            out[bytes([hi, lo]).decode("euc-kr")] = code_of_slot(1 + 96 * row + col)
    return out


def single_bytes(repo):
    out = {}
    for line in (repo / "constants/charmap.asm").read_text(encoding="utf-8").splitlines():
        m = re.match(r'\s*charmap\s+"(.+?)",\s*\$([0-9a-fA-F]{2})', line)
        if m and len(m.group(1)) == 1 and m.group(1) not in out:
            out[m.group(1)] = int(m.group(2), 16)
    return out


def decoder(double, single):
    back2 = {v: k for k, v in double.items()}
    back1 = {v: k for k, v in single.items()}

    def decode(raw):
        s, k, unknown = [], 0, 0
        while k < len(raw) and raw[k] != 0x50:
            if 0x01 <= raw[k] <= 0x0B and k + 1 < len(raw):
                c = raw[k] << 8 | raw[k + 1]
                s.append(back2.get(c, "?")); unknown += c not in back2; k += 2
            else:
                s.append(back1.get(raw[k], "?")); unknown += raw[k] not in back1; k += 1
        return "".join(s), unknown
    return decode


def name_lists(rom, decode):
    """NamesPointers type 1 (Pokémon, fixed 10 bytes) and 2·4 (moves, items: '@'-terminated)"""
    def ptr(t):
        b, a = rom[NAMES_POINTERS + 3 * (t - 1)], rom[NAMES_POINTERS + 3 * (t - 1) + 1] | rom[NAMES_POINTERS + 3 * (t - 1) + 2] << 8
        return b * 0x4000 + a - 0x4000
    o = ptr(1)
    mons = [decode(rom[o + 10 * i:o + 10 * i + 10]) for i in range(251)]
    out = {"pokemon": mons}
    for t, name, n in ((2, "moves", 251), (4, "items", 255)):
        o, lst = ptr(t), []
        for _ in range(n):
            end = rom.index(0x50, o)
            lst.append(decode(rom[o:end + 1]))
            o = end + 1
        out[name] = lst
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True, help="Korean Gold or Silver ROM")
    ap.add_argument("--out", required=True)
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--ko-names", help="PokéAPI pokemon_species_names.csv (language 3 = Korean)")
    a = ap.parse_args()
    rom = Path(a.rom).read_bytes()
    glyph = lambda c: rom[FONT + 16 * c:FONT + 16 * c + 16]
    double = {ch: c for ch, c in hangul().items() if c not in EMPTY_GLYPH}
    double.update(SYMBOLS)
    bold = {str(i): 0x0BF0 + i for i in range(10)}      # plain digits are single bytes ($F6-$FF); the bold ones apart
    blank = [ch for ch, c in double.items() if not any(glyph(c))]
    assert not blank, f"codes with an empty glyph: {blank[:10]}"
    single = single_bytes(Path(a.repo))
    decode = decoder(double, single)
    lists = name_lists(rom, decode)
    report = []
    for kind, lst in lists.items():
        bad = [(i + 1, s) for i, (s, u) in enumerate(lst) if u]
        report.append(f"{kind}: {len(lst)} names, {len(lst) - len(bad)} decoded fully" + (f", unknown codes in {bad[:5]}" if bad else ""))
    if a.ko_names:
        ko = {int(r["pokemon_species_id"]): r["name"] for r in csv.DictReader(open(a.ko_names, encoding="utf-8"))
              if r["local_language_id"] == "3"}
        diff = [(i + 1, s, ko.get(i + 1)) for i, (s, _) in enumerate(lists["pokemon"]) if s != ko.get(i + 1)]
        report.append(f"pokemon vs official Korean names: {251 - len(diff)} same, different: {diff}")
    json.dump({"double": {k: f"{v:04X}" for k, v in sorted(double.items(), key=lambda kv: kv[1])},
               "bold_digits": {k: f"{v:04X}" for k, v in bold.items()},
               "single": {k: f"{v:02X}" for k, v in single.items()},
               "samples": {k: [s for s, _ in v[:20]] for k, v in lists.items()}},
              open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{a.out}: {len(double)} two-byte characters ({sum(1 for k in double if '가' <= k <= '힣')} Hangul), "
          f"{len(single)} single-byte")
    print("\n".join(report))


if __name__ == "__main__":
    main()
