"""Schematic ECO 2026-11-10 (R-V3-15): reverse-battery FET Q6 + gate R68 in the BT1- lead.
BT1.2 leaves BAT- for a new net CELL-; Q6 (CSD83325L, same part as Q3) joins CELL- to BAT-,
gates through R68 10K to BAT+. Text-level edit, run once with the schematic closed in KiCad."""
import re
import sys
import uuid

path = sys.argv[1]
t = open(path).read()
ROOT = "/63bfc1c7-4623-455a-8f83-dca1d491c7db"
if '(reference "Q6")' in t:
    sys.exit("Q6 already present")

U = lambda: str(uuid.uuid4())


def prop(name, val, x, y, hide=False, justify=None):
    h = "\n\t\t\t(hide yes)" if hide else ""
    j = f"\n\t\t\t\t(justify {justify})" if justify else ""
    return (f'\t\t(property "{name}" "{val}"\n\t\t\t(at {x} {y} 0){h}\n\t\t\t(show_name no)\n'
            f'\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n'
            f'\t\t\t\t){j}\n\t\t\t)\n\t\t)\n')


def symbol(lib_id, ref, x, y, rot, props, pins):
    s = (f'\t(symbol\n\t\t(lib_id "{lib_id}")\n\t\t(at {x} {y} {rot})\n\t\t(unit 1)\n\t\t(body_style 1)\n'
         f'\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n'
         f'\t\t(dnp no)\n\t\t(fields_autoplaced yes)\n\t\t(uuid "{U()}")\n')
    s += "".join(props)
    for p in pins:
        s += f'\t\t(pin "{p}"\n\t\t\t(uuid "{U()}")\n\t\t)\n'
    s += (f'\t\t(instances\n\t\t\t(project "airgradient-go-main"\n\t\t\t\t(path "{ROOT}"\n'
          f'\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')
    return s


def wire(a, b):
    return (f'\t(wire\n\t\t(pts\n\t\t\t(xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})\n\t\t)\n\t\t(stroke\n'
            f'\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)\n')


def label(name, x, y, rot):
    j = "right bottom" if rot == 180 else "left bottom"
    return (f'\t(label "{name}"\n\t\t(at {x} {y} {rot})\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n'
            f'\t\t\t)\n\t\t\t(justify {j})\n\t\t)\n\t\t(uuid "{U()}")\n\t)\n')


def junction(x, y):
    return (f'\t(junction\n\t\t(at {x} {y})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{U()}")\n\t)\n')


def text(s, x, y):
    return (f'\t(text "{s}"\n\t\t(exclude_from_sim no)\n\t\t(at {x} {y} 0)\n\t\t(effects\n\t\t\t(font\n'
            f'\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "{U()}")\n\t)\n')


# 1. cut BT1.2 off BAT-: drop the wire BT1.2 -> BAT- label corner
old = re.search(r'\n\t\(wire\n\t\t\(pts\n\t\t\t\(xy 35\.56 280\.67\) \(xy 45\.72 280\.67\)\n\t\t\).*?\n\t\)', t, re.S)
if not old:
    sys.exit("BT1.2 wire not found")
t = t[:old.start()] + t[old.end():]

new = []
# BT1.2 -> CELL-
new += [wire((35.56, 280.67), (35.56, 283.21)), label("CELL-", 35.56, 283.21, 180)]

# Q6 at (213.36, 270.51): S1 A1/C1 left, S2 C2/A2 right, G1 B1 / G2 B2 below
qx, qy = 213.36, 270.51
new.append(symbol("easyeda2kicad-oaf:CSD83325L", "Q6", qx, qy, 0, [
    prop("Reference", "Q6", round(qx - 1.27, 2), round(qy - 10.16, 2)),
    prop("Value", "CSD83325L", round(qx - 1.27, 2), round(qy - 7.62, 2)),
    prop("Footprint", "easyeda2kicad-oaf:PICOSTAR-6_L2.2-W1.1-R2-C3-P0.65-BL", qx, round(qy + 15.24, 2), hide=True),
    prop("Datasheet", "", qx, qy, hide=True),
    prop("Description", "Reverse-battery FET, both halves in series (R-V3-15)", qx, qy, hide=True),
    prop("LCSC Part", "C2860700", qx, round(qy + 17.78, 2), hide=True),
    prop("LCSC", "", qx, qy, hide=True),
], ["C2", "C1", "B2", "B1", "A2", "A1"]))
new += [wire((200.66, 270.51), (200.66, 273.05)), wire((193.04, 270.51), (200.66, 270.51)),
        label("CELL-", 193.04, 270.51, 180),
        wire((223.52, 270.51), (223.52, 273.05)), wire((223.52, 270.51), (231.14, 270.51)),
        label("BAT-", 231.14, 270.51, 0),
        wire((208.28, 278.13), (208.28, 283.21)), wire((215.9, 278.13), (215.9, 283.21)),
        wire((208.28, 283.21), (215.9, 283.21)), wire((215.9, 283.21), (219.71, 283.21)),
        junction(215.9, 283.21)]
# R68 10K gate resistor, horizontal: pin1 (219.71, 283.21), pin2 (227.33, 283.21)
new.append(symbol("Device:R", "R68", 223.52, 283.21, 90, [
    prop("Reference", "R68", 223.52, 280.67),
    prop("Value", "10K", 223.52, 285.75),
    prop("Footprint", "Resistor_SMD:R_0402_1005Metric", 223.52, 283.21, hide=True),
    prop("Datasheet", "https://lcsc.com/product-detail/Others_Huaxin-S-T-MR04X1002FTL_C327797.html", 223.52, 283.21, hide=True),
    prop("Description", "", 223.52, 283.21, hide=True),
    prop("LCSC Part", "C327797", 223.52, 283.21, hide=True),
    prop("LCSC", "", 223.52, 283.21, hide=True),
], ["2", "1"]))
new += [wire((227.33, 283.21), (231.14, 283.21)), label("BAT+", 231.14, 283.21, 0)]
new.append(text("Reverse battery (R-V3-15): Q6 sits in the BT1- lead, gates on BAT+.\\n"
                "Cell in backwards: gates at the cell's - end, Q6 off, both body diodes block.\\n"
                "U3 sits across the cell and Q3 can conduct reversed, so neither protects.\\n"
                "Drop: 10.9 mohm typ at VGS 3.8 V (SLPS494C), 22 mV at 2 A.", 182.88, 289.56))

i = t.rfind("\n\t(sheet_instances")
if i < 0:
    i = t.rstrip().rfind(")")
t = t[:i] + "\n" + "".join(new) + t[i:]
open(path, "w").write(t)
print("ok")
