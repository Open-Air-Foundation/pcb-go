"""Remove named copper runs of one net, for route_chain.py. Runs under KiCad's Python.

  chain_cut.py BOARD OPS.json
OPS is a list of:
  {"net", "cut": [layer, A, B]}      walk tracks on layer from point A to point B and delete them; B may be a pad "R26.1"
  {"net", "add_via": [x, y]}         through via 0.5/0.3
  {"net", "add_track": [layer, width, [[x, y], ...]]}
  {"net", "clean": true}             delete a via whose tracks all sit on one layer and meet at its centre
  {"net", "tee": [layer, [x, y], [dx, dy], width]}   stub out of a track, at its joint there or at a split made there
  {"net", "chamfer": [layer, [x, y], d]}             cut a corner to 45 degrees, d back along both arms
  {"net", "rename": ["U1.5", "/NAND MOSI"]}          move the copper still joined to that pad onto the new net
Any via left with no track on it after a cut is deleted. Stops if a walk cannot finish.
"""
import json
import math
import sys

import pcbnew

TOL = 0.02
LAYERS = {"F": pcbnew.F_Cu, "I2": pcbnew.In2_Cu, "B": pcbnew.B_Cu}


def mm(v):
    return (v.x / 1e6, v.y / 1e6)


def near(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1]) <= TOL


def find_pad(board, name):
    ref, num = name.split(".")
    for pad in board.FindFootprintByReference(ref).Pads():
        if pad.GetNumber() == num:
            return pad
    raise SystemExit(f"no pad {name}")


def cut(board, net, layer, a, b):
    tracks = [t for t in board.GetTracks()
              if t.GetClass() != "PCB_VIA" and t.GetNetname() == net and t.GetLayer() == LAYERS[layer]]
    target = find_pad(board, b) if isinstance(b, str) else None

    def arrived(p):
        if target:
            return target.HitTest(pcbnew.VECTOR2I(int(p[0] * 1e6), int(p[1] * 1e6)))
        return near(p, b)

    # breadth first: at a junction both arms are tried and the one that reaches B wins
    frontier, gone = [(tuple(a), [])], None
    while frontier and gone is None:
        cur, walked = frontier.pop(0)
        if arrived(cur) and walked:
            gone = walked
            break
        for t in tracks:
            if t in walked:
                continue
            if near(mm(t.GetStart()), cur):
                frontier.append((mm(t.GetEnd()), walked + [t]))
            elif near(mm(t.GetEnd()), cur):
                frontier.append((mm(t.GetStart()), walked + [t]))
    if gone is None:
        raise SystemExit(f"{net} {layer} {a}->{b}: no run")
    ends = [mm(t.GetStart()) for t in gone] + [mm(t.GetEnd()) for t in gone]
    length = sum(t.GetLength() for t in gone) / 1e6
    for t in gone:
        board.Delete(t)
    return ends, length


def drop_orphans(board, net, ends):
    tracks = [t for t in board.GetTracks() if t.GetClass() != "PCB_VIA" and t.GetNetname() == net]
    for v in [v for v in board.GetTracks() if v.GetClass() == "PCB_VIA" and v.GetNetname() == net]:
        c = mm(v.GetPosition())
        if not any(near(c, e) for e in ends):
            continue
        r = v.GetWidth(pcbnew.F_Cu) / 2e6
        touching = any(math.hypot(c[0] - p[0], c[1] - p[1]) <= r for t in tracks for p in (mm(t.GetStart()), mm(t.GetEnd())))
        if not touching:
            board.Delete(v)
            print(f"  via gone {net} ({c[0]:.2f},{c[1]:.2f})")


def add_via(board, net, x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetPosition(pcbnew.VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6))))
    v.SetWidth(500000)
    v.SetDrill(300000)
    v.SetNet(board.FindNet(net))
    board.Add(v)


def add_track(board, net, layer, width, pts):
    for p, q in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(int(round(p[0] * 1e6)), int(round(p[1] * 1e6))))
        t.SetEnd(pcbnew.VECTOR2I(int(round(q[0] * 1e6)), int(round(q[1] * 1e6))))
        t.SetWidth(int(round(width * 1e6)))
        t.SetLayer(LAYERS[layer])
        t.SetNet(board.FindNet(net))
        board.Add(t)


def on_layer(board, net, layer):
    return [t for t in board.GetTracks()
            if t.GetClass() != "PCB_VIA" and t.GetNetname() == net and t.GetLayer() == LAYERS[layer]]


def tee(board, net, layer, at, step, width):
    tracks = on_layer(board, net, layer)
    joint = next((p for t in tracks for p in (mm(t.GetStart()), mm(t.GetEnd())) if near(p, at)), None)
    if joint is None:
        for t in tracks:
            a, b = mm(t.GetStart()), mm(t.GetEnd())
            dx, dy = b[0] - a[0], b[1] - a[1]
            u = ((at[0] - a[0]) * dx + (at[1] - a[1]) * dy) / (dx * dx + dy * dy)
            p = (a[0] + u * dx, a[1] + u * dy)
            if 0 < u < 1 and near(p, at):
                add_track(board, net, layer, t.GetWidth() / 1e6, [p, b])
                t.SetEnd(pcbnew.VECTOR2I(int(round(p[0] * 1e6)), int(round(p[1] * 1e6))))
                joint = p
                break
    if joint is None:
        raise SystemExit(f"{net} {layer}: no track at {at}")
    add_track(board, net, layer, width, [joint, (joint[0] + step[0], joint[1] + step[1])])


def chamfer(board, net, layer, at, d):
    arms = [t for t in on_layer(board, net, layer) if near(mm(t.GetStart()), at) or near(mm(t.GetEnd()), at)]
    if len(arms) != 2:
        raise SystemExit(f"{net} {layer} {at}: {len(arms)} tracks, chamfer needs 2")
    new = []
    for t in arms:
        start_here = near(mm(t.GetStart()), at)
        p, far = (mm(t.GetStart()), mm(t.GetEnd())) if start_here else (mm(t.GetEnd()), mm(t.GetStart()))
        L = math.hypot(far[0] - p[0], far[1] - p[1])
        if L <= d:
            raise SystemExit(f"{net} {layer} {at}: arm {L:.2f} mm is shorter than the chamfer")
        q = (p[0] + (far[0] - p[0]) * d / L, p[1] + (far[1] - p[1]) * d / L)
        v = pcbnew.VECTOR2I(int(round(q[0] * 1e6)), int(round(q[1] * 1e6)))
        t.SetStart(v) if start_here else t.SetEnd(v)
        new.append(q)
    add_track(board, net, layer, min(t.GetWidth() for t in arms) / 1e6, new)


def rename(board, net, pad_name, new):
    """Flood from a pad through the old net's tracks and vias. Run after the cuts that separate the branches."""
    pad = find_pad(board, pad_name)
    items = [t for t in board.GetTracks() if t.GetNetname() == net]
    def is_via(t):
        return t.GetClass() == "PCB_VIA"
    def ends(t):
        return [mm(t.GetPosition())] if is_via(t) else [mm(t.GetStart()), mm(t.GetEnd())]
    def joined(a, c):
        if is_via(a) or is_via(c):
            v, o = (a, c) if is_via(a) else (c, a)
            r = v.GetWidth(pcbnew.F_Cu) / 2e6
            return any(math.hypot(mm(v.GetPosition())[0] - p[0], mm(v.GetPosition())[1] - p[1]) <= r for p in ends(o))
        return a.GetLayer() == c.GetLayer() and any(near(p, q) for p in ends(a) for q in ends(c))
    seen = [t for t in items if any(pad.HitTest(pcbnew.VECTOR2I(int(p[0] * 1e6), int(p[1] * 1e6))) and (is_via(t) or pad.IsOnLayer(t.GetLayer())) for p in ends(t))]
    todo = list(seen)
    while todo:
        cur = todo.pop()
        for t in items:
            if t not in seen and joined(cur, t):
                seen.append(t); todo.append(t)
    info = board.FindNet(new)
    for t in seen:
        t.SetNet(info)
    print(f"  renamed {len(seen)} items from {pad_name} to {new}; {len(items) - len(seen)} left on {net}")


def clean(board, net):
    tracks = [t for t in board.GetTracks() if t.GetClass() != "PCB_VIA" and t.GetNetname() == net]
    for v in [v for v in board.GetTracks() if v.GetClass() == "PCB_VIA" and v.GetNetname() == net]:
        c = mm(v.GetPosition())
        r = v.GetWidth(pcbnew.F_Cu) / 2e6
        on = [(t.GetLayer(), p) for t in tracks for p in (mm(t.GetStart()), mm(t.GetEnd()))
              if math.hypot(c[0] - p[0], c[1] - p[1]) <= r]
        if len({l for l, _ in on}) == 1 and all(math.hypot(c[0] - p[0], c[1] - p[1]) < 0.002 for _, p in on):
            board.Delete(v)
            print(f"  one-layer via gone {net} ({c[0]:.2f},{c[1]:.2f})")


def main():
    board = pcbnew.LoadBoard(sys.argv[1])
    ends = {}
    for op in json.load(open(sys.argv[2])):
        net = op["net"]
        if "cut" in op:
            layer, a, b = op["cut"]
            got, length = cut(board, net, layer, a, b)
            ends.setdefault(net, []).extend(got)
            print(f"  cut {net} {layer} {a} -> {b}: {length:.1f} mm")
        if "add_via" in op:
            add_via(board, net, *op["add_via"])
        if "add_track" in op:
            add_track(board, net, *op["add_track"])
        if "tee" in op:
            tee(board, net, *op["tee"])
        if "chamfer" in op:
            chamfer(board, net, *op["chamfer"])
        if "rename" in op:
            rename(board, net, *op["rename"])
        if op.get("clean"):
            clean(board, net)
    for net, got in ends.items():
        drop_orphans(board, net, got)
    board.Save(sys.argv[1])


main()
