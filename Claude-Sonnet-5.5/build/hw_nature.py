"""Forest / rock scatter: density fields, point generation, geometry-nodes instancing."""
import bpy
import numpy as np
import math
import hw_layout as L
import hw_terrain as T
from hw_noise import fbm2, smoothstep, sdf_polygon, dist_polyline, hash01
import hw_trees as TR
import hw_scene as S

CAM_POINTS = np.array([[-30.0, -520.0], [-10.0, -175.0], [250.0, 0.0], [-420.0, -520.0], [-45.0, -120.0]])


def _slope(smp, x, y, e=3.0):
    zx = (smp.z(x + e, y) - smp.z(x - e, y)) / (2 * e)
    zy = (smp.z(x, y + e) - smp.z(x, y - e)) / (2 * e)
    return np.hypot(zx, zy)


def plateau_dist(x, y):
    poly = L.PLATFORMS[0]['poly']
    return -sdf_polygon(x, y, poly)     # positive outside


def density(x, y, z, slope, paths=()):
    noise_tl = FBM(x / 260.0, y / 260.0, 3, 91)
    tl = 1.0 - smoothstep(470.0, 640.0, z + 70.0 * noise_tl)
    low = smoothstep(1.4, 4.5, z)
    slope_f = 1.0 - smoothstep(0.80, 1.30, slope)
    big = FBM(x / 170.0, y / 170.0, 4, 92)
    fine = FBM(x / 38.0, y / 38.0, 3, 93)
    clump = smoothstep(-0.28, 0.12, big) * (0.55 + 0.45 * smoothstep(-0.4, 0.2, fine))
    valley = 0.72 + 0.28 * smoothstep(320.0, 20.0, z)
    dcas = plateau_dist(x, y)
    thin = smoothstep(22.0, 210.0, dcas)
    pf = np.ones_like(x)
    for (cxx, cyy, rr) in L.CLEARINGS:
        pf *= smoothstep(rr * 0.6, rr * 1.2, np.hypot(x - cxx, y - cyy))
    for pth in paths:
        d, _, _, _ = dist_polyline(x, y, pth)
        pf *= smoothstep(4.0, 11.0, d)
    return tl * low * slope_f * clump * valley * thin * pf


def FBM(x, y, o, seed):
    return fbm2(x, y, o, seed=seed) * 1.6


def forest_points(smp, rng, paths=(), extent=5600.0, d0=0.9, max_points=140000):
    zones = [(0.0, 950.0, 6.0, 1.0), (950.0, 2600.0, 10.0, 1.35), (2600.0, extent, 20.0, 1.9)]
    P = []
    for (r0, r1, c, sc) in zones:
        n = int(2 * r1 / c) + 1
        gx = -r1 + np.arange(n) * c
        X, Y = np.meshgrid(gx, gx)
        X = X.ravel() + 20.0
        Y = Y.ravel() - 100.0
        rr = np.hypot(X - 20.0, Y + 100.0)
        m = (rr >= r0) & (rr < r1)
        X, Y = X[m], Y[m]
        X = X + (rng.random(len(X)) - 0.5) * c * 0.92
        Y = Y + (rng.random(len(Y)) - 0.5) * c * 0.92
        z = smp.z(X, Y)
        ok = ~np.isnan(z)
        X, Y, z = X[ok], Y[ok], z[ok]
        # quick reject
        q = (z > 1.2) & (z < 700.0)
        X, Y, z = X[q], Y[q], z[q]
        sl = _slope(smp, X, Y, e=max(2.0, c * 0.5))
        D = density(X, Y, z, sl, paths) * d0
        acc = rng.random(len(X)) < D
        X, Y, z, sl = X[acc], Y[acc], z[acc], sl[acc]
        cam_d = np.min(np.hypot(X[:, None] - CAM_POINTS[None, :, 0], Y[:, None] - CAM_POINTS[None, :, 1]), axis=1)
        lod = np.where(cam_d < 380.0, 0, np.where(cam_d < 1500.0, 1, 2))
        # species
        u = rng.random(len(X))
        alt = smoothstep(150.0, 480.0, z)
        sp = np.where(u < 0.30 - 0.10 * alt, 0, np.where(u < 0.56 - 0.12 * alt, 1, np.where(u < 0.78 - 0.14 * alt, 2, 3)))
        variant = sp + 5 * lod
        # tree variants: 0..3 spruce/fir per lod block of 4, pines at index 12..14 -> remap
        var_idx = lod * 4 + sp
        size = np.exp(rng.normal(0.0, 0.16, len(X))) * sc * (1.0 - 0.45 * smoothstep(250.0, 620.0, z))
        rot = rng.random(len(X)) * 2 * math.pi
        P.append(np.column_stack([X, Y, z - 0.35, var_idx, size, rot]))
    P = np.concatenate(P)
    P = np.concatenate([P, ledge_trees(smp, rng, paths)])
    if len(P) > max_points:
        idx = rng.choice(len(P), max_points, replace=False)
        P = P[idx]
    return P


def ledge_trees(smp, rng, paths=(), region=(-330.0, 330.0, -150.0, 130.0), step=3.0, p=0.02):
    """Small wind-bent conifers clinging to the ledges of the crag."""
    x0, x1, y0, y1 = region
    gx = np.arange(x0, x1, step)
    gy = np.arange(y0, y1, step)
    X, Y = np.meshgrid(gx, gy)
    X = X.ravel() + (rng.random(X.size) - 0.5) * step
    Y = Y.ravel() + (rng.random(Y.size) - 0.5) * step
    z, s, amount, inside = T.height(X, Y, 1.0)
    e = 2.0
    zx = (smp.z(X + e, Y) - smp.z(X - e, Y)) / (2 * e)
    zy = (smp.z(X, Y + e) - smp.z(X, Y - e)) / (2 * e)
    sl = np.hypot(zx, zy)
    ok = (inside < 0.05) & (amount > 0.2) & (sl < 0.85) & (z > 4.0) & (z < L.Z0 - 5.0) & (rng.random(len(X)) < p)
    for pth in paths:
        d, _, _, _ = dist_polyline(X, Y, pth)
        ok &= d > 4.0
    for (cxx, cyy, rr) in L.CLEARINGS:
        ok &= np.hypot(X - cxx, Y - cyy) > rr * 0.9
    X, Y, z = X[ok], Y[ok], z[ok]
    cam_d = np.min(np.hypot(X[:, None] - CAM_POINTS[None, :, 0], Y[:, None] - CAM_POINTS[None, :, 1]), axis=1)
    lod = np.where(cam_d < 380.0, 0, 1)
    sp = rng.choice([0, 1, 3], size=len(X))
    var_idx = lod * 4 + sp
    size = rng.uniform(0.5, 0.95, len(X))
    rot = rng.random(len(X)) * 2 * math.pi
    return np.column_stack([X, Y, z - 0.3, var_idx, size, rot])


def make_proto_collection(order_geos, order, coll_name='Tree_Protos'):
    """Prototype collection for Collection Info + Pick Instance.  Blender sorts the children by name, therefore
    `order` must already be in alphabetical order (asserted) so that the instance index equals the position in `order`."""
    assert list(order) == sorted(order), 'prototype names must sort like their instance index: %s' % (order,)
    coll = S.ensure_collection(coll_name, parent=S.ensure_collection('Nature'))
    S.clear_collection(coll_name)
    objs = []
    for nm in order:
        g = order_geos[nm]
        g.consolidate()
        o = g.to_object(bpy, coll, nm)
        o.hide_render = False
        objs.append(o)
    return coll, objs


def build_scatter_gn(name, proto_coll, points, attr_names=('variant', 'scale', 'rot')):
    """Point cloud object + geometry-nodes graph instancing proto_coll children by 'variant'."""
    coll = S.ensure_collection('Nature')
    S.remove_object(name)
    n = len(points)
    mesh = bpy.data.meshes.new(name)
    mesh.vertices.add(n)
    co = points[:, :3].astype(np.float32)
    mesh.vertices.foreach_set('co', co.ravel())
    a1 = mesh.attributes.new('variant', 'INT', 'POINT')
    a1.data.foreach_set('value', points[:, 3].astype(np.int32))
    a2 = mesh.attributes.new('scale', 'FLOAT', 'POINT')
    a2.data.foreach_set('value', points[:, 4].astype(np.float32))
    a3 = mesh.attributes.new('rot', 'FLOAT', 'POINT')
    a3.data.foreach_set('value', points[:, 5].astype(np.float32))
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    # geometry nodes
    ng = bpy.data.node_groups.get('GN_' + name)
    if ng is not None:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new('GN_' + name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nd = ng.nodes
    gi = nd.new('NodeGroupInput')
    go = nd.new('NodeGroupOutput')
    ci = nd.new('GeometryNodeCollectionInfo')
    ci.transform_space = 'RELATIVE'
    ci.inputs['Collection'].default_value = proto_coll
    ci.inputs['Separate Children'].default_value = True
    ci.inputs['Reset Children'].default_value = True
    iop = nd.new('GeometryNodeInstanceOnPoints')
    iop.inputs['Pick Instance'].default_value = True
    na_var = nd.new('GeometryNodeInputNamedAttribute')
    na_var.data_type = 'INT'
    na_var.inputs['Name'].default_value = 'variant'
    na_sc = nd.new('GeometryNodeInputNamedAttribute')
    na_sc.data_type = 'FLOAT'
    na_sc.inputs['Name'].default_value = 'scale'
    na_rot = nd.new('GeometryNodeInputNamedAttribute')
    na_rot.data_type = 'FLOAT'
    na_rot.inputs['Name'].default_value = 'rot'
    comb_s = nd.new('ShaderNodeCombineXYZ')
    comb_r = nd.new('ShaderNodeCombineXYZ')
    e2r = nd.new('FunctionNodeEulerToRotation')
    lk = ng.links
    lk.new(gi.outputs[0], iop.inputs['Points'])
    lk.new(ci.outputs['Instances'], iop.inputs['Instance'])
    lk.new(na_var.outputs['Attribute'], iop.inputs['Instance Index'])
    for k in ('X', 'Y', 'Z'):
        lk.new(na_sc.outputs['Attribute'], comb_s.inputs[k])
    lk.new(comb_s.outputs['Vector'], iop.inputs['Scale'])
    lk.new(na_rot.outputs['Attribute'], comb_r.inputs['Z'])
    lk.new(comb_r.outputs['Vector'], e2r.inputs['Euler'])
    lk.new(e2r.outputs['Rotation'], iop.inputs['Rotation'])
    lk.new(iop.outputs['Instances'], go.inputs[0])
    mod = obj.modifiers.new('Scatter', 'NODES')
    mod.node_group = ng
    return obj


# --------------------------------------------------------------------------------------
# terrain attribute helpers (path mask + forest darkening)
# --------------------------------------------------------------------------------------
from hw_noise import catmull_rom


def smoothed_paths():
    out = {}
    for k, pts in L.PATHS.items():
        out[k] = catmull_rom(np.array(pts, float), per_seg=10)
    return out


def terrain_extra(paths):
    def fn(X, Y, z, slope, s, amount, inside):
        pm = np.zeros(X.shape)
        for k, pth in paths.items():
            d, _, _, _ = dist_polyline(X, Y, pth)
            pm = np.maximum(pm, smoothstep(2.6, 0.8, d))
        D = density(X, Y, z, slope, ())
        return dict(path=pm, forest=np.clip(D * 1.6, 0, 1))
    return fn


# --------------------------------------------------------------------------------------
# rock scatter (slabs on the crag flank, talus, shore stones, moor stones, rim spires)
# --------------------------------------------------------------------------------------

def _euler_from_normal(nrm, yaw):
    """XYZ Euler that maps +Z to `nrm` and then spins by `yaw` about it."""
    z = nrm / np.linalg.norm(nrm, axis=1, keepdims=True)
    ref = np.where((np.abs(z[:, 2]) < 0.95)[:, None], np.array([[0.0, 0.0, 1.0]]), np.array([[1.0, 0.0, 0.0]]))
    x = np.cross(ref, z)
    x /= np.linalg.norm(x, axis=1, keepdims=True)
    y = np.cross(z, x)
    c, s = np.cos(yaw)[:, None], np.sin(yaw)[:, None]
    xr = x * c + y * s
    yr = -x * s + y * c
    R = np.stack([xr, yr, z], axis=2)          # columns = rotated axes  -> R[:, :, k]
    ry = -np.arcsin(np.clip(R[:, 2, 0], -1, 1))
    rx = np.arctan2(R[:, 2, 1], R[:, 2, 2])
    rz = np.arctan2(R[:, 1, 0], R[:, 0, 0])
    return rx, ry, rz


def rock_points(rng, stair_polys=(), paths=(), region=(-440.0, 520.0, -560.0, 160.0), step=2.6, density_scale=1.0):
    x0, x1, y0, y1 = region
    gx = np.arange(x0, x1, step)
    gy = np.arange(y0, y1, step)
    X, Y = np.meshgrid(gx, gy)
    X = X.ravel() + (rng.random(X.size) - 0.5) * step
    Y = Y.ravel() + (rng.random(Y.size) - 0.5) * step
    z, s, amount, inside = T.height(X, Y, 1.0)
    e = 2.0
    zx = (T.height(X + e, Y, 1.0)[0] - T.height(X - e, Y, 1.0)[0]) / (2 * e)
    zy = (T.height(X, Y + e, 1.0)[0] - T.height(X, Y - e, 1.0)[0]) / (2 * e)
    slope = np.hypot(zx, zy)
    nrm = np.stack([-zx, -zy, np.ones_like(zx)], axis=1)
    u = rng.random(len(X))
    cat = np.full(len(X), -1)
    ok = inside < 0.05
    for pth in stair_polys:
        d, _, _, _ = dist_polyline(X, Y, pth[:, :2])
        ok &= d > 5.5
    for pth in paths:
        d, _, _, _ = dist_polyline(X, Y, pth)
        ok &= d > 4.0
    # boat shelf / boathouse footprint
    bh = L.BOATHOUSE
    ok &= ~((X > bh['cx'] - 34.0) & (X < bh['cx'] + 35.0) & (Y > bh['cy'] - 34.0) & (Y < bh['cy'] + 16.0) & (z < 12))
    A = ok & (amount > 0.25) & (slope > 0.55) & (slope < 4.0) & (z > 3.0) & (z < L.Z0 - 3.0) & (u < 0.060 * density_scale)     # slabs on the flank
    B = ok & (amount > 0.04) & (z > -1.5) & (z < 26.0) & (slope < 1.7) & (u < 0.085 * density_scale) & ~A   # talus boulders
    clump = smoothstep(0.42, 0.66, fbm2(X * 0.05 + 11.0, Y * 0.05 - 4.0, 3, seed=31))       # stones come in groups
    C = ok & (z > -0.6) & (z < 3.4) & (slope < 1.0) & (amount < 0.9) & (u < 0.24 * density_scale * clump) & ~A & ~B   # shore stones
    D = ok & (z > 5.0) & (slope < 0.8) & (amount < 0.05) & (u < 0.0022 * density_scale) & ~A & ~B & ~C      # moor stones
    E = ok & (amount > 0.6) & (z > L.Z0 - 26.0) & (z < L.Z0 - 4.0) & (slope > 1.5) & (u < 0.010 * density_scale) & ~A   # rim spires (on the cliff, not the rim)
    F = ok & (Y < -300.0) & (z > -0.5) & (z < 3.2) & (slope < 1.3) & (u < 0.13 * density_scale * (0.35 + clump)) & ~A & ~B & ~C   # foreground shores
    pts = []
    def add(mask, variants, size_fn, flat_fn, sink=0.22, align=1.0, yaw_fn=None, sxy=None, inset=0.0):
        idx = np.nonzero(mask)[0]
        if len(idx) == 0:
            return
        k = len(idx)
        var = rng.choice(variants, size=k)
        sz = size_fn(k)
        fl = flat_fn(k)
        nn = nrm[idx] * align + np.array([[0.0, 0.0, 1.0]]) * (1.0 - align) * np.linalg.norm(nrm[idx], axis=1, keepdims=True)
        yaw = yaw_fn(idx, k) if yaw_fn is not None else rng.random(k) * 2 * math.pi
        rx, ry, rz = _euler_from_normal(nn, yaw)
        if sxy is None:
            sx = sz * (0.85 + 0.6 * rng.random(k))
            sy = sz * (0.7 + 0.6 * rng.random(k))
        else:
            sx = sz * (sxy[0] + (sxy[1] - sxy[0]) * rng.random(k))
            sy = sz * (sxy[2] + (sxy[3] - sxy[2]) * rng.random(k))
        szz = sz * fl
        px, py = X[idx].copy(), Y[idx].copy()
        if inset > 0.0:                      # push the block into the wall along the horizontal outward normal
            nh = nrm[idx][:, :2]
            nh = nh / np.maximum(np.linalg.norm(nh, axis=1, keepdims=True), 1e-6)
            px -= nh[:, 0] * inset * sx
            py -= nh[:, 1] * inset * sx
        pos = np.column_stack([px, py, z[idx] - sink * szz])
        pts.append(np.column_stack([pos, var, sx, sy, szz, rx, ry, rz]))

    def wall_yaw(idx, k):
        return np.arctan2(nrm[idx][:, 1], nrm[idx][:, 0]) + math.pi / 2 + rng.normal(0.0, 0.30, k)
    # bedded ledge blocks on the flank: upright, long axis along the wall, half buried
    A2 = ok & (amount > 0.30) & (slope > 0.6) & (slope < 4.0) & (z > 2.0) & (z < L.Z0 - 2.0) & (u > 0.40) & (u < 0.40 + 0.20 * density_scale) & ~A
    A = A & (rng.random(len(A)) < 0.55)
    add(A2, [0, 1, 2, 3, 4], lambda k: np.exp(rng.normal(np.log(1.9), 0.42, k)), lambda k: 0.5 + 0.35 * rng.random(k),
        sink=0.40, align=0.08, yaw_fn=wall_yaw, sxy=(0.6, 1.0, 0.9, 1.6), inset=0.28)
    add(A, [0, 1, 2, 3, 4], lambda k: np.exp(rng.normal(np.log(4.6), 0.42, k)), lambda k: 0.55 + 0.30 * rng.random(k),
        sink=0.42, align=0.06, yaw_fn=wall_yaw, sxy=(0.55, 0.95, 0.95, 1.7), inset=0.30)
    add(B, [5, 6, 7, 8, 9, 10], lambda k: np.exp(rng.normal(np.log(2.4), 0.55, k)), lambda k: 0.7 + 0.4 * rng.random(k), sink=0.3, align=0.4)
    add(C, [5, 6, 7, 8, 9, 10], lambda k: np.exp(rng.normal(np.log(0.85), 0.72, k)), lambda k: 0.7 + 0.35 * rng.random(k), sink=0.25, align=0.3)
    add(F, [5, 6, 7, 8, 9, 10], lambda k: np.exp(rng.normal(np.log(1.15), 0.70, k)), lambda k: 0.62 + 0.35 * rng.random(k), sink=0.30, align=0.3)
    add(D, [5, 6, 7, 8, 9, 10], lambda k: np.exp(rng.normal(np.log(1.6), 0.5, k)), lambda k: 0.7 + 0.35 * rng.random(k), sink=0.3, align=0.3)
    add(E, [11, 12, 13, 14], lambda k: np.exp(rng.normal(np.log(3.2), 0.4, k)), lambda k: 1.0 + 0.5 * rng.random(k), sink=0.15, align=0.25)
    return np.concatenate(pts) if pts else np.zeros((0, 10))


def shore_points(rng, region=(-470.0, 470.0, -500.0, -230.0), step=0.85, density_scale=1.0):
    """Reed clumps along the waterline and grass / heather tufts on the low ground of the foreground shores."""
    x0, x1, y0, y1 = region
    gx = np.arange(x0, x1, step)
    gy = np.arange(y0, y1, step)
    X, Y = np.meshgrid(gx, gy)
    X = X.ravel() + (rng.random(X.size) - 0.5) * step
    Y = Y.ravel() + (rng.random(Y.size) - 0.5) * step
    z, s_, amount, inside = T.height(X, Y, 1.0)
    e = 1.5
    zx = (T.height(X + e, Y, 1.0)[0] - T.height(X - e, Y, 1.0)[0]) / (2 * e)
    zy = (T.height(X, Y + e, 1.0)[0] - T.height(X, Y - e, 1.0)[0]) / (2 * e)
    slope = np.hypot(zx, zy)
    nrm = np.stack([-zx, -zy, np.ones_like(zx)], axis=1)
    u = rng.random(len(X))
    clump = smoothstep(0.38, 0.62, fbm2(X * 0.07 - 5.0, Y * 0.07 + 2.0, 3, seed=47))
    reeds = (z > -1.1) & (z < 1.5) & (slope < 1.3) & (amount < 0.7) & (u < 0.36 * density_scale * (0.12 + clump))
    tufts = (z > 0.6) & (z < 16.0) & (slope < 1.1) & (amount < 0.25) & (inside < 0.05) & \
        (u < 0.95 * density_scale * (0.30 + clump)) & ~reeds
    pts = []
    for mask, variants, hgt, wid in ((reeds, [0, 1, 2], 1.0, 1.0), (tufts, [3, 4, 5], 1.0, 1.0)):
        idx = np.nonzero(mask)[0]
        k = len(idx)
        if k == 0:
            continue
        var = rng.choice(variants, size=k)
        sc = np.exp(rng.normal(0.0, 0.22, k))
        sx = sc * (0.9 + 0.4 * rng.random(k))
        sz = sc * hgt * (0.85 + 0.35 * rng.random(k))
        rz = rng.random(k) * 2 * math.pi
        rx, ry, _ = _euler_from_normal(nrm[idx] * 0.35 + np.array([[0.0, 0.0, 1.0]]) * 0.65 * np.linalg.norm(nrm[idx], axis=1, keepdims=True),
                                       np.zeros(k))
        pos = np.column_stack([X[idx], Y[idx], z[idx] - 0.06])
        pts.append(np.column_stack([pos, var, sx, sx, sz, rx, ry, rz]))
    return np.concatenate(pts) if pts else np.zeros((0, 10))


def build_rock_gn(name, proto_coll, pts):
    coll = S.ensure_collection('Nature')
    S.remove_object(name)
    n = len(pts)
    mesh = bpy.data.meshes.new(name)
    mesh.vertices.add(n)
    mesh.vertices.foreach_set('co', pts[:, :3].astype(np.float32).ravel())
    a = mesh.attributes.new('variant', 'INT', 'POINT')
    a.data.foreach_set('value', pts[:, 3].astype(np.int32))
    for i, nm in enumerate(('sx', 'sy', 'sz', 'rx', 'ry', 'rz')):
        at = mesh.attributes.new(nm, 'FLOAT', 'POINT')
        at.data.foreach_set('value', pts[:, 4 + i].astype(np.float32))
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    ng = bpy.data.node_groups.get('GN_' + name)
    if ng is not None:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new('GN_' + name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nd = ng.nodes
    lk = ng.links
    gi = nd.new('NodeGroupInput')
    go = nd.new('NodeGroupOutput')
    ci = nd.new('GeometryNodeCollectionInfo')
    ci.transform_space = 'RELATIVE'
    ci.inputs['Collection'].default_value = proto_coll
    ci.inputs['Separate Children'].default_value = True
    ci.inputs['Reset Children'].default_value = True
    iop = nd.new('GeometryNodeInstanceOnPoints')
    iop.inputs['Pick Instance'].default_value = True

    def named(nm, dt):
        x = nd.new('GeometryNodeInputNamedAttribute')
        x.data_type = dt
        x.inputs['Name'].default_value = nm
        return x
    v = named('variant', 'INT')
    sc = nd.new('ShaderNodeCombineXYZ')
    rt = nd.new('ShaderNodeCombineXYZ')
    e2r = nd.new('FunctionNodeEulerToRotation')
    for nm, k in (('sx', 'X'), ('sy', 'Y'), ('sz', 'Z')):
        lk.new(named(nm, 'FLOAT').outputs['Attribute'], sc.inputs[k])
    for nm, k in (('rx', 'X'), ('ry', 'Y'), ('rz', 'Z')):
        lk.new(named(nm, 'FLOAT').outputs['Attribute'], rt.inputs[k])
    lk.new(gi.outputs[0], iop.inputs['Points'])
    lk.new(ci.outputs['Instances'], iop.inputs['Instance'])
    lk.new(v.outputs['Attribute'], iop.inputs['Instance Index'])
    lk.new(sc.outputs['Vector'], iop.inputs['Scale'])
    lk.new(rt.outputs['Vector'], e2r.inputs['Euler'])
    lk.new(e2r.outputs['Rotation'], iop.inputs['Rotation'])
    lk.new(iop.outputs['Instances'], go.inputs[0])
    mod = obj.modifiers.new('Rocks', 'NODES')
    mod.node_group = ng
    return obj
