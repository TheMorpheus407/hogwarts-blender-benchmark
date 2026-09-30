"""Stage 2e: lower terrace (greenhouses, terrace wall, lamps)."""
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
import hw_glass as GL
import hw_scene as S
import hw_mats
import s01_terrain as s1
for _m in (L, hw_geo, G, TW, W, GL, S, hw_mats):
    importlib.reload(_m)
from hw_geo import Geo, boxes

Z_T = 38.0
ARCS = {}


def finish(g, name, coll):
    g.consolidate()
    obj = g.to_object(bpy, coll, name)
    return obj, g.count()


def build_greenhouses(coll, seed=51):
    rng = np.random.default_rng(seed)
    g = Geo('Castle_Greenhouses')
    smp = s1.SAMPLER
    GL.barrel_house(g, 40.0, -62.0, Z_T, 30.0, 10.0, 3.0, 4.2, rng, yaw=math.pi / 2)
    GL.dome_house(g, 74.0, -63.0, Z_T, 6.6, 3.4, 4.6, rng)
    GL.lean_to(g, 26.0, -52.5, Z_T, 16.0, 6.0, 2.6, 5.6, rng)
    # small potting shed with lit window, lamp posts, paved walks
    post = W.lantern_post(2.8)
    for (x, y) in ((22.0, -66.0), (58.0, -56.0), (58.0, -70.0), (88.0, -60.0), (10.0, -58.0), (92.0, -50.0)):
        g.add_geo(post, pos=(x, y, Z_T))
        W.reg('terrace', x, y, Z_T + 2.75)
    for (x, y) in ((40.0, -62.0), (74.0, -63.0), (26.0, -52.5), (54.0, -62.0)):
        W.reg('interior', x, y, Z_T + 3.4)
    return finish(g, 'Castle_Greenhouses', coll)


def build_terrace_walls(coll, seed=52):
    rng = np.random.default_rng(seed)
    smp = s1.SAMPLER
    g = Geo('Castle_TerraceWalls')
    arcs = W.rim_arcs((58.0, -62.0), Z_T, drop=1.6, n=720, r_max=140.0, r_min=6.0)
    ARCS['terrace'] = arcs
    for arc in arcs:
        if len(arc) < 8:
            continue
        W.wall_run(g, arc, smp, Z_T, off=1.0, t=2.0, rng=rng, buttress_every=10.0)
    return finish(g, 'Castle_TerraceWalls', coll)


BUILDERS = dict(greenhouses=build_greenhouses, terracewalls=build_terrace_walls)


def run(which=None):
    hw_mats.build_all_glasshouse()
    coll = S.ensure_collection('Castle')
    out = {}
    for k in (which or BUILDERS.keys()):
        S.remove_object('Castle_' + {'greenhouses': 'Greenhouses', 'terracewalls': 'TerraceWalls'}[k])
        t0 = time.time()
        obj, cnt = BUILDERS[k](coll)
        out[k] = (cnt, round(time.time() - t0, 2))
    return out
