"""R-V3-16 charger input for a 2 A charge: widen the U5.18 (VBUS) lead.

The lead from U5.18 to C30.2 and the two VBUS vias was 0.2 mm. From y 96.45 down it goes
to 0.35 mm: the most that keeps 0.115 mm to the PMID zone (x >= 122.122), and 0.17 mm to
U5.1 (BTST), an L-shaped pad reaching down to y 96.68 at x 121.60. A third VBUS via does not fit: the pocket between B.Cu SCL (y 94.09) and
SDA (y 95.74) holds the two there now, and C30's pads close the rest.
"""
import math
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
F = pcbnew.F_Cu
TOL = 0.02


def v(x, y):
    return pcbnew.VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6)))


def mm(p):
    return (p.x / 1e6, p.y / 1e6)


def near(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1]) <= TOL


def seg(p, q):
    for t in b.GetTracks():
        if t.GetClass() == "PCB_TRACK" and t.GetNetname() == "VBUS" and t.GetLayer() == F:
            a, e = mm(t.GetStart()), mm(t.GetEnd())
            if (near(a, p) and near(e, q)) or (near(a, q) and near(e, p)):
                return t
    raise SystemExit(f"no VBUS track {p} {q}")


old = seg((121.832, 97.13), (121.832, 95.59))
diag = seg((121.832, 95.59), (121.522, 95.28))
if old.GetWidth() != int(0.2e6):
    raise SystemExit("already applied")
locked = old.IsLocked()
b.Delete(old)


def track(p0, p1, width):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(v(*p0))
    t.SetEnd(v(*p1))
    t.SetWidth(int(round(width * 1e6)))
    t.SetLayer(F)
    t.SetNet(b.FindNet("VBUS"))
    t.SetLocked(locked)
    b.Add(t)


track((121.832, 97.13), (121.832, 96.45), 0.2)   # pad, then clear of U5.1's L-shaped pad (y >= 96.68)
track((121.832, 96.45), (121.832, 95.59), 0.35)
diag.SetWidth(int(0.35e6))

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
print("saved")
