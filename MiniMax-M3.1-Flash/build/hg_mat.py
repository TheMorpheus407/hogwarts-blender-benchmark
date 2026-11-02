"""Hogwarts — procedural material library.  Every material is built from nodes."""
import bpy, math

TAU = math.pi * 2.0


# ---------------------------------------------------------------- node helpers
def NN(nt, t, loc=(0, 0), **kw):
    n = nt.nodes.new(t)
    n.location = loc
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def _is_socket(v):
    return isinstance(v, bpy.types.NodeSocket)


def _sock(v, prefer='Value'):
    """Return a socket from a socket, a node (default output), or None."""
    if v is None:
        return None
    if _is_socket(v):
        return v
    if hasattr(v, 'outputs'):
        outs = list(v.outputs)
        for o in outs:
            if o.name == prefer and o.type == 'VALUE':
                return o
        for o in outs:
            if o.type == 'VALUE':
                return o
        return outs[0] if outs else None
    return None


def L(nt, a, sa, b, sb=None):
    """Link a->b.

    5-arg form: L(nt, node_a, 'Out', node_b, 'In')
    4-arg form: L(nt, out_socket, node_b, 'In')
    """
    if sb is None:
        nt.links.new(a, sa.inputs[b])
        return
    out = a.outputs[sa] if hasattr(a, 'outputs') else a
    inp = b.inputs[sb] if hasattr(b, 'inputs') else b
    nt.links.new(out, inp)


def ramp(nt, loc, stops, interp='LINEAR'):
    n = NN(nt, 'ShaderNodeValToRGB', loc)
    n.color_ramp.interpolation = interp
    el = n.color_ramp.elements
    while len(el) > 1:
        el.remove(el[-1])
    el[0].position = stops[0][0]
    el[0].color = stops[0][1]
    for pos, col in stops[1:]:
        e = el.new(pos)
        e.color = col
    return n


def mixrgb(nt, loc, fac=0.5, c1=(0, 0, 0, 1), c2=(1, 1, 1, 1)):
    n = NN(nt, 'ShaderNodeMixRGB', loc)
    n.inputs['Factor'].default_value = fac
    for sock, col in (('Color1', c1), ('Color2', c2)):
        if len(col) == 3:
            col = tuple(col) + (1.0,)
        n.inputs[sock].default_value = col
    return n


def mathn(nt, loc, op, a=None, b=None, c=None):
    n = NN(nt, 'ShaderNodeMath', loc)
    n.operation = op
    for i, v in enumerate((a, b, c)):
        if v is None:
            continue
        sk = _sock(v)
        if sk is not None:
            nt.links.new(sk, n.inputs[i])
        else:
            n.inputs[i].default_value = v
    return n


def maprange(nt, loc, src, fmin, fmax, tmin, tmax, clamp=True):
    n = NN(nt, 'ShaderNodeMapRange', loc)
    n.clamp = clamp
    n.inputs['From Min'].default_value = fmin
    n.inputs['From Max'].default_value = fmax
    n.inputs['To Min'].default_value = tmin
    n.inputs['To Max'].default_value = tmax
    if src is not None:
        sk = _sock(src)
        if sk is not None:
            nt.links.new(sk, n.inputs['Value'])
        else:
            n.inputs['Value'].default_value = src
    return n


def noise(nt, loc, scale=5.0, detail=6.0, rough=0.5, distortion=0.0, vec=None):
    n = NN(nt, 'ShaderNodeTexNoise', loc)
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough
    n.inputs['Distortion'].default_value = distortion
    if vec is not None:
        L(nt, vec, 'Vector', n, 'Vector')
    return n


def voronoi(nt, loc, scale=1.0, rand=1.0, feature='F1', vec=None):
    n = NN(nt, 'ShaderNodeTexVoronoi', loc)
    n.feature = feature
    n.inputs['Scale'].default_value = scale
    n.inputs['Randomness'].default_value = rand
    if vec is not None:
        L(nt, vec, 'Vector', n, 'Vector')
    return n


def mapping(nt, loc, vec, scale=(1, 1, 1), loc_off=(0, 0, 0), rot=(0, 0, 0)):
    n = NN(nt, 'ShaderNodeMapping', loc)
    n.inputs['Scale'].default_value = scale
    n.inputs['Location'].default_value = loc_off
    n.inputs['Rotation'].default_value = rot
    L(nt, vec, 'Vector', n, 'Vector')
    return n


def sepxyz(nt, loc, vec):
    n = NN(nt, 'ShaderNodeSeparateXYZ', loc)
    L(nt, vec, 'Vector', n, 'Vector')
    return n


def combxyz(nt, loc, x=None, y=None, z=None):
    n = NN(nt, 'ShaderNodeCombineXYZ', loc)
    for i, v in enumerate((x, y, z)):
        if v is None:
            continue
        sk = _sock(v)
        if sk is not None:
            nt.links.new(sk, n.inputs[i])
        else:
            n.inputs[i].default_value = v
    return n


def newmat(name):
    """Create (or reuse and reset) a material.  Safe to call repeatedly."""
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = NN(nt, 'ShaderNodeOutputMaterial', (900, 0))
    return m, nt, out


def newmat_volume(name):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = NN(nt, 'ShaderNodeOutputMaterial', (900, 0))
    return m, nt, out


# ---------------------------------------------------------------- masonry core
def masonry_mask(nt, vec, bw, rh, mortar, msize=0.018, msoft=0.06,
                 offset=0.5, squash=1.0, loc=(0, 0)):
    """Brick texture used as a mortar-joint mask (1 = mortar, 0 = face)."""
    b = NN(nt, 'ShaderNodeTexBrick', loc)
    b.offset = offset
    b.squash = squash
    b.inputs['Color1'].default_value = (0, 0, 0, 1)
    b.inputs['Color2'].default_value = (0, 0, 0, 1)
    b.inputs['Mortar'].default_value = (1, 1, 1, 1)
    b.inputs['Scale'].default_value = 1.0
    b.inputs['Mortar Size'].default_value = msize
    b.inputs['Mortar Smooth'].default_value = msoft
    b.inputs['Bias'].default_value = 0.0
    b.inputs['Brick Width'].default_value = bw
    b.inputs['Row Height'].default_value = rh
    L(nt, vec, 'Vector', b, 'Vector')
    return b


def _tri_weights(nt, nrm, loc, sharp=8.0):
    """Blend weights for three planar projections, driven by the normal."""
    sn = sepxyz(nt, (loc[0] - 300, loc[1]), nrm)
    ax = mathn(nt, (loc[0] - 160, loc[1]), 'ABSOLUTE', sn.outputs['X'])
    ay = mathn(nt, (loc[0] - 160, loc[1] - 90), 'ABSOLUTE', sn.outputs['Y'])
    az = mathn(nt, (loc[0] - 160, loc[1] - 180), 'ABSOLUTE', sn.outputs['Z'])
    wx = mathn(nt, (loc[0] - 60, loc[1]), 'POWER', ax, sharp)
    wy = mathn(nt, (loc[0] - 60, loc[1] - 90), 'POWER', ay, sharp)
    wz = mathn(nt, (loc[0] - 60, loc[1] - 180), 'POWER', az, sharp)
    s = mathn(nt, (loc[0] + 40, loc[1] - 90), 'ADD',
              mathn(nt, (loc[0] + 40, loc[1]), 'ADD', wx, wy), wz)
    wx = mathn(nt, (loc[0] + 140, loc[1]), 'DIVIDE', wx, s)
    wy = mathn(nt, (loc[0] + 140, loc[1] - 90), 'DIVIDE', wy, s)
    wz = mathn(nt, (loc[0] + 140, loc[1] - 180), 'DIVIDE', wz, s)
    return wx, wy, wz


def triplanar_masonry(nt, pos, nrm, bw, rh, msize=0.016, msoft=0.055,
                      loc=(0, 0), sharp=8.0):
    """Mortar-joint mask evaluated on three planar projections and blended
    by the surface normal.

    A single planar projection collapses to a constant on any face that is
    parallel to the projection plane, so big walls come out as blank,
    plaster-like surfaces with no course lines at all.  The triplanar blend
    keeps the masonry readable on every face of the castle, and each of the
    three grids is offset so the blend does not read as plaid.
    """
    sx = sepxyz(nt, (loc[0] - 300, loc[1]), pos)
    wx, wy, wz = _tri_weights(nt, nrm, (loc[0] + 260, loc[1] - 260), sharp)
    off = ((0.0, 0.0), (5.13, 2.71), (9.37, 4.19))
    ms = []
    for i, (ax, ay) in enumerate(((('X'), 'Y'), ('X', 'Z'), ('Y', 'Z'))):
        v = combxyz(nt, (loc[0] + 460, loc[1] - 300 * i),
                    mathn(nt, (loc[0] + 300, loc[1] - 300 * i), 'ADD',
                          sx.outputs[ax], off[i][0]),
                    mathn(nt, (loc[0] + 300, loc[1] - 300 * i - 60), 'ADD',
                          sx.outputs[ay], off[i][1]))
        ms.append(masonry_mask(nt, v, bw, rh, None, msize, msoft,
                               loc=(loc[0] + 460, loc[1] - 300 * i - 140)))
    t = []
    for m, w in zip(ms, (wx, wy, wz)):
        t.append(mathn(nt, (loc[0] + 660, loc[1] - 300 * len(ms)), 'MULTIPLY',
                      m.outputs['Fac'], w))
    s = mathn(nt, (loc[0] + 760, loc[1] - 900), 'ADD', t[0], t[1])
    return mathn(nt, (loc[0] + 860, loc[1] - 900), 'ADD', s, t[2])


def triplanar_brick_color(nt, pos, nrm, bw, rh, c1, c2, mortar, msize=0.018,
                          msoft=0.06, bias=0.0, offset=0.5, loc=(0, 0),
                          sharp=8.0):
    """Per-tile colour from three offset planar brick projections."""
    sx = sepxyz(nt, (loc[0] - 300, loc[1]), pos)
    wx, wy, wz = _tri_weights(nt, nrm, (loc[0] + 260, loc[1] - 260), sharp)
    off = ((0.0, 0.0), (3.71, 7.13), (8.29, 1.97))
    cs = []
    for i, (ax, ay) in enumerate((('X', 'Y'), ('X', 'Z'), ('Y', 'Z'))):
        v = combxyz(nt, (loc[0] + 460, loc[1] - 300 * i),
                    mathn(nt, (loc[0] + 300, loc[1] - 300 * i), 'ADD',
                          sx.outputs[ax], off[i][0]),
                    mathn(nt, (loc[0] + 300, loc[1] - 300 * i - 60), 'ADD',
                          sx.outputs[ay], off[i][1]))
        cs.append(brick_color(nt, v, bw, rh, c1, c2, mortar, msize, msoft,
                               bias, offset, loc=(loc[0] + 460,
                                                  loc[1] - 300 * i - 140)))
    # the blend has to be per-channel, so it is done with vector math
    t = []
    for c, w in zip(cs, (wx, wy, wz)):
        wv = combxyz(nt, (loc[0] + 600, loc[1] - 900), w, w, w)
        vm = NN(nt, 'ShaderNodeVectorMath', (loc[0] + 660, loc[1] - 900))
        vm.operation = 'MULTIPLY'
        L(nt, c.outputs['Color'], 'Vector', vm, 0)
        L(nt, wv, 'Vector', vm, 1)
        t.append(vm.outputs['Vector'])
    va = NN(nt, 'ShaderNodeVectorMath', (loc[0] + 760, loc[1] - 900))
    va.operation = 'ADD'
    L(nt, t[0], 'Vector', va, 0)
    L(nt, t[1], 'Vector', va, 1)
    vb = NN(nt, 'ShaderNodeVectorMath', (loc[0] + 860, loc[1] - 900))
    vb.operation = 'ADD'
    L(nt, va.outputs['Vector'], 'Vector', vb, 0)
    L(nt, t[2], 'Vector', vb, 1)
    return vb.outputs['Vector']


def brick_color(nt, vec, bw, rh, c1, c2, mortar, msize=0.018, msoft=0.06,
                bias=0.0, offset=0.5, loc=(0, 0)):
    b = NN(nt, 'ShaderNodeTexBrick', loc)
    b.offset = offset
    b.inputs['Color1'].default_value = c1
    b.inputs['Color2'].default_value = c2
    b.inputs['Mortar'].default_value = mortar
    b.inputs['Scale'].default_value = 1.0
    b.inputs['Mortar Size'].default_value = msize
    b.inputs['Mortar Smooth'].default_value = msoft
    b.inputs['Bias'].default_value = bias
    b.inputs['Brick Width'].default_value = bw
    b.inputs['Row Height'].default_value = rh
    L(nt, vec, 'Vector', b, 'Vector')
    return b


# =================================================================== materials

def shade_modulate(nt, loc, col_sock, noise_sock, lo=0.72, hi=1.34,
                   mid_lo=0.32, mid_hi=0.68):
    """Modulate a colour by a noise instead of mixing it toward white.

    `mix(base, white, noise)` does not add *grain* -- it lifts the base
    colour by roughly (1 - noise) of full white, so a dark surface ends up
    a uniform pale grey and every texture underneath is washed out.  This
    multiplies the base colour by a remapped noise instead, which keeps the
    material's own value and its detail intact.
    """
    m = maprange(nt, loc, noise_sock, mid_lo, mid_hi, lo, hi)
    v = combxyz(nt, (loc[0] + 170, loc[1]), m.outputs['Result'],
                m.outputs['Result'], m.outputs['Result'])
    vm = NN(nt, 'ShaderNodeVectorMath', (loc[0] + 330, loc[1]))
    vm.operation = 'MULTIPLY'
    L(nt, col_sock, 'Color', vm, 0)
    L(nt, v, 'Vector', vm, 1)
    return vm


def m_stone(name='M_Stone', cylindrical=False, radius=8.0, tint=(1, 1, 1),
            base_col=(0.345, 0.330, 0.300), courses=(1.7, 0.62)):
    """Weathered quarried ashlar: per-batch colour, dirt streaks, moss, edge wear."""
    m, nt, out = newmat(name)
    geo = NN(nt, 'ShaderNodeNewGeometry', (-1500, 200))
    pos = geo.outputs['Position']

    # ---- masonry coordinates (planar or cylindrical unwrap) ----
    tc = NN(nt, 'ShaderNodeTexCoord', (-1500, -300))
    obj = tc.outputs['Object']
    # ---- break the perfect coursing -----------------------------------
    # Real ashlar never lies on a perfect grid, and a perfect grid of equal
    # blocks with even joints reads as ceramic tile -- which is exactly what
    # the boathouse wall looked like in the close-up.  A slow noise offset
    # on the masonry coordinate makes the courses wander and the joints
    # wander with them.
    wn = noise(nt, (-1500, -820), 0.42, 3.0, 0.55, 0.0, obj)
    wsub = NN(nt, 'ShaderNodeVectorMath', (-1300, -820), operation='SUBTRACT')
    L(nt, wn.outputs['Color'], 'Vector', wsub, 0)
    wsub.inputs[1].default_value = (0.5, 0.5, 0.5)
    wsc = NN(nt, 'ShaderNodeVectorMath', (-1150, -820), operation='SCALE')
    L(nt, wsub.outputs['Vector'], 'Vector', wsc, 0)
    wsc.inputs['Scale'].default_value = 0.42
    wadd = NN(nt, 'ShaderNodeVectorMath', (-1000, -820), operation='ADD')
    L(nt, obj, 'Vector', wadd, 0)
    L(nt, wsc.outputs['Vector'], 'Vector', wadd, 1)
    wobj = wadd.outputs['Vector']
    if cylindrical:
        sep = sepxyz(nt, (-1300, -300), obj)
        ang = NN(nt, 'ShaderNodeMath', (-1150, -300))
        ang.operation = 'ARCTAN2'
        L(nt, sep, 'Y', ang, 0)
        L(nt, sep, 'X', ang, 1)
        u = mathn(nt, (-1000, -300), 'MULTIPLY', ang, radius)
        v = sep.outputs['Z']
        mu = combxyz(nt, (-850, -300), u, v)
        mj = masonry_mask(nt, mu, courses[0], courses[1], None, msize=0.024,
                          msoft=0.038, loc=(-650, -300))
        blk = None
    else:
        # Object-space normal, so the triplanar blend follows the wall and
        # every face keeps its course lines (a single planar projection
        # collapses to nothing on walls facing along that axis).
        vtr = NN(nt, 'ShaderNodeVectorTransform', (-1500, -560))
        vtr.vector_type = 'NORMAL'
        vtr.convert_from = 'WORLD'
        vtr.convert_to = 'OBJECT'
        L(nt, geo.outputs['Normal'], 'Vector', vtr, 'Vector')
        mj = triplanar_masonry(nt, wobj, vtr.outputs['Vector'],
                               courses[0], courses[1], msize=0.024,
                               msoft=0.038, loc=(-650, -300))
        # per-block tonal variation -- quarried stone is never one flat tone.
        # A wide spread here is what separates weathered ashlar from a sheet
        # of ceramic tile: without it the wall reads as a printed grid.
        # The BIAS has to stay near zero.  The Brick node's Bias ramps each
        # block from Colour1 to Colour2 across its width, so at bias 0.5
        # every block was a smooth 2.7x gradient and the wall came out
        # looking quilted -- padded panels of leather rather than stone.
        # Near zero the block is flat and the variety comes from the node's
        # random pick of one colour or the other per block, which is what
        # quarried ashlar actually does.
        blk = triplanar_brick_color(nt, wobj, vtr.outputs['Vector'],
                                    courses[0], courses[1],
                                    (0.60, 0.575, 0.535, 1),
                                    (1.24, 1.20, 1.13, 1),
                                    (0.98, 0.97, 0.94, 1),
                                    msize=0.020, msoft=0.036, bias=0.06,
                                    loc=(-650, 900))

    # ---- quarry batch colour ----
    v1 = voronoi(nt, (-1300, 500), 0.021, 1.0, 'F1', pos)
    s1 = NN(nt, 'ShaderNodeSeparateXYZ', (-1150, 500))
    L(nt, v1, 'Color', s1, 'Vector')
    batch = ramp(nt, (-980, 500), [(0.0, (0.74, 0.70, 0.63, 1)),
                                  (0.33, (0.92, 0.88, 0.80, 1)),
                                  (0.66, (1.05, 1.02, 0.96, 1)),
                                  (1.0, (0.80, 0.77, 0.72, 1))])
    L(nt, s1, 'X', batch, 'Factor')

    v2 = voronoi(nt, (-1300, 700), 0.0055, 1.0, 'F1', pos)
    s2 = NN(nt, 'ShaderNodeSeparateXYZ', (-1150, 700))
    L(nt, v2, 'Color', s2, 'Vector')
    big = ramp(nt, (-980, 700), [(0.0, (0.80, 0.82, 0.86, 1)),
                                 (0.5, (1.0, 1.0, 1.0, 1)),
                                 (1.0, (1.12, 1.10, 1.06, 1))])
    L(nt, s2, 'X', big, 'Factor')

    # base_col * batch * big  (base_col must stay in the chain: it was being
    # overwritten by the batch link before, which dropped the albedo entirely)
    stone = mixrgb(nt, (-760, 560), 1.0, base_col, (1, 1, 1, 1))
    stone.blend_type = 'MULTIPLY'
    L(nt, batch, 'Color', stone, 'Color2')
    stonetint = mixrgb(nt, (-660, 560), 1.0, (1, 1, 1, 1), (1, 1, 1, 1))
    stonetint.blend_type = 'MULTIPLY'
    L(nt, stone, 'Color', stonetint, 'Color1')
    L(nt, big, 'Color', stonetint, 'Color2')

    # ---- fine grain mottle ----
    gr = noise(nt, (-760, 250), 3.2, 9.0, 0.62, 0.4, pos)
    grain = mixrgb(nt, (-560, 400), 0.14, (0, 0, 0, 1), (1, 1, 1, 1))
    L(nt, gr, 'Fac', grain, 'Factor')

    # ---- dirt streaks (vertical, under ledges) ----
    streak_map = mapping(nt, (-1000, 100), pos, scale=(1.6, 1.6, 0.10))
    streak = noise(nt, (-820, 100), 2.4, 8.0, 0.7, 0.9, streak_map)
    sr = ramp(nt, (-640, 100), [(0.40, (0, 0, 0, 1)), (0.62, (1, 1, 1, 1))])
    L(nt, streak, 'Fac', sr, 'Factor')
    low = maprange(nt, (-460, 40), geo.outputs['Position'], 165.0, 95.0, 0.0, 1.0)
    sepp = sepxyz(nt, (-760, -60), pos)
    L(nt, sepp, 'Z', low, 'Value')
    dirtf = mathn(nt, (-280, 60), 'MULTIPLY', sr.outputs['Color'], low)
    dirtf2 = mathn(nt, (-120, 60), 'MULTIPLY', dirtf, 0.85)
    dirt = mixrgb(nt, (60, 300), 1.0, (0, 0, 0, 1), (0.20, 0.165, 0.125, 1))
    L(nt, stonetint, 'Color', dirt, 'Color1')
    L(nt, dirtf2, 'Value', dirt, 'Factor')

    # ---- per-block tonal variation ----
    if blk is not None:
        bv = mixrgb(nt, (240, 470), 1.0, (1, 1, 1, 1), (1, 1, 1, 1))
        bv.blend_type = 'MULTIPLY'
        L(nt, dirt, 'Color', bv, 'Color1')
        L(nt, blk, 'Color', bv, 'Color2')
        dirt = bv

    # ---- mortar darkening (lime mortar is darker than the weathered face) --
    mor = mixrgb(nt, (240, 300), 1.0, (0, 0, 0, 1), (0.150, 0.144, 0.130, 1))
    L(nt, dirt, 'Color', mor, 'Color1')
    mf = mathn(nt, (60, 120), 'MULTIPLY', mj, 0.88)
    L(nt, mf, 'Value', mor, 'Factor')

    # ---- edge wear (convex) ----
    pw = maprange(nt, (-760, -520), geo.outputs['Pointiness'], 0.52, 0.66, 0.0, 1.0)
    wear = mixrgb(nt, (420, 300), 1.0, (0, 0, 0, 1), (0.56, 0.53, 0.48, 1))
    L(nt, mor, 'Color', wear, 'Color1')
    L(nt, pw, 'Result', wear, 'Factor')

    # ---- moss (concave + low + damp) ----
    # Moss belongs in the damp crevices low down, not as a soft green wash
    # over the whole wall.  A wide Pointiness window plus a large-scale moss
    # noise painted a broad teal-green blob across the clock tower's face.
    conc = maprange(nt, (-760, -700), geo.outputs['Pointiness'], 0.40, 0.28, 0.0, 1.0)
    mossy = maprange(nt, (-580, -700), geo.outputs['Position'], 80.0, 62.0, 0.0, 1.0)
    sepp2 = sepxyz(nt, (-760, -840), pos)
    L(nt, sepp2, 'Z', mossy, 'Value')
    mossn = noise(nt, (-580, -900), 1.7, 7.0, 0.65, 0.5, pos)
    mr = ramp(nt, (-400, -900), [(0.42, (0, 0, 0, 1)), (0.60, (1, 1, 1, 1))])
    L(nt, mossn, 'Fac', mr, 'Factor')
    m1 = mathn(nt, (-200, -800), 'MULTIPLY', conc, mossy)
    m2 = mathn(nt, (-40, -800), 'MULTIPLY', m1, mr)
    m3 = mathn(nt, (120, -800), 'MULTIPLY', m2, 0.9)
    moss = mixrgb(nt, (600, 300), 1.0, (0, 0, 0, 1), (0.050, 0.064, 0.046, 1))
    L(nt, wear, 'Color', moss, 'Color1')
    L(nt, m3, 'Value', moss, 'Factor')

    # ---- global tint ----
    # MULTIPLY: moss * tint.  Color2 must hold the tint colour itself — never
    # this node's own output, which would create a dependency cycle (black).
    tintmix = mixrgb(nt, (760, 300), 1.0, (0, 0, 0, 1), tuple(tint) + (1,))
    tintmix.blend_type = 'MULTIPLY'
    L(nt, moss, 'Color', tintmix, 'Color1')

    # ---- very large scale weathering -------------------------------------
    # A wall 30 m across is a single flat value with only course lines on
    # it, and a horizontal deck is worse: the courses vanish and the whole
    # plane reads as a sheet of card.  A 50 m weathering field multiplied in
    # at the very end breaks any surface of that size into light and shade.
    wth = noise(nt, (420, 620), 0.020, 4.0, 0.60, 0.4, pos)
    wthr = ramp(nt, (600, 620), [(0.20, (0.66, 0.66, 0.69, 1)),
                                 (0.50, (0.94, 0.94, 0.96, 1)),
                                 (0.82, (1.16, 1.15, 1.11, 1))])
    L(nt, wth.outputs['Fac'], wthr, 'Factor')
    weather = mixrgb(nt, (760, 620), 1.0, (1, 1, 1, 1), (1, 1, 1, 1))
    weather.blend_type = 'MULTIPLY'
    L(nt, tintmix, 'Color', weather, 'Color1')
    L(nt, wthr, 'Color', weather, 'Color2')

    # ---- roughness ----
    r1 = mixrgb(nt, (420, -260), 1.0, (0.82, 0.82, 0.82, 1), (0.70, 0.70, 0.70, 1))
    L(nt, pw, 'Result', r1, 'Factor')
    r2 = mixrgb(nt, (600, -260), 1.0, (0, 0, 0, 1), (0.95, 0.95, 0.95, 1))
    L(nt, r1, 'Color', r2, 'Color1')
    L(nt, m3, 'Value', r2, 'Factor')
    rough = NN(nt, 'ShaderNodeMapRange', (760, -260))
    L(nt, r2, 'Color', rough, 'Value')
    rough.inputs['From Min'].default_value = 0.0
    rough.inputs['From Max'].default_value = 1.0
    rough.inputs['To Min'].default_value = 0.86
    rough.inputs['To Max'].default_value = 0.58

    # ---- bump ----
    coarse = noise(nt, (-200, -1200), 0.9, 8.0, 0.6, 0.6, pos)
    fine = noise(nt, (-200, -1400), 13.0, 10.0, 0.7, 0.3, pos)
    h1 = mathn(nt, (0, -1200), 'MULTIPLY', coarse, 0.55)
    h2 = mathn(nt, (0, -1400), 'MULTIPLY', fine, 0.22)
    h3 = mathn(nt, (180, -1300), 'ADD', h1, h2)
    jointneg = mathn(nt, (180, -1100), 'MULTIPLY', mj, -1.15)
    h4 = mathn(nt, (360, -1200), 'ADD', h3, jointneg)
    bump1 = NN(nt, 'ShaderNodeBump', (360, -1300))
    bump1.inputs['Strength'].default_value = 0.62
    bump1.inputs['Distance'].default_value = 0.060
    L(nt, h4, 'Value', bump1, 'Height')
    bump2 = NN(nt, 'ShaderNodeBump', (560, -1300))
    bump2.inputs['Strength'].default_value = 0.30
    bump2.inputs['Distance'].default_value = 0.006
    L(nt, fine, 'Fac', bump2, 'Height')
    L(nt, bump1, 'Normal', bump2, 'Normal')

    bsdf = NN(nt, 'ShaderNodeBsdfPrincipled', (760, 100))
    L(nt, weather, 'Color', bsdf, 'Base Color')
    L(nt, rough, 'Result', bsdf, 'Roughness')
    L(nt, bump2, 'Normal', bsdf, 'Normal')
    bsdf.inputs['Specular IOR Level'].default_value = 0.32
    L(nt, bsdf, 'BSDF', out, 'Surface')
    return m


def m_brick(name='M_Brick'):
    """Victorian red brick in English bond -- the dwarf walls of the
    cliff greenhouses.  Stone makes a glasshouse look like a chapel."""
    m, nt, out = newmat(name)
    geo = NN(nt, 'ShaderNodeNewGeometry', (-1500, 200))
    pos = geo.outputs['Position']
    tc = NN(nt, 'ShaderNodeTexCoord', (-1500, -300))
    obj = tc.outputs['Object']
    # the courses wander, so the bond is not a machine grid
    wn = noise(nt, (-1500, -820), 0.55, 3.0, 0.55, 0.0, obj)
    wsub = NN(nt, 'ShaderNodeVectorMath', (-1300, -820), operation='SUBTRACT')
    L(nt, wn.outputs['Color'], 'Vector', wsub, 0)
    wsub.inputs[1].default_value = (0.5, 0.5, 0.5)
    wsc = NN(nt, 'ShaderNodeVectorMath', (-1150, -820), operation='SCALE')
    L(nt, wsub.outputs['Vector'], 'Vector', wsc, 0)
    wsc.inputs['Scale'].default_value = 0.30
    wadd = NN(nt, 'ShaderNodeVectorMath', (-1000, -820), operation='ADD')
    L(nt, obj, 'Vector', wadd, 0)
    L(nt, wsc.outputs['Vector'], 'Vector', wadd, 1)
    wobj = wadd.outputs['Vector']
    vtr = NN(nt, 'ShaderNodeVectorTransform', (-1500, -560))
    vtr.vector_type = 'NORMAL'
    vtr.convert_from = 'WORLD'
    vtr.convert_to = 'OBJECT'
    L(nt, geo.outputs['Normal'], 'Vector', vtr, 'Vector')
    bw, rh = 0.225, 0.075
    col = triplanar_brick_color(nt, wobj, vtr.outputs['Vector'], bw, rh,
                                (0.0700, 0.0230, 0.0170, 1),
                                (0.1450, 0.0520, 0.0330, 1),
                                (0.0980, 0.0930, 0.0850, 1),
                                msize=0.009, msoft=0.028, bias=0.30,
                                loc=(-650, 600))
    mj = triplanar_masonry(nt, wobj, vtr.outputs['Vector'], bw, rh,
                           msize=0.009, msoft=0.028, loc=(-650, -300))
    # soot and weather staining, strongest low down
    low = maprange(nt, (-1100, 900), pos, 55.0, 46.0, 0.0, 1.0)
    sepz = sepxyz(nt, (-1300, 900), pos)
    L(nt, sepz, 'Z', low, 'Value')
    st = noise(nt, (-1100, 1100), 1.4, 6.0, 0.6, 0.4, pos)
    stf = mathn(nt, (-880, 1000), 'MULTIPLY', st.outputs['Fac'], low.outputs['Result'])
    sooty = mixrgb(nt, (-420, 600), 1.0, (1, 1, 1, 1), (0.62, 0.60, 0.58, 1))
    sooty.blend_type = 'MULTIPLY'
    L(nt, col, 'Vector', sooty, 'Color1')
    L(nt, stf.outputs['Value'], sooty, 'Factor')
    # mortar joint darkening
    mor = mixrgb(nt, (-200, 600), 1.0, (0, 0, 0, 1), (0.085, 0.080, 0.073, 1))
    L(nt, sooty, 'Color', mor, 'Color1')
    mf = mathn(nt, (-420, 400), 'MULTIPLY', mj, 0.85)
    L(nt, mf.outputs['Value'], mor, 'Factor')
    bsdf = NN(nt, 'ShaderNodeBsdfPrincipled', (300, 0))
    L(nt, mor, 'Color', bsdf, 'Base Color')
    bsdf.inputs['Roughness'].default_value = 0.90
    L(nt, bsdf, 'BSDF', out, 'Surface')
    return m


def m_greenhouse_glass(name='M_GreenhouseGlass'):
    """Cliff greenhouse glazing: cold dark panes with a warm interior glow
    leaking out of the lit bays.

    A plain transmissive glass would be black at night -- there is nothing
    behind it -- so the lit glasshouse has to carry its own emission, broken
    up bay by bay so it reads as rooms rather than as one orange panel.
    """
    m, nt, out = newmat(name)
    geo = NN(nt, 'ShaderNodeNewGeometry', (-1200, 0))
    pos = geo.outputs['Position']
    n = noise(nt, (-1000, 220), 0.22, 2.0, 0.55, 0.2, pos)
    lit = ramp(nt, (-780, 220), [(0.30, (0.0, 0.0, 0.0, 1)),
                                 (0.78, (1.0, 1.0, 1.0, 1))])
    L(nt, n.outputs['Fac'], lit, 'Factor')
    n2 = noise(nt, (-1000, -80), 0.9, 3.0, 0.5, 0.3, pos)
    lit2 = mathn(nt, (-560, 120), 'MULTIPLY', lit.outputs['Color'],
                  n2.outputs['Fac'])
    # Only a minority of the bays are lit, and dimly.  At full strength the
    # whole house read as one glowing cream lantern; at a high noise contrast
    # the panes read as camouflage blotches.  A soft, low gradient over a
    # dark pane lets the glazing bars stay legible and the sky reflect off
    # the roof.
    strength = maprange(nt, (-340, 120), lit2.outputs['Value'], 0.0, 1.0,
                        0.0, 0.48)
    bsdf = NN(nt, 'ShaderNodeBsdfPrincipled', (300, 0))
    bsdf.inputs['Base Color'].default_value = (0.014, 0.026, 0.032, 1)
    bsdf.inputs['Roughness'].default_value = 0.07
    L(nt, strength.outputs['Result'], bsdf, 'Emission Strength')
    bsdf.inputs['Emission Color'].default_value = (1.0, 0.56, 0.21, 1)
    L(nt, bsdf, 'BSDF', out, 'Surface')
    return m


def m_slate(name='M_Slate', col=(0.075, 0.090, 0.100)):
    m, nt, out = newmat(name)
    geo = NN(nt, 'ShaderNodeNewGeometry', (-1400, 400))
    # Slates are laid on the roof plane, so the tile grid must follow the
    # surface -- a single planar projection stretches into stripes on any
    # slope that is not aligned with it.
    bc = triplanar_brick_color(nt, geo.outputs['Position'], geo.outputs['Normal'],
                               0.42, 0.20, (col[0], col[1], col[2], 1),
                               (col[0] * 1.55, col[1] * 1.5, col[2] * 1.45, 1),
                               (0.035, 0.042, 0.048, 1), msize=0.03, msoft=0.05,
                               bias=0.15, offset=0.5, loc=(-800, 0))
    mj = triplanar_masonry(nt, geo.outputs['Position'], geo.outputs['Normal'],
                           0.42, 0.20, msize=0.03, msoft=0.05,
                           loc=(-800, -900))
    mott = noise(nt, (-800, 400), 1.6, 8.0, 0.6, 0.4, geo.outputs['Position'])
    # mottle MODULATES the brick colour -- mixing it toward white washed
    # the whole masonry out into flat plaster
    c2 = shade_modulate(nt, (-380, 250), bc, mott.outputs['Fac'],
                        lo=0.80, hi=1.24)
    # weathering / lichen
    lich = noise(nt, (-800, 700), 2.6, 7.0, 0.6, 0.3, geo.outputs['Position'])
    lr = ramp(nt, (-600, 700), [(0.55, (0, 0, 0, 1)), (0.75, (1, 1, 1, 1))])
    L(nt, lich, 'Fac', lr, 'Factor')
    c3 = mixrgb(nt, (-200, 250), 1.0, (0, 0, 0, 1), (0.085, 0.100, 0.070, 1))
    L(nt, c2, 'Vector', c3, 'Color1')
    L(nt, lr, 'Color', c3, 'Factor')
    c3.inputs['Factor'].default_value = 0.35
    rough = maprange(nt, (100, -100), mott, 0.0, 1.0, 0.78, 0.52)
    bump1 = NN(nt, 'ShaderNodeBump', (300, -400))
    bump1.inputs['Strength'].default_value = 0.5
    bump1.inputs['Distance'].default_value = 0.02
    jneg = mathn(nt, (100, -400), 'MULTIPLY', mj, -0.9)
    L(nt, jneg, 'Value', bump1, 'Height')
    bump2 = NN(nt, 'ShaderNodeBump', (480, -400))
    bump2.inputs['Strength'].default_value = 0.25
    bump2.inputs['Distance'].default_value = 0.005
    L(nt, mott, 'Fac', bump2, 'Height')
    L(nt, bump1, 'Normal', bump2, 'Normal')
    bsdf = NN(nt, 'ShaderNodeBsdfPrincipled', (760, 100))
    L(nt, c3, 'Color', bsdf, 'Base Color')
    L(nt, rough, 'Result', bsdf, 'Roughness')
    L(nt, bump2, 'Normal', bsdf, 'Normal')
    bsdf.inputs['Specular IOR Level'].default_value = 0.42
    L(nt, bsdf, 'BSDF', out, 'Surface')
    return m


def m_verdigris(name='M_Verdigris'):
    m, nt, out = newmat(name)
    geo = NN(nt, 'ShaderNodeNewGeometry', (-900, 200))
    n1 = noise(nt, (-700, 200), 2.2, 9.0, 0.62, 0.5, geo.outputs['Position'])
    r = ramp(nt, (-480, 200), [(0.30, (0.055, 0.115, 0.095, 1)),
                               (0.55, (0.135, 0.290, 0.245, 1)),
                               (0.80, (0.235, 0.400, 0.330, 1))])
    L(nt, n1, 'Fac', r, 'Factor')
    n2 = noise(nt, (-700, -150), 14.0, 8.0, 0.6, 0.2, geo.outputs['Position'])
    bump = NN(nt, 'ShaderNodeBump', (300, -300))
    bump.inputs['Strength'].default_value = 0.3
    bump.inputs['Distance'].default_value = 0.01
    L(nt, n2, 'Fac', bump, 'Height')
    bsdf = NN(nt, 'ShaderNodeBsdfPrincipled', (700, 0))
    L(nt, r, 'Color', bsdf, 'Base Color')
    bsdf.inputs['Metallic'].default_value = 0.25
    bsdf.inputs['Roughness'].default_value = 0.62
    L(nt, bump, 'Normal', bsdf, 'Normal')
    L(nt, bsdf, 'BSDF', out, 'Surface')
    return m


def m_lead(name='M_Lead'):
    m, nt, out = newmat(name)
    geo = NN(nt, 'ShaderNodeNewGeometry', (-800, 0))
    n1 = noise(nt, (-600, 0), 22.0, 8.0, 0.6, 0.3, geo.outputs['Position'])
    bump = NN(nt, 'ShaderNodeBump', (100, -200))
    bump.inputs['Strength'].default_value = 0.25
    bump.inputs['Distance'].default_value = 0.004
    L(nt, n1, 'Fac', bump, 'Height')
    bsdf = NN(nt, 'ShaderNodeBsdfPrincipled', (700, 0))
    bsdf.inputs['Base Color'].default_value = (0.022, 0.023, 0.026, 1)
    bsdf.inputs['Metallic'].default_value = 0.85
    bsdf.inputs['Roughness'].default_value = 0.48
    L(nt, bump, 'Normal', bsdf, 'Normal')
    L(nt, bsdf, 'BSDF', out, 'Surface')
    return m


def m_window_glass(name='M_WindowGlass', warm=(1.0, 0.55, 0.18), max_strength=11.0,
                   lit_frac=0.70):
    """Emissive window: per-window brightness, some rooms dark.

    The randomness is driven by each window's own world position, not by
    Object Info > Random.  With ~480 separately placed window objects the
    object random proved to be tightly clustered, so almost every window
    fell under the "lit" threshold and the castle read as dead.  A 4D noise
    over the position -- with the object random as the W channel, so
    neighbouring windows never collide -- gives a reliable spread.
    """
    m, nt, out = newmat(name)
    # One value per window object, constant across the pane.  Object Info >
    # Random proved tightly clustered across ~480 window objects, so the
    # golden-ratio hash of the object index is used instead: consecutive
    # indices land on well-separated values, and every window keeps the
    # same value over its whole surface (no blotches across the glass).
    oi = NN(nt, 'ShaderNodeObjectInfo', (-1400, 320))
    g = mathn(nt, (-1200, 320), 'MULTIPLY', oi.outputs['Object Index'],
              0.6180339887498949)
    rnd = mathn(nt, (-1020, 320), 'FRACT', g)

    # colour variation (candle -> firelight -> gaslight)
    cr = ramp(nt, (-560, 380), [(0.22, (1.0, 0.30, 0.055, 1)),
                                (0.45, (1.0, 0.47, 0.120, 1)),
                                (0.68, (1.0, 0.64, 0.260, 1)),
                                (0.88, (1.0, 0.76, 0.420, 1))])
    L(nt, rnd, 'Value', cr, 'Factor')
    # lit mask
    lit = maprange(nt, (-560, 120), rnd, 1.0 - lit_frac,
                   1.0 - lit_frac + 0.08, 0.0, 1.0)
    # brightness -- a wide spread so no two windows read the same
    amp = maprange(nt, (-560, -120), rnd, 1.0 - lit_frac, 1.0, 0.14, 1.0)
    st = mathn(nt, (-340, -120), 'MULTIPLY', amp.outputs['Result'], max_strength)
    st2 = mathn(nt, (-180, -120), 'MULTIPLY', st.outputs['Value'],
                lit.outputs['Result'])
    bsdf = NN(nt, 'ShaderNodeBsdfPrincipled', (400, 100))
    # dark blue-grey glass: an unlit pane must still read as glass catching
    # the sky, never as a black hole punched in the wall
    bsdf.inputs['Base Color'].default_value = (0.021, 0.030, 0.042, 1)
    bsdf.inputs['Roughness'].default_value = 0.11
    bsdf.inputs['IOR'].default_value = 1.52
    L(nt, cr, 'Color', bsdf, 'Emission Color')
    L(nt, st2, 'Value', bsdf, 'Emission Strength')
    L(nt, bsdf, 'BSDF', out, 'Surface')
    return m


def m_boathouse_glass(name='M_BoathouseGlass'):
    """The boat door's glazing: a big warm lamp seen through dirty glass.

    A 6 x 9 m pane at a single flat emission strength reads as a yellow
    slab pasted on the wall.  This one is graded down the opening -- bright
    at the sill where the lamp inside the boat house sits, dimmer towards
    the head of the arch -- and broken up with a slow noise so the light
    looks like it is coming through a room rather than off a lightbulb.
    """
    m, nt, out = newmat(name)
    tc = NN(nt, 'ShaderNodeTexCoord', (-1400, 0))
    sep = NN(nt, 'ShaderNodeSeparateXYZ', (-1200, 0))
    # Generated is the bounding-box normalised position, so Z runs 0 at the
    # sill and 1 at the head of the arch whatever the opening's size.
    L(nt, tc.outputs['Generated'], sep, 'Vector')
    grad = maprange(nt, (-1000, 120), sep.outputs['Z'], 0.03, 0.92, 0.78, 0.085)
    nz = noise(nt, (-1200, -220), 1.1, 1.0, 0.62, 0.45, tc.outputs['Object'])
    nzr = maprange(nt, (-1000, -220), nz.outputs['Fac'], 0.28, 0.72, 0.70, 1.26)
    st = mathn(nt, (-760, 0), 'MULTIPLY', grad.outputs['Result'],
               nzr.outputs['Result'])
    bsdf = NN(nt, 'ShaderNodeBsdfPrincipled', (300, 0))
    bsdf.inputs['Base Color'].default_value = (0.030, 0.022, 0.014, 1)
    bsdf.inputs['Roughness'].default_value = 0.16
    bsdf.inputs['IOR'].default_value = 1.52
    bsdf.inputs['Emission Color'].default_value = (1.0, 0.50, 0.16, 1)
    L(nt, st.outputs['Value'], bsdf, 'Emission Strength')
    L(nt, bsdf, 'BSDF', out, 'Surface')
    return m


def m_rock(name='M_Rock'):
    """Stratified crag granite: banded layers, pitting, lichen, wet waterline."""
    m, nt, out = newmat(name)
    geo = NN(nt, 'ShaderNodeNewGeometry', (-1500, 200))
    pos = geo.outputs['Position']
    sep = sepxyz(nt, (-1300, 300), pos)
    # strata: bands along Z, distorted.  The mapping compresses Z by 9x, so a
    # wave scale of 0.5 gives a bedding plane every ~18 m of real height.
    # The bedding planes are broad and irregular.  A tight saw-tooth band at
    # 5 m spacing lined up with the geometry's ledges and the cliff read as
    # stacked masonry courses instead of rock.
    wmap = mapping(nt, (-1300, 60), pos, scale=(1.0, 1.0, 0.075))
    w = NN(nt, 'ShaderNodeTexWave', (-1100, 60), wave_type='BANDS',
           bands_direction='Z', wave_profile='SAW')
    w.inputs['Scale'].default_value = 0.62
    w.inputs['Distortion'].default_value = 2.6
    w.inputs['Detail'].default_value = 2.0
    w.inputs['Detail Scale'].default_value = 1.8
    L(nt, wmap, 'Vector', w, 'Vector')
    sr = ramp(nt, (-880, 60), [(0.12, (0.1350, 0.1270, 0.1130, 1)),
                               (0.40, (0.1950, 0.1810, 0.1530, 1)),
                               (0.66, (0.3050, 0.2830, 0.2340, 1)),
                               (0.88, (0.1600, 0.1490, 0.1270, 1)),
                               (1.00, (0.2300, 0.2130, 0.1780, 1))])
    L(nt, w, 'Fac', sr, 'Factor')
    # blocky fracture: voronoi distance-to-edge.  The cells are stretched
    # vertically (the mapping squashes Z) so they read as the big joint
    # planes that split a crag face, instead of the crazed-mud pattern
    # isotropic Voronoi cells produce.  The scale is deliberately coarse:
    # small cells make the cliff look like a rubble wall.
    vmap = mapping(nt, (-1480, 600), pos, scale=(1.0, 1.0, 0.62))
    # The joint pattern must not be a tidy polygon grid.  An unwarped
    # Voronoi gives straight-edged cells, and on a cliff that reads as a
    # stack of masonry blocks; a slow warp of the lookup coordinate turns
    # the cells into irregular, interlocking joint planes.
    wn = noise(nt, (-1480, 900), 0.032, 4.0, 0.55, 0.3, pos)
    wsub = NN(nt, 'ShaderNodeVectorMath', (-1300, 900), operation='SUBTRACT')
    L(nt, wn.outputs['Color'], 'Vector', wsub, 0)
    wsub.inputs[1].default_value = (0.5, 0.5, 0.5)
    wsc = NN(nt, 'ShaderNodeVectorMath', (-1150, 900), operation='SCALE')
    L(nt, wsub.outputs['Vector'], 'Vector', wsc, 0)
    wsc.inputs['Scale'].default_value = 11.0
    vw = NN(nt, 'ShaderNodeVectorMath', (-1000, 900), operation='ADD')
    L(nt, vmap.outputs['Vector'], 'Vector', vw, 0)
    L(nt, wsc.outputs['Vector'], 'Vector', vw, 1)
    ve = voronoi(nt, (-1300, 600), 0.048, 1.0, 'DISTANCE_TO_EDGE',
                 vw.outputs['Vector'])
    vr = ramp(nt, (-1080, 600), [(0.0, (0, 0, 0, 1)), (0.105, (1, 1, 1, 1))])
    L(nt, ve, 'Distance', vr, 'Factor')
    # --- secondary joint network -------------------------------------------
    # A real crag breaks at two or three scales.  The big Voronoi above gives
    # the major joint planes; without a finer network every block stays one
    # unbroken surface and the cliff reads as smooth pillows of rock.
    wn2 = noise(nt, (-1480, 1260), 0.085, 3.0, 0.50, 0.30, pos)
    wsub2 = NN(nt, 'ShaderNodeVectorMath', (-1300, 1260), operation='SUBTRACT')
    L(nt, wn2.outputs['Color'], 'Vector', wsub2, 0)
    wsub2.inputs[1].default_value = (0.5, 0.5, 0.5)
    wsc2 = NN(nt, 'ShaderNodeVectorMath', (-1150, 1260), operation='SCALE')
    L(nt, wsub2.outputs['Vector'], 'Vector', wsc2, 0)
    wsc2.inputs['Scale'].default_value = 6.5
    vw2 = NN(nt, 'ShaderNodeVectorMath', (-1000, 1260), operation='ADD')
    L(nt, vmap.outputs['Vector'], 'Vector', vw2, 0)
    L(nt, wsc2.outputs['Vector'], 'Vector', vw2, 1)
    ve2 = voronoi(nt, (-1300, 1260), 0.115, 1.0, 'DISTANCE_TO_EDGE',
                  vw2.outputs['Vector'])
    vr2 = ramp(nt, (-1080, 1260), [(0.0, (0, 0, 0, 1)), (0.072, (1, 1, 1, 1))])
    L(nt, ve2, 'Distance', vr2, 'Factor')
    # a joint in either network counts as a joint
    vrc = mathn(nt, (-900, 380), 'MULTIPLY', vr.outputs['Color'],
                vr2.outputs['Color'])
    # `vr` is 1 in the CELL INTERIOR and 0 on the fracture line, so the rock
    # colour has to land on Color2 and the dark crack on Color1.  Wired the
    # other way round the fracture came out INVERTED: the cliff rendered as
    # near-black polygons separated by bright seams, and the whole crag came
    # out ~20x darker than the castle masonry (measured: 0.003 linear vs
    # 0.09), which is what turned the promontory into a featureless slab.
    frac = mixrgb(nt, (-820, 500), 1.0, (0.048, 0.044, 0.039, 1), (0, 0, 0, 1))
    L(nt, sr, 'Color', frac, 'Color2')
    L(nt, vrc, 'Value', frac, 'Factor')
    # fine noise
    nz = noise(nt, (-820, 760), 1.9, 10.0, 0.62, 0.5, pos)
    # the fine noise modulates the rock; mixing it to white turned the
    # crag into flat TV static
    c2 = shade_modulate(nt, (-400, 500), frac, nz.outputs['Fac'],
                        lo=0.70, hi=1.38)
    # --- per-block tone ----------------------------------------------------
    # The Voronoi F1 cell id is a random number per block.  Tinting each
    # block by its own value is what stops the cliff reading as one
    # continuous melted mass: the eye has to see separate stones.  The same
    # random number also becomes a per-block height offset further down.
    vcell = voronoi(nt, (-1300, 1560), 0.048, 1.0, 'F1', vw.outputs['Vector'])
    csep = sepxyz(nt, (-1100, 1560), vcell.outputs['Color'])
    cblk = maprange(nt, (-900, 1560), csep.outputs['X'], 0.10, 0.90, 0.70, 1.32)
    cvec = combxyz(nt, (-760, 1560), cblk.outputs['Result'],
                   cblk.outputs['Result'], cblk.outputs['Result'])
    c2b = mixrgb(nt, (-560, 500), 1.0, (1, 1, 1, 1), (1, 1, 1, 1))
    c2b.blend_type = 'MULTIPLY'
    L(nt, c2, 'Vector', c2b, 'Color1')
    L(nt, cvec, 'Vector', c2b, 'Color2')
    # lichen / moss on upper + crevices
    pw = maprange(nt, (-600, 900), geo.outputs['Pointiness'], 0.49, 0.36, 0.0, 1.0)
    hgt = maprange(nt, (-600, 1060), sep.outputs['Z'], 120.0, 30.0, 0.0, 1.0)
    mossn = noise(nt, (-820, 1200), 0.5, 7.0, 0.65, 0.6, pos)
    mr = ramp(nt, (-600, 1200), [(0.46, (0, 0, 0, 1)), (0.62, (1, 1, 1, 1))])
    L(nt, mossn, 'Fac', mr, 'Factor')
    m1 = mathn(nt, (-360, 1000), 'MULTIPLY', pw, hgt)
    m2 = mathn(nt, (-200, 1000), 'MULTIPLY', m1, mr)
    m3 = mathn(nt, (-40, 1000), 'MULTIPLY', m2, 1.0)
    moss = mixrgb(nt, (-200, 500), 1.0, (0, 0, 0, 1), (0.045, 0.062, 0.032, 1))
    L(nt, c2b, 'Color', moss, 'Color1')
    L(nt, m3, 'Value', moss, 'Factor')
    # wet band at the waterline
    wet = maprange(nt, (-200, 760), sep.outputs['Z'], 6.0, -1.5, 0.0, 1.0)
    wetc = mixrgb(nt, (60, 500), 1.0, (0, 0, 0, 1), (0.016, 0.020, 0.021, 1))
    L(nt, moss, 'Color', wetc, 'Color1')
    L(nt, wet, 'Result', wetc, 'Factor')
    rough = maprange(nt, (260, 760), wet, 0.0, 1.0, 0.88, 0.34)
    # bump
    h1 = noise(nt, (260, 300), 6.0, 12.0, 0.68, 0.6, pos)
    h1 = mathn(nt, (260, 160), 'ADD', h1,
               mathn(nt, (260, 40), 'MULTIPLY', w.outputs['Fac'], 0.55))
    # the grooves run along the FRACTURE lines, so the bump needs (1 - vr);
    # using vr put a groove in the middle of every rock face instead
    vinv = mathn(nt, (420, 380), 'SUBTRACT', 1.0, vr)
    h2 = mathn(nt, (420, 300), 'MULTIPLY', vinv, -0.62)
    # the secondary joints get their own, narrower groove
    v2inv = mathn(nt, (420, 180), 'SUBTRACT', 1.0, vr2)
    h2b = mathn(nt, (560, 180), 'MULTIPLY', v2inv, -0.30)
    # Each block sits at its own level.  A per-cell constant in the height
    # field puts a hard step exactly along the joint lines, and that step is
    # what turns a smooth mass into stacked, fractured slabs.
    chgt = maprange(nt, (560, 1560), csep.outputs['X'], 0.0, 1.0, -0.08, 0.08)
    h3 = mathn(nt, (560, 300), 'ADD', h1, h2)
    h3 = mathn(nt, (640, 240), 'ADD', h3, h2b)
    h4 = mathn(nt, (700, 180), 'ADD', h3, chgt)
    bump = NN(nt, 'ShaderNodeBump', (820, 200))
    bump.inputs['Strength'].default_value = 0.82
    bump.inputs['Distance'].default_value = 0.19
    L(nt, h4, 'Value', bump, 'Height')
    bump2 = NN(nt, 'ShaderNodeBump', (900, 200))
    bump2.inputs['Strength'].default_value = 0.45
    bump2.inputs['Distance'].default_value = 0.045
    L(nt, nz, 'Fac', bump2, 'Height')
    L(nt, bump, 'Normal', bump2, 'Normal')
    bsdf = NN(nt, 'ShaderNodeBsdfPrincipled', (1000, 100))
    L(nt, wetc, 'Color', bsdf, 'Base Color')
    L(nt, rough, 'Result', bsdf, 'Roughness')
    L(nt, bump2, 'Normal', bsdf, 'Normal')
    bsdf.inputs['Specular IOR Level'].default_value = 0.4
    L(nt, bsdf, 'BSDF', out, 'Surface')
    return m


def m_terrain(name='M_Terrain'):
    """Moorland: heather, peat, dark forest floor, exposed rock on slopes.

    The "ground" colour attribute carries (forest density, rockiness, 0).
    The forest channel matches the tree scatter exactly, so the dark canopy
    mass and the individual conifers always agree.
    """
    m, nt, out = newmat(name)
    geo = NN(nt, 'ShaderNodeNewGeometry', (-1600, 200))
    pos = geo.outputs['Position']
    attr = NN(nt, 'ShaderNodeVertexColor', (-1600, -320))
    attr.layer_name = "ground"
    sep = NN(nt, 'ShaderNodeSeparateXYZ', (-1400, -320))
    L(nt, attr, 'Color', sep, 'Vector')
    # slope -> rock
    nrm = geo.outputs['Normal']
    sepn = sepxyz(nt, (-1300, -60), nrm)
    slope = maprange(nt, (-1100, -60), sepn.outputs['Z'], 0.97, 0.70, 0.0, 1.0)
    # heath / peat
    hn = noise(nt, (-1300, 520), 0.075, 8.0, 0.62, 0.5, pos)
    # Moorland albedo is deliberately very low: wet peat, heather and dark
    # rock at night.  At the previous values the ground rendered BRIGHTER
    # than the night sky and the whole landscape read as a snowfield.
    hr = ramp(nt, (-1080, 520), [(0.26, (0.0420, 0.0465, 0.0300, 1)),
                                 (0.50, (0.0670, 0.0670, 0.0370, 1)),
                                 (0.74, (0.0890, 0.0795, 0.0448, 1))])
    L(nt, hn, 'Fac', hr, 'Factor')
    # forest floor: dark, cool, needle-littered
    fn = noise(nt, (-1300, 260), 0.30, 8.0, 0.60, 0.5, pos)
    fr = ramp(nt, (-1080, 260), [(0.28, (0.0082, 0.0134, 0.0093, 1)),
                                 (0.72, (0.0210, 0.0292, 0.0165, 1))])
    L(nt, fn, 'Fac', fr, 'Factor')
    # heath <-> forest floor
    base = mixrgb(nt, (-860, 420), 0.5, (0, 0, 0, 1), (0, 0, 0, 1))
    L(nt, hr, 'Color', base, 'Color1')
    L(nt, fr, 'Color', base, 'Color2')
    L(nt, sep.outputs['X'], base, 'Factor')
    # exposed rock: on steep slopes and where the rockiness attribute is high
    rockn = noise(nt, (-1300, 800), 0.45, 10.0, 0.65, 0.6, pos)
    rockc = mixrgb(nt, (-860, 800), 1.0, (0.0470, 0.0455, 0.0425, 1),
                    (0.1010, 0.0970, 0.0895, 1))
    L(nt, rockn, 'Fac', rockc, 'Factor')
    rockmask = mathn(nt, (-1080, -320), 'ADD', slope, sep.outputs['Y'])
    rockmask = maprange(nt, (-880, -320), rockmask, 0.35, 1.05, 0.0, 1.0)
    rk = mixrgb(nt, (-660, 650), 1.0, (0, 0, 0, 1), (1, 1, 1, 1))
    L(nt, base, 'Color', rk, 'Color1')
    L(nt, rockc, 'Color', rk, 'Color2')
    L(nt, rockmask, 'Result', rk, 'Factor')
    # fine detail
    fn2 = noise(nt, (-460, 400), 2.2, 10.0, 0.68, 0.5, pos)
    # fine detail modulates the ground colour -- mixing it toward white was
    # lifting the whole moorland to a flat pale grey that read as snowfield
    cfin = shade_modulate(nt, (-60, 650), rk, fn2.outputs['Fac'],
                          lo=0.72, hi=1.32)
    rough = maprange(nt, (140, 400), fn2, 0.0, 1.0, 0.94, 0.80)
    bump = NN(nt, 'ShaderNodeBump', (500, 200))
    bump.inputs['Strength'].default_value = 0.6
    bump.inputs['Distance'].default_value = 0.10
    L(nt, fn2, 'Fac', bump, 'Height')
    bump2 = NN(nt, 'ShaderNodeBump', (700, 200))
    bump2.inputs['Strength'].default_value = 0.32
    bump2.inputs['Distance'].default_value = 0.025
    L(nt, rockn, 'Fac', bump2, 'Height')
    L(nt, bump, 'Normal', bump2, 'Normal')
    bsdf = NN(nt, 'ShaderNodeBsdfPrincipled', (1000, 100))
    L(nt, cfin, 'Vector', bsdf, 'Base Color')
    L(nt, rough, 'Result', bsdf, 'Roughness')
    L(nt, bump2, 'Normal', bsdf, 'Normal')
    bsdf.inputs['Specular IOR Level'].default_value = 0.12
    L(nt, bsdf, 'BSDF', out, 'Surface')
    return m


def m_foliage(name='M_Foliage'):
    m, nt, out = newmat(name)
    geo = NN(nt, 'ShaderNodeNewGeometry', (-1000, 200))
    pos = geo.outputs['Position']
    n1 = noise(nt, (-760, 200), 1.4, 8.0, 0.6, 0.4, pos)
    r = ramp(nt, (-520, 200), [(0.25, (0.0075, 0.0165, 0.0105, 1)),
                               (0.50, (0.0140, 0.0290, 0.0165, 1)),
                               (0.75, (0.0230, 0.0430, 0.0225, 1))])
    L(nt, n1, 'Fac', r, 'Factor')
    n2 = noise(nt, (-760, -100), 24.0, 9.0, 0.65, 0.3, pos)
    bump = NN(nt, 'ShaderNodeBump', (300, -200))
    bump.inputs['Strength'].default_value = 0.4
    bump.inputs['Distance'].default_value = 0.03
    L(nt, n2, 'Fac', bump, 'Height')
    bsdf = NN(nt, 'ShaderNodeBsdfPrincipled', (700, 0))
    L(nt, r, 'Color', bsdf, 'Base Color')
    bsdf.inputs['Roughness'].default_value = 0.82
    bsdf.inputs['Sheen Weight'].default_value = 0.12
    L(nt, bump, 'Normal', bsdf, 'Normal')
    L(nt, bsdf, 'BSDF', out, 'Surface')
    return m


def m_bark(name='M_Bark'):
    m, nt, out = newmat(name)
    geo = NN(nt, 'ShaderNodeNewGeometry', (-900, 0))
    pos = geo.outputs['Position']
    wm = mapping(nt, (-700, 0), pos, scale=(5.0, 5.0, 0.55))
    w = NN(nt, 'ShaderNodeTexWave', (-500, 0), wave_type='BANDS',
           bands_direction='X', wave_profile='SIN')
    w.inputs['Scale'].default_value = 2.6
    w.inputs['Distortion'].default_value = 8.0
    w.inputs['Detail'].default_value = 5.0
    L(nt, wm, 'Vector', w, 'Vector')
    r = ramp(nt, (-280, 0), [(0.20, (0.014, 0.011, 0.009, 1)),
                              (0.60, (0.040, 0.033, 0.026, 1)),
                              (0.90, (0.058, 0.048, 0.038, 1))])
    L(nt, w, 'Fac', r, 'Factor')
    bump = NN(nt, 'ShaderNodeBump', (200, -260))
    bump.inputs['Strength'].default_value = 0.6
    bump.inputs['Distance'].default_value = 0.03
    L(nt, w, 'Fac', bump, 'Height')
    bsdf = NN(nt, 'ShaderNodeBsdfPrincipled', (700, 0))
    L(nt, r, 'Color', bsdf, 'Base Color')
    bsdf.inputs['Roughness'].default_value = 0.9
    L(nt, bump, 'Normal', bsdf, 'Normal')
    L(nt, bsdf, 'BSDF', out, 'Surface')
    return m


def m_wood(name='M_Wood', col=(0.052, 0.036, 0.023)):
    m, nt, out = newmat(name)
    tc = NN(nt, 'ShaderNodeTexCoord', (-900, 0))
    sep = sepxyz(nt, (-720, 0), tc.outputs['Object'])
    mu = combxyz(nt, (-560, 0), sep.outputs['X'], sep.outputs['Y'])
    w = NN(nt, 'ShaderNodeTexWave', (-400, 0), wave_type='BANDS',
           bands_direction='X', wave_profile='SAW')
    w.inputs['Scale'].default_value = 3.2
    w.inputs['Distortion'].default_value = 3.0
    w.inputs['Detail'].default_value = 3.0
    L(nt, mu, 'Vector', w, 'Vector')
    r = ramp(nt, (-180, 0), [(0.10, (col[0] * 0.55, col[1] * 0.55, col[2] * 0.55, 1)),
                              (0.55, (col[0], col[1], col[2], 1)),
                              (1.00, (col[0] * 1.7, col[1] * 1.7, col[2] * 1.7, 1))])
    L(nt, w, 'Fac', r, 'Factor')
    bump = NN(nt, 'ShaderNodeBump', (200, -260))
    bump.inputs['Strength'].default_value = 0.45
    bump.inputs['Distance'].default_value = 0.012
    L(nt, w, 'Fac', bump, 'Height')
    bsdf = NN(nt, 'ShaderNodeBsdfPrincipled', (700, 0))
    L(nt, r, 'Color', bsdf, 'Base Color')
    bsdf.inputs['Roughness'].default_value = 0.78
    L(nt, bump, 'Normal', bsdf, 'Normal')
    L(nt, bsdf, 'BSDF', out, 'Surface')
    return m


def m_rose_glass(name='M_RoseGlass'):
    """Stained glass for the great rose window: a mosaic of leaded panels.

    The rose window used the ordinary window glass, and because every
    window is one object with one random value the whole seven metre disc
    came out as a single flat saturated orange decal pasted on the wall.
    A rose window is a patchwork of coloured panels, so this one is built
    from the polar coordinates of the opening.

    Four things have to be right for that to come out as a rose window and
    not as a test pattern:

    * The disc is built in the XZ plane -- every window profile in this
      library is an (x, z) polygon extruded through Y -- so the polar
      coordinates have to be taken from X and Z.  Reading Y instead meant
      the "angle" was measured across the thickness of the glass, and the
      whole window came out as vertical rainbow stripes.
    * The panel grid has to agree with the TRACERY.  The glass had twelve
      sectors while the stonework has eight principal spokes, so the
      colours ran across the stone instead of with it, and the window read
      as a pinwheel.  There are eight sectors here, phased so their edges
      land exactly on the spokes, and each is cut into three lights.
    * The panels have to be SMALL.  Sixteen concentric rings times eight
      sectors times three lights is nearly two hundred pieces of glass.
    * The colour has to be a property of the PANEL, not of the position
      inside it, and it has to be WEIGHTED.  A palette of eight evenly
      spaced primaries gave every eighth panel a different primary and
      the window came out as a colour wheel.  Medieval glass is mostly
      cobalt and ruby with a little amber and green, so the ramp is
      weighted towards the blues and the reds.
    """
    m, nt, out = newmat(name)
    tc = NN(nt, 'ShaderNodeTexCoord', (-2200, 0))
    sep = NN(nt, 'ShaderNodeSeparateXYZ', (-2020, 0))
    L(nt, tc.outputs['Generated'], 'Vector', sep, 'Vector')
    cx = mathn(nt, (-1840, 160), 'SUBTRACT', sep.outputs['X'], 0.5)
    cy = mathn(nt, (-1840, -40), 'SUBTRACT', sep.outputs['Z'], 0.5)
    x2 = mathn(nt, (-1660, 160), 'POWER', cx, 2.0)
    y2 = mathn(nt, (-1660, -40), 'POWER', cy, 2.0)
    ss = mathn(nt, (-1480, 60), 'ADD', x2, y2)
    rad = mathn(nt, (-1300, 60), 'SQRT', ss)
    ang = mathn(nt, (-1300, -220), 'ARCTAN2', cy, cx)
    # --- the panel grid ---------------------------------------------------
    # Eight sectors, phased so that their edges fall on the eight principal
    # spokes of the stone tracery (the spokes sit at 2*pi*i/8 + pi/8).
    ang01 = mathn(nt, (-1120, -220), 'MULTIPLY_ADD', ang, 0.15915494, -0.0625)
    sectf = mathn(nt, (-940, -220), 'MULTIPLY', ang01, 8.0)
    secti = mathn(nt, (-760, -360), 'FLOOR', sectf)
    sf = mathn(nt, (-760, -220), 'FRACT', sectf)
    # sixteen concentric rings
    ringf = mathn(nt, (-940, 60), 'MULTIPLY', rad, 16.0)
    ringi = mathn(nt, (-760, 60), 'FLOOR', ringf)
    rf = mathn(nt, (-760, 240), 'FRACT', ringf)
    # three lights inside every sector
    subf = mathn(nt, (-580, -220), 'MULTIPLY', sf, 3.0)
    subi = mathn(nt, (-400, -360), 'FLOOR', subf)
    subfr = mathn(nt, (-400, -220), 'FRACT', subf)
    # --- one identity per panel ------------------------------------------
    a1 = mathn(nt, (-220, -460), 'MULTIPLY', ringi, 24.0)
    a2 = mathn(nt, (-40, -460), 'MULTIPLY', secti, 3.0)
    a3 = mathn(nt, (140, -460), 'ADD', a1, a2)
    idx = mathn(nt, (320, -460), 'ADD', a3, subi)
    h1 = mathn(nt, (500, -460), 'MULTIPLY', idx, 12.9898)
    h2 = mathn(nt, (680, -460), 'SINE', h1)
    h3 = mathn(nt, (860, -460), 'MULTIPLY', h2, 43758.5453)
    h4 = mathn(nt, (1040, -460), 'FRACT', h3)
    # The middle of a rose window is a deep cool field, not a bag of
    # sweets: the inner rings are biased into the blue end of the palette,
    # and the outer field -- by far the biggest area -- keeps the full
    # weighted palette, so the window reads as a mosaic of blue, ruby and
    # pale glass rather than as one blue field with a jewel in the middle.
    inner = maprange(nt, (320, -700), ringi, 1.0, 3.0, 0.0, 1.0)
    hscale = mathn(nt, (500, -700), 'MULTIPLY_ADD', inner, 0.70, 0.30)
    hcol = mathn(nt, (1220, -460), 'MULTIPLY', h4, hscale)
    glass = ramp(nt, (1400, -320),
                 [(0.00, (0.0180, 0.0330, 0.2000, 1)),
                  (0.14, (0.0260, 0.0520, 0.2900, 1)),
                  (0.30, (0.0420, 0.0760, 0.2600, 1)),
                  (0.41, (0.2600, 0.0240, 0.0300, 1)),
                  (0.53, (0.3300, 0.0700, 0.0350, 1)),
                  (0.67, (0.3000, 0.2700, 0.2000, 1)),
                  (0.81, (0.3200, 0.2100, 0.0500, 1)),
                  (0.91, (0.0300, 0.1100, 0.0550, 1)),
                  (1.00, (0.0250, 0.0900, 0.1150, 1))], interp='CONSTANT')
    L(nt, hcol, 'Value', glass, 'Factor')
    # --- the lead cames ----------------------------------------------------
    # Real stained glass is a mosaic held together by dark lead lines, and
    # without them the coloured pieces run into one another and the window
    # reads as a painted disc.  The distance to the nearest panel edge
    # darkens the glass to almost nothing.
    rf2 = mathn(nt, (-400, 320), 'SUBTRACT', 1.0, rf)
    edgeR = mathn(nt, (-220, 320), 'MINIMUM', rf, rf2)
    sf2 = mathn(nt, (-400, -60), 'SUBTRACT', 1.0, subfr)
    edgeS = mathn(nt, (-220, -60), 'MINIMUM', subfr, sf2)
    edge = mathn(nt, (1400, 200), 'MINIMUM', edgeR, edgeS)
    came = maprange(nt, (1580, 200), edge, 0.0, 0.13, 0.04, 1.0)
    # --- how much light each panel gets -----------------------------------
    # the light behind the window is strongest in the oculus and dies away
    # towards the outer ring
    fall = maprange(nt, (1400, 480), rad, 0.50, 0.06, 0.42, 1.0)
    # Not every panel is lit from behind.  The dark ones are what make a
    # rose window read as stained glass instead of a rainbow decal.  This
    # is a second hash of the same panel index, so the brightness belongs
    # to the panel rather than to a band crossing it.
    g1 = mathn(nt, (500, -880), 'MULTIPLY', idx, 78.233)
    g2 = mathn(nt, (680, -880), 'SINE', g1)
    g3 = mathn(nt, (860, -880), 'MULTIPLY', g2, 43758.5453)
    g4 = mathn(nt, (1040, -880), 'FRACT', g3)
    lit = mathn(nt, (1220, -880), 'MULTIPLY_ADD', g4, 0.85, 0.15)
    # old glass is never perfectly even
    gn = noise(nt, (1400, 720), 9.0, 8.0, 0.6, 0.4, tc.outputs['Generated'])
    gk = mathn(nt, (1580, 720), 'MULTIPLY_ADD', gn.outputs['Fac'], 0.55, 0.72)
    st = mathn(nt, (1760, 480), 'MULTIPLY', fall.outputs['Result'],
               gk.outputs['Value'])
    st = mathn(nt, (1940, 480), 'MULTIPLY', st, lit.outputs['Value'])
    st = mathn(nt, (2120, 480), 'MULTIPLY', st, came.outputs['Result'])
    bsdf = NN(nt, 'ShaderNodeBsdfPrincipled', (2300, 100))
    bsdf.inputs['Base Color'].default_value = (0.018, 0.020, 0.028, 1)
    bsdf.inputs['Roughness'].default_value = 0.18
    bsdf.inputs['IOR'].default_value = 1.52
    L(nt, glass, 'Color', bsdf, 'Emission Color')
    L(nt, st, 'Value', bsdf, 'Emission Strength')
    L(nt, bsdf, 'BSDF', out, 'Surface')
    return m


def m_clock_face(name='M_ClockFace'):
    """Pale dial plate with a faint warm glow so the clock face reads at
    night -- a purely reflective dial would vanish in the moonlight.

    The plate is mottled and darkens towards its rim so the seven metre
    disc does not read as one flat cream circle, and the glow is kept low:
    a clock face lit from within is a warm lantern, not a floodlight.
    """
    m, nt, out = newmat(name)
    geo = NN(nt, 'ShaderNodeNewGeometry', (-900, 0))
    grain = noise(nt, (-700, 0), 2.4, 8.0, 0.6, 0.4, geo.outputs['Position'])
    r = ramp(nt, (-500, 0), [(0.30, (0.2600, 0.2340, 0.1880, 1)),
                             (0.66, (0.3400, 0.3070, 0.2460, 1)),
                             (0.92, (0.4400, 0.3960, 0.3160, 1))])
    L(nt, grain, 'Fac', r, 'Factor')
    # the plate darkens towards its rim.  The dial lies in the X-Z plane,
    # so the radial coordinate is built from X and Z -- using Y measured
    # the depth of the object and gave a left-right gradient instead.
    tc = NN(nt, 'ShaderNodeTexCoord', (-900, -320))
    sep = NN(nt, 'ShaderNodeSeparateXYZ', (-720, -320))
    L(nt, tc.outputs['Generated'], 'Vector', sep, 'Vector')
    px = mathn(nt, (-540, -260), 'SUBTRACT', sep.outputs['X'], 0.5)
    py = mathn(nt, (-540, -420), 'SUBTRACT', sep.outputs['Z'], 0.5)
    ax = mathn(nt, (-380, -260), 'POWER', px, 2.0)
    ay = mathn(nt, (-380, -420), 'POWER', py, 2.0)
    su = mathn(nt, (-220, -340), 'ADD', ax, ay)
    rr = mathn(nt, (-60, -340), 'SQRT', su)
    rim = maprange(nt, (100, -340), rr, 0.18, 0.50, 1.0, 0.74)
    shade = mixrgb(nt, (260, 0), 1.0, (0, 0, 0, 1), (1, 1, 1, 1))
    shade.blend_type = 'MULTIPLY'
    L(nt, r, 'Color', shade, 'Color1')
    L(nt, rim, 'Result', shade, 'Color2')
    bsdf = NN(nt, 'ShaderNodeBsdfPrincipled', (560, 0))
    L(nt, shade, 'Color', bsdf, 'Base Color')
    bsdf.inputs['Roughness'].default_value = 0.62
    bsdf.inputs['Emission Color'].default_value = (1.0, 0.70, 0.34, 1)
    bsdf.inputs['Emission Strength'].default_value = 0.55
    L(nt, bsdf, 'BSDF', out, 'Surface')
    return m


def m_emissive(name='M_Lantern', col=(1.0, 0.52, 0.18), strength=22.0):
    m, nt, out = newmat(name)
    e = NN(nt, 'ShaderNodeEmission', (400, 0))
    e.inputs['Color'].default_value = (col[0], col[1], col[2], 1)
    e.inputs['Strength'].default_value = strength
    L(nt, e, 'Emission', out, 'Surface')
    return m


def m_gold(name='M_Gold'):
    m, nt, out = newmat(name)
    geo = NN(nt, 'ShaderNodeNewGeometry', (-600, 0))
    n1 = noise(nt, (-400, 0), 9.0, 6.0, 0.5, 0.2, geo.outputs['Position'])
    r = ramp(nt, (-180, 0), [(0.3, (0.52, 0.34, 0.08, 1)),
                             (0.7, (0.85, 0.62, 0.20, 1))])
    L(nt, n1, 'Fac', r, 'Factor')
    bsdf = NN(nt, 'ShaderNodeBsdfPrincipled', (400, 0))
    L(nt, r, 'Color', bsdf, 'Base Color')
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.28
    L(nt, bsdf, 'BSDF', out, 'Surface')
    return m


def m_ridge(name='M_Ridge', haze=(0.0270, 0.0390, 0.0510), d0=1800.0, d1=4200.0,
            power=1.15):
    """Far mountains — dark rock veiled by aerial perspective.

    The haze mix is driven by camera view distance, so the three receding
    ranges separate in tone exactly the way a real skyline does.  The rock
    must be much darker than the haze or the fade has nothing to reveal.

    The haze colour is an ALBEDO, not a radiance.  It has to sit BELOW the
    moonlit sky, or the ranges read as sheets of torn paper hanging over the
    horizon -- but it also has to sit ABOVE the near moorland, or the ranges
    turn into a featureless black hole behind the castle.  The old value of
    0.048-0.103 was far too high (the ranges came out brighter than the sky);
    the value of 0.011 was far too low (they came out as a void).  This is
    the middle ground: a dark blue-grey that recedes without disappearing.
    """
    m, nt, out = newmat(name)
    geo = NN(nt, 'ShaderNodeNewGeometry', (-800, 0))
    n1 = noise(nt, (-600, 0), 0.012, 8.0, 0.6, 0.5, geo.outputs['Position'])
    r = ramp(nt, (-380, 0), [(0.30, (0.0105, 0.0145, 0.0220, 1)),
                             (0.55, (0.0165, 0.0230, 0.0330, 1)),
                             (0.80, (0.0250, 0.0330, 0.0440, 1))])
    L(nt, n1, 'Fac', r, 'Factor')
    cam = NN(nt, 'ShaderNodeCameraData', (-800, -420))
    hz = maprange(nt, (-600, -420), cam.outputs['View Distance'], d0, d1, 0.0, 1.0)
    hz = mathn(nt, (-420, -420), 'POWER', hz, power)
    mix = mixrgb(nt, (-180, 0), 0.0, (0, 0, 0, 1), haze + (1.0,))
    L(nt, hz, 'Value', mix, 'Factor')
    L(nt, r, 'Color', mix, 'Color1')
    bsdf = NN(nt, 'ShaderNodeBsdfPrincipled', (400, 0))
    L(nt, mix, 'Color', bsdf, 'Base Color')
    bsdf.inputs['Roughness'].default_value = 1.0
    # No dielectric sheen on the far ranges.  A rough surface at three
    # kilometres still catches the moon's halo at a grazing angle, and the
    # Fresnel edge turned whole flanks of the massif into sheets of bright
    # white paper hanging over the horizon.
    bsdf.inputs['Specular IOR Level'].default_value = 0.05
    L(nt, bsdf, 'BSDF', out, 'Surface')
    return m


def m_massif(name='M_Massif', haze=(0.0230, 0.0335, 0.0440), d0=900.0, d1=3200.0):
    """The close backdrop mountain: dark rock, snow on the summits, aerial haze.

    It has to stay a *silhouette* -- the castle is the subject and the hill is
    the ground it stands against.  So the rock is very dark, the snow is a
    cold blue-grey rather than white, and the aerial-perspective haze is a
    deep teal rather than the pale grey of a daytime sky.  A pale haze would
    turn the hill into a bright card and the castle would stop reading.

    But it must not be so dark that it becomes a hole in the picture either.
    The massif fills the top third of the aerial view, and with almost no
    light on it there was nothing there at all: a flat black field.  The
    values below put it a little under the near moorland, so the ranges
    recede but still show their form.
    """
    m, nt, out = newmat(name)
    geo = NN(nt, 'ShaderNodeNewGeometry', (-1500, 0))
    pos = geo.outputs['Position']
    sep = sepxyz(nt, (-1300, -260), pos)

    # --- rock: two scales of breakup so the face is never a flat card ---
    n_big = noise(nt, (-1300, 260), 0.0045, 8.0, 0.62, 0.4, pos)
    n_fine = noise(nt, (-1300, 60), 0.030, 8.0, 0.58, 0.3, pos)
    nb = mathn(nt, (-1100, 260), 'MULTIPLY', n_big.outputs['Fac'], 0.72)
    nf = mathn(nt, (-1100, 60), 'MULTIPLY', n_fine.outputs['Fac'], 0.28)
    nsum = mathn(nt, (-900, 200), 'ADD', nb.outputs['Value'], nf.outputs['Value'])
    rock = ramp(nt, (-700, 200), [(0.18, (0.0148, 0.0192, 0.0283, 1)),
                                  (0.50, (0.0324, 0.0396, 0.0516, 1)),
                                  (0.82, (0.0540, 0.0643, 0.0792, 1))])
    L(nt, nsum, 'Value', rock, 'Factor')

    # --- snow: only high up, only on the upward faces, broken by noise ---
    # The snow used to be gated hard on the face normal, and on a coarse
    # massif mesh that picked out scattered, hard-edged flakes -- torn bits
    # of white paper hanging in the sky.  The gate is much softer now, the
    # altitude band is wider, and the mask is broken up by a broad noise so
    # the snow reads as patches lying on the ridge rather than as confetti.
    alt = maprange(nt, (-1100, -260), sep.outputs['Z'], 380.0, 720.0, 0.0, 1.0)
    nsep = sepxyz(nt, (-1300, -460), geo.outputs['Normal'])
    upface = maprange(nt, (-1100, -460), nsep.outputs['Z'], 0.02, 0.50, 0.0, 1.0)
    sn = noise(nt, (-1100, -660), 0.011, 6.0, 0.55, 0.2, pos)
    sn2 = noise(nt, (-1100, -860), 0.0035, 4.0, 0.55, 0.3, pos)
    snm = mathn(nt, (-880, -780), 'MULTIPLY', sn.outputs['Fac'],
                sn2.outputs['Fac'])
    snowmask = mathn(nt, (-880, -460), 'MULTIPLY', alt.outputs['Result'],
                      upface.outputs['Result'])
    snowmask = mathn(nt, (-700, -460), 'MULTIPLY', snowmask.outputs['Value'],
                      snm.outputs['Value'])
    snowmask = maprange(nt, (-520, -460), snowmask.outputs['Value'], 0.16, 0.62,
                        0.0, 1.0)
    snowcol = ramp(nt, (-700, -700), [(0.0, (0.0384, 0.0504, 0.0696, 1)),
                                      (1.0, (0.0720, 0.0912, 0.1224, 1))])
    L(nt, snowmask, 'Result', snowcol, 'Factor')
    withsnow = mixrgb(nt, (-300, 0), 0.0, (0, 0, 0, 1), (0, 0, 0, 1))
    L(nt, rock, 'Color', withsnow, 'Color1')
    L(nt, snowcol, 'Color', withsnow, 'Color2')
    L(nt, snowmask, 'Result', withsnow, 'Factor')

    # --- aerial perspective ---
    cam = NN(nt, 'ShaderNodeCameraData', (-1500, -900))
    hz = maprange(nt, (-1300, -900), cam.outputs['View Distance'], d0, d1, 0.0, 1.0)
    hz = mathn(nt, (-1100, -900), 'POWER', hz, 1.25)
    mix = mixrgb(nt, (-60, 0), 0.0, (0, 0, 0, 1), haze + (1.0,))
    L(nt, hz, 'Value', mix, 'Factor')
    L(nt, withsnow, 'Color', mix, 'Color1')

    bsdf = NN(nt, 'ShaderNodeBsdfPrincipled', (300, 0))
    L(nt, mix, 'Color', bsdf, 'Base Color')
    bsdf.inputs['Roughness'].default_value = 1.0
    # the same grazing-angle sheen as the far ranges: no dielectric specular
    bsdf.inputs['Specular IOR Level'].default_value = 0.05
    L(nt, bsdf, 'BSDF', out, 'Surface')
    return m


def m_grass(name='M_Grass'):
    m, nt, out = newmat(name)
    geo = NN(nt, 'ShaderNodeNewGeometry', (-900, 0))
    pos = geo.outputs['Position']
    n1 = noise(nt, (-700, 0), 1.2, 8.0, 0.6, 0.4, pos)
    r = ramp(nt, (-480, 0), [(0.25, (0.019, 0.025, 0.010, 1)),
                             (0.55, (0.031, 0.034, 0.014, 1)),
                             (0.85, (0.041, 0.038, 0.017, 1))])
    L(nt, n1, 'Fac', r, 'Factor')
    bsdf = NN(nt, 'ShaderNodeBsdfPrincipled', (400, 0))
    L(nt, r, 'Color', bsdf, 'Base Color')
    bsdf.inputs['Roughness'].default_value = 0.9
    L(nt, bsdf, 'BSDF', out, 'Surface')
    return m


def m_water(name='M_Water'):
    """Deep dark lake: depth-graded transparency over rock, sharp sky reflection."""
    m, nt, out = newmat(name)
    geo = NN(nt, 'ShaderNodeNewGeometry', (-1200, 0))
    attr = NN(nt, 'ShaderNodeVertexColor', (-1200, -300))
    attr.layer_name = "depth"
    sep = NN(nt, 'ShaderNodeSeparateXYZ', (-1000, -300))
    L(nt, attr, 'Color', sep, 'Vector')
    shallow = maprange(nt, (-800, -300), sep.outputs['X'], 0.0, 0.9, 1.0, 0.0)
    # wave detail
    wm = mapping(nt, (-1000, 300), geo.outputs['Position'], scale=(1.0, 1.0, 1.0))
    w1 = NN(nt, 'ShaderNodeTexWave', (-800, 300), wave_type='BANDS',
            bands_direction='X', wave_profile='SIN')
    w1.inputs['Scale'].default_value = 0.055
    w1.inputs['Distortion'].default_value = 6.0
    w1.inputs['Detail'].default_value = 6.0
    w1.inputs['Detail Scale'].default_value = 3.0
    L(nt, wm, 'Vector', w1, 'Vector')
    w2 = NN(nt, 'ShaderNodeTexWave', (-800, 60), wave_type='BANDS',
            bands_direction='Y', wave_profile='SIN')
    w2.inputs['Scale'].default_value = 0.085
    w2.inputs['Distortion'].default_value = 4.0
    w2.inputs['Detail'].default_value = 5.0
    L(nt, wm, 'Vector', w2, 'Vector')
    wmix = mathn(nt, (-600, 200), 'ADD', w1, w2)
    wsc = mathn(nt, (-440, 200), 'MULTIPLY', wmix, 0.35)
    bump = NN(nt, 'ShaderNodeBump', (-200, 200))
    # a gentle slope keeps the mirror intact -- a strong bump scatters the
    # sky and window reflections into the black water body
    bump.inputs['Strength'].default_value = 0.022
    bump.inputs['Distance'].default_value = 0.14
    L(nt, wsc, 'Value', bump, 'Height')
    # water surface
    wsurf = NN(nt, 'ShaderNodeBsdfPrincipled', (300, 200))
    wsurf.inputs['Base Color'].default_value = (0.0090, 0.0185, 0.0245, 1)
    wsurf.inputs['Roughness'].default_value = 0.035
    wsurf.inputs['IOR'].default_value = 1.333
    wsurf.inputs['Metallic'].default_value = 0.0
    L(nt, bump, 'Normal', wsurf, 'Normal')
    # Shallows.  A fully transparent water body showed the near-black lake
    # bed straight through it, which turned the whole foreground into a
    # void, so the shallow mix goes to a silty shallow-water shader rather
    # than to Transparency -- the shore still reads as a shore, but it reads
    # as WATER.
    wshal = NN(nt, 'ShaderNodeBsdfPrincipled', (300, -100))
    wshal.inputs['Base Color'].default_value = (0.0250, 0.0430, 0.0380, 1)
    wshal.inputs['Roughness'].default_value = 0.20
    wshal.inputs['IOR'].default_value = 1.333
    L(nt, bump, 'Normal', wshal, 'Normal')
    mixsh = NN(nt, 'ShaderNodeMixShader', (600, 100))
    L(nt, shallow, 'Result', mixsh, 'Fac')
    L(nt, wshal, 'BSDF', mixsh, 1)
    L(nt, wsurf, 'BSDF', mixsh, 2)
    L(nt, mixsh, 'Shader', out, 'Surface')
    return m


def m_mist(name='M_Mist', col=(0.36, 0.46, 0.58), density=0.010,
           z_top=20.0, z_peak=3.0, z_bot=-6.0, floor=0.5, nscale=0.012,
           rough=0.6, r_in=None, r_out=None, r_cx=0.0, r_cy=0.0):
    """Height-graded volumetric mist.

    Density follows a trapezoid in Z: 0 above `z_top`, rising to 1.0 at
    `z_peak`, easing to `floor` at `z_bot`.  A trapezoid (rather than a
    one-sided ramp) is what keeps a lake mist from swallowing the castle:
    rays climbing away from the water leave the layer within metres.

    `r_in`/`r_out` add a radial falloff (density 0 beyond `r_out`, full
    inside `r_in`) around (`r_cx`, `r_cy`).  Without it a bounded volume
    box shows a hard seam where camera rays stop hitting its side wall.
    """
    m, nt, out = newmat_volume(name)
    geo = NN(nt, 'ShaderNodeNewGeometry', (-1000, 0))
    sep = sepxyz(nt, (-800, 0), geo.outputs['Position'])
    up = maprange(nt, (-600, 140), sep.outputs['Z'], z_top, z_peak, 0.0, 1.0)
    dn = maprange(nt, (-600, -60), sep.outputs['Z'], z_bot, z_peak, floor, 1.0)
    fall = mathn(nt, (-420, 40), 'MINIMUM', up, dn)
    n1 = noise(nt, (-800, 300), nscale, 6.0, rough, 0.4, geo.outputs['Position'])
    nr = ramp(nt, (-600, 300), [(0.32, (0.10, 0.10, 0.10, 1)),
                                (0.70, (1.0, 1.0, 1.0, 1))])
    L(nt, n1, 'Fac', nr, 'Factor')
    d1 = mathn(nt, (-380, 100), 'MULTIPLY', fall, nr)
    if r_in is not None and r_out is not None:
        cx = mathn(nt, (-800, -220), 'SUBTRACT', sep.outputs['X'], r_cx)
        cy = mathn(nt, (-800, -320), 'SUBTRACT', sep.outputs['Y'], r_cy)
        comb = combxyz(nt, (-640, -260), x=cx, y=cy, z=0.0)
        ln = NN(nt, 'ShaderNodeVectorMath', (-460, -260), operation='LENGTH')
        L(nt, comb.outputs['Vector'], ln, 0)
        rf = maprange(nt, (-300, -260), ln.outputs['Value'], r_out, r_in, 0.0, 1.0)
        d1 = mathn(nt, (-180, 40), 'MULTIPLY', d1, rf)
    d2 = mathn(nt, (-60, 100), 'MULTIPLY', d1, density)
    vs = NN(nt, 'ShaderNodeVolumeScatter', (300, 0))
    vs.inputs['Color'].default_value = (col[0], col[1], col[2], 1)
    vs.inputs['Anisotropy'].default_value = 0.35
    L(nt, d2, 'Value', vs, 'Density')
    L(nt, vs, 'Volume', out, 'Volume')
    return m


def m_conifer(name='M_Conifer', dark=(0.0180, 0.0270, 0.0195),
              light=(0.0460, 0.0620, 0.0420)):
    """Conifer needles — per-tree colour variation, vertical falloff, needle
    breakup.  The "tree" colour attribute carries (per-tree random, height
    fraction) so a merged forest still reads as individual trees."""
    m, nt, out = newmat(name)
    geo = NN(nt, 'ShaderNodeNewGeometry', (-1200, 300))
    attr = NN(nt, 'ShaderNodeVertexColor', (-1200, -60))
    attr.layer_name = "tree"
    sep = NN(nt, 'ShaderNodeSeparateXYZ', (-1000, -60))
    L(nt, attr, 'Color', sep, 'Vector')
    tv = maprange(nt, (-820, -60), sep.outputs['X'], 0.0, 1.0, 0.0, 1.0)
    hf = maprange(nt, (-820, -180), sep.outputs['Y'], 0.0, 1.0, 0.0, 1.0)
    # needle breakup
    n1 = noise(nt, (-1000, 300), 22.0, 8.0, 0.62, 0.5, geo.outputs['Position'])
    nb = ramp(nt, (-800, 300), [(0.32, (0.55, 0.58, 0.54, 1)),
                                (0.70, (1.30, 1.24, 1.16, 1))])
    L(nt, n1, 'Fac', nb, 'Factor')
    # per-tree hue/value
    base = mixrgb(nt, (-560, 120), 0.5, dark + (1.0,), light + (1.0,))
    L(nt, tv, 'Result', base, 'Factor')
    # darken towards the ground (self shadowing)
    ao = maprange(nt, (-560, -180), hf, 0.0, 1.0, 0.42, 1.0)
    c1 = mixrgb(nt, (-360, 120), 1.0, (1.0, 1.0, 1.0, 1), (1.0, 1.0, 1.0, 1))
    c1.blend_type = 'MULTIPLY'
    L(nt, base, 'Color', c1, 'Color1')
    L(nt, nb, 'Color', c1, 'Color2')
    c2 = mixrgb(nt, (-200, 120), 1.0, (1.0, 1.0, 1.0, 1), (1.0, 1.0, 1.0, 1))
    c2.blend_type = 'MULTIPLY'
    L(nt, c1, 'Color', c2, 'Color1')
    L(nt, ao, 'Result', c2, 'Color2')
    bsdf = NN(nt, 'ShaderNodeBsdfPrincipled', (200, 100))
    L(nt, c2, 'Color', bsdf, 'Base Color')
    bsdf.inputs['Roughness'].default_value = 0.84
    bsdf.inputs['Specular IOR Level'].default_value = 0.18
    L(nt, bsdf, 'BSDF', out, 'Surface')
    return m


def m_path(name='M_Path', worn=(0.0620, 0.0500, 0.0355),
           edge=(0.0300, 0.0350, 0.0210)):
    """Worn track: bare earth in the middle fading into the moor grass."""
    m, nt, out = newmat(name)
    geo = NN(nt, 'ShaderNodeNewGeometry', (-900, 200))
    attr = NN(nt, 'ShaderNodeVertexColor', (-900, -60))
    attr.layer_name = "path"
    sep = NN(nt, 'ShaderNodeSeparateXYZ', (-700, -60))
    L(nt, attr, 'Color', sep, 'Vector')
    w = maprange(nt, (-520, -60), sep.outputs['X'], 0.0, 1.0, 0.0, 1.0)
    n1 = noise(nt, (-700, 240), 1.6, 8.0, 0.6, 0.5, geo.outputs['Position'])
    nr = ramp(nt, (-500, 240), [(0.28, (0.55, 0.55, 0.58, 1)),
                                (0.72, (1.25, 1.20, 1.10, 1))])
    L(nt, n1, 'Fac', nr, 'Factor')
    base = mixrgb(nt, (-320, 120), 0.5, edge + (1.0,), worn + (1.0,))
    L(nt, w, 'Result', base, 'Factor')
    c1 = mixrgb(nt, (-160, 120), 1.0, (1.0, 1.0, 1.0, 1), (1.0, 1.0, 1.0, 1))
    c1.blend_type = 'MULTIPLY'
    L(nt, base, 'Color', c1, 'Color1')
    L(nt, nr, 'Color', c1, 'Color2')
    bsdf = NN(nt, 'ShaderNodeBsdfPrincipled', (200, 100))
    L(nt, c1, 'Color', bsdf, 'Base Color')
    bsdf.inputs['Roughness'].default_value = 0.92
    L(nt, bsdf, 'BSDF', out, 'Surface')
    return m


def build_all():
    mats = {}
    mats['stone'] = m_stone('M_Stone')
    mats['stone_c'] = m_stone('M_StoneRound', cylindrical=True, radius=8.0)
    mats['stone_w'] = m_stone('M_StoneWarm', tint=(1.05, 0.98, 0.90),
                              base_col=(0.330, 0.300, 0.262))
    # The terrace decks are weathered flagstone, not ashlar: a horizontal
    # plane of the castle's wall stone reads as a sheet of card, and it is
    # also the wrong thing to walk on.
    mats['paving'] = m_stone('M_Paving', tint=(0.72, 0.71, 0.68),
                              base_col=(0.128, 0.122, 0.110))
    mats['brick'] = m_brick('M_Brick')
    mats['ghglass'] = m_greenhouse_glass('M_GreenhouseGlass')
    mats['slate'] = m_slate('M_Slate')
    mats['verdigris'] = m_verdigris('M_Verdigris')
    mats['lead'] = m_lead('M_Lead')
    mats['glass'] = m_window_glass('M_WindowGlass')
    mats['rock'] = m_rock('M_Rock')
    mats['terrain'] = m_terrain('M_Terrain')
    mats['foliage'] = m_foliage('M_Foliage')
    mats['bark'] = m_bark('M_Bark')
    mats['wood'] = m_wood('M_Wood')
    mats['wood_dark'] = m_wood('M_WoodDark', col=(0.030, 0.021, 0.014))
    mats['lantern'] = m_emissive('M_Lantern')
    mats['clockface'] = m_clock_face('M_ClockFace')
    mats['roseglass'] = m_rose_glass('M_RoseGlass')
    mats['gold'] = m_gold('M_Gold')
    mats['ridge'] = m_ridge('M_Ridge')
    mats['massif'] = m_massif('M_Massif')
    mats['conifer'] = m_conifer('M_Conifer')
    mats['path'] = m_path('M_Path')
    mats['grass'] = m_grass('M_Grass')
    mats['water'] = m_water('M_Water')
    mats['mist'] = m_mist('M_Mist')
    return mats
