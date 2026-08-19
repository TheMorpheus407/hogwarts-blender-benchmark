# Flying buttresses along Great Hall + around tower cluster
import bpy, bmesh, math, random
from mathutils import Vector

_lib = {}
exec(compile(bpy.data.texts['lib'].as_string(), "lib.py", "exec"), _lib)
finish = _lib['finish']; new_obj = _lib['new_obj']
random.seed(77)

def rm_old(names):
    for n in names:
        ob = bpy.data.objects.get(n)
        if ob:
            me = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            if me and me.users == 0: bpy.data.meshes.remove(me)
rm_old(["FlyingButtresses"])

MATS = [bpy.data.materials["M_StoneWall"], bpy.data.materials["M_Slate"], bpy.data.materials["M_Copper"]]
ob = new_obj("FlyingButtresses", "Castle")
bm = bmesh.new()
tl = bm.loops.layers.float_color.new("tint")

P = 44.0
rot = math.radians(-8)
ca, sa = math.cos(rot), math.sin(rot)
def HP(px, py):
    return Vector((-5 + ca*px - sa*py, 22 + sa*px + ca*py))

def arch_strut(a, b, rise, w=0.5, mat=0):
    # quarter-arch from a (low, on buttress) to b (high, on wall)
    n = 6
    vs = []
    for i in range(n+1):
        t = i/n
        p = a.lerp(b, t)
        p.z += rise * math.sin(math.pi*t) * 0.5
        vs.append(p)
    fs = []
    for i in range(n):
        p0, p1 = vs[i], vs[i+1]
        side = (p1-p0).cross(Vector((0,0,1))).normalized() * w/2
        q = [p0-side, p1-side, p1+side, p0+side]
        try:
            f = bm.faces.new([bm.verts.new(v) for v in q]); f.material_index = mat; fs.append(f)
        except ValueError: pass
    return fs

bays = 7
for i in range(bays):
    bx = -32 + 64*i/(bays-1)
    for s in (-1, 1):
        wall = HP(bx, s*7.5)
        # pinnacle post
        butt = HP(bx, s*10.5)
        zt = P + 20
        # pinnacle: small octagonal spire
        pv_lo = [bm.verts.new((butt.x + 0.45*math.cos(a), butt.y + 0.45*math.sin(a), P+13))
                 for a in [k*math.pi/4 for k in range(8)]]
        pv_hi = [bm.verts.new((butt.x + 0.45*math.cos(a), butt.y + 0.45*math.sin(a), P+15.4))
                 for a in [k*math.pi/4 for k in range(8)]]
        for k in range(8):
            f = bm.faces.new((pv_lo[k], pv_lo[(k+1)%8], pv_hi[(k+1)%8], pv_hi[k])); f.material_index = 0
        apex = bm.verts.new((butt.x, butt.y, P+17.5))
        for k in range(8):
            f = bm.faces.new((pv_hi[k], pv_hi[(k+1)%8], apex)); f.material_index = 0
        # strut from pinnacle top to wall high
        arch_strut(Vector((butt.x, butt.y, P+14.5)), Vector((wall.x, wall.y, P+18.5)), 2.2)
        # second lower strut
        arch_strut(Vector((butt.x, butt.y, P+8.0)), Vector((wall.x, wall.y, P+13.0)), 2.6)

# around tower cluster base: radial struts
for az in [math.radians(a) for a in (30, 100, 170, 240, 300)]:
    bx, by = 30 + 11.5*math.cos(az), -4 + 11.5*math.sin(az)
    wx, wy = 30 + 8.4*math.cos(az), -4 + 8.4*math.sin(az)
    arch_strut(Vector((bx, by, P+10)), Vector((wx, wy, P+16)), 2.0, w=0.6)

finish(ob, bm, smooth_deg=45)
for mm in MATS: ob.data.materials.append(mm)
bpy.context.scene.view_layers[0].update()
bpy.ops.wm.save_as_mainfile(filepath="/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/hogwarts.blend")
result = {"ok": True}
