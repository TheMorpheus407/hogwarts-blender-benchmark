"""Vectorised noise + small math helpers (numpy only).  All functions accept arrays."""
import numpy as np
import math

U32 = np.uint32
_ANG = np.linspace(0.0, 2.0 * np.pi, 256, endpoint=False)
_GX = np.cos(_ANG)
_GY = np.sin(_ANG)
_G3 = np.array([[1, 1, 0], [-1, 1, 0], [1, -1, 0], [-1, -1, 0],
                [1, 0, 1], [-1, 0, 1], [1, 0, -1], [-1, 0, -1],
                [0, 1, 1], [0, -1, 1], [0, 1, -1], [0, -1, -1],
                [1, 1, 0], [-1, 1, 0], [0, -1, 1], [0, -1, -1]], dtype=np.float64) / np.sqrt(2.0)


def _hash2(ix, iy, seed):
    with np.errstate(over='ignore'):
        h = ix.astype(U32) * U32(374761393) + iy.astype(U32) * U32(668265263) \
            + U32((int(seed) * 1013904223 + 12345) & 0xFFFFFFFF)
        h ^= h >> U32(13)
        h *= U32(1274126177)
        h ^= h >> U32(16)
    return h


def _hash3(ix, iy, iz, seed):
    with np.errstate(over='ignore'):
        h = ix.astype(U32) * U32(374761393) + iy.astype(U32) * U32(668265263) \
            + iz.astype(U32) * U32(2246822519) + U32((int(seed) * 1013904223 + 777) & 0xFFFFFFFF)
        h ^= h >> U32(13)
        h *= U32(1274126177)
        h ^= h >> U32(16)
    return h


def fade(t):
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, dtype=np.float64) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def clamp01(x):
    return np.clip(x, 0.0, 1.0)


def smax(a, b, k):
    """Polynomial smooth maximum."""
    h = np.clip(0.5 + 0.5 * (a - b) / k, 0.0, 1.0)
    return b + (a - b) * h + k * h * (1.0 - h) * 0.5


def smin(a, b, k):
    return -smax(-a, -b, k)


def perlin2(x, y, seed=0):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    x0 = np.floor(x)
    y0 = np.floor(y)
    fx = x - x0
    fy = y - y0
    ix = x0.astype(np.int64)
    iy = y0.astype(np.int64)

    def g(ox, oy):
        h = _hash2(ix + ox, iy + oy, seed)
        k = (h >> U32(8)) & U32(255)
        return _GX[k] * (fx - ox) + _GY[k] * (fy - oy)

    u = fade(fx)
    v = fade(fy)
    n00 = g(0, 0)
    n10 = g(1, 0)
    n01 = g(0, 1)
    n11 = g(1, 1)
    a = n00 + u * (n10 - n00)
    b = n01 + u * (n11 - n01)
    return (a + v * (b - a)) * 1.4142


def perlin3(x, y, z, seed=0):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    z = np.asarray(z, dtype=np.float64)
    x0 = np.floor(x)
    y0 = np.floor(y)
    z0 = np.floor(z)
    fx = x - x0
    fy = y - y0
    fz = z - z0
    ix = x0.astype(np.int64)
    iy = y0.astype(np.int64)
    iz = z0.astype(np.int64)

    def g(ox, oy, oz):
        h = _hash3(ix + ox, iy + oy, iz + oz, seed)
        k = (h >> U32(8)) & U32(15)
        gg = _G3[k]
        return gg[..., 0] * (fx - ox) + gg[..., 1] * (fy - oy) + gg[..., 2] * (fz - oz)

    u = fade(fx)
    v = fade(fy)
    w = fade(fz)
    x00 = g(0, 0, 0) + u * (g(1, 0, 0) - g(0, 0, 0))
    x10 = g(0, 1, 0) + u * (g(1, 1, 0) - g(0, 1, 0))
    x01 = g(0, 0, 1) + u * (g(1, 0, 1) - g(0, 0, 1))
    x11 = g(0, 1, 1) + u * (g(1, 1, 1) - g(0, 1, 1))
    y0_ = x00 + v * (x10 - x00)
    y1_ = x01 + v * (x11 - x01)
    return (y0_ + w * (y1_ - y0_)) * 1.5


def fbm2(x, y, octaves=5, lac=2.0, gain=0.5, seed=0, res=None, lam0=None):
    """fBm. If `res` (local grid spacing, metres) and `lam0` (base wavelength, metres) are given,
    octaves finer than the grid can resolve fade out (no aliasing)."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    s = np.zeros(np.broadcast(x, y).shape)
    amp = 1.0
    tot = 0.0
    c, sn = 0.8, 0.6
    for i in range(octaves):
        n = perlin2(x, y, seed + i * 17)
        if res is not None:
            lam = lam0 / (lac ** i)
            n = n * (1.0 - smoothstep(0.16 * lam, 0.42 * lam, res))
        s = s + amp * n
        tot += amp
        x, y = (x * c - y * sn) * lac + 13.7, (x * sn + y * c) * lac - 7.3
        amp *= gain
    return s / tot


def fbm3(x, y, z, octaves=4, lac=2.0, gain=0.5, seed=0):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    z = np.asarray(z, dtype=np.float64)
    s = 0.0
    amp = 1.0
    tot = 0.0
    for i in range(octaves):
        s = s + amp * perlin3(x, y, z, seed + i * 31)
        tot += amp
        x, y, z = x * lac + 5.1, y * lac - 3.7, z * lac + 9.3
        amp *= gain
    return s / tot


def ridged2(x, y, octaves=5, lac=2.1, gain=0.5, seed=0, sharp=2.0, res=None, lam0=None, soften=0.02):
    """Musgrave-style ridged multifractal, result roughly 0..1 (creases softened, resolution aware)."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    s = np.zeros(np.broadcast(x, y).shape)
    amp = 0.5
    tot = 0.0
    w = 1.0
    c, sn = 0.8, 0.6
    se = math.sqrt(soften)
    for i in range(octaves):
        n = perlin2(x, y, seed + i * 23)
        t = 1.0 - (np.sqrt(n * n + soften) - se)
        t = np.clip(t, 0.0, 1.0) ** sharp
        t = t * w
        w = np.clip(t * 1.6, 0.0, 1.0)
        if res is not None:
            lam = lam0 / (lac ** i)
            t = t * (1.0 - smoothstep(0.16 * lam, 0.42 * lam, res))
        s = s + t * amp
        tot += amp
        amp *= gain
        x, y = (x * c - y * sn) * lac + 3.3, (x * sn + y * c) * lac + 8.1
    return s / tot


def worley2(x, y, seed=0, jitter=1.0):
    """Cellular noise. Returns (F1, F2, cell_hash01)."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    x0 = np.floor(x)
    y0 = np.floor(y)
    f1 = np.full(np.broadcast(x, y).shape, 9.0)
    f2 = f1.copy()
    cid = np.zeros_like(f1)
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            cx = x0 + ox
            cy = y0 + oy
            h = _hash2(cx.astype(np.int64), cy.astype(np.int64), seed)
            px = cx + 0.5 + jitter * ((h & U32(0xFFFF)) / 65535.0 - 0.5)
            py = cy + 0.5 + jitter * (((h >> U32(16)) & U32(0xFFFF)) / 65535.0 - 0.5)
            d = np.hypot(x - px, y - py)
            m = d < f1
            f2 = np.where(m, f1, np.minimum(f2, d))
            cid = np.where(m, h / 4294967295.0, cid)
            f1 = np.where(m, d, f1)
    return f1, f2, cid


def hash01(ix, iy=None, seed=0):
    """Deterministic 0..1 random per integer cell."""
    ix = np.asarray(ix)
    iy = np.zeros_like(ix) if iy is None else np.asarray(iy)
    return _hash2(ix.astype(np.int64), iy.astype(np.int64), seed) / 4294967295.0


# --------------------------------------------------------------------------------------
# polyline / polygon helpers
# --------------------------------------------------------------------------------------

def catmull_rom(pts, per_seg=12, closed=False):
    pts = np.asarray(pts, dtype=np.float64)
    n = len(pts)
    out = []
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if (closed or i > 0) else pts[0]
        p1 = pts[i % n]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else pts[-1]
        t = np.linspace(0.0, 1.0, per_seg, endpoint=False)[:, None]
        a = 2 * p1
        b = p2 - p0
        c = 2 * p0 - 5 * p1 + 4 * p2 - p3
        d = -p0 + 3 * p1 - 3 * p2 + p3
        out.append(0.5 * (a + b * t + c * t ** 2 + d * t ** 3))
    if not closed:
        out.append(pts[-1][None, :])
    return np.concatenate(out, axis=0)


def dist_polyline(px, py, pts, closed=False):
    """Distance from points to a 2D polyline. Returns (dist, arc_param, seg_index, t_on_seg)."""
    pts = np.asarray(pts, dtype=np.float64)
    if closed:
        pts = np.concatenate([pts, pts[:1]], axis=0)
    px = np.asarray(px, dtype=np.float64)
    py = np.asarray(py, dtype=np.float64)
    best = np.full(px.shape, 1e18)
    arc = np.zeros(px.shape)
    seg_i = np.zeros(px.shape, dtype=np.int32)
    tt = np.zeros(px.shape)
    acc = 0.0
    for i in range(len(pts) - 1):
        ax, ay = pts[i, 0], pts[i, 1]
        bx, by = pts[i + 1, 0], pts[i + 1, 1]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        L = np.sqrt(L2)
        if L2 < 1e-12:
            continue
        t = np.clip(((px - ax) * dx + (py - ay) * dy) / L2, 0.0, 1.0)
        qx = ax + t * dx
        qy = ay + t * dy
        d = np.hypot(px - qx, py - qy)
        m = d < best
        best = np.where(m, d, best)
        arc = np.where(m, acc + t * L, arc)
        seg_i = np.where(m, i, seg_i)
        tt = np.where(m, t, tt)
        acc += L
    return best, arc, seg_i, tt


def inside_polygon(px, py, poly):
    poly = np.asarray(poly, dtype=np.float64)
    px = np.asarray(px, dtype=np.float64)
    py = np.asarray(py, dtype=np.float64)
    inside = np.zeros(px.shape, dtype=bool)
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if y1 == y2:
            continue
        cond = ((y1 > py) != (y2 > py))
        xint = (x2 - x1) * (py - y1) / (y2 - y1) + x1
        inside ^= cond & (px < xint)
    return inside


def sdf_polygon(px, py, poly):
    """Signed distance: positive inside, negative outside."""
    d, _, _, _ = dist_polyline(px, py, poly, closed=True)
    ins = inside_polygon(px, py, poly)
    return np.where(ins, d, -d)


def resample(pts, step):
    pts = np.asarray(pts, dtype=np.float64)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    n = max(2, int(cum[-1] / step) + 1)
    s = np.linspace(0.0, cum[-1], n)
    out = np.stack([np.interp(s, cum, pts[:, k]) for k in range(pts.shape[1])], axis=1)
    return out, s
