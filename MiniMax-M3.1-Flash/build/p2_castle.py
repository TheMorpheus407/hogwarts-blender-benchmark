"""PASS 2 — the castle architecture: walls, towers, halls, viaduct, stair."""
import bpy, math, importlib, sys, os
import numpy as np
from mathutils import Vector, Matrix

BUILD = "/home/morpheus/Documents/Morpheus-Produktion/Benchmarks/Blender/MiniMax-M3.1-Flash/build"
if BUILD not in sys.path:
    sys.path.insert(0, BUILD)

import hg_lib, hg_np, hg_mat, hg_cfg, hg_land, hg_castle
for m in (hg_lib, hg_np, hg_mat, hg_cfg, hg_land, hg_castle):
    importlib.reload(m)
import hg_lib as L
import hg_cfg as C
import hg_castle as K
import hg_np as N

P = C.PLATEAU_Z

# material slots (filled by main())
STONE = SLATE = VERD = LEAD = GLASS = WOOD = WOOD_D = LANTERN = GOLD = ROCK = None
STONE_STAIR = None
CLOCKFACE = None
PAVING = BRICK = GHGLASS = None
c_cast = c_win = None
WIN = None


# --------------------------------------------------------------------- helpers
def wall(c, name, cx, cy, length, z0, height, nx, ny, thickness=1.1,
         bays=0, win_w=2.2, win_h=7.0, sill=9.0, per_bay=2, kind='lancet',
         style='lancet', profile=None, mat=None, win_off=0.0, win_sill=None,
         extra_frames=None):
    """A straight wall panel with cut window openings.  nx,ny = outward normal."""
    mat = mat if mat is not None else STONE
    phi = math.atan2(-nx, ny)
    if profile is None:
        profile = [(-length * .5, 0.0), (length * .5, 0.0),
                   (length * .5, height), (-length * .5, height)]
    mb = L.MB()
    mb.add(*L.p_prism(profile, 0.0, -thickness), mat=0)
    wall_obj = mb.to_object(name, c, [mat], fix_normals=False)
    frame = Matrix.Translation((cx, cy, z0)) @ Matrix.Rotation(phi, 4, 'Z')
    wall_obj.matrix_world = frame

    frames = []
    if bays:
        s = sill if win_sill is None else win_sill
        bw = length / bays
        for b in range(bays):
            ctr = -length * .5 + bw * (b + 0.5)
            if per_bay == 1:
                offs = [ctr]
            else:
                d = min(bw * 0.26, win_w * 1.3)
                offs = [ctr - d, ctr + d]
            for o in offs:
                frames.append(dict(matrix=K.fmat(o + win_off, s), kind=kind,
                                   w=win_w, h=win_h, style=style))
    if extra_frames:
        frames.extend(extra_frames)
    if frames:
        cmb = L.MB()
        WIN.cutters(cmb, frames, parent=frame)
        cut = cmb.to_object(name + "_cut", c, None, fix_normals=False)
        # identity matrix on purpose -- cutters() bakes world space already
        L.boolean_cut(wall_obj, cut)
        WIN.place(frames, name, parent=frame)
    return wall_obj


def cornice(mb, cx, cy, hx, hy, z, out, mat, h=0.9):
    v, f = L.p_box_minmax(-hx - out, -hy - out, z, hx + out, hy + out, z + h)
    mb.add(v, f, mat, Matrix.Translation((cx, cy, 0.0)))


def crenellated_box(mb, cx, cy, hx, hy, z, mat, h=2.4, merlon_w=1.6, gap=1.4,
                    depth=0.7):
    """Crenellated parapet around a rectangular roof edge."""
    n = max(2, int((hx * 2) / (merlon_w + gap)))
    step = (hx * 2) / n
    for i in range(n):
        if i % 2:
            continue
        x = -hx + step * (i + 0.5)
        for sgn in (-1, 1):
            v, f = L.p_box_minmax(x - merlon_w * .5, sgn * hy - (depth if sgn > 0 else 0.0),
                                  z, x + merlon_w * .5, sgn * hy + (0.0 if sgn > 0 else depth),
                                  z + h)
            mb.add(v, f, mat, Matrix.Translation((cx, cy, 0.0)))
    m = max(2, int((hy * 2) / (merlon_w + gap)))
    step = (hy * 2) / m
    for i in range(m):
        if i % 2:
            continue
        y = -hy + step * (i + 0.5)
        for sgn in (-1, 1):
            v, f = L.p_box_minmax(sgn * hx - (depth if sgn > 0 else 0.0), y - merlon_w * .5,
                                  z, sgn * hx + (0.0 if sgn > 0 else depth), y + merlon_w * .5,
                                  z + h)
            mb.add(v, f, mat, Matrix.Translation((cx, cy, 0.0)))


def round_tower(c, name, cx, cy, r, z0, h, win_rows, mat=None, roof='conical',
                roof_h=None, crown='crenel', nseg=40, tap=0.0, mat_roof=None,
                mat_cap=None):
    """A round tower: shaft with windows, cornice, parapet and crown."""
    mat = mat if mat is not None else STONE
    mat_roof = mat_roof if mat_roof is not None else SLATE
    mb = L.MB()
    r2 = r * (1.0 - tap)
    v, f = L.p_cyl(r, h, nseg, r2=r2, z0=z0)
    mb.add(v, f, 0)
    v, f = L.p_cyl(r + 0.9, 2.4, nseg, z0=z0 - 1.2)
    mb.add(v, f, 0)
    obj = mb.to_object(name, c, [mat], fix_normals=False)
    frame = Matrix.Translation((cx, cy, 0.0))
    obj.matrix_world = frame

    frames = []
    for (wz, nwin, ww, wh, st) in win_rows:
        if nwin <= 0:
            continue
        for i in range(nwin):
            a = math.pi * 2 * i / nwin + 0.26
            rr = r + (r2 - r) * (wz / h)
            frames.append(dict(matrix=K.fmat(0.0, z0 + wz, a, rr), kind='lancet',
                               w=ww, h=wh, style=st))
    if frames:
        cmb = L.MB()
        WIN.cutters(cmb, frames, parent=frame)
        cut = cmb.to_object(name + "_cut", c, None, fix_normals=False)
        # identity matrix on purpose -- cutters() bakes world space already
        L.boolean_cut(obj, cut)
        WIN.place(frames, name, parent=frame)

    mb = L.MB()
    ztop = z0 + h
    v, f = L.p_cyl(r2 + 0.9, 1.7, nseg, z0=ztop - 1.4)
    mb.add(v, f, 0)
    K.corbel_ring(mb, r2 + 0.7, ztop - 1.4, max(10, nseg // 2), 1.0, 1.6, 0)
    if crown == 'crenel':
        K.crenellation(mb, r2 + 0.2, ztop + 0.3, max(12, nseg // 2), 1.7, 2.3,
                       0.8, 0)
        if roof == 'conical':
            K.conical_cap(mb, r2 + 0.9, ztop + 2.7, roof_h or (r * 2.2), nseg, 1,
                          fin_mat=1)
    elif crown == 'battlement':
        v, f = L.p_cyl(r2 + 0.9, 1.7, nseg, z0=ztop + 0.3)
        mb.add(v, f, 0)
        K.crenellation(mb, r2 + 0.9, ztop + 2.0, max(12, nseg // 2), 1.9, 2.5,
                       0.9, 0)
        if roof == 'conical':
            K.conical_cap(mb, r2 + 1.0, ztop + 4.6, roof_h or (r * 2.4), nseg, 1,
                          fin_mat=1)
    cap = mb.to_object(name + "_crown", c, [mat, mat_roof], fix_normals=False)
    cap.matrix_world = frame
    L.smooth(cap, 40)
    return obj


def square_tower(c, name, cx, cy, hx, hy, z0, h, tiers, mat=None, roof='spire',
                 roof_h=None, mat_roof=None, pinnacles=0, win_w=2.0, win_h=5.6):
    """A square/rectangular tower with tiered windows."""
    mat = mat if mat is not None else STONE
    mat_roof = mat_roof if mat_roof is not None else SLATE
    sides = (('S', 0, -1, cx, cy - hy, hx * 2), ('N', 0, 1, cx, cy + hy, hx * 2),
             ('W', -1, 0, cx - hx, cy, hy * 2), ('E', 1, 0, cx + hx, cy, hy * 2))
    for (side, nx, ny, wx, wy, length) in sides:
        frames = []
        for (sill, cnt, ww, wh, st, kind) in tiers:
            if cnt <= 0:
                continue
            for k in range(cnt):
                off = -length * .5 + length * (k + 0.5) / cnt
                frames.append(dict(matrix=K.fmat(off, sill), kind=kind, w=ww,
                                   h=wh, style=st))
        wall(c_cast, "%s_%s" % (name, side), wx, wy, length, z0, h, nx, ny,
             thickness=1.2, mat=mat, extra_frames=frames)

    mb = L.MB()
    cornice(mb, 0, 0, hx, hy, z0 + h, 0.7, 0)
    if roof == 'flat':
        crenellated_box(mb, 0, 0, hx, hy, z0 + h + 0.9, 0)
    cap = mb.to_object(name + "_cap", c, [mat, mat_roof], fix_normals=False)
    cap.matrix_world = Matrix.Translation((cx, cy, 0.0))
    if pinnacles:
        pm = L.MB()
        for (px, py) in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
            K.pinnacle(pm, 1.7, 0.0, 9.0, 0, 4, fin_mat=1)
        po = pm.to_object(name + "_pinnacles", c, [mat, mat_roof])
        po.matrix_world = Matrix.Translation((cx, cy, z0 + h + 0.9))
    if roof == 'spire':
        mb = L.MB()
        K.conical_cap(mb, max(hx, hy) * 1.10, z0 + h + 0.9, roof_h or 24.0, 8, 1,
                      fin_mat=1, collar=1.4)
        so = mb.to_object(name + "_spire", c, [mat_roof])
        so.matrix_world = Matrix.Translation((cx, cy, 0.0))
        L.smooth(so, 40)
    elif roof == 'gable':
        mb = L.MB()
        K.gable_roof(mb, cx, cy, hx + 0.8, hy + 0.8, z0 + h + 0.9,
                     z0 + h + (roof_h or 14.0), 0)
        mb.to_object(name + "_roof", c, [mat_roof])
    return True


# ------------------------------------------------------------------ buildings
def great_hall():
    """The Great Hall: long gabled hall, lancet bays, stepped buttresses, turrets."""
    cx, cy = C.GH_CX, C.GH_CY
    hx, hy = C.GH_W * .5, C.GH_L * .5
    z0 = P - 2.0
    wall_h = C.GH_WALL_H
    gable_h = C.GH_RIDGE_H
    ztop = z0 + wall_h
    bays = 10

    for side, nx, ny, wx, wy in (('W', -1, 0, cx - hx, cy), ('E', 1, 0, cx + hx, cy)):
        wall(c_cast, "Hall_%s" % side, wx, wy, hy * 2, z0, wall_h, nx, ny,
             thickness=1.4, bays=bays, win_w=2.7, win_h=13.0, sill=9.0,
             per_bay=2, kind='lancet', style='lancet')
        mb = L.MB()
        for b in range(bays):
            bx = -hy + (hy * 2 / bays) * (b + 0.5)
            K.buttress(mb, bx, 0.0, z0, wall_h * 0.92, 2.8, 3.6, 0,
                       rot=0.0, steps=3, pinnacle_h=7.5, p_mat=0)
        bo = mb.to_object("Hall_%s_buttress" % side, c_cast, [STONE])
        bo.matrix_world = Matrix.Translation((wx, wy, 0.0)) @ \
            Matrix.Rotation(math.atan2(-nx, ny), 4, 'Z')
        mb = L.MB()
        cornice(mb, 0, 0, 0.75, hy, ztop - 1.4, 0.55, 0)
        so = mb.to_object("Hall_%s_cornice" % side, c_cast, [STONE])
        so.matrix_world = Matrix.Translation((wx, wy, 0.0)) @ \
            Matrix.Rotation(math.atan2(-nx, ny), 4, 'Z')

    for side, nx, ny, wx, wy, sgn in (('S', 0, -1, cx, cy - hy, -1),
                                      ('N', 0, 1, cx, cy + hy, 1)):
        prof = K.gable_wall_profile(hx, wall_h, gable_h)
        frame = Matrix.Translation((wx, wy, z0)) @ Matrix.Rotation(math.atan2(-nx, ny), 4, 'Z')
        fr = [dict(matrix=K.fmat(0.0, wall_h * 0.34), kind='rose', w=7.0, h=7.0,
                   style='rose'),
              dict(matrix=K.fmat(-hx * 0.62, 6.0), kind='lancet', w=2.2, h=7.0,
                   style='lancet'),
              dict(matrix=K.fmat(hx * 0.62, 6.0), kind='lancet', w=2.2, h=7.0,
                   style='lancet')]
        wall(c_cast, "Hall_%s" % side, wx, wy, hx * 2, z0, wall_h, nx, ny,
             thickness=1.4, profile=prof, extra_frames=fr)
        for sx in (-1, 1):
            tx = cx + sx * (hx - 1.4)
            ty = wy + sgn * 1.2
            round_tower(c_cast, "Hall_%s_turret%d" % (side, sx), tx, ty, 3.7,
                        z0, wall_h + 13.0,
                        [(7.0, 3, 1.5, 4.2, 'single'), (19.0, 3, 1.3, 3.4, 'single')],
                        roof='conical', roof_h=13.0, crown='crenel', nseg=20)

    mb = L.MB()
    K.gable_roof(mb, cx, cy, hx, hy, ztop, z0 + gable_h, 0, thick=0.7)
    ro = mb.to_object("Hall_roof", c_cast, [SLATE])
    mb = L.MB()
    v, f = L.p_box_minmax(cx - 0.9, cy - hy, z0 + gable_h - 0.3,
                          cx + 0.9, cy + hy, z0 + gable_h + 0.9)
    mb.add(v, f, 0)
    for yy in (-hy + 5, 0.0, hy - 5):
        v, f = L.p_cyl(0.24, 3.4, 6, z0=z0 + gable_h + 0.9)
        mb.add(v, f, 0, Matrix.Translation((cx, yy, 0.0)))
        v, f = L.p_sphere(0.42, 8, 6, z0=z0 + gable_h + 3.6)
        mb.add(v, f, 0, Matrix.Translation((cx, yy, 0.0)))
    mb.to_object("Hall_roof_crest", c_cast, [LEAD])
    mb = L.MB()
    for i in range(9):
        yy = cy - hy + 8 + (hy * 2 - 16) * i / 8.0
        zz = z0 + wall_h + (gable_h - wall_h) * 0.40
        for sx in (-1, 1):
            # the dormers sit on the hall's own roof -- they were previously
            # built around x=0 and floated free over the courtyard
            dx = cx + sx * (hx * 0.56)
            v, f = L.p_box_minmax(dx - 1.7, yy - 1.4, zz - 1.2,
                                  dx + 1.7, yy + 1.4, zz + 3.6)
            mb.add(v, f, 0)
    mb.to_object("Hall_dormers", c_cast, [STONE])


def main_spire():
    """The tallest structure: a layered central tower with attendant turrets."""
    cx, cy = C.T_MAIN
    r = 15.5
    z0 = P - 2.0
    drum = 40.0
    mb = L.MB()
    v, f = L.p_cyl(r, drum, 24, z0=z0)
    mb.add(v, f, 0)
    obj = mb.to_object("Spire_drum", c_cast, [STONE], fix_normals=False)
    frame = Matrix.Translation((cx, cy, 0.0))
    obj.matrix_world = frame

    frames = []
    for (wz, nwin, ww, wh, st) in ((7.0, 12, 2.3, 8.4, 'lancet'),
                                   (21.0, 12, 1.8, 5.6, 'single')):
        for i in range(nwin):
            a = math.pi * 2 * i / nwin + 0.26
            frames.append(dict(matrix=K.fmat(0.0, z0 + wz, a, r), kind='lancet',
                               w=ww, h=wh, style=st))
    cmb = L.MB()
    WIN.cutters(cmb, frames, parent=frame)
    cut = cmb.to_object("Spire_cut", c_cast, None)
    # identity matrix on purpose -- cutters() bakes world space already
    L.boolean_cut(obj, cut)
    WIN.place(frames, "Spire", parent=frame)

    mb = L.MB()
    zt = z0 + drum
    v, f = L.p_cyl(r + 1.7, 2.3, 24, z0=zt - 1.3)
    mb.add(v, f, 0)
    K.corbel_ring(mb, r + 1.5, zt - 1.3, 16, 1.2, 1.9, 0)
    v, f = L.p_cyl(r * 0.88, 1.4, 24, z0=zt + 1.0)
    mb.add(v, f, 0)
    v, f = L.p_cone(r * 0.86, 92.0, 8, z0=zt + 2.4)
    mb.add(v, f, 1)
    v, f = L.p_cyl(0.5, 2.2, 8, z0=zt + 92.0)
    mb.add(v, f, 1)
    v, f = L.p_sphere(0.95, 12, 8, z0=zt + 93.8)
    mb.add(v, f, 1)
    v, f = L.p_cyl(0.2, 8.5, 6, z0=zt + 93.0)
    mb.add(v, f, 1)
    cap = mb.to_object("Spire_crown", c_cast, [STONE, SLATE], fix_normals=False)
    cap.matrix_world = frame
    L.smooth(cap, 40)

    for i in range(4):
        a = math.pi * .25 + math.pi * .5 * i
        tx = cx + math.cos(a) * (r + 1.4)
        ty = cy + math.sin(a) * (r + 1.4)
        round_tower(c_cast, "Spire_turret%d" % i, tx, ty, 3.4, zt - 17.0, 23.0,
                    [(6.0, 3, 1.4, 4.0, 'single')], roof='conical', roof_h=15.0,
                    crown='crenel', nseg=16)


def clock_tower():
    """Clock tower with readable dials and a belfry."""
    cx, cy = C.T_CLOCK
    z0 = P - 2.0
    h = 38.0
    tiers = [(7.0, 2, 2.5, 8.4, 'lancet', 'lancet'),
             (20.0, 2, 2.3, 6.4, 'lancet', 'lancet')]
    square_tower(c_cast, "Clock", cx, cy, 9.5, 9.5, z0, h, tiers,
                 roof='spire', roof_h=48.0, pinnacles=1)

    # belfry openings just under the eaves
    for (nx, ny) in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        phi = math.atan2(-nx, ny)
        frame = Matrix.Translation((cx, cy, 0.0)) @ Matrix.Rotation(phi, 4, 'Z') @ \
            Matrix.Translation((nx * 9.5, ny * 9.5, 0.0))
        fr = [dict(matrix=K.fmat(k, z0 + h - 8.0), kind='lancet', w=2.6, h=5.6,
                   style='single') for k in (-3.0, 3.0)]
        cmb = L.MB()
        WIN.cutters(cmb, fr, parent=frame)
        cut = cmb.to_object("Clock_belfry_cut", c_cast, None)
        # identity matrix on purpose -- cutters() bakes world space already
        side = {(-1, 0): 'W', (1, 0): 'E', (0, -1): 'S', (0, 1): 'N'}[(nx, ny)]
        tgt = bpy.data.objects.get("Clock_%s" % side)
        if tgt:
            L.boolean_cut(tgt, cut)
        WIN.place(fr, "Clock_belfry", parent=frame)

    # clock dials
    zz = z0 + h - 15.0
    for (nx, ny) in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        phi = math.atan2(-nx, ny)
        mb = L.MB()
        v, f = L.p_cyl(4.4, 0.55, 36, z0=0.0)
        mb.add(v, f, 0, Matrix.Translation((0, 0.25, 0)) @ Matrix.Rotation(math.pi / 2, 4, 'X'))
        # A raised collar round the plate so the dial is not a bare disc.
        # It has to be a RING: a plain cylinder here is a solid disc that
        # sits in front of the clock face and hides it completely.
        ro = L.circle_points(4.95, 0.0, 36)
        ri = L.circle_points(4.38, 0.0, 36)
        v, f = L.p_band(ro, ri, 0.25, 0.62)
        mb.add(v, f, 1)
        # Hour marks: slender bars lying along the radius, the quarters
        # longer and wider than the rest, the way a real dial is cut.
        for k in range(12):
            a = math.pi * 2 * k / 12
            quarter = (k % 3 == 0)
            ln = 1.05 if quarter else 0.66
            wd = 0.50 if quarter else 0.32
            v, f = L.p_box_minmax(-ln * 0.5, -0.13, -wd * 0.5,
                                  ln * 0.5, 0.13, wd * 0.5)
            mb.add(v, f, 1, Matrix.Translation((math.sin(a) * 3.62, 0.60,
                                                math.cos(a) * 3.62))
                   @ Matrix.Rotation(a - math.pi * 0.5, 4, 'Y'))
        v, f = L.p_box_minmax(-0.24, -0.12, -0.10, 0.24, 0.12, 2.6)
        mb.add(v, f, 1, Matrix.Translation((0, 0.62, 0)) @ Matrix.Rotation(math.radians(38), 4, 'Y'))
        v, f = L.p_box_minmax(-0.20, -0.12, -0.10, 0.20, 0.12, 3.7)
        mb.add(v, f, 1, Matrix.Translation((0, 0.64, 0)) @ Matrix.Rotation(math.radians(-100), 4, 'Y'))
        # the boss the hands turn on
        v, f = L.p_cyl(0.34, 0.22, 16, z0=0.0)
        mb.add(v, f, 1, Matrix.Translation((0, 0.60, 0))
               @ Matrix.Rotation(-math.pi / 2, 4, 'X'))
        o = mb.to_object("Clock_dial", c_cast, [CLOCKFACE, LEAD])
        o.matrix_world = Matrix.Translation((cx + nx * 9.7, cy + ny * 9.7, zz)) @ \
            Matrix.Rotation(phi, 4, 'Z')


def ranges_and_towers():
    """Ranges and the tower group."""
    z0 = P - 2.0

    def block(tag, cx, cy, hx, hy, h, bays, ww, wh, sill, ridge, per_bay=2):
        for (side, nx, ny, wx, wy, length) in (
                ('S', 0, -1, cx, cy - hy, hx * 2), ('N', 0, 1, cx, cy + hy, hx * 2),
                ('W', -1, 0, cx - hx, cy, hy * 2), ('E', 1, 0, cx + hx, cy, hy * 2)):
            wall(c_cast, "%s_%s" % (tag, side), wx, wy, length, z0, h, nx, ny,
                 thickness=1.2, bays=bays, win_w=ww, win_h=wh, sill=sill,
                 per_bay=per_bay)
        mb = L.MB()
        K.gable_roof(mb, cx, cy, hx, hy, z0 + h, z0 + h + ridge, 0)
        mb.to_object("%s_roof" % tag, c_cast, [SLATE])

    block("North", -10.0, 44.0, 24.0, 17.0, 26.0, 6, 2.0, 6.2, 8.0, 15.0)
    block("East", 52.0, -24.0, 17.0, 13.0, 24.0, 5, 1.9, 5.6, 7.5, 13.0)
    block("West", -34.0, -36.0, 16.0, 15.0, 21.0, 5, 1.8, 5.2, 7.0, 12.0)
    block("South", 12.0, -54.0, 20.0, 10.0, 18.0, 6, 1.8, 5.0, 6.0, 10.0)

    round_tower(c_cast, "TowerE_A", C.T_EAST_A[0], C.T_EAST_A[1], 9.8, z0, 33.0,
                [(6.0, 8, 1.9, 6.0, 'lancet'), (17.0, 8, 1.5, 4.2, 'single'),
                 (25.0, 8, 1.4, 3.6, 'single')],
                roof='conical', roof_h=27.0, crown='crenel', nseg=32)
    square_tower(c_cast, "TowerE_B", C.T_EAST_B[0], C.T_EAST_B[1], 7.5, 7.5, z0, 27.0,
                 [(6.0, 2, 1.9, 6.0, 'lancet', 'lancet'),
                  (16.0, 2, 1.7, 5.0, 'lancet', 'lancet')],
                 roof='spire', roof_h=30.0, pinnacles=1)
    round_tower(c_cast, "TowerE_C", C.T_EAST_C[0], C.T_EAST_C[1], 7.2, z0, 24.0,
                [(5.0, 7, 1.7, 5.2, 'lancet'), (15.0, 7, 1.4, 3.8, 'single')],
                roof='conical', roof_h=20.0, crown='crenel', nseg=24)
    square_tower(c_cast, "TowerE_D", C.T_EAST_D[0], C.T_EAST_D[1], 4.8, 4.8, z0, 17.0,
                 [(5.0, 2, 1.6, 5.0, 'lancet', 'lancet')], roof='flat', pinnacles=1)
    for i, (gx, gy) in enumerate((C.T_GATE_A, C.T_GATE_B)):
        round_tower(c_cast, "Gate%d" % i, gx, gy, 5.6, z0 - 1.0, 27.0,
                    [(6.0, 5, 1.6, 5.0, 'lancet'), (16.0, 5, 1.4, 3.6, 'single')],
                    roof='conical', roof_h=19.0, crown='crenel', nseg=20)
    for (sx, sy, sr, sh) in ((-33.0, -14.0, 3.6, 20.0), (16.0, -14.0, 3.4, 18.0),
                              (36.0, -12.0, 3.2, 17.0), (70.0, -12.0, 3.4, 18.0),
                              (-34.0, 26.0, 3.6, 19.0), (14.0, 26.0, 3.4, 18.0),
                              (-6.0, -66.0, 3.2, 16.0), (34.0, -42.0, 3.0, 15.0)):
        round_tower(c_cast, "Turret_%d_%d" % (int(sx), int(sy)), sx, sy, sr, z0, sh,
                    [(5.0, 5, 1.4, 4.2, 'single'), (12.0, 5, 1.2, 3.2, 'single')],
                    roof='conical', roof_h=11.0, crown='crenel', nseg=16)


def viaduct():
    """The grand viaduct: a pointed arcade on tall piers across the gorge.

    Built WITHOUT booleans.  The spandrel is one extruded ribbon whose
    lower edge follows the arcade profile -- the arch head over every bay,
    a flat impost course over every pier -- while the piers are solid blocks
    standing from the gorge floor up to that impost line.  The result is a
    closed manifold of quads with no coplanar faces, so nothing can
    z-fight and nothing can come out non-manifold.
    """
    hw = C.VIA_DECK_W * .5
    x0 = C.VIA_X0
    n = C.VIA_ARCHES
    span = C.VIA_SPAN
    pier = C.VIA_PIER
    deck_z = P
    zbot = C.GORGE_FLOOR_Z - 6.0
    spring = C.VIA_SPRING
    rise = C.VIA_RISE
    d = hw * 0.88                    # half depth of the spandrel wall
    a = span * 0.5
    pitch = span + pier
    y = C.VIA_Y

    # ---- the arcade profile -------------------------------------------
    # NB: the first arch's springing point IS (x0, spring), so the profile
    # must not be seeded with that point as well -- a repeated vertex makes
    # a degenerate quad and a zero-area face.
    lower = []
    arches = []
    for k in range(n):
        A = x0 + a + k * pitch
        pts = L.lancet_points(span, spring, rise, 22)
        arches.append((A, pts))
        for (lx, lz) in pts:
            lower.append((A + lx, lz))
    x_end = lower[-1][0]
    upper = [(px, deck_z - 0.8) for (px, _pz) in lower]

    mb = L.MB()
    v, f = L.p_strip(lower, upper, y - d, y + d)
    mb.add(v, f, 0)

    # ---- piers ----------------------------------------------------------
    for k in range(1, n):
        cxp = x0 - pier * .5 + k * pitch
        # shaft, slightly proud of the spandrel wall
        v, f = L.p_box_minmax(cxp - pier * .5, y - d - 0.32, zbot,
                              cxp + pier * .5, y + d + 0.32, spring + 0.6)
        mb.add(v, f, 0)
        # splayed base
        v, f = L.p_box_minmax(cxp - pier * .5 - 1.0, y - d - 1.15, zbot,
                              cxp + pier * .5 + 1.0, y + d + 1.15, zbot + 8.0)
        mb.add(v, f, 0)
        # impost band the arch springs from
        v, f = L.p_box_minmax(cxp - pier * .5 - 0.6, y - d - 0.58, spring - 1.2,
                              cxp + pier * .5 + 0.6, y + d + 0.58, spring + 1.2)
        mb.add(v, f, 0)

    # ---- abutments ------------------------------------------------------
    for (xa, xb) in ((x0 - 13.0, x0), (x_end, x_end + 13.0)):
        v, f = L.p_box_minmax(xa, y - d - 0.32, zbot, xb, y + d + 0.32,
                              deck_z - 0.6)
        mb.add(v, f, 0)

    # ---- arch rings (voussoirs), proud of the wall on both faces --------
    cc = (rise * rise - a * a) / (2.0 * a)      # two-centred arch offset
    for (A, pts) in arches:
        inner = []
        outer = []
        for (lx, lz) in pts:
            s = 1.0 if lx >= 0.0 else -1.0
            nx = lx + s * cc
            nz = lz - spring
            ll = math.hypot(nx, nz)
            inner.append((A + lx, lz))
            outer.append((A + lx + nx / ll * 1.5, lz + nz / ll * 1.5))
        for (ya, yb) in ((d - 0.30, d + 0.32), (-d - 0.32, -d + 0.30)):
            v, f = L.p_strip(inner, outer, y + ya, y + yb)
            mb.add(v, f, 0)

    # ---- cornice, deck, parapet ----------------------------------------
    v, f = L.p_box_minmax(x0 - 13.0, y - d - 0.30, deck_z - 2.1,
                          x_end + 13.0, y + d + 0.30, deck_z - 1.3)
    mb.add(v, f, 0)
    v, f = L.p_box_minmax(x0 - 13.0, y - hw, deck_z - 1.8,
                          x_end + 13.0, y + hw, deck_z + 0.7)
    mb.add(v, f, 0)
    for sgn in (-1, 1):
        y0 = sgn * hw - (0.6 if sgn > 0 else 0.0)
        y1 = sgn * hw + (0.0 if sgn > 0 else 0.6)
        v, f = L.p_box_minmax(x0 - 13.0, min(y0, y1), deck_z + 0.7,
                              x_end + 13.0, max(y0, y1), deck_z + 2.3)
        mb.add(v, f, 0)
    # A darker stone for the viaduct: at the castle's own value the piers and
    # the parapet coping read as pale concrete and pulled the eye straight out
    # of the composition.
    stone_via = hg_mat.m_stone(name='M_StoneViaduct', tint=(0.50, 0.49, 0.47))
    obj = mb.to_object("Viaduct", c_cast, [stone_via])

    # ---- parapet lanterns ----------------------------------------------
    lamps = []
    for k in range(n + 1):
        lx = x0 - pier * .5 + k * pitch
        for sgn in (-1, 1):
            lamps.append((lx, y + sgn * (hw - 0.9)))
    mb = L.MB()
    for (lx, ly) in lamps:
        v, f = L.p_cyl(0.17, 3.3, 6, z0=deck_z + 2.3)
        mb.add(v, f, 0, Matrix.Translation((lx, ly, 0.0)))
        # An OPEN iron frame, not a solid box.  The glass cylinder used to be
        # sealed inside a closed block of lead, so every lamp read as a black
        # brick on a stick and the viaduct carried no warm light at all.
        for dx, dy in ((0.34, 0.34), (-0.34, 0.34), (0.34, -0.34), (-0.34, -0.34)):
            v, f = L.p_box_minmax(lx + dx - 0.045, ly + dy - 0.045,
                                  deck_z + 5.05, lx + dx + 0.045, ly + dy + 0.045,
                                  deck_z + 6.45)
            mb.add(v, f, 0)
        # conical hood and a base ring
        v, f = L.p_cone(0.52, 0.30, 6, z0=deck_z + 6.45)
        mb.add(v, f, 0, Matrix.Translation((lx, ly, 0.0)))
        v, f = L.p_cyl(0.42, 0.10, 6, z0=deck_z + 4.98)
        mb.add(v, f, 0, Matrix.Translation((lx, ly, 0.0)))
    o1 = mb.to_object("Viaduct_lanterns", c_cast, [LEAD])
    mb = L.MB()
    for (lx, ly) in lamps:
        v, f = L.p_cyl(0.26, 1.05, 8, z0=deck_z + 5.15)
        mb.add(v, f, 0, Matrix.Translation((lx, ly, 0.0)))
    o2 = mb.to_object("Viaduct_lamp_glass", c_cast, [LANTERN])
    return obj


def boathouse_and_stair():
    """Boathouse at the waterline plus the switchback stair up the cliff."""
    bx, by = C.BOAT_X, C.BOAT_Y
    z0 = -1.0
    h = 13.0
    hx, hy = 11.0, 8.0
    south = None
    for (side, nx, ny, wx, wy, length) in (
            ('S', 0, -1, bx, by - hy, hx * 2), ('N', 0, 1, bx, by + hy, hx * 2),
            ('W', -1, 0, bx - hx, by, hy * 2), ('E', 1, 0, bx + hx, by, hy * 2)):
        o = wall(c_cast, "Boathouse_%s" % side, wx, wy, length, z0, h, nx, ny,
                 thickness=0.9, bays=2, win_w=1.6, win_h=3.4, sill=5.0, per_bay=1)
        if side == 'S':
            south = o
    # The boat door has to hang in the SOUTH wall's own frame.  That wall is
    # rotated by pi (its outward normal points south), and a window unit's
    # local -y is "into the wall".  Placing the door in a plain translation
    # instead left the glass 0.3 m PROUD of the wall face and behind it the
    # glazing bars -- so the emissive pane hid its own tracery and the door
    # read as a flat slab of light.
    frame = south.matrix_world.copy()
    fr = [dict(matrix=K.fmat(0.0, 0.2), kind='lancet', w=6.0, h=9.0,
               style='greatdoor')]
    cmb = L.MB()
    WIN.cutters(cmb, fr, parent=frame)
    cut = cmb.to_object("Boathouse_cut", c_cast, None)
    # identity matrix on purpose -- cutters() bakes world space already
    tgt = bpy.data.objects.get("Boathouse_S")
    if tgt:
        L.boolean_cut(tgt, cut)
    doors = WIN.place(fr, "Boathouse_door", parent=frame)
    # The boat door is a 6 x 9 m opening.  A flat emissive pane at the
    # ordinary window strength blows out to a white slab, so it gets its own
    # glass -- graded from the lamp at the sill up into the dark of the
    # arch, the way a boat house doorway actually reads.
    door_glass = hg_mat.m_boathouse_glass('M_BoathouseGlass')
    for d in doors:
        d.data = d.data.copy()
        d.data.materials[0] = door_glass

    mb = L.MB()
    K.gable_roof(mb, bx, by, hx, hy, z0 + h, z0 + h + 7.5, 0)
    mb.to_object("Boathouse_roof", c_cast, [SLATE])
    mb = L.MB()
    v, f = L.p_box_minmax(bx - 3.2, by - hy - 15.0, 1.4, bx + 3.2, by - hy, 2.3)
    mb.add(v, f, 0)
    for i in range(7):
        xx = bx - 2.7 + 5.4 * (i / 6.0)
        yy = by - hy - 14.0 + 13.0 * (i / 6.0)
        v, f = L.p_cyl(0.24, 3.6, 6, z0=-2.2)
        mb.add(v, f, 0, Matrix.Translation((xx, yy, 0.0)))
    mb.to_object("Boathouse_jetty", c_cast, [WOOD_D])

    # a lantern at the head of the boathouse jetty: it lights the moored
    # boat and lays a warm streak across the black water in the foreground
    mb = L.MB()
    v, f = L.p_cyl(0.11, 3.4, 8, z0=0.0)
    mb.add(v, f, 0, Matrix.Translation((bx + 2.6, by - hy - 13.4, 2.3)))
    mb.to_object("Boathouse_jetty_post", c_cast, [WOOD_D])
    # A lantern, not a glowing cylinder: a small hot glass inside a dark
    # iron frame with a conical hood, so it reads as an object at close
    # range instead of a white blob pasted on the pier.
    mb = L.MB()
    v, f = L.p_cyl(0.185, 0.07, 8, z0=0.0)
    mb.add(v, f, 0, Matrix.Translation((bx + 2.6, by - hy - 13.4, 5.62)))
    v, f = L.p_cone(0.235, 0.20, 8, z0=0.0)
    mb.add(v, f, 0, Matrix.Translation((bx + 2.6, by - hy - 13.4, 6.26)))
    for dx, dy in ((0.15, 0.0), (-0.15, 0.0), (0.0, 0.15), (0.0, -0.15)):
        v, f = L.p_box_minmax(bx + 2.6 + dx - 0.022, by - hy - 13.4 + dy - 0.022,
                              5.66, bx + 2.6 + dx + 0.022, by - hy - 13.4 + dy + 0.022,
                              6.28)
        mb.add(v, f, 0)
    mb.to_object("Boathouse_jetty_lantern_frame", c_cast, [LEAD])
    mb = L.MB()
    v, f = L.p_cyl(0.135, 0.50, 8, z0=0.0)
    mb.add(v, f, 0, Matrix.Translation((bx + 2.6, by - hy - 13.4, 5.69)))
    mb.to_object("Boathouse_jetty_lantern", c_cast, [LANTERN])

    mb = L.MB()
    # ---------------------------------------------------------------------
    # The switchback stair.
    #
    # The crag mesh is *displaced* by tens of metres, so a stair laid out
    # against the undisplaced profile is swallowed by the rock half way up
    # (measured drift: up to 20 m).  Every station is therefore placed
    # against the REAL displaced cliff radius, and each flight is subdivided
    # so the ribbon follows the rock instead of cutting through it.
    #
    # The wall it climbs runs roughly east-west along the castle's
    # south-east flank, just east of the boathouse, from the waterline up
    # to the rim.  A flight runs *out* from the rock as it climbs and the
    # next runs back *in*, so the stair zig-zags between the cliff face and
    # a gallery standing four metres proud of it -- steep flights, not a
    # shallow ramp, and unmistakably a switchback.
    FLIGHTS = 9
    SUB = 8
    A_LO, A_HI = -47.5, -45.0      # bearing span of one flight
    DRIFT = 0.70                   # the stair creeps east as it climbs
    OFF_IN, OFF_OUT = 0.0, 4.6     # distance the gallery stands off the rock
    Z_LO, Z_HI = 2.5, 57.0
    INNER, OUTER = -3.4, 1.8       # deck edges relative to the station radius
    THICK = 1.1                    # slab thickness at the inner edge
    SKIRT = 1.3                    # extra depth at the outer edge

    def cliff_r(a_deg, z):
        T = np.array([[math.radians(a_deg)]])
        Z = np.array([[float(z)]])
        return float(hg_land.crag_radius(T, Z)[0, 0])

    def push_out(px, py, d):
        rr = math.hypot(px, py)
        s = (rr + d) / rr
        return (px * s, py * s)

    # ---- the path: (bearing, stand-off from the rock, height) ----
    path = []
    for f in range(FLIGHTS):
        a_lo = A_LO + DRIFT * f
        a_hi = A_HI + DRIFT * f
        z0 = Z_LO + (Z_HI - Z_LO) * f / FLIGHTS
        z1 = Z_LO + (Z_HI - Z_LO) * (f + 1) / FLIGHTS
        off0 = OFF_IN if f % 2 == 0 else OFF_OUT
        off1 = OFF_OUT if f % 2 == 0 else OFF_IN
        for s in range(SUB):
            t = s / float(SUB)
            path.append((a_lo + (a_hi - a_lo) * t,
                         off0 + (off1 - off0) * t,
                         z0 + (z1 - z0) * t))
    # a final short flight onto the rim
    a_end = A_HI + DRIFT * FLIGHTS
    path.append((a_end, OFF_IN, Z_HI + 3.0))

    ring = []
    for (a_deg, off, z) in path:
        a = math.radians(a_deg)
        r = cliff_r(a_deg, z) + off
        ring.append(((r + INNER) * math.cos(a), (r + INNER) * math.sin(a),
                     (r + OUTER) * math.cos(a), (r + OUTER) * math.sin(a), z))

    for i in range(len(ring) - 1):
        ax, ay, ax2, ay2, az = ring[i]
        bx, by, bx2, by2, bz = ring[i + 1]
        # Ribbon solid.  The section is a wedge, not a slab: thin where it is
        # keyed into the rock, deeper at the outer edge, so the stair reads as
        # a masonry gallery rather than a shelf floating in front of the rock.
        ai = (ax, ay, az - THICK)
        bo = (ax2, ay2, az - THICK - SKIRT)
        bi = (bx, by, bz - THICK)
        bo2 = (bx2, by2, bz - THICK - SKIRT)
        mb.add([(ax, ay, az), (ax2, ay2, az), (bx2, by2, bz), (bx, by, bz),
                ai, bo, bi, bo2],
               [(0, 1, 2, 3),          # walk surface
                (4, 7, 6, 5),          # soffit
                (1, 5, 7, 2),          # outer face
                (0, 4, 6, 3)], 0)      # inner face
        # parapet on the outer edge
        po = [(ax2, ay2, az), (bx2, by2, bz),
              (bx2, by2, bz + 1.35), (ax2, ay2, az + 1.35)]
        mb.add(po, [(0, 1, 2, 3)], 0)
        # step nosings
        n = max(1, int(abs(bz - az) * 2.2))
        for s in range(n):
            t = (s + 0.5) / n
            z = az + (bz - az) * t
            cxp = ax + (bx - ax) * t
            cyp = ay + (by - ay) * t
            oxp = ax2 + (bx2 - ax2) * t
            oyp = ay2 + (by2 - ay2) * t
            v = [(cxp, cyp, z + 0.26), (oxp, oyp, z + 0.26),
                 (oxp, oyp, z), (cxp, cyp, z)]
            mb.add(v, [(0, 1, 2, 3)], 0)

    # landings: a platform at each turn, where the stair doubles back
    for f in range(1, FLIGHTS):
        i = f * SUB
        ax, ay, ax2, ay2, az = ring[i]
        ax3, ay3 = push_out(ax, ay, 2.8)
        ax23, ay23 = push_out(ax2, ay2, 2.8)
        top = [(ax, ay, az), (ax2, ay2, az), (ax23, ay23, az), (ax3, ay3, az)]
        bot = [(ax, ay, az - THICK), (ax2, ay2, az - THICK - SKIRT),
               (ax23, ay23, az - THICK - SKIRT), (ax3, ay3, az - THICK - SKIRT)]
        mb.add(top + bot[::-1], [(0, 1, 2, 3), (7, 6, 5, 4),
                                 (0, 4, 5, 1), (1, 5, 6, 2),
                                 (2, 6, 7, 3), (3, 7, 4, 0)], 0)
    mb.to_object("Cliff_stair", c_cast, [STONE_STAIR])


def _prism_x(profile, x0, x1):
    """profile: [(y,z),...] polygon in the YZ plane, extruded along X."""
    n = len(profile)
    v = [(x0, p[0], p[1]) for p in profile] + [(x1, p[0], p[1]) for p in profile]
    f = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    f.append(tuple(range(n - 1, -1, -1)))
    f.append(tuple(range(n, 2 * n)))
    return v, f


def glasshouse(mb_brick, mb_stone, mb_glass, mb_lead, mb_wood, mtx, Lx, Dp,
               z0=0.0, chimney=True):
    """A Victorian glasshouse, built in a local frame.

    Local +X runs along the ridge, local +Y is the depth (outward from the
    cliff), the origin is the centre of the footprint and z0 is the terrace
    level.  Everything is placed through `mtx`, which stands the house on the
    terrace and turns it to follow the cliff line.
    """
    hx, hy = Lx * 0.5, Dp * 0.5
    WALL = 0.90      # brick dwarf wall
    COP = 1.04       # top of the coping
    EAVE = 3.60      # head of the vertical glazing
    RIDGE = 5.35     # ridge
    OH = 0.42        # eave overhang
    BAR = 0.105      # glazing bar
    GL = 0.05        # glass thickness
    DR = 0.62        # half width of the doorway
    DH = 2.35        # door head

    def bx(mb, x0, y0, zb, x1, y1, zt, mat=0):
        v, f = L.p_box_minmax(x0, y0, zb, x1, y1, zt)
        mb.add(v, f, mat, mtx)

    def slab_x(mb, prof, x0, x1, mat=0):
        v, f = _prism_x(prof, x0, x1)
        mb.add(v, f, mat, mtx)

    # ---- brick dwarf wall, broken by the doorway --------------------------
    for (y0, y1) in ((-hy, -hy + 0.28), (hy - 0.28, hy)):
        bx(mb_brick, -hx, y0, z0, hx, y1, z0 + WALL)
    bx(mb_brick, hx - 0.28, -hy, z0, hx, hy, z0 + WALL)
    bx(mb_brick, -hx, -hy, z0, -hx + 0.28, -DR, z0 + WALL)
    bx(mb_brick, -hx, DR, z0, -hx + 0.28, hy, z0 + WALL)

    # ---- stone coping, overhanging the dwarf wall -------------------------
    for (y0, y1) in ((-hy - 0.05, -hy + 0.33), (hy - 0.33, hy + 0.05)):
        bx(mb_stone, -hx - 0.05, y0, z0 + WALL, hx + 0.05, y1, z0 + COP)
    bx(mb_stone, hx - 0.33, -hy - 0.05, z0 + WALL, hx + 0.05, hy + 0.05, z0 + COP)
    bx(mb_stone, -hx - 0.05, -hy - 0.05, z0 + WALL, -hx + 0.33, -DR, z0 + COP)
    bx(mb_stone, -hx - 0.05, DR, z0 + WALL, -hx + 0.33, hy + 0.05, z0 + COP)

    # ---- floor and staging benches ---------------------------------------
    bx(mb_stone, -hx + 0.28, -hy + 0.28, z0, hx - 0.28, hy - 0.28, z0 + 0.10)
    for (y0, y1) in ((-hy + 0.34, -hy + 1.16), (hy - 1.16, hy - 0.34)):
        bx(mb_wood, -hx + 0.5, y0, z0 + 0.80, hx - 0.5, y1, z0 + 0.88)
        for xx in np.arange(-hx + 0.8, hx - 0.4, 2.4):
            bx(mb_wood, xx - 0.05, y0, z0 + 0.10, xx + 0.05, y1, z0 + 0.80)

    # ---- glass: long walls, gable ends, gable triangles, roof ------------
    for (y0, y1) in ((-hy - GL * .5, -hy + GL * .5), (hy - GL * .5, hy + GL * .5)):
        bx(mb_glass, -hx + 0.28, y0, z0 + COP, hx - 0.28, y1, z0 + EAVE)
    for (x0, x1) in ((hx - GL * .5, hx + GL * .5),):
        bx(mb_glass, x0, -hy + 0.28, z0 + COP, x1, hy - 0.28, z0 + EAVE)
    # the west gable is glazed above the door head only
    bx(mb_glass, -hx - GL * .5, -hy + 0.28, z0 + DH, -hx + GL * .5, hy - 0.28,
       z0 + EAVE)
    # gable triangles  (note: the profile z values are LOCAL -- the whole
    # house is lifted onto the terrace by z0, so these must be offset too)
    for (x0, x1) in ((hx - GL * .5, hx + GL * .5),
                     (-hx - GL * .5, -hx + GL * .5)):
        slab_x(mb_glass, [(-hy + 0.28, z0 + EAVE), (hy - 0.28, z0 + EAVE),
                          (0.0, z0 + RIDGE)], x0, x1)
    # roof slopes
    ry = hy + OH
    slab_x(mb_glass, [(ry, z0 + EAVE), (0.0, z0 + RIDGE),
                      (0.0, z0 + RIDGE - 0.07), (ry, z0 + EAVE - 0.07)],
           -hx - OH, hx + OH)
    slab_x(mb_glass, [(-ry, z0 + EAVE), (0.0, z0 + RIDGE),
                      (0.0, z0 + RIDGE - 0.07), (-ry, z0 + EAVE - 0.07)],
           -hx - OH, hx + OH)

    # ---- leadwork: posts, bars, transoms, rafters, ridge vent ------------
    for (sx, sy) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        bx(mb_lead, sx * hx - 0.07, sy * hy - 0.07, z0 + COP,
           sx * hx + 0.07, sy * hy + 0.07, z0 + EAVE)
    nbar = max(3, int(Lx / 1.55))
    for i in range(1, nbar):
        xx = -hx + Lx * i / nbar
        for (y0, y1) in ((-hy - 0.065, -hy + 0.065), (hy - 0.065, hy + 0.065)):
            bx(mb_lead, xx - BAR * .5, y0, z0 + COP, xx + BAR * .5, y1, z0 + EAVE)
        # roof rafter on the same line
        ang = math.atan2(ry, RIDGE - EAVE)
        slen = math.hypot(ry, RIDGE - EAVE)
        m = (Matrix.Translation((xx, ry * 0.5, z0 + (EAVE + RIDGE) * 0.5))
             @ Matrix.Rotation(ang, 4, 'X'))
        v, f = L.p_box_minmax(-BAR * .5, -0.05, -slen * .5,
                              BAR * .5, 0.05, slen * .5)
        mb_lead.add(v, f, 0, mtx @ m)
    # transoms and top plates on the long walls
    for (y0, y1) in ((-hy - 0.065, -hy + 0.065), (hy - 0.065, hy + 0.065)):
        bx(mb_lead, -hx, y0, z0 + 2.30, hx, y1, z0 + 2.41)
        bx(mb_lead, -hx, y0, z0 + EAVE - 0.12, hx, y1, z0 + EAVE)
    # gable end bars
    nb2 = max(3, int(Dp / 1.35))
    for i in range(1, nb2):
        yy = -hy + Dp * i / nb2
        bx(mb_lead, hx - 0.065, yy - BAR * .5, z0 + COP, hx + 0.065,
           yy + BAR * .5, z0 + EAVE)
        if abs(yy) > DR:
            bx(mb_lead, -hx - 0.065, yy - BAR * .5, z0 + COP, -hx + 0.065,
               yy + BAR * .5, z0 + EAVE)
    for (x0, x1) in ((hx - 0.065, hx + 0.065),):
        bx(mb_lead, x0, -hy, z0 + 2.30, x1, hy, z0 + 2.41)
        bx(mb_lead, x0, -hy, z0 + EAVE - 0.12, x1, hy, z0 + EAVE)
        # the gable triangle frame
        bx(mb_lead, x0, -0.06, z0 + EAVE, x1, 0.06, z0 + RIDGE)
        ang = math.atan2(hy, RIDGE - EAVE)
        slen = math.hypot(hy, RIDGE - EAVE)
        for s in (-1, 1):
            m = (Matrix.Translation((0.0, s * hy * 0.5,
                                     z0 + (EAVE + RIDGE) * 0.5))
                 @ Matrix.Rotation(-s * ang, 4, 'X'))
            v, f = L.p_box_minmax(-0.05, -BAR * .5, -slen * .5,
                                  0.05, BAR * .5, slen * .5)
            mb_lead.add(v, f, 0, mtx @ m)
    # ridge beam and a running ridge vent
    bx(mb_lead, -hx - OH, -0.10, z0 + RIDGE - 0.16, hx + OH, 0.10, z0 + RIDGE)
    bx(mb_lead, -hx + 0.4, -0.34, z0 + RIDGE, hx - 0.4, 0.34, z0 + RIDGE + 0.09)
    bx(mb_glass, -hx + 0.4, -0.28, z0 + RIDGE + 0.09, hx - 0.4, 0.28,
       z0 + RIDGE + 0.44)
    bx(mb_lead, -hx + 0.4, -0.36, z0 + RIDGE + 0.44, hx - 0.4, 0.36,
       z0 + RIDGE + 0.53)

    # ---- the door ---------------------------------------------------------
    bx(mb_wood, -hx - 0.04, -DR + 0.06, z0 + 0.04, -hx + 0.04, DR - 0.06,
       z0 + DH - 0.06)
    bx(mb_lead, -hx - 0.07, -DR - 0.07, z0, -hx + 0.07, -DR, z0 + DH + 0.09)
    bx(mb_lead, -hx - 0.07, DR, z0, -hx + 0.07, DR + 0.07, z0 + DH + 0.09)
    bx(mb_lead, -hx - 0.07, -DR - 0.07, z0 + DH, -hx + 0.07, DR + 0.07,
       z0 + DH + 0.09)
    # stone stoop outside the door
    bx(mb_stone, -hx - 1.30, -1.30, z0 - 0.30, -hx - 0.02, 1.30, z0 + 0.10)

    # ---- chimney breast on the gable end ----------------------------------
    if chimney:
        bx(mb_brick, hx - 0.1, -0.55, z0, hx + 0.85, 0.55, z0 + 1.60)
        bx(mb_stone, hx - 0.16, -0.62, z0 + 1.60, hx + 0.91, 0.62, z0 + 1.74)
        v, f = L.p_cyl(0.20, 1.25, 12, z0=z0 + 1.74)
        mb_lead.add(v, f, 0, mtx @ Matrix.Translation((hx + 0.36, 0.0, 0.0)))
        v, f = L.p_cone(0.30, 0.22, 12, z0=z0 + 2.99)
        mb_lead.add(v, f, 0, mtx @ Matrix.Translation((hx + 0.36, 0.0, 0.0)))


def greenhouses():
    """Glasshouses on the lower cliff terrace.

    The cliff face wanders by several metres from bearing to bearing, so
    each house is pushed clear of the biggest rock radius it covers and
    turned so that its ridge follows the cliff.
    """
    mb_brick = L.MB()
    mb_stone = L.MB()
    mb_glass = L.MB()
    mb_lead = L.MB()
    mb_wood = L.MB()
    for g in C.greenhouse_layout():
        a = g["angle"]
        mtx = (Matrix.Translation((g["cx"], g["cy"], 0.0))
               @ Matrix.Rotation(g["rot"], 4, 'Z'))
        glasshouse(mb_brick, mb_stone, mb_glass, mb_lead, mb_wood, mtx,
                   g["length"], g["depth"], C.TERRACE_Z)
    mb_brick.to_object("Greenhouse_brick", c_cast, [BRICK])
    mb_stone.to_object("Greenhouse_stone", c_cast, [STONE])
    mb_glass.to_object("Greenhouse_glass", c_cast, [GHGLASS])
    mb_lead.to_object("Greenhouse_frames", c_cast, [LEAD])
    mb_wood.to_object("Greenhouse_interior", c_cast, [WOOD_D])




def terrace_platform(mb, cx, cy, hx, hy, z, mat, drop=30.0):
    """A ledge platform cut into the crag, with a retaining skirt below."""
    v, f = L.p_box_minmax(cx - hx, cy - hy, z - 1.4, cx + hx, cy + hy, z)
    mb.add(v, f, mat)
    for (x0, x1, y0, y1) in ((cx - hx, cx + hx, cy - hy, cy - hy + 1.8),
                             (cx - hx, cx - hx + 1.8, cy - hy, cy + hy),
                             (cx + hx - 1.8, cx + hx, cy - hy, cy + hy)):
        v, f = L.p_box_minmax(x0, y0, z - drop, x1, y1, z)
        mb.add(v, f, mat)
    # low parapet on the outer edge
    for (x0, x1, y0, y1) in ((cx - hx, cx + hx, cy - hy, cy - hy + 0.9),
                             (cx - hx, cx - hx + 0.9, cy - hy, cy + hy),
                             (cx + hx - 0.9, cx + hx, cy - hy, cy + hy)):
        v, f = L.p_box_minmax(x0, y0, z, x1, y1, z + 1.5)
        mb.add(v, f, mat)


def curtain_wall(mb, a0, a1, z, h, mat, merlon_w=1.9, gap=1.8, thick=1.3):
    """Crenellated curtain wall following the rim of the crag.

    The wall has to follow the *displaced* rim, not the undisplaced
    profile: the rock's plan radius wanders by ten metres or more from one
    bearing to the next, so a wall laid out on the smooth profile is
    swallowed by the rock at one end and left hanging in the air at the
    other.
    """
    span = abs(a1 - a0)
    n = max(3, int(span / 0.10))
    prev = None
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        r = C.cliff_r(math.degrees(a), z + 1.0) * 0.99
        p = Vector((math.cos(a) * r, math.sin(a) * r, 0.0))
        if prev is not None:
            d = p - prev
            ln = d.length
            ang = math.atan2(d.y, d.x)
            v, f = L.p_box_minmax(-ln * .5, -thick * .5, z, ln * .5, thick * .5, z + h)
            mb.add(v, f, mat, Matrix.Translation(((p.x + prev.x) * .5,
                                                 (p.y + prev.y) * .5, 0.0))
                   @ Matrix.Rotation(ang, 4, 'Z'))
        prev = p
    # merlons
    rads = [C.cliff_r(math.degrees(a0 + (a1 - a0) * (i + 0.5) / 24.0), z + 1.0)
            for i in range(24)]
    r_avg = sum(rads) / len(rads)
    m = max(4, int(span * r_avg / (merlon_w + gap)))
    for i in range(m):
        if i % 2:
            continue
        a = a0 + (a1 - a0) * (i + 0.5) / m
        r = C.cliff_r(math.degrees(a), z + 1.0) * 0.99
        v, f = L.p_box_minmax(-merlon_w * .5, -thick * .5, z + h,
                              merlon_w * .5, thick * .5, z + h + 2.2)
        mb.add(v, f, mat, Matrix.Translation((math.cos(a) * r, math.sin(a) * r, 0.0))
               @ Matrix.Rotation(a, 4, 'Z'))


def cloister_arcade(mb, cx, cy, a0, a1, radius, z, h, mat, bays=9,
                    arch_h=5.2, pier_w=1.6):
    """A row of pointed arches on a curved terrace edge.

    `radius` may be a number or a function of the bearing: the rim of the
    crag wanders by several metres from one side to the other, so an arcade
    laid on a fixed circle hangs off the rock at one end and is swallowed by
    it at the other.
    """
    rad = radius if callable(radius) else (lambda a: radius)
    for i in range(bays):
        a = a0 + (a1 - a0) * i / bays
        a2 = a0 + (a1 - a0) * (i + 1) / bays
        am = (a + a2) * .5
        r_mid = rad(am)
        r_end = rad(a2)
        # The panel has to be a little wider than its bay: the rim radius
        # wanders, so a panel cut to the exact bay chord leaves a gap at
        # every bay joint and the arcade comes out as a row of loose slabs.
        bw = abs(a2 - a) * r_mid * 1.12
        spring = h - arch_h
        rise = arch_h * 0.95
        arch = L.lancet_points(bw - pier_w * 2, spring, rise, 12)
        # The wall has to span the WHOLE bay, not just the arch: with the
        # panel only as wide as the arch the bays came out as a row of
        # free-standing pointed slabs with daylight between them, and from
        # the hero camera that read as white shards floating in the sky.
        prof = [(-bw * .5, h), (bw * .5, h)] + list(reversed(arch))
        v, f = L.p_prism(prof, -0.9, 0.9)
        px = cx + math.cos(am) * r_mid
        py = cy + math.sin(am) * r_mid
        mb.add(v, f, mat, Matrix.Translation((px, py, z))
               @ Matrix.Rotation(am, 4, 'Z'))
        # pier
        v, f = L.p_box_minmax(-pier_w * .5, -0.95, z, pier_w * .5, 0.95, z + spring)
        mb.add(v, f, mat, Matrix.Translation((cx + math.cos(a) * rad(a),
                                               cy + math.sin(a) * rad(a), 0.0))
               @ Matrix.Rotation(a, 4, 'Z'))


def _battered_pier(a_deg, r_top, z_top, r_bot, z_bot, half_top, half_bot,
                   rad_w, mat):
    """A raking buttress: a slab that leans back to meet the rock below.

    The cliff is very nearly vertical, so a ledge cut into it needs a
    retaining wall as deep as the cliff is steep.  A solid wall that size
    reads as a slab across the whole cliff; carrying the deck on a row of
    these instead lets the rock show through between them.
    """
    a = math.radians(a_deg)
    ca, sa = math.cos(a), math.sin(a)
    tx, ty = -sa, ca                       # tangent
    dr, dz = r_bot - r_top, z_bot - z_top
    ln = math.hypot(dr, dz)
    if ln < 1e-6:
        return
    pr, pz = -dz / ln, dr / ln             # radial-vertical perpendicular
    def corner(r, z, pr2, t):
        rr = r + pr2 * pr
        return (ca * rr + tx * t, sa * rr + ty * t, z + pr2 * pz)
    v = [corner(r_top, z_top, -rad_w, -half_top),
         corner(r_top, z_top, -rad_w, half_top),
         corner(r_top, z_top, rad_w, half_top),
         corner(r_top, z_top, rad_w, -half_top),
         corner(r_bot, z_bot, -rad_w, -half_bot),
         corner(r_bot, z_bot, -rad_w, half_bot),
         corner(r_bot, z_bot, rad_w, half_bot),
         corner(r_bot, z_bot, rad_w, -half_bot)]
    f = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 3, 7, 4), (1, 2, 6, 5),
         (0, 4, 5, 1), (3, 2, 6, 7)]
    return v, f


def cliff_terrace(mb, a0, a1, z, mat_deck, mat_wall, embed=8.0, width=12.0,
                  n=56, pier_every=8, z_foot=3.0, mat_arc=None):
    """A ledge keyed into the cliff flank and carried on raking buttresses.

    The inner edge follows the *displaced* rock radius, not the undisplaced
    profile: the profile is up to twenty metres inside the real rock face,
    so a terrace laid out against it hangs in mid-air over the cliff with
    nothing under it.  The outer edge follows a smoothed version of the same
    radius so the parapet reads as one clean line rather than a squiggle.

    `mat_arc` is the material for the substructure -- the piers and the
    arcade under the deck.  It wants to be the darker weathered stone: in
    the castle's own ashlar the arcade came out the brightest thing in the
    frame, a row of white teeth drawing the eye away from the castle.
    """
    if mat_arc is None:
        mat_arc = mat_wall
    angs = [a0 + (a1 - a0) * i / n for i in range(n + 1)]
    rock = [C.cliff_r(math.degrees(a), z) for a in angs]
    sm = []
    for i in range(n + 1):
        lo = max(0, i - 3)
        hi = min(n, i + 3)
        sm.append(sum(rock[lo:hi + 1]) / float(hi - lo + 1))
    inner = [(math.cos(a) * (rock[i] - embed), math.sin(a) * (rock[i] - embed))
             for i, a in enumerate(angs)]
    outer = [(math.cos(a) * (sm[i] + width), math.sin(a) * (sm[i] + width))
             for i, a in enumerate(angs)]
    TH = 0.85        # deck slab thickness
    for i in range(n):
        a0p, a1p = inner[i], inner[i + 1]
        b0p, b1p = outer[i], outer[i + 1]
        # deck
        mb.add_poly([(a0p[0], a0p[1], z), (b0p[0], b0p[1], z),
                     (b1p[0], b1p[1], z), (a1p[0], a1p[1], z)], mat_deck)
        # outer fascia and soffit: the deck is a slab, not a sheet of paper
        mb.add_poly([(b0p[0], b0p[1], z), (b1p[0], b1p[1], z),
                     (b1p[0], b1p[1], z - TH), (b0p[0], b0p[1], z - TH)], mat_wall)
        mb.add_poly([(a0p[0], a0p[1], z - TH), (b0p[0], b0p[1], z - TH),
                     (b1p[0], b1p[1], z - TH), (a1p[0], a1p[1], z - TH)], mat_wall)
        mb.add_poly([(a0p[0], a0p[1], z - TH), (a1p[0], a1p[1], z - TH),
                     (a1p[0], a1p[1], z), (a0p[0], a0p[1], z)], mat_wall)
        # cornice under the outer edge
        c0 = (b0p[0] + math.cos(angs[i]) * 0.55,
              b0p[1] + math.sin(angs[i]) * 0.55)
        c1 = (b1p[0] + math.cos(angs[i + 1]) * 0.55,
              b1p[1] + math.sin(angs[i + 1]) * 0.55)
        mb.add_poly([(b0p[0], b0p[1], z - TH), (b1p[0], b1p[1], z - TH),
                     (c1[0], c1[1], z - TH), (c0[0], c0[1], z - TH)], mat_wall)
        mb.add_poly([(b0p[0], b0p[1], z - TH - 0.30),
                     (b1p[0], b1p[1], z - TH - 0.30),
                     (c1[0], c1[1], z - TH), (c0[0], c0[1], z - TH)], mat_wall)
        # parapet on the cliff side, with a coping course
        o0 = (b0p[0] + math.cos(angs[i]) * 0.14,
              b0p[1] + math.sin(angs[i]) * 0.14)
        o1 = (b1p[0] + math.cos(angs[i + 1]) * 0.14,
              b1p[1] + math.sin(angs[i + 1]) * 0.14)
        mb.add_poly([(b0p[0], b0p[1], z), (b1p[0], b1p[1], z),
                     (b1p[0], b1p[1], z + 1.40),
                     (b0p[0], b0p[1], z + 1.40)], mat_wall)
        mb.add_poly([(b0p[0], b0p[1], z + 1.40), (b1p[0], b1p[1], z + 1.40),
                     (o1[0], o1[1], z + 1.68), (o0[0], o0[1], z + 1.68)], mat_wall)
        mb.add_poly([(o0[0], o0[1], z + 1.40), (o1[0], o1[1], z + 1.40),
                     (o1[0], o1[1], z + 1.68), (o0[0], o0[1], z + 1.68)], mat_wall)

    # ---- raking buttresses -------------------------------------------------
    # These are PIERS, not planks.  A 1.5 m wide slab leaning against the
    # cliff read as a row of grey boards hanging in the dark; a pier needs
    # enough width to look like load-bearing masonry, and a bearing block
    # where it meets the deck slab.
    pier_idx = list(range(0, n + 1, pier_every))
    for i in pier_idx:
        a = angs[i]
        ad = math.degrees(a)
        r_top = sm[i] + width - 0.6
        r_bot = C.cliff_r(ad, z_foot) - 0.4
        pf = _battered_pier(ad, r_top, z - TH, r_bot, z_foot, 1.35, 2.40,
                            1.05, mat_arc)
        if pf:
            mb.add(pf[0], pf[1], mat_arc)
        bb = L.p_box_minmax(-1.35, -1.80, z - TH - 1.05, 1.35, 1.80, z - TH + 0.06)
        mb.add(bb[0], bb[1], mat_arc,
               Matrix.Translation((math.cos(a) * r_top, math.sin(a) * r_top, 0.0))
               @ Matrix.Rotation(a, 4, 'Z'))

    # ---- an arcaded screen slung between the buttresses -------------------
    # A bare row of raking struts reads as a set of flat planks, however
    # carefully they are built.  Hanging a blind arcade between them turns
    # the substructure into a piece of Victorian engineering, which is what
    # a cliff terrace wants to be: a wall carried on raking buttresses, with
    # tall pointed openings through which the void behind shows.
    z_top = z - TH - 0.32
    z_base = z_top - 11.0
    z_spring = z_base + 1.6
    rise = 6.2
    for k in range(len(pier_idx) - 1):
        i0, i1 = pier_idx[k], pier_idx[k + 1]
        a0, a1 = angs[i0], angs[i1]
        am = (a0 + a1) * .5
        r_w = (sm[i0] + sm[i1]) * .5 + width - 0.6
        bw = abs(a1 - a0) * r_w
        arch = L.lancet_points(bw - 3.4, z_spring, rise, 14)
        # plinth: the arcade has to stand on something
        prof = [(-bw * .5, z_base), (bw * .5, z_base), (bw * .5, z_spring),
                (-bw * .5, z_spring)]
        v, f = L.p_prism(prof, -0.60, 0.60)
        # The profile's X is the arch's width, so it has to run along the
        # cliff, not away from it: rotate the bay by a quarter turn.
        mb.add(v, f, mat_arc, Matrix.Translation(
            (math.cos(am) * r_w, math.sin(am) * r_w, 0.0))
            @ Matrix.Rotation(am + math.pi * .5, 4, 'Z'))
        # spandrel: the wall above the arch heads, notched by the arch itself
        prof = [(-bw * .5, z_top), (bw * .5, z_top)] + list(reversed(arch))
        v, f = L.p_prism(prof, -0.50, 0.50)
        mb.add(v, f, mat_arc, Matrix.Translation(
            (math.cos(am) * r_w, math.sin(am) * r_w, 0.0))
            @ Matrix.Rotation(am + math.pi * .5, 4, 'Z'))
    # ---- end walls closing the ledge off ----------------------------------
    for idx in (0, n):
        a = angs[idx]
        p0 = inner[idx]
        p1 = outer[idx]
        mb.add_poly([(p0[0], p0[1], z), (p1[0], p1[1], z),
                     (p1[0], p1[1], z - TH), (p0[0], p0[1], z - TH)], mat_wall)
        mb.add_poly([(p0[0], p0[1], z - TH), (p1[0], p1[1], z - TH),
                     (p1[0], p1[1], z - TH - 6.0),
                     (p0[0], p0[1], z - TH - 6.0)], mat_wall)





def terraces_and_walls():
    """Defensive terraces, curtain walls and the cliff-edge arcade."""
    mb = L.MB()
    # east gate terrace (links the castle to the viaduct)
    terrace_platform(mb, 126.0, C.VIA_Y, 22.0, 12.0, P, 0, drop=46.0)
    # south-west terrace with the greenhouses, wrapped round the cliff flank
    cliff_terrace(mb, math.radians(C.TERRACE_A0), math.radians(C.TERRACE_A1),
                  C.TERRACE_Z, 1, 0, embed=C.TERRACE_EMBED,
                  width=C.TERRACE_W, mat_arc=1)
    mb.to_object("Terraces", c_cast, [STONE, PAVING])
    # cliff-edge parapet along the south-west rim.  A free-standing arcade
    # of pointed panels was tried here first and rejected: seen from below
    # and outside, the arch soffits caught the fill light and the whole row
    # read as a handful of white shards floating against the sky.
    # curtain walls
    mb = L.MB()
    curtain_wall(mb, math.radians(150), math.radians(205), P - 1.0, 3.0, 0)
    curtain_wall(mb, math.radians(205), math.radians(232), P - 1.0, 3.0, 0)
    curtain_wall(mb, math.radians(248), math.radians(300), P - 1.0, 3.0, 0)
    curtain_wall(mb, math.radians(300), math.radians(345), P - 1.0, 3.0, 0)
    mb.to_object("Curtain_walls", c_cast, [STONE])


def main():
    global STONE, SLATE, VERD, LEAD, GLASS, WOOD, WOOD_D, LANTERN, GOLD, ROCK
    global STONE_STAIR
    global CLOCKFACE
    global PAVING, BRICK, GHGLASS
    global c_cast, c_win, WIN
    mats = hg_mat.build_all()
    STONE, SLATE = mats['stone'], mats['slate']
    VERD, LEAD, GLASS = mats['verdigris'], mats['lead'], mats['glass']
    WOOD, WOOD_D = mats['wood'], mats['wood_dark']
    LANTERN, GOLD = mats['lantern'], mats['gold']
    ROCK = mats['rock']
    PAVING = mats['paving']
    BRICK = mats['brick']
    GHGLASS = mats['ghglass']
    # The cliff stair is cut from the same rock as the cliff but reads as
    # dressed stone; a darker, greyer variant keeps it from glowing pale
    # grey against the rock behind it.
    STONE_STAIR = hg_mat.m_stone(name='M_StoneStair', tint=(0.66, 0.64, 0.60))
    CLOCKFACE = mats['clockface']

    for cn in ("Castle", "Castle_Windows"):
        cc = bpy.data.collections.get(cn)
        if cc:
            for o in list(cc.objects):
                bpy.data.objects.remove(o, do_unlink=True)
    c_cast = L.coll("Castle")
    c_win = L.coll("Castle_Windows")
    WIN = K.Windows(c_win, [GLASS, LEAD, STONE])

    print("great hall...");     great_hall()
    # The great rose window gets its own stained glass.  With the ordinary
    # window material the whole seven metre disc came out as one flat
    # saturated orange decal, because every window is a single object with
    # a single random value.
    rose = mats['roseglass']
    for o in c_win.objects:
        if o.type == 'MESH' and o.data.name.startswith('W_rose_'):
            o.data = o.data.copy()
            o.data.materials[0] = rose
    print("main spire...");     main_spire()
    print("clock tower...");    clock_tower()
    print("ranges...");         ranges_and_towers()
    print("viaduct...");        viaduct()
    print("boathouse...");      boathouse_and_stair()
    print("greenhouses...");    greenhouses()
    print("terraces...");      terraces_and_walls()
    print("windows placed:", WIN.count)


if __name__ == "__main__":
    main()
