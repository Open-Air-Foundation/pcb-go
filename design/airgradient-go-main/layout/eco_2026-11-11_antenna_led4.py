"""R-V3-31, R-V3-32 and R-V3-33 on the board. Runs under KiCad's Python after
`pcb_import --replace --refresh AE1` with the schematic of eco/sch_eco_2026-11-11_gnss_match.py
(AE1 with the manual's pads, L4 and L5 as 0402 inductors where R45 and C62 were, C86 staged, C61 left over).

R-V3-31, the antenna as the CA-G01 manual has it (CA-G01_V01 5.2 to 5.4):
- Pads 1.2 x 3.0 mm, 8.0 mm apart (the footprint in the library). They reach 0.25 mm further out than the old
  ones, which leaves pad 2 0.12 mm from the board's corner, so AE1 moves 0.16 mm along its own axis towards pad 1.
- T network: L4 (Series 1) in the clear area 1.1 mm from the feed pad, L5 (Shunt 1) on the edge of the ground
  where C62 was, C86 (Series 2) on the last stretch into U18 pin 11. C61 and its ground track leave the clear
  area. The feed is 0.5 mm wide from the pad to the T node; it runs 0.25 mm above the pad's centre line, which
  keeps it 0.7 mm from the ground under the neck. L5's ground pad gets a via 0.6 mm away.
- Nothing but the feed and L4 within 2.0 mm of the pads, on any layer: the `gnss-antenna` rule area follows that
  distance (chamfer and south edge), the ground vias at y 70.75 leave, the one east of the holder wall moves.

R-V3-32, LED4 lies like the other three: (158.80, 71.90), turned as LED1, on LED1's line. The holder's pocket is
2.78 mm wide there and the pads take 2.50. What passes the neck north of the holder screw, by layer:
- F.Cu   MCU_TX, MCU_RX, their diagonals 0.1 mm nearer the screw hole. LED4's two lines leave this layer.
- In2    LED_4_R, LED_4_G and a +3.3V track for LED4's anode: the plane cannot pass the neck any more and the
         east strip's plane has no other link. Pack+ takes the 0.62 mm between the screw hole and the cut-out.
- B.Cu   SCL, LED_4_B, PRTRG, 0.15 mm on the diagonal. LED_4_B needs no via now. SDA passes south of the
         screw hole like Pack+, as ePaper RES already does on F.Cu.
PRTRG passes north and east of LED4 and returns to its via; SCL and SDA pass between LED4 and the cut-out.
The anode's and green's vias sit under LED4, between its pads; red's is south of it.
The ground via beside the GNSS feed that R-V3-29 took away is back, 0.06 mm further south.

R-V3-33: U14 pad 3 (SA0) gets a track to C57's ground pad; the ground via inside USB1 pad A1B12 moves out of
the pad, south between the shell lug and the locating peg. TP footprints that pcb_import re-adds are dropped.
"""
import math
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
F, B, IN1, IN2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu
TOL = 0.02
R2 = math.sqrt(2)
ANT, TEE, RF = "Net-(AE1-A)", "/GNSS_T", "/GNSS_RF"
P33, PRTRG, SCL, SDA, RX, TX, PACK = "+3.3V", "/PRTRG", "/SCL", "/SDA", "/MCU_RX", "/MCU_TX", "Pack+"
HOLE = (155.4708, 71.1515)          # BT1's screw hole, r 1.02
CUT = (155.9708, 74.2915)           # centre of the cut-out's corner, r 1.5
CLEAR = 2.0                         # manual 5.4.2, 5.4.3: ground 2 to 6 mm from the pads
GAP = 0.105
W = 0.15                            # line width where room is short


def v(x, y): return pcbnew.VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6)))
def mm(p): return (p.x / 1e6, p.y / 1e6)
def near(p, q, tol=TOL): return math.hypot(p[0] - q[0], p[1] - q[1]) <= tol
def led(c): return f"/LED_4_{c}"


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


def via(netname, at, d=0.4, drill=0.2):
    t = pcbnew.PCB_VIA(b)
    t.SetPosition(v(*at))
    t.SetViaType(pcbnew.VIATYPE_THROUGH)
    t.SetWidth(F, int(round(d * 1e6)))
    t.SetDrill(int(round(drill * 1e6)))
    t.SetLayerPair(F, B)
    t.SetNet(net(netname))
    t.SetLocked(True)
    b.Add(t)


def place(ref, x, y, rot):
    f = fp(ref)
    f.SetPosition(v(x, y))
    f.SetOrientationDegrees(rot)
    f.SetLocked(True)
    f.Reference().SetVisible(False)     # labels come from the pcb_silk pass
    return f


def ring_s(centre, rho):
    """x - y of the 45 degree line (running south-east) that passes rho from centre on its north-east side."""
    return centre[0] - centre[1] + rho * R2


def on(s, x=None, y=None):
    """The point of the line x - y = s at the given x or y."""
    return (x, x - s) if y is None else (s + y, y)


if not near(mm(fp("LED4").GetPosition()), (159.45, 72.85), 0.05):
    raise SystemExit("already applied (LED4 is not upright at the east wall)")
for ref, num, name in (("L4", "1", ANT), ("L4", "2", TEE), ("L5", "1", TEE), ("L5", "2", "GND"), ("C86", "1", TEE),
                       ("C86", "2", RF), ("U18", "11", RF), ("AE1", "1", ANT)):
    if pad(ref, num)[1] != name:
        raise SystemExit(f"{ref}.{num} is on {pad(ref, num)[1]!r}: run pcb_import with the R-V3-31 schematic first")
for ref in ("L4", "L5"):
    if "L_0402" not in fp(ref).GetFPIDAsString():
        raise SystemExit(f"{ref} is still {fp(ref).GetFPIDAsString()}: run pcb_import with --replace")
ae = fp("AE1")
if abs(math.hypot(*(a - c for a, c in zip(pad("AE1", "1")[0], pad("AE1", "2")[0]))) - 8.0) > 0.01:
    raise SystemExit("AE1 does not have the manual's pads: run pcb_import with --refresh AE1")

# 1. test points pcb_import brought back, and C61, which the schematic no longer has
tps = [f for f in b.GetFootprints() if f.GetReference().startswith("TP")]
for f in tps:
    b.Delete(f)
print("removed", len(tps), "TP footprints")
b.Delete(fp("C61"))

# 2. removals
# antenna feed and the ground track to C61
drop(ANT, F, [(156.5216, 67.7287), (160.0575, 67.7287)])
drop(RF, F, [(155.5016, 67.7287), (154.1716, 67.7287), (154.1716, 68.2025)])
drop(RF, F, [(153.3716, 69.0025), (151.202, 69.002)])
drop("GND", F, [(157.7916, 66.7687), (154.1716, 66.7687)])
arc = [t for t in b.GetTracks() if t.GetClass() == "PCB_ARC" and t.GetNetname() == RF]
assert len(arc) == 1 and near(mm(arc[0].GetEnd()), (154.1716, 68.2025), 0.02) | near(mm(arc[0].GetStart()), (154.1716, 68.2025), 0.02)
b.Delete(arc[0])
# LED4's lines on F.Cu, its stubs and vias
drop(led("B"), F, [(153.27, 69.88), (153.489, 69.88), (154.3653, 69.0027), (156.7775, 69.0027), (157.8243, 70.0495),
                   (157.8243, 70.6144), (158.51, 71.3), (159.15, 71.3)])
drop(led("G"), F, [(153.2, 70.5301), (154.471, 69.2577), (156.6719, 69.2577), (157.5693, 70.1551), (157.5693, 70.72),
                   (158.5293, 71.68), (159.5, 71.68), (159.75, 71.43), (159.75, 71.3)])
drop(led("B"), B, [(153.01, 68.75), (153.27, 69.01), (153.27, 69.88)])
drop(led("B"), B, [(159.15, 71.3), (159.15, 72.05)])
drop(led("G"), B, [(159.75, 71.3), (159.75, 72.05)])
drop(led("R"), B, [(159.75, 74.45), (159.75, 73.65)])
drop(P33, B, [(159.17, 74.47), (159.15, 73.65)])
R_OLD = [(152.62, 70.75), (152.82, 70.95), (153.41, 70.95), (154.808, 69.552), (156.134, 69.552), (157.071, 70.489),
         (157.071, 71.723)]
drop(led("R"), IN2, R_OLD + [(158.402, 73.054), (158.402, 74.675), (158.632, 74.905), (159.5, 74.905), (159.75, 74.655),
                             (159.75, 74.45)])
for name, at in ((led("B"), (153.27, 69.88)), (led("B"), (159.15, 71.3)), (led("G"), (159.75, 71.3)),
                 (led("R"), (159.75, 74.45)), (P33, (159.17, 74.47)),
                 ("GND", (158.6, 70.75)), ("GND", (160.0, 70.75)), ("GND", (161.3, 70.75)),
                 ("GND", (149.6983, 130.3252))):                    # the last one: inside USB1 pad A1B12
    b.Delete(via_at(name, at))
# the lines round the screw hole that move
RX_OLD = [(154.5862, 69.5353), (156.5569, 69.5353), (157.2916, 70.27), (157.2916, 72.02)]
TX_OLD = [(154.7083, 69.83), (156.4348, 69.83), (156.9969, 70.3921), (156.9969, 72.1421)]
PACK_OLD = [(152.4356, 72.32), (154.9241, 69.8315), (156.0176, 69.8315), (156.7908, 70.6047), (156.7908, 71.8393),
            (158.1216, 73.17), (158.1216, 92.13)]
rx_w = polyline(RX, F, RX_OLD)[0].GetWidth() / 1e6
drop(RX, F, RX_OLD)
drop(TX, F, TX_OLD)
drop(PACK, IN2, PACK_OLD)
drop(PRTRG, B, [(154.52, 69.02), (156.62, 69.02), (157.71, 70.11), (157.71, 71.87), (158.7, 72.86), (158.7, 75.2), (158.95, 75.45)])
drop(SCL, B, [(153.7016, 70.4), (154.6516, 69.45), (156.4758, 69.45), (157.3116, 70.2857), (157.3116, 72.0257),
              (158.3916, 73.1057), (158.3916, 93.2514)])
drop(SDA, B, [(153.4058, 72.1), (154.0016, 71.5043), (154.0016, 70.5243), (154.7758, 69.75), (156.3516, 69.75),
              (157.0116, 70.41), (157.0116, 72.15), (158.0916, 73.23), (158.0916, 91.7)])

# 3. the antenna: 0.16 mm along its axis, away from the board's corner
p1, p2 = pad("AE1", "1")[0], pad("AE1", "2")[0]
ax = ((p1[0] - p2[0]) / 8.0, (p1[1] - p2[1]) / 8.0)
at = mm(ae.GetPosition())
ae.SetPosition(v(at[0] + 0.16 * ax[0], at[1] + 0.16 * ax[1]))
ae.Reference().SetVisible(False)
ae.SetLocked(True)
feed_poly = ae.FindPadByNumber("1").GetEffectivePolygon(F, pcbnew.ERROR_INSIDE).Outline(0)
PAD1 = [mm(feed_poly.CPoint(i)) for i in range(feed_poly.PointCount())]
pad_w, pad_s = min(p[0] for p in PAD1), max(p[1] for p in PAD1)        # west edge, south edge
FEED_Y = round(pad("AE1", "1")[0][1] - 0.25, 2)
print("AE1 pad 1: west edge %.3f, south edge %.3f, feed at y %.2f" % (pad_w, pad_s, FEED_Y))

# 4. the matching parts and the feed
place("L4", round(pad_w - 1.1, 2), FEED_Y, 180)
place("L5", 154.1716, FEED_Y - 0.485, 90)
place("C86", 153.29, 69.0025, 180)          # its courtyard clear of U18's
l41, l42, l51, l52 = pad("L4", "1")[0], pad("L4", "2")[0], pad("L5", "1")[0], pad("L5", "2")[0]
c861, c862, u1811 = pad("C86", "1")[0], pad("C86", "2")[0], pad("U18", "11")[0]
assert near(l51, (154.1716, FEED_Y)) and l41[0] > l42[0] and c861[0] > c862[0], (l41, l42, l51, c861, c862)
track(ANT, F, 0.5, [l41, (pad_w + 0.4, FEED_Y)])
track(TEE, F, 0.5, [l42, l51])
ra = l51[0] - c861[0]                        # the feed turns into C86 on a quarter circle, as it turned into the old run
track(TEE, F, 0.25, [l51, (l51[0], c861[1] - ra)])
bend = pcbnew.PCB_ARC(b)
bend.SetStart(v(l51[0], c861[1] - ra))
bend.SetMid(v(c861[0] + ra / R2, c861[1] - ra + ra / R2))
bend.SetEnd(v(*c861))
bend.SetWidth(int(0.25e6))
bend.SetLayer(F)
bend.SetNet(net(TEE))
bend.SetLocked(True)
b.Add(bend)
track(RF, F, 0.25, [c862, u1811])
L5_GND = (153.55, round(l52[1], 4))
track("GND", F, 0.3, [l52, L5_GND])
via("GND", L5_GND, 0.45, 0.2)
via("GND", (153.4616, 69.75), 0.45, 0.2)        # beside the feed, where v2 had its fourth one

# 5. the clear area: 2 mm from pad 1 for everything but the feed
s_pad = min(p[0] - p[1] for p in PAD1)                  # the pad's south-west corner
KO_S = s_pad - (CLEAR + 0.01) * R2                      # chamfer of the rule area
KO_Y = round(pad_s + CLEAR + 0.02, 2)                   # its south edge east of the chamfer
rho_ko = (KO_S - (HOLE[0] - HOLE[1])) / R2              # how far the chamfer passes from the screw hole's centre
print("rule area: chamfer %.3f mm from the hole's centre (copper may start at 1.22), south edge y %.2f" % (rho_ko, KO_Y))
zone = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName() == "gnss-antenna"]
assert len(zone) == 1
old = [mm(zone[0].Outline().Outline(0).CPoint(i)) for i in range(zone[0].Outline().Outline(0).PointCount())]
assert len(old) == 6 and near(old[3], (154.39, 68.81), 0.01) and near(old[4], (154.39, 59.0), 0.01), old
east = old[0][0] + (KO_Y - old[0][1]) * 0.0262          # the east side follows the board edge
KO = [(round(east, 3), KO_Y), on(KO_S, y=KO_Y), on(KO_S, y=68.81), old[3], old[4], old[5]]
o = zone[0].Outline()
o.RemoveAllContours()
o.NewOutline()
for x, y in KO:
    o.Append(int(round(x * 1e6)), int(round(y * 1e6)))
zone[0].HatchBorder()
via("GND", (161.3, round(KO_Y + 0.27, 2)), 0.5, 0.3)    # the stitching via east of the holder wall, moved out of the 2 mm

# 6. LED4, as LED1 lies
place("LED4", 158.80, 71.90, 0)
A, Bp, G, Rp = (pad("LED4", n)[0] for n in "1234")
assert near(A, (158.00, 71.60)) and near(Bp, (159.60, 71.60)) and near(G, (159.60, 72.20)) and near(Rp, (158.00, 72.20)), (A, Bp, G, Rp)
assert [pad("LED4", n)[1] for n in "1234"] == [P33, led("B"), led("G"), led("R")]
VA, VG, VR = (158.80, 71.60), (158.80, 72.20), (158.70, 72.80)      # anode and green under the LED, red south of it

# 7. F.Cu: the UART pair, diagonals 0.1 mm nearer the hole
for name, run in ((RX, RX_OLD), (TX, TX_OLD)):
    s = run[1][0] - run[1][1] - 0.1 * R2
    track(name, F, rx_w, [run[0], on(s, y=run[1][1]), on(s, x=run[2][0]), run[3]])

# 8. In2. North of the hole, from the inside out: LED_4_R on Pack+'s old lane, LED_4_G on LED_4_R's, +3.3V outside.
low = ring_s(CUT, 1.79)                                               # 0.15 mm lines 0.2 mm from the cut-out's corner
track(PACK, IN2, W, [PACK_OLD[0], (PACK_OLD[0][0] + 0.16, 72.48), on(low, y=72.48), on(low, x=PACK_OLD[-1][0])])
track(PACK, IN2, 0.2, [on(low, x=PACK_OLD[-1][0]), PACK_OLD[-1]])
pack_sum = PACK_OLD[1][0] + PACK_OLD[1][1]                            # x + y of the run up to the neck
track(led("R"), IN2, W, R_OLD[:2] + [(pack_sum - 70.95, 70.95)] + PACK_OLD[1:5]
      + [(PACK_OLD[4][0] + 72.80 - PACK_OLD[4][1], 72.80), VR])
r_sum = R_OLD[3][0] + R_OLD[3][1]
track(led("G"), IN2, W, [(153.2, 70.5301), (r_sum - 70.5301, 70.5301)] + R_OLD[3:6]
      + [(R_OLD[5][0], 71.45), (R_OLD[5][0] + 0.55, 72.00), (VG[0] - 0.20, 72.00), VG])
r_rho = (R_OLD[5][0] - R_OLD[5][1] - (HOLE[0] - HOLE[1])) / R2        # LED_4_R's old diagonal, now LED_4_G's
a_s, a_y = ring_s(HOLE, r_rho + W + GAP), R_OLD[4][1] - W - GAP
A_N = round(KO_Y + 0.16, 2)                                           # the anode's line north of LED4
assert r_rho + W + GAP + W / 2 <= rho_ko, (r_rho, rho_ko)
track(P33, IN2, W, [(153.80, a_y), on(a_s, y=a_y), on(a_s, y=A_N), (VA[0] - (VA[1] - A_N), A_N), VA])
for name, at_ in ((led("G"), VG), (led("R"), VR), (P33, VA)):
    via(name, at_)
track(P33, B, 0.2, [VA, A])
track(led("G"), B, W, [VG, G])
track(led("R"), B, W, [VR, (Rp[0] + 0.25, Rp[1] + 0.15)])

# 9. B.Cu round the hole: SCL, LED_4_B, PRTRG from the inside out
rho_p = rho_ko - 0.01 - W / 2
rho_b = rho_p - W - GAP
rho_s = rho_b - W - GAP
assert rho_s - W / 2 >= 1.02 + 0.22, rho_s
sp, sb, ss = ring_s(HOLE, rho_p), ring_s(HOLE, rho_b), ring_s(HOLE, rho_s)
Y_P, Y_B, Y_S = 69.02, 69.30, 69.58                                  # straight part north of the hole
N_P = round(KO_Y + 0.10, 2)                                          # PRTRG north of LED4, its edge on the rule area
N_B = round(N_P + 0.1 + GAP + W / 2, 2)                              # LED_4_B south of it
assert A[1] - 0.2 - (N_B + W / 2) >= 0.15, N_B                       # clear of LED4's north pads
# PRTRG: north of LED4, down east of it, back to its via. 0.15 wide while LED_4_B runs beside its bend.
PX = 160.40
track(PRTRG, B, 0.2, [(154.52, 69.02), on(sp, y=Y_P)])
track(PRTRG, B, W, [on(sp, y=Y_P), on(sp, y=N_P), (158.10, N_P)])
track(PRTRG, B, 0.2, [(158.10, N_P), (PX - 0.25, N_P), (PX, N_P + 0.25), (PX, 74.65), (159.60, 75.45), (158.95, 75.45)])
# LED_4_B: from its lane straight to the LED
track(led("B"), B, 0.12, [(153.01, 68.75), (153.01 + Y_B - 68.75, Y_B)])
track(led("B"), B, W, [(153.01 + Y_B - 68.75, Y_B), on(sb, y=Y_B), on(sb, y=N_B), (Bp[0] - 0.25, N_B), (Bp[0], N_B + 0.25), Bp])
# SCL: west of LED4, then between its corner and the cut-out
SX = 156.85
s_low = ring_s(CUT, 2.10)
track(SCL, B, 0.2, [(153.7016, 70.4), (153.7016 + 70.4 - Y_S, Y_S), (155.50, Y_S)])
track(SCL, B, W, [(155.50, Y_S), on(ss, y=Y_S), on(ss, x=SX), (SX, 70.95)])
track(SCL, B, 0.2, [(SX, 70.95), on(s_low, x=SX), on(s_low, x=158.3916), (158.3916, 93.2514)])
# SDA: south of the hole, then inside SCL round the cut-out
track(SDA, B, W, [(153.4058, 72.1), (153.7858, 72.48), on(low, y=72.48), on(low, x=158.0916)])
track(SDA, B, 0.2, [on(low, x=158.0916), (158.0916, 91.7)])

# 10. R-V3-33: U14 pad 3 on copper, USB1's ground via out of the pad
u143 = pad("U14", "3")
assert u143[1] == "GND" and near(u143[0], (142.2816, 134.53)) and pad("C57", "1")[1] == "GND"
track("GND", F, 0.2, [u143[0], (142.75, 134.53), (143.05, 134.83)])
usb = pad("USB1", "A1B12")
assert usb[1] == "GND" and near(usb[0], (149.8616, 130.6875))
UV = (149.56, 132.23)
track("GND", F, 0.2, [(149.72, 131.15), (149.52, 131.35), (149.52, 132.19), UV])
via("GND", UV)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())

# 11. nothing but the feed and L4 within 2 mm of AE1's pads
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


OWN = (ANT, TEE, RF)
worst = (99, "")
for num in "12":
    poly = ae.FindPadByNumber(num).GetEffectivePolygon(F, pcbnew.ERROR_INSIDE).Outline(0)
    ring = [mm(poly.CPoint(i)) for i in range(poly.PointCount())]
    for t in b.GetTracks():
        if t.GetNetname() in OWN:
            continue
        if t.GetClass() == "PCB_VIA":
            d, what = ring_d(ring, mm(t.GetPosition()), mm(t.GetPosition())) - t.GetWidth(F) / 2e6, "via"
        else:
            d, what = ring_d(ring, mm(t.GetStart()), mm(t.GetEnd())) - t.GetWidth() / 2e6, "track"
        if d < worst[0]:
            worst = (d, f"{what} {t.GetNetname()} {b.GetLayerName(t.GetLayer())} near pad {num}")
    for z in b.Zones():
        if z.GetIsRuleArea():
            continue
        for layer in (F, IN1, IN2, B):
            if not z.IsOnLayer(layer) or not z.HasFilledPolysForLayer(layer):
                continue
            fill = z.GetFilledPolysList(layer)
            for i in range(fill.OutlineCount()):
                c = fill.Outline(i)
                pts = [mm(c.CPoint(k)) for k in range(c.PointCount())]
                pts = [p for p in pts if abs(p[0] - 160) < 8 and abs(p[1] - 66) < 8]
                for a, z_ in zip(pts, pts[1:]):
                    if math.hypot(a[0] - z_[0], a[1] - z_[1]) > 3:
                        continue                                    # two points far apart are not neighbours here
                    d = ring_d(ring, a, z_)
                    if d < worst[0]:
                        worst = (d, f"pour {z.GetNetname()} {b.GetLayerName(layer)} near pad {num}")
    for f in b.GetFootprints():
        if f.GetReference() in ("AE1", "L4"):
            continue
        for q in f.Pads():
            if q.GetNetname() in OWN:
                continue
            c = mm(q.GetBoundingBox().GetCenter())
            if abs(c[0] - 160) > 8 or abs(c[1] - 66) > 8:
                continue
            qp = q.GetEffectivePolygon(F if q.IsOnLayer(F) else B, pcbnew.ERROR_INSIDE).Outline(0)
            qr = [mm(qp.CPoint(i)) for i in range(qp.PointCount())]
            d = min(ring_d(ring, qr[i], qr[(i + 1) % len(qr)]) for i in range(len(qr)))
            if d < worst[0]:
                worst = (d, f"pad {f.GetReference()}.{q.GetNumber()} near pad {num}")
print("nearest copper of another net to AE1's pads: %.3f mm (%s)" % worst)
if worst[0] < CLEAR - 0.005:
    raise SystemExit("copper inside the 2 mm of the antenna pads: not saved")

b.Save(sys.argv[1])
print("saved")
