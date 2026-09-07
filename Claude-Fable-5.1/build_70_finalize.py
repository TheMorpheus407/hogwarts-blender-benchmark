"""Pass 7 — finalize: detail cameras, final render settings, deliverable renders.

Renders run sequentially off a timer (so the MCP call returns immediately);
progress is logged to wip/final_render.log and a <name>.done marker per frame.
Set RENDER = False (globals) to only set things up.
"""
import bpy, os, sys, importlib, math, time
from mathutils import Vector
FOLDER = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else bpy.path.abspath("//")
if FOLDER not in sys.path:
    sys.path.insert(0, FOLDER)
import hog_lib as H; importlib.reload(H)

scn = bpy.context.scene
RENDER = globals().get("RENDER", True)
ONLY = globals().get("ONLY", None)          # optional list of output names to render
SAMPLES = globals().get("SAMPLES", 1024)
RES = globals().get("RES", (3840, 2160))

# --------------------------------------------------------------------------- detail cameras
DETAIL_CAMS = {
    # turret cap + machicolated parapet of the Grand Tower, dormers and window glow
    "Cam_Detail_01": dict(loc=(-72, -84, 128), target=(-34, -34, 136), lens=60),
    # boathouse door, quay steps and moored boats from the water
    "Cam_Detail_02": dict(loc=(52, -122, 1.6), target=(60, -100, 4.5), lens=35),
    # Great Hall bay: buttress, pinnacle, traceried window at dusk-glow
    "Cam_Detail_03": dict(loc=(-96, -74, 86), target=(-74, -47, 90), lens=45),
}
for name, c in DETAIL_CAMS.items():
    ob = bpy.data.objects.get(name)
    if ob is None:
        cam = bpy.data.cameras.new(name); ob = bpy.data.objects.new(name, cam); H.link_obj(ob, "Cameras")
    ob.data.lens = c["lens"]; ob.data.sensor_width = 36.0; ob.data.clip_start = 0.3; ob.data.clip_end = 30000.0
    ob.location = c["loc"]
    ob.rotation_euler = (Vector(c["target"]) - Vector(c["loc"])).to_track_quat('-Z', 'Y').to_euler()
    # a little depth of field on the close-ups
    ob.data.dof.use_dof = True
    ob.data.dof.focus_distance = (Vector(c["target"]) - Vector(c["loc"])).length
    ob.data.dof.aperture_fstop = 5.6 if name != "Cam_Detail_02" else 4.0

# --------------------------------------------------------------------------- final settings
scn.render.engine = 'CYCLES'
scn.cycles.device = 'GPU'
scn.render.resolution_x, scn.render.resolution_y = RES
scn.render.resolution_percentage = 100
scn.cycles.samples = SAMPLES
scn.cycles.use_adaptive_sampling = True
scn.cycles.adaptive_threshold = 0.008
scn.cycles.use_denoising = True
scn.cycles.denoiser = 'OPENIMAGEDENOISE'
scn.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
scn.cycles.denoising_prefilter = 'ACCURATE'
scn.render.image_settings.file_format = 'PNG'
scn.render.image_settings.color_mode = 'RGB'
scn.render.image_settings.color_depth = '8'
scn.render.image_settings.compression = 30
scn.render.use_persistent_data = True

JOBS = [("hero.png", "Cam_Hero"), ("angle_aerial.png", "Cam_Aerial"), ("angle_boathouse.png", "Cam_Boathouse"),
        ("angle_viaduct.png", "Cam_Viaduct"), ("detail_01.png", "Cam_Detail_01"), ("detail_02.png", "Cam_Detail_02"),
        ("detail_03.png", "Cam_Detail_03")]
if ONLY:
    JOBS = [j for j in JOBS if j[0] in ONLY]

log_path = os.path.join(H.WIP, "final_render.log")

def _run_jobs():
    with open(log_path, "a") as log:
        log.write("batch start %s samples=%d res=%dx%d\n" % (time.strftime("%H:%M:%S"), SAMPLES, RES[0], RES[1]))
    for fname, cam in JOBS:
        out = os.path.join(FOLDER, fname)
        t0 = time.time()
        try:
            scn.camera = bpy.data.objects[cam]
            scn.render.filepath = out
            bpy.ops.render.render(write_still=True)
            msg = "%s %s %.0fs" % (time.strftime("%H:%M:%S"), fname, time.time() - t0)
        except Exception as e:
            msg = "%s %s ERROR %r" % (time.strftime("%H:%M:%S"), fname, e)
        with open(log_path, "a") as log:
            log.write(msg + "\n")
        with open(out + ".done", "w") as f:
            f.write(msg + "\n")
    with open(log_path, "a") as log:
        log.write("batch done %s\n" % time.strftime("%H:%M:%S"))
    with open(os.path.join(H.WIP, "final_render.batch"), "w") as f:
        f.write("done\n")
    return None

if RENDER:
    try:
        os.remove(os.path.join(H.WIP, "final_render.batch"))
    except FileNotFoundError:
        pass
    bpy.app.timers.register(_run_jobs, first_interval=0.1)

result = {"jobs": [j[0] for j in JOBS], "render": RENDER, "samples": SAMPLES, "res": list(RES)}
