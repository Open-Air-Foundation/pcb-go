"""R-V3-19..25 on the board. Runs under KiCad's Python after pcb_import put C80-C82 and R71-R75 on the board
(staged off the outline) and moved U4.39/40, C75.2, U23.5 and U23.7 to their new nets.

Layout:
- R-V3-24 CO AFE filters, west of U23 in the 1.9 mm between the UART lane and U23's courtyard, all above the
  O-Ring silk frame (y 104.95). In2 under them is SYS (y 99.0-101.4), the 1.6 mm VBUS strip that carries the
  charger input (y 101.7-103.3) and +3.3V below: nothing here may put a via in the VBUS strip.
  R71 stands at the end of the VOUT lane (y 98.5). Below it four parts lie flat, their pads in two rails:
      west rail  GND    | CO_ZERO | CO_ZERO | CO_ZERO
      east rail  AIN1   | +3.3V   | GND     | GND
                 C80      R72       R73       C81
  +3.3V comes on F.Cu from U23's AIN0 via, so the divider hangs on the supply U23 measures against. R73 and
  C81 return to U23's GND lead (pin 6). CO_ZERO runs down the west rail and along y 104.7 to pin 7. C80's GND
  pad gets the one new via here, 0.4 mm, between the B.Cu BAT+ and CO_MENB runs (In2 there is SYS).
- Room for that: ePaper RES / MCU_TX / MCU_RX turn west below the battery cut-out and run at x 142.70 /
  143.33 / 144.33 (were 145.45 / 145.75 / 146.05).
- R-V3-25 R74/R75 stand in that lane at y 105.9, just north of CN1's silk label; there is no room for them
  at U4. Every track and via from there to U4.39/40 changes net to U0TXD/U0RXD.
- R-V3-20 C82 beside C75, antiparallel: C75.2 to C82.1 is one straight link, C82.2 goes to a GND via. The GND
  via at (159.91, 85.49) sat where C82.1 is now; its replacement is the one at C82.2. C82 also sits on C75's
  silk label, which is hidden like the new parts' until the pcb_silk pass.
- R-V3-21 U16 pads 5-8 end at x 162.73, 0.3 mm inside the board edge they used to cross. The S12 body edge is
  at x 162.62, so the lands still cover the sensor's pads.
- R-V3-19 R35/R46 stay on the board, not fitted (pcb_import set the attribute; checked here).
- pcb_import re-adds the TP footprints the board never carried: drop every TP*.
"""
import math
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
F, B = pcbnew.F_Cu, pcbnew.B_Cu
TOL = 0.02
P33 = "+3.3V"
ZERO, AIN1, MID = "/CO_ZERO", "/CO_AIN1", "Net-(C75-Pad2)"


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


def pad_net(ref, num):
    return b.FindFootprintByReference(ref).FindPadByNumber(num).GetNetname()


if b.FindFootprintByReference("R71").GetPosition().x < int(170e6):
    raise SystemExit("already applied (R71 is on the board)")
for ref, num, want in (("U23", "7", ZERO), ("U23", "5", AIN1), ("C75", "2", MID), ("U4", "39", "/U0TXD"),
                       ("U4", "40", "/U0RXD")):
    if pad_net(ref, num) != want:
        raise SystemExit(f"{ref}.{num} is not on {want}: run pcb_import with the 2026-11-11 schematic first")
for ref in ("R35", "R46"):
    assert b.FindFootprintByReference(ref).IsDNP(), ref

# ---------------------------------------------------------------- 1. removals
tps = [f for f in b.GetFootprints() if f.GetReference().startswith("TP")]
for f in tps:
    b.Delete(f)
print("removed", len(tps), "TP footprints")


def polyline(netname, layer, pts):
    """The existing tracks that draw the polyline pts, one per leg."""
    out = []
    for a, z in zip(pts, pts[1:]):
        hit = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetNetname() == netname
               and t.GetLayer() == layer
               and sorted(near(mm(e), q) for e in (t.GetStart(), t.GetEnd()) for q in (a, z)) == [0, 0, 1, 1]]
        if len(hit) != 1:
            raise SystemExit(f"{netname}: {len(hit)} tracks from {a} to {z}")
        out += hit
    return out


gone = polyline("/CO_VOUT", F, [(147.4, 98.5), (147.2, 98.7), (147.2, 99.45)])    # lane's turn into old AIN1
gone += polyline("GND", F, [(147.7, 103.75), (147.7, 102.75), (147.45, 102.5)])   # pin 7 was grounded
gone += polyline("/ePaper RES", F, [(145.45, 94.62), (145.45, 107.65), (145.084, 108.02), (141.984, 111.12)])
gone += polyline("/MCU_TX", F, [(145.752, 95.04), (145.752, 108.34), (143.502, 110.59), (143.152, 110.59)])
gone += polyline("/MCU_RX", F, [(146.046, 95.162), (146.046, 108.462), (143.71, 110.798)])
old_via = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == "GND"
           and near(mm(t.GetPosition()), (159.912, 85.49))]
assert len(old_via) == 1, len(old_via)
for g in gone + old_via:
    b.Delete(g)
print("removed", len(gone), "tracks and 1 via")

# ---------------------------------------------------------------- 2. U4 side of the UART becomes U0TXD/U0RXD
JOIN = 0.06   # a few track ends sit 0.03 mm off their via centre


def retag(old, new, seed, expect):
    """Tracks and vias of net old that connect to the point seed move to net new."""
    items = [t for t in b.GetTracks() if t.GetNetname() == old]
    ends = [[mm(t.GetPosition())] if t.GetClass() == "PCB_VIA" else [mm(t.GetStart()), mm(t.GetEnd())]
            for t in items]
    reached, front = set(), [seed]
    while front:
        p = front.pop()
        for i, e in enumerate(ends):
            if i not in reached and any(near(q, p, JOIN) for q in e):
                reached.add(i)
                front += e
    assert len(reached) == expect, (old, len(reached))
    for i in reached:
        items[i].SetNet(net(new))
    print(old, "->", new, len(reached), "tracks and vias")


retag("/MCU_TX", "/U0TXD", (113.67, 108.97), 27)
retag("/MCU_RX", "/U0RXD", (112.82, 108.97), 35)

# ---------------------------------------------------------------- 3. placement
PLACE = {  # ref: (x, y, rot)
    "R71": (145.90, 99.01, 270),
    "C80": (145.42, 100.42, 180),
    "R72": (145.45, 101.37, 180),
    "R73": (145.45, 102.33, 0),
    "C81": (145.42, 103.28, 0),
    "R74": (143.33, 105.90, 90),
    "R75": (144.33, 105.90, 270),
    "C82": (160.47, 85.10, 90),
}
for ref, (x, y, rot) in PLACE.items():
    fp = b.FindFootprintByReference(ref)
    fp.SetPosition(v(x, y))
    fp.SetOrientationDegrees(rot)
    fp.SetLocked(True)
    fp.Reference().SetVisible(False)   # labels come from the pcb_silk pass
b.FindFootprintByReference("C75").Reference().SetVisible(False)

PAD = {}
for ref in list(PLACE) + ["C75", "U23"]:
    for p in b.FindFootprintByReference(ref).Pads():
        PAD[f"{ref}.{p.GetNumber()}"] = (mm(p.GetPosition()), p.GetNetname())
EXPECT = {"R71.1": ((145.90, 98.50), "/CO_VOUT"), "R71.2": ((145.90, 99.52), AIN1),
          "C80.1": ((145.90, 100.42), AIN1), "C80.2": ((144.94, 100.42), "GND"),
          "R72.1": ((145.96, 101.37), P33), "R72.2": ((144.94, 101.37), ZERO),
          "R73.1": ((144.94, 102.33), ZERO), "R73.2": ((145.96, 102.33), "GND"),
          "C81.1": ((144.94, 103.28), ZERO), "C81.2": ((145.90, 103.28), "GND"),
          "R74.1": ((143.33, 106.41), "/U0TXD"), "R74.2": ((143.33, 105.39), "/MCU_TX"),
          "R75.1": ((144.33, 105.39), "/MCU_RX"), "R75.2": ((144.33, 106.41), "/U0RXD"),
          "C82.1": ((160.47, 85.58), MID), "C82.2": ((160.47, 84.62), "GND"),
          "C75.2": ((161.40, 85.58), MID), "U23.5": ((147.2, 99.45), AIN1), "U23.6": ((147.2, 103.75), "GND"),
          "U23.7": ((147.7, 103.75), ZERO)}
for k, (p, n) in EXPECT.items():
    assert near(PAD[k][0], p) and PAD[k][1] == n, (k, PAD[k])

# ---------------------------------------------------------------- 4. routing helpers
SENSE, UART = 0.15, 0.194671


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


def at45(p, x, dy=1):
    """The point in column x that a 45-degree leg from p reaches going down (dy=1) or up (dy=-1)."""
    return (x, p[1] + dy * abs(p[0] - x))


# ---------------------------------------------------------------- 5. the lane, moved west below the cut-out
# Ends of the tracks that stay, to the nm: TX and RX leave the corridor exactly 0.1 mm apart, and a new
# track joins an old one only where the two ends coincide.
RES0, RES1 = (145.45, 94.62), (141.984, 111.12)                # corridor end, via
TX0, TX1 = (145.751559, 95.039999), (143.131559, 110.61)       # corridor end, via
RX0, RX1 = (146.04623, 95.162057), (143.709923, 110.798363)    # corridor end, tail to the via
XRES, XTX, XRX = 142.70, 143.33, 144.33
# RES turns first and keeps 0.4 mm of copper-to-edge at the cut-out's corner arc (centre 144.061, 96.852, r 0.5)
res_turn, tx_turn, rx_turn = (RES0[0], 96.85), (TX0[0], 97.05), (RX0[0], 97.26)
track("/ePaper RES", F, SENSE, [RES0, res_turn, at45(res_turn, XRES), at45(RES1, XRES, -1), RES1])
track("/MCU_TX", F, UART, [TX0, tx_turn, at45(tx_turn, XTX), (XTX, 105.39)])
track("/U0TXD", F, UART, [(XTX, 106.41), at45(TX1, XTX, -1), TX1])
track("/MCU_RX", F, UART, [RX0, rx_turn, at45(rx_turn, XRX), (XRX, 105.39)])
track("/U0RXD", F, UART, [(XRX, 106.41), at45(RX1, XRX, -1), RX1])

# ---------------------------------------------------------------- 6. CO AFE filters at U23
track("/CO_VOUT", F, SENSE, [(147.4, 98.5), (145.90, 98.5)])
track(AIN1, F, SENSE, [(147.2, 99.52), (145.90, 99.52), (145.90, 100.42)])
track("GND", F, 0.2, [(144.94, 100.42), (144.94, 99.99), (145.25, 99.68)])       # C80.2
via("GND", 145.25, 99.68, 0.4, 0.2)
track(P33, F, SENSE, [(147.7, 100.75), (147.08, 101.37), (145.96, 101.37)])      # AIN0 via to R72.1
track("GND", F, 0.2, [(145.96, 102.33), (145.96, 103.28), (147.2, 103.28)])      # R73.2, C81.2 to pin 6
track(ZERO, F, SENSE, [(144.94, 101.37), (144.94, 102.33), (144.94, 103.28), (144.94, 104.4), (145.24, 104.7),
                       (147.5, 104.7), (147.7, 104.5), (147.7, 103.75)])

# ---------------------------------------------------------------- 7. C82 in series with C75
track(MID, F, 0.3, [PAD["C75.2"][0], (160.47, PAD["C75.2"][0][1])])
track("GND", F, 0.25, [(160.47, 84.62), (159.85, 84.62)])
via("GND", 159.85, 84.62)

# ---------------------------------------------------------------- 8. U16 pads 5-8 inside the board edge
END, u16 = 162.73, b.FindFootprintByReference("U16")
for num in "5678":
    p = u16.FindPadByNumber(num)
    (x, y), w, h = mm(p.GetPosition()), p.GetSizeX() / 1e6, p.GetSizeY() / 1e6
    assert abs(x - 162.372) < TOL and near((w, h), (2.5, 1.75)), (num, x, w, h)
    left = x - w / 2
    p.SetSize(pcbnew.F_Cu, v(END - left, h))
    p.SetPosition(v((left + END) / 2, y))

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
print("saved")
