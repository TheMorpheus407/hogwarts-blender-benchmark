# Rebuild viaduct with arches that stay BELOW the deck
import bpy, bmesh, math, random, json
from mathutils import Vector, Matrix

_lib = {}
exec(compile(bpy.data.texts['lib'].as_string(), "lib.py", "exec"), _lib)
finish = _lib['finish']; new_obj = _lib['new_obj']; ground_z = _lib['ground_z']
ring = _lib['ring']; band_faces = _lib['band_faces']; build_tower = _lib['build_tower']

random.seed(11)
scn = bpy.context.scene
scn.view_layers[0].update()

MATS = [bpy.data.materials["M_StoneWall"], bpy.data.materials["M_Slate"], bpy.data.materials["M_Copper"]]

ob = bpy.data.objects.get("Viaduct")
if ob:
    me = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)

ob = new_obj("Viaduct", "Castle")
bm = bmesh.new()
tl = bm.loops.layers.float_color.new("tint")

def tintc(base=(1,1,1), var=0.05, hs=0.0):
    v = [max(0, min(2, c + random.uniform(-var, var))) for c in base]
    v[0] = max(0, min(2, v[0] + hs))
    return (v[0], v[1], v[2], 1.0)
tV = tintc((1.0, 0.99, 0.96), 0.04, 0.01)

Y0, Y1 = -45.0, -251.0
L = Y0 - Y1
n_arch = 8
span = L / n_arch
deck_z0, deck_z1 = 40.5, 43.5
W2 = 4.5
pier_w = 4.6

def box(x0, x1, y0, y1, z0, z1, mat=0, tint=tV):
    vs = [bm.verts.new((x0,y0,z0)), bm.verts.new((x1,y0,z0)), bm.verts.new((x1,y1,z0)), bm.verts.new((x0,y1,z0)),
          bm.verts.new((x0,y0,z1)), bm.verts.new((x1,y0,z1)), bm.verts.new((x1,y1,z1)), bm.verts.new((x0,y1,z1))]
    fs = []
    fs.append(bm.faces.new((vs[0],vs[3],vs[7],vs[4])))
    fs.append(bm.faces.new((vs[1],vs[0],vs[4],vs[5])))
    fs.append(bm.faces.new((vs[2],vs[1],vs[5],vs[6])))
    fs.append(bm.faces.new((vs[3],vs[2],vs[6],vs[7])))
    fs.append(bm.faces.new((vs[4],vs[7],vs[6],vs[5])))
    fs.append(bm.faces.new((vs[0],vs[1],vs[2],vs[3])))
    for f in fs:
        f.material_index = mat
        for l in f.loops: l[tl] = tint
    return fs

# piers
for i in range(n_arch + 1):
    yc = Y1 + span*i
    gz = ground_z(0, yc)
    top = min(deck_z0 - 1.0, gz + 1.0)
    if top - (gz - 3.0) < 1.0:
        continue
    box(-W2, W2, yc - pier_w/2, yc + pier_w/2, gz - 3.0, top)
    if 0 < i < n_arch:
        for s in (-1, 1):
            a = bm.verts.new((-1.6, yc + s*pier_w/2, gz-3)); b = bm.verts.new((1.6, yc + s*pier_w/2, gz-3))
            c = bm.verts.new((1.6, yc + s*(pier_w/2+1.8), top)); d = bm.verts.new((-1.6, yc + s*(pier_w/2+1.8), top))
            f = bm.faces.new((a,b,c,d)); f.material_index = 0
            for l in f.loops: l[tl] = tV

# spandrel walls + arches per bay (arch apex strictly below deck bottom)
SEGS = 12
deck_bot = deck_z0 - 1.5   # 39.0
for i in range(n_arch):
    yl = Y1 + span*i + pier_w/2
    yr = Y1 + span*(i+1) - pier_w/2
    yc = (yl + yr)/2
    r_half = (yr - yl)/2
    gzc = ground_z(0, yc)
    spring = max(gzc + 0.6, deck_bot - r_half - 0.5)
    apex = spring + r_half
    apex = min(apex, deck_bot - 0.4)
    rise = apex - spring
    if rise < 1.2:
        # solid spandrel: full wall pier-top to deck bottom
        for s in (-1, 1):
            xw = s*W2
            a = bm.verts.new((xw, yl, gzc)); b = bm.verts.new((xw, yr, gzc))
            c = bm.verts.new((xw, yr, deck_bot)); d = bm.verts.new((xw, yl, deck_bot))
            f = bm.faces.new((a,b,c,d)); f.material_index = 0
            for l in f.loops: l[tl] = tV
        continue
    # segmental arch curve from spring to apex
    for s in (-1, 1):
        xw = s*W2
        arch_lo, arch_hi = [], []
        for k in range(SEGS+1):
            t = k/SEGS
            ang = math.pi * t
            yy = yc - r_half*math.cos(ang)
            zz = spring + rise*math.sin(ang)
            arch_lo.append(bm.verts.new((xw, yy, zz)))
            arch_hi.append(bm.verts.new((xw, yy, deck_bot)))
        for k in range(SEGS):
            f = bm.faces.new((arch_lo[k], arch_lo[k+1], arch_hi[k+1], arch_hi[k]))
            f.material_index = 0
            for l in f.loops: l[tl] = tV
        # wall below springing down to ground
        a = bm.verts.new((xw, yl, gzc)); b = bm.verts.new((xw, yr, gzc))
        c = bm.verts.new((xw, yr, spring)); d = bm.verts.new((xw, yl, spring))
        f = bm.faces.new((a,b,c,d)); f.material_index = 0
        for l in f.loops: l[tl] = tV
    # soffit barrel
    for k in range(SEGS):
        t0, t1 = k/SEGS, (k+1)/SEGS
        y0_ = yc - r_half*math.cos(math.pi*t0); z0_ = spring + rise*math.sin(math.pi*t0)
        y1_ = yc - r_half*math.cos(math.pi*t1); z1_ = spring + rise*math.sin(math.pi*t1)
        a = bm.verts.new((-W2, y0_, z0_)); b = bm.verts.new((W2, y0_, z0_))
        c = bm.verts.new((W2, y1_, z1_)); d = bm.verts.new((-W2, y1_, z1_))
        f = bm.faces.new((a,b,c,d)); f.material_index = 0
        for l in f.loops: l[tl] = tV

# deck slab + parapets + merlons
box(-W2, W2, Y1, Y0, deck_bot, deck_z1)
for s in (-1, 1):
    box(s*W2 - 0.5, s*W2 + 0.1, Y1, Y0, deck_z1, deck_z1 + 1.1)
    yy = Y1 + 1.0
    while yy < Y0 - 1.0:
        box(s*W2 - 0.55, s*W2 + 0.15, yy, yy + 1.1, deck_z1 + 1.1, deck_z1 + 2.0)
        yy += 2.4

# end gate towers
build_tower(bm, -W2-2.2, Y1+2, 38.0, 55, 3.4, sides=8, stages=2, strings=1,
            parapet="cone", roof_h=6.5, roof_mat=1, tint=tV, tlay=tl)
build_tower(bm, W2+2.2, Y1+2, 38.0, 53, 3.4, sides=8, stages=2, strings=1,
            parapet="crenel", tint=tV, tlay=tl)

finish(ob, bm, smooth_deg=45)
for mm in MATS: ob.data.materials.append(mm)

# reposition deck camera now that deck is clear
cam = bpy.data.objects["Cam_Viaduct"]
cam.location = (2.5, -232, 45.4)
from mathutils import Vector as V
d = V((0, -40, 66)) - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 36

scn.view_layers[0].update()
bpy.ops.wm.save_as_mainfile(filepath="/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/hogwarts.blend")
result = {"ok": True, "tris": len(ob.data.polygons)}
