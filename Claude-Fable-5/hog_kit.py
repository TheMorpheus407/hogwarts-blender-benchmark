"""Gothic architecture kit. Loaded as module 'hogkit'.

Conventions:
- Window templates face local -Y (glass recessed toward +Y).
- windows_on_wall walks along `direction`; windows face RIGHT of direction.
- Locations are bottom-anchored unless noted.
"""
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
import hog

TAU = math.pi * 2


# ------------------------------------------------------------- role materials
def role_mats():
    """Placeholder materials by role; the materials pass rewrites node trees."""
    return {
        'wall': hog.flat_mat('WallStone', (0.45, 0.42, 0.36), 0.9),
        'trim': hog.flat_mat('TrimStone', (0.55, 0.52, 0.46), 0.85),
        'slate': hog.flat_mat('RoofSlate', (0.09, 0.11, 0.14), 0.7),
        'copper': hog.flat_mat('RoofCopper', (0.18, 0.42, 0.36), 0.5),
        'glass': hog.flat_mat('WindowGlass', (0.03, 0.03, 0.04), 0.15),
        'wood': hog.flat_mat('Wood', (0.13, 0.09, 0.06), 0.8),
        'rock': hog.mat_rock(),
    }


M = None  # filled by init()


def init():
    global M
    M = role_mats()


# ------------------------------------------------------------------ 2D shapes
def arch_outline(w, rise, seg=10):
    """Two-centre pointed arch from right springing (w/2,0) via apex (0,rise)
    to left springing (-w/2,0). Returns list of (x, z)."""
    hw = w / 2.0
    if rise <= hw * 1.001:
        rise = hw * 1.001
    d = (rise * rise - hw * hw) / w
    r = d + hw
    pts = []
    a1 = math.atan2(rise, d)
    for i in range(seg + 1):
        a = a1 * i / seg
        pts.append((-d + r * math.cos(a), r * math.sin(a)))
    left = [(-x, z) for (x, z) in reversed(pts)]
    return pts + left[1:]


def _profile_extrude_x(bm, pts_yz, w, mat_index=0):
    """Closed (y,z) profile polygon extruded along X by w, centered."""
    verts = [bm.verts.new((-w / 2, p[0], p[1])) for p in pts_yz]
    face = bm.faces.new(verts)
    res = bmesh.ops.extrude_face_region(bm, geom=[face])
    new_verts = [g for g in res['geom'] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(w, 0, 0), verts=new_verts)
    for f in bm.faces:
        f.material_index = mat_index
    return bm


# ------------------------------------------------------------- window builder
_window_cache = {}


def window_template(key, w, h, mullions=0, transom=False, frame_t=0.14,
                    frame_d=0.10, recess=0.22, sill=True):
    """Pointed-arch window: raised surround + recessed glass + mullions.
    Origin bottom-center; faces -Y. Cached mesh datablock per key."""
    if key in _window_cache:
        return _window_cache[key]
    rise = min(w * 0.85, h * 0.32)
    body_h = h - rise
    arch = arch_outline(w, rise, seg=8)

    bm = bmesh.new()

    def ring(pts, y):
        return [bm.verts.new((p[0], y, p[1])) for p in pts]

    outline = [(w / 2, 0.0), (w / 2, body_h)] + \
              [(x, z + body_h) for (x, z) in arch[1:]] + \
              [(-w / 2, 0.0)]
    sx = (w / 2 + frame_t) / (w / 2)
    sz = (h + frame_t) / h
    fr_out = [(x * sx, z * sz) for (x, z) in outline]

    glass = ring(outline, recess)
    gf = bm.faces.new(glass)
    gf.material_index = 1
    inner_f = ring(outline, -frame_d)
    outer_f = ring(fr_out, -frame_d)
    outer_w = ring(fr_out, 0.0)
    n = len(outline)
    for i in range(n - 1):
        bm.faces.new([inner_f[i], inner_f[i + 1], outer_f[i + 1], outer_f[i]])
        bm.faces.new([glass[i], glass[i + 1], inner_f[i + 1], inner_f[i]])
        bm.faces.new([outer_f[i], outer_f[i + 1], outer_w[i + 1], outer_w[i]])

    bar_w, bar_d = 0.10, recess * 0.9

    def add_box(cx, cz, sxx, szz, syy=bar_d, ty=None):
        vs = bmesh.ops.create_cube(bm, size=1.0)['verts']
        bmesh.ops.scale(bm, vec=(sxx, syy, szz), verts=vs)
        bmesh.ops.translate(bm, vec=(cx, recess - syy / 2 if ty is None else ty,
                                     cz), verts=vs)

    for mi in range(mullions):
        mx = -w / 2 + w * (mi + 1) / (mullions + 1)
        frac = 1 - abs(mx) / (w / 2 + 1e-6)
        bh = body_h + rise * frac * 0.85
        add_box(mx, bh / 2, bar_w, bh)
    if transom:
        add_box(0, body_h * 0.55, w, bar_w)
    if sill:
        add_box(0, -0.09, w + 0.4, 0.2, syy=0.6, ty=-0.18)

    # shift whole window outward so the glass pane clears solid wall geometry
    bmesh.ops.translate(bm, vec=(0, -0.26, 0), verts=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('WIN_' + key)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M['trim'])
    me.materials.append(M['glass'])
    _window_cache[key] = me
    return me


def place_window(me, cname, loc, rot_z, scale=1.0):
    ob = bpy.data.objects.new(me.name + '_i', me)
    hog.coll(cname).objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (0, 0, rot_z)
    if scale != 1.0:
        ob.scale = (scale, scale, scale)
    return ob


def windows_on_wall(me, cname, origin, direction, count, spacing, z,
                    start=0.0):
    """Row of windows along unit XY `direction`, facing right of direction."""
    dx, dy = direction
    rot = math.atan2(dy, dx)
    obs = []
    for i in range(count):
        t = start + i * spacing
        obs.append(place_window(me, cname,
                                (origin[0] + dx * t, origin[1] + dy * t, z),
                                rot))
    return obs


# --------------------------------------------------------------- wall pieces
def crenel_strip(name, cname, length, base_h=1.1, merlon_h=0.75,
                 merlon_w=1.05, gap=0.85, t=0.45, loc=(0, 0, 0), rot=0.0):
    """Parapet with merlons along local X, centered, sitting on z=0."""
    bm = bmesh.new()

    def add_box(cx, cz, sx, sz):
        vs = bmesh.ops.create_cube(bm, size=1.0)['verts']
        bmesh.ops.scale(bm, vec=(sx, t, sz), verts=vs)
        bmesh.ops.translate(bm, vec=(cx, 0, cz), verts=vs)

    add_box(0, base_h / 2, length, base_h)
    n = max(1, int((length - merlon_w) / (merlon_w + gap)))
    total = n * merlon_w + (n - 1) * gap
    x0 = -total / 2 + merlon_w / 2
    for i in range(n):
        add_box(x0 + i * (merlon_w + gap), base_h + merlon_h / 2,
                merlon_w, merlon_h)
    ob = hog.obj_from_bm(bm, name, cname, M['trim'])
    ob.location = loc
    ob.rotation_euler = (0, 0, rot)
    return ob


def buttress(name, cname, h, loc, rot=0.0, w=1.3, d0=2.0, steps=3):
    """Stepped buttress. Back face on wall plane (y=0), steps out to +Y,
    sloped weatherings. Origin at wall base; local X along wall."""
    slope = 1.0
    pts = [(0.0, 0.0), (d0, 0.0)]
    d = d0
    step_h = h / steps
    for s in range(steps):
        z_top = (s + 1) * step_h
        nd = d * 0.68 if s < steps - 1 else 0.28
        pts.append((d, z_top - slope))
        pts.append((nd, z_top))
        d = nd
    pts.append((0.0, h))
    bm = bmesh.new()
    _profile_extrude_x(bm, pts, w)
    ob = hog.obj_from_bm(bm, name, cname, M['wall'])
    ob.location = loc
    ob.rotation_euler = (0, 0, rot)
    return ob


def pinnacle(name, cname, loc, r=0.5, h=3.0):
    bm = bmesh.new()
    vs = bmesh.ops.create_cone(bm, cap_ends=True, segments=6,
                               radius1=r, radius2=r * 0.8,
                               depth=r * 1.2)['verts']
    bmesh.ops.translate(bm, vec=(0, 0, r * 0.6), verts=vs)
    vs = bmesh.ops.create_cone(bm, cap_ends=True, segments=6,
                               radius1=r * 0.95, radius2=0.02,
                               depth=h - r * 1.2)['verts']
    bmesh.ops.translate(bm, vec=(0, 0, r * 1.2 + (h - r * 1.2) / 2), verts=vs)
    ob = hog.obj_from_bm(bm, name, cname, M['trim'])
    ob.location = loc
    return ob


# --------------------------------------------------------------- tower pieces
def spun_profile(name, cname, profile, segs=24, loc=(0, 0, 0), mat=None,
                 smooth=True, close=False):
    """Lathe a (radius, z) polyline around Z at loc."""
    bm = bmesh.new()
    prof = list(profile)
    if close:
        prof = prof + [profile[0]]
    verts = [bm.verts.new((p[0], 0, p[1])) for p in prof]
    edges = [bm.edges.new((verts[i], verts[i + 1]))
             for i in range(len(verts) - 1)]
    bmesh.ops.spin(bm, geom=verts + edges, cent=(0, 0, 0), axis=(0, 0, 1),
                   angle=TAU, steps=segs, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    if smooth:
        for f in bm.faces:
            f.smooth = True
    ob = hog.obj_from_bm(bm, name, cname, mat or M['slate'])
    ob.location = loc
    return ob


def witch_hat(name, cname, r, h, loc, segs=24, mat=None, flare=1.18):
    """Bell-cast conical roof with eave flare and finial."""
    prof = [(r * flare, 0.0),
            (r * 1.02, h * 0.10),
            (r * 0.78, h * 0.32),
            (r * 0.50, h * 0.58),
            (r * 0.24, h * 0.80),
            (0.05, h * 0.985),
            (0.0, h)]
    ob = spun_profile(name, cname, prof, segs=segs, loc=loc,
                      mat=mat or M['slate'])
    bm = bmesh.new()
    vs = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.10,
                               radius2=0.02, depth=max(1.2, h * 0.14))['verts']
    bmesh.ops.translate(bm, vec=(0, 0, h + max(0.5, h * 0.05)), verts=vs)
    vs = bmesh.ops.create_icosphere(bm, subdivisions=2,
                                    radius=max(0.16, r * 0.07))['verts']
    for v in vs:
        pass
    bmesh.ops.translate(bm, vec=(0, 0, h + max(1.0, h * 0.11)), verts=vs)
    fob = hog.obj_from_bm(bm, name + '_fin', cname, M['copper'])
    fob.location = loc
    return ob


def machicolated_crown(name, cname, r, loc, segs=24, corbel_n=None,
                       parapet_h=1.8, overhang=0.55):
    """Corbel ring + overhanging crenellated parapet. loc z = body top."""
    bm = bmesh.new()
    rp = r + overhang
    corbel_n = corbel_n or max(10, int(r * 5))
    for i in range(corbel_n):
        a = TAU * i / corbel_n
        vs = bmesh.ops.create_cube(bm, size=1.0)['verts']
        bmesh.ops.scale(bm, vec=(0.42, overhang + 0.4, 0.8), verts=vs)
        bmesh.ops.translate(bm, vec=(0, r + (overhang + 0.4) / 2 - 0.4, -0.4),
                            verts=vs)
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(a, 3, 'Z'),
                         verts=vs)
    wall_top = parapet_h * 0.62
    ring_prof = [(rp - 0.5, 0.0), (rp - 0.5, wall_top), (rp, wall_top),
                 (rp, 0.0), (rp - 0.5, 0.0)]
    verts = [bm.verts.new((p[0], 0, p[1])) for p in ring_prof]
    edges = [bm.edges.new((verts[i], verts[i + 1]))
             for i in range(len(verts) - 1)]
    bmesh.ops.spin(bm, geom=verts + edges, cent=(0, 0, 0), axis=(0, 0, 1),
                   angle=TAU, steps=segs, use_merge=True)
    mn = max(8, int(rp * 2.2))
    for i in range(mn):
        a = TAU * i / mn
        vs = bmesh.ops.create_cube(bm, size=1.0)['verts']
        bmesh.ops.scale(bm, vec=(rp * TAU / mn * 0.52, 0.5,
                                 parapet_h * 0.38), verts=vs)
        bmesh.ops.translate(bm, vec=(0, rp - 0.25,
                                     wall_top + parapet_h * 0.19), verts=vs)
        bmesh.ops.rotate(bm, cent=(0, 0, 0),
                         matrix=Matrix.Rotation(a + TAU / mn / 2, 3, 'Z'),
                         verts=vs)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    ob = hog.obj_from_bm(bm, name, cname, M['trim'])
    ob.location = loc
    return ob


def string_ring(name, cname, r, loc, segs=24, t=0.28, proud=0.22):
    prof = [(r, 0), (r + proud, t * 0.35), (r + proud, t * 0.75), (r, t)]
    return spun_profile(name, cname, prof, segs=segs, loc=loc, mat=M['trim'],
                        smooth=False)


def round_tower(name, cname, x, y, zbase, r, body_h, roof_h=None, segs=24,
                taper=0.94, bands=2, roof='witch', win_me=None, win_rows=3,
                win_cols=None, win_z0=8.0, glow_cname='Windows', seed=0,
                machicolate=True, roof_mat=None, win_row_step=None):
    """Full detailed round tower. Returns dict of created objects."""
    out = {}
    r_top = r * taper
    prof = [(0.0, 0.0), (r * 1.06, 0.0), (r * 1.06, 1.2), (r, 2.2)]
    prof += [(r + (r_top - r) * t, 2.2 + (body_h - 2.2) * t)
             for t in (0.25, 0.5, 0.75, 1.0)]
    prof += [(r_top * 0.4, body_h), (0.0, body_h)]
    out['body'] = spun_profile(name, cname, prof, segs=segs,
                               loc=(x, y, zbase), mat=M['wall'])
    for b in range(bands):
        f = (0.35 + 0.5 * b / max(1, bands - 1)) if bands > 1 else 0.5
        bz = zbase + 2.2 + (body_h - 2.2) * f
        rr = r + (r_top - r) * f
        out[f'band{b}'] = string_ring(f'{name}_band{b}', cname, rr + 0.02,
                                      (x, y, bz), segs=segs)
    top = zbase + body_h
    if machicolate:
        out['crown'] = machicolated_crown(f'{name}_crown', cname, r_top,
                                          (x, y, top), segs=segs)
    if roof == 'witch' and roof_h:
        out['roof'] = witch_hat(f'{name}_roof', cname, r_top + 0.35, roof_h,
                                (x, y, top + (1.1 if machicolate else 0.0)),
                                segs=segs, mat=roof_mat)
    elif roof == 'cone' and roof_h:
        out['roof'] = spun_profile(f'{name}_roof', cname,
                                   [(r_top * 1.12, 0), (0.0, roof_h)],
                                   segs=segs, loc=(x, y, top),
                                   mat=roof_mat or M['slate'])
    if win_me is not None:
        import random as _r
        rng = _r.Random(seed)
        cols = win_cols or max(3, segs // 6)
        row_step = win_row_step or max(5.5, (body_h - win_z0 - 6) /
                                       max(1, win_rows - 1))
        for row in range(win_rows):
            wz = zbase + win_z0 + row * row_step
            if wz > top - 4:
                break
            frac = max(0.0, (wz - zbase - 2.2) / (body_h - 2.2))
            rr = r + (r_top - r) * frac
            a_off = rng.uniform(0, TAU)
            for c in range(cols):
                a = a_off + TAU * c / cols + rng.uniform(-0.05, 0.05)
                wx = x + (rr + 0.02) * math.cos(a)
                wy = y + (rr + 0.02) * math.sin(a)
                place_window(win_me, glow_cname, (wx, wy, wz), a + math.pi / 2)
    return out


# ------------------------------------------------------------- prisms/rect
def prism_xz(name, cname, pts_xz, depth, loc=(0, 0, 0), rot=0.0, mat=None):
    """Closed polygon in local (x,z) plane extruded along +Y by depth,
    centered on y=0."""
    bm = bmesh.new()
    verts = [bm.verts.new((p[0], -depth / 2, p[1])) for p in pts_xz]
    face = bm.faces.new(verts)
    res = bmesh.ops.extrude_face_region(bm, geom=[face])
    nv = [g for g in res['geom'] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, depth, 0), verts=nv)
    ob = hog.obj_from_bm(bm, name, cname, mat or M['wall'])
    ob.location = loc
    ob.rotation_euler = (0, 0, rot)
    return ob


def windows_on_rect(me, cname, center, sx, sy, rot, face, zs, count,
                    margin=2.5):
    """Windows on one face of a rotated box footprint (center, sx, sy, rot).
    face: 'S' (-y), 'N', 'E', 'W' in the box's LOCAL frame. zs: list of row z."""
    cx, cy = center
    cr, sr = math.cos(rot), math.sin(rot)

    def to_world(lx, ly):
        return (cx + lx * cr - ly * sr, cy + lx * sr + ly * cr)

    if face == 'S':
        n_local = (0, -1)
        axis_len = sx
        def lpos(t):
            return (t, -sy / 2)
    elif face == 'N':
        n_local = (0, 1)
        axis_len = sx
        def lpos(t):
            return (t, sy / 2)
    elif face == 'E':
        n_local = (1, 0)
        axis_len = sy
        def lpos(t):
            return (sx / 2, t)
    else:
        n_local = (-1, 0)
        axis_len = sy
        def lpos(t):
            return (-sx / 2, t)
    nx = n_local[0] * cr - n_local[1] * sr
    ny = n_local[0] * sr + n_local[1] * cr
    rot_z = math.atan2(nx, -ny)  # maps template -Y onto (nx, ny)
    obs = []
    span = axis_len - 2 * margin
    for z in zs:
        for i in range(count):
            t = -span / 2 + (span * i / max(1, count - 1) if count > 1 else 0)
            lx, ly = lpos(t)
            wx, wy = to_world(lx, ly)
            obs.append(place_window(me, cname,
                                    (wx + nx * 0.05, wy + ny * 0.05, z),
                                    rot_z))
    return obs


# ---------------------------------------------------------------- clock face
def clock_face(name, cname, loc, rot_z, r=2.6):
    """Round clock: pale dial object + separate ironwork object (ring,
    marks, hands). Faces -Y at rot 0 like windows."""
    dial_m = hog.flat_mat('ClockDial', (0.86, 0.80, 0.62), 0.5)
    iron_m = hog.flat_mat('IronWork', (0.02, 0.02, 0.025), 0.6)
    rotm = Matrix.Rotation(math.pi / 2, 3, 'X')

    bm = bmesh.new()
    vs = bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=r,
                               radius2=r, depth=0.12)['verts']
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rotm, verts=vs)
    dial = hog.obj_from_bm(bm, name + '_dial', cname, dial_m)
    dial.location = loc
    dial.rotation_euler = (0, 0, rot_z)

    bm = bmesh.new()
    vs = bmesh.ops.create_cone(bm, cap_ends=False, segments=24,
                               radius1=r + 0.22, radius2=r + 0.22,
                               depth=0.3)['verts']
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rotm, verts=vs)

    def bar(cx, cz, sx, sz, sy=0.1, ty=-0.11):
        vv = bmesh.ops.create_cube(bm, size=1.0)['verts']
        bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=vv)
        bmesh.ops.translate(bm, vec=(cx, ty, cz), verts=vv)
        return vv

    for hh in range(12):
        a = TAU * hh / 12
        vv = bar(0, r * 0.86, 0.09, r * 0.16)
        bmesh.ops.rotate(bm, cent=(0, 0, 0),
                         matrix=Matrix.Rotation(a, 3, 'Y'), verts=vv)
    vv = bar(0, r * 0.27, 0.14, r * 0.62)
    bmesh.ops.rotate(bm, cent=(0, 0, 0),
                     matrix=Matrix.Rotation(math.radians(-115), 3, 'Y'),
                     verts=vv)
    vv = bar(0, r * 0.38, 0.11, r * 0.85)
    bmesh.ops.rotate(bm, cent=(0, 0, 0),
                     matrix=Matrix.Rotation(math.radians(150), 3, 'Y'),
                     verts=vv)
    iron = hog.obj_from_bm(bm, name + '_iron', cname, iron_m)
    iron.location = loc
    iron.rotation_euler = (0, 0, rot_z)
    return dial


def octagonal_spire(name, cname, base_w, h, loc, mat=None, concave=0.12):
    """8-sided spire with slightly concave sides + corner pinnacle stubs."""
    r0 = base_w / 2 * 1.08
    prof = [(r0, 0.0), (r0 * (0.62 - concave), h * 0.33),
            (r0 * (0.34 - concave), h * 0.62), (r0 * 0.12, h * 0.88),
            (0.0, h)]
    ob = spun_profile(name, cname, prof, segs=8, loc=loc,
                      mat=mat or M['slate'], smooth=False)
    return ob


# ---------------------------------------------------------------- roofs
def gable_roof(name, cname, sx, sy, h, loc, rot=0.0, overhang=0.35, mat=None):
    """Roof prism only (open underside), ridge along local X, base at loc z."""
    hx, hy = sx / 2 + overhang, sy / 2 + overhang
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in
         [(-hx, -hy, 0), (hx, -hy, 0), (hx, hy, 0), (-hx, hy, 0),
          (-hx, 0, h), (hx, 0, h)]]
    bm.faces.new([v[0], v[1], v[5], v[4]])
    bm.faces.new([v[2], v[3], v[4], v[5]])
    bm.faces.new([v[1], v[2], v[5]])
    bm.faces.new([v[3], v[0], v[4]])
    ob = hog.obj_from_bm(bm, name, cname, mat or M['slate'])
    ob.location = loc
    ob.rotation_euler = (0, 0, rot)
    return ob


# ---------------------------------------------------------------- lanterns
_lantern_cache = {}


def lantern_template(key='std', post_h=2.6):
    """Lamp post: post + head cage + small emissive core."""
    if key in _lantern_cache:
        return _lantern_cache[key]
    glow = hog.flat_mat('LanternGlow', (1.0, 0.62, 0.25), 0.4, emit=18.0)
    bm = bmesh.new()
    vs = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.09,
                               radius2=0.06, depth=post_h)['verts']
    bmesh.ops.translate(bm, vec=(0, 0, post_h / 2), verts=vs)
    n_post_faces = len(bm.faces)
    vs = bmesh.ops.create_cone(bm, cap_ends=False, segments=6, radius1=0.16,
                               radius2=0.20, depth=0.42)['verts']
    bmesh.ops.translate(bm, vec=(0, 0, post_h + 0.21), verts=vs)
    n_tube_faces = len(bm.faces)
    vs = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.26,
                               radius2=0.02, depth=0.2)['verts']
    bmesh.ops.translate(bm, vec=(0, 0, post_h + 0.52), verts=vs)
    bm.faces.ensure_lookup_table()
    for i in range(n_post_faces, n_tube_faces):
        bm.faces[i].material_index = 1    # glass panes of the cage
    me_body = bpy.data.meshes.new('LANT_' + key)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me_body)
    bm.free()
    me_body.materials.append(hog.flat_mat('IronWork', (0.02, 0.02, 0.025), 0.6))
    me_body.materials.append(hog.flat_mat('LanternGlass', (0.9, 0.75, 0.5), 0.1))
    # emissive core as second mesh merged: simpler = separate tiny sphere mesh
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.15)
    me_core = bpy.data.meshes.new('LANTCORE_' + key)
    bm.to_mesh(me_core)
    bm.free()
    me_core.materials.append(glow)
    _lantern_cache[key] = (me_body, me_core, post_h)
    return _lantern_cache[key]


def place_lantern(cname, loc, key='std'):
    me_body, me_core, post_h = lantern_template(key)
    ob = bpy.data.objects.new('Lantern', me_body)
    hog.coll(cname).objects.link(ob)
    ob.location = loc
    core = bpy.data.objects.new('LanternCore', me_core)
    hog.coll(cname).objects.link(core)
    core.location = (loc[0], loc[1], loc[2] + post_h + 0.21)
    return ob
