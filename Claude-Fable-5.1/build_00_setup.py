"""Pass 0 — scene setup: clear factory scene, render settings, collections."""
import bpy, os, sys, importlib
FOLDER = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else bpy.path.abspath("//")
if FOLDER not in sys.path:
    sys.path.insert(0, FOLDER)
import hog_lib as H; importlib.reload(H)

scn = bpy.context.scene
scn.name = "Hogwarts"

# --- remove factory objects
for name in ("Cube", "Light", "Camera"):
    o = bpy.data.objects.get(name)
    if o:
        bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections):
    if c.name == "Collection" and len(c.objects) == 0 and len(c.children) == 0:
        bpy.data.collections.remove(c)
H.purge_orphans()

# --- collections
for name in ("Castle", "Terrain", "Water", "Nature", "Lights", "FX", "Cameras"):
    H.coll(name)
for name in ("GreatHall", "TowerCluster", "Towers", "Walls", "Viaduct", "Boathouse", "Greenhouses", "Windows", "Details"):
    H.coll(name, "Castle")

# --- units
scn.unit_settings.system = 'METRIC'
scn.unit_settings.scale_length = 1.0

# --- render
scn.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = 'OPTIX'
prefs.get_devices()
for d in prefs.devices:
    d.use = (d.type == 'OPTIX')
scn.cycles.device = 'GPU'
scn.cycles.samples = 1024
scn.cycles.use_adaptive_sampling = True
scn.cycles.adaptive_threshold = 0.01
scn.cycles.use_denoising = True
scn.cycles.denoiser = 'OPENIMAGEDENOISE'
scn.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
scn.cycles.denoising_use_gpu = True
scn.cycles.max_bounces = 12
scn.cycles.diffuse_bounces = 4
scn.cycles.glossy_bounces = 6
scn.cycles.transmission_bounces = 8
scn.cycles.volume_bounces = 2
scn.cycles.transparent_max_bounces = 16
scn.cycles.caustics_reflective = False
scn.cycles.caustics_refractive = False
scn.cycles.blur_glossy = 1.0
scn.cycles.volume_step_rate = 1.0
scn.cycles.volume_max_steps = 512
scn.cycles.use_light_tree = True
scn.cycles.film_exposure = 1.0
scn.render.resolution_x = 3840
scn.render.resolution_y = 2160
scn.render.resolution_percentage = 100
scn.render.film_transparent = False
scn.render.use_persistent_data = True
scn.render.image_settings.file_format = 'PNG'
scn.render.image_settings.color_mode = 'RGB'
scn.render.image_settings.color_depth = '8'
scn.render.image_settings.compression = 50

# --- colour management
scn.view_settings.view_transform = 'AgX'
scn.view_settings.exposure = 0.0
scn.view_settings.gamma = 1.0
scn.display_settings.display_device = 'sRGB'
try:
    scn.view_settings.look = 'AgX - Punchy'
except Exception:
    pass

# --- viewport: keep it light
for area in bpy.context.window_manager.windows[0].screen.areas:
    if area.ui_type == 'VIEW_3D':
        for sp in area.spaces:
            if sp.type == 'VIEW_3D':
                sp.shading.type = 'SOLID'
                sp.clip_end = 20000.0

result = {"objects": len(bpy.data.objects), "collections": [c.name for c in bpy.data.collections],
          "look": scn.view_settings.look, "device": scn.cycles.device}
