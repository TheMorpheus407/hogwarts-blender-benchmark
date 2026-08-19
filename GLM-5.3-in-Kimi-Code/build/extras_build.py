# Extra windows (infill), standing stones, owlery, hut, quidditch; shore & path attrs
import bpy, bmesh, math, random, json
from mathutils import Vector, Matrix

exec(compile(open("/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/build/arch2.py").read(), "arch2.py", "exec"))
load_reg()
random.seed(23)

_lib = {}
exec(compile(bpy.data.texts['lib'].as_string(), "lib.py", "exec"), _lib)
finish = _lib['finish']; new_obj = _lib['new_obj']; terrain_h = _lib['terrain_h']

MATS = [bpy.data.materials["M_StoneWall"], bpy.data.materials["M_Slate"], bpy.data.materials["M_Copper"]]

# ---------------- window infill ----------------
def W(p, az, z, w=0.9, h=2.0, g=None):
    p = Vector(p)
    n = Vector((math.cos(az), math.sin(az), 0))
    reg_win(p, n, Vector((0,0,1)), w, h,
            g if g is not None else random.choice([0, 0, 0.3, 0.5, 0.8, 1.0, 1.2]),
            random.uniform(0.75, 1.0), random.choice([1, 1, 2]), "lancet")

P = 44.0
# gatehouse towers
for bx, bz0, bz1 in [(-6.5, 47, 62), (6.5, 47, 62)]:
    for z in [48, 53, 58]:
        for az in [math.radians(a) for a in (-90, -30, 30, 90, 150, 210)]:
            if az == math.radians(-90) and z == 53: continue
            W((bx + 4.7*math.cos(az), -47 + 4.7*math.sin(az), z), az, 0.8, 1.8)
# south wall towers
for bx, by, hh in [(-26, -45, 62), (26, -45, 59), (52, 42, 56), (-53, 42, 54)]:
    for z in [P+6, P+12]:
        for az in [math.radians(a) for a in range(0, 360, 60)]:
            W((bx + 3.7*math.cos(az), by + 3.7*math.sin(az), z), az, 0.7, 1.5)
# west keep + astronomy more rows
for z in [P+8, P+20, P+40]:
    for az in [math.radians(a) for a in (30, 60, 120, 150, 300, 330)]:
        W((-34 + 6.1*math.cos(az), 20 + 6.1*math.sin(az), z), az, 0.9, 1.9)
# clock tower shaft
for z in [P+8, P+16, P+24]:
    for az in [math.radians(a) for a in (0, 90, 180, 270)]:
        W((-42 + 5.5*math.cos(az), 4 + 5.5*math.sin(az), z), az, 0.8, 1.7)
# attendant turret rows
for cx, cy, rr, zlist in [(20, 9, 5.3, [P+8, P+18, P+28]), (39, -18, 5.9, [P+8, P+16]),
                          (13, -17, 4.5, [P+8]), (27, 12, 4.9, [P+6])]:
    for z in zlist:
        for az in [math.radians(a) for a in (30, 150, 270)]:
            W((cx + rr*math.cos(az), cy + rr*math.sin(az), z), az, 0.6, 1.3)
# courtyard range extra row (north face of south range)
for i in range(6):
    W((-14 + 5.5*i, -24.9, P+5), math.radians(-90), 1.1, 2.2)
# great hall interior-side (east end & north face seen from aerial)
for i in range(4):
    W((-24 + 12*i, 30.2, P+6), math.radians(82), 1.6, 3.8)
# viaduct gate towers
for sx in (-1, 1):
    for z in [40, 46]:
        for az in [math.radians(a) for a in (0, 90, 180, 270)]:
            W((sx*6.7 + 3.5*math.cos(az), -259 + 3.5*math.sin(az), z), az, 0.6, 1.4)

# ---------------- standing stones (SW shore, hero foreground) ----------------
ob = new_obj("StandingStones", "Extras")
bm = bmesh.new()
tl = bm.loops.layers.float_color.new("tint")
# pick a shore point visible from hero cam: between cam and castle, on land
cands = []
for ang in range(200, 260, 4):
    a = math.radians(ang)
    for r in (300, 330, 360):
        x, y = r*math.cos(a), r*math.sin(a)
        h = terrain_h(x, y)
        if 1.5 < h < 6:
            cands.append((x, y, h))
stones_center = None
if cands:
    # choose the one most westerly (left in frame)
    cands.sort(key=lambda c: c[0])
    x, y, h = cands[0]
    stones_center = (x, y, h)
    random.seed(41)
    n = 9
    for i in range(n):
        a = 2*math.pi*i/n + random.uniform(-0.2, 0.2)
        rr = 5.5 + random.uniform(-0.8, 0.8)
        sx, sy = x + rr*math.cos(a), y + rr*math.sin(a)
        sz = terrain_h(sx, sy) - 0.3
        hh = random.uniform(1.6, 3.4)
        wd = random.uniform(0.7, 1.2)
        tilt = random.uniform(-0.12, 0.12)
        vs = []
        for dx, dy in [(-wd/2, -wd/4), (wd/2, -wd/4), (wd/2, wd/4), (-wd/2, wd/4)]:
            px = sx + dx*math.cos(tilt) - dy*math.sin(tilt)
            py = sy + dx*math.sin(tilt) + dy*math.cos(tilt)
            vs.append(bm.verts.new((px, py, sz)))
        vs2 = []
        for dx, dy in [(-wd/2, -wd/4), (wd/2, -wd/4), (wd/2, wd/4), (-wd/2, wd/4)]:
            px = sx + dx*math.cos(tilt) - dy*math.sin(tilt) + hh*0.1
            py = sy + dx*math.sin(tilt) + dy*math.cos(tilt) - hh*0.05
            vs2.append(bm.verts.new((px, py, sz + hh)))
        for f in [bm.faces.new((vs[0], vs[1], vs2[1], vs2[0])),
                  bm.faces.new((vs[1], vs[2], vs2[2], vs2[1])),
                  bm.faces.new((vs[2], vs[3], vs2[3], vs2[2])),
                  bm.faces.new((vs[3], vs[0], vs2[0], vs2[3])),
                  bm.faces.new(vs2)]:
            f.material_index = 0
            g = random.uniform(0.85, 1.1)
            for l in f.loops: l[tl] = (g, g, g, 1.0)
finish(ob, bm, smooth_deg=55)
ob.data.materials.append(bpy.data.materials["M_RockCliff"])

# ---------------- owlery on outcrop W ----------------
ob = new_obj("Owlery", "Extras")
bm = bmesh.new()
tl = bm.loops.layers.float_color.new("tint")
ox, oy = -287.4, 616.3
oz = terrain_h(ox, oy)
# knoll base
ring_l = _lib['ring']
lo = ring_l(bm, ox, oy, oz-4, 9, 10)
hi = ring_l(bm, ox, oy, oz+1.2, 7.2, 10)
_lib['band_faces'](bm, lo, hi, mat=0)
cap, _ = _lib['cap_faces'](bm, hi)
for f in bm.faces: f.material_index = 0
# ruined drum tower
lo2 = ring_l(bm, ox, oy, oz+1.2, 4.2, 10)
hi2 = ring_l(bm, ox, oy, oz+9.5, 4.2, 10)
fs2 = _lib['band_faces'](bm, lo2, hi2, mat=0)
cap2, _ = _lib['cap_faces'](bm, hi2)
# jagged top: vary via crenels
_lib['crenel_ring'](bm, ox, oy, oz+9.5, 4.3, 4.6, 10, mat=0, merlon_h=0.8, duty=0.6)
# few dark window slits
for az in [0, 1.3, 2.6, 4.0]:
    W((ox + 4.3*math.cos(az), oy + 4.3*math.sin(az), oz+4), az, 0.5, 1.1, g=random.choice([0, 0.5]))
finish(ob, bm, smooth_deg=45)
ob.data.materials.append(bpy.data.materials["M_StoneWall"])

# ---------------- gamekeeper's hut SE forest edge ----------------
ob = new_obj("KeepersHut", "Extras")
bm = bmesh.new()
tl = bm.loops.layers.float_color.new("tint")
hx, hy = 589.8, -413.0
hz = terrain_h(hx, hy)
# stone base + walls (simple cottage 6x5)
def hbox(x0,x1,y0,y1,z0,z1):
    vs = [bm.verts.new((x,y,z)) for x in (x0,x1) for y in (y0,y1) for z in (z0,z1)]
    fs = []
    fs.append(bm.faces.new((vs[0],vs[1],vs[3],vs[2])))  # bottom-ish
    fs.append(bm.faces.new((vs[4+0],vs[4+1],vs[4+3],vs[4+2])))
    return fs
vs = [bm.verts.new((hx-3, hy-2.5, hz)), bm.verts.new((hx+3, hy-2.5, hz)),
      bm.verts.new((hx+3, hy+2.5, hz)), bm.verts.new((hx-3, hy+2.5, hz))]
vs2 = [bm.verts.new((hx-3, hy-2.5, hz+2.6)), bm.verts.new((hx+3, hy-2.5, hz+2.6)),
       bm.verts.new((hx+3, hy+2.5, hz+2.6)), bm.verts.new((hx-3, hy+2.5, hz+2.6))]
for i in range(4):
    f = bm.faces.new((vs[i], vs[(i+1)%4], vs2[(i+1)%4], vs2[i])); f.material_index = 0
f = bm.faces.new(vs2); f.material_index = 0
# roof
r1 = bm.verts.new((hx-3.5, hy, hz+4.4)); r2 = bm.verts.new((hx+3.5, hy, hz+4.4))
e1 = bm.verts.new((hx-3.5, hy-3, hz+2.7)); e2 = bm.verts.new((hx+3.5, hy-3, hz+2.7))
e3 = bm.verts.new((hx+3.5, hy+3, hz+2.7)); e4 = bm.verts.new((hx-3.5, hy+3, hz+2.7))
for f in [bm.faces.new((e1,e2,r2,r1)), bm.faces.new((e3,e4,r1,r2))]:
    f.material_index = 1
# chimney
for f in [bm.faces.new((bm.verts.new((hx+1.8,hy+1.4,hz+3.2)), bm.verts.new((hx+2.4,hy+1.4,hz+3.2)),
                      bm.verts.new((hx+2.4,hy+2.0,hz+3.2)), bm.verts.new((hx+1.8,hy+2.0,hz+3.2))))]: pass
ch = [bm.verts.new((hx+1.8, hy+1.4, hz+3.0)), bm.verts.new((hx+2.4, hy+1.4, hz+3.0)),
      bm.verts.new((hx+2.4, hy+2.0, hz+3.0)), bm.verts.new((hx+1.8, hy+2.0, hz+3.0))]
ch2 = [bm.verts.new((hx+1.8, hy+1.4, hz+5.2)), bm.verts.new((hx+2.4, hy+1.4, hz+5.2)),
       bm.verts.new((hx+2.4, hy+2.0, hz+5.2)), bm.verts.new((hx+1.8, hy+2.0, hz+5.2))]
for i in range(4):
    f = bm.faces.new((ch[i], ch[(i+1)%4], ch2[(i+1)%4], ch2[i])); f.material_index = 0
f = bm.faces.new(ch2); f.material_index = 0
# warm windows
W((hx, hy-2.55, hz+1.2), math.radians(-90), 0.9, 0.9, g=1.2)
W((hx-3.05, hy, hz+1.2), math.radians(180), 0.8, 0.8, g=0.9)
reg_lantern(Vector((hx+2.5, hy-2.8, hz+1.6)), 0.9)
finish(ob, bm, smooth_deg=45)
ob.data.materials.append(bpy.data.materials["M_StoneWall"])
ob.data.materials.append(bpy.data.materials["M_Slate"])

# chimney smoke: tiny volume
def smoke(name, p):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    outn = nt.nodes.get("Material Output")
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.location = (100, 0)
    vol.inputs['Density'].default_value = 0.35
    vol.inputs['Color'].default_value = (0.35, 0.36, 0.38, 1.0)
    vol.inputs['Anisotropy'].default_value = 0.0
    nt.links.new(vol.outputs[0], outn.inputs[1])
    me = bpy.data.meshes.new(name)
    ob2 = bpy.data.objects.new(name, me)
    bpy.data.collections['FX'].objects.link(ob2)
    bmm = bmesh.new()
    bmesh.ops.create_cube(bmm, size=1.0)
    bmm.to_mesh(me); bmm.free()
    ob2.location = p
    ob2.scale = (2.0, 2.0, 5.0)
    ob2.data.materials.append(m)
smoke("ChimneySmoke", (hx+2.1, hy+1.7, hz+7.5))

# ---------------- Quidditch pitch (east moor) ----------------
ob = new_obj("Quidditch", "Extras")
bm = bmesh.new()
tl = bm.loops.layers.float_color.new("tint")
qx, qy = 520, -110
qz = terrain_h(qx, qy)
# grass oval boundary: ring of low stands
for i in range(3):
    az = 2*math.pi*i/3
    tx, ty = qx + 92*math.cos(az), qy + 62*math.sin(az)
    tz = terrain_h(tx, ty)
    # scaffold tower
    for lvl in range(3):
        zz = tz + lvl*3.2
        lo = [bm.verts.new((tx + 3.2*math.cos(a), ty + 2.4*math.sin(a), zz)) for a in
              [k*math.pi/2 for k in range(4)]]
        hi = [bm.verts.new((tx + 3.2*math.cos(a), ty + 2.4*math.sin(a), zz+2.6)) for a in
              [k*math.pi/2 for k in range(4)]]
        for k in range(4):
            f = bm.faces.new((lo[k], lo[(k+1)%4], hi[(k+1)%4], hi[k])); f.material_index = 0
    # roof ring
    lo = [bm.verts.new((tx + 3.6*math.cos(a), ty + 2.7*math.sin(a), tz+9.6)) for a in
          [k*math.pi/2 for k in range(4)]]
    ctr = bm.verts.new((tx, ty, tz+11.4))
    for k in range(4):
        f = bm.faces.new((lo[k], lo[(k+1)%4], ctr)); f.material_index = 1
    reg_lantern(Vector((tx, ty, tz+10.2)), 0.5)
# golden hoops: 3 per end
for ex in (-1, 1):
    for k in (-1, 0, 1):
        px, py = qx + ex*70, qy + k*22
        pz = terrain_h(px, py)
        # poles
        for seg in range(6):
            z0 = pz + seg*2.6; z1 = pz + (seg+1)*2.6
            ringv = _lib['ring'](bm, px, py, z0, 0.16, 6)
            ringv2 = _lib['ring'](bm, px, py, z1, 0.16, 6)
            _lib['band_faces'](bm, ringv, ringv2, mat=2)
        ztop = pz + 15.6
        hr = 3.2
        for seg in range(12):
            a0 = 2*math.pi*seg/12
            v0 = bm.verts.new((px + hr*math.cos(a0), py + hr*math.sin(a0), ztop))
            v1 = bm.verts.new((px + hr*math.cos(a0), py + hr*math.sin(a0), ztop+0.14))
            # torus band simplified: ring quads
        ringA = [bm.verts.new((px + hr*math.cos(2*math.pi*s/12), py + hr*math.sin(2*math.pi*s/12), ztop)) for s in range(12)]
        ringB = [bm.verts.new((px + hr*math.cos(2*math.pi*s/12), py + hr*math.sin(2*math.pi*s/12), ztop+0.16)) for s in range(12)]
        _lib['band_faces'](bm, ringA, ringB, mat=2)
for v in ob.data.vertices:
    if v.co.z < 0.5:
        v.co.z = 0.5
finish(ob, bm, smooth_deg=45)
ob.data.materials.append(bpy.data.materials["M_StoneWall"])
ob.data.materials.append(bpy.data.materials["M_Slate"])
ob.data.materials.append(bpy.data.materials["M_Copper"])

save_reg()
bpy.context.scene.view_layers[0].update()
bpy.ops.wm.save_as_mainfile(filepath="/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/hogwarts.blend")
result = {"windows_total": len(WINREG["windows"]), "lanterns_total": len(WINREG["lanterns"]),
          "stones_center": stones_center, "hut_z": round(hz,1), "quidditch_z": round(qz,1), "owlery_z": round(oz,1)}
