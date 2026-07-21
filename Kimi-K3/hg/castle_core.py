import bpy, math, random
from mathutils import Vector, Matrix, Euler
from math import sin, cos, pi

C  = bpy.data.collections["Castle"]
CW = bpy.data.collections["Castle_Windows"]

stone  = mat_stone()
stoned = mat_stone_dark()
slate  = mat_slate()
verdi  = mat_verdigris()
metal  = mat_metal()

g_dark  = mat_glass_dark()
g_l1 = mat_glass("GlassWarm1", 0.85, 1.5)
g_l2 = mat_glass("GlassWarm2", 0.9, 4.0)
g_l3 = mat_glass("GlassWarm3", 1.0, 9.0)
g_l4 = mat_glass("GlassWarm4", 0.8, 18.0)
WINMATS = [g_dark, g_l1, g_l2, g_l3, g_l4]

ZB = 52.0   # castle plateau height

# ============================================================ GREAT HALL
# axis along X, at x[-88,-24], y center 20, width 26, wall h 17, roof h 13
gh_x0, gh_x1 = -82.0, -24.0
gh_len = gh_x1 - gh_x0
gh_cx, gh_cy = (gh_x0+gh_x1)/2, 8.0
gh_w, gh_wh, gh_rh = 26.0, 17.0, 13.0

box_obj("GreatHall_Body", (gh_cx, gh_cy, ZB+gh_wh/2), (gh_len, gh_w, gh_wh), C, stone)
gable_roof("GreatHall_Roof", gh_len, gh_w, gh_rh, (gh_cx, gh_cy, ZB+gh_wh), C, slate, overhang=1.2, axis='X')

# clerestory dormers along the roof
for i in range(9):
    dx = gh_x0 + 6 + i*6.6
    for sgn in (-1, 1):
        box_obj(f"GH_dorm_{i}_{sgn}", (dx, gh_cy+sgn*(gh_w/2-2.2), ZB+gh_wh+3.2), (2.2, 2.4, 3.6), C, stone)
        gable_roof(f"GH_dormroof_{i}_{sgn}", 2.2, 2.4, 1.6, (dx, gh_cy+sgn*(gh_w/2-2.2), ZB+gh_wh+5.0), C, slate, overhang=0.25, axis='Y')

# corner turrets: 4 slender with conical caps + finials
for i, (tx, ty) in enumerate([(gh_x0-1, gh_cy-gh_w/2-1), (gh_x0-1, gh_cy+gh_w/2+1),
                               (gh_x1+1, gh_cy-gh_w/2-1), (gh_x1+1, gh_cy+gh_w/2+1)]):
    tower(f"GH_Turret_{i}", tx, ty, ZB, 2.3, gh_wh+6.0, C, stone, slate, spire_h=9.0, corbel=True)

# buttresses + tall lancet windows on both long sides
specs = []
bays = 8
bay_w = gh_len / bays
for side in (-1, 1):
    wy = gh_cy + side*(gh_w/2 + 0.05)
    rot = Euler((0, 0, pi if side<0 else 0), 'XYZ')
    for b in range(bays):
        bx = gh_x0 + bay_w*(b+0.5)
        # twin lancets per bay
        for k in (-1, 1):
            wx = bx + k*bay_w*0.18
            specs.append(((wx, wy, ZB+2.5), rot, 2.4, 11.5, 8.0))
        # buttress at bay boundary
        if b > 0:
            buttress(f"GH_but_{side}_{b}", (gh_x0+bay_w*b, gh_cy+side*(gh_w/2+0.9), ZB),
                     14.5, C, stone, rot_z=0, depth=1.8, width=1.6, steps=3)
add_window_panes("GH_Windows", specs, CW, WINMATS)

# west gable end: big rose-ish tall window
specs_w = [((gh_x0-0.05, gh_cy, ZB+3.0), Euler((0, 0, pi/2), 'XYZ'), 5.0, 12.0, 8.5)]
add_window_panes("GH_WestWindow", specs_w, CW, [g_l2, g_l3])

# ============================================================ GRAND STAIRCASE TOWER (main cone)
gst_x, gst_y, gst_r = -14.0, -4.0, 13.0
tower("GrandTower", gst_x, gst_y, ZB, gst_r, 62, C, stone, slate,
      spire_h=46, corbel=True, finial=True, verts_n=28)
# ring of small windows spiraling up
specs = []
for row in range(6):
    z = ZB + 8 + row*9
    n = 7
    for i in range(n):
        a = (i/n)*2*pi + row*0.35
        wx, wy = gst_x+(gst_r+0.05)*cos(a), gst_y+(gst_r+0.05)*sin(a)
        specs.append(((wx, wy, z), Euler((0, 0, a-pi/2), 'XYZ'), 1.5, 3.4, 2.2))
add_window_panes("GT_Windows", specs, CW, WINMATS)
# attendant turrets on the grand tower (3 small ones clinging at mid height)
for i, a in enumerate([0.5, 2.4, 4.3]):
    tx, ty = gst_x+(gst_r+2.2)*cos(a), gst_y+(gst_r+2.2)*sin(a)
    tower(f"GT_att_{i}", tx, ty, ZB+18, 3.0, 40, C, stone, slate, spire_h=14, corbel=True)

# ============================================================ CLOCK TOWER
ct_x, ct_y = 36.0, 14.0
ct_w, ct_h = 15.0, 52.0
box_obj("ClockTower_Body", (ct_x, ct_y, ZB+ct_h/2), (ct_w, ct_w, ct_h), C, stone)
# corner pinnacles
for i,(sx,sy) in enumerate([(-1,-1),(-1,1),(1,-1),(1,1)]):
    tower(f"CT_pin_{i}", ct_x+sx*(ct_w/2-0.8), ct_y+sy*(ct_w/2-0.8), ZB+ct_h-6, 1.3, 6, C, stone, slate, spire_h=7, corbel=False)
# clock stage: slight flare
box_obj("ClockTower_Stage", (ct_x, ct_y, ZB+ct_h+2.5), (ct_w+2, ct_w+2, 5), C, stone)
cren = crenellations("CT_cren", ct_w+2, (ct_x, ct_y-(ct_w+2)/2, ZB+ct_h+5), C, stone, axis='X')
cren2 = crenellations("CT_cren2", ct_w+2, (ct_x, ct_y+(ct_w+2)/2, ZB+ct_h+5), C, stone, axis='X')
# gabled top with spire
gable_roof("CT_Gable", ct_w+2, ct_w+2, 9.0, (ct_x, ct_y, ZB+ct_h+5), C, slate, overhang=0.5, axis='X')
tower("CT_spire", ct_x, ct_y, ZB+ct_h+14, 3.2, 6, C, stone, slate, spire_h=16, corbel=True)

# clock faces on south and west: emissive dial + hands
dm = bpy.data.materials.new("ClockDial"); dm.use_nodes = True
_pbs = dm.node_tree.nodes.get("Principled BSDF")
_pbs.inputs["Emission Color"].default_value = (1.0, 0.72, 0.42, 1)
_pbs.inputs["Emission Strength"].default_value = 2.2
dial_mat = dm
def clock_face(name, loc, facing):
    # dial disc
    cyl_obj(name+"_dial", loc, 3.4, 0.3, C, dial_mat, verts=32)
    ob = bpy.context.active_object if False else bpy.data.objects[name+"_dial"]
    ob.rotation_euler[1] = pi/2 if facing=='W' else 0
    if facing in ('S','N'):
        ob.rotation_euler[0] = pi/2
    # hands: thin boxes
    ang_h, ang_m = 0.9, 2.6
    for nm, ang, ln in [("h", ang_h, 2.1), ("m", ang_m, 3.2)]:
        if facing=='W':
            hnd = box_obj(name+"_hand_"+nm, (loc[0]-0.45, loc[1], loc[2]), (0.18, 0.5, ln), C, metal)
            hnd.rotation_euler[0] = 0; hnd.rotation_euler[1] = 0
            hnd.rotation_euler[2] = 0
            hnd.rotation_euler[0] = ang
        else:
            hnd = box_obj(name+"_hand_"+nm, (loc[0], loc[1]-0.45 if facing=='S' else loc[1]+0.45, loc[2]), (0.5, 0.18, ln), C, metal)
            hnd.rotation_euler[1] = ang
    return

clock_face("Clock_S", (ct_x, ct_y-ct_w/2-0.6, ZB+ct_h-2), 'S')
clock_face("Clock_W", (ct_x-ct_w/2-0.6, ct_y, ZB+ct_h-2), 'W')

# clock tower windows
specs=[]
for row in range(4):
    z = ZB+6+row*10
    for face in range(4):
        a = face*pi/2
        off = ct_w/2+0.05
        wx, wy = ct_x+off*sin(a), ct_y-off*cos(a) if False else ct_y+off*cos(a)
        specs.append(((wx, wy, z), Euler((0,0,-a),'XYZ'), 1.6, 4.0, 2.8))
add_window_panes("CT_Windows", specs, CW, WINMATS)

# ============================================================ ASTRONOMY + EAST CLUSTER
tower("Astronomy", 64, 30, ZB, 7.0, 56, C, stone, slate, spire_h=34, corbel=True, verts_n=22)
tower("EastTower1", 82, 4, ZB, 9.0, 44, C, stone, slate, spire_h=26, corbel=True, verts_n=24)
tower("EastTower2", 56, -16, ZB, 7.5, 38, C, stone, slate, spire_h=20, corbel=True)
tower("SouthTurret", 28, -22, ZB, 5.0, 30, C, stone, slate, spire_h=16, corbel=True)
tower("NorthTurret", 10, 34, ZB, 4.5, 34, C, stone, verdi, spire_h=18, corbel=True)  # verdigris cap accent

# windows for east towers
specs=[]
for (tx,ty,tr,hgt) in [(64,30,7,50),(82,4,9,40),(56,-16,7.5,34),(28,-22,5,26),(10,34,4.5,30)]:
    rows = int(hgt/9)
    for row in range(rows):
        z = ZB+6+row*8.5
        n = max(4, int(tr*1.1))
        for i in range(n):
            a = i/n*2*pi + row*0.5
            specs.append(((tx+(tr+0.05)*cos(a), ty+(tr+0.05)*sin(a), z),
                          Euler((0,0,a-pi/2),'XYZ'), 1.1, 2.6, 1.7))
add_window_panes("East_Windows", specs, CW, WINMATS)

# ============================================================ CENTRAL WARD: hall linking grand tower & clock tower
box_obj("CentralHall", (12, 4, ZB+7), (40, 18, 14), C, stone)
gable_roof("CentralHall_Roof", 40, 18, 9, (12, 4, ZB+14), C, slate, overhang=0.9, axis='X')
specs=[]
for side in (-1,1):
    for i in range(6):
        wx = -6 + i*7.0
        wy = 4 + side*9.05
        rot = Euler((0,0, pi if side<0 else 0),'XYZ')
        specs.append(((wx, wy, ZB+3), rot, 1.8, 7.0, 4.8))
add_window_panes("CH_Windows", specs, CW, WINMATS)
# small roof turret
tower("CH_rooftur", 12, 4, ZB+23, 2.2, 4, C, stone, slate, spire_h=8, corbel=True)

# ============================================================ PERIMETER WALLS on plateau edge
# south curtain wall along y=-32 from x=-70..90
wall_pts = [(-56,-32), (-20,-34), (30,-32), (92,-18)]
for i in range(len(wall_pts)-1):
    x0,y0 = wall_pts[i]; x1,y1 = wall_pts[i+1]
    L = math.hypot(x1-x0, y1-y0)
    ang = math.atan2(y1-y0, x1-x0)
    cx, cy = (x0+x1)/2, (y0+y1)/2
    ob = box_obj(f"Curtain_S_{i}", (cx, cy, ZB+3.5), (L, 2.2, 7), C, stone)
    ob.rotation_euler[2] = ang
    cr = crenellations(f"Curtain_S_cren{i}", L, (0,0,0), C, stone, merlon_w=1.0, gap=0.9, h=1.3, thick=0.5)
    cr.location = (cx, cy, ZB+7)
    cr.rotation_euler[2] = ang
# north + west walls lower
wall_pts2 = [(-56,-32), (-80, 10), (-70, 44), (-10, 52), (60, 48), (92, 30)]
for i in range(len(wall_pts2)-1):
    x0,y0 = wall_pts2[i]; x1,y1 = wall_pts2[i+1]
    L = math.hypot(x1-x0, y1-y0)
    ang = math.atan2(y1-y0, x1-x0)
    cx, cy = (x0+x1)/2, (y0+y1)/2
    ob = box_obj(f"Curtain_N_{i}", (cx, cy, ZB+2.8), (L, 2.0, 5.6), C, stone)
    ob.rotation_euler[2] = ang
    cr = crenellations(f"Curtain_N_cren{i}", L, (0,0,0), C, stone, merlon_w=1.0, gap=0.9, h=1.2, thick=0.5)
    cr.location = (cx, cy, ZB+5.6)
    cr.rotation_euler[2] = ang
# wall turrets
for i,(tx,ty) in enumerate([(-56,-32),(-20,-34),(30,-32),(-80,10),(-70,44),(-10,52),(60,48),(92,30)]):
    tower(f"WallTur_{i}", tx, ty, ZB, 2.6, 10, C, stone, slate, spire_h=6, corbel=True, finial=True)

# ============================================================ SOUTH TERRACE (lower, with gallery)
box_obj("SouthTerrace", (10, -44, ZB-9), (110, 24, 18), C, stone)
cren = crenellations("STerr_cren", 110, (10, -55.5, ZB), C, stone, merlon_w=1.0, gap=0.9, h=1.2, thick=0.5)
# arched gallery openings on terrace face
specs=[]
for i in range(11):
    wx = -40 + i*10.0
    specs.append(((wx, -56.05, ZB-16), Euler((0,0,pi),'XYZ'), 2.6, 8.0, 5.5))
add_window_panes("STerr_Arches", specs, CW, [g_dark, g_l1, g_l2])

result = {"castle_core": "built", "objects": len(bpy.data.objects)}
