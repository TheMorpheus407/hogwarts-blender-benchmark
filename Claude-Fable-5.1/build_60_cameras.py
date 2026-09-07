"""Pass 6 — cameras (also used for block-out checks)."""
import bpy, os, sys, importlib, math
from mathutils import Vector
FOLDER = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else bpy.path.abspath("//")
if FOLDER not in sys.path:
    sys.path.insert(0, FOLDER)
import hog_lib as H; importlib.reload(H)
import hog_layout as L; importlib.reload(L)

def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

H.clear_collection("Cameras")
for name, c in L.CAMERAS.items():
    cam = bpy.data.cameras.new(name)
    cam.lens = c["lens"]
    cam.sensor_width = 36.0
    cam.clip_start = 0.5
    cam.clip_end = 30000.0
    if c.get("ortho"):
        cam.type = 'ORTHO'; cam.ortho_scale = c["ortho"]
    ob = bpy.data.objects.new(name, cam)
    H.link_obj(ob, "Cameras")
    ob.location = c["loc"]
    look_at(ob, c["target"])
bpy.context.scene.camera = bpy.data.objects["Cam_Hero"]
result = {"cameras": list(L.CAMERAS.keys())}
