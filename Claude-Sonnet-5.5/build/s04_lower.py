"""Stage 2c: stair, rim walls, wall towers (everything that ties the castle to the crag)."""
import bpy
import numpy as np
import math
import time
import importlib
import hw_layout as L
import hw_geo
import hw_gothic as G
import hw_towers as TW
import hw_walls as W
import hw_terrain as T
import hw_scene as S
import s01_terrain as s1
for _m in (L, hw_geo, G, TW, W, S):
    importlib.reload(_m)
from hw_geo import Geo, boxes

Z0 = L.Z0
ARCS = {}


def finish(g, name, coll):
    g.consolidate()
    obj = g.to_object(bpy, coll, name)
    return obj, g.count()


def build_stair(coll, seed=21):
    rng = np.random.default_rng(seed)
    smp = s1.SAMPLER
    g = Geo('Castle_BoathouseStair')
    width = L.STAIR['width']
    lamps = []
    for i, p in enumerate(s1.STAIR_PTS):
        stair_info = W.stair_flight(g, p, smp, width=width, depth=2.6)
        W.stair_parapets(g, p, smp, width=width)
        # lanterns along the outer (south) side every ~15 m
        P, s = W.resample_path(p, 1.0)
        for sl in np.arange(6.0, s[-1] - 3.0, 15.0):
            k = int(np.searchsorted(s, sl))
            tan, nrm = W.path_normals(P[:, :2])
            sd = -1 if nrm[k, 1] > 0 else 1     # side towards the lake (south)
            pos = P[k, :2] + nrm[k] * sd * (width / 2 + 0.25)
            lamps.append((pos[0], pos[1], P[k, 2] + 1.0))
    # landings + lamps
    for i, p in enumerate(s1.STAIR_PTS):
        for end in (0, -1):
            q = p[end]
            W.landing(g, q[0], q[1], q[2], R=4.6)
            lamps.append((q[0], q[1] - 3.6, q[2]))
    post = W.lantern_post(3.0)
    for (x, y, z) in lamps:
        g.add_geo(post, pos=(x, y, z))
        W.reg('stair', x, y, z + 3.05)
    return finish(g, 'Castle_BoathouseStair', coll)


def build_rim_walls(coll, seed=22):
    rng = np.random.default_rng(seed)
    smp = s1.SAMPLER
    g = Geo('Castle_RimWalls')
    arcs = W.rim_arcs((-45.0, 20.0), Z0, drop=1.6, n=900, r_max=280.0)
    ARCS['plateau'] = arcs
    info = []
    # stair gate gap: where the last flight meets the plateau
    top = s1.STAIR_PTS[-1][-1]
    for ai, arc in enumerate(arcs):
        P, s = W.resample_path(arc, 1.4)
        d = np.hypot(P[:, 0] - top[0], P[:, 1] - top[1])
        gaps = []
        if d.min() < 12.0:
            k = int(np.argmin(d))
            gaps.append((max(0.0, s[k] - 5.0), s[k] + 5.0))
        r = W.wall_run(g, arc, smp, Z0, off=1.0, t=2.2, gaps=gaps, rng=rng)
        info.append(r)
    return finish(g, 'Castle_RimWalls', coll)


def build_courtyard(coll, seed=23):
    """Lamp posts along the castle terraces and courtyards + a few benches / planters for scale."""
    rng = np.random.default_rng(seed)
    g = Geo('Castle_Courtyard')
    post = W.lantern_post(3.2)
    pts = []
    for x in np.arange(-196.0, -118.0, 15.5):
        pts.append((x, -28.5))
    for x in np.arange(-82.0, -36.0, 11.5):
        pts.append((x, -27.5))
    for x in np.arange(-30.0, 50.0, 14.0):
        pts.append((x, -26.0))
    for y in np.arange(-20.0, 60.0, 16.0):
        pts.append((-236.0 if False else -222.0, y))
    for x in np.arange(-60.0, 60.0, 20.0):
        pts.append((x, 46.0))
    for (x, y) in pts:
        z = float(s1.SAMPLER.z(x, y))
        if z < Z0 - 3.0 or z > Z0 + 3.0:
            continue
        g.add_geo(post, pos=(x, y, z))
        W.reg('court', x, y, z + 3.2 - 0.28 + 0.36)
    return finish(g, 'Castle_Courtyard', coll)


BUILDERS = dict(stair=build_stair, walls=build_rim_walls, courtyard=build_courtyard)


def run(which=None):
    coll = S.ensure_collection('Castle')
    for n in ('Castle_BoathouseStair', 'Castle_RimWalls', 'Castle_Courtyard'):
        if which is None or n.split('_', 1)[1].lower().startswith(tuple(which)):
            S.remove_object(n)
    out = {}
    for k in (which or BUILDERS.keys()):
        t0 = time.time()
        obj, cnt = BUILDERS[k](coll)
        out[k] = (cnt, round(time.time() - t0, 2))
    return out
