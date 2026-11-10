"""Gold/Silver exclusives in each other's wild tables (mod 2nd stage).

The game picks every species in a table with the same probability (engine/overworld/wildmons.asm), so a
slot whose species already appears earlier in the same table is spare. In maps where Gold and Silver
differ, spare slots of each version get the other version's exclusive species. Everything else (species,
levels, rates, maps) is the original game's: each region keeps its own Pokémon (user decision 2026-11-10 —
the earlier mix of the other region's Pokémon into the rarer slots put e.g. Aerodactyl Lv3 on Route 46).

Tables are always rebuilt from the original files at --base-ref, so rerunning does not stack changes.

Usage: python -X utf8 tools/mix_wild.py [--repo DIR] [--base-ref origin/master]
"""

import argparse
import re
import subprocess
from pathlib import Path

FILES = {
    "data/wild/kanto_grass.asm": "grass",
    "data/wild/kanto_water.asm": "water",
    "data/wild/johto_grass.asm": "grass",
    "data/wild/johto_water.asm": "water",
}


def git_show(repo, ref, path):
    return subprocess.run(
        ["git", "-C", str(repo), "show", f"{ref}:{path}"],
        capture_output=True, encoding="utf-8", check=True,
    ).stdout


def merge_versions(text, kind):
    """mod 2nd stage (user request 2026-11-09): the game now picks every species in a table with the same
    probability, so a slot whose species already appears earlier in the same table is spare. In maps where
    Gold and Silver differ (IF DEF(_GOLD) / ELIF DEF(_SILVER) blocks), spare slots of each version get the
    other version's exclusive species, so both versions' species appear in either game.
    Returns (new text, list of (map, version, species that did not fit))."""
    n = 7 if kind == "grass" else 3
    lines = text.splitlines(keepends=True)
    slot_re = re.compile(r"(\tdb )(\d+), (\w+)(.*)", re.S)
    blocks, mapname, cur = [], None, None   # (map, gold line indices, silver line indices)
    for i, line in enumerate(lines):
        m = re.match(r"\tdef_\w+_wildmons (\w+)", line)
        if m:
            mapname = m.group(1)
        s = line.strip()
        if s == "IF DEF(_GOLD)":
            cur = [mapname, [], []]
            which = 1
        elif s == "ELIF DEF(_SILVER)" and cur:
            which = 2
        elif s == "ENDC" and cur:
            blocks.append(cur)
            cur = None
        elif cur and slot_re.match(line):
            cur[which].append(i)
    short = []
    for mapname, gold, silver in blocks:
        if len(gold) != len(silver) or len(gold) % n:
            continue
        for t in range(0, len(gold), n):
            g, s = gold[t:t + n], silver[t:t + n]
            sp = lambda idx: slot_re.match(lines[idx]).group(3)
            gs, ss = [sp(i) for i in g], [sp(i) for i in s]
            for mine, theirs, name in ((g, ss, "gold"), (s, gs, "silver")):
                own = [sp(i) for i in mine]
                extra = [x for x in dict.fromkeys(theirs) if x not in own]
                seen, spare = set(), []
                for k, x in enumerate(own):
                    if x in seen:
                        spare.append(k)
                    seen.add(x)
                for k, x in zip(spare, extra):
                    m = slot_re.match(lines[mine[k]])
                    lines[mine[k]] = f"{m.group(1)}{m.group(2)}, {x}{m.group(4)}"
                if len(extra) > len(spare):
                    short.append((mapname, name, extra[len(spare):]))
    return "".join(lines), short


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--base-ref", default="origin/master")
    args = ap.parse_args()
    repo = Path(args.repo)
    for path, kind in FILES.items():
        text, short = merge_versions(git_show(repo, args.base_ref, path), kind)
        (repo / path).write_text(text, encoding="utf-8", newline="\n")
        print(f"{path}: merged Gold/Silver exclusives into spare {kind} slots")
        for mapname, version, left in short:
            print(f"  {mapname} {version}: no spare slot for {', '.join(left)}")


if __name__ == "__main__":
    main()
