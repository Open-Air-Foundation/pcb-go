"""Schematic ECO 2026-11-11 (R-V3-27): R18 and R19, the BQ25628 TS divider, get part numbers that match their values.
Since 9af7b11 (v2.1) the values are 5.23k / 30.1k for NTC1 = NCP15XH103F03RC, but the LCSC fields still named the
v2.0 pair (C327340 = 4.12k, C851231 = 17.4k), and the assembly BOM is built from the LCSC field.
Text-level edit, run once with the schematic closed in KiCad."""
import re
import sys

path = sys.argv[1]
t = open(path).read()

PARTS = {
    "R18": ("5.23k", "C327340", "C2933105", "FRC0402F5231TS"),     # FOJAN 5.23 kΩ 1 %
    "R19": ("30.1k", "C851231", "C29402", "0402WGF3012TCE"),       # UNI-ROYAL 30.1 kΩ 1 %
}


def block(ref):
    """(start, end) of the symbol whose reference is ref."""
    i = t.find(f'(property "Reference" "{ref}"')
    if i < 0:
        sys.exit(f"{ref} not found")
    return t.rfind('\n\t(symbol\n', 0, i), t.find('\n\t)\n', i) + 3


def prop(b, name):
    m = re.search(rf'\(property "{name}" "([^"]*)"', b)
    if not m:
        sys.exit(f"property {name} not found")
    return m.group(1)


def set_prop(b, name, val):
    prop(b, name)
    return re.sub(rf'\(property "{name}" "[^"]*"', f'(property "{name}" "{val}"', b, count=1)


if all(prop(t[slice(*block(r))], "LCSC Part") == new for r, (_, _, new, _) in PARTS.items()):
    sys.exit("already applied")
for ref, (value, old, new, mpn) in PARTS.items():
    s, e = block(ref)
    b = t[s:e]
    if prop(b, "Value") != value or prop(b, "LCSC Part") != old:
        sys.exit(f"{ref}: expected {value} with {old}, found {prop(b, 'Value')} with {prop(b, 'LCSC Part')}")
    b = set_prop(b, "LCSC Part", new)
    b = set_prop(b, "Datasheet", f"https://www.lcsc.com/product-detail/{new}.html")
    b = set_prop(b, "Description", mpn)
    t = t[:s] + b + t[e:]
open(path, "w").write(t)
print("ok")
