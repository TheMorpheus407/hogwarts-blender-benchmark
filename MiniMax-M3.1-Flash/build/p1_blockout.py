"""PASS 1 — block-out: terrain, crag, lake, mountains, castle massing."""
import bpy, math, importlib, sys, os
from mathutils import Vector, Matrix

BUILD = "/home/morpheus/Documents/Morpheus-Produktion/Benchmarks/Blender/MiniMax-M3.1-Flash/build"
if BUILD not in sys.path:
    sys.path.insert(0, BUILD)

import hg_lib, hg_np, hg_mat, hg_cfg, hg_land, hg_castle
for m in (hg_lib, hg_np, hg_mat, hg_cfg, hg_land, hg_castle):
    importlib.reload(m)
import hg_lib as L
import hg_cfg as C
import hg_land as LD
import hg_castle as K

L.purge_all()

scn = bpy.context.scene
scn.render.engine = 'CYCLES'
scn.cycles.device = 'GPU'
scn.cycles.samples = 64
scn.cycles.use_denoising = True
scn.render.resolution_x = 1600
scn.render.resolution_y = 900

c_terr = L.coll("Terrain")
c_cast = L.coll("Castle")
c_nat = L.coll("Nature")
c_light = L.coll("Lights")
c_fx = L.coll("FX")
c_cam = L.coll("Cameras")

mats = hg_mat.build_all()
ST, SL, RK, TR, WA, RD = (mats['stone'], mats['slate'], mats['rock'],
                          mats['terrain'], mats['water'], mats['ridge'])
MS = mats['massif']

print("terrain...")
terr = LD.make_terrain("Terrain_Land", c_terr, [TR])
print("crag...")
crag = LD.make_crag("Crag_Rock", c_terr, [RK])
plateau = LD.make_plateau("Terrain_Plateau", c_terr, [TR])
print("water...")
water = LD.make_water("Lake_Surface", c_terr, [WA])
print("mountains...")
# The three receding ranges sit BEHIND the backdrop massif so the skyline
# layers properly: near massif, then three fading ridge lines.
LD.make_mountains("Ridge_Near", c_terr, [RD], 3400, 4600, 620.0, 3)
LD.make_mountains("Ridge_Mid", c_terr, [RD], 4600, 6000, 780.0, 11)
LD.make_mountains("Ridge_Far", c_terr, [RD], 6000, 8000, 950.0, 23)
# The close backdrop massif: a vast hill standing behind the castle, to the
# north-west.  The distant rings alone leave the castle floating against
# empty sky; every reference backs the massing with a near hill whose crest
# passes behind the middle of the castle.  Bearings are mathematical
# (0 deg = east, 90 deg = north).  The eastern edge stops at 100 deg so the
# moon, which the hero camera places at ~93 deg, keeps clear sky.
# The crest has to land at ~13 deg above the hero camera's horizon: any
# higher and it is cropped off the top of the frame, any lower and it
# disappears behind the castle's own roofline.  At 3.2 km with a ~800 m crest
# that works out.
LD.make_massif("Massif_NW", c_terr, [MS], 100.0, 175.0, 2200.0, 4600.0,
               890.0, 61)

# ------------------------------------------------------------------ massing
def box(name, x0, x1, y0, y1, z0, z1, mat, c=c_cast):
    mb = L.MB()
    mb.add(*L.p_box_minmax(x0, y0, z0, x1, y1, z1), mat=0)
    return mb.to_object(name, c, [mat])


def cyl(name, cx, cy, r, z0, z1, mat, n=28, c=c_cast):
    mb = L.MB()
    mb.add(*L.p_cyl(r, z1 - z0, n, z0=z0), mat=0)
    return mb.to_object(name, c, [mat])


def cone(name, cx, cy, r, z0, z1, mat, n=28, c=c_cast):
    mb = L.MB()
    mb.add(*L.p_cone(r, z1 - z0, n, z0=z0), mat=0)
    return mb.to_object(name, c, [mat])


def roof(name, cx, cy, hx, hy, eave, ridge, mat=SL):
    mb = L.MB()
    K.gable_roof(mb, cx, cy, hx, hy, eave, ridge, 0)
    return mb.to_object(name, c_cast, [mat])


P = C.PLATEAU_Z
# Great Hall
box("MS_Hall", C.GH_CX - C.GH_W / 2, C.GH_CX + C.GH_W / 2,
    C.GH_CY - C.GH_L / 2, C.GH_CY + C.GH_L / 2, P, P + C.GH_WALL_H, ST)
roof("MS_HallRoof", C.GH_CX, C.GH_CY, C.GH_W / 2, C.GH_L / 2,
     P + C.GH_WALL_H, P + C.GH_RIDGE_H)
# North range
box("MS_NorthRange", -37, 12, 24, 60, P, P + 24, ST)
roof("MS_NorthRoof", -12.5, 42, 24.5, 18, P + 24, P + 40)
# Main spire
cyl("MS_MainDrum", C.T_MAIN[0], C.T_MAIN[1], 15.5, P, P + 38, ST)
cone("MS_MainSpire", C.T_MAIN[0], C.T_MAIN[1], 15.5, P + 38, P + 104, SL)
# Clock tower
box("MS_Clock", C.T_CLOCK[0] - 8.5, C.T_CLOCK[0] + 8.5,
    C.T_CLOCK[1] - 8.5, C.T_CLOCK[1] + 8.5, P, P + 34, ST)
cone("MS_ClockSpire", C.T_CLOCK[0], C.T_CLOCK[1], 9.5, P + 34, P + 68, SL)
# East range
box("MS_EastRange", 36, 72, -38, -12, P, P + 22, ST)
roof("MS_EastRoof", 54, -25, 18, 13, P + 22, P + 36)
# East towers
cyl("MS_EastA", C.T_EAST_A[0], C.T_EAST_A[1], 9.5, P, P + 30, ST)
cone("MS_EastACone", C.T_EAST_A[0], C.T_EAST_A[1], 9.5, P + 30, P + 50, SL)
box("MS_EastB", C.T_EAST_B[0] - 7, C.T_EAST_B[0] + 7,
    C.T_EAST_B[1] - 7, C.T_EAST_B[1] + 7, P, P + 26, ST)
cyl("MS_EastC", C.T_EAST_C[0], C.T_EAST_C[1], 7.0, P, P + 22, ST)
cone("MS_EastCCone", C.T_EAST_C[0], C.T_EAST_C[1], 7.0, P + 22, P + 38, SL)
box("MS_EastD", C.T_EAST_D[0] - 4.5, C.T_EAST_D[0] + 4.5,
    C.T_EAST_D[1] - 4.5, C.T_EAST_D[1] + 4.5, P, P + 17, ST)
# West range
box("MS_WestRange", -44, -16, -56, -22, P, P + 20, ST)
roof("MS_WestRoof", -30, -39, 14, 17, P + 20, P + 32)
# Gate towers
for i, (gx, gy) in enumerate((C.T_GATE_A, C.T_GATE_B)):
    cyl("MS_Gate%d" % i, gx, gy, 5.5, P, P + 24, ST)
    cone("MS_GateCone%d" % i, gx, gy, 5.5, P + 24, P + 40, SL)
# Hall corner turrets
for sx in (-1, 1):
    for sy in (-1, 1):
        tx = C.GH_CX + sx * (C.GH_W / 2 - 1.0)
        ty = C.GH_CY + sy * (C.GH_L / 2 - 1.0)
        cyl("MS_HallTurret_%d%d" % (sx, sy), tx, ty, 4.5, P, P + 38, ST)
        cone("MS_HallTurretCap_%d%d" % (sx, sy), tx, ty, 4.5, P + 38, P + 58, SL)

# Viaduct (massing)
mb = L.MB()
for i in range(C.VIA_ARCHES + 1):
    x = C.VIA_X0 + i * (C.VIA_SPAN + C.VIA_PIER)
    mb.add(*L.p_box_minmax(x - C.VIA_PIER * .5, C.VIA_Y - C.VIA_DECK_W * .5, C.GORGE_FLOOR_Z - 6.0,
                           x + C.VIA_PIER * .5, C.VIA_Y + C.VIA_DECK_W * .5,
                           P + 5.0), mat=0)
mb.add(*L.p_box_minmax(C.VIA_X0 - 4, C.VIA_Y - C.VIA_DECK_W * .5, P,
                       C.VIA_X1 + 4, C.VIA_Y + C.VIA_DECK_W * .5, P + 5.0), mat=0)
mb.to_object("MS_Viaduct", c_cast, [ST])

# Boathouse
box("MS_Boathouse", C.BOAT_X - 11, C.BOAT_X + 11, C.BOAT_Y - 8, C.BOAT_Y + 8,
    0, 14, ST)

# ------------------------------------------------------------------ light/cam
sun_data = bpy.data.lights.new("Moon", 'SUN')
sun_data.energy = 3.2
sun_data.angle = math.radians(1.2)
sun_data.color = (0.70, 0.80, 1.0)
sun = bpy.data.objects.new("Moon", sun_data)
c_light.objects.link(sun)
sun.rotation_euler = (math.radians(58), 0, math.radians(-48))

world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scn.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.030, 0.045, 0.075, 1)
bg.inputs[1].default_value = 1.0

cam = L.place_cam("Cam_Hero", c_cam, target=(0.0, 6.0, 92.0), dist=615.0,
                  azim=25.0, z=30.0, lens=62.0)
scn.camera = cam

if globals().get('RENDER_PREVIEW', True):
    scn.render.filepath = os.path.join(os.path.dirname(BUILD), "_preview_blockout.png")
    bpy.ops.render.render(write_still=True)

result = {"objects": len(bpy.data.objects),
          "faces": sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')}
print(result)
