#!/usr/bin/env python3
"""GO main v3 full re-route: rebuild every zone, keepout and hand route from data.

Placement stays. Everything on copper is deleted and redrawn:
  1. zones and keepouts (planes.json is written here, then applied)
  2. route.json: power clusters, USB and NAND SPI keep the geometry proven on v2 (read from the BASE
     board, net by net); the battery straps, the ePaper SPI lanes through the left rail and the LED
     lanes through the FPC neck are new and written out below
  3. pcb_route.py applies route.json; reroute_autoroute.py routes the rest

Goal of the new planes: In1 is solid GND with no signal on it. The old 17 x 22 mm In1 BAT- island is
gone; battery return runs on In2 and only a small gauge island stays on In1, so SCLK no longer crosses
a plane split.

Run with KiCad's Python, KiCad closed:
  $KPY reroute_build.py BASE.kicad_pcb OUT.kicad_pcb
Coordinates in this file are absolute board mm; route.json is local (abs - outline origin).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
ORIGIN = (100.511559, 58.790008)
LAYER = {pcbnew.F_Cu: "F.Cu", pcbnew.In1_Cu: "GND", pcbnew.In2_Cu: "PWR", pcbnew.B_Cu: "B.Cu"}
S = 0.15   # lane width: R-V3-10 Z0 about 52 ohm over the 0.1 mm plane


def mm(v: int) -> float:
    return v / 1e6


def nm(v: float) -> int:
    return int(round(v * 1e6))


def loc(p):
    return [round(p[0] - ORIGIN[0], 6), round(p[1] - ORIGIN[1], 6)]


class Spec:
    def __init__(self) -> None:
        self.groups: dict[str, dict] = {}

    def group(self, name: str, why: str) -> dict:
        return self.groups.setdefault(name, {"_why": why, "tracks": [], "vias": []})

    def t(self, g: str, net: str, layer: str, width: float, pts) -> None:
        self.groups[g]["tracks"].append({"net": net, "layer": layer, "width": width,
                                         "path": [loc(p) for p in pts]})

    def v(self, g: str, net: str, at, size: float = 0.5, drill: float = 0.3) -> None:
        self.groups[g]["vias"].append({"net": net, "at": loc(at), "size": size, "drill": drill})


def carry(spec: Spec, group: str, base: pcbnew.BOARD, nets, box=None, layers=("F.Cu", "B.Cu"), skip=None,
          vias=True) -> None:
    """Copy tracks and vias of the named nets from the base board. box limits both ends of a track."""
    def inside(x, y):
        return box is None or (box[0] <= x <= box[2] and box[1] <= y <= box[3])
    for it in base.GetTracks():
        net = it.GetNetname()
        if net not in nets:
            continue
        if it.GetClass() == "PCB_VIA":
            p = it.GetPosition()
            at = (mm(p.x), mm(p.y))
            if vias and inside(*at) and not (skip and skip(net, "via", at, at)):
                spec.v(group, net, at, mm(it.GetWidth(pcbnew.F_Cu)), mm(it.GetDrill()))
            continue
        layer = LAYER[it.GetLayer()]
        a, b = it.GetStart(), it.GetEnd()
        pa, pb = (mm(a.x), mm(a.y)), (mm(b.x), mm(b.y))
        if layer not in layers or not (inside(*pa) and inside(*pb)):
            continue
        if skip and skip(net, layer, pa, pb):
            continue
        if pa != pb:
            spec.t(group, net, layer, mm(it.GetWidth()), [pa, pb])


# ---------------------------------------------------------------------------------------------- #
# Zones and keepouts
# ---------------------------------------------------------------------------------------------- #

def planes(old_zones: list[dict]) -> list[dict]:
    """Kept outlines come from the v3 board; the In1/In2 battery shapes are new."""
    out = []
    for z in old_zones:
        if z["rule"]:
            continue
        if z["net"] in ("Net-(U8-L1)", "Net-(U8-L2)"):
            continue    # replaced by short wide tracks: both zones sat almost wholly inside the L2 rule area
        if z["net"] == "/BAT-":
            continue    # the 17 x 22 mm In1 island, see below
        if z["net"] == "GND" and len(z["layers"]) > 1:
            for lay in z["layers"]:     # one zone per layer: pcb_tidy and pcb_check read fills by zone layer
                out.append({**z, "layers": [lay], "name": f"GND-{lay}"})
            continue
        out.append(z)
    # In1: gauge ground only. Vias at U3.D1, C13.2 and C9.2/C16.2, strip north to the NT1.1 vias.
    out.append({"name": "gauge-gnd", "net": "/BAT-", "rule": False, "layers": ["GND"], "prio": 24, "connect": "2",
                "clearance": 0.0, "minw": 0.25,
                "pts": [(117.2, 92.35), (118.75, 92.35), (118.75, 103.3), (114.3, 103.3), (114.3, 99.2), (117.2, 99.2)]})
    # In2: battery return from BT1.2 down the rail, then east below the NPTH to the NT1.1 vias.
    out.append({"name": "bat-return", "net": "/BAT-", "rule": False, "layers": ["PWR"], "prio": 24, "connect": "2",
                "clearance": 0.0, "minw": 0.25,
                "pts": [(100.9, 80.6), (103.75, 80.6), (103.75, 91.0), (118.75, 91.0), (118.75, 96.0), (100.9, 96.0)]})
    return out


KEEPOUTS = [
    {"name": "enclosure-br", "layers": ["F.Cu", "B.Cu"], "no": ["footprints"],
     "pts": [(158.412, 124.08), (158.412, 137.11), (163.393, 137.11), (163.393, 124.08)]},
    {"name": "enclosure-bl", "layers": ["B.Cu"], "no": ["footprints"],
     "pts": [(105.512, 124.08), (105.512, 137.11), (100.53, 137.11), (100.53, 124.08)]},
    {"name": "l2-noplane", "layers": ["F.Cu", "B.Cu", "GND", "PWR"], "no": ["vias", "pour"],
     "pts": [(162.796, 108.99), (158.412, 109.001), (158.412, 104.651), (162.807, 104.64)]},
    {"name": "gnss-antenna", "layers": ["F.Cu", "B.Cu", "GND", "PWR"], "no": ["pour"],
     "pts": [(162.042, 68.81), (154.392, 68.81), (154.392, 59.004), (161.982, 59.18)]},
]


def apply_zones(board: pcbnew.BOARD, plist: list[dict]) -> None:
    def lset(names):
        s = pcbnew.LSET()
        ids = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu, "GND": pcbnew.In1_Cu, "PWR": pcbnew.In2_Cu}
        for n in names:
            s.AddLayer(ids[n])
        return s
    for p in plist:
        z = pcbnew.ZONE(board)
        z.SetLayerSet(lset(p["layers"]))
        z.SetNetCode(board.FindNet(p["net"]).GetNetCode())
        z.SetZoneName(p.get("name", ""))
        z.SetAssignedPriority(int(p["prio"]))
        z.SetLocalClearance(nm(p.get("clearance") or 0))   # a new ZONE defaults to 0.5 mm, which breaks the islands
        z.SetMinThickness(nm(p.get("minw", 0.25)))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetThermalReliefGap(nm(0.25))
        z.SetThermalReliefSpokeWidth(nm(0.3))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        o = z.Outline()
        o.NewOutline()
        for x, y in p["pts"]:
            o.Append(nm(x), nm(y))
        board.Add(z)
    for k in KEEPOUTS:
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetLayerSet(lset(k["layers"]))
        z.SetZoneName(k["name"])
        z.SetDoNotAllowTracks(False)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowVias("vias" in k["no"])
        z.SetDoNotAllowZoneFills("pour" in k["no"])
        z.SetDoNotAllowFootprints("footprints" in k["no"])
        o = z.Outline()
        o.NewOutline()
        for x, y in k["pts"]:
            o.Append(nm(x), nm(y))
        board.Add(z)


# ---------------------------------------------------------------------------------------------- #
# Route spec
# ---------------------------------------------------------------------------------------------- #

def bat_skip(net, layer, pa, pb):
    """Keep only the short F.Cu column at R5/R9/C5/C10 and the C75 stub; the strap is redrawn."""
    if layer == "via" or layer == "B.Cu":
        return True
    if max(pa[1], pb[1]) > 102.5 and min(pa[0], pb[0]) < 130:
        return True     # the old tap to the strap via at (112.67,103.08), and R6's
    if pa == (110.66, 99.63) or pb == (110.66, 99.63):
        return min(mm(0), 0) == 0 and abs(pa[0] - pb[0]) < 0.1     # the old 1 mm jog to R8.1, redrawn
    return False


def build(base: pcbnew.BOARD) -> Spec:
    s = Spec()

    # -- battery ---------------------------------------------------------------------------------
    g = "bat-straps"
    s.group(g, "BAT+ from BT1.1 round the battery on B.Cu. Same path as v2 up to the diagonal, then y 104.0 "
               "(was 103.08) so a signal can hop from B.Cu to F.Cu between the F.Cu power wall and the strap; "
               "two 0.8/0.4 vias into R8.1 (PWR-52, one before). BAT- return is on In2, see planes.")
    s.t(g, "/BAT+", "B.Cu", 1.25, [(161.20, 82.32), (161.20, 92.34), (158.55, 94.99), (154.81, 94.99), (153.80, 93.98),
                                   (146.83, 93.98), (146.25, 94.56), (146.25, 97.22), (144.74, 98.73), (130.96, 98.73),
                                   (126.29, 103.4)])
    s.t(g, "/BAT+", "B.Cu", 1.0, [(126.29, 103.4), (119.85, 103.4), (119.2, 103.4), (118.6, 104.0), (112.66, 104.0), (110.66, 102.0), (110.66, 100.13)])
    s.t(g, "/BAT+", "B.Cu", 1.0, [(110.66, 100.13), (110.16, 99.63)])
    s.t(g, "/BAT+", "B.Cu", 1.0, [(110.66, 100.13), (111.16, 99.63)])
    s.v(g, "/BAT+", (110.16, 99.63), 0.8, 0.4)
    s.v(g, "/BAT+", (111.16, 99.63), 0.8, 0.4)
    s.t(g, "/BAT+", "F.Cu", 0.8, [(110.16, 99.63), (110.66, 99.63), (111.16, 99.63)])
    s.t(g, "/BAT+", "F.Cu", 1.0, [(110.66, 99.63), (110.62, 100.56)])
    s.t(g, "/BAT+", "F.Cu", 0.25, [(111.16, 99.63), (112.19, 99.63)])
    s.v(g, "/BAT+", (119.85, 103.4))
    s.t(g, "/BAT+", "F.Cu", 0.25, [(119.22, 103.69), (119.53, 103.69), (119.82, 103.4), (119.85, 103.4)])
    carry(s, g, base, {"/BAT+"}, layers=("F.Cu",), vias=False,
          skip=lambda n, l, a, b: (max(a[1], b[1]) > 102.5 and min(a[0], b[0]) < 130)
          or 110.0 < a[0] < 111.3 and 99.0 < a[1] < 101.0 or 110.0 < b[0] < 111.3 and 99.0 < b[1] < 101.0)
    s.t(g, "/BAT-", "F.Cu", 0.25, [(108.31, 101.37), (108.31, 100.55)])
    s.v(g, "/BAT-", (108.31, 100.55))
    s.t(g, "/BAT-", "B.Cu", 0.25, [(108.31, 100.55), (109.1, 99.76), (109.1, 96.45), (109.7, 95.85)])
    s.v(g, "/BAT-", (109.7, 95.85))
    carry(s, g, base, {"/BAT-"}, box=(112.0, 90.0, 120.0, 105.0),
          skip=lambda n, l, a, b: l == "F.Cu" and (a[1] > 102.3 or b[1] > 102.3))
    s.t(g, "/BAT-", "F.Cu", 0.2, [(114.95, 103.65), (114.4, 103.65), (113.85, 103.1), (113.85, 102.44), (114.07, 102.22)])

    # -- power clusters: geometry proven on v2 --------------------------------------------------
    g = "pwr-charger"
    s.group(g, "BQ25628 cluster, Q1/Q2 and +5V: copied from v3 (= v2 layout, charger and BMS bring-up done on it).")
    carry(s, g, base, {"/SW", "/BTST", "/REGN", "PMID", "SYS", "VBUS", "Net-(Q1-G)", "Net-(Q2-D)", "+5V", "/CE",
                       "Net-(U5-ILIM)", "/PMID_GD", "Net-(U5-TS_BIAS)"},
          skip=lambda n, l, a, b: l == "via" and n == "/SW" and abs(a[0] - 125.52) < 0.05 and abs(a[1] - 97.94) < 0.05)
    s.v(g, "/SW", (125.6, 97.94))     # 0.08 east: the CHG_INT In2 lane passes between this via and the SCL via
    carry(s, g, base, {"Pack+"}, layers=("F.Cu", "B.Cu", "PWR"))     # the U9 feed stays on In2, 0.2 mm, about 1 mA

    g = "pwr-gauge"
    s.group(g, "BQ27742 cluster: copied from v3. The 0.25/0.15 via at U3.C2 is the only way out of that ball; "
               "its hole clearance to D2, D3, C3 is known and unchanged.")
    carry(s, g, base, {"Net-(C73-Pad2)", "Net-(C72-Pad2)", "Net-(U3-SRP)", "Net-(U3-SRN)", "Net-(U3-VPWR)",
                       "Net-(U3-BAT)", "Net-(U3-PACKP)", "Net-(U3-CHG)", "Net-(U3-DSG)", "Net-(Q3-G-PadB1)",
                       "Net-(Q3-G-PadB2)"},
          skip=lambda n, l, a, b: l == "via" and abs(a[0] - 109.82) < 0.05)
    s.v(g, "Net-(C73-Pad2)", (109.95, 96.55))

    g = "pwr-dcdc"
    s.group(g, "TPS63802 and LM66200: copied from v3. L1/L2 are now short 0.45 mm tracks: the old 0.25 mm tracks "
               "carried the inductor current, their zones sat inside the L2 keepout (PWR-20).")
    carry(s, g, base, {"Net-(U8-EN)", "Net-(U8-FB)", "Net-(U8-PG)", "Net-(C28-Pad2)", "Net-(U19-VIN1)", "Net-(U19-ST)"})
    s.t(g, "Net-(U8-L1)", "F.Cu", 0.3, [(157.92, 106.34), (158.5, 106.34)])
    s.t(g, "Net-(U8-L1)", "F.Cu", 0.45, [(158.5, 106.34), (159.2, 105.66)])
    s.t(g, "Net-(U8-L2)", "F.Cu", 0.3, [(157.92, 107.34), (158.5, 107.34)])
    s.t(g, "Net-(U8-L2)", "F.Cu", 0.45, [(158.5, 107.34), (159.25, 108.04)])

    g = "gnd-power"
    s.group(g, "GND and +3.3V vias around the power stages, the U4 pad and the USB shield, copied from v3: the "
               "autorouter only fans out one via per pad.")
    for box in ((119.0, 92.0, 136.0, 108.0), (143.0, 101.0, 163.0, 116.0), (146.0, 124.0, 158.0, 137.0),
                (112.0, 113.0, 117.5, 119.0)):
        carry(s, g, base, {"GND"}, box=box, layers=())
    carry(s, g, base, {"+3.3V"}, box=(143.0, 101.0, 163.0, 116.0), layers=())

    # -- USB, NAND SPI, GNSS, display booster: proven, no inner layer ----------------------------
    g = "usb"
    s.group(g, "USB input, ESD-side parts and the D+/D- pair on B.Cu over the In2 GND island: copied from v3.")
    carry(s, g, base, {"Net-(F1-Pad1)", "Net-(C1-Pad2)", "/USB_D+", "/USB_D-", "/USB+", "/USB-",
                       "Net-(USB1-CC1)", "Net-(USB1-CC2)"})

    g = "nand-spi"
    s.group(g, "NAND SCLK, MISO, NAND CS and the east MOSI branch: copied from v3 (10 MHz nets, short, on F/B).")
    carry(s, g, base, {"/SCLK", "/NAND SCLK", "/MISO", "/NAND CS", "Net-(TF1-CLK)", "Net-(TF1-CMD)", "Net-(TF1-DAT0)"})
    carry(s, g, base, {"/MOSI"}, box=(118.4, 105.5, 140.0, 137.0))
    s.t(g, "/MOSI", "B.Cu", 0.2, [(119.30, 106.06), (118.1, 104.86), (118.1, 104.85)])

    g = "gnss-lp5036"
    s.group(g, "GNSS RF feed and backup supply, LP5036 local parts: copied from v3.")
    carry(s, g, base, {"/GNSS_RF", "Net-(AE1-A)", "VDD_BAK", "Net-(U20-ADDR0)", "Net-(U20-IREF)", "Net-(U20-VCAP)"})

    g = "booster"
    s.group(g, "ePaper booster: copied from v3. GDR and RESE keep their ends and run on In2 below the FPC via row.")
    carry(s, g, base, {"Net-(Q5-D)", "Net-(C48-Pad2)", "/PREVGL", "/PREVGH", "Net-(C51-Pad2)", "Net-(C53-Pad2)",
                       "Net-(C58-Pad2)", "/VCOM"})
    carry(s, g, base, {"/GDR"}, box=(125.0, 68.0, 128.2, 70.3), vias=False,
          skip=lambda n, l, a, b: l == "B.Cu" and (abs(a[1] - 69.92) < 0.02 or abs(b[1] - 69.92) < 0.02))
    carry(s, g, base, {"/RESE"}, layers=("F.Cu", "B.Cu"), vias=False)
    carry(s, g, base, {"/GDR", "/RESE"}, layers=(),
          skip=lambda n, l, a, b: abs(a[0] - 122.89) < 0.05 or abs(a[0] - 138.22) < 0.05)
    s.v(g, "/GDR", (138.2, 69.75), 0.4, 0.2)
    s.t(g, "/GDR", "F.Cu", 0.2, [(138.2, 69.75), (138.84, 69.11), (138.84, 67.86)])
    s.t(g, "/GDR", "PWR", 0.15, [(125.53, 69.11), (125.97, 69.55), (138.0, 69.55), (138.2, 69.75)])
    s.t(g, "/RESE", "PWR", 0.15, [(126.03, 68.64), (126.64, 69.25), (140.24, 69.25), (141.02, 68.47), (141.02, 68.46)])
    s.v(g, "Net-(C41-Pad2)", (128.1, 68.33), 0.4, 0.2)
    s.t(g, "Net-(C41-Pad2)", "F.Cu", 0.2, [(126.94, 67.02), (127.22, 67.02), (127.6, 67.4), (127.6, 67.83), (128.1, 68.33)])
    s.t(g, "Net-(C41-Pad2)", "B.Cu", 0.2, [(128.1, 68.33), (128.12, 67.58)])

    # -- ePaper SPI lanes --------------------------------------------------------------------------
    g = "epaper-lanes"
    s.group(g, "R-V3-10 and the return-path review: SCLK runs R63 to the FPC on F.Cu over solid In1 GND, no via until "
               "the FPC hop. MOSI, D/C, CS, BUSY beside it through the left rail at 0.15/0.15 (52 ohm). D/C, CS and "
               "BUSY drop to B.Cu south of C78; the rest of those three is autorouted. U5-TS, U3-TS and REG25 stay on "
               "B.Cu so they do not cross the lanes on the way to the NTCs.")
    s.t(g, "/ePaper SCLK", "F.Cu", S, [(116.29, 107.49), (116.19, 107.49), (112.2, 103.5), (111.0, 103.5), (110.7, 103.2),
                                       (107.55, 103.2), (107.1, 102.75), (107.1, 95.65), (104.65, 93.2), (104.65, 73.2),
                                       (108.45, 69.4), (118.0, 69.4), (121.35, 66.05), (128.3, 66.05), (129.9, 67.65),
                                       (131.0, 67.65), (131.58, 68.23), (131.58, 68.7)])
    s.t(g, "/MOSI", "F.Cu", S, [(118.1, 104.85), (118.1, 104.4), (117.9, 104.2), (114.15, 104.2), (112.9, 102.95),
                                (111.4, 102.95), (109.85, 101.4), (109.7, 101.4), (109.45, 101.15), (109.45, 96.3),
                                (105.85, 92.7), (105.85, 73.7), (108.95, 70.6), (118.3, 70.6), (119.15, 71.45),
                                (131.93, 71.45), (132.54, 70.84)])
    s.t(g, "/ePaper BUSY", "F.Cu", S, [(109.9, 102.75), (109.75, 102.9), (107.9, 102.9), (107.45, 102.45), (107.45, 95.57),
                                       (104.95, 93.07), (104.95, 73.33), (108.58, 69.7), (118.12, 69.7), (121.47, 66.35),
                                       (127.9, 66.35), (129.43, 67.88), (129.43, 68.69)])
    s.t(g, "/ePaper D{slash}C", "F.Cu", S, [(108.98, 101.85), (108.85, 101.6), (108.85, 96.55), (105.25, 92.95),
                                            (105.25, 73.45), (108.7, 70.0), (120.4, 70.0), (120.53, 70.13), (121.75, 70.13),
                                            (122.07, 70.45), (122.07, 70.64), (122.6, 70.64), (122.74, 70.5), (128.74, 70.5),
                                            (130.55, 68.69)])
    s.t(g, "/ePaper CS", "F.Cu", S, [(109.62, 101.85), (109.15, 101.38), (109.15, 96.42), (105.55, 92.82), (105.55, 73.58),
                                     (108.83, 70.3), (120.0, 70.3), (120.34, 70.64), (121.13, 70.64), (121.64, 71.15),
                                     (130.9, 71.15), (131.21, 70.84), (131.6, 70.84)])
    for net, at in (("/MOSI", (118.1, 104.85)), ("/ePaper BUSY", (109.9, 102.75)), ("/ePaper D{slash}C", (108.98, 101.85)),
                    ("/ePaper CS", (109.62, 101.85)), ("/ePaper BUSY", (129.43, 68.69)),
                    ("/ePaper D{slash}C", (130.55, 68.69)), ("/ePaper SCLK", (131.58, 68.7)),
                    ("/ePaper CS", (131.6, 70.84)), ("/MOSI", (132.54, 70.84))):
        s.v(g, net, at)
    # FPC1 stubs on B.Cu
    s.t(g, "/ePaper BUSY", "B.Cu", 0.2, [(129.43, 68.69), (130.12, 68.0), (130.12, 67.58)])
    s.t(g, "/ePaper D{slash}C", "B.Cu", 0.2, [(130.55, 68.69), (131.12, 68.13), (131.12, 67.58)])
    s.t(g, "/ePaper SCLK", "B.Cu", 0.2, [(131.58, 68.7), (131.77, 68.7), (132.12, 68.35), (132.12, 67.58)])
    s.t(g, "/ePaper CS", "B.Cu", 0.2, [(131.6, 70.84), (131.62, 70.82), (131.62, 69.82)])
    s.t(g, "/MOSI", "B.Cu", 0.2, [(132.54, 70.84), (132.62, 70.76), (132.62, 69.82)])
    # ePaper RES comes from the east: hop past the CS and MOSI vias
    s.v(g, "/ePaper RES", (133.2, 71.28), 0.45, 0.25)
    s.t(g, "/ePaper RES", "B.Cu", S, [(133.2, 71.28), (131.0, 71.28), (130.62, 70.9), (130.62, 69.82)])
    # C78: BAT- via north of the pad joins the In2 return; GND via in the free spot east of the pad
    s.t(g, "GND", "F.Cu", 0.25, [(108.31, 102.33), (109.1, 102.45)])
    s.v(g, "GND", (109.1, 102.45))
    # R39.1 and R40.1 +3.3V to In2; FPC +3.3V and GND
    s.t(g, "+3.3V", "F.Cu", 0.2, [(121.13, 69.62), (121.6, 69.15), (121.6, 68.95)])
    s.t(g, "+3.3V", "F.Cu", 0.2, [(122.07, 69.62), (121.6, 69.15)])
    s.v(g, "+3.3V", (121.6, 68.95))
    s.t(g, "+3.3V", "B.Cu", 0.2, [(132.72, 68.81), (133.48, 68.81), (133.62, 68.95), (133.62, 69.82)])
    s.t(g, "+3.3V", "B.Cu", 0.2, [(133.12, 67.58), (133.12, 69.32), (133.62, 69.82)])
    s.t(g, "+3.3V", "B.Cu", 0.2, [(133.62, 69.82), (133.62, 70.72), (134.59, 71.69)])
    s.v(g, "+3.3V", (132.72, 68.81))
    s.v(g, "+3.3V", (134.59, 71.69))
    s.t(g, "GND", "B.Cu", 0.15, [(128.58, 68.71), (128.64, 68.71), (129.46, 69.53), (129.62, 69.82)])
    s.t(g, "GND", "F.Cu", 0.2, [(127.98, 68.98), (128.58, 68.71)])
    for at in ((128.58, 68.71), (134.59, 68.74), (135.52, 68.74), (129.23, 71.97)):
        s.v(g, "GND", at)
    # NTC lanes on B.Cu
    s.t(g, "Net-(U3-REG25)", "B.Cu", S, [(103.52, 84.96), (104.4, 84.96), (104.75, 85.31), (104.75, 91.9), (107.6, 94.75),
                                           (113.65, 94.75), (113.95, 95.05), (113.95, 102.35), (114.45, 102.85)])
    s.t(g, "Net-(U3-TS)", "B.Cu", S, [(103.52, 85.82), (104.05, 85.82), (104.35, 86.12), (104.35, 91.92), (107.48, 95.05),
                                        (113.25, 95.05), (113.55, 95.35), (113.55, 102.95), (113.9, 103.3), (116.1, 103.3),
                                        (116.5, 102.9), (116.5, 102.7)])
    s.t(g, "Net-(U5-TS)", "B.Cu", S, [(102.31, 85.82), (102.31, 86.2), (102.7, 86.59), (103.6, 86.59), (103.95, 86.94),
                                        (103.95, 91.95), (107.35, 95.35), (112.5, 95.35), (112.9, 95.75)])
    s.v(g, "Net-(U3-REG25)", (114.45, 102.85))
    s.v(g, "Net-(U3-TS)", (116.5, 102.7))
    s.v(g, "Net-(U5-TS)", (112.9, 95.75))
    s.t(g, "Net-(U3-REG25)", "F.Cu", 0.2, [(115.18, 101.78), (115.18, 102.52), (114.96, 102.73)])
    s.t(g, "Net-(U3-REG25)", "F.Cu", 0.2, [(114.96, 102.73), (114.45, 102.85)])
    s.t(g, "Net-(U3-REG25)", "F.Cu", 0.25, [(114.96, 102.73), (115.88, 103.65), (115.91, 103.65)])
    s.t(g, "Net-(U3-TS)", "F.Cu", 0.25, [(115.68, 101.78), (115.92, 102.03), (115.92, 102.73)])
    s.t(g, "Net-(U3-TS)", "F.Cu", 0.2, [(115.92, 102.73), (116.5, 102.7)])

    # U3 I2C fan-out: the pocket has no B.Cu way out, so a short In2 hop to south of the BAT+ strap
    g = "gauge-i2c"
    s.group(g, "U3 SDA and SCL leave the ball field on In2 (as v3) and land south of the BAT+ strap; autorouted on from there.")
    s.t(g, "/SDA", "F.Cu", 0.2, [(116.18, 100.78), (116.56, 100.78), (116.62, 100.84)])
    s.v(g, "/SDA", (116.62, 100.84), 0.4, 0.2)
    s.t(g, "/SDA", "PWR", 0.15, [(116.62, 100.84), (116.62, 100.93), (115.65, 101.9), (115.65, 104.2), (117.07, 105.62),
                                 (117.78, 105.62), (118.01, 105.85)])
    s.v(g, "/SDA", (118.01, 105.85))
    s.t(g, "/SCL", "F.Cu", 0.2, [(116.18, 101.78), (116.32, 101.78), (116.41, 101.88), (116.41, 102.14)])
    s.v(g, "/SCL", (116.41, 102.14), 0.4, 0.2)
    s.t(g, "/SCL", "PWR", 0.15, [(116.41, 102.14), (116.05, 102.5), (116.05, 104.1), (116.95, 105.0), (117.46, 105.0)])
    s.v(g, "/SCL", (117.46, 105.0))

    # -- long nets through the right rail and the neck -------------------------------------------
    g = "rail-right"
    s.group(g, "RX and TX as on v3 (F.Cu right rail, under U18). I2C to U20 and on through the neck on In2 to CN2, U5 to U15 on "
               "In2, tab to U12: v3 paths, no In1. ePaper RES is new: F.Cu south of the BT1 NPTH to the FPC hop.")
    carry(s, g, base, {"/MCU_RX", "/MCU_TX", "Net-(U16-EN)"})
    carry(s, g, base, {"/SDA", "/SCL"}, box=(133.4, 58.0, 160.0, 104.0), layers=("F.Cu", "B.Cu", "PWR"))
    carry(s, g, base, {"/SDA", "/SCL"}, box=(123.0, 94.0, 138.5, 118.0), layers=("PWR",))
    carry(s, g, base, {"/SDA", "/SCL"}, box=(123.5, 97.0, 125.0, 99.0), vias=False)
    carry(s, g, base, {"/SDA", "/SCL"}, box=(105.0, 133.0, 112.0, 148.0))
    s.t(g, "/SDA", "PWR", 0.2, [(133.66, 70.70), (132.86, 69.9), (130.4, 69.9), (130.2, 70.1), (129.2, 70.1), (128.18, 71.12),
                                (126.39, 71.12), (126.0, 71.51), (126.0, 72.04)])
    s.t(g, "/SCL", "PWR", 0.2, [(133.53, 71.0), (132.78, 70.25), (130.6, 70.25), (130.4, 70.45), (129.6, 70.45), (128.63, 71.42),
                                (126.96, 71.42), (126.79, 71.59), (126.79, 71.83), (127.05, 72.09)])
    s.v(g, "/SDA", (126.0, 72.04))
    s.v(g, "/SCL", (127.05, 72.09))
    s.t(g, "/SDA", "B.Cu", S, [(126.0, 72.04), (125.8, 72.25), (114.25, 72.25), (113.7, 71.7), (113.7, 65.8), (113.4, 65.5), (113.4, 65.44)])
    s.t(g, "/SCL", "B.Cu", S, [(127.05, 72.09), (126.56, 71.6), (114.6, 71.6), (114.0, 71.0), (114.0, 64.84), (113.6, 64.44), (113.4, 64.44)])
    s.v(g, "/SDA", (113.4, 65.44))
    s.v(g, "/SCL", (113.4, 64.44))
    s.t(g, "/SDA", "F.Cu", 0.2, [(113.4, 65.44), (112.32, 65.44)])
    s.t(g, "/SCL", "F.Cu", 0.2, [(113.4, 64.44), (112.32, 64.44)])
    s.t(g, "/ePaper RES", "F.Cu", S, [(145.45, 108.0), (145.45, 94.62), (146.2, 93.87), (155.68, 93.87), (157.8, 91.75), (157.8, 73.5), (156.78, 72.48), (134.6, 72.48), (134.1, 71.98), (134.1, 71.6),
                                      (133.78, 71.28), (133.2, 71.28)])

    # -- U5 pins that face the F.Cu power wall ---------------------------------------------------
    g = "u5-escapes"
    s.group(g, "U5 pins behind the F.Cu power wall. QON crosses the BAT+ strap through the F.Cu gap between REGN and C22. CHG_INT cannot "
               "get south on F or B (TS, TS_BIAS and the SYS and Pack+ pours), so it runs on In2 beside SDA and SCL, as v3 did on B.Cu "
               "round the west end before the NTC lanes took that way. U5-TS keeps its v3 ties and reaches the NTC lane on F.Cu along the battery cut-out.")
    s.t(g, "/QON", "F.Cu", 0.2, [(122.23, 99.43), (122.23, 100.37), (121.68, 100.92), (121.10, 100.92), (120.87, 100.69), (120.62, 100.69)])
    s.v(g, "/QON", (120.62, 100.69))
    s.t(g, "/QON", "B.Cu", 0.2, [(120.62, 100.69), (120.62, 100.84), (120.59, 100.87), (120.59, 101.82), (120.77, 102.0)])
    s.v(g, "/QON", (120.77, 102.0))
    s.t(g, "/QON", "F.Cu", 0.2, [(120.77, 102.0), (120.95, 102.18), (120.95, 104.3)])
    s.v(g, "/QON", (120.95, 104.3))
    s.t(g, "/CHG_INT", "F.Cu", S, [(123.86, 98.69), (124.34, 98.69), (124.71, 99.07)])
    s.v(g, "/CHG_INT", (124.71, 99.07))
    s.t(g, "/CHG_INT", "PWR", S, [(124.71, 99.07), (125.15, 98.63), (125.15, 96.15), (125.45, 95.85), (127.7, 95.85), (128.2, 96.35), (128.2, 99.1),
                                  (128.35, 99.25), (128.35, 102.0), (128.65, 102.3), (128.65, 106.45), (128.35, 106.75), (127.02, 106.75)])
    s.v(g, "/CHG_INT", (127.02, 106.75))
    carry(s, g, base, {"Net-(U5-TS)"}, box=(121.0, 92.0, 130.0, 102.0))
    s.t(g, "Net-(U5-TS)", "F.Cu", S, [(124.72, 92.25), (116.35, 92.25), (112.9, 95.7), (112.9, 95.75)])

    g = "plane-bridges"
    s.group(g, "The In2 lanes and the FPC via row fill the whole neck, so the +3.3V plane comes through in three pieces: top left "
               "(LED1, LED2, CN2, R39, R40), FPC1, and the rest. A 0.2 mm B.Cu link north of the FPC pads and a 0.15 mm B.Cu link south of "
               "the cap vias join them (the v3 board needed the same, group p31-bridge).")
    s.t(g, "+3.3V", "B.Cu", 0.2, [(133.12, 67.58), (133.12, 67.0), (132.74, 66.62), (120.0, 66.62), (119.3, 66.62)])
    s.v(g, "+3.3V", (119.3, 66.62))
    s.t(g, "+3.3V", "B.Cu", S, [(134.59, 71.69), (135.38, 72.48), (144.2, 72.48), (144.7, 71.98), (144.7, 71.85)])
    s.v(g, "+3.3V", (144.7, 71.85))

    # -- LED lanes on In2 through the FPC neck --------------------------------------------------
    g = "led-in2"
    s.group(g, "LED1 and LED2 from U20: the neck has no room on F/B beside the FPC rows, so all six run on In2 (LED2 was on "
               "In1, which now carries no signal). Slow PWM lines, 0.15 mm at 0.28 pitch, In1 GND is their reference.")
    carry(s, g, base, {"/LED_1_B", "/LED_1_G", "/LED_1_R", "/LED_2_B", "/LED_2_G", "/LED_2_R"})
    p = "PWR"
    s.t(g, "/LED_2_R", p, S, [(144.54, 61.15), (144.54, 61.45), (143.97, 62.02), (139.26, 62.02), (138.4, 62.88), (138.4, 66.25),
                              (138.1, 66.55), (122.2, 66.55), (121.35, 65.7), (121.35, 63.0), (121.76, 62.59), (126.19, 62.59),
                              (126.62, 62.16), (126.62, 61.57)])
    s.t(g, "/LED_2_G", p, S, [(145.44, 61.37), (144.49, 62.33), (139.38, 62.33), (138.7, 63.0), (138.7, 66.53), (138.4, 66.83),
                              (121.93, 66.83), (121.05, 65.95), (121.05, 62.19), (121.36, 61.88), (122.42, 61.88)])
    s.t(g, "/LED_2_B", p, S, [(146.24, 61.89), (146.09, 62.04), (145.44, 62.04), (144.86, 62.62), (139.51, 62.62), (139.0, 63.13),
                              (139.0, 66.81), (138.7, 67.11), (121.65, 67.11), (120.75, 66.21), (120.75, 61.91), (121.33, 61.33),
                              (123.03, 61.33), (123.57, 61.87)])
    s.t(g, "/LED_1_B", p, S, [(141.11, 66.09), (141.11, 66.31), (140.03, 67.39), (121.39, 67.39), (120.45, 66.45), (120.45, 62.66),
                              (119.04, 61.25), (113.48, 61.25), (112.87, 60.64)])
    s.t(g, "/LED_1_G", p, S, [(141.08, 66.98), (141.08, 67.05), (140.46, 67.67), (121.22, 67.67), (120.15, 66.6), (120.15, 62.97),
                              (118.73, 61.55), (111.7, 61.55), (111.45, 61.8)])
    s.t(g, "/LED_1_R", p, S, [(141.0, 67.8), (140.85, 67.95), (121.05, 67.95), (119.85, 66.75), (119.85, 63.1), (118.6, 61.85),
                              (113.43, 61.85), (113.03, 62.25), (110.65, 62.25), (110.31, 61.91)])
    plane_fabric(s, base)
    s.stitch = {"net": "GND", "pitch": 5.0, "margin": 0.8, "edge_pitch": 6.0}
    return s


def _seg_d(p, a, b):
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / l2))
    return ((p[0] - ax - t * dx) ** 2 + (p[1] - ay - t * dy) ** 2) ** 0.5


def _seg_seg(a, b, c, d):
    def cross(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    hit = cross(a, b, c) * cross(a, b, d) < 0 and cross(c, d, a) * cross(c, d, b) < 0
    return 0.0 if hit else min(_seg_d(a, c, d), _seg_d(b, c, d), _seg_d(c, a, b), _seg_d(d, a, b))


def plane_fabric(s: Spec, base: pcbnew.BOARD) -> None:
    """The decoupling and return vias and their pad stubs stay where they were on v3, unless new copper took the spot."""
    g = "plane-fabric"
    s.group(g, "GND and +3.3V vias with their stubs, copied from v3 except where the new lanes need the spot. "
               "The autorouter gets no pins on these two nets; vias reach In1 and In2 directly.")
    hand_t, hand_v = [], []
    for grp in s.groups.values():
        for t in grp["tracks"]:
            for a, b in zip(t["path"], t["path"][1:]):
                hand_t.append((t["net"], t["layer"], t["width"] / 2, a, b))
        for v in grp["vias"]:
            hand_v.append((v["net"], v["at"], v["size"] / 2))
    gap = 0.1
    have = {tuple(v["at"]) for grp in s.groups.values() for v in grp["vias"]}
    for it in base.GetTracks():
        net = it.GetNetname()
        if net not in ("GND", "+3.3V"):
            continue
        if it.GetClass() == "PCB_VIA":
            p = it.GetPosition()
            at = loc((mm(p.x), mm(p.y)))
            if any(abs(at[0] - c[0]) < 0.05 and abs(at[1] - c[1]) < 0.05 for c in have):
                continue
            if net == "GND" and 16.3 < at[0] < 16.9 and 1.3 < at[1] < 1.9:
                continue    # beside CN2.6: with its neighbour it shut the In2 way to the LED2 corner
            r = mm(it.GetWidth(pcbnew.F_Cu)) / 2
            if any(n != net and _seg_d(at, a, b) < w + r + gap for n, _, w, a, b in hand_t):
                continue
            if any(n != net and ((at[0] - c[0]) ** 2 + (at[1] - c[1]) ** 2) ** 0.5 < cr + r + gap for n, c, cr in hand_v):
                continue
            s.groups[g]["vias"].append({"net": net, "at": at, "size": r * 2, "drill": mm(it.GetDrill())})
        else:
            layer = LAYER[it.GetLayer()]
            if layer not in ("F.Cu", "B.Cu"):
                continue
            a0, b0 = it.GetStart(), it.GetEnd()
            if net == "+3.3V" and layer == "F.Cu" and 121.0 < mm(a0.x) < 133.5 and 66.0 < mm(a0.y) < 70.0:
                continue    # the v3 F.Cu bridge R40.1 to FPC1: In2 is whole again
            a, b = loc((mm(a0.x), mm(a0.y))), loc((mm(b0.x), mm(b0.y)))
            if a == b:
                continue
            w = mm(it.GetWidth()) / 2
            if any(n != net and l == layer and _seg_seg(a, b, c, d) < w + cw + gap for n, l, cw, c, d in hand_t):
                continue
            if any(n != net and min(_seg_d(c, a, b), 1e9) < w + cr + gap for n, c, cr in hand_v):
                continue
            s.groups[g]["tracks"].append({"net": net, "layer": layer, "width": w * 2, "path": [a, b]})


def strip(board: pcbnew.BOARD) -> tuple[int, int]:
    groups = [g for g in board.Groups() if g.GetName().startswith("route:")]
    for g in groups:
        g.RemoveAll()
        board.Delete(g)
    n = 0
    for t in list(board.GetTracks()):
        board.Delete(t)
        n += 1
    z = 0
    for x in list(board.Zones()):
        board.Delete(x)
        z += 1
    return n, z


def main() -> int:
    src, out = sys.argv[1], sys.argv[2]
    board = pcbnew.LoadBoard(src)
    spec = build(board)
    (HERE / "route.json").write_text(json.dumps({"groups": spec.groups, "stitch": spec.stitch}, indent=1))

    old = json.loads((HERE / "planes_v3_old.json").read_text())
    plist = planes(old)
    (HERE / "planes.json").write_text(json.dumps({"zones": plist, "keepouts": KEEPOUTS}, indent=1))
    n, z = strip(board)
    apply_zones(board, plist)
    board.Save(out)
    print(f"stripped {n} tracks and vias, {z} zones; {len(plist)} zones and {len(KEEPOUTS)} keepouts drawn; "
          f"{sum(len(g['tracks']) for g in spec.groups.values())} track runs, "
          f"{sum(len(g['vias']) for g in spec.groups.values())} vias in {len(spec.groups)} groups")
    return 0


if __name__ == "__main__":
    sys.exit(main())
