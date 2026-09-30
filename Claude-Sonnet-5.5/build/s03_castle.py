"""Stage 2b: the castle proper.  Each building becomes its own object (meaningful names)."""
import bpy
import numpy as np
import math
import time
import importlib
import hw_layout as L
import hw_geo
import hw_arch as A
import hw_gothic as G
import hw_towers as TW
import hw_halls as H
import hw_scene as S
for _m in (L, hw_geo, A, G, TW, H, S):
    importlib.reload(_m)
from hw_geo import Geo, boxes

Z0 = L.Z0
MATS = dict(M_Stone=((0.42, 0.38, 0.32), 0.9), M_StoneDress=((0.5, 0.46, 0.38), 0.85), M_Slate=((0.09, 0.11, 0.16), 0.5),
            M_Copper=((0.1, 0.45, 0.38), 0.4), M_Iron=((0.05, 0.05, 0.05), 0.5), M_Lead=((0.2, 0.22, 0.25), 0.4),
            M_Brick=((0.35, 0.16, 0.1), 0.9), M_Dark=((0.005, 0.005, 0.006), 0.6), M_ClockMark=((0.02, 0.02, 0.02), 0.5))


def placeholder_mats():
    for k, (c, r) in MATS.items():
        S.ensure_material(k, c, r)
    S.ensure_material('M_GlassLit', (0.02, 0.02, 0.03), 0.1, emission=(1.0, 0.55, 0.2), strength=4.0)
    S.ensure_material('M_ClockFace', (0.9, 0.9, 0.8), 0.5, emission=(1.0, 0.8, 0.5), strength=3.0)


def lan(w, h, l=1, **k):
    return G.window_lancet(w, h, l, **k)


def finish(g, name, coll, weld=False):
    g.consolidate()
    obj = g.to_object(bpy, coll, name)
    return obj, g.count()


def build_great_hall(coll, seed=1):
    rng = np.random.default_rng(seed)
    h = L.CASTLE['hall']
    g = Geo('Castle_GreatHall')
    H.gothic_hall(g, h['cx'], h['cy'], h['L'], h['D'], h['base'], h['eaves'], h['pitch'], rng, bay_w=10.0,
                  lit_p=0.72, corner_turrets=True, chimneys=4, flying=True, big=(2.5, 10.6), sill_z=10.2)
    return finish(g, 'Castle_GreatHall', coll)


def build_hall_turrets(coll, seed=2):
    rng = np.random.default_rng(seed)
    g = Geo('Castle_GreatHall_Turrets')
    for i, (x, y, R, dz, shaft, cone, kind) in enumerate([t for t in L.TURRETS if t[6] == 'corner']):
        cop = TW.COPPER if i in (0, 3) else TW.SLATE
        TW.round_tower(g, x, y, Z0 + dz, R, shaft, cone, rng, bands=(10.0, 22.0, 34.5),
                       tiers=[(6.0, 3, G.window_slit(0.3, 2.2)), (16.0, 3, lan(0.7, 2.0, 1)), (27.0, 3, G.window_slit(0.3, 2.2))],
                       top='corbel_cone', eave_out=1.0, fin=4.5, lit_p=0.55, segs=22, cone_p=1.1, cone_mat=cop, found=26.0, flare=1.1,
                       band_out=0.3)
    return finish(g, 'Castle_GreatHall_Turrets', coll)


def build_grand_tower(coll, seed=3):
    rng = np.random.default_rng(seed)
    t = L.CASTLE['grand']
    g = Geo('Castle_GrandTower')
    tiers = [(6, 12, lan(1.5, 5.0, 1, transoms=1), 0.1), (15, 16, lan(1.2, 3.6, 1), 0.15), (20, 5, lan(2.4, 9.0, 2)),
             (34, 18, lan(1.1, 3.0, 1), 0.2), (46, 18, G.window_rect(1.0, 1.8, 1, 3), 0.2), (58, 16, lan(0.9, 2.4, 1), 0.2)]
    TW.round_tower(g, t['x'], t['y'], t['base'], t['R'], t['shaft'], t['cone'], rng, bands=(12.5, 31, 43, 55, 65.5),
                   tiers=tiers, top='corbel_cone', cone_p=1.18, ribs=14,
                   dormers=[(0.2, 10, 1.7), (0.46, 7, 1.4), (0.7, 5, 1.1)], fin=t['fin'], lit_p=0.6, segs=72,
                   eave_out=2.2, found=14.0)
    return finish(g, 'Castle_GrandTower', coll)


def build_attendants(coll, seed=4):
    rng = np.random.default_rng(seed)
    g = Geo('Castle_GrandTower_Turrets')
    for i, (x, y, R, dz, shaft, cone, kind) in enumerate([t for t in L.TURRETS if t[6] in ('plain', 'bracket')]):
        cop = TW.COPPER if i == 4 else TW.SLATE
        if kind == 'bracket':
            TW.bracket_turret(g, x, y, Z0 + dz, R, shaft, cone, rng, cone_mat=cop)
        else:
            tiers = [(8.0 + 14 * k, 3, lan(0.8, 2.4, 1) if k % 2 == 0 else G.window_slit(0.3, 2.2)) for k in range(int(shaft / 16))]
            TW.round_tower(g, x, y, Z0 + dz, R, shaft, cone, rng, bands=tuple(np.arange(12.0, shaft - 4, 16.0)),
                           tiers=tiers, top='corbel_cone', eave_out=1.1, fin=4.5, lit_p=0.55, segs=24, cone_p=1.12,
                           cone_mat=cop, found=(20.0 if dz < 1 else 4.0), flare=1.2 if dz < 1 else 0.0, band_out=0.35)
    return finish(g, 'Castle_GrandTower_Turrets', coll)


def build_library(coll, seed=5):
    rng = np.random.default_rng(seed)
    lb = L.CASTLE['library']
    g = Geo('Castle_LibraryWing')
    H.gothic_hall(g, lb['cx'], lb['cy'], lb['L'], lb['D'], lb['base'], lb['eaves'], lb['pitch'], rng, bay_w=9.0,
                  lit_p=0.6, buttresses=True, chimneys=2, flying=True, big=(2.3, 8.0), sill_z=15.5, low_win=False,
                  frieze=True, ends=False)
    ga = L.CASTLE['gallery']
    H.arcade_gallery(g, ga['x0'], ga['x1'], ga['y0'], ga['y1'], ga['base'], ga['h'], rng, lit_p=0.75)
    # cross-gable wing behind the library (ridge along Y)
    w = Geo('wing', [])
    H.gothic_hall(w, 0.0, 0.0, 24.0, 20.0, Z0, 27.0, 52.0, rng, bay_w=8.0, lit_p=0.55, buttresses=True, big=(2.0, 8.0),
                  sill_z=9.0, low_win=False, frieze=False, ends=True, chimneys=1, north_lit=0.45)
    g.add_geo(w, pos=(-58.0, 26.0, 0.0), yaw=math.pi / 2, rng=rng)
    return finish(g, 'Castle_LibraryWing', coll)


def build_clock_tower(coll, seed=6):
    rng = np.random.default_rng(seed)
    c = L.CASTLE['clock']
    g = Geo('Castle_ClockTower')
    shaft = c['shaft'] + c['belfry']
    TW.square_tower(g, c['x'], c['y'], c['base'], c['s'], c['s'], shaft, rng, bands=(14, 30, 45),
                    tiers=[(6, 3, lan(1.4, 5.5, 1)), (19, 3, lan(1.3, 4.6, 1)), (35, 3, lan(1.3, 4.0, 1)),
                           (shaft - 12.0, 3, lan(1.2, 8.0, 1, rise_k=1.05))],
                    clock=dict(z=44, r=3.5, faces=('S', 'E', 'W')), spire=dict(H=c['spire'], lucarnes=((0.3, 1.0), (0.55, 0.8)), fin=c['fin']),
                    lit_p=0.55, found=14.0)
    return finish(g, 'Castle_ClockTower', coll)


def build_spire_tower(coll, seed=7):
    rng = np.random.default_rng(seed)
    s = L.CASTLE['spire']
    g = Geo('Castle_SpireTower')
    TW.square_tower(g, s['x'], s['y'], s['base'], s['s'], s['s'], s['shaft'], rng, bands=(14, 28, 42, 56),
                    tiers=[(7, 2, lan(1.4, 5.0, 1)), (20, 2, lan(1.3, 4.2, 1)), (34, 3, lan(1.2, 3.6, 1)),
                           (48, 3, lan(1.1, 3.2, 1)), (61, 2, lan(1.0, 2.6, 1))],
                    spire=dict(H=s['spire'], lucarnes=((0.28, 1.1), (0.52, 0.9)), fin=s['fin']), lit_p=0.55, found=14.0)
    return finish(g, 'Castle_SpireTower', coll)


def build_right_cluster(coll, seed=8):
    rng = np.random.default_rng(seed)
    C = L.CASTLE
    g = Geo('Castle_RightCluster')
    rh = C['righthall']
    H.gothic_hall(g, rh['cx'], rh['cy'], rh['L'], rh['D'], rh['base'], rh['eaves'], rh['pitch'], rng, bay_w=9.2,
                  lit_p=0.6, chimneys=2, big=(2.3, 9.0), sill_z=9.5, flying=False)
    r = C['roundb']
    TW.round_tower(g, r['x'], r['y'], r['base'], r['R'], r['shaft'], r['cone'], rng, bands=(12, 25, 37),
                   tiers=[(6, 8, lan(1.1, 3.6, 1), 0.1), (18, 9, lan(1.0, 3.2, 1), 0.15), (30, 9, G.window_rect(0.9, 1.7, 1, 2), 0.2),
                          (41, 8, lan(0.9, 2.2, 1), 0.2)],
                   top='crenel_cone', cone_p=1.12, ribs=8, dormers=[(0.3, 5, 1.0)], fin=r['fin'], lit_p=0.55, segs=40,
                   eave_out=1.5, found=14.0)
    o = C['octc']
    TW.round_tower(g, o['x'], o['y'], o['base'], o['R'], o['shaft'], o['cone'], rng, bands=(14, 30, 46),
                   tiers=[(7, 8, lan(0.9, 3.2, 1)), (22, 8, lan(0.9, 3.0, 1)), (37, 8, lan(0.8, 2.6, 1)), (51, 8, G.window_slit(0.3, 2.2))],
                   top='corbel_cone', cone_p=1.22, cone_mat=TW.COPPER, fin=o['fin'], lit_p=0.5, segs=8, smooth=False,
                   yaw0=math.pi / 8, eave_out=1.2, found=14.0, dormers=[(0.35, 4, 0.9)])
    d = C['roundd']
    TW.round_tower(g, d['x'], d['y'], d['base'], d['R'], d['shaft'], d['cone'], rng, bands=(12, 24, 34),
                   tiers=[(6, 9, lan(1.0, 3.0, 1)), (16, 10, lan(0.9, 2.6, 1), 0.2), (27, 9, G.window_slit(0.3, 2.2))],
                   top='corbel_cone', cone_p=1.14, fin=d['fin'], lit_p=0.5, segs=32, eave_out=1.4, found=14.0,
                   dormers=[(0.3, 4, 1.0)])
    for (kind, x, y, r, shaft, roof, sty) in L.CLUSTER_R:
        mat = TW.COPPER if sty == 'copper' else TW.SLATE
        if kind == 'round':
            n_t = 1 + int(shaft / 30)
            tiers = [(8.0 + 17.0 * k, 3 if r < 3 else 6, lan(0.8, 2.4, 1) if k % 2 == 0 else G.window_slit(0.3, 2.2)) for k in range(n_t)]
            TW.round_tower(g, x, y, Z0, r, shaft, roof, rng, bands=tuple(np.arange(13.0, shaft - 3, 17.0)), tiers=tiers,
                           top='corbel_cone', eave_out=1.0 if r < 3 else 1.4, fin=4.5, lit_p=0.55, segs=20 if r < 3 else 30,
                           cone_p=1.12, cone_mat=mat, found=14.0, flare=1.0, band_out=0.3, dormers=[(0.35, 3, 0.8)] if r > 4 else ())
        else:
            TW.square_tower(g, x, y, Z0, r, r, shaft, rng, bands=(14, 28, 42), tiers=[(7, 2, lan(1.1, 3.6, 1)), (20, 2, lan(1.0, 3.2, 1)), (34, 2, lan(1.0, 3.0, 1)), (47, 2, lan(0.9, 2.6, 1))],
                            spire=dict(H=roof, lucarnes=((0.3, 0.9),), fin=5.0), lit_p=0.55, found=14.0, corner_pinnacles=False)
    return finish(g, 'Castle_RightCluster', coll)


def build_gatehouse(coll, seed=9):
    rng = np.random.default_rng(seed)
    gh = L.CASTLE['gatehouse']
    g = Geo('Castle_Gatehouse')
    H.gatehouse(g, gh['cx'], gh['cy'], gh['sx'], gh['sy'], gh['base'], gh['h'], rng)
    H.arcade_gallery(g, 59.0, 82.0, -15.0, -5.0, Z0, 16.0, rng, lit_p=0.7)
    return finish(g, 'Castle_Gatehouse', coll)


def build_north_range(coll, seed=10):
    rng = np.random.default_rng(seed)
    nr = L.CASTLE['northrange']
    g = Geo('Castle_NorthRange')
    H.gothic_hall(g, nr['cx'], nr['cy'], nr['L'], nr['D'], nr['base'], nr['eaves'], nr['pitch'], rng, bay_w=10.0,
                  lit_p=0.5, north_lit=0.4, chimneys=3, flying=True, big=(2.2, 8.4), sill_z=7.5, low_win=True)
    return finish(g, 'Castle_NorthRange', coll)


BUILDERS = dict(hall=build_great_hall, hall_turrets=build_hall_turrets, grand=build_grand_tower,
                attendants=build_attendants, library=build_library, clock=build_clock_tower, spire=build_spire_tower,
                right=build_right_cluster, gate=build_gatehouse, north=build_north_range)


def run(which=None, clear=True):
    placeholder_mats()
    coll = S.ensure_collection('Castle')
    if clear:
        S.clear_collection('Castle')
    out = {}
    for k in (which or BUILDERS.keys()):
        t0 = time.time()
        obj, cnt = BUILDERS[k](coll)
        out[k] = (cnt, round(time.time() - t0, 2))
    return out
