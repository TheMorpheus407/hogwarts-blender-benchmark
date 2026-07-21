import bpy, math
from mathutils import Vector
from math import pi, sin, cos

L = bpy.data.collections["Lights"]
FX = bpy.data.collections["FX"]
CAM = bpy.data.collections["Cameras"]

# ============================================================ WORLD: night sky, stars, clouds, moon glow
w = bpy.data.worlds["World"]
nt = w.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputWorld"); out.location = (900, 0)
bg = nt.nodes.new("ShaderNodeBackground"); bg.location = (650, 0)
tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-1200, 0)
sep = nt.nodes.new("ShaderNodeSeparateXYZ"); sep.location = (-1000, 200)
# vertical gradient: deep blue zenith -> teal horizon
grad = nt.nodes.new("ShaderNodeValToRGB"); grad.location = (-750, 300)
grad.color_ramp.elements[0].position = 0.0
grad.color_ramp.elements[0].color = (0.030, 0.075, 0.125, 1)
grad.color_ramp.elements[1].position = 0.55
grad.color_ramp.elements[1].color = (0.006, 0.012, 0.030, 1)
e = grad.color_ramp.elements.new(0.25); e.color = (0.015, 0.040, 0.065, 1)
# stars: voronoi distance tiny
vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.location = (-750, -100)
vor.distance = 'EUCLIDEAN'
vor.feature = 'F1'
vor.inputs["Scale"].default_value = 220.0
sramp = nt.nodes.new("ShaderNodeValToRGB"); sramp.location = (-500, -100)
sramp.color_ramp.elements[0].position = 0.0
sramp.color_ramp.elements[0].color = (2.2, 2.3, 2.5, 1)
sramp.color_ramp.elements[1].position = 0.045
sramp.color_ramp.elements[1].color = (0, 0, 0, 1)
# clouds: stretched noise
mapping = nt.nodes.new("ShaderNodeMapping"); mapping.location = (-950, -450)
mapping.inputs["Scale"].default_value = (1.0, 1.0, 3.0)
cn = nt.nodes.new("ShaderNodeTexNoise"); cn.location = (-700, -450)
cn.inputs["Scale"].default_value = 1.6
cn.inputs["Detail"].default_value = 5.0
cn.inputs["Roughness"].default_value = 0.7
cramp = nt.nodes.new("ShaderNodeValToRGB"); cramp.location = (-450, -450)
cramp.color_ramp.elements[0].position = 0.44
cramp.color_ramp.elements[0].color = (0,0,0,1)
cramp.color_ramp.elements[1].position = 0.72
cramp.color_ramp.elements[1].color = (0.09, 0.15, 0.19, 1)
# moon glow: dot with moon direction
import math as _m2
_az, _el = _m2.radians(-13.0), _m2.radians(13.0)
moon_dir = Vector((_m2.sin(_az)*_m2.cos(_el), _m2.cos(_az)*_m2.cos(_el), _m2.sin(_el))).normalized()
vdot = nt.nodes.new("ShaderNodeVectorMath"); vdot.operation='DOT_PRODUCT'; vdot.location = (-750, -750)
vdot.inputs[1].default_value = tuple(moon_dir)
mramp = nt.nodes.new("ShaderNodeValToRGB"); mramp.location = (-480, -750)
mramp.color_ramp.elements[0].position = 0.85
mramp.color_ramp.elements[0].color = (0,0,0,1)
mramp.color_ramp.elements[1].position = 0.995
mramp.color_ramp.elements[1].color = (0.55, 0.68, 0.82, 1)
# combine: base gradient + stars*(1-cloud) + cloud + moonglow
add1 = nt.nodes.new("ShaderNodeMixRGB"); add1.blend_type='ADD'; add1.location = (-150, 200)
add2 = nt.nodes.new("ShaderNodeMixRGB"); add2.blend_type='ADD'; add2.location = (100, 100)
add3 = nt.nodes.new("ShaderNodeMixRGB"); add3.blend_type='ADD'; add3.location = (350, 50)
clmul = nt.nodes.new("ShaderNodeMixRGB"); clmul.blend_type='MULTIPLY'; clmul.location = (-250, -50)
inv = nt.nodes.new("ShaderNodeInvert"); inv.location = (-250, -300)
nt.links.new(tc.outputs["Normal"], sep.inputs[0])
nt.links.new(tc.outputs["Normal"], mapping.inputs["Vector"])
nt.links.new(tc.outputs["Normal"], vdot.inputs[0])
nt.links.new(sep.outputs["Z"], grad.inputs["Fac"])
nt.links.new(tc.outputs["Normal"], vor.inputs["Vector"])
nt.links.new(vor.outputs["Distance"], sramp.inputs["Fac"])
nt.links.new(mapping.outputs["Vector"], cn.inputs["Vector"])
nt.links.new(cn.outputs["Fac"], cramp.inputs["Fac"])
nt.links.new(cramp.outputs["Color"], inv.inputs["Color"])
nt.links.new(sramp.outputs["Color"], clmul.inputs[1])
nt.links.new(inv.outputs["Color"], clmul.inputs[2])
nt.links.new(grad.outputs["Color"], add1.inputs[1])
nt.links.new(clmul.outputs["Color"], add1.inputs[2])
nt.links.new(add1.outputs["Color"], add2.inputs[1])
nt.links.new(cramp.outputs["Color"], add2.inputs[2])
nt.links.new(add2.outputs["Color"], add3.inputs[1])
nt.links.new(mramp.outputs["Color"], add3.inputs[2])
nt.links.new(vdot.outputs["Value"], mramp.inputs["Fac"])
nt.links.new(add3.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.3
nt.links.new(bg.outputs[0], out.inputs["Surface"])

# ============================================================ MOON DISC
moon_mat = mat_moon()
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, radius=55)
moon = bpy.context.active_object
moon.name = "MoonDisc"
move_to_col(moon, FX)
mdir = moon_dir
campos = Vector((185,-455,9))
moon.location = tuple(campos + mdir * 2400)
moon.scale = (1.25,1.25,1.25)
moon.data.materials.append(moon_mat)

# key sun aligned with moon direction
sd = bpy.data.lights.new("MoonKey", 'SUN')
sd.energy = 3.0
sd.color = (0.53, 0.66, 0.94)
sd.angle = 0.02
so = bpy.data.objects.new("MoonKey", sd)
L.objects.link(so)
d = -mdir
so.rotation_euler = d.to_track_quat('-Z','Y').to_euler()

# ============================================================ MIST over lake (layered volumes)
def mist_box(name, loc, dims, density, noise_scale, col=(0.35,0.45,0.55,1)):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree; n.nodes.clear()
    o = n.nodes.new("ShaderNodeOutputMaterial")
    pv = n.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Color"].default_value = col
    pv.inputs["Anisotropy"].default_value = 0.25
    nz = n.nodes.new("ShaderNodeTexNoise")
    nz.noise_dimensions = '4D'
    nz.inputs["Scale"].default_value = noise_scale
    nz.inputs["Detail"].default_value = 3.0
    nz.inputs["Roughness"].default_value = 0.75
    nz.inputs["W"].default_value = 0.6
    ramp = n.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (0,0,0,1)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (density, density, density, 1)
    tcl = n.nodes.new("ShaderNodeTexCoord")
    n.links.new(tcl.outputs["Generated"], nz.inputs["Vector"])
    n.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    n.links.new(ramp.outputs["Color"], pv.inputs["Density"])
    n.links.new(pv.outputs["Volume"], o.inputs["Volume"])
    bpy.ops.mesh.primitive_cube_add(location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (dims[0]/2, dims[1]/2, dims[2]/2)
    bpy.ops.object.transform_apply(scale=True)
    move_to_col(ob, FX)
    ob.data.materials.append(m)
    ob.display_type = 'WIRE'
    return ob

mist_box("MistLake_Low", (0, -150, 3.0), (1300, 900, 7.0), 0.011, 0.012, col=(0.22,0.28,0.36,1))
mist_box("MistLake_High", (-50, -50, 14.0), (1500, 1100, 22.0), 0.0045, 0.006, col=(0.2,0.26,0.34,1))
mist_box("MistValley", (250, 300, 30), (900, 700, 45), 0.006, 0.008, col=(0.2,0.26,0.34,1))

# ============================================================ CLOUD LAYER (high volume slabs)
def cloud_box(name, loc, dims, density):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree; n.nodes.clear()
    o = n.nodes.new("ShaderNodeOutputMaterial")
    pv = n.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Color"].default_value = (0.10, 0.14, 0.18, 1)
    pv.inputs["Anisotropy"].default_value = 0.4
    nz = n.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.8
    nz.inputs["Detail"].default_value = 6.0
    nz.inputs["Roughness"].default_value = 0.72
    mp = n.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 1.0, 3.5)
    ramp = n.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.42
    ramp.color_ramp.elements[0].color = (0,0,0,1)
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = (density,density,density,1)
    tcl = n.nodes.new("ShaderNodeTexCoord")
    n.links.new(tcl.outputs["Generated"], mp.inputs["Vector"])
    n.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    n.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    n.links.new(ramp.outputs["Color"], pv.inputs["Density"])
    n.links.new(pv.outputs["Volume"], o.inputs["Volume"])
    bpy.ops.mesh.primitive_cube_add(location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (dims[0]/2, dims[1]/2, dims[2]/2)
    bpy.ops.object.transform_apply(scale=True)
    move_to_col(ob, FX)
    ob.data.materials.append(m)
    ob.display_type = 'WIRE'
    return ob

# ============================================================ PRACTICAL LIGHTS (warm points)
def point_warm(name, loc, energy=400, color=(1.0, 0.55, 0.22), radius=0.4):
    ld = bpy.data.lights.new(name, 'POINT')
    ld.energy = energy
    ld.color = color
    ld.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, ld)
    L.objects.link(ob)
    ob.location = loc
    return ob

# viaduct lanterns (matching posts every 2 spans)
for i in range(0, 11):
    x = i*20.0
    for sgn in (-1,1):
        ax = 0.13636  # axis angle approx atan2(28,205)
        lx = 95 + cos(ax)*x - sin(ax)*sgn*3.9
        ly = -8 + sin(ax)*x + cos(ax)*sgn*3.9
        import math as _m
        z = 56.0 + 2.2*_m.sin(_m.pi*x/210) + 5.4
        point_warm(f"VL_{i}_{sgn}", (lx, ly, z), energy=250)
# stair lanterns
for i, e in enumerate([(40,-95,12),(56,-88,24),(34,-72,36),(32,-54,50.5)]):
    point_warm(f"SL_{i}", (e[0], e[1], e[2]+3.0), energy=200)
point_warm("BH_light", (37, -92, 6), energy=500)
point_warm("Gate_light", (92, -10, 60), energy=600)
point_warm("Hut_light", (380, 58, 26), energy=250)
# courtyard glow
point_warm("Court_light", (12, -14, 58), energy=700)
# great hall interior bounce
point_warm("GH_interior", (-56, 8, 62), energy=2500, color=(1.0,0.6,0.3), radius=3.0)

fsd = bpy.data.lights.new("FillSouth", 'SUN')
fsd.energy = 0.8
fsd.color = (0.40, 0.50, 0.72)
fso = bpy.data.objects.new("FillSouth", fsd)
L.objects.link(fso)
fso.rotation_euler = (pi/2.1, 0, pi)

bpy.context.scene.view_settings.exposure = 1.0

def area_light(name, loc, target, energy, color, size):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy
    ld.color = color
    ld.shape = 'DISK'
    ld.size = size
    ob = bpy.data.objects.new(name, ld)
    L.objects.link(ob)
    ob.location = loc
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z','Y').to_euler()
    return ob

area_light("CragWash_S", (160, -210, 70), (-20, -40, 30), 45000, (0.35, 0.48, 0.70), 90)
area_light("CragWarm_S", (70, -150, 12), (20, -55, 35), 18000, (1.0, 0.55, 0.25), 50)
area_light("CragWash_W", (-220, -120, 50), (-40, -20, 30), 30000, (0.30, 0.42, 0.65), 70)
point_warm("TerraceSpill1", (-40, -50, 56), energy=900, radius=2.0)
point_warm("TerraceSpill2", (40, -48, 56), energy=900, radius=2.0)
point_warm("TerraceSpill3", (0, -30, 60), energy=700, radius=2.0)

# compositor: subtle fog glow on brights
scn = bpy.context.scene
cn = bpy.data.node_groups.get("CompGlow")
if cn is None:
    cn = bpy.data.node_groups.new("CompGlow", 'CompositorNodeTree')
cn.nodes.clear()
cn.interface.new_socket("Image", in_out='INPUT', socket_type='NodeSocketColor')
cn.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
scn.compositing_node_group = cn
rl = cn.nodes.new("NodeGroupInput")
gl = cn.nodes.new("CompositorNodeGlare")
gl.inputs['Type'].default_value = 'Fog Glow'
gl.inputs['Quality'].default_value = 'High'
gl.inputs['Threshold'].default_value = 1.2
gl.inputs['Size'].default_value = 0.7
gl.inputs['Strength'].default_value = 1.0
comp = cn.nodes.new("NodeGroupOutput")
cn.links.new(rl.outputs["Image"], gl.inputs["Image"])
cn.links.new(gl.outputs["Image"], comp.inputs["Image"])

result = {"lighting": "built"}
