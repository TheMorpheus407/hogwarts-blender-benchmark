"""Pass 3b — extras: gamekeeper's hut with smoke, stone circle, Quidditch pitch,
owlery, covered wooden bridge, moored boats."""
import bpy, bmesh, os, sys, importlib, math, random
from mathutils import Vector, Matrix
FOLDER = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else bpy.path.abspath("//")
if FOLDER not in sys.path:
    sys.path.insert(0, FOLDER)
import hog_lib as H; importlib.reload(H)
import hog_layout as L; importlib.reload(L)
import hog_kit as K; importlib.reload(K)
import hog_windows as HW; importlib.reload(HW)
from hog_lib import bm_box, bm_box_zrange, bm_cylinder, bm_cone, bm_prism, bm_gable_roof, circle_pts, NB

K.DETAIL = 1
K.reset_ground_cache()
gz = K.ground_z
H.clear_collection("Extras")
coll = H.coll("Extras", "Castle")
K._mats()
rng = random.Random(99)
lanterns = []

# --------------------------------------------------------------------------- gamekeeper's hut
hx, hy, hr = L.HUT["cx"], L.HUT["cy"], L.HUT["r"]
g = gz(hx, hy, 40.0)
bm = bmesh.new()
wins = [dict(seg=3, n=2, z=g + 1.4, h=1.3), dict(seg=13, n=2, z=g + 1.4, h=1.3), dict(seg=22, n=2, z=g + 0.2, h=2.3, kind="door")]
pl = HW.cylinder_with_windows(bm, hx, hy, hr, g - 4.0, g + 3.6, 28, wins)
bm_cylinder(bm, hr + 0.35, g + 3.3, g + 3.7, 28, center=(hx, hy))
# chimney
bm_box_zrange(bm, hx + hr * 0.55 - 0.5, hx + hr * 0.55 + 0.5, hy - 0.5, hy + 0.5, g + 2.0, g + 8.6)
hut = H.finish_bmesh(bm, "Hut", coll, mat="M_Stone", recalc=False)
for i, (pos, nrm, w) in enumerate(pl):
    arc = 2 * math.pi * hr / 28 * w["n"]
    if w.get("kind") == "door":
        me = HW.build_window_unit("round", arc - 0.12, w["h"] - 0.22, glass=True, tracery=False)
        HW.place_window(me, pos, nrm, coll, 0.0, 0.5, name="Hut_Door")
    else:
        me = HW.build_window_unit("rect", arc - 0.12, w["h"] - 0.22, lights=2, transom=True)
        HW.place_window(me, pos, nrm, coll, 0.9, 0.85, name=f"Hut_Win{i}")
# thatch roof: cone with a ragged eave
bm = bmesh.new()
segs = 28
ring = [bm.verts.new((hx + (hr + 1.1 + 0.15 * rng.random()) * math.cos(2 * math.pi * k / segs), hy + (hr + 1.1 + 0.15 * rng.random()) * math.sin(2 * math.pi * k / segs), g + 3.5 - 0.2 * rng.random())) for k in range(segs)]
apex = bm.verts.new((hx, hy, g + 9.5))
for k in range(segs):
    bm.faces.new((ring[k], ring[(k + 1) % segs], apex))
bm.faces.new(list(reversed(ring)))
thatch = H.finish_bmesh(bm, "Hut_Roof", coll, mat="M_Thatch", smooth=True)
# chimney smoke: a tall thin volume box
bm = bmesh.new()
bm_box(bm, (9.0, 9.0, 40.0), (hx + hr * 0.55, hy, g + 8.6 + 20.0))
smoke = H.finish_bmesh(bm, "Hut_Smoke", "FX", mat=None)
sm = bpy.data.materials.get("M_Smoke") or bpy.data.materials.new("M_Smoke")
sm.use_nodes = True
nb = NB(sm.node_tree)
tc = nb.n("ShaderNodeTexCoord")
gen = nb.n("ShaderNodeSeparateXYZ", Vector=tc.outputs["Generated"])
# plume: narrow at the bottom, drifting & widening upward, breaking up with noise
cx_ = nb.n("ShaderNodeMath", _operation='SUBTRACT', Value=gen.outputs["X"], Value_1=0.5)
cy_ = nb.n("ShaderNodeMath", _operation='SUBTRACT', Value=gen.outputs["Y"], Value_1=0.5)
drift = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=gen.outputs["Z"], Value_1=0.35, Value_2=cx_.outputs[0])
r2a = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=drift.outputs[0], Value_1=drift.outputs[0])
r2b = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=cy_.outputs[0], Value_1=cy_.outputs[0])
r2 = nb.n("ShaderNodeMath", _operation='ADD', Value=r2a.outputs[0], Value_1=r2b.outputs[0])
rad = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=gen.outputs["Z"], Value_1=0.08, Value_2=0.006)
core = nb.n("ShaderNodeMath", _operation='DIVIDE', Value=r2.outputs[0], Value_1=rad.outputs[0])
fall = nb.n("ShaderNodeMath", _operation='EXPONENT', Value=nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=core.outputs[0], Value_1=-1.0).outputs[0])
top = nb.n("ShaderNodeMapRange", Value=gen.outputs["Z"], From__Min=0.55, From__Max=1.0, To__Min=1.0, To__Max=0.0)
n = nb.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=0.35, Detail=4.0)
nv = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=n.outputs["Factor"], Value_1=1.6, Value_2=-0.35, _use_clamp=True)
d1 = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=fall.outputs[0], Value_1=top.outputs["Result"])
d2 = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=d1.outputs[0], Value_1=nv.outputs[0])
dens = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=d2.outputs[0], Value_1=0.35)
vol = nb.n("ShaderNodeVolumePrincipled", Color=(0.7, 0.72, 0.75, 1), Anisotropy=0.2)
nb.link(dens.outputs[0], vol.inputs["Density"])
out = nb.n("ShaderNodeOutputMaterial"); nb.link(vol.outputs[0], out.inputs["Volume"])
smoke.data.materials.append(sm); smoke.display_type = 'WIRE'
lanterns.append((hx + hr + 0.6, hy - 1.0, g + 2.6))
# woodpile & a fence of posts
bm = bmesh.new()
for i in range(10):
    a = math.radians(200 + i * 14)
    px, py = hx + (hr + 4.0) * math.cos(a), hy + (hr + 4.0) * math.sin(a)
    bm_cylinder(bm, 0.09, gz(px, py, g) - 0.3, gz(px, py, g) + 1.1, 6, center=(px, py))
for i in range(8):
    bm_cylinder(bm, 0.18, g + 0.1 + (i % 3) * 0.36, g + 0.1 + (i % 3) * 0.36 + 0.9, 7, center=(hx - hr - 1.2 + 0.2 * (i // 3), hy + 2.0 + (i % 3) * 0.37 - (i // 3) * 0.19))
H.finish_bmesh(bm, "Hut_Fence", coll, mat="M_Wood")

# --------------------------------------------------------------------------- stone circle
sx, sy, sr = L.STONE_CIRCLE["cx"], L.STONE_CIRCLE["cy"], L.STONE_CIRCLE["r"]
bm = bmesh.new()
for i in range(9):
    a = 2 * math.pi * i / 9 + 0.2
    px, py = sx + sr * math.cos(a), sy + sr * math.sin(a)
    g = gz(px, py, 30.0)
    hgt = 2.6 + 1.4 * rng.random()
    vs = bm_box(bm, (1.1 + 0.4 * rng.random(), 0.7, hgt), (px, py, g - 0.6 + hgt / 2))
    m = Matrix.Translation(Vector((px, py, g))) @ Matrix.Rotation(a + math.pi / 2 + rng.uniform(-0.2, 0.2), 4, 'Z') @ Matrix.Rotation(rng.uniform(-0.12, 0.12), 4, 'X') @ Matrix.Translation(Vector((-px, -py, -g)))
    bmesh.ops.transform(bm, matrix=m, verts=vs)
H.finish_bmesh(bm, "StoneCircle", coll, mat="M_Stone")

# --------------------------------------------------------------------------- Quidditch pitch
q = L.QUIDDITCH
qx, qy, qrx, qry, qz = q["cx"], q["cy"], q["rx"], q["ry"], q["z"]
qrot = math.radians(q["rot_deg"])
def qp(u, v):
    return (qx + u * math.cos(qrot) - v * math.sin(qrot), qy + u * math.sin(qrot) + v * math.cos(qrot))
bm = bmesh.new()
# field oval (slightly above the terrace) with a low wooden palisade
pts = [qp(qrx * math.cos(2 * math.pi * k / 48), qry * math.sin(2 * math.pi * k / 48)) for k in range(48)]
bm_prism(bm, pts, qz - 1.0, qz + 0.15)
field = H.finish_bmesh(bm, "Quidditch_Field", coll, mat="M_Pitch")
bm = bmesh.new()
for k in range(48):
    pass
bmp = bmesh.new()
for k in range(48):
    (ax, ay), (bx, by) = pts[k], pts[(k + 1) % 48]
    bm_cylinder(bmp, 0.12, qz, qz + 1.6, 6, center=(ax, ay))
    L_ = math.hypot(bx - ax, by - ay)
    mx, my = (ax + bx) / 2, (ay + by) / 2
    vs = bm_box(bmp, (L_, 0.06, 0.25), (mx, my, qz + 1.3))
    m = Matrix.Translation(Vector((mx, my, 0))) @ Matrix.Rotation(math.atan2(by - ay, bx - ax), 4, 'Z') @ Matrix.Translation(Vector((-mx, -my, 0)))
    bmesh.ops.transform(bmp, matrix=m, verts=vs)
H.finish_bmesh(bmp, "Quidditch_Palisade", coll, mat="M_Wood")
# goal hoops: three per end
for end in (-1, 1):
    for j, (off, hh) in enumerate(((-9.0, 14.0), (0.0, 18.0), (9.0, 14.0))):
        px, py = qp(end * (qrx - 6.0), off)
        bm_cylinder(bm, 0.22, qz, qz + hh, 8, center=(px, py))
        # ring
        rr = 2.2
        ring = []
        for k in range(20):
            a = 2 * math.pi * k / 20
            ring.append((px + rr * math.cos(a) * -math.sin(qrot), py + rr * math.cos(a) * math.cos(qrot), qz + hh + rr + rr * math.sin(a)))
        for k in range(20):
            (x0, y0, z0), (x1, y1, z1) = ring[k], ring[(k + 1) % 20]
            mx, my, mz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
            seg = math.dist((x0, y0, z0), (x1, y1, z1))
            vs = bm_box(bm, (0.14, 0.14, seg + 0.05), (mx, my, mz))
            d = Vector((x1 - x0, y1 - y0, z1 - z0)).normalized()
            rot = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
            m = Matrix.Translation(Vector((mx, my, mz))) @ rot @ Matrix.Translation(Vector((-mx, -my, -mz)))
            bmesh.ops.transform(bm, matrix=m, verts=vs)
hoops = H.finish_bmesh(bm, "Quidditch_Hoops", coll, mat="M_Gold")
# spectator towers: six tall timber towers with tented tops
bm = bmesh.new()
for i in range(6):
    a = math.radians(30 + i * 60)
    px, py = qp((qrx + 9.0) * math.cos(a), (qry + 9.0) * math.sin(a))
    g = gz(px, py, qz)
    th = 22.0 + 4.0 * (i % 2)
    for sx_ in (-1, 1):
        for sy_ in (-1, 1):
            bm_box_zrange(bm, px + sx_ * 2.4 - 0.25, px + sx_ * 2.4 + 0.25, py + sy_ * 2.4 - 0.25, py + sy_ * 2.4 + 0.25, g - 2.0, g + th)
    bm_box_zrange(bm, px - 3.0, px + 3.0, py - 3.0, py + 3.0, g + th - 6.0, g + th)     # box seating
    bm_box_zrange(bm, px - 3.2, px + 3.2, py - 3.2, py + 3.2, g + th - 6.2, g + th - 5.8)
    bm_cone(bm, 3.6, g + th, g + th + 5.0, 8, center=(px, py))
    bm_cylinder(bm, 0.06, g + th + 4.8, g + th + 7.5, 6, center=(px, py))
    for k in range(3):
        zz = g + 4.0 + k * 5.5
        bm_box_zrange(bm, px - 2.5, px + 2.5, py - 2.5, py + 2.5, zz, zz + 0.3)
    lanterns.append((px + 3.3, py, g + th - 3.0))
H.finish_bmesh(bm, "Quidditch_Towers", coll, mat="M_Wood")

# --------------------------------------------------------------------------- owlery
o = L.OWLERY
g = gz(o["cx"], o["cy"], 60.0)
K.build_tower(dict(name="T_Owlery", kind="round", cx=o["cx"], cy=o["cy"], r=o["r"], z0=g, z_top=g + 17.0, roof="cone", z_apex=g + 27.0,
                   segs=28, bands=(g + 8.0,), win_rows=(g + 4.0, g + 9.0, g + 13.0), copper=False, lit=0.15), coll="Extras")

# --------------------------------------------------------------------------- covered wooden bridge
cb = L.COVERED_BRIDGE
(xa, ya), (xb, yb) = cb["p0"], cb["p1"]
za, zb = cb["z0"], cb["z1"]
W = cb["width"]
Lb = math.hypot(xb - xa, yb - ya)
ux, uy = (xb - xa) / Lb, (yb - ya) / Lb
nx, ny = -uy, ux
def P(s, off, dz):
    t = s / Lb
    return (xa + ux * s + nx * off, ya + uy * s + ny * off, za + (zb - za) * t + dz)
bm = bmesh.new()
# deck
deck = [P(0, -W / 2, 0), P(Lb, -W / 2, 0), P(Lb, W / 2, 0), P(0, W / 2, 0)]
vb = [bm.verts.new(p) for p in deck]; vt = [bm.verts.new((p[0], p[1], p[2] + 0.25)) for p in deck]
bm.faces.new(list(reversed(vb))); bm.faces.new(vt)
for i in range(4):
    j = (i + 1) % 4
    bm.faces.new((vb[i], vb[j], vt[j], vt[i]))
# posts, rails, roof frames every 3.2 m; trestles to the ground every 9.6 m
nseg = int(Lb / 3.2)
roof_h = 3.2
for i in range(nseg + 1):
    s_ = min(Lb, i * 3.2)
    for side in (-1, 1):
        p = P(s_, side * (W / 2 - 0.15), 0.2)
        bm_box(bm, (0.22, 0.22, roof_h), (p[0], p[1], p[2] + roof_h / 2))
        p2 = P(s_, side * (W / 2 - 0.15), 0.2 + 1.1)
        if i < nseg:
            q2 = P(min(Lb, s_ + 3.2), side * (W / 2 - 0.15), 0.2 + 1.1)
            for zz in (0.0, 1.9):
                mx, my, mz = (p2[0] + q2[0]) / 2, (p2[1] + q2[1]) / 2, (p2[2] + q2[2]) / 2 + zz
                vs = bm_box(bm, (3.25, 0.12, 0.12), (mx, my, mz))
                d = Vector((q2[0] - p2[0], q2[1] - p2[1], q2[2] - p2[2])).normalized()
                rot = d.to_track_quat('X', 'Z').to_matrix().to_4x4()
                m = Matrix.Translation(Vector((mx, my, mz))) @ rot @ Matrix.Translation(Vector((-mx, -my, -mz)))
                bmesh.ops.transform(bm, matrix=m, verts=vs)
            # lattice diagonals
            for zz0, zz1 in ((0.0, 1.9),):
                pa = P(s_, side * (W / 2 - 0.15), 0.2 + 1.1); pb = P(min(Lb, s_ + 3.2), side * (W / 2 - 0.15), 0.2 + 3.0)
                mx, my, mz = (pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2, (pa[2] + pb[2]) / 2
                seg = math.dist(pa, pb)
                vs = bm_box(bm, (seg, 0.08, 0.08), (mx, my, mz))
                d = Vector((pb[0] - pa[0], pb[1] - pa[1], pb[2] - pa[2])).normalized()
                rot = d.to_track_quat('X', 'Z').to_matrix().to_4x4()
                m = Matrix.Translation(Vector((mx, my, mz))) @ rot @ Matrix.Translation(Vector((-mx, -my, -mz)))
                bmesh.ops.transform(bm, matrix=m, verts=vs)
    if i % 3 == 0 and 0 < s_ < Lb:
        # trestle: two legs down to the ground plus a cross beam
        for side in (-1, 1):
            p = P(s_, side * (W / 2 + 0.3), -0.1)
            gg = gz(p[0], p[1], p[2] - 10)
            if p[2] - gg > 1.0:
                bm_box(bm, (0.35, 0.35, p[2] - gg + 1.0), (p[0], p[1], (p[2] + gg - 1.0) / 2))
        pl_ = P(s_, -W / 2 - 0.3, -0.2); pr_ = P(s_, W / 2 + 0.3, -0.2)
        bm_box(bm, (0.3, W + 0.9, 0.3), ((pl_[0] + pr_[0]) / 2, (pl_[1] + pr_[1]) / 2, pl_[2]))
    if i % 2 == 1:
        lanterns.append(P(s_, 0.0, 0.2 + roof_h - 0.7))
frame = H.finish_bmesh(bm, "CoveredBridge", coll, mat="M_Wood")
# roof: gabled shingles following the slope
bm = bmesh.new()
eave = 0.2 + roof_h
ridge = eave + 1.7
rl = [bm.verts.new(P(-0.6, -W / 2 - 0.6, eave)), bm.verts.new(P(Lb + 0.6, -W / 2 - 0.6, eave)), bm.verts.new(P(Lb + 0.6, 0, ridge)), bm.verts.new(P(-0.6, 0, ridge))]
rr = [bm.verts.new(P(-0.6, W / 2 + 0.6, eave)), bm.verts.new(P(Lb + 0.6, W / 2 + 0.6, eave))]
bm.faces.new((rl[0], rl[1], rl[2], rl[3]))
bm.faces.new((rl[3], rl[2], rr[1], rr[0]))
bm.faces.new((rl[0], rl[3], rr[0]))
bm.faces.new((rl[1], rr[1], rl[2]))
bm.faces.new((rr[0], rr[1], rl[1], rl[0]))
H.finish_bmesh(bm, "CoveredBridge_Roof", coll, mat="M_Slate")

# --------------------------------------------------------------------------- boats at the jetty
b = L.BOATHOUSE
rot = math.radians(b["rot_deg"])
bm = bmesh.new()
for i in range(3):
    # local: hull along Y, moored beside the jetty
    lx = b["cx"] + (-3.6 if i < 2 else 3.6)
    ly = b["cy"] - b["d"] / 2 - 4.0 - i * 5.0
    n = 9; length = 4.4; width = 1.5
    prof = [(math.sin(math.pi * k / (n - 1)) ** 0.7 * width / 2, -length / 2 + length * k / (n - 1)) for k in range(n)]
    rings = []
    for (hw, yy) in prof:
        rings.append([bm.verts.new((lx - hw, ly + yy, 0.55)), bm.verts.new((lx - hw * 0.8, ly + yy, 0.0)), bm.verts.new((lx + hw * 0.8, ly + yy, 0.0)), bm.verts.new((lx + hw, ly + yy, 0.55))])
    for r0, r1 in zip(rings[:-1], rings[1:]):
        for k in range(3):
            try:
                bm.faces.new((r0[k], r0[k + 1], r1[k + 1], r1[k]))
            except ValueError:
                pass
    # thwarts
    for yy in (-1.2, 0.2, 1.4):
        bm_box(bm, (width * 0.8, 0.18, 0.05), (lx, ly + yy, 0.45))
    vs = [v for ring in rings for v in ring]
    m = Matrix.Translation(Vector((b["cx"], b["cy"], 0))) @ Matrix.Rotation(rot, 4, 'Z') @ Matrix.Translation(Vector((-b["cx"], -b["cy"], 0)))
    bmesh.ops.transform(bm, matrix=m, verts=[v for v in bm.verts if v.co.z < 1.0 and abs(v.co.x - lx) < 3 and abs(v.co.y - ly) < 4])
boats = H.finish_bmesh(bm, "Boats", coll, mat="M_Wood", smooth=True)

# --------------------------------------------------------------------------- lone boat in the hero foreground
bm = bmesh.new()
bx, by = -150.0, -335.0
ang = math.radians(58)
n = 11; length = 5.2; width = 1.7
prof = [(math.sin(math.pi * k / (n - 1)) ** 0.65 * width / 2, -length / 2 + length * k / (n - 1)) for k in range(n)]
rings = []
for (hw, yy) in prof:
    rings.append([bm.verts.new((-hw, yy, 0.62)), bm.verts.new((-hw * 0.75, yy, 0.02)), bm.verts.new((hw * 0.75, yy, 0.02)), bm.verts.new((hw, yy, 0.62))])
for r0, r1 in zip(rings[:-1], rings[1:]):
    for k in range(3):
        try:
            bm.faces.new((r0[k], r0[k + 1], r1[k + 1], r1[k]))
        except ValueError:
            pass
for yy in (-1.6, 0.0, 1.5):
    bm_box(bm, (width * 0.85, 0.2, 0.05), (0.0, yy, 0.5))
bm_box(bm, (0.3, 0.3, 0.06), (0.0, -2.2, 0.62))
bm_cylinder(bm, 0.05, 0.6, 2.4, 6, center=(0.0, 2.2))
HW.lantern_mesh(bm, 0.0, 2.2, 2.55, size=0.3)
m = Matrix.Translation(Vector((bx, by, 0.0))) @ Matrix.Rotation(ang, 4, 'Z')
bmesh.ops.transform(bm, matrix=m, verts=list(bm.verts))
lone = H.finish_bmesh(bm, "Boat_Lone", coll, mat="M_Wood", smooth=True)
lp = m @ Vector((0.0, 2.2, 2.55))
lanterns.append((lp.x, lp.y, lp.z))

# --------------------------------------------------------------------------- courtyard paving
bm = bmesh.new()
bm_box_zrange(bm, -36.0, 56.0, -1.0, 46.0, 71.0, 72.18)
H.finish_bmesh(bm, "Courtyard_Paving", coll, mat="M_Cobble")
# a well in the middle of the courtyard
bm = bmesh.new()
bm_cylinder(bm, 1.6, 72.1, 73.1, 20, center=(10.0, 22.0))
bm_cylinder(bm, 1.2, 72.1, 73.2, 20, center=(10.0, 22.0))
for sx in (-1, 1):
    bm_box_zrange(bm, 10.0 + sx * 1.3 - 0.1, 10.0 + sx * 1.3 + 0.1, 21.9, 22.1, 73.0, 75.2)
bm_box_zrange(bm, 8.5, 11.5, 21.85, 22.15, 75.1, 75.4)
H.finish_bmesh(bm, "Courtyard_Well", coll, mat="M_StoneTrim")

# extra materials
def _simple(name, col, rough=0.9, emit=0.0, metal=0.0):
    m = H.new_material(name); nb = NB(m.node_tree)
    tc = nb.n("ShaderNodeTexCoord")
    n = nb.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=3.0, Detail=5.0)
    v = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=n.outputs["Factor"], Value_1=0.5, Value_2=0.7)
    c = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=col, Scale=v.outputs[0])
    bump = nb.n("ShaderNodeBump", Strength=0.5, Distance=0.05, Height=n.outputs["Factor"])
    bsdf = nb.n("ShaderNodeBsdfPrincipled", Base__Color=c.outputs[0], Roughness=rough, Metallic=metal, Normal=bump.outputs["Normal"])
    if emit > 0:
        bsdf.inputs["Emission Color"].default_value = col + (1,)
        bsdf.inputs["Emission Strength"].default_value = emit
    o = nb.n("ShaderNodeOutputMaterial"); nb.link(bsdf.outputs[0], o.inputs["Surface"])
    return m
_simple("M_Thatch", (0.30, 0.22, 0.10), rough=0.95)
_simple("M_Pitch", (0.06, 0.09, 0.03), rough=0.95)
_simple("M_Gold", (0.9, 0.7, 0.25), rough=0.35, emit=0.15, metal=0.9)

bpy.context.scene["hog_lanterns_extra"] = [c for p in lanterns for c in p]
H.purge_orphans()
result = {"lanterns": len(lanterns), "objects": len(coll.objects)}
