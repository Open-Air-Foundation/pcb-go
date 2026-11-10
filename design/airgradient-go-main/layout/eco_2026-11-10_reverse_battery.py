"""R-V3-15 reverse-battery FET. Runs under KiCad's Python after pcb_import put Q6/R68 on the board.

- pcb_import re-adds the TP footprints the board never carried: drop every TP*.
- Net-(C73-Pad2) (R8.2 / Q3 S1) is named BAT+_RS in the schematic now: pcb_import moved the
  pads, this moves the tracks, vias and zones.
- The In2 (PWR) zone from BT1.2 to NT1 was BAT-; it becomes CELL- (BT1.2 is CELL- now).
- Q6 on B.Cu west of NT1, between the battery cut-out (edge y 91.79, notch to 92.74 at
  x 111.7-115.27) and the SPS30 (y 94.96). S1 column (C1/A1) west on a CELL- island with
  three vias into the In2 CELL- zone (0.2 mm off the notch edge x 115.27); S2 column (C2/A2) east on a BAT- island over NT1.1
  and its three vias. Vias keep clear of the F.Cu U5-TS diagonal (x + y = 208.6).
- Gates G1-G2 joined, west to R68 10K, R68.2 to a via, then F.Cu south-west to the
  BAT+_RS via (111.51, 96.56) beside R8.2.
- The BAT- via (109.7, 95.85) and its B.Cu stub only met the old In2 zone: removed.
"""
import math
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
F, B = pcbnew.F_Cu, pcbnew.B_Cu
PWR = b.GetLayerID("PWR")
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


if any(z.GetNetname() == "/CELL-" for z in b.Zones()):
    raise SystemExit("already applied")

# 1. TP footprints re-added by pcb_import
tps = [f for f in b.GetFootprints() if f.GetReference().startswith("TP")]
for f in tps:
    b.Delete(f)
print("removed", len(tps), "TP footprints")

# 2. Net-(C73-Pad2) -> /BAT+_RS on tracks, vias and zones (pads already moved by pcb_import)
old = b.FindNet("Net-(C73-Pad2)")
rs = net("/BAT+_RS")
moved = 0
if old:
    for t in b.GetTracks():
        if t.GetNetCode() == old.GetNetCode():
            t.SetNet(rs)
            moved += 1
    for z in b.Zones():
        if z.GetNetCode() == old.GetNetCode():
            z.SetNet(rs)
            moved += 1
print("BAT+_RS items moved", moved)

# 3. In2 battery-return zone -> CELL-
pz = [z for z in b.Zones() if z.GetNetname() == "/BAT-" and z.IsOnLayer(PWR)]
assert len(pz) == 1, pz
pz[0].SetNet(net("/CELL-"))

# 4. dead BAT- via + stub that only met the old In2 zone
dead = []
for t in b.GetTracks():
    if t.GetNetname() != "/BAT-":
        continue
    if t.GetClass() == "PCB_VIA" and near(mm(t.GetPosition()), (109.7, 95.85)):
        dead.append(t)
    elif t.GetClass() == "PCB_TRACK" and t.GetLayer() == B:
        ends = {tuple(round(c, 2) for c in mm(t.GetStart())), tuple(round(c, 2) for c in mm(t.GetEnd()))}
        if ends & {(109.1, 99.76), (109.7, 95.85)}:
            dead.append(t)
assert len(dead) == 3, [(d.GetClass(), mm(d.GetStart())) for d in dead]
for t in dead:
    b.Delete(t)

# 5. place Q6 and R68 on B.Cu
q = b.FindFootprintByReference("Q6")
r = b.FindFootprintByReference("R68")
for fp, x, y, ang in ((q, 116.5, 93.3, 90), (r, 114.75, 93.3, 180)):
    fp.SetPosition(v(x, y))
    if not fp.IsFlipped():
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    fp.SetOrientationDegrees(ang)
    fp.SetLocked(True)
# both sit under the SPS30: no room or view for silk, references stay on Fab only
for fp in (q, r):
    fp.Reference().SetVisible(False)
pads = {p.GetNumber(): mm(p.GetPosition()) for p in q.Pads()}
assert near(pads["C1"], (116.18, 92.65)) and near(pads["A1"], (116.18, 93.95)), pads
assert near(pads["C2"], (116.82, 92.65)) and near(pads["A2"], (116.82, 93.95)), pads
assert near(pads["B1"], (116.18, 93.3)) and near(pads["B2"], (116.82, 93.3)), pads
rp = {p.GetNumber(): (mm(p.GetPosition()), p.GetNetname()) for p in r.Pads()}
assert near(rp["1"][0], (115.26, 93.3)) and near(rp["2"][0], (114.24, 93.3)), rp
assert rp["2"][1] == "/BAT+_RS", rp
GATE = q.FindPadByNumber("B1").GetNetname()
assert rp["1"][1] == GATE, rp


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


def via(netname, x, y):
    t = pcbnew.PCB_VIA(b)
    t.SetViaType(pcbnew.VIATYPE_THROUGH)
    t.SetPosition(v(x, y))
    t.SetWidth(int(0.5e6))
    t.SetDrill(int(0.3e6))
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


# 6. gate: G2-G1, west to R68.1
track(GATE, B, 0.15, [(116.82, 93.3), (116.18, 93.3), (115.26, 93.3)])
# 7. BAT+_RS lead: R68.2 -> via -> F.Cu south-west to the via beside R8.2
track("/BAT+_RS", B, 0.15, [(114.24, 93.3), (113.55, 93.3)])
via("/BAT+_RS", 113.55, 93.3)
track("/BAT+_RS", F, 0.15, [(113.55, 93.3), (111.6, 95.25), (111.6, 96.3), (111.51, 96.56)])
# 8. CELL- island west of S1, three vias into the In2 CELL- zone
for x, y in ((115.73, 92.25), (115.6, 94.25), (115.0, 94.35)):
    via("/CELL-", x, y)
zone("/CELL-", B, [(114.85, 91.9), (116.25, 91.9), (116.25, 94.65), (114.85, 94.65)])
# 9. BAT- island east of S2, over NT1.1 and its three vias
zone("/BAT-", B, [(116.6, 92.0), (118.6, 92.0), (118.6, 94.45), (116.6, 94.45)])

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
print("saved")
