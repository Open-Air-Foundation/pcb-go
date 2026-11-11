"""R-V3-29 on the board: LED4 moves into the holder pocket at the east wall, where Tanapat's sketch had it.
Layout only. Runs under KiCad's Python on the board after eco_2026-11-11_led.py, and after Tanapat moved the
chamfer of the `gnss-antenna` rule area 1.13 mm east (2026-11-11, by hand in KiCad).

What stood in the way (R-V3-28): every way to the pocket passes the neck north of the holder screw, 1.1 mm of
board between the antenna rule area (y 68.81) and the screw hole. That stretch is as it was, the rule area only
moved where it runs diagonally.
- F.Cu had 0.63 mm free north of MCU_RX: room for two 0.15 mm tracks.
- In2 had the +3.3V plane link, 0.67 mm, north of Pack+: one 0.15 mm track fits beside Pack+ and leaves 0.41 mm
  of plane. Three tracks there cut the link (tried in R-V3-28).
- B.Cu is full (PRTRG, SCL, SDA).
So blue and green cross the neck on F.Cu, red on In2, and the plane link stays.

LED4 at (159.45, 72.85), turned 90 degrees: the floor of the pocket is 2.7 mm wide, from the holder's screw boss
to its wall (x 160.25), and SCL, SDA and PRTRG take the west half of it on B.Cu, so the LED only fits standing,
0.4 mm from the wall. Each pad has its via straight north or south of it and no track runs beside the LED:
N1 blue, N2 green, S2 red, S1 the anode into the In2 +3.3V plane.

West of the neck the three 0.12 mm lanes from U20 stay as they are down to the two ground vias of the GNSS feed
and end in three vias south of the feed: blue (153.27, 69.88) and green to F.Cu, red to In2. The ground via at
(153.46, 69.69) goes. With it in place blue's via only fits north-east of it, 0.07 mm from the feed's bend
(tried, a DRC error); without it nothing new comes nearer than 0.27 mm to the feed. The feed keeps its ground
vias at (152.16, 68.16), (153.41, 68.24) and (152.20, 70.10).

East of the neck green follows MCU_RX and blue follows green, both pass south of the ground via at
(158.60, 70.75), then run east to their vias. Blue is the one that needs the rule area moved: beside the screw
it runs 0.13 mm inside the old outline. Red follows Pack+ round the screw and reaches S2 from the south-west,
below S1, so that S1 sits in the part of the plane that joins the rest.

PRTRG changed layer at (159.15, 73.30), where the LED now sits. Its B.Cu run goes on south beside SCL and the
via moves to (158.95, 75.45).

The anode via this morning's script put at (149.55, 70.35) goes with its stub.
"""
import math
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
F, B, IN2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu
TOL = 0.02
P33, PRTRG, RX, PACK = "+3.3V", "/PRTRG", "/MCU_RX", "Pack+"
SIG, THIN = 0.15, 0.12
GAP = 0.105                     # between neighbours; the board minimum is 0.1


def v(x, y): return pcbnew.VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6)))
def mm(p): return (p.x / 1e6, p.y / 1e6)
def near(p, q, tol=TOL): return math.hypot(p[0] - q[0], p[1] - q[1]) <= tol
def led(c): return f"/LED_4_{c}"


def net(name):
    n = b.FindNet(name)
    if not n:
        raise SystemExit(f"no net {name}")
    return n


def pad(ref, num):
    p = b.FindFootprintByReference(ref).FindPadByNumber(num)
    return mm(p.GetPosition()), p.GetNetname()


def tracks(netname, layer=None):
    return [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetNetname() == netname
            and (layer is None or t.GetLayer() == layer)]


def polyline(netname, layer, pts):
    """The existing tracks that draw the polyline pts, one per leg."""
    out = []
    for a, z in zip(pts, pts[1:]):
        hit = [t for t in tracks(netname, layer)
               if sorted(near(mm(e), q) for e in (t.GetStart(), t.GetEnd()) for q in (a, z)) == [0, 0, 1, 1]]
        if len(hit) != 1:
            raise SystemExit(f"{netname}: {len(hit)} tracks from {a} to {z}")
        out += hit
    return out


def via_at(netname, at):
    hit = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == netname and near(mm(t.GetPosition()), at)]
    if len(hit) != 1:
        raise SystemExit(f"{netname}: {len(hit)} vias at {at}")
    return hit[0]


NEW = []                        # (layer or None for a via, half width, points) of everything added, for the rule-area check


def track(netname, layer, width, pts):
    NEW.append((layer, width / 2, pts))
    for a, z in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(v(*a))
        t.SetEnd(v(*z))
        t.SetWidth(int(round(width * 1e6)))
        t.SetLayer(layer)
        t.SetNet(net(netname))
        t.SetLocked(True)
        b.Add(t)


def via(netname, x, y, d=0.4, drill=0.2):
    NEW.append((None, d / 2, [(x, y)]))
    t = pcbnew.PCB_VIA(b)
    t.SetPosition(v(x, y))
    t.SetViaType(pcbnew.VIATYPE_THROUGH)
    t.SetWidth(F, int(round(d * 1e6)))
    t.SetDrill(int(round(drill * 1e6)))
    t.SetLayerPair(F, B)
    t.SetNet(net(netname))
    t.SetLocked(True)
    b.Add(t)


def beside(pts, d):
    """The polyline d to the outside of pts: north of a run east, east of a run south (y grows downwards)."""
    lines = []
    for (ax, ay), (zx, zy) in zip(pts, pts[1:]):
        n = math.hypot(zx - ax, zy - ay)
        ox, oy = (zy - ay) / n * d, -(zx - ax) / n * d
        lines.append(((ax + ox, ay + oy), (zx + ox, zy + oy)))
    out = [lines[0][0]]
    for ((a, c), (e, g)) in zip(lines, lines[1:]):
        r, s = (c[0] - a[0], c[1] - a[1]), (g[0] - e[0], g[1] - e[1])
        t = ((e[0] - a[0]) * s[1] - (e[1] - a[1]) * s[0]) / (r[0] * s[1] - r[1] * s[0])
        out.append((a[0] + t * r[0], a[1] + t * r[1]))
    return out + [lines[-1][1]]


def on_leg(p, q, x=None, y=None):
    """The point of the line p-q at the given x or y."""
    t = (x - p[0]) / (q[0] - p[0]) if x is not None else (y - p[1]) / (q[1] - p[1])
    return (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]))


if not near(mm(b.FindFootprintByReference("LED4").GetPosition()), (151.00, 71.05), 0.05):
    raise SystemExit("already applied (LED4 is not west of the holder screw)")

# 1. the copper the new routes are measured from must be where it was
RX_RUN = [(153.702, 70.42), (154.586, 69.535), (156.557, 69.535), (157.292, 70.27), (157.292, 72.02)]
PACK_RUN = [(152.436, 72.32), (154.924, 69.832), (156.018, 69.832), (156.791, 70.605), (156.791, 71.839),
            (158.122, 73.17), (158.122, 92.13)]
rx_w = {t.GetWidth() / 1e6 for t in polyline(RX, F, RX_RUN)}
pack_w = {t.GetWidth() / 1e6 for t in polyline(PACK, IN2, PACK_RUN)}
assert len(rx_w) == 1 and len(pack_w) == 1, (rx_w, pack_w)
rx_w, pack_w = rx_w.pop(), pack_w.pop()
LANE = {"R": 152.56, "G": 152.785, "B": 153.01}
polyline(PRTRG, B, [(157.71, 70.11), (157.71, 71.87)])
for at in ((152.162, 68.155), (153.412, 68.24), (152.202, 70.103), (158.60, 70.75), (160.00, 70.75)):
    via_at("GND", at)

# 2. removals
OLD = {led("B"): [(153.01, 61.50), (153.01, 69.50), (152.86, 69.65), (151.85, 69.65), (151.70, 69.80), (151.70, 70.75)],
       led("G"): [(152.785, 62.05), (152.785, 69.23), (152.635, 69.38), (151.275, 69.38), (151.125, 69.53), (151.125, 71.20),
                  (151.275, 71.35), (151.80, 71.35)],
       led("R"): [(152.56, 62.60), (152.56, 68.96), (152.41, 69.11), (151.025, 69.11), (150.875, 69.26), (150.875, 71.20),
                  (150.725, 71.35), (150.20, 71.35)],
       P33: [(149.55, 70.35), (149.95, 70.75), (150.20, 70.75)],
       PRTRG: [(157.71, 71.87), (158.79, 72.95), (159.15, 73.30)]}
for name, pts in OLD.items():
    for t in polyline(name, B, pts):
        b.Delete(t)
for t in polyline(PRTRG, F, [(159.15, 73.30), (159.15, 93.90)]):
    b.Delete(t)
b.Delete(via_at(P33, (149.55, 70.35)))
b.Delete(via_at("GND", (153.462, 69.69)))
b.Delete(via_at(PRTRG, (159.15, 73.30)))

# 3. placement
fp = b.FindFootprintByReference("LED4")
fp.SetPosition(v(159.45, 72.85))
fp.SetOrientationDegrees(90)
fp.SetLocked(True)
fp.Reference().SetVisible(False)
A = {}
for num, name, want in (("1", P33, (159.15, 73.65)), ("2", led("B"), (159.15, 72.05)),
                        ("3", led("G"), (159.75, 72.05)), ("4", led("R"), (159.75, 73.65))):
    got = pad("LED4", num)
    assert near(got[0], want) and got[1] == name, (num, got)
    A[name] = want
N1, N2, S1, S2 = (159.15, 71.30), (159.75, 71.30), (159.17, 74.47), (159.75, 74.45)

# 4. west of the neck: lane ends on B.Cu and the three vias
VB, VR = (153.27, 69.88), (152.62, 70.75)
track(led("B"), B, THIN, [(LANE["B"], 61.50), (LANE["B"], 68.75), (VB[0], 68.75 + VB[0] - LANE["B"])])
track(led("B"), B, SIG, [(VB[0], 68.75 + VB[0] - LANE["B"]), VB])
green = beside(RX_RUN, rx_w / 2 + GAP + SIG / 2)
blue = beside(RX_RUN, rx_w / 2 + 2 * GAP + 1.5 * SIG)
red = beside(PACK_RUN, pack_w / 2 + GAP + SIG / 2)
VG = on_leg(green[0], green[1], x=153.20)
GX = 152.86                     # green and red step east below the lanes: red clears the ground via at (152.20, 70.10)
track(led("G"), B, THIN, [(LANE["G"], 62.05), (LANE["G"], 69.00), (GX, 69.00 + GX - LANE["G"]), (GX, VG[1] - (VG[0] - GX))])
track(led("G"), B, SIG, [(GX, VG[1] - (VG[0] - GX)), VG])
track(led("R"), B, THIN, [(LANE["R"], 62.60), (LANE["R"], 69.20), (VR[0], 69.20 + VR[0] - LANE["R"]), VR])
for name, at in ((led("B"), VB), (led("G"), VG), (led("R"), VR)):
    via(name, *at)

# 5. green on F.Cu beside MCU_RX, blue beside green, both south of the ground via at (158.60, 70.75)
Y_G, Y_B = 71.68, N1[1]         # where green and blue run east to their vias; green passes south of N1
gx, bx = green[4][0], blue[4][0]
leave_g = Y_G - 0.96            # green leaves its run south here, on a 45 degree line that clears that via
leave_b = leave_g + (bx - gx) - (GAP + SIG) * math.sqrt(2)      # same pitch on the diagonal as beside MCU_RX
track(led("G"), F, SIG, [VG] + green[1:4] + [(gx, leave_g), (gx + Y_G - leave_g, Y_G), (N2[0] - 0.25, Y_G),
                                             (N2[0], Y_G - 0.25), N2])
track(led("B"), F, SIG, [VB, on_leg(blue[0], blue[1], y=VB[1])] + blue[1:4] + [(bx, leave_b), (bx + Y_B - leave_b, Y_B), N1])

# 6. red on In2 beside Pack+, then east below S1 and up into S2
RED_Y, START_Y = 74.905, 70.95
red_start = on_leg(red[0], red[1], y=START_Y)
rx_ = red[5][0]
track(led("R"), IN2, SIG, [VR, (VR[0] + START_Y - VR[1], START_Y), red_start] + red[1:6]
      + [(rx_, RED_Y - 0.23), (rx_ + 0.23, RED_Y), (S2[0] - 0.25, RED_Y), (S2[0], RED_Y - 0.25), S2])

# 7. the four vias at the LED
for name, at, d, drill in ((led("B"), N1, 0.4, 0.2), (led("G"), N2, 0.4, 0.2), (led("R"), S2, 0.4, 0.2), (P33, S1, 0.5, 0.3)):
    via(name, *at, d, drill)
    track(name, B, 0.2 if name == P33 else SIG, [at, A[name]])

# 8. PRTRG: on south beside SCL, via below the LED
PV = (158.95, 75.45)
track(PRTRG, B, 0.2, [(157.71, 71.87), (158.70, 72.86), (158.70, PV[1] - 0.25), PV])
via(PRTRG, *PV, 0.5, 0.3)
track(PRTRG, F, 0.2, [PV, (159.15, PV[1] + 0.20), (159.15, 93.90)])

# 9. nothing new may lie inside the antenna rule area: it keeps pours out, not tracks
area = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName() == "gnss-antenna"]
assert len(area) == 1, len(area)
ring = area[0].Outline().Outline(0)
ring = [mm(ring.CPoint(i)) for i in range(ring.PointCount())]


def inside(p):
    hit = False
    for (ax, ay), (zx, zy) in zip(ring, ring[1:] + ring[:1]):
        if (ay > p[1]) != (zy > p[1]) and p[0] < ax + (p[1] - ay) / (zy - ay) * (zx - ax):
            hit = not hit
    return hit


def to_ring(p):
    best = 1e9
    for (ax, ay), (zx, zy) in zip(ring, ring[1:] + ring[:1]):
        t = max(0.0, min(1.0, ((p[0] - ax) * (zx - ax) + (p[1] - ay) * (zy - ay)) / ((zx - ax) ** 2 + (zy - ay) ** 2)))
        best = min(best, math.hypot(p[0] - ax - t * (zx - ax), p[1] - ay - t * (zy - ay)))
    return best


for layer, half, pts in NEW:
    for (ax, ay), (zx, zy) in zip(pts, pts[1:] or pts):
        for i in range(int(math.hypot(zx - ax, zy - ay) / 0.02) + 1):
            t = i * 0.02 / max(math.hypot(zx - ax, zy - ay), 1e-9)
            p = (ax + t * (zx - ax), ay + t * (zy - ay))
            if inside(p) or to_ring(p) < half:
                raise SystemExit(f"new copper at ({p[0]:.3f}, {p[1]:.3f}) is inside the gnss-antenna rule area")

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
print("saved")
