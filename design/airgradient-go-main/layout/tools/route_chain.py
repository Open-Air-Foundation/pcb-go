#!/usr/bin/env python3
"""Turn a branched signal net into one chain: cut named runs, then join named ends pad to pad on F.Cu and B.Cu.

fill_net.py may land on any copper of the net, which makes a new T. Here a link starts and ends only on the named
pad or via, and every other piece of the same net is an obstacle, so a pad gets a second track and no junction appears.
  python3 route_chain.py BOARD PLAN.json [--only NET]
PLAN: {"nets": [{"net": "/SDA", "cuts": [[layer, A, B], ...]}], "links": [["/SDA", "U5.12", "CN2.2"], ["/SDA", "R1.1", "via:1.0,2.0"], ["/SDA", "R1.1", "pt:B:1.0,2.0"]]}
Links run in the order given. A "pt" end is the free end a cut or a tee left behind, on the named layer; "pt:F:1.0,2.0:S" also keeps the heading of the stub it starts from.
"""
import argparse
import heapq
import json
import math
import os
import subprocess
import sys
import tempfile

import numpy as np

from fill_net import CL, EDGE, KPY, ST, dbox, dseg, inpoly

HERE = os.path.dirname(os.path.abspath(__file__))
VD, VH = 0.5, 0.3
VR = VD / 2
LAY = {"F": 0, "B": 3}
TOUCH = 0.03        # gap kept to the net's own copper, so a link never lands on it by accident
ESCAPE = 0.3        # own tracks are passable this far around a link's own end: two tracks leave one pad here
SHARE_COST = 0.5    # per cell inside that box on top of an own track, so the two tracks part at the pad
NO_COPPER_RULES = ("gnss-antenna", "l2-noplane")    # noTracks is off in the file, but nothing may run here
NO_B_OVER = ("/SW",)                                # B.Cu faces In2: no signal on top of the In2 switch node
VIA_COST = 6.0
MARGINS = (10.0, 30.0)
WIDTHS = (0.2, 0.15)


def run_kpy(*args):
    r = subprocess.run([KPY, *args], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"{args[0]} failed: {r.stdout[-400:]} {r.stderr[-400:]}")
    return r.stdout


def export(board):
    with tempfile.TemporaryDirectory() as tmp:
        js = os.path.join(tmp, "o.json")
        run_kpy(os.path.join(HERE, "fill_export.py"), board, js)
        return json.load(open(js))


def find_end(d, net, name):
    if name.startswith("pt:"):
        _, layer, xy, *heading = name.split(":")
        x, y = [float(v) for v in xy.split(",")]
        di = {"E": 0, "S": 2, "W": 4, "N": 6}[heading[0]] if heading else -1
        return {"k": "p", "net": net, "x": x, "y": y, "l": x, "t": y, "r2": x, "b": y, "layers": [layer], "di": di}
    if name.startswith("via:"):
        x, y = [float(v) for v in name[4:].split(",")]
        for i in d["items"]:
            if i["k"] == "v" and i["net"] == net and math.hypot(i["x"] - x, i["y"] - y) < 0.02:
                return i
        raise SystemExit(f"{net}: no via {name}")
    for i in d["items"]:
        if i["k"] == "p" and i.get("ref") == name and i["net"] == net:
            return i
    raise SystemExit(f"{net}: no pad {name}")


class Grid:
    """Blocked cells for one link. The origin sits on the start end, so the first track leaves it on the 45-degree grid."""

    def __init__(self, d, net, a, b, width, margin):
        self.half = width / 2
        boxes = [(a["x"], a["y"]), (b["x"], b["y"])]
        x0 = min(p[0] for p in boxes) - margin
        y0 = min(p[1] for p in boxes) - margin
        self.X0 = a["x"] - round((a["x"] - x0) / ST) * ST
        self.Y0 = a["y"] - round((a["y"] - y0) / ST) * ST
        xs = np.arange(self.X0, max(p[0] for p in boxes) + margin + ST / 2, ST)
        ys = np.arange(self.Y0, max(p[1] for p in boxes) + margin + ST / 2, ST)
        self.GX, self.GY = np.meshgrid(xs, ys)
        self.H, self.W = self.GX.shape
        self.blk = {L: np.zeros(self.GX.shape, bool) for L in (0, 3)}
        self.own = {L: np.zeros(self.GX.shape, bool) for L in (0, 3)}
        self.own_via = {L: np.zeros(self.GX.shape, bool) for L in (0, 3)}
        self.shared = {L: np.zeros(self.GX.shape, bool) for L in (0, 3)}
        self.vb = np.zeros(self.GX.shape, bool)
        self.own_vb = np.zeros(self.GX.shape, bool)
        self._items(d, net, a, b)
        self._zones(d, net)
        self._outline(d)
        self._release(a)
        self._release(b)
        for end in (a, b):     # no via in a link's own pad
            if end["k"] == "p" and end["r2"] > end["l"]:
                self.own_vb |= dbox(self.GX, self.GY, end["l"], end["t"], end["r2"], end["b"]) < VR + 0.05

    def _slice(self, l, t, r, b, pad=1.5):
        return (max(int((t - pad - self.Y0) / ST), 0), min(int((b + pad - self.Y0) / ST) + 2, self.H),
                max(int((l - pad - self.X0) / ST), 0), min(int((r + pad - self.X0) / ST) + 2, self.W))

    def _items(self, d, net, a, b):
        half = self.half
        for i in d["items"]:
            mine = i["net"] == net
            if i is a or i is b:
                continue
            blk, vb = (self.own, self.own_vb) if mine else (self.blk, self.vb)
            gap = TOUCH if mine else CL
            if i["k"] == "t":
                j0, j1, i0, i1 = self._slice(min(i["x1"], i["x2"]), min(i["y1"], i["y2"]), max(i["x1"], i["x2"]), max(i["y1"], i["y2"]))
                if j0 >= j1 or i0 >= i1:
                    continue
                D = dseg(self.GX[j0:j1, i0:i1], self.GY[j0:j1, i0:i1], i["x1"], i["y1"], i["x2"], i["y2"])
                for L in i["layers"]:
                    if L in LAY:
                        blk[LAY[L]][j0:j1, i0:i1] |= D < i["w"] / 2 + half + gap
                # a stub a link starts from may carry the link's first via at its free end
                stub = mine and any(e["k"] == "p" and e["r2"] == e["l"] and any(math.hypot(px - e["x"], py - e["y"]) < 0.01
                                    for px, py in ((i["x1"], i["y1"]), (i["x2"], i["y2"]))) for e in (a, b))
                if not stub:
                    vb[j0:j1, i0:i1] |= D < i["w"] / 2 + (VR + TOUCH if mine else max(VR + CL, VH / 2 + 0.205))
            elif i["k"] == "v":
                j0, j1, i0, i1 = self._slice(i["x"], i["y"], i["x"], i["y"])
                if j0 >= j1 or i0 >= i1:
                    continue
                D = np.hypot(self.GX[j0:j1, i0:i1] - i["x"], self.GY[j0:j1, i0:i1] - i["y"])
                solid = self.own_via if mine else blk
                solid[0][j0:j1, i0:i1] |= D < i["r"] + half + gap
                solid[3][j0:j1, i0:i1] |= D < i["r"] + half + gap
                vb[j0:j1, i0:i1] |= D < max(i["r"] + VR + CL, i["h"] / 2 + VH / 2 + 0.205, i["h"] / 2 + VR + 0.205)
            else:
                j0, j1, i0, i1 = self._slice(i["l"], i["t"], i["r2"], i["b"])
                if j0 >= j1 or i0 >= i1:
                    continue
                D = dbox(self.GX[j0:j1, i0:i1], self.GY[j0:j1, i0:i1], i["l"], i["t"], i["r2"], i["b"])
                # a small holed pad's ring is thin: keep off the hole too. A connector shell pad's copper already covers it
                extra = 0.1 if i.get("hole") and min(i["r2"] - i["l"], i["b"] - i["t"]) < 0.8 else 0
                for L in i["layers"]:
                    if L in LAY:
                        blk[LAY[L]][j0:j1, i0:i1] |= D < half + gap + extra
                if i.get("hole") or "F" in i["layers"] or "B" in i["layers"]:
                    vb[j0:j1, i0:i1] |= D < VR + (0.21 if i.get("hole") else 0.11)

    def _zones(self, d, net):
        for z in d["zones"]:
            if z["net"] == net:
                continue
            m = inpoly(self.GX, self.GY, z["pts"])
            if "F" in z["layers"]:
                self.blk[0] |= m
                self.vb |= m
            if "B" in z["layers"]:
                self.blk[3] |= m
                self.vb |= m
            if "I2" in z["layers"] and z["net"] in NO_B_OVER:
                self.blk[3] |= m
                self.vb |= m
        for z in d["rules"]:
            m = inpoly(self.GX, self.GY, z["pts"])
            named = z.get("name") in NO_COPPER_RULES
            if z["noT"] or named:
                if "F" in z["layers"]:
                    self.blk[0] |= m
                if "B" in z["layers"]:
                    self.blk[3] |= m
            if z["noV"] or named:
                self.vb |= m

    def _outline(self, d):
        inside = inpoly(self.GX, self.GY, d["outline"])
        for h in d["holes"]:
            inside &= ~inpoly(self.GX, self.GY, h)
        for poly in [d["outline"]] + d["holes"]:
            for k, (x1, y1) in enumerate(poly):
                x2, y2 = poly[(k + 1) % len(poly)]
                if max(x1, x2) < self.X0 - 2 or min(y1, y2) > self.GY[-1, 0] + 2 or min(x1, x2) > self.GX[0, -1] + 2 or max(y1, y2) < self.Y0 - 2:
                    continue
                D = dseg(self.GX, self.GY, x1, y1, x2, y2)
                self.blk[0] |= D < self.half + EDGE
                self.blk[3] |= D < self.half + EDGE
                self.vb |= D < VR + EDGE
        self.blk[0] |= ~inside
        self.blk[3] |= ~inside
        self.vb |= ~inside

    def _release(self, end):
        """Own copper does not block inside the escape box of a link's end."""
        if end["k"] == "p":
            m = dbox(self.GX, self.GY, end["l"], end["t"], end["r2"], end["b"]) < ESCAPE
        else:
            m = np.hypot(self.GX - end["x"], self.GY - end["y"]) < end["r"] + ESCAPE
        for L in (0, 3):
            self.shared[L] |= self.own[L] & m
            self.own[L] &= ~m

    def cell(self, x, y):
        return int(round((y - self.Y0) / ST)), int(round((x - self.X0) / ST))

    def layers(self, end):
        if end["k"] == "v":
            return [0, 3]
        return [LAY[L] for L in end["layers"] if L in LAY]


DIRS = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]


def search(g, a, b, limit=8_000_000):
    """A* over (row, col, layer, direction). Bends are 45 degrees; a via may be followed by any direction."""
    r0, c0 = g.cell(a["x"], a["y"])
    r1, c1 = g.cell(b["x"], b["y"])
    goal = {(r1, c1, L) for L in g.layers(b)}
    free = {L: ~(g.blk[L] | g.own[L] | g.own_via[L]) for L in (0, 3)}
    via_ok = ~(g.vb | g.own_vb)
    for L in g.layers(a):
        free[L][r0, c0] = True
    for L in g.layers(b):
        free[L][r1, c1] = True

    def h(r, c):
        dr, dc = abs(r - r1), abs(c - c1)
        return ST * (max(dr, dc) + 0.414 * min(dr, dc))

    pq, best, prev = [], {}, {}
    for L in g.layers(a):
        s = (r0, c0, L, a.get("di", -1))
        best[s] = 0.0
        heapq.heappush(pq, (h(r0, c0), 0.0, s))
    n = 0
    while pq:
        _, cost, s = heapq.heappop(pq)
        if best.get(s, 1e9) < cost - 1e-9:
            continue
        r, c, L, di = s
        if (r, c, L) in goal:
            path = []
            while s is not None:
                path.append(s)
                s = prev.get(s)
            return path[::-1], n
        n += 1
        if n > limit:
            return None, n
        for k, (dr, dc) in enumerate(DIRS):
            if di >= 0 and min((k - di) % 8, (di - k) % 8) > 1:
                continue
            q = (r + dr, c + dc)
            if not (0 <= q[0] < g.H and 0 <= q[1] < g.W) or not free[L][q]:
                continue
            ng = cost + ST * (1.414 if dr and dc else 1) + (0.03 if di >= 0 and k != di else 0) + (SHARE_COST if g.shared[L][q] else 0)
            t = (q[0], q[1], L, k)
            if ng < best.get(t, 1e9) - 1e-9:
                best[t] = ng
                prev[t] = s
                heapq.heappush(pq, (ng + h(*q), ng, t))
        if di >= 0 and via_ok[r, c] and free[3 - L][r, c]:
            t = (r, c, 3 - L, -2)
            ng = cost + VIA_COST
            if ng < best.get(t, 1e9) - 1e-9:
                best[t] = ng
                prev[t] = s
                heapq.heappush(pq, (ng + h(r, c), ng, t))
    return None, n


def to_copper(g, path):
    def straighten(ps):
        out = [ps[0]]
        for i in range(1, len(ps) - 1):
            A, B, C = out[-1], ps[i], ps[i + 1]
            if abs((B[0] - A[0]) * (C[1] - B[1]) - (B[1] - A[1]) * (C[0] - B[0])) > 1e-6:
                out.append(B)
        out.append(ps[-1])
        return out

    pts = [(round(g.X0 + p[1] * ST, 3), round(g.Y0 + p[0] * ST, 3), p[2]) for p in path]
    tracks, vias, cur, lay = [], [], [pts[0][:2]], pts[0][2]
    for x, y, L in pts[1:]:
        if L != lay:
            if len(cur) > 1:
                tracks.append((lay, straighten(cur)))
            vias.append((x, y))
            cur, lay = [(x, y)], L
        else:
            cur.append((x, y))
    if len(cur) > 1:
        tracks.append((lay, straighten(cur)))
    return tracks, vias


def land_square(ps, end):
    """Snapping the last point onto the real end skews the last segment. Slide the point before it along its own
    segment so the last one keeps its grid direction."""
    if len(ps) < 3:
        return
    A, B, C = ps[-3], ps[-2], ps[-1]
    ex, ey = B[0] - A[0], B[1] - A[1]
    dx, dy = C[0] - B[0], C[1] - B[1]
    den = ex * dy - ey * dx
    if abs(den) < 1e-9:
        return
    s = ((end[0] - A[0]) * dy - (end[1] - A[1]) * dx) / den
    if 0.1 < s < 3:
        ps[-2] = (round(A[0] + s * ex, 4), round(A[1] + s * ey, 4))


def route_link(board, d, net, na, nb):
    a, b = find_end(d, net, na), find_end(d, net, nb)
    for margin in MARGINS:
        for width in WIDTHS:
            g = Grid(d, net, a, b, width, margin)
            path, n = search(g, a, b)
            if not path:
                continue
            tracks, vias = to_copper(g, path)
            land_square(tracks[-1][1], (b["x"], b["y"]))
            length = sum(math.hypot(B[0] - A[0], B[1] - A[1]) for _, ps in tracks for A, B in zip(ps, ps[1:]))
            print(f"  link {net} {na} -> {nb}: {length:.1f} mm w{width} vias {len(vias)} ({n} expanded)", flush=True)
            out = {"net": net, "width": width, "via": [VD, VH],
                   "tracks": [{"layer": "F" if l == 0 else "B", "pts": ps} for l, ps in tracks],
                   "vias": vias, "snap": [{"it": a, "at": "start"}, {"it": b, "at": "end"}]}
            with tempfile.TemporaryDirectory() as tmp:
                js = os.path.join(tmp, "p.json")
                json.dump(out, open(js, "w"))
                run_kpy(os.path.join(HERE, "fill_apply.py"), board, js)
            return True
    print(f"  FAILED {net} {na} -> {nb}", flush=True)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("board")
    ap.add_argument("plan")
    ap.add_argument("--only", action="append", default=[])
    a = ap.parse_args()
    plan = json.load(open(a.plan))
    nets = [n for n in plan["nets"] if not a.only or n["net"] in a.only]
    ops = []
    for n in nets:
        ops += [{"net": n["net"], "cut": c} for c in n.get("cuts", [])]
        ops += [{"net": n["net"], "add_via": v} for v in n.get("add_vias", [])]
        ops += [{"net": n["net"], "add_track": t} for t in n.get("add_tracks", [])]
        ops += [{"net": n["net"], "tee": t} for t in n.get("tees", [])]
        ops += [{"net": n["net"], "rename": t} for t in n.get("renames", [])]
    with tempfile.TemporaryDirectory() as tmp:
        js = os.path.join(tmp, "ops.json")
        json.dump(ops, open(js, "w"))
        print(run_kpy(os.path.join(HERE, "chain_cut.py"), a.board, js).strip(), flush=True)
    failed = 0
    wanted = {n["net"] for n in nets} | {r[1] for n in nets for r in n.get("renames", [])}
    for net, na, nb in plan["links"]:
        if net in wanted:
            failed += not route_link(a.board, export(a.board), net, na, nb)
    clean = [{"net": n["net"], "clean": True} for n in nets]
    clean += [{"net": net, "chamfer": [layer, at, d]} for net, layer, at, d in plan.get("post", []) if net in wanted]
    with tempfile.TemporaryDirectory() as tmp:
        js = os.path.join(tmp, "ops.json")
        json.dump(clean, open(js, "w"))
        print(run_kpy(os.path.join(HERE, "chain_cut.py"), a.board, js).strip(), flush=True)
    print("failed links:", failed)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
