#!/usr/bin/env python3
"""Review fixes on top of the autorouted v3-reroute board (autorouted tracks live only in the board file).

  $KPY reroute_fixes.py BOARD.kicad_pcb

Every edit names the exact copper it replaces and stops if that copper is not there.
Nets the fill_net.py A* joins afterwards are listed in the closing section of design/requirements.md.
"""
import math
import sys

import pcbnew

LAYER = {"F": pcbnew.F_Cu, "I2": pcbnew.In2_Cu, "B": pcbnew.B_Cu}
TOL = 0.03


def nm(v):
    return int(round(v * 1e6))


def mm(v):
    return v / 1e6


class Board:
    def __init__(self, path):
        self.path = path
        self.b = pcbnew.LoadBoard(path)

    def tracks(self, net):
        return [t for t in self.b.GetTracks() if t.GetNetname() == net]

    def del_seg(self, net, layer, x1, y1, x2, y2):
        for t in self.tracks(net):
            if t.GetClass() == "PCB_VIA" or t.GetLayer() != LAYER[layer]:
                continue
            s, e = t.GetStart(), t.GetEnd()
            a = (mm(s.x), mm(s.y))
            c = (mm(e.x), mm(e.y))
            for p, q in ((a, c), (c, a)):
                if max(abs(p[0] - x1), abs(p[1] - y1), abs(q[0] - x2), abs(q[1] - y2)) < TOL:
                    self.b.Delete(t)
                    return
        raise SystemExit(f"no segment {net} {layer} {x1},{y1} {x2},{y2}")

    def del_box(self, net, layer, x0, y0, x1, y1):
        n = 0
        for t in self.tracks(net):
            if t.GetClass() == "PCB_VIA" or t.GetLayer() != LAYER[layer]:
                continue
            s, e = t.GetStart(), t.GetEnd()
            if all(x0 <= mm(p.x) <= x1 and y0 <= mm(p.y) <= y1 for p in (s, e)):
                self.b.Delete(t)
                n += 1
        if not n:
            raise SystemExit(f"box empty {net} {layer}")
        return n

    def snap(self, net, layer, x, y):
        """Track ends join only when they coincide: take the exact joint, via or pad centre within TOL."""
        best = (nm(x), nm(y))
        tol = nm(TOL)
        cands = []
        for t in self.tracks(net):
            if t.GetClass() == "PCB_VIA":
                cands.append(t.GetPosition())
            elif t.GetLayer() == LAYER[layer]:
                cands += [t.GetStart(), t.GetEnd()]
        for f in self.b.GetFootprints():
            for pad in f.Pads():
                if pad.GetNetname() == net:
                    cands.append(pad.GetPosition())
        for c in cands:
            if abs(c.x - best[0]) < tol and abs(c.y - best[1]) < tol:
                return (c.x, c.y)
        return best

    def add(self, net, layer, width, *pts):
        ni = self.b.FindNet(net)
        if ni is None or not net:
            raise SystemExit(f"no net {net}")
        pts = [self.snap(net, layer, *p) for p in pts]
        for p, q in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(self.b)
            t.SetStart(pcbnew.VECTOR2I(p[0], p[1]))
            t.SetEnd(pcbnew.VECTOR2I(q[0], q[1]))
            t.SetWidth(nm(width))
            t.SetLayer(LAYER[layer])
            t.SetNet(ni)
            self.b.Add(t)

    def via(self, net, x, y, d=0.5, h=0.3, free=False):
        v = pcbnew.PCB_VIA(self.b)
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetPosition(pcbnew.VECTOR2I(nm(x), nm(y)))
        v.SetWidth(nm(d))
        v.SetDrill(nm(h))
        v.SetNet(self.b.FindNet(net))
        v.SetIsFree(free)
        self.b.Add(v)

    def del_via(self, net, x, y):
        for t in self.tracks(net):
            if t.GetClass() == "PCB_VIA":
                p = t.GetPosition()
                if max(abs(mm(p.x) - x), abs(mm(p.y) - y)) < TOL:
                    self.b.Delete(t)
                    return
        raise SystemExit(f"no via {net} {x},{y}")

    def zone(self, name, net, layer):
        for z in self.b.Zones():
            if z.GetZoneName() == name and z.GetNetname() == net and z.GetLayerSet().Contains(layer):
                return z
        raise SystemExit(f"no zone {name!r} {net}")

    def outline(self, z, pts):
        o = z.Outline()
        o.RemoveAllContours()
        o.NewOutline()
        for x, y in pts:
            o.Append(nm(x), nm(y))

    def orphan_vias(self, net):
        """Vias a deleted lane leaves behind: no track end and no pad touches them."""
        tr = [t for t in self.tracks(net) if t.GetClass() != "PCB_VIA"]
        pads = [p for f in self.b.GetFootprints() for p in f.Pads() if p.GetNetname() == net]
        gone = []
        for v in [t for t in self.tracks(net) if t.GetClass() == "PCB_VIA"]:
            c = v.GetPosition()
            r = v.GetWidth(pcbnew.F_Cu) / 2
            touch = any(math.hypot(q.x - c.x, q.y - c.y) <= r for t in tr for q in (t.GetStart(), t.GetEnd()))
            touch = touch or any(p.GetBoundingBox().Contains(c) for p in pads)
            if not touch:
                gone.append((round(mm(c.x), 2), round(mm(c.y), 2)))
                self.b.Delete(v)
        return gone


def usb_on_in2(B):
    """12 Mbit/s: In1 is the return, and the In2 GND strip and B.Cu y 128 corridor come free."""
    for net in ("/USB_D+", "/USB_D-"):
        for t in B.tracks(net):
            if t.GetClass() != "PCB_VIA" and t.GetLayer() == pcbnew.B_Cu:
                t.SetLayer(pcbnew.In2_Cu)
    B.b.Delete(B.zone("", "GND", pcbnew.In2_Cu))


def gnss_clearance(B):
    """CA-G01 manual 5.4.2-5.4.3: pad 1 to ground 2-6 mm. PRTRG leaves the clearance: F.Cu to a via at x 154.1, then B.Cu outside SCL."""
    B.outline(B.zone("gnss-antenna", "", pcbnew.In2_Cu), [
        (162.2, 70.4), (158.1, 70.4), (156.5, 68.81), (154.39, 68.81), (154.39, 59.0), (161.98, 59.18)])

    B.del_seg("/PRTRG", "F", 153.45, 61.3, 156.01, 63.86)
    B.del_seg("/PRTRG", "F", 156.01, 63.86, 156.01, 68.56)
    B.del_seg("/PRTRG", "F", 156.01, 68.56, 159.15, 71.69)
    B.del_seg("/PRTRG", "F", 159.15, 71.69, 159.15, 102.66)
    B.del_seg("/PRTRG", "F", 152.2, 61.3, 153.45, 61.3)
    B.add("/PRTRG", "F", 0.2, (152.2, 61.3), (153.75, 61.3), (154.1, 61.65), (154.1, 64.9))
    B.via("/PRTRG", 154.1, 64.9)
    B.add("/PRTRG", "B", 0.2, (154.1, 64.9), (154.1, 68.6), (154.52, 69.02), (156.62, 69.02), (157.71, 70.11),
          (157.71, 71.87), (158.79, 72.95), (159.15, 73.3))
    B.via("/PRTRG", 159.15, 73.3)
    B.add("/PRTRG", "F", 0.2, (159.15, 73.3), (159.15, 102.66))

    for x, y in ((158.83, 69.15), (161.16, 69.15), (157.66, 69.55), (154.13, 63.65), (154.13, 65.43), (153.96, 59.74)):
        B.del_via("GND", x, y)
    B.del_seg("GND", "F", 157.66, 69.55, 157.66, 68.26)
    B.del_seg("GND", "F", 157.66, 68.26, 157.79, 68.13)
    for x, y in ((153.6, 63.65), (153.6, 64.54), (153.6, 65.43), (153.5, 66.25), (153.3, 59.75),
                 (158.6, 70.75), (160.0, 70.75), (161.3, 70.75)):
        B.via("GND", x, y, free=True)


def rf_straight(B):
    """RF feed in one straight line on the centre of AE1.1: C62, R45 and C61 drop onto that line (Tanapat)."""
    ae1 = B.b.FindFootprintByReference("AE1").FindPadByNumber("1").GetPosition()
    yc = ae1.y
    for ref, num in (("C62", "1"), ("R45", "1"), ("C61", "1")):
        f = B.b.FindFootprintByReference(ref)
        p = f.GetPosition()
        f.SetPosition(pcbnew.VECTOR2I(p.x, p.y + yc - f.FindPadByNumber(num).GetPosition().y))
    B.del_box("/GNSS_RF", "F", 153.9, 67.0, 155.6, 68.25)
    B.del_box("Net-(AE1-A)", "F", 156.0, 66.5, 161.0, 68.5)
    y = mm(yc)
    B.add("/GNSS_RF", "F", 0.25, (154.172, 68.203), (154.172, y), (155.502, y))
    B.add("Net-(AE1-A)", "F", 0.25, (156.522, y), (mm(ae1.x), y))
    c612 = B.b.FindFootprintByReference("C61").FindPadByNumber("2").GetPosition()
    B.add("GND", "F", 0.25, (mm(c612.x), mm(c612.y)), (157.231, mm(c612.y)), (156.75, 69.17))


def eepa_off_l2(B):
    """Back over In1: the l2-noplane hole leaves nothing between B.Cu and U8's L1/L2 traces."""
    B.del_seg("/EEPA", "B", 158.55, 104.06, 159.64, 102.96)
    B.del_seg("/EEPA", "B", 158.55, 111.2, 158.55, 104.06)
    B.del_seg("/EEPA", "B", 159.17, 111.83, 158.55, 111.2)
    B.del_seg("/EEPA", "B", 162.37, 111.83, 159.17, 111.83)
    B.add("/EEPA", "B", 0.2, (159.64, 102.96), (158.1, 104.5), (158.1, 111.25), (158.68, 111.83), (162.37, 111.83))


def dead_ends(B):
    B.del_seg("/MOSI", "F", 118.77, 110.38, 118.77, 108.97)
    B.del_seg("/SCL", "F", 144.59, 135.69, 144.5, 135.6)
    B.del_seg("/SDA", "B", 154.86, 103.1, 154.65, 102.88)
    B.del_seg("/SDA", "B", 154.65, 102.88, 147.29, 102.88)
    B.del_seg("/SDA", "F", 154.86, 103.1, 154.67, 103.1)
    B.del_via("/SDA", 154.86, 103.1)
    B.del_seg("/SDA", "F", 154.39, 102.82, 154.67, 103.1)
    B.del_seg("/SDA", "F", 154.67, 103.1, 153.4, 104.34)
    B.add("/SDA", "F", 0.2, (154.39, 102.82), (154.39, 103.35), (153.4, 104.34))
    B.del_seg("/SCL", "B", 148.36, 104.73, 147.32, 103.7)
    B.del_seg("/SCL", "B", 147.32, 103.7, 155.95, 103.7)
    B.del_seg("/SCL", "B", 155.95, 103.7, 156.05, 103.6)
    B.add("/SCL", "B", 0.2, (148.36, 104.73), (149.39, 103.7), (155.95, 103.7), (156.05, 103.6))


def charger_ground(B):
    """BQ25628 11.1 items 1-4: C3 ground straight to the GND pin, multiple vias on every cap ground."""
    B.add("GND", "F", 0.15, (123.04, 97.3), (123.04, 96.72), (123.17, 96.55), (123.4, 96.32), (123.65, 96.07))
    for x, y in ((123.64, 94.03), (124.84, 94.03), (122.02, 93.62), (121.27, 93.37),
                 (122.93, 102.35), (123.89, 102.35), (124.65, 102.35), (125.35, 102.3), (119.82, 94.03)):
        B.via("GND", x, y, free=True)


def u8_input_ground(B):
    """TPS63802 12.1: input cap return next to the cap, not 1.9 mm of pour away."""
    for x, y in ((156.18, 102.63), (158.48, 102.03)):
        B.via("GND", x, y, free=True)


def r8_kelvin(B):
    """BQ27742 10.1.2: sense from the resistor pad, not from a via that carries battery current."""
    B.del_seg("/BAT+", "F", 111.16, 99.63, 112.19, 99.63)
    B.del_seg("/BAT+", "F", 112.19, 99.63, 112.2, 99.64)
    B.add("/BAT+", "F", 0.25, (110.62, 100.56), (112.2, 100.56))


def charger_pins(B):
    B.del_seg("SYS", "F", 123.04, 99.26, 123.04, 100.8)
    B.del_seg("SYS", "F", 123.04, 100.8, 123.69, 101.45)
    B.add("SYS", "F", 0.2, (123.04, 99.26), (123.04, 100.1), (123.1, 100.16))
    B.add("SYS", "F", 0.35, (123.1, 100.16), (123.1, 100.86), (123.69, 101.45))
    B.del_seg("Pack+", "F", 122.7, 99.32, 122.7, 100.98)
    B.del_seg("Pack+", "F", 122.7, 100.98, 122.23, 101.45)
    B.add("Pack+", "F", 0.2, (122.7, 99.32), (122.7, 100.12), (122.62, 100.2))
    B.add("Pack+", "F", 0.3, (122.62, 100.2), (122.62, 101.06), (122.23, 101.45))


def r43_at_q5(B):
    """R43 back to Q5's source, so booster current no longer rides the 14 mm In2 RESE lane to FPC1."""
    f = B.b.FindFootprintByReference("R43")
    f.SetPosition(pcbnew.VECTOR2I(nm(139.3), nm(69.5)))
    f.SetOrientationDegrees(90)
    B.del_box("/RESE", "F", 124.9, 68.4, 127.3, 70.2)
    B.add("/RESE", "F", 0.3, (140.14, 67.86), (140.14, 68.2), (139.3, 68.98))
    B.del_box("/GDR", "F", 138.1, 67.8, 138.9, 69.9)
    B.add("/GDR", "F", 0.2, (138.84, 67.86), (138.84, 68.2), (138.4, 68.64), (138.4, 69.55), (138.2, 69.75))
    B.via("GND", 138.72, 70.2, free=True)
    B.add("GND", "F", 0.2, (139.3, 70.02), (138.72, 70.2))


def i2c_off_sw(B):
    """BQ25628 11.1 item 8: no I2C round the SW island. U5 hangs off U3; the east group gets a south link (fill_net)."""
    B.del_box("/SDA", "I2", 124.0, 94.0, 138.0, 118.0)
    B.del_box("/SCL", "I2", 124.0, 95.0, 138.0, 118.0)
    print("orphan vias", B.orphan_vias("/SDA"), B.orphan_vias("/SCL"))
    B.del_seg("Net-(U3-BAT)", "B", 115.94, 101.03, 115.94, 100.72)
    B.del_seg("Net-(U3-BAT)", "B", 115.94, 100.72, 116.21, 100.44)
    B.del_seg("Net-(U3-BAT)", "B", 116.21, 100.44, 116.79, 100.44)
    B.del_seg("Net-(U3-BAT)", "B", 116.79, 100.44, 117.43, 101.08)
    B.del_seg("Net-(U3-BAT)", "B", 117.43, 101.08, 117.43, 101.89)
    B.add("Net-(U3-BAT)", "B", 0.15, (115.94, 101.03), (116.15, 101.24), (117.2, 101.24), (117.43, 101.47), (117.43, 101.89))
    B.del_seg("/BAT-", "F", 116.8, 101.55, 116.8, 101.39)
    B.del_via("/BAT-", 116.8, 101.55)
    B.via("/BAT-", 116.75, 101.62, 0.4, 0.2)
    B.add("/BAT-", "F", 0.2, (116.75, 101.62), (116.8, 101.39))
    B.add("/SDA", "B", 0.15, (115.62, 96.94), (115.62, 100.0), (116.46, 100.84), (116.62, 100.84))


def int_on_f(B):
    """0.15 mm passes the BT1.2 pad on F.Cu, so the B.Cu hop and its two vias go."""
    B.del_seg("/INT", "F", 103.51, 71.46, 103.51, 79.25)
    B.del_seg("/INT", "B", 103.51, 79.25, 104.33, 80.07)
    B.del_seg("/INT", "B", 104.33, 80.07, 104.33, 83.73)
    B.del_seg("/INT", "B", 104.33, 83.73, 103.87, 84.19)
    B.del_seg("/INT", "F", 103.87, 84.19, 103.87, 93.47)
    B.del_via("/INT", 103.51, 79.25)
    B.del_via("/INT", 103.87, 84.19)
    B.add("/INT", "F", 0.2, (103.51, 71.46), (103.51, 79.0))
    B.add("/INT", "F", 0.15, (103.51, 79.0), (104.35, 79.84), (104.35, 84.8), (103.87, 85.28))
    B.add("/INT", "F", 0.2, (103.87, 85.28), (103.87, 93.47))


def planes_in2(B):
    """SW island keeps only the current path. VBUS band gives its south 1.7 mm back to +3.3V (F1 750 mA, 1.5 mm is enough)."""
    B.outline(B.zone("SW", "/SW", pcbnew.In2_Cu), [
        (121.6, 97.26), (127.41, 97.3), (127.41, 98.75), (125.7, 98.75), (125.7, 100.5), (123.4, 100.5),
        (123.4, 99.35), (121.6, 99.35)])
    for z in B.b.Zones():
        if z.GetNetname() == "VBUS" and z.GetLayerSet().Contains(pcbnew.In2_Cu) and z.GetAssignedPriority() == 4:
            B.outline(z, [(128.95, 92.31), (132.03, 92.31), (132.03, 101.7), (148.61, 101.69), (148.61, 124.15),
                          (159.15, 124.15), (159.15, 127.08), (146.34, 127.08), (146.42, 103.3), (128.95, 103.3)])
            return
    raise SystemExit("no VBUS band")


def bends(B):
    """RT-01: the corners the router and the copied v3 groups left sharper than 135 degrees."""
    B.del_seg("Net-(U5-TS_BIAS)", "B", 127.61, 99.26, 128.09, 99.26)
    B.del_seg("Net-(U5-TS_BIAS)", "B", 128.09, 99.26, 128.12, 99.29)
    B.del_seg("Net-(U5-TS_BIAS)", "B", 128.12, 99.29, 128.67, 98.74)
    B.add("Net-(U5-TS_BIAS)", "B", 0.25, (127.61, 99.26), (128.15, 99.26), (128.67, 98.74))
    B.del_seg("/ePaper RES", "F", 145.08, 108.02, 145.45, 108.0)
    B.del_seg("/ePaper RES", "F", 145.45, 108.0, 145.45, 94.62)
    B.add("/ePaper RES", "F", 0.2, (145.08, 108.02), (145.45, 107.65))
    B.add("/ePaper RES", "F", 0.15, (145.45, 107.65), (145.45, 94.62))


def no_y(B):
    """RT-02: a tap is a perpendicular T on a straight line, never a Y."""
    B.del_box("/MOSI", "B", 117.9, 104.7, 122.4, 108.2)
    B.add("/MOSI", "B", 0.25, (118.592, 108.12), (118.592, 106.06), (122.292, 106.06))
    B.add("/MOSI", "B", 0.25, (118.592, 106.06), (118.592, 105.35))
    B.add("/MOSI", "B", 0.2, (118.592, 105.35), (118.1, 104.85))

    B.del_seg("/BAT+", "B", 110.66, 100.13, 110.16, 99.63)
    B.del_seg("/BAT+", "B", 110.66, 100.13, 111.16, 99.63)
    B.del_seg("/BAT+", "B", 110.66, 102.0, 110.66, 100.13)
    B.add("/BAT+", "B", 1.0, (110.66, 102.0), (110.66, 99.63))
    B.add("/BAT+", "B", 1.0, (110.16, 99.63), (110.66, 99.63), (111.16, 99.63))
    B.del_seg("/BAT+", "F", 110.16, 99.63, 110.66, 99.63)
    B.del_seg("/BAT+", "F", 110.66, 99.63, 111.16, 99.63)
    B.del_seg("/BAT+", "F", 110.66, 99.63, 110.62, 100.56)
    B.add("/BAT+", "F", 0.8, (110.16, 99.63), (110.62, 99.63), (111.16, 99.63))
    B.add("/BAT+", "F", 1.0, (110.62, 99.63), (110.62, 100.56))

    B.del_seg("/SCL", "F", 143.08, 136.05, 144.02, 136.05)
    B.del_seg("/SCL", "F", 144.02, 136.05, 144.02, 136.46)
    B.del_seg("/SCL", "F", 144.02, 136.46, 144.32, 136.76)
    B.add("/SCL", "F", 0.2, (143.08, 136.05), (143.75, 136.05), (144.05, 136.05))
    B.add("/SCL", "F", 0.15, (143.75, 136.05), (143.75, 136.46), (144.05, 136.76), (144.32, 136.76))

    B.del_box("/EN", "F", 107.2, 107.1, 110.7, 109.0)
    B.add("/EN", "F", 0.2, (110.662, 108.119), (108.57, 108.119), (107.96, 108.119), (107.332, 107.491), (107.332, 107.18))
    B.add("/EN", "F", 0.2, (108.57, 108.119), (108.57, 108.97))

    B.del_box("/QON", "F", 115.9, 123.4, 116.8, 124.2)
    B.add("/QON", "F", 0.15, (116.62, 123.43), (116.62, 123.57), (116.62, 124.07), (116.67, 124.12))
    B.add("/QON", "F", 0.15, (116.62, 123.57), (115.97, 123.57))

    B.del_seg("+3.3V", "F", 140.187, 135.03, 139.742, 134.585)
    B.add("+3.3V", "F", 0.25, (139.742, 134.585), (139.742, 134.8), (139.972, 135.03), (140.187, 135.03))

    B.del_seg("Net-(U5-TS)", "F", 127.83, 97.11, 128.45, 96.49)
    B.add("Net-(U5-TS)", "F", 0.25, (128.45, 96.49), (127.98, 96.49), (127.83, 96.64), (127.83, 97.11))

    B.del_seg("/SDA", "B", 140.38, 130.237, 141.9, 131.757)
    B.del_seg("/SDA", "B", 141.9, 131.757, 144.039, 129.618)
    B.del_seg("/SDA", "B", 141.9, 131.757, 142.434, 132.291)
    B.del_seg("/SDA", "B", 142.434, 132.291, 142.434, 133.52)
    B.add("/SDA", "B", 0.2, (140.38, 130.237), (142.434, 130.237), (143.42, 130.237), (144.039, 129.618))
    B.add("/SDA", "B", 0.2, (142.434, 130.237), (142.434, 133.52))


def hooks(B):
    B.del_seg("/SW", "F", 122.64, 98.03, 122.59, 98.12)
    B.del_box("/MISO", "F", 121.9, 107.6, 123.3, 108.3)
    B.add("/MISO", "F", 0.25, (123.22, 108.29), (122.635, 107.703), (121.99, 107.7))


def tidy(B):
    """Duplicate segments and router slivers: they read as acute junctions and add nothing."""
    seen = {}
    dup = 0
    for t in sorted([t for t in B.b.GetTracks() if t.GetClass() != "PCB_VIA"], key=lambda t: -t.GetWidth()):
        s, e = t.GetStart(), t.GetEnd()
        ends = sorted(((round(s.x / 5000), round(s.y / 5000)), (round(e.x / 5000), round(e.y / 5000))))
        key = (t.GetNetname(), t.GetLayer(), *ends)
        if key in seen:
            B.b.Delete(t)
            dup += 1
        else:
            seen[key] = t
    tiny = 0
    for t in [t for t in B.b.GetTracks() if t.GetClass() != "PCB_VIA"]:
        s, e = t.GetStart(), t.GetEnd()
        if math.hypot(e.x - s.x, e.y - s.y) > nm(0.035):
            continue
        if math.hypot(e.x - s.x, e.y - s.y) < nm(0.005):
            B.b.Delete(t)
            tiny += 1
            continue
        keep = pcbnew.VECTOR2I(s.x, s.y)
        gone = pcbnew.VECTOR2I(e.x, e.y)
        same = [o for o in B.tracks(t.GetNetname()) if o.GetClass() != "PCB_VIA" and o.GetLayer() == t.GetLayer()
                and o.m_Uuid.AsString() != t.m_Uuid.AsString()]
        near = [o for o in same if (o.GetStart().x, o.GetStart().y) == (gone.x, gone.y)
                or (o.GetEnd().x, o.GetEnd().y) == (gone.x, gone.y)]
        # Moving a long neighbour swings it into the track beside it (0.1 mm lanes): leave that sliver.
        if any(o.GetLength() > nm(3) for o in near):
            continue
        for o in near:
            if (o.GetStart().x, o.GetStart().y) == (gone.x, gone.y):
                o.SetStart(keep)
            else:
                o.SetEnd(keep)
        B.b.Delete(t)
        tiny += 1
    print("duplicates", dup, "slivers", tiny)
    for net, layer, x, y in (("/SCL", "F", 116.32, 101.78), ("Net-(U5-TS_BIAS)", "B", 120.98, 99.88),
                             ("/SDA", "B", 125.8, 72.25),
                             ("/NAND SCLK", "F", 127.69, 117.14), ("+3.3V", "F", 112.22, 105.98),
                             ("Net-(U5-ILIM)", "B", 120.67, 98.61), ("+3.3V", "F", 113.11, 105.7),
                             ("/CHG_INT", "F", 124.34, 98.69), ("GND", "F", 108.34, 144.71)):
        square(B, net, layer, x, y)


def square(B, net, layer, x, y):
    """A bend a few degrees off 135: slide the joint along its straight leg until the other leg is exactly 45."""
    tol = nm(TOL)
    legs = []
    for t in B.tracks(net):
        if t.GetClass() == "PCB_VIA" or t.GetLayer() != LAYER[layer]:
            continue
        for end, other in ((t.GetStart(), t.GetEnd()), (t.GetEnd(), t.GetStart())):
            if abs(end.x - nm(x)) < tol and abs(end.y - nm(y)) < tol:
                legs.append((t, end is t.GetStart() or (end.x, end.y) == (t.GetStart().x, t.GetStart().y), other.x, other.y, end.x, end.y))
    if len(legs) != 2:
        raise SystemExit(f"no bend {net} {x},{y}: {len(legs)} legs")
    a, c = legs
    if abs(a[2] - a[4]) > tol and abs(a[3] - a[5]) > tol:
        a, c = c, a
    if abs(a[2] - a[4]) <= tol:  # vertical leg
        jx = a[2]
        dy = abs(c[2] - jx)
        jy = c[3] - dy if a[3] < c[3] else c[3] + dy
    else:  # horizontal leg
        jy = a[3]
        dx = abs(c[3] - jy)
        jx = c[2] - dx if a[2] < c[2] else c[2] + dx
    p = pcbnew.VECTOR2I(int(jx), int(jy))
    for t, start, *_ in (a, c):
        t.SetStart(p) if start else t.SetEnd(p)


def main():
    B = Board(sys.argv[1])
    for step in (usb_on_in2, gnss_clearance, rf_straight, eepa_off_l2, dead_ends, charger_ground, u8_input_ground, r8_kelvin,
                 charger_pins, r43_at_q5, i2c_off_sw, int_on_f, planes_in2, bends, no_y, tidy, hooks):
        step(B)
        print("ok", step.__name__)
    B.b.Save(sys.argv[1])


if __name__ == "__main__":
    main()
