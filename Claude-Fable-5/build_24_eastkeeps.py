"""East keep group: main keep with bartizans, terraced gate halls,
gatehouse at the viaduct shelf, east round tower, south gallery."""
import bpy
import math
import hog
import hogkit as hk

hk.init()
M = hk.M

win_s = hk.window_template('lancet_s', 0.9, 2.4)
win_m = hk.window_template('lancet_m', 1.5, 3.6, mullions=1)
win_sq = hk.window_template('sq_mull', 1.8, 2.6, mullions=1, transom=True)
win_slit = hk.window_template('slit', 0.55, 1.6, frame_t=0.10, sill=False)

# ---------------------------------------------------------------- Keep_Main
KX, KY, KR = 34.0, 10.0, math.radians(15)
hog.box('Keep_Body', 'TowerCluster', size=(26, 20, 47), loc=(KX, KY, 72),
        rot=KR, mat=M['wall'])
hk.gable_roof('Keep_Roof', 'TowerCluster', 26, 20, 10.5, (KX, KY, 119),
              rot=KR)
hk.windows_on_rect(win_m, 'Windows', (KX, KY), 26, 20, KR, 'S',
                   [88.0, 99.0, 110.0], 4)
hk.windows_on_rect(win_sq, 'Windows', (KX, KY), 26, 20, KR, 'N',
                   [92.0, 104.0], 3)
hk.windows_on_rect(win_s, 'Windows', (KX, KY), 26, 20, KR, 'W',
                   [90.0, 102.0], 2)
# corner bartizans
for i, (lx, ly) in enumerate([(-13, -10), (13, -10), (13, 10), (-13, 10)]):
    cr, sr = math.cos(KR), math.sin(KR)
    bx = KX + lx * cr - ly * sr
    by = KY + lx * sr + ly * cr
    hk.round_tower(f'Keep_Bart_{i}', 'TowerCluster', bx, by, 104.0, r=1.7,
                   body_h=15, roof_h=6.5, segs=12, taper=1.0, bands=0,
                   machicolate=False, win_me=win_slit, win_rows=1,
                   win_cols=2, win_z0=8, seed=40 + i)

# ------------------------------------------------- terraced gate halls (E)
hog.box('GateHall_Low', 'TowerCluster', size=(18, 16, 32), loc=(80, -7, 58),
        mat=M['wall'])
hk.gable_roof('GateHall_LowRoof', 'TowerCluster', 18, 16, 7, (80, -7, 90))
hk.windows_on_rect(win_sq, 'Windows', (80, -7), 18, 16, 0.0, 'S',
                   [72.0, 82.0], 3)
hk.windows_on_rect(win_s, 'Windows', (80, -7), 18, 16, 0.0, 'E',
                   [70.0, 80.0], 3)
hk.windows_on_rect(win_sq, 'Windows', (62, -9), 16, 14, 0.0, 'E',
                   [80.0, 92.0], 2)
hog.box('GateHall_High', 'TowerCluster', size=(16, 14, 32), loc=(62, -9, 72),
        mat=M['wall'])
hk.gable_roof('GateHall_HighRoof', 'TowerCluster', 16, 14, 6.5, (62, -9, 104))
hk.windows_on_rect(win_m, 'Windows', (62, -9), 16, 14, 0.0, 'S',
                   [82.0, 94.0], 3)

# ---------------------------------------------------- gatehouse at viaduct
GHX, GHY = 97.0, -6.0
hog.box('Gatehouse_Body', 'TowerCluster', size=(10, 13, 17), loc=(GHX, GHY, 58),
        mat=M['wall'])
# entrance arch (dark recess) facing east toward the viaduct
arch = hk.arch_outline(4.6, 3.2, seg=8)
pts = [(4.6 / 2, 0)] + [(x, z + 3.4) for (x, z) in arch[0:]] + [(-4.6 / 2, 0)]
hk.prism_xz('Gatehouse_Arch', 'TowerCluster',
            [(p[0], p[1] + 58.0 - 58.0) for p in pts], 0.8,
            loc=(GHX + 5.0, GHY, 58.0), rot=math.pi / 2,
            mat=hog.flat_mat('DarkVoid', (0.01, 0.01, 0.01), 1.0))
hk.crenel_strip('Gatehouse_Cren_E', 'TowerCluster', 13,
                loc=(GHX + 5.1, GHY, 75), rot=math.pi / 2, t=0.5)
# windows above the arch, facing the viaduct
hk.place_window(win_s, 'Windows', (GHX + 5.05, GHY - 2.2, 67.5), math.pi / 2)
hk.place_window(win_s, 'Windows', (GHX + 5.05, GHY + 2.2, 67.5), math.pi / 2)
hk.place_window(win_slit, 'Windows', (GHX + 5.05, GHY, 71.0), math.pi / 2)
for sy in (-1, 1):
    hk.round_tower(f'Gatehouse_Turret_{sy}', 'TowerCluster', GHX + 4.0,
                   GHY + sy * 6.0, 58.0, r=2.0, body_h=20, roof_h=8, segs=12,
                   taper=1.0, bands=1, machicolate=False, win_me=win_slit,
                   win_rows=2, win_cols=2, win_z0=10, seed=50 + sy)

# ---------------------------------------------------------------- EastTower
hk.round_tower('EastTower', 'TowerCluster', 74, 18, 72, r=7.0, body_h=76,
               roof_h=30, segs=28, taper=0.93, bands=3, machicolate=True,
               win_me=win_m, win_rows=4, win_cols=4, win_z0=20,
               win_row_step=16, seed=5)

# ---------------------------------------------------------------- gallery S
hog.box('Gallery_Body', 'Walls', size=(58, 9, 34), loc=(-8, -52, 62),
        mat=M['wall'])
hk.gable_roof('Gallery_Roof', 'Walls', 58, 9, 5.5, (-8, -52, 96))
hk.windows_on_rect(win_m, 'Windows', (-8, -52), 58, 9, 0.0, 'S',
                   [78.0, 88.0], 7, margin=4)
for k in range(6):
    xr = -8 - 24 + k * 9.6 + 4.8
    hk.buttress(f'Gal_But_{k}', 'Walls', 28.0, (xr, -56.5, 62.0),
                rot=math.pi, w=1.3, d0=2.0, steps=3)
