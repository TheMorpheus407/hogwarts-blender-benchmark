# Rebuild lake with shore attr + displacement; paint paths on moor
import bpy, bmesh, math
from mathutils import Vector
exec(compile(open("/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/build/mat_common.py").read(), "mat_common.py", "exec"))

_lib = {}
exec(compile(bpy.data.texts['lib'].as_string(), "lib.py", "exec"), _lib)
terrain_h = _lib['terrain_h']; lake_R = _lib['lake_R']
finish = _lib['finish']; new_obj = _lib['new_obj']

scn = bpy.context.scene
scn.view_layers[0].update()

# ---------- LAKE rebuild ----------
ob = bpy.data.objects.get("Lake")
if ob:
    me = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
ob = new_obj("Lake", "Water")
bm = bmesh.new()
N = 200
S = 4200
for i in range(N+1):
    x = -S/2 + S*i/N
    for j in range(N+1):
        y = -S/2 + S*j/N
        bm.verts.new((x, y, 0))
bm.verts.ensure_lookup_table()
idx = lambda i, j: i*(N+1) + j
for i in range(N):
    for j in range(N):
        a = bm.verts[idx(i,j)]; b = bm.verts[idx(i+1,j)]
        c = bm.verts[idx(i+1,j+1)]; d = bm.verts[idx(i,j+1)]
        bm.faces.new((a,b,c,d))
# shore attribute
lay = bm.verts.layers.float.new("shore")
for v in bm.verts:
    h = terrain_h(v.co.x, v.co.y)
    r = math.hypot(v.co.x, v.co.y)
    # in-lake mask: r < lake edge & terrain below 0
    if h < 0:
        d_shallow = min(1.0, max(0.0, (h + 7.0)/7.0))   # 0 at -7m, 1 at 0
        v[lay] = d_shallow**1.6
    else:
        v[lay] = 0.0
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
finish(ob, bm, smooth_deg=None)
ob.data.materials.append(bpy.data.materials["M_Water"])

# ---------- water material: displacement + shore foam ----------
m = bpy.data.materials["M_Water"]
nt = m.node_tree
bs = [n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'][0]
outn = nt.nodes["Material Output"]
pos = geo_out(nt, "Position", (-1600, 0))
w1 = noise(nt, 0.055, 5, loc=(-1300, 300), roughness=0.25, distortion=3.0, vec=pos)
w2 = noise(nt, 0.22, 4, loc=(-1300, 150), roughness=0.5, distortion=6.0, vec=pos)
w3 = noise(nt, 0.9, 3, loc=(-1300, 0), roughness=0.6, vec=pos)
hcomb = mathn(nt, 'ADD',
              mathn(nt, 'MULTIPLY', w1.outputs['Fac'], 0.5, loc=(-1100, 280)),
              mathn(nt, 'MULTIPLY', w2.outputs['Fac'], 0.35, loc=(-1100, 150)), loc=(-1000, 200))
hcomb = mathn(nt, 'ADD', hcomb, mathn(nt, 'MULTIPLY', w3.outputs['Fac'], 0.12), loc=(-900, 180))
hcomb = mathn(nt, 'SUBTRACT', hcomb, 0.48, loc=(-820, 180))
# displacement
dn = mknode(nt, "ShaderNodeDisplacement", (300, -400))
dn.inputs['Scale'].default_value = 0.22
dn.inputs['Midlevel'].default_value = 0.0
L(nt, hcomb, 0, dn, 0)
L(nt, dn.outputs[0], 0, outn, 2)  # Displacement socket
try:
    m.cycles.displacement_method = 'DISPLACEMENT_AND_BUMP'
except Exception:
    pass
# bump strength tie to waves
bump = [n for n in nt.nodes if n.type=='BUMP'][0]
L(nt, hcomb, 0, bump, 2)
bump.inputs['Strength'].default_value = 0.06
# shore: lighten + transparent
shore_a = mknode(nt, "ShaderNodeAttribute", (-600, -350)); shore_a.attribute_name = "shore"
newbase = mixc(nt, bs.inputs['Base Color'].links[0].from_socket if bs.inputs['Base Color'].is_linked else rgb(nt,(0.004,0.01,0.014),(0,0)),
               rgb(nt, (0.05, 0.09, 0.10), (-400, -350)),
               mathn(nt, 'MULTIPLY', shore_a.outputs['Fac'], 0.85), loc=(-200, -200))
L(nt, newbase, 0, bs, "Base Color")
# roughness up near shore
L(nt, mathn(nt, 'ADD', mathn(nt, 'MULTIPLY', shore_a.outputs['Fac'], 0.25, loc=(-200,-300)), 0.03, loc=(-50,-280)), 0, bs, "Roughness")
# stronger transparency near shore
mixsh = [n for n in nt.nodes if n.type=='MIX_SHADER'][0]
shf = [l for l in nt.links if l.to_node == mixsh and l.to_socket == mixsh.inputs[0]][0].from_socket
shf2 = mathn(nt, 'POWER', shore_a.outputs['Fac'], 1.4, loc=(-300, -420))
L(nt, shf2, 0, mixsh, 0)

# ---------- paths on moor ----------
PATHS = [
    # esplanade -> south shore
    [(0,-262),(3,-290),(10,-320),(22,-345)],
    # west shore path toward standing stones
    [(-70,-120),(-110,-160),(-160,-205),(-210,-245),(-260,-275)],
    # east shore path toward quidditch direction
    [(120,-90),(180,-60),(240,-40),(310,-60),(400,-85)],
    # gate->greenhouse terrace
    [(40,-40),(58,-36)],
]
def dist_seg(px, py, ax, ay, bx, by):
    abx, aby = bx-ax, by-ay
    t = max(0.0, min(1.0, ((px-ax)*abx + (py-ay)*aby)/(abx*abx+aby*aby)))
    return math.hypot(px-(ax+abx*t), py-(ay+aby*t))

moor = bpy.data.objects["Moor"]
me = moor.data
if "path" not in me.attributes:
    at = me.attributes.new("path", 'FLOAT', 'POINT')
else:
    at = me.attributes["path"]
vals = [0.0]*len(me.vertices)
for i, v in enumerate(me.vertices):
    if v.co.z < 1.0:   # only near/above waterline
        continue
    dmin = 1e9
    for pl in PATHS:
        for k in range(len(pl)-1):
            d = dist_seg(v.co.x, v.co.y, pl[k][0], pl[k][1], pl[k+1][0], pl[k+1][1])
            dmin = min(dmin, d)
    if dmin < 6.0:
        t = max(0.0, min(1.0, 1.0 - dmin/6.0))
        vals[i] = t*t*(3-2*t)
at.data.foreach_set('value', vals)
me.update()

scn.view_layers[0].update()
bpy.ops.wm.save_as_mainfile(filepath="/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/hogwarts.blend")
result = {"ok": True, "lake_verts": len(ob.data.vertices)}
