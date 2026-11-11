"""R-V3-34 on the board: C86 out from under the battery holder's foot. Runs under KiCad's Python.

The holder (BT1's model, GO_v2.12_26.08.17_2.07.step) has a foot on the front of the board round its screw:
a slot shape, 2.5 mm round the line (154.952, 71.09) to (155.952, 71.09), 1.0 mm thick. The model has its
underside 0.24 mm below the board's front face: it bears on the board (R-V3-18 moved U18 away from it).
R-V3-31 laid C86 east-west at (153.29, 69.00), on the last stretch into U18 pin 11, with its east end 0.32 mm
under that foot.

C86 now stands north-south at (152.85, 68.12), between U18 and L5, pad 1 up: the part itself takes the step
from the feed's row down to pin 11's row.
- GNSS_T leaves L5 pad 1 westward, steps 0.25 mm north and enters C86 pad 1. The quarter circle into the old
  place goes.
- GNSS_RF runs from C86 pad 2 down to pin 11's centre line and west into the pad.
- The ground via at (153.41, 68.24) stood where C86's pads are now. It moves to (153.55, 68.45), still on the
  B.Cu ground strip between LED_4_B and PRTRG.
- C86's label stands north of the part.
The board is not saved while a pad on the front is nearer the foot than KEEP.
"""
import math
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
F, B = pcbnew.F_Cu, pcbnew.B_Cu
TOL = 0.02
TEE, RF = "/GNSS_T", "/GNSS_RF"
FOOT = ((154.952, 71.09), (155.952, 71.09))     # axis of the foot's outline north of the screw
FOOT_R = 2.5
KEEP = 0.3                                      # U18 pad 10 has 0.45 mm (R-V3-18)
C86_AT, C86_ROT = (152.85, 68.12), 270
LABEL = (152.75, 66.42)
VIA_OLD, VIA_NEW = (153.4116, 68.24), (153.55, 68.45)


def v(x, y): return pcbnew.VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6)))
def mm(p): return (p.x / 1e6, p.y / 1e6)
def near(p, q, tol=TOL): return math.hypot(p[0] - q[0], p[1] - q[1]) <= tol


def net(name):
    n = b.FindNet(name)
    if not n:
        raise SystemExit(f"no net {name}")
    return n


def fp(ref):
    f = b.FindFootprintByReference(ref)
    if not f:
        raise SystemExit(f"no footprint {ref}")
    return f


def pad(ref, num):
    p = fp(ref).FindPadByNumber(num)
    return mm(p.GetPosition()), p.GetNetname()


def polyline(netname, layer, pts):
    """The existing tracks that draw the polyline pts, one per leg."""
    out = []
    for a, z in zip(pts, pts[1:]):
        hit = [t for t in b.GetTracks() if t.GetClass() in ("PCB_TRACK", "PCB_ARC") and t.GetNetname() == netname
               and t.GetLayer() == layer
               and sorted(near(mm(e), q) for e in (t.GetStart(), t.GetEnd()) for q in (a, z)) == [0, 0, 1, 1]]
        if len(hit) != 1:
            raise SystemExit(f"{netname}: {len(hit)} tracks from {a} to {z}")
        out += hit
    return out


def drop(netname, layer, pts):
    for t in polyline(netname, layer, pts):
        b.Delete(t)


def via_at(netname, at):
    hit = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == netname and near(mm(t.GetPosition()), at)]
    if len(hit) != 1:
        raise SystemExit(f"{netname}: {len(hit)} vias at {at}")
    return hit[0]


def track(netname, layer, width, pts):
    for a, z in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(v(*a))
        t.SetEnd(v(*z))
        t.SetWidth(int(round(width * 1e6)))
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


def seg_d(p, a, z):
    dx, dy = z[0] - a[0], z[1] - a[1]
    if dx == dy == 0:
        return math.hypot(p[0] - a[0], p[1] - a[1])
    t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


def ring_d(ring, a, z):
    """Distance between a closed polygon and the segment a-z (they do not cross here)."""
    return min(min(seg_d(p, a, z) for p in ring),
               min(seg_d(q, ring[i], ring[(i + 1) % len(ring)]) for q in (a, z) for i in range(len(ring))))


c86 = fp("C86")
if not near(mm(c86.GetPosition()), (153.29, 69.0025)):
    raise SystemExit("already applied (C86 is not lying at its R-V3-31 place)")
for ref, num, name in (("L5", "1", TEE), ("C86", "1", TEE), ("C86", "2", RF), ("U18", "11", RF)):
    if pad(ref, num)[1] != name:
        raise SystemExit(f"{ref}.{num} is on {pad(ref, num)[1]!r}")
l51, u1811 = pad("L5", "1")[0], pad("U18", "11")[0]
assert near(l51, (154.1716, 67.89)) and near(u1811, (151.2016, 69.0025)), (l51, u1811)

# 1. what leaves: the feed's last stretch into the old place, and the via in the way
drop(TEE, F, [l51, (154.1716, 68.6009), pad("C86", "1")[0]])
drop(RF, F, [pad("C86", "2")[0], u1811])
b.Delete(via_at("GND", VIA_OLD))

# 2. C86 upright, pad 1 north
c86.SetPosition(v(*C86_AT))
c86.SetOrientationDegrees(C86_ROT)
c861, c862 = pad("C86", "1")[0], pad("C86", "2")[0]
assert near(c861, (C86_AT[0], C86_AT[1] - 0.48)) and near(c862, (C86_AT[0], C86_AT[1] + 0.48)), (c861, c862)
label = c86.Reference()
label.SetPosition(v(*LABEL))
label.SetTextAngleDegrees(90)

# 3. the feed: the step north sits midway between L5's pad and C86's
up = l51[1] - c861[1]
track(TEE, F, 0.25, [l51, (153.63, l51[1]), (153.63 - up, c861[1]), c861])
down = u1811[1] - c862[1]
track(RF, F, 0.25, [c862, (c862[0] - down, u1811[1]), u1811])
via("GND", VIA_NEW, 0.45, 0.2)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())

# 4. no pad on the front under the foot or within KEEP of it
found = []
for f in b.GetFootprints():
    if f.GetReference() == "BT1":
        continue
    for q in f.Pads():
        if not q.IsOnLayer(F) or seg_d(mm(q.GetPosition()), *FOOT) > 8:
            continue
        poly = q.GetEffectivePolygon(F, pcbnew.ERROR_INSIDE).Outline(0)
        ring = [mm(poly.CPoint(i)) for i in range(poly.PointCount())]
        found.append((ring_d(ring, *FOOT) - FOOT_R, f"{f.GetReference()}.{q.GetNumber()}"))
found.sort()
print("front pads nearest the holder's foot: " + ", ".join("%s %.3f mm" % (name, d) for d, name in found[:4]))
if found[0][0] < KEEP:
    raise SystemExit(f"{found[0][1]} is within {KEEP} mm of the foot: not saved")

b.Save(sys.argv[1])
print("saved")
