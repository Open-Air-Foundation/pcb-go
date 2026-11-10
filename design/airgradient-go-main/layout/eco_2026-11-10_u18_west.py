"""U18 (TAU1113 GNSS module) moves 1.0 mm west, clear of the battery holder.

Why: the holder (BT1 model GO_v2.12_26.08.17_2.07.step) has a 0.77 mm flange round its screw boss that rests on the
board, its west edge at x 152.45. U18 pad 10 (GND) reached x 153.10: 0.65 mm of the pad, where the solder fillet sits,
was under the flange, and the module body was 0.15 mm from it. v2.0 has the same placement.
After the move the pad ends at x 152.10 (0.35 mm clear) and the body at x 151.30 (1.15 mm clear).

What had to follow, because the 1.0 mm between U18's west pads and L3/Q5 held four vias and C65:
- LED_1_R/G/B vias (x 141.0-141.1) go east under the module body to x 142.8 as 0.4/0.2 vias; the In2 lanes and the
  B.Cu tracks are extended from the old via points to the new ones.
- RESE via (141.02, 68.46) goes south to (140.14, 70.25): RESE on F.Cu down the gap between R43 and U18's pads, the
  In2 lane (y 69.25) ends at x 140.14 and drops to the via. FPC1's GND pad on B.Cu (x 138.52-140.32, y 67.7-69.7)
  rules out anything nearer.
- L3 0.4 mm west (0.41 mm to U18's pads, 0.27 mm to C45); its tracks still end inside its pads.
- C65 (10 uF for U18) no longer fits beside pad 8, and the strip south of the module (y > 71.3) is under the holder:
  it goes to B.Cu at (141.75, 68.75), under pad 8, +3.3V pad on the via (143.79, 68.39) that feeds pad 8, GND pad on
  the pour of FPC1 pad 25 and C35.
- Three GND stitching vias round U20, (150.85, 67.40), (150.75, 64.27) and (150.79, 69.21), would touch U18's pads
  13, 15 and 11 (GNSS_RF): 0.9-0.95 mm west. A GND via at (142.9, 64.6) ties in the B.Cu pour that the
  LED_1_B run cuts off.
- U18's own tracks follow: MCU_RX, MCU_TX, VDD_BAK, +3.3V, GNSS_RF, PRTRG; its two GND vias stay and get a track.
- The block divider on F.Silkscreen west of U18 moves to x 140.4.
"""
import math
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
F, B, I2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu
TOL = 0.03
DX = -1.0


def v(x, y):
    return pcbnew.VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6)))


def mm(p):
    return (p.x / 1e6, p.y / 1e6)


def near(p, q, tol=TOL):
    return math.hypot(p[0] - q[0], p[1] - q[1]) <= tol


def net(name):
    n = b.FindNet(name)
    if not n:
        raise SystemExit(f"no net {name}")
    return n


def seg(netname, layer, p, q):
    hit = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetNetname() == netname and t.GetLayer() == layer
           and ((near(mm(t.GetStart()), p) and near(mm(t.GetEnd()), q)) or (near(mm(t.GetStart()), q) and near(mm(t.GetEnd()), p)))]
    if len(hit) != 1:
        raise SystemExit(f"{netname} {p} {q}: found {len(hit)}")
    return hit[0]


def move_end(t, old, new):
    if near(mm(t.GetStart()), old):
        t.SetStart(v(*new))
    elif near(mm(t.GetEnd()), old):
        t.SetEnd(v(*new))
    else:
        raise SystemExit(f"{t.GetNetname()}: no end at {old}")


def via_at(netname, p):
    hit = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == netname and near(mm(t.GetPosition()), p)]
    if len(hit) != 1:
        raise SystemExit(f"via {netname} {p}: found {len(hit)}")
    return hit[0]


def track(netname, layer, width, pts, locked=True):
    for p0, p1 in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(v(*p0))
        t.SetEnd(v(*p1))
        t.SetWidth(int(round(width * 1e6)))
        t.SetLayer(layer)
        t.SetNet(net(netname))
        t.SetLocked(locked)
        b.Add(t)


def via(netname, x, y, d, drill):
    t = pcbnew.PCB_VIA(b)
    t.SetViaType(pcbnew.VIATYPE_THROUGH)
    t.SetPosition(v(x, y))
    t.SetWidth(pcbnew.F_Cu, int(round(d * 1e6))) if hasattr(t, "SetWidth") and t.SetWidth.__doc__ and "PCB_LAYER_ID" in t.SetWidth.__doc__ else t.SetWidth(int(round(d * 1e6)))
    t.SetDrill(int(round(drill * 1e6)))
    t.SetNet(net(netname))
    t.SetLocked(True)
    b.Add(t)


u18 = b.FindFootprintByReference("U18")
if not near(mm(u18.GetPosition()), (147.351559, 65.7025)):
    raise SystemExit("U18 is not at its old position: already applied?")

# ---- 1. U18 and its own tracks -----------------------------------------------------------------------------------
u18.SetPosition(v(147.351559 + DX, 65.7025))
pad = {p.GetNumber(): mm(p.GetPosition()) for p in u18.Pads()}
assert near(pad["8"], (141.502, 69.002)) and near(pad["10"], (151.202, 70.103)), pad
move_end(seg("/MCU_RX", F, (143.991, 62.403), (142.502, 62.403)), (142.502, 62.403), (141.502, 62.403))
move_end(seg("/MCU_TX", F, (142.502, 63.502), (144.674, 63.502)), (142.502, 63.502), (141.502, 63.502))
s = seg("VDD_BAK", F, (144.162, 66.59), (142.714, 66.59))
d = seg("VDD_BAK", F, (142.714, 66.59), (142.502, 66.802))
move_end(s, (142.714, 66.59), (141.714, 66.59))
d.SetStart(v(141.714, 66.59))
d.SetEnd(v(141.502, 66.802))
move_end(seg("+3.3V", F, (143.281, 69.002), (142.502, 69.002)), (142.502, 69.002), (141.502, 69.002))
b.Delete(seg("+3.3V", F, (142.502, 69.002), (142.214, 69.29)))
b.Delete(seg("+3.3V", F, (142.214, 69.29), (140.582, 69.29)))
move_end(seg("/GNSS_RF", F, (153.372, 69.002), (152.202, 69.002)), (152.202, 69.002), (151.202, 69.002))
move_end(seg("/PRTRG", F, (153.75, 61.3), (152.202, 61.303)), (152.202, 61.303), (151.202, 61.303))
via_at("GND", (152.202, 70.103))
via_at("GND", (152.162, 68.155))
track("GND", F, 0.3, [(151.202, 70.103), (152.202, 70.103)])
track("GND", F, 0.3, [(151.202, 68.155), (152.162, 68.155)])

# ---- 2. GND vias in U20's pad that would touch U18's reserved pads ------------------------------------------------
for p in ((150.852, 67.4), (150.752, 64.27)):
    g = via_at("GND", p)
    g.SetPosition(v(p[0] - 0.95, p[1]))
g = via_at("GND", (150.792, 69.21))          # stitching via below U20's pins; it would sit against pad 11 (GNSS_RF)
g.SetPosition(v(149.892, 69.21))

# ---- 3. LED_1 vias under the module -------------------------------------------------------------------------------
LED = {"/LED_1_B": ((141.112, 66.09), (141.11, 66.09), 65.70), "/LED_1_G": ((141.077, 66.979), (141.08, 66.98), 67.20),
       "/LED_1_R": ((140.995, 67.799), (141.0, 67.8), 67.85)}
XV = 142.8
for name, (pv, pi, y) in LED.items():
    b.Delete(via_at(name, pv))
    dy = y - pv[1]
    track(name, B, 0.2, [pv, (pv[0] + abs(dy), y), (XV, y)])
    track(name, I2, 0.15, [pi, (pi[0] + abs(y - pi[1]), y), (XV, y)])
    via(name, XV, y, 0.4, 0.2)

# The LED_1_B run on B.Cu (y 65.70) cuts the pour round R49.1 and U20.46 off from the rest: a GND via of its own.
via("GND", 142.9, 64.6, 0.5, 0.3)

# ---- 4. RESE --------------------------------------------------------------------------------------------------------
b.Delete(seg("/RESE", F, (141.016, 68.461), (140.743, 68.461)))
b.Delete(seg("/RESE", F, (140.743, 68.461), (140.142, 67.86)))
b.Delete(via_at("/RESE", (141.016, 68.461)))
b.Delete(seg("/RESE", I2, (140.24, 69.25), (141.02, 68.47)))
move_end(seg("/RESE", I2, (126.64, 69.25), (140.24, 69.25)), (140.24, 69.25), (140.14, 69.25))
track("/RESE", I2, 0.15, [(140.14, 69.25), (140.14, 70.25)])
track("/RESE", F, 0.2, [(140.14, 68.2), (140.14, 70.25)])
via("/RESE", 140.14, 70.25, 0.4, 0.2)

# ---- 5. L3 ----------------------------------------------------------------------------------------------------------
l3 = b.FindFootprintByReference("L3")
p = mm(l3.GetPosition())
l3.SetPosition(v(p[0] - 0.4, p[1]))

# ---- 6. C65 to B.Cu under pad 8 ------------------------------------------------------------------------------------
c65 = b.FindFootprintByReference("C65")
c65.SetPosition(v(141.75, 68.75))
c65.Flip(c65.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
c65.SetOrientationDegrees(0)
cp = {q.GetNumber(): (q.GetNetname(), mm(q.GetPosition())) for q in c65.Pads()}
if cp["2"][1][0] < cp["1"][1][0]:
    c65.SetOrientationDegrees(180)
    cp = {q.GetNumber(): (q.GetNetname(), mm(q.GetPosition())) for q in c65.Pads()}
assert c65.IsFlipped() and cp["1"][0] == "GND" and near(cp["1"][1], (140.975, 68.75)) and near(cp["2"][1], (142.525, 68.75)), cp
via_at("+3.3V", (143.794, 68.39))
track("+3.3V", B, 0.4, [(142.525, 68.75), (142.885, 68.39), (143.794, 68.39)])
track("GND", B, 0.3, [(140.975, 68.75), (140.0, 68.75)])          # to FPC1 pad 25 (GND)

# ---- 7. block frames on silk: the divider west of U18 to x 140.4 ---------------------------------------------------
FRAME = {((141.232, 59.04), (137.803, 58.975)): ((140.4, 59.024), None),
         ((141.232, 59.04), (160.971, 59.417)): ((140.4, 59.024), None),
         ((141.242, 71.519), (141.232, 59.04)): ((140.4, 71.519), (140.4, 59.024)),
         ((141.242, 71.519), (120.411, 71.519)): ((140.4, 71.519), None),
         ((161.881, 71.519), (141.242, 71.519)): (None, (140.4, 71.519))}
n = 0
for dr in b.GetDrawings():
    if dr.GetClass() != "PCB_SHAPE" or dr.GetLayer() != pcbnew.F_SilkS:
        continue
    for (a0, e0), (a1, e1) in FRAME.items():
        if near(mm(dr.GetStart()), a0) and near(mm(dr.GetEnd()), e0):
            if a1:
                dr.SetStart(v(*a1))
            if e1:
                dr.SetEnd(v(*e1))
            n += 1
assert n == 5, n
c65.Reference().SetPosition(v(141.75, 69.4))

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
print("saved")
