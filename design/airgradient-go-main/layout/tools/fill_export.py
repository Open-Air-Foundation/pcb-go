import json, sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
LN = {pcbnew.F_Cu: "F", pcbnew.In1_Cu: "I1", pcbnew.In2_Cu: "I2", pcbnew.B_Cu: "B"}
items = []
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        p = t.GetPosition()
        items.append({"k": "v", "net": t.GetNetname(), "x": p.x / 1e6, "y": p.y / 1e6, "r": t.GetWidth(pcbnew.F_Cu) / 2e6,
                      "h": t.GetDrill() / 1e6, "layers": ["F", "I1", "I2", "B"]})
    else:
        s, e = t.GetStart(), t.GetEnd()
        items.append({"k": "t", "net": t.GetNetname(), "x1": s.x / 1e6, "y1": s.y / 1e6, "x2": e.x / 1e6, "y2": e.y / 1e6,
                      "w": t.GetWidth() / 1e6, "layers": [LN[t.GetLayer()]]})
for f in b.GetFootprints():
    for p in f.Pads():
        bb = p.GetBoundingBox()
        c = p.GetPosition()
        ls = [n for l, n in LN.items() if p.IsOnLayer(l)]
        hole = p.GetDrillSize().x > 0
        if hole and not ls:
            ls = ["F", "B"]
        items.append({"k": "p", "net": p.GetNetname(), "x": c.x / 1e6, "y": c.y / 1e6, "l": bb.GetX() / 1e6, "t": bb.GetY() / 1e6,
                      "r2": bb.GetRight() / 1e6, "b": bb.GetBottom() / 1e6, "layers": ls, "hole": hole, "ref": f.GetReference() + "." + p.GetNumber()})
def pts(z):
    o = z.Outline().Outline(0)
    return [(o.CPoint(i).x / 1e6, o.CPoint(i).y / 1e6) for i in range(o.PointCount())]
zones, rules = [], []
def add(z):
    ls = [LN[l] for l in z.GetLayerSet().Seq() if l in LN]
    if z.GetIsRuleArea():
        rules.append({"name": z.GetZoneName(), "pts": pts(z), "layers": ls, "noT": z.GetDoNotAllowTracks(), "noV": z.GetDoNotAllowVias()})
    elif z.GetNetname() != "GND":
        zones.append({"pts": pts(z), "layers": ls, "net": z.GetNetname()})
for z in b.Zones():
    add(z)
for f in b.GetFootprints():
    for z in f.Zones():
        add(z)
ps = pcbnew.SHAPE_POLY_SET()
b.GetBoardPolygonOutlines(ps, False)
def line(o):
    return [(o.CPoint(i).x / 1e6, o.CPoint(i).y / 1e6) for i in range(o.PointCount())]
out = {"items": items, "zones": zones, "rules": rules, "outline": line(ps.Outline(0)), "holes": [line(ps.Hole(0, h)) for h in range(ps.HoleCount(0))]}
json.dump(out, open(sys.argv[2], "w"))
