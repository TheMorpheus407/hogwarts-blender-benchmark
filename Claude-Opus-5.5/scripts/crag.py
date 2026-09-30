"""The rock promontory: several lofted rock bodies with stratified ledges, blocky
joint facets, vertical fractures and a talus flare into the lake."""
import bpy, math, random
from mathutils import Vector, noise
import geo


def ellipse_rim(cx, cy, rx, ry, n=48, wob=0.0, seed=0):
    rnd = random.Random(seed)
    ph = [rnd.random() * 6.28 for _ in range(4)]
    pts = []
    for i in range(n):
        a = geo.TAU * i / n
        k = 1 + wob * (0.5 * math.sin(2 * a + ph[0]) + 0.3 * math.sin(3 * a + ph[1]) + 0.2 * math.sin(5 * a + ph[2]))
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    return pts


# Top-rim outlines (CCW). The main body carries the castle at z=55.
MAIN_RIM = [(-150, 10), (-146, -30), (-136, -58), (-122, -69), (-66, -69), (-58, -62), (-44, -80),
            (-22, -86), (-4, -76), (14, -66), (40, -68), (62, -66), (80, -58), (98, -50), (118, -34),
            (136, -14), (156, 18), (160, 52), (146, 84), (104, 106), (44, 128), (-20, 122), (-84, 104),
            (-124, 82), (-146, 46)]

DZ = 30.0  # the whole crag / castle is lifted by this much above the original 55 m design

BLOBS = [
    dict(name='Crag_Main', c=(0.0, 5.0), rim=MAIN_RIM, top=55.0 + DZ, bot=-20.0, flare=0.10, toe=10.0, seed=1, drop=7.0),
    dict(name='Crag_East', c=(146.0, -40.0), rim=ellipse_rim(146, -40, 58, 40, 40, 0.3, 2), top=31.0 + DZ,
         bot=-20.0, flare=0.12, toe=8.0, seed=2, drop=5.0),
    dict(name='Crag_West', c=(-152.0, -52.0), rim=ellipse_rim(-152, -52, 42, 36, 40, 0.15, 3), top=41.0 + DZ,
         bot=-20.0, flare=0.12, toe=8.0, seed=3),
    dict(name='Crag_Owlery', c=(-222.0, 58.0), rim=ellipse_rim(-222, 58, 17, 14, 32, 0.2, 4), top=68.0 + DZ,
         bot=-10.0, flare=0.16, toe=10.0, seed=4),
    # lower stepped shoulders in front of the south face
    dict(name='Crag_FrontW', c=(-100.0, -84.0), rim=ellipse_rim(-100, -84, 46, 20, 40, 0.2, 5), top=44.0,
         bot=-20.0, flare=0.16, toe=9.0, seed=5),
    dict(name='Crag_FrontC', c=(-32.0, -86.0), rim=ellipse_rim(-32, -86, 22, 17, 36, 0.2, 6), top=58.0,
         bot=-20.0, flare=0.14, toe=9.0, seed=6),
    dict(name='Crag_FrontE', c=(62.0, -80.0), rim=ellipse_rim(62, -80, 36, 18, 36, 0.2, 7), top=36.0,
         bot=-20.0, flare=0.16, toe=9.0, seed=7),
    dict(name='Crag_EastHill', c=(356.0, 42.0), rim=ellipse_rim(356, 42, 30, 34, 36, 0.22, 9), top=80.0,
         bot=-20.0, flare=0.14, toe=9.0, seed=9, slope=0.35),
    dict(name='Crag_Spur', c=(-150.0, 20.0), rim=ellipse_rim(-150, 20, 26, 40, 36, 0.2, 8), top=52.0,
         bot=-20.0, flare=0.14, toe=9.0, seed=8),
]


def ray_poly(c, a, poly):
    """distance from c along angle a to polygon boundary (max hit)."""
    dx, dy = math.cos(a), math.sin(a)
    best = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        ex, ey = x2 - x1, y2 - y1
        den = dx * ey - dy * ex
        if abs(den) < 1e-9:
            continue
        t = ((x1 - c[0]) * ey - (y1 - c[1]) * ex) / den
        u = ((x1 - c[0]) * dy - (y1 - c[1]) * dx) / den
        if t > 0 and -1e-6 <= u <= 1 + 1e-6:
            best = max(best, t)
    return best


def _hash(i, s):
    return (math.sin(i * 127.1 + s * 311.7) * 43758.5453) % 1.0


# gully in the south face where the boathouse stair climbs
STAIR_ANG = None  # filled lazily


def gully(bl, x, y, z):
    if bl['name'] != 'Crag_Main':
        return 0.0
    # recess centred on x≈-5 on the south face
    if y > -60:
        return 0.0
    w = math.exp(-((x - 2.0) / 20.0) ** 2)
    return -9.0 * w * geo.smoothstep(-5, 20, z)


def radial_offset(bl, a, z, R, x, y):
    top, bot, s = bl['top'], bl['bot'], bl['seed']
    H = top - z
    # sheer upper cliff band, then steep broken slopes whose angle varies around the rock
    n1 = noise.noise(Vector((x / 70.0, y / 70.0, s * 2.3)))
    n2 = noise.noise(Vector((x / 45.0, y / 45.0, s * 4.1 + 9)))
    band = max(8.0, (top - bl['bot']) * (0.32 + 0.14 * n1))
    slope = max(0.04, bl.get('slope', 0.28) + 0.3 * n2)
    off = H * bl['flare']
    if H > band:
        off += (H - band) * slope
    # benches: the face steps out below a couple of ledge heights
    for li in range(2):
        zl = bl['bot'] + (top - bl['bot']) * (0.3 + 0.28 * li) + 14.0 * noise.noise(Vector((x / 40.0, y / 40.0, li + s)))
        w = 3.5 * max(0.0, noise.noise(Vector((x / 26.0, y / 26.0, li * 3.1 + s))) + 0.15)
        off += w * geo.smoothstep(zl + 0.5, zl - 1.5, z)
    off += bl['toe'] * geo.smoothstep(10, -12, z) ** 1.5
    # strata: tilted layers with per-layer hardness -> protruding / receding bands
    sc = z + 0.22 * x - 0.12 * y + noise.noise(Vector((x / 30, y / 30, z / 60 + s))) * 1.6
    T = 3.4 + 1.6 * noise.noise(Vector((x / 90.0, y / 90.0, s * 1.3)))
    k = math.floor(sc / T)
    f = sc / T - k
    h0 = _hash(k, s)
    h1 = _hash(k + 1, s)
    hard = geo.lerp(h0, h1, geo.smoothstep(0.82, 1.0, f))
    patchy = geo.smoothstep(-0.15, 0.35, noise.noise(Vector((x / 55.0, y / 55.0, s * 2.9))))
    off += (hard - 0.5) * 1.1 * patchy * geo.smoothstep(top, top - 6, z)
    # vertical joints (columns)
    p = Vector((x / 9.0, y / 9.0, z / 38.0 + s * 3))
    off += noise.noise(p) * 2.4
    # blocky facets from voronoi cells
    vd, vp = noise.voronoi(Vector((x / 12.0, y / 12.0, z / 12.0 + s)), distance_metric='DISTANCE', exponent=2.5)
    cid = vp[0]
    off += (_hash(round(cid.x * 7 + cid.y * 13 + cid.z * 17, 3), s) - 0.5) * 3.4
    # fine roughness
    off += noise.fractal(Vector((x / 3.0, y / 3.0, z / 3.0 + s)), 0.6, 2.0, 3) * 0.55
    # large spurs and gullies, deepening towards the foot
    sp = noise.noise(Vector((x / 38.0, y / 38.0, z / 90.0 + s * 5)))
    off += sp * (3.0 + 9.0 * geo.smoothstep(top, 0, z))
    # rounded lip at the very top
    off -= 1.2 * geo.smoothstep(top - 1.5, top, z)
    return off


def build_blob(bl, coll, na=None, dz=0.55):
    c = bl['c']
    rim = bl['rim']
    per = sum(math.dist(rim[i], rim[(i + 1) % len(rim)]) for i in range(len(rim)))
    na = na or max(96, int(per / 1.1))
    angs = [geo.TAU * i / na for i in range(na)]
    R = [ray_poly(c, a, rim) for a in angs]
    zs = []
    z = bl['bot']
    while z < bl['top'] - 1e-6:
        zs.append(z)
        z += dz * (2.2 if z < 0 else 1.0)
    zs.append(bl['top'])
    tops = []
    for a, r in zip(angs, R):
        x0, y0 = c[0] + math.cos(a) * r, c[1] + math.sin(a) * r
        dn = noise.noise(Vector((x0 / 45.0, y0 / 45.0, bl['seed'] * 1.7)))
        tops.append(bl['top'] - bl.get('drop', 0.0) * geo.smoothstep(-0.05, 0.45, dn))
    rings = []
    for z in zs:
        ring = []
        for a, r, tl in zip(angs, R, tops):
            ca, sa = math.cos(a), math.sin(a)
            x0, y0 = c[0] + ca * r, c[1] + sa * r
            zz = min(z, tl)
            o = radial_offset(bl, a, zz, r, x0, y0)
            if z > tl:  # above the local rock top: pull in under the masonry
                o -= (z - tl) * 1.6 + 1.0
            rr = max(r + o, 2.0)
            ring.append((c[0] + ca * rr, c[1] + sa * rr, zz if z <= tl else z))
        rings.append(ring)
    # plateau: inset ring then apex
    top = bl['top']
    inset = [(c[0] + (p[0] - c[0]) * 0.93, c[1] + (p[1] - c[1]) * 0.93, top + 0.3) for p in rings[-1]]
    rings.append(inset)
    rings.append([(c[0], c[1], top + 0.4)])
    mb = geo.MB(bl['name'])
    mb.loft(rings, 'Rock', cap_bot=False, cap_top=False)
    ob = mb.build(coll, smooth_angle=70)
    return ob


def build(coll=None):
    coll = coll or geo.get_coll('Terrain')
    obs = []
    for bl in BLOBS:
        obs.append(build_blob(bl, coll))
    return obs


def rim_point(name, x, y, inset=0.0):
    """Top-rim point of a rock body in the direction of (x,y), optionally inset."""
    bl = next(b for b in BLOBS if b['name'] == name)
    c = bl['c']
    a = math.atan2(y - c[1], x - c[0])
    r = ray_poly(c, a, bl['rim']) - inset
    return (c[0] + math.cos(a) * r, c[1] + math.sin(a) * r)
