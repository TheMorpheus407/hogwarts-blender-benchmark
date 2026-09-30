"""Delivery cameras."""
import math
import scene

DZ = 30.0

SHOTS = {
    # name: (location, target, lens, extra)
    'Cam_Hero': ((-95.0, -470.0, 9.0), (8.0, -20.0, 88.0), 32.0, {}),
    'Cam_Aerial': ((-400.0, -610.0, 235.0), (30.0, 0.0, 128.0), 32.0, {}),
    'Cam_Boathouse': ((52.0, -225.0, 1.6), (0.0, -120.0, 75.0), 22.0, {}),
    'Cam_Viaduct': ((301.0, 42.0, 84.7), (150.0, 38.0, 103.0), 26.0, {}),
    # Great Hall south facade: traceried lancets, stepped buttresses, pinnacles, slate roof & dormers
    'Cam_Detail_01': ((-128.0, -92.0, 90.0), (-96.0, -60.0, 99.0), 32.0, {}),
    # the big cone tower's crown: machicolations, slate cone with lucarnes, finial against the sky
    'Cam_Detail_02': ((-10.0, -30.0, 150.0), (40.0, -20.0, 165.0), 24.0, {}),
    # clock tower face with its gothic frame and bartizans
    'Cam_Detail_03': ((176.0, 18.0, 116.0), (140.0, 30.0, 124.0), 40.0, {}),
}


def boathouse_centre():
    import bpy
    from mathutils import Vector
    ob = bpy.data.objects.get('Castle_Boathouse')
    if not ob:
        return Vector((6.0, -150.0, 5.0))
    vs = [v.co for v in ob.data.vertices]
    mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return (mn + mx) / 2


def setup():
    c = boathouse_centre()
    SHOTS['Cam_Boathouse'] = ((c.x - 4.0, c.y - 66.0, 1.2), (c.x - 12.0, c.y + 40.0, 50.0), 17.0, {})
    for name, (loc, tgt, lens, extra) in SHOTS.items():
        scene.add_camera(name, loc, tgt, lens=lens, **extra)
    return list(SHOTS)
