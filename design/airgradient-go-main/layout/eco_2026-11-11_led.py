"""R-V3-28 on the board: the four status LEDs move under the battery holder (Tanapat's sketch, 2026-11-11).
Layout only, no schematic change. Runs under KiCad's Python on the board after eco_2026-11-11_co_ldo.py.

Where the holder is (from its 3D model, back side of the board, gap = board to plastic):
- its two frames stand on the board with walls at x 102.6-103.6 / 120.8-121.8 and x 142.0-143.0 / 160.4-161.2;
- the bar across each frame is 10 mm up, so LED1 and LED4 at the top edge were under it but far from it, and LED2
  and LED3 sat in the open between the frames;
- the shoulders at y 69.8-73.0 are 5.2 mm up and 1 mm thick: x 103.6-108.8 on the left, and on the right
  x 148.1-153.5 west of the holder screw and x 157.4-160.4 east of it.

New places:
- LED1 (106.20, 71.90) in the left shoulder pocket;
- LED4 (151.00, 71.05) under the right shoulder, west of the screw. The pocket east of the screw, where the sketch
  has it, cannot be reached: the 1.1 mm neck north of the screw is the only way there, F.Cu and B.Cu are full in
  it (UART, I2C, PRTRG), and on In2 it is the one link of the +3.3V plane to U18, U20 and the e-paper booster;
- LED2 (119.40, 60.92) and LED3 (144.50, 60.92) under the bar ends, each 0.2 mm inside its frame wall.

Routing, B.Cu except where In2 is named:
- LED1, LED2: the In2 runs and their vias stay; only the ends change. LED1's three lines go west along
  y 61.9-62.75 and down x 104.5 / 106.2 / 107.0; the middle one passes between the LED's pads.
- LED3 lands where LED2's vias were: those three vias move to straight above their U20 pads (y 62.55, the middle
  one at 62.00), and their In2 runs are lengthened to reach them. LED3's green and blue pass north of these vias
  and south of the LED.
- LED4: up from U20, east, then down between U20 and the row of ground vias at x 153.5. The two ground vias of
  the GNSS feed at (152.16, 68.16) and (153.41, 68.24) leave 0.8 mm, so the three lines are 0.12 mm wide there.
- AE1, its keep-out and its ground vias do not move: turned along the top edge, its feed pad would end 1 mm
  from U18.
- Every LED gets its +3.3V from a via into the In2 plane next to its anode pad. The old anode vias stay as plane
  stitches (the one at (139.90, 63.47) also feeds the e-paper booster).
"""
import math
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
F, B, IN2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu
TOL = 0.02
P33 = "+3.3V"
COLOURS = "RGB"


def v(x, y): return pcbnew.VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6)))
def mm(p): return (p.x / 1e6, p.y / 1e6)
def near(p, q, tol=TOL): return math.hypot(p[0] - q[0], p[1] - q[1]) <= tol
def led(i, c): return f"/LED_{i}_{c}"


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


def vias(netname):
    return [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == netname]


def drop(items, expect, what):
    assert len(items) == expect, (what, len(items))
    for t in items:
        b.Delete(t)


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


def via(netname, x, y, d=0.4, drill=0.2):
    t = pcbnew.PCB_VIA(b)
    t.SetPosition(v(x, y))
    t.SetViaType(pcbnew.VIATYPE_THROUGH)
    t.SetWidth(F, int(round(d * 1e6)))
    t.SetDrill(int(round(drill * 1e6)))
    t.SetLayerPair(F, B)
    t.SetNet(net(netname))
    t.SetLocked(True)
    b.Add(t)


if not near(mm(b.FindFootprintByReference("LED1").GetPosition()), (111.106, 60.92), 0.05):
    raise SystemExit("already applied (LED1 is not at the top edge)")
if b.FindFootprintByReference("U24").GetPosition().x > int(170e6):
    raise SystemExit("run eco_2026-11-11_co_ldo.py first")

# 1. removals
for i in (3, 4):                                             # LED3 and LED4 are routed again from U20
    for c in COLOURS:
        for t in tracks(led(i, c)) + vias(led(i, c)):
            b.Delete(t)
for c in COLOURS:
    drop(tracks(led(2, c), B), {"R": 7, "G": 7, "B": 6}[c], f"LED2 {c} on B.Cu")
    drop([t for t in vias(led(2, c)) if mm(t.GetPosition())[0] > 140], 1, f"LED2 {c} via at U20")
    drop([t for t in tracks(led(1, c), B) if max(mm(t.GetStart())[0], mm(t.GetEnd())[0]) < 115],
         {"R": 1, "G": 2, "B": 1}[c], f"LED1 {c} end on B.Cu")
EAST = {}                                                    # east end of each LED2 run on In2, after its old tail goes
for c, x_end, n in (("R", 143.97, 2), ("G", 144.49, 1), ("B", 144.86, 3)):
    drop([t for t in tracks(led(2, c), IN2) if min(mm(t.GetStart())[0], mm(t.GetEnd())[0]) > x_end - 0.02], n,
         f"LED2 {c} tail on In2")
    ends = [mm(e) for t in tracks(led(2, c), IN2) for e in (t.GetStart(), t.GetEnd())]
    EAST[c] = max(ends)
    assert abs(EAST[c][0] - x_end) < 0.02, (c, EAST[c])
for pts in ([(110.306, 60.62), (109.2416, 60.62), (109.1716, 60.69)], [(125.4715, 61.2201), (125.4715, 61.8401)],
            [(139.9016, 63.47), (140.4291, 62.9425), (140.4291, 61.22)], [(153.6016, 62.12), (153.6016, 61.55)]):
    for t in polyline(P33, B, pts):                          # old anode stubs; their vias stay
        b.Delete(t)

# 2. placement
PLACE = {"LED1": (106.20, 71.90, 0), "LED2": (119.40, 60.92, 0), "LED3": (144.50, 60.92, 180), "LED4": (151.00, 71.05, 0)}
for ref, (x, y, rot) in PLACE.items():
    fp = b.FindFootprintByReference(ref)
    fp.SetPosition(v(x, y))
    fp.SetOrientationDegrees(rot)
    fp.SetLocked(True)
    fp.Reference().SetVisible(False)   # labels come from the pcb_silk pass
EXPECT = {"LED1": [(105.40, 71.60), (107.00, 71.60), (107.00, 72.20), (105.40, 72.20)],
          "LED2": [(118.60, 60.62), (120.20, 60.62), (120.20, 61.22), (118.60, 61.22)],
          "LED3": [(145.30, 61.22), (143.70, 61.22), (143.70, 60.62), (145.30, 60.62)],
          "LED4": [(150.20, 70.75), (151.80, 70.75), (151.80, 71.35), (150.20, 71.35)]}
for ref, pts in EXPECT.items():
    i = ref[-1]
    for num, want, name in zip("1234", pts, (P33, led(i, "B"), led(i, "G"), led(i, "R"))):
        got = pad(ref, num)
        assert near(got[0], want) and got[1] == name, (ref, num, got)
A = {ref: dict(zip(("A", "B", "G", "R"), pts)) for ref, pts in EXPECT.items()}    # pad centres by function
U20 = {(i, c): pad("U20", str(n))[0] for n, (i, c) in enumerate(((i, c) for i in (1, 2, 3, 4) for c in "BGR"), 1)}
for (i, c), (p, name) in ((k, pad("U20", str(n))) for n, k in enumerate(U20, 1)):
    assert name == led(i, c), (i, c, name)
SIG = 0.15

# 3. LED1: from the vias that end its In2 runs, west and down into the left pocket
via(P33, 105.40, 70.90, 0.5, 0.3)
track(P33, B, 0.2, [(105.40, 70.90), A["LED1"]["A"]])
track(led(1, "R"), B, SIG, [(110.3116, 61.91), (105.00, 61.91), (104.50, 62.41), (104.50, 71.75), (104.95, 72.20), A["LED1"]["R"]])
track(led(1, "G"), B, SIG, [(111.454, 61.7995), (111.454, 62.05), (111.054, 62.45), (106.70, 62.45), (106.20, 62.95),
                           (106.20, 71.95), (106.45, 72.20), A["LED1"]["G"]])
track(led(1, "B"), B, SIG, [(112.8716, 60.64), (112.8716, 62.35), (112.4716, 62.75), (107.50, 62.75), (107.00, 63.25),
                           A["LED1"]["B"]])

# 4. LED2: from its three vias east of the frame wall
via(P33, 117.75, 60.62, 0.5, 0.3)
track(P33, B, 0.2, [(117.75, 60.62), A["LED2"]["A"]])
track(led(2, "G"), B, SIG, [(122.4216, 61.88), (121.7616, 61.22), A["LED2"]["G"]])
track(led(2, "B"), B, SIG, [(123.5716, 61.87), (123.5716, 61.50), (122.6916, 60.62), A["LED2"]["B"]])
track(led(2, "R"), B, SIG, [(126.6216, 61.57), (126.6216, 62.00), (126.1716, 62.45), (121.30, 62.45), (120.57, 61.72),
                           (118.90, 61.72), (118.60, 61.42), A["LED2"]["R"]])

# 5. LED2 at U20: vias above the pads (the middle one a row higher), In2 runs lengthened to them
V2 = {"B": (U20[(2, "B")][0], 62.55), "G": (U20[(2, "G")][0], 62.00), "R": (U20[(2, "R")][0], 62.55)}
for c, p in V2.items():
    via(led(2, c), *p)
    track(led(2, c), B, SIG, [U20[(2, c)], p])
(ex, ey) = EAST["R"]
track(led(2, "R"), IN2, SIG, [(ex, ey), (146.75, ey), (146.75 + (ey - 61.55), 61.55), (V2["R"][0] - 0.15, 61.55), (V2["R"][0], 61.70), V2["R"]])
(ex, ey) = EAST["G"]
track(led(2, "G"), IN2, SIG, [(ex, ey), (146.90, ey), (146.90 + (ey - 62.00), 62.00), V2["G"]])
(ex, ey) = EAST["B"]
track(led(2, "B"), IN2, SIG, [(ex, ey), (V2["B"][0] - (ey - V2["B"][1]), ey), V2["B"]])

# 6. LED3: red straight in; green and blue run north of LED2's vias, then south of the LED (green comes up
#    between its pads)
via(P33, 146.20, 61.22, 0.5, 0.3)
track(P33, B, 0.2, [(146.20, 61.22), A["LED3"]["A"]])
x, y = U20[(3, "R")]
track(led(3, "R"), B, SIG, [(x, y), (x, 60.92), (x - 0.30, 60.62), A["LED3"]["R"]])
x, y = U20[(3, "G")]
track(led(3, "G"), B, SIG, [(x, y), (x, 61.50), (x - 0.30, 61.20), (147.15, 61.20), (146.63, 61.72), (144.75, 61.72),
                           (144.50, 61.47), (144.50, 60.87), (144.25, 60.62), A["LED3"]["G"]])
x, y = U20[(3, "B")]
track(led(3, "B"), B, SIG, [(x, y), (x, 61.80), (x - 0.30, 61.50), (147.27, 61.50), (146.75, 62.02), (144.00, 62.02),
                           (143.70, 61.72), A["LED3"]["B"]])

# 7. LED4: all on B.Cu. Up from U20, down the 0.6 mm between the two ground vias east of it (0.12 mm tracks
#    there), west above the LED and down into its pads; red and green pass between the pads.
LANE = {"R": 152.56, "G": 152.785, "B": 153.01}
RUN = {"R": (62.30, 69.11), "G": (61.75, 69.38), "B": (61.20, 69.65)}       # y of the run east of U20, y of the run above the LED
DROP = {"R": 150.875, "G": 151.125, "B": 151.70}
THIN = 0.12
for c, rise in (("R", 0.60), ("G", 0.30), ("B", 0.30)):
    (x, y), lane, (top, low), dx = U20[(4, c)], LANE[c], RUN[c], DROP[c]
    track(led(4, c), B, SIG, [(x, y), (x, top + rise), (x + rise, top), (lane - 0.30, top)])
    track(led(4, c), B, THIN, [(lane - 0.30, top), (lane, top + 0.30), (lane, low - 0.15), (lane - 0.15, low)])
    track(led(4, c), B, SIG, [(lane - 0.15, low), (dx + 0.15, low), (dx, low + 0.15)])
track(led(4, "B"), B, SIG, [(DROP["B"], RUN["B"][1] + 0.15), (DROP["B"], 70.75)])
track(led(4, "G"), B, THIN, [(DROP["G"], RUN["G"][1] + 0.15), (DROP["G"], 71.20), (DROP["G"] + 0.15, 71.35)])
track(led(4, "G"), B, SIG, [(DROP["G"] + 0.15, 71.35), A["LED4"]["G"]])
track(led(4, "R"), B, THIN, [(DROP["R"], RUN["R"][1] + 0.15), (DROP["R"], 71.20), (DROP["R"] - 0.15, 71.35)])
track(led(4, "R"), B, SIG, [(DROP["R"] - 0.15, 71.35), A["LED4"]["R"]])
via(P33, 149.55, 70.35, 0.5, 0.3)
track(P33, B, 0.2, [(149.55, 70.35), (149.95, 70.75), A["LED4"]["A"]])

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
print("saved")
