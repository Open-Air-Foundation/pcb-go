"""R-V3-15 follow-up: Q6 moves from B.Cu to F.Cu at (115.9, 94.9).

Why: the 3D check against the enclosure model (BT1's GO_v2.12_26.08.17_2.07.step) found a rib under the board
at x 115.5-116.75, y 91.75-95.0, its top 0.25 mm below the bottom copper; Q6 on B.Cu reached 0.29 mm down.
The top side at x 111.8-117.4, y 93.3-96.4 is clear of the holder (it ends at y 93.0) and of parts.

- Removed: the B.Cu CELL- and BAT- islands, the three B.Cu-side CELL- vias, the B.Cu gate track G2-G1-R68.1.
- Q6 on F.Cu, rot -90 like Q3: S1 column (A1/C1) west at x 115.58, S2 column (A2/C2) east at x 116.22,
  gates in the middle row at y 94.9.
- CELL-: an F.Cu island west of S1 with three vias into the In2 CELL- zone, clear of the F.Cu U5-TS diagonal
  (x + y = 208.6) and the B.Cu REG25 riser (x 113.95).
- BAT-: an F.Cu island east of S2 over the existing BAT- vias (117.65, 93.4) and (118.22, 94.01), which reach the
  In1 BAT- strip and NT1.1 on B.Cu.
- Gate: G1-G2 joined, a 0.1 mm lead north between A1 and A2 to a 0.4/0.2 via (as Q3's gates use), B.Cu to R68.1.
  R68 stays on B.Cu (clear of the rib).
"""
import math
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
F, B = pcbnew.F_Cu, pcbnew.B_Cu
TOL = 0.02


def v(x, y):
    return pcbnew.VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6)))


def mm(p):
    return (p.x / 1e6, p.y / 1e6)


def near(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1]) <= TOL


def net(name):
    n = b.FindNet(name)
    if not n:
        raise SystemExit(f"no net {name}")
    return n


q = b.FindFootprintByReference("Q6")
if not q.IsFlipped():
    raise SystemExit("Q6 is already on F.Cu")
GATE = q.FindPadByNumber("B1").GetNetname()

# 1. remove the B.Cu islands, the old CELL- vias and the old gate track
gone = []
for z in list(b.Zones()):
    if z.IsOnLayer(B) and z.GetAssignedPriority() == 30 and z.GetNetname() in ("/CELL-", "/BAT-"):
        gone.append(z)
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA" and t.GetNetname() == "/CELL-" and any(
            near(mm(t.GetPosition()), p) for p in ((115.73, 92.25), (115.6, 94.25), (115.0, 94.35))):
        gone.append(t)
    elif t.GetClass() == "PCB_TRACK" and t.GetNetname() == GATE:
        gone.append(t)
assert len(gone) == 2 + 3 + 2, [(g.GetClass(), g.GetNetname()) for g in gone]
for g in gone:
    b.Delete(g)

# 2. Q6 to F.Cu
q.SetLocked(False)
q.Flip(q.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
q.SetPosition(v(115.9, 94.9))
q.SetOrientationDegrees(-90)
q.SetLocked(True)
q.Reference().SetVisible(False)
pads = {p.GetNumber(): mm(p.GetPosition()) for p in q.Pads()}
assert near(pads["A1"], (115.58, 94.25)) and near(pads["C1"], (115.58, 95.55)), pads
assert near(pads["A2"], (116.22, 94.25)) and near(pads["C2"], (116.22, 95.55)), pads
assert near(pads["B1"], (115.58, 94.9)) and near(pads["B2"], (116.22, 94.9)), pads


def track(netname, layer, width, pts):
    for p0, p1 in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(v(*p0))
        t.SetEnd(v(*p1))
        t.SetWidth(int(round(width * 1e6)))
        t.SetLayer(layer)
        t.SetNet(net(netname))
        t.SetLocked(True)
        b.Add(t)


def via(netname, x, y, d=0.5, drill=0.3):
    t = pcbnew.PCB_VIA(b)
    t.SetViaType(pcbnew.VIATYPE_THROUGH)
    t.SetPosition(v(x, y))
    t.SetWidth(int(round(d * 1e6)))
    t.SetDrill(int(round(drill * 1e6)))
    t.SetNet(net(netname))
    t.SetLocked(True)
    b.Add(t)


def zone(netname, layer, pts, prio=30):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(net(netname))
    z.SetAssignedPriority(prio)
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetMinThickness(int(0.15e6))
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        o.Append(int(round(x * 1e6)), int(round(y * 1e6)))
    b.Add(z)


# 3. gate: G1-G2, north between A1 and A2 to a via, B.Cu to R68.1
track(GATE, F, 0.15, [(115.58, 94.9), (116.22, 94.9)])
track(GATE, F, 0.1, [(115.9, 94.9), (115.9, 93.55)])
via(GATE, 115.9, 93.55, 0.4, 0.2)
track(GATE, B, 0.15, [(115.9, 93.55), (115.65, 93.3), (115.26, 93.3)])
# 4. CELL-: F.Cu island west of S1, three vias into In2
for x, y in ((114.85, 94.55), (114.95, 95.3), (114.55, 95.7)):
    via("/CELL-", x, y)
zone("/CELL-", F, [(114.2, 94.0), (115.62, 94.0), (115.62, 95.95), (114.2, 95.95)])
# 5. BAT-: F.Cu island east of S2 over the existing BAT- vias
zone("/BAT-", F, [(116.2, 93.1), (118.5, 93.1), (118.5, 95.95), (116.2, 95.95)])

# 6. the 'BMS/FG' block label sat over Q6's pads: stand it up, at the house 0.5 mm size, in the 0.9 mm
#    between Q6's outline and the block frame line at x 117.54
lbl = [d for d in b.GetDrawings() if d.GetClass() == "PCB_TEXT" and d.GetText() == "BMS/FG"]
assert len(lbl) == 1
lbl[0].SetTextAngleDegrees(90)
lbl[0].SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
lbl[0].SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
lbl[0].SetTextSize(pcbnew.VECTOR2I(int(0.5e6), int(0.5e6)))
lbl[0].SetTextThickness(int(0.1e6))
lbl[0].SetPosition(v(117.1, 95.45))

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
print("saved")
