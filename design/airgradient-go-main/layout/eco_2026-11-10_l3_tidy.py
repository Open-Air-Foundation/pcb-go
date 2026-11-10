"""Tidy round L3 after U18 moved west (eco_2026-11-10_u18_west.py).

L3 now sits in 2.06 mm between C45 / D5 and U18's west pads, and its silk outline (2.04 mm wide, 0.25 mm lines) lay
over the pads on both sides, with Q5's outline and the block divider on U18's pads as well.
- C45 0.25 mm west (0.68 mm to the board edge): L3 to C45 goes from 0.27 to 0.52 mm. L3 to D5 0.36, to U18 0.41 mm.
- L3 silk: only a short top line is kept, the rest moves to F.Fab. Q5 silk: the east side, which lay on U18's pads
  6 and 7, moves to F.Fab.
- Labels: C45 follows its part, L3 moves left of the divider, R43 moves below its part (it lay on Q5's pads).
- C65's label (B.Silkscreen) is hidden.
- Block divider at x 140.4: opened from y 67.15 to 68.55, where Q5's pad 2 reaches it.
"""
import math
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
SILK = pcbnew.F_SilkS


def v(x, y):
    return pcbnew.VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6)))


def mm(p):
    return (p.x / 1e6, p.y / 1e6)


def near(p, q, tol=0.03):
    return math.hypot(p[0] - q[0], p[1] - q[1]) <= tol


c45 = b.FindFootprintByReference("C45")
if not near(mm(c45.GetPosition()), (138.232, 62.48)):
    raise SystemExit("C45 is not at its old position: already applied?")
c45.SetPosition(v(137.982, 62.48))
c45.Reference().SetPosition(v(138.112, 61.17))

l3 = b.FindFootprintByReference("L3")
assert near(mm(l3.GetPosition()), (139.502, 63.61)), mm(l3.GetPosition())
l3.Reference().SetPosition(v(139.5, 61.16))
kept = 0
for g in list(l3.GraphicalItems()):
    if g.GetLayer() != SILK or g.GetClass() != "PCB_SHAPE":
        continue
    a, e = mm(g.GetStart()), mm(g.GetEnd())
    if near(a, (140.262, 61.67)) and near(e, (138.862, 61.67)):
        g.SetStart(v(140.05, 61.67))
        g.SetEnd(v(138.95, 61.67))
        g.SetWidth(int(0.15e6))
        kept += 1
    else:
        g.SetLayer(pcbnew.F_Fab)             # off the silk, kept on F.Fab (deleting a footprint's graphic crashes pcbnew)
assert kept == 1, kept

q5 = b.FindFootprintByReference("Q5")
gone = 0
for g in list(q5.GraphicalItems()):
    if g.GetLayer() == SILK and g.GetClass() == "PCB_SHAPE":
        a, e = mm(g.GetStart()), mm(g.GetEnd())
        if near(a, (140.622, 67.66)) and near(e, (140.622, 66.26)):
            g.SetLayer(pcbnew.F_Fab)
            gone += 1
        elif near(a, (140.622, 66.26)) and near(e, (139.902, 66.26)):
            g.SetStart(v(140.2, 66.26))
            gone += 1
assert gone == 2, gone

div = [d for d in b.GetDrawings() if d.GetClass() == "PCB_SHAPE" and d.GetLayer() == SILK
       and near(mm(d.GetStart()), (140.4, 71.519)) and near(mm(d.GetEnd()), (140.4, 59.024))]
assert len(div) == 1, len(div)
low = div[0].Duplicate()
div[0].SetStart(v(140.4, 67.15))            # upper piece: 59.024 .. 67.15
low.SetEnd(v(140.4, 68.55))                 # lower piece: 68.55 .. 71.519
b.Add(low)

r43 = b.FindFootprintByReference("R43").Reference()               # its label lay on Q5's pads
r43.SetPosition(v(139.1, 70.85))
r43.SetTextAngleDegrees(0)
b.FindFootprintByReference("C65").Reference().SetVisible(False)      # on B.Cu now, its label lay on C65's own pad

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
print("saved")
