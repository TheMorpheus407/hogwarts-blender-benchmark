# Viaduct, boathouse, switchback stair, greenhouses, terraces, esplanade
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

exec(compile(open("/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/build/arch2.py").read(), "arch2.py", "exec"))
load_reg()
random.seed(11)

_lib = {}
exec(compile(bpy.data.texts['lib'].as_string(), "lib.py", "exec"), _lib)
ground_z = _lib['ground_z']
finish = _lib['finish']; ensure_fcol = _lib['ensure_fcol']; new_obj = _lib['new_obj']
ring = _lib['ring']; band_faces = _lib['band_faces']; cap_faces = _lib['cap_faces']
cone_roof = _lib['cone_roof']; build_tower = _lib['build_tower']

MATS = [bpy.data.materials["M_StoneWall"], bpy.data.materials["M_Slate"], bpy.data.materials["M_Copper"]]

def rm_old(names):
    for n in names:
        ob = bpy.data.objects.get(n)
        if ob:
            me = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            if me and me.users == 0: bpy.data.meshes.remove(me)

rm_old(["Viaduct","Boathouse","CliffStair","Greenhouses","Terraces","Esplanade","Gate"])

def mkobj(name, coll="Castle"):
    ob = new_obj(name, coll)
    for mm in MATS: ob.data.materials.append(mm)
    return ob

def tintc(base=(1,1,1), var=0.05, hs=0.0):
    v = [max(0, min(2, c + random.uniform(-var, var))) for c in base]
    v[0] = max(0, min(2, v[0] + hs))
    return (v[0], v[1], v[2], 1.0)

scn = bpy.context.scene
scn.view_layers[0].update()

# ============================================================
# VIADUCT: from y=-45 (gatehouse) to y=-251 (esplanade), x=0
# deck z 40.5..43.5, 8 arches
# ============================================================
ob = mkobj("Viaduct")
bm = bmesh.new()
tl = ensure_fcol(bm)
tV = tintc((1.0, 0.99, 0.96), 0.04, 0.01)
Y0, Y1 = -45.0, -251.0
L = Y0 - Y1
n_arch = 8
span = L / n_arch
deck_z0, deck_z1 = 40.5, 43.5
pier_w = 4.6
arch_r = (span - pier_w) / 2.0   # semicircular arch radius per bay
arch_h = 9.0
fs = []
def box(bm, x0, x1, y0, y1, z0, z1, mat=0, tint=None):
    vs = [bm.verts.new((x0,y0,z0)), bm.verts.new((x1,y0,z0)), bm.verts.new((x1,y1,z0)), bm.verts.new((x0,y1,z0)),
          bm.verts.new((x0,y0,z1)), bm.verts.new((x1,y0,z1)), bm.verts.new((x1,y1,z1)), bm.verts.new((x0,y1,z1))]
    fs2 = []
    fs2.append(bm.faces.new((vs[0],vs[3],vs[7],vs[4])))
    fs2.append(bm.faces.new((vs[1],vs[0],vs[4],vs[5])))
    fs2.append(bm.faces.new((vs[2],vs[1],vs[5],vs[6])))
    fs2.append(bm.faces.new((vs[3],vs[2],vs[6],vs[7])))
    fs2.append(bm.faces.new((vs[4],vs[7],vs[6],vs[5])))
    fs2.append(bm.faces.new((vs[0],vs[1],vs[2],vs[3])))
    for f in fs2: f.material_index = mat
    if tint: paint(bm, tl, fs2, tint)
    return fs2

W2 = 4.5  # half width
# piers + arches
for i in range(n_arch + 1):
    yc = Y1 + span*i
    gz = ground_z(0, yc)
    box(bm, -W2, W2, yc - pier_w/2, yc + pier_w/2, gz - 3.0, deck_z0 - 1.0, tint=tV)
    # pier cutwater upstream/downstream
    if 0 < i < n_arch:
        th = 0.9
        for s in (-1, 1):
            a = bm.verts.new((-1.6, yc + s*pier_w/2, gz-3)); b = bm.verts.new((1.6, yc + s*pier_w/2, gz-3))
            c = bm.verts.new((1.6, yc + s*(pier_w/2+1.8), deck_z0-1)); d = bm.verts.new((-1.6, yc + s*(pier_w/2+1.8), deck_z0-1))
            f = bm.faces.new((a,b,c,d)); f.material_index = 0; paint(bm, tl, [f], tV)
# arch barrel + spandrel: build as deck box minus arches (approximate with segmented soffit)
# spandrel walls: two side walls with arch profile
SEGS = 12
for i in range(n_arch):
    yl = Y1 + span*i + pier_w/2
    yr = Y1 + span*(i+1) - pier_w/2
    yc = (yl + yr)/2
    r = (yr - yl)/2
    for s in (-1, 1):
        xw = s*W2
        arch_vs_lo = []; arch_vs_hi = []
        for k in range(SEGS+1):
            t = k/SEGS
            ang = math.pi * t
            yy = yc - r*math.cos(ang)
            zz = (deck_z0 - 1.5) + r*math.sin(ang)
            arch_vs_lo.append(bm.verts.new((xw, yy, zz)))
            arch_vs_hi.append(bm.verts.new((xw, yy, deck_z1)))
        for k in range(SEGS):
            f = bm.faces.new((arch_vs_lo[k], arch_vs_lo[k+1], arch_vs_hi[k+1], arch_vs_hi[k]))
            f.material_index = 0; paint(bm, tl, [f], tV)
    # arch soffit (inner barrel)
    for k in range(SEGS):
        t0, t1 = k/SEGS, (k+1)/SEGS
        y0_ = yc - r*math.cos(math.pi*t0); z0_ = (deck_z0-1.5) + r*math.sin(math.pi*t0)
        y1_ = yc - r*math.cos(math.pi*t1); z1_ = (deck_z0-1.5) + r*math.sin(math.pi*t1)
        a = bm.verts.new((-W2, y0_, z0_)); b = bm.verts.new((W2, y0_, z0_))
        c = bm.verts.new((W2, y1_, z1_)); d = bm.verts.new((-W2, y1_, z1_))
        f = bm.faces.new((a,b,c,d)); f.material_index = 0; paint(bm, tl, [f], tV)
# deck slab + parapets + crenels
box(bm, -W2, W2, Y1, Y0, deck_z0 - 1.5, deck_z1, tint=tV)
for s in (-1, 1):
    box(bm, s*W2 - 0.5, s*W2 + 0.1, Y1, Y0, deck_z1, deck_z1 + 1.1, tint=tV)
    yy = Y1 + 1.0
    while yy < Y0 - 1.0:
        box(bm, s*W2 - 0.55, s*W2 + 0.15, yy, yy + 1.1, deck_z1 + 1.1, deck_z1 + 2.0, tint=tV)
        yy += 2.4
# lantern posts along parapet (register)
yy = Y1 + 8
while yy < Y0 - 4:
    for s in (-1, 1):
        reg_lantern(Vector((s*(W2-0.9), yy, deck_z1 + 1.0)), random.uniform(0.75, 1.15))
    yy += 24.0
# small gate tower at far end
build_tower(bm, -W2-2.2, Y1+2, 38.0, 55, 3.4, sides=8, stages=2, strings=1,
            parapet="cone", roof_h=6.5, roof_mat=1, tint=tV, tlay=tl)
build_tower(bm, W2+2.2, Y1+2, 38.0, 53, 3.4, sides=8, stages=2, strings=1,
            parapet="crenel", tint=tV, tlay=tl)
finish(ob, bm, smooth_deg=45)

# ============================================================
# ESPLANADE (far side landing)
# ============================================================
ob = mkobj("Esplanade")
bm = bmesh.new()
tl = ensure_fcol(bm)
tE = tintc((0.97, 0.98, 1.0), 0.04, 0.0)
gz = ground_z(0, -262)
box(bm, -17, 17, -273, -249, 42.5, 44.3, tint=tE)
for s in (-1, 1):
    box(bm, s*17 - 0.4, s*17 + 0.2, -273, -249, 44.3, 45.3, tint=tE)
finish(ob, bm, smooth_deg=45)

# ============================================================
# BOATHOUSE at waterline (SW face of crag) + jetty
# ============================================================
ob = mkobj("Boathouse")
bm = bmesh.new()
tl = ensure_fcol(bm)
tB = tintc((0.95, 0.96, 1.0), 0.05, -0.01)
rotB = math.radians(-38)
ca, sa = math.cos(rotB), math.sin(rotB)
def PB(px, py):
    return (-84 + ca*px - sa*py, -62 + sa*px + ca*py)
# base slab over water
bx0, by0 = PB(-13, -8.5); bx1, by1 = PB(13, 8.5)
box(bm, min(bx0,bx1), max(bx0,bx1), min(by0,by1), max(by0,by1), -1.5, 2.2, tint=tB)
# walls with arched openings both gable ends (boathouse style)
for s in (-1, 1):
    x0, y0 = PB(s*12.6, -8.2); x1, y1 = PB(s*12.6, 8.2)
    # wall segments above/bide arch opening: simple: full wall + big arch hole approximated by leaving center open
    yc = (y0+y1)/2
    # side pieces
    box(bm, x0-0.3, x0+0.3, y0, yc-4.0, 2.2, 8.5, tint=tB)
    box(bm, x0-0.3, x0+0.3, yc+4.0, y1, 2.2, 8.5, tint=tB)
    # arch top piece (segmented)
    SEGS2 = 8
    pts = []
    for k in range(SEGS2+1):
        t = k/SEGS2
        yy = yc - 4.0*math.cos(math.pi*t)
        zz = 4.4 + 4.0*math.sin(math.pi*t)
        pts.append((x0, yy, zz))
    for k in range(SEGS2):
        a = bm.verts.new((pts[k][0]-0.3, pts[k][1], pts[k][2]))
        b = bm.verts.new((pts[k][0]+0.3, pts[k][1], pts[k][2]))
        c = bm.verts.new((pts[k+1][0]+0.3, pts[k+1][1], pts[k+1][2]))
        d = bm.verts.new((pts[k+1][0]-0.3, pts[k+1][1], pts[k+1][2]))
        f = bm.faces.new((a,b,c,d)); f.material_index = 0; paint(bm, tl, [f], tB)
    # gable triangle
    a = bm.verts.new((x0-0.3, yc-8.2, 8.5)); b = bm.verts.new((x0+0.3, yc-8.2, 8.5))
    c = bm.verts.new((x0+0.3, yc+8.2, 8.5)); d = bm.verts.new((x0-0.3, yc+8.2, 8.5))
    e = bm.verts.new((x0+0.3, yc, 13.5)); g = bm.verts.new((x0-0.3, yc, 13.5))
    f = bm.faces.new((a,b,c,d)); f.material_index = 0; paint(bm, tl, [f], tB)
# long walls
for s in (-1, 1):
    x0, y0 = PB(-12.6, s*8.2); x1, y1 = PB(12.6, s*8.2)
    box(bm, min(x0,x1), max(x0,x1), min(y0,y1)-0.3, max(y0,y1)+0.3, 2.2, 8.5, tint=tB)
    # windows along boathouse
    for frac in (0.3, 0.5, 0.7):
        px, py = PB(-25.2*frac + 12.6 if False else -12.6 + 25.2*frac, s*8.6)
        p = Vector((px, py, 4.2))
        nrm = Vector((ca*0 - sa*s, sa*0 + ca*s, 0))
        nrm = Vector((-sa*s, ca*s, 0))
        reg_win(p, nrm, Vector((0,0,1)), 1.0, 1.8, random.choice([0.6, 0.9, 1.1]), 1.0, 1, "lancet")
# roof (slate, gable)
gx0, gy0 = PB(-13.5, 0); 
ridge1 = bm.verts.new((*PB(-13.0, 0), 13.8))
ridge2 = bm.verts.new((*PB(13.0, 0), 13.8))
e1 = bm.verts.new((*PB(-13.4, -9.2), 9.0)); e2 = bm.verts.new((*PB(13.4, -9.2), 9.0))
e3 = bm.verts.new((*PB(13.4, 9.2), 9.0)); e4 = bm.verts.new((*PB(-13.4, 9.2), 9.0))
for f in [bm.faces.new((e1,e2,ridge2,ridge1)), bm.faces.new((e3,e4,ridge1,ridge2))]:
    f.material_index = 1; f.smooth = False; paint(bm, tl, [f], tB)
# jetty planks
jx, jy = PB(-16, 6)
box(bm, jx-2, jx+2, jy-12, jy+12, 0.5, 0.9, tint=tB)
reg_lantern(Vector((jx, jy-10, 1.8)), 0.9)
finish(ob, bm, smooth_deg=45)

# ============================================================
# SWITCHBACK STAIR up cliff face
# ============================================================
ob = mkobj("CliffStair")
bm = bmesh.new()
tl = ensure_fcol(bm)
tS = tintc((0.96, 0.97, 0.99), 0.04, 0.0)
flights = [
    (( -97.5, -46.5), 2.5, 8.5,  math.radians(-38+90)),
    (( -85.5, -52.5), 8.5, 15.5, math.radians(-38-90)),
    (( -88.5, -37.0), 15.5, 22.5, math.radians(-38+90)),
    (( -76.5, -43.0), 22.5, 29.5, math.radians(-38-90)),
    (( -79.5, -27.5), 29.5, 36.5, math.radians(-38+90)),
    (( -67.5, -33.5), 36.5, 43.6, math.radians(-38-90)),
]
for (fx, fy), z0, z1, ang in flights:
    ln = 16.0
    dirv = Vector((math.cos(ang), math.sin(ang), 0))
    steps_n = 14
    for k in range(steps_n):
        t0, t1 = k/steps_n, (k+1)/steps_n
        z00 = z0 + (z1-z0)*t0; z11 = z0 + (z1-z0)*t1
        c0 = Vector((fx, fy, 0)) + dirv*(ln*(t0-0.5))
        c1 = Vector((fx, fy, 0)) + dirv*(ln*(t1-0.5))
        sidev = Vector((-dirv.y, dirv.x, 0)) * 1.4
        a = bm.verts.new(c0 - sidev + Vector((0,0,z00))); b = bm.verts.new(c0 + sidev + Vector((0,0,z00)))
        c = bm.verts.new(c1 + sidev + Vector((0,0,z11))); d = bm.verts.new(c1 - sidev + Vector((0,0,z11)))
        f = bm.faces.new((a,b,c,d)); f.material_index = 0; paint(bm, tl, [f], tS)
    # railing wall
    c0 = Vector((fx, fy, 0)) + dirv*(ln*(-0.5)); c1 = Vector((fx, fy, 0)) + dirv*(0.5)
    sidev = Vector((-dirv.y, dirv.x, 0)) * 1.55
    a = bm.verts.new(c0 + sidev + Vector((0,0,z0))); b = bm.verts.new(c1 + sidev + Vector((0,0,z1)))
    c = bm.verts.new(c1 + sidev + Vector((0,0,z1+0.9))); d = bm.verts.new(c0 + sidev + Vector((0,0,z0+0.9)))
    f = bm.faces.new((a,b,c,d)); f.material_index = 0; paint(bm, tl, [f], tS)
# lanterns on stair turns
for (fx, fy), z0, z1, ang in flights[::2]:
    reg_lantern(Vector((fx, fy, z1+1.2)), random.uniform(0.7, 1.0))
finish(ob, bm, smooth_deg=45)

# ============================================================
# GREENHOUSES on east terrace
# ============================================================
ob = mkobj("Greenhouses")
bm = bmesh.new()
tl = ensure_fcol(bm)
tG = tintc((0.98, 1.0, 0.98), 0.04, 0.0)
# terrace retaining + slab
gz = ground_z(58, -36)
box(bm, 44, 74, -47, -25, gz-2, 30.2, tint=tG)
# three glass ranges (frames now; glass panes via window system big)
for k, (gx0, gy0, gw, gh_) in enumerate([(48.5, -44, 10, 16), (48.5, -26, 10, 16), (61.5, -35, 9, 12)]):
    cx = gx0 + gw/2; cy = gy0 + gh_/2
    box(bm, gx0-0.2, gx0+gw+0.2, gy0-0.2, gy0+gh_+0.2, 30.2, 30.8, tint=tG)
    # knee wall
    box(bm, gx0, gx0+gw, gy0, gy0+gh_, 30.8, 32.6, tint=tG)
    # gable glass roof registers as windows (big glow low)
    reg_win(Vector((cx, cy, 34.0)), Vector((0,1,0)), Vector((0,0,1)), gw*0.9, 3.2, 0.28, 0.9, 0, "greenhouse")
    reg_win(Vector((cx, cy, 34.0)), Vector((0,-1,0)), Vector((0,0,1)), gw*0.9, 3.2, 0.28, 0.9, 0, "greenhouse")
finish(ob, bm, smooth_deg=45)

save_reg()
scn.view_layers[0].update()
bpy.ops.wm.save_as_mainfile(filepath="/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/hogwarts.blend")
result = {"objs": [(o.name, len(o.data.polygons)) for o in bpy.data.collections['Castle'].objects if o.name in ("Viaduct","Esplanade","Boathouse","CliffStair","Greenhouses")],
          "windows": len(WINREG["windows"]), "lanterns": len(WINREG["lanterns"])}
