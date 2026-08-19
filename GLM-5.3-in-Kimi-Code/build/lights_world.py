# Night sky world, moonlight sun, fill lights, mist volumes
import bpy, math
from mathutils import Vector
exec(compile(open("/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/build/mat_common.py").read(), "mat_common.py", "exec"))

scn = bpy.context.scene

# ---------- World: procedural night sky ----------
w = bpy.data.worlds.get("NightSky") or bpy.data.worlds.new("NightSky")
if w.use_nodes is False: w.use_nodes = True
nt = w.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_WORLD': nt.nodes.remove(n)
out = nt.nodes.get("World Output") or nt.nodes.new("ShaderNodeOutputWorld")
bg = mknode(nt, "ShaderNodeBackground", (400, 0))

geo = mknode(nt, "ShaderNodeNewGeometry", (-1500, 0))
inc = geo.outputs['Incoming']
sep = mknode(nt, "ShaderNodeSeparateXYZ", (-1350, 100)); L(nt, inc, 0, sep, 0)
zen = sep.outputs[2]

# base gradient: deep zenith -> slightly pale horizon
base = mixc(nt, rgb(nt, (0.012, 0.020, 0.045), (-1100, 300)),
                rgb(nt, (0.055, 0.075, 0.125), (-1100, 180)),
                clampn(nt, mathn(nt, 'SUBTRACT', 1.0, zen, loc=(-1100, 60)), 0, 1), loc=(-900, 220))

# moon: direction vector
MOON = Vector((-0.42, 0.80, 0.43)).normalized()
mdot = mknode(nt, "ShaderNodeVectorMath", (-1350, -150)); mdot.operation = 'DOT_PRODUCT'
L(nt, inc, 0, mdot, 0)
mvec = mknode(nt, "ShaderNodeCombineXYZ", (-1500, -250))
mvec.inputs[0].default_value = MOON.x; mvec.inputs[1].default_value = MOON.y; mvec.inputs[2].default_value = MOON.z
L(nt, mvec, 0, mdot, 1)
cosr = mdot.outputs['Value']
disc_edge = val(nt, math.cos(math.radians(1.6)), (-1200, -150))
halo_edge = val(nt, math.cos(math.radians(14.0)), (-1200, -260))
disc_f = mathn(nt, 'GREATER_THAN', cosr, disc_edge, loc=(-1000, -150))
halo_f = clampn(nt, mathn(nt, 'DIVIDE', mathn(nt, 'SUBTRACT', cosr, halo_edge, loc=(-1000,-300)),
                          mathn(nt, 'SUBTRACT', 1.0, halo_edge, loc=(-1000,-380)), loc=(-950,-300)), 0, 1, loc=(-900,-300))
halo_pow = mathn(nt, 'POWER', halo_f, 3.0, loc=(-800, -300))
# subtle craters on disc
mn = noise(nt, 6.0, 4, loc=(-1000, -40), vec=inc)
moon_col_base = rgb(nt, (0.92, 0.94, 1.0), (-900, -60))
moon_col = mixc(nt, moon_col_base, rgb(nt, (0.72, 0.76, 0.86), (-900, -140)), mathn(nt, 'MULTIPLY', mn.outputs['Fac'], 0.5), loc=(-750, -80))
moon_add = mathn(nt, 'MULTIPLY', disc_f, 3.5, loc=(-700, -150))
# stars
st = mknode(nt, "ShaderNodeTexVoronoi", (-1300, 400)); st.inputs['Scale'].default_value = 240.0
L(nt, inc, 0, st, 0)
star_sel = mathn(nt, 'LESS_THAN', st.outputs['Distance'], 0.014, loc=(-1100, 400))
stsep = mknode(nt, "ShaderNodeSeparateColor", (-1100, 560)); L(nt, st.outputs['Color'], 0, stsep, 0)
star_bright = mathn(nt, 'MULTIPLY', mathn(nt, 'POWER', stsep.outputs[0], 6.0, loc=(-1000, 560)), 6.0, loc=(-950, 500))
stars = mathn(nt, 'MULTIPLY', star_sel, star_bright, loc=(-800, 440))
# mask stars near horizon and inside moon halo
horizon_mask = clampn(nt, mathn(nt, 'SUBTRACT', zen, 0.02, loc=(-800, 620)), 0, 1, loc=(-700, 620))
stars = mathn(nt, 'MULTIPLY', stars, horizon_mask, loc=(-620, 480))
# clouds: subtle stratus
cl = noise(nt, 1.6, 5, loc=(-1300, 800), roughness=0.6, distortion=1.5, vec=inc)
cl_f = mathn(nt, 'POWER', mathn(nt, 'MULTIPLY', cl.outputs['Fac'], 1.25, loc=(-1100, 800)), 2.0, loc=(-950, 800))
cl_f = mathn(nt, 'MULTIPLY', cl_f, clampn(nt, mathn(nt, 'SUBTRACT', zen, 0.0, loc=(-950, 980)), 0, 1), loc=(-800, 840))
cloud_col = mixc(nt, base, rgb(nt, (0.06, 0.07, 0.10), (-700, 700)), mathn(nt, 'MULTIPLY', cl_f, 0.55), loc=(-520, 620))

sky_col = cloud_col
# combine: background color = sky; moon disc adds emission via Add (mix ADD)
with_moon = mixc(nt, sky_col, moon_col, disc_f, loc=(-500, -150))
bg_col = with_moon
bg.inputs[0].default_value = (0.02, 0.03, 0.05, 1.0)
L(nt, bg_col, 0, bg, 0)
bg.inputs[1].default_value = 1.0
# add star + halo brightness by math on color? approximate: add via mix ADD on color
add_stars = mixc(nt, bg_col, rgb(nt, (1.0, 1.0, 1.0), (-500, 300)), clampn(nt, stars, 0, 1, loc=(-560, 440)), loc=(-380, 240))
add_stars.node.blend_type = 'ADD'
L(nt, add_stars, 0, bg, 0)
add_halo = mixc(nt, add_stars, rgb(nt, (0.45, 0.55, 0.8), (-380, -260)), clampn(nt, mathn(nt, 'MULTIPLY', halo_pow, 0.8, loc=(-380,-330)), 0, 1, loc=(-320,-260)), loc=(-200, 0))
add_halo.node.blend_type = 'ADD'
L(nt, add_halo, 0, bg, 0)
add_moon = mixc(nt, add_halo, moon_col, clampn(nt, mathn(nt, 'MULTIPLY', disc_f, moon_add, loc=(-200,-150)), 0, 5, loc=(-140,-150)), loc=(0, 0))
add_moon.node.blend_type = 'ADD'
L(nt, add_moon, 0, bg, 0)
L(nt, bg.outputs[0], 0, out, 0)
scn.world = w

# ---------- Moon sun light ----------
sun_ob = bpy.data.objects.get("MoonSun")
sun = sun_ob.data
sun.type = 'SUN'
sun.energy = 1.6
sun.angle = math.radians(1.2)
sun.color = (0.55, 0.68, 1.0)
# sun direction: light travels along -moon_dir
target = -MOON
sun_ob.rotation_euler = target.to_track_quat('-Z', 'Y').to_euler()

# ---------- warm practical point lights ----------
Lc = bpy.data.collections['Lights']
def plight(name, p, energy, color=(1.0, 0.6, 0.3), radius=1.5):
    ob = bpy.data.objects.get(name)
    if ob: bpy.data.objects.remove(ob, do_unlink=True)
    ld = bpy.data.lights.new(name, 'POINT')
    ld.energy = energy; ld.color = color; ld.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, ld)
    Lc.objects.link(ob)
    ob.location = p
    return ob

plight("PL_GateCourt", (0, -34, 50), 800, (1.0, 0.62, 0.30), 3.0)
plight("PL_Boathouse", (-84, -62, 5), 1200, (1.0, 0.55, 0.25), 4.0)
plight("PL_Esplanade", (0, -258, 47), 600, (1.0, 0.6, 0.3), 3.0)
plight("PL_Greenhouse", (56, -36, 36), 900, (0.6, 0.9, 0.7), 5.0)
plight("PL_MainTower", (30, -4, 100), 300, (1.0, 0.7, 0.4), 2.5)

# ---------- mist volumes ----------
FX = bpy.data.collections['FX']
def mistbox(name, center, size, density=0.006, aniso=0.55, noise_scale=0.02, noise_amount=0.8, height_fade=True):
    ob = bpy.data.objects.get(name)
    if ob: bpy.data.objects.remove(ob, do_unlink=True)
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    outn = nt.nodes.get("Material Output")
    vol = mknode(nt, "ShaderNodeVolumePrincipled", (100, 0))
    vol.inputs['Density'].default_value = density
    try: vol.inputs['Anisotropy'].default_value = aniso
    except Exception: pass
    col = rgb(nt, (0.55, 0.65, 0.85), (-200, 200))
    L(nt, col, 0, vol, "Color")
    E = rgb(nt, (0.0, 0.0, 0.0), (-200, -100))
    L(nt, E, 0, vol, "Emission Color")
    # noise-modulated density
    texco = mknode(nt, "ShaderNodeTexCoord", (-600, -200))
    nse = noise(nt, noise_scale, 4, loc=(-400, -200), vec=texco)
    dn = mathn(nt, 'MULTIPLY', nse.outputs['Fac'], noise_amount, loc=(-200, -220))
    dn = mathn(nt, 'ADD', dn, 1.0 - noise_amount*0.5, loc=(-50, -220))
    dn = mathn(nt, 'MULTIPLY', dn, density, loc=(0, -220))
    L(nt, dn, 0, vol, "Density")
    L(nt, vol.outputs[0], 0, outn, 1)
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    FX.objects.link(ob)
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bm.to_mesh(me); bm.free()
    ob.location = center
    ob.data.materials.append(m)
    ob.visible_camera = True
    return ob

mistbox("Mist_Lake", (0, -320, 7), (1400, 1000, 16), density=0.0045, noise_scale=0.012)
mistbox("Mist_Gorge", (0, -150, 14), (140, 230, 36), density=0.010, noise_scale=0.02)
mistbox("Mist_Moor_N", (150, 500, 14), (1500, 900, 24), density=0.0035, noise_scale=0.008)
mistbox("Mist_W", (-650, 100, 10), (500, 1200, 20), density=0.004, noise_scale=0.01)

scn.view_layers[0].update()
bpy.ops.wm.save_as_mainfile(filepath="/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/hogwarts.blend")
result = {"ok": True, "moon_dir": tuple(round(v,2) for v in MOON)}
