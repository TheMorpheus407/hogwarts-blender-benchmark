"""Hogwarts — castle architecture: gothic walls, windows, towers, roofs, buttresses."""
import bpy, bmesh, math
from mathutils import Vector, Matrix
import hg_lib as L
import hg_cfg as C

RECESS = 0.32          # window reveal depth
BAND_PROJ = 0.10       # stone surround projection


# =============================================================== window system
def spring_z(kind, h):
    if kind == 'round':
        return h * 0.5
    if kind == 'rect':
        return h
    return h * 0.62


def _bar(mb, p0, p1, w, y0, y1, mat):
    x0, z0 = p0
    x1, z1 = p1
    dx, dz = x1 - x0, z1 - z0
    ln = math.hypot(dx, dz)
    if ln < 1e-6:
        return
    ux, uz = dx / ln, dz / ln
    px, pz = -uz * w * .5, ux * w * .5
    prof = [(x0 + px, z0 + pz), (x1 + px, z1 + pz), (x1 - px, z1 - pz), (x0 - px, z0 - pz)]
    v, f = L.p_prism(prof, y0, y1)
    mb.add(v, f, mat)


def _ring(mb, r_in, r_out, z_c, y0, y1, mat, segs=32):
    """A closed lead ring (annulus) lying in the window plane."""
    outer = L.circle_points(r_out, z_c, segs)
    inner = L.circle_points(r_in, z_c, segs)
    v, f = L.p_band(outer, inner, y0, y1)
    mb.add(v, f, mat)


def _petal(mb, a, r0, r1, wmax, z_c, y0, y1, mat):
    """A pointed lens (spindle) lying along the radius at angle `a`."""
    pts = []
    n = 9
    ca, sa = math.cos(a), math.sin(a)
    for side in (-1, 1):
        rng = range(n + 1) if side == -1 else range(n, -1, -1)
        for i in rng:
            t = i / float(n)
            r = r0 + (r1 - r0) * t
            w = wmax * (math.sin(math.pi * t) ** 0.75)
            pts.append((ca * r - side * sa * w, z_c + sa * r + side * ca * w))
    v, f = L.p_prism(pts, y0, y1)
    mb.add(v, f, mat)


def _window_mesh(kind, w, h, style):
    """Returns (verts, faces, matidx) for one window unit.

    local frame: x across, z up from sill, y = 0 at the outer wall face,
    negative y goes into the wall.  materials: 0 glass, 1 lead, 2 stone
    """
    mb = L.MB()
    prof = L.opening_profile(kind, w, 0.0, h)
    cx, cz = L.opening_center(kind, w, 0.0, h)
    # --- glass ---
    # the inset is taken about the opening's own centre, otherwise a rose
    # window shrinks towards the sill instead of towards its own axis
    gp = [(cx + (x - cx) * 0.99, cz + (z - cz) * 0.995) for (x, z) in prof]
    v, f = L.p_prism(gp, -RECESS + 0.035, -RECESS + 0.008)
    mb.add(v, f, 0)
    # --- tracery ---
    ty0, ty1 = -RECESS + 0.075, -RECESS + 0.040
    # p_band wants its two ends the other way round from p_prism -- its
    # outward-facing skin is the y1 end -- so the ring bands use (ty1, ty0)
    by0, by1 = ty1, ty0
    if style == 'rose':
        r = min(w, h) * 0.5
        zc = h * 0.5
        # three concentric lead rings: outer band, middle ring, central oculus
        _ring(mb, r * 0.945, r * 0.995, zc, by0, by1, 1, segs=40)
        _ring(mb, r * 0.400, r * 0.470, zc, by0, by1, 1, segs=32)
        _ring(mb, r * 0.150, r * 0.215, zc, by0, by1, 1, segs=24)
        # eight principal spokes with a petal between each pair
        for i in range(8):
            a = math.pi * 2 * i / 8 + math.pi / 8
            _bar(mb, (0.0, zc), (math.cos(a) * r * 0.95, zc + math.sin(a) * r * 0.95),
                 0.075, ty0, ty1, 1)
            b = math.pi * 2 * (i + 0.5) / 8
            _petal(mb, b, r * 0.24, r * 0.90, r * 0.115, zc, ty0, ty1, 1)
    elif style == 'lancet':
        sz = spring_z(kind, h)
        for sx in (-w / 6.0, w / 6.0):
            _bar(mb, (sx, 0.02), (sx, sz), 0.075, ty0, ty1, 1)
        _bar(mb, (-w * .45, sz * 0.52), (w * .45, sz * 0.52), 0.075, ty0, ty1, 1)
        apex = h * 0.94
        _bar(mb, (0.0, sz), (0.0, apex), 0.075, ty0, ty1, 1)
        for sx in (-w / 6.0, w / 6.0):
            _bar(mb, (sx, sz), (0.0, apex * 0.98), 0.065, ty0, ty1, 1)
    elif style == 'single':
        sz = spring_z(kind, h)
        _bar(mb, (0.0, 0.02), (0.0, sz), 0.075, ty0, ty1, 1)
        _bar(mb, (-w * .42, sz * 0.55), (w * .42, sz * 0.55), 0.07, ty0, ty1, 1)
    elif style == 'greatdoor':
        # The boat house door is six metres wide and nine tall.  The slim
        # tracery of an ordinary lancet disappears at that size -- a 15 cm
        # bar is one pixel across in the close-up -- so the opening gets
        # heavy glazing bars: three mullions, two transoms and a traceried
        # head, which reads as a real leaded door instead of a slab of light.
        sz = spring_z(kind, h)
        for sx in (-w * 0.25, 0.0, w * 0.25):
            _bar(mb, (sx, 0.02), (sx, sz), 0.40, ty0, ty1, 1)
        for tz in (h * 0.30, h * 0.56):
            _bar(mb, (-w * 0.455, tz), (w * 0.455, tz), 0.38, ty0, ty1, 1)
        _bar(mb, (-w * 0.455, sz), (w * 0.455, sz), 0.38, ty0, ty1, 1)
        # head: two pointed sub-arches springing from the transom
        apex = h * 0.965
        _bar(mb, (0.0, sz), (0.0, apex), 0.32, ty0, ty1, 1)
        for sx in (-w * 0.25, w * 0.25):
            _bar(mb, (sx, sz), (0.0, apex * 0.99), 0.26, ty0, ty1, 1)
        for sx in (-w * 0.455, w * 0.455):
            _bar(mb, (sx, sz), (sx, sz + (apex - sz) * 0.62), 0.24, ty0, ty1, 1)
            _bar(mb, (sx, sz + (apex - sz) * 0.62), (0.0, apex * 0.985),
                 0.24, ty0, ty1, 1)
        # the door leaves themselves: two vertical stiles and a meeting rail
        _bar(mb, (-0.06, 0.02), (-0.06, h * 0.56), 0.30, ty0, ty1, 1)
        _bar(mb, (0.06, 0.02), (0.06, h * 0.56), 0.30, ty0, ty1, 1)
    # --- stone surround ---
    outer, inner = L.arch_band_points(kind, w, 0.0, h, 12, 0.24)
    v, f = L.p_band(outer, inner, -0.04, BAND_PROJ)
    mb.add(v, f, 2)
    return mb


class Windows:
    """Builds and places window units; also generates boolean cutters."""

    def __init__(self, coll, mats):
        self.coll = coll
        self.mats = mats
        self.tpl = {}
        self.count = 0

    def mesh_for(self, kind, w, h, style):
        key = (kind, round(w, 2), round(h, 2), style)
        if key not in self.tpl:
            mb = _window_mesh(kind, w, h, style)
            me = bpy.data.meshes.new("W_%s_%s_%0.2fx%0.2f" % (kind, style, w, h))
            me.from_pydata(mb.verts, [], mb.faces)
            me.update()
            # Recalculate outward normals for every closed shell (glass, lead
            # bars and rings, petals, stone surround).  The parts are extruded
            # from profiles with different winding -- a horizontal bar comes
            # out clockwise while a vertical one comes out anticlockwise --
            # so without this some of them ended up inside-out and shaded
            # from the wrong side.
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bm.to_mesh(me)
            bm.free()
            for i, p in enumerate(me.polygons):
                if i < len(mb.mats):
                    p.material_index = mb.mats[i]
            for m in self.mats:
                me.materials.append(m)
            self.tpl[key] = me
        return self.tpl[key]

    def cutters(self, mb, frames, parent=None):
        """frames: list of dict(matrix, kind, w, h, style)"""
        for fr in frames:
            prof = L.opening_profile(fr['kind'], fr['w'], 0.0, fr['h'])
            v, f = L.p_prism(prof, 0.6, -RECESS)
            m = fr['matrix'] if parent is None else parent @ fr['matrix']
            mb.add(v, f, 0, m)

    def place(self, frames, name, parent=None):
        out = []
        for fr in frames:
            me = self.mesh_for(fr['kind'], fr['w'], fr['h'], fr['style'])
            obj = bpy.data.objects.new("%s_%03d" % (name, self.count), me)
            m = fr['matrix'] if parent is None else parent @ fr['matrix']
            obj.matrix_world = m
            # Cycles' Object Info > "Object Index" output is the object's
            # pass_index, which defaults to 0 for every object -- so every
            # window would get the SAME random value and the whole castle
            # would light up (or not) as one.  A unique index per window is
            # what lets each pane have its own brightness.
            obj.pass_index = 1 + (self.count % 32000)
            self.coll.objects.link(obj)
            self.count += 1
            out.append(obj)
        return out


def fmat(x, sill, theta=None, R=None):
    """Frame matrix for a window.  x = distance along a flat wall, or angle."""
    if theta is None:
        return Matrix.Translation((x, 0.0, sill))
    return (Matrix.Translation((R * math.cos(theta), R * math.sin(theta), sill))
            @ Matrix.Rotation(theta - math.pi * 0.5, 4, 'Z'))


# =============================================================== wall / panel
def panel(name, c, solid_vf, frames, mats, win, parent=None, coll_name=None):
    """Create a wall solid, cut the window openings, and place window units."""
    mb = L.MB()
    mb.add(*solid_vf, mat=0)
    wall = mb.to_object(name, c, mats, fix_normals=False)
    if parent is not None:
        wall.matrix_world = parent
    if frames:
        cmb = L.MB()
        win.cutters(cmb, frames, parent=parent)
        cut = cmb.to_object(name + "_cut", c, None, fix_normals=False)
        # NO matrix_world here: Windows.cutters() already bakes `parent @
        # fr['matrix']` into the vertex positions (MB.add transforms the
        # points), so the cutter mesh is already in world space and its
        # object matrix must stay identity.  Setting it again applied the
        # parent transform a SECOND time, which threw every cutter clear of
        # its wall -- the boolean then cut nothing and all 477 windows stayed
        # buried inside solid masonry.
        L.boolean_cut(wall, cut)
    if frames:
        win.place(frames, name, parent=parent)
    return wall


def wall_frames(length, height, n_bays, win_w, win_h, sill, kind='lancet',
                style='lancet', x0=0.0, per_bay=2):
    """Evenly spaced window frames along a flat wall of the given length."""
    fr = []
    if n_bays <= 0:
        return fr
    bw = length / n_bays
    for b in range(n_bays):
        c = x0 + bw * (b + 0.5)
        if per_bay == 1:
            fr.append(dict(matrix=fmat(c, sill), kind=kind, w=win_w, h=win_h, style=style))
        else:
            d = min(bw * 0.24, win_w * 1.25)
            for s in (-1, 1):
                fr.append(dict(matrix=fmat(c + s * d, sill), kind=kind, w=win_w,
                               h=win_h, style=style))
    return fr


def cyl_frames(radius, n, z, win_w, win_h, kind='lancet', style='lancet',
               a0=0.0, phase=0.0):
    fr = []
    for i in range(n):
        a = a0 + math.pi * 2 * i / n + phase
        fr.append(dict(matrix=fmat(0.0, z, a, radius), kind=kind, w=win_w,
                       h=win_h, style=style))
    return fr


# =============================================================== ornament
def crenellation(mb, r, z, n, mw, mh, depth, mat, a0=0.0, taper=0.0):
    """Merlons around a circle (taper>0 pulls them inward as they rise)."""
    for i in range(n):
        a = a0 + math.pi * 2 * i / n
        w = mw if taper <= 0 else mw * (1 - taper * (mh / max(mh, 1)))
        v, f = L.p_box_minmax(-w * .5, -depth * .5, 0.0, w * .5, depth * .5, mh)
        mb.add(v, f, mat, Matrix.Translation((r * math.cos(a), r * math.sin(a), z))
               @ Matrix.Rotation(a, 4, 'Z'))


def corbel_ring(mb, r, z, n, size, out, mat):
    for i in range(n):
        a = math.pi * 2 * i / n
        v, f = L.p_box_minmax(-size * .5, 0.0, -size * 1.6, size * .5, out, 0.0)
        mb.add(v, f, mat, Matrix.Translation((r * math.cos(a), r * math.sin(a), z))
               @ Matrix.Rotation(a - math.pi * .5, 4, 'Z'))


def string_course(mb, r, z, h, out, mat, n=40):
    v, f = L.p_cyl(r + out, h, n, z0=z - h * .5)
    mb.add(v, f, mat)


def conical_cap(mb, r, z, h, n, mat, finial=True, fin_mat=None, collar=0.0):
    if collar > 0:
        v, f = L.p_cyl(r + collar, collar * 0.9, n, z0=z)
        mb.add(v, f, mat)
        z += collar * 0.9
    v, f = L.p_cone(r, h, n, z0=z)
    mb.add(v, f, mat)
    if finial:
        zt = z + h
        fm = fin_mat if fin_mat is not None else mat
        v, f = L.p_cyl(0.30, 0.9, 8, z0=zt - 0.35)
        mb.add(v, f, fm)
        v, f = L.p_sphere(0.42, 10, 7, z0=zt + 0.45)
        mb.add(v, f, fm)
        v, f = L.p_cyl(0.10, 2.6, 6, z0=zt + 0.6)
        mb.add(v, f, fm)


def pinnacle(mb, r, z, h, mat, sides=4, fin_mat=None):
    """Slender square/hex pinnacle with a pointed cap."""
    fm = fin_mat if fin_mat is not None else mat
    v, f = L.p_box_minmax(-r * .5, -r * .5, 0.0, r * .5, r * .5, h * 0.30)
    mb.add(v, f, mat)
    v, f = L.p_box_minmax(-r * .34, -r * .34, h * 0.30, r * .34, r * .34, h * 0.62)
    mb.add(v, f, mat)
    v, f = L.p_cone(r * 0.62, h * 0.38, sides, z0=h * 0.62)
    mb.add(v, f, fm)


def buttress(mb, x, y, z, h, width, proj, mat, rot=0.0, steps=3, pinnacle_h=0.0,
             p_mat=None):
    """Stepped buttress projecting from a wall face (local +Y is outward)."""
    for s in range(steps):
        t = s / max(steps - 1, 1)
        z0 = z + h * (s / steps)
        z1 = z + h * ((s + 1) / steps)
        pr = proj * (1.0 - 0.55 * t)
        wd = width * (1.0 - 0.18 * t)
        v, f = L.p_box_minmax(-wd * .5, -0.15, z0, wd * .5, pr, z1)
        mb.add(v, f, mat, Matrix.Translation((x, y, 0.0)) @ Matrix.Rotation(rot, 4, 'Z'))
    if pinnacle_h > 0:
        pm = p_mat if p_mat is not None else mat
        v, f = L.p_box_minmax(-width * .32, -0.10, z + h, width * .32, proj * 0.45, z + h + 0.7)
        mb.add(v, f, pm, Matrix.Translation((x, y, 0.0)) @ Matrix.Rotation(rot, 4, 'Z'))
        pb = L.MB()
        pinnacle(pb, width * 0.6, 0.0, pinnacle_h, pm, 4)
        mb.add(pb.verts, pb.faces, pm, Matrix.Translation((x, y, 0.0))
               @ Matrix.Rotation(rot, 4, 'Z') @ Matrix.Translation((0, proj * 0.20, z + h + 0.7)))


def gable_roof(mb, cx, cy, hx, hy, eave_z, ridge_z, mat, thick=0.55,
               oh=1.4, oh_len=1.0):
    """Gable roof over a rectangle centred at (cx,cy) with half-extents hx,hy.

    The ridge runs along the longer side.  eave_z / ridge_z are absolute heights.
    """
    if hy >= hx:
        for s in (-1, 1):
            prof = [(0.0, ridge_z - thick), (s * (hx + oh), eave_z - thick),
                    (s * (hx + oh), eave_z), (0.0, ridge_z)]
            if s < 0:
                prof = list(reversed(prof))
            v, f = L.p_prism(prof, -hy - oh_len, hy + oh_len)
            mb.add(v, f, mat, Matrix.Translation((cx, cy, 0.0)))
    else:
        for s in (-1, 1):
            prof = [(0.0, ridge_z - thick), (s * (hy + oh), eave_z - thick),
                    (s * (hy + oh), eave_z), (0.0, ridge_z)]
            if s < 0:
                prof = list(reversed(prof))
            v, f = L.p_prism(prof, -hx - oh_len, hx + oh_len)
            mb.add(v, f, mat, Matrix.Translation((cx, cy, 0.0))
                   @ Matrix.Rotation(math.pi * 0.5, 4, 'Z'))


def hip_roof(mb, cx, cy, hx, hy, eave_z, ridge_z, mat):
    """Pyramidal hip roof over a rectangle."""
    base = [(cx - hx, cy - hy, eave_z), (cx + hx, cy - hy, eave_z),
            (cx + hx, cy + hy, eave_z), (cx - hx, cy + hy, eave_z)]
    mb.verts.extend(base)
    mb.verts.append((cx, cy, ridge_z))
    for i in range(4):
        j = (i + 1) % 4
        mb.faces.append((i, j, 4))
        mb.mats.append(0)


def gable_wall_profile(half_w, wall_h, gable_h):
    """Polygon (x,z) of a gable end wall."""
    return [(-half_w, 0.0), (half_w, 0.0), (half_w, wall_h),
            (0.0, gable_h), (-half_w, wall_h)]
