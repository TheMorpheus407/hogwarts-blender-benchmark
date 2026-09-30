"""Boats with lanterns, Hagrid's hut (+ chimney smoke), Quidditch pitch, stone circle."""
import bpy, math, random
from mathutils import Vector, Matrix, noise
import geo, arch, terrain
from geo import MB, mat_loc, TAU
from materials import NT

LIGHTS = []   # (x, y, z, power, colour)


# ------------------------------------------------------------------ boats
def boat(mb, M, rnd, people=3):
    L = 3.8
    secs = 9
    rings = [[(-L / 2, 0.0, 0.42)]]
    for i in range(1, secs):
        u = -1 + 2 * i / secs
        x = u * L / 2
        hw = 0.66 * (1 - abs(u) ** 2.2) ** 0.55
        dep = 0.55 * (1 - abs(u) ** 3) ** 0.5
        sheer = 0.32 + 0.14 * u * u
        ring = []
        for k in range(7):
            a = math.pi * k / 6
            ring.append((x, -hw * math.cos(a), sheer - dep * math.sin(a) * (0.6 + 0.4 * math.sin(a))))
        rings.append(ring)
    rings.append([(L / 2, 0.0, 0.5)])
    mb.loft(rings, 'Wood', M, cap_bot=False, cap_top=False, closed=False)
    # gunwale rails and thwarts
    for sy in (-1, 1):
        pts = [(r[0][0], sy * abs(r[0][1]), r[0][2]) for r in rings[1:-1]]
        pts = [(-L / 2, 0, 0.42)] + pts + [(L / 2, 0, 0.5)]
        for a, b in zip(pts[:-1], pts[1:]):
            va, vb = Vector(a), Vector(b)
            ln = (vb - va).length
            mid = (va + vb) / 2
            ang = math.atan2(vb.y - va.y, vb.x - va.x)
            m = M @ Matrix.Translation(mid) @ Matrix.Rotation(ang, 4, 'Z')
            mb.box(-ln / 2, -0.04, -0.03, ln / 2, 0.04, 0.05, 'Beam', m)
    for x in (-0.9, 0.1, 1.0):
        hw = 0.66 * (1 - abs(2 * x / L) ** 2.2) ** 0.55
        mb.box(x - 0.12, -hw + 0.05, 0.1, x + 0.12, hw - 0.05, 0.16, 'Beam', M)
    # lantern on a bow pole
    mb.box(L / 2 - 0.35 - 0.03, -0.03, 0.2, L / 2 - 0.35 + 0.03, 0.03, 1.75, 'Iron', M)
    mb.box(L / 2 - 0.35, -0.03, 1.7, L / 2 + 0.05, 0.03, 1.76, 'Iron', M)
    lx = L / 2 + 0.05
    mb.box(lx - 0.1, -0.1, 1.3, lx + 0.1, 0.1, 1.58, 'Lantern', M)
    mb.lathe([(0.14, 1.58), (0.02, 1.72)], 4, 'Iron', M @ mat_loc((lx, 0, 0), math.pi / 4))
    p = M @ Vector((lx, 0, 1.44))
    LIGHTS.append((p.x, p.y, p.z, 2.2 + rnd.uniform(-0.5, 0.8), (1.0, 0.55, 0.22)))
    # passengers: cloaked figures
    seats = [(-0.9, 0.0), (0.1, -0.22), (0.1, 0.22), (1.0, 0.0)]
    rnd.shuffle(seats)
    for sx, sy in seats[:people]:
        h = rnd.uniform(1.05, 1.25)
        m = M @ mat_loc((sx, sy, 0.1), rnd.uniform(-0.3, 0.3))
        mb.lathe([(0.0, 0.0), (0.3, 0.02), (0.26, h * 0.45), (0.17, h * 0.78), (0.1, h * 0.82), (0.0, h * 0.84)],
                 8, 'Cloak', m)
        mb.lathe([(0.0, h * 0.8), (0.11, h * 0.86), (0.12, h * 0.95), (0.09, h * 1.04), (0.0, h * 1.07)], 8, 'Skin', m)


def build_boats(coll):
    rnd = random.Random(5)
    mb = MB('Lake_Boats')
    # a loose flotilla heading for the boathouse
    head = math.radians(72.0)
    base = Vector((-30.0, -300.0, 0.0))
    offsets = [(0, 0), (-9, -14), (10, -12), (-20, -30), (2, -31), (19, -28), (-12, -47), (9, -50), (-28, -60),
               (23, -58), (-3, -70)]
    for i, (ox, oy) in enumerate(offsets):
        R = Matrix.Rotation(head - math.pi / 2, 4, 'Z')
        pos = base + R @ Vector((ox, oy, 0))
        pos.x += rnd.uniform(-2.5, 2.5)
        pos.y += rnd.uniform(-2.5, 2.5)
        yaw = head + rnd.uniform(-0.12, 0.12)
        M = Matrix.Translation((pos.x, pos.y, -0.08)) @ Matrix.Rotation(yaw, 4, 'Z') @ \
            Matrix.Rotation(rnd.uniform(-0.03, 0.03), 4, 'X')
        boat(mb, M, rnd, people=rnd.choice((2, 3, 3, 4)))
    import castle
    for (x, y, yaw) in castle.MOORED:
        M = Matrix.Translation((x, y, -0.1)) @ Matrix.Rotation(yaw, 4, 'Z')
        boat(mb, M, rnd, people=0)
    ob = mb.build(coll, smooth_angle=50)
    return ob


# ------------------------------------------------------------------ Hagrid's hut
def build_hut(coll):
    mb = MB('Hagrid_Hut')
    x, y = terrain.HUT
    g = min(terrain.height(x + dx, y + dy) for dx in (-5, 0, 5) for dy in (-5, 0, 5))
    z0 = g - 0.8
    r = 4.2
    arch.RNG.seed(3)
    mb.lathe([(r + 0.3, z0), (r, z0 + 0.9), (r, z0 + 3.8)], 14, 'Stone', mat_loc((x, y, 0)))
    for k, a in enumerate((0.4, 2.0, 3.6, 5.0)):
        rr = r * math.cos(math.pi / 14)
        M = mat_loc((x + rr * math.cos(a), y + rr * math.sin(a), z0 + 1.6), a + math.pi / 2)
        arch.window(mb, M, 0.75, 1.1, 'round', depth=0.18, frame=0.12, glow=1.6 if k != 2 else 0.9, mullion=0,
                    sill=False, hood=False)
    M = mat_loc((x + r * math.cos(-1.2), y + r * math.sin(-1.2), z0 + 0.9), -1.2 + math.pi / 2)
    arch.door(mb, M, 1.4, 2.5, glow=0.0)
    # steep conical roof (thatch/turf)
    mb.lathe([(r + 1.0, z0 + 3.6), (r + 0.9, z0 + 3.9), (r * 0.55, z0 + 6.4), (0.3, z0 + 8.4), (0.0, z0 + 8.6)], 18, 'Thatch',
             mat_loc((x, y, 0)))
    # chimney
    cx, cy = x + 1.6, y + 2.1
    mb.box(cx - 0.55, cy - 0.55, z0 + 3.0, cx + 0.55, cy + 0.55, z0 + 9.2, 'Stone')
    mb.box(cx - 0.7, cy - 0.7, z0 + 9.2, cx + 0.7, cy + 0.7, z0 + 9.5, 'StoneTrim')
    # woodpile, fence, pumpkin patch
    rnd = random.Random(8)
    for k in range(10):
        px = x - 9 + k * 1.3
        py = y - 9 + rnd.uniform(-0.3, 0.3)
        gz = terrain.height(px, py)
        mb.box(px - 0.06, py - 0.06, gz - 0.3, px + 0.06, py + 0.06, gz + 1.1, 'Beam')
        mb.box(px - 0.7, py - 0.04, gz + 0.8, px + 0.7, py + 0.04, gz + 0.9, 'Beam')
    for k in range(9):
        px = x - 8 + rnd.uniform(-3, 3)
        py = y - 5 + rnd.uniform(-3, 3)
        gz = terrain.height(px, py)
        rr = rnd.uniform(0.3, 0.6)
        mb.lathe([(0.0, gz - 0.05), (rr, gz + rr * 0.35), (rr * 0.9, gz + rr * 0.8), (0.0, gz + rr * 0.95)], 10, 'Pumpkin',
                 mat_loc((px, py, 0)))
    mb.build(coll, smooth_angle=45)
    LIGHTS.append((x, y, z0 + 2.0, 60.0, (1.0, 0.5, 0.2)))
    LIGHTS.append((x + r * math.cos(-1.2) * 1.3, y + r * math.sin(-1.2) * 1.3, z0 + 2.6, 12.0, (1.0, 0.5, 0.2)))
    # chimney smoke volume
    smoke(coll, cx, cy, z0 + 9.5)


def smoke(coll, x, y, z):
    t = NT('ChimneySmoke')
    tc = t.n('ShaderNodeTexCoord')
    obj = tc.outputs['Object']
    sep = t.n('ShaderNodeSeparateXYZ', inp={'Vector': obj})
    lz = t.math('SUBTRACT', sep.outputs[2], z)
    # drift with the wind (towards +x) as it rises
    drift = t.math('MULTIPLY', t.math('POWER', t.math('MAXIMUM', lz, 0.0), 1.35), 0.55)
    dx = t.math('SUBTRACT', t.math('SUBTRACT', sep.outputs[0], x), drift)
    dy = t.math('SUBTRACT', sep.outputs[1], y)
    rad = t.math('SQRT', t.math('ADD', t.math('MULTIPLY', dx, dx), t.math('MULTIPLY', dy, dy)))
    width = t.math('ADD', 0.5, t.math('MULTIPLY', lz, 0.42))
    core = t.maprange(t.math('DIVIDE', rad, width), 1.0, 0.0, 0.0, 1.0)
    n = t.noise(obj, 0.7, 5.0, 0.6, dist=0.8).outputs['Fac']
    puff = t.maprange(n, 0.35, 0.75, 0.0, 1.0)
    fade = t.maprange(lz, 0.0, 26.0, 1.0, 0.0)
    dens = t.math('MULTIPLY', t.math('MULTIPLY', core, puff), t.math('MULTIPLY', fade, 0.22))
    pv = t.n('ShaderNodeVolumePrincipled', inp={'Color': (0.35, 0.36, 0.38, 1), 'Anisotropy': 0.2})
    t.l(dens, pv.inputs['Density'])
    t.l(pv.outputs[0], t.out.inputs['Volume'])
    mb = MB('FX_ChimneySmoke')
    mb.box(x - 5, y - 9, z - 0.2, x + 26, y + 9, z + 27, 'ChimneySmoke')
    ob = mb.build(geo.get_coll('FX'))
    return ob


# ------------------------------------------------------------------ Quidditch pitch
def build_pitch(coll):
    mb = MB('Quidditch_Pitch')
    px, py = terrain.PITCH
    zg = terrain.height(px, py)
    rx, ry = 88.0, 52.0
    # mown oval (slightly lighter grass) with a chalk centre circle
    ring = [(px + rx * math.cos(TAU * i / 64), py + ry * math.sin(TAU * i / 64)) for i in range(64)]
    mb.add([(x, y, zg + 0.08) for x, y in ring], [tuple(range(64))], 'Pitch')
    rnd = random.Random(12)
    house = ['ClothRed', 'ClothGreen', 'ClothBlue', 'ClothYellow']
    n = 14
    for i in range(n):
        a = TAU * (i + 0.5) / n
        tx, ty = px + (rx + 9) * math.cos(a), py + (ry + 9) * math.sin(a)
        gz = terrain.height(tx, ty)
        h = rnd.uniform(16, 24)
        w = rnd.uniform(4.0, 5.0)
        M = mat_loc((tx, ty, 0), a + math.pi / 2)
        # timber scaffold
        for sx in (-1, 1):
            for sy in (-1, 1):
                mb.box(sx * w / 2 - 0.2, sy * w / 2 - 0.2, gz - 0.5, sx * w / 2 + 0.2, sy * w / 2 + 0.2, gz + h, 'Beam', M)
        for zz in range(int(h / 3)):
            z = gz + 1.5 + zz * 3
            mb.box(-w / 2, -w / 2, z, w / 2, -w / 2 + 0.15, z + 0.2, 'Beam', M)
            mb.box(-w / 2, w / 2 - 0.15, z, w / 2, w / 2, z + 0.2, 'Beam', M)
        # stand box clad in house cloth, roof cone
        cl = house[i % 4]
        mb.box(-w / 2 - 0.3, -w / 2 - 0.3, gz + h - 1.5, w / 2 + 0.3, w / 2 + 0.3, gz + h + 1.6, cl, M)
        mb.box(-w / 2 - 0.3, -w / 2 - 0.3, gz + h - 5.5, w / 2 + 0.3, w / 2 + 0.3, gz + h - 1.5, cl, M)
        arch.pyramid_roof(mb, [tuple((M @ Vector(p))[:2]) for p in
                               [(-w / 2 - 0.5, -w / 2 - 0.5, 0), (w / 2 + 0.5, -w / 2 - 0.5, 0),
                                (w / 2 + 0.5, w / 2 + 0.5, 0), (-w / 2 - 0.5, w / 2 + 0.5, 0)]],
                          gz + h + 1.6, rnd.uniform(4.5, 6.5), over=0.2, mat=cl, finial=True, bell=0.0)
    # three golden hoops at each end
    for side in (-1, 1):
        for k, (dy, hh) in enumerate(((-9, 15.0), (0, 18.0), (9, 13.0))):
            hx, hy = px + side * (rx - 6), py + dy
            gz = terrain.height(hx, hy)
            mb.lathe([(0.18, gz - 0.5), (0.14, gz + hh - 2.4)], 10, 'Gold', mat_loc((hx, hy, 0)))
            # torus ring in the x-z plane facing along x
            R, r = 2.2, 0.16
            cz = gz + hh
            rings = []
            for j in range(24):
                a = TAU * j / 24
                c = Vector((0, R * math.cos(a), R * math.sin(a)))
                ringp = []
                for q in range(8):
                    b = TAU * q / 8
                    nrm = Vector((0, math.cos(a), math.sin(a)))
                    p = c + nrm * (r * math.cos(b)) + Vector((r * math.sin(b), 0, 0))
                    ringp.append(p)
                rings.append(ringp)
            verts = []
            faces = []
            for j in range(24):
                for q in range(8):
                    verts.append(tuple(rings[j][q]))
            for j in range(24):
                for q in range(8):
                    a0 = j * 8 + q
                    a1 = j * 8 + (q + 1) % 8
                    b0 = ((j + 1) % 24) * 8 + q
                    b1 = ((j + 1) % 24) * 8 + (q + 1) % 8
                    faces.append((b0, b1, a1, a0))
            mb.add(verts, faces, 'Gold', mat_loc((hx, hy, cz)))
    mb.build(coll, smooth_angle=60)


# ------------------------------------------------------------------ stone circle
def build_stones(coll):
    mb = MB('Stone_Circle')
    sx, sy = terrain.STONES
    rnd = random.Random(21)
    n = 13
    for i in range(n):
        a = TAU * i / n + rnd.uniform(-0.08, 0.08)
        rr = 13.0 + rnd.uniform(-0.8, 0.8)
        x, y = sx + rr * math.cos(a), sy + rr * math.sin(a)
        gz = terrain.height(x, y)
        h = rnd.uniform(2.6, 4.4)
        if i in (4, 9):
            h *= 0.45  # fallen / broken
        w, d = rnd.uniform(1.0, 1.6), rnd.uniform(0.5, 0.8)
        prof = []
        rings = []
        for k in range(6):
            t = k / 5
            s = 1.0 - 0.35 * t * t
            jx = rnd.uniform(-0.08, 0.08)
            rings.append([(jx + s * w / 2 * math.cos(TAU * q / 8 + 0.3) * (1 + rnd.uniform(-0.12, 0.12)),
                           s * d / 2 * math.sin(TAU * q / 8 + 0.3) * (1 + rnd.uniform(-0.12, 0.12)),
                           -0.6 + (h + 0.6) * t) for q in range(8)])
        rings.append([(rnd.uniform(-0.1, 0.1), 0, h + 0.25)])
        mb.loft(rings, 'Rock', mat_loc((x, y, gz), a + rnd.uniform(-0.3, 0.3)))
    mb.build(coll, smooth_angle=35)


def build_islet(coll):
    """foreground islet framing the hero: slabby rocks, a few old pines, heather."""
    import nature
    mb = MB('Foreground_Islet')
    rnd = random.Random(44)
    cx, cy = -113.0, -402.0
    # rock mass: lofted blob
    rings = []
    na = 40
    for k, (z, s) in enumerate(((-3.0, 1.15), (-0.5, 1.1), (0.6, 1.0), (1.5, 0.85), (2.3, 0.6), (2.7, 0.3))):
        ring = []
        for i in range(na):
            a = TAU * i / na
            r = (14.0 + 5.0 * math.sin(2 * a + 0.7) + 3.0 * math.sin(3 * a + 2.0)) * (0.62 + 0.38 * abs(math.cos(a - 0.4)))
            r *= s * (1 + 0.12 * noise.noise(Vector((math.cos(a) * 2, math.sin(a) * 2, z * 0.3))))
            ring.append((cx + r * math.cos(a), cy + r * math.sin(a) * 0.7, z + rnd.uniform(-0.25, 0.25)))
        rings.append(ring)
    rings.append([(cx, cy, 2.9)])
    mb.loft(rings, 'Rock', cap_bot=False, cap_top=False)
    # slabs and boulders
    for k in range(26):
        a = rnd.random() * TAU
        rr = rnd.uniform(2, 15)
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a) * 0.7
        sz = rnd.uniform(0.8, 3.0)
        prof = [(0.0, -0.4), (sz, 0.0), (sz * 0.85, sz * 0.45), (sz * 0.3, sz * 0.8), (0.0, sz * 0.85)]
        mb.lathe(prof, 6, 'Rock', mat_loc((x, y, max(0.0, 2.4 - rr * 0.15) + rnd.uniform(-0.8, 0.2)), rnd.random() * 6))
    # pines (scaled prototype geometry)
    for k, (dx, dy, h) in enumerate(((-5, 2, 23.0), (2, -2, 18.0), (7, 3, 13.0), (-9, -3, 10.0), (10, -2, 7.0))):
        tm = MB('tmp')
        nature.conifer2(tm, h, h * 0.22, 500 + k, 'spruce')
        M = mat_loc((cx + dx, cy + dy, 2.0), rnd.random() * 6)
        base = len(mb.v)
        for v in tm.v:
            q = M @ Vector(v)
            mb.v.append((q.x, q.y, q.z))
        for f_, m_ in zip(tm.f, tm.fm):
            mb.f.append(tuple(base + i for i in f_))
            mb.fm.append(mb.mi(tm.mats[m_]))
            mb.fg.append(0.0)
            mb.fr.append(rnd.random())
    for k in range(22):
        a = rnd.random() * TAU
        rr = rnd.uniform(2, 16)
        tm = MB('tmp')
        nature.shrub(tm, rnd.uniform(0.6, 1.3), 900 + k)
        M = mat_loc((cx + rr * math.cos(a), cy + rr * math.sin(a) * 0.7, 2.6 - rr * 0.12), rnd.random() * 6)
        base = len(mb.v)
        for v in tm.v:
            q = M @ Vector(v)
            mb.v.append((q.x, q.y, q.z))
        for f_, m_ in zip(tm.f, tm.fm):
            mb.f.append(tuple(base + i for i in f_))
            mb.fm.append(mb.mi(tm.mats[m_]))
            mb.fg.append(0.0)
            mb.fr.append(rnd.random())
    mb.build(coll, smooth_angle=60)


def materials():
    from materials import simple
    simple('Cloak', (0.012, 0.012, 0.014), 0.85)
    simple('Skin', (0.35, 0.22, 0.16), 0.6)
    simple('Thatch', (0.08, 0.06, 0.035), 0.95, bumpscale=9.0, bumpstr=0.9)
    simple('Pumpkin', (0.45, 0.14, 0.02), 0.5)
    simple('Pitch', (0.04, 0.07, 0.025), 0.9, bumpscale=3.0, bumpstr=0.2)
    simple('ClothRed', (0.25, 0.02, 0.02), 0.8)
    simple('ClothGreen', (0.02, 0.12, 0.05), 0.8)
    simple('ClothBlue', (0.02, 0.05, 0.22), 0.8)
    simple('ClothYellow', (0.4, 0.28, 0.02), 0.8)


def build():
    LIGHTS.clear()
    materials()
    geo.clear_coll('Props')
    coll = geo.get_coll('Props', geo.get_coll('Nature'))
    for n in ('FX_ChimneySmoke',):
        o = bpy.data.objects.get(n)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)
    build_boats(geo.get_coll('Water'))
    build_hut(coll)
    build_pitch(coll)
    build_stones(coll)
    build_islet(coll)
    return len(LIGHTS)
