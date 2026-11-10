"""C78 out, U21 USB ESD on B.Cu, R65 and R66 from B.Cu to F.Cu (they sat under the SPS30).
Runs under KiCad's Python after pcb_import put the parts on the board. Refill zones afterwards."""
import math
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
F, B, I2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu
TOL = 0.02


def v(p):
    return pcbnew.VECTOR2I(int(round(p[0] * 1e6)), int(round(p[1] * 1e6)))


def mm(a):
    return (a.x / 1e6, a.y / 1e6)


def near(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1]) <= TOL


def seg(net, layer, p, q):
    for t in b.GetTracks():
        if t.GetClass() != "PCB_VIA" and t.GetNetname() == net and t.GetLayer() == layer:
            a, e = mm(t.GetStart()), mm(t.GetEnd())
            if (near(a, p) and near(e, q)) or (near(a, q) and near(e, p)):
                return t
    raise SystemExit(f"no track {net} {p} {q}")


def drop(net, layer, p, q):
    b.Delete(seg(net, layer, p, q))


def drop_via(net, p):
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" and t.GetNetname() == net and near(mm(t.GetPosition()), p):
            b.Delete(t)
            return
    raise SystemExit(f"no via {net} {p}")


def add(net, layer, width, pts, locked=False):
    for p, q in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetLocked(locked)
        t.SetStart(v(p))
        t.SetEnd(v(q))
        t.SetWidth(int(round(width * 1e6)))
        t.SetLayer(layer)
        t.SetNet(b.FindNet(net))
        b.Add(t)


def via(net, p):
    t = pcbnew.PCB_VIA(b)
    t.SetViaType(pcbnew.VIATYPE_THROUGH)
    t.SetLayerPair(F, B)
    t.SetPosition(v(p))
    t.SetWidth(500000)
    t.SetDrill(300000)
    t.SetNet(b.FindNet(net))
    b.Add(t)


def trim_end(net, layer, keep, old_end, new_end):
    """Pull a track's old_end back to new_end; keep is its other end."""
    t = seg(net, layer, keep, old_end)
    if near(mm(t.GetStart()), old_end):
        t.SetStart(v(new_end))
    else:
        t.SetEnd(v(new_end))


def place(ref, xy, rot, back=None, text=None):
    f = b.FindFootprintByReference(ref)
    if back is not None and back != f.IsFlipped():
        f.Flip(f.GetPosition(), False)
    f.SetPosition(v(xy))
    f.SetOrientationDegrees(rot)
    t = f.Reference()
    t.SetVisible(True)
    t.SetTextSize(pcbnew.VECTOR2I(500000, 500000))
    t.SetTextThickness(100000)
    if text:
        t.SetPosition(v(text))
    print(ref, b.GetLayerName(f.GetLayer()), [(p.GetNumber(), p.GetNetname(), tuple(round(c, 3) for c in mm(p.GetPosition()))) for p in f.Pads()])
    return f


# C78: bridge is gone, its two stub vias with it
b.Delete(b.FindFootprintByReference("C78"))
drop("GND", F, (108.31, 102.33), (109.1, 102.45))
drop_via("GND", (109.1, 102.45))
drop("/BAT-", F, (108.31, 101.37), (108.31, 100.55))
drop_via("/BAT-", (108.31, 100.55))
drop("/BAT-", B, (108.31, 100.55), (109.1, 99.76))

# R65, R66 on F.Cu
drop("/ePaper MOSI", F, (118.1, 104.85), (118.1, 104.4))
drop("/ePaper MOSI", F, (118.1, 104.4), (117.9, 104.2))
drop("/ePaper MOSI", B, (118.45, 105.2), (118.1, 104.85))
drop("/ePaper MOSI", B, (118.69, 105.2), (118.45, 105.2))
drop_via("/ePaper MOSI", (118.1, 104.85))
drop("/MOSI", B, (120.69, 106.06), (120.84, 105.91))
drop("/MOSI", B, (120.84, 105.91), (120.84, 105.86))
drop("/MOSI", B, (120.84, 105.86), (120.18, 105.2))
drop("/MOSI", B, (120.18, 105.2), (119.71, 105.2))
place("R65", (116.2, 105.2), 180, back=False, text=(116.2, 104.55))
place("R66", (120.65, 107.4), 0, back=False, text=(120.65, 108.1))

# ePaper branch: R65.2 up to the F.Cu run
trim_end("/ePaper MOSI", F, (114.15, 104.2), (117.9, 104.2), (115.29, 104.2))
add("/ePaper MOSI", F, 0.15, [(115.69, 105.2), (115.69, 104.6), (115.29, 104.2)], locked=True)

# MOSI to R65.1: T off the B.Cu riser, one via, F.Cu to the pad
t = seg("/MOSI", B, (118.592, 108.12), (118.592, 106.36))
w = t.GetWidth() / 1e6
trim_end("/MOSI", B, (118.592, 108.12), (118.592, 106.36), (118.592, 106.55))
add("/MOSI", B, w, [(118.592, 106.55), (118.592, 106.36)])
add("/MOSI", B, 0.2, [(118.592, 106.55), (117.95, 106.55)])
via("/MOSI", (117.95, 106.55))
add("/MOSI", F, 0.2, [(117.95, 106.55), (116.71, 105.31), (116.71, 105.2)])

# MOSI to R66.1
trim_end("/MOSI", B, (118.892, 106.06), (120.69, 106.06), (120.02, 106.06))
add("/MOSI", B, 0.2, [(120.02, 106.06), (120.36, 106.4), (120.36, 106.7)])
via("/MOSI", (120.36, 106.7))
add("/MOSI", F, 0.2, [(120.36, 106.7), (120.14, 106.92), (120.14, 107.4)])

# R66.2 to the NAND MOSI run
via("/NAND MOSI", (120.95, 106.82))
add("/NAND MOSI", F, 0.2, [(120.95, 106.82), (121.16, 107.03), (121.16, 107.4)])
add("/NAND MOSI", B, 0.2, [(120.95, 106.82), (120.95, 106.4), (121.29, 106.06), (121.71, 106.06)])

# U21: USB ESD on B.Cu, both lines tapped at a via next to the connector
place("U21", (153.6, 127.9), 0, back=True, text=(153.6, 126.5))
via("/USB_D-", (152.27, 129.03))
add("/USB_D-", B, 0.2, [(152.27, 129.03), (152.27, 127.6), (152.47, 127.4), (152.8875, 127.4)])
add("/USB_D+", B, 0.2, [(153.312, 129.188), (154.1, 128.4), (154.3125, 128.4)])
add("GND", B, 0.25, [(154.3125, 127.4), (154.45, 127.4), (154.85, 127.0)])
via("GND", (154.85, 127.0))

pcbnew.SaveBoard(sys.argv[1], b)
