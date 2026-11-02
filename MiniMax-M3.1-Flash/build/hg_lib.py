"""Hogwarts — procedural geometry library.

Everything is built from primitives/bmesh; no external assets.
Units are metres, Z up, water plane at z = 0.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler
from mathutils.geometry import tessellate_polygon

TAU = math.pi * 2.0
RAD = math.radians


# ----------------------------------------------------------------------------
# scene / collection helpers
# ----------------------------------------------------------------------------
def purge_all():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for blocks in (bpy.data.meshes, bpy.data.materials, bpy.data.lights,
                   bpy.data.cameras, bpy.data.curves, bpy.data.node_groups,
                   bpy.data.textures, bpy.data.fonts):
        for b in list(blocks):
            try:
                if b.users == 0:
                    blocks.remove(b)
            except Exception:
                pass


def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        p = parent if parent is not None else bpy.context.scene.collection
        p.children.link(c)
    return c


def move_to(obj, c):
    for uc in list(obj.users_collection):
        uc.objects.unlink(obj)
    c.objects.link(obj)
    return obj


def M(loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    return Matrix.LocRotScale(Vector(loc), Euler(rot, 'XYZ'), Vector(scale))


def activate(obj):
    vl = bpy.context.view_layer
    try:
        bpy.ops.object.select_all(action='DESELECT')
    except Exception:
        pass
    obj.select_set(True)
    vl.objects.active = obj


def apply_mod(obj, mod):
    activate(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)


def join_objs(objs, name=None):
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
    if len(objs) == 1:
        if name:
            objs[0].name = name
        return objs[0]
    activate(objs[0])
    for o in objs[1:]:
        o.select_set(True)
    bpy.ops.object.join()
    res = objs[0]
    if name:
        res.name = name
        res.data.name = name
    return res


def recalc_normals(obj):
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return obj


def place_cam(name, c, target, dist, azim, z, lens=50.0, shift_y=0.0, roll=0.0):
    """Place a camera aimed at `target`.

    azim: degrees east of due south (0 = looking north, 90 = looking west).
    z: absolute camera height.
    """
    a = math.radians(azim)
    loc = Vector((target[0] + dist * math.sin(a),
                  target[1] - dist * math.cos(a),
                  z))
    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = lens
    cam_data.shift_y = shift_y
    # A newly created camera inherits Blender's default clip_end of 1000 m.
    # Every mountain range in this scene sits 3-8 km out, so with the default
    # range they were silently clipped out of every render -- the backdrop
    # simply did not exist on screen.
    cam_data.clip_start = 0.1
    cam_data.clip_end = 30000.0
    cam = bpy.data.objects.new(name, cam_data)
    c.objects.link(cam)
    cam.location = loc
    d = Vector(target) - loc
    q = d.to_track_quat('-Z', 'Y')
    cam.rotation_euler = q.to_euler()
    if roll:
        cam.rotation_euler.rotate_axis('Z', roll)
    bpy.context.scene.camera = cam
    return cam


def smooth(obj, angle=35.0):
    activate(obj)
    try:
        bpy.ops.object.shade_auto_smooth(angle=RAD(angle))
    except Exception:
        try:
            bpy.ops.object.shade_smooth_by_angle(angle=RAD(angle))
        except Exception:
            bpy.ops.object.shade_smooth()
    return obj


def bevel(obj, width=0.04, segments=2, angle=50.0, apply=True):
    m = obj.modifiers.new("Bevel", 'BEVEL')
    m.width = width
    m.segments = segments
    m.limit_method = 'ANGLE'
    m.angle_limit = RAD(angle)
    m.harden_normals = False
    if apply:
        try:
            apply_mod(obj, m)
        except Exception:
            obj.modifiers.remove(m)
    return obj


# ----------------------------------------------------------------------------
# mesh builder — accumulates verts/faces/material slots
# ----------------------------------------------------------------------------
# name -> number of malformed faces that had to be dropped
BAD_FACES = {}


class MB:
    def __init__(self):
        self.verts = []
        self.faces = []
        self.mats = []

    def add(self, verts, faces, mat=0, matrix=None):
        base = len(self.verts)
        if matrix is not None:
            verts = [tuple(matrix @ Vector(v)) for v in verts]
        self.verts.extend([tuple(v) for v in verts])
        for f in faces:
            self.faces.append(tuple(i + base for i in f))
            self.mats.append(mat)
        return self

    def add_poly(self, pts, mat=0, matrix=None):
        """single flat polygon"""
        n = len(pts)
        base = len(self.verts)
        if matrix is not None:
            pts = [tuple(matrix @ Vector(p)) for p in pts]
        self.verts.extend(pts)
        self.faces.append(tuple(range(base, base + n)))
        self.mats.append(mat)
        return self

    def to_object(self, name, c, materials=None, fix_normals=True):
        me = bpy.data.meshes.new(name)
        # Sanitise the face list BEFORE handing it to Blender.  A face with a
        # repeated vertex index or an out-of-range index makes from_pydata
        # build an inconsistent loop array, and the next bm.from_mesh() then
        # segfaults Blender -- the whole application dies, not just the build.
        nv = len(self.verts)
        faces = []
        mats = []
        dropped = 0
        for i, f in enumerate(self.faces):
            if len(f) < 3 or len(set(f)) != len(f) or min(f) < 0 or max(f) >= nv:
                dropped += 1
                continue
            faces.append(tuple(int(x) for x in f))
            mats.append(self.mats[i] if i < len(self.mats) else 0)
        if dropped:
            BAD_FACES.setdefault(name, 0)
            BAD_FACES[name] += dropped
        me.from_pydata(self.verts, [], faces)
        if materials:
            for m in materials:
                me.materials.append(m)
        for i, p in enumerate(me.polygons):
            if i < len(mats):
                p.material_index = mats[i]
        me.validate(verbose=False, clean_customdata=False)
        c.objects.link(obj := bpy.data.objects.new(name, me))
        if fix_normals:
            recalc_normals(obj)
        return obj


# ----------------------------------------------------------------------------
# primitives (return verts, faces)
# ----------------------------------------------------------------------------
def p_box(sx, sy, sz, center=(0, 0, 0)):
    hx, hy, hz = sx * .5, sy * .5, sz * .5
    cx, cy, cz = center
    v = [(cx - hx, cy - hy, cz - hz), (cx + hx, cy - hy, cz - hz),
         (cx + hx, cy + hy, cz - hz), (cx - hx, cy + hy, cz - hz),
         (cx - hx, cy - hy, cz + hz), (cx + hx, cy - hy, cz + hz),
         (cx + hx, cy + hy, cz + hz), (cx - hx, cy + hy, cz + hz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
         (2, 3, 7, 6), (3, 0, 4, 7)]
    return v, f


def p_box_minmax(x0, y0, z0, x1, y1, z1):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
         (2, 3, 7, 6), (3, 0, 4, 7)]
    return v, f


def p_cyl(r, h, n=24, r2=None, cap=True, z0=0.0, a0=0.0):
    r2 = r if r2 is None else r2
    v = []
    for i in range(n):
        a = a0 + TAU * i / n
        v.append((r * math.cos(a), r * math.sin(a), z0))
    for i in range(n):
        a = a0 + TAU * i / n
        v.append((r2 * math.cos(a), r2 * math.sin(a), z0 + h))
    f = []
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, n + j, n + i))
    if cap:
        f.append(tuple(range(n - 1, -1, -1)))
        f.append(tuple(range(n, 2 * n)))
    return v, f


def p_cone(r, h, n=24, z0=0.0, cap=True, a0=0.0):
    v = []
    for i in range(n):
        a = a0 + TAU * i / n
        v.append((r * math.cos(a), r * math.sin(a), z0))
    apex = len(v)
    v.append((0.0, 0.0, z0 + h))
    f = []
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, apex))
    if cap:
        f.append(tuple(range(n - 1, -1, -1)))
    return v, f


def p_sphere(r, nseg=16, nring=10, z0=0.0):
    v = []
    for ri in range(nring + 1):
        phi = math.pi * ri / nring
        rr = r * math.sin(phi)
        zz = z0 + r * math.cos(phi)
        for i in range(nseg):
            a = TAU * i / nseg
            v.append((rr * math.cos(a), rr * math.sin(a), zz))
    f = []
    for ri in range(nring):
        for i in range(nseg):
            j = (i + 1) % nseg
            a0 = ri * nseg + i
            a1 = ri * nseg + j
            b0 = (ri + 1) * nseg + i
            b1 = (ri + 1) * nseg + j
            f.append((a0, b0, b1, a1))
    return v, f


def _tess(profile):
    vecs = [Vector((p[0], p[1])) for p in profile]
    key = lambda v: (round(v.x, 6), round(v.y, 6))
    lut = {}
    for i, v in enumerate(vecs):
        lut.setdefault(key(v), i)
    tris = tessellate_polygon([vecs])
    out = []
    for t in tris:
        try:
            if isinstance(t[0], int):
                out.append((t[0], t[1], t[2]))
            else:
                out.append((lut[key(t[0])], lut[key(t[1])], lut[key(t[2])]))
        except KeyError:
            pass
    return out


def p_prism(profile, y0, y1, cap=True):
    """profile: [(x,z), ...] polygon in XZ. Extruded along Y from y0 to y1."""
    n = len(profile)
    v = [(p[0], y0, p[1]) for p in profile] + [(p[0], y1, p[1]) for p in profile]
    f = []
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, n + j, n + i))
    if cap:
        tris = _tess(profile)
        for a, b, c in tris:
            f.append((c, b, a))
            f.append((n + a, n + b, n + c))
    return v, f


def p_strip(lower, upper, y0, y1):
    """Solid between two equal-length polylines in the XZ plane, extruded
    along Y from y0 to y1.

    Only quads are produced -- no triangulation -- so the profile may be
    arbitrarily concave (arch heads, voussoir bands).  The result is a
    closed, manifold solid, which makes it a safe replacement for a boolean
    cut: coplanar cutter faces cannot wreck it.
    """
    n = len(lower)
    if n != len(upper) or n < 2:
        raise ValueError("p_strip needs two equal-length polylines of >= 2 pts")
    v = []
    # The vertex layout MUST be the interleaved one the face indices below
    # assume: 4i = lower@y0, 4i+1 = upper@y0, 4i+2 = lower@y1, 4i+3 =
    # upper@y1.  Building the four blocks separately (all the lower@y0
    # points, then all the upper@y0 points, ...) left every face pointing at
    # the wrong vertices: the strip came out with half its faces on the far
    # plane, the rest degenerate, and the viaduct spandrel rendered as a
    # black slab with inverted normals.
    for i in range(n):
        v.append((lower[i][0], y0, lower[i][1]))
        v.append((upper[i][0], y0, upper[i][1]))
        v.append((lower[i][0], y1, lower[i][1]))
        v.append((upper[i][0], y1, upper[i][1]))
    f = []
    for i in range(n - 1):
        a0, b0 = 4 * i, 4 * i + 1
        a1, b1 = 4 * i + 2, 4 * i + 3
        c0, d0 = 4 * (i + 1), 4 * (i + 1) + 1
        c1, d1 = 4 * (i + 1) + 2, 4 * (i + 1) + 3
        f.append((a0, c0, d0, b0))      # front skin (y0)
        f.append((a1, b1, d1, c1))      # back skin (y1)
        f.append((a0, a1, c1, c0))      # lower skin
        f.append((b0, d0, d1, b1))      # upper skin
    f.append((0, 1, 3, 2))              # start cap
    e = 4 * (n - 1)
    f.append((e, e + 2, e + 3, e + 1))  # end cap
    return v, f


def p_band(outer, inner, y0, y1):
    """closed ring band between two matching-length closed paths."""
    n = len(outer)
    assert len(inner) == n
    v = ([(p[0], y0, p[1]) for p in outer] + [(p[0], y0, p[1]) for p in inner] +
         [(p[0], y1, p[1]) for p in outer] + [(p[0], y1, p[1]) for p in inner])
    O0, I0, O1, I1 = 0, n, 2 * n, 3 * n
    f = []
    for i in range(n):
        j = (i + 1) % n
        f.append((O0 + i, O0 + j, I0 + j, I0 + i))
        f.append((O1 + j, O1 + i, I1 + i, I1 + j))
        f.append((O0 + j, O0 + i, O1 + i, O1 + j))
        f.append((I0 + i, I0 + j, I1 + j, I1 + i))
    return v, f


# ----------------------------------------------------------------------------
# gothic profiles
# ----------------------------------------------------------------------------
def lancet_points(w, z_spring, rise, segs=12):
    """Two-centred (pointed) arch sampled left-springing -> apex -> right-springing."""
    a = w * .5
    if a <= 1e-6:
        return [(0.0, z_spring + rise)]
    cx = (rise * rise - a * a) / (2 * a)
    R = a + cx
    ang = math.atan2(rise, cx)
    right = []
    for i in range(segs + 1):
        t = ang * i / segs
        right.append((-cx + R * math.cos(t), z_spring + R * math.sin(t)))
    left = [(-x, z) for (x, z) in right]
    return left + right[-2::-1]


def round_points(r, z_c, segs=16, a0=-math.pi * .5):
    return [(r * math.cos(a0 + math.pi * i / segs),
             z_c + r * math.sin(a0 + math.pi * i / segs)) for i in range(segs + 1)]


def circle_points(r, z_c, segs=24):
    """CLOSED full-circle path (no duplicated seam vertex).

    `round_points` only sweeps a half turn (-90 deg -> +90 deg), so using it
    for a rose window produced a half-disc with a flat vertical edge and the
    great window rendered as a D-shape.  A ring band also needs a genuinely
    closed loop, otherwise `p_band` closes it with a degenerate zero-area quad.
    """
    return [(r * math.cos(2.0 * math.pi * i / segs),
             z_c + r * math.sin(2.0 * math.pi * i / segs)) for i in range(segs)]


def opening_center(kind, w, sill, h):
    """Pivot that the opening outline is inset about (glass, tracery)."""
    if kind == 'rose':
        return (0.0, sill + h * 0.5)
    if kind == 'round':
        return (0.0, sill + h - w * 0.5)
    return (0.0, sill)


def opening_profile(kind, w, sill, h, segs=12):
    """Closed polygon (x,z) of a window opening.

    kind: 'lancet' | 'round' | 'rect' | 'ogive' | 'rose'
    h: total opening height measured from sill.
    """
    a = w * .5
    if kind == 'rose':
        # a rose window is a full circle inscribed in the opening box
        r = min(w, h) * .5
        return circle_points(r, sill + h * .5, segs=24)
    if kind == 'round':
        # a round-arched opening: straight jambs up to the spring line, then
        # a semicircular head of radius w/2.  The old version returned the
        # semicircle alone, which made every 'round' window a D-shaped
        # half-disc with a flat vertical edge.
        r = w * .5
        spring = max(sill, sill + h - r)
        arc = round_points(r, spring, segs=16, a0=0.0)
        return [(-a, sill), (a, sill)] + arc
    if kind == 'rect':
        return [(-a, sill), (a, sill), (a, sill + h), (-a, sill + h)]
    if kind == 'ogive':
        # two-centred arch whose head is more sharply pointed
        spring = sill + h * .55
        rise = h - (spring - sill)
        arch = lancet_points(w, spring, rise, segs)
        return [(-a, sill), (a, sill)] + list(reversed(arch))
    # lancet: rectangular body, pointed head
    spring = sill + h * .62
    rise = h - (spring - sill)
    arch = lancet_points(w, spring, rise, segs)
    return [(-a, sill), (a, sill)] + list(reversed(arch))


def opening_path(kind, w, sill, h, segs=12, expand=0.0):
    """Open path (not closed) of the opening outline, expanded outward by `expand`."""
    a = w * .5 + expand
    if kind == 'rose':
        r = min(w, h) * .5 + expand
        return circle_points(r, sill + h * .5, segs=24)
    if kind == 'round':
        r = w * .5 + expand
        spring = max(sill, sill + h - w * .5)
        arc = round_points(r, spring, segs=16, a0=0.0)
        return [(-a, sill), (a, sill)] + arc
    if kind == 'rect':
        return [(-a, sill), (a, sill), (a, sill + h + expand), (-a, sill + h + expand)]
    spring = sill + (h * .62)
    rise = (h) - (spring - sill)
    if expand:
        spring_o = spring - expand * .5
        rise_o = rise + expand * .8
        arch = lancet_points(w + 2 * expand, spring_o, rise_o, segs)
    else:
        arch = lancet_points(w, spring, rise, segs)
    return [(-a, sill)] + list(arch) + [(a, sill)]


def arch_band_points(kind, w, sill, h, segs=12, expand=0.0):
    """Two matching-length paths for a moulding band around an opening."""
    inner = opening_path(kind, w, sill, h, segs)
    outer = opening_path(kind, w, sill, h, segs, expand)
    if len(inner) != len(outer):
        n = min(len(inner), len(outer))
        inner, outer = inner[:n], outer[:n]
    return outer, inner


# ----------------------------------------------------------------------------
# boolean helper
# ----------------------------------------------------------------------------
def boolean_cut(target, cutter_obj, remove_cutter=True):
    m = target.modifiers.new("Cut", 'BOOLEAN')
    m.operation = 'DIFFERENCE'
    m.object = cutter_obj
    m.solver = 'EXACT'
    try:
        apply_mod(target, m)
    except Exception:
        target.modifiers.remove(m)
        raise
    if remove_cutter:
        bpy.data.objects.remove(cutter_obj, do_unlink=True)
    return target


def boolean_union(target, other_obj, remove_other=True):
    m = target.modifiers.new("Union", 'BOOLEAN')
    m.operation = 'UNION'
    m.object = other_obj
    m.solver = 'EXACT'
    try:
        apply_mod(target, m)
    except Exception:
        target.modifiers.remove(m)
        raise
    if remove_other:
        bpy.data.objects.remove(other_obj, do_unlink=True)
    return target


# ----------------------------------------------------------------------------
# misc maths
# ----------------------------------------------------------------------------
def clamp(x, a=0.0, b=1.0):
    return a if x < a else (b if x > b else x)


def smoothstep(a, b, x):
    if a == b:
        return 0.0 if x < a else 1.0
    t = clamp((x - a) / (b - a))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def dist_point_seg(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    wx, wy = px - ax, py - ay
    L2 = vx * vx + vy * vy
    t = 0.0 if L2 < 1e-9 else clamp((wx * vx + wy * vy) / L2)
    cx, cy = ax + t * vx, ay + t * vy
    return math.hypot(px - cx, py - cy)


def polyline_dist(px, py, pts):
    d = 1e9
    for i in range(len(pts) - 1):
        d = min(d, dist_point_seg(px, py, pts[i][0], pts[i][1],
                                  pts[i + 1][0], pts[i + 1][1]))
    return d


from mathutils import noise as _mnoise


def value_noise2(x, y, seed=0):
    """deterministic smooth 2D value noise in [-1,1]"""
    return _mnoise.noise(Vector((x, y, seed)))


def fbm(x, y, oct=4, lac=2.03, gain=0.5, seed=0.0):
    a, f, s = 1.0, 1.0, 0.0
    norm = 0.0
    for i in range(oct):
        s += a * _mnoise.noise(Vector((x * f, y * f, seed + i * 13.7)))
        norm += a
        a *= gain
        f *= lac
    return s / norm


def ridged(x, y, oct=4, seed=0.0):
    a, f, s = 1.0, 1.0, 0.0
    norm = 0.0
    for i in range(oct):
        s += a * (1.0 - abs(_mnoise.noise(Vector((x * f, y * f, seed + i * 7.3)))))
        norm += a
        a *= 0.5
        f *= 2.07
    return s / norm


# ----------------------------------------------------------------------------
# grid mesh
# ----------------------------------------------------------------------------
def make_grid(name, c, x0, x1, y0, y1, nx, ny, hfn, materials=None, mat_index=0):
    """hfn(x, y) -> (z, [attr0, attr1, ...]) ; attributes written to a color attr."""
    mb = MB()
    attrs = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = lerp(x0, x1, i / nx)
            y = lerp(y0, y1, j / ny)
            z, a = hfn(x, y)
            mb.verts.append((x, y, z))
            attrs.append(a)
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            b = a + 1
            cidx = a + (nx + 1)
            d = cidx + 1
            mb.faces.append((a, b, d, cidx))
            mb.mats.append(mat_index)
    obj = mb.to_object(name, c, materials, fix_normals=False)
    return obj, attrs


def write_color_attr(obj, name, attrs, channels=3):
    """attrs: list (or ndarray) of per-vertex tuples (same order as mesh verts)"""
    import numpy as np
    me = obj.data
    if name in me.color_attributes:
        me.color_attributes.remove(me.color_attributes[name])
    at = me.color_attributes.new(name=name, type='FLOAT_COLOR', domain='POINT')
    a = np.asarray(attrs, dtype=np.float64)
    if a.ndim == 1:
        a = a.reshape((-1, channels))
    n = len(me.vertices)
    if len(a) < n:
        a = np.vstack([a, np.zeros((n - len(a), a.shape[1]))])
    a = a[:n]
    flat = np.ones((n, 4), dtype=np.float32)
    k = min(a.shape[1], 3)
    flat[:, :k] = a[:, :k]
    at.data.foreach_set("color", flat.ravel())
    return at
