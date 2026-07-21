import bpy

# clear default scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob)

# collections
for name in ["Castle", "Castle_Windows", "Terrain", "Nature", "Lights", "FX", "Cameras", "Bridge", "Props"]:
    get_col(name)

scn = bpy.context.scene
scn.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = 'OPTIX'
for d in prefs.devices:
    d.use = (d.type == 'OPTIX')
scn.cycles.device = 'GPU'
scn.cycles.samples = 48
scn.cycles.use_denoising = True
scn.cycles.use_preview_denoising = True
scn.cycles.max_bounces = 8
scn.cycles.diffuse_bounces = 3
scn.cycles.glossy_bounces = 3
scn.cycles.transmission_bounces = 4
scn.cycles.volume_bounces = 1
scn.cycles.use_fast_gi = True
scn.render.resolution_x = 960
scn.render.resolution_y = 540
scn.render.resolution_percentage = 100
scn.render.image_settings.file_format = 'PNG'
scn.render.film_transparent = False
scn.render.use_file_extension = True
scn.view_settings.view_transform = 'AgX'
try:
    scn.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass

# world
w = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scn.world = w
w.use_nodes = True
bg = w.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.004, 0.006, 0.012, 1)
bg.inputs["Strength"].default_value = 0.35

scn.unit_settings.system = 'METRIC'
scn.unit_settings.scale_length = 1.0

result = {"setup": "done", "collections": [c.name for c in bpy.data.collections]}
