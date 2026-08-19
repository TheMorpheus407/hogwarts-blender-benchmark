# Build merged Windows / Lanterns / Clock meshes from registry
import bpy, bmesh, math, json, random
from mathutils import Vector, Matrix

exec(compile(open("/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/build/arch2.py").read(), "arch2.py", "exec"))
load_reg()

_lib = {}
exec(compile(bpy.data.texts['lib'].as_string(), "lib.py", "exec"), _lib)
finish = _lib['finish']; new_obj = _lib['new_obj']

def rm_old(names):
    for n in names:
        ob = bpy.data.objects.get(n)
        if ob:
            me = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            if me and me.users == 0: bpy.data.meshes.remove(me)

rm_old(["Windows", "Lanterns", "ClockFaces"])
MATS = [bpy.data.materials["M_StoneWall"], bpy.data.materials["M_Slate"], bpy.data.materials["M_Copper"]]

ob = new_obj("Windows", "CastleDetail")
bm = bmesh.new()
# float attrs per vertex
a_glow = bm.verts.layers.float.new("glow")
a_warm = bm.verts.layers.float.new("warm")
tl = bm.loops.layers.float_color.new("tint")
# int material layer via face material_index: 0 = glass? We'll set per-face mats:
# mat slots: 0 glass, 1 stone-surround
ob.data.materials.clear()
MGLASS = bpy.data.materials.get("M_WindowGlass")
MFRAME = bpy.data.materials["M_StoneWall"]

def window_unit(p, n, up, w, h, glow, warm, mull, kind):
    n = Vector(n).normalized(); up = Vector(up).normalized()
    right = up.cross(n).normalized()
    if right.length < 0.01: right = Vector((1,0,0))
    M = Matrix((right, n, up)).transposed()
    origin = Vector(p)
    rise = w*0.5 if kind in ("arch","great") else (w*0.55 if kind=="lancet" else 0.0)
    SEGS = 3
    pts = [(-w/2, 0.0), (-w/2, h)]
    for k in range(1, SEGS+1):
        t = k/SEGS
        pts.append((-w/2 + (w/2)*t, h + rise*math.sin((1-t)*math.pi/2)))
    pts.append((0.0, h + rise))
    for k in range(SEGS-1, -1, -1):
        t = k/SEGS
        pts.append((w/2 - (w/2)*t, h + rise*math.sin(t*math.pi/2)))
    pts.append((w/2, h))
    pts.append((w/2, 0.0))
    # glass face (offset slightly into wall)
    gv = []
    for (lx, ly) in pts:
        v = bm.verts.new(origin + M @ Vector((lx, -0.05, ly)))
        v[a_glow] = glow; v[a_warm] = warm
        gv.append(v)
    f = bm.faces.new(gv)
    f.material_index = 0; f.smooth = False
    # surround frame (border ring outward 0.14)
    if kind != "greenhouse":
        fo = []
        fi = []
        for (lx, ly) in pts:
            fi.append(bm.verts.new(origin + M @ Vector((lx, -0.02, ly))))
        # outer outline: push outward from centroid
        cx = sum(x for x,_ in pts)/len(pts); cy = sum(y for _,y in pts)/len(pts)
        for (lx, ly) in pts:
            d = math.hypot(lx-cx, ly-cy)
            s = 1.0 + 0.16/max(d, 0.15)
            fo.append(bm.verts.new(origin + M @ Vector((cx+(lx-cx)*s, 0.02, cy+(ly-cy)*s))))
        n_pt = len(pts)
        for i in range(n_pt):
            j = (i+1) % n_pt
            fr = bm.faces.new((fi[i], fi[j], fo[j], fo[i]))
            fr.material_index = 1; fr.smooth = False
    # mullion bars
    def bar(lx, ly0, ly1, bw=0.075):
        c0 = origin + M @ Vector((lx, 0.03, ly0))
        c1 = origin + M @ Vector((lx, 0.03, ly1))
        r = M @ Vector((bw/2, 0, 0))
        fv = [c0-r, c1-r, c1+r, c0+r]
        vs = [bm.verts.new(v) for v in fv]
        fb = bm.faces.new(vs); fb.material_index = 1
    if mull >= 1:
        bar(0.0, 0.0, h + rise*0.8)
    if mull >= 2:
        bar(-w/4, 0.1, h*0.55); bar(w/4, 0.1, h*0.55)
        bar(0.0, h*0.55, h*0.56, bw=w*0.95)
    if mull >= 3:
        bar(-w/6, 0.1, h*0.6); bar(w/6, 0.1, h*0.6)

for wd in WINREG["windows"]:
    window_unit(Vector(wd["p"]), Vector(wd["n"]), Vector(wd["up"]),
                wd["w"], wd["h"], wd["glow"], wd["warm"], wd["mull"], wd["kind"])

finish(ob, bm, smooth_deg=None)

# ================= Lanterns =================
ob = new_obj("Lanterns", "CastleDetail")
bm = bmesh.new()
a_glow = bm.verts.layers.float.new("glow")
for ln in WINREG["lanterns"]:
    p = Vector(ln["p"]); g = ln["glow"]
    # post
    pv = [bm.verts.new(p + Vector((dx, dy, 0))) for dx, dy in [(-0.06,-0.06),(0.06,-0.06),(0.06,0.06),(-0.06,0.06)]]
    ptop = [bm.verts.new(p + Vector((dx, dy, 1.15))) for dx, dy in [(-0.06,-0.06),(0.06,-0.06),(0.06,0.06),(-0.06,0.06)]]
    f = bm.faces.new(pv); f.material_index = 1
    f2 = bm.faces.new(ptop); f2.material_index = 1
    for i in range(4):
        f3 = bm.faces.new((pv[i], pv[(i+1)%4], ptop[(i+1)%4], ptop[i])); f3.material_index = 1
    # glowing head
    hv = []
    for dx, dy in [(-0.16,-0.16),(0.16,-0.16),(0.16,0.16),(-0.16,0.16)]:
        v = bm.verts.new(p + Vector((dx, dy, 1.32))); v[a_glow] = g
        hv.append(v)
    hb = []
    for dx, dy in [(-0.16,-0.16),(0.16,-0.16),(0.16,0.16),(-0.16,0.16)]:
        v = bm.verts.new(p + Vector((dx, dy, 1.78))); v[a_glow] = g
        hb.append(v)
    f = bm.faces.new(hv); f.material_index = 0
    f = bm.faces.new(hb); f.material_index = 0
    for i in range(4):
        f = bm.faces.new((hv[i], hv[(i+1)%4], hb[(i+1)%4], hb[i])); f.material_index = 0
    # cap
    cap = bm.verts.new(p + Vector((0,0,1.95)))
    for i in range(4):
        f = bm.faces.new((hb[i], hb[(i+1)%4], cap)); f.material_index = 1
finish(ob, bm, smooth_deg=None)

# ================= Clock faces =================
ob = new_obj("ClockFaces", "CastleDetail")
bm = bmesh.new()
for cl in WINREG.get("clocks", []):
    p = Vector(cl["p"]); n = Vector(cl["n"]).normalized(); r = cl["r"]
    up = Vector((0,0,1)); right = up.cross(n).normalized()
    M = Matrix((right, n, up)).transposed()
    # face disc
    disc = []
    for k in range(20):
        a = 2*math.pi*k/20
        disc.append(bm.verts.new(p + M @ Vector((r*math.cos(a), 0.06, r*math.sin(a)))))
    f = bm.faces.new(disc); f.material_index = 0; f.smooth = False
    # ring border
    disco = []
    for k in range(20):
        a = 2*math.pi*k/20
        disco.append(bm.verts.new(p + M @ Vector((r*1.12*math.cos(a), 0.03, r*1.12*math.sin(a)))))
    for i in range(20):
        j = (i+1) % 20
        f = bm.faces.new((disc[i], disc[j], disco[j], disco[i])); f.material_index = 1
    # hands: 10:10
    for ang_deg, ln_ in ((60, r*0.55), (-55, r*0.42)):
        a = math.radians(ang_deg)
        d = M @ Vector((math.cos(a)*ln_, 0.1, math.sin(a)*ln_))
        c0 = p + M @ Vector((0, 0.12, 0))
        c1 = p + M @ Vector((0,0.1,0)) + d
        rvec = (c1 - c0).cross(n).normalized() * 0.10
        vs = [bm.verts.new(x) for x in (c0-rvec, c1-rvec, c1+rvec, c0+rvec)]
        f = bm.faces.new(vs); f.material_index = 2
finish(ob, bm, smooth_deg=None)

bpy.context.scene.view_layers[0].update()
bpy.ops.wm.save_as_mainfile(filepath="/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/hogwarts.blend")
result = {"windows_meshed": len(WINREG["windows"]), "lanterns": len(WINREG["lanterns"]),
          "clocks": len(WINREG.get("clocks", []))}
