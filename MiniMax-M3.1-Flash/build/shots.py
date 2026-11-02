"""Render helper — shoot named cameras to PNG files.

Usage from the MCP:
    exec(open(BUILD + "/shots.py").read())
    shots.shots([("Cam_Hero", "hero")], res=(1600, 900), spp=64)
"""
import bpy, os

ROOT = "/home/morpheus/Documents/Morpheus-Produktion/Benchmarks/Blender/MiniMax-M3.1-Flash"
DIAG = os.path.join(ROOT, "_diag")


def shot(cam, tag, res=(800, 450), spp=24, folder=None, exposure=None):
    scn = bpy.context.scene
    scn.camera = bpy.data.objects[cam]
    scn.render.resolution_x, scn.render.resolution_y = res
    scn.cycles.samples = spp
    scn.render.image_settings.file_format = 'PNG'
    if exposure is not None:
        scn.view_settings.exposure = exposure
    scn.render.filepath = os.path.join(folder or DIAG, tag + ".png")
    bpy.ops.render.render(write_still=True)
    return scn.render.filepath


def shots(specs, res=(800, 450), spp=24, folder=None):
    out = []
    for c, t in specs:
        out.append(shot(c, t, res, spp, folder))
    return out


def bbox(names):
    """World-space bbox of the named collections."""
    from mathutils import Vector
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for cn in names:
        c = bpy.data.collections.get(cn)
        if not c:
            continue
        for ob in c.objects:
            if ob.type != 'MESH':
                continue
            for corner in ob.bound_box:
                p = ob.matrix_world @ Vector(corner)
                for i in range(3):
                    lo[i] = min(lo[i], p[i])
                    hi[i] = max(hi[i], p[i])
    return [round(v, 1) for v in lo], [round(v, 1) for v in hi]
