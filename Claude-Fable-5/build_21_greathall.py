"""Great Hall, detailed: podium, bays with tall lancet windows, buttresses,
parapet with pinnacles, corner turrets, gable windows, entrance hall."""
import bpy
import math
import hog
import hogkit as hk

hog.clear_coll('GreatHall')
hk.init()
M = hk.M

CX, CY = -58.0, -16.0     # hall center
SX, SY = 64.0, 19.0       # footprint
WZ0, WZ1 = 70.0, 108.0    # wall base/top
ROOF_H = 12.5
PODZ = 62.0

# window meshes
win_hall = hk.window_template('gh_hall', 2.6, 12.0, mullions=2, transom=True)
win_low = hk.window_template('gh_low', 1.3, 3.0)
win_north = hk.window_template('gh_north', 1.7, 4.5, mullions=1)
win_gable = hk.window_template('gh_gable', 5.2, 14.0, mullions=3, transom=True)
win_slit = hk.window_template('slit', 0.55, 1.6, frame_t=0.10, sill=False)

# ---------------------------------------------------------------- podium
hog.box('GH_Podium', 'GreatHall', size=(SX + 2.4, SY + 2.4, 9),
        loc=(CX, CY, PODZ), mat=M['wall'])
# hall body
hog.box('GH_Body', 'GreatHall', size=(SX, SY, WZ1 - WZ0),
        loc=(CX, CY, WZ0), mat=M['wall'])
# roof
hk.gable_roof('GH_Roof', 'GreatHall', SX, SY, ROOF_H, (CX, CY, WZ1),
              overhang=0.45)

# ---------------------------------------------------------------- south face
SFY = CY - SY / 2
for k in range(7):
    xr = -25.5 + k * 8.5
    hk.place_window(win_hall, 'Windows', (CX + xr, SFY - 0.05, 89.0), 0.0)
for k in range(6):
    xr = -21.25 + k * 8.5
    hk.buttress(f'GH_But_S{k}', 'GreatHall', 33.0, (CX + xr, SFY, WZ0),
                rot=math.pi, w=1.6, d0=3.1, steps=4)
    hk.pinnacle(f'GH_Pin_S{k}', 'GreatHall', (CX + xr, SFY - 0.75, 103.0),
                r=0.55, h=4.5)
# sparse low windows on the podium/lower wall
for xr in (-17.0, 0.0, 17.0):
    hk.place_window(win_low, 'Windows', (CX + xr, SFY - 0.05, 76.5), 0.0)
# parapet
hk.crenel_strip('GH_Cren_S', 'GreatHall', SX - 5, loc=(CX, SFY + 0.1, WZ1),
                t=0.55)

# ---------------------------------------------------------------- north face
NFY = CY + SY / 2
for k in range(7):
    xr = -25.5 + k * 8.5
    hk.place_window(win_north, 'Windows', (CX + xr, NFY + 0.05, 88.0),
                    math.pi)
for k in range(6):
    xr = -21.25 + k * 8.5
    hk.buttress(f'GH_But_N{k}', 'GreatHall', 33.0, (CX + xr, NFY, WZ0),
                rot=0.0, w=1.5, d0=2.2, steps=4)
hk.crenel_strip('GH_Cren_N', 'GreatHall', SX - 5, loc=(CX, NFY - 0.1, WZ1),
                t=0.55)

# ---------------------------------------------------------------- gable ends
# template faces -Y at rot 0; rot -pi/2 faces -X (west), +pi/2 faces +X (east)
for sgn in (-1, 1):
    gx = CX + sgn * SX / 2
    grot = -math.pi / 2 if sgn < 0 else math.pi / 2
    hk.place_window(win_gable, 'Windows', (gx + sgn * 0.05, CY, 88.0), grot)
    hk.place_window(win_slit, 'Windows', (gx + sgn * 0.05, CY, 106.0), grot)

# ---------------------------------------------------------------- turrets
for i, (dx, dy) in enumerate([(-32, -9.5), (32, -9.5), (32, 9.5), (-32, 9.5)]):
    hk.round_tower(f'GH_Turret_{i}', 'GreatHall', CX + dx, CY + dy,
                   66.0, r=2.9, body_h=50, roof_h=12, segs=16, taper=0.99,
                   bands=1, machicolate=False, win_me=win_slit, win_rows=2,
                   win_cols=3, win_z0=38, seed=10 + i)

# ------------------------------------------------------- entrance hall (N)
EX, EY = -26.0, 12.0
hog.box('GH_EntranceBody', 'GreatHall', size=(17, 26, 22), loc=(EX, EY, 70),
        mat=M['wall'])
hk.gable_roof('GH_EntranceRoof', 'GreatHall', 26, 17, 7.5, (EX, EY, 92),
              rot=math.pi / 2)
for k in range(3):
    yr = EY - 8 + k * 8
    hk.place_window(win_north, 'Windows', (EX - 8.55, yr, 82.0), -math.pi / 2)
hk.round_tower('GH_StairTurret', 'GreatHall', EX - 8.5, EY + 11.5, 70.0,
               r=2.2, body_h=26, roof_h=9, segs=12, taper=1.0, bands=1,
               machicolate=False, win_me=win_slit, win_rows=2, win_cols=2,
               win_z0=8, seed=33)
