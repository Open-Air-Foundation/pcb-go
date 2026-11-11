"""R-V3-26 on the board: the CO AFE on its own 3.0 V rail. Runs under KiCad's Python after pcb_import put U24, C84
and C85 on the board (staged off the outline) and moved the block's +3.3V pads and their copper to VDD_CO.

Layout:
- Everything of the block that hung on +3.3V keeps its copper; only the net changes. Two islands come out of that:
  north (U22 VDD and VREF, C76, R70, the B.Cu link under U22) and south (U23, C79, R72, the B.Cu trunk y 100.75).
  They used to meet through the In2 +3.3V plane, so they now get two In2 tracks from U24's output via.
- U24 sits in the pocket north of U22, the only free copper next to Pack+ (In2, y 94.12). B.Cu under that pocket is
  the 1.25 mm BAT+ track (y 94.37-95.62), so a via only fits at y >= 95.85: U24 is turned with OUT to the south-east,
  its via at (156.95, 95.96), and IN/EN to the west where Pack+ arrives.
- Pack+ leaves In2 through a via at (152.3, 95.1) in the 1.06 mm strip between MCU_RX and CO_VOUT, passes C84
  and runs along that strip to U24. C84's ground pad uses the GND via that was already at (149.90, 95.27).
- C85 lies east of U24, above C76 and clear of U22's courtyard. Ground of U24 and C85 goes over C85 to C76's ground
  pad, which the track from U22 pin 7 into the exposed pad already ties to the plane.
- No RC at U22 VREF: on F.Cu C77 and R69 sit 0.5 mm apart at pin 11 and B.Cu there is under the sensor body.
- All of the block is not fitted (pcb_import set the attribute; checked here). TP footprints that pcb_import
  re-adds are dropped, as in eco_2026-11-11.py.
"""
import math
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
F, B, IN2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu
TOL = 0.02
VDD, PACK = "VDD_CO", "Pack+"


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


if b.FindFootprintByReference("U24").GetPosition().x < int(170e6):
    raise SystemExit("already applied (U24 is on the board)")
for ref, num in (("U22", "6"), ("U22", "11"), ("C76", "1"), ("R70", "2"), ("U23", "1"), ("U23", "4"), ("U23", "8"),
                 ("C79", "1"), ("R72", "1"), ("U24", "1"), ("C85", "1")):
    if pad(ref, num)[1] != VDD:
        raise SystemExit(f"{ref}.{num} is not on {VDD}: run pcb_import with the R-V3-26 schematic first")
for ref in ("U22", "U23", "U24", "C76", "C77", "C79", "C80", "C81", "C84", "C85", "R69", "R70", "R71", "R72", "R73"):
    assert b.FindFootprintByReference(ref).IsDNP(), ref

# 1. test points pcb_import brought back
tps = [f for f in b.GetFootprints() if f.GetReference().startswith("TP")]
for f in tps:
    b.Delete(f)
print("removed", len(tps), "TP footprints")


# 2. pcb_import already moved the block's old +3.3V copper to VDD_CO with its pads: check it took all of it
VIA_B, VIA_C = (153.05, 97.90), (154.20, 100.75)
old = [t for t in b.GetTracks() if t.GetNetname() == VDD]
assert len(old) == 28, len(old)
for at in ((159.75, 96.90), VIA_B, VIA_C, (152.60, 103.10)):
    assert any(t.GetClass() == "PCB_VIA" and near(mm(t.GetPosition()), at) for t in old), at

# 3. placement
PLACE = {"U24": (156.80, 95.10, 180), "C84": (151.05, 95.10, 180), "C85": (158.60, 95.00, 0)}
for ref, (x, y, rot) in PLACE.items():
    fp = b.FindFootprintByReference(ref)
    fp.SetPosition(v(x, y))
    fp.SetOrientationDegrees(rot)
    fp.SetLocked(True)
    fp.Reference().SetVisible(False)   # labels come from the pcb_silk pass
EXPECT = {"U24.1": ((157.23, 95.42), VDD), "U24.2": ((157.23, 94.78), "GND"), "U24.3": ((156.37, 94.78), PACK),
          "U24.4": ((156.37, 95.42), PACK), "U24.5": ((156.80, 95.10), "GND"),
          "C84.1": ((151.53, 95.10), PACK), "C84.2": ((150.57, 95.10), "GND"),
          "C85.1": ((158.12, 95.00), VDD), "C85.2": ((159.08, 95.00), "GND"),
          "C76.2": ((158.90, 96.17), "GND"), "U22.7": ((157.71, 96.40), "GND"), "U22.15": ((155.80, 97.90), "GND")}
for k, want in EXPECT.items():
    got = pad(*k.split("."))
    assert near(got[0], want[0]) and got[1] == want[1], (k, got)


# 4. routing helpers
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


def split(netname, layer, a, z, at):
    """Cut the existing track a-z at the point `at`, so a branch can join it end to end."""
    hit = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetNetname() == netname and t.GetLayer() == layer
           and sorted(near(mm(e), q) for e in (t.GetStart(), t.GetEnd()) for q in (a, z)) == [0, 0, 1, 1]]
    assert len(hit) == 1, (netname, a, z, len(hit))
    t = hit[0]
    width, s, e = t.GetWidth() / 1e6, mm(t.GetStart()), mm(t.GetEnd())
    b.Delete(t)
    track(netname, layer, width, [s, at])
    track(netname, layer, width, [at, e])


# 5. Pack+ from In2 to U24
VP = (152.30, 95.10)
split(PACK, IN2, (147.3516, 94.12), (156.1316, 94.12), (VP[0], 94.12))
track(PACK, IN2, 0.2, [(VP[0], 94.12), VP])
via(PACK, *VP)
track(PACK, F, 0.15, [(151.53, 95.10), VP, (156.20, 95.10)])
track(PACK, F, 0.15, [(156.20, 94.78), (156.20, 95.10), (156.20, 95.42)])    # EN and IN, west of the thermal pad
track("GND", F, 0.2, [(150.57, 95.10), (150.07, 95.10), (149.9016, 95.27)])  # C84 to the via that was there

# 6. U24 output: C85, the via, and the two In2 tracks that replace the +3.3V plane
VO = (156.95, 95.96)
track(VDD, F, 0.2, [(157.23, 95.42), (157.23, 95.68), VO])
via(VDD, *VO)
track(VDD, F, 0.2, [(157.23, 95.42), (157.70, 95.42), (157.95, 95.17)])
track(VDD, IN2, 0.2, [VO, (156.95, 97.20)])
track(VDD, IN2, 0.2, [(156.95, 97.20), (156.95, 97.70), (154.85, 99.80), (154.85, 100.10), VIA_C])
track(VDD, IN2, 0.2, [(156.95, 97.20), (153.75, 97.20), VIA_B])

# 7. ground of U24 and C85
track("GND", F, 0.15, [(157.23, 94.78), (157.12, 94.78), (156.80, 95.10)])
track("GND", F, 0.15, [(157.23, 94.78), (157.23, 94.62), (157.40, 94.45), (158.84, 94.45), (159.08, 94.69), (159.08, 95.00)])
track("GND", F, 0.2, [(159.08, 95.00), (159.08, 95.50), (158.90, 95.68), (158.90, 96.17)])

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
print("saved")
