"""Stage 2d: viaduct, boathouse, jetty, boats."""
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
import hw_viaduct as V
import hw_boathouse as B
import hw_scene as S
import s01_terrain as s1
import hw_terrain as T
for _m in (L, hw_geo, G, TW, W, V, B, S):
    importlib.reload(_m)
from hw_geo import Geo, boxes

Z0 = L.Z0


def placeholder_mats():
    S.ensure_material('M_Timber', (0.12, 0.07, 0.04), 0.7)
    S.ensure_material('M_Plaster', (0.55, 0.52, 0.46), 0.9)
    S.ensure_material('M_Cobble', (0.25, 0.24, 0.22), 0.9)
    S.ensure_material('M_Rope', (0.3, 0.25, 0.18), 0.9)
    S.ensure_material('M_LanternGlass', (0.1, 0.05, 0.02), 0.2, emission=(1, 0.5, 0.15), strength=8.0)


def finish(g, name, coll):
    g.consolidate()
    obj = g.to_object(bpy, coll, name)
    return obj, g.count()


def build_viaduct(coll, seed=41):
    rng = np.random.default_rng(seed)
    v = L.VIADUCT
    g = Geo('Castle_Viaduct')
    info = V.build_viaduct(g, s1.SAMPLER, v['x0'], v['n'], v['y'], v['deck'], width=v['width'], pitch=(v['x1'] - v['x0']) / v['n'] - 0.0, rng=rng)
    return finish(g, 'Castle_Viaduct', coll)


def build_boathouse(coll, seed=42):
    rng = np.random.default_rng(seed)
    b = L.BOATHOUSE
    g = Geo('Castle_Boathouse')
    B.boathouse(g, b['cx'], b['cy'], b['base'], b['L'], b['D'], rng)
    ys = b['cy'] - b['D'] / 2
    B.jetty(g, b['cx'] + 6.0, ys - 1.6, 0.7, 22.0, 3.2, rng)
    post = W.lantern_post(2.4)
    for yy in (ys - 4.0, ys - 12.0, ys - 22.5):
        for sx in (-1, 1):
            g.add_geo(post, pos=(b['cx'] + 6.0 + sx * 1.75, yy, 0.72))
            W.reg('boat', b['cx'] + 6.0 + sx * 1.75, yy, 0.72 + 2.15)
    for xx in (b['cx'] - 7.6, b['cx'] - 2.4, b['cx'] + 2.4, b['cx'] + 7.6):
        W.reg('boat', xx, ys - 1.7, b['base'] + 4.7)
    B.rowboat(g, b['cx'] + 9.6, ys - 11.0, 0.18, math.pi / 2 + 0.06, rng=rng, lantern=True)
    B.rowboat(g, b['cx'] + 2.4, ys - 9.0, 0.16, math.pi / 2 - 0.05, rng=rng)
    B.rowboat(g, b['cx'] + 13.5, ys - 4.5, 0.15, math.pi / 2 + 0.3, rng=rng)
    B.rowboat(g, b['cx'] - 6.0, ys - 16.0, 0.12, 0.35, rng=rng, lantern=True)
    # masonry quay wall along the shelf edge (follows the terrain), with bollards
    smp = s1.SAMPLER
    pts = np.array(s1.QUAY_PTS[0]) if s1.QUAY_PTS else None
    if pts is None:
        pts = T.quay_line(b)
    W.wall_run(g, pts, smp, b['base'] + 0.35, off=-0.1, t=1.8, parapet=0.42, merlons=False, buttress_every=7.0, foot=1.6, wall_mat='M_Quay', rng=rng)
    for xx in np.arange(b['cx'] - 22.0, b['cx'] + 24.0, 5.5):
        k = int(np.argmin(np.abs(pts[:, 0] - xx)))
        g.add_geo(G.finial(0.7, 0.16, 'M_Iron'), pos=(xx, pts[k, 1] + 0.5, b['base'] + 0.75))
    return finish(g, 'Castle_Boathouse', coll)


BUILDERS = dict(viaduct=build_viaduct, boathouse=build_boathouse)


def run(which=None):
    placeholder_mats()
    coll = S.ensure_collection('Castle')
    out = {}
    for k in (which or BUILDERS.keys()):
        S.remove_object('Castle_' + k.capitalize())
        t0 = time.time()
        obj, cnt = BUILDERS[k](coll)
        out[k] = (cnt, round(time.time() - t0, 2))
    return out
