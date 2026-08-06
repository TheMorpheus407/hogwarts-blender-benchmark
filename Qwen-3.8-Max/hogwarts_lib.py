import bpy, bmesh, math, random
import numpy as np
from mathutils import Vector, Matrix

WS = '/home/morpheus/Documents/Projects/Blender/Qwen-3.8-Max'
UP = Vector((0, 0, 1))

def get_coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c

def clear_coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        return
    for ob in list(c.objects):
        me = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if me and me.users == 0:
            try:
                bpy.data.meshes.remove(me)
            except Exception:
                pass

def new_obj(name, bm, coll):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    get_coll(coll).objects.link(ob)
    return ob

def wall_mat(base, tangent, normal):
    t = Vector(tangent).normalized()
    n = Vector(normal).normalized()
    m = Matrix.Identity(4)
    m.col[0][:3] = t
    m.col[1][:3] = UP
    m.col[2][:3] = n
    m.col[3][:3] = Vector(base)
    return m

def M4(loc=(0, 0, 0), rot_z=0.0):
    return Matrix.Translation(Vector(loc)) @ Matrix.Rotation(rot_z, 4, 'Z')

def bm_box(bm, w, d, h, mat=None, z0=0.0, cx=0.0, cy=0.0):
    res = bmesh.ops.create_cube(bm, size=1.0)
    verts = res['verts']
    bmesh.ops.scale(bm, vec=(w, d, h), verts=verts)
    bmesh.ops.translate(bm, vec=(cx, cy, z0 + h * 0.5), verts=verts)
    if mat is not None:
        bmesh.ops.transform(bm, matrix=mat, verts=verts)
    return verts

def bm_wbox(bm, w, h, d, mat, y0=0.0):
    res = bmesh.ops.create_cube(bm, size=1.0)
    verts = res['verts']
    bmesh.ops.scale(bm, vec=(w, h, d), verts=verts)
    bmesh.ops.translate(bm, vec=(0, y0 + h * 0.5, 0), verts=verts)
    bmesh.ops.transform(bm, matrix=mat, verts=verts)
    return verts

def bm_cyl(bm, r, h, seg=16, mat=None, z0=0.0, r2=None, cx=0.0, cy=0.0):
    res = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                                radius1=r, radius2=r2 if r2 is not None else r, depth=h)
    verts = res['verts']
    bmesh.ops.translate(bm, vec=(cx, cy, z0 + h * 0.5), verts=verts)
    if mat is not None:
        bmesh.ops.transform(bm, matrix=mat, verts=verts)
    return verts

def bm_cone(bm, r, h, seg=16, mat=None, z0=0.0, cx=0.0, cy=0.0):
    res = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                                radius1=r, radius2=0.0, depth=h)
    verts = res['verts']
    bmesh.ops.translate(bm, vec=(cx, cy, z0 + h * 0.5), verts=verts)
    if mat is not None:
        bmesh.ops.transform(bm, matrix=mat, verts=verts)
    return verts

def lancet_pts(w, h, segs=4):
    spring = h - 0.866 * w
    pts = [(-w / 2, 0.0), (-w / 2, spring)]
    for i in range(1, segs + 1):
        a = math.radians(180 - 60.0 * i / segs)
        pts.append((w / 2 + w * math.cos(a), spring + w * math.sin(a)))
    for i in range(segs, 0, -1):
        a = math.radians(60.0 * i / segs)
        pts.append((-w / 2 + w * math.cos(a), spring + w * math.sin(a)))
    pts.append((w / 2, 0.0))
    out = []
    seen = set()
    for p in pts:
        key = (round(p[0], 4), round(p[1], 4))
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out

def _wr_layer(bm):
    return bm.faces.layers.float.get('wr') or bm.faces.layers.float.new('wr')

def bm_lancet_face(bm, pts, mat, off, glow=None):
    lay = _wr_layer(bm) if glow is not None else None
    vs = [bm.verts.new(mat @ Vector((x, y, off))) for (x, y) in pts]
    f = bm.faces.new(vs)
    if glow is not None:
        f[lay] = glow
    return f

def bm_lancet_ring(bm, pts, mat, off, scale=1.18, pivot_frac=0.45):
    h = max(p[1] for p in pts)
    pv = h * pivot_frac
    outer = [(x * scale, (y - pv) * scale + pv) for (x, y) in pts]
    vo = [bm.verts.new(mat @ Vector((x, y, off))) for (x, y) in outer]
    vi = [bm.verts.new(mat @ Vector((x, y, off))) for (x, y) in pts]
    n = len(vo)
    for i in range(n):
        j = (i + 1) % n
        try:
            bm.faces.new((vo[i], vo[j], vi[j], vi[i]))
        except ValueError:
            pass

def add_window(bm_g, bm_t, bm_m, w, h, mat, rng, lit_prob=0.75):
    pts = lancet_pts(w, h)
    lit = rng.random() < lit_prob
    glow = rng.uniform(0.15, 1.0) if lit else -1.0
    bm_lancet_face(bm_g, pts, mat, 0.03, glow=glow)
    bm_lancet_ring(bm_t, pts, mat, 0.07)
    bm_wbox(bm_m, w * 0.09, h * 0.85, 0.06, mat, y0=h * 0.05)
    bm_wbox(bm_m, w * 0.9, 0.08, 0.06, mat, y0=h * 0.42)
    bm_wbox(bm_m, w * 0.72, 0.08, 0.06, mat, y0=h * 0.66)

def crenel_ring(bm, r, top, n=None, t=0.35, h=0.9):
    if n is None:
        n = max(8, int(2 * math.pi * r / 1.5))
    for i in range(n):
        a = 2 * math.pi * i / n
        mat = Matrix.Rotation(a, 4, 'Z') @ Matrix.Translation(Vector((r - t * 0.5, 0, top)))
        bm_box(bm, t, 0.55, h, mat=mat, z0=0)

def corbel_ring(bm, r, top, n=None):
    if n is None:
        n = max(10, int(2 * math.pi * r / 1.1))
    bm_cyl(bm, r + 0.25, 0.5, seg=24, z0=top - 0.5)
    for i in range(n):
        a = 2 * math.pi * i / n
        mat = Matrix.Rotation(a, 4, 'Z') @ Matrix.Translation(Vector((r + 0.1, 0, top - 1.1)))
        bm_box(bm, 0.3, 0.45, 0.8, mat=mat, z0=0)

def string_course(bm, r, z, seg=24):
    bm_cyl(bm, r + 0.18, 0.45, seg=seg, z0=z)

def finial(bm, z, h=1.6, mat=None):
    bm_cone(bm, 0.22, h, seg=8, z0=z, mat=mat)
    res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.28)
    bmesh.ops.translate(bm, vec=(0, 0, z + h * 0.75), verts=res['verts'])
    if mat is not None:
        bmesh.ops.transform(bm, matrix=mat, verts=res['verts'])

def cone_roof(bm, r, rh, z0, seg=20, bell=True):
    if bell:
        bm_cone(bm, r * 1.18, rh * 0.22, seg=seg, z0=z0, cx=0, cy=0)
        bm_cyl(bm, r * 1.02, rh * 0.1, seg=seg, z0=z0)
        bm_cone(bm, r * 1.02, rh * 0.85, seg=seg, z0=z0 + rh * 0.15)
    else:
        bm_cone(bm, r, rh, seg=seg, z0=z0)

def build_tower(name, loc, r, h, cap='cone', roof_h=None, rng=None, win_w=0.9, win_h=2.2,
                cols=None, rows=None, crenel=True, corbels=True, courses=(), seg=20,
                cap_r=None, lit_prob=0.75, taper=1.0, base_z=0.0, flare=0.0):
    rng = rng or random.Random(7)
    bm = bmesh.new()
    bm_g = bmesh.new()
    bm_t = bmesh.new()
    bm_m = bmesh.new()
    r2 = r * taper
    if flare > 0:
        bm_cyl(bm, r * (1 + flare), h * 0.35, seg=seg, z0=base_z, r2=r)
        bm_cyl(bm, r, h - h * 0.35, seg=seg, z0=base_z + h * 0.35, r2=r2)
    else:
        bm_cyl(bm, r, h, seg=seg, z0=base_z, r2=r2)
    for z in courses:
        string_course(bm, r, z)
    top = base_z + h
    if cap in ('cone', 'spire'):
        if corbels:
            corbel_ring(bm, r2, top, n=seg)
        cr = cap_r or r2 * 1.15
        rh = roof_h or cr * 2.6
        if cap == 'spire':
            cone_roof(bm, cr, rh, top + 0.3, seg=8, bell=False)
        else:
            cone_roof(bm, cr, rh, top + 0.3, seg=seg)
        finial(bm, top + 0.3 + rh)
    else:
        if crenel:
            crenel_ring(bm, r2, top)
    if cols is None:
        cols = max(2, int(2 * math.pi * r / 4.5))
    if rows is None:
        rows = max(2, int(h / 9))
    for ci in range(cols):
        a = 2 * math.pi * (ci + 0.5) / cols + rng.uniform(-0.08, 0.08)
        nrm = Vector((math.cos(a), math.sin(a), 0))
        tng = Vector((-math.sin(a), math.cos(a), 0))
        for ri in range(rows):
            if rng.random() < 0.18:
                continue
            z = base_z + 5 + (h - 11) * (ri + 0.5) / rows + rng.uniform(-0.8, 0.8)
            ww = win_w * rng.uniform(0.85, 1.2)
            wh = win_h * rng.uniform(0.85, 1.2)
            base = Vector((loc[0], loc[1], z)) + nrm * (r * 0.99)
            m = wall_mat(base, tng, nrm)
            add_window(bm_g, bm_t, bm_m, ww, wh, m, rng, lit_prob)
    bmesh.ops.translate(bm, verts=bm.verts[:], vec=(loc[0], loc[1], 0))
    ob = new_obj(name, bm, 'Castle')
    new_obj(name + '_trim', bm_t, 'Castle')
    new_obj(name + '_mull', bm_m, 'Castle')
    new_obj(name + '_glass', bm_g, 'Castle')
    return ob

def build_hall(name, loc, rot_z, L, W, H, rng=None, win_w=1.1, win_h=3.6, bay=6.5,
               turret_r=2.2, turret_h=None, lit_prob=0.8, base_z=0.0):
    rng = rng or random.Random(11)
    bm = bmesh.new()
    bm_g = bmesh.new()
    bm_t = bmesh.new()
    bm_m = bmesh.new()
    mat0 = M4((loc[0], loc[1], base_z), rot_z)
    bm_box(bm, L, W, H, mat=mat0)
    roof_h = W * 0.9
    prof = [(-L / 2 - 0.6, H - 0.3), (L / 2 + 0.6, H - 0.3), (L / 2 + 0.6, H + 0.2),
            (0, H + roof_h), (-L / 2 - 0.6, H + 0.2)]
    vs = [bm.verts.new(Vector((x, -W / 2 - 0.6, z))) for (x, z) in prof]
    vs2 = [bm.verts.new(Vector((x, W / 2 + 0.6, z))) for (x, z) in prof]
    n = len(vs)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vs[i], vs[j], vs2[j], vs2[i]))
    bm.faces.new(vs)
    bm.faces.new(list(reversed(vs2)))
    bm_box(bm, L + 1.4, 0.18, 0.5, mat=mat0, z0=H + roof_h - 0.1)
    nb = max(2, int(L / bay))
    for side in (-1, 1):
        for i in range(nb + 1):
            x = -L / 2 + L * i / nb
            mloc = mat0 @ Matrix.Translation(Vector((x, side * (W / 2 + 0.25), 0)))
            bm_box(bm, 1.1, 1.4, H + 2.2, mat=mloc)
            bm_box(bm, 0.8, 1.0, 1.2, mat=mloc, z0=H + 2.2)
            bm_cone(bm, 0.45, 2.2, seg=8, mat=mloc, z0=H + 3.2)
        for i in range(nb):
            x = -L / 2 + L * (i + 0.5) / nb
            nrm = Vector((0, side, 0))
            tng = Vector((1, 0, 0))
            for (zz, ww, hh) in ((4.0, win_w, win_h), (10.0, win_w * 0.8, win_h * 0.75)):
                base = mat0 @ (Vector((x, side * (W / 2), zz)))
                n2 = mat0.to_3x3() @ nrm
                t2 = mat0.to_3x3() @ tng
                m = wall_mat(base, t2, n2)
                add_window(bm_g, bm_t, bm_m, ww * rng.uniform(0.9, 1.1), hh, m, rng, lit_prob)
    for sx in (-1, 1):
        tl = mat0 @ Matrix.Translation(Vector((sx * L / 2, 0, 0)))
        nrm = mat0.to_3x3() @ Vector((sx, 0, 0))
        tng = mat0.to_3x3() @ Vector((0, -sx, 0))
        for i in range(2):
            zz = 5 + i * 6
            base = mat0 @ (Vector((sx * L / 2, 0, zz)))
            m = wall_mat(base, tng, nrm)
            add_window(bm_g, bm_t, bm_m, win_w * 1.4, win_h * 1.3, m, rng, lit_prob)
    for sx in (-1, 1):
        for sy in (-1, 1):
            tl = mat0 @ Matrix.Translation(Vector((sx * L / 2, sy * W / 2, 0)))
            th = (turret_h or H + 10) + rng.uniform(0, 4)
            bm_cyl(bm, turret_r, th, seg=12, mat=tl)
            corbel_ring(bm, turret_r, th, n=10)
            cone_roof(bm, turret_r * 1.2, turret_r * 3.0, th + 0.2, seg=12)
            finial(bm, th + 0.2 + turret_r * 3.0, mat=tl)
    new_obj(name, bm, 'Castle')
    new_obj(name + '_trim', bm_t, 'Castle')
    new_obj(name + '_mull', bm_m, 'Castle')
    new_obj(name + '_glass', bm_g, 'Castle')

def build_wall(name, p0, p1, h, t=1.2, cren=True, z0=0.0, rng=None):
    rng = rng or random.Random(5)
    bm = bmesh.new()
    p0 = Vector((p0[0], p0[1], 0))
    p1 = Vector((p1[0], p1[1], 0))
    d = p1 - p0
    L = d.length
    ang = math.atan2(d.y, d.x)
    mat = Matrix.Translation(p0) @ Matrix.Rotation(ang, 4, 'Z')
    bm_box(bm, L, t, h, mat=mat, z0=z0, cx=L * 0.5)
    if cren:
        nn = max(2, int(L / 1.6))
        for i in range(nn + 1):
            x = L * i / nn
            bm_box(bm, 0.55, t + 0.1, 0.9, mat=mat, z0=z0 + h)
    new_obj(name, bm, 'Castle')

def build_viduct(name, p0, p1, deck, pier_w=3.0, arch_n=8, width=5.0, z0=0.0):
    bm = bmesh.new()
    p0 = Vector((p0[0], p0[1], 0))
    p1 = Vector((p1[0], p1[1], 0))
    d = p1 - p0
    L = d.length
    ang = math.atan2(d.y, d.x)
    span = L / arch_n
    prof = [(0.0, z0 - 1.0)]
    for i in range(arch_n):
        x0 = i * span
        rise = deck - 5.0
        prof.append((x0 + pier_w * 0.5, z0 - 1.0))
        prof.append((x0 + pier_w * 0.5, rise * 0.55))
        for s in range(1, 6):
            a = math.pi * s / 6.0
            px = x0 + span * 0.5 - (span * 0.5 - pier_w * 0.5) * math.cos(a)
            pz = rise * 0.55 + (rise * 0.45) * math.sin(a)
            prof.append((px, pz))
        prof.append((x0 + span - pier_w * 0.5, rise * 0.55))
        prof.append((x0 + span - pier_w * 0.5, z0 - 1.0))
    prof.append((L, z0 - 1.0))
    prof.append((L, deck))
    prof.append((0.0, deck))
    vs = [bm.verts.new(Vector((x, -width / 2, z))) for (x, z) in prof]
    vs2 = [bm.verts.new(Vector((x, width / 2, z))) for (x, z) in prof]
    n = len(vs)
    for i in range(n):
        j = (i + 1) % n
        try:
            bm.faces.new((vs[i], vs[j], vs2[j], vs2[i]))
        except ValueError:
            pass
    bm.faces.new(vs)
    bm.faces.new(list(reversed(vs2)))
    mat = Matrix.Translation(p0) @ Matrix.Rotation(ang, 4, 'Z')
    bmesh.ops.transform(bm, matrix=mat, verts=bm.verts[:])
    new_obj(name, bm, 'Castle')
    bmp = bmesh.new()
    bm_box(bmp, L, 0.35, 1.1, mat=Matrix.Translation(Vector((L * 0.5, width / 2 - 0.15, deck))))
    bm_box(bmp, L, 0.35, 1.1, mat=Matrix.Translation(Vector((L * 0.5, -width / 2 + 0.15, deck))))
    nl = int(L / 6.0)
    for i in range(nl + 1):
        x = L * i / nl
        for side in (-1, 1):
            bm_box(bmp, 0.35, 0.35, 0.9, mat=Matrix.Translation(Vector((x, side * (width / 2 - 0.15), deck + 1.1))))
    bmesh.ops.transform(bmp, matrix=mat, verts=bmp.verts[:])
    new_obj(name + '_parapet', bmp, 'Castle')

def build_stair(name, p0, p1, z0, z1, width=2.2, wall_h=1.1):
    bm = bmesh.new()
    p0 = Vector((p0[0], p0[1], 0))
    p1 = Vector((p1[0], p1[1], 0))
    d = p1 - p0
    L = d.length
    ang = math.atan2(d.y, d.x)
    n = max(4, int((z1 - z0) / 0.35))
    prof = [(0.0, z0 - 0.5)]
    for i in range(n):
        x = L * i / n
        x2 = L * (i + 1) / n
        z2 = z0 + (z1 - z0) * (i + 1) / n
        prof.append((x, z2))
        prof.append((x2, z2))
    prof.append((L, z1))
    prof.append((L, z0 - 0.5))
    vs = [bm.verts.new(Vector((x, -width / 2, z))) for (x, z) in prof]
    vs2 = [bm.verts.new(Vector((x, width / 2, z))) for (x, z) in prof]
    nn = len(vs)
    for i in range(nn):
        j = (i + 1) % nn
        try:
            bm.faces.new((vs[i], vs[j], vs2[j], vs2[i]))
        except ValueError:
            pass
    bm.faces.new(vs)
    bm.faces.new(list(reversed(vs2)))
    mat = Matrix.Translation(p0) @ Matrix.Rotation(ang, 4, 'Z')
    bmesh.ops.transform(bm, matrix=mat, verts=bm.verts[:])
    new_obj(name, bm, 'Castle')
    slope = math.atan2(z1 - z0, L)
    sl = math.sqrt(L * L + (z1 - z0) ** 2)
    bmp = bmesh.new()
    for side in (-1, 1):
        mm = Matrix.Translation(Vector((0, side * width / 2, 0))) @ Matrix.Rotation(-slope, 4, 'Y')
        bm_box(bmp, sl, 0.25, wall_h, mat=mm, z0=0, cx=sl * 0.5)
    bmesh.ops.transform(bmp, matrix=mat, verts=bmp.verts[:])
    new_obj(name + '_wall', bmp, 'Castle')

def build_greenhouse(name, loc, w, d, h, rot_z=0.0):
    bm = bmesh.new()
    bm_g = bmesh.new()
    mat0 = M4(loc, rot_z)
    bm_box(bm, w, d, 1.2, mat=mat0)
    gh = h
    prof = [(-w / 2, 1.2), (w / 2, 1.2), (w / 2, 1.2 + gh * 0.6), (0, 1.2 + gh), (-w / 2, 1.2 + gh * 0.6)]
    vs = [bm_g.verts.new(Vector((x, -d / 2, z))) for (x, z) in prof]
    vs2 = [bm_g.verts.new(Vector((x, d / 2, z))) for (x, z) in prof]
    n = len(vs)
    for i in range(n):
        j = (i + 1) % n
        bm_g.faces.new((vs[i], vs[j], vs2[j], vs2[i]))
    bm_g.faces.new(vs)
    bm_g.faces.new(list(reversed(vs2)))
    bmesh.ops.transform(bm_g, matrix=mat0, verts=bm_g.verts[:])
    nr = max(2, int(d / 1.4))
    for i in range(1, nr):
        y = -d / 2 + d * i / nr
        p2 = [(-w / 2 - 0.08, 1.15), (w / 2 + 0.08, 1.15), (w / 2 + 0.08, 1.2 + gh * 0.6),
              (0, 1.2 + gh + 0.08), (-w / 2 - 0.08, 1.2 + gh * 0.6)]
        a = [bm.verts.new(mat0 @ Vector((x, y - 0.04, z))) for (x, z) in p2]
        b = [bm.verts.new(mat0 @ Vector((x, y + 0.04, z))) for (x, z) in p2]
        nn = len(a)
        for i2 in range(nn):
            j = (i2 + 1) % nn
            bm.faces.new((a[i2], a[j], b[j], b[i2]))
    new_obj(name, bm, 'Castle')
    obg = new_obj(name + '_glass', bm_g, 'Castle')
    obg['mat'] = 'ghglass'

def build_lantern(name, loc, z):
    bm = bmesh.new()
    bm_cyl(bm, 0.06, 2.6, seg=6, z0=0)
    bm_cyl(bm, 0.16, 0.25, seg=6, z0=2.95)
    res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.14)
    bmesh.ops.translate(bm, vec=(0, 0, 2.8), verts=res['verts'])
    bm_cone(bm, 0.22, 0.3, seg=6, z0=3.2)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector((loc[0], loc[1], z))), verts=bm.verts[:])
    ob = new_obj(name, bm, 'Lights')
    ob['mat'] = 'lantern'

def build_clock(name, loc, size, h, rng=None, lit_prob=0.7, base_z=0.0):
    rng = rng or random.Random(21)
    bm = bmesh.new()
    bm_g = bmesh.new()
    bm_t = bmesh.new()
    bm_m = bmesh.new()
    s = size
    bm_box(bm, s, s, h)
    top = h
    crenel_ring(bm, s * 0.62, top, n=16, t=0.4)
    bm_cone(bm, s * 0.5, s * 2.2, seg=8, z0=top + 0.5)
    finial(bm, top + 0.5 + s * 2.2)
    for side in range(4):
        a = math.radians(90 * side - 90)
        nrm = Vector((math.cos(a), math.sin(a), 0))
        tng = Vector((-math.sin(a), math.cos(a), 0))
        for ri in range(3):
            z = 8 + ri * 10
            if z > h - 8:
                break
            base = Vector((0, 0, z)) + nrm * (s * 0.5)
            m = wall_mat(base, tng, nrm)
            add_window(bm_g, bm_t, bm_m, 1.0, 2.6, m, rng, lit_prob)
    tr = Matrix.Translation(Vector((loc[0], loc[1], base_z)))
    bmesh.ops.transform(bm, matrix=tr, verts=bm.verts[:])
    bmesh.ops.transform(bm_g, matrix=tr, verts=bm_g.verts[:])
    bmesh.ops.transform(bm_t, matrix=tr, verts=bm_t.verts[:])
    bmesh.ops.transform(bm_m, matrix=tr, verts=bm_m.verts[:])
    new_obj(name, bm, 'Castle')
    new_obj(name + '_trim', bm_t, 'Castle')
    new_obj(name + '_mull', bm_m, 'Castle')
    new_obj(name + '_glass', bm_g, 'Castle')
    bmc = bmesh.new()
    nrm = Vector((0, -1, 0))
    tng = Vector((1, 0, 0))
    cz = h - 6
    base = Vector((0, -s * 0.5, cz))
    m = wall_mat(base, tng, nrm)
    res = bmesh.ops.create_cone(bmc, cap_ends=True, segments=24, radius1=2.4, radius2=2.4, depth=0.15)
    bmesh.ops.transform(bmc, matrix=tr @ m, verts=res['verts'])
    new_obj(name + '_clockface', bmc, 'Castle')['mat'] = 'clockface'
    bmh = bmesh.new()
    m1 = m @ Matrix.Rotation(math.radians(20), 4, 'Z') @ Matrix.Translation(Vector((0, 0, 0.12)))
    bm_wbox(bmh, 0.16, 1.7, 0.08, m1, y0=-0.3)
    m2 = m @ Matrix.Rotation(math.radians(115), 4, 'Z') @ Matrix.Translation(Vector((0, 0, 0.14)))
    bm_wbox(bmh, 0.13, 1.25, 0.08, m2, y0=-0.25)
    bmesh.ops.transform(bmh, matrix=tr, verts=bmh.verts[:])
    new_obj(name + '_hands', bmh, 'Castle')['mat'] = 'clockhand'
