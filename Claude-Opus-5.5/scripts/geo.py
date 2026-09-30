"""Procedural mesh toolkit: accumulate faces in Python, emit one mesh per builder.

Every face carries a material slot plus two float attributes:
  glow  - emissive strength for window panes (0 = dark)
  rnd   - per-element random value (stone batch / tile variation)
UVs are generated in metres: u runs horizontally along the face, v up the face.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

TAU = math.tau


def mat_loc(loc=(0, 0, 0), rz=0.0, s=1.0):
    m = Matrix.Translation(Vector(loc)) @ Matrix.Rotation(rz, 4, 'Z')
    if s != 1.0:
        m = m @ Matrix.Scale(s, 4)
    return m


def get_coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def clear_coll(name):
    c = bpy.data.collections.get(name)
    if not c:
        return
    for ch in list(c.children):
        clear_coll(ch.name)
        bpy.data.collections.remove(ch)
    for o in list(c.objects):
        d = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if d is not None and d.users == 0:
            if isinstance(d, bpy.types.Mesh):
                bpy.data.meshes.remove(d)
            elif isinstance(d, bpy.types.Light):
                bpy.data.lights.remove(d)
            elif isinstance(d, bpy.types.Camera):
                bpy.data.cameras.remove(d)
            elif isinstance(d, bpy.types.Curve):
                bpy.data.curves.remove(d)


class MB:
    def __init__(self, name):
        self.name = name
        self.v = []
        self.f = []
        self.fm = []
        self.fg = []
        self.fr = []
        self.mats = []
        self.glow = 0.0
        self.rnd = 0.5
        self.zoff = 0.0

    # ---------------- core ----------------
    def mi(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def add(self, verts, faces, mat, M=None, glow=None, rnd=None):
        """verts: local coords; faces: index tuples; mat: str or list per face."""
        base = len(self.v)
        zo = self.zoff
        if M is None:
            self.v.extend((p[0], p[1], p[2] + zo) for p in verts)
        else:
            for p in verts:
                q = M @ Vector(p)
                self.v.append((q.x, q.y, q.z + zo))
        g = self.glow if glow is None else glow
        r = self.rnd if rnd is None else rnd
        for i, fc in enumerate(faces):
            self.f.append(tuple(base + j for j in fc))
            m = mat[i] if isinstance(mat, (list, tuple)) else mat
            self.fm.append(self.mi(m))
            self.fg.append(g[i] if isinstance(g, (list, tuple)) else g)
            self.fr.append(r)
        return base

    # ---------------- primitives ----------------
    def loft(self, rings, mat, M=None, cap_bot=True, cap_top=True, closed=True):
        """rings: list of point lists (same length, CCW seen from above) bottom->top.
        A ring of length 1 is an apex."""
        verts = []
        idx = []
        for r in rings:
            idx.append(list(range(len(verts), len(verts) + len(r))))
            verts.extend(r)
        faces = []
        for a, b in zip(idx[:-1], idx[1:]):
            n = max(len(a), len(b))
            segs = n if closed else n - 1
            for i in range(segs):
                j = (i + 1) % n
                if len(a) == 1:
                    faces.append((a[0], b[j], b[i]))
                elif len(b) == 1:
                    faces.append((a[i], a[j], b[0]))
                else:
                    faces.append((a[i], a[j], b[j], b[i]))
        if closed and cap_bot and len(idx[0]) > 2:
            faces.append(tuple(reversed(idx[0])))
        if closed and cap_top and len(idx[-1]) > 2:
            faces.append(tuple(idx[-1]))
        return self.add(verts, faces, mat, M)

    def lathe(self, prof, n, mat, M=None, phase=0.0, cap_bot=True, cap_top=True):
        rings = []
        for r, z in prof:
            if r < 1e-6:
                rings.append([(0.0, 0.0, z)])
            else:
                rings.append([(r * math.cos(phase + TAU * i / n), r * math.sin(phase + TAU * i / n), z)
                              for i in range(n)])
        return self.loft(rings, mat, M, cap_bot, cap_top)

    def prism(self, poly, z0, z1, mat, M=None, cap_bot=True, cap_top=True):
        return self.loft([[(x, y, z0) for x, y in poly], [(x, y, z1) for x, y in poly]], mat, M, cap_bot, cap_top)

    def box(self, x0, y0, z0, x1, y1, z1, mat, M=None):
        return self.prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1, mat, M)

    def boxc(self, c, s, mat, M=None, rz=0.0):
        """centered box; c centre (bottom-centre z), s full size."""
        m = mat_loc(c, rz)
        if M is not None:
            m = M @ m
        hx, hy = s[0] / 2, s[1] / 2
        return self.box(-hx, -hy, 0, hx, hy, s[2], mat, m)

    def seg_box(self, p0, p1, z0, z1, thick, mat, off=0.0):
        """wall slab along the 2D segment p0->p1, 'off' shifts it along the left normal."""
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy)
        if L < 1e-6:
            return
        a = math.atan2(dy, dx)
        cx, cy = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        nx, ny = -dy / L, dx / L
        m = mat_loc((cx + nx * off, cy + ny * off, 0), a)
        self.box(-L / 2, -thick / 2, z0, L / 2, thick / 2, z1, mat, m)

    # ---------------- emit ----------------
    def build(self, coll, smooth_angle=None, obname=None):
        if not self.f:
            return None
        name = obname or self.name
        old = bpy.data.objects.get(name)
        if old:
            d = old.data
            bpy.data.objects.remove(old, do_unlink=True)
            if d and d.users == 0:
                bpy.data.meshes.remove(d)
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        for m in self.mats:
            mat = bpy.data.materials.get(m)
            if mat is None:
                mat = bpy.data.materials.new(m)
            me.materials.append(mat)
        me.polygons.foreach_set('material_index', self.fm)
        ag = me.attributes.new('glow', 'FLOAT', 'FACE')
        ag.data.foreach_set('value', self.fg)
        ar = me.attributes.new('rnd', 'FLOAT', 'FACE')
        ar.data.foreach_set('value', self.fr)
        # metre-scaled planar UVs per face
        uvl = me.uv_layers.new(name='UVMap')
        co = self.v
        uvs = [0.0] * (2 * len(me.loops))
        li = 0
        for fc in self.f:
            n = Vector((0, 0, 0))
            k = len(fc)
            for i in range(k):
                a = co[fc[i]]
                b = co[fc[(i + 1) % k]]
                n.x += (a[1] - b[1]) * (a[2] + b[2])
                n.y += (a[2] - b[2]) * (a[0] + b[0])
                n.z += (a[0] - b[0]) * (a[1] + b[1])
            if n.length > 1e-12:
                n.normalize()
            if abs(n.z) > 0.97:
                tx, ty, tz = 1.0, 0.0, 0.0
                bx, by, bz = 0.0, 1.0, 0.0
            else:
                t = Vector((-n.y, n.x, 0.0)).normalized()
                b = n.cross(t)
                tx, ty, tz = t
                bx, by, bz = b
            for vi in fc:
                p = co[vi]
                uvs[li * 2] = p[0] * tx + p[1] * ty + p[2] * tz
                uvs[li * 2 + 1] = p[0] * bx + p[1] * by + p[2] * bz
                li += 1
        uvl.data.foreach_set('uv', uvs)
        me.validate(clean_customdata=False)
        if smooth_angle is not None:
            bm = bmesh.new()
            bm.from_mesh(me)
            for f in bm.faces:
                f.smooth = True
            thr = math.radians(smooth_angle)
            for e in bm.edges:
                if len(e.link_faces) != 2 or e.calc_face_angle(0) > thr:
                    e.smooth = False
            bm.to_mesh(me)
            bm.free()
        me.update()
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        return ob


# ---------------- shape helpers ----------------

def pointed_arch(w, h, seg=6, sharp=1.0):
    """Outline (x,z) of a pointed-arch opening, width w, total height h.
    Order: bottom-left, bottom-right, up the right side, apex, down the left side
    (CCW when viewed from -y)."""
    rad = w * sharp
    c = rad - w / 2            # right-side arc centre sits at x = -c
    ah = math.sqrt(max(rad * rad - c * c, 0.0))
    s = max(h - ah, 0.0)
    a1 = math.atan2(ah, c)
    right = [(-c + rad * math.cos(a1 * i / seg), s + rad * math.sin(a1 * i / seg)) for i in range(seg + 1)]
    right[-1] = (0.0, s + ah)
    left = [(-x, z) for x, z in reversed(right[:-1])]
    pts = [(-w / 2, 0.0), (w / 2, 0.0)] + right + left
    res = []
    for p in pts:
        if not res or abs(res[-1][0] - p[0]) + abs(res[-1][1] - p[1]) > 1e-5:
            res.append(p)
    if abs(res[-1][0] - res[0][0]) + abs(res[-1][1] - res[0][1]) < 1e-5:
        res.pop()
    return res


def round_arch(w, h, seg=8):
    r = w / 2
    s = h - r
    pts = [(-w / 2, 0.0), (w / 2, 0.0)]
    for i in range(seg + 1):
        a = math.pi * i / seg
        pts.append((r * math.cos(a), s + r * math.sin(a)))
    return pts


def rect_outline(w, h):
    return [(-w / 2, 0.0), (w / 2, 0.0), (w / 2, h), (-w / 2, h)]


def offset_outline(pts, d):
    """offset a convex CCW outline (x,z) outward by d (approximate miter)."""
    n = len(pts)
    out = []
    for i in range(n):
        p0 = Vector(pts[i - 1])
        p1 = Vector(pts[i])
        p2 = Vector(pts[(i + 1) % n])
        e0 = (p1 - p0).normalized()
        e1 = (p2 - p1).normalized()
        n0 = Vector((e0.y, -e0.x))
        n1 = Vector((e1.y, -e1.x))
        m = (n0 + n1)
        if m.length < 1e-6:
            m = n0
        m.normalize()
        cosh = max(m.dot(n0), 0.35)
        q = p1 + m * (d / cosh)
        out.append((q.x, q.y))
    return out


def smoothstep(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t
