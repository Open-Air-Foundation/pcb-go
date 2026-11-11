"""Schematic ECO 2026-11-11 (R-V3-30): `ePaper D/C` and `CHG_INT` change places.
Sam asked for the display's D/C line on a native GPIO: firmware sets it in every display transfer, and on the
expander each change is an I2C write. D/C goes from U17 P3 to U4 IO0. CHG_INT, which had IO0, takes P3, so the
charger's interrupt reaches U4 through EXP_INT like touch and the accelerometer.
Two labels change name. R62 (CHG_INT pull-up), R40 (D/C pull-up), U5 and FPC1 hang on their nets by label and
stay as drawn. The INT LINE note comes from blocks/int_lines.json.
Text-level edit, run once with the schematic closed in KiCad."""
import sys

path = sys.argv[1]
t = open(path).read()
DC, CHG = "ePaper D{slash}C", "CHG_INT"
# old name, new name, where the label sits, the wire from it to the pin
SWAP = [(CHG, DC, "(at 115.57 63.5 0)", "(xy 115.57 63.5) (xy 133.35 63.5)"),             # U4 pin 16, IO0
        (DC, CHG, "(at 247.65 181.61 180)", "(xy 236.22 181.61) (xy 247.65 181.61)")]     # U17 pin 5, P3


def label(name, at):
    return f'\t(label "{name}"\n\t\t{at}\n'


if all(label(new, at) in t for _, new, at, _ in SWAP):
    sys.exit("already applied")
for old, new, at, wire in SWAP:
    if t.count(label(old, at)) != 1 or t.count(wire) != 1:
        sys.exit(f"label {old} {at} or its wire not found")
    t = t.replace(label(old, at), label(new, at))
open(path, "w").write(t)
print("ok")
