"""All procedural materials."""
import bpy, math


class NT:
    def __init__(self, name):
        m = bpy.data.materials.get(name)
        if m is None:
            m = bpy.data.materials.new(name)
        m.use_nodes = True
        self.m = m
        self.t = m.node_tree
        self.t.nodes.clear()
        self.x = 0
        self.out = self.n('ShaderNodeOutputMaterial')

    def n(self, typ, inp=None, **props):
        nd = self.t.nodes.new(typ)
        nd.location = (self.x, 0)
        self.x += 200
        for k, v in props.items():
            setattr(nd, k, v)
        if inp:
            for k, v in inp.items():
                s = nd.inputs[k]
                if hasattr(v, 'is_output') or isinstance(v, bpy.types.NodeSocket):
                    self.t.links.new(v, s)
                else:
                    s.default_value = v
        return nd

    def l(self, a, b):
        self.t.links.new(a, b)

    # helpers ---------------------------------------------------------
    def math(self, op, a, b=None, c=None, clamp=False):
        nd = self.n('ShaderNodeMath', operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, bpy.types.NodeSocket):
                self.l(v, nd.inputs[i])
            else:
                nd.inputs[i].default_value = v
        return nd.outputs[0]

    def mix(self, fac, a, b, blend='MIX', clamp=True):
        nd = self.n('ShaderNodeMix', data_type='RGBA', blend_type=blend, clamp_result=clamp)
        for sock, v in ((nd.inputs[0], fac), (nd.inputs[6], a), (nd.inputs[7], b)):
            if isinstance(v, bpy.types.NodeSocket):
                self.l(v, sock)
            else:
                sock.default_value = v if not isinstance(v, (tuple, list)) or len(v) == 4 else (*v, 1.0)
        return nd.outputs[2]

    def mixf(self, fac, a, b):
        nd = self.n('ShaderNodeMix', data_type='FLOAT', clamp_factor=True)
        for sock, v in ((nd.inputs[0], fac), (nd.inputs[2], a), (nd.inputs[3], b)):
            if isinstance(v, bpy.types.NodeSocket):
                self.l(v, sock)
            else:
                sock.default_value = v
        return nd.outputs[0]

    def ramp(self, fac, stops, interp='LINEAR'):
        nd = self.n('ShaderNodeValToRGB')
        cr = nd.color_ramp
        cr.interpolation = interp
        while len(cr.elements) < len(stops):
            cr.elements.new(0.5)
        for el, (p, c) in zip(cr.elements, stops):
            el.position = p
            el.color = c if len(c) == 4 else (*c, 1.0)
        self.l(fac, nd.inputs[0])
        return nd

    def maprange(self, v, a, b, c=0.0, d=1.0, clamp=True):
        nd = self.n('ShaderNodeMapRange', clamp=clamp)
        self.l(v, nd.inputs[0])
        nd.inputs[1].default_value = a
        nd.inputs[2].default_value = b
        nd.inputs[3].default_value = c
        nd.inputs[4].default_value = d
        return nd.outputs[0]

    def noise(self, vec, scale, detail=4.0, rough=0.55, dist=0.0, dim='3D', w=0.0):
        nd = self.n('ShaderNodeTexNoise', noise_dimensions=dim)
        if vec is not None:
            self.l(vec, nd.inputs['Vector'])
        nd.inputs['Scale'].default_value = scale
        nd.inputs['Detail'].default_value = detail
        nd.inputs['Roughness'].default_value = rough
        nd.inputs['Distortion'].default_value = dist
        if dim == '4D':
            nd.inputs['W'].default_value = w
        return nd

    def vmul(self, v, s):
        nd = self.n('ShaderNodeVectorMath', operation='MULTIPLY')
        self.l(v, nd.inputs[0])
        nd.inputs[1].default_value = s
        return nd.outputs[0]

    def vadd(self, v, s):
        nd = self.n('ShaderNodeVectorMath', operation='ADD')
        self.l(v, nd.inputs[0])
        if isinstance(s, bpy.types.NodeSocket):
            self.l(s, nd.inputs[1])
        else:
            nd.inputs[1].default_value = s
        return nd.outputs[0]

    def attr(self, name, typ='GEOMETRY'):
        return self.n('ShaderNodeAttribute', attribute_name=name, attribute_type=typ)

    def bump(self, h, strength, dist=0.1, normal=None):
        nd = self.n('ShaderNodeBump')
        nd.inputs['Strength'].default_value = strength
        nd.inputs['Distance'].default_value = dist
        self.l(h, nd.inputs['Height'])
        if normal is not None:
            self.l(normal, nd.inputs['Normal'])
        return nd.outputs['Normal']

    def bsdf(self, **kw):
        nd = self.n('ShaderNodeBsdfPrincipled')
        for k, v in kw.items():
            key = k.replace('_', ' ')
            s = nd.inputs[key]
            if isinstance(v, bpy.types.NodeSocket):
                self.l(v, s)
            else:
                s.default_value = v if not (isinstance(v, tuple) and len(v) == 3) else (*v, 1.0)
        return nd

    def done(self, shader, disp=None, vol=None):
        self.l(shader, self.out.inputs['Surface'])
        if disp is not None:
            self.l(disp, self.out.inputs['Displacement'])
        if vol is not None:
            self.l(vol, self.out.inputs['Volume'])
        return self.m


# ======================================================================= stone
def stone(name='Stone', base=(0.34, 0.31, 0.27), bw=0.78, bh=0.36, tint=1.0):
    t = NT(name)
    uv = t.n('ShaderNodeTexCoord')
    geo_ = t.n('ShaderNodeNewGeometry')
    obj = uv.outputs['Object']
    rnd = t.attr('rnd').outputs['Fac']
    # ashlar blocks in metre UV space
    warp = t.noise(uv.outputs['UV'], 1.3, 2.0, 0.5)
    wv = t.n('ShaderNodeVectorMath', operation='MULTIPLY_ADD')
    t.l(warp.outputs['Color'], wv.inputs[0])
    wv.inputs[1].default_value = (0.035, 0.02, 0.0)
    t.l(uv.outputs['UV'], wv.inputs[2])
    br = t.n('ShaderNodeTexBrick', inp={'Vector': wv.outputs[0], 'Scale': 1.0, 'Mortar Size': 0.011,
                                         'Mortar Smooth': 0.6, 'Bias': 0.0, 'Brick Width': bw,
                                         'Row Height': bh, 'Color1': (1, 1, 1, 1), 'Color2': (0, 0, 0, 1),
                                         'Mortar': (0, 0, 0, 1)}, offset=0.37, offset_frequency=2,
                  squash=0.62, squash_frequency=3)
    brick_var = br.outputs['Color']     # per-block random grey
    mortar = br.outputs['Fac']          # 1 at mortar
    # regional quarry-batch variation (large scale) + per-element rnd
    reg = t.noise(obj, 0.018, 2.0, 0.5).outputs['Fac']
    batch = t.math('ADD', t.math('MULTIPLY', reg, 0.9), t.math('MULTIPLY', rnd, 0.55))
    c_batch = t.ramp(batch, [(0.25, (base[0] * 0.78, base[1] * 0.78, base[2] * 0.8)),
                             (0.55, base),
                             (0.85, (base[0] * 1.12, base[1] * 1.05, base[2] * 0.95))]).outputs[0]
    # per-block variation
    bv = t.math('MULTIPLY', t.n('ShaderNodeSeparateColor', inp={'Color': brick_var}).outputs[0], 1.0)
    col = t.mix(t.maprange(bv, 0, 1, 0.0, 0.55), c_batch, (base[0] * 0.62, base[1] * 0.6, base[2] * 0.58))
    col = t.mix(t.maprange(bv, 0.55, 1, 0.0, 0.35), col, (base[0] * 1.3, base[1] * 1.22, base[2] * 1.1))
    # a few blocks from a warmer / cooler batch
    hue = t.maprange(bv, 0.42, 0.47, 0.0, 0.45)
    col = t.mix(hue, col, (base[0] * 1.05, base[1] * 0.92, base[2] * 0.78))
    # fine grain
    grain = t.noise(obj, 9.0, 6.0, 0.65).outputs['Fac']
    col = t.mix(t.maprange(grain, 0.3, 0.7, 0.0, 0.25), col, (0.1, 0.095, 0.09), 'MULTIPLY')
    # dirt streaks (vertical smears below ledges)
    sv = t.n('ShaderNodeSeparateXYZ', inp={'Vector': obj})
    streak_vec = t.n('ShaderNodeCombineXYZ')
    t.l(t.math('MULTIPLY', sv.outputs[0], 3.0), streak_vec.inputs[0])
    t.l(t.math('MULTIPLY', sv.outputs[1], 3.0), streak_vec.inputs[1])
    t.l(t.math('MULTIPLY', sv.outputs[2], 0.12), streak_vec.inputs[2])
    streak = t.noise(streak_vec.outputs[0], 1.0, 3.0, 0.6).outputs['Fac']
    streak_zone = t.maprange(t.noise(obj, 0.08, 2.0).outputs['Fac'], 0.45, 0.65, 0.0, 1.0)
    streak_m = t.math('MULTIPLY', t.maprange(streak, 0.5, 0.75, 0.0, 0.45), streak_zone)
    # AO grime in crevices and under sills
    ao = t.n('ShaderNodeAmbientOcclusion', inp={'Distance': 1.2}, samples=8)
    grime = t.maprange(ao.outputs['AO'], 0.4, 0.97, 0.85, 0.0)
    dirt = t.math('MAXIMUM', t.math('MULTIPLY', streak_m, 0.8), grime)
    col = t.mix(dirt, col, (0.035, 0.034, 0.03))
    # moss: upward facing & lower / damp
    nz = t.n('ShaderNodeSeparateXYZ', inp={'Vector': geo_.outputs['Normal']}).outputs[2]
    up = t.maprange(nz, 0.35, 0.85, 0.0, 1.0)
    low = t.maprange(sv.outputs[2], 40.0, 62.0, 1.0, 0.15)
    mossn = t.noise(obj, 0.35, 5.0, 0.6).outputs['Fac']
    mossm = t.math('MULTIPLY', t.maprange(mossn, 0.45, 0.62, 0.0, 1.0),
                   t.math('MAXIMUM', t.math('MULTIPLY', up, 0.9), t.math('MULTIPLY', low, t.math('MULTIPLY', grime, 1.3))),
                   clamp=True)
    moss_col = t.mix(t.noise(obj, 2.0, 3).outputs['Fac'], (0.05, 0.075, 0.025), (0.09, 0.1, 0.035))
    col = t.mix(mossm, col, moss_col)
    # lichen blooms (pale grey-green), favouring upward faces
    lv = t.n('ShaderNodeTexVoronoi', inp={'Vector': obj, 'Scale': 2.2, 'Randomness': 1.0})
    lspot = t.maprange(lv.outputs['Distance'], 0.22, 0.08, 0.0, 1.0)
    lmask = t.math('MULTIPLY', lspot, t.maprange(t.noise(obj, 0.6, 3).outputs['Fac'], 0.5, 0.65, 0.0, 1.0))
    lmask = t.math('MULTIPLY', lmask, t.math('ADD', 0.35, t.math('MULTIPLY', up, 0.65)))
    col = t.mix(t.math('MULTIPLY', lmask, 0.7), col, (base[0] * 1.1, base[1] * 1.15, base[2] * 0.95))
    # edge wear: exposed corners slightly lighter (AO 'inside' inverted trick approximated by bump curvature)
    col = t.mix(t.math('MULTIPLY', mortar, 0.6), col, (base[0] * 0.62, base[1] * 0.6, base[2] * 0.56))
    # bump
    chips = t.noise(obj, 4.0, 6.0, 0.7).outputs['Fac']
    h = t.math('ADD', t.math('MULTIPLY', mortar, -0.7), t.math('MULTIPLY', chips, 0.45))
    h = t.math('ADD', h, t.math('MULTIPLY', bv, 0.3))
    nrm = t.bump(h, 0.4, 0.04)
    rough = t.maprange(dirt, 0, 1, 0.82, 0.92)
    b = t.bsdf(Base_Color=col, Roughness=rough, Normal=nrm)
    b.inputs['Specular IOR Level'].default_value = 0.25
    return t.done(b.outputs[0])


# ======================================================================= slate
def slate():
    t = NT('Slate')
    tc = t.n('ShaderNodeTexCoord')
    uv = tc.outputs['UV']
    obj = tc.outputs['Object']
    br = t.n('ShaderNodeTexBrick', inp={'Vector': uv, 'Scale': 1.0, 'Mortar Size': 0.012, 'Mortar Smooth': 0.2,
                                         'Brick Width': 0.34, 'Row Height': 0.19, 'Color1': (1, 1, 1, 1),
                                         'Color2': (0, 0, 0, 1), 'Mortar': (0, 0, 0, 1)}, offset=0.5)
    var = t.n('ShaderNodeSeparateColor', inp={'Color': br.outputs['Color']}).outputs[0]
    base = t.ramp(var, [(0.0, (0.035, 0.042, 0.052)), (0.5, (0.055, 0.062, 0.075)), (1.0, (0.085, 0.09, 0.1))]).outputs[0]
    # weathering patches and lichen
    wn = t.noise(obj, 0.25, 4.0, 0.6).outputs['Fac']
    base = t.mix(t.maprange(wn, 0.5, 0.75, 0.0, 0.5), base, (0.11, 0.1, 0.085))
    lich = t.n('ShaderNodeTexVoronoi', inp={'Vector': obj, 'Scale': 1.3, 'Randomness': 1.0})
    lm = t.math('MULTIPLY', t.maprange(lich.outputs['Distance'], 0.12, 0.05, 0.0, 1.0),
                t.maprange(t.noise(obj, 0.8, 2).outputs['Fac'], 0.52, 0.62, 0.0, 1.0))
    base = t.mix(lm, base, (0.16, 0.16, 0.11))
    # streaks down the slope (v is up-slope)
    sep = t.n('ShaderNodeSeparateXYZ', inp={'Vector': uv})
    sv = t.n('ShaderNodeCombineXYZ')
    t.l(t.math('MULTIPLY', sep.outputs[0], 2.5), sv.inputs[0])
    t.l(t.math('MULTIPLY', sep.outputs[1], 0.15), sv.inputs[1])
    stre = t.noise(sv.outputs[0], 1.0, 3).outputs['Fac']
    base = t.mix(t.maprange(stre, 0.5, 0.8, 0, 0.45), base, (0.02, 0.022, 0.026))
    # tile edges lift: bump using brick fac + slope within row (overlap)
    fr = t.math('FRACT', t.math('DIVIDE', sep.outputs[1], 0.19))
    h = t.math('ADD', t.math('MULTIPLY', br.outputs['Fac'], -1.0), t.math('MULTIPLY', fr, 0.6))
    h = t.math('ADD', h, t.math('MULTIPLY', var, 0.25))
    nrm = t.bump(h, 0.5, 0.02)
    rough = t.maprange(var, 0, 1, 0.38, 0.62)
    b = t.bsdf(Base_Color=base, Roughness=rough, Normal=nrm)
    b.inputs['Specular IOR Level'].default_value = 0.5
    return t.done(b.outputs[0])


def copper():
    """verdigris: blue-green patina with vertical run-off streaks and residual bronze patches."""
    t = NT('Copper')
    tc = t.n('ShaderNodeTexCoord')
    obj = tc.outputs['Object']
    uv = tc.outputs['UV']
    br = t.n('ShaderNodeTexBrick', inp={'Vector': uv, 'Scale': 1.0, 'Mortar Size': 0.01,
                                         'Brick Width': 0.6, 'Row Height': 1.2, 'Color1': (1, 1, 1, 1),
                                         'Color2': (0, 0, 0, 1), 'Mortar': (0, 0, 0, 1)})
    sep = t.n('ShaderNodeSeparateXYZ', inp={'Vector': obj})
    sv = t.n('ShaderNodeCombineXYZ')
    t.l(t.math('MULTIPLY', sep.outputs[0], 4.0), sv.inputs[0])
    t.l(t.math('MULTIPLY', sep.outputs[1], 4.0), sv.inputs[1])
    t.l(t.math('MULTIPLY', sep.outputs[2], 0.25), sv.inputs[2])
    streak = t.noise(sv.outputs[0], 1.0, 4.0, 0.6).outputs['Fac']
    n1 = t.noise(obj, 0.5, 4.0, 0.55).outputs['Fac']
    pat = t.ramp(t.math('ADD', t.math('MULTIPLY', streak, 0.7), t.math('MULTIPLY', n1, 0.4)),
                 [(0.35, (0.08, 0.22, 0.19)), (0.55, (0.16, 0.36, 0.3)), (0.72, (0.26, 0.46, 0.39)),
                  (0.9, (0.34, 0.52, 0.45))]).outputs[0]
    bronze = t.maprange(t.noise(obj, 1.6, 5.0, 0.6).outputs['Fac'], 0.6, 0.7, 0, 0.8)
    col = t.mix(bronze, pat, (0.09, 0.055, 0.03))
    dirt = t.maprange(streak, 0.6, 0.8, 0.0, 0.5)
    col = t.mix(dirt, col, (0.04, 0.06, 0.05))
    b = t.bsdf(Base_Color=col, Roughness=t.maprange(bronze, 0, 1, 0.62, 0.4), Metallic=t.math('MULTIPLY', bronze, 0.8),
               Normal=t.bump(t.math('ADD', br.outputs['Fac'], t.math('MULTIPLY', n1, 0.3)), 0.3, 0.02))
    return t.done(b.outputs[0])


def glass():
    """dark reflective leaded glass; inhabited panes glow from within (attribute 'glow')."""
    t = NT('Glass')
    tc = t.n('ShaderNodeTexCoord')
    uv = tc.outputs['UV']
    obj = tc.outputs['Object']
    g = t.attr('glow').outputs['Fac']
    rnd = t.n('ShaderNodeObjectInfo').outputs['Random']
    # leaded cames: small quarry panes
    br = t.n('ShaderNodeTexBrick', inp={'Vector': uv, 'Scale': 1.0, 'Mortar Size': 0.018,
                                         'Brick Width': 0.24, 'Row Height': 0.3, 'Color1': (1, 1, 1, 1),
                                         'Color2': (0.6, 0.6, 0.6, 1), 'Mortar': (0, 0, 0, 1)}, offset=0.0)
    lead = br.outputs['Fac']
    panevar = t.n('ShaderNodeSeparateColor', inp={'Color': br.outputs['Color']}).outputs[0]
    # interior light variation: warm hue per window (glow value hashes hue), falloff pattern
    hue_n = t.noise(obj, 0.6, 1.0).outputs['Fac']
    warm = t.ramp(t.math('FRACT', t.math('ADD', t.math('MULTIPLY', g, 7.13), hue_n)),
                  [(0.0, (1.0, 0.32, 0.07)), (0.45, (1.0, 0.43, 0.12)), (0.8, (1.0, 0.54, 0.2)),
                   (1.0, (0.95, 0.38, 0.1))]).outputs[0]
    flick = t.maprange(t.noise(uv, 1.6, 2.0).outputs['Fac'], 0.3, 0.7, 0.45, 1.15)
    strength = t.math('MULTIPLY', t.math('MULTIPLY', g, flick), 2.4)
    strength = t.math('MULTIPLY', strength, t.maprange(lead, 0.0, 1.0, 1.0, 0.03))
    strength = t.math('MULTIPLY', strength, t.maprange(panevar, 0.55, 1.0, 0.8, 1.15))
    b = t.bsdf(Base_Color=(0.012, 0.014, 0.016), Roughness=t.maprange(lead, 0, 1, 0.06, 0.6),
               Emission_Color=warm, Emission_Strength=strength,
               Normal=t.bump(t.math('ADD', t.math('MULTIPLY', lead, -1.0),
                                    t.math('MULTIPLY', panevar, 0.2)), 0.35, 0.01))
    b.inputs['Specular IOR Level'].default_value = 0.8
    return t.done(b.outputs[0])


def interior():
    """lit interior seen through an open arch: warm falloff, dark silhouettes of posts and hulls."""
    t = NT('Interior')
    tc = t.n('ShaderNodeTexCoord')
    uv = tc.outputs['UV']
    sep = t.n('ShaderNodeSeparateXYZ', inp={'Vector': uv})
    v = t.math('FRACT', t.math('DIVIDE', sep.outputs[1], 7.0))
    grad = t.maprange(sep.outputs[1], 0.0, 6.5, 1.0, 0.35)
    n = t.noise(uv, 0.9, 3.0).outputs['Fac']
    posts = t.n('ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', inp={'Vector': uv, 'Scale': 0.9, 'Distortion': 1.5})
    sil = t.maprange(posts.outputs['Fac'], 0.85, 0.95, 1.0, 0.25)
    hull = t.maprange(sep.outputs[1], 0.8, 1.6, 0.2, 1.0)
    e = t.math('MULTIPLY', t.math('MULTIPLY', grad, sil), t.math('MULTIPLY', hull, t.maprange(n, 0.3, 0.7, 0.6, 1.2)))
    g = t.attr('glow').outputs['Fac']
    b = t.bsdf(Base_Color=(0.02, 0.015, 0.01), Roughness=0.8, Emission_Color=(1.0, 0.5, 0.18),
               Emission_Strength=t.math('MULTIPLY', t.math('MULTIPLY', e, g), 9.0))
    return t.done(b.outputs[0])


def clock_dial():
    """backlit opal-glass dial: warm, brighter at the centre, darker chapter ring."""
    t = NT('ClockFace')
    tc = t.n('ShaderNodeTexCoord')
    obj = tc.outputs['Object']
    g = t.n('ShaderNodeNewGeometry')
    n = t.noise(obj, 6.0, 4.0).outputs['Fac']
    lw = t.n('ShaderNodeLayerWeight', inp={'Blend': 0.3})
    e = t.math('MULTIPLY', t.maprange(n, 0.3, 0.7, 0.85, 1.1), 0.32)
    col = t.mix(t.maprange(n, 0.35, 0.65, 0, 1), (0.62, 0.55, 0.4), (0.55, 0.47, 0.33))
    b = t.bsdf(Base_Color=col, Roughness=0.35, Emission_Color=(1.0, 0.7, 0.38), Emission_Strength=e)
    return t.done(b.outputs[0])


def shrub_mat():
    t = NT('Shrub')
    tc = t.n('ShaderNodeTexCoord')
    obj = tc.outputs['Object']
    oi = t.n('ShaderNodeObjectInfo')
    n = t.noise(obj, 4.0, 5.0, 0.7).outputs['Fac']
    v = t.math('ADD', t.math('MULTIPLY', oi.outputs['Random'], 0.6), t.math('MULTIPLY', n, 0.6))
    col = t.ramp(v, [(0.2, (0.018, 0.03, 0.012)), (0.55, (0.035, 0.045, 0.016)), (0.75, (0.05, 0.042, 0.02)),
                     (0.95, (0.07, 0.055, 0.025))]).outputs[0]
    fine = t.n('ShaderNodeTexVoronoi', inp={'Vector': obj, 'Scale': 14.0})
    b = t.bsdf(Base_Color=col, Roughness=0.85,
               Normal=t.bump(t.math('ADD', fine.outputs['Distance'], t.math('MULTIPLY', n, 0.5)), 1.0, 0.08))
    tr = t.n('ShaderNodeBsdfTranslucent', inp={'Color': (0.02, 0.04, 0.01, 1)})
    ms = t.n('ShaderNodeMixShader', inp={0: 0.15})
    t.l(b.outputs[0], ms.inputs[1])
    t.l(tr.outputs[0], ms.inputs[2])
    return t.done(ms.outputs[0])


def lantern_glass():
    t = NT('Lantern')
    tc = t.n('ShaderNodeTexCoord')
    uv = tc.outputs['UV']
    br = t.n('ShaderNodeTexBrick', inp={'Vector': uv, 'Scale': 1.0, 'Mortar Size': 0.012, 'Brick Width': 0.2,
                                         'Row Height': 0.155, 'Color1': (1, 1, 1, 1), 'Color2': (1, 1, 1, 1),
                                         'Mortar': (0, 0, 0, 1)}, offset=0.0)
    lw = t.n('ShaderNodeLayerWeight', inp={'Blend': 0.45})
    face = t.maprange(lw.outputs['Facing'], 0.0, 1.0, 1.0, 0.25)
    flick = t.maprange(t.noise(tc.outputs['Object'], 3.0, 2.0).outputs['Fac'], 0.3, 0.7, 0.7, 1.2)
    e = t.math('MULTIPLY', t.math('MULTIPLY', face, flick), t.maprange(br.outputs['Fac'], 0.0, 1.0, 1.0, 0.0))
    col = t.mix(face, (1.0, 0.22, 0.03), (1.0, 0.55, 0.16))
    b = t.bsdf(Base_Color=(0.03, 0.02, 0.012), Roughness=0.2, Emission_Color=col,
               Emission_Strength=t.math('MULTIPLY', e, 1.1))
    return t.done(b.outputs[0])


def simple(name, col, rough=0.6, metal=0.0, emit=None, estr=0.0, bumpscale=None, bumpstr=0.3):
    t = NT(name)
    kw = dict(Base_Color=col, Roughness=rough, Metallic=metal)
    if emit is not None:
        kw['Emission_Color'] = emit
        kw['Emission_Strength'] = estr
    if bumpscale:
        tc = t.n('ShaderNodeTexCoord')
        kw['Normal'] = t.bump(t.noise(tc.outputs['Object'], bumpscale, 5).outputs['Fac'], bumpstr, 0.05)
    b = t.bsdf(**kw)
    return t.done(b.outputs[0])


def wood():
    t = NT('Wood')
    tc = t.n('ShaderNodeTexCoord')
    uv = tc.outputs['UV']
    br = t.n('ShaderNodeTexBrick', inp={'Vector': uv, 'Scale': 1.0, 'Mortar Size': 0.006, 'Brick Width': 2.4,
                                         'Row Height': 0.22, 'Color1': (1, 1, 1, 1), 'Color2': (0, 0, 0, 1),
                                         'Mortar': (0, 0, 0, 1)})
    sep = t.n('ShaderNodeSeparateXYZ', inp={'Vector': uv})
    gv = t.n('ShaderNodeCombineXYZ')
    t.l(t.math('MULTIPLY', sep.outputs[0], 0.4), gv.inputs[0])
    t.l(t.math('MULTIPLY', sep.outputs[1], 12.0), gv.inputs[1])
    grain = t.noise(gv.outputs[0], 3.0, 5).outputs['Fac']
    var = t.n('ShaderNodeSeparateColor', inp={'Color': br.outputs['Color']}).outputs[0]
    col = t.ramp(t.math('ADD', t.math('MULTIPLY', grain, 0.6), t.math('MULTIPLY', var, 0.4)),
                 [(0.2, (0.035, 0.022, 0.014)), (0.6, (0.075, 0.048, 0.028)), (0.9, (0.11, 0.075, 0.045))]).outputs[0]
    b = t.bsdf(Base_Color=col, Roughness=0.78,
               Normal=t.bump(t.math('ADD', t.math('MULTIPLY', br.outputs['Fac'], -1), t.math('MULTIPLY', grain, 0.3)), 0.4, 0.02))
    return t.done(b.outputs[0])


# ======================================================================= rock
def rock():
    t = NT('Rock')
    tc = t.n('ShaderNodeTexCoord')
    obj = tc.outputs['Object']
    geo_ = t.n('ShaderNodeNewGeometry')
    sep = t.n('ShaderNodeSeparateXYZ', inp={'Vector': obj})
    z = sep.outputs[2]
    # strata bands
    wv = t.n('ShaderNodeTexWave', wave_type='BANDS', bands_direction='Z',
             inp={'Vector': obj, 'Scale': 0.028, 'Distortion': 9.0, 'Detail': 4.0, 'Detail Scale': 1.4,
                  'Detail Roughness': 0.7})
    band = wv.outputs['Fac']
    # strata only faintly, broken up by large patches of differently weathered rock
    patch = t.noise(obj, 0.03, 4.0, 0.6).outputs['Fac']
    c1 = t.ramp(patch, [(0.3, (0.062, 0.06, 0.056)), (0.5, (0.1, 0.094, 0.084)), (0.68, (0.125, 0.117, 0.1)),
                        (0.8, (0.085, 0.085, 0.08))]).outputs[0]
    c1 = t.mix(t.math('MULTIPLY', t.maprange(band, 0.2, 0.9, 0.0, 1.0), 0.28), c1, (0.18, 0.165, 0.14))
    n1 = t.noise(obj, 0.12, 5.0, 0.6).outputs['Fac']
    c1 = t.mix(t.maprange(n1, 0.4, 0.7, 0, 0.5), c1, (0.06, 0.058, 0.055))
    # lichen crusts: pale grey-green / ochre blotches
    lich = t.maprange(t.noise(obj, 0.9, 5.0, 0.7).outputs['Fac'], 0.6, 0.72, 0.0, 0.6)
    lc = t.mix(t.noise(obj, 0.2, 2).outputs['Fac'], (0.2, 0.21, 0.17), (0.22, 0.18, 0.1))
    c1 = t.mix(lich, c1, lc)
    # cracks
    # fractures: noise-warped, squashed vertically so joints run up and down the face
    wn = t.noise(obj, 0.25, 3.0, 0.5)
    wv = t.n('ShaderNodeVectorMath', operation='MULTIPLY_ADD')
    t.l(wn.outputs['Color'], wv.inputs[0])
    wv.inputs[1].default_value = (3.0, 3.0, 3.0)
    t.l(obj, wv.inputs[2])
    sq = t.n('ShaderNodeVectorMath', operation='MULTIPLY', inp={0: wv.outputs[0], 1: (1.0, 1.0, 0.35)})
    vor = t.n('ShaderNodeTexVoronoi', feature='DISTANCE_TO_EDGE', inp={'Vector': sq.outputs[0], 'Scale': 0.22, 'Randomness': 1.0})
    crack = t.math('MULTIPLY', t.maprange(vor.outputs['Distance'], 0.0, 0.03, 1.0, 0.0),
                   t.maprange(t.noise(obj, 0.15, 2.0).outputs['Fac'], 0.4, 0.6, 0.2, 1.0))
    vor2 = t.n('ShaderNodeTexVoronoi', feature='DISTANCE_TO_EDGE', inp={'Vector': wv.outputs[0], 'Scale': 1.1, 'Randomness': 1.0})
    crack2 = t.math('MULTIPLY', t.maprange(vor2.outputs['Distance'], 0.0, 0.03, 1.0, 0.0),
                    t.maprange(t.noise(obj, 0.4, 2.0).outputs['Fac'], 0.45, 0.6, 0.0, 0.8))
    ao = t.n('ShaderNodeAmbientOcclusion', inp={'Distance': 3.0}, samples=8)
    occl = t.maprange(ao.outputs['AO'], 0.3, 0.95, 1.0, 0.0)
    col = t.mix(t.math('MAXIMUM', t.math('MULTIPLY', crack, 0.7), t.math('MULTIPLY', occl, 0.8)), c1, (0.025, 0.024, 0.022))
    # moss / grass on ledges
    nz = t.n('ShaderNodeSeparateXYZ', inp={'Vector': geo_.outputs['Normal']}).outputs[2]
    ledge = t.maprange(nz, 0.45, 0.8, 0.0, 1.0)
    mn = t.noise(obj, 0.25, 4.0, 0.6).outputs['Fac']
    mossm = t.math('MULTIPLY', ledge, t.maprange(mn, 0.35, 0.55, 0.2, 1.0), clamp=True)
    wetlow = t.maprange(z, 3.0, 18.0, 0.7, 0.0)
    mossm = t.math('MAXIMUM', mossm, t.math('MULTIPLY', wetlow, t.maprange(mn, 0.45, 0.6, 0, 1)))
    moss = t.mix(t.noise(obj, 1.5, 3).outputs['Fac'], (0.03, 0.05, 0.018), (0.07, 0.08, 0.03))
    col = t.mix(mossm, col, moss)
    # wet dark band at the waterline
    wet = t.maprange(z, 0.2, 2.2, 1.0, 0.0)
    col = t.mix(t.math('MULTIPLY', wet, 0.7), col, (0.015, 0.016, 0.014))
    rough = t.mixf(wet, t.maprange(mossm, 0, 1, 0.75, 0.9), 0.25)
    h = t.math('ADD', t.math('MULTIPLY', crack, -0.6), t.math('MULTIPLY', crack2, -0.25))
    h = t.math('ADD', h, t.math('MULTIPLY', t.noise(obj, 1.2, 8.0, 0.65).outputs['Fac'], 0.9))
    h = t.math('ADD', h, t.math('MULTIPLY', band, 0.15))
    b = t.bsdf(Base_Color=col, Roughness=rough, Normal=t.bump(h, 0.8, 0.25))
    b.inputs['Specular IOR Level'].default_value = 0.22
    return t.done(b.outputs[0])


# ======================================================================= terrain
def terrain():
    t = NT('Ground')
    tc = t.n('ShaderNodeTexCoord')
    obj = tc.outputs['Object']
    geo_ = t.n('ShaderNodeNewGeometry')
    sep = t.n('ShaderNodeSeparateXYZ', inp={'Vector': obj})
    z = sep.outputs[2]
    nz = t.n('ShaderNodeSeparateXYZ', inp={'Vector': geo_.outputs['Normal']}).outputs[2]
    path = t.attr('path').outputs['Fac']
    # moorland: grass / heather / bracken patches
    n1 = t.noise(obj, 0.02, 5.0, 0.6).outputs['Fac']
    n2 = t.noise(obj, 0.15, 4.0, 0.6).outputs['Fac']
    moor = t.ramp(n1, [(0.3, (0.020, 0.032, 0.012)), (0.5, (0.034, 0.045, 0.016)), (0.62, (0.05, 0.04, 0.022)),
                       (0.75, (0.04, 0.025, 0.028))]).outputs[0]
    moor = t.mix(t.maprange(n2, 0.4, 0.7, 0, 0.5), moor, (0.055, 0.05, 0.03))
    # rock outcrops on steep slopes and high up
    steep = t.maprange(nz, 0.86, 0.72, 0.0, 1.0)
    alt = t.maprange(z, 350.0, 800.0, 0.0, 0.8)
    rn = t.noise(obj, 0.05, 4.0).outputs['Fac']
    rockm = t.math('MAXIMUM', steep, t.math('MULTIPLY', alt, t.maprange(rn, 0.4, 0.6, 0.3, 1.0)), clamp=True)
    rockc = t.ramp(t.noise(obj, 0.08, 5).outputs['Fac'], [(0.3, (0.05, 0.049, 0.047)), (0.7, (0.1, 0.095, 0.088))]).outputs[0]
    col = t.mix(rockm, moor, rockc)
    # shore: wet mud/pebbles
    shore = t.maprange(z, 0.0, 1.8, 1.0, 0.0)
    col = t.mix(shore, col, (0.04, 0.036, 0.03))
    under = t.maprange(z, 0.0, -1.0, 0.0, 1.0)
    col = t.mix(under, col, (0.05, 0.045, 0.035))
    # paths
    pn = t.noise(obj, 0.8, 3).outputs['Fac']
    pm = t.math('MULTIPLY', path, t.maprange(pn, 0.2, 0.6, 0.7, 1.0), clamp=True)
    col = t.mix(pm, col, (0.075, 0.065, 0.05))
    h = t.math('ADD', t.math('MULTIPLY', t.noise(obj, 0.6, 6).outputs['Fac'], 1.0), t.math('MULTIPLY', rockm, t.noise(obj, 0.2, 6).outputs['Fac']))
    rough = t.mixf(shore, 0.97, 0.35)
    b = t.bsdf(Base_Color=col, Roughness=rough, Normal=t.bump(h, 0.6, 0.5))
    b.inputs['Specular IOR Level'].default_value = 0.15
    return t.done(b.outputs[0])


def water():
    t = NT('Water')
    tc = t.n('ShaderNodeTexCoord')
    obj = tc.outputs['Object']
    # wind ripples: stretched noise + fine noise
    sep = t.n('ShaderNodeSeparateXYZ', inp={'Vector': obj})
    wv = t.n('ShaderNodeCombineXYZ')
    t.l(t.math('MULTIPLY', sep.outputs[0], 0.25), wv.inputs[0])
    t.l(t.math('MULTIPLY', sep.outputs[1], 1.6), wv.inputs[1])
    r1 = t.noise(wv.outputs[0], 1.2, 6.0, 0.55).outputs['Fac']
    r2 = t.noise(wv.outputs[0], 5.0, 4.0, 0.5).outputs['Fac']
    r3 = t.noise(obj, 0.02, 3.0, 0.5).outputs['Fac']
    calm = t.maprange(r3, 0.35, 0.65, 0.35, 1.0)
    h = t.math('MULTIPLY', t.math('ADD', r1, t.math('MULTIPLY', r2, 0.35)), calm)
    b = t.bsdf(Base_Color=(0.02, 0.03, 0.035), Roughness=0.012, Transmission_Weight=1.0, IOR=1.333,
               Normal=t.bump(h, 0.12, 0.03))
    b.inputs['Specular IOR Level'].default_value = 0.5
    vol = t.n('ShaderNodeVolumeAbsorption', inp={'Color': (0.35, 0.55, 0.5, 1), 'Density': 0.35})
    return t.done(b.outputs[0], vol=vol.outputs[0])


def foliage():
    t = NT('Conifer')
    tc = t.n('ShaderNodeTexCoord')
    obj = tc.outputs['Object']
    oi = t.n('ShaderNodeObjectInfo')
    n = t.noise(obj, 3.0, 4).outputs['Fac']
    var = t.math('ADD', oi.outputs['Random'], t.math('MULTIPLY', n, 0.5))
    col = t.ramp(var, [(0.2, (0.012, 0.024, 0.012)), (0.6, (0.022, 0.04, 0.018)), (1.0, (0.035, 0.05, 0.025))]).outputs[0]
    b = t.bsdf(Base_Color=col, Roughness=0.7, Subsurface_Weight=0.0,
               Normal=t.bump(t.noise(obj, 12.0, 4).outputs['Fac'], 0.6, 0.1))
    tr = t.n('ShaderNodeBsdfTranslucent', inp={'Color': (0.02, 0.05, 0.015, 1)})
    ms = t.n('ShaderNodeMixShader', inp={0: 0.2})
    t.l(b.outputs[0], ms.inputs[1])
    t.l(tr.outputs[0], ms.inputs[2])
    return t.done(ms.outputs[0])


def build_all():
    stone('Stone', (0.27, 0.25, 0.22), 0.78, 0.36)
    stone('StoneTrim', (0.25, 0.235, 0.205), 0.5, 0.3)
    slate()
    copper()
    glass()
    wood()
    rock()
    terrain()
    water()
    foliage()
    interior()
    simple('Iron', (0.02, 0.02, 0.022), 0.45, 0.8)
    simple('Gold', (0.8, 0.55, 0.18), 0.3, 1.0)
    simple('Bark', (0.03, 0.022, 0.016), 0.9, bumpscale=6.0, bumpstr=0.5)
    lantern_glass()
    clock_dial()
    gg = NT('GreenhouseGlass')
    b = gg.bsdf(Base_Color=(0.75, 0.85, 0.78), Roughness=0.12, Transmission_Weight=1.0, IOR=1.45)
    gg.done(b.outputs[0])
    stone('Paving', (0.11, 0.105, 0.097), 1.1, 0.8)
    bpy.data.materials['Paving'].node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.1
    simple('Soil', (0.03, 0.022, 0.015), 0.95, bumpscale=6.0, bumpstr=0.5)
    simple('Plaster', (0.2, 0.18, 0.15), 0.9, bumpscale=3.0, bumpstr=0.25)
    simple('Beam', (0.02, 0.013, 0.008), 0.8, bumpscale=4.0, bumpstr=0.3)
    simple('Frame', (0.02, 0.03, 0.025), 0.5, 0.6)
    shrub_mat()
    simple('Plant', (0.02, 0.06, 0.015), 0.7, bumpscale=8.0, bumpstr=0.6)
    return 'ok'
