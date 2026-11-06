import json, math, sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
d = json.load(open(sys.argv[2]))
ni = b.FindNet(d["net"])
L = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu}
nm = lambda v: int(round(v * 1e6))
tracks = d["tracks"]

def split_at(it, x, y):
    """End a new track exactly on a joint of the track it meets, so the join is end to end."""
    x1, y1, x2, y2 = it["x1"], it["y1"], it["x2"], it["y2"]
    dx, dy = x2 - x1, y2 - y1
    l2 = dx * dx + dy * dy
    u = 0 if l2 == 0 else max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / l2))
    px, py = x1 + u * dx, y1 + u * dy
    if u < 1e-3:
        return x1, y1
    if u > 1 - 1e-3:
        return x2, y2
    layer = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu}[it["layers"][0]]
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" or t.GetLayer() != layer or t.GetNetname() != it["net"]:
            continue
        s, e = t.GetStart(), t.GetEnd()
        if abs(s.x - nm(x1)) < 3 and abs(s.y - nm(y1)) < 3 and abs(e.x - nm(x2)) < 3 and abs(e.y - nm(y2)) < 3:
            n = pcbnew.PCB_TRACK(b)
            n.SetStart(pcbnew.VECTOR2I(nm(px), nm(py)))
            n.SetEnd(pcbnew.VECTOR2I(e.x, e.y))
            n.SetWidth(t.GetWidth())
            n.SetLayer(layer)
            n.SetNet(t.GetNet())
            n.SetLocked(t.IsLocked())
            b.Add(n)
            t.SetEnd(pcbnew.VECTOR2I(nm(px), nm(py)))
            return px, py
    return px, py

for sn in d["snap"]:
    it = sn["it"]
    if not it or not tracks:
        continue
    tr = tracks[0] if sn["at"] == "start" else tracks[-1]
    i = 0 if sn["at"] == "start" else -1
    x, y = tr["pts"][i]
    if it["k"] == "t":
        tr["pts"][i] = list(split_at(it, x, y))
    elif it["k"] == "v":
        tr["pts"][i] = [it["x"], it["y"]]
    else:
        tr["pts"][i] = [it["x"], it["y"]]

for t in tracks:
    for p, q in zip(t["pts"], t["pts"][1:]):
        if p == q:
            continue
        n = pcbnew.PCB_TRACK(b)
        n.SetStart(pcbnew.VECTOR2I(nm(p[0]), nm(p[1])))
        n.SetEnd(pcbnew.VECTOR2I(nm(q[0]), nm(q[1])))
        n.SetWidth(nm(d["width"]))
        n.SetLayer(L[t["layer"]])
        n.SetNet(ni)
        b.Add(n)
for v in d["vias"]:
    n = pcbnew.PCB_VIA(b)
    n.SetViaType(pcbnew.VIATYPE_THROUGH)
    n.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    n.SetPosition(pcbnew.VECTOR2I(nm(v[0]), nm(v[1])))
    n.SetWidth(nm(d["via"][0]))
    n.SetDrill(nm(d["via"][1]))
    n.SetNet(ni)
    b.Add(n)
b.Save(sys.argv[1])
print("applied", sum(len(t["pts"]) - 1 for t in tracks), "segments", len(d["vias"]), "vias")
