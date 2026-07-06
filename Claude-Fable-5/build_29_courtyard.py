"""North grounds: cloister quad, library hall, courtyard paving slabs."""
import bpy
import math
import hog
import hogkit as hk

hk.init()
M = hk.M

# idempotent: remove anything this script previously created
for ob in list(bpy.data.objects):
    if ob.name.startswith(('Cloister_', 'Library_')):
        bpy.data.objects.remove(ob, do_unlink=True)
walls_coll = bpy.data.collections.get('Walls')
if walls_coll:
    for ob in list(walls_coll.objects):
        if ob.name.startswith(('Lantern', 'LanternCore')):
            bpy.data.objects.remove(ob, do_unlink=True)
hog.purge()

win_s = hk.window_template('lancet_s', 0.9, 2.4)
win_m = hk.window_template('lancet_m', 1.5, 3.6, mullions=1)

# ------------------------------------------------------------ cloister quad
CQX, CQY = -62.0, 30.0
S = 26.0
hog.box('Cloister_Court', 'Walls', size=(S, S, 0.4), loc=(CQX, CQY, 74.8),
        mat=M['trim'])
for i, (dx, dy, sx, sy) in enumerate([(0, -S / 2, S, 1.2), (0, S / 2, S, 1.2),
                                      (-S / 2, 0, 1.2, S), (S / 2, 0, 1.2, S)]):
    hog.box(f'Cloister_Wall_{i}', 'Walls', size=(sx, sy, 4.2),
            loc=(CQX + dx, CQY + dy, 75.0), mat=M['wall'])
# cloister walk roofs (lean-to strips inside)
for i, (dx, dy, sx, sy) in enumerate([(0, -S / 2 + 1.6, S - 3, 2.6),
                                      (0, S / 2 - 1.6, S - 3, 2.6),
                                      (-S / 2 + 1.6, 0, 2.6, S - 3),
                                      (S / 2 - 1.6, 0, 2.6, S - 3)]):
    hog.box(f'Cloister_Walk_{i}', 'Walls', size=(sx, sy, 0.3),
            loc=(CQX + dx, CQY + dy, 78.6), mat=M['slate'])
for (dx, dy) in [(-S / 2, -S / 2), (S / 2, -S / 2), (S / 2, S / 2),
                 (-S / 2, S / 2)]:
    hk.pinnacle(f'Cloister_Pin_{dx}_{dy}', 'Walls',
                (CQX + dx, CQY + dy, 79.2), r=0.5, h=3.4)
# small fountain at center
hog.cyl('Cloister_Fountain', 'Walls', r=2.2, h=0.8, loc=(CQX, CQY, 75.0),
        segs=16, mat=M['trim'])
hog.cyl('Cloister_Fountain2', 'Walls', r=0.4, h=2.2, loc=(CQX, CQY, 75.0),
        segs=10, mat=M['trim'])

# ------------------------------------------------------------ library hall
LX, LY, LR = 8.0, 46.0, math.radians(8)
hog.box('Library_Body', 'Walls', size=(20, 11, 14), loc=(LX, LY, 72),
        rot=LR, mat=M['wall'])
hk.gable_roof('Library_Roof', 'Walls', 20, 11, 5.5, (LX, LY, 86), rot=LR)
hk.windows_on_rect(win_m, 'Windows', (LX, LY), 20, 11, LR, 'N', [80.0], 4)
hk.windows_on_rect(win_s, 'Windows', (LX, LY), 20, 11, LR, 'S', [80.0], 4)
hk.round_tower('Library_Turret', 'Walls', LX + 11.5, LY + 4, 72.0, r=1.9,
               body_h=18, roof_h=7, segs=12, taper=1.0, bands=1,
               machicolate=False, win_me=win_s, win_rows=1, win_cols=2,
               win_z0=12, seed=80)

# lanterns along the main courtyard path (entrance -> cloister)
for t in range(5):
    x = -26 - (26 + 36) * t / 4
    y = 22 + 8 * math.sin(t * 1.3)
    hk.place_lantern('Walls', (x, y, 75.05))
