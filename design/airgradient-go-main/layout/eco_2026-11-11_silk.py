"""Silk labels for the parts v3 added or moved (2026-11-11). Runs under KiCad's Python.

The board's labels were placed by hand for v2 (0.5 mm high, 0.1 mm stroke) and stay as they are. The parts
that came or moved since had their references hidden. Two steps:

  eco_2026-11-11_silk.py BOARD --keep     prints the references that are on silk now, and the logo footprints
  pcb_silk.py BOARD --size 0.5 --thickness 0.1 --keep <that list>
  eco_2026-11-11_silk.py BOARD            the five labels pcb_silk put on top of a kept label or an edge

pcb_silk places 27 labels (AE1, C65, C76, C77, C79 to C82, C85, C86, L4, L5, LED1 to LED4, NT1, Q6, R27, R68 to
R71, R74, R75, U22, U23) and finds no room for C75, C84, R72, R73 and U24, which stay on the Fab layer only.
It does not see kept labels as obstacles, so:
- Q6 lands on R17 and R20: it goes to the free space west of the part.
- R75 lands on the O-Ring box: it goes above its part.
- C65 touches C68's label, U23 reaches the slot beside it, C79 lies on R32's label: hidden again (Fab only).
  U23 and C79 belong to the CO block, which is not fitted.
"""
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
SILK = (pcbnew.F_SilkS, pcbnew.B_SilkS)
MOVE = {"Q6": (114.25, 94.45), "R75": (144.50, 104.45)}
HIDE = ("C65", "C79", "U23")


def on_silk(f):
    r = f.Reference()
    return r.IsVisible() and r.GetLayer() in SILK


if "--keep" in sys.argv:
    refs = {f.GetReference() for f in b.GetFootprints() if f.GetReference() and (on_silk(f) or "*" in f.GetReference())}
    print(",".join(sorted(refs)))
    sys.exit()

for ref in list(MOVE) + list(HIDE) + ["R74", "LED4", "L4"]:
    f = b.FindFootprintByReference(ref)
    if not f or not on_silk(f):
        raise SystemExit(f"{ref} has no label on silk: run pcb_silk.py first (see the top of this file)")
for ref, (x, y) in MOVE.items():
    r = b.FindFootprintByReference(ref).Reference()
    r.SetPosition(pcbnew.VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6))))
    r.SetTextAngleDegrees(0)
for ref in HIDE:
    b.FindFootprintByReference(ref).Reference().SetVisible(False)
b.Save(sys.argv[1])
print("moved", ", ".join(MOVE), "| hidden", ", ".join(HIDE))
