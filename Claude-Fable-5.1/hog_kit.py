"""Architectural kit: procedural builders for towers, halls, walls, bridges.

DETAIL = 0 -> block-out masses, DETAIL = 1 -> windows, buttresses, corbels, dormers...
"""
import bpy, bmesh, math, random, importlib
from mathutils import Vector, Matrix
import numpy as np
import hog_lib as H
importlib.reload(H)
import hog_windows as HW
importlib.reload(HW)
from hog_lib import bm_box, bm_box_zrange, bm_cylinder, bm_cone, bm_prism, bm_gable_roof, circle_pts, rect_pts

DETAIL = 1
FOUND = 10.0   # foundation depth below stated base z (buried in rock)
WIN_COLL = "Windows"

_bvh = None
def ground_z(x, y, default=60.0):
    """Terrain height at (x, y) from Terrain_Near / Terrain_Far via BVH ray cast."""
    global _bvh
    from mathutils.bvhtree import BVHTree
    if _bvh is None:
        _bvh = []
        dg = bpy.context.evaluated_depsgraph_get()
        for n in ("Terrain_CragHi", "Terrain_Crag", "Terrain_Near", "Terrain_Far"):
            o = bpy.data.objects.get(n)
            if o:
                _bvh.append(BVHTree.FromObject(o, dg))
    for b in _bvh:
        hit = b.ray_cast(Vector((x, y, 3000.0)), Vector((0, 0, -1)), 6000.0)
        if hit[0] is not None:
            return hit[0].z
    return default

def reset_ground_cache():
    global _bvh
    _bvh = None

MAT_STONE = "M_Stone"
MAT_TRIM = "M_StoneTrim"
MAT_SLATE = "M_Slate"
MAT_COPPER = "M_Copper"
MAT_WOOD = "M_Wood"
MAT_GLASS = "M_Glass"
MAT_LEAD = "M_Lead"

def _mats():
    H.ensure_material(MAT_STONE, (0.55, 0.50, 0.42, 1))
    H.ensure_material(MAT_TRIM, (0.62, 0.58, 0.50, 1))
    H.ensure_material(MAT_SLATE, (0.18, 0.20, 0.24, 1))
    H.ensure_material(MAT_COPPER, (0.25, 0.45, 0.40, 1))
    H.ensure_material(MAT_WOOD, (0.30, 0.20, 0.12, 1))
    H.ensure_material(MAT_LEAD, (0.30, 0.30, 0.33, 1))
    H.ensure_material("M_Cobble", (0.42, 0.40, 0.36, 1))
    H.ensure_material("M_SlateCone", (0.18, 0.20, 0.24, 1))
    g = bpy.data.materials.get(MAT_GLASS)
    if g is not None and not any(n.type == 'OBJECT_INFO' for n in g.node_tree.nodes):
        bpy.data.materials.remove(g); g = None
    if g is None:
        g = H.ensure_material(MAT_GLASS, (0.9, 0.7, 0.4, 1))
        nt = g.node_tree; nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission")
        oi = nt.nodes.new("ShaderNodeObjectInfo")
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 6.0
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'
        mix.inputs[6].default_value = (1.0, 0.72, 0.42, 1); mix.inputs[7].default_value = (1.0, 0.45, 0.16, 1)
        nt.links.new(oi.outputs["Color"], sep.inputs["Color"])
        nt.links.new(sep.outputs["Red"], mul.inputs[0])
        nt.links.new(sep.outputs["Green"], mix.inputs[0])
        nt.links.new(mix.outputs[2], em.inputs["Color"])
        nt.links.new(mul.outputs[0], em.inputs["Strength"])
        nt.links.new(em.outputs[0], out.inputs["Surface"])

def _obj(bm, name, coll, mat, smooth_deg=None, recalc=True):
    return H.finish_bmesh(bm, name, coll, mat=mat, smooth=smooth_deg is not None, auto_smooth_deg=smooth_deg, recalc=recalc)

def recenter(ob, cx, cy):
    """Move the object origin to (cx, cy, 0) keeping the world geometry in place."""
    ob.data.transform(Matrix.Translation(Vector((-cx, -cy, 0.0))))
    ob.location = (cx, cy, 0.0)
    return ob

def _round_roof_mat(t_copper):
    return MAT_COPPER if t_copper else "M_SlateCone"

def _rng(name):
    return random.Random(sum(ord(c) * (i + 1) for i, c in enumerate(name)))

# --------------------------------------------------------------------------- roofs
def roof_cone(bm, cx, cy, r, z0, z1, segs, flare=0.0):
    """Cone roof; optional concave flare at the eaves (list of rings)."""
    if flare <= 0:
        bm_cone(bm, r, z0, z1, segs, center=(cx, cy), cap=True)
        return
    n = 7
    rings = []
    for i in range(n + 1):
        t = i / n
        # radius profile: straight cone with a concave sweep near the bottom
        rr = r * (1.0 - t) * (1.0 + flare * (1.0 - t) ** 6)
        z = z0 + (z1 - z0) * t
        if i == n:
            rings.append(bm.verts.new((cx, cy, z1)))
        else:
            rings.append([bm.verts.new((cx + rr * math.cos(2 * math.pi * k / segs), cy + rr * math.sin(2 * math.pi * k / segs), z)) for k in range(segs)])
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(segs):
            k2 = (k + 1) % segs
            if isinstance(b, list):
                bm.faces.new((a[k], a[k2], b[k2], b[k]))
            else:
                bm.faces.new((a[k], a[k2], b))
    bm.faces.new(list(reversed(rings[0])))

def roof_pyramid(bm, cx, cy, half, z0, z1, rot=0.0):
    pts = [(cx - half, cy - half), (cx + half, cy - half), (cx + half, cy + half), (cx - half, cy + half)]
    vb = [bm.verts.new((x, y, z0)) for x, y in pts]
    apex = bm.verts.new((cx, cy, z1))
    for i in range(4):
        bm.faces.new((vb[i], vb[(i + 1) % 4], apex))
    bm.faces.new(list(reversed(vb)))

def roof_bell(bm, cx, cy, r, z0, z1, segs):
    prof = []
    n = 12
    for i in range(n + 1):
        t = i / n
        rr = r * (1.0 + 0.12 * math.sin(math.pi * t ** 0.8)) * (1.0 - t) ** 0.8
        if i == n:
            rr = 0.0
        prof.append((rr, z0 + (z1 - z0) * (t ** 1.2)))
    rings = []
    for rr, z in prof:
        if rr > 1e-6:
            rings.append([bm.verts.new((cx + rr * math.cos(2 * math.pi * k / segs), cy + rr * math.sin(2 * math.pi * k / segs), z)) for k in range(segs)])
        else:
            rings.append(bm.verts.new((cx, cy, z)))
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(segs):
            k2 = (k + 1) % segs
            if isinstance(b, list):
                bm.faces.new((a[k], a[k2], b[k2], b[k]))
            else:
                bm.faces.new((a[k], a[k2], b))
    bm.faces.new(list(reversed(rings[0])))

def roof_spire(bm, cx, cy, half, z0, z1, rot=0.0):
    segs = 8
    r = half * 1.02
    ring = [bm.verts.new((cx + r * math.cos(rot + math.pi / 8 + 2 * math.pi * k / segs), cy + r * math.sin(rot + math.pi / 8 + 2 * math.pi * k / segs), z0)) for k in range(segs)]
    apex = bm.verts.new((cx, cy, z1))
    for k in range(segs):
        bm.faces.new((ring[k], ring[(k + 1) % segs], apex))
    bm.faces.new(list(reversed(ring)))
    if abs(rot) > 1e-6:
        return
    # broaches: small triangular fills at the square corners
    for k in range(4):
        a = rot + math.pi / 2 * k + math.pi / 4
        cxk, cyk = cx + half * 1.02 * math.sqrt(2) * math.cos(a) * 0.98, cy + half * 1.02 * math.sqrt(2) * math.sin(a) * 0.98
        p0 = bm.verts.new((cxk, cyk, z0))
        ka = ring[(2 * k) % 8]; kb = ring[(2 * k + 1) % 8]
        top = bm.verts.new((cx + (cxk - cx) * 0.55, cy + (cyk - cy) * 0.55, z0 + (z1 - z0) * 0.18))
        bm.faces.new((ka, p0, top)); bm.faces.new((p0, kb, top)); bm.faces.new((kb, ka, top))

def finial(bm, x, y, z, h=2.6, r=0.18):
    bm_cylinder(bm, r, z - 0.6, z + h * 0.6, 8, center=(x, y))
    bm_cylinder(bm, r * 3.0, z + h * 0.35, z + h * 0.5, 8, center=(x, y), r_top=r * 0.5)
    bm_cylinder(bm, r * 0.5, z + h * 0.5, z + h, 6, center=(x, y), r_top=0.02)
    bm_cylinder(bm, r * 1.6, z + h * 0.72, z + h * 0.8, 8, center=(x, y), r_top=r * 1.6)

# --------------------------------------------------------------------------- parapets
def crenellation_ring(bm, cx, cy, r, z0, h=1.4, thick=0.7, n=None, merlon_frac=0.55, segs_per=3, phase=0.0):
    if n is None:
        n = max(8, int(2 * math.pi * r / 1.7))
    for i in range(n):
        a0 = phase + 2 * math.pi * i / n
        a1 = a0 + 2 * math.pi * merlon_frac / n
        pts = []
        for k in range(segs_per + 1):
            a = a0 + (a1 - a0) * k / segs_per
            pts.append((cx + (r + thick * 0.15) * math.cos(a), cy + (r + thick * 0.15) * math.sin(a)))
        for k in range(segs_per, -1, -1):
            a = a0 + (a1 - a0) * k / segs_per
            pts.append((cx + (r - thick) * math.cos(a), cy + (r - thick) * math.sin(a)))
        bm_prism(bm, pts, z0, z0 + h)

def parapet_ring(bm, cx, cy, r, z0, h=1.0, thick=0.6, segs=48):
    """Solid parapet wall (ring) + crenellations on top."""
    outer = circle_pts(cx, cy, r, segs)
    inner = circle_pts(cx, cy, r - thick, segs)
    vo0 = [bm.verts.new((x, y, z0)) for x, y in outer]; vo1 = [bm.verts.new((x, y, z0 + h)) for x, y in outer]
    vi0 = [bm.verts.new((x, y, z0)) for x, y in inner]; vi1 = [bm.verts.new((x, y, z0 + h)) for x, y in inner]
    for k in range(segs):
        k2 = (k + 1) % segs
        bm.faces.new((vo0[k], vo0[k2], vo1[k2], vo1[k]))
        bm.faces.new((vi1[k], vi1[k2], vi0[k2], vi0[k]))
        bm.faces.new((vo1[k], vo1[k2], vi1[k2], vi1[k]))
        bm.faces.new((vi0[k], vi0[k2], vo0[k2], vo0[k]))
    crenellation_ring(bm, cx, cy, r, z0 + h, h=1.1, thick=thick)

def crenellation_line(bm, p0, p1, z0, h=1.4, thick=0.7, pitch=1.8, merlon=1.0, side=1.0):
    x0, y0 = p0; x1, y1 = p1
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 1e-6:
        return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy * side, ux * side
    n = max(1, int(L / pitch))
    for i in range(n):
        s0 = i * pitch + (L - n * pitch) / 2
        s1 = s0 + merlon
        pts = [(x0 + ux * s0, y0 + uy * s0), (x0 + ux * s1, y0 + uy * s1),
               (x0 + ux * s1 + nx * thick, y0 + uy * s1 + ny * thick), (x0 + ux * s0 + nx * thick, y0 + uy * s0 + ny * thick)]
        bm_prism(bm, pts, z0, z0 + h)

def parapet_box(bm, x0, x1, y0, y1, z0, h=1.0, thick=0.55, crenel=True):
    """Parapet wall around a rectangular roof/terrace edge."""
    for (ax, ay, bx, by, nx, ny) in ((x0, y0, x1, y0, 0, -1), (x1, y0, x1, y1, 1, 0), (x1, y1, x0, y1, 0, 1), (x0, y1, x0, y0, -1, 0)):
        pts = [(ax, ay), (bx, by), (bx - nx * thick, by - ny * thick), (ax - nx * thick, ay - ny * thick)]
        # inset the inner points along the segment direction so corners close
        bm_prism(bm, pts, z0, z0 + h)
        if crenel:
            crenellation_line(bm, (ax, ay), (bx, by), z0 + h, h=1.0, thick=thick, side=-1)

# --------------------------------------------------------------------------- window layout helpers
def _win_unit(kind, hole_w, hole_h, lights=1, glass=True):
    return HW.build_window_unit(kind, hole_w - 0.12, hole_h - 0.22, lights=lights, glass=glass)

def _place(me, pos, nrm, glow, name):
    return HW.place_window(me, pos, nrm, WIN_COLL, glow[0], glow[1], name=name)

# --------------------------------------------------------------------------- towers
def build_tower(t, coll="Towers"):
    _mats()
    rng = _rng(t["name"])
    kind = t["kind"]; cx, cy = t["cx"], t["cy"]; r = t["r"]
    z0 = t["z0"]; z_top = t["z_top"]; roof = t["roof"]; z_apex = t["z_apex"]
    segs = t.get("segs", 48)
    gz = ground_z(cx, cy, z0)
    zb = min(z0, gz) - FOUND
    lit = t.get("lit", 0.5)
    objs = []
    bm = bmesh.new()
    win_defs = []
    placements = []
    # ------------------------------------------------------------- shaft
    if kind == "round":
        if DETAIL >= 1:
            arc = 2 * math.pi * r / segs
            for ri, wz in enumerate(t.get("win_rows", ())):
                n_around = max(3, int(2 * math.pi * r / 6.0))
                hole_w = 1.15 if r >= 5 else 0.85
                hole_h = 2.7 if r >= 5 else 2.0
                nseg = max(1, int(round(hole_w / arc)))
                hole_w = nseg * arc
                for i in range(n_around):
                    seg = int((i + 0.5 * (ri % 2)) * segs / n_around) % segs
                    win_defs.append(dict(seg=seg, n=nseg, z=wz, h=hole_h, kind="lancet"))
            # arrow slits low down
            for i in range(max(2, int(r))):
                seg = int(i * segs / max(2, int(r)) + segs / 7) % segs
                zz = max(gz, z0) + 3.0 + 2.5 * (i % 2)
                win_defs.append(dict(seg=seg, n=1, z=zz, h=1.4, kind="slit"))
            placements = HW.cylinder_with_windows(bm, cx, cy, r, zb, z_top, segs, win_defs)
        else:
            bm_cylinder(bm, r, zb, z_top, segs, center=(cx, cy))
        bm_cylinder(bm, r * 1.12, zb, min(z_top, gz + 6.0), segs, center=(cx, cy), r_top=r * 1.0)
    elif kind == "oct":
        pts = circle_pts(cx, cy, r, 8, phase=math.pi / 8)
        if DETAIL >= 1:
            # 8 flat faces, windows on alternate faces per row
            for i in range(8):
                (ax, ay), (bx, by) = pts[i], pts[(i + 1) % 8]
                L = math.hypot(bx - ax, by - ay)
                ux, uy = (bx - ax) / L, (by - ay) / L
                nx, ny = uy, -ux
                holes = []
                for ri, wz in enumerate(t.get("win_rows", ())):
                    if (i + ri) % 2 == 0:
                        hw, hh = 1.1, 2.6
                        holes.append((L / 2 - hw / 2, L / 2 + hw / 2, wz, wz + hh))
                        placements.append(((ax + ux * L / 2, ay + uy * L / 2, wz), (nx, ny), dict(kind="lancet", w=hw, h=hh)))
                HW._partition_face(bm, (ax, ay, zb), (ux, uy, 0), (0, 0, 1), L, zb, z_top, holes)
            vb = [bm.verts.new((x, y, zb)) for x, y in pts]; vt = [bm.verts.new((x, y, z_top)) for x, y in pts]
            bm.faces.new(list(reversed(vb))); bm.faces.new(vt)
        else:
            bm_prism(bm, pts, zb, z_top)
        bm_prism(bm, circle_pts(cx, cy, r * 1.1, 8, phase=math.pi / 8), zb, min(z_top, gz + 5.0))
    else:  # square
        if DETAIL >= 1:
            wins = []
            Lu = 2 * r
            n_per = max(1, int(Lu / 5.5))
            big = r >= 6.5
            for ri, wz in enumerate(t.get("win_rows", ())):
                for side in "SENW":
                    for i in range(n_per):
                        s = Lu * (i + 0.5) / n_per
                        if big:
                            wins.append(dict(side=side, s=s, z=wz, w=1.9, h=4.6, kind="twin"))
                        else:
                            wins.append(dict(side=side, s=s, z=wz, w=1.25, h=2.9, kind="lancet"))
            placements = [(p, n, w) for (p, n, w) in HW.wall_box_with_windows(bm, cx - r, cx + r, cy - r, cy + r, zb, z_top, wins)]
        else:
            bm_box_zrange(bm, cx - r, cx + r, cy - r, cy + r, zb, z_top)
        bm_box_zrange(bm, cx - r * 1.08, cx + r * 1.08, cy - r * 1.08, cy + r * 1.08, zb, min(z_top, gz + 5.0))
        # corner pilaster strips
        if DETAIL >= 1:
            for sx in (-1, 1):
                for sy in (-1, 1):
                    bm_box_zrange(bm, cx + sx * r - 0.55 + (0.35 * sx), cx + sx * r + 0.55 + (0.35 * sx), cy + sy * r - 0.55 + (0.35 * sy), cy + sy * r + 0.55 + (0.35 * sy), zb, z_top + 0.6)
    # ------------------------------------------------------------- string courses
    for bz in t.get("bands", ()):
        if kind == "round":
            bm_cylinder(bm, r + 0.28, bz, bz + 0.45, segs, center=(cx, cy))
        elif kind == "oct":
            bm_prism(bm, circle_pts(cx, cy, r + 0.28, 8, phase=math.pi / 8), bz, bz + 0.45)
        else:
            bm_box_zrange(bm, cx - r - 0.28, cx + r + 0.28, cy - r - 0.28, cy + r + 0.28, bz, bz + 0.45)
    # ------------------------------------------------------------- machicolated parapet
    par_r = r
    has_par = bool(t.get("machicolation") or t.get("corbels"))
    if has_par:
        if kind == "round":
            if DETAIL >= 1:
                HW.corbel_ring(bm, cx, cy, r, z_top - 1.1, n=max(12, int(2 * math.pi * r / 1.3)), size=0.42, depth=1.0)
                bm_cylinder(bm, r, z_top - 0.5, z_top, segs, center=(cx, cy), r_top=r + 1.0)
                parapet_ring(bm, cx, cy, r + 1.0, z_top, h=1.1, thick=0.6, segs=segs)
            else:
                bm_cylinder(bm, r, z_top - 2.0, z_top - 0.3, segs, center=(cx, cy), r_top=r + 0.9)
                bm_cylinder(bm, r + 0.9, z_top - 0.3, z_top + 0.6, segs, center=(cx, cy))
            par_r = r + 1.0
        elif kind == "square":
            if DETAIL >= 1:
                for (p0, p1, nrm) in (((cx - r, cy - r), (cx + r, cy - r), (0, -1)), ((cx + r, cy - r), (cx + r, cy + r), (1, 0)),
                                      ((cx + r, cy + r), (cx - r, cy + r), (0, 1)), ((cx - r, cy + r), (cx - r, cy - r), (-1, 0))):
                    HW.corbel_line(bm, p0, p1, z_top - 1.0, nrm, pitch=1.2, size=0.4, depth=0.9)
            bm_box_zrange(bm, cx - r - 0.9, cx + r + 0.9, cy - r - 0.9, cy + r + 0.9, z_top - 0.4, z_top + 0.5)
            parapet_box(bm, cx - r - 0.9, cx + r + 0.9, cy - r - 0.9, cy + r + 0.9, z_top + 0.5, h=0.9, thick=0.55)
            par_r = r + 0.9
    # ------------------------------------------------------------- flat-top crenellations
    if roof == "flat":
        if kind == "round":
            if not has_par:
                parapet_ring(bm, cx, cy, r, z_top, h=1.0, thick=0.6, segs=segs)
        elif not has_par:
            parapet_box(bm, cx - r, cx + r, cy - r, cy + r, z_top, h=1.0, thick=0.55)
    objs.append(_obj(bm, t["name"], coll, MAT_STONE, smooth_deg=30 if kind == "round" else None, recalc=(DETAIL == 0)))

    # ------------------------------------------------------------- windows
    if DETAIL >= 1:
        for i, (pos, nrm, w) in enumerate(placements):
            kind_w = w.get("kind", "lancet")
            if kind_w == "slit":
                hole_w = w["n"] * (2 * math.pi * r / segs) if kind == "round" else 0.6
                me = HW.build_window_unit("slit", 0.34, 1.25, glass=True, plate_w=hole_w + 0.3)
                glow = (0.0, 0.5) if rng.random() > 0.35 else (0.15 + 0.2 * rng.random(), 0.7)
            else:
                if kind == "round":
                    hw = w["n"] * (2 * math.pi * r / segs); hh = w["h"]
                elif kind == "oct":
                    hw = w["w"]; hh = w["h"]
                else:
                    hw = w["w"]; hh = w["h"]
                me = _win_unit("lancet", hw, hh, lights=2 if w.get("kind") == "twin" else 1)
                glow = HW.glow_pick(rng, lit)
            _place(me, pos, nrm, glow, f"Win_{t['name']}_{i}")

    # ------------------------------------------------------------- roof
    bm = bmesh.new()
    rmat = MAT_COPPER if t.get("copper") else MAT_SLATE
    roof_base_r = ((par_r - 0.45) if has_par else (r + 0.15)) if kind == "round" else r * 1.10
    z_rb = z_top + (0.4 if not has_par else 0.9)
    if roof == "cone":
        rr = roof_base_r * (1.06 if not has_par else 1.0)
        if kind == "oct":
            roof_cone(bm, cx, cy, r * 1.12, z_rb, z_apex, 8)
        else:
            roof_cone(bm, cx, cy, rr, z_rb, z_apex, segs, flare=0.25 if DETAIL >= 1 else 0.0)
        # eave lip
        bm_cylinder(bm, rr, z_rb - 0.45, z_rb, segs if kind != "oct" else 8, center=(cx, cy), r_top=rr)
    elif roof == "bell":
        roof_bell(bm, cx, cy, roof_base_r, z_rb, z_apex, segs)
        bm_cylinder(bm, roof_base_r, z_rb - 0.45, z_rb, segs, center=(cx, cy))
    elif roof == "pyramid":
        roof_pyramid(bm, cx, cy, r * 1.10, z_rb, z_apex)
        bm_box_zrange(bm, cx - r * 1.1, cx + r * 1.1, cy - r * 1.1, cy + r * 1.1, z_rb - 0.45, z_rb)
    elif roof == "spire":
        # the spire is turned so that no facet is seen edge-on while moonlit from any delivered camera
        roof_spire(bm, cx, cy, r * 1.05, z_rb, z_apex, rot=math.radians(t.get("spire_rot", 28.0)))
        bm_box_zrange(bm, cx - r * 1.08, cx + r * 1.08, cy - r * 1.08, cy + r * 1.08, z_rb - 0.45, z_rb)
    if roof != "flat":
        finial(bm, cx, cy, z_apex, h=2.2 + 0.05 * r)
        # dormers (lucarnes) on big conical roofs
        if DETAIL >= 1 and roof in ("cone", "bell") and r >= 6.5 and kind == "round":
            nd = 4 if r >= 9 else 3
            rr = roof_base_r
            hgt = z_apex - z_rb
            for i in range(nd):
                a = 2 * math.pi * (i + 0.3) / nd
                frac = 0.18
                rd = rr * (1 - frac)
                dz = z_rb + hgt * frac
                dx, dy = cx + rd * math.cos(a), cy + rd * math.sin(a)
                HW.dormer(bm, dx, dy, dz - 0.3, (math.cos(a), math.sin(a)), w=1.7, h=2.4, depth=2.2)
                me = _win_unit("lancet", 1.0, 1.7)
                # window sits on the dormer face
                px, py = dx + math.cos(a) * 2.11, dy + math.sin(a) * 2.11
                _place(me, (px, py, dz + 0.25), (math.cos(a), math.sin(a)), HW.glow_pick(rng, lit * 0.7), f"Win_{t['name']}_D{i}")
        rm = rmat if (t.get("copper") or kind == "square") else "M_SlateCone"
        # faceted spires / pyramids / octagonal cones must stay flat-shaded (smooth normals rim-light the ridges)
        smooth = 40 if (roof in ("cone", "bell") and kind != "oct") else None
        ro = _obj(bm, t["name"] + "_Roof", coll, rm, smooth_deg=smooth)
        if kind != "square":
            recenter(ro, cx, cy)
        objs.append(ro)
    else:
        bm.free()

    # ------------------------------------------------------------- corner turrets on square towers
    if t.get("corner_turrets"):
        ct_r = t["ct_r"]; ct_top = t["ct_top"]; ct_apex = t["ct_apex"]
        for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
            tx, ty = cx + sx * (r - ct_r * 0.3), cy + sy * (r - ct_r * 0.3)
            bm = bmesh.new()
            zb_t = z_top - 28 + i * 3
            if DETAIL >= 1:
                wins = [dict(seg=k * 6 + 2, n=1, z=zb_t + 8 + 7 * j, h=1.6) for j in range(3) for k in range(2)]
                pl = HW.cylinder_with_windows(bm, tx, ty, ct_r, zb_t, ct_top + i * 1.5, 24, wins)
                for j, (pos, nrm, w) in enumerate(pl):
                    _place(_win_unit("lancet", 2 * math.pi * ct_r / 24, 1.6), pos, nrm, HW.glow_pick(rng, lit), f"Win_{t['name']}_CT{i}_{j}")
                bm_cylinder(bm, 0.25, zb_t - 2.5, zb_t, 24, center=(tx, ty), r_top=ct_r)
            else:
                bm_cylinder(bm, ct_r, zb_t, ct_top + i * 1.5, 24, center=(tx, ty))
            bm_cylinder(bm, ct_r + 0.3, ct_top + i * 1.5 - 0.3, ct_top + i * 1.5 + 0.4, 24, center=(tx, ty))
            objs.append(_obj(bm, f"{t['name']}_CT{i}", coll, MAT_STONE, smooth_deg=30, recalc=(DETAIL == 0)))
            bm = bmesh.new()
            roof_cone(bm, tx, ty, (ct_r + 0.3) * 1.1, ct_top + i * 1.5 + 0.4, ct_apex + i * 2.0, 24, flare=0.2)
            finial(bm, tx, ty, ct_apex + i * 2.0, h=1.6, r=0.1)
            objs.append(recenter(_obj(bm, f"{t['name']}_CT{i}_Roof", coll, _round_roof_mat(t.get("copper")), smooth_deg=40), tx, ty))
    # ------------------------------------------------------------- crown of turrets (astronomy tower)
    if t.get("crown"):
        n = 6
        for i in range(n):
            a = 2 * math.pi * i / n + math.pi / 6
            tx, ty = cx + (par_r + 0.2) * math.cos(a), cy + (par_r + 0.2) * math.sin(a)
            bm = bmesh.new()
            bm_cylinder(bm, 1.3, z_top - 8, z_top + 4.5, 16, center=(tx, ty))
            bm_cylinder(bm, 0.2, z_top - 10.5, z_top - 8, 16, center=(tx, ty), r_top=1.3)
            if DETAIL >= 1:
                bm_cylinder(bm, 1.45, z_top + 3.9, z_top + 4.5, 16, center=(tx, ty))
                crenellation_ring(bm, tx, ty, 1.45, z_top + 4.5, h=0.6, thick=0.35, n=8)
            objs.append(_obj(bm, f"{t['name']}_Crown{i}", coll, MAT_STONE, smooth_deg=30))
            bm = bmesh.new()
            roof_cone(bm, tx, ty, 1.5, z_top + 4.8, z_top + 11.0, 16, flare=0.2)
            finial(bm, tx, ty, z_top + 11.0, h=1.2, r=0.08)
            objs.append(recenter(_obj(bm, f"{t['name']}_Crown{i}_Roof", coll, _round_roof_mat(t.get("copper")), smooth_deg=40), tx, ty))
    # ------------------------------------------------------------- attendant turret (Grand Tower)
    if t.get("turrets"):
        a = math.radians(-35)
        tx, ty = cx + (r + 1.6) * math.cos(a), cy + (r + 1.6) * math.sin(a)
        bm = bmesh.new()
        zb_t = z_top - 30
        if DETAIL >= 1:
            wins = [dict(seg=(k * 8 + 3) % 24, n=1, z=zb_t + 6 + 8 * j, h=1.6) for j in range(4) for k in range(3)]
            pl = HW.cylinder_with_windows(bm, tx, ty, 2.2, zb_t, z_top + 8, 24, wins)
            for j, (pos, nrm, w) in enumerate(pl):
                _place(_win_unit("lancet", 2 * math.pi * 2.2 / 24, 1.6), pos, nrm, HW.glow_pick(rng, lit), f"Win_{t['name']}_TU_{j}")
        else:
            bm_cylinder(bm, 2.2, zb_t, z_top + 8, 24, center=(tx, ty))
        bm_cylinder(bm, 0.3, zb_t - 3.5, zb_t, 24, center=(tx, ty), r_top=2.2)
        bm_cylinder(bm, 2.5, z_top + 7.4, z_top + 8.2, 24, center=(tx, ty))
        objs.append(_obj(bm, f"{t['name']}_Turret", coll, MAT_STONE, smooth_deg=30, recalc=(DETAIL == 0)))
        bm = bmesh.new()
        roof_cone(bm, tx, ty, 2.6, z_top + 8.2, z_top + 19, 24, flare=0.2)
        finial(bm, tx, ty, z_top + 19, h=1.6, r=0.1)
        objs.append(recenter(_obj(bm, f"{t['name']}_Turret_Roof", coll, _round_roof_mat(t.get("copper")), smooth_deg=40), tx, ty))
    # ------------------------------------------------------------- clock face & lantern
    if t.get("clock"):
        cz = t.get("clock_z", z_top - 12)
        bm = bmesh.new()
        # face plate on the south side, slightly proud
        R = min(4.2, r * 0.6)
        ring = [bm.verts.new((cx + R * math.cos(2 * math.pi * k / 32), cy - r - 0.05, cz + R * math.sin(2 * math.pi * k / 32))) for k in range(32)]
        ring2 = [bm.verts.new((cx + (R + 0.35) * math.cos(2 * math.pi * k / 32), cy - r - 0.30, cz + (R + 0.35) * math.sin(2 * math.pi * k / 32))) for k in range(32)]
        f = bm.faces.new(ring); f.material_index = 1
        for k in range(32):
            k2 = (k + 1) % 32
            bm.faces.new((ring2[k], ring2[k2], ring[k2], ring[k]))
        # hands & hour marks
        for k in range(12):
            a = 2 * math.pi * k / 12
            bm_box(bm, (0.16, 0.12, 0.42), (cx + (R - 0.35) * math.sin(a), cy - r - 0.12, cz + (R - 0.35) * math.cos(a)))
        for (L, ang, w) in ((R * 0.55, math.radians(20), 0.2), (R * 0.8, math.radians(150), 0.14)):
            hx, hz = math.sin(ang) * L / 2, math.cos(ang) * L / 2
            vs = bm_box(bm, (w, 0.1, L), (cx + hx, cy - r - 0.14, cz + hz))
            m = Matrix.Translation(Vector((cx + hx, cy - r - 0.14, cz + hz))) @ Matrix.Rotation(-ang, 4, 'Y') @ Matrix.Translation(Vector((-(cx + hx), -(cy - r - 0.14), -(cz + hz))))
            bmesh.ops.transform(bm, matrix=m, verts=vs)
        ob = _obj(bm, f"{t['name']}_Clock", coll, MAT_TRIM)
        ob.data.materials.append(bpy.data.materials.get("M_ClockFace") or H.ensure_material("M_ClockFace", (0.85, 0.8, 0.65, 1)))
        objs.append(ob)
    if t.get("lantern"):
        bm = bmesh.new()
        lz = z_apex - 7
        pts = circle_pts(cx, cy, 2.4, 8)
        if DETAIL >= 1:
            # open arcaded lantern: 8 posts + openings
            for (px, py) in pts:
                bm_box(bm, (0.5, 0.5, 7.0), (px, py, lz + 3.5))
            bm_prism(bm, circle_pts(cx, cy, 2.7, 8), lz, lz + 0.6)
            bm_prism(bm, circle_pts(cx, cy, 2.7, 8), lz + 6.6, lz + 7.4)
        else:
            bm_prism(bm, pts, lz, lz + 7.4)
        objs.append(_obj(bm, f"{t['name']}_Lantern", coll, MAT_STONE))
        bm = bmesh.new()
        roof_cone(bm, cx, cy, 2.9, lz + 7.4, lz + 14.0, 8)
        finial(bm, cx, cy, lz + 14.0, h=1.8, r=0.1)
        objs.append(_obj(bm, f"{t['name']}_Lantern_Roof", coll, MAT_LEAD, smooth_deg=40))
    return objs

# --------------------------------------------------------------------------- halls / ranges
def build_range(rg, coll="Walls"):
    _mats()
    rng = _rng(rg["name"])
    x0, x1, y0, y1 = rg["x0"], rg["x1"], rg["y0"], rg["y1"]
    z0 = rg["z0"]; wall_h = rg["wall_h"]; ridge_h = rg["ridge_h"]; axis = rg.get("axis", 'x')
    bays = rg.get("bays", 6)
    lit = rg.get("lit", 0.55)
    gz = min(ground_z(x0, y0, z0), ground_z(x1, y0, z0), ground_z(x0, y1, z0), ground_z(x1, y1, z0), z0)
    zb = gz - FOUND
    z_eave = z0 + wall_h
    objs = []
    bm = bmesh.new()
    placements = []
    if DETAIL >= 1:
        wins = []
        long_sides = ("S", "N") if axis == 'x' else ("E", "W")
        end_sides = ("E", "W") if axis == 'x' else ("S", "N")
        L_long = (x1 - x0) if axis == 'x' else (y1 - y0)
        L_end = (y1 - y0) if axis == 'x' else (x1 - x0)
        big = wall_h >= 17
        # tall traceried windows per bay on the long sides
        for side in long_sides:
            for i in range(bays):
                s = L_long * (i + 0.5) / bays
                if big:
                    wins.append(dict(side=side, s=s, z=z0 + 4.0, w=min(2.4, L_long / bays * 0.42), h=wall_h * 0.62, kind="twin"))
                else:
                    nfl = max(1, int(wall_h / 5.0))
                    for f in range(nfl):
                        wins.append(dict(side=side, s=s, z=z0 + 1.8 + f * (wall_h - 1.5) / nfl, w=1.4, h=2.4, kind="lancet" if f == nfl - 1 else "rect"))
        # open cloister arcade at ground level on the courtyard side
        if rg.get("arcade"):
            side = rg["arcade"]
            Lx = L_long if side in long_sides else L_end
            na = max(2, int(Lx / 3.4))
            for i in range(na):
                wins.append(dict(side=side, s=Lx * (i + 0.5) / na, z=z0 + 0.3, w=2.1, h=3.6, kind="arcade"))
        # end walls: a great window if requested, else a pair
        for side in end_sides:
            if rg.get("big_window") or big:
                wins.append(dict(side=side, s=L_end / 2, z=z0 + 4.5, w=min(5.0, L_end * 0.42), h=wall_h * 0.7, kind="great"))
            else:
                for s in (L_end * 0.3, L_end * 0.7):
                    wins.append(dict(side=side, s=s, z=z0 + 2.0, w=1.2, h=2.2, kind="lancet"))
        placements = HW.wall_box_with_windows(bm, x0, x1, y0, y1, zb, z_eave, wins)
    else:
        bm_box_zrange(bm, x0, x1, y0, y1, zb, z_eave)
    # plinth
    bm_box_zrange(bm, x0 - 0.4, x1 + 0.4, y0 - 0.4, y1 + 0.4, zb, min(z_eave, max(gz, z0) + 1.2))
    # string courses
    if DETAIL >= 1:
        HW.string_course_box(bm, x0, x1, y0, y1, z0 + 3.2)
        if wall_h > 12:
            HW.string_course_box(bm, x0, x1, y0, y1, z_eave - 1.6)
    # buttresses
    if rg.get("buttress"):
        if axis == 'x':
            for i in range(bays + 1):
                bx = x0 + (x1 - x0) * i / bays
                bx = min(max(bx, x0 + 0.8), x1 - 0.8)
                if DETAIL >= 1:
                    HW.buttress(bm, bx, y0, (0, -1), zb, z_eave + 0.3, w=1.4, d0=2.0)
                    HW.buttress(bm, bx, y1, (0, 1), zb, z_eave + 0.3, w=1.4, d0=2.0)
                    if rg.get("flying") and 0 < i < bays:
                        for (yy, sgn) in ((y0, -1), (y1, 1)):
                            HW.flying_buttress(bm, bx, yy, (0, sgn), zb, z0 + wall_h * 0.45, z_eave - 1.0, reach=5.0)
                else:
                    for (ya, yb) in ((y0 - 1.6, y0 + 0.4), (y1 - 0.4, y1 + 1.6)):
                        bm_box_zrange(bm, bx - 0.7, bx + 0.7, ya, yb, zb, z_eave + 2.5)
        else:
            for i in range(bays + 1):
                by = y0 + (y1 - y0) * i / bays
                by = min(max(by, y0 + 0.8), y1 - 0.8)
                if DETAIL >= 1:
                    HW.buttress(bm, x0, by, (-1, 0), zb, z_eave + 0.3, w=1.4, d0=2.0)
                    HW.buttress(bm, x1, by, (1, 0), zb, z_eave + 0.3, w=1.4, d0=2.0)
                else:
                    for (xa, xb) in ((x0 - 1.6, x0 + 0.4), (x1 - 0.4, x1 + 1.6)):
                        bm_box_zrange(bm, xa, xb, by - 0.7, by + 0.7, zb, z_eave + 2.5)
    # parapet
    if rg.get("parapet", True):
        parapet_box(bm, x0 - 0.25, x1 + 0.25, y0 - 0.25, y1 + 0.25, z_eave, h=0.8, thick=0.5, crenel=True)
    objs.append(_obj(bm, rg["name"], coll, MAT_STONE, recalc=(DETAIL == 0)))
    # windows
    if DETAIL >= 1:
        for i, (pos, nrm, w) in enumerate(placements):
            k = w.get("kind", "lancet")
            lights = 1
            if k == "twin":
                lights = 2
            elif k == "great":
                lights = 4 if w["w"] > 3.5 else 3
            if k == "arcade":
                me = HW.build_window_unit("lancet", w["w"] - 0.12, w["h"] - 0.22, lights=1, glass=False, tracery=False)
                _place(me, pos, nrm, (0.0, 0.5), f"Win_{rg['name']}_{i}")
                continue
            me = _win_unit("lancet" if k in ("twin", "great") else k, w["w"], w["h"], lights=lights)
            g = HW.glow_pick(rng, lit)
            if k == "great":
                g = (max(g[0], 0.9), 0.4)
            if rg.get("glow_cap"):
                g = (min(g[0], rg["glow_cap"]), g[1])
            _place(me, pos, nrm, g, f"Win_{rg['name']}_{i}")
    # roof
    bm = bmesh.new()
    bm_gable_roof(bm, x0, x1, y0, y1, z_eave + 0.5, z_eave + 0.5 + ridge_h, axis=axis, overhang=0.1)
    if axis == 'x':
        bm_box_zrange(bm, x0 - 0.2, x1 + 0.2, (y0 + y1) / 2 - 0.22, (y0 + y1) / 2 + 0.22, z_eave + 0.3 + ridge_h, z_eave + 0.8 + ridge_h)
    else:
        bm_box_zrange(bm, (x0 + x1) / 2 - 0.22, (x0 + x1) / 2 + 0.22, y0 - 0.2, y1 + 0.2, z_eave + 0.3 + ridge_h, z_eave + 0.8 + ridge_h)
    # dormers on long ranges
    if DETAIL >= 1 and ridge_h >= 6 and not rg.get("no_dormers"):
        L = (x1 - x0) if axis == 'x' else (y1 - y0)
        nd = max(1, int(L / 12))
        W = (y1 - y0) if axis == 'x' else (x1 - x0)
        slope = ridge_h / (W / 2)
        for i in range(nd):
            s = L * (i + 0.5) / nd
            for side in (-1, 1):
                dist = W / 2 * 0.62
                dz = z_eave + 0.5 + ridge_h - slope * dist
                if axis == 'x':
                    dx, dy = x0 + s, (y0 + y1) / 2 + side * dist; nrm = (0, side)
                else:
                    dx, dy = (x0 + x1) / 2 + side * dist, y0 + s; nrm = (side, 0)
                HW.dormer(bm, dx, dy, dz - 0.6, nrm, w=1.5, h=2.1, depth=2.0)
                me = _win_unit("lancet", 0.9, 1.5)
                _place(me, (dx + nrm[0] * 1.91, dy + nrm[1] * 1.91, dz - 0.1), nrm, HW.glow_pick(rng, lit * 0.6), f"Win_{rg['name']}_D{i}{side}")
    objs.append(_obj(bm, rg["name"] + "_Roof", coll, MAT_LEAD if ridge_h < 5 else MAT_SLATE))
    return objs

def build_great_hall(gh, coll="GreatHall"):
    _mats()
    rng = _rng(gh["name"])
    objs = build_range(dict(gh, parapet=True, lit=0.95, no_dormers=True, glow_cap=0.8), coll=coll)
    x0, x1, y0, y1 = gh["x0"], gh["x1"], gh["y0"], gh["y1"]
    z_eave = gh["z0"] + gh["wall_h"]
    tr = gh.get("turret_r", 2.0)
    gz = ground_z((x0 + x1) / 2, (y0 + y1) / 2, gh["z0"])
    for i, (tx, ty) in enumerate(((x0, y0), (x1, y0), (x1, y1), (x0, y1))):
        bm = bmesh.new()
        zt = z_eave + gh["turret_h"]
        if DETAIL >= 1:
            wins = [dict(seg=(k * 8 + 1) % 24, n=1, z=zt - 6 - 7 * j, h=1.5) for j in range(3) for k in range(3)]
            pl = HW.cylinder_with_windows(bm, tx, ty, tr, gz - FOUND, zt, 24, wins)
            for j, (pos, nrm, w) in enumerate(pl):
                _place(_win_unit("lancet", 2 * math.pi * tr / 24, 1.5), pos, nrm, HW.glow_pick(rng, 0.6), f"Win_{gh['name']}_T{i}_{j}")
            HW.corbel_ring(bm, tx, ty, tr, zt - 0.9, n=12, size=0.3, depth=0.5)
            bm_cylinder(bm, tr + 0.4, zt - 0.4, zt + 0.4, 24, center=(tx, ty))
            crenellation_ring(bm, tx, ty, tr + 0.4, zt + 0.4, h=0.7, thick=0.4, n=10)
        else:
            bm_cylinder(bm, tr, gz - FOUND, zt, 24, center=(tx, ty))
            bm_cylinder(bm, tr + 0.3, zt - 0.4, zt + 0.4, 24, center=(tx, ty))
        objs.append(_obj(bm, f"{gh['name']}_Turret{i}", coll, MAT_STONE, smooth_deg=30, recalc=(DETAIL == 0)))
        bm = bmesh.new()
        roof_cone(bm, tx, ty, (tr + 0.4) * 1.05, zt + 0.5, zt + gh["turret_cone"], 24, flare=0.25)
        finial(bm, tx, ty, zt + gh["turret_cone"], h=1.8, r=0.1)
        objs.append(recenter(_obj(bm, f"{gh['name']}_Turret{i}_Roof", coll, "M_SlateCone", smooth_deg=40), tx, ty))
    return objs

# --------------------------------------------------------------------------- curtain walls
def build_wall_polyline(w, coll="Walls", closed=False, towers=True):
    _mats()
    pts = w["pts"]; h = w["h"]; thick = w["thick"]
    objs = []
    bm = bmesh.new()
    for i, ((xa, ya), (xb, yb)) in enumerate(zip(pts[:-1], pts[1:])):
        L = math.hypot(xb - xa, yb - ya)
        ux, uy = (xb - xa) / L, (yb - ya) / L
        nx, ny = -uy, ux
        n = max(1, int(L / 8.0))
        for k in range(n):
            s0, s1 = k * L / n, (k + 1) * L / n
            p0 = (xa + ux * s0, ya + uy * s0); p1 = (xa + ux * s1, ya + uy * s1)
            g = max(ground_z(*p0, 60.0), ground_z(*p1, 60.0), ground_z((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, 60.0))
            gmin = min(ground_z(*p0, 60.0), ground_z(*p1, 60.0))
            zt = g + h
            poly = [(p0[0] + nx * thick / 2, p0[1] + ny * thick / 2), (p1[0] + nx * thick / 2, p1[1] + ny * thick / 2),
                    (p1[0] - nx * thick / 2, p1[1] - ny * thick / 2), (p0[0] - nx * thick / 2, p0[1] - ny * thick / 2)]
            bm_prism(bm, poly, gmin - FOUND, zt)
            # outer face crenellations (outer side = -normal for CW polylines seen from above; use both for safety on towers=False walls)
            crenellation_line(bm, (p0[0] + nx * thick / 2, p0[1] + ny * thick / 2), (p1[0] + nx * thick / 2, p1[1] + ny * thick / 2), zt, h=1.3, thick=0.5, side=-1)
            if DETAIL >= 1:
                # string course just under the wall walk
                poly2 = [(p0[0] + nx * (thick / 2 + 0.2), p0[1] + ny * (thick / 2 + 0.2)), (p1[0] + nx * (thick / 2 + 0.2), p1[1] + ny * (thick / 2 + 0.2)),
                         (p1[0] - nx * (thick / 2 + 0.2), p1[1] - ny * (thick / 2 + 0.2)), (p0[0] - nx * (thick / 2 + 0.2), p0[1] - ny * (thick / 2 + 0.2))]
                bm_prism(bm, poly2, zt - 1.2, zt - 0.85)
        if towers and i % 2 == 1:
            g = ground_z(xb, yb, 60.0)
            tr = thick * 1.5
            bm_cylinder(bm, tr, g - FOUND, g + h + 2.5, 20, center=(xb, yb))
            if DETAIL >= 1:
                HW.corbel_ring(bm, xb, yb, tr, g + h + 1.6, n=12, size=0.3, depth=0.45)
            bm_cylinder(bm, tr + 0.4, g + h + 2.0, g + h + 2.9, 20, center=(xb, yb))
            crenellation_ring(bm, xb, yb, tr + 0.4, g + h + 2.9, h=1.0, thick=0.45)
    objs.append(_obj(bm, w["name"], coll, MAT_STONE))
    return objs

# --------------------------------------------------------------------------- viaduct
def build_viaduct(v, coll="Viaduct"):
    _mats()
    (xa, ya), (xb, yb) = v["p0"], v["p1"]
    L = math.hypot(xb - xa, yb - ya)
    ux, uy = (xb - xa) / L, (yb - ya) / L
    nx, ny = -uy, ux
    W = v["width"]; zd = v["z_deck"]; n = v["n_arches"]; pw = v["pier_w"]
    span = L / n
    objs = []
    bm = bmesh.new()
    def P(s, off, z):
        return (xa + ux * s + nx * off, ya + uy * s + ny * off, z)
    def poly_at(s, off0, off1, s0, s1):
        return [(xa + ux * s0 + nx * off0, ya + uy * s0 + ny * off0), (xa + ux * s1 + nx * off0, ya + uy * s1 + ny * off0),
                (xa + ux * s1 + nx * off1, ya + uy * s1 + ny * off1), (xa + ux * s0 + nx * off1, ya + uy * s0 + ny * off1)]
    # piers
    for i in range(n + 1):
        s = i * span
        cx, cy = xa + ux * s, ya + uy * s
        g = ground_z(cx, cy, -30.0)
        base = min(g, -2.0) - FOUND
        bm_prism(bm, poly_at(s, -(W + 3.0) / 2, (W + 3.0) / 2, s - pw * 0.75, s + pw * 0.75), base, zd - 16)
        bm_prism(bm, poly_at(s, -(W + 1.2) / 2, (W + 1.2) / 2, s - pw / 2, s + pw / 2), zd - 16.5, zd - 3.0)
        # pilasters on the outer faces, rising to refuges at deck level
        for side in (-1, 1):
            bm_prism(bm, poly_at(s, side * (W / 2 + 0.6), side * (W / 2 + 1.5), s - pw * 0.45, s + pw * 0.45), base, zd + 0.3)
            if DETAIL >= 1:
                # semicircular refuge balcony
                rc = pw * 0.9
                px, py = xa + ux * s + nx * side * (W / 2 + 0.4), ya + uy * s + ny * side * (W / 2 + 0.4)
                pts = [(px + rc * math.cos(a) * ux + rc * math.sin(a) * nx * side, py + rc * math.cos(a) * uy + rc * math.sin(a) * ny * side) for a in [math.pi * k / 8 for k in range(9)]]
                bm_prism(bm, pts, zd - 0.6, zd + 0.05)
                # refuge parapet
                for k in range(8):
                    (x0_, y0_), (x1_, y1_) = pts[k], pts[k + 1]
                    crenellation_line(bm, (x0_, y0_), (x1_, y1_), zd + 0.05, h=1.1, thick=0.35, pitch=0.9, merlon=0.55, side=-1)
    # spandrel walls with pointed arches
    rise = span * 0.42
    z_spring = zd - 3.4 - rise
    for i in range(n):
        s0 = i * span + pw / 2; s1 = (i + 1) * span - pw / 2
        sm = (s0 + s1) / 2; half = (s1 - s0) / 2
        prof = [(s0, z_spring - 6.0), (s0, z_spring)]
        m = 16
        for k in range(1, m):
            t = k / m
            s = s0 + (s1 - s0) * t
            u = (s - sm) / half
            if v.get("arch") == "pointed":
                zz = z_spring + rise * math.sqrt(max(0.0, 1.0 - abs(u) ** 1.7))
            else:
                zz = z_spring + rise * math.sqrt(max(0.0, 1 - u * u))
            prof.append((s, zz))
        prof += [(s1, z_spring), (s1, z_spring - 6.0), (s1, zd - 0.2), (s0, zd - 0.2)]
        va = [bm.verts.new(P(s, -W / 2, z)) for s, z in prof]
        vb = [bm.verts.new(P(s, W / 2, z)) for s, z in prof]
        bm.faces.new(va); bm.faces.new(list(reversed(vb)))
        for k in range(len(prof)):
            k2 = (k + 1) % len(prof)
            bm.faces.new((va[k], va[k2], vb[k2], vb[k]))
        # archivolt: a slightly proud band following the arch on both faces
        if DETAIL >= 1:
            for side in (-1, 1):
                for k in range(1, len(prof) - 5):
                    (sa, za), (sb, zb_) = prof[k], prof[k + 1]
                    if k == 1 or k + 1 >= len(prof) - 4:
                        continue
                    dx, dz = sb - sa, zb_ - za
                    Ls = math.hypot(dx, dz) or 1.0
                    ox, oz = -dz / Ls * 0.35, dx / Ls * 0.35
                    q = [bm.verts.new(P(sa, side * (W / 2 + 0.12), za)), bm.verts.new(P(sb, side * (W / 2 + 0.12), zb_)),
                         bm.verts.new(P(sb + ox, side * (W / 2 + 0.12), zb_ + oz)), bm.verts.new(P(sa + ox, side * (W / 2 + 0.12), za + oz))]
                    bm.faces.new(q if side > 0 else list(reversed(q)))
                    q2 = [bm.verts.new(P(sa, side * (W / 2), za)), bm.verts.new(P(sb, side * (W / 2), zb_)),
                          bm.verts.new(P(sb, side * (W / 2 + 0.12), zb_)), bm.verts.new(P(sa, side * (W / 2 + 0.12), za))]
                    bm.faces.new(q2 if side < 0 else list(reversed(q2)))
    # deck (separate cobbled object) + string course
    bmd = bmesh.new()
    bm_prism(bmd, poly_at(0, -W / 2, W / 2, -0.5, L + 0.5), zd - 1.0, zd)
    if DETAIL >= 1:
        bm_prism(bm, poly_at(0, -W / 2 - 0.25, W / 2 + 0.25, -0.5, L + 0.5), zd - 1.7, zd - 1.3)
    # parapets
    ph = v.get("parapet_h", 1.2)
    for side in (-1, 1):
        off = side * (W / 2 - 0.35)
        bm_prism(bm, poly_at(0, off - 0.35, off + 0.35, -0.5, L + 0.5), zd, zd + ph)
        # rounded coping course
        bm_prism(bm, poly_at(0, off - 0.45, off + 0.45, -0.5, L + 0.5), zd + ph, zd + ph + 0.22)
        if DETAIL >= 1:
            for i in range(n + 1):
                HW.pinnacle(bm, *P(i * span, off, 0)[:2], zd + ph + 0.22, base=0.55, h=1.5)
    objs.append(_obj(bm, v["name"], coll, MAT_STONE))
    objs.append(H.finish_bmesh(bmd, v["name"] + "_Deck", coll, mat="M_Cobble"))
    # lantern posts: a post on the parapet with a bracket arm and a hanging lantern
    posts = []
    for i in range(n + 1):
        if i % v.get("lantern_every", 2) == 0:
            for side in (-1, 1):
                posts.append(P(i * span, side * (W / 2 - 0.35), zd + ph + 2.4))
    v["_lanterns"] = posts
    bm = bmesh.new()
    for (px, py, pz) in posts:
        bm_cylinder(bm, 0.11, pz - 2.4, pz + 0.6, 8, center=(px, py))
        bm_cylinder(bm, 0.2, pz - 2.4, pz - 2.1, 8, center=(px, py))
        bm_cylinder(bm, 0.16, pz + 0.55, pz + 0.7, 8, center=(px, py), r_top=0.04)
        HW.lantern_mesh(bm, px, py, pz, size=0.42)
    objs.append(_obj(bm, v["name"] + "_Lanterns", coll, MAT_LEAD))
    return objs

# --------------------------------------------------------------------------- gatehouse
def build_gatehouse(gh, coll="Walls"):
    """Gate block between the two drum towers, with a great pointed arch facing the viaduct."""
    _mats()
    rng = _rng(gh["name"])
    cx, cy = gh["cx"], gh["cy"]; w, d = gh["w"], gh["d"]; rot = math.radians(gh["rot_deg"])
    z0, wh = gh["z0"], gh["wall_h"]
    M = Matrix.Translation(Vector((cx, cy, 0))) @ Matrix.Rotation(rot, 4, 'Z') @ Matrix.Translation(Vector((-cx, -cy, 0)))
    objs = []
    bm = bmesh.new()
    wins = [dict(side="S", s=w / 2, z=z0 + 0.2, w=5.0, h=7.6, kind="gate"), dict(side="N", s=w / 2, z=z0 + 0.2, w=5.0, h=7.6, kind="gate"),
            dict(side="S", s=w / 2, z=z0 + 10.5, w=2.2, h=3.4, kind="twin"), dict(side="N", s=w / 2, z=z0 + 10.5, w=2.2, h=3.4, kind="twin")]
    gz = ground_z(cx, cy, z0)
    pl = HW.wall_box_with_windows(bm, cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, min(z0, gz) - FOUND, z0 + wh, wins)
    HW.string_course_box(bm, cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, z0 + 9.2)
    for (p0, p1, nrm) in (((cx - w / 2, cy - d / 2), (cx + w / 2, cy - d / 2), (0, -1)), ((cx + w / 2, cy + d / 2), (cx - w / 2, cy + d / 2), (0, 1))):
        HW.corbel_line(bm, p0, p1, z0 + wh - 1.0, nrm, pitch=1.2, size=0.4, depth=0.8)
    bm_box_zrange(bm, cx - w / 2 - 0.8, cx + w / 2 + 0.8, cy - d / 2 - 0.8, cy + d / 2 + 0.8, z0 + wh - 0.4, z0 + wh + 0.4)
    parapet_box(bm, cx - w / 2 - 0.8, cx + w / 2 + 0.8, cy - d / 2 - 0.8, cy + d / 2 + 0.8, z0 + wh + 0.4, h=0.9, thick=0.55)
    # passage floor (cobbled deck continues)
    bm_box_zrange(bm, cx - 3.0, cx + 3.0, cy - d / 2 - 0.5, cy + d / 2 + 0.5, z0 - 0.6, z0 + 0.2)
    bmesh.ops.transform(bm, matrix=M, verts=list(bm.verts))
    objs.append(_obj(bm, gh["name"], coll, MAT_STONE, recalc=False))
    for i, (pos, nrm, wd) in enumerate(pl):
        p = M @ Vector(pos); nn = Matrix.Rotation(rot, 2) @ Vector(nrm)
        if wd["kind"] == "gate":
            me = HW.build_window_unit("lancet", wd["w"] - 0.12, wd["h"] - 0.22, glass=False, tracery=False)
            _place(me, p, (nn.x, nn.y), (0.0, 0.5), f"Win_{gh['name']}_gate{i}")
        else:
            _place(_win_unit("lancet", wd["w"], wd["h"], lights=2), p, (nn.x, nn.y), HW.glow_pick(rng, 0.7), f"Win_{gh['name']}_{i}")
    # portcullis: vertical bars in the passage
    bm = bmesh.new()
    for k in range(7):
        xx = cx - 2.1 + k * 0.7
        bm_box_zrange(bm, xx - 0.06, xx + 0.06, cy - 0.06, cy + 0.06, z0 + 4.2, z0 + 8.0)
    for zz in (z0 + 5.2, z0 + 6.6):
        bm_box_zrange(bm, cx - 2.3, cx + 2.3, cy - 0.05, cy + 0.05, zz - 0.06, zz + 0.06)
    bmesh.ops.transform(bm, matrix=M, verts=list(bm.verts))
    objs.append(_obj(bm, gh["name"] + "_Portcullis", coll, MAT_LEAD))
    # lanterns either side of the arch
    gh["_lanterns"] = []
    for sx in (-1, 1):
        p = M @ Vector((cx + sx * 3.4, cy - d / 2 - 0.6, z0 + 4.0))
        gh["_lanterns"].append((p.x, p.y, p.z))
    bm = bmesh.new()
    for (lx_, ly_, lz_) in gh["_lanterns"]:
        HW.lantern_mesh(bm, lx_, ly_, lz_, size=0.4)
    objs.append(_obj(bm, gh["name"] + "_Lanterns", coll, MAT_LEAD))
    return objs

# --------------------------------------------------------------------------- boathouse & stair
def build_boathouse(b, coll="Boathouse"):
    _mats()
    rng = _rng(b["name"])
    cx, cy, w, d = b["cx"], b["cy"], b["w"], b["d"]
    rot = math.radians(b["rot_deg"]); z0 = b["z0"]; wh = b["wall_h"]; rh = b["ridge_h"]
    objs = []
    M = Matrix.Translation(Vector((cx, cy, 0))) @ Matrix.Rotation(rot, 4, 'Z') @ Matrix.Translation(Vector((-cx, -cy, 0)))
    def T(vs):
        bmesh.ops.transform(bm, matrix=M, verts=vs)
    bm = bmesh.new()
    # walls (stone), with an arched boat door on the lake gable and windows on the long sides
    if DETAIL >= 1:
        wins = []
        for side in ("E", "W"):
            for i in range(3):
                wins.append(dict(side=side, s=d * (i + 0.5) / 3, z=z0 + 1.6, w=1.1, h=2.3, kind="lancet"))
        wins.append(dict(side="S", s=w / 2, z=z0 + 0.4, w=w * 0.5, h=wh - 0.9, kind="door"))
        wins.append(dict(side="N", s=w / 2, z=z0 + 1.6, w=1.4, h=2.6, kind="lancet"))
        pl = HW.wall_box_with_windows(bm, cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, z0, z0 + wh, wins)
        T(list(bm.verts))
        for i, (pos, nrm, wd) in enumerate(pl):
            p = M @ Vector(pos)
            nn = (Matrix.Rotation(rot, 2) @ Vector(nrm))
            if wd["kind"] == "door":
                me = HW.build_window_unit("round", wd["w"] - 0.12, wd["h"] - 0.22, lights=1, glass=False, tracery=False)
                _place(me, p, (nn.x, nn.y), (0.0, 0.9), f"Win_{b['name']}_door")
            else:
                _place(_win_unit("lancet", wd["w"], wd["h"]), p, (nn.x, nn.y), HW.glow_pick(rng, 0.8), f"Win_{b['name']}_{i}")
    else:
        vs = bm_box_zrange(bm, cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, z0, z0 + wh); T(vs)
    # stone quay / base with steps to the water on the lake side (local -Y is the lake side)
    vs = bm_box_zrange(bm, cx - w / 2 - 2.5, cx + w / 2 + 2.5, cy - d / 2 - 1.0, cy + d / 2 + 2.5, -6.0, z0 + 0.4); T(vs)
    for k in range(4):
        vs = bm_box_zrange(bm, cx - w / 2 - 2.5, cx + w / 2 + 2.5, cy - d / 2 - 1.0 - 0.45 * (k + 1), cy - d / 2 - 1.0 - 0.45 * k, -6.0, z0 + 0.4 - 0.32 * (k + 1)); T(vs)
    # corner buttresses
    for sx in (-1, 1):
        for sy in (-1, 1):
            vs = bm_box_zrange(bm, cx + sx * w / 2 - 0.5 + sx * 0.35, cx + sx * w / 2 + 0.5 + sx * 0.35, cy + sy * d / 2 - 0.5 + sy * 0.35, cy + sy * d / 2 + 0.5 + sy * 0.35, z0 - 0.5, z0 + wh + 1.2); T(vs)
            vs = bm_cone(bm, 0.6, z0 + wh + 1.2, z0 + wh + 3.2, 8, center=(cx + sx * (w / 2 + 0.35), cy + sy * (d / 2 + 0.35))); T(vs)
    # gable ends up to the ridge
    for sy in (-1, 1):
        yy = cy + sy * d / 2
        tri = [bm.verts.new((cx - w / 2, yy - 0.25, z0 + wh)), bm.verts.new((cx + w / 2, yy - 0.25, z0 + wh)), bm.verts.new((cx, yy - 0.25, z0 + wh + rh)),
               bm.verts.new((cx - w / 2, yy + 0.25, z0 + wh)), bm.verts.new((cx + w / 2, yy + 0.25, z0 + wh)), bm.verts.new((cx, yy + 0.25, z0 + wh + rh))]
        bm.faces.new((tri[0], tri[1], tri[2])); bm.faces.new((tri[5], tri[4], tri[3]))
        bm.faces.new((tri[0], tri[2], tri[5], tri[3])); bm.faces.new((tri[1], tri[4], tri[5], tri[2]))
        T(tri)
    objs.append(_obj(bm, b["name"], coll, MAT_STONE, recalc=(DETAIL == 0)))
    # roof
    bm = bmesh.new()
    verts, faces = bm_gable_roof(bm, cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, z0 + wh + 0.2, z0 + wh + rh + 0.2, axis='y', overhang=0.6)
    T(verts)
    vs = bm_box_zrange(bm, cx - 0.25, cx + 0.25, cy - d / 2 - 0.7, cy + d / 2 + 0.7, z0 + wh + rh, z0 + wh + rh + 0.5); T(vs)
    sp = M @ Vector((cx, cy + d * 0.2, 0.0))
    bm_cylinder(bm, 0.5, z0 + wh + rh - 1, z0 + wh + rh + 1.5, 8, center=(sp.x, sp.y))
    bm_cone(bm, 0.7, z0 + wh + rh + 1.5, z0 + wh + rh + 5.5, 8, center=(sp.x, sp.y))
    finial(bm, sp.x, sp.y, z0 + wh + rh + 5.5, h=1.2, r=0.06)
    objs.append(_obj(bm, b["name"] + "_Roof", coll, MAT_SLATE))
    # jetty
    bm = bmesh.new()
    jl = 16.0
    jy = cy - d / 2 - 1.5 - jl / 2
    vs = bm_box_zrange(bm, cx - 1.6, cx + 1.6, jy - jl / 2, jy + jl / 2, 0.35, 0.7); T(vs)
    for k in range(6):
        t = jy - jl / 2 + 1.5 + k * (jl - 3) / 5
        for sx in (-1, 1):
            vs = bm_cylinder(bm, 0.14, -4.0, 1.4, 8, center=(cx + sx * 1.5, t)); T(vs)
    objs.append(_obj(bm, b["name"] + "_Jetty", coll, MAT_WOOD))
    # lanterns flanking the boat door and at the jetty end
    door = M @ Vector((cx, cy - d / 2, 0))
    fwd = Matrix.Rotation(rot, 2) @ Vector((0, -1))
    side = Matrix.Rotation(rot, 2) @ Vector((1, 0))
    b["_lanterns"] = [(door.x + side.x * (w * 0.32) + fwd.x * 0.5, door.y + side.y * (w * 0.32) + fwd.y * 0.5, z0 + 3.4),
                      (door.x - side.x * (w * 0.32) + fwd.x * 0.5, door.y - side.y * (w * 0.32) + fwd.y * 0.5, z0 + 3.4)]
    je = M @ Vector((cx, jy - jl / 2 + 0.8, 0))
    b["_lanterns"].append((je.x, je.y, 2.6))
    for yy in (cy - d * 0.2, cy + d * 0.25):
        ip = M @ Vector((cx, yy, 0))
        b["_lanterns"].append((ip.x, ip.y, z0 + wh - 0.9))
    bm = bmesh.new()
    for (lx_, ly_, lz_) in b["_lanterns"]:
        HW.lantern_mesh(bm, lx_, ly_, lz_, size=0.36)
    bm_cylinder(bm, 0.09, 0.5, 2.3, 8, center=(je.x, je.y))
    objs.append(_obj(bm, b["name"] + "_Lanterns", coll, MAT_LEAD))
    return objs

def build_stair(st, coll="Boathouse"):
    _mats()
    pts = st["flights"]; w = st["width"]
    objs = []
    bm = bmesh.new()
    for (xa, ya, za), (xb, yb, zb) in zip(pts[:-1], pts[1:]):
        L = math.hypot(xb - xa, yb - ya)
        ux, uy = (xb - xa) / L, (yb - ya) / L
        nx, ny = -uy, ux
        rise = zb - za
        nsteps = max(2, int(rise / 0.19))
        step_len = L / nsteps
        for k in range(nsteps):
            s0, s1 = k * step_len, (k + 1) * step_len
            zt = za + rise * (k + 1) / nsteps
            poly = [(xa + ux * s0 + nx * w / 2, ya + uy * s0 + ny * w / 2), (xa + ux * s1 + nx * w / 2, ya + uy * s1 + ny * w / 2),
                    (xa + ux * s1 - nx * w / 2, ya + uy * s1 - ny * w / 2), (xa + ux * s0 - nx * w / 2, ya + uy * s0 - ny * w / 2)]
            gmin = min(ground_z(poly[0][0], poly[0][1], 0.0), ground_z(poly[2][0], poly[2][1], 0.0))
            bm_prism(bm, poly, min(gmin, zt) - 3.0, zt)
        poly = [(xb + nx * w / 2, yb + ny * w / 2), (xb + nx * w / 2 + ux * w, yb + ny * w / 2 + uy * w),
                (xb - nx * w / 2 + ux * w, yb - ny * w / 2 + uy * w), (xb - nx * w / 2, yb - ny * w / 2)]
        gmin = min(ground_z(p[0], p[1], 0.0) for p in poly)
        bm_prism(bm, poly, min(gmin, zb) - 3.0, zb)
        for side in (-1, 1):
            off = side * (w / 2 - 0.2)
            # uphill side (towards the crag centre) gets a taller retaining wall
            uphill = (nx * side) * (50.0 - xa) + (ny * side) * (-70.0 - ya) > 0
            ph = 2.2 if uphill else 1.1
            th = 0.35 if uphill else 0.2
            poly = [(xa + nx * (off - th), ya + ny * (off - th)), (xb + nx * (off - th), yb + ny * (off - th)),
                    (xb + nx * (off + th), yb + ny * (off + th)), (xa + nx * (off + th), ya + ny * (off + th))]
            vs, fs = bm_prism(bm, poly, 0.0, 1.0)
            for vv in vs:
                s = ((vv.co.x - xa) * ux + (vv.co.y - ya) * uy) / L
                base = za + rise * s
                vv.co.z = base + (-2.5 if vv.co.z < 0.5 else ph)
    objs.append(_obj(bm, st["name"], coll, MAT_STONE))
    # lantern posts at landings
    bm = bmesh.new()
    lps = []
    for i, (x, y, z) in enumerate(pts):
        # post on the outer (downhill) corner of each landing
        HW.lantern_mesh(bm, x, y, z + 2.6, size=0.36)
        bm_cylinder(bm, 0.1, z - 0.2, z + 2.3, 8, center=(x, y))
        lps.append((x, y, z + 2.6))
    st["_lanterns"] = lps
    objs.append(_obj(bm, st["name"] + "_Lanterns", coll, MAT_LEAD))
    return objs

# --------------------------------------------------------------------------- greenhouses
def build_greenhouse(g, coll="Greenhouses"):
    _mats()
    cx, cy, w, d = g["cx"], g["cy"], g["w"], g["d"]
    rot = math.radians(g["rot_deg"]); z0 = g["z0"]; wh = g["wall_h"]; rh = g["ridge_h"]
    objs = []
    M = Matrix.Translation(Vector((cx, cy, 0))) @ Matrix.Rotation(rot, 4, 'Z') @ Matrix.Translation(Vector((-cx, -cy, 0)))
    bm = bmesh.new()
    vs = bm_box_zrange(bm, cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, z0 - 2.0, z0 + 0.9); bmesh.ops.transform(bm, matrix=M, verts=vs)
    objs.append(_obj(bm, g["name"] + "_Base", coll, MAT_STONE))
    # iron frame
    bm = bmesh.new()
    nb = max(2, int(d / 1.5))
    for i in range(nb + 1):
        yy = cy - d / 2 + d * i / nb
        for sx in (-1, 1):
            vs = bm_box_zrange(bm, cx + sx * w / 2 - 0.05, cx + sx * w / 2 + 0.05, yy - 0.05, yy + 0.05, z0 + 0.9, z0 + wh); bmesh.ops.transform(bm, matrix=M, verts=vs)
            # rafter: from the eave to the ridge
            L = math.hypot(w / 2, rh)
            ang = math.atan2(rh, w / 2)
            mx, mz = cx + sx * w / 4, z0 + wh + rh / 2
            vs = bm_box(bm, (L, 0.08, 0.08), (mx, yy, mz))
            mrot = Matrix.Translation(Vector((mx, yy, mz))) @ Matrix.Rotation(sx * ang, 4, 'Y') @ Matrix.Translation(Vector((-mx, -yy, -mz)))
            bmesh.ops.transform(bm, matrix=mrot, verts=vs); bmesh.ops.transform(bm, matrix=M, verts=vs)
    vs = bm_box_zrange(bm, cx - 0.06, cx + 0.06, cy - d / 2, cy + d / 2, z0 + wh + rh - 0.06, z0 + wh + rh + 0.06); bmesh.ops.transform(bm, matrix=M, verts=vs)
    for sx in (-1, 1):
        vs = bm_box_zrange(bm, cx + sx * w / 2 - 0.06, cx + sx * w / 2 + 0.06, cy - d / 2, cy + d / 2, z0 + wh - 0.06, z0 + wh + 0.06); bmesh.ops.transform(bm, matrix=M, verts=vs)
    for i in range(1, 3):
        zz = z0 + 0.9 + (wh - 0.9) * i / 3
        for sx in (-1, 1):
            vs = bm_box_zrange(bm, cx + sx * w / 2 - 0.04, cx + sx * w / 2 + 0.04, cy - d / 2, cy + d / 2, zz - 0.04, zz + 0.04); bmesh.ops.transform(bm, matrix=M, verts=vs)
    objs.append(_obj(bm, g["name"] + "_Frame", coll, MAT_LEAD))
    # glass skin
    bm = bmesh.new()
    vs = bm_box_zrange(bm, cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, z0 + 0.9, z0 + wh); bmesh.ops.transform(bm, matrix=M, verts=vs)
    verts, faces = bm_gable_roof(bm, cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, z0 + wh, z0 + wh + rh, axis='y', overhang=0.15)
    bmesh.ops.transform(bm, matrix=M, verts=verts)
    ob = _obj(bm, g["name"] + "_Glass", coll, "M_GreenhouseGlass")
    ob.color = (0.35, 0.2, 0.0, 1.0)
    objs.append(ob)
    return objs
