"""R-V3-17 CO sensor AFE on the board. Runs under KiCad's Python after pcb_import put U22, U23, R69, R70,
C76, C77, C79 on the board (staged off the outline) and set U11.1-3 to CO_RE / CO_S / CO_CE.

Layout (SNIS163B §10: the LMP91002 sits over the sensor):
- U22 LMP91002 on F.Cu at (155.8, 97.9), rot 90, right over the ES1 body (U11 is on B.Cu), analog side
  (VOUT..CE) facing U11's pins at x 150.6. WE -> R69 -> U11.2 and CE -> U11.3 on F.Cu; RE crosses to B.Cu
  and reaches U11.1 from the south-east (U22's CE-RE-WE order cannot meet U11's RE-S-CE order on one layer).
- C77 (TIA C1-C2) and the VREF via hug U22's west pads; C76 decouples VDD to AGND on the east pads, R70
  pulls MENB up beside it. The AFE runs on +3.3V: In2 under the pocket is the +3.3V plane, so VREF, C76 and
  R70 take it through one via each.
- U23 ADS1115 on F.Cu at (148.2, 101.6), rot 270, west of U11's pins below the board slot. VOUT runs on
  F.Cu north of U11.1, down between the slot and U11.1, and along the 0.15 mm lane under the slot to AIN1.
  In2 under U23 is SYS/VBUS, so its +3.3V comes on B.Cu from a pocket via, under U11 between pins 2 and 3.
  C79 sits south of EEPA's B.Cu run and reaches U23's VDD lead on B.Cu.
- SDA/SCL: the F.Cu run from the strip vias to the vias at (153.4, 104.34) / (156.05, 103.6) moves to In2
  inside the pocket; U22 taps it through vias east of U22, U23 the B.Cu runs south of it.
- CO_MENB: U22.2 / R70.1 -> via -> B.Cu west under U22, U11 (pins 2-3) and the ePaper/GNSS lanes ->
  F.Cu hop over EEPA at x 142 -> B.Cu via at (142.0, 102.3); the rest to U17.10 is the menb-tail route.
- Room: PRTRG's F.Cu run moves 1.3 mm east in the pocket (x 160.45, 0.25 mm off the board notch); five GND
  stitching vias in the pocket go (re-stitched by the stitch pass).
- pcb_import re-adds the TP footprints the board never carried: drop every TP*.
"""
import math
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
F, B = pcbnew.F_Cu, pcbnew.B_Cu
IN2 = b.GetLayerID("PWR")
TOL = 0.02
P33 = "+3.3V"


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


if b.FindFootprintByReference("U22").GetPosition().x < int(170e6):
    raise SystemExit("already applied (U22 is on the board)")
if b.FindFootprintByReference("U22").FindPadByNumber("6").GetNetname() != P33:
    raise SystemExit("U22.6 is not on +3.3V: run pcb_import with the +3.3V schematic first")

# ---------------------------------------------------------------- 1. removals
tps = [f for f in b.GetFootprints() if f.GetReference().startswith("TP")]
for f in tps:
    b.Delete(f)
print("removed", len(tps), "TP footprints")


def tracks_between(netname, layer, a, z):
    """Every track of a chain on one layer from point a to point z (inclusive)."""
    segs = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetNetname() == netname
            and t.GetLayer() == layer]
    chain, cur = [], a
    while not near(cur, z):
        nxt = [t for t in segs if t not in chain and (near(mm(t.GetStart()), cur) or near(mm(t.GetEnd()), cur))]
        if len(nxt) != 1:
            raise SystemExit(f"{netname}: {len(nxt)} tracks at {cur}")
        t = nxt[0]
        chain.append(t)
        cur = mm(t.GetEnd()) if near(mm(t.GetStart()), cur) else mm(t.GetStart())
    return chain


gone = []
gone += tracks_between("/SDA", F, (157.43, 93.94), (153.4, 104.34))
gone += tracks_between("/SCL", F, (158.14, 93.51), (156.05, 103.6))
gone += tracks_between("/PRTRG", F, (159.15, 73.3), (159.15, 102.66))
STITCH = [(160.02, 95.71), (160.0, 99.0), (160.0, 102.17), (156.73, 96.27), (156.31, 99.59)]
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA" and t.GetNetname() == "GND" and any(near(mm(t.GetPosition()), p) for p in STITCH):
        gone.append(t)
assert len(gone) == 6 + 5 + 1 + len(STITCH), len(gone)
for g in gone:
    b.Delete(g)
print("removed", len(gone), "tracks and vias")

# ---------------------------------------------------------------- 2. placement
PLACE = {  # ref: (x, y, rot)
    "U22": (155.8, 97.9, 90),
    "C77": (152.6, 96.75, 90),
    "R69": (151.95, 98.4, 180),
    "C76": (158.9, 96.65, 90),
    "R70": (159.75, 98.6, 90),
    "U23": (148.2, 101.6, 270),
    "C79": (151.4, 103.1, 180),
}
for ref, (x, y, rot) in PLACE.items():
    fp = b.FindFootprintByReference(ref)
    fp.SetPosition(v(x, y))
    fp.SetOrientationDegrees(rot)
    fp.SetLocked(True)
    fp.Reference().SetVisible(False)   # labels come from the pcb_silk pass

PAD = {}
for ref in PLACE:
    for p in b.FindFootprintByReference(ref).Pads():
        PAD[f"{ref}.{p.GetNumber()}"] = (mm(p.GetPosition()), p.GetNetname())
EXPECT = {"U22.8": (153.89, 96.4), "U22.14": (153.89, 99.4), "U22.7": (157.71, 96.4), "U22.1": (157.71, 99.4),
          "U23.5": (147.2, 99.45), "U23.1": (149.2, 99.45), "U23.6": (147.2, 103.75), "U23.10": (149.2, 103.75),
          "C77.1": (152.6, 97.23), "R69.1": (152.46, 98.4), "C76.1": (158.9, 97.13), "C79.1": (151.88, 103.1),
          "R70.1": (159.75, 99.11), "R70.2": (159.75, 98.09)}
for k, p in EXPECT.items():
    assert near(PAD[k][0], p), (k, PAD[k])
for k in ("U22.6", "U22.11", "U23.1", "U23.4", "U23.8", "C76.1", "C79.1", "R70.2"):
    assert PAD[k][1] == P33, (k, PAD[k][1])

# ---------------------------------------------------------------- 3. routing helpers
SENSE = 0.15


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


WE, C1, C2 = "Net-(U22-WE)", "Net-(U22-C1)", "Net-(U22-C2)"

# ---------------------------------------------------------------- 4. U22 analog side (west)
# VOUT: north, west above C77 and U11.1, down between the slot and U11.1, along the lane to U23 AIN1
track("/CO_VOUT", F, SENSE, [(153.89, 96.4), (153.89, 95.9), (153.69, 95.7), (149.84, 95.7), (149.64, 95.9),
                             (149.64, 98.3), (149.44, 98.5), (147.4, 98.5), (147.2, 98.7), (147.2, 99.45)])
track(C2, F, SENSE, [(153.89, 96.9), (153.29, 96.9), (152.66, 96.27), (152.6, 96.27)])
track(C1, F, SENSE, [(153.89, 97.4), (152.77, 97.4), (152.6, 97.23)])
track(P33, F, SENSE, [(153.89, 97.9), (153.05, 97.9)])                            # VREF to the In2 plane
via(P33, 153.05, 97.9, 0.4, 0.2)
track(WE, F, SENSE, [(153.89, 98.4), (152.46, 98.4)])
track("/CO_S", F, SENSE, [(151.44, 98.4), (150.6, 99.24), (150.6, 99.4)])
track("/CO_RE", F, SENSE, [(153.89, 98.9), (153.05, 98.9)])
via("/CO_RE", 153.05, 98.9, 0.4, 0.2)
track("/CO_RE", B, SENSE, [(153.05, 98.9), (151.4, 97.25), (151.01, 96.86), (150.6, 96.86)])
track("/CO_CE", F, SENSE, [(153.89, 99.4), (153.4, 99.4), (151.06, 101.74), (150.86, 101.94), (150.6, 101.94)])

# ---------------------------------------------------------------- 5. U22 digital side (east) and ground
track("GND", F, 0.2, [(157.71, 96.4), (156.9, 96.4)])                             # AGND to EP
track("GND", F, 0.2, [(157.71, 99.4), (156.9, 99.4)])                             # DGND to EP
track("GND", F, 0.2, [(157.71, 96.4), (158.66, 96.4), (158.9, 96.16)])           # AGND to C76.2
track(P33, F, 0.2, [(157.71, 96.9), (158.67, 96.9), (158.9, 97.13)])             # VDD to C76.1
track(P33, F, 0.2, [(158.9, 97.13), (159.52, 97.13), (159.75, 96.9)])
via(P33, 159.75, 96.9)
track(P33, F, 0.2, [(159.75, 96.9), (159.75, 98.09)])                             # R70.2
track("GND", F, 0.2, [(155.5, 99.3), (155.5, 100.1)])                             # EP vias
via("GND", 155.5, 100.1)
track("GND", F, 0.2, [(155.5, 96.5), (155.5, 95.95)])
via("GND", 155.5, 95.95, 0.4, 0.2)
track("/SDA", F, 0.15, [(157.71, 97.9), (158.35, 97.9)])
via("/SDA", 158.35, 97.9, 0.4, 0.2)
track("/SCL", F, 0.15, [(157.71, 98.4), (158.7, 98.4), (158.85, 98.55)])
via("/SCL", 158.85, 98.55, 0.4, 0.2)
track("/CO_MENB", F, 0.15, [(157.71, 98.9), (157.86, 99.05), (159.69, 99.05), (159.75, 99.11)])
track("/CO_MENB", F, 0.15, [(159.75, 99.11), (159.75, 99.8), (159.6, 99.95)])
via("/CO_MENB", 159.6, 99.95)

# ---------------------------------------------------------------- 6. U23
track("GND", F, 0.2, [(148.2, 99.45), (148.2, 101.75), (147.45, 102.5)])          # pin 3
track("GND", F, 0.2, [(147.2, 103.75), (147.2, 102.75), (147.45, 102.5)])         # pin 6
track("GND", F, 0.2, [(147.7, 103.75), (147.7, 102.75), (147.45, 102.5)])         # pin 7
via("GND", 147.45, 102.5, 0.4, 0.2)
track(P33, F, 0.15, [(147.7, 99.45), (147.7, 100.75)])                            # AIN0
via(P33, 147.7, 100.75, 0.4, 0.2)
track(P33, F, 0.15, [(149.2, 99.45), (149.2, 100.75)])                            # ADDR
via(P33, 149.2, 100.75, 0.4, 0.2)
track(P33, F, 0.2, [(148.2, 103.75), (148.2, 102.4), (149.2, 101.4), (149.2, 100.75)])   # VDD to ADDR
via(P33, 148.7, 101.9, 0.4, 0.2)                                                  # C79 link lands here
track("/SDA", F, 0.15, [(148.7, 103.75), (148.7, 104.8), (149.0, 105.1)])
via("/SDA", 149.0, 105.1, 0.4, 0.2)
track("/SDA", B, 0.2, [(149.0, 105.1), (152.64, 105.1)])                          # onto the B.Cu SDA run
track("/SCL", F, 0.15, [(149.2, 103.7), (149.75, 103.7)])
via("/SCL", 149.75, 103.7, 0.4, 0.2)                                              # on the B.Cu SCL run
track(P33, F, 0.2, [(151.88, 103.1), (152.6, 103.1)])                             # C79.1
via(P33, 152.6, 103.1, 0.4, 0.2)

# ---------------------------------------------------------------- 7. B.Cu: +3.3V to U23 and C79, CO_MENB
# The In2 SDA run and Pack+ wall the pocket's west part off from the rest of the In2 +3.3V plane; this B.Cu
# link ties the VREF via (and through that island the U23 feed) to the via beside C76.
track(P33, B, 0.2, [(153.05, 97.9), (153.75, 97.2), (159.45, 97.2), (159.75, 96.9)])
via(P33, 154.2, 100.75)                                                           # In2 +3.3V
track(P33, B, 0.2, [(154.2, 100.75), (147.7, 100.75)])
track(P33, B, 0.2, [(152.6, 103.1), (152.25, 102.75), (149.55, 102.75), (148.7, 101.9)])
track("/CO_MENB", B, 0.15, [(159.6, 99.95), (159.25, 99.6), (153.8, 99.6), (153.25, 100.15), (142.0, 100.15)])
via("/CO_MENB", 142.0, 100.15)
track("/CO_MENB", F, 0.15, [(142.0, 100.15), (142.0, 102.38)])                   # hop over EEPA
via("/CO_MENB", 142.0, 102.38)
# menb-tail to U17.10: found with pcb_path (grid A*, --routed --join-net, 0.15 mm), last leg squared to 45°
track("/CO_MENB", F, 0.15, [(121.96, 129.65), (127.02, 129.65), (128.77, 127.9), (128.77, 125.5), (128.62, 125.35),
                            (128.62, 125.05), (128.92, 124.75), (130.97, 124.75), (131.47, 125.25), (131.47, 125.45),
                            (131.72, 125.7), (133.07, 125.7)])
via("/CO_MENB", 133.07, 125.7)
track("/CO_MENB", B, 0.15, [(133.07, 125.7), (134.22, 125.7), (140.27, 119.65), (140.27, 116.95)])
via("/CO_MENB", 140.27, 116.95)
track("/CO_MENB", F, 0.15, [(140.27, 116.95), (140.27, 113.6)])
via("/CO_MENB", 140.27, 113.6)
track("/CO_MENB", B, 0.15, [(140.27, 113.6), (142.07, 111.8), (143.77, 111.8), (144.02, 111.55), (144.02, 104.4),
                            (142.0, 102.38)])

# the tail cuts two F.Cu GND pour pieces off their stitching (round C14.1/C18.1 and U15.3): one via each
via("GND", 129.06, 128.49)
via("GND", 139.63, 115.58)

# ---------------------------------------------------------------- 8. PRTRG 1.3 mm east in the pocket
track("/PRTRG", F, 0.2, [(159.15, 73.3), (159.15, 93.9), (160.45, 95.2), (160.45, 101.36), (159.15, 102.66)])

# ---------------------------------------------------------------- 9. In2: SDA/SCL across the pocket
track("/SDA", IN2, 0.2, [(157.43, 93.94), (158.35, 94.86), (158.35, 99.4), (153.41, 104.34), (153.4, 104.34)])
track("/SCL", IN2, 0.2, [(158.14, 93.51), (158.85, 94.22), (158.85, 100.8), (156.05, 103.6)])

# ---------------------------------------------------------------- 10. silk: the O-Ring block frame now ends above U23/C79
SHIFT = 104.95 - 102.91
for d in b.GetDrawings():
    if d.GetLayer() != pcbnew.F_SilkS:
        continue
    if d.GetClass() == "PCB_SHAPE" and d.GetShapeStr() == "Rect" and near(mm(d.GetStart()), (145.0, 102.91)):
        d.SetStart(v(145.0, 104.95))                                              # frame top edge under U23
    elif d.GetClass() == "PCB_SHAPE" and near(mm(d.GetEnd()), (152.13, 103.15)):
        d.SetEnd(v(152.13, 104.95))                                               # inner divider
    elif d.GetClass() == "PCB_TEXT" and d.GetText() == "O-Ring":
        x, y = mm(d.GetPosition())
        d.SetPosition(v(x, y + SHIFT))

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
print("saved")
