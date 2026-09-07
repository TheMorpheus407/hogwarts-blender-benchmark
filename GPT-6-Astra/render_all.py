import bpy
from pathlib import Path

root = Path(bpy.data.filepath).parent
scene = bpy.context.scene
shots = [
    ("Cam_Hero", "hero.png"),
    ("Cam_Aerial", "angle_aerial.png"),
    ("Cam_Boathouse", "angle_boathouse.png"),
    ("Cam_Viaduct", "angle_viaduct.png"),
    ("Cam_Detail_01", "detail_01.png"),
    ("Cam_Detail_02", "detail_02.png"),
    ("Cam_Detail_03", "detail_03.png"),
]
scene.render.engine = "CYCLES"
scene.render.resolution_x = 3840
scene.render.resolution_y = 2160
scene.render.resolution_percentage = 100
scene.cycles.samples = 1024
scene.cycles.use_adaptive_sampling = False
scene.cycles.use_denoising = True
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.image_settings.color_depth = "16"
for marker in scene.timeline_markers:
    marker.camera = None
for camera, filename in shots:
    scene.camera = bpy.data.objects[camera]
    scene.render.filepath = str(root / filename)
    bpy.ops.render.render(write_still=True)
scene.camera = bpy.data.objects["Cam_Hero"]
scene.render.filepath = str(root / "hero.png")
bpy.ops.wm.save_as_mainfile(filepath=str(root / "hogwarts.blend"))
