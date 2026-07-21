import bpy, math, random
from mathutils import Vector, noise
from math import sin, cos, pi, hypot

N = bpy.data.collections["Nature"]
T = bpy.data.collections["Terrain"]
fol = mat_foliage()
trk = mat_trunk()

# ============================================================ TREE PROTOTYPES
AC = bpy.data.collections.new("TreeAssets")
bpy.context.scene.collection.children.link(AC)
AC.hide_render = True
AC.hide_viewport = True

def make_conifer(name, h, r, layers, seed):
    random.seed(seed)
    verts, faces = [], []
    # trunk
    tb = len(verts)
    th = h*0.22
    seg = 7
    for i in range(seg):
        a = i/seg*2*pi
        verts.append((0.16*cos(a), 0.16*sin(a), 0))
        verts.append((0.11*cos(a), 0.11*sin(a), th))
    for i in range(seg):
        i2 = (i+1)%seg
        faces.append((tb+i*2, tb+i2*2, tb+i2*2+1, tb+i*2+1))
    # cone layers
    z = th*0.5
    for li in range(layers):
        frac = li/layers
        cr = r*(1-frac*0.75)*random.uniform(0.9,1.1)
        ch = h*(1-frac)*0.42
        z0 = z
        z1 = z + ch
        b = len(verts)
        seg2 = 8
        for i in range(seg2):
            a = i/seg2*2*pi
            rr = cr*(1+0.12*noise.noise(Vector((a*2, li*3, seed))))
            verts.append((rr*cos(a), rr*sin(a), z0))
        apex = b+seg2
        verts.append((random.uniform(-0.1,0.1), random.uniform(-0.1,0.1), z1))
        for i in range(seg2):
            faces.append((b+i, b+(i+1)%seg2, apex))
        faces.append(tuple(b+i for i in range(seg2))[::-1])
        z = z0 + ch*0.55
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces); me.update()
    ob = bpy.data.objects.new(name, me)
    AC.objects.link(ob)
    me.materials.append(fol)
    me.materials.append(trk)
    # trunk faces -> material 1
    for pi_, poly in enumerate(me.polygons):
        poly.material_index = 1 if pi_ < seg else 0
        poly.use_smooth = True
    return ob

t1 = make_conifer("Conifer_A", 14, 3.4, 5, 11)
t2 = make_conifer("Conifer_B", 10, 2.8, 4, 23)
t3 = make_conifer("Conifer_C", 18, 4.2, 6, 37)

# ============================================================ FOREST DENSITY ATTRIBUTE on Moor
moor = bpy.data.objects["Moor"]
me = moor.data
attr = me.attributes.new("forest", 'FLOAT', 'POINT')
crag_c = Vector((0,-5))
for i, v in enumerate(me.vertices):
    x, y, z = v.co.x, v.co.y, v.co.z
    d = hypot(x-crag_c.x, y-crag_c.y)
    f = 0.0
    if z > 1.5 and z < 95 and d > 135:
        # noise clumping; denser in valleys (low z), thinner high up
        cl = noise.noise(Vector((x*0.006, y*0.006, 4.2)))
        base = 1.0 - (z/95)*0.7
        f = max(0.0, base*(0.35 + 0.9*max(0.0, cl)))
        # keep castle grounds + connector clear
        if d < 200 and y > -20:
            f *= max(0.0, (d-140)/60)
        # gorge/viaduct corridor clear
        if 80 < x < 320 and -40 < y < 50:
            f = 0.0
        # hut clearing
        if hypot(x-380, y-60) < 30:
            f = 0.0
    attr.data[i].value = f

# slope check via normals would need update; approximate ok

# ============================================================ GEOMETRY NODES SCATTER
ng = bpy.data.node_groups.new("ForestScatter", 'GeometryNodeTree')
ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
n_in = ng.nodes.new("NodeGroupInput"); n_in.location = (-700, 100)
n_out = ng.nodes.new("NodeGroupOutput"); n_out.location = (500, 100)
dist = ng.nodes.new("GeometryNodeDistributePointsOnFaces"); dist.location = (-450, 100)
dist.distribute_method = 'RANDOM'
dist.inputs["Density"].default_value = 0.004
named = ng.nodes.new("GeometryNodeInputNamedAttribute"); named.location = (-700, -150)
named.data_type = 'FLOAT'
named.inputs["Name"].default_value = "forest"
mul = ng.nodes.new("ShaderNodeMath"); mul.operation='MULTIPLY'; mul.location = (-450, -150)
mul.inputs[1].default_value = 0.006
col = ng.nodes.new("GeometryNodeCollectionInfo"); col.location = (-450, -400)
col.inputs["Collection"].default_value = AC
col.inputs["Separate Children"].default_value = True
col.inputs["Reset Children"].default_value = True
inst = ng.nodes.new("GeometryNodeInstanceOnPoints"); inst.location = (-100, 100)
inst.inputs["Pick Instance"].default_value = True
rnd_s = ng.nodes.new("FunctionNodeRandomValue"); rnd_s.data_type='FLOAT_VECTOR'; rnd_s.location = (-100, -250)
rnd_s.inputs["Min"].default_value = (0.7, 0.7, 0.7)
rnd_s.inputs["Max"].default_value = (1.5, 1.5, 1.6)
rnd_r = ng.nodes.new("FunctionNodeRandomValue"); rnd_r.data_type='FLOAT_VECTOR'; rnd_r.location = (-100, -450)
rnd_r.inputs["Min"].default_value = (0, 0, 0)
rnd_r.inputs["Max"].default_value = (0.06, 0.06, 6.283)
ng.links.new(n_in.outputs["Geometry"], dist.inputs["Mesh"])
ng.links.new(named.outputs["Attribute"], mul.inputs[0])
ng.links.new(mul.outputs[0], dist.inputs["Density"])
ng.links.new(dist.outputs["Points"], inst.inputs["Points"])
ng.links.new(col.outputs["Instances"], inst.inputs["Instance"])
ng.links.new(rnd_s.outputs["Value"], inst.inputs["Scale"])
ng.links.new(rnd_r.outputs["Value"], inst.inputs["Rotation"])
ng.links.new(inst.outputs["Instances"], n_out.inputs["Geometry"])
mod = moor.modifiers.new("Forest", 'NODES')
mod.node_group = ng

# ============================================================ HERO FOREGROUND TREES (detailed, near shore)
for i in range(14):
    x = random.uniform(240, 420) * random.choice([1, 1]) + random.uniform(-40, 40)
    y = random.uniform(-420, -260)
    z = terrain_h(x, y)
    if z < 0.5:
        continue
    proto = random.choice([t1, t2, t3])
    ob = bpy.data.objects.new(f"HeroTree_{i}", proto.data)
    N.objects.link(ob)
    ob.location = (x, y, z-0.3)
    s = random.uniform(0.9, 1.7)
    ob.scale = (s, s, s*random.uniform(0.95, 1.2))
    ob.rotation_euler[2] = random.uniform(0, 6.28)

# west shore cluster
for i in range(10):
    x = random.uniform(-420, -260)
    y = random.uniform(-300, -120)
    z = terrain_h(x, y)
    if z < 0.5:
        continue
    proto = random.choice([t1, t2, t3])
    ob = bpy.data.objects.new(f"WestTree_{i}", proto.data)
    N.objects.link(ob)
    ob.location = (x, y, z-0.3)
    s = random.uniform(0.8, 1.5)
    ob.scale = (s, s, s)

# pines clinging to south crag ledges
crag_pines = [(-55,-68,14), (-30,-78,22), (-15,-82,10), (5,-85,18), (22,-78,8),
              (-48,-60,30), (-8,-70,28), (15,-68,34), (-60,-45,38), (40,-60,42)]
for i, (px, py, pz) in enumerate(crag_pines):
    proto = [t1, t2, t3][i % 3]
    ob = bpy.data.objects.new(f"CragPine_{i}", proto.data)
    N.objects.link(ob)
    ob.location = (px, py, pz)
    s = 0.5 + (i % 4)*0.18
    ob.scale = (s, s, s)
    ob.rotation_euler[2] = i*1.7

result = {"nature": "built", "trees_est": "gn", "objects": len(bpy.data.objects)}
