"""Schematic ECO 2026-11-11 (R-V3-19, 20, 22, 23, 25), the hand-drawn parts of the sheet.
R-V3-19  R35 and R46 not fitted: U19 VIN1 comes off raw VBUS (LM66200 abs max 6 V), U8 runs from SYS only.
R-V3-20  C82 in series with C75 (BAT+ to PGND), so one shorted capacitor cannot short the cell.
R-V3-22  R26, R30 (I2C pull-ups) 10K to 100K.
R-V3-23  R49 (LP5036 IREF) 5.1K to 10K.
R-V3-25  R74, R75 499R in series with UART0: U4 TXD0/RXD0 become nets U0TXD/U0RXD.
The CO AFE change (R-V3-24) is drawn by sch_writer from blocks/co_afe.json.
Text-level edit, run once with the schematic closed in KiCad."""
import re
import sys
import uuid

path = sys.argv[1]
t = open(path).read()
ROOT = "/63bfc1c7-4623-455a-8f83-dca1d491c7db"
if '(reference "C82")' in t:
    sys.exit("already applied")

U = lambda: str(uuid.uuid4())


def prop(name, val, x, y, rot=0, hide=False):
    h = "\n\t\t\t(hide yes)" if hide else ""
    return (f'\t\t(property "{name}" "{val}"\n\t\t\t(at {x} {y} {rot}){h}\n\t\t\t(show_name no)\n'
            f'\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n'
            f'\t\t\t\t)\n\t\t\t)\n\t\t)\n')


def symbol(lib_id, ref, x, y, rot, props, mirror=None):
    m = f"\n\t\t(mirror {mirror})" if mirror else ""
    s = (f'\t(symbol\n\t\t(lib_id "{lib_id}")\n\t\t(at {x} {y} {rot}){m}\n\t\t(unit 1)\n\t\t(body_style 1)\n'
         f'\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n'
         f'\t\t(dnp no)\n\t\t(uuid "{U()}")\n')
    s += "".join(props)
    for p in ("2", "1"):
        s += f'\t\t(pin "{p}"\n\t\t\t(uuid "{U()}")\n\t\t)\n'
    s += (f'\t\t(instances\n\t\t\t(project "airgradient-go-main"\n\t\t\t\t(path "{ROOT}"\n'
          f'\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')
    return s


def wire(a, b):
    return (f'\t(wire\n\t\t(pts\n\t\t\t(xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})\n\t\t)\n\t\t(stroke\n'
            f'\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)\n')


def label(name, x, y):
    return (f'\t(label "{name}"\n\t\t(at {x} {y} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n'
            f'\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "{U()}")\n\t)\n')


def text(s, x, y):
    return (f'\t(text "{s}"\n\t\t(exclude_from_sim no)\n\t\t(at {x} {y} 0)\n\t\t(effects\n\t\t\t(font\n'
            f'\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify left top)\n\t\t)\n\t\t(uuid "{U()}")\n\t)\n')


def block(ref):
    """(start, end) of the symbol whose reference is ref."""
    i = t.find(f'(property "Reference" "{ref}"')
    if i < 0:
        sys.exit(f"{ref} not found")
    s = t.rfind('\n\t(symbol\n', 0, i)
    e = t.find('\n\t)\n', i) + 3
    return s, e


def edit(ref, fn):
    global t
    s, e = block(ref)
    new = fn(t[s:e])
    if new == t[s:e]:
        sys.exit(f"{ref}: nothing changed")
    t = t[:s] + new + t[e:]


def once(old, new):
    global t
    if t.count(old) != 1:
        sys.exit(f"expected one match, found {t.count(old)}: {old[:60]!r}")
    t = t.replace(old, new)


def set_prop(b, name, val):
    n = re.subn(rf'\(property "{name}" "[^"]*"', f'(property "{name}" "{val}"', b, count=1)
    if n[1] != 1:
        sys.exit(f"property {name} not found")
    return n[0]


def shift(b, dx, dy):
    """Move a symbol and its field texts."""
    def f(m):
        x, y = round(float(m.group(1)) + dx, 4), round(float(m.group(2)) + dy, 4)
        return f"(at {x:g} {y:g} {m.group(3)})"
    return re.sub(r'\(at (-?[\d.]+) (-?[\d.]+) (\d+)\)', f, b)


# R-V3-19: R35, R46 not fitted
for ref in ("R35", "R46"):
    edit(ref, lambda b: b.replace("(in_bom yes)", "(in_bom no)", 1).replace("(dnp no)", "(dnp yes)", 1))

# R-V3-22: I2C pull-ups 100K (same part as R61)
for ref in ("R26", "R30"):
    edit(ref, lambda b: set_prop(set_prop(set_prop(set_prop(
        b, "Value", "100K"),
        "Datasheet", "https://lcsc.com/product-detail/Chip-Resistor-Surface-Mount_100KR-1003-1_C60491.html"),
        "Description", "RC0402FR-07100KL"),
        "LCSC Part", "C60491"))
# "100K" is one character longer than "10K" and would reach R30: R26's texts go to its left side
edit("R26", lambda b: b.replace("(at 181.61 35.5599 0)", "(at 176.53 35.5599 0)", 1)
     .replace("(at 181.61 38.0999 0)", "(at 176.53 38.0999 0)", 1).replace("(justify right)", "(justify left)", 2))

# R-V3-23: LP5036 IREF 10K (same part as R36)
edit("R49", lambda b: set_prop(set_prop(set_prop(set_prop(
    b, "Value", "10K"),
    "Datasheet", "https://lcsc.com/product-detail/Others_Huaxin-S-T-MR04X1002FTL_C327797.html"),
    "Description", "MR04X1002FTL"),
    "LCSC Part", "C327797"))

# R-V3-20: C75 up 2.54, C82 beside it, the PGND symbol moves to C82
edit("C75", lambda b: shift(b, 0, -2.54))
edit("#PWR0121", lambda b: shift(b, 12.7, -1.27))
once("(xy 49.53 275.59) (xy 49.53 279.4)", "(xy 49.53 275.59) (xy 49.53 276.86)")
once("(xy 49.53 287.02) (xy 49.53 288.29)", "(xy 49.53 284.48) (xy 49.53 285.75)")
C100072 = ("https://lcsc.com/product-detail/Multilayer-Ceramic-Capacitors-MLCC-SMD-SMT_SAMSUNG_"
           "CL05A104KA5NNNC_100nF-104-10-25V_C100072.html")
new = [wire((49.53, 285.75), (52.07, 285.75)),
       symbol("Device:C", "C82", 55.88, 285.75, 90, [
           prop("Reference", "C82", 55.88, 289.56, 90),
           prop("Value", "0.1uF/25V", 55.88, 292.1, 90),
           prop("Footprint", "Capacitor_SMD:C_0402_1005Metric", 55.88, 285.75, hide=True),
           prop("Datasheet", C100072, 55.88, 285.75, hide=True),
           prop("Description", "CL05A104KA5NNNC", 55.88, 285.75, hide=True),
           prop("LCSC Part", "C100072", 55.88, 285.75, hide=True),
           prop("LCSC", "", 55.88, 285.75, hide=True),
       ]),
       wire((59.69, 285.75), (62.23, 285.75)), wire((62.23, 285.75), (62.23, 287.02))]

# R-V3-25: UART0 series resistors, drawn like the SPI series group
once('(label "MCU_TX"\n\t\t(at 172.72 58.42 180)', '(label "U0TXD"\n\t\t(at 172.72 58.42 180)')
once('(label "MCU_RX"\n\t\t(at 172.72 60.96 180)', '(label "U0RXD"\n\t\t(at 172.72 60.96 180)')
for ref, y, left, right in (("R74", 60.96, "U0TXD", "MCU_TX"), ("R75", 68.58, "MCU_RX", "U0RXD")):
    new += [label(left, 226.06, y), wire((226.06, y), (236.22, y)),
            symbol("Device:R", ref, 240.03, y, 90, [
                prop("Reference", ref, 240.03, round(y + 2.794, 3), 90),
                prop("Value", "499R", 240.03, round(y + 5.334, 3), 90),
                prop("Footprint", "Resistor_SMD:R_0402_1005Metric", 240.03, y, hide=True),
                prop("Datasheet", "https://www.lcsc.com/product-detail/C2960788.html", 240.03, y, hide=True),
                prop("Description", "FRC0402F4990TS", 240.03, y, hide=True),
                prop("LCSC Part", "C2960788", 240.03, y, hide=True),
                prop("LCSC", "", 240.03, y, hide=True),
            ], mirror="x"),
            wire((243.84, y), (247.65, y)), label(right, 247.65, y)]
new.append(text("R74/R75 499R (R-V3-25):\\nEspressif asks it on U0TXD;\\nR75 lets a tool drive RX0.", 226.06, 50.8))
new.append(text("R35, R46 DNP (R-V3-19):\\nU19 VIN1 off raw VBUS\\n(6 V abs max), SYS only", 233.68, 315.595))

i = t.rfind("\n\t(sheet_instances")
if i < 0:
    sys.exit("sheet_instances not found")
t = t[:i] + "\n" + "".join(new) + t[i:]
open(path, "w").write(t)
print("ok")
