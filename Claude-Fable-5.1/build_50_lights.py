"""Pass 5 — moonlit night: moon sun, procedural night sky (moon, stars, clouds),
volumetric mist, lanterns, fill, compositor bloom."""
import bpy, os, sys, importlib, math
from mathutils import Vector
FOLDER = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else bpy.path.abspath("//")
if FOLDER not in sys.path:
    sys.path.insert(0, FOLDER)
import hog_lib as H; importlib.reload(H)
from hog_lib import NB
import hog_layout as L; importlib.reload(L)

scn = bpy.context.scene
H.clear_collection("Lights")
H.clear_collection("FX")

# --------------------------------------------------------------------------- moon
MOON_AZ = math.radians(34.0)      # compass azimuth (0 = +Y north, clockwise)
MOON_EL = math.radians(19.0)
moon_dir = Vector((math.sin(MOON_AZ) * math.cos(MOON_EL), math.cos(MOON_AZ) * math.cos(MOON_EL), math.sin(MOON_EL)))  # towards the moon
sun = bpy.data.lights.new("Moon", 'SUN')
sun.energy = 3.0
sun.angle = math.radians(3.2)   # soft enough that thin light shafts in the haze blur out
sun.color = (0.78, 0.86, 1.0)
try:
    sun.specular_factor = 0.3   # tame grazing-angle rim glints on backlit spires
except Exception:
    pass
so = bpy.data.objects.new("Moon", sun)
H.link_obj(so, "Lights")
so.rotation_euler = (-moon_dir).to_track_quat('-Z', 'Y').to_euler()   # sun lamps shine along their -Z
so.location = (0, 0, 400)

# soft cool fill from the camera side (cinematic "sky bounce")
fill = bpy.data.lights.new("Fill_SW", 'AREA')
fill.energy = 6.0e6
fill.color = (0.45, 0.76, 0.98)
fill.shape = 'DISK'; fill.size = 260.0
fo = bpy.data.objects.new("Fill_SW", fill)
H.link_obj(fo, "Lights")
fo.location = (-380, -1300, 420)
fo.rotation_euler = (Vector((20, 0, 70)) - fo.location).to_track_quat('-Z', 'Y').to_euler()
# light linking: the fill models surfaces only, never the mist (keeps the volume from glowing grey)
ll = bpy.data.collections.get("LL_Surfaces")
if ll is None:
    ll = bpy.data.collections.new("LL_Surfaces")
for cname in ("Castle", "Terrain", "Water", "Nature"):
    c = bpy.data.collections.get(cname)
    if c and c.name not in ll.children:
        ll.children.link(c)
try:
    fill.light_linking.receiver_collection = ll
except Exception:
    pass

# second, weaker fill from the east-south-east, low, raking across the south cliff and the boathouse stair
fill2 = bpy.data.lights.new("Fill_ESE", 'AREA')
fill2.energy = 2.2e6
fill2.color = (0.5, 0.72, 1.0)
fill2.shape = 'DISK'; fill2.size = 200.0
f2o = bpy.data.objects.new("Fill_ESE", fill2)
H.link_obj(f2o, "Lights")
f2o.location = (1300, -700, 260)
f2o.rotation_euler = (Vector((60, -60, 40)) - f2o.location).to_track_quat('-Z', 'Y').to_euler()
try:
    fill2.light_linking.receiver_collection = ll
except Exception:
    pass

# warm rim from the courtyards' collective glow is emissive geometry; add a faint warm bounce under the castle
warm = bpy.data.lights.new("Bounce_Castle", 'POINT')
warm.energy = 14000.0; warm.color = (1.0, 0.82, 0.62); warm.shadow_soft_size = 40.0
wo = bpy.data.objects.new("Bounce_Castle", warm)
H.link_obj(wo, "Lights"); wo.location = (30, 10, 95)

# --------------------------------------------------------------------------- lanterns
lan = list(scn.get("hog_lanterns", []))
pts = [(lan[i], lan[i + 1], lan[i + 2]) for i in range(0, len(lan) - 2, 3)]
lan2 = list(scn.get("hog_lanterns_extra", []))
pts_extra2 = [(lan2[i], lan2[i + 1], lan2[i + 2]) for i in range(0, len(lan2) - 2, 3)]
# courtyard / gate lanterns (fixed positions on the plateau)
extra = [(118, -44, 65.5), (110, -48, 64.5), (-40, -50, 74.0), (-8, -42, 74.5), (40, -48, 76.5), (0, 18, 76.0), (-30, 30, 75.5), (30, 34, 79.0),
         (20, 92, 63.5), (-8, 60, 72.0), (12, 60, 72.0), (100, 44, 62.0), (60, -70, 61.5), (30, -68, 61.5), (84, -68, 61.5)]
pts += extra + pts_extra2
lmat = bpy.data.materials.get("M_LanternGlass") or H.ensure_material("M_LanternGlass", (1, 0.6, 0.3, 1))
import bmesh
bm = bmesh.new()
for (x, y, z) in pts:
    H.bm_box(bm, (0.24, 0.24, 0.30), (x, y, z))
glass = H.finish_bmesh(bm, "Lantern_Glass", "Lights", mat=lmat)
n_stair = len(pts) - len(extra) - 12   # viaduct posts come first (12), then the stair, then the extras
for i, (x, y, z) in enumerate(pts):
    lt = bpy.data.lights.new(f"Lantern_{i:02d}", 'POINT')
    on_stair = 12 <= i < 12 + n_stair
    lt.energy = 2200.0 if on_stair else 700.0; lt.color = (1.0, 0.62, 0.30); lt.shadow_soft_size = 0.12
    lo = bpy.data.objects.new(f"Lantern_{i:02d}", lt)
    H.link_obj(lo, "Lights"); lo.location = (x, y, z)

# --------------------------------------------------------------------------- world: night sky
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scn.world = world
world.use_nodes = True
nb = NB(world.node_tree)
tc = nb.n("ShaderNodeTexCoord")
d = nb.n("ShaderNodeVectorMath", _operation='NORMALIZE', Vector=tc.outputs["Generated"])
dz = nb.n("ShaderNodeSeparateXYZ", Vector=d.outputs[0])
lp = nb.n("ShaderNodeLightPath")
# gradient: horizon glow -> zenith
horiz = nb.n("ShaderNodeMapRange", Value=dz.outputs["Z"], From__Min=-0.05, From__Max=0.55, To__Min=0.0, To__Max=1.0)
grad = nb.n("ShaderNodeValToRGB", Factor=horiz.outputs["Result"])
grad.color_ramp.elements[0].color = (0.010, 0.026, 0.060, 1)
e = grad.color_ramp.elements.new(0.35); e.color = (0.005, 0.013, 0.034, 1)
grad.color_ramp.elements[-1].color = (0.004, 0.008, 0.02, 1)
# moon disc + halo
md = nb.n("ShaderNodeVectorMath", _operation='DOT_PRODUCT', Vector=d.outputs[0], Vector_1=tuple(moon_dir))
disc = nb.n("ShaderNodeMapRange", Value=md.outputs["Value"], From__Min=math.cos(math.radians(1.05)), From__Max=math.cos(math.radians(0.75)), To__Min=0.0, To__Max=1.0)
halo1 = nb.n("ShaderNodeMapRange", Value=md.outputs["Value"], From__Min=math.cos(math.radians(9.0)), From__Max=1.0, To__Min=0.0, To__Max=1.0)
halo_p = nb.n("ShaderNodeMath", _operation='POWER', Value=halo1.outputs["Result"], Value_1=3.0)
halo2 = nb.n("ShaderNodeMapRange", Value=md.outputs["Value"], From__Min=math.cos(math.radians(45.0)), From__Max=1.0, To__Min=0.0, To__Max=1.0)
halo2p = nb.n("ShaderNodeMath", _operation='POWER', Value=halo2.outputs["Result"], Value_1=2.5)
# limb darkening / maria on the disc
mn = nb.n("ShaderNodeTexNoise", Vector=d.outputs[0], Scale=120.0, Detail=3.0)
mnv = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=mn.outputs["Factor"], Value_1=0.5, Value_2=0.7)
disc_v = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=disc.outputs["Result"], Value_1=mnv.outputs[0])
# stars: high-frequency voronoi points, hidden below the horizon
vor = nb.n("ShaderNodeTexVoronoi", Vector=d.outputs[0], Scale=260.0, _feature='F1', Randomness=1.0)
star_r = nb.n("ShaderNodeMapRange", Value=vor.outputs["Distance"], From__Min=0.055, From__Max=0.02, To__Min=0.0, To__Max=1.0)
star_p = nb.n("ShaderNodeMath", _operation='POWER', Value=star_r.outputs["Result"], Value_1=2.0)
star_bri = nb.n("ShaderNodeTexNoise", Vector=vor.outputs["Position"], Scale=50.0)
sb = nb.n("ShaderNodeMath", _operation='POWER', Value=star_bri.outputs["Factor"], Value_1=4.0)
stars0 = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=star_p.outputs[0], Value_1=sb.outputs[0])
above = nb.n("ShaderNodeMapRange", Value=dz.outputs["Z"], From__Min=0.02, From__Max=0.12, To__Min=0.0, To__Max=1.0)
stars = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=stars0.outputs[0], Value_1=above.outputs["Result"])
# clouds: fbm on a projected plane; brighter near the moon (rim-lit), occluding moon & stars
zc = nb.n("ShaderNodeMath", _operation='MAXIMUM', Value=dz.outputs["Z"], Value_1=0.06)
proj = nb.n("ShaderNodeVectorMath", _operation='DIVIDE', Vector=d.outputs[0], Vector_1=zc.outputs[0])
pm = nb.n("ShaderNodeMapping", Vector=proj.outputs[0], Scale=(0.55, 0.55, 0.0), Rotation=(0, 0, 0.35))
cn = nb.n("ShaderNodeTexNoise", Vector=pm.outputs["Vector"], Scale=1.0, Detail=7.0, Roughness=0.58, Lacunarity=2.1)
cn2 = nb.n("ShaderNodeTexNoise", Vector=pm.outputs["Vector"], Scale=0.35, Detail=3.0)
cmask = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=cn2.outputs["Factor"], Value_1=1.4, Value_2=-0.7)
cloud0 = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=cn.outputs["Factor"], Value_1=2.4, Value_2=cmask.outputs[0])
cloud1 = nb.n("ShaderNodeMapRange", Value=cloud0.outputs[0], From__Min=1.05, From__Max=1.75, To__Min=0.0, To__Max=1.0)
cloud_h = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=cloud1.outputs["Result"], Value_1=above.outputs["Result"])
# thin the clouds toward the horizon (perspective compression already helps)
cloud = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=cloud_h.outputs[0], Value_1=0.9)
occl = nb.n("ShaderNodeMath", _operation='SUBTRACT', Value=1.0, Value_1=cloud.outputs[0], _use_clamp=True)
# cloud shading: dark base, moon-lit edges
lit = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=halo2p.outputs[0], Value_1=7.0, Value_2=1.0)
edge = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=cloud1.outputs["Result"], Value_1=1.0)
edge_inv = nb.n("ShaderNodeMath", _operation='SUBTRACT', Value=1.3, Value_1=edge.outputs[0])
cloud_l0 = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=lit.outputs[0], Value_1=edge_inv.outputs[0])
cloud_l = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=cloud_l0.outputs[0], Value_1=cloud_h.outputs[0])
cloud_col = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=(0.075, 0.10, 0.14), Scale=cloud_l.outputs[0])
# assemble
sky = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=grad.outputs["Color"], Scale=1.0)
halo_gate = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=lp.outputs["Is Camera Ray"], Value_1=0.75, Value_2=0.25)
halo_pg = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=halo_p.outputs[0], Value_1=halo_gate.outputs[0])
halo_col = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=(0.16, 0.24, 0.40), Scale=halo_pg.outputs[0])
halo2_col = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=(0.018, 0.03, 0.055), Scale=halo2p.outputs[0])
s1 = nb.n("ShaderNodeVectorMath", _operation='ADD', Vector=sky.outputs[0], Vector_1=halo_col.outputs[0])
s2 = nb.n("ShaderNodeVectorMath", _operation='ADD', Vector=s1.outputs[0], Vector_1=halo2_col.outputs[0])
star_col = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=(1.6, 1.7, 2.0), Scale=stars.outputs[0])
s3 = nb.n("ShaderNodeVectorMath", _operation='ADD', Vector=s2.outputs[0], Vector_1=star_col.outputs[0])
# the drawn moon disc (and its bright core halo) are for camera rays only: the sun lamp carries the
# actual moonlight, and a 60x disc in glossy reflections paints hard rim lines along every spire silhouette
cam_only = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=disc_v.outputs[0], Value_1=lp.outputs["Is Camera Ray"])
moon_col = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=(60.0, 62.0, 66.0), Scale=cam_only.outputs[0])
s4 = nb.n("ShaderNodeVectorMath", _operation='ADD', Vector=s3.outputs[0], Vector_1=moon_col.outputs[0])
s5 = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=s4.outputs[0], Scale=occl.outputs[0])
s6 = nb.n("ShaderNodeVectorMath", _operation='MULTIPLY_ADD', Vector=cloud_col.outputs[0], Vector_1=(1, 1, 1), Vector_2=s5.outputs[0])
# below the horizon: keep it dark blue-grey (lake reflections of the sky need something)
below = nb.n("ShaderNodeMapRange", Value=dz.outputs["Z"], From__Min=-0.2, From__Max=0.0, To__Min=0.0, To__Max=1.0)
s7 = nb.n("ShaderNodeMix", _data_type='RGBA', Factor=below.outputs["Result"], A=(0.02, 0.03, 0.05, 1), B=s6.outputs[0])
bg = nb.n("ShaderNodeBackground", Color=nb.o(s7, "Result"), Strength=1.0)
# light path: camera rays see the full sky; lighting uses a smoother version to keep noise down
out = nb.n("ShaderNodeOutputWorld")
nb.link(bg.outputs[0], out.inputs["Surface"])
try:
    world.cycles.sampling_method = 'MANUAL'
    world.cycles.sample_map_resolution = 2048
except Exception:
    pass

# --------------------------------------------------------------------------- mist volume
bm = bmesh.new()
H.bm_box(bm, (3600.0, 3600.0, 320.0), (0.0, 0.0, 150.0))
mist = H.finish_bmesh(bm, "FX_Mist", "FX", mat=None)
mm = bpy.data.materials.get("M_Mist") or bpy.data.materials.new("M_Mist")
mm.use_nodes = True
nb = NB(mm.node_tree)
geo = nb.n("ShaderNodeNewGeometry")
pos = nb.n("ShaderNodeSeparateXYZ", Vector=geo.outputs["Position"])
# height falloff: exp(-(z)/H) — dense over the lake, thinning upward; valleys pool
hz = nb.n("ShaderNodeMath", _operation='DIVIDE', Value=pos.outputs["Z"], Value_1=-9.0)
ex = nb.n("ShaderNodeMath", _operation='EXPONENT', Value=hz.outputs[0])
mp = nb.n("ShaderNodeMapping", Vector=geo.outputs["Position"], Scale=(1.0, 1.0, 2.5))
n1 = nb.n("ShaderNodeTexNoise", Vector=mp.outputs["Vector"], Scale=0.004, Detail=5.0, Roughness=0.6)
n1v = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=n1.outputs["Factor"], Value_1=3.0, Value_2=-1.15, _use_clamp=True)
n2 = nb.n("ShaderNodeTexNoise", Vector=mp.outputs["Vector"], Scale=0.02, Detail=3.0)
n2v = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=n2.outputs["Factor"], Value_1=0.8, Value_2=0.5)
mist_d = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=ex.outputs[0], Value_1=n1v.outputs[0])
mist_d2 = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=mist_d.outputs[0], Value_1=n2v.outputs[0])
dens_lake = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=mist_d2.outputs[0], Value_1=0.007)
# global haze for aerial perspective (thins with height)
hz2 = nb.n("ShaderNodeMath", _operation='DIVIDE', Value=pos.outputs["Z"], Value_1=-900.0)
ex2 = nb.n("ShaderNodeMath", _operation='EXPONENT', Value=hz2.outputs[0])
haze = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=ex2.outputs[0], Value_1=0.00009)
dens = nb.n("ShaderNodeMath", _operation='ADD', Value=dens_lake.outputs[0], Value_1=haze.outputs[0])
vol = nb.n("ShaderNodePrincipledVolume" if hasattr(bpy.types, "ShaderNodePrincipledVolume") else "ShaderNodeVolumePrincipled")
vol.inputs["Color"].default_value = (0.62, 0.78, 1.0, 1)
vol.inputs["Anisotropy"].default_value = 0.25
nb.link(dens.outputs[0], vol.inputs["Density"])
out = nb.n("ShaderNodeOutputMaterial")
nb.link(vol.outputs[0], out.inputs["Volume"])
mist.data.materials.append(mm)
mist.display_type = 'WIRE'
try:
    mm.volume_step_rate = 1.0
except Exception:
    pass

# --------------------------------------------------------------------------- render look
scn.cycles.volume_step_rate = 1.0
scn.cycles.volume_max_steps = 256
scn.view_settings.view_transform = 'AgX'
try:
    scn.view_settings.look = 'AgX - Punchy'
except Exception:
    pass
scn.view_settings.exposure = 0.45
scn.cycles.film_exposure = 1.0

# --------------------------------------------------------------------------- compositor: bloom
glare_info = None
ct = None
try:
    ng = bpy.data.node_groups.get("HogComp")
    if ng is None:
        ng = bpy.data.node_groups.new("HogComp", 'CompositorNodeTree')
    scn.compositing_node_group = ng
    ct = ng
    ng.nodes.clear()
    if not any(i.item_type == 'SOCKET' and i.in_out == 'OUTPUT' for i in ng.interface.items_tree):
        ng.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    rl = ng.nodes.new("CompositorNodeRLayers")
    glare = ng.nodes.new("CompositorNodeGlare")
    glare_info = {"props": [pp.identifier for pp in glare.bl_rna.properties][:40], "inputs": [i.name for i in glare.inputs]}
    for sock, val in (("Type", 'Bloom'), ("Quality", 'High')):
        if sock in glare.inputs:
            try:
                glare.inputs[sock].default_value = val
            except Exception:
                pass
    for attr, val in (("quality", 'HIGH'), ("mix", -0.55), ("threshold", 1.2), ("size", 7)):
        try:
            setattr(glare, attr, val)
        except Exception:
            pass
    for name, val in (("Threshold", 1.5), ("Strength", 0.14), ("Size", 0.6), ("Smoothness", 0.25), ("Saturation", 1.0)):
        if name in glare.inputs:
            try:
                glare.inputs[name].default_value = val
            except Exception:
                pass
    go = ng.nodes.new("NodeGroupOutput")
    ng.links.new(rl.outputs["Image"], glare.inputs["Image"])
    ng.links.new(glare.outputs["Image"], go.inputs[0])
except Exception as e:
    glare_info = {"error": repr(e)}

result = {"lanterns": len(pts), "moon_dir": [round(c, 3) for c in moon_dir], "comp": ct.name if ct else None, "glare": glare_info}
