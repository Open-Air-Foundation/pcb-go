"""3D contact sweep: every part's model against every other model on the board. Needs numpy (KiCad's Python has it).

  kicad-cli pcb export glb --subst-models --include-tracks --no-dnp -o board.glb BOARD
  clash_sweep.py board.glb [margin_mm]

The box of each part's model, grown by the margin on every side, is tested against the triangles of every other
part's model (exact box-triangle test). Models above BIG (the battery holder, the enclosure part) are tested as
triangles only, never as a box. The board's own layers are left out.
A hit is a candidate, not a verdict: a box is larger than the part in it (U16's reaches under the end of the
holder, which passes 1.7 mm clear of the sensor there). Run it with margin 0 and 0.3 after a part is placed or
moved on either side: R-V3-34 was C86 under the holder's foot on the front, after a check of the back only.
"""
import json
import struct
import sys

import numpy as np

CT = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
NC = {"SCALAR": 1, "VEC3": 3}
BIG = 2000          # mm3 of a model's box


def load(path):
    """KiCad's glTF export as [(name, triangles Nx3x3)] in the board's frame: x right, y down, z up, mm."""
    glb = open(path, "rb").read()
    jlen = struct.unpack("<I", glb[12:16])[0]
    g = json.loads(glb[20:20 + jlen])
    off = 20 + jlen
    blen = struct.unpack("<I", glb[off:off + 4])[0]
    binbuf = glb[off + 8:off + 8 + blen]
    nodes, meshes, acc, views = g["nodes"], g.get("meshes", []), g["accessors"], g["bufferViews"]

    def read(ai):
        a = acc[ai]
        view = views[a["bufferView"]]
        dt, n = CT[a["componentType"]], NC[a["type"]]
        start = view.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = view.get("byteStride", 0)
        if stride and stride != n * np.dtype(dt).itemsize:
            raw = np.frombuffer(binbuf, np.uint8, count=stride * a["count"], offset=start).reshape(a["count"], stride)
            return raw[:, :n * np.dtype(dt).itemsize].copy().view(dt).reshape(a["count"], n)
        return np.frombuffer(binbuf, dt, count=a["count"] * n, offset=start).reshape(a["count"], n)

    def trs(nd):
        if "matrix" in nd:
            return np.array(nd["matrix"], float).reshape(4, 4).T
        x, y, z, w = nd.get("rotation", [0, 0, 0, 1])
        sc, t = nd.get("scale", [1, 1, 1]), nd.get("translation", [0, 0, 0])
        r = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        m = np.eye(4)
        m[:3, :3] = r * np.array(sc)
        m[:3, 3] = t
        return m

    def tris(i, m, out):
        nd = nodes[i]
        m = m @ trs(nd)
        for prim in meshes[nd["mesh"]]["primitives"] if "mesh" in nd else []:
            if prim.get("mode", 4) != 4:
                continue
            p = read(prim["attributes"]["POSITION"]).astype(float)
            p = (np.c_[p, np.ones(len(p))] @ m.T)[:, :3]
            p = np.c_[p[:, 0], p[:, 2], p[:, 1]] * 1e3          # glTF has y up and metres
            idx = read(prim["indices"]).ravel() if "indices" in prim else np.arange(len(p))
            out.append(p[idx.reshape(-1, 3)])
        for c in nd.get("children", []):
            tris(c, m, out)

    inst = []
    for root in g["scenes"][g.get("scene", 0)]["nodes"]:
        top = nodes[root]
        for c in top.get("children", []) if "mesh" not in top else [root]:
            out = []
            tris(c, trs(top) if c != root else np.eye(4), out)
            if out:
                inst.append((nodes[c].get("name", "?"), np.concatenate(out)))
    return inst


def tri_box(T, lo, hi):
    """Which triangles of T (Nx3x3) meet the box lo..hi (separating-axis test: 3 box axes, the normal, 9 cross axes)."""
    c, h = (lo + hi) / 2, (hi - lo) / 2
    v = T - c
    e = [v[:, 1] - v[:, 0], v[:, 2] - v[:, 1], v[:, 0] - v[:, 2]]
    hit = np.ones(len(T), bool)
    for k in range(3):
        hit &= ~((v[:, :, k].min(1) > h[k]) | (v[:, :, k].max(1) < -h[k]))
    n = np.cross(e[0], e[1])
    hit &= np.abs(np.einsum("ij,ij->i", n, v[:, 0])) <= np.abs(n) @ h
    for ei in e:
        for k in range(3):
            a = np.zeros_like(ei)
            if k == 0:
                a[:, 1], a[:, 2] = -ei[:, 2], ei[:, 1]
            elif k == 1:
                a[:, 0], a[:, 2] = ei[:, 2], -ei[:, 0]
            else:
                a[:, 0], a[:, 1] = -ei[:, 1], ei[:, 0]
            p = np.einsum("ijk,ik->ij", v, a)
            r = np.abs(a) @ h
            hit &= ~((p.min(1) > r) | (p.max(1) < -r))
    return hit


margin = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
inst = [(n, T, T.reshape(-1, 3).min(0), T.reshape(-1, 3).max(0)) for n, T in load(sys.argv[1]) if not n.startswith("=>")]
big = {n for n, T, lo, hi in inst if np.prod(hi - lo) > BIG}
print(len(inst), "models; triangles only:", ", ".join(sorted(big)))
found = 0
for n, T, lo, hi in inst:
    if n in big:
        continue
    slo, shi = lo - margin, hi + margin
    for n2, T2, lo2, hi2 in inst:
        if n2 == n or not (np.all(shi > lo2) and np.all(slo < hi2)):
            continue
        if n2 not in big and n2 < n:
            continue                                            # two small parts: once
        m = np.all(T2.max(1) >= slo, 1) & np.all(T2.min(1) <= shi, 1)
        k = int(tri_box(T2[m], slo, shi).sum()) if m.any() else 0
        if k:
            found += 1
            print(f"  {n:6s} box x {lo[0]:.2f}..{hi[0]:.2f} y {lo[1]:.2f}..{hi[1]:.2f} z {lo[2]:.2f}..{hi[2]:.2f}  meets {n2} ({k} triangles)")
print(f"pairs with margin {margin}: {found}")
