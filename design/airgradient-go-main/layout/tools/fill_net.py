#!/usr/bin/env python3
"""Join the split pieces of one net with a 45-degree A* on F.Cu and B.Cu.

Knows what pcb_path does not: power zones on F.Cu, inner-layer tracks (a via must clear them), rule areas.
  python3 fill_net.py BOARD NET [--width 0.15] [--via 0.5,0.3] [--margin 12] [--dry]
"""
import argparse, heapq, json, math, os, subprocess, sys, tempfile
import numpy as np

KPY = "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3"
HERE = os.path.dirname(os.path.abspath(__file__))
ST = 0.05
CL = 0.105       # copper to copper
EDGE = 0.21

def dseg(GX, GY, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L = dx * dx + dy * dy
    u = np.clip(((GX - x1) * dx + (GY - y1) * dy) / L, 0, 1) if L > 0 else 0
    return np.hypot(GX - x1 - u * dx, GY - y1 - u * dy)

def dbox(GX, GY, l, t, r, b):
    return np.hypot(np.maximum(np.maximum(l - GX, GX - r), 0), np.maximum(np.maximum(t - GY, GY - b), 0))

def inpoly(GX, GY, pts):
    c = np.zeros(GX.shape, bool)
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        if y1 == y2:
            continue
        m = ((y1 > GY) != (y2 > GY)) & (GX < (x2 - x1) * (GY - y1) / (y2 - y1) + x1)
        c ^= m
    return c

def components(net, d):
    items = [i for i in d["items"] if i["net"] == net]
    p = list(range(len(items)))
    def f(a):
        while p[a] != a:
            p[a] = p[p[a]]
            a = p[a]
        return a
    def touch(a, b):
        la, lb = set(a["layers"]), set(b["layers"])
        if not la & lb:
            return False
        def pts(i):
            if i["k"] == "t":
                return [(i["x1"], i["y1"]), (i["x2"], i["y2"])]
            return [(i["x"], i["y"])]
        def hit(i, q):
            x, y = q
            if i["k"] == "t":
                return float(dseg(np.array(x), np.array(y), i["x1"], i["y1"], i["x2"], i["y2"])) <= i["w"] / 2 + 1e-4
            if i["k"] == "v":
                return math.hypot(x - i["x"], y - i["y"]) <= i["r"] + 1e-4
            return i["l"] - 1e-4 <= x <= i["r2"] + 1e-4 and i["t"] - 1e-4 <= y <= i["b"] + 1e-4
        return any(hit(b, q) for q in pts(a)) or any(hit(a, q) for q in pts(b))
    for a in range(len(items)):
        for b in range(a + 1, len(items)):
            if f(a) != f(b) and touch(items[a], items[b]):
                p[f(a)] = f(b)
    comp = {}
    for a, it in enumerate(items):
        comp.setdefault(f(a), []).append(it)
    return list(comp.values())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("board"); ap.add_argument("net")
    ap.add_argument("--width", type=float, default=0.15)
    ap.add_argument("--via", default="0.5,0.3")
    ap.add_argument("--margin", type=float, default=12.0)
    ap.add_argument("--viacost", type=float, default=3.0)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--avoid", action="append", default=[], help="x0,y0,x1,y1 abs no-go on both layers")
    a = ap.parse_args()
    VD, VH = [float(v) for v in a.via.split(",")]
    VR = VD / 2
    half = a.width / 2
    with tempfile.TemporaryDirectory() as tmp:
        js = os.path.join(tmp, "o.json")
        subprocess.run([KPY, os.path.join(HERE, "fill_export.py"), a.board, js], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=True)
        d = json.load(open(js))
    for round_ in range(20):
        comps = components(a.net, d)
        if len(comps) < 2:
            print(a.net, "connected")
            return
        comps.sort(key=len)
        src, others = comps[0], [c for c in comps[1:]]
        print(a.net, "pieces", [len(c) for c in comps])
        def bbox(c):
            xs, ys = [], []
            for i in c:
                if i["k"] == "t":
                    xs += [i["x1"], i["x2"]]; ys += [i["y1"], i["y2"]]
                else:
                    xs.append(i["x"]); ys.append(i["y"])
            return min(xs), min(ys), max(xs), max(ys)
        allc = src + [i for c in others for i in c]
        bs = bbox(src)
        bo = [bbox(c) for c in others]
        # window: source plus the nearest other piece, with margin
        def gap(b):
            return max(b[0] - bs[2], bs[0] - b[2], 0) + max(b[1] - bs[3], bs[1] - b[3], 0)
        nb = min(bo, key=gap)
        X0 = min(bs[0], nb[0]) - a.margin; X1 = max(bs[2], nb[2]) + a.margin
        Y0 = min(bs[1], nb[1]) - a.margin; Y1 = max(bs[3], nb[3]) + a.margin
        xs = np.arange(X0, X1 + ST / 2, ST); ys = np.arange(Y0, Y1 + ST / 2, ST)
        GX, GY = np.meshgrid(xs, ys)
        H, W = GX.shape
        blk = {0: np.zeros(GX.shape, bool), 3: np.zeros(GX.shape, bool)}
        vb = np.zeros(GX.shape, bool)
        LAY = {"F": 0, "B": 3, "I1": 1, "I2": 2}
        def sl(l, t, r, b, pad=1.5):
            ja, jb = max(int((t - pad - Y0) / ST), 0), min(int((b + pad - Y0) / ST) + 2, H)
            ia, ib = max(int((l - pad - X0) / ST), 0), min(int((r + pad - X0) / ST) + 2, W)
            return ja, jb, ia, ib
        for i in d["items"]:
            if i["net"] == a.net:
                continue
            if i["k"] == "t":
                j0, j1, i0, i1 = sl(min(i["x1"], i["x2"]), min(i["y1"], i["y2"]), max(i["x1"], i["x2"]), max(i["y1"], i["y2"]))
                if j0 >= j1 or i0 >= i1:
                    continue
                D = dseg(GX[j0:j1, i0:i1], GY[j0:j1, i0:i1], i["x1"], i["y1"], i["x2"], i["y2"])
                for L in i["layers"]:
                    if L in ("F", "B"):
                        blk[LAY[L]][j0:j1, i0:i1] |= D < i["w"] / 2 + half + CL
                vb[j0:j1, i0:i1] |= D < i["w"] / 2 + max(VR + CL, VH / 2 + 0.205)
            elif i["k"] == "v":
                j0, j1, i0, i1 = sl(i["x"], i["y"], i["x"], i["y"])
                if j0 >= j1 or i0 >= i1:
                    continue
                D = np.hypot(GX[j0:j1, i0:i1] - i["x"], GY[j0:j1, i0:i1] - i["y"])
                blk[0][j0:j1, i0:i1] |= D < i["r"] + half + CL
                blk[3][j0:j1, i0:i1] |= D < i["r"] + half + CL
                vb[j0:j1, i0:i1] |= D < max(i["r"] + VR + CL, i["h"] / 2 + VH / 2 + 0.205, i["h"] / 2 + VR + 0.205)
            else:
                j0, j1, i0, i1 = sl(i["l"], i["t"], i["r2"], i["b"])
                if j0 >= j1 or i0 >= i1:
                    continue
                D = dbox(GX[j0:j1, i0:i1], GY[j0:j1, i0:i1], i["l"], i["t"], i["r2"], i["b"])
                extra = 0.1 if i.get("hole") else 0
                for L in i["layers"]:
                    if L in ("F", "B"):
                        blk[LAY[L]][j0:j1, i0:i1] |= D < half + CL + extra
                if i.get("hole") or "F" in i["layers"] or "B" in i["layers"]:
                    vb[j0:j1, i0:i1] |= D < VR + (0.21 if i.get("hole") else 0.11)
        # own-net pads get a mask web against a new via
        for i in d["items"]:
            if i["net"] == a.net and i["k"] == "p":
                j0, j1, i0, i1 = sl(i["l"], i["t"], i["r2"], i["b"])
                if j0 < j1 and i0 < i1:
                    vb[j0:j1, i0:i1] |= dbox(GX[j0:j1, i0:i1], GY[j0:j1, i0:i1], i["l"], i["t"], i["r2"], i["b"]) < VR + 0.05
        for z in d["zones"]:
            if z["net"] == a.net:
                continue
            m = inpoly(GX, GY, z["pts"])
            if "F" in z["layers"]:
                blk[0] |= m
                vb |= m
            if "B" in z["layers"]:
                blk[3] |= m
                vb |= m
        for z in d["rules"]:
            m = inpoly(GX, GY, z["pts"])
            if z["noT"]:
                if "F" in z["layers"]:
                    blk[0] |= m
                if "B" in z["layers"]:
                    blk[3] |= m
            if z["noV"]:
                vb |= m
        inside = inpoly(GX, GY, d["outline"])
        for h in d["holes"]:
            inside &= ~inpoly(GX, GY, h)
        for poly in [d["outline"]] + d["holes"]:
            n = len(poly)
            for k in range(n):
                x1, y1 = poly[k]; x2, y2 = poly[(k + 1) % n]
                if max(x1, x2) < X0 - 2 or min(x1, x2) > X1 + 2 or max(y1, y2) < Y0 - 2 or min(y1, y2) > Y1 + 2:
                    continue
                D = dseg(GX, GY, x1, y1, x2, y2)
                blk[0] |= D < half + EDGE
                blk[3] |= D < half + EDGE
                vb |= D < VR + EDGE
        for L in blk:
            blk[L] |= ~inside
        vb |= ~inside
        for r in a.avoid:
            x0, y0, x1, y1 = [float(v) for v in r.split(",")]
            m = (GX >= x0) & (GX <= x1) & (GY >= y0) & (GY <= y1)
            blk[0] |= m; blk[3] |= m; vb |= m
        def cells(c):
            out = {}
            for i in c:
                if i["k"] == "t":
                    L = LAY.get(i["layers"][0])
                    if L not in (0, 3):
                        continue
                    n = max(2, int(math.hypot(i["x2"] - i["x1"], i["y2"] - i["y1"]) / ST) + 1)
                    for s in range(n):
                        x = i["x1"] + (i["x2"] - i["x1"]) * s / (n - 1)
                        y = i["y1"] + (i["y2"] - i["y1"]) * s / (n - 1)
                        q = (int(round((y - Y0) / ST)), int(round((x - X0) / ST)), L)
                        if 0 <= q[0] < H and 0 <= q[1] < W:
                            out[q] = i
                elif i["k"] == "v":
                    for L in (0, 3):
                        q = (int(round((i["y"] - Y0) / ST)), int(round((i["x"] - X0) / ST)), L)
                        if 0 <= q[0] < H and 0 <= q[1] < W:
                            out[q] = i
                else:
                    for Ln in i["layers"]:
                        if Ln in ("F", "B"):
                            for q0 in ((i["y"], i["x"]),):
                                q = (int(round((q0[0] - Y0) / ST)), int(round((q0[1] - X0) / ST)), LAY[Ln])
                                if 0 <= q[0] < H and 0 <= q[1] < W:
                                    out[q] = i
            return out
        start = cells(src)
        goal = {}
        for c in others:
            goal.update(cells(c))
        if not start or not goal:
            print("no cells in window")
            return
        # free a little room around the ends
        def free(q, r=0.3):
            a_, c_, L = q
            R = int(r / ST)
            for aa in range(max(a_ - R, 0), min(a_ + R + 1, H)):
                for cc in range(max(c_ - R, 0), min(c_ + R + 1, W)):
                    if math.hypot((aa - a_) * ST, (cc - c_) * ST) <= r and inside[aa, cc]:
                        pass
        DIRS = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]
        pq = []; best = {}; prev = {}
        own = {0: np.zeros(GX.shape, bool), 3: np.zeros(GX.shape, bool)}
        for q in list(start) + list(goal):
            # a pad end may sit in a clearance halo of its neighbour: allow the first 0.25 mm
            own[q[2]][q[0], q[1]] = True
        for q in start:
            s = (q[0], q[1], q[2], -1)
            best[s] = 0.0
            heapq.heappush(pq, (0.0, s))
        end = None; n = 0
        while pq:
            g, s = heapq.heappop(pq); n += 1
            if best.get(s, 1e9) < g - 1e-9:
                continue
            aa, cc, L, di = s
            if (aa, cc, L) in goal:
                end = s
                break
            if n > 6000000:
                break
            for k, (da, dc) in enumerate(DIRS):
                if di >= 0 and min((k - di) % 8, (di - k) % 8) > 1:
                    continue
                q = (aa + da, cc + dc)
                if not (0 <= q[0] < H and 0 <= q[1] < W):
                    continue
                if blk[L][q] and not own[L][q]:
                    continue
                ng = g + ST * (1.414 if da and dc else 1) + (0.03 if k != di and di >= 0 else 0)
                t = (q[0], q[1], L, k)
                if ng < best.get(t, 1e9) - 1e-9:
                    best[t] = ng; prev[t] = s; heapq.heappush(pq, (ng, t))
            if not vb[aa, cc] and di >= 0:
                L2 = 3 - L
                t = (aa, cc, L2, -2)
                if not blk[L2][aa, cc] or own[L2][aa, cc]:
                    ng = g + a.viacost
                    if ng < best.get(t, 1e9) - 1e-9:
                        best[t] = ng; prev[t] = s; heapq.heappush(pq, (ng, t))
            if di == -2:
                # just changed layer: any direction next
                for k, (da, dc) in enumerate(DIRS):
                    q = (aa + da, cc + dc)
                    if not (0 <= q[0] < H and 0 <= q[1] < W) or (blk[L][q] and not own[L][q]):
                        continue
                    ng = g + ST * (1.414 if da and dc else 1)
                    t = (q[0], q[1], L, k)
                    if ng < best.get(t, 1e9) - 1e-9:
                        best[t] = ng; prev[t] = s; heapq.heappush(pq, (ng, t))
        print(" expanded", n, "found", end is not None)
        if not end:
            sys.exit(2)
        path = []; s = end
        while s is not None:
            path.append(s); s = prev.get(s)
        path = path[::-1]
        pts = [(round(X0 + p[1] * ST, 3), round(Y0 + p[0] * ST, 3), p[2]) for p in path]
        tracks, vias, cur = [], [], [pts[0][:2]]
        lay = pts[0][2]
        def simp(ps):
            o = [ps[0]]
            for i in range(1, len(ps) - 1):
                A, B, C = o[-1], ps[i], ps[i + 1]
                if abs((B[0] - A[0]) * (C[1] - B[1]) - (B[1] - A[1]) * (C[0] - B[0])) > 1e-6:
                    o.append(B)
            o.append(ps[-1])
            return o
        for x, y, L in pts[1:]:
            if L != lay:
                if len(cur) > 1:
                    tracks.append((lay, simp(cur)))
                vias.append((x, y)); cur = [(x, y)]; lay = L
            else:
                cur.append((x, y))
        if len(cur) > 1:
            tracks.append((lay, simp(cur)))
        # snap both ends onto the copper they join
        def snap(q, table, track_i, at_start):
            it = table.get(q)
            if not it or not tracks:
                return None
            return it
        st_it = start.get(path[0][:3]); en_it = goal.get(path[-1][:3])
        ln = sum(math.hypot(B[0] - A[0], B[1] - A[1]) for _, ps in tracks for A, B in zip(ps, ps[1:]))
        print(f" length {ln:.1f} mm, vias {len(vias)}", vias, [("F" if l == 0 else "B", ps[0], ps[-1]) for l, ps in tracks])
        out = {"net": a.net, "width": a.width, "via": [VD, VH],
               "tracks": [{"layer": "F" if l == 0 else "B", "pts": ps} for l, ps in tracks],
               "vias": vias,
               "snap": [{"it": st_it, "at": "start"}, {"it": en_it, "at": "end"}]}
        if a.dry:
            print(json.dumps(out)[:400])
            return
        with tempfile.TemporaryDirectory() as tmp:
            js = os.path.join(tmp, "p.json")
            json.dump(out, open(js, "w"))
            r = subprocess.run([KPY, os.path.join(HERE, "fill_apply.py"), a.board, js], stderr=subprocess.DEVNULL, stdout=subprocess.PIPE, text=True)
            print(" ", r.stdout.strip()[-200:])
            js2 = os.path.join(tmp, "o.json")
            subprocess.run([KPY, os.path.join(HERE, "fill_export.py"), a.board, js2], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=True)
            d = json.load(open(js2))

if __name__ == "__main__":
    main()
