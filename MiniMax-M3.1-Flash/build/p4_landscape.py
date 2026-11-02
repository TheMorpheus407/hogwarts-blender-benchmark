"""PASS 3 — landscape: dense conifer forest, worn moorland paths, exposed rock.

Everything is built from scratch: the conifers are cones-and-trunks assembled
in bmesh, scattered from a procedural density field, then merged into chunked
meshes so the outliner stays readable and the BVH stays sane.  Per-tree
variation rides on a "tree" colour attribute (R = per-tree random,
G = height fraction) which the conifer shader reads.
"""
import bpy, bmesh, math, importlib, sys
import numpy as np
from mathutils import Vector, Matrix, Euler
import hg_lib, hg_np, hg_mat, hg_cfg, hg_land
for m in (hg_lib, hg_np, hg_mat, hg_cfg, hg_land):
    importlib.reload(m)
import hg_lib as L
import hg_np as N
import hg_mat as M
import hg_cfg as C
import hg_land as LD

STEP = 8.0                 # candidate scatter spacing (m)
TREE_FRACTION = 0.125      # share of candidates that become a tree
CHUNKS = 3                 # forest is split into CHUNKS x CHUNKS spatial chunks


# ------------------------------------------------------------------ conifers
def _cone(v, f, m, z0, r, z1, sides, mat, twist=0.0, sag=0.0):
    """A closed, slightly drooping foliage cone."""
    base = len(v)
    for i in range(sides):
        a = 2.0 * math.pi * i / sides + twist
        rr = r * (1.0 - 0.18 * ((i * 7) % 5) / 5.0)
        v.append((rr * math.cos(a), rr * math.sin(a), z0 - sag))
    apex = len(v)
    v.append((0.0, 0.0, z1))
    c = len(v)
    v.append((0.0, 0.0, z0 - sag - 0.05 * r))
    for i in range(sides):
        j = (i + 1) % sides
        f.append((base + i, base + j, apex))
        m.append(mat)
        f.append((c, base + j, base + i))
        m.append(mat)


def _trunk(v, f, m, z0, z1, r0, r1, sides, mat):
    base = len(v)
    for i in range(sides):
        a = 2.0 * math.pi * i / sides
        v.append((r0 * math.cos(a), r0 * math.sin(a), z0))
    for i in range(sides):
        a = 2.0 * math.pi * i / sides
        v.append((r1 * math.cos(a), r1 * math.sin(a), z1))
    for i in range(sides):
        j = (i + 1) % sides
        f.append((base + i, base + j, base + sides + j, base + sides + i))
        m.append(mat)


def conifer(h, rmax, tiers, sides, variant=0):
    """Spruce/fir silhouette.  Returns (verts, faces, matidx)."""
    v, f, m = [], [], []
    ht = h * (0.22 + 0.05 * (variant % 3))
    if variant == 0:                       # spruce — dense, narrow
        rmax *= 0.92
        ht = h * 0.18
    _trunk(v, f, m, 0.0, ht * 1.1, h * 0.030, h * 0.013, 5, 0)
    span = h - ht * 0.4
    for t in range(tiers):
        fr = t / max(1, tiers - 1)
        z0 = ht * 0.40 + span * (t / tiers) * 0.88
        z1 = z0 + span * (0.36 - 0.11 * fr)
        r = rmax * (1.0 - 0.74 * fr) * (1.0 + 0.10 * ((t * 5 + variant) % 3) / 3.0)
        _cone(v, f, m, z0, r, z1, sides, 1, twist=0.42 * t + 0.7 * variant,
              sag=0.10 * r)
    top = z1
    _cone(v, f, m, top - h * 0.13, rmax * 0.14, h, 5, 1, twist=0.3 * variant)
    return v, f, m


def dead_tree(h):
    """A bare, broken trunk — sparse punctuation in the stands."""
    v, f, m = [], [], []
    _trunk(v, f, m, 0.0, h, h * 0.026, h * 0.006, 5, 0)
    for k in range(3):
        z = h * (0.42 + 0.16 * k)
        a = 2.1 * k + 0.7
        ln = h * (0.16 - 0.03 * k)
        base = len(v)
        r = h * 0.010
        v.append((0, 0, z))
        for i in range(3):
            aa = 2 * math.pi * i / 3
            v.append((ln * math.cos(a) + r * math.cos(aa) * 0.5,
                      ln * math.sin(a) + r * math.sin(aa) * 0.5, z + h * 0.05))
        for i in range(3):
            j = (i + 1) % 3
            f.append((base, base + 1 + i, base + 1 + j))
            m.append(0)
    return v, f, m


# ------------------------------------------------------------------ forest
def make_forest(c, mats):
    for o in list(c.objects):
        if o.name.startswith("Forest_"):
            bpy.data.objects.remove(o, do_unlink=True)

    rng = np.random.default_rng(20241023)
    span = LD.TERRAIN_SPAN - 40.0
    g = np.arange(-span, span, STEP)
    X, Y = np.meshgrid(g, g, indexing='ij')
    X = X + rng.uniform(-STEP * 0.49, STEP * 0.49, X.shape)
    Y = Y + rng.uniform(-STEP * 0.49, STEP * 0.49, Y.shape)
    Z = LD.land_height(X, Y)
    gy, gx = np.gradient(Z, STEP, STEP)
    slope = np.hypot(gx, gy)
    dens = LD.forest_density(X, Y, Z, slope)
    w = dens * rng.random(dens.shape)
    thr = float(np.quantile(w, 1.0 - TREE_FRACTION))
    keep = w > thr
    idx = np.nonzero(keep)
    n = len(idx[0])
    print("forest candidates:", dens.size, "-> trees:", n)

    if n == 0:
        return []

    px = X[idx]
    py = Y[idx]
    pz = LD.terrain_z(px, py)
    rad = np.hypot(px, py)

    # per-tree attributes
    r1 = rng.random(n)
    r2 = rng.random(n)
    r3 = rng.random(n)
    r4 = rng.random(n)
    height = 13.0 + 15.0 * (r1 ** 0.75)
    height *= 0.70 + 0.55 * N.smoothstep(150.0, 20.0, pz)   # smaller up high
    canopy = height * (0.20 + 0.10 * r2)
    rot = r3 * math.tau
    lean = (r4 - 0.5) * 0.10

    objs = []
    chunk_span = (2 * span) / CHUNKS
    for ci in range(CHUNKS):
        for cj in range(CHUNKS):
            x0 = -span + ci * chunk_span
            y0 = -span + cj * chunk_span
            sel = ((px >= x0) & (px < x0 + chunk_span)
                   & (py >= y0) & (py < y0 + chunk_span))
            k = int(sel.sum())
            if k == 0:
                continue
            verts, faces, mats_idx, cols = [], [], [], []
            for t in range(k):
                i = int(np.nonzero(sel)[0][t])
                h = float(height[i])
                near = rad[i] < 1050.0
                if r1[i] > 0.965:
                    tv, tf, tm = dead_tree(h * 0.9)
                    fmat = 0
                else:
                    tiers = 4 if near else 3
                    sides = 7 if near else 5
                    variant = int(r2[i] * 3.0)
                    tv, tf, tm = conifer(h, float(canopy[i]), tiers, sides, variant)
                mt = Matrix.Translation((float(px[i]), float(py[i]),
                                         float(pz[i]) - 0.55))
                rz = Matrix.Rotation(float(rot[i]), 4, 'Z')
                if abs(lean[i]) > 1e-5:
                    rz = rz @ Matrix.Rotation(float(lean[i]), 4, 'X')
                mt = mt @ rz
                base = len(verts)
                for p in tv:
                    verts.append(tuple(mt @ Vector(p)))
                for j, ff in enumerate(tf):
                    faces.append(tuple(a + base for a in ff))
                    mats_idx.append(tm[j])
                # per-vertex attribute: R = tree random, G = height fraction
                rr = float(r3[i])
                for p in tv:
                    cols.append((rr, min(1.0, max(0.0, p[2] / max(h, 1.0))),
                                 0.0))
            mb = L.MB()
            mb.verts = verts
            mb.faces = faces
            mb.mats = mats_idx
            ob = mb.to_object("Forest_%d_%d" % (ci, cj), c, mats,
                              fix_normals=False)
            L.write_color_attr(ob, "tree", cols)
            L.smooth(ob, 46)
            objs.append(ob)
    print("forest chunks:", len(objs))
    return objs


# ------------------------------------------------------------------ paths
def _catmull(pts, step=5.0):
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(len(p) - 3):
        p0, p1, p2, p3 = p[i], p[i + 1], p[i + 2], p[i + 3]
        seg = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        n = max(2, int(seg / step))
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t
                       + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
                       + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(tuple(pts[-1]))
    return out


def make_paths(c, mats):
    for o in list(c.objects):
        if o.name.startswith("Path_"):
            bpy.data.objects.remove(o, do_unlink=True)
    rng = np.random.default_rng(4242)
    routes = [
        ("Path_Main", C.PATH_MAIN, 4.6),
        ("Path_Moor", C.PATH_MOOR, 3.4),
        ("Path_Quidditch", C.PATH_QUID, 3.8),
    ]
    objs = []
    for name, pts, width in routes:
        line = _catmull(pts, 5.0)
        n = len(line)
        xs = np.array([p[0] for p in line])
        ys = np.array([p[1] for p in line])
        z = LD.terrain_z(xs, ys)
        verts, faces, cols = [], [], []
        # tangents
        tx = np.gradient(xs)
        ty = np.gradient(ys)
        tl = np.hypot(tx, ty) + 1e-6
        nx, ny = -ty / tl, tx / tl
        wob = N.fbm(xs / 34.0, ys / 34.0, 3, seed=63)
        for i in range(n):
            w = width * (0.55 + 0.55 * (0.5 + 0.5 * float(wob[i])))
            for k, off in enumerate((-1.0, 0.0, 1.0)):
                px = float(xs[i]) + float(nx[i]) * w * off
                py = float(ys[i]) + float(ny[i]) * w * off
                pz = float(z[i]) + (0.14 if off == 0.0 else 0.10)
                verts.append((px, py, pz))
                cols.append((1.0 if off == 0.0 else 0.0, 0.0, 0.0))
        for i in range(n - 1):
            a = i * 3
            b = (i + 1) * 3
            faces.append((a, a + 1, b + 1, b))
            faces.append((a + 1, a + 2, b + 2, b + 1))
        mb = L.MB()
        mb.verts = verts
        mb.faces = faces
        mb.mats = [0] * len(faces)
        ob = mb.to_object(name, c, mats, fix_normals=False)
        L.write_color_attr(ob, "path", cols)
        L.smooth(ob, 50)
        objs.append(ob)
    print("paths:", len(objs))
    return objs


# ------------------------------------------------------------------ boulders
def _rock(rx, ry, rz, seed, rough=0.34):
    """Angular boulder: a low-res sphere pushed around by hashed noise."""
    nu, nv = 7, 4
    v = []
    for j in range(nv + 1):
        th = math.pi * j / nv
        for i in range(nu):
            ph = math.tau * i / nu
            sx = math.sin(th) * math.cos(ph)
            sy = math.sin(th) * math.sin(ph)
            sz = math.cos(th)
            h = (math.sin(sx * 5.1 + seed) * math.cos(sy * 4.3 - seed)
                 + 0.6 * math.sin(sz * 7.7 + seed * 1.7))
            k = 1.0 + rough * h
            v.append((sx * rx * k, sy * ry * k, sz * rz * k))
    f = []
    for j in range(nv):
        for i in range(nu):
            i2 = (i + 1) % nu
            a = j * nu
            b = (j + 1) * nu
            f.append((a + i, a + i2, b + i2, b + i))
    return v, f


def make_rocks(c, mats):
    for o in list(c.objects):
        if o.name.startswith("Rock_"):
            bpy.data.objects.remove(o, do_unlink=True)
    rng = np.random.default_rng(90210)
    span = LD.TERRAIN_SPAN - 120.0
    g = np.arange(-span, span, 22.0)
    X, Y = np.meshgrid(g, g, indexing='ij')
    X = X + rng.uniform(-11.0, 11.0, X.shape)
    Y = Y + rng.uniform(-11.0, 11.0, Y.shape)
    Z = LD.land_height(X, Y)
    gy, gx = np.gradient(Z, 22.0, 22.0)
    slope = np.hypot(gx, gy)
    rocky = N.smoothstep(0.16, 0.55, slope)
    rocky *= N.smoothstep(0.30, 0.70, LD.land_mask(X, Y))
    rocky *= N.smoothstep(140.0, 220.0, np.hypot(X, Y))
    w = rocky * rng.random(rocky.shape)
    thr = float(np.quantile(w, 0.97))
    idx = np.nonzero(w > thr)
    n = len(idx[0])
    px, py = X[idx], Y[idx]
    pz = LD.terrain_z(px, py)
    print("boulders:", n)
    objs = []
    nb = 4
    per = max(1, n // nb)
    for b in range(nb):
        lo = b * per
        hi = n if b == nb - 1 else (b + 1) * per
        if lo >= hi:
            continue
        mb = L.MB()
        for i in range(lo, hi):
            s = float(rng.uniform(1.1, 5.2))
            rx = s * float(rng.uniform(0.8, 1.9))
            ry = s * float(rng.uniform(0.8, 1.9))
            rz = s * float(rng.uniform(0.45, 1.0))
            v, f = _rock(rx, ry, rz, float(rng.uniform(0, 10)))
            mt = (Matrix.Translation((float(px[i]), float(py[i]),
                                      float(pz[i]) - rz * 0.45))
                  @ Matrix.Rotation(float(rng.uniform(0, math.tau)), 4, 'Z')
                  @ Matrix.Rotation(float(rng.uniform(-0.25, 0.25)), 4, 'X'))
            mb.add(v, f, 0, mt)
        ob = mb.to_object("Rock_Chunk_%d" % b, c, mats, fix_normals=False)
        L.smooth(ob, 40)
        objs.append(ob)
    return objs


def main():
    c = L.coll("Nature")
    mats = [M.m_bark('M_Bark'), M.m_conifer('M_Conifer')]
    make_forest(c, mats)
    make_paths(c, [M.m_path('M_Path')])
    make_rocks(c, [M.m_rock('M_Rock')])
    print("landscape done")


if __name__ == "__main__":
    main()
