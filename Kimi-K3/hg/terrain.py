import bpy, math
from mathutils import Vector, noise
from math import sin, cos, pi, hypot

T = bpy.data.collections["Terrain"]
rock = mat_rock()
ground = mat_ground()
water = mat_water()

def sstep(e0, e1, x):
    t = max(0.0, min(1.0, (x-e0)/(e1-e0)))
    return t*t*(3-2*t)

def lerp(a, b, t): return a + (b-a)*t

CRAG_CX, CRAG_CY, CRAG_ZT = 0.0, -5.0, 52.0

# ============================================================ CRAG
def build_crag(name, cx, cy, z_top, r_base, r_top, z_bot, col, mat,
               segs=96, rings=26, strata=4.5, steep_south=0.26, seed=0.0):
    verts, faces = [], []
    for j in range(rings+1):
        t = j/rings
        z = z_bot + t*(z_top-z_bot)
        br = lerp(r_base, r_top, t)
        band = int(z/strata)
        ledge = 4.2*noise.noise(Vector((band*0.73+seed, seed, 0)))
        for i in range(segs):
            a = i/segs*2*pi
            ca, sa = cos(a), sin(a)
            o1 = noise.noise(Vector((ca*1.3+seed, sa*1.3, seed*2.0)))*1.35
            o2 = noise.noise(Vector((ca*4.4+seed*3, sa*4.4, z*0.06)))*1.3
            lo = noise.noise(Vector((band*0.73+seed, a*0.8, seed)))
            o3 = noise.noise(Vector((ca*6.2+seed, sa*6.2, z*0.13)))
            calm = 0.30 + 0.70*t
            r = br*(1 + (0.16*o1 + 0.09*o2 + 0.05*o3)*calm) + (ledge + 2.2*lo)*calm
            r *= (1 - steep_south*(1.0-0.55*t)*max(0.0, -sa))
            verts.append((cx+r*ca, cy+r*sa, z))
    for j in range(rings):
        for i in range(segs):
            i2 = (i+1) % segs
            a = j*segs+i; b = j*segs+i2
            c = (j+1)*segs+i2; d = (j+1)*segs+i
            faces.append((a, b, c, d))
    ob = new_mesh_obj(name, verts, faces, col, mat)
    for p in ob.data.polygons: p.use_smooth = True
    # plateau cap
    top_ring = verts[rings*segs:]
    pv = [(cx, cy, z_top)] + [(x, y, z_top+0.02) for (x, y, z) in top_ring]
    pf = []
    for i in range(segs):
        pf.append((0, 1+i, 1+(i+1) % segs))
    pob = new_mesh_obj(name+"_Plateau", pv, pf, col, ground)
    return ob

build_crag("Crag", CRAG_CX, CRAG_CY, CRAG_ZT, 118, 94, -8, T, rock, rings=34)
build_crag("CragOwlery", -150, -70, 16, 34, 20, -6, T, rock, segs=48, rings=12, seed=7.0)
build_crag("CragSouth", 108, -148, 7, 15, 9, -6, T, rock, segs=48, rings=10, seed=13.0)
build_crag("CragShoulderW", -78, 4, 50, 34, 24, 18, T, rock, segs=48, rings=12, seed=21.0)
build_crag("CragMidS", -42, -72, 32, 26, 15, 2, T, rock, segs=48, rings=12, seed=31.0)
build_crag("CragMidS2", 30, -80, 22, 20, 12, 0, T, rock, segs=40, rings=10, seed=41.0)

# ============================================================ TERRAIN FUNCTION
def terrain_h(x, y):
    d = hypot(x-CRAG_CX, y-CRAG_CY)
    n1 = noise.noise(Vector((x*0.0035, y*0.0035, 0)))
    n2 = noise.noise(Vector((x*0.02, y*0.02, 0)))
    h = 6 + 8*n1 + 2.5*n2
    # east moor rises toward viaduct land
    h += sstep(80, 420, x)*16
    # north mountains
    mtn = sstep(260, 1050, y)
    rid = abs(noise.noise(Vector((x*0.0016, y*0.0016, 3.7))))
    h += mtn*(70 + 230*rid)
    # side hills
    h += sstep(520, 1150, abs(x))*(40 + 100*abs(noise.noise(Vector((x*0.002, y*0.002, 9.1)))))
    # lake basin: south and around crag
    lake = sstep(30, 190, -(y+30))
    around = sstep(210, 115, d) if y < 70 else 0.0
    sub = max(lake, around)
    h = lerp(h, -7.5, sub)
    # north connector saddle up to plateau base
    if y > 8:
        conn = sstep(170, 85, d)*sstep(8, 45, y)
        h = lerp(h, 44, conn)
    # viaduct gorge: inlet along segment A(95,-8) -> B(300,20)
    ax, ay, bx, by = 95.0, -8.0, 300.0, 20.0
    vx, vy = bx-ax, by-ay
    L2 = vx*vx+vy*vy
    t = max(0.0, min(1.0, ((x-ax)*vx+(y-ay)*vy)/L2))
    px, py = ax+vx*t, ay+vy*t
    gd = hypot(x-px, y-py)
    g = 1 - sstep(10, 30, gd)
    if t > 0.02:
        h = lerp(h, -6.0, g)
    return h

# ============================================================ MOOR GRID
X0, X1, Y0, Y1 = -1300, 1300, -800, 1400
NX, NY = 190, 160
verts, faces = [], []
for j in range(NY+1):
    y = Y0 + (Y1-Y0)*j/NY
    for i in range(NX+1):
        x = X0 + (X1-X0)*i/NX
        verts.append((x, y, terrain_h(x, y)))
for j in range(NY):
    for i in range(NX):
        a = j*(NX+1)+i; b = a+1; c = a+NX+2; d2 = a+NX+1
        faces.append((a, b, c, d2))
moor = new_mesh_obj("Moor", verts, faces, T, ground)
for p in moor.data.polygons: p.use_smooth = True

# ============================================================ FAR MOUNTAIN RIDGES (silhouette layers)
def ridge_mat(name, colr):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = colr
    b.inputs["Roughness"].default_value = 1.0
    return m
rm1 = ridge_mat("RidgeMat1", (0.012, 0.022, 0.038, 1))
rm2 = ridge_mat("RidgeMat2", (0.020, 0.036, 0.058, 1))
rm3 = ridge_mat("RidgeMat3", (0.030, 0.052, 0.080, 1))
def ridge(name, y0, depth, h_base, h_var, seed, col):
    segs = 420
    verts, faces = [], []
    xs = -2200
    for i in range(segs+1):
        x = -2200 + 4400*i/segs
        r = abs(noise.noise(Vector((x*0.0009, seed, 0))))
        r2 = abs(noise.noise(Vector((x*0.004, seed*2, 0))))
        h = h_base + h_var*(0.65*r + 0.35*r2)
        verts.append((x, y0, -20))
        verts.append((x, y0, h))
        verts.append((x, y0+depth, -20))
        verts.append((x, y0+depth, h*0.8))
    for i in range(segs):
        a = i*4
        faces.append((a, a+4, a+5, a+1))       # front slope
        faces.append((a+1, a+5, a+7, a+3))     # top
        faces.append((a+3, a+7, a+6, a+2))     # back slope
    ob = new_mesh_obj(name, verts, faces, col, rock)
    for p in ob.data.polygons: p.use_smooth = True
    return ob




ridge("RidgeWest", 0, 0, 0, 0, 0, T) if False else None
# west ridge strip (rotated): build along Y at x=-1500
def ridge_y(name, x0, depth, h_base, h_var, seed, col):
    segs = 300
    verts, faces = [], []
    for i in range(segs+1):
        y = -600 + 2600*i/segs
        r = abs(noise.noise(Vector((y*0.001, seed, 0))))
        r2 = abs(noise.noise(Vector((y*0.005, seed*2, 0))))
        h = h_base + h_var*(0.65*r + 0.35*r2)
        verts.append((x0, y, -20)); verts.append((x0, y, h))
        verts.append((x0-depth, y, -20)); verts.append((x0-depth, y, h*0.8))
    for i in range(segs):
        a = i*4
        faces.append((a+2, a+3, a+7, a+6))
        faces.append((a+3, a+1, a+5, a+7))
        faces.append((a+1, a+0, a+4, a+5))
    ob = new_mesh_obj(name, verts, faces, col, rock)
    for p in ob.data.polygons: p.use_smooth = True
    return ob


def ridge_m(name, y0, depth, h_base, h_var, seed, col, mat):
    ob = ridge(name, y0, depth, h_base, h_var, seed, col)
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return ob

def ridge_ym(name, x0, depth, h_base, h_var, seed, col, mat):
    ob = ridge_y(name, x0, depth, h_base, h_var, seed, col)
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return ob

ridge_m("RidgeNear", 1250, 260, 70, 170, 5.0, T, rm1)
ridge_m("RidgeMid", 1700, 320, 140, 260, 11.0, T, rm2)
ridge_m("RidgeFar", 2300, 420, 220, 360, 23.0, T, rm3)
ridge_ym("RidgeWestM", -1900, 320, 40, 120, 17.0, T, rm2)

# ============================================================ LAKE
bpy.ops.mesh.primitive_plane_add(size=5000, location=(0, 100, 0))
lake = bpy.context.active_object
lake.name = "Lake"
move_to_col(lake, T)
lake.data.materials.append(water)

result = {"terrain": "built", "objects": len(bpy.data.objects)}
