"""Stage 3: forest (geometry-nodes instancing of procedural conifer prototypes)."""
import bpy
import numpy as np
import time
import importlib
import hw_layout as L
import hw_trees as TR
import hw_nature as NA
import hw_scene as S
import hw_mats
import s01_terrain as s1
for _m in (L, TR, NA, S, hw_mats):
    importlib.reload(_m)


def run(seed=5, d0=0.9, max_points=140000, hide_view=True):
    t0 = time.time()
    hw_mats.build_all_nature()
    geos, order = TR.make_prototypes(seed=7)
    pcoll, objs = NA.make_proto_collection(geos, order)
    S.exclude_collection('Tree_Protos')
    rng = np.random.default_rng(seed)
    pts = NA.forest_points(s1.SAMPLER, rng, paths=list(s1.PATHS.values()), d0=d0, max_points=max_points)
    obj = NA.build_scatter_gn('Forest', pcoll, pts)
    if hide_view:
        obj.hide_viewport = True
    lods = [int(((pts[:, 3] // 4) if False else 0)) for _ in range(1)]
    return dict(n_trees=len(pts), t=round(time.time() - t0, 1), protos=len(order))


def run_rocks(seed=9, density_scale=1.0, hide_view=True):
    t0 = time.time()
    hw_mats.build_rockchunk('M_RockChunk')
    geos, order = TR.make_rock_prototypes(seed=11)
    pcoll, objs = NA.make_proto_collection(geos, order, coll_name='Rock_Protos')
    S.exclude_collection('Rock_Protos')
    rng = np.random.default_rng(seed)
    pts = NA.rock_points(rng, stair_polys=list(s1.STAIR_PTS), paths=list(s1.PATHS.values()), density_scale=density_scale)
    obj = NA.build_rock_gn('Rocks', pcoll, pts)
    if hide_view:
        obj.hide_viewport = True
    cats = {}
    for v in np.unique(pts[:, 3]).astype(int):
        cats[int(v)] = int((pts[:, 3] == v).sum())
    return dict(n_rocks=len(pts), t=round(time.time() - t0, 1), by_variant=cats)


def run_shore(seed=13, density_scale=1.0, hide_view=True):
    """Reed clumps + grass tufts on the foreground shores (geometry-nodes instances, like the rocks)."""
    t0 = time.time()
    hw_mats.build_reed('M_Reed')
    geos, order = TR.make_shore_prototypes(seed=21)
    pcoll, objs = NA.make_proto_collection(geos, order, coll_name='Shore_Protos')
    S.exclude_collection('Shore_Protos')
    rng = np.random.default_rng(seed)
    pts = NA.shore_points(rng, density_scale=density_scale)
    obj = NA.build_rock_gn('Nature_ShoreVeg', pcoll, pts)
    if hide_view:
        obj.hide_viewport = True
    return dict(n=len(pts), reeds=int((pts[:, 3] < 3).sum()), tufts=int((pts[:, 3] >= 3).sum()), t=round(time.time() - t0, 1))
