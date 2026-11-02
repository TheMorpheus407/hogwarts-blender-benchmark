"""PASS 6 — story props: owlery, quidditch pitch, gamekeeper's hut,
standing-stone circle, covered wooden bridge, distant railway viaduct.

Everything is built from primitives/bmesh through the hg_lib mesh builder —
no imported assets, no image textures, no external files.  Units are metres,
Z up, water plane at z = 0.

Every prop is seated with `hg_land.terrain_z`, which samples the *rendered*
terrain surface (the terrain mesh is a warped grid, so `land_height` alone can
be off by a metre).  The sites were chosen by probing that same field:

  owlery     C.T_OWLERY (-172, 86) — the anchor falls in the lake (rendered
             bed z = -0.59, water at z = 0), so the tower stands on a rock
             outcrop (skerry) whose foot is sunk into the bed
  quidditch  (450, -240) on the eastern moor, flat stone terrace
  hut        (556, -236) in a clearing ~60 m off the conifer forest edge
  stones     (-236, 904) open moor on the northern shore
  bridge     PATH_MAIN crosses a gully at x = 704 between y = 264 and 298
  viaduct    the west moor at y = -200, x = -1180 .. -860 (level shelf)

Re-running the module is safe: it only deletes objects whose names start with
"Prop_" and rebuilds them.
"""
import bpy, bmesh, math, random, importlib, sys, os
import numpy as np
from mathutils import Vector, Matrix

BUILD = os.path.dirname(os.path.abspath(__file__))
if not os.path.isdir(BUILD):                       # pragma: no cover
    BUILD = "/home/morpheus/Documents/Morpheus-Produktion/Benchmarks/Blender/MiniMax-M3.1-Flash/build"
if BUILD not in sys.path:
    sys.path.insert(0, BUILD)

import hg_lib, hg_np, hg_mat, hg_cfg, hg_land, hg_castle
for _m in (hg_lib, hg_np, hg_mat, hg_cfg, hg_land, hg_castle):
    importlib.reload(_m)
import hg_lib as L
import hg_mat as M
import hg_cfg as C
import hg_land as LD
import hg_np as N
import hg_castle as K

TAU = math.pi * 2.0
SEED = 20261023
COLL_NAME = "Props"
PREFIX = "Prop_"


# ============================================================== site constants
SITE_OWLERY = C.T_OWLERY                    # (-172.0, 86.0)
SITE_QUID = (450.0, -240.0)                 # pitch centre
SITE_HUT = (556.0, -236.0)                  # gamekeeper's cottage
SITE_STONES = (-236.0, 904.0)               # standing-stone circle
BRIDGE_X = 704.0                            # gully crossed by PATH_MAIN
BRIDGE_Y0, BRIDGE_Y1 = 264.0, 298.0         # span, north -> south
BRIDGE_Z0, BRIDGE_Z1 = 40.6, 33.0           # deck level at each end
VIA_X0, VIA_Y = -1180.0, -200.0             # distant railway viaduct
VIA_LENGTH = 320.0
VIA_ARCHES = 16
VIA_DECK_W = 7.0


# ============================================================ small utilities
def _tz(x, y):
    """Height of the rendered terrain surface at (x, y)."""
    return float(LD.terrain_z(np.array([float(x)]), np.array([float(y)]))[0])


def _tz_many(xs, ys):
    return LD.terrain_z(np.asarray(xs, dtype=np.float64),
                        np.asarray(ys, dtype=np.float64))


def _purge_props():
    """Remove only what a previous run of this module created."""
    for o in list(bpy.data.objects):
        if o.name.startswith(PREFIX):
            bpy.data.objects.remove(o, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.name.startswith(PREFIX) and me.users == 0:
            bpy.data.meshes.remove(me)
    for cu in list(bpy.data.curves):
        if cu.name.startswith(PREFIX) and cu.users == 0:
            bpy.data.curves.remove(cu)


def _cut(target, cutter):
    """Boolean difference that never aborts the whole build."""
    try:
        L.boolean_cut(target, cutter)
    except Exception as exc:                      # pragma: no cover
        print("   ! boolean cut failed:", exc)
        if cutter.name in bpy.data.objects:
            bpy.data.objects.remove(cutter, do_unlink=True)


def _ellipse(cx, cy, z, rx, ry, n, a0=0.0):
    return [(cx + rx * math.cos(a0 + TAU * i / n),
             cy + ry * math.sin(a0 + TAU * i / n), z) for i in range(n)]


def _washer(mb, cx, cy, z, r_out, r_in, h, mat, n=24):
    """Closed hollow ring (a washer) whose axis is Z."""
    ob = _ellipse(cx, cy, z, r_out, r_out, n)
    ot = _ellipse(cx, cy, z + h, r_out, r_out, n)
    ib = _ellipse(cx, cy, z, r_in, r_in, n)
    it = _ellipse(cx, cy, z + h, r_in, r_in, n)
    for i in range(n):
        j = (i + 1) % n
        mb.add([ob[i], ob[j], ot[j], ot[i]], [(0, 1, 2, 3)], mat)
        mb.add([ib[j], ib[i], it[i], it[j]], [(0, 1, 2, 3)], mat)
        mb.add([ot[i], ot[j], it[j], it[i]], [(0, 1, 2, 3)], mat)
        mb.add([ib[i], ib[j], ob[j], ob[i]], [(0, 1, 2, 3)], mat)


def _disc_y(mb, r, thick, mat, n=24, cx=0.0, cy=0.0, cz=0.0):
    """A closed disc whose axis is Y (a window pane)."""
    v, f = L.p_cyl(r, thick, n, z0=-thick * .5)
    mb.add(v, f, mat, Matrix.Translation((cx, cy, cz))
           @ Matrix.Rotation(-math.pi * .5, 4, 'X'))


def _torus(mb, R, r, mat, n=28, m=8, matrix=None):
    """Torus (a hoop) whose axis is Z; `matrix` may re-orient it."""
    verts, faces = [], []
    for i in range(n):
        u = TAU * i / n
        for j in range(m):
            v = TAU * j / m
            rr = R + r * math.cos(v)
            verts.append((rr * math.cos(u), rr * math.sin(u), r * math.sin(v)))
    for i in range(n):
        i2 = (i + 1) % n
        for j in range(m):
            j2 = (j + 1) % m
            faces.append((i * m + j, i2 * m + j, i2 * m + j2, i * m + j2))
    mb.add(verts, faces, mat, matrix)


def _beam(mb, p0, p1, w, h, mat, up=(0.0, 0.0, 1.0)):
    """Rectangular beam between two 3D points."""
    p0 = Vector(p0)
    p1 = Vector(p1)
    d = (p1 - p0)
    if d.length < 1e-6:
        return
    d.normalize()
    upv = Vector(up)
    if abs(d.dot(upv)) > 0.98:
        upv = Vector((1.0, 0.0, 0.0))
    side = d.cross(upv).normalized()
    upv2 = side.cross(d).normalized()
    prof = []
    for sgn in (-1, 1):
        for s2 in (-1, 1):
            prof.append(sgn * w * .5 * side + s2 * h * .5 * upv2)
    v = [tuple(p0 + p) for p in prof] + [tuple(p1 + p) for p in prof]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
         (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mb.add(v, f, mat)


def _slab(mb, x0, x1, z0, z1, y0, y1, mat, thick=0.16):
    """A sloping slab between two heights (roof planes, ramps)."""
    prof = [(x0, z0), (x1, z1), (x1, z1 + thick), (x0, z0 + thick)]
    v, f = L.p_prism(prof, y0, y1)
    mb.add(v, f, mat)


def _solid_disc(mb, cx, cy, z0, z1, rx, ry, n=48, mat=0):
    """A closed thin elliptical disc (top + bottom + rim)."""
    base = len(mb.verts)
    mb.verts.extend(_ellipse(cx, cy, z1, rx, ry, n))      # top ring
    mb.verts.extend(_ellipse(cx, cy, z0, rx, ry, n))      # bottom ring
    ct = len(mb.verts)
    mb.verts.append((cx, cy, z1))
    cb = len(mb.verts)
    mb.verts.append((cx, cy, z0))
    for i in range(n):
        j = (i + 1) % n
        ti, tj = base + i, base + j
        bi, bj = base + n + i, base + n + j
        mb.faces.append((ct, ti, tj))
        mb.mats.append(mat)
        mb.faces.append((cb, bj, bi))
        mb.mats.append(mat)
        mb.faces.append((ti, bi, bj, tj))
        mb.mats.append(mat)


def _pyramid_roof(mb, cx, cy, hx, hy, eave_z, ridge_z, thick, mat):
    """Closed pyramidal roof shell (outer pyramid, inner pyramid, eave band)."""
    H = max(ridge_z - eave_z, 0.01)
    outer = [(cx - hx, cy - hy, eave_z), (cx + hx, cy - hy, eave_z),
             (cx + hx, cy + hy, eave_z), (cx - hx, cy + hy, eave_z)]
    k = 1.0 - thick / H
    inner = [(cx - hx * k, cy - hy * k, eave_z - thick),
             (cx + hx * k, cy - hy * k, eave_z - thick),
             (cx + hx * k, cy + hy * k, eave_z - thick),
             (cx - hx * k, cy + hy * k, eave_z - thick)]
    ao = len(mb.verts)
    mb.verts.extend(outer)
    ai = len(mb.verts)
    mb.verts.extend(inner)
    oa = len(mb.verts)
    mb.verts.append((cx, cy, ridge_z))
    ia = len(mb.verts)
    mb.verts.append((cx, cy, ridge_z - thick))
    for i in range(4):
        j = (i + 1) % 4
        mb.faces.append((ao + i, ao + j, oa))
        mb.mats.append(mat)
        mb.faces.append((ia + j, ia + i, ia))
        mb.mats.append(mat)
        mb.faces.append((ao + j, ao + i, ai + i, ai + j))
        mb.mats.append(mat)


def _arch_spandrel_profile(x0, x1, z_top, spring, crown, segs=12):
    """Profile (x, z) of a spandrel wall pierced by a segmental arch.

    The wall is the material ABOVE the arch: the arc runs from the left
    springing over the crown to the right springing and the polygon closes
    across the top.  The opening below the arc is left empty, so the arcade
    reads as arches on piers rather than a solid wall.
    """
    cx = (x0 + x1) * .5
    rx = (x1 - x0) * .5
    prof = []
    for i in range(segs + 1):
        t = math.pi * i / segs                  # left springing -> right
        prof.append((cx - rx * math.cos(t),
                     spring + (crown - spring) * math.sin(t)))
    prof.append((x1, z_top))
    prof.append((x0, z_top))
    return prof


def _boulder(rx, ry, rz, rng, nu=7, nv=4):
    """Angular low-poly boulder (closed)."""
    v = []
    for j in range(nv + 1):
        th = math.pi * j / nv
        for i in range(nu):
            ph = TAU * i / nu
            sx = math.sin(th) * math.cos(ph)
            sy = math.sin(th) * math.sin(ph)
            sz = math.cos(th)
            seed = rng.uniform(0.0, 10.0)
            h = (math.sin(sx * 5.1 + seed) * math.cos(sy * 4.3 - seed)
                 + 0.6 * math.sin(sz * 7.7 + seed * 1.7))
            k = 1.0 + 0.30 * h
            v.append((sx * rx * k, sy * ry * k, sz * rz * k))
    f = []
    for j in range(nv):
        for i in range(nu):
            i2 = (i + 1) % nu
            a = j * nu
            b = (j + 1) * nu
            f.append((a + i, a + i2, b + i2, b + i))
    return v, f


# ================================================================== materials
def build_materials():
    """Every material is an existing hg_mat procedural; variants are the same
    function called with different arguments."""
    return {
        'stone': M.m_stone('M_Stone'),
        'stone_warm': M.m_stone('M_StoneWarmProp', tint=(1.05, 0.98, 0.90),
                                base_col=(0.330, 0.300, 0.262)),
        'slate': M.m_slate('M_Slate'),
        'lead': M.m_lead('M_Lead'),
        'gold': M.m_gold('M_Gold'),
        'verdigris': M.m_verdigris('M_Verdigris'),
        'rock': M.m_rock('M_Rock'),
        'bark': M.m_bark('M_Bark'),
        'wood': M.m_wood('M_Wood'),
        'wood_dark': M.m_wood('M_WoodDark', col=(0.030, 0.021, 0.014)),
        'glass': M.m_window_glass('M_WindowGlass'),
        'hut_glass': M.m_window_glass('M_HutWindow', warm=(1.0, 0.62, 0.26),
                                     max_strength=7.0, lit_frac=1.0),
        'lantern': M.m_emissive('M_Lantern'),
        'grass': M.m_grass('M_Grass'),
    }


def build_smoke_material(z0, z1, density=0.80):
    """Volume material for the chimney plume: dense at the stack, thinning with
    height (same node style as hg_mat.m_mist)."""
    return M.m_mist('M_PropSmoke', col=(0.42, 0.45, 0.50), density=density,
                    z_top=z1, z_peak=z0 + 1.2, z_bot=z0 - 4.0, floor=0.0,
                    nscale=0.26, rough=0.62)


# ==================================================================== 1. owlery
def build_owlery(c, mats, rng):
    """Owlery tower on a rock outcrop (islet) at C.T_OWLERY."""
    out = []
    ox, oy = SITE_OWLERY
    bed = _tz(ox, oy)
    top_z = 7.2                       # top of the rock plateau
    site = Matrix.Translation((ox, oy, top_z))

    local_parts = []          # modelled in the tower's local frame

    # ---------------------------------------------------------------- outcrop
    mb = L.MB()
    nring, nseg = 9, 26
    base_z = bed - 5.0
    for ri in range(nring):
        t = ri / (nring - 1.0)          # 0 bottom -> 1 top
        z = base_z + (top_z - base_z) * (t ** 0.75)
        if t > 0.92:
            r = 7.6 - (t - 0.92) * 2.0
        else:
            r = 19.0 - (19.0 - 7.6) * (t ** 1.6)
        for k in range(nseg):
            a = TAU * k / nseg
            wob = 1.0 + 0.16 * math.sin(a * 3.0 + ri * 0.7) \
                      + 0.09 * math.sin(a * 5.0 - ri * 1.3)
            rr = r * wob * (1.0 - 0.05 * t)
            mb.verts.append((ox + rr * math.cos(a), oy + rr * math.sin(a),
                             z + 0.55 * math.sin(a * 4.0 + ri)))
    for ri in range(nring - 1):
        for k in range(nseg):
            k2 = (k + 1) % nseg
            a = ri * nseg
            b = (ri + 1) * nseg
            mb.faces.append((a + k, a + k2, b + k2, b + k))
            mb.mats.append(0)
    ct = len(mb.verts)
    mb.verts.append((ox, oy, top_z))
    cb = len(mb.verts)
    mb.verts.append((ox, oy, base_z))
    for k in range(nseg):
        k2 = (k + 1) % nseg
        mb.faces.append((ct, (nring - 1) * nseg + k2, (nring - 1) * nseg + k))
        mb.mats.append(0)
        mb.faces.append((cb, k, k2))
        mb.mats.append(0)
    out.append(mb.to_object(PREFIX + "Owlery_Outcrop", c, [mats['rock']]))

    # --------------------------------------------------------- tower (stone)
    hw, wall_t, h = 3.5, 0.75, 13.0
    mb = L.MB()
    v, f = L.p_box_minmax(-hw, -hw, 0.0, hw, -hw + wall_t, h)
    mb.add(v, f, 0)                                   # south wall
    v, f = L.p_box_minmax(-hw, hw - wall_t, 0.0, hw, hw, h)
    mb.add(v, f, 0)                                   # north wall
    v, f = L.p_box_minmax(-hw, -hw + wall_t, 0.0, -hw + wall_t, hw - wall_t, h)
    mb.add(v, f, 0)                                   # west wall
    v, f = L.p_box_minmax(hw - wall_t, -hw + wall_t, 0.0, hw, hw - wall_t, h)
    mb.add(v, f, 0)                                   # east wall
    v, f = L.p_box_minmax(-hw, -hw, 0.0, hw, hw, 0.30)
    mb.add(v, f, 0)                                   # floor slab
    for sgn in (-1, 1):
        v, f = L.p_box_minmax(-hw - 0.35, sgn * hw - 0.35, h - 0.45,
                              hw + 0.35, sgn * hw + 0.35, h)
        mb.add(v, f, 0)
        v, f = L.p_box_minmax(sgn * hw - 0.35, -hw - 0.35, h - 0.45,
                              sgn * hw + 0.35, hw + 0.35, h)
        mb.add(v, f, 0)
    po, pi = 3.85, 3.20                               # parapet outer / inner
    z0p, z1p = h, h + 1.30
    for sgn in (-1, 1):
        v, f = L.p_box_minmax(-po, sgn * po - 0.65, z0p, po, sgn * po, z1p)
        mb.add(v, f, 0)
        v, f = L.p_box_minmax(sgn * po - 0.65, -po, z0p, sgn * po, pi, z1p)
        mb.add(v, f, 0)
    tower = mb.to_object(PREFIX + "Owlery_Tower", c, [mats['stone']])
    local_parts.append(tower)

    # merlons on the parapet
    mb = L.MB()
    merlon_w = 0.85
    for sgn in (-1, 1):
        n = 8
        step = 2 * po / n
        for i in range(n):
            cx = -po + step * (i + 0.5)
            v, f = L.p_box_minmax(cx - merlon_w * .5, sgn * po - 0.65, z1p,
                                  cx + merlon_w * .5, sgn * po, z1p + 0.70)
            mb.add(v, f, 0)
        for i in range(n):
            cy = -po + step * (i + 0.5)
            v, f = L.p_box_minmax(sgn * po - 0.65, cy - merlon_w * .5, z1p,
                                  sgn * po, cy + merlon_w * .5, z1p + 0.70)
            mb.add(v, f, 0)
    local_parts.append(mb.to_object(PREFIX + "Owlery_Merlons", c, [mats['stone']]))

    # ------------------------------------------------- pointed-arch doorway
    mb = L.MB()
    door_w, door_h = 1.90, 2.55
    prof = L.opening_profile('lancet', door_w, 0.0, door_h, 12)
    v, f = L.p_prism(prof, -hw - 0.6, -hw + wall_t + 0.6)
    mb.add(v, f, 0)
    cutter = mb.to_object(PREFIX + "Owlery_DoorCut", c, None, fix_normals=False)
    _cut(tower, cutter)

    mb = L.MB()
    outer, inner = L.arch_band_points('lancet', door_w, 0.0, door_h, 12, 0.22)
    v, f = L.p_band(outer, inner, -hw - 0.14, -hw + 0.02)
    mb.add(v, f, 0)
    v, f = L.p_box_minmax(-1.05, -hw + 0.10, 0.0, 1.05, -hw + 0.32, 0.22)
    mb.add(v, f, 0)                                    # threshold step
    local_parts.append(mb.to_object(PREFIX + "Owlery_Doorway", c,
                                    [mats['stone_warm']]))

    mb = L.MB()
    leaf = [(-door_w * .5 + 0.06, 0.06), (door_w * .5 - 0.06, 0.06),
            (door_w * .5 - 0.06, door_h * .60), (-door_w * .5 + 0.06, door_h * .60)]
    v, f = L.p_prism(leaf, -hw + wall_t - 0.14, -hw + wall_t - 0.02)
    mb.add(v, f, 0)
    local_parts.append(mb.to_object(PREFIX + "Owlery_Door", c,
                                    [mats['wood_dark']]))

    # ------------------------------------------------------- round window
    win_z = 8.60
    mb = L.MB()
    v, f = L.p_cyl(1.20, 1.40, 24, z0=2.40)
    mb.add(v, f, 0, Matrix.Translation((0.0, 0.0, win_z))
           @ Matrix.Rotation(-math.pi * .5, 4, 'X'))
    cutter = mb.to_object(PREFIX + "Owlery_WinCut", c, None, fix_normals=False)
    _cut(tower, cutter)

    mb = L.MB()
    _washer(mb, 0.0, 0.0, -0.13, 1.42, 1.20, 0.26, 0)
    surround = mb.to_object(PREFIX + "Owlery_WindowSurround", c, [mats['stone']])
    surround.matrix_world = (Matrix.Translation((0.0, hw - 0.06, win_z))
                             @ Matrix.Rotation(-math.pi * .5, 4, 'X'))
    local_parts.append(surround)

    mb = L.MB()
    _disc_y(mb, 1.19, 0.05, 0, 24, 0.0, hw - wall_t + 0.05, win_z)
    local_parts.append(mb.to_object(PREFIX + "Owlery_WindowGlass", c,
                                    [mats['glass']]))

    mb = L.MB()
    for k in range(4):                                  # iron tracery bars
        a = k * math.pi / 4.0
        p0 = (0.0, hw - wall_t + 0.08, win_z)
        p1 = (1.18 * math.cos(a), hw - wall_t + 0.08, win_z + 1.18 * math.sin(a))
        _beam(mb, p0, p1, 0.07, 0.07, 0)
    local_parts.append(mb.to_object(PREFIX + "Owlery_WindowTracery", c,
                                    [mats['lead']]))

    # ------------------------------------------------------------- roof
    mb = L.MB()
    _pyramid_roof(mb, 0.0, 0.0, 3.25, 3.25, 13.40, 21.00, 0.28, 0)
    local_parts.append(mb.to_object(PREFIX + "Owlery_Roof", c, [mats['slate']]))

    mb = L.MB()
    v, f = L.p_cyl(0.30, 0.55, 8, z0=20.85)
    mb.add(v, f, 0)
    v, f = L.p_cone(0.34, 2.10, 8, z0=21.30)
    mb.add(v, f, 0)
    v, f = L.p_sphere(0.36, 10, 7, z0=21.05)
    mb.add(v, f, 0)
    local_parts.append(mb.to_object(PREFIX + "Owlery_Finial", c,
                                    [mats['verdigris']]))

    # ---------------------------------------------------------- dormers
    slope = math.atan2(3.25, 7.60)      # roof face angle from the vertical
    tilt = math.pi * .5 - slope
    for idx, (sgn, axis) in enumerate(((-1, 'S'), (1, 'E'))):
        roof_z = 15.40
        dist = 3.25 * (1.0 - (roof_z - 13.40) / 7.60)
        mb = L.MB()
        v, f = L.p_box_minmax(-0.65, -0.45, 0.0, 0.65, 0.45, 1.15)
        mb.add(v, f, 0)
        _slab(mb, -0.85, 0.0, 1.15, 1.60, -0.55, 0.55, 0)
        _slab(mb, 0.0, 0.85, 1.60, 1.15, -0.55, 0.55, 0)
        if sgn < 0:
            mtx = (Matrix.Translation((0.0, -dist, roof_z))
                   @ Matrix.Rotation(tilt, 4, 'X'))
        else:
            mtx = (Matrix.Translation((dist, 0.0, roof_z))
                   @ Matrix.Rotation(tilt, 4, 'Y')
                   @ Matrix.Rotation(math.pi * .5, 4, 'Z'))
        dormer = mb.to_object(PREFIX + "Owlery_Dormer_%d" % (idx + 1),
                              c, [mats['slate']])
        dormer.matrix_world = mtx
        local_parts.append(dormer)

        mb = L.MB()
        v, f = L.p_box_minmax(-0.30, -0.50, 0.35, 0.30, -0.46, 0.95)
        mb.add(v, f, 0)
        gl = mb.to_object(PREFIX + "Owlery_DormerGlass_%d" % (idx + 1),
                          c, [mats['glass']])
        gl.matrix_world = mtx
        local_parts.append(gl)

    # ------------------------------------------------- drystone wall arc
    mb = L.MB()
    a0, a1 = math.radians(-40.0), math.radians(210.0)
    nseg_w = 26
    for i in range(nseg_w):
        t0 = a0 + (a1 - a0) * i / nseg_w
        t1 = a0 + (a1 - a0) * (i + 1) / nseg_w
        tm = (t0 + t1) * .5
        rr = 6.35 + 0.12 * math.sin(i * 2.3)
        for cse in range(4):
            zh = top_z + 0.02 + cse * 0.23
            w = 0.62 + rng.uniform(-0.05, 0.05)
            dpt = 0.46 + rng.uniform(-0.05, 0.05)
            mtx = (Matrix.Translation((ox + rr * math.cos(tm),
                                       oy + rr * math.sin(tm), zh))
                   @ Matrix.Rotation(tm, 4, 'Z'))
            v, f = L.p_box_minmax(-w * .5, -dpt * .5, 0.0, w * .5, dpt * .5,
                                  0.23 + rng.uniform(-0.03, 0.03))
            mb.add(v, f, 0, mtx)
    out.append(mb.to_object(PREFIX + "Owlery_DrystoneWall", c, [mats['stone']]))

    # ------------------------------------------------------- owl perches
    mb = L.MB()
    for (px, py) in ((-3.4, 3.1), (3.2, 2.2)):
        gx = ox + px
        gy = oy + py
        gz = max(_tz(gx, gy), top_z - 1.2)
        mtx = Matrix.Translation((gx, gy, gz))
        v, f = L.p_box_minmax(-0.16, -0.16, 0.0, 0.16, 0.16, 2.35)
        mb.add(v, f, 0, mtx)
        v, f = L.p_box_minmax(-0.85, -0.11, 2.05, 0.85, 0.11, 2.25)
        mb.add(v, f, 0, mtx)
        v, f = L.p_box_minmax(-0.30, -0.30, 0.0, 0.30, 0.30, 0.22)
        mb.add(v, f, 0, mtx)
        v, f = L.p_sphere(0.16, 8, 6, z0=2.52)
        mb.add(v, f, 1, mtx @ Matrix.Translation((0.25, 0.0, 0.0)))
        v, f = L.p_sphere(0.11, 8, 6, z0=2.70)
        mb.add(v, f, 1, mtx @ Matrix.Translation((0.25, 0.0, 0.0)))
    out.append(mb.to_object(PREFIX + "Owlery_Perches", c,
                            [mats['bark'], mats['wood']]))

    # only now, with the wall booleans finished, move the tower onto the rock
    for o in local_parts:
        o.matrix_world = site @ o.matrix_world
    out.extend(local_parts)
    return out


# ============================================================== 2. quidditch
def build_quidditch(c, mats, rng):
    """Quidditch pitch on a flat stone terrace in the middle distance."""
    out = []
    cx, cy = SITE_QUID
    rx, ry = 60.0, 30.0                      # mown grass oval
    trx, try_ = 66.0, 34.0                  # terrace half extents

    xs = [cx + rx * math.cos(TAU * i / 36) for i in range(36)]
    ys = [cy + ry * math.sin(TAU * i / 36) for i in range(36)]
    # the terrace level is set by the HIGHEST ground under the whole terrace,
    # so the pitch is flat and no mound pokes through it
    probe_x, probe_y = list(xs), list(ys)
    for i in range(56):
        a = TAU * i / 56
        probe_x.append(cx + trx * math.cos(a))
        probe_y.append(cy + try_ * math.sin(a))
    for gx in np.linspace(cx - trx, cx + trx, 9):
        for gy in np.linspace(cy - try_, cy + try_, 7):
            if ((gx - cx) / trx) ** 2 + ((gy - cy) / try_) ** 2 <= 1.0:
                probe_x.append(float(gx))
                probe_y.append(float(gy))
    z_terrace = float(np.max(_tz_many(probe_x, probe_y))) + 0.30

    # ------------------------------------------------------- stone terrace
    # A battered stone revetment holds the pitch flat: the wall flares out at
    # its foot so it reads as a cut into the hillside, not as a sheer face.
    mb = L.MB()
    n = 56
    top = _ellipse(cx, cy, z_terrace, trx, try_, n)
    ring_x = [cx + (trx + 2.0) * math.cos(TAU * i / n) for i in range(n)]
    ring_y = [cy + (try_ + 2.0) * math.sin(TAU * i / n) for i in range(n)]
    ring_z = _tz_many(ring_x, ring_y)
    bot = []
    for i in range(n):
        gz = float(ring_z[i])
        flare = 0.70 * max(z_terrace - gz, 0.0)
        a = TAU * i / n
        bot.append((cx + (trx + 2.0 + flare) * math.cos(a),
                    cy + (try_ + 2.0 + flare) * math.sin(a),
                    min(gz - 1.5, z_terrace - 1.5)))
    mb.verts.extend(top)
    mb.verts.extend(bot)
    ct = len(mb.verts)
    mb.verts.append((cx, cy, z_terrace))
    cb = len(mb.verts)
    mb.verts.append((cx, cy, min(b[2] for b in bot) - 0.5))
    for i in range(n):
        j = (i + 1) % n
        mb.faces.append((ct, i, j))                       # top fan
        mb.mats.append(0)
        mb.faces.append((cb, n + j, n + i))               # bottom fan
        mb.mats.append(0)
        mb.faces.append((i, n + i, n + j, j))             # battered flank
        mb.mats.append(0)
    out.append(mb.to_object(PREFIX + "Quidditch_Terrace", c, [mats['stone']]))

    # ------------------------------------------------------ mown grass oval
    mb = L.MB()
    _solid_disc(mb, cx, cy, z_terrace + 0.01, z_terrace + 0.07, rx, ry, 56, 0)
    out.append(mb.to_object(PREFIX + "Quidditch_Pitch", c, [mats['grass']]))

    # ------------------------------------------------------------- six hoops
    hoop_positions = []
    for sgn in (-1, 1):
        hoop_positions.append((cx + sgn * 52.0, cy - 8.0))
        hoop_positions.append((cx + sgn * 52.0, cy + 8.0))
        hoop_positions.append((cx + sgn * 34.0, cy))
    for i, (hx, hy) in enumerate(hoop_positions):
        mb = L.MB()
        z0 = z_terrace + 0.07
        post_h = 2.05
        # the post must stand at the hoop, not at the world origin
        v, f = L.p_cyl(0.085, post_h, 10, z0=z0)
        mb.add(v, f, 0, Matrix.Translation((hx, hy, 0.0)))
        v, f = L.p_cyl(0.22, 0.14, 10, z0=z0)
        mb.add(v, f, 0, Matrix.Translation((hx, hy, 0.0)))
        mtx = Matrix.Translation((hx, hy, z0 + post_h)) \
            @ Matrix.Rotation(math.pi * .5, 4, 'Y')
        _torus(mb, 0.75, 0.055, 1, n=28, m=8, matrix=mtx)
        out.append(mb.to_object(PREFIX + "Quidditch_Hoop_%02d" % (i + 1), c,
                                [mats['bark'], mats['gold']]))

    # ----------------------------------------------------- boundary markers
    mb = L.MB()
    for i in range(24):
        a = TAU * i / 24.0
        mx = cx + (trx - 3.0) * math.cos(a)
        my = cy + (try_ - 3.0) * math.sin(a)
        mtx = Matrix.Translation((mx, my, z_terrace))
        v, f = L.p_cyl(0.16, 0.85, 6, z0=0.0)
        mb.add(v, f, 0, mtx)
        v, f = L.p_sphere(0.18, 8, 6, z0=0.80)
        mb.add(v, f, 1, mtx)
    out.append(mb.to_object(PREFIX + "Quidditch_Markers", c,
                            [mats['stone'], mats['gold']]))

    # --------------------------------------------------- two timber stands
    for si, sgn in enumerate((-1, 1)):
        mb = L.MB()
        y_in = cy + sgn * (ry + 0.3)        # front row, next to the pitch
        for t in range(4):
            zz = z_terrace + 0.45 * t
            yy = y_in + sgn * (0.95 * t)
            v, f = L.p_box_minmax(cx - 20.0, min(yy, yy + sgn * 0.95), zz,
                                  cx + 20.0, max(yy, yy + sgn * 0.95), zz + 0.45)
            mb.add(v, f, 0)
        y_back = y_in + sgn * 3.8
        v, f = L.p_box_minmax(cx - 20.0, min(y_back, y_in), z_terrace,
                              cx + 20.0, max(y_back, y_in), z_terrace + 1.80)
        mb.add(v, f, 0)
        for px in (-18.0, -9.0, 0.0, 9.0, 18.0):
            v, f = L.p_box_minmax(cx + px - 0.16, min(y_back, y_in),
                                  z_terrace + 1.80, cx + px + 0.16,
                                  max(y_back, y_in), z_terrace + 3.90)
            mb.add(v, f, 0)
        out.append(mb.to_object(PREFIX + "Quidditch_Stand_%d" % (si + 1), c,
                                [mats['wood']]))

        # lean-to roof over the seating
        mb = L.MB()
        y_a = y_back + sgn * 0.2              # high edge, over the top row
        y_b = y_in - sgn * 0.4                # low edge, over the pitch
        z_a = z_terrace + 4.25
        z_b = z_terrace + 2.95
        length = math.hypot(y_a - y_b, z_a - z_b)
        ang = math.atan2(z_a - z_b, abs(y_a - y_b))
        mtx = (Matrix.Translation((cx, (y_a + y_b) * .5, (z_a + z_b) * .5))
               @ Matrix.Rotation(-ang * sgn, 4, 'X'))
        v, f = L.p_box_minmax(cx - 21.0, -length * .5, -0.09,
                              cx + 21.0, length * .5, 0.09)
        mb.add(v, f, 0, mtx)
        out.append(mb.to_object(PREFIX + "Quidditch_Stand_%d_Roof" % (si + 1),
                                c, [mats['slate']]))

    # --------------------------------------------------------- scoreboard
    sx, sy = cx - trx + 5.0, cy
    mb = L.MB()
    for dx in (-1.9, 1.9):
        v, f = L.p_box_minmax(sx + dx - 0.18, sy - 0.18, z_terrace,
                              sx + dx + 0.18, sy + 0.18, z_terrace + 4.4)
        mb.add(v, f, 0)
    v, f = L.p_box_minmax(sx - 2.6, sy - 0.14, z_terrace + 4.4,
                          sx + 2.6, sy + 0.14, z_terrace + 7.3)
    mb.add(v, f, 0)
    out.append(mb.to_object(PREFIX + "Quidditch_Scoreboard", c, [mats['wood']]))

    mb = L.MB()
    for dx in (-1.35, 1.35):
        v, f = L.p_box_minmax(sx + dx - 0.85, sy - 0.20, z_terrace + 5.0,
                              sx + dx + 0.85, sy - 0.14, z_terrace + 6.7)
        mb.add(v, f, 0)
    v, f = L.p_box_minmax(sx - 2.35, sy - 0.20, z_terrace + 6.95,
                          sx + 2.35, sy - 0.14, z_terrace + 7.25)
    mb.add(v, f, 0)
    out.append(mb.to_object(PREFIX + "Quidditch_ScoreboardPanel", c,
                            [mats['lead']]))

    # ------------------------------------------------------- picket fence
    mb = L.MB()
    fy = cy - (try_ - 2.2)
    x_a, x_b = cx - 26.0, cx + 26.0
    nposts = 18
    for i in range(nposts + 1):
        px = x_a + (x_b - x_a) * i / nposts
        v, f = L.p_box_minmax(px - 0.09, fy - 0.09, z_terrace,
                              px + 0.09, fy + 0.09, z_terrace + 1.15)
        mb.add(v, f, 0)
    for zz in (z_terrace + 0.45, z_terrace + 0.95):
        v, f = L.p_box_minmax(x_a, fy - 0.06, zz - 0.07, x_b, fy + 0.06, zz + 0.07)
        mb.add(v, f, 0)
    for i in range(int((x_b - x_a) / 0.42)):
        px = x_a + 0.25 + 0.42 * i
        v, f = L.p_box_minmax(px - 0.055, fy - 0.045, z_terrace + 0.1,
                              px + 0.055, fy + 0.045, z_terrace + 1.05)
        mb.add(v, f, 0)
    out.append(mb.to_object(PREFIX + "Quidditch_Fence", c, [mats['wood']]))
    return out


# ============================================================ 3. gamekeeper
def build_hut(c, mats, rng):
    """Gamekeeper's cottage with a smoking chimney at the forest edge.

    The cottage is 5 m (X) x 7 m (Y); the ridge runs along Y so the gable
    ends face the camera side.  Everything is modelled in a local frame and
    then placed on the site.
    """
    out = []
    hx, hy = SITE_HUT
    half_x, half_y = 2.5, 3.5          # walls
    eave_h, gable_h = 2.60, 3.70

    corners = [(hx + sx * (half_x + 0.9), hy + sy * (half_y + 0.9))
               for sx in (-1, 1) for sy in (-1, 1)]
    z_pad = max(float(_tz(x, y)) for (x, y) in corners) + 0.12
    base = Matrix.Translation((hx, hy, z_pad))

    # a stone plinth so the cottage never floats on the slope
    mb = L.MB()
    n = 28
    top = _ellipse(hx, hy, z_pad, 3.7, 4.7, n)
    bxs = [hx + 4.2 * math.cos(TAU * i / n) for i in range(n)]
    bys = [hy + 5.2 * math.sin(TAU * i / n) for i in range(n)]
    bzs = _tz_many(bxs, bys)
    bot = [(bxs[i], bys[i], min(float(bzs[i]) - 1.0, z_pad - 1.2))
           for i in range(n)]
    mb.verts.extend(top)
    mb.verts.extend(bot)
    ct = len(mb.verts)
    mb.verts.append((hx, hy, z_pad))
    cb = len(mb.verts)
    mb.verts.append((hx, hy, min(b[2] for b in bot) - 0.4))
    for i in range(n):
        j = (i + 1) % n
        mb.faces.append((ct, i, j))
        mb.mats.append(0)
        mb.faces.append((cb, n + j, n + i))
        mb.mats.append(0)
        mb.faces.append((i, n + i, n + j, j))
        mb.mats.append(0)
    out.append(mb.to_object(PREFIX + "Hut_Plinth", c, [mats['stone']]))

    # --------------------------------------------------------- stone walls
    mb = L.MB()
    prof = [(-half_x, 0.0), (half_x, 0.0), (half_x, eave_h), (0.0, gable_h),
            (-half_x, eave_h)]
    v, f = L.p_prism(prof, -half_y, half_y)
    mb.add(v, f, 0)
    walls = mb.to_object(PREFIX + "Hut_Walls", c, [mats['stone_warm']])

    # door in the south gable, windows in the long walls
    mb = L.MB()
    v, f = L.p_box_minmax(0.55, -half_y - 0.5, 0.0, 1.65, -half_y + 0.6, 2.05)
    mb.add(v, f, 0)
    cut = mb.to_object(PREFIX + "Hut_DoorCut", c, None, fix_normals=False)
    _cut(walls, cut)

    mb = L.MB()
    v, f = L.p_box_minmax(half_x - 0.6, -0.70, 1.05, half_x + 0.5, 0.45, 2.10)
    mb.add(v, f, 0)
    cut = mb.to_object(PREFIX + "Hut_WinCut", c, None, fix_normals=False)
    _cut(walls, cut)

    mb = L.MB()
    v, f = L.p_box_minmax(-half_x - 0.5, -0.75, 1.55, -half_x + 0.6, -0.15, 2.45)
    mb.add(v, f, 0)
    cut = mb.to_object(PREFIX + "Hut_WinCut2", c, None, fix_normals=False)
    _cut(walls, cut)

    walls.matrix_world = base
    out.append(walls)

    # ------------------------------------------------------------- roof
    mb = L.MB()
    K.gable_roof(mb, 0.0, 0.0, half_x, half_y, eave_h, 4.10, 0,
                 thick=0.35, oh=0.35, oh_len=0.40)
    roof = mb.to_object(PREFIX + "Hut_Roof", c, [mats['slate']])
    roof.matrix_world = base
    out.append(roof)

    # --------------------------------------------------------- chimney
    mb = L.MB()
    v, f = L.p_box_minmax(-1.95, 2.75, 0.0, -0.85, 3.70, 5.30)
    mb.add(v, f, 0)
    v, f = L.p_box_minmax(-2.10, 2.60, 5.30, -0.70, 3.85, 5.62)
    mb.add(v, f, 0)
    v, f = L.p_box_minmax(-1.75, 2.80, 5.62, -1.05, 3.65, 5.80)
    mb.add(v, f, 0)
    chim = mb.to_object(PREFIX + "Hut_Chimney", c, [mats['stone']])
    chim.matrix_world = base
    out.append(chim)

    # -------------------------------------------------------- door & frame
    mb = L.MB()
    v, f = L.p_box_minmax(0.60, -half_y - 0.12, 0.0, 1.60, -half_y - 0.02, 2.02)
    mb.add(v, f, 0)
    door = mb.to_object(PREFIX + "Hut_Door", c, [mats['wood_dark']])
    door.matrix_world = base
    out.append(door)

    mb = L.MB()
    for dx in (0.48, 1.72):
        v, f = L.p_box_minmax(dx - 0.12, -half_y - 0.22, 0.0, dx + 0.12,
                              -half_y + 0.04, 2.22)
        mb.add(v, f, 0)
    v, f = L.p_box_minmax(0.48, -half_y - 0.22, 2.10, 1.72, -half_y + 0.04, 2.22)
    mb.add(v, f, 0)
    v, f = L.p_box_minmax(half_x - 0.08, -0.85, 0.95, half_x + 0.08, 0.60, 2.20)
    mb.add(v, f, 0)
    v, f = L.p_box_minmax(half_x - 0.08, -0.85, 0.95, half_x + 0.08, -0.70, 1.10)
    mb.add(v, f, 0)
    v, f = L.p_box_minmax(half_x - 0.08, 0.45, 0.95, half_x + 0.08, 0.60, 1.10)
    mb.add(v, f, 0)
    frames = mb.to_object(PREFIX + "Hut_Frames", c, [mats['wood']])
    frames.matrix_world = base
    out.append(frames)

    # ------------------------------------------------------ lit window
    mb = L.MB()
    v, f = L.p_box_minmax(half_x - 0.30, -0.65, 1.10, half_x - 0.22, 0.40, 2.05)
    mb.add(v, f, 0)
    gl = mb.to_object(PREFIX + "Hut_WindowGlass", c, [mats['hut_glass']])
    gl.matrix_world = base
    out.append(gl)

    mb = L.MB()
    v, f = L.p_box_minmax(-half_x + 0.22, -0.70, 1.60, -half_x + 0.30, -0.20, 2.40)
    mb.add(v, f, 0)
    gl2 = mb.to_object(PREFIX + "Hut_WindowGlass2", c, [mats['glass']])
    gl2.matrix_world = base
    out.append(gl2)

    # door lantern
    mb = L.MB()
    v, f = L.p_box_minmax(1.78, -half_y - 0.22, 1.85, 2.01, -half_y + 0.00, 2.20)
    mb.add(v, f, 0)
    lamp = mb.to_object(PREFIX + "Hut_Lantern", c, [mats['lantern']])
    lamp.matrix_world = base
    out.append(lamp)

    # --------------------------------------------------------- lean-to
    lx, ly = hx + half_x + 1.7, hy - 0.6
    lgz = _tz(lx, ly)
    mb = L.MB()
    for dx in (-1.4, 1.4):
        for dy in (-1.2, 1.2):
            v, f = L.p_box_minmax(dx - 0.10, dy - 0.10, 0.0, dx + 0.10,
                                  dy + 0.10, 2.15)
            mb.add(v, f, 0)
    v, f = L.p_box_minmax(-1.75, -1.5, 2.05, 1.75, 1.5, 2.20)
    mb.add(v, f, 0)
    lean = mb.to_object(PREFIX + "Hut_LeantoFrame", c, [mats['bark']])
    lean.matrix_world = Matrix.Translation((lx, ly, lgz - 0.15))
    out.append(lean)

    mb = L.MB()
    v, f = L.p_box_minmax(-1.8, -1.55, 2.08, 1.8, 1.55, 2.26)
    mb.add(v, f, 0)
    lroof = mb.to_object(PREFIX + "Hut_LeantoRoof", c, [mats['slate']])
    lroof.matrix_world = Matrix.Translation((lx, ly, lgz - 0.15))
    out.append(lroof)

    # stacked logs
    mb = L.MB()
    for row in range(4):
        for col in range(6 - row):
            lxx = -1.05 + col * 0.42 + row * 0.21
            lzz = 0.22 + row * 0.36
            v, f = L.p_cyl(0.19, 2.2, 8, z0=0.0)
            mb.add(v, f, 0, Matrix.Translation((lxx, 0.0, lzz))
                   @ Matrix.Rotation(math.pi * .5, 4, 'X'))
    logs = mb.to_object(PREFIX + "Hut_Woodpile", c, [mats['bark']])
    logs.matrix_world = Matrix.Translation((lx, ly, lgz - 0.15))
    out.append(logs)

    # ----------------------------------------------------------- kennel
    kx, ky = hx + half_x + 2.6, hy + 2.2
    kgz = _tz(kx, ky)
    mb = L.MB()
    v, f = L.p_box_minmax(-0.75, -0.65, 0.0, 0.75, 0.65, 0.10)
    mb.add(v, f, 0)                                     # floor
    v, f = L.p_box_minmax(-0.75, 0.53, 0.10, 0.75, 0.65, 1.05)
    mb.add(v, f, 0)                                     # back wall
    v, f = L.p_box_minmax(-0.75, -0.65, 0.10, -0.63, 0.65, 1.05)
    mb.add(v, f, 0)                                     # left wall
    v, f = L.p_box_minmax(0.63, -0.65, 0.10, 0.75, 0.65, 1.05)
    mb.add(v, f, 0)                                     # right wall
    v, f = L.p_box_minmax(-0.75, -0.65, 0.10, -0.42, -0.53, 1.05)
    mb.add(v, f, 0)                                     # front pier, left
    v, f = L.p_box_minmax(0.42, -0.65, 0.10, 0.75, -0.53, 1.05)
    mb.add(v, f, 0)                                     # front pier, right
    v, f = L.p_box_minmax(-0.42, -0.65, 0.78, 0.42, -0.53, 1.05)
    mb.add(v, f, 0)                                     # lintel over the doorway
    kennel = mb.to_object(PREFIX + "Hut_Kennel", c, [mats['wood']])
    kennel.matrix_world = Matrix.Translation((kx, ky, kgz - 0.10))
    out.append(kennel)

    mb = L.MB()
    _slab(mb, -0.95, 0.0, 1.05, 1.45, -0.85, 0.85, 0)
    _slab(mb, 0.0, 0.95, 1.45, 1.05, -0.85, 0.85, 0)
    kroof = mb.to_object(PREFIX + "Hut_KennelRoof", c, [mats['slate']])
    kroof.matrix_world = Matrix.Translation((kx, ky, kgz - 0.10))
    out.append(kroof)

    # ------------------------------------------------------------ fence
    mb = L.MB()
    fpts = [(hx - 6.5, hy - 6.0), (hx + 6.5, hy - 6.0), (hx + 6.5, hy + 1.0)]
    for (ax, ay), (bx2, by2) in zip(fpts[:-1], fpts[1:]):
        n = int(math.hypot(bx2 - ax, by2 - ay) / 2.4) + 1
        posts = []
        for i in range(n + 1):
            t = i / n
            px = ax + (bx2 - ax) * t
            py = ay + (by2 - ay) * t
            pz = _tz(px, py)
            posts.append((px, py, pz))
            v, f = L.p_box_minmax(px - 0.09, py - 0.09, pz - 0.3,
                                  px + 0.09, py + 0.09, pz + 1.25)
            mb.add(v, f, 0)
        # rails follow the ground, bay by bay
        for i in range(len(posts) - 1):
            p0, p1 = posts[i], posts[i + 1]
            for zz in (0.45, 0.95):
                zr = min(p0[2], p1[2]) + zz
                v, f = L.p_box_minmax(min(p0[0], p1[0]), min(p0[1], p1[1]) - 0.05,
                                      zr - 0.07, max(p0[0], p1[0]),
                                      max(p0[1], p1[1]) + 0.05, zr + 0.07)
                mb.add(v, f, 0)
    out.append(mb.to_object(PREFIX + "Hut_Fence", c, [mats['wood']]))

    # ----------------------------------------------------------- smoke
    smoke_base = z_pad + 5.80
    smoke_top = smoke_base + 9.0
    drift = (-2.6, 1.4)
    sx0, sy0 = hx - 1.40, hy + 3.25
    mb = L.MB()
    nring, nseg = 12, 10
    for ri in range(nring + 1):
        t = ri / nring
        z = smoke_base + (smoke_top - smoke_base) * t
        ccx = sx0 + drift[0] * (t ** 1.7)
        ccy = sy0 + drift[1] * (t ** 1.7)
        rr = 0.30 + 1.55 * (t ** 0.8)
        for k in range(nseg):
            a = TAU * k / nseg
            wob = 1.0 + 0.18 * math.sin(a * 3.0 + t * 5.0)
            mb.verts.append((ccx + rr * wob * math.cos(a),
                             ccy + rr * wob * math.sin(a), z))
    for ri in range(nring):
        for k in range(nseg):
            k2 = (k + 1) % nseg
            a = ri * nseg
            b = (ri + 1) * nseg
            mb.faces.append((a + k, a + k2, b + k2, b + k))
            mb.mats.append(0)
    c0 = len(mb.verts)
    mb.verts.append((sx0, sy0, smoke_base))
    c1 = len(mb.verts)
    mb.verts.append((sx0 + drift[0], sy0 + drift[1], smoke_top))
    for k in range(nseg):
        k2 = (k + 1) % nseg
        mb.faces.append((c0, k2, k))
        mb.mats.append(0)
        mb.faces.append((c1, nring * nseg + k, nring * nseg + k2))
        mb.mats.append(0)
    smoke_mat = build_smoke_material(smoke_base, smoke_top, density=0.80)
    out.append(mb.to_object(PREFIX + "Hut_Smoke", c, [smoke_mat]))
    return out


# ======================================================== 4. standing stones
def _menhir(v, f, m, h, w, d, rng):
    """One weathered standing stone as a closed faceted solid (origin at base)."""
    n = 6
    levels = [0.0, 0.18, 0.48, 0.78, 1.0]
    rings = []
    for t in levels:
        rx = w * (1.0 - 0.52 * t) * rng.uniform(0.88, 1.12)
        ry = d * (1.0 - 0.40 * t) * rng.uniform(0.88, 1.12)
        ring = []
        for i in range(n):
            a = TAU * i / n + rng.uniform(-0.30, 0.30)
            k = rng.uniform(0.80, 1.20)
            zz = h * t + (rng.uniform(-0.06, 0.06) * h if 0 < t < 1 else 0.0)
            ring.append((rx * k * math.cos(a), ry * k * math.sin(a), zz))
        rings.append(ring)
    base = len(v)
    for ring in rings:
        v.extend(ring)
    for ri in range(len(rings) - 1):
        for i in range(n):
            j = (i + 1) % n
            a = base + ri * n
            b = base + (ri + 1) * n
            f.append((a + i, a + j, b + j, b + i))
            m.append(0)
    cb = len(v)
    v.append((0.0, 0.0, -0.12 * h))
    for i in range(n):
        j = (i + 1) % n
        f.append((cb, base + j, base + i))
        m.append(0)
    ct = len(v)
    v.append((0.0, 0.0, h * 1.02))
    top = base + (len(rings) - 1) * n
    for i in range(n):
        j = (i + 1) % n
        f.append((ct, top + i, top + j))
        m.append(0)


def build_stone_circle(c, mats, rng):
    """Eleven weathered menhirs in a ring, one fallen stone, rubble at the feet."""
    out = []
    cx, cy = SITE_STONES
    ring_r = 7.5
    n_stones = 11
    a_off = rng.uniform(0.0, TAU)

    mb = L.MB()
    for i in range(n_stones):
        a = a_off + TAU * i / n_stones + rng.uniform(-0.055, 0.055)
        rr = ring_r + rng.uniform(-0.55, 0.55)
        sx = cx + rr * math.cos(a)
        sy = cy + rr * math.sin(a)
        h = rng.uniform(2.2, 4.6)
        w = rng.uniform(0.75, 1.35)
        d = rng.uniform(0.48, 0.85)
        tilt = math.radians(rng.uniform(1.5, 8.0))
        az = a + rng.uniform(-0.6, 0.6)
        gz = _tz(sx, sy)
        v, f, m = [], [], []
        _menhir(v, f, m, h, w, d, rng)
        mb.add(v, f, 0, L.M((sx, sy, gz - 0.35), (tilt, 0.0, az)))
    out.append(mb.to_object(PREFIX + "StoneCircle_Menhirs", c, [mats['rock']]))

    # the fallen stone, lying flat beside the ring
    mb = L.MB()
    fx = cx + 3.1
    fy = cy - 4.2
    fz = _tz(fx, fy)
    v, f, m = [], [], []
    _menhir(v, f, m, 3.6, 1.05, 0.62, rng)
    mb.add(v, f, 0, L.M((fx, fy, fz + 0.30),
                        (math.pi * .5, 0.0, rng.uniform(0, TAU))))
    out.append(mb.to_object(PREFIX + "StoneCircle_Fallen", c, [mats['rock']]))

    # rubble scatter at the foot of every stone
    mb = L.MB()
    rubble = []
    for i in range(n_stones):
        a = a_off + TAU * i / n_stones + rng.uniform(-0.055, 0.055)
        rr = ring_r + rng.uniform(-0.55, 0.55)
        sx = cx + rr * math.cos(a)
        sy = cy + rr * math.sin(a)
        for _ in range(rng.randint(5, 8)):
            ra = rng.uniform(0.0, TAU)
            dd = rng.uniform(0.4, 1.5)
            rubble.append((sx + dd * math.cos(ra), sy + dd * math.sin(ra),
                           rng.uniform(0.16, 0.42), rng.uniform(0, TAU),
                           rng.uniform(-0.4, 0.4)))
    if rubble:
        pzs = _tz_many([r[0] for r in rubble], [r[1] for r in rubble])
        for (px, py, s, rot, tilt), pz in zip(rubble, pzs):
            v, f = _boulder(s * 1.3, s * 1.1, s * 0.72, rng)
            mb.add(v, f, 0, Matrix.Translation((px, py, float(pz) + s * 0.25))
                   @ Matrix.Rotation(rot, 4, 'Z')
                   @ Matrix.Rotation(tilt, 4, 'X'))
    out.append(mb.to_object(PREFIX + "StoneCircle_Rubble", c, [mats['rock']]))
    return out


# ====================================================== 5. covered bridge
def build_bridge(c, mats, rng):
    """Timber covered bridge over a gully crossed by PATH_MAIN.

    The deck ramps from z = 40.6 on the north bank down to z = 33.0 on the
    south bank; the gully floor below is at z = 30.7, i.e. a real drop of
    ~6.9 m under the north end of the span.
    """
    out = []
    bx = BRIDGE_X
    y0, y1 = BRIDGE_Y0, BRIDGE_Y1
    z0, z1 = BRIDGE_Z0, BRIDGE_Z1
    dy, dz = y1 - y0, z1 - z0
    span = math.hypot(dy, dz)
    theta = math.atan2(dz, dy)          # local +Y runs down the span
    base = Matrix.Translation((bx, y0, z0)) @ Matrix.Rotation(theta, 4, 'X')

    # -------------------------------------------------------- stone abutments
    for i, (yy, zz) in enumerate(((y0 - 3.0, z0), (y1 + 3.0, z1))):
        mb = L.MB()
        gz = _tz(bx, yy)
        top = zz - 0.25
        # the abutment reaches under the deck end so nothing is left floating
        by0, by1 = ((yy - 2.6, y0 + 0.4) if i == 0 else (y1 - 0.4, yy + 2.6))
        v, f = L.p_box_minmax(bx - 5.0, by0, gz - 3.0, bx + 5.0, by1, top)
        mb.add(v, f, 0)
        ya = yy - 3.0 if i == 0 else yy        # wing walls splay into the bank
        yb = yy if i == 0 else yy + 3.0
        for sgn in (-1, 1):
            v, f = L.p_box_minmax(bx + sgn * 4.4, min(ya, yb), gz - 2.0,
                                  bx + sgn * 5.6, max(ya, yb), top)
            mb.add(v, f, 0)
        out.append(mb.to_object(PREFIX + "Bridge_Abutment_%d" % (i + 1), c,
                                [mats['stone']]))

    # -------------------------------------------------- timber superstructure
    mb = L.MB()
    deck_w = 3.60
    for sx in (-1.45, 1.45):
        v, f = L.p_box_minmax(sx - 0.16, 0.0, -0.62, sx + 0.16, span, -0.22)
        mb.add(v, f, 0)
    nb = int(span / 1.6) + 1
    for i in range(nb):
        yy = span * i / (nb - 1.0)
        v, f = L.p_box_minmax(-deck_w * .5, yy - 0.14, -0.86,
                              deck_w * .5, yy + 0.14, -0.60)
        mb.add(v, f, 0)
    npk = int(span / 0.34)
    for i in range(npk):
        yy = span * (i + 0.5) / npk
        v, f = L.p_box_minmax(-deck_w * .5, yy - 0.145, -0.22,
                              deck_w * .5, yy + 0.145, 0.0)
        mb.add(v, f, 1)
    npost = int(span / 1.5) + 1
    for i in range(npost):
        yy = span * i / (npost - 1.0)
        for sx in (-deck_w * .5 + 0.10, deck_w * .5 - 0.10):
            v, f = L.p_box_minmax(sx - 0.07, yy - 0.07, 0.0, sx + 0.07,
                                  yy + 0.07, 1.05)
            mb.add(v, f, 0)
    for sx in (-deck_w * .5 + 0.10, deck_w * .5 - 0.10):
        v, f = L.p_box_minmax(sx - 0.07, 0.0, 0.92, sx + 0.07, span, 1.06)
        mb.add(v, f, 0)
        v, f = L.p_box_minmax(sx - 0.05, 0.0, 0.44, sx + 0.05, span, 0.56)
        mb.add(v, f, 0)
    for i in range(5):
        yy = span * i / 4.0
        for sx in (-2.30, 2.30):
            v, f = L.p_box_minmax(sx - 0.10, yy - 0.10, 0.0, sx + 0.10,
                                  yy + 0.10, 2.35)
            mb.add(v, f, 0)
    for sx in (-2.30, 2.30):
        v, f = L.p_box_minmax(sx - 0.10, 0.0, 2.25, sx + 0.10, span, 2.45)
        mb.add(v, f, 0)
    v, f = L.p_box_minmax(-2.30, 0.0, 2.30, 2.30, span, 2.48)
    mb.add(v, f, 0)
    timber = mb.to_object(PREFIX + "Bridge_Timber", c, [mats['bark'], mats['wood']])
    timber.matrix_world = base
    out.append(timber)

    # ------------------------------------------------------------- roof
    mb = L.MB()
    ridge_x, eave_x = 0.0, 2.62
    eave_z, ridge_z = 2.40, 3.55
    _slab(mb, -eave_x, ridge_x, eave_z, ridge_z, -0.45, span + 0.45, 0)
    _slab(mb, ridge_x, eave_x, ridge_z, eave_z, -0.45, span + 0.45, 0)
    v, f = L.p_box_minmax(-0.13, -0.45, ridge_z - 0.10, 0.13, span + 0.45,
                          ridge_z + 0.16)
    mb.add(v, f, 0)
    roof = mb.to_object(PREFIX + "Bridge_Roof", c, [mats['slate']])
    roof.matrix_world = base
    out.append(roof)

    # ------------------------------------------------- approach causeways
    mb = L.MB()
    segs = []
    for (ya, yb) in ((y0 - 14.0, y0 - 1.0), (y1 + 1.0, y1 + 14.0)):
        n = int(abs(yb - ya) / 2.0) + 1
        for i in range(n):
            t0 = ya + (yb - ya) * i / n
            t1 = ya + (yb - ya) * (i + 1) / n
            segs.append((t0, t1))
    zs = _tz_many([bx] * (2 * len(segs)),
                   [v for (t0, t1) in segs for v in (t0, t1)])
    for k, (t0, t1) in enumerate(segs):
        za = float(zs[2 * k])
        zb = float(zs[2 * k + 1])
        # the causeway narrows as it climbs into the hillside
        hw = 2.4 - 0.9 * float(N.smoothstep(0.0, 1.0,
                                            min(abs(t0 - y0), abs(t1 - y0)) / 13.0))
        v, f = L.p_box_minmax(bx - hw, min(t0, t1), min(za, zb) - 3.0,
                              bx + hw, max(t0, t1), max(za, zb) + 0.10)
        mb.add(v, f, 0)
    out.append(mb.to_object(PREFIX + "Bridge_Approach", c, [mats['stone']]))
    return out


# ==================================================== 6. distant railway viaduct
def build_viaduct(c, mats, rng):
    """A tall, narrow multi-arch railway viaduct far away on the west moor."""
    out = []
    x0, y0 = VIA_X0, VIA_Y
    n_arch = VIA_ARCHES
    pitch = VIA_LENGTH / n_arch
    span = pitch * 0.72
    pier_w = (pitch - span) * 0.5
    deck_w = VIA_DECK_W

    ground = [_tz(x0 + i * pitch, y0) for i in range(n_arch + 1)]
    gmax = max(ground)
    spring = gmax - 2.0                     # arch springing line
    crown = spring + span * 0.62
    deck_z = crown + 3.60
    spandrel_top = deck_z - 2.40

    # ------------------------------------------------------- piers + spandrel
    mb = L.MB()
    for i in range(n_arch + 1):
        px = x0 + i * pitch
        gz = ground[i]
        v, f = L.p_box_minmax(px - pier_w * .5, y0 - deck_w * .40,
                              gz - 3.0, px + pier_w * .5, y0 + deck_w * .40,
                              spandrel_top)
        mb.add(v, f, 0)
        v, f = L.p_box_minmax(px - pier_w * .72, y0 - deck_w * .46,
                              spandrel_top, px + pier_w * .72, y0 + deck_w * .46,
                              spandrel_top + 0.9)
        mb.add(v, f, 0)
    for i in range(n_arch):
        ax = x0 + i * pitch + pier_w * .5 - 0.05
        bx = x0 + (i + 1) * pitch - pier_w * .5 + 0.05
        prof = _arch_spandrel_profile(ax, bx, spandrel_top, spring, crown, 12)
        v, f = L.p_prism(prof, y0 - deck_w * .395, y0 + deck_w * .395)
        mb.add(v, f, 0)
    out.append(mb.to_object(PREFIX + "Viaduct_Arcade", c, [mats['stone']]))

    # ------------------------------------------------------------- deck
    mb = L.MB()
    xa, xb = x0 - 6.0, x0 + VIA_LENGTH + 6.0
    v, f = L.p_box_minmax(xa, y0 - deck_w * .5, spandrel_top + 0.9,
                          xb, y0 + deck_w * .5, deck_z)
    mb.add(v, f, 0)
    for sgn in (-1, 1):
        ya = y0 + sgn * deck_w * .5 - (0.45 if sgn > 0 else 0.0)
        yb = y0 + sgn * deck_w * .5 + (0.0 if sgn > 0 else 0.45)
        v, f = L.p_box_minmax(xa, min(ya, yb), deck_z, xb, max(ya, yb),
                              deck_z + 1.15)
        mb.add(v, f, 0)
    out.append(mb.to_object(PREFIX + "Viaduct_Deck", c, [mats['stone']]))

    # ballast and rails
    mb = L.MB()
    v, f = L.p_box_minmax(xa + 1.0, y0 - 1.9, deck_z, xb - 1.0, y0 + 1.9,
                          deck_z + 0.30)
    mb.add(v, f, 0)
    out.append(mb.to_object(PREFIX + "Viaduct_Ballast", c, [mats['rock']]))

    mb = L.MB()
    for sy in (-0.72, 0.72):
        v, f = L.p_box_minmax(xa + 1.0, y0 + sy - 0.08, deck_z + 0.30,
                              xb - 1.0, y0 + sy + 0.08, deck_z + 0.48)
        mb.add(v, f, 0)
    out.append(mb.to_object(PREFIX + "Viaduct_Rails", c, [mats['lead']]))

    # ------------------------------------------------------- end embankments
    mb = L.MB()
    seg, nseg = 9.0, 8
    for (ex, sgn) in ((xa, -1.0), (xb, 1.0)):
        gz_end = _tz(ex + sgn * seg * nseg, y0)
        for i in range(nseg):
            xs0 = ex + sgn * seg * i
            xs1 = ex + sgn * seg * (i + 1)
            gz = min(_tz(xs0, y0), _tz(xs1, y0))
            t = (i + 1) / float(nseg)
            top = (deck_z + 0.9) + (gz_end + 0.4 - (deck_z + 0.9)) * t
            w = deck_w * (0.5 + 0.55 * t)
            v, f = L.p_box_minmax(min(xs0, xs1), y0 - w, min(gz, top) - 3.0,
                                  max(xs0, xs1), y0 + w, top)
            mb.add(v, f, 0)
    out.append(mb.to_object(PREFIX + "Viaduct_Embankment", c, [mats['stone']]))
    return out


# ==================================================================== 7. jetty
def build_jetty(c, mats, rng):
    """A small timber jetty at the boathouse waterline, with a moored punt.

    It is the foreground anchor of the hero shot: a lit lantern at the head
    of the pier, its reflection in the black water, and the punt's pale
    gunwale catching the moon.
    """
    out = []
    x0 = C.BOAT_X - 15.0          # just west of the boathouse door
    y_root = C.BOAT_Y - 12.0
    y_tip = y_root - 24.0
    z_deck = 1.55
    half = 1.65
    # --- deck planks ---
    mb = L.MB()
    n_plank = 26
    for i in range(n_plank):
        y0 = y_root + (y_tip - y_root) * i / n_plank
        y1 = y_root + (y_tip - y_root) * (i + 1) / n_plank
        v, f = L.p_box_minmax(x0 - half, y0 + 0.02, z_deck,
                              x0 + half, y1 - 0.02, z_deck + 0.11)
        mb.add(v, f, 0)
    # stringers under the deck
    for sx in (-1, 1):
        v, f = L.p_box_minmax(x0 + sx * (half - 0.18), y_tip, z_deck - 0.30,
                              x0 + sx * (half - 0.18) + 0.16, y_root,
                              z_deck - 0.02)
        mb.add(v, f, 0)
    out.append(mb.to_object(PREFIX + "Jetty_Deck", c, [mats['wood']]))

    # --- piles and cross bracing ---
    mb = L.MB()
    for i in range(8):
        y = y_root - 3.0 * i
        for sx in (-1, 1):
            px = x0 + sx * (half - 0.22)
            v, f = L.p_cyl(0.19, 6.4, 8, z0=-3.4)
            mb.add(v, f, 0, Matrix.Translation((px, y, 0.0)))
        # cross brace
        v, f = L.p_box_minmax(x0 - half + 0.2, y - 0.09, z_deck - 1.15,
                              x0 + half - 0.2, y + 0.09, z_deck - 0.95)
        mb.add(v, f, 0)
    out.append(mb.to_object(PREFIX + "Jetty_Piles", c, [mats['wood_dark']]))

    # --- lantern post at the head of the pier ---
    mb = L.MB()
    v, f = L.p_cyl(0.10, 3.1, 8, z0=z_deck)
    mb.add(v, f, 0, Matrix.Translation((x0, y_tip + 0.4, 0.0)))
    out.append(mb.to_object(PREFIX + "Jetty_Post", c, [mats['wood_dark']]))
    mb = L.MB()
    v, f = L.p_cyl(0.055, 0.46, 8, z0=0.0)
    mb.add(v, f, 0, Matrix.Translation((x0, y_tip + 0.4, z_deck + 2.72)))
    v, f = L.p_cyl(0.24, 0.10, 8, z0=0.0)
    mb.add(v, f, 0, Matrix.Translation((x0, y_tip + 0.4, z_deck + 3.16)))
    out.append(mb.to_object(PREFIX + "Jetty_Lantern", c, [mats['lantern']]))

    # --- a moored punt, pulled up alongside ---
    mb = L.MB()
    bl, bw = 5.4, 1.05
    bx, by = x0 + half + 1.25, y_tip + 6.0
    rings = 9
    prof = []
    for i in range(rings):
        t = i / (rings - 1.0)
        # pointed at both ends, fullest amidships
        w = bw * (math.sin(math.pi * t) ** 0.62)
        prof.append((bx, by - bl * .5 + bl * t, w))
    verts = []
    for (px, py, w) in prof:
        seg = 9
        for k in range(seg):
            a = math.pi * k / (seg - 1.0)
            verts.append((px + w * math.cos(a), py, 0.10 + 1.05 * math.sin(a)))
    mb.verts.extend(verts)
    stride = 9
    for i in range(rings - 1):
        for k in range(stride - 1):
            a0 = i * stride + k
            mb.faces.append((a0, a0 + 1, a0 + stride + 1, a0 + stride))
            mb.mats.append(0)
    out.append(mb.to_object(PREFIX + "Jetty_Punt", c, [mats['wood']]))
    # gunwale / thwart
    mb = L.MB()
    for (px, py, w) in (prof[1], prof[rings // 2], prof[rings - 2]):
        v, f = L.p_box_minmax(px - w * 0.92, py - 0.09, 1.12,
                              px + w * 0.92, py + 0.09, 1.24)
        mb.add(v, f, 0)
    out.append(mb.to_object(PREFIX + "Jetty_Punt_Thwart", c, [mats['wood_dark']]))
    return out


# ==================================================================== 8. rowboat
def build_rowboat(c, mats, rng):
    """A clinker-built rowing boat moored alongside the boathouse jetty.

    The boathouse's boat door is nine metres tall, so a seven-metre boat at
    its foot is the scale cue that tells the eye how big the building is --
    and it gives the black water something to reflect and something to
    break its mirror.

    The hull is a real double shell (outer skin, inner skin, gunwale rails
    and end plates), lofted from a sheer line and a rounded-V section, with
    lapstrake planks modelled as proud ridges so the silhouette is that of a
    clinker boat rather than a smooth dinghy.
    """
    LOA = 6.9          # length overall
    BEAM = 2.05        # beam
    NS, NA = 17, 7     # stations along the hull, samples per half-section
    M = 2 * NA - 2     # points per station ring
    cx = C.BOAT_X + 4.9
    cy = C.BOAT_Y - 20.0
    z0 = 0.18            # keel below the waterline
    NLAP = 5           # clinker planks a side
    out = []

    def station(t):
        w = 0.5 * BEAM * (0.04 + 0.96 * math.sin(math.pi * t) ** 0.80)
        d = 0.54 * (math.sin(math.pi * t) ** 0.28) + 0.045
        sh = 0.24 + 0.46 * ((2.0 * t - 1.0) ** 2)      # sheer: high at the ends
        return w, d, sh

    def sect(w, d, sh, a):
        s = abs(a)
        return (w * math.sin(s * math.pi * 0.5),
                -d * math.cos(s * math.pi * 0.5) + sh * (s ** 2))

    def ring(t, inner):
        w, d, sh = station(t)
        pts = []
        for k in range(M + 1):
            a = (k / float(M)) * 2.0 - 1.0
            x, z = sect(w, d, sh, a)
            if a < 0.0:
                x = -x                       # mirror to port
            if inner:
                x *= 0.90
                z = (-d + 0.055) + (z + d) * 0.90
            pts.append((x, z))
        return pts

    def ypos(t):
        return cy + LOA * 0.5 - LOA * t

    # ---------------- hull ----------------
    mb = L.MB()
    outer, inner = [], []
    for i in range(NS):
        t = i / (NS - 1.0)
        outer.append(ring(t, False))
        inner.append(ring(t, True))
    base = len(mb.verts)
    for i in range(NS):
        yy = ypos(i / (NS - 1.0))
        for (x, z) in outer[i]:
            mb.verts.append((cx + x, yy, z0 + z))
    for i in range(NS):
        yy = ypos(i / (NS - 1.0))
        for (x, z) in inner[i]:
            mb.verts.append((cx + x, yy, z0 + z))

    def o(i, k):
        return base + i * (M + 1) + k

    def n(i, k):
        return base + NS * (M + 1) + i * (M + 1) + k

    for i in range(NS - 1):
        for k in range(M):
            mb.faces.append((o(i, k), o(i, k + 1), o(i + 1, k + 1), o(i + 1, k)))
            mb.mats.append(0)
            mb.faces.append((n(i, k), n(i + 1, k), n(i + 1, k + 1), n(i, k + 1)))
            mb.mats.append(0)
        mb.faces.append((o(i, 0), o(i + 1, 0), n(i + 1, 0), n(i, 0)))   # port rail
        mb.mats.append(0)
        mb.faces.append((o(i, M), n(i, M), n(i + 1, M), o(i + 1, M)))   # stbd rail
        mb.mats.append(0)

    # end plates: a fan from the section centre closes the stem and the stern
    for i_end in (0, NS - 1):
        yy = ypos(0.0 if i_end == 0 else 1.0)
        c1 = len(mb.verts)
        mb.verts.append((cx, yy, z0 + 0.035))
        c2 = len(mb.verts)
        mb.verts.append((cx, yy, z0 + 0.090))
        for k in range(M):
            mb.faces.append((c1, o(i_end, k), o(i_end, k + 1)))
            mb.mats.append(0)
            mb.faces.append((c2, n(i_end, k + 1), n(i_end, k)))
            mb.mats.append(0)
            mb.faces.append((o(i_end, k), n(i_end, k), n(i_end, k + 1),
                             o(i_end, k + 1)))
            mb.mats.append(0)
    out.append(mb.to_object(PREFIX + "Rowboat_Hull", c, [mats['wood']]))

    # ---------------- lapstrake planks ----------------
    mb = L.MB()
    a_lo, a_hi = 0.05, 0.97
    step = (a_hi - a_lo) / NLAP
    for sg in (1, -1):
        for j in range(NLAP):
            a0 = a_lo + j * step
            prof = ((a0, 0.000), (a0 + 0.018, 0.021), (a0 + 0.052, 0.021),
                    (a0 + 0.070, 0.000))
            rows = []
            for (aa, off) in prof:
                row = []
                for i in range(NS):
                    t = i / (NS - 1.0)
                    w, d, sh = station(t)
                    x, z = sect(w, d, sh, aa)
                    row.append((cx + sg * (x + off), ypos(t), z0 + z))
                rows.append(row)
            vbase = len(mb.verts)
            for row in rows:
                mb.verts.extend(row)
            W = NS
            for r in range(len(prof) - 1):
                for i in range(NS - 1):
                    a0v = vbase + r * W + i
                    mb.faces.append((a0v, a0v + 1, a0v + W + 1, a0v + W))
                    mb.mats.append(0)
    out.append(mb.to_object(PREFIX + "Rowboat_Laps", c, [mats['wood_dark']]))

    # ---------------- gunwale rail, thwarts and oars ----------------
    mb = L.MB()
    for sg in (1, -1):
        for i in range(NS - 1):
            t = i / (NS - 1.0)
            w, d, sh = station(t)
            x, z = sect(w, d, sh, 1.0)
            v, f = L.p_box_minmax(min(cx + sg * x, cx + sg * (x + 0.05)),
                                  ypos(t + 1.0 / (NS - 1.0)), z0 + z - 0.055,
                                  max(cx + sg * x, cx + sg * (x + 0.05)),
                                  ypos(t), z0 + z + 0.035)
            mb.add(v, f, 0)
    # thwarts
    for tt in (0.30, 0.50, 0.70):
        w, d, sh = station(tt)
        v, f = L.p_box_minmax(cx - w * 0.97, ypos(tt) - 0.11, z0 + sh - 0.30,
                              cx + w * 0.97, ypos(tt) + 0.11, z0 + sh - 0.22)
        mb.add(v, f, 0)
    # two oars stowed fore-and-aft inside the gunwales
    for sg in (1, -1):
        t = 0.52
        w, d, sh = station(t)
        x = sg * w * 0.62
        v, f = L.p_box_minmax(cx + x - 0.035, ypos(0.18), z0 + sh - 0.20,
                              cx + x + 0.035, ypos(0.86), z0 + sh - 0.13)
        mb.add(v, f, 0)
        # blade
        v, f = L.p_box_minmax(cx + x - 0.075, ypos(0.08), z0 + sh - 0.215,
                              cx + x + 0.075, ypos(0.19), z0 + sh - 0.115)
        mb.add(v, f, 0)
    out.append(mb.to_object(PREFIX + "Rowboat_Fittings", c, [mats['wood_dark']]))

    # ---------------- bow lantern ----------------
    mb = L.MB()
    v, f = L.p_cyl(0.035, 0.30, 6, z0=0.0)
    mb.add(v, f, 0, Matrix.Translation((cx, ypos(0.02), z0 + 0.70)))
    out.append(mb.to_object(PREFIX + "Rowboat_LanternPost", c, [mats['wood_dark']]))
    mb = L.MB()
    v, f = L.p_cyl(0.115, 0.26, 8, z0=0.0)
    mb.add(v, f, 0, Matrix.Translation((cx, ypos(0.02), z0 + 1.00)))
    v, f = L.p_cyl(0.145, 0.06, 8, z0=0.0)
    mb.add(v, f, 0, Matrix.Translation((cx, ypos(0.02), z0 + 1.24)))
    out.append(mb.to_object(PREFIX + "Rowboat_Lantern", c, [mats['lantern']]))
    return out


# ==================================================================== driver
def main():
    c = L.coll(COLL_NAME)
    _purge_props()
    rng = random.Random(SEED)
    mats = build_materials()
    made = []
    made += build_owlery(c, mats, rng)
    made += build_quidditch(c, mats, rng)
    made += build_hut(c, mats, rng)
    made += build_stone_circle(c, mats, rng)
    made += build_bridge(c, mats, rng)
    made += build_viaduct(c, mats, rng)
    made += build_jetty(c, mats, rng)
    made += build_rowboat(c, mats, rng)
    faces = sum(len(o.data.polygons) for o in made if o.type == 'MESH')
    groups = {}
    for o in made:
        key = o.name.replace(PREFIX, "").split("_")[0]
        groups[key] = groups.get(key, 0) + 1
    summary = {
        "objects": len(made),
        "faces": faces,
        "collection": COLL_NAME,
        "groups": groups,
    }
    print("props built:", summary)
    return summary


if __name__ == "__main__":
    main()
