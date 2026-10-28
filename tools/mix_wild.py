"""Mix the other region's Pokémon into wild encounter tables.

Kanto maps get Johto-native species (#152-251) and Johto maps get Kanto-native
species (#1-151) in their rarer slots. The common slots, levels, encounter rates
and map list stay as in the original game.

- Grass: slots 4-6 (10%, 5%, 4%) are replaced, the same species in morn/day/nite.
- Water: slot 3 (10%) is replaced.
- Species are drawn from base forms and evolved to fit the slot level:
  level/stat evolutions at their level, item/trade/happiness ones from level 30.
- Grass slots never get a Water-primary species, water slots only get Water types.
- Legendaries, mythicals and Unown are excluded (Unown needs its letter logic).
- Choices are seeded by map and slot, so reruns give the same tables.

Tables are always rebuilt from the original files at --base-ref, so rerunning
does not stack changes.

Usage: python -X utf8 tools/mix_wild.py [--repo DIR] [--base-ref origin/master]
"""

import argparse
import random
import re
import subprocess
from pathlib import Path

EXCLUDED = {
    "ARTICUNO", "ZAPDOS", "MOLTRES", "MEWTWO", "MEW",
    "RAIKOU", "ENTEI", "SUICUNE", "LUGIA", "HO_OH", "CELEBI",
    "UNOWN",
}
NON_LEVEL_EVO_LEVEL = 30
GRASS_SLOTS = (3, 4, 5)
WATER_SLOTS = (2,)
FILES = {
    "data/wild/kanto_grass.asm": ("johto", "grass"),
    "data/wild/kanto_water.asm": ("johto", "water"),
    "data/wild/johto_grass.asm": ("kanto", "grass"),
    "data/wild/johto_water.asm": ("kanto", "water"),
}


def git_show(repo, ref, path):
    return subprocess.run(
        ["git", "-C", str(repo), "show", f"{ref}:{path}"],
        capture_output=True, encoding="utf-8", check=True,
    ).stdout


def load_species(repo):
    text = (repo / "constants/pokemon_constants.asm").read_text(encoding="utf-8")
    names = re.findall(r"^\tconst (\w+)\s*; ([0-9a-f]{2})", text, re.M)
    return [n for n, _ in names][:251]


def load_types(repo):
    types = {}
    for f in (repo / "data/pokemon/base_stats").glob("*.asm"):
        text = f.read_text(encoding="utf-8")
        name = re.search(r"^\tdb (\w+) ; \d+", text, re.M).group(1)
        t = re.search(r"^\tdb (\w+), (\w+) ; type", text, re.M)
        types[name] = (t.group(1), t.group(2))
    return types


def load_evolutions(repo, species):
    text = (repo / "data/pokemon/evos_attacks.asm").read_text(encoding="utf-8")
    blocks = re.split(r"^\w+EvosAttacks:\n", text, flags=re.M)[1:]
    evos = {}
    for name, block in zip(species, blocks):
        evos[name] = []
        for line in block.splitlines():
            m = re.match(r"\tdb (EVOLVE_\w+), (.*)", line)
            if not m:
                continue
            args = [a.strip() for a in m.group(2).split(";")[0].split(",")]
            kind, target = m.group(1), args[-1]
            if kind in ("EVOLVE_LEVEL", "EVOLVE_STAT"):
                need = int(args[0])
            else:
                need = NON_LEVEL_EVO_LEVEL
            evos[name].append((need, target))
    return evos


def evolve(base, level, evos, rng):
    mon = base
    while True:
        options = [t for need, t in evos.get(mon, []) if level >= need]
        if not options:
            return mon
        mon = rng.choice(options)


def build_pools(species, types, evos):
    evolved = {t for lst in evos.values() for _, t in lst}
    bases = [s for s in species if s not in evolved and s not in EXCLUDED]
    region = {s: ("kanto" if i < 151 else "johto") for i, s in enumerate(species)}
    return bases, region


def pick(level, region_name, kind, bases, region, types, evos, rng):
    for _ in range(500):
        mon = evolve(rng.choice(bases), level, evos, rng)
        if region[mon] != region_name or mon in EXCLUDED:
            continue
        is_water = "WATER" in types[mon]
        if kind == "water" and not is_water:
            continue
        if kind == "grass" and types[mon][0] == "WATER":
            continue
        return mon
    raise RuntimeError(f"no {region_name} {kind} species for level {level}")


def mix_file(text, region_name, kind, pool_args):
    slots = GRASS_SLOTS if kind == "grass" else WATER_SLOTS
    out, mapname, idx, chosen = [], None, 0, {}
    for line in text.splitlines(keepends=True):
        m = re.match(r"\tdef_\w+_wildmons (\w+)", line)
        if m:
            mapname, idx, chosen = m.group(1), 0, {}
        m = re.match(r"(\tdb )(\d+), (\w+)(.*)", line, re.S)
        if mapname and m:
            slot = idx % (7 if kind == "grass" else 3)
            idx += 1
            if slot in slots:
                level = int(m.group(2))
                if slot not in chosen:
                    rng = random.Random(f"{mapname}:{slot}")
                    chosen[slot] = pick(level, region_name, kind, *pool_args, rng)
                line = f"{m.group(1)}{m.group(2)}, {chosen[slot]}{m.group(4)}"
        out.append(line)
    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--base-ref", default="origin/master")
    args = ap.parse_args()
    repo = Path(args.repo)

    species = load_species(repo)
    types = load_types(repo)
    evos = load_evolutions(repo, species)
    bases, region = build_pools(species, types, evos)
    for path, (region_name, kind) in FILES.items():
        text = git_show(repo, args.base_ref, path)
        mixed = mix_file(text, region_name, kind, (bases, region, types, evos))
        (repo / path).write_text(mixed, encoding="utf-8", newline="\n")
        print(f"{path}: mixed {region_name} species into {kind} slots")


if __name__ == "__main__":
    main()
