import bpy, math, random
from mathutils import Vector, Euler
from math import sin, cos, pi, hypot

C  = bpy.data.collections["Castle"]
CW = bpy.data.collections["Castle_Windows"]
P  = bpy.data.collections["Props"]

stone  = mat_stone()
stoned = mat_stone_dark()
slate  = mat_slate()
metal  = mat_metal()

g_dark = bpy.data.materials["GlassDark"]
g_l1 = bpy.data.materials["GlassWarm1"]
g_l2 = bpy.data.materials["GlassWarm2"]
g_l3 = bpy.data.materials["GlassWarm3"]
g_l4 = bpy.data.materials["GlassWarm4"]

ZB = 52.0
gh_x0, gh_x1, gh_cy, gh_w, gh_wh = -82.0, -24.0, 8.0, 26.0, 17.0
gh_len = gh_x1 - gh_x0
bays = 8
bay_w = gh_len / bays

# ============================================================ GH window stone frames
for side in (-1, 1):
    wy = gh_cy + side*(gh_w/2 + 0.12)
    for b in range(bays):
        bx = gh_x0 + bay_w*(b+0.5)
        for k in (-1, 1):
            wx = bx + k*bay_w*0.18
            arch_frame(f"GHF_{side}_{b}_{k}", 2.6, 11.7, 8.0, 0.35, 0.5, C, stone,
                       loc=(wx, wy, ZB+2.4), rot=Euler((0,0,pi if side<0 else 0),'XYZ'), seg=5)
# west gable frame
arch_frame("GHF_W", 5.2, 12.2, 8.5, 0.45, 0.6, C, stone,
           loc=(gh_x0-0.12, gh_cy, ZB+2.9), rot=Euler((0,0,pi/2),'XYZ'), seg=6)

# rose window above west gable lancet: ring of glowing circles
bpy.ops.mesh.primitive_torus_add(major_radius=2.2, minor_radius=0.28, major_segments=24, minor_segments=8,
                                 location=(gh_x0-0.15, gh_cy, ZB+13.5), rotation=(0,pi/2,0))
rose_rim = bpy.context.active_object; rose_rim.name="GH_RoseRim"; move_to_col(rose_rim, C); rose_rim.data.materials.append(stone)
specs=[]
for i in range(8):
    a = i/8*2*pi
    specs.append(((gh_x0-0.2, gh_cy+1.5*cos(a), ZB+13.5+1.5*sin(a)), Euler((pi/2,0,pi/2),'XYZ'), 0.8, 0.9, 0.4))
add_window_panes("GH_Rose", specs, CW, [g_l3, g_l2])

# ============================================================ flying buttresses GH (upper flyers to clerestory)
for side in (-1, 1):
    for b in range(1, bays):
        bx = gh_x0 + bay_w*b
        y0 = gh_cy + side*(gh_w/2+1.15)
        # diagonal strut from buttress top (z ~ ZB+13) to wall (z ~ ZB+15.5)
        z0, z1 = ZB+12.0, ZB+15.0
        dy = abs(side)*1.0
        ob = box_obj(f"GHfly_{side}_{b}", (bx, y0 - side*0.5, (z0+z1)/2), (0.7, 2.6, 0.8), C, stone)
        ob.rotation_euler[0] = side*math.atan2(z1-z0, 2.4)

# ============================================================ string courses on big towers
def string_course(name, x, y, z, r, h=0.55):
    cone_obj(name, (x,y,z+h/2), r+0.35, r+0.18, h, C, stone, verts=24)

string_course("SC_GT1", -14, -4, ZB+22, 13.0)
string_course("SC_GT2", -14, -4, ZB+44, 13.0)
string_course("SC_AST", 64, 30, ZB+30, 7.0)
string_course("SC_ET1", 82, 4, ZB+24, 9.0)

# ============================================================ clock dial rim + ticks
ct_x, ct_y, ct_w, ct_h = 36.0, 14.0, 15.0, 52.0
dial_z = ZB + ct_h - 2
for (nm, loc, rot) in [("S", (ct_x, ct_y-ct_w/2-0.75, dial_z), (pi/2,0,0)),
                        ("W", (ct_x-ct_w/2-0.75, ct_y, dial_z), (0,pi/2,0))]:
    bpy.ops.mesh.primitive_torus_add(major_radius=3.5, minor_radius=0.35, major_segments=28, minor_segments=8,
                                     location=loc, rotation=rot)
    ob = bpy.context.active_object; ob.name=f"DialRim_{nm}"; move_to_col(ob, C); ob.data.materials.append(stone)
    # 12 ticks
    for i in range(12):
        a = i/12*2*pi
        if nm == "S":
            tx, ty, tz = loc[0]+2.9*cos(a), loc[1]-0.42, loc[2]+2.9*sin(a)
            tk = box_obj(f"Tick_{nm}_{i}", (tx,ty,tz), (0.28,0.16,0.7), C, metal)
            tk.rotation_euler[1] = pi/2-a
        else:
            tx, ty, tz = loc[0]-0.42, loc[1]+2.9*cos(a), loc[2]+2.9*sin(a)
            tk = box_obj(f"Tick_{nm}_{i}", (tx,ty,tz), (0.16,0.28,0.7), C, metal)
            tk.rotation_euler[0] = a

# ============================================================ west-end corbels under GH overhang
for i in range(7):
    wx = gh_x0 - 0.5
    wy = gh_cy - gh_w/2 + 2 + i*(gh_w-4)/6
    cone_obj(f"GHcorbel_{i}", (wx, wy, ZB-1.2), 0.7, 0.35, 2.6, C, stone, verts=6)

# ============================================================ extra towers for skyline variety
tower("DrumLibrary", -48, 38, ZB, 9.5, 26, C, stone, slate, spire_h=0, corbel=True, cren=True, verts_n=26)
specs=[]
for row in range(2):
    for i in range(6):
        a = i/6*2*pi + row*0.3
        specs.append(((-48+9.55*cos(a), 38+9.55*sin(a), ZB+8+row*9), Euler((0,0,a-pi/2),'XYZ'), 1.6, 3.0, 1.8))
add_window_panes("DrumLibrary_Win", specs, CW, [g_l2, g_l3, g_l1, g_dark])
tower("StairTurret_C", 24, -2, ZB, 2.8, 40, C, stone, slate, spire_h=12, corbel=True)
tower("Turret_N2", -34, 42, ZB, 3.2, 22, C, stone, slate, spire_h=10, corbel=True)
tower("Turret_SE", 72, -18, ZB, 3.6, 26, C, stone, slate, spire_h=11, corbel=True)

# ============================================================ QUIDDITCH PITCH (middle distance east)
qx, qy = 460, 190
qz = terrain_h(qx, qy)
gold = bpy.data.materials.new("Gold"); gold.use_nodes=True
gbs = gold.node_tree.nodes.get("Principled BSDF")
gbs.inputs["Base Color"].default_value = (0.45, 0.28, 0.08, 1)
gbs.inputs["Metallic"].default_value = 0.9
gbs.inputs["Roughness"].default_value = 0.3
for end in (-1, 1):
    ex = qx + end*55
    for k in (-1, 0, 1):
        ey = qy + k*14
        hgt = 12 + (0 if k==0 else -3)
        cyl_obj(f"QP_pole_{end}_{k}", (ex, ey, qz+hgt/2), 0.25, hgt, P, metal, verts=8)
        bpy.ops.mesh.primitive_torus_add(major_radius=2.2, minor_radius=0.18, major_segments=16, minor_segments=6,
                                         location=(ex, ey, qz+hgt+2.2), rotation=(pi/2,0,0))
        ob = bpy.context.active_object; ob.name=f"QP_hoop_{end}_{k}"; move_to_col(ob, P); ob.data.materials.append(gold)
# two spectator stands
for sgn in (-1, 1):
    st = box_obj(f"QP_stand_{sgn}", (qx, qy+sgn*40, qz+4), (50, 6, 8), P, mat_wood())
    gable_roof(f"QP_standroof_{sgn}", 50, 6, 3, (qx, qy+sgn*40, qz+8), P, slate, overhang=0.4, axis='X')

# ============================================================ PATHS (ribbons on terrain)
def path_ribbon(name, pts, width, mat):
    verts, faces = [], []
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        if i == 0: dx, dy = pts[1][0]-x, pts[1][1]-y
        elif i == n-1: dx, dy = x-pts[i-1][0], y-pts[i-1][1]
        else: dx, dy = pts[i+1][0]-pts[i-1][0], pts[i+1][1]-pts[i-1][1]
        L = hypot(dx, dy) or 1
        nx, ny = -dy/L, dx/L
        z = terrain_h(x, y) + 0.25
        verts.append((x+nx*width/2, y+ny*width/2, z))
        verts.append((x-nx*width/2, y-ny*width/2, z))
    for i in range(n-1):
        faces.append((i*2, i*2+1, i*2+3, i*2+2))
    ob = new_mesh_obj(name, verts, faces, P, mat)
    return ob

dirt = bpy.data.materials.new("Dirt"); dirt.use_nodes=True
dbs = dirt.node_tree.nodes.get("Principled BSDF")
dbs.inputs["Base Color"].default_value = (0.035, 0.028, 0.02, 1)
dbs.inputs["Roughness"].default_value = 1.0

pts = []
for t in range(24):
    tt = t/23
    x = 320 + (95-320)*tt + 30*sin(tt*5)
    y = 40 + (-8-40)*tt - 20*sin(tt*3)
    pts.append((x, y))
path_ribbon("Path_Gate", pts, 4.5, dirt)
pts2 = []
for t in range(20):
    tt = t/19
    x = 380 + (320)* (1-tt) + 15*sin(tt*7)
    y = 60 + (150-60)*tt
    pts2.append((x, y))
path_ribbon("Path_Hut", pts2, 3.0, dirt)

result = {"detail": "built", "objects": len(bpy.data.objects)}
