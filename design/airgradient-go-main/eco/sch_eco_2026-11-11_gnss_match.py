"""Schematic ECO 2026-11-11 (R-V3-31, R-V3-33), the GPS block and three library slips.
R-V3-31  AE1 matching as the CA-G01 manual draws it (CA-G01_V01 5.3, p4): a T network, 6.2 nH in series at the
         antenna (L4, was R45 0R), 6.2 nH to ground (L5, was C62 not fitted), 100 pF in series at the RF port
         (C86, new). C61, the unfitted capacitor at the antenna, is not in the manual and goes. Values are those
         of the maker's test board. The T node gets the net name GNSS_T.
R-V3-33  AE1's value names the part (CA-G01). U4's symbol has two pins numbered 12 and none numbered 11 (both NC,
         module datasheet Table 3-1): the first becomes 11, here and in the library. L3's value is spelled as
         the part C39846618 is (XRIM201210S100MBCA).
Text-level edit, run once with the schematic closed in KiCad:
  sch_eco_2026-11-11_gnss_match.py SCH libraries/Espressif/Espressif.kicad_sym"""
import re
import sys
import uuid

path, espressif_lib = sys.argv[1], sys.argv[2]
t = open(path).read()
ROOT = "/63bfc1c7-4623-455a-8f83-dca1d491c7db"
STOCK = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/Device.kicad_sym"
if '(reference "C86")' in t:
    sys.exit("already applied")

U = lambda: str(uuid.uuid4())
L_FP, L_MPN, L_LCSC = "Inductor_SMD:L_0402_1005Metric", "LQG15HS6N2S02D", "C133049"
L_URL = "https://www.lcsc.com/product-detail/C133049.html"


def prop(name, val, x, y, rot=0, hide=False):
    h = "\n\t\t\t(hide yes)" if hide else ""
    return (f'\t\t(property "{name}" "{val}"\n\t\t\t(at {x} {y} {rot}){h}\n\t\t\t(show_name no)\n'
            f'\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n'
            f'\t\t\t\t)\n\t\t\t)\n\t\t)\n')


def symbol(lib_id, ref, x, y, rot, props):
    s = (f'\t(symbol\n\t\t(lib_id "{lib_id}")\n\t\t(at {x} {y} {rot})\n\t\t(unit 1)\n\t\t(body_style 1)\n'
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


def sub1(b, old, new):
    if b.count(old) != 1:
        sys.exit(f"expected one match in the symbol, found {b.count(old)}: {old[:50]!r}")
    return b.replace(old, new)


def set_prop(b, name, val):
    n = re.subn(rf'\(property "{name}" "[^"]*"', f'(property "{name}" "{val}"', b, count=1)
    if n[1] != 1:
        sys.exit(f"property {name} not found")
    return n[0]


def drop(start_marker):
    """Remove the top-level item (wire, junction) that holds start_marker."""
    global t
    if t.count(start_marker) != 1:
        sys.exit(f"expected one match, found {t.count(start_marker)}: {start_marker[:60]!r}")
    i = t.index(start_marker)
    s = max(t.rfind('\n\t(wire\n', 0, i + 12), t.rfind('\n\t(junction\n', 0, i + 12))
    e = t.find('\n\t)\n', i) + 3
    t = t[:s] + t[e:]


def to_inductor(b, old_ref, new_ref):
    b = re.subn(r'\(lib_id "Device:[^"]+"\)', '(lib_id "Device:L")', b, count=1)[0]
    b = sub1(b, f'(property "Reference" "{old_ref}"', f'(property "Reference" "{new_ref}"')
    b = sub1(b, f'(reference "{old_ref}")', f'(reference "{new_ref}")')
    for name, val in (("Value", "6.2nH"), ("Footprint", L_FP), ("Datasheet", L_URL), ("Description", L_MPN)):
        b = set_prop(b, name, val)
    return b


# Device:L is not on this sheet yet: copy it from KiCad's own library into lib_symbols
if '(symbol "Device:L"' not in t:
    stock = open(STOCK).read()
    i = stock.index('\n\t(symbol "L"\n') + 1
    e = stock.index('\n\t)\n', i) + 3
    sym = "\n".join("\t" + line for line in stock[i:e].split("\n")).replace('(symbol "L"', '(symbol "Device:L"', 1)
    once('\t\t(symbol "Device:NetTie_2"', sym + '\n\t\t(symbol "Device:NetTie_2"')

# R-V3-31: R45 becomes L4 (series, antenna side)
edit("R45", lambda b: set_prop(to_inductor(b, "R45", "L4"), "LCSC Part", L_LCSC))

# C62 becomes L5 (to ground at the T node); an inductor's pins reach 1.27 mm further than the small capacitor's
def c62_to_l5(b):
    b = to_inductor(b, "C62", "L5")
    b = sub1(b, "(in_bom no)", "(in_bom yes)")
    b = sub1(b, "(dnp yes)", "(dnp no)")
    return sub1(b, '\t\t(property "LCSC" ""', prop("LCSC Part", L_LCSC, 480.06, 35.56, hide=True).rstrip("\n")
                + '\n\t\t(property "LCSC" ""')
edit("C62", c62_to_l5)
once("(xy 480.06 26.67) (xy 480.06 33.02)", "(xy 480.06 26.67) (xy 480.06 31.75)")
once("(xy 480.06 38.1) (xy 480.06 41.91)", "(xy 480.06 39.37) (xy 480.06 41.91)")

# C61 and its ground symbol go
for ref in ("C61", "#PWR0141"):
    s, e = block(ref)
    t = t[:s] + t[e:]
drop("(xy 462.28 33.02) (xy 462.28 26.67)")
drop("(xy 462.28 41.91) (xy 462.28 38.1)")
drop("(junction\n\t\t(at 462.28 26.67)")

# C86 in series between the T node and GNSS_RF
once("(xy 480.06 26.67) (xy 501.65 26.67)", "(xy 480.06 26.67) (xy 486.41 26.67)")
new = [symbol("Device:C", "C86", 490.22, 26.67, 90, [
           prop("Reference", "C86", 490.22, 20.32, 90),
           prop("Value", "100pF/50V", 490.22, 22.86, 90),
           prop("Footprint", "Capacitor_SMD:C_0402_1005Metric", 490.22, 26.67, hide=True),
           prop("Datasheet", "https://www.lcsc.com/product-detail/C1546.html", 490.22, 26.67, hide=True),
           prop("Description", "0402CG101J500NT", 490.22, 26.67, hide=True),
           prop("LCSC Part", "C1546", 490.22, 26.67, hide=True),
           prop("LCSC", "", 490.22, 26.67, hide=True),
       ]),
       wire((494.03, 26.67), (501.65, 26.67)),
       label("GNSS_T", 476.25, 26.67),
       text("AE1 match (R-V3-31): T network of the CA-G01\\nmanual 5.3, values of the maker's test board.\\n"
            "Tune L4, L5, C86 on a complete unit.", 427.99, 46.99)]

# R-V3-33: AE1 names its part
edit("AE1", lambda b: set_prop(set_prop(set_prop(
    b, "Value", "CA-G01"),
    "Datasheet", "http://www.gzhwjdz.com"),
    "Description", "CrossAir CA-G01 GNSS chip antenna 8.0x3.0x1.0 mm (HWJ ELEC)"))

# R-V3-33: L3's value as the part is spelled
edit("L3", lambda b: set_prop(b, "Value", "XRIM201210S100MBCA"))

# R-V3-33: U4 pin 11. The symbol stacks its NC pins 11 to 15 on one spot and numbered two of them 12.
PIN12 = '(number "12"'
def first_12_to_11(s, start):
    end = s.index('(embedded_fonts', start)
    n12, n11 = s.count(PIN12, start, end), s.count('(number "11"', start, end)
    if (n12, n11) == (1, 1):
        return s                                    # this copy has the fix already
    if (n12, n11) != (2, 0):
        sys.exit(f"ESP32-C5-MINI-1: {n12} pins numbered 12 and {n11} numbered 11")
    i = s.index(PIN12, start)
    return s[:i] + '(number "11"' + s[i + len(PIN12):]
t = first_12_to_11(t, t.index('(symbol "Espressif-oaf:ESP32-C5-MINI-1"'))
edit("U4", lambda b: b.replace('(pin "12"', '(pin "11"', 1))
lib = open(espressif_lib).read()
lib_fixed = first_12_to_11(lib, lib.index('(symbol "ESP32-C5-MINI-1"'))

i = t.rfind("\n\t(sheet_instances")
if i < 0:
    sys.exit("sheet_instances not found")
t = t[:i] + "\n" + "".join(new) + t[i:]
if lib_fixed != lib:
    open(espressif_lib, "w").write(lib_fixed)
open(path, "w").write(t)
print("ok")
