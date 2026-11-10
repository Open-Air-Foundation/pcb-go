"""C61 (GNSS antenna match, shunt at the antenna end, DNP) turns round so its GND pad points north.

Why: the battery holder (BT1 model GO_v2.12_26.08.17_2.07.step) has a screw boss of radius 3.02 mm at
(155.47, 71.15) that rests on the top of the board. C61's GND pad reached y 68.97 at x 157.48, 2.97 mm from
the boss centre: 0.05 mm under the boss, and a fitted part's solder fillet would lift the holder.

- C61 from rot -90 at (157.79, 68.21) to rot 90 at (157.79, 67.25), the way C62 sits: pad 1 stays on the
  antenna track at y 67.73, the GND pad moves to y 66.77 (4.5 mm from the boss centre).
- GND: the F.Cu track from the old pad round to the via at (153.46, 69.69) goes; a 0.25 mm track joins the
  new pad to C62's GND pad along y 66.77, 0.52 mm above R45's pads. The via stays as a stitching via.
- The C61 label moves below the part.
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


c61 = b.FindFootprintByReference("C61")
if abs(c61.GetOrientationDegrees() - 90) < 0.1:
    raise SystemExit("already applied")
old_pad = mm(c61.FindPadByNumber("2").GetPosition())
assert near(old_pad, (157.792, 68.689)), old_pad

CHAIN = [(157.792, 68.689), (157.232, 68.689), (156.752, 69.169), (156.712, 69.209), (153.942, 69.209), (153.462, 69.689)]
gone = []
for p, q in zip(CHAIN, CHAIN[1:]):
    hit = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetNetname() == "GND" and t.GetLayer() == F
           and ((near(mm(t.GetStart()), p) and near(mm(t.GetEnd()), q)) or (near(mm(t.GetStart()), q) and near(mm(t.GetEnd()), p)))]
    if len(hit) != 1:
        raise SystemExit(f"GND track {p} {q}: found {len(hit)}")
    gone.append(hit[0])
locked = gone[0].IsLocked()
for t in gone:
    b.Delete(t)

c61.SetPosition(v(157.791559, 67.248715))
c61.SetOrientationDegrees(90)
p1, p2 = mm(c61.FindPadByNumber("1").GetPosition()), mm(c61.FindPadByNumber("2").GetPosition())
assert near(p1, (157.792, 67.729)) and near(p2, (157.792, 66.769)), (p1, p2)
g62 = mm(b.FindFootprintByReference("C62").FindPadByNumber("2").GetPosition())
assert near(g62, (154.172, 66.769)), g62

t = pcbnew.PCB_TRACK(b)
t.SetStart(v(*p2))
t.SetEnd(v(*g62))
t.SetWidth(int(0.25e6))
t.SetLayer(F)
t.SetNet(b.FindNet("GND"))
t.SetLocked(locked)
b.Add(t)

ref = c61.Reference()
ref.SetPosition(v(157.79, 68.75))
ref.SetTextAngleDegrees(0)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
print("saved")
