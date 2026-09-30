"""Conifer prototypes, forest scatter (geometry nodes), rock-ledge vegetation, grounds props."""
import bpy, math, random
from mathutils import Vector, noise
import geo, terrain, crag
from geo import MB, mat_loc, TAU


# ---------------------------------------------------------------- tree prototypes
def conifer(mb, h, w, tiers, seed, kind='spruce'):
    rnd = random.Random(seed)
    # trunk
    mb.lathe([(w * 0.06, -0.5), (w * 0.045, h * 0.5), (0.02, h * 0.95)], 7, 'Bark')
    base = h * (0.12 if kind == 'spruce' else 0.35)
    for t in range(tiers):
        f0 = t / tiers
        f1 = (t + 1.35) / tiers
        z0 = base + (h - base) * f0
        z1 = min(base + (h - base) * f1, h)
        if kind == 'spruce':
            r = w * (1 - f0) ** 1.05 * rnd.uniform(0.85, 1.1) + 0.2
        else:  # pine: rounded crown
            r = w * math.sin(math.pi * (0.25 + 0.75 * f0)) * rnd.uniform(0.8, 1.15) + 0.3
        n = 11 + rnd.randint(0, 4)
        ring_out = []
        ring_in = []
        ph = rnd.random() * TAU
        droop = r * 0.35
        for i in range(n):
            a = ph + TAU * i / n
            rr = r * rnd.uniform(0.7, 1.15)
            ring_out.append((rr * math.cos(a), rr * math.sin(a), z0 - droop * rnd.uniform(0.6, 1.2)))
            a2 = a + TAU / n / 2
            ri = rr * 0.45
            ring_in.append((ri * math.cos(a2), ri * math.sin(a2), z0 + droop * 0.2))
        # zig-zag skirt: interleave outer tips and inner notches
        ring = []
        for o, ii in zip(ring_out, ring_in):
            ring.append(o)
            ring.append(ii)
        apex = [(rnd.uniform(-0.1, 0.1) * r, rnd.uniform(-0.1, 0.1) * r, z1)]
        under = [(0.0, 0.0, z0 + (z1 - z0) * 0.15)]
        mb.loft([under, [(p[0] * 0.3, p[1] * 0.3, z0 - droop * 0.2) for p in ring], ring, apex], 'Conifer',
                cap_bot=False, cap_top=False)


def _ribbon(mb, pts, W0, axis, rnd, drop=0.0, taper=0.8, sc=1.0):
    verts = []
    n = len(pts)
    for i, p in enumerate(pts):
        t = i / (n - 1)
        wv = W0 * (1 - taper * t) * sc * rnd.uniform(0.6, 1.0)
        off = axis * wv
        dz = Vector((0, 0, -drop * wv))
        verts.append(tuple(p + off + dz))
        verts.append(tuple(p - off + dz))
    faces = [(2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1) for i in range(n - 1)]
    mb.add(verts, faces, 'Conifer')


def conifer2(mb, h, w, seed, kind='spruce'):
    """branch-level conifer: tapered trunk; many jittered drooping branches with upturned tips,
    each a pair of crossed needle ribbons plus side twigs (reads in silhouette and from above)."""
    rnd = random.Random(seed)
    tr = w * 0.07 + 0.08
    mb.lathe([(tr * 1.3, -0.6), (tr, 0.4), (tr * 0.6, h * 0.5), (tr * 0.25, h * 0.85), (0.03, h)], 8, 'Bark')
    base = h * (0.16 if kind == 'spruce' else 0.45)
    nbr = int((h - base) * (9.0 if kind == 'spruce' else 6.5))
    up = Vector((0, 0, 1))
    for k in range(nbr):
        f = (k + rnd.random()) / nbr
        z = base + (h - base) * f * 0.97
        if kind == 'spruce':
            L = w * (1 - f) ** 0.9 + 0.2
        else:
            L = w * (0.3 + 0.7 * math.sin(math.pi * min(1.0, 0.15 + f))) + 0.2
        L *= rnd.uniform(0.6, 1.15)
        a = rnd.random() * TAU
        d = Vector((math.cos(a), math.sin(a), 0.0))
        side = Vector((-math.sin(a), math.cos(a), 0.0))
        droop = rnd.uniform(0.25, 0.45) * (1.0 if kind == 'spruce' else 0.5)
        curl = rnd.uniform(0.05, 0.2)
        pts = []
        for i in range(9):
            t = i / 8
            p = Vector((0, 0, z)) + d * (L * t + tr * 0.5) + up * (L * (0.1 * t - droop * t * t + curl * t ** 4))
            p += side * (L * 0.08 * math.sin(t * 3.0 + a))
            pts.append(p)
        W0 = min(0.5 * L, 1.1) * rnd.uniform(0.85, 1.15)
        _ribbon(mb, pts, W0, side, rnd, 0.0, 0.7)
        _ribbon(mb, pts, W0, up, rnd, 0.3, 0.75, 0.45)
        # side twigs
        for j in range(4 if L > 1.2 else 1):
            t0 = rnd.uniform(0.2, 0.75)
            i0 = int(t0 * 8)
            sgn = 1 if j % 2 == 0 else -1
            dd = (d * 0.6 + side * sgn * 0.8).normalized()
            Lt = L * rnd.uniform(0.25, 0.4)
            tp = [pts[i0] + dd * (Lt * q / 4) + up * (-Lt * 0.15 * (q / 4) ** 2) for q in range(5)]
            _ribbon(mb, tp, W0 * 0.7, Vector((-dd.y, dd.x, 0.0)), rnd, 0.0, 0.85)
    mb.lathe([(0.1, h - 0.2), (0.0, h + 0.8)], 5, 'Conifer')


def shrub(mb, r, seed):
    """juniper / gorse clump: several jagged spiky mounds."""
    rnd = random.Random(seed)
    for k in range(6):
        c = (rnd.uniform(-r, r) * 0.55, rnd.uniform(-r, r) * 0.55, rnd.uniform(-0.1, r * 0.15))
        rr = r * rnd.uniform(0.35, 0.7)
        hh = rr * rnd.uniform(0.9, 1.6)
        n = 9 + rnd.randint(0, 4)
        rings = [[(c[0], c[1], c[2] - 0.1)]]
        for lvl, (fr, fz) in enumerate(((1.0, 0.18), (0.8, 0.5), (0.45, 0.8))):
            ring = []
            for i in range(n * 2):
                a = TAU * i / (n * 2) + lvl * 0.4
                rad = rr * fr * (1.0 if i % 2 == 0 else 0.62) * rnd.uniform(0.8, 1.15)
                ring.append((c[0] + rad * math.cos(a), c[1] + rad * math.sin(a), c[2] + hh * fz + rnd.uniform(-0.08, 0.08) * rr))
            rings.append(ring)
        rings.append([(c[0] + rnd.uniform(-0.1, 0.1) * rr, c[1], c[2] + hh)])
        mb.loft(rings, 'Shrub', cap_bot=False, cap_top=False)


def make_prototypes():
    coll = geo.get_coll('TreeProtos', geo.get_coll('Nature'))
    for o in list(coll.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    specs = [('Tree_Spruce_A', 22, 4.0, 1, 'spruce'), ('Tree_Spruce_B', 17, 3.4, 2, 'spruce'),
             ('Tree_Spruce_C', 26, 4.4, 3, 'spruce'), ('Tree_Fir_Young', 9, 2.2, 4, 'spruce'),
             ('Tree_Pine_A', 19, 4.6, 5, 'pine'), ('Tree_Pine_B', 15, 3.8, 6, 'pine'),
             ('Tree_Spruce_D', 20, 3.0, 7, 'spruce')]
    obs = []
    for name, h, w, seed, kind in specs:
        mb = MB(name)
        conifer2(mb, h, w, seed, kind)
        ob = mb.build(coll, smooth_angle=None)
        obs.append(ob)
    sc = geo.get_coll('ShrubProtos', geo.get_coll('Nature'))
    for o in list(sc.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for i in range(4):
        mb = MB('Shrub_%d' % i)
        shrub(mb, 1.2 + i * 0.4, 20 + i)
        mb.build(sc, smooth_angle=80)
    # keep prototypes out of the render (instanced only)
    for c in (coll, sc):
        lc = find_layer_coll(bpy.context.view_layer.layer_collection, c.name)
        if lc:
            lc.exclude = True
    return coll, sc


def find_layer_coll(lc, name):
    if lc.collection.name == name:
        return lc
    for ch in lc.children:
        r = find_layer_coll(ch, name)
        if r:
            return r
    return None


# ---------------------------------------------------------------- masks
def forest_mask(ob):
    me = ob.data
    n = len(me.vertices)
    co = [0.0] * (3 * n)
    me.vertices.foreach_get('co', co)
    nrm = [0.0] * (3 * n)
    me.vertices.foreach_get('normal', nrm)
    path = [0.0] * n
    if 'path' in me.attributes:
        me.attributes['path'].data.foreach_get('value', path)
    vals = [0.0] * n
    for i in range(n):
        x, y, z = co[3 * i], co[3 * i + 1], co[3 * i + 2]
        if z < 1.2:
            continue
        d = math.hypot(x, y)
        if d > 4200:
            continue
        nz = nrm[3 * i + 2]
        m = geo.smoothstep(0.72, 0.86, nz)
        m *= 1.0 - geo.smoothstep(380, 560, z)
        # keep the castle grounds open
        g = min(math.hypot((x - 20) / 1.25, (y - 170) / 1.0), 1e9)
        m *= geo.smoothstep(230, 360, g) if y > -50 else geo.smoothstep(240, 300, d)
        # east hill with the stone circle: open moor on top
        m *= geo.smoothstep(70, 150, math.hypot(x - terrain.EAST_HILL[0], y - terrain.EAST_HILL[1]))
        # quidditch pitch clearing
        m *= geo.smoothstep(140, 210, math.hypot((x - terrain.PITCH[0]) / 1.3, y - terrain.PITCH[1]))
        # clearings and denser valleys
        cl = noise.noise(Vector((x / 380.0, y / 380.0, 4.2)))
        m *= geo.smoothstep(-0.35, 0.15, cl)
        vn = noise.noise(Vector((x / 160.0, y / 160.0, 8.7)))
        m *= 0.55 + 0.45 * geo.smoothstep(-0.2, 0.3, vn)
        # the Forbidden Forest (west / north-west of the hut): dense
        ff = math.hypot(x + 420, y - 560)
        if ff < 700:
            m = max(m * (1.0 - geo.smoothstep(700, 300, ff)), m * 1.0)
            m = min(1.0, m + 0.35 * geo.smoothstep(700, 250, ff) * geo.smoothstep(0.72, 0.86, nz)
                    * geo.smoothstep(140, 210, math.hypot((x - terrain.PITCH[0]) / 1.3, y - terrain.PITCH[1]))
                    * geo.smoothstep(40, 70, math.hypot(x - terrain.HUT[0], y - terrain.HUT[1])))
        m *= 1.0 - path[i]
        # thin out with distance (cost), trees there are sub-pixel texture anyway
        m *= 1.0 - 0.55 * geo.smoothstep(1800, 4200, d)
        vals[i] = max(0.0, min(1.0, m))
    a = me.attributes.get('forest') or me.attributes.new('forest', 'FLOAT', 'POINT')
    a.data.foreach_set('value', vals)
    me.update()
    return sum(vals)


def moor_mask(ob):
    """sparse gorse / juniper on open moorland, thicker along forest edges."""
    me = ob.data
    n = len(me.vertices)
    co = [0.0] * (3 * n)
    me.vertices.foreach_get('co', co)
    fo = [0.0] * n
    me.attributes['forest'].data.foreach_get('value', fo)
    pa = [0.0] * n
    me.attributes['path'].data.foreach_get('value', pa)
    vals = [0.0] * n
    for i in range(n):
        x, y, z = co[3 * i], co[3 * i + 1], co[3 * i + 2]
        if z < 1.5 or z > 600 or math.hypot(x, y) > 2500:
            continue
        edge = 4.0 * fo[i] * (1.0 - fo[i])
        m = (0.35 + 0.65 * edge) * (1.0 - pa[i])
        m *= 0.3 + 0.7 * geo.smoothstep(-0.1, 0.4, noise.noise(Vector((x / 60.0, y / 60.0, 2.2))))
        vals[i] = m
    a = me.attributes.get('moor') or me.attributes.new('moor', 'FLOAT', 'POINT')
    a.data.foreach_set('value', vals)


def ledge_mask(ob, top):
    me = ob.data
    n = len(me.vertices)
    co = [0.0] * (3 * n)
    nrm = [0.0] * (3 * n)
    me.vertices.foreach_get('co', co)
    me.vertices.foreach_get('normal', nrm)
    vals = [0.0] * n
    for i in range(n):
        z = co[3 * i + 2]
        nz = nrm[3 * i + 2]
        if z > top - 4.0 or z < 1.5:
            continue
        m = geo.smoothstep(0.3, 0.75, nz)
        m *= 0.3 + 0.7 * geo.smoothstep(-0.2, 0.3, noise.noise(Vector((co[3 * i] / 25, co[3 * i + 1] / 25, z / 25))))
        vals[i] = m
    a = me.attributes.get('veg') or me.attributes.new('veg', 'FLOAT', 'POINT')
    a.data.foreach_set('value', vals)
    # fallen blocks and boulders collecting at the waterline
    bv = [0.0] * n
    for i in range(n):
        z = co[3 * i + 2]
        if -1.5 < z < 5.0:
            bv[i] = geo.smoothstep(5.0, 1.0, z) * (0.3 + 0.7 * geo.smoothstep(-0.2, 0.3, noise.noise(Vector((co[3 * i] / 18, co[3 * i + 1] / 18, 7.7)))))
    a = me.attributes.get('boulder') or me.attributes.new('boulder', 'FLOAT', 'POINT')
    a.data.foreach_set('value', bv)
    me.update()


def make_boulders():
    coll = geo.get_coll('BoulderProtos', geo.get_coll('Nature'))
    for o in list(coll.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for k in range(5):
        rnd = random.Random(300 + k)
        mb = MB('Boulder_%d' % k)
        rings = []
        nr, na = 7, 10
        sx, sy, sz = rnd.uniform(0.8, 1.4), rnd.uniform(0.7, 1.2), rnd.uniform(0.5, 0.9)
        for i in range(nr + 1):
            t = i / nr
            ph = math.pi * t
            ring = []
            for j in range(na):
                a = TAU * j / na
                d = Vector((math.sin(ph) * math.cos(a), math.sin(ph) * math.sin(a), -math.cos(ph)))
                r = 1.0 + 0.25 * noise.noise(d * 1.7 + Vector((k * 3.1, 0, 0))) + 0.1 * noise.noise(d * 4.0)
                # flatten into facets
                r = round(r * 6) / 6
                ring.append((d.x * r * sx, d.y * r * sy, d.z * r * sz - 0.2))
            rings.append(ring if 0 < i < nr else [(0, 0, (-sz if i == 0 else sz) * r - 0.2)])
        mb.loft(rings, 'Rock')
        mb.build(coll, smooth_angle=30)
    lc = find_layer_coll(bpy.context.view_layer.layer_collection, coll.name)
    if lc:
        lc.exclude = True
    return coll


# ---------------------------------------------------------------- GN scatter
def scatter_group(name, attr, density, coll, scale=(0.6, 1.3), seed=0, align=False):
    ng = bpy.data.node_groups.get(name)
    if ng:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes
    L = ng.links
    gi = N.new('NodeGroupInput')
    go = N.new('NodeGroupOutput')
    na = N.new('GeometryNodeInputNamedAttribute')
    na.data_type = 'FLOAT'
    na.inputs['Name'].default_value = attr
    mul = N.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = density
    L.new(na.outputs['Attribute'], mul.inputs[0])
    dp = N.new('GeometryNodeDistributePointsOnFaces')
    dp.distribute_method = 'RANDOM'
    dp.inputs['Seed'].default_value = seed
    L.new(gi.outputs[0], dp.inputs['Mesh'])
    L.new(mul.outputs[0], dp.inputs['Density'])
    ci = N.new('GeometryNodeCollectionInfo')
    ci.inputs['Collection'].default_value = coll
    ci.inputs['Separate Children'].default_value = True
    ci.inputs['Reset Children'].default_value = True
    ip = N.new('GeometryNodeInstanceOnPoints')
    ip.inputs['Pick Instance'].default_value = True
    L.new(dp.outputs['Points'], ip.inputs['Points'])
    L.new(ci.outputs[0], ip.inputs['Instance'])
    # random rotation about Z (plus slight lean) and random scale
    rv = N.new('FunctionNodeRandomValue')
    rv.data_type = 'FLOAT_VECTOR'
    rv.inputs['Min'].default_value = (-0.05, -0.05, 0.0)
    rv.inputs['Max'].default_value = (0.05, 0.05, 6.283)
    rv.inputs['Seed'].default_value = seed + 1
    L.new(rv.outputs['Value'], ip.inputs['Rotation'])
    rs = N.new('FunctionNodeRandomValue')
    rs.data_type = 'FLOAT'
    rs.inputs[2].default_value = scale[0]
    rs.inputs[3].default_value = scale[1]
    rs.inputs['Seed'].default_value = seed + 2
    # bigger trees where the density is high (mature forest), smaller at the fringes
    sm = N.new('ShaderNodeMath')
    sm.operation = 'MULTIPLY_ADD'
    L.new(na.outputs['Attribute'], sm.inputs[0])
    sm.inputs[1].default_value = 0.35
    sm.inputs[2].default_value = 0.75
    sc2 = N.new('ShaderNodeMath')
    sc2.operation = 'MULTIPLY'
    L.new(rs.outputs[1], sc2.inputs[0])
    L.new(sm.outputs[0], sc2.inputs[1])
    L.new(sc2.outputs[0], ip.inputs['Scale'])
    ii = N.new('FunctionNodeRandomValue')
    ii.data_type = 'INT'
    ii.inputs[4].default_value = 0
    ii.inputs[5].default_value = 99
    ii.inputs['Seed'].default_value = seed + 3
    L.new(ii.outputs[2], ip.inputs['Instance Index'])
    j = N.new('GeometryNodeJoinGeometry')
    L.new(gi.outputs[0], j.inputs[0])
    L.new(ip.outputs[0], j.inputs[0])
    L.new(j.outputs[0], go.inputs[0])
    return ng


def add_scatter(ob, ng, modname='Scatter'):
    m = ob.modifiers.get(modname)
    if m is None:
        m = ob.modifiers.new(modname, 'NODES')
    m.node_group = ng
    return m


def build_forest():
    protos, shrubs = make_prototypes()
    ter = bpy.data.objects['Terrain']
    tot = forest_mask(ter)
    ng = scatter_group('GN_Forest', 'forest', 0.022, protos, (0.55, 1.25), 11)
    add_scatter(ter, ng, 'Forest')
    moor_mask(ter)
    ngm = scatter_group('GN_MoorShrubs', 'moor', 0.012, shrubs, (0.5, 1.4), 41)
    add_scatter(ter, ngm, 'MoorShrubs')
    ngl = scatter_group('GN_LedgeVeg', 'veg', 0.16, shrubs, (0.6, 1.8), 21)
    ngt = scatter_group('GN_LedgeTrees', 'veg', 0.03, protos, (0.45, 1.0), 31)
    bcoll = make_boulders()
    ngb = scatter_group('GN_Boulders', 'boulder', 0.05, bcoll, (0.6, 2.2), 51)
    for bl in crag.BLOBS:
        ob = bpy.data.objects.get(bl['name'])
        if not ob:
            continue
        ledge_mask(ob, bl['top'])
        add_scatter(ob, ngl, 'LedgeVeg')
        add_scatter(ob, ngt, 'LedgeTrees')
        add_scatter(ob, ngb, 'Boulders')
    return tot
