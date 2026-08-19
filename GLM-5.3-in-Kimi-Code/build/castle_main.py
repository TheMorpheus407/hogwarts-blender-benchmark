# Build the castle architecture (real geometry). Run inside Blender via MCP.
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

exec(compile(open("/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/build/arch2.py").read(), "arch2.py", "exec"))

random.seed(7)
scn = bpy.context.scene
P = 44.0  # plateau

def rm_old(names):
    for n in names:
        ob = bpy.data.objects.get(n) if isinstance(n, str) else n
        if ob:
            me = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            if me and me.users == 0:
                bpy.data.meshes.remove(me)

rm_old(list(bpy.data.collections['Castle'].objects))
# also remove blockout meshes
for n in ["GH_body","GH_roof","T_Main","T_Main_spire","T_Stair","T_Att1","T_Att2","T_Att3",
          "ClockTower","ClockTower_roof","T_Astronomy","T_WestKeep","GateTower_L","GateTower_R",
          "Wall_S_L","Wall_S_R","Wall_N","Wall_E","Wall_W","Terrace_S","Viaduct_deck",
          "Gate_esplanade","Boathouse","Boathouse_roof","Jetty","Switchback_0","Switchback_1",
          "Switchback_2","Switchback_3","Switchback_4","Terrace_E","Greenhouse","Quid_tower_0",
          "Quid_tower_1","Quid_tower_2"]:
    rm_old([n])

MATS = [bpy.data.materials["M_StoneWall"], bpy.data.materials["M_Slate"], bpy.data.materials["M_Copper"]]

def mkobj(name):
    ob = new_obj(name, "Castle")
    for mm in MATS: ob.data.materials.append(mm)
    return ob

def tintc(base=(1,1,1), var=0.05, hue_shift=0.0):
    v = [max(0, min(2, c + random.uniform(-var, var))) for c in base]
    v[0] = max(0, min(2, v[0] + hue_shift))
    return (v[0], v[1], v[2], 1.0)

# ============================================================
# OBJECT 1: Great Hall (center-north, angled -8 deg)
# ============================================================
ob = mkobj("GreatHall")
bm = bmesh.new()
tl = ensure_fcol(bm)
tGH = tintc((1.0, 0.98, 0.95), 0.05, 0.02)
great_hall(bm, -5, 22, math.radians(-8), P, 64, 15, 22, mat=0, roof_mat=1, tint=tGH, tlay=tl)
# four corner turrets
rot = math.radians(-8)
ca, sa = math.cos(rot), math.sin(rot)
for sx, sy in [(-31.5, 8.0), (31.5, 8.0), (-31.5, -8.0), (31.5, -8.0)]:
    x = -5 + ca*sx - sa*sy
    y = 22 + sa*sx + ca*sy
    corner_turret(bm, x, y, P-2, P+30, 3.3, sides=10, roof_h=7.5, mat=0,
                  roof_mat=2 if (sx*sy > 0) else 1, tint=tGH, tlay=tl, glow_bias=1.0)
# end windows (large east window)
v = Vector((-5 + ca*(-32.6), 22 + sa*(-32.6), P+7))
n = Vector((-ca, -sa, 0)).normalized() if False else Vector((math.sin(rot), -math.cos(rot), 0))
reg_win(v, Vector((-ca, -sa, 0)).normalized(), Vector((0,0,1)), 5.0, 9.0, 1.0, 1.0, 3, "great")
finish(ob, bm, smooth_deg=45)

# ============================================================
# OBJECT 2: Central tower cluster
# ============================================================
ob = mkobj("TowerCluster")
bm = bmesh.new()
tl = ensure_fcol(bm)
tTC = tintc((0.96, 0.97, 1.0), 0.04, -0.02)
# main spire tower: shaft to 122, cone to 142
build_tower(bm, 30, -4, P-6, 122, 8.2, sides=16, stages=4, strings=3,
            parapet="cone", roof_h=20, roof_mat=2, roof_curve=1.05,
            tint=tTC, tlay=tl, finial=True)
# windows on main tower (two rows, cardinal dirs)
for zc, wsize in [(P+18, 1.3), (P+42, 1.1), (P+66, 0.9), (P+90, 0.8)]:
    for az in [0, math.pi/2, math.pi, -math.pi/2]:
        p = Vector((30 + 8.3*math.cos(az), -4 + 8.3*math.sin(az), zc))
        n = Vector((math.cos(az), math.sin(az), 0))
        glow = random.choice([0, 0.4, 0.8, 1.0, 1.2])
        reg_win(p, n, Vector((0,0,1)), wsize, wsize*2.2, glow, random.uniform(0.8,1.0), 1, "lancet")
# attendant turrets, no two identical
build_tower(bm, 20, 9, P-4, 94, 5.2, sides=12, stages=3, strings=2,
            parapet="cone", roof_h=12, roof_mat=1, roof_curve=1.15, tint=tTC, tlay=tl)
build_tower(bm, 39, -18, P-4, 88, 5.8, sides=10, stages=3, strings=2,
            parapet="crenel", tint=tTC, tlay=tl)
build_tower(bm, 13, -17, P-4, 80, 4.4, sides=12, stages=2, strings=2,
            parapet="cone", roof_h=9, roof_mat=2, roof_curve=1.2, tint=tTC, tlay=tl)
build_tower(bm, 27, 12, P-4, 74, 4.8, sides=8, stages=2, strings=1,
            parapet="crenel", tint=tTC, tlay=tl)
# linking range block between main and hall
wall_segment(bm, 18, -14, 42, -6, P, 12, thick=2.4, mat=0, crenel=False, tint=tTC, tlay=tl)
gable_roof(bm, 30, -10, P+12, 26, 10, 6, math.radians(20), mat=1, tint=tTC, tlay=tl)
finish(ob, bm, smooth_deg=45)

# ============================================================
# OBJECT 3: Clock tower
# ============================================================
ob = mkobj("ClockTower")
bm = bmesh.new()
tl = ensure_fcol(bm)
tCT = tintc((1.02, 0.99, 0.94), 0.04, 0.03)
build_tower(bm, -42, 4, P-5, 92, 5.4, sides=12, stages=3, strings=3,
            parapet="crenel", tint=tCT, tlay=tl)
# pyramidal spire
fs = []
base = ring(bm, -42, 4, 92, 6.0, 4, math.radians(45))
apex = bm.verts.new((-42, 4, 106))
cap_faces(bm, base, center=apex, mat=1)
# lucarne windows on spire
for az in [0, math.pi/2, math.pi, -math.pi/2]:
    p = Vector((-42 + 6.1*math.cos(az), 4 + 6.1*math.sin(az), 96))
    reg_win(p, Vector((math.cos(az), math.sin(az), 0)), Vector((0,0,1)), 1.0, 2.0, 0.7, 0.95, 1, "lancet")
# clock face: white disc + hands registered separately; big window slits
for az in [0, math.pi/2, math.pi, -math.pi/2]:
    p = Vector((-42 + 5.5*math.cos(az), 4 + 5.5*math.sin(az), P+33))
    WINREG["clocks"] = WINREG.get("clocks", [])
    WINREG["clocks"].append(dict(p=[p.x,p.y,p.z], n=[math.cos(az), math.sin(az), 0], r=3.6))
finish(ob, bm, smooth_deg=45)

# ============================================================
# OBJECT 4: Curtain walls + gatehouse + wall towers
# ============================================================
ob = mkobj("CurtainWalls")
bm = bmesh.new()
tl = ensure_fcol(bm)
tCW = tintc((0.98, 0.99, 0.97), 0.05, 0.0)
# south wall with gate opening
wall_segment(bm, -26, -45, -6.5, -45, P, 12, thick=2.6, tint=tCW, tlay=tl)
wall_segment(bm, 6.5, -45, 26, -45, P, 12, thick=2.6, tint=tCW, tlay=tl)
wall_segment(bm, -6.5, -45, 6.5, -45, P+7.5, 4.5, thick=2.6, crenel=True, tint=tCW, tlay=tl)  # gate arch top
# N, E, W walls
wall_segment(bm, -52, 46, 42, 44, P, 12, thick=2.4, tint=tCW, tlay=tl)
wall_segment(bm, 52, -40, 50, 42, P, 12, thick=2.4, tint=tCW, tlay=tl)
wall_segment(bm, -54, -20, -52, 42, P, 12, thick=2.4, tint=tCW, tlay=tl)
# wall towers (varied)
build_tower(bm, -26, -45, P-3, 66, 4.0, sides=10, stages=2, strings=1,
            parapet="cone", roof_h=8, roof_mat=1, tint=tCW, tlay=tl)
build_tower(bm, 26, -45, P-3, 63, 4.0, sides=10, stages=2, strings=1,
            parapet="crenel", tint=tCW, tlay=tl)
build_tower(bm, 52, 42, P-3, 60, 3.6, sides=8, stages=2, strings=1,
            parapet="cone", roof_h=7, roof_mat=2, tint=tCW, tlay=tl)
build_tower(bm, -53, 42, P-3, 58, 3.8, sides=8, stages=2, strings=1,
            parapet="crenel", tint=tCW, tlay=tl)
# gatehouse D-towers
build_tower(bm, -6.5, -47, P-3, 70, 4.6, sides=12, stages=2, strings=2,
            parapet="crenel", tint=tCW, tlay=tl)
build_tower(bm, 6.5, -47, P-3, 68, 4.6, sides=12, stages=2, strings=2,
            parapet="crenel", tint=tCW, tlay=tl)
# west keep + astronomy tower
build_tower(bm, -34, 20, P-4, 86, 6.0, sides=12, stages=3, strings=2,
            parapet="cone", roof_h=13, roof_mat=2, roof_curve=1.1, tint=tCW, tlay=tl)
for zc in [P+14, P+32, P+50]:
    for az in [math.radians(a) for a in (-20, 90, 200)]:
        p = Vector((-34 + 6.1*math.cos(az), 20 + 6.1*math.sin(az), zc))
        reg_win(p, Vector((math.cos(az), math.sin(az), 0)), Vector((0,0,1)), 1.0, 2.2,
                random.choice([0, 0.4, 0.9]), random.uniform(0.8,1.0), 1, "lancet")
build_tower(bm, -48, -12, P-3, 78, 5.0, sides=10, stages=3, strings=2,
            parapet="crenel", tint=tCW, tlay=tl)
# windows on west keep body
for zc in [P+12, P+28]:
    for az in [math.radians(a) for a in (170, 210, 250)]:
        p = Vector((-48 + 5.1*math.cos(az), -12 + 5.1*math.sin(az), zc))
        reg_win(p, Vector((math.cos(az), math.sin(az), 0)), Vector((0,0,1)), 0.9, 2.0,
                random.choice([0, 0.5, 0.9]), 0.9, 1, "lancet")
# courtyard ranges (fill interior so aerial reads dense)
wall_segment(bm, -20, -20, 12, -20, P, 10, thick=5.0, crenel=False, tint=tCW, tlay=tl)
gable_roof(bm, -4, -22.5, P+10, 32, 11, 5.5, 0, mat=1, tint=tCW, tlay=tl)
for i in range(4):
    v = Vector((-16 + 8*i, -17.4, P+4))
    reg_win(v, Vector((0,1,0)), Vector((0,0,1)), 1.4, 3.0,
            random.choice([0, 0.6, 1.0, 1.2]), random.uniform(0.8,1.0), 1, "arch")
wall_segment(bm, 16, 6, 16, 26, P, 9, thick=4.0, crenel=False, tint=tCW, tlay=tl)
gable_roof(bm, 18.5, 16, P+9, 22, 8, 4.5, math.radians(90), mat=1, tint=tCW, tlay=tl)
finish(ob, bm, smooth_deg=45)

# ============================================================
# OBJECT 5: Courtyard slab
# ============================================================
ob = mkobj("Courtyard")
bm = bmesh.new()
tl = ensure_fcol(bm)
bmesh.ops.create_grid(bm, x_segments=4, y_segments=4, size=0.5)
bmesh.ops.scale(bm, vec=Vector((110, 100, 1)), verts=bm.verts)
bmesh.ops.translate(bm, vec=Vector((0, 0, P+0.6)), verts=bm.verts)
tint_all = ensure_fcol(bm)
for f in bm.faces:
    for l in f.loops: l[tl] = (0.9, 0.9, 0.88, 1.0)
finish(ob, bm, smooth_deg=80)

save_reg()
scn.view_layers[0].update()
bpy.ops.wm.save_as_mainfile(filepath="/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/hogwarts.blend")
result = {"objs": [(o.name, len(o.data.polygons)) for o in bpy.data.collections['Castle'].objects],
          "windows": len(WINREG["windows"]), "clocks": len(WINREG.get("clocks", []))}
