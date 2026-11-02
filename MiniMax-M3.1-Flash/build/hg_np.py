"""Vectorised procedural field helpers (numpy, bundled with Blender)."""
import numpy as np


def _hash2(ix, iy, seed=0):
    with np.errstate(over='ignore'):
        x = (ix.astype(np.uint64) * np.uint64(0x9E3779B97F4A7C15))
        y = (iy.astype(np.uint64) * np.uint64(0xC2B2AE3D27D4EB4F))
        h = (x ^ y ^ np.uint64((int(seed) * 0x165667B19E3779F9) & 0xFFFFFFFFFFFFFFFF))
        h ^= (h >> np.uint64(29))
        h *= np.uint64(0xBF58476D1CE4E5B9)
        h ^= (h >> np.uint64(32))
    return (h & np.uint64(0xFFFFFF)).astype(np.float64) / float(0xFFFFFF)


def vnoise(x, y, seed=0.0):
    """Bilinear value noise in [-1,1]."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    x0 = np.floor(x)
    y0 = np.floor(y)
    fx = x - x0
    fy = y - y0
    ix = x0.astype(np.int64)
    iy = y0.astype(np.int64)
    u = fx * fx * (3 - 2 * fx)
    v = fy * fy * (3 - 2 * fy)
    n00 = _hash2(ix, iy, int(seed))
    n10 = _hash2(ix + 1, iy, int(seed))
    n01 = _hash2(ix, iy + 1, int(seed))
    n11 = _hash2(ix + 1, iy + 1, int(seed))
    a = n00 + (n10 - n00) * u
    b = n01 + (n11 - n01) * u
    return (a + (b - a) * v) * 2.0 - 1.0


def fbm(x, y, octaves=5, freq=1.0, seed=0.0, gain=0.5, lac=2.03):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    total = np.zeros(np.shape(x), dtype=np.float64)
    amp, f, norm = 1.0, float(freq), 0.0
    for i in range(octaves):
        total += amp * vnoise(x * f, y * f, seed + i * 17.31)
        norm += amp
        amp *= gain
        f *= lac
    return total / norm


def ridged(x, y, octaves=4, freq=1.0, seed=0.0):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    total = np.zeros(np.shape(x), dtype=np.float64)
    amp, f, norm = 1.0, float(freq), 0.0
    for i in range(octaves):
        total += amp * (1.0 - np.abs(vnoise(x * f, y * f, seed + i * 9.7)))
        norm += amp
        amp *= 0.5
        f *= 2.07
    return total / norm


def worley(x, y, freq=1.0, seed=0, jitter=0.85):
    """Nearest-feature-point field: (d1, d2, per-cell random value).

    Feature points sit on a jittered lattice of spacing 1/freq.  `cellr` is
    a random number in [0,1) belonging to the cell that owns the nearest
    point, so a field built on it is constant across each cell and jumps at
    the cell boundary.  That is exactly what a jointed crag needs: flat
    slabs at different depths separated by sharp joints.

    `d2` is the distance to the second-nearest point, and half the gap
    between the two is a good approximation of the distance to the cell
    boundary -- which is how a joint is traced.
    """
    x, y = np.broadcast_arrays(np.asarray(x, dtype=np.float64) * float(freq),
                               np.asarray(y, dtype=np.float64) * float(freq))
    ix = np.floor(x).astype(np.int64)
    iy = np.floor(y).astype(np.int64)
    best_d = np.full(x.shape, 1e9)
    sec_d = np.full(x.shape, 1e9)
    best_r = np.zeros(x.shape)
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            cx = ix + ox
            cy = iy + oy
            rx = _hash2(cx, cy, int(seed))
            ry = _hash2(cx, cy, int(seed) + 977)
            px = cx + 0.5 + (rx - 0.5) * jitter
            py = cy + 0.5 + (ry - 0.5) * jitter
            d = np.hypot(x - px, y - py)
            better = d < best_d
            sec_d = np.where(better, best_d, np.minimum(sec_d, d))
            best_d = np.where(better, d, best_d)
            best_r = np.where(better, rx, best_r)
    return best_d, sec_d, best_r


def smoothstep(a, b, x):
    if a == b:
        return np.where(x < a, 0.0, 1.0)
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def dist_polyline(X, Y, pts):
    """Distance from each (X,Y) to a polyline (list of (x,y))."""
    d = np.full(X.shape, 1e9)
    for i in range(len(pts) - 1):
        ax, ay = pts[i]
        bx, by = pts[i + 1]
        vx, vy = bx - ax, by - ay
        L2 = vx * vx + vy * vy
        t = 0.0 if L2 < 1e-9 else np.clip(((X - ax) * vx + (Y - ay) * vy) / L2, 0.0, 1.0)
        cx, cy = ax + t * vx, ay + t * vy
        d = np.minimum(d, np.hypot(X - cx, Y - cy))
    return d


def dist_point(X, Y, px, py):
    return np.hypot(X - px, Y - py)
