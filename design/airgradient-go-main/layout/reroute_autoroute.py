#!/usr/bin/env python3
"""pcb_autoroute.py with the changes GO main needs. Same arguments.

- KiCad's DSN export throws on empty or duplicate references (2 unnamed holes, 6 G*** logos, 2 REF**):
  the work copy gets unique names.
- KiCad 10 ImportSpecctraSES fails on this board: a small SES reader adds the tracks and vias instead.
- The GND zone spans F.Cu, B.Cu and In1. The work copy keeps it on In1 only, so GND fans out to the plane.
- Power zones on F.Cu become DSN keepouts, so the router goes round them instead of cutting them. A plane on a
  signal layer is no obstacle in Freerouting.
- GND and +3.3V get no pins in the DSN: their vias are placed by hand, so the router does not join them with tracks.
"""
import os
import re
import sys

sys.path.insert(0, os.path.expanduser("~/.claude/skills/pcb-design/scripts"))
import pcb_autoroute as pa  # noqa: E402
import pcbnew  # noqa: E402


def tokenize(text):
    return re.findall(r'"[^"]*"|\(|\)|[^\s()]+', text)


def parse(tokens):
    stack = [[]]
    for t in tokens:
        if t == "(":
            stack.append([])
        elif t == ")":
            x = stack.pop()
            stack[-1].append(x)
        else:
            stack[-1].append(t.strip('"') if t.startswith('"') else t)
    return stack[0][0]


def find(node, name):
    for c in node:
        if isinstance(c, list) and c and c[0] == name:
            yield c


def fixed(node):
    return any(isinstance(c, list) and c[0] == "type" and c[1] in ("protect", "fix") for c in node)


def import_ses(board, path):
    routes = next(find(parse(tokenize(open(path).read())), "routes"))
    res = next(find(routes, "resolution"))
    k = {"um": 1000.0, "mm": 1e6}[res[1]] / float(res[2])
    layers = {board.GetLayerName(l): l for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)}
    layers.update({"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu})
    for net in find(next(find(routes, "network_out")), "net"):
        ni = board.FindNet(net[1])
        for w in find(net, "wire"):
            if fixed(w):
                continue
            p = next(find(w, "path"))
            nums = [float(v) for v in p[3:] if not isinstance(v, list)]
            pts = [(int(nums[i] * k), int(-nums[i + 1] * k)) for i in range(0, len(nums) - 1, 2)]
            for a, b in zip(pts, pts[1:]):
                if a != b:
                    t = pcbnew.PCB_TRACK(board)
                    t.SetStart(pcbnew.VECTOR2I(*a))
                    t.SetEnd(pcbnew.VECTOR2I(*b))
                    t.SetLayer(layers[p[1]])
                    t.SetWidth(int(float(p[2]) * k))
                    t.SetNet(ni)
                    board.Add(t)
        for v in find(net, "via"):
            if fixed(v):
                continue
            m = re.search(r"_(\d+):(\d+)_um", v[1])
            size, drill = (int(m.group(1)) * 1000, int(m.group(2)) * 1000) if m else (500000, 300000)
            t = pcbnew.PCB_VIA(board)
            t.SetPosition(pcbnew.VECTOR2I(int(float(v[2]) * k), int(-float(v[3]) * k)))
            t.SetWidth(size)
            t.SetDrill(drill)
            t.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            t.SetNet(ni)
            board.Add(t)
    return True


def prepare(board, signal_inner):
    seen, n = set(), 0
    for f in board.GetFootprints():
        r = f.GetReference()
        if not r or r in seen or "*" in r:
            n += 1
            f.SetReference(f"MECH{n}")
        seen.add(f.GetReference())
    in1 = pcbnew.LSET()
    in1.AddLayer(pcbnew.In1_Cu)
    for z in list(board.Zones()):
        if z.GetIsRuleArea():
            if not (z.GetDoNotAllowTracks() or z.GetDoNotAllowVias() or z.GetDoNotAllowPads()):
                board.Delete(z)
        elif z.GetNetname() == "GND" and z.GetLayerSet().Contains(pcbnew.F_Cu):
            z.SetLayerSet(in1)
    notes = [f"{n} mech refs renamed"]
    for layer in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu):
        pa.split_planes(board, layer)
    for layer in (pcbnew.In1_Cu, pcbnew.In2_Cu):
        board.SetLayerType(layer, pcbnew.LT_POWER)
    return notes


_export = pcbnew.ExportSpecctraDSN


def export(board, path):
    if not _export(board, path):
        return False
    text = open(path).read()
    text = re.sub(r'\(plane\s+(?:"[^"]+"|\S+)\s+\(polygon F\.Cu', '(keepout "" (polygon F.Cu', text)
    for net in ("GND", "+3.3V"):
        text, n = re.subn(r'\(net %s\s+\(pins[^)]*\)' % re.escape(net), '(net %s (pins)' % net, text, count=1)
        if not n:
            raise SystemExit(f"no pin list for {net}")
    open(path, "w").write(text)
    return True


pa.prepare = prepare
pcbnew.ExportSpecctraDSN = export
pcbnew.ImportSpecctraSES = import_ses
sys.exit(pa.main())
