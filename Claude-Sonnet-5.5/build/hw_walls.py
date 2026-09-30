"""Rim curtain walls, wall towers, stair flights and lanterns."""
import numpy as np
import math
from hw_geo import (Geo, boxes, beams, lathe, loft, sweep, prism, pyramid, poly_cap, xf, rotz, yaw_axes, obox)
import hw_terrain as T
import hw_towers as TW
import hw_gothic as G

STONE = 'M_Stone'
DRESS = 'M_StoneDress'

LAMP_REG = {}


def reg(cat, x, y, z):
    LAMP_REG.setdefault(cat, []).append((float(x), float(y), float(z)))


# --------------------------------------------------------------------------------------
# geometry helpers on paths
# --------------------------------------------------------------------------------------

def smooth_circ(v, k=5):
    ker = np.ones(k) / k
    pad = k // 2
    vv = np.concatenate([v[-pad:], v, v[:pad]])
    return np.convolve(vv, ker, mode='valid')


def rim_arcs(center, level, drop=1.6, n=900, r_max=280.0, step=0.6, res=1.0, r_min=8.0):
    """Ray-march from `center`; returns list of arcs, each a (m,2) array of rim points (CCW order)."""
    th = np.linspace(0, 2 * math.pi, n, endpoint=False)
    rs = np.arange(r_min, r_max, step)
    X = center[0] + rs[None, :] * np.cos(th)[:, None]
    Y = center[1] + rs[None, :] * np.sin(th)[:, None]
    z = T.height(X.ravel(), Y.ravel(), res)[0].reshape(X.shape)
    below = z < (level - drop)
    found = below.any(axis=1)
    idx = np.argmax(below, axis=1)
    r = rs[idx] - step / 2.0
    r = np.where(found, r, np.nan)
    # split into contiguous found runs (circular)
    arcs = []
    run = []
    start = 0
    # rotate so that we start at a not-found index if there is one
    nf = np.where(~found)[0]
    if len(nf) == 0:
        rr = smooth_circ(r, 5)
        pts = np.column_stack([center[0] + rr * np.cos(th), center[1] + rr * np.sin(th)])
        return [np.vstack([pts, pts[:1]])]
    order = np.roll(np.arange(n), -int(nf[0]))
    for i in order:
        if found[i]:
            run.append(i)
        else:
            if len(run) > 6:
                arcs.append(np.array(run))
            run = []
    if len(run) > 6:
        arcs.append(np.array(run))
    out = []
    for a in arcs:
        rr = r[a].copy()
        k = 7
        pad = k // 2
        rp = np.concatenate([np.full(pad, rr[0]), rr, np.full(pad, rr[-1])])
        rr = np.convolve(rp, np.ones(k) / k, mode='valid')
        out.append(np.column_stack([center[0] + rr * np.cos(th[a]), center[1] + rr * np.sin(th[a])]))
    return out


def resample_path(pts, ds):
    pts = np.asarray(pts, float)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    n = max(2, int(cum[-1] / ds) + 1)
    s = np.linspace(0, cum[-1], n)
    out = np.stack([np.interp(s, cum, pts[:, k]) for k in range(pts.shape[1])], axis=1)
    return out, s


def path_normals(P2):
    t = np.gradient(P2, axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
    nrm = np.column_stack([t[:, 1], -t[:, 0]])     # right of travel
    return t, nrm


def strip_quads(A, B, C, D):
    """Quads from four (n,3) arrays: (A_j, B_j, C_j, D_j)."""
    return np.stack([A, B, C, D], axis=1)


def wall_run(g, P2, smp, z_walk, off=1.2, t=2.2, parapet=1.15, merlon_h=1.35, ds=1.4, wall_mat=STONE, gaps=(),
             foot=1.4, buttress_every=9.0, rng=None, merlons=True):
    """Curtain wall along a CCW arc `P2` (m,2).  Outer face steps down to the terrain (sampler `smp`)."""
    rng = rng or np.random.default_rng(1)
    P, s = resample_path(P2, ds)
    tan, nrm = path_normals(P)
    n = len(P)
    keep = np.ones(n, bool)
    for (a, b) in gaps:
        keep &= ~((s > a) & (s < b))
    # segments where both endpoints are kept
    segok = keep[:-1] & keep[1:]
    Pout = P + nrm * off
    Pin = Pout - nrm * t
    zt = z_walk
    # bottom of outer face: terrain at slightly outside
    zb = np.minimum(smp.z(Pout[:, 0], Pout[:, 1]), smp.z(Pout[:, 0] + nrm[:, 0] * 0.8, Pout[:, 1] + nrm[:, 1] * 0.8)) - foot
    zb = np.minimum(zb, zt - 1.0)
    # irregular masonry foot: stepped
    zb = np.floor(zb / 0.9) * 0.9
    def ring(Pxy, z):
        return np.column_stack([Pxy, z])
    ja = np.where(segok)[0]
    jb = ja + 1
    # outer face
    Ao, Bo = ring(Pout[ja], zb[ja]), ring(Pout[jb], zb[jb])
    Co, Do = ring(Pout[jb], np.full(len(jb), zt)), ring(Pout[ja], np.full(len(ja), zt))
    uu_a = s[ja][:, None]
    g.add(strip_quads(Ao, Bo, Co, Do), wall_mat)
    # walk top
    Wa, Wb = ring(Pout[ja], np.full(len(ja), zt)), ring(Pout[jb], np.full(len(jb), zt))
    Wc, Wd = ring(Pin[jb], np.full(len(jb), zt)), ring(Pin[ja], np.full(len(ja), zt))
    g.add(strip_quads(Wa, Wb, Wc, Wd), DRESS)
    # parapet (outer half): outer face, top, inner face
    pt = 0.9
    Pp = Pout - nrm * pt
    zp = zt + parapet
    a1, b1 = ring(Pout[ja], np.full(len(ja), zt)), ring(Pout[jb], np.full(len(jb), zt))
    c1, d1 = ring(Pout[jb], np.full(len(jb), zp)), ring(Pout[ja], np.full(len(ja), zp))
    g.add(strip_quads(a1, b1, c1, d1), wall_mat)
    # top
    a2, b2 = ring(Pout[ja], np.full(len(ja), zp)), ring(Pout[jb], np.full(len(jb), zp))
    c2, d2 = ring(Pp[jb], np.full(len(jb), zp)), ring(Pp[ja], np.full(len(ja), zp))
    g.add(strip_quads(a2, b2, c2, d2), DRESS)
    # inner face of parapet (faces inward)
    a3, b3 = ring(Pp[jb], np.full(len(jb), zt)), ring(Pp[ja], np.full(len(ja), zt))
    c3, d3 = ring(Pp[ja], np.full(len(ja), zp)), ring(Pp[jb], np.full(len(jb), zp))
    g.add(strip_quads(a3, b3, c3, d3), wall_mat)
    # merlons
    if merlons:
        step_m = 2.4
        sm = np.arange(1.0, s[-1] - 1.0, step_m)
        okm = np.ones(len(sm), bool)
        for (a, b) in gaps:
            okm &= ~((sm > a - 0.5) & (sm < b + 0.5))
        sm = sm[okm]
        idx = np.clip(np.searchsorted(s, sm), 0, n - 1)
        cx = Pout[idx, 0] - nrm[idx, 0] * pt / 2
        cy = Pout[idx, 1] - nrm[idx, 1] * pt / 2
        yaw = np.arctan2(tan[idx, 1], tan[idx, 0])
        C = np.column_stack([cx, cy, np.full(len(idx), zp)])
        boxes(g, C, [(1.35, pt, merlon_h)], yaw=yaw, m=wall_mat)
        boxes(g, C + np.array([0, 0, merlon_h]), [(1.5, pt + 0.16, 0.16)], yaw=yaw, m=DRESS)
    # buttresses along the outer face
    if buttress_every:
        sb = np.arange(buttress_every / 2, s[-1] - 1.0, buttress_every)
        okb = np.ones(len(sb), bool)
        for (a, b) in gaps:
            okb &= ~((sb > a - 1.5) & (sb < b + 1.5))
        sb = sb[okb]
        idx = np.clip(np.searchsorted(s, sb), 0, n - 1)
        hb = (zt - zb[idx]) * (0.62 + 0.3 * rng.random(len(idx))) + 0.5
        cx = Pout[idx, 0] + nrm[idx, 0] * 0.45
        cy = Pout[idx, 1] + nrm[idx, 1] * 0.45
        yaw = np.arctan2(tan[idx, 1], tan[idx, 0])
        C = np.column_stack([cx, cy, zt - hb])
        boxes(g, C, np.column_stack([np.full(len(idx), 1.6), np.full(len(idx), 1.5), hb]), yaw=yaw, m=wall_mat, faces=(0, 1, 2, 3, 4))
        boxes(g, np.column_stack([cx, cy, np.full(len(idx), zt - 0.4)]), [(1.9, 1.8, 0.4)], yaw=yaw, m=DRESS)
    return dict(length=float(s[-1]), n=n)


# --------------------------------------------------------------------------------------
# lantern posts
# --------------------------------------------------------------------------------------

def lantern_post(h=3.2, lantern_h=0.62, w=0.36):
    key = ('lantern_post', h)

    def build():
        g = Geo('lantern_post', ['M_Iron', 'M_LanternGlass'])
        pole = [(0.20, 0.0), (0.18, 0.25), (0.10, 0.45), (0.07, 0.9), (0.07, h - 0.5), (0.13, h - 0.42), (0.13, h - 0.32),
                (0.22, h - 0.28)]
        lathe(g, pole, (0, 0, 0), segs=10, m='M_Iron')
        z0 = h - 0.28
        boxes(g, [(0, 0, z0)], [(w + 0.12, w + 0.12, 0.08)], m='M_Iron', faces=(0, 1, 2, 3, 4, 5))
        # glass box with four corner posts
        g.add_geo_glass = None
        gl = []
        hh = lantern_h
        # four glass faces (emissive)
        for (nx, ny) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            c = np.array([nx * w / 2, ny * w / 2, z0 + 0.08 + hh / 2])
            r = np.array([-ny, nx, 0.0]) * 1.0
            u = np.array([0, 0, 1.0])
            # r x u must equal normal: r=( -ny, nx,0 ), u=(0,0,1): r x u = (nx*1 - 0, 0 - (-ny)*1 ... ) check numerically
            nrm = np.cross(r, u)
            if np.dot(nrm, np.array([nx, ny, 0.0])) < 0:
                r = -r
            q = np.stack([c - r * w / 2 - u * hh / 2, c + r * w / 2 - u * hh / 2, c + r * w / 2 + u * hh / 2, c - r * w / 2 + u * hh / 2])
            gl.append(q)
        g.add(np.stack(gl), 'M_LanternGlass', a={'glow': 1.0, 'hue': 0.12, 'seed': 0.5})
        for (sx, sy) in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            boxes(g, [(sx * w / 2, sy * w / 2, z0 + 0.08)], [(0.05, 0.05, hh)], m='M_Iron')
        cap_base = np.array([[-w / 2 - 0.08, -w / 2 - 0.08, z0 + 0.08 + hh], [w / 2 + 0.08, -w / 2 - 0.08, z0 + 0.08 + hh],
                             [w / 2 + 0.08, w / 2 + 0.08, z0 + 0.08 + hh], [-w / 2 - 0.08, w / 2 + 0.08, z0 + 0.08 + hh]])
        pyramid(g, cap_base, (0, 0, z0 + 0.08 + hh + 0.34), 'M_Iron')
        lathe(g, [(0.05, z0 + hh + 0.4), (0.06, z0 + hh + 0.5), (0.0, z0 + hh + 0.62)], (0, 0, 0), segs=6, m='M_Iron')
        return g
    return G.cached(key, build)


def lantern_wall(w=0.34):
    key = ('lantern_wall',)

    def build():
        g = Geo('lantern_wall', ['M_Iron', 'M_LanternGlass'])
        beams(g, [(0, 0.0, 0.0)], [(0, -0.6, 0.0)], 0.08, 0.08, m='M_Iron')
        beams(g, [(0, -0.6, -0.05)], [(0, -0.6, 0.45)], 0.05, 0.05, m='M_Iron')
        hh = 0.55
        boxes(g, [(0, -0.6, 0.02)], [(w, w, 0.06)], m='M_Iron')
        gl = []
        for (nx, ny) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            c = np.array([nx * w / 2, -0.6 + ny * w / 2, 0.08 + hh / 2])
            r = np.array([-ny, nx, 0.0])
            u = np.array([0, 0, 1.0])
            if np.dot(np.cross(r, u), np.array([nx, ny, 0.0])) < 0:
                r = -r
            gl.append(np.stack([c - r * w / 2 - u * hh / 2, c + r * w / 2 - u * hh / 2, c + r * w / 2 + u * hh / 2, c - r * w / 2 + u * hh / 2]))
        g.add(np.stack(gl), 'M_LanternGlass', a={'glow': 1.0, 'hue': 0.1, 'seed': 0.3})
        cap = np.array([[-w / 2 - 0.05, -0.6 - w / 2 - 0.05, 0.08 + hh], [w / 2 + 0.05, -0.6 - w / 2 - 0.05, 0.08 + hh],
                        [w / 2 + 0.05, -0.6 + w / 2 + 0.05, 0.08 + hh], [-w / 2 - 0.05, -0.6 + w / 2 + 0.05, 0.08 + hh]])
        pyramid(g, cap, (0, -0.6, 0.08 + hh + 0.25), 'M_Iron')
        return g
    return G.cached(key, build)


# --------------------------------------------------------------------------------------
# stairs
# --------------------------------------------------------------------------------------

def stair_flight(g, pts, smp, width=3.6, tread=0.60, depth=2.4, parapet=True, mat=STONE, rng=None, lanterns=None):
    """pts: (n,3) centreline (x,y,z) of the walking surface, monotone in z.  Returns per-step arrays."""
    P, s = resample_path(pts, 0.5)
    L = s[-1]
    nst = max(2, int(round(L / tread)))
    si = (np.arange(nst) + 0.5) / nst * L
    X = np.interp(si, s, P[:, 0])
    Y = np.interp(si, s, P[:, 1])
    Z0_, Z1_ = P[0, 2], P[-1, 2]
    rise = (Z1_ - Z0_) / nst
    Z = Z0_ + (np.arange(nst) + 1) * rise
    d = np.gradient(np.column_stack([X, Y]), axis=0)
    yaw = np.arctan2(d[:, 1], d[:, 0])
    trd = L / nst
    C = np.column_stack([X, Y, Z - depth])
    boxes(g, C, np.column_stack([np.full(nst, trd * 1.03), np.full(nst, width), np.full(nst, depth)]), yaw=yaw, m=mat,
          faces=(0, 1, 2, 3, 4, 5))
    # nosing lip
    boxes(g, np.column_stack([X, Y, Z - 0.12]), np.column_stack([np.full(nst, trd * 1.03 + 0.06), np.full(nst, width + 0.0), np.full(nst, 0.12)]),
          yaw=yaw, m=DRESS, faces=(4,))
    return dict(X=X, Y=Y, Z=Z, yaw=yaw)


def stair_parapets(g, pts_all, smp, width=3.6, h=1.0, t=0.5, side=(-1, 1), mat=STONE, foot=1.5):
    """Low walls along both sides of the continuous stair polyline (n,3).  Skirt goes down to the terrain."""
    P, s = resample_path(pts_all, 0.8)
    tan, nrm = path_normals(P[:, :2])
    for sd in side:
        edge = P[:, :2] + nrm * sd * (width / 2 + t / 2)
        zt = P[:, 2] + h
        zb = np.minimum(smp.z(edge[:, 0] + nrm[:, 0] * sd * 0.6, edge[:, 1] + nrm[:, 1] * sd * 0.6),
                        smp.z(edge[:, 0], edge[:, 1])) - foot
        zb = np.minimum(zb, P[:, 2] - 0.6)
        outer = P[:, :2] + nrm * sd * (width / 2 + t)
        inner = P[:, :2] + nrm * sd * (width / 2)
        n = len(P)
        ja = np.arange(n - 1)
        jb = ja + 1
        def r(Pxy, z):
            return np.column_stack([Pxy, z])
        # outer face (normal outwards from the stair)  ; orientation depends on side
        A, B = r(outer[ja], zb[ja]), r(outer[jb], zb[jb])
        C, D = r(outer[jb], zt[jb]), r(outer[ja], zt[ja])
        q = strip_quads(A, B, C, D)
        if sd < 0:
            q = q[:, ::-1]
        g.add(q, mat)
        # top
        A, B = r(outer[ja], zt[ja]), r(outer[jb], zt[jb])
        C, D = r(inner[jb], zt[jb]), r(inner[ja], zt[ja])
        q = strip_quads(A, B, C, D)
        if sd < 0:
            q = q[:, ::-1]
        g.add(q, DRESS)
        # inner face
        A, B = r(inner[jb], P[jb, 2]), r(inner[ja], P[ja, 2])
        C, D = r(inner[ja], zt[ja]), r(inner[jb], zt[jb])
        q = strip_quads(A, B, C, D)
        if sd < 0:
            q = q[:, ::-1]
        g.add(q, mat)
    return P


def landing(g, x, y, z, R=4.6, depth=3.0, mat=STONE, ring=True, segs=28):
    prof = [(R + 0.9, z - depth - 6.0), (R + 0.9, z - 2.0), (R + 0.2, z - 0.3), (R, z - 0.06), (R - 0.1, z)]
    lathe(g, [(R + 0.9, z - depth - 6.0), (R + 0.5, z - 2.5), (R, z - 0.4), (R, z)], (x, y, 0), segs=segs, m=mat)
    # paved top
    top = [(R, z), (0.0, z)]
    lathe(g, top, (x, y, 0), segs=segs, m=DRESS)
