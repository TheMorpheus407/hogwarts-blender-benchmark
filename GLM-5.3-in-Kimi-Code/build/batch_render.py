import bpy, time, json

scn = bpy.context.scene
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = 'OPTIX'
prefs.get_devices()
for d in prefs.devices:
    d.use = (d.type == 'OPTIX')
scn.cycles.device = 'GPU'
scn.render.engine = 'CYCLES'

scn.render.resolution_x = 3840
scn.render.resolution_y = 2160
scn.render.resolution_percentage = 100
scn.cycles.samples = 1024
scn.cycles.use_adaptive_sampling = True
scn.cycles.adaptive_threshold = 0.008
scn.cycles.use_denoising = True
scn.cycles.denoiser = 'OPENIMAGEDENOISE'
scn.render.image_settings.file_format = 'PNG'
scn.render.image_settings.color_mode = 'RGB'

FRAMES = [
    ("Cam_Hero",     "/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/hero.png"),
    ("Cam_Aerial",   "/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/angle_aerial.png"),
    ("Cam_Boathouse","/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/angle_boathouse.png"),
    ("Cam_Viaduct",  "/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/angle_viaduct.png"),
    ("Cam_Detail1",  "/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/detail_01.png"),
    ("Cam_Detail2",  "/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/detail_02.png"),
    ("Cam_Detail3",  "/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/detail_03.png"),
]

log = []
for cam, out in FRAMES:
    if bpy.data.objects.get(cam) is None:
        log.append({"cam": cam, "error": "camera missing"})
        continue
    scn.camera = bpy.data.objects[cam]
    scn.render.filepath = out
    t0 = time.time()
    try:
        bpy.ops.render.render(write_still=True)
        log.append({"cam": cam, "sec": round(time.time()-t0, 1), "out": out})
    except Exception as e:
        log.append({"cam": cam, "error": str(e)})

# keep final render settings in the saved scene
scn.camera = bpy.data.objects["Cam_Hero"]
bpy.ops.wm.save_as_mainfile(filepath="/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/hogwarts.blend")

with open("/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/preview/render_batch_log2.json", "w") as f:
    json.dump(log, f, indent=1)
print(json.dumps(log, indent=1))
