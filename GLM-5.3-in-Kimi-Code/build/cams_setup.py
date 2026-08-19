# Set up the four final cameras
import bpy, math
from mathutils import Vector

scn = bpy.context.scene
CAMS = bpy.data.collections['Cameras']

def mkcam(name, loc, target, lens, tilt_shift=0.0):
    cd = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36.0
    try:
        cd.shift_y = tilt_shift
    except Exception: pass
    ob = bpy.data.objects.get(name)
    if not ob:
        ob = bpy.data.objects.new(name, cd)
        CAMS.objects.link(ob)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob

# Hero: low across the lake, SW, castle NE behind; viaduct broadside-left
mkcam("Cam_Hero", (-140, -640, 7.5), (5, -60, 78), 52)
# Aerial: elevated three-quarter from SSW
mkcam("Cam_Aerial", (-430, -680, 330), (10, -60, 60), 60)
# Boathouse: water level close, looking NE at boathouse + stair + castle above
mkcam("Cam_Boathouse", (-152, -102, 3.5), (-60, -45, 40), 44)
# Viaduct: standing on the causeway looking at gatehouse
mkcam("Cam_Viaduct", (6, -218, 46.5), (-2, -46, 62), 40)

scn.camera = bpy.data.objects["Cam_Hero"]
scn.render.resolution_x = 1920
scn.render.resolution_y = 1080
scn.render.resolution_percentage = 50
scn.cycles.samples = 96
scn.cycles.use_adaptive_sampling = True

# remove temp cams
for n in ("TempCam", "OrthoProf"):
    ob = bpy.data.objects.get(n)
    if ob:
        cd = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.cameras.remove(cd)

bpy.ops.wm.save_as_mainfile(filepath="/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/hogwarts.blend")
result = {"ok": True, "cams": [o.name for o in CAMS.objects]}
