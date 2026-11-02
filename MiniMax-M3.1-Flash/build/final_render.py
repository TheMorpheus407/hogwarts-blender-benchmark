"""Final deliverable renders: 3840x2160, 1024 samples, denoised.

The frames are rendered from a main-thread ``bpy.app.timers`` callback, one
frame per tick.  An earlier version drove the same sequence from a
background Python thread and Blender 5.1 segfaulted on the second frame:
``bpy.ops.render.render`` is not thread safe, and the operator needs the
main loop.  The timer keeps every render on the main thread while still
letting the MCP call return immediately.

Progress is written to a log file; poll that with the shell rather than
through the MCP socket, because the socket is blocked while a frame is
being rendered.
"""
import bpy, os, time, traceback

ROOT = "/home/morpheus/Documents/Morpheus-Produktion/Benchmarks/Blender/MiniMax-M3.1-Flash"
LOG = "/tmp/hogwarts_final.log"

SHOTS = [("Cam_Hero", "hero.png"),
         ("Cam_Aerial", "angle_aerial.png"),
         ("Cam_Boathouse", "angle_boathouse.png"),
         ("Cam_Viaduct", "angle_viaduct.png"),
         ("Cam_Detail_Wall", "detail_01.png"),
         ("Cam_Detail_Boathouse", "detail_02.png"),
         ("Cam_Detail_Turret", "detail_03.png")]

_state = {"i": 0}


def log(msg):
    with open(LOG, "a") as f:
        f.write(msg + "\n")
        f.flush()


def apply_settings():
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    scn.cycles.device = 'GPU'
    scn.render.resolution_x, scn.render.resolution_y = 3840, 2160
    scn.render.resolution_percentage = 100
    scn.cycles.samples = 1024
    scn.cycles.use_denoising = True
    scn.cycles.use_adaptive_sampling = True
    scn.cycles.adaptive_threshold = 0.006
    # cap the peak memory of a 4K frame
    try:
        scn.cycles.use_auto_tile = True
        scn.cycles.tile_size = 256
    except Exception:
        pass
    scn.render.image_settings.file_format = 'PNG'
    scn.render.image_settings.color_mode = 'RGB'
    scn.render.image_settings.color_depth = '16'
    scn.render.image_settings.compression = 15
    scn.render.film_transparent = False
    scn.view_settings.view_transform = 'AgX'
    try:
        scn.view_settings.look = 'AgX - Punchy'
    except Exception:
        pass
    scn.view_settings.exposure = 0.0
    return scn


def _tick():
    """Render one frame, then come back for the next one."""
    try:
        scn = bpy.context.scene
        if _state["i"] >= len(SHOTS):
            log("ALLDONE")
            return None
        cam, name = SHOTS[_state["i"]]
        scn.camera = bpy.data.objects[cam]
        scn.render.filepath = os.path.join(ROOT, name)
        log("START %s %s" % (name, time.strftime("%H:%M:%S")))
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        log("DONE  %s %.1fs" % (name, time.time() - t0))
        _state["i"] += 1
        if _state["i"] >= len(SHOTS):
            log("ALLDONE")
            return None
        return 0.5
    except Exception:
        log("ERROR " + traceback.format_exc()[-2000:])
        return None


def start():
    apply_settings()
    try:
        os.remove(LOG)
    except OSError:
        pass
    _state["i"] = 0
    bpy.app.timers.register(_tick, first_interval=1.0)
    log("QUEUED %d frames" % len(SHOTS))
    return True
