"""Terrain height field, masks and mesh builders (numpy).  One graded tensor-grid mesh -> no LOD seams."""
import numpy as np
import math
from hw_noise import (fbm2, ridged2, perlin2, smoothstep, lerp, smax, smin, sdf_polygon,
                      dist_polyline, catmull_rom, worley2, resample)
import hw_layout as L

FBM_GAIN = 1.6   # fbm2 comes back in about +-0.65, this brings it to about +-1

# carve features registered at runtime (stairs, paths)
CARVES = {'stairs': [], 'paths': [], 'flats': [], 'quay': []}


def wgt(lam, res):
    """Detail weight: 1 when the local grid spacing resolves wavelength `lam`, 0 when it does not."""
    return 1.0 - smoothstep(lam * 0.16, lam * 0.42, res)


def warp(x, y, amp, scale, seed):
    return (x + amp * FBM_GAIN * fbm2(x / scale, y / scale, 3, seed=seed),
            y + amp * FBM_GAIN * fbm2(x / scale + 11.3, y / scale - 4.7, 3, seed=seed + 1))


# ----------------------------------------------------------------------------------------------
# lake / base landform
# ----------------------------------------------------------------------------------------------

def lake_sd(x, y):
    xw, yw = warp(x, y, 42.0, 330.0, 21)
    d = None
    for (cx, cy, rx, ry) in L.LAKE_BLOBS:
        r = np.sqrt(((xw - cx) / rx) ** 2 + ((yw - cy) / ry) ** 2)
        s = (1.0 - r) * min(rx, ry)
        d = s if d is None else smax(d, s, 45.0)
    for (cx, cy, rx, ry, h) in L.LAND_BUMPS:
        xb, yb = warp(x, y, 8.0, 40.0, 27)
        r = np.sqrt(((xb - cx) / rx) ** 2 + ((yb - cy) / ry) ** 2)
        s = (1.0 - r) * min(rx, ry)
        d = smin(d, -s, 10.0)
    return d


def mountains(x, y, res):
    """Highland bowl around the lake spine with E-W stretched, domain-warped ridges (layered silhouettes)."""
    xw, yw = warp(x, y, 300.0, 1400.0, 41)
    ax, ay, bx, by = 0.0, -1750.0, 0.0, -130.0
    px, py = xw - ax, yw - ay
    tt = np.clip((px * (bx - ax) + py * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2), 0.0, 1.0)
    d = np.hypot(xw - (ax + tt * (bx - ax)), yw - (ay + tt * (by - ay)))
    bowl = 0.52 * np.maximum(d - 380.0, 0.0)
    rid = ridged2(xw / 2400.0, yw / 1250.0, 6, seed=42, sharp=1.25, res=res, lam0=1250.0)
    soft = 0.5 + 0.5 * FBM_GAIN * fbm2(xw / 1500.0, yw / 1100.0, 5, seed=44, res=res, lam0=1100.0)
    body = 0.5 + 0.5 * FBM_GAIN * fbm2(xw / 3600.0, yw / 3600.0, 4, seed=8)
    shape = 0.32 + 0.62 * np.clip(0.55 * rid + 0.45 * soft, 0, 1)
    h = bowl * shape * np.clip(0.6 + 0.6 * body, 0.35, 1.3)
    # crags / corries: sharper ridged detail that fades in with distance from the castle
    envd = smoothstep(500.0, 2400.0, d)
    c1 = ridged2(xw / 520.0, yw / 420.0, 4, seed=51, sharp=1.8, res=res, lam0=420.0)
    c2 = ridged2(xw / 210.0 + 5.0, yw / 190.0, 3, seed=52, sharp=2.2, res=res, lam0=190.0)
    h = h + envd * (0.20 * bowl * np.clip(c1, 0, 1) + 95.0 * np.clip(c2, 0, 1) * smoothstep(400.0, 1600.0, bowl))
    h = h + smoothstep(500.0, 2500.0, d) * 42.0 * FBM_GAIN * fbm2(x / 380.0, y / 260.0, 4, seed=43, res=res, lam0=260.0)
    return np.minimum(h, 1700.0)


def upland(x, y, res):
    n1 = fbm2(x / 700.0, y / 700.0, 4, seed=31) * FBM_GAIN
    h = 63.0 + 15.0 * n1
    h = h + 6.0 * fbm2(x / 150.0, y / 150.0, 3, seed=32) * FBM_GAIN * wgt(150.0, res)
    h = h + 1.8 * fbm2(x / 38.0, y / 38.0, 3, seed=33) * FBM_GAIN * wgt(38.0, res)
    return h + mountains(x, y, res)


def base_z(x, y, res):
    s = lake_sd(x, y)
    g = upland(x, y, res)
    Wl = 120.0 - 100.0 * np.exp(-(((x - 80.0) / 480.0) ** 2 + ((y + 120.0) / 620.0) ** 2))
    land_w = smoothstep(0.0, 1.0, np.clip(-s / Wl, 0.0, 1.0))
    z_land = g * land_w
    for (cx, cy, rx, ry, h) in L.LAND_BUMPS:
        xb, yb = warp(x, y, 8.0, 40.0, 27)
        r = np.sqrt(((xb - cx) / rx) ** 2 + ((yb - cy) / ry) ** 2)
        bs = (1.0 - r) * min(rx, ry)
        zb = h * smoothstep(0.0, 0.85 * min(rx, ry), bs) + 0.6 * FBM_GAIN * fbm2(x / 12.0, y / 12.0, 2, seed=29) * (bs > 0)
        capmask = smoothstep(-25.0, 0.0, bs)
        z_land = lerp(z_land, np.minimum(z_land, zb), capmask)
    bed = -46.0 * smoothstep(0.0, 105.0, np.maximum(s, 0.0)) ** 0.9
    bed = bed + 2.5 * FBM_GAIN * fbm2(x / 45.0, y / 45.0, 3, seed=35) * smoothstep(0.0, 30.0, s) * wgt(45.0, res)
    z = np.where(s > 0, bed, z_land)
    return z, s


# ----------------------------------------------------------------------------------------------
# crag platforms
# ----------------------------------------------------------------------------------------------
_BBOX = None


def _platform_bbox():
    global _BBOX
    if _BBOX is None:
        pts = np.concatenate([np.asarray(P['poly'], float) for P in L.PLATFORMS])
        wmax = max(P['W'] for P in L.PLATFORMS)
        _BBOX = (pts[:, 0].min() - wmax * 1.6, pts[:, 0].max() + wmax * 1.6,
                 pts[:, 1].min() - wmax * 1.6, pts[:, 1].max() + wmax * 1.6)
    return _BBOX


def platforms(x, y, z, res):
    """Crag skirts (smooth max) then flat tops.  Returns z, flank(0..1), inside(0..1)."""
    bx0, bx1, by0, by1 = _platform_bbox()
    m = (x > bx0) & (x < bx1) & (y > by0) & (y < by1)
    flank = np.zeros(x.shape)
    inside = np.zeros(x.shape)
    if not m.any():
        return z, flank, inside
    xs, ys, zs, rs = x[m], y[m], z[m], res[m]
    xw, yw = warp(xs, ys, 5.0, 36.0, 51)
    order = sorted(L.PLATFORMS, key=lambda P: P['z'])
    sds = {}
    zc = zs.copy()
    fl = np.zeros(xs.shape)
    for P in order:
        sd = sdf_polygon(xw, yw, P['poly'])
        sds[P['name']] = sd
        Wv = P['W'] * (1.0 + 0.35 * FBM_GAIN * fbm2(xs / 55.0 + P['seed'], ys / 55.0, 2, seed=P['seed']))
        sp = (24.0 * FBM_GAIN * fbm2(xs / 95.0, ys / 110.0, 3, seed=P['seed'] + 9)
              + 6.0 * FBM_GAIN * fbm2(xs / 24.0, ys / 32.0, 2, seed=P['seed'] + 10) + 8.0)
        sd_eff = sd + np.maximum(sp, 0.0) * P.get('spur', 1.0)
        c = np.clip(-sd_eff / Wv, 0.0, 1.0)
        S = 1.0 - (1.0 - c) ** P['p']
        top = P['z']
        floor = P.get('floor', -46.0)
        h = np.where(sd_eff >= 0, top, top - (top - floor) * S)
        zc = smax(zc, h, 3.0)
        f = smoothstep(0.0, 0.06, c) * (1.0 - smoothstep(0.55, 0.95, c)) * (sd_eff < 0)
        fl = np.maximum(fl, f)
    ins = np.zeros(xs.shape)
    for P in order:
        sd = sds[P['name']]
        ins_i = smoothstep(-1.2, 2.2, sd)
        micro = 0.10 * FBM_GAIN * fbm2(xs / 6.0, ys / 6.0, 2, seed=P['seed'] + 5) * wgt(6.0, rs)
        zc = lerp(zc, P['z'] + micro, ins_i)
        ins = np.maximum(ins, ins_i)
    out = z.copy()
    out[m] = zc
    flank[m] = fl
    inside[m] = ins
    return out, flank, inside


# ----------------------------------------------------------------------------------------------
# strata
# ----------------------------------------------------------------------------------------------

def strata(x, y, z, amount):
    """Tilted, irregular rock layering: wide flat ledges + short risers, blended by `amount`."""
    zt = z + 6.0 * FBM_GAIN * fbm2(x / 55.0, y / 55.0, 3, seed=71) + 0.21 * x + 0.05 * y
    T = 6.5 + 3.2 * FBM_GAIN * fbm2(x / 90.0 + 3.0, y / 90.0, 2, seed=72)
    T = np.clip(T, 3.5, 12.0)
    kk = np.floor(zt / T)
    f = zt / T - kk
    z2 = T * (kk + smoothstep(0.52, 1.0, f)) - (zt - z)
    return lerp(z, z2, np.clip(amount, 0, 1) * 0.95)


def strata_fine(x, y, z, amount, res):
    """Thin bedding: short ledges and risers (1.5-3.5 m) on the cliff flanks, same tilt as the main strata."""
    zt = z + 2.5 * FBM_GAIN * fbm2(x / 23.0 + 5.0, y / 23.0, 3, seed=81) + 0.21 * x + 0.05 * y
    T = np.clip(2.4 + 1.1 * FBM_GAIN * fbm2(x / 40.0 + 9.0, y / 40.0, 2, seed=82), 1.5, 3.6)
    kk = np.floor(zt / T)
    f = zt / T - kk
    z2 = T * (kk + smoothstep(0.55, 1.0, f)) - (zt - z)
    return lerp(z, z2, np.clip(amount, 0, 1) * 0.55 * wgt(T.mean() if np.ndim(T) else T, res))


def height0(x, y, res):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    res = np.broadcast_to(np.asarray(res, float), x.shape)
    z, s = base_z(x, y, res)
    z, flank, inside = platforms(x, y, z, res)
    bluff = smoothstep(0.0, -12.0, s) * smoothstep(-90.0, -30.0, s)
    rnoise = smoothstep(-0.15, 0.25, FBM_GAIN * fbm2(x / 95.0, y / 95.0, 3, seed=73))
    amount = np.maximum(flank, bluff * rnoise * 0.8) * (1.0 - inside)
    a_str = np.maximum(flank, bluff * rnoise * 0.4) * (1.0 - inside)      # terracing: strong on the crag, faint on lake bluffs
    if np.any(amount > 0.01):
        z = strata(x, y, z, a_str)
        lump = FBM_GAIN * fbm2(x / 34.0, y / 34.0, 3, seed=74)
        z = z + lump * 3.6 * amount * wgt(34.0, res)
        rough = FBM_GAIN * (0.9 * fbm2(x / 8.0, y / 8.0, 3, seed=75) * wgt(8.0, res)
                            + 0.45 * fbm2(x / 2.8, y / 2.8, 2, seed=76) * wgt(2.8, res))
        z = z + rough * amount * 1.5
        cr = ridged2(x / 12.0, y / 12.0, 3, seed=77, sharp=3.0)
        z = z + (cr - 0.35) * 0.9 * amount * wgt(12.0, res)
        z = strata_fine(x, y, z, flank * (1.0 - inside), res)
    return z, s, amount, inside


# ----------------------------------------------------------------------------------------------
# carving: stairs / paths
# ----------------------------------------------------------------------------------------------

def carve(x, y, z):
    for st in CARVES['stairs']:
        pts = st['pts']
        d, arc, si, tt = dist_polyline(x, y, pts[:, :2])
        zs = np.interp(arc, st['cum'], pts[:, 2])
        w = smoothstep(st['half'] + st['fade'], st['half'], d)
        z = lerp(z, zs - 0.45, w)
    for pa in CARVES['paths']:
        d, arc, si, tt = dist_polyline(x, y, pa['pts'][:, :2])
        w = smoothstep(pa['half'] + 1.5, pa['half'] * 0.4, d)
        z = z - 0.22 * w
    for q in CARVES['quay']:
        # water side of a masonry quay wall: no rock lip in front of the wall foot, the ground falls straight into the lake
        px, py = q['pts'][:, 0], q['pts'][:, 1]
        yl = np.interp(x, px, py)
        d = yl - y + q.get('inset', 1.6)               # > 0 on the water (south) side, starting `inset` m behind the wall face
        inx = smoothstep(px[0] - 3.0, px[0] + 1.0, x) * smoothstep(px[-1] + 3.0, px[-1] - 1.0, x)
        zt = q['z'] - q['drop'] * smoothstep(0.25, q['reach'], d)
        w = smoothstep(0.0, 0.6, d) * inx * (1.0 - smoothstep(8.0, 12.0, d))     # only the strip in front of the wall
        z = np.where(w > 0.0, np.minimum(z, lerp(z, zt, w)), z)
    return z


def quay_line(b, z_edge=2.4):
    """Plan line of the boathouse quay wall: where the shelf drops below `z_edge`, going south from the building."""
    xs = np.arange(b['cx'] - 27.0, b['cx'] + 28.0, 1.5)
    yy = np.arange(b['cy'] - 6.0, b['cy'] - 30.0, -0.5)
    pts = []
    for xx in xs:
        zz = height0(np.full_like(yy, xx), yy, 1.0)[0]
        k = int(np.argmax(zz < z_edge))
        pts.append((xx, yy[k] if zz[k] < z_edge else b['cy'] - 13.0))
    pts = np.array(pts)
    ker = np.ones(5) / 5.0
    pts[:, 1] = np.convolve(np.concatenate([[pts[0, 1]] * 2, pts[:, 1], [pts[-1, 1]] * 2]), ker, mode='valid')
    return pts


def register_quay(pts, z=2.2, drop=5.0, reach=3.2):
    CARVES['quay'] = [dict(pts=np.asarray(pts, float), z=z, drop=drop, reach=reach)]


def height(x, y, res):
    z, s, amount, inside = height0(x, y, res)
    z = carve(x, y, z)
    return z, s, amount, inside


def plan_flight(xa, za, xb, zb, y_lo, y_hi, n=None, res=1.0):
    """Path from (xa, za) to (xb, zb) hugging the cliff: for every x find y where height0 == z."""
    n = n or max(8, int(abs(xb - xa) / 2.5))
    xs = np.linspace(xa, xb, n)
    zt = np.linspace(za, zb, n)
    lo = np.full(n, y_lo, dtype=float)
    hi = np.full(n, y_hi, dtype=float)
    for _ in range(28):
        mid = 0.5 * (lo + hi)
        zm = height0(xs, mid, res)[0]
        higher = zm > zt
        hi = np.where(higher, mid, hi)
        lo = np.where(higher, lo, mid)
    ys = 0.5 * (lo + hi)
    k = np.array([0.25, 0.5, 0.25])
    yp = np.concatenate([[ys[0]], ys, [ys[-1]]])
    ys2 = np.convolve(yp, k, mode='valid')
    ys2[0], ys2[-1] = ys[0], ys[-1]
    return np.column_stack([xs, ys2, zt])


def register_stair(name, pts, half=2.6, fade=4.0):
    pts = np.asarray(pts, dtype=float)
    seg = np.linalg.norm(np.diff(pts[:, :2], axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    CARVES['stairs'] = [s for s in CARVES['stairs'] if s['name'] != name]
    CARVES['stairs'].append(dict(name=name, pts=pts, cum=cum, half=half, fade=fade))


def register_path(name, pts, half=1.8):
    pts = np.asarray(pts, dtype=float)
    CARVES['paths'] = [s for s in CARVES['paths'] if s['name'] != name]
    CARVES['paths'].append(dict(name=name, pts=pts, half=half))


# ----------------------------------------------------------------------------------------------
# graded axes + terrain mesh
# ----------------------------------------------------------------------------------------------

def graded_axis(segments, lo, hi, growth):
    """segments: [(a, b, step), ...] contiguous, ascending.  Outside spacing grows geometrically."""
    pts = [segments[0][0]]
    for a, b, st in segments:
        n = max(1, int(round((b - a) / st)))
        pts.extend(list(np.linspace(a, b, n + 1)[1:]))
    a0, b0 = segments[0][0], segments[-1][1]
    st_lo = segments[0][2]
    st_hi = segments[-1][2]
    left = []
    x, st = a0, st_lo
    while x > lo:
        st *= growth
        x -= st
        left.append(x)
    right = []
    x, st = b0, st_hi
    while x < hi:
        st *= growth
        x += st
        right.append(x)
    return np.array(left[::-1] + pts + right)


class Sampler:
    """Bilinear sampling on a non-uniform tensor grid."""

    def __init__(self, xs, ys, Z):
        self.xs, self.ys, self.Z = xs, ys, Z

    def z(self, x, y):
        x = np.asarray(x, float)
        y = np.asarray(y, float)
        xs, ys, Z = self.xs, self.ys, self.Z
        ix = np.clip(np.searchsorted(xs, x) - 1, 0, len(xs) - 2)
        iy = np.clip(np.searchsorted(ys, y) - 1, 0, len(ys) - 2)
        tx = np.clip((x - xs[ix]) / (xs[ix + 1] - xs[ix]), 0, 1)
        ty = np.clip((y - ys[iy]) / (ys[iy + 1] - ys[iy]), 0, 1)
        return (Z[iy, ix] * (1 - tx) * (1 - ty) + Z[iy, ix + 1] * tx * (1 - ty)
                + Z[iy + 1, ix] * (1 - tx) * ty + Z[iy + 1, ix + 1] * tx * ty)


def build_terrain(bpy, coll, name, xs, ys, mat=None, extra_fn=None):
    nx, ny = len(xs), len(ys)
    X, Y = np.meshgrid(xs, ys)
    dx = np.gradient(xs)
    dy = np.gradient(ys)
    res = np.maximum(dx[None, :], dy[:, None])
    res = np.broadcast_to(res, X.shape)
    z, s, amount, inside = height(X, Y, res)
    gy = np.gradient(z, axis=0) / dy[:, None]
    gx = np.gradient(z, axis=1) / dx[None, :]
    slope = np.hypot(gx, gy)
    idx = np.arange(nx * ny).reshape(ny, nx)
    quads = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], -1).reshape(-1, 4)
    V = np.stack([X, Y, z], -1).reshape(-1, 3).astype(np.float32)
    mesh = bpy.data.meshes.new(name)
    nf = len(quads)
    mesh.vertices.add(len(V))
    mesh.vertices.foreach_set('co', V.ravel())
    mesh.loops.add(nf * 4)
    mesh.loops.foreach_set('vertex_index', quads.ravel().astype(np.int32))
    mesh.polygons.add(nf)
    mesh.polygons.foreach_set('loop_start', (np.arange(nf) * 4).astype(np.int32))
    mesh.polygons.foreach_set('loop_total', np.full(nf, 4, np.int32))
    mesh.update(calc_edges=True)
    fields = dict(slope=slope, amount=amount, inside=inside, shore=s)
    if extra_fn is not None:
        fields.update(extra_fn(X, Y, z, slope, s, amount, inside))
    for key, arr in fields.items():
        a = mesh.attributes.new(key, 'FLOAT', 'POINT')
        a.data.foreach_set('value', np.asarray(arr, dtype=np.float32).ravel())
    if mat is not None:
        mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    return obj, Sampler(xs, ys, z), dict(nverts=len(V), nquads=nf)


# ----------------------------------------------------------------------------------------------
# water: closed slab with wave displacement on the top face
# ----------------------------------------------------------------------------------------------

def wave_z(x, y, amp=1.0):
    """Sum of a few directional sine swells + short chop (metres)."""
    z = np.zeros(np.broadcast(x, y).shape)
    waves = [(0.020, 0.95, 0.045), (0.034, 2.10, 0.030), (0.061, 0.30, 0.018), (0.11, 1.35, 0.010),
             (0.19, 2.75, 0.006), (0.31, 0.75, 0.003)]
    for k, ang, a in waves:
        kx, ky = k * math.cos(ang), k * math.sin(ang)
        z = z + a * np.sin(kx * x + ky * y + 3.7 * k * 40)
    z = z + 0.018 * FBM_GAIN * fbm2(x / 23.0, y / 23.0, 3, seed=81)
    return z * amp


def build_water(bpy, coll, name, mat, xs, ys, depth=-90.0):
    nx, ny = len(xs), len(ys)
    X, Y = np.meshgrid(xs, ys)
    dist = np.hypot(X, Y + 300.0)
    amp = 1.0 - 0.6 * smoothstep(600.0, 3000.0, dist)
    Z = wave_z(X, Y, amp * 1.5)
    top = np.stack([X, Y, Z], -1).reshape(-1, 3)
    idx = np.arange(nx * ny).reshape(ny, nx)
    quads = [np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], -1).reshape(-1, 4)]
    south = idx[0, :]
    east = idx[:, -1]
    north = idx[-1, ::-1]
    west = idx[::-1, 0]
    ring_top = np.concatenate([south[:-1], east[:-1], north[:-1], west[:-1]])
    nb = len(ring_top)
    base = nx * ny
    bot = np.column_stack([top[ring_top, 0], top[ring_top, 1], np.full(nb, depth)])
    ring_bot = base + np.arange(nb)
    center = base + nb
    a = ring_top
    b = np.roll(ring_top, -1)
    c = np.roll(ring_bot, -1)
    d = ring_bot
    quads.append(np.stack([a, d, c, b], -1))
    tris = np.stack([np.full(nb, center), np.roll(ring_bot, -1), ring_bot], -1)
    V = np.concatenate([top, bot, np.array([[0.0, -300.0, depth]])]).astype(np.float32)
    allq = np.concatenate(quads)
    mesh = bpy.data.meshes.new(name)
    mesh.vertices.add(len(V))
    mesh.vertices.foreach_set('co', V.ravel())
    nq, nt = len(allq), len(tris)
    mesh.loops.add(nq * 4 + nt * 3)
    mesh.loops.foreach_set('vertex_index', np.concatenate([allq.ravel(), tris.ravel()]).astype(np.int32))
    mesh.polygons.add(nq + nt)
    mesh.polygons.foreach_set('loop_start', np.concatenate([np.arange(nq) * 4, nq * 4 + np.arange(nt) * 3]).astype(np.int32))
    mesh.polygons.foreach_set('loop_total', np.concatenate([np.full(nq, 4), np.full(nt, 3)]).astype(np.int32))
    mesh.update(calc_edges=True)
    if mat is not None:
        mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    return obj, dict(nverts=len(V), nquads=nq, ntris=nt)
