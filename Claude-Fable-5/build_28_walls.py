"""Curtain/retaining walls around the plateau rim: varied heights, windows,
crenellated tops, detailed drum towers. Replaces the blockout wall band."""
import bpy
import math
import hog
import hogkit as hk

hk.init()
M = hk.M

win_s = hk.window_template('lancet_s', 0.9, 2.4)
win_m = hk.window_template('lancet_m', 1.5, 3.6, mullions=1)
win_slit = hk.window_template('slit', 0.55, 1.6, frame_t=0.10, sill=False)
win_sq = hk.window_template('sq_mull', 1.8, 2.6, mullions=1, transom=True)

pts = [(-102, 0), (-95, -33), (-64, -55), (-26, -66), (16, -62), (54, -50),
       (85, -34), (100, -6), (95, 25), (72, 46), (39, 60), (-5, 64),
       (-49, 58), (-84, 37), (-102, 0)]

# per-segment top heights (varied; south segments lower so the buildings
# behind them read above the band)
tops = [76, 72, 70, 71, 72, 70, 74, 78, 75, 74, 76, 75, 77, 76]
BASE = 52.0

for i in range(len(pts) - 1):
    (x0, y0), (x1, y1) = pts[i], pts[i + 1]
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    L = math.hypot(x1 - x0, y1 - y0)
    ang = math.atan2(y1 - y0, x1 - x0)
    top = tops[i]
    hog.box(f'Wall_{i:02d}', 'Walls', size=(L + 1.5, 3, top - BASE),
            loc=(mx, my, BASE), rot=ang, mat=M['wall'])
    hk.crenel_strip(f'Wall_Cren_{i:02d}', 'Walls', L + 1.5,
                    loc=(mx + math.sin(ang) * 1.35, my - math.cos(ang) * 1.35,
                         top), rot=ang, t=0.5)
    # windows punched into the tall south/east faces (inhabited walls)
    if y0 < -20 or x0 > 80:
        n = max(3, int(L / 6.5))
        import random as _rr
        rngw = _rr.Random(900 + i)
        for k in range(n):
            t = (k + 0.5) / n
            wx = x0 + (x1 - x0) * t
            wy = y0 + (y1 - y0) * t
            # outward = right of direction
            ox, oy = math.sin(ang), -math.cos(ang)
            jz = rngw.uniform(-1.4, 1.4)
            hk.place_window(win_m, 'Windows',
                            (wx + ox * 1.55, wy + oy * 1.55, top - 7.5 + jz),
                            math.atan2(ox, -oy))
            if k % 2 == 0 and rngw.random() < 0.75:
                hk.place_window(win_s, 'Windows',
                                (wx + ox * 1.55, wy + oy * 1.55,
                                 top - 13.5 + rngw.uniform(-1.2, 1.2)),
                                math.atan2(ox, -oy))
    # shallow pilaster buttresses at segment joints
    ox, oy = math.sin(ang), -math.cos(ang)
    hog.box(f'Wall_But_{i:02d}', 'Walls', size=(2.4, 1.2, top - BASE - 2),
            loc=(x0 + ox * 1.6, y0 + oy * 1.6, BASE), rot=ang, mat=M['wall'])

# detailed drum towers at alternating vertices, no two alike
drums = [
    (0, 4.2, 30, 8, 'witch', True),
    (2, 3.6, 34, 9, 'witch', False),
    (4, 4.6, 28, None, None, True),      # open crenellated top
    (6, 3.9, 33, 10, 'cone', False),
    (8, 4.4, 30, 9, 'witch', True),
    (10, 3.5, 27, None, None, True),
    (12, 4.0, 31, 8, 'witch', False),
]
for (i, r, h, roof_h, style, mach) in drums:
    x, y = pts[i]
    hk.round_tower(f'WallDrum_{i:02d}', 'Walls', x, y, 54.0, r=r, body_h=h,
                   roof_h=roof_h, segs=16, taper=0.97, bands=1,
                   machicolate=mach, roof=style or 'witch',
                   win_me=win_slit, win_rows=2, win_cols=3, win_z0=h - 12,
                   win_row_step=6, seed=60 + i)

# west anchor tower (bigger, distinct: copper roof)
hk.round_tower('WestTower', 'Walls', -95, 8, 58.0, r=6.0, body_h=44,
               roof_h=15, segs=24, taper=0.94, bands=2, machicolate=True,
               win_me=win_s, win_rows=3, win_cols=4, win_z0=14,
               roof_mat=M['copper'], seed=70)
