"""Stage 2a: castle block-out from the layout data (massing / silhouette check)."""
import bpy
import numpy as np
import math
import importlib
import hw_layout as L
import hw_geo
import hw_arch as A
import hw_scene as S
for _m in (L, hw_geo, A, S):
    importlib.reload(_m)
from hw_geo import Geo, boxes


def run():
    coll = S.ensure_collection('Castle')
    S.clear_collection('Castle')
    S.ensure_material('M_Stone', (0.42, 0.38, 0.32), 0.9)
    S.ensure_material('M_Slate', (0.10, 0.12, 0.17), 0.5)
    S.ensure_material('M_Copper', (0.10, 0.45, 0.38), 0.4)
    g = Geo('Castle_Blockout', ['M_Stone', 'M_Slate', 'M_Copper'])
    C = L.CASTLE
    h = C['hall']
    A.hall_blockout(g, h['cx'], h['cy'], h['L'], h['D'], h['base'], h['eaves'], h['pitch'])
    t = C['grand']
    A.round_tower_blockout(g, t['x'], t['y'], t['base'], t['R'], t['shaft'], t['cone'], t['fin'], t['gallery'])
    lb = C['library']
    A.hall_blockout(g, lb['cx'], lb['cy'], lb['L'], lb['D'], lb['base'], lb['eaves'], lb['pitch'])
    ga = C['gallery']
    boxes(g, [((ga['x0'] + ga['x1']) / 2, (ga['y0'] + ga['y1']) / 2, ga['base'] - 26)],
          [(ga['x1'] - ga['x0'], ga['y1'] - ga['y0'], ga['h'] + 26)], m='M_Stone', faces=(0, 1, 2, 3, 4))
    c = C['clock']
    A.square_tower_blockout(g, c['x'], c['y'], c['base'], c['s'], c['shaft'] + c['belfry'], c['spire'], c['fin'])
    sp = C['spire']
    A.square_tower_blockout(g, sp['x'], sp['y'], sp['base'], sp['s'], sp['shaft'], sp['spire'], sp['fin'])
    for key in ('roundb', 'octc', 'roundd'):
        r = C[key]
        A.round_tower_blockout(g, r['x'], r['y'], r['base'], r['R'], r['shaft'], r['cone'], r['fin'],
                               segs=32 if key != 'octc' else 8)
    rh = C['righthall']
    A.hall_blockout(g, rh['cx'], rh['cy'], rh['L'], rh['D'], rh['base'], rh['eaves'], rh['pitch'])
    gh = C['gatehouse']
    boxes(g, [(gh['cx'], gh['cy'], gh['base'] - 26)], [(gh['sx'], gh['sy'], gh['h'] + 26)], m='M_Stone',
          faces=(0, 1, 2, 3, 4))
    nr = C['northrange']
    A.hall_blockout(g, nr['cx'], nr['cy'], nr['L'], nr['D'], nr['base'], nr['eaves'], nr['pitch'])
    for (x, y, R, dz, shaft, cone, kind) in L.TURRETS:
        A.round_tower_blockout(g, x, y, L.Z0 + dz, R, shaft, cone, 3.0, found=(26.0 if dz < 1 else 6.0), segs=16)
    # boathouse
    b = L.BOATHOUSE
    A.hall_blockout(g, b['cx'], b['cy'], b['L'], b['D'], b['base'], 8.0, 52.0, found=6.0)
    # viaduct blockout
    v = L.VIADUCT
    n = v['n']
    pitch = (v['x1'] - v['x0']) / n
    for i in range(n + 1):
        xp = v['x0'] + i * pitch
        boxes(g, [(xp, v['y'], -20.0)], [(4.2, v['width'], v['deck'] - 14.0 + 20.0)], m='M_Stone')
    boxes(g, [((v['x0'] + v['x1']) / 2, v['y'], v['deck'] - 14.0)], [(v['x1'] - v['x0'], v['width'] + 1.0, 14.0)],
          m='M_Stone')
    obj = g.to_object(bpy, coll, 'Castle_Blockout')
    return dict(faces=g.count())
