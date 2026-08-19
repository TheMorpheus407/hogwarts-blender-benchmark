# Conifer forest scatter + boulders, merged meshes
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, noise as mbnoise

_lib = {}
exec(compile(bpy.data.texts['lib'].as_string(), "lib.py", "exec"), _lib)
finish = _lib['finish']; new_obj = _lib['new_obj']; fbm2 = _lib['fbm2']
terrain_h = _lib['terrain_h']

random.seed(31)
mbnoise.seed_set(31)

def rm_old(names):
    for n in names:
        ob = bpy.data.objects.get(n)
        if ob:
            me = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            if me and me.users == 0: bpy.data.meshes.remove(me)
rm_old(["Forest", "ForestFar", "Boulders", "Shrubs"])

MPINE = bpy.data.materials.get("M_Pine") or bpy.data.materials.new("M_Pine")
MPINE.use_nodes = True
bs = MPINE.node_tree.nodes.get("Principled BSDF")
bs.inputs['Base Color'].default_value = (0.05, 0.09, 0.05, 1.0)
bs.inputs['Roughness'].default_value = 0.85

def tree_into(bm, x, y, h, scale, tcol, tl):
    z = h
    az = random.uniform(0, 2*math.pi)
    lean = Matrix.Rotation(random.uniform(-0.06, 0.06), 4, 'X')
    S = Matrix.Scale(scale, 4)
    Rz = Matrix.Rotation(az, 4, 'Z')
    T = Matrix.Translation((x, y, z))
    W = T @ Rz @ lean @ S
    fs = []
    # trunk
    tr_lo = [bm.verts.new(W @ Vector((0.14*math.cos(a), 0.14*math.sin(a), 0))) for a in
             [i*2*math.pi/5 for i in range(5)]]
    tr_hi = [bm.verts.new(W @ Vector((0.10*math.cos(a), 0.10*math.sin(a), 0.9))) for a in
             [i*2*math.pi/5 for i in range(5)]]
    for i in range(5):
        f = bm.faces.new((tr_lo[i], tr_lo[(i+1)%5], tr_hi[(i+1)%5], tr_hi[i])); f.material_index = 1; fs.append(f)
    # 3 canopy cones
    tiers = [(0.5, 4.6, 0.0), (2.8, 3.4, 0.0), (4.9, 2.2, 0.0)]
    heights = [4.8, 3.8, 2.6]
    for (cz, cr, _), chh in zip(tiers, heights):
        seg = 6
        lo = [bm.verts.new(W @ Vector((cr*math.cos(a), cr*math.sin(a), cz))) for a in
              [i*2*math.pi/seg for i in range(seg)]]
        apex = bm.verts.new(W @ Vector((0, 0, cz + chh)))
        midr = cr*0.86
        mid = [bm.verts.new(W @ Vector((midr*math.cos(a), midr*math.sin(a), cz + chh*0.42))) for a in
               [i*2*math.pi/seg for i in range(seg)]]
        for i in range(seg):
            f = bm.faces.new((lo[i], lo[(i+1)%seg], mid[(i+1)%seg], mid[i])); f.material_index = 0; f.smooth = True; fs.append(f)
            f = bm.faces.new((mid[i], mid[(i+1)%seg], apex)); f.material_index = 0; f.smooth = True; fs.append(f)
    for f in fs:
        for l in f.loops: l[tl] = tcol

# sampling
def slope(x, y, d=6.0):
    hx = terrain_h(x+d, y) - terrain_h(x-d, y)
    hy = terrain_h(x, y+d) - terrain_h(x, y-d)
    return math.hypot(hx, hy)/(2*d)

def tree_ok(x, y):
    r = math.hypot(x, y)
    if r < 175: return False   # castle grounds
    if r > 2050: return False
    h = terrain_h(x, y)
    if h < 6.5 or h > 115: return False
    if slope(x, y) > 0.75: return False
    # lake check
    th = math.atan2(y, x)
    import math as _m2
    Rlake = _lib['lake_R'](th)
    if r < Rlake + 25 and h < 8.5: return False
    # gorge banks keep sparse
    if abs(x) < 55 and -260 < y < -25: return False
    dens = fbm2(x*0.004+5.0, y*0.004-2.0, 4, 1.0, 71.3)
    dens = dens.real if isinstance(dens, complex) else dens
    alt = 1.0 - max(0.0, (h-70)/45.0)
    p = (0.15 + max(0.0, dens)**1.4) * alt
    return random.random() < p

ob = new_obj("Forest", "Nature")
bm = bmesh.new()
tl = bm.loops.layers.float_color.new("tint")
count = 0
GSTEP = 10.5
for gx in range(-2040, 2041, int(GSTEP)):
    for gy in range(-2040, 2041, int(GSTEP)):
        x = gx + random.uniform(-GSTEP/2, GSTEP/2)
        y = gy + random.uniform(-GSTEP/2, GSTEP/2)
        r = math.hypot(x, y)
        if 650 < r < 2050 and random.random() < 0.36:  # thin far field
            continue
        if not tree_ok(x, y): continue
        h = terrain_h(x, y)
        sc = random.uniform(0.75, 1.5) * (1.0 + 0.3*fbm2(x*0.01, y*0.01, 2, 1, 8.8))
        g = random.uniform(0.7, 1.3)
        tcol = (0.75*g, 1.05*g, 0.7*g, 1.0)
        tree_into(bm, x, y, h-0.3, sc, tcol, tl)
        count += 1
finish(ob, bm, smooth_deg=40)
ob.data.materials.append(MPINE)
# trunk mat slot
MTRUNK = bpy.data.materials.get("M_Trunk") or bpy.data.materials.new("M_Trunk")
MTRUNK.use_nodes = True
bs = MTRUNK.node_tree.nodes.get("Principled BSDF")
bs.inputs['Base Color'].default_value = (0.09, 0.065, 0.045, 1.0)
bs.inputs['Roughness'].default_value = 0.9
ob.data.materials.append(MTRUNK)

# ---------- boulders ----------
ob = new_obj("Boulders", "Nature")
bm = bmesh.new()
tl = bm.loops.layers.float_color.new("tint")
MROCK = bpy.data.materials["M_RockCliff"]
n_b = 0
for i in range(500):
    az = random.uniform(0, 2*math.pi)
    r = random.uniform(150, 1500)
    x, y = r*math.cos(az), r*math.sin(az)
    h = terrain_h(x, y)
    if h < 3.5: continue
    if math.hypot(x, y) < 175: continue
    sc = random.uniform(0.8, 5.0)
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=sc)
    new_vs = [v for v in bm.verts][-42:]
    bmesh.ops.scale(bm, vec=Vector((random.uniform(0.7,1.4), random.uniform(0.7,1.4), random.uniform(0.5,0.9))), verts=new_vs)
    bmesh.ops.translate(bm, vec=Vector((x, y, h - sc*0.2)), verts=new_vs)
    g = random.uniform(0.8, 1.2)
    for f in bm.faces:
        if all(v in new_vs for v in f.verts):
            for l in f.loops: l[tl] = (g, g, g, 1.0)
    n_b += 1
finish(ob, bm, smooth_deg=50)
ob.data.materials.append(MROCK)

bpy.context.scene.view_layers[0].update()
bpy.ops.wm.save_as_mainfile(filepath="/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/hogwarts.blend")
result = {"trees": count, "boulders": n_b,
          "forest_tris": len(bpy.data.objects['Forest'].data.polygons)}
