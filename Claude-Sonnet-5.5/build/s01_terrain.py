"""Stage 1: terrain + water.  quality = 'preview' | 'final'."""
import bpy
import numpy as np
import time
import importlib
import hw_layout
import hw_noise
import hw_terrain as T
import hw_scene as S
for _m in (hw_layout, hw_noise, T, S):
    importlib.reload(_m)

SAMPLER = None
AXES = {}


def axes(quality):
    if quality == 'preview':
        xs = T.graded_axis([(-800, -360, 8.0), (-360, 430, 1.3), (430, 900, 8.0)], -9500, 9500, 1.09)
        ys = T.graded_axis([(-520, -155, 8.0), (-155, 135, 1.3), (135, 700, 8.0)], -9500, 9500, 1.09)
        wx = T.graded_axis([(-720, 720, 8.0)], -11000, 11000, 1.1)
        wy = T.graded_axis([(-1050, 320, 8.0)], -11000, 11000, 1.1)
    else:
        xs = T.graded_axis([(-800, -360, 3.0), (-360, 430, 0.55), (430, 900, 3.0)], -9500, 9500, 1.03)
        ys = T.graded_axis([(-520, -155, 2.2), (-155, 135, 0.55), (135, 700, 3.0)], -9500, 9500, 1.03)
        wx = T.graded_axis([(-720, 720, 3.2)], -11000, 11000, 1.045)
        wy = T.graded_axis([(-1050, 320, 3.2)], -11000, 11000, 1.045)
    return xs, ys, wx, wy


STAIR_PTS = []
QUAY_PTS = []


def plan_and_register_stairs():
    """Contour-following stair flights + landings -> terrain carves."""
    global STAIR_PTS
    St = hw_layout.STAIR
    STAIR_PTS = []
    T.CARVES['stairs'] = []
    for i, (xa, za, xb, zb) in enumerate(St['flights']):
        p = T.plan_flight(xa, za, xb, zb, St['y_lo'], St['y_hi'], res=1.0)
        STAIR_PTS.append(p)
        T.register_stair('flight_%d' % i, p, half=St['width'] / 2 + 0.6, fade=2.6)
    # landings at the switchbacks (short 2-point polylines)
    for i in range(len(STAIR_PTS)):
        for end in (0, -1):
            q = STAIR_PTS[i][end]
            T.register_stair('land_%d_%d' % (i, end), np.array([[q[0] - 0.3, q[1], q[2]], [q[0] + 0.3, q[1], q[2]]]),
                             half=5.0, fade=2.8)
    return STAIR_PTS


PATHS = {}


def run(quality='preview', extra_fn=None, stairs=True, paths=True):
    global SAMPLER, PATHS
    t0 = time.time()
    T.CARVES['quay'] = []
    if stairs:
        plan_and_register_stairs()
    QUAY_PTS[:] = []
    if paths:
        import hw_nature
        importlib.reload(hw_nature)
        PATHS = hw_nature.smoothed_paths()
        T.CARVES['paths'] = []
        for k, p in PATHS.items():
            T.register_path(k, p, half=1.9)
        if extra_fn is None:
            extra_fn = hw_nature.terrain_extra(PATHS)
    QUAY_PTS.append(T.quay_line(hw_layout.BOATHOUSE))
    T.register_quay(QUAY_PTS[0])
    coll = S.ensure_collection('Terrain')
    wcoll = S.ensure_collection('Water', parent=S.ensure_collection('Terrain'))
    S.clear_collection('Terrain')
    S.clear_collection('Water')
    xs, ys, wx, wy = axes(quality)
    mat = S.ensure_material('M_Ground', (0.10, 0.12, 0.09), 0.9)
    obj, smp, info = T.build_terrain(bpy, coll, 'Terrain', xs, ys, mat=mat, extra_fn=extra_fn)
    wmat = S.ensure_material('M_Water', (0.02, 0.05, 0.07), 0.05)
    ow, iw = T.build_water(bpy, wcoll, 'Lake_Water', wmat, wx, wy)
    SAMPLER = smp
    AXES.update(xs=xs, ys=ys)
    info['water'] = iw
    info['time'] = round(time.time() - t0, 1)
    return info
