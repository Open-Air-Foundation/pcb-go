"""Mark on the schematic what the 2026-11-10 ECO changed (R-V3-15, R-V3-16): magenta dashed boxes,
a tag per box and a change list. Same style as mark_v2.py, its own UUID prefix.

  mark_eco_2026-11-10.py SCH            replace the marks with the set below
  mark_eco_2026-11-10.py SCH --remove   delete every mark
"""
import re
import sys

PREFIX = 'd317b000'
COLOR = '(color 255 0 255 1)'

# (x0, y0, x1, y1) in sheet mm, the tag, and its top-left corner (None: just above the box's top-left corner).
# Boxes are dashed polylines, not rectangles, so the readability lint does not take them for block frames.
BOXES = [
    ((179.6, 247.6, 254.0, 286.4), 'R-V3-15', None),             # Q6, R68, note
    ((29.0, 279.9, 37.0, 284.2), 'R-V3-15', (29.0, 284.9)),      # BT1.2 -> CELL- (tag below: BT1 value above)
    ((76.6, 209.8, 80.0, 219.6), 'R-V3-15', (67.3, 206.4)),     # BAT+_RS label on R8.2 / Q3 S1 (tag left of C73)
    ((60.6, 42.9, 80.4, 52.6), 'R-V3-16', None),                 # F1
    ((112.5, 305.8, 121.2, 315.5), 'R-V3-16', None),             # R21
    ((129.8, 341.9, 177.0, 355.0), 'R-V3-16', (150.0, 339.4)),             # charger-input note
    ((262.0, 336.5, 382.5, 406.6), 'R-V3-17 (new block)', (262.6, 340.2)),  # CO SENSOR AFE block, tag under its title
    ((307.5, 313.6, 333.5, 327.0), 'R-V3-17', None),             # U11 ES1-CO-100-01 + labels
    ((236.6, 190.0, 258.5, 193.0), 'R-V3-17', (236.6, 193.6)),   # U17 P7 -> CO_MENB
]
LIST_BOX = (430.0, 306.5, 578.0, 337.5)
LIST_TITLE = ('ECO 2026-11-10: R-V3-15 REVERSE BATTERY, R-V3-16 2 A CHARGE, R-V3-17 CO AFE', 433.0, 308.6)
LIST_AT = (433.0, 313.4)
LIST = [
    'R-V3-15  Q6 CSD83325L (C2860700) added in the BT1- lead, both halves in series; BT1.2 net BAT- to CELL-.',
    '              R68 10K (C327797): Q6 gates to BAT+_RS. Cell in backwards: Q6 off, U3 and the rest never see it.',
    '              BAT+_RS: new name of the R8.2 / Q3 S1 node (was Net-(C73-Pad2)), no connection change.',
    'R-V3-16  F1 BSMD1206-075-6V to BSMD1206-260-6V (C976306): 2.6 A hold, a 2 A charge no longer trips it.',
    '              R21 2.49K to 1.1K (C2845203): ILIM 2.05/2.27/2.50 A, so 2 A holds even with EN_EXTILIM = 1.',
    'PCB only: In2 battery-return zone BAT- to CELL-; Q6 on F.Cu (a B.Cu spot hit an enclosure rib), R68 on B.Cu;',
    '              U5.18 VBUS lead 0.2 to 0.35 mm;',
    '              dead BAT- via (109.7, 95.85) removed. Details: design/requirements.md R-V3-15, R-V3-16.',
    'R-V3-17  New CO SENSOR AFE block: U22 LMP91002 + U23 ADS1115 (0x49) on +3.3V; U11 = ES1-CO-100-01 (DNP);',
    '              U17 P7 drives CO_MENB (U22 at 0x48 only while low). PCB: U22 over the sensor, U23 west of U11 pins.',
]


def block_end(s, i):
    d, q, j = 0, False, i
    while True:
        c = s[j]
        if q:
            if c == '\\':
                j += 1
            elif c == '"':
                q = False
        elif c == '"':
            q = True
        elif c == '(':
            d += 1
        elif c == ')':
            d -= 1
            if d == 0:
                return j + 1
        j += 1


def remove(s):
    gone = 0
    for m in reversed(list(re.finditer(r'\(uuid "' + PREFIX, s))):
        i = max(s.rfind('(rectangle', 0, m.start()), s.rfind('(polyline', 0, m.start()), s.rfind('(text "', 0, m.start()))
        e = block_end(s, i)
        if not (i < m.start() < e):
            raise SystemExit(f'mark at {m.start()} is not inside a rectangle, polyline or text')
        start = s.rfind('\n', 0, i) + 1
        s = s[:start] + s[e:].lstrip('\n')
        gone += 1
    return s, gone


def uid(n):
    return f'{PREFIX}-{n >> 32:04x}-4000-8000-{n & 0xffffffffffff:012x}'


def box(b, n, width=0.254):
    x0, y0, x1, y1 = b
    pts = ' '.join(f'(xy {x} {y})' for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)))
    return (f'\t(polyline\n\t\t(pts\n\t\t\t{pts}\n\t\t)\n'
            f'\t\t(stroke\n\t\t\t(width {width})\n\t\t\t(type dash)\n\t\t\t{COLOR}\n\t\t)\n'
            f'\t\t(fill\n\t\t\t(type none)\n\t\t)\n\t\t(uuid "{uid(n)}")\n\t)\n')


def text(t, x, y, n, size=1.27, bold=True):
    b = '\t\t\t\t(thickness 0.254)\n\t\t\t\t(bold yes)\n' if bold else ''
    t = t.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    return (f'\t(text "{t}"\n\t\t(exclude_from_sim no)\n\t\t(at {x} {y} 0)\n\t\t(effects\n\t\t\t(font\n'
            f'\t\t\t\t(size {size} {size})\n{b}\t\t\t\t{COLOR}\n\t\t\t)\n\t\t\t(justify left top)\n\t\t)\n'
            f'\t\t(uuid "{uid(n)}")\n\t)\n')


def main():
    path = sys.argv[1]
    s, gone = remove(open(path).read())
    new = ''
    if '--remove' not in sys.argv:
        n = 0
        for b, tag, at in BOXES:
            n += 1
            new += box(b, n)
            n += 1
            x, y = at or (b[0], round(b[1] - 1.9, 2))
            new += text(tag, x, y, n)
        n += 1
        new += box(LIST_BOX, n, 0.3)
        n += 1
        new += text(LIST_TITLE[0], LIST_TITLE[1], LIST_TITLE[2], n, size=2.0)
        n += 1
        new += text('\n'.join(LIST), LIST_AT[0], LIST_AT[1], n, bold=False)
        at = s.index('\t(sheet_instances')
        s = s[:at] + new + s[at:]
    open(path, 'w').write(s)
    print(f'removed {gone}, added {new.count("(uuid ")}')


main()
