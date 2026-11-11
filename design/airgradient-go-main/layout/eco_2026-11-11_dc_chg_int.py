"""R-V3-30 on the board: `ePaper D/C` and `CHG_INT` change places (schematic: eco/sch_eco_2026-11-11_dc_chg_int.py).
Runs under KiCad's Python after pcb_import, which gives U4 pad 16 (IO0) to `ePaper D/C` and U17 pin 5 (P3) to
`CHG_INT` and leaves the copper on its old nets.

Before: D/C ran from FPC1 down the west side and under U4 to U17 pin 5; CHG_INT came from U5 to a via at
(122.77, 121.70) beside R62 and went on to U4 pad 16. Their new ends lie across each other: on F.Cu the touch line
INT runs between D/C (x 118.37 under U4) and pad 16, on B.Cu BUZZ runs between the CHG_INT via and U17.

- D/C keeps its run from FPC1 to (118.37, 121.50) under U4. A via there, 2.3 mm of B.Cu under INT, a via at
  (120.65, 121.92), and F.Cu into pad 16.
- CHG_INT keeps its run from U5 to the via beside R62, and R62 stays on that via (its link loses the corner the
  stub to pad 16 left behind). It is a through via: from it 5.3 mm of In2 pass under BUZZ and INT to a new via
  at (118.71, 124.62). That via sits on what was the last 9 mm
  of D/C, the F.Cu run round the west of U17 into pin 5, which now belongs to CHG_INT.
- The D/C copper between the two vias on its old run (it passed between U4 pads 12 and 13) and the CHG_INT stub
  into pad 16 go.
- TP footprints that pcb_import re-adds are dropped, as in eco_2026-11-11.py.
"""
import math
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
F, B, IN2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu
TOL = 0.02
DC, CHG = "/ePaper D{slash}C", "/CHG_INT"
W = 0.2


def v(x, y): return pcbnew.VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6)))
def mm(p): return (p.x / 1e6, p.y / 1e6)
def near(p, q, tol=TOL): return math.hypot(p[0] - q[0], p[1] - q[1]) <= tol


def net(name):
    n = b.FindNet(name)
    if not n:
        raise SystemExit(f"no net {name}")
    return n


def pad(ref, num):
    p = b.FindFootprintByReference(ref).FindPadByNumber(num)
    return mm(p.GetPosition()), p.GetNetname()


def polyline(netname, layer, pts):
    """The existing tracks that draw the polyline pts, one per leg."""
    out = []
    for a, z in zip(pts, pts[1:]):
        hit = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetNetname() == netname and t.GetLayer() == layer
               and sorted(near(mm(e), q) for e in (t.GetStart(), t.GetEnd()) for q in (a, z)) == [0, 0, 1, 1]]
        if len(hit) != 1:
            raise SystemExit(f"{netname}: {len(hit)} tracks from {a} to {z}")
        out += hit
    return out


def vias_at(netname, at):
    return [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == netname and near(mm(t.GetPosition()), at)]


def track(netname, layer, pts):
    for a, z in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(v(*a))
        t.SetEnd(v(*z))
        t.SetWidth(int(round(W * 1e6)))
        t.SetLayer(layer)
        t.SetNet(net(netname))
        t.SetLocked(True)
        b.Add(t)


def via(netname, at, d, drill):
    t = pcbnew.PCB_VIA(b)
    t.SetPosition(v(*at))
    t.SetViaType(pcbnew.VIATYPE_THROUGH)
    t.SetWidth(F, int(round(d * 1e6)))
    t.SetDrill(int(round(drill * 1e6)))
    t.SetLayerPair(F, B)
    t.SetNet(net(netname))
    t.SetLocked(True)
    b.Add(t)


PAD16, PIN5 = (121.52, 121.92), (119.7716, 130.84)
DC_UP, DC_EAST = (118.3673, 121.50), (120.65, 121.92)       # D/C: via on the old run, via beside pad 16
CHG_NODE, CHG_TAIL = (122.77, 121.70), (118.7128, 124.62)   # CHG_INT: the via beside R62, via on the old end of D/C

if vias_at(DC, DC_EAST):
    raise SystemExit("already applied (D/C has its via beside U4 pad 16)")
for ref, num, at, name in (("U4", "16", PAD16, DC), ("U17", "5", PIN5, CHG)):
    got = pad(ref, num)
    if not near(got[0], at) or got[1] != name:
        raise SystemExit(f"{ref}.{num} is {got}: run pcb_import with the R-V3-30 schematic first")
assert len(vias_at(CHG, CHG_NODE)) == 1
R62_1 = (123.3016, 122.17)
assert near(pad("R62", "1")[0], R62_1) and pad("R62", "1")[1] == CHG

# 1. test points pcb_import brought back
tps = [f for f in b.GetFootprints() if f.GetReference().startswith("TP")]
for f in tps:
    b.Delete(f)
print("removed", len(tps), "TP footprints")

# 2. removals, and the old end of D/C to CHG_INT
OLD_RUN = [(118.3673, 118.2738), (118.3673, 123.7005), (118.7128, 124.046), (118.7128, 124.9189)]
TAIL = [(118.7128, 124.9189), (117.3336, 126.2981), (117.3336, 130.027), (118.4483, 131.1417), (119.4699, 131.1417), PIN5]
for t in polyline(DC, F, OLD_RUN) + polyline(CHG, F, [CHG_NODE, (122.77, 122.17), (121.77, 122.17), PAD16]) \
        + polyline(CHG, F, [(122.77, 122.17), R62_1]):
    b.Delete(t)
for t in polyline(DC, F, TAIL):
    t.SetNet(net(CHG))

# 3. D/C: under INT on B.Cu, into pad 16
track(DC, F, [OLD_RUN[0], DC_UP])
via(DC, DC_UP, 0.5, 0.3)
track(DC, B, [DC_UP, (DC_EAST[0] - 0.42, DC_UP[1]), DC_EAST])
via(DC, DC_EAST, 0.5, 0.3)
track(DC, F, [DC_EAST, PAD16])

# 4. CHG_INT: under BUZZ and INT on In2, onto the old end of D/C
track(CHG, IN2, [CHG_NODE, (120.10, 124.37), (CHG_TAIL[0] + 0.25, 124.37), CHG_TAIL])
via(CHG, CHG_TAIL, 0.4, 0.2)        # 0.5 does not fit between the +3.3V via at (118.21, 124.24) and the GND via at (119.24, 124.95)
track(CHG, F, [CHG_TAIL, TAIL[0]])
track(CHG, F, [CHG_NODE, (CHG_NODE[0], CHG_NODE[1] + 0.17), (CHG_NODE[0] + 0.30, R62_1[1]), R62_1])     # R62, no 90 degree corner

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
print("saved")
