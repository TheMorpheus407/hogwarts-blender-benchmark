"""Nature: conifer templates + forest scatter, owlery, gamekeeper's hut,
standing stones, Quidditch pitch."""
import bpy
import bmesh
import math
import random
import hog
import hogkit as hk
from mathutils import Vector, Matrix

hog.clear_coll('Nature')
hk.init()
M = hk.M

CONIFER = hog.flat_mat('Conifer', (0.030, 0.075, 0.038), 0.9)
BARK = hog.flat_mat('Bark', (0.09, 0.06, 0.04), 0.95)


# ------------------------------------------------------------ tree templates
def spruce(name, height, layers, rseed):
    rng = random.Random(rseed)
    bm = bmesh.new()
    trunk_h = height * 0.16
    vs = bmesh.ops.create_cone(bm, cap_ends=True, segments=7,
                               radius1=height * 0.02, radius2=height * 0.012,
                               depth=trunk_h)['verts']
    bmesh.ops.translate(bm, vec=(0, 0, trunk_h / 2), verts=vs)
    trunk_faces = list(bm.faces)
    z0 = trunk_h * 0.8
    rem = height - z0
    r = height * 0.16
    for i in range(layers):
        f0 = i / layers
        lz = z0 + rem * f0
        lh = rem / layers * 2.1
        lr = r * (1 - f0 * 0.82)
        seg = 9 if i < layers - 2 else 7
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg,
                                    radius1=lr, radius2=lr * 0.05,
                                    depth=lh)
        vv = res['verts']
        # radial jitter for irregular silhouette
        for v in vv:
            rr = math.hypot(v.co.x, v.co.y)
            if rr > 0.01:
                k = 1.0 + rng.uniform(-0.16, 0.16)
                v.co.x *= k
                v.co.y *= k
        bmesh.ops.translate(bm, vec=(rng.uniform(-0.3, 0.3),
                                     rng.uniform(-0.3, 0.3), lz + lh / 2),
                            verts=vv)
    me = bpy.data.meshes.new(name)
    for f in bm.faces:
        f.material_index = 0 if f in trunk_faces else 1
        f.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(BARK)
    me.materials.append(CONIFER)
    ob = bpy.data.objects.new(name, me)
    hog.coll('Nature').objects.link(ob)
    return ob


trees = [spruce('Tree_A', 15.0, 6, 1), spruce('Tree_B', 11.0, 5, 2),
         spruce('Tree_C', 19.0, 7, 3)]
# park templates far below the lake so originals never show
for t in trees:
    t.location = (0, 0, -500)

# ------------------------------------------------------------ forest scatter
# deterministic: sample terrain vertices by forest_w, jitter, instance via
# geometry nodes (instances stay upright, random yaw + scale)
import numpy as np

ter = bpy.data.objects['Terrain_Main']
me = ter.data
nv = len(me.vertices)
cos = np.empty(nv * 3)
me.vertices.foreach_get('co', cos)
cos = cos.reshape(-1, 3)
fw = np.empty(nv)
me.attributes['forest_w'].data.foreach_get('value', fw)
# damp trees on the upper crag, keep some at the base
cw = np.empty(nv)
me.attributes['cliff_w'].data.foreach_get('value', cw)
fw = fw * (1.0 - 0.85 * cw)

rng_np = np.random.default_rng(42)
u = rng_np.random(nv)
DENS = 1.35
pick = u < np.clip(fw * DENS, 0, 0.97)
pts = cos[pick]
# jitter in xy, slight sink so trunks meet ground on slopes
pts = pts + np.column_stack([rng_np.uniform(-2.0, 2.0, len(pts)),
                             rng_np.uniform(-2.0, 2.0, len(pts)),
                             rng_np.uniform(-0.9, -0.3, len(pts))])
# split among the 3 variants
which = rng_np.integers(0, 3, len(pts))


def instancer(name, points, tree, seed):
    pm = bpy.data.meshes.new(name)
    pm.vertices.add(len(points))
    pm.vertices.foreach_set('co', points.ravel())
    ob = bpy.data.objects.new(name, pm)
    hog.coll('Nature').objects.link(ob)
    ng = bpy.data.node_groups.new(name + '_NG', 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT',
                            socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT',
                            socket_type='NodeSocketGeometry')
    n_in = ng.nodes.new('NodeGroupInput')
    n_out = ng.nodes.new('NodeGroupOutput')
    n_iop = ng.nodes.new('GeometryNodeInstanceOnPoints')
    n_obj = ng.nodes.new('GeometryNodeObjectInfo')
    n_obj.inputs['Object'].default_value = tree
    n_obj.transform_space = 'ORIGINAL'
    n_obj.inputs['As Instance'].default_value = True
    n_rot = ng.nodes.new('FunctionNodeRandomValue')
    n_rot.data_type = 'FLOAT_VECTOR'
    n_rot.inputs['Min'].default_value = (0, 0, 0)
    n_rot.inputs['Max'].default_value = (0.06, 0.06, 6.2831)
    n_rot.inputs['Seed'].default_value = seed
    n_scl = ng.nodes.new('FunctionNodeRandomValue')
    n_scl.data_type = 'FLOAT'
    n_scl.inputs[2].default_value = 0.55   # min
    n_scl.inputs[3].default_value = 1.55   # max
    n_scl.inputs['Seed'].default_value = seed + 1
    ng.links.new(n_in.outputs['Geometry'], n_iop.inputs['Points'])
    ng.links.new(n_obj.outputs['Geometry'], n_iop.inputs['Instance'])
    ng.links.new(n_rot.outputs['Value'], n_iop.inputs['Rotation'])
    ng.links.new(n_scl.outputs[1], n_iop.inputs['Scale'])
    ng.links.new(n_iop.outputs['Instances'], n_out.inputs['Geometry'])
    md = ob.modifiers.new('Trees', 'NODES')
    md.node_group = ng
    return ob


for ti, tree in enumerate(trees):
    sel = pts[which == ti]
    instancer(f'ForestPts_{ti}', sel, tree, 1000 + ti)

# ---------------------------------------------------------------- owlery
win_slit = hk.window_template('slit', 0.55, 1.6, frame_t=0.10, sill=False)
oz = hog.ground_z(215, 25) or 50
hk.round_tower('Owlery', 'Nature', 215, 25, oz - 2, r=4.2, body_h=24,
               roof_h=10, segs=16, taper=0.9, bands=1, machicolate=False,
               win_me=win_slit, win_rows=3, win_cols=5, win_z0=12,
               win_row_step=5, seed=90)

# ------------------------------------------------------- gamekeeper's hut
HX, HY = -195.0, -55.0
hz = hog.ground_z(HX, HY)
if hz is None or hz < 1.0:
    hz = 1.0
hog.cyl('Hut_Body', 'Nature', r=4.6, h=3.4, loc=(HX, HY, hz - 0.4), segs=14,
        mat=M['wall'])
hk.witch_hat('Hut_Roof', 'Nature', 4.9, 4.4, (HX, HY, hz + 3.0), segs=14,
             mat=hog.flat_mat('Thatch', (0.25, 0.17, 0.09), 0.95), flare=1.1)
hog.cyl('Hut_Chimney', 'Nature', r=0.55, h=3.6, loc=(HX + 3.4, HY + 1.2, hz + 2.4),
        segs=8, mat=M['trim'])
win_s = hk.window_template('lancet_s', 0.9, 2.4)
hk.place_window(win_s, 'Windows', (HX - 4.4, HY - 1.2, hz + 0.8),
                -math.pi / 2)
hk.place_window(win_s, 'Windows', (HX + 1.5, HY - 4.35, hz + 0.8), 0.15)
hk.place_lantern('Nature', (HX - 2.5, HY - 4.5, hz))
# wood pile + fence posts
for i in range(6):
    a = i * 1.05
    hog.box(f'Hut_Fence_{i}', 'Nature', size=(0.25, 0.25, 1.4),
            loc=(HX + 7 * math.cos(a), HY + 7 * math.sin(a), hz - 0.2),
            mat=M['wood'])

# ------------------------------------------------------- standing stones
SSX, SSY = -318.0, 96.0
sz = hog.ground_z(SSX, SSY) or 12
rng = random.Random(7)
for i in range(9):
    a = math.pi * 2 * i / 9
    r = 11 + rng.uniform(-1, 1)
    stx, sty = SSX + r * math.cos(a), SSY + r * math.sin(a)
    stz = hog.ground_z(stx, sty) or sz
    ob = hog.box(f'Stone_{i}', 'Nature',
                 size=(rng.uniform(1.2, 1.9), rng.uniform(0.7, 1.1),
                       rng.uniform(3.0, 4.6)),
                 loc=(stx, sty, stz - 0.5), rot=rng.uniform(0, 3),
                 mat=M['rock'])
    ob.rotation_euler[0] = rng.uniform(-0.08, 0.08)
    ob.rotation_euler[1] = rng.uniform(-0.08, 0.08)

# ------------------------------------------------------- quidditch pitch
QX, QY = -300.0, 260.0
qz = hog.ground_z(QX, QY) or 15
GOLD = hog.flat_mat('GoldHoop', (0.75, 0.55, 0.12), 0.35)
BANNER = hog.flat_mat('Banner', (0.35, 0.08, 0.08), 0.8)
# arena: low elliptical wall ring
bm = bmesh.new()
segs = 40
for i in range(segs):
    a0 = math.pi * 2 * i / segs
    vs = bmesh.ops.create_cube(bm, size=1.0)['verts']
    bmesh.ops.scale(bm, vec=(8.0, 1.2, 3.2), verts=vs)
    bmesh.ops.translate(bm, vec=(0, 42.0, 1.6), verts=vs)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(a0, 3, 'Z'),
                     verts=vs)
ob = hog.obj_from_bm(bm, 'QP_Ring', 'Nature', M['wood'])
ob.location = (QX, QY, qz - 0.8)
ob.scale = (1.15, 0.72, 1.0)
# goal hoops: 3 each end, varied heights
for sgn in (-1, 1):
    for k, hh in enumerate((14.0, 9.5, 12.0)):
        px = QX + sgn * 40.0
        py = QY + (k - 1) * 7.5
        pz = hog.ground_z(px, py) or qz
        hog.cyl(f'QP_Pole_{sgn}_{k}', 'Nature', r=0.28, h=hh,
                loc=(px, py, pz - 0.3), segs=8, mat=GOLD)
        ring = hk.spun_profile(f'QP_Hoop_{sgn}_{k}', 'Nature',
                               [(2.2, 0), (2.2, 0.28), (1.9, 0.28), (1.9, 0)],
                               segs=18, loc=(px, py, pz + hh + 2.2),
                               mat=GOLD, close=True)
        ring.rotation_euler = (0, math.pi / 2, 0)
        ring.location.z = pz + hh + 2.2
# spectator towers: striped tents on stilts
for i in range(6):
    a = math.pi * 2 * i / 6 + 0.4
    tx = QX + 52 * math.cos(a) * 1.15
    ty = QY + 52 * math.sin(a) * 0.72
    tz = hog.ground_z(tx, ty) or qz
    hog.box(f'QP_TowerBase_{i}', 'Nature', size=(5, 5, 12), loc=(tx, ty, tz - 0.5),
            mat=M['wood'])
    hog.box(f'QP_TowerBox_{i}', 'Nature', size=(7, 7, 4), loc=(tx, ty, tz + 11.5),
            mat=BANNER)
    hk.witch_hat(f'QP_TowerRoof_{i}', 'Nature', 4.2, 5.0, (tx, ty, tz + 15.5),
                 segs=8, mat=BANNER, flare=1.05)


# ------------------------------------------------- foreground rock islets
# small dark skerries in the near lake for hero-frame depth
import bmesh as _bm
for i, (ix, iy, ir, ih) in enumerate([(-250, -415, 9, 2.2), (-175, -448, 6, 1.5),
                                      (-315, -372, 12, 3.0)]):
    bm = _bm.new()
    _bm.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    rngi = random.Random(500 + i)
    for v in bm.verts:
        n = 1.0 + 0.38 * (noise_like := (rngi.random() - 0.5))
        v.co.x *= ir * (1 + 0.3 * (rngi.random() - 0.5))
        v.co.y *= ir * (1 + 0.3 * (rngi.random() - 0.5))
        v.co.z *= ih
    for f in bm.faces:
        f.smooth = True
    ob = hog.obj_from_bm(bm, f'Skerry_{i}', 'Nature', M['rock'])
    ob.location = (ix, iy, -0.4)


# ------------------------------------------------- courtyard garden clumps
# small trees inside the walls so the lawns aren't bald from the aerial
garden_spots = [(-20, 40, 4, 60), (28, 44, 3, 61), (-4, -6, 3, 62),
                (56, 22, 3, 63), (-44, -8, 2, 64), (14, 66, 3, 65),
                (-78, 14, 2, 66)]
grng = random.Random(77)
gpts = []
for (gx, gy, cnt, sd) in garden_spots:
    for i in range(cnt):
        gpts.append((gx + grng.uniform(-7, 7), gy + grng.uniform(-6, 6),
                     75.0 - 0.8))
if gpts:
    import numpy as _np
    arr = _np.array(gpts)
    instancer('GardenPts', arr, trees[1], 4242)
