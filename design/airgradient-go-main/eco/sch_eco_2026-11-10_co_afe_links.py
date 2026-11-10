"""R-V3-17 links outside the CO SENSOR AFE block (drawn by sch_writer from blocks/co_afe.json):
U11 pins C/S/R get labels CO_CE/CO_S/CO_RE, U11 becomes ES1-CO-100-01 (same footprint, still DNP),
U17 P7 loses its NC flag and drives CO_MENB. Text-level edit, run once with the schematic closed."""
import re
import sys
import uuid

p = sys.argv[1]
t = open(p).read()
if '(label "CO_MENB"\n\t\t(at 247.65 191.77' in t:
    sys.exit("already applied")
U = lambda: str(uuid.uuid4())


def wire(a, b):
    return (f'\t(wire\n\t\t(pts\n\t\t\t(xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})\n\t\t)\n\t\t(stroke\n'
            f'\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)\n')


def label(name, x, y, rot):
    j = "right bottom" if rot == 180 else "left bottom"
    return (f'\t(label "{name}"\n\t\t(at {x} {y} {rot})\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n'
            f'\t\t\t)\n\t\t\t(justify {j})\n\t\t)\n\t\t(uuid "{U()}")\n\t)\n')


# U17 P7: drop the NC flag
m = re.search(r'\n\t\(no_connect\n\t\t\(at 236\.22 191\.77\)\n\t\t\(uuid "[^"]+"\)\n\t\)', t)
if not m:
    sys.exit("U17 P7 NC flag not found")
t = t[:m.start()] + t[m.end():]
new = [wire((236.22, 191.77), (247.65, 191.77)), label("CO_MENB", 247.65, 191.77, 0)]
# U11: R pin 1 (316.23), S pin 2 (320.04), C pin 3 (323.85), pins face left at x 321.31
for name, y in (("CO_RE", 316.23), ("CO_S", 320.04), ("CO_CE", 323.85)):
    new += [wire((321.31, y), (316.23, y)), label(name, 316.23, y, 180)]

# U11 fields
i = t.find('(property "Reference" "U11"')
s = t.rfind('\n\t(symbol\n', 0, i)
e = t.find('\n\t\t(instances', i)
blk = t[s:e]
nb = blk.replace('(property "Value" "PS1-CO-SMOKE-10k"', '(property "Value" "ES1-CO-100-01"')
nb = re.sub(r'\(property "Datasheet" "[^"]*"', '(property "Datasheet" "https://www.ecsense.com/"', nb)
nb = re.sub(r'\(property "Description" "[^"]*"',
            '(property "Description" "EC Sense 3-electrode CO sensor, 0 mV bias, 0-100 ppm; fitted by hand, PS1 footprint (R-V3-17)"', nb)
assert nb != blk and '"ES1-CO-100-01"' in nb
t = t[:s] + nb + t[e:]

k = t.rfind("\n\t(sheet_instances")
t = t[:k] + "\n" + "".join(new) + t[k:]
open(p, "w").write(t)
print("ok")
