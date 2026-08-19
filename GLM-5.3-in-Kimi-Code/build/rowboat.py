# Foreground rowboat + west fill light + moon check
import bpy, bmesh, math, random, json
from mathutils import Vector, Matrix

exec(compile(open("/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/build/arch2.py").read(), "arch2.py", "exec"))
load_reg()
_lib = {}
exec(compile(bpy.data.texts['lib'].as_string(), "lib.py", "exec"), _lib)
finish = _lib['finish']; new_obj = _lib['new_obj']; ring = _lib['ring']
band_faces = _lib['band_faces']; cap_faces = _lib['cap_faces']

random.seed(5)

def rm_old(names):
    for n in names:
        ob = bpy.data.objects.get(n)
        if ob:
            me = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            if me and me.users == 0: bpy.data.meshes.remove(me)
rm_old(["Rowboat"])

MW = bpy.data.materials.get("M_Wood") or bpy.data.materials.new("M_Wood")
MW.use_nodes = True
bs = MW.node_tree.nodes.get("Principled BSDF")
bs.inputs['Base Color'].default_value = (0.11, 0.075, 0.045, 1.0)
bs.inputs['Roughness'].default_value = 0.75

ob = new_obj("Rowboat", "Extras")
bm = bmesh.new()
tl = bm.loops.layers.float_color.new("tint")
# hull: lofted profile
cx, cy, cz = -118, -560, 0.35
import math
prof = []
NS = 10
for i in range(NS+1):
    t = i/NS          # -1..1 along length
    lx = (t-0.5)*5.6
    halfw = 0.95*math.sin(math.pi*(0.08+0.84*t))**0.7
    depth = 0.55*(0.35+0.65*math.sin(math.pi*t))
    prof.append((lx, halfw, depth))
# gunwale + hull bottom
tops, bots = [], []
for lx, hw, dp in prof:
    tops.append(bm.verts.new((cx+lx, cy-hw, cz+0.55)))
    tops.append(bm.verts.new((cx+lx, cy+hw, cz+0.55)))
for lx, hw, dp in prof:
    bots.append(bm.verts.new((cx+lx, cy, cz-dp)))
# build side faces
fs = []
for i in range(NS):
    t0, t1 = 2*i, 2*i+2
    # left side: top-left i, bot i, bot i+1, top-left i+1
    f = bm.faces.new((tops[2*i], bots[i], bots[i+1], tops[2*i+2])); fs.append(f)
    f = bm.faces.new((tops[2*i+3], bots[i+1], bots[i], tops[2*i+1])); fs.append(f)
# transoms
f = bm.faces.new((tops[0], bots[0], tops[1])); fs.append(f)
f = bm.faces.new((tops[-1], tops[-2], bots[-1])); fs.append(f)
for f in fs: f.material_index = 0
# bench
bx0, bx1 = cx-0.5, cx+0.5
vs = [bm.verts.new((bx0, cy-0.75, cz+0.38)), bm.verts.new((bx1, cy-0.75, cz+0.38)),
      bm.verts.new((bx1, cy+0.75, cz+0.38)), bm.verts.new((bx0, cy+0.75, cz+0.38))]
f = bm.faces.new(vs); f.material_index = 0
# lantern pole at stern
pv = bm.verts.new((cx-2.4, cy, cz+0.55)); pt = bm.verts.new((cx-2.4, cy, cz+1.75))
sv = [bm.verts.new((cx-2.4+dx, cy+dy, cz+0.55+dz)) for dx,dy,dz in
      [(-0.04,-0.04,0),(0.04,-0.04,0),(0.04,0.04,0),(-0.04,0.04,0)]]
st = [bm.verts.new((cx-2.4+dx, cy+dy, cz+1.75+dz)) for dx,dy,dz in
      [(-0.04,-0.04,0),(0.04,-0.04,0),(0.04,0.04,0),(-0.04,0.04,0)]]
for i in range(4):
    f = bm.faces.new((sv[i], sv[(i+1)%4], st[(i+1)%4], st[i])); f.material_index = 0
f = bm.faces.new(st); f.material_index = 0
finish(ob, bm, smooth_deg=45)
ob.data.materials.append(MW)
# lantern head registered (bigger glow)
reg_lantern(Vector((cx-2.4, cy, cz+1.95)), 1.3)
save_reg()

# oars
ob2 = new_obj("Oars", "Extras")
bm = bmesh.new()
for ex, ey, ang in [(cx+0.8, cy+1.3, 0.9), (cx+0.2, cy-1.4, -0.8)]:
    p0 = Vector((ex, ey, 0.62))
    d = Vector((math.cos(ang), math.sin(ang), -0.35)).normalized()
    p1 = p0 + d*3.4
    r0, r1 = 0.045, 0.03
    ra = ring(bm, p0.x, p0.y, p0.z, r0, 5); rb = ring(bm, p1.x, p1.y, p1.z, r1, 5)
    # orient rings around oar axis: cheat - vertical rings fine at this size
    band_faces(bm, ra, rb, mat=0)
finish(ob2, bm, smooth_deg=None)
ob2.data.materials.append(MW)

# rebuild lanterns mesh
exec(compile(open("/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/build/windows_build.py").read(), "windows_build.py", "exec"))
exec(compile(open("/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/build/mat_glow.py").read(), "mat_glow.py", "exec"))

# west fill light
Lc = bpy.data.collections['Lights']
fill = bpy.data.objects.get("Fill_West")
if not fill:
    ld = bpy.data.lights.new("Fill_West", 'SUN')
    ld.energy = 0.35
    ld.color = (0.35, 0.45, 0.65)
    ld.angle = math.radians(12)
    fill = bpy.data.objects.new("Fill_West", ld)
    Lc.objects.link(fill)
d = Vector((math.cos(math.radians(245)), math.sin(math.radians(245)), -math.sin(math.radians(25))))
fill.rotation_euler = (-d).to_track_quat('-Z','Y').to_euler()

bpy.context.scene.view_layers[0].update()
bpy.ops.wm.save_as_mainfile(filepath="/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/hogwarts.blend")
result = {"ok": True}
