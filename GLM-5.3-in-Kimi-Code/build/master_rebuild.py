# Master rebuild: fix lib rp bug, rebuild all architecture with correct corbels
import bpy, bmesh, math, random
from mathutils import Vector

B = "/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/build"

# 1) patch lib text inside the blend
t = bpy.data.texts['lib']
s = t.as_string()
BUG = "    if parapet == \"crenel\":\n        rp = rings[-1][0].co.xy.length"
FIX = "    if parapet == \"crenel\":\n        rp = (rings[-1][0].co.xy - Vector((cx, cy))).length"
assert BUG in s, "crenel branch not found"
s = s.replace(BUG, FIX)
BUG2 = "    elif parapet == \"cone\":\n        rp = rings[-1][0].co.xy.length"
FIX2 = "    elif parapet == \"cone\":\n        rp = (rings[-1][0].co.xy - Vector((cx, cy))).length"
assert BUG2 in s, "cone branch not found"
s = s.replace(BUG2, FIX2)
t.from_string(s)

# 2) rebuild chain (each script removes its own old objects)
import io, traceback
log = {}
for script in ["castle_main.py", "castle_outer.py", "extras_build.py",
               "rowboat.py", "windows_build.py", "mat_glow.py",
               "viaduct_fix.py", "buttresses.py"]:
    try:
        exec(compile(open(f"{B}/{script}").read(), script, "exec"), dict(globals()))
        log[script] = "ok"
    except Exception as e:
        log[script] = traceback.format_exc()[-400:]
        break

# 3) re-add gate doors (was a GUI-only fix)
_lib = {}
exec(compile(t.as_string(), "lib.py", "exec"), _lib)
finish = _lib['finish']; new_obj = _lib['new_obj']
if bpy.data.objects.get("GateDoors"):
    me = bpy.data.objects["GateDoors"].data
    bpy.data.objects.remove(bpy.data.objects["GateDoors"], do_unlink=True)
    bpy.data.meshes.remove(me)
ob = new_obj("GateDoors", "Castle")
bm = bmesh.new()
MW = bpy.data.materials.get("M_Wood")
for s_ in (-1, 1):
    ang = s_*math.radians(28)
    for k in range(4):
        z0 = 44.2 + k*2.2; z1 = 44.2 + (k+1)*2.2
        x0 = s_*1.0; x1 = s_*(1.0 + math.sin(ang)*3.0)
        y0 = -45.4; y1 = y0 - math.cos(ang)*2.6
        a = bm.verts.new((x0, y0, z0)); b = bm.verts.new((x1, y1, z0))
        c = bm.verts.new((x1, y1, z1)); d = bm.verts.new((x0, y0, z1))
        f = bm.faces.new((a,b,c,d)); f.material_index = 0
finish(ob, bm, smooth_deg=None)
ob.data.materials.append(MW)

# 4) stray-vertex audit across rebuilt objects
scn = bpy.context.scene
scn.view_layers[0].update()
audit = {}
for obn in ("GreatHall","TowerCluster","ClockTower","CurtainWalls","Viaduct","Courtyard","Boathouse","CliffStair","Greenhouses","Esplanade","Owlery","Quidditch","FlyingButtresses"):
    ob = bpy.data.objects.get(obn)
    if not ob: continue
    me = ob.data
    # expected max radius from origin region: everything castle-side within 300
    bad = sum(1 for v in me.vertices if v.co.xy.length > 330)
    zs = [round(v.co.z,1) for v in me.vertices] if me.vertices else [0]
    audit[obn] = {"verts": len(me.vertices), "far_strays": bad,
                  "zmin": min(zs), "zmax": max(zs)}

bpy.ops.wm.save_as_mainfile(filepath="/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/hogwarts.blend")
result = {"log": log, "audit": audit}
