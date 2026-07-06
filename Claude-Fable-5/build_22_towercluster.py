"""Central tower cluster: grand tower + engaged attendants, mid towers,
clock tower with dial + octagonal spire."""
import bpy
import math
import hog
import hogkit as hk

hog.clear_coll('TowerCluster')
hog.clear_coll('ClockTower')
hk.init()
M = hk.M

win_s = hk.window_template('lancet_s', 0.9, 2.4)
win_m = hk.window_template('lancet_m', 1.5, 3.6, mullions=1)
win_pair = hk.window_template('lancet_pair', 2.2, 4.6, mullions=1)
win_slit = hk.window_template('slit', 0.55, 1.6, frame_t=0.10, sill=False)
win_belfry = hk.window_template('belfry', 2.6, 6.5, mullions=1)

GX, GY, GZ = -6.0, 26.0, 72.0

# ------------------------------------------------------- grand tower
hk.round_tower('GT_Main', 'TowerCluster', GX, GY, GZ, r=9.5, body_h=100,
               roof_h=34, segs=32, taper=0.92, bands=3, machicolate=True,
               win_me=win_pair, win_rows=5, win_cols=5, win_z0=30,
               win_row_step=14, seed=2)

# engaged attendant turrets, each different (no two towers identical)
att = [
    dict(dx=8.8, dy=8.8, r=2.6, h=112, roof=13, seed=21, style='witch'),
    dict(dx=-8.8, dy=8.8, r=2.2, h=88, roof=None, seed=22, style=None),
    dict(dx=8.8, dy=-8.8, r=2.4, h=96, roof=12, seed=23, style='cone'),
    dict(dx=-8.8, dy=-8.8, r=2.9, h=74, roof=14, seed=24, style='witch'),
]
for i, a in enumerate(att):
    hk.round_tower(f'GT_Att_{i}', 'TowerCluster', GX + a['dx'], GY + a['dy'],
                   GZ, r=a['r'], body_h=a['h'], roof_h=a['roof'], segs=16,
                   taper=0.97, bands=2,
                   machicolate=(i % 2 == 0) or a['roof'] is None,
                   roof=a['style'] or 'witch',
                   win_me=win_slit, win_rows=4, win_cols=3, win_z0=20,
                   win_row_step=18, seed=a['seed'])

# ------------------------------------------------------- mid towers
hk.round_tower('MT_South', 'TowerCluster', 14, -14, 72, r=5.0, body_h=52,
               roof_h=16, segs=24, taper=0.93, bands=2, machicolate=True,
               win_me=win_s, win_rows=3, win_cols=4, win_z0=16, seed=3)
hk.round_tower('MT_North', 'TowerCluster', 44, 34, 72, r=6.0, body_h=62,
               roof_h=18, segs=24, taper=0.95, bands=2, machicolate=False,
               win_me=win_m, win_rows=3, win_cols=4, win_z0=18, seed=4,
               roof_mat=hk.role_mats()['copper'])

# ------------------------------------------------------- clock tower
CTX, CTY = -36.0, -18.0
CT_W = 11.0
CT_TOP = 126.0
hog.box('CT_Body', 'ClockTower', size=(CT_W, CT_W, CT_TOP - 72), loc=(CTX, CTY, 72),
        mat=M['wall'])
# corner pilaster strips
for sx in (-1, 1):
    for sy in (-1, 1):
        hog.box(f'CT_Pil_{sx}{sy}', 'ClockTower', size=(1.1, 1.1, CT_TOP - 72),
                loc=(CTX + sx * (CT_W / 2 - 0.4), CTY + sy * (CT_W / 2 - 0.4), 72),
                mat=M['trim'])
# string courses
for z in (96.0, 112.0):
    hog.box(f'CT_String_{int(z)}', 'ClockTower', size=(CT_W + 0.7, CT_W + 0.7, 0.5),
            loc=(CTX, CTY, z), mat=M['trim'])
# clock dials on south and west faces
hk.clock_face('CT_Dial_S', 'ClockTower', (CTX, CTY - CT_W / 2 - 0.05, 116.5),
              0.0, r=2.8)
hk.clock_face('CT_Dial_W', 'ClockTower', (CTX - CT_W / 2 - 0.05, CTY, 116.5),
              -math.pi / 2, r=2.8)
# belfry openings below dials
for rot, (ox, oy) in ((0.0, (0, -CT_W / 2 - 0.03)),
                      (-math.pi / 2, (-CT_W / 2 - 0.03, 0)),
                      (math.pi, (0, CT_W / 2 + 0.03)),
                      (math.pi / 2, (CT_W / 2 + 0.03, 0))):
    hk.place_window(win_belfry, 'Windows', (CTX + ox, CTY + oy, 98.0), rot)
# tall paired windows lower shaft (south face)
for z in (78.0, 87.0):
    hk.place_window(win_m, 'Windows', (CTX, CTY - CT_W / 2 - 0.03, z), 0.0)
# parapet + corner pinnacles + spire
hk.crenel_strip('CT_Cren_S', 'ClockTower', CT_W + 0.8,
                loc=(CTX, CTY - CT_W / 2 - 0.2, CT_TOP), t=0.5)
hk.crenel_strip('CT_Cren_N', 'ClockTower', CT_W + 0.8,
                loc=(CTX, CTY + CT_W / 2 + 0.2, CT_TOP), t=0.5)
hk.crenel_strip('CT_Cren_W', 'ClockTower', CT_W + 0.8,
                loc=(CTX - CT_W / 2 - 0.2, CTY, CT_TOP), rot=math.pi / 2, t=0.5)
hk.crenel_strip('CT_Cren_E', 'ClockTower', CT_W + 0.8,
                loc=(CTX + CT_W / 2 + 0.2, CTY, CT_TOP), rot=math.pi / 2, t=0.5)
for sx in (-1, 1):
    for sy in (-1, 1):
        hk.pinnacle(f'CT_Pin_{sx}{sy}', 'ClockTower',
                    (CTX + sx * (CT_W / 2 - 0.4), CTY + sy * (CT_W / 2 - 0.4),
                     CT_TOP), r=0.62, h=5.5)
hk.octagonal_spire('CT_Spire', 'ClockTower', CT_W * 0.78, 19.0,
                   (CTX, CTY, CT_TOP + 0.3))
