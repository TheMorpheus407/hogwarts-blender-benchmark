"""Procedural conifer / rock prototypes (numpy -> Geo)."""
import numpy as np
import math
from hw_geo import Geo, lathe, loft, beams, boxes
from hw_noise import perlin3, fbm3

FOL = 'M_Conifer'
BARK = 'M_Bark'
ROCK = 'M_RockChunk'
REED = 'M_Reed'


def _ring(cx, cy, z, radii, ang0, n):
    t = ang0 + 2 * math.pi * np.arange(n) / n
    return np.column_stack([cx + radii * np.cos(t), cy + radii * np.sin(t), np.full(n, z)])


def spruce(rng, height=16.0, radius=3.4, tiers=16, seg=18, droop=0.11, slim=1.0, lean=0.0, base=0.20, name='spruce',
           tip_attr=True, bark_r=0.34, sprays=0.0, droop_scale=1.0, core=True):
    g = Geo(name, [FOL, BARK])
    # trunk
    tr = np.array([(bark_r * 1.25, -0.3), (bark_r, 0.4), (bark_r * 0.75, height * 0.35), (bark_r * 0.32, height * 0.78),
                   (0.05, height)])
    lathe(g, tr, (0, 0, 0), segs=7, m=BARK)
    z_start = height * base
    z_end = height * 0.985
    if core:
        z0c = z_start * 0.9
        span = height - z0c
        cprof = np.array([(radius * 0.60 * slim, z0c), (radius * 0.47 * slim, z0c + span * 0.33),
                          (radius * 0.26 * slim, z0c + span * 0.68), (0.0, height * 0.995)])
        lathe(g, cprof, (0, 0, 0), segs=max(seg - 4, 8), m=FOL, smooth=True, a={'tip': 0.05})
    for i in range(tiers):
        t = i / max(tiers - 1, 1)
        zi = z_start + (z_end - z_start) * (t ** 0.92)
        R = radius * (1.0 - t) ** 0.85 * (0.80 + 0.28 * rng.random()) * slim + 0.10
        drop = max(height * droop * (1.0 - 0.45 * t) * (0.85 + 0.3 * rng.random()) * droop_scale, R * (0.95 + 0.2 * droop_scale) * (0.9 + 0.2 * rng.random()))
        ang0 = rng.random() * 2 * math.pi
        n = max(seg - int(6 * t), 6)
        # jagged outer edge: alternate long / short branches, noisy
        k = np.arange(n)
        jag = 0.72 + 0.28 * (np.cos(k * 2.0 * math.pi / n * (2.0 + (i % 3))) * 0.5 + 0.5) + 0.22 * (rng.random(n) - 0.5)
        Ro = R * np.clip(jag, 0.45, 1.15)
        sag = drop * (0.75 + 0.5 * rng.random(n)) * (0.9 + 0.35 * np.cos(k * 2 * math.pi / n * 3.0 + i))
        sw = 0.12 * R * np.sin(k * 1.7 + i)
        r0 = _ring(0, 0, zi + 0.25 * drop, np.full(n, 0.10 * R + 0.06), ang0, n)
        r1 = _ring(0, 0, zi - 0.30 * drop, 0.55 * Ro, ang0, n)
        r2 = _ring(0, 0, zi, Ro, ang0, n)
        r2[:, 2] = zi - sag
        r3 = _ring(0, 0, zi, 0.62 * Ro, ang0, n)
        r3[:, 2] = zi - sag * 0.85 - 0.25 * drop
        r4 = _ring(0, 0, zi, np.full(n, 0.16 * R + 0.05), ang0, n)
        r4[:, 2] = zi - 0.55 * drop
        # lean the whole crown slightly
        for rr in (r0, r1, r2, r3, r4):
            rr[:, 0] += lean * (rr[:, 2] / height) ** 2 * height * 0.5
        rings_up = np.stack([r2, r1, r0])          # outer edge -> centre : normals point up / outward
        rings_dn = np.stack([r4, r3, r2])          # centre -> outer edge   : normals point down / outward
        tipv = np.stack([np.zeros(n), np.full(n, 0.45), np.ones(n)])
        for rings, tv in ((rings_up, tipv[::-1]), (rings_dn, tipv)):
            n_r = rings.shape[0]
            a = None
            if tip_attr:
                # per-face tip factor: average of the two ring values of each quad row
                fv = np.repeat(((tv[:-1] + tv[1:]) / 2.0)[:, :1], 1, axis=1)
                fac = np.repeat(fv[:, 0], n)     # one value per (ring pair, seg)
                a = {'tip': fac}
            loft(g, rings, closed=True, m=FOL, smooth=True, a=a)
        if sprays > 0:
            step = 1 if sprays >= 1.0 else 2
            for kk in range(0, n, step):
                ang = ang0 + 2 * math.pi * kk / n
                rr = Ro[kk]
                px, py, pz = rr * math.cos(ang), rr * math.sin(ang), zi - sag[kk]
                dvec = np.array([math.cos(ang) * 0.8, math.sin(ang) * 0.8, -0.55 - 0.25 * rng.random()])
                ln = (0.9 + 0.6 * rng.random()) * (0.8 + 0.09 * R)
                _fan(g, np.array([px, py, pz + 0.05]), dvec, ln, rng, count=22, spread=0.55, width=0.05, tip=0.85, droop=0.25)
                if rng.random() < 0.8:
                    rr2 = rr * (0.5 + 0.3 * rng.random())
                    ang2 = ang + (rng.random() - 0.5) * 0.4
                    dv2 = np.array([math.cos(ang2) * 0.65, math.sin(ang2) * 0.65, -0.5])
                    _fan(g, np.array([rr2 * math.cos(ang2), rr2 * math.sin(ang2), zi - sag[kk] * 0.5]), dv2, ln * 0.8, rng,
                         count=16, spread=0.6, width=0.05, tip=0.6, droop=0.2)
    return g


def boulder(rng, size=1.0, name='rock', n_lat=9, n_lon=14, flat=0.62, seed=0):
    """Faceted, strata-banded boulder (unit-ish size, origin at base)."""
    g = Geo(name, [ROCK])
    la = np.linspace(-math.pi / 2, math.pi / 2, n_lat + 2)
    lo = 2 * math.pi * np.arange(n_lon) / n_lon
    LA, LO = np.meshgrid(la, lo, indexing='ij')
    X = np.cos(LA) * np.cos(LO)
    Y = np.cos(LA) * np.sin(LO)
    Z = np.sin(LA) * flat
    P = np.stack([X, Y, Z], -1)
    noise = fbm3(P[..., 0] * 1.8 + seed, P[..., 1] * 1.8, P[..., 2] * 2.4, 4, seed=seed + 7)
    rad = 1.0 + 0.55 * noise * 1.6
    P = P * rad[..., None]
    # planar facets: clip against a few random planes
    for _ in range(6):
        nrm = rng.normal(size=3)
        nrm[2] = abs(nrm[2]) * 0.5
        nrm /= np.linalg.norm(nrm)
        d = 0.62 + 0.25 * rng.random()
        proj = P @ nrm
        over = proj > d
        P = np.where(over[..., None], P - nrm * (proj - d)[..., None], P)
    P[..., 2] = np.maximum(P[..., 2], -flat * 0.45)
    P *= size
    P[..., 2] -= P[..., 2].min() - 0.05 * size
    # collapse poles
    P[0] = P[0].mean(axis=0)
    P[-1] = P[-1].mean(axis=0)
    loft(g, P, closed=True, m=ROCK, smooth=False)
    return g


def make_prototypes(seed=7):
    """Returns dict name -> Geo for the tree collection (variant order matters)."""
    rng = np.random.default_rng(seed)
    P = {}
    # LOD0 (near), LOD1 (mid), LOD2 (far)
    specs = [
        ('spruce_a', dict(height=17.0, radius=3.4, tiers=(17, 13, 10), seg=(20, 16, 12), droop=0.11)),
        ('spruce_b', dict(height=13.0, radius=3.9, tiers=(15, 12, 9), seg=(20, 16, 12), droop=0.13, slim=1.0)),
        ('spruce_c', dict(height=23.0, radius=3.2, tiers=(20, 15, 11), seg=(20, 16, 12), droop=0.09, slim=0.9)),
        ('fir_d', dict(height=10.0, radius=2.6, tiers=(12, 10, 8), seg=(18, 14, 10), droop=0.14, slim=1.0)),
    ]
    order = []
    for lod in range(3):
        for k, (nm, sp) in enumerate(specs):
            # NB: the Collection Info node hands out children sorted BY NAME, so the name must sort like the
            # instance index (lod * 4 + species) the scatter points refer to
            name = 't%d%d_%s' % (lod, k, nm)
            g = spruce(rng, sp['height'], sp['radius'], sp['tiers'][lod], sp['seg'][lod], sp['droop'], sp.get('slim', 1.0),
                       lean=0.01 * (rng.random() - 0.5), name=name, sprays=(1.0 if lod == 0 else 0.0),
                       droop_scale=(1.0, 1.3, 1.6)[lod])
            P[name] = g
            order.append(name)
    return P, order


def _spray(g, base, direction, length, radius, m=FOL, segs=6, droop=0.35, tip=0.7):
    """Needle tuft: tapered lathe along `direction` from `base`."""
    d = np.asarray(direction, float)
    d = d / max(np.linalg.norm(d), 1e-9)
    # build lathe along +Z then rotate to d
    prof = [(0.04 * radius, 0.0), (radius, 0.35 * length), (0.75 * radius, 0.75 * length), (0.0, length)]
    tmp = Geo('spray', [m])
    lathe(tmp, prof, (0, 0, 0), segs=segs, m=m, smooth=True, a={'tip': tip})
    z = np.array([0, 0, 1.0])
    v = np.cross(z, d)
    s = np.linalg.norm(v)
    c = float(np.dot(z, d))
    if s < 1e-8:
        Rm = np.eye(3) if c > 0 else np.diag([1, -1, -1.0])
    else:
        vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        Rm = np.eye(3) + vx + vx @ vx * ((1 - c) / (s * s))
    for ch in tmp.c4 + tmp.c3:
        P = ch['P'].astype(float) @ Rm.T + np.asarray(base)
        N = None if ch['N'] is None else (ch['N'].astype(float) @ Rm.T).astype(np.float32)
        nc = dict(ch)
        nc['P'] = P.astype(np.float32)
        nc['N'] = N
        (g.c4 if P.shape[1] == 4 else g.c3).append(nc)


def _fan(g, base, direction, length, rng, count=14, spread=0.5, width=0.045, tip=0.7, droop=0.0, m=FOL):
    """Fan of thin needle pyramids radiating from `base` around `direction` (vectorised)."""
    d0 = np.asarray(direction, float)
    d0 = d0 / max(np.linalg.norm(d0), 1e-9)
    e1 = np.cross(d0, [0.0, 0.0, 1.0])
    if np.linalg.norm(e1) < 1e-6:
        e1 = np.array([1.0, 0.0, 0.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(d0, e1)
    ang = rng.random(count) * 2 * math.pi
    rad = spread * rng.random(count) ** 0.6
    dirs = d0[None, :] + rad[:, None] * (np.cos(ang)[:, None] * e1[None, :] + np.sin(ang)[:, None] * e2[None, :])
    dirs[:, 2] -= droop * rng.random(count)
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    L = length * (0.55 + 0.45 * rng.random(count))
    B = np.asarray(base, float)[None, :] + d0[None, :] * (rng.random(count) - 0.5)[:, None] * 0.15
    a1 = np.cross(dirs, [0.0, 0.0, 1.0])
    bad = np.linalg.norm(a1, axis=1) < 1e-6
    a1[bad] = np.array([1.0, 0.0, 0.0])
    a1 /= np.linalg.norm(a1, axis=1, keepdims=True)
    a2 = np.cross(dirs, a1)
    w = width * (0.8 + 0.5 * rng.random(count))
    corners = []
    for ph in (0.0, 2 * math.pi / 3, 4 * math.pi / 3):
        corners.append(B + w[:, None] * (math.cos(ph) * a1 + math.sin(ph) * a2))
    apex = B + dirs * L[:, None]
    T = []
    for i in range(3):
        T.append(np.stack([corners[i], corners[(i + 1) % 3], apex], axis=1))
    T = np.concatenate(T)
    g.add(T, m, a={'tip': tip + 0.25 * (rng.random(len(T)) - 0.5)})


def hero_pine(rng, height=26.0, crown=7.5, name='hero_pine', whorls=9, lean=0.03, spray_len=1.9, density=1.0):
    """Detailed foreground conifer: curved trunk, branch whorls, hundreds of needle sprays."""
    g = Geo(name, [FOL, BARK])
    # trunk: chain of lathes is heavy; use one lathe + gentle bend by chained beams for upper part
    tr = np.array([(0.85, -0.5), (0.62, 0.8), (0.48, 3.0), (0.34, height * 0.4), (0.22, height * 0.72), (0.09, height * 0.94), (0.0, height)])
    lathe(g, tr, (0, 0, 0), segs=9, m=BARK)
    # root flare
    for k in range(6):
        a = 2 * math.pi * k / 6 + rng.random()
        beams(g, [(0.5 * math.cos(a), 0.5 * math.sin(a), 0.9)], [(1.6 * math.cos(a), 1.6 * math.sin(a), -0.3)], 0.35, 0.3, m=BARK)
    for w in range(whorls):
        t = 0.34 + 0.64 * (w / max(whorls - 1, 1)) ** 0.9
        zc = height * t
        nbr = 6 if t < 0.8 else 4
        Lw = crown * (1.05 - t) ** 0.75 * (0.75 + 0.35 * rng.random()) + 0.6
        ang0 = rng.random() * 2 * math.pi
        for b in range(nbr):
            a = ang0 + 2 * math.pi * b / nbr + (rng.random() - 0.5) * 0.5
            dirh = np.array([math.cos(a), math.sin(a), 0.0])
            Lb = Lw * (0.7 + 0.5 * rng.random())
            # branch curve (droops then lifts at the tip)
            npts = 5
            pts = []
            for i in range(npts):
                s = i / (npts - 1)
                pts.append(np.array([0, 0, zc]) + dirh * Lb * s + np.array([0, 0, -0.25 * Lb * s * (1 - s) * 2.0 + 0.10 * Lb * s * s]))
            pts = np.array(pts)
            for i in range(npts - 1):
                wdt = 0.16 * (1 - i / npts) + 0.03
                beams(g, [pts[i]], [pts[i + 1]], wdt, wdt, m=BARK)
            # needle fans along the branch (both sides + upward)
            ns = int(Lb * 2.6 * density) + 2
            for k in range(ns):
                s = 0.20 + 0.80 * (k + rng.random()) / ns
                i = min(int(s * (npts - 1)), npts - 2)
                fr = s * (npts - 1) - i
                p = pts[i] * (1 - fr) + pts[i + 1] * fr
                side = np.cross(dirh, [0, 0, 1.0])
                ln = spray_len * (1.05 - 0.4 * s) * (0.8 + 0.4 * rng.random())
                for sgn in (-1, 1):
                    dv = dirh * 0.5 + side * sgn * (0.6 + 0.3 * rng.random()) + np.array([0, 0, -0.15 + 0.5 * rng.random()])
                    _fan(g, p, dv, ln, rng, count=24, spread=0.5, width=0.05, tip=0.4 + 0.5 * s, droop=0.15)
                if rng.random() < 0.7:
                    _fan(g, p, np.array([0.25 * dirh[0], 0.25 * dirh[1], 1.0]), ln * 0.8, rng, count=18, spread=0.5, width=0.05, tip=0.8)
    # leader tip
    _fan(g, np.array([0, 0, height * 0.965]), np.array([0, 0, 1.0]), 2.6, rng, count=40, spread=0.35, width=0.05, tip=0.9)
    return g


def standing_stone(rng, h=3.6, w=1.3, name='stone', seed=0):
    g = boulder(rng, 1.0, name, n_lat=10, n_lon=12, flat=0.7, seed=seed)
    # stretch to a tall slab: scale vertices
    for ch in g.c4 + g.c3:
        P = ch['P']
        P[..., 0] *= w
        P[..., 1] *= w * 0.55
        P[..., 2] *= h
        ch['P'] = P
    return g


def rock_facets(rng, size=1.0, flat=0.6, cuts=9, name='rock', seed=0, n_lat=13, n_lon=22, rough=0.35):
    """Angular, faceted rock: displaced sphere clipped by many random planes, plus two scales of surface noise."""
    g = Geo(name, [ROCK])
    la = np.linspace(-math.pi / 2, math.pi / 2, n_lat + 2)
    lo = 2 * math.pi * np.arange(n_lon) / n_lon
    LA, LO = np.meshgrid(la, lo, indexing='ij')
    P = np.stack([np.cos(LA) * np.cos(LO), np.cos(LA) * np.sin(LO), np.sin(LA) * flat], -1)
    nz = fbm3(P[..., 0] * 2.2 + seed, P[..., 1] * 2.2, P[..., 2] * 3.0, 4, seed=seed + 5)
    P = P * (1.0 + rough * 1.5 * nz)[..., None]
    for _ in range(cuts):
        nrm = rng.normal(size=3)
        nrm[2] = abs(nrm[2]) * (0.4 if flat < 0.5 else 0.8)
        nrm /= np.linalg.norm(nrm)
        d = 0.46 + 0.34 * rng.random()
        proj = P @ nrm
        over = proj > d
        P = np.where(over[..., None], P - nrm * (proj - d)[..., None], P)
    # surface chipping: two noise scales along the radial direction
    r = np.linalg.norm(P, axis=-1, keepdims=True)
    dirn = P / np.maximum(r, 1e-6)
    n1 = fbm3(P[..., 0] * 5.5 + seed * 1.7, P[..., 1] * 5.5, P[..., 2] * 5.5, 3, seed=seed + 21)
    n2 = fbm3(P[..., 0] * 14.0, P[..., 1] * 14.0 + seed, P[..., 2] * 14.0, 2, seed=seed + 33)
    P = P + dirn * (0.045 * n1 + 0.016 * n2)[..., None]
    P[..., 2] = np.maximum(P[..., 2], -flat * 0.35)
    P *= size
    P[..., 2] -= P[..., 2].min() - 0.02 * size
    P[0] = P[0].mean(axis=0)
    P[-1] = P[-1].mean(axis=0)
    loft(g, P, closed=True, m=ROCK, smooth=False)
    return g


def reed_clump(rng, blades=16, h=1.5, spread=0.30, lean=0.35, width=0.04, name='reed'):
    """Clump of tapered, gently arching blades (reeds / rushes / grass tufts).  Single quads, both sides render."""
    g = Geo(name, [REED])
    rows = 5
    for _ in range(blades):
        th = rng.random() * 2 * math.pi
        r = spread * math.sqrt(rng.random())
        base = np.array([r * math.cos(th), r * math.sin(th), 0.0])
        hh = h * (0.55 + 0.55 * rng.random())
        out = np.array([math.cos(th), math.sin(th), 0.0])
        tw = rng.random() * 2 * math.pi
        side = np.array([math.cos(tw), math.sin(tw), 0.0])
        lb = lean * (0.4 + 1.1 * rng.random())
        cen = []
        for k in range(rows):
            t = k / (rows - 1)
            cen.append(base + out * (lb * hh * t * t) + np.array([0.0, 0.0, hh * t * (1.0 - 0.14 * t)]))
        quads = []
        tips = []
        for k in range(rows - 1):
            t0, t1 = k / (rows - 1), (k + 1) / (rows - 1)
            w0 = width * (1.0 - t0) ** 0.7
            w1 = width * (1.0 - t1) ** 0.9
            quads.append([cen[k] - side * w0, cen[k] + side * w0, cen[k + 1] + side * w1, cen[k + 1] - side * w1])
            tips.append(0.5 * (t0 + t1))
        g.add_quads(np.array(quads), REED, a={'tip': np.array(tips)})
    return g


def make_shore_prototypes(seed=21):
    rng = np.random.default_rng(seed)
    P, order = {}, []
    for i in range(3):        # reeds / rushes 0..2
        g = reed_clump(rng, blades=14 + 4 * i, h=1.25 + 0.28 * i, spread=0.30 + 0.05 * i, lean=0.30, width=0.038, name='reed%d' % i)
        P['reed%d' % i] = g
        order.append('reed%d' % i)
    for i in range(3):        # grass / heather tufts 3..5
        g = reed_clump(rng, blades=22 + 6 * i, h=0.42 + 0.12 * i, spread=0.20 + 0.04 * i, lean=0.55, width=0.030, name='tuft%d' % i)
        P['tuft%d' % i] = g
        order.append('tuft%d' % i)
    return P, order


def rock_block(rng, size=1.0, flat=0.6, cuts=6, name='block', seed=0, n_lat=15, n_lon=28, rough=0.14, eps=0.40,
               aspect=(1.0, 1.0)):
    """Chunky angular block (bedded rock): superellipsoid, a few plane cuts, chipped by two noise scales."""
    g = Geo(name, [ROCK])
    la = np.linspace(-math.pi / 2, math.pi / 2, n_lat + 2)
    lo = 2 * math.pi * np.arange(n_lon) / n_lon
    LA, LO = np.meshgrid(la, lo, indexing='ij')

    def sp(v, e):
        return np.sign(v) * np.abs(v) ** e
    cl = np.cos(LA)
    P = np.stack([sp(cl, eps) * sp(np.cos(LO), eps) * aspect[0], sp(cl, eps) * sp(np.sin(LO), eps) * aspect[1],
                  sp(np.sin(LA), eps) * flat], -1)
    nz = fbm3(P[..., 0] * 1.6 + seed, P[..., 1] * 1.6, P[..., 2] * 2.0, 3, seed=seed + 5)
    P = P * (1.0 + rough * nz)[..., None]
    for _ in range(cuts):
        nrm = rng.normal(size=3)
        nrm[2] *= 0.35
        nrm /= np.linalg.norm(nrm)
        d = 0.70 + 0.22 * rng.random()
        proj = P @ nrm
        over = proj > d
        P = np.where(over[..., None], P - nrm * (proj - d)[..., None], P)
    r = np.linalg.norm(P, axis=-1, keepdims=True)
    dirn = P / np.maximum(r, 1e-6)
    n1 = fbm3(P[..., 0] * 4.5 + seed * 1.7, P[..., 1] * 4.5, P[..., 2] * 4.5, 3, seed=seed + 21)
    n2 = fbm3(P[..., 0] * 13.0, P[..., 1] * 13.0 + seed, P[..., 2] * 13.0, 2, seed=seed + 33)
    P = P + dirn * (0.030 * n1 + 0.012 * n2)[..., None]
    P[..., 2] = np.maximum(P[..., 2], -flat * 0.8)
    P *= size
    P[..., 2] -= P[..., 2].min() - 0.02 * size
    P[0] = P[0].mean(axis=0)
    P[-1] = P[-1].mean(axis=0)
    loft(g, P, closed=True, m=ROCK, smooth=False)
    return g


def make_rock_prototypes(seed=11):
    rng = np.random.default_rng(seed)
    P, order = {}, []
    for i in range(5):        # bedded blocks 0..4 (flank ledges)
        g = rock_block(rng, 1.0, flat=0.50 + 0.07 * i, cuts=5 + i % 3, name='block%d' % i, seed=i * 5 + 1,
                       eps=0.34 + 0.03 * i, aspect=(1.0, 0.85 + 0.08 * (i % 3)))
        P['block%d' % i] = g
        order.append('block%d' % i)
    for i in range(6):        # rounded boulders 5..10
        g = rock_block(rng, 1.0, flat=0.55 + 0.08 * (i % 3), cuts=3 + i % 2, name='boulder%d' % i, seed=i * 7 + 40,
                       eps=0.62 + 0.07 * i, rough=0.20, aspect=(1.0, 0.75 + 0.07 * i))
        P['boulder%d' % i] = g
        order.append('boulder%d' % i)
    for i in range(4):        # spires 11..14 (tall, jagged)
        g = rock_facets(rng, 1.0, flat=1.9 + 0.5 * i, cuts=11, name='spire%d' % i, seed=i * 11 + 90, rough=0.35, n_lat=10)
        P['spire%d' % i] = g
        order.append('spire%d' % i)
    return P, order
