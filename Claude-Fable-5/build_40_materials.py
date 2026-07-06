"""Materials pass: rewrite node trees of all role materials in place.
All procedural — no image textures."""
import bpy
import hog

D = 300  # node layout spacing


def tree_of(name):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        m.use_fake_user = True
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    return m, nt


def N(nt, typ, x=0, y=0, **kw):
    n = nt.nodes.new(typ)
    n.location = (x * D, y * D)
    for k, v in kw.items():
        if k == 'inputs':
            for ik, iv in v.items():
                n.inputs[ik].default_value = iv
        else:
            setattr(n, k, v)
    return n


def L(nt, a, b):
    nt.links.new(a, b)


def ramp(nt, x, y, stops):
    """stops: list of (pos, (r,g,b,a))"""
    n = N(nt, 'ShaderNodeValToRGB', x, y)
    cr = n.color_ramp
    while len(cr.elements) > 1:
        cr.elements.remove(cr.elements[-1])
    cr.elements[0].position = stops[0][0]
    cr.elements[0].color = stops[0][1]
    for p, c in stops[1:]:
        e = cr.elements.new(p)
        e.color = c
    return n


def mix(nt, x, y, blend='MIX'):
    n = N(nt, 'ShaderNodeMix', x, y)
    n.data_type = 'RGBA'
    n.blend_type = blend
    return n


# ================================================================ WallStone
def build_wall(name='WallStone', base_hues=None, grime=0.5, moss=0.55):
    m, nt = tree_of(name)
    out = N(nt, 'ShaderNodeOutputMaterial', 10, 0)
    bsdf = N(nt, 'ShaderNodeBsdfPrincipled', 8, 0,
             inputs={'Roughness': 0.86, 'Specular IOR Level': 0.25})
    tc = N(nt, 'ShaderNodeTexCoord', -6, 0)

    # quarry batches: large-scale hue variation
    n_batch = N(nt, 'ShaderNodeTexNoise', -4, 2, inputs={'Scale': 0.012,
                                                         'Detail': 2.0})
    hues = base_hues or [(0.360, 0.328, 0.278, 1), (0.300, 0.282, 0.248, 1),
                         (0.410, 0.356, 0.288, 1), (0.328, 0.310, 0.294, 1)]
    r_batch = ramp(nt, -2.6, 2, [(0.30, hues[0]), (0.48, hues[1]),
                                 (0.62, hues[2]), (0.75, hues[3])])
    L(nt, tc.outputs['Object'], n_batch.inputs['Vector'])
    L(nt, n_batch.outputs['Fac'], r_batch.inputs['Fac'])

    # medium mottle
    n_mot = N(nt, 'ShaderNodeTexNoise', -4, 1, inputs={'Scale': 0.35,
                                                       'Detail': 5.0})
    L(nt, tc.outputs['Object'], n_mot.inputs['Vector'])
    m_mot = mix(nt, -1.5, 1.6, 'OVERLAY')
    m_mot.inputs['Factor'].default_value = 0.22
    L(nt, r_batch.outputs['Color'], m_mot.inputs['A'])
    L(nt, n_mot.outputs['Color'], m_mot.inputs['B'])

    # vertical grime streaks (stretched noise), stronger low + under ledges
    map_st = N(nt, 'ShaderNodeMapping', -4.6, -0.6,
               inputs={'Scale': (3.0, 3.0, 0.25)})
    L(nt, tc.outputs['Object'], map_st.inputs['Vector'])
    n_st = N(nt, 'ShaderNodeTexNoise', -3.6, -0.6, inputs={'Scale': 1.0,
                                                           'Detail': 4.0})
    L(nt, map_st.outputs['Vector'], n_st.inputs['Vector'])
    r_st = ramp(nt, -2.6, -0.6, [(0.42, (0, 0, 0, 1)), (0.62, (1, 1, 1, 1))])
    L(nt, n_st.outputs['Fac'], r_st.inputs['Fac'])
    ao = N(nt, 'ShaderNodeAmbientOcclusion', -3.6, -1.6,
           inputs={'Distance': 2.2})
    ao_inv = N(nt, 'ShaderNodeMath', -2.6, -1.6, operation='SUBTRACT',
               inputs={0: 1.0})
    L(nt, ao.outputs['AO'], ao_inv.inputs[1])
    grime_f = N(nt, 'ShaderNodeMath', -1.6, -1.1, operation='MAXIMUM')
    st_scaled = N(nt, 'ShaderNodeMath', -2.0, -0.75, operation='MULTIPLY',
                  inputs={1: 0.8})
    L(nt, r_st.outputs['Color'], st_scaled.inputs[0])
    L(nt, st_scaled.outputs['Value'], grime_f.inputs[0])
    L(nt, ao_inv.outputs['Value'], grime_f.inputs[1])
    m_grime = mix(nt, 0.5, 1.2, 'MULTIPLY')
    m_grime.inputs['B'].default_value = (0.30, 0.27, 0.24, 1)
    gf = N(nt, 'ShaderNodeMath', -0.5, 0.8, operation='MULTIPLY',
           inputs={1: grime})
    L(nt, grime_f.outputs['Value'], gf.inputs[0])
    L(nt, gf.outputs['Value'], m_grime.inputs['Factor'])
    L(nt, m_mot.outputs['Result'], m_grime.inputs['A'])

    # moss creeping at low z + crevices
    sep = N(nt, 'ShaderNodeSeparateXYZ', -4.6, -2.6)
    L(nt, tc.outputs['Object'], sep.inputs['Vector'])
    z_low = N(nt, 'ShaderNodeMapRange', -3.6, -2.6,
              inputs={'From Min': 78.0, 'From Max': 60.0,
                      'To Min': 0.0, 'To Max': 1.0})
    L(nt, sep.outputs['Z'], z_low.inputs['Value'])
    n_moss = N(nt, 'ShaderNodeTexNoise', -3.6, -3.4, inputs={'Scale': 0.8,
                                                             'Detail': 5.0})
    L(nt, tc.outputs['Object'], n_moss.inputs['Vector'])
    r_moss = ramp(nt, -2.6, -3.4, [(0.52, (0, 0, 0, 1)),
                                   (0.72, (1, 1, 1, 1))])
    L(nt, n_moss.outputs['Fac'], r_moss.inputs['Fac'])
    moss_m = N(nt, 'ShaderNodeMath', -1.6, -2.9, operation='MULTIPLY')
    L(nt, z_low.outputs['Result'], moss_m.inputs[0])
    L(nt, r_moss.outputs['Color'], moss_m.inputs[1])
    moss_m2 = N(nt, 'ShaderNodeMath', -0.8, -2.9, operation='MULTIPLY',
                inputs={1: moss})
    L(nt, moss_m.outputs['Value'], moss_m2.inputs[0])
    m_moss = mix(nt, 1.6, 0.9)
    m_moss.inputs['B'].default_value = (0.068, 0.092, 0.038, 1)
    L(nt, moss_m2.outputs['Value'], m_moss.inputs['Factor'])
    L(nt, m_grime.outputs['Result'], m_moss.inputs['A'])

    # edge wear: bevel-based edge lightening
    bev = N(nt, 'ShaderNodeBevel', -3.0, -4.2, samples=4,
            inputs={'Radius': 0.05})
    geo = N(nt, 'ShaderNodeNewGeometry', -3.0, -4.9)
    vsub = N(nt, 'ShaderNodeVectorMath', -2.2, -4.5, operation='DOT_PRODUCT')
    L(nt, bev.outputs['Normal'], vsub.inputs[0])
    L(nt, geo.outputs['Normal'], vsub.inputs[1])
    edge = N(nt, 'ShaderNodeMapRange', -1.4, -4.5,
             inputs={'From Min': 0.92, 'From Max': 0.999,
                     'To Min': 1.0, 'To Max': 0.0})
    L(nt, vsub.outputs['Value'], edge.inputs['Value'])
    m_edge = mix(nt, 2.6, 0.6, 'SCREEN')
    m_edge.inputs['B'].default_value = (0.22, 0.20, 0.17, 1)
    ew = N(nt, 'ShaderNodeMath', 1.8, -0.4, operation='MULTIPLY',
           inputs={1: 0.5})
    L(nt, edge.outputs['Result'], ew.inputs[0])
    L(nt, ew.outputs['Value'], m_edge.inputs['Factor'])
    L(nt, m_moss.outputs['Result'], m_edge.inputs['A'])
    L(nt, m_edge.outputs['Result'], bsdf.inputs['Base Color'])

    # bump: mortar courses + stone crackle + fine grain
    map_br = N(nt, 'ShaderNodeMapping', -4.6, 3.6,
               inputs={'Scale': (1.0, 1.0, 1.0)})
    L(nt, tc.outputs['Object'], map_br.inputs['Vector'])
    sep2 = N(nt, 'ShaderNodeSeparateXYZ', -3.8, 3.6)
    L(nt, map_br.outputs['Vector'], sep2.inputs['Vector'])
    addxy = N(nt, 'ShaderNodeMath', -3.0, 3.8, operation='ADD')
    L(nt, sep2.outputs['X'], addxy.inputs[0])
    L(nt, sep2.outputs['Y'], addxy.inputs[1])
    comb = N(nt, 'ShaderNodeCombineXYZ', -2.2, 3.6, inputs={'Z': 0.0})
    L(nt, addxy.outputs['Value'], comb.inputs['X'])
    L(nt, sep2.outputs['Z'], comb.inputs['Y'])
    brick = N(nt, 'ShaderNodeTexBrick', -1.4, 3.6,
              inputs={'Scale': 1.0, 'Mortar Size': 0.03, 'Bias': 0.0,
                      'Brick Width': 1.7, 'Row Height': 0.55})
    brick.offset = 0.5
    L(nt, comb.outputs['Vector'], brick.inputs['Vector'])
    n_crack = N(nt, 'ShaderNodeTexVoronoi', -1.4, 2.6, feature='F2',
                inputs={'Scale': 2.1})
    L(nt, tc.outputs['Object'], n_crack.inputs['Vector'])
    n_fine = N(nt, 'ShaderNodeTexNoise', -1.4, 1.9,
               inputs={'Scale': 18.0, 'Detail': 6.0})
    L(nt, tc.outputs['Object'], n_fine.inputs['Vector'])
    bmix1 = N(nt, 'ShaderNodeMath', -0.4, 3.0, operation='MULTIPLY_ADD',
              inputs={1: 0.35})
    L(nt, n_crack.outputs['Distance'], bmix1.inputs[0])
    L(nt, brick.outputs['Fac'], bmix1.inputs[2])
    bmix2 = N(nt, 'ShaderNodeMath', 0.4, 2.8, operation='MULTIPLY_ADD',
              inputs={1: 0.25})
    L(nt, n_fine.outputs['Fac'], bmix2.inputs[0])
    L(nt, bmix1.outputs['Value'], bmix2.inputs[2])
    bump = N(nt, 'ShaderNodeBump', 5, 2, inputs={'Strength': 0.4,
                                                 'Distance': 0.4})
    L(nt, bmix2.outputs['Value'], bump.inputs['Height'])
    L(nt, bump.outputs['Normal'], bsdf.inputs['Normal'])

    # roughness variation
    r_rough = N(nt, 'ShaderNodeMapRange', 5, -1,
                inputs={'From Min': 0.0, 'From Max': 1.0, 'To Min': 0.78,
                        'To Max': 0.95})
    L(nt, n_mot.outputs['Fac'], r_rough.inputs['Value'])
    L(nt, r_rough.outputs['Result'], bsdf.inputs['Roughness'])
    L(nt, bsdf.outputs['BSDF'], out.inputs['Surface'])
    return m


# ================================================================ RoofSlate
def build_slate(name='RoofSlate'):
    m, nt = tree_of(name)
    out = N(nt, 'ShaderNodeOutputMaterial', 8, 0)
    bsdf = N(nt, 'ShaderNodeBsdfPrincipled', 6, 0,
             inputs={'Roughness': 0.45, 'Specular IOR Level': 0.5})
    tc = N(nt, 'ShaderNodeTexCoord', -5, 0)
    # per-tile variation via voronoi cells
    vor = N(nt, 'ShaderNodeTexVoronoi', -3.5, 1)
    vor.feature = 'F1'
    vor.inputs['Scale'].default_value = 3.2
    L(nt, tc.outputs['Object'], vor.inputs['Vector'])
    r_tiles = ramp(nt, -2.2, 1, [
        (0.0, (0.020, 0.026, 0.038, 1)),
        (0.35, (0.035, 0.045, 0.062, 1)),
        (0.62, (0.028, 0.030, 0.040, 1)),
        (0.85, (0.052, 0.060, 0.080, 1)),
        (1.0, (0.030, 0.026, 0.030, 1))])
    L(nt, vor.outputs['Color'], r_tiles.inputs['Fac'])
    # weathering blotches
    n_w = N(nt, 'ShaderNodeTexNoise', -3.5, -0.6,
            inputs={'Scale': 0.15, 'Detail': 4.0})
    L(nt, tc.outputs['Object'], n_w.inputs['Vector'])
    m_w = mix(nt, -0.8, 0.6, 'OVERLAY')
    m_w.inputs['Factor'].default_value = 0.35
    L(nt, r_tiles.outputs['Color'], m_w.inputs['A'])
    L(nt, n_w.outputs['Color'], m_w.inputs['B'])
    # subtle moss on roofs low areas
    L(nt, m_w.outputs['Result'], bsdf.inputs['Base Color'])
    # bump: tile rows (z bands) + cell edges
    sep = N(nt, 'ShaderNodeSeparateXYZ', -3.5, 2.6)
    L(nt, tc.outputs['Object'], sep.inputs['Vector'])
    rows = N(nt, 'ShaderNodeMath', -2.6, 2.6, operation='FRACT')
    zscale = N(nt, 'ShaderNodeMath', -3.0, 3.2, operation='MULTIPLY',
               inputs={1: 1.8})
    L(nt, sep.outputs['Z'], zscale.inputs[0])
    L(nt, zscale.outputs['Value'], rows.inputs[0])
    vor2 = N(nt, 'ShaderNodeTexVoronoi', -2.6, 1.9, feature='DISTANCE_TO_EDGE',
             inputs={'Scale': 3.2})
    L(nt, tc.outputs['Object'], vor2.inputs['Vector'])
    edge_r = ramp(nt, -1.8, 1.9, [(0.0, (0, 0, 0, 1)), (0.12, (1, 1, 1, 1))])
    L(nt, vor2.outputs['Distance'], edge_r.inputs['Fac'])
    bsum = N(nt, 'ShaderNodeMath', -0.8, 2.2, operation='MULTIPLY_ADD',
             inputs={1: 0.4})
    L(nt, rows.outputs['Value'], bsum.inputs[0])
    L(nt, edge_r.outputs['Color'], bsum.inputs[2])
    bump = N(nt, 'ShaderNodeBump', 3, 1.4, inputs={'Strength': 0.20,
                                                   'Distance': 0.15})
    L(nt, bsum.outputs['Value'], bump.inputs['Height'])
    L(nt, bump.outputs['Normal'], bsdf.inputs['Normal'])
    L(nt, bsdf.outputs['BSDF'], out.inputs['Surface'])
    return m


# ================================================================ Copper
def build_copper(name='RoofCopper'):
    m, nt = tree_of(name)
    out = N(nt, 'ShaderNodeOutputMaterial', 6, 0)
    bsdf = N(nt, 'ShaderNodeBsdfPrincipled', 4, 0,
             inputs={'Roughness': 0.5, 'Metallic': 0.25})
    tc = N(nt, 'ShaderNodeTexCoord', -3, 0)
    n1 = N(nt, 'ShaderNodeTexNoise', -2, 0.6, inputs={'Scale': 0.6,
                                                      'Detail': 5.0})
    L(nt, tc.outputs['Object'], n1.inputs['Vector'])
    r1 = ramp(nt, -1, 0.6, [
        (0.30, (0.045, 0.135, 0.108, 1)),     # deep verdigris
        (0.55, (0.086, 0.192, 0.150, 1)),     # patina green
        (0.75, (0.128, 0.110, 0.058, 1)),     # worn bronze
        (0.92, (0.190, 0.100, 0.048, 1))])    # raw copper streak
    L(nt, n1.outputs['Fac'], r1.inputs['Fac'])
    L(nt, r1.outputs['Color'], bsdf.inputs['Base Color'])
    n2 = N(nt, 'ShaderNodeTexNoise', -2, -0.8, inputs={'Scale': 8.0,
                                                       'Detail': 5.0})
    L(nt, tc.outputs['Object'], n2.inputs['Vector'])
    bump = N(nt, 'ShaderNodeBump', 2, -0.8, inputs={'Strength': 0.12,
                                                    'Distance': 0.2})
    L(nt, n2.outputs['Fac'], bump.inputs['Height'])
    L(nt, bump.outputs['Normal'], bsdf.inputs['Normal'])
    L(nt, bsdf.outputs['BSDF'], out.inputs['Surface'])
    return m


# ================================================================ Windows
def build_window_glass(name='WindowGlass'):
    """Object-random: ~58% lit warm (varying intensity/hue), rest dark glass."""
    m, nt = tree_of(name)
    out = N(nt, 'ShaderNodeOutputMaterial', 8, 0)
    obj = N(nt, 'ShaderNodeObjectInfo', -6, 1)
    # lit gate: random < 0.58
    lit = N(nt, 'ShaderNodeMath', -4.5, 1.4, operation='LESS_THAN',
            inputs={1: 0.58})
    L(nt, obj.outputs['Random'], lit.inputs[0])
    # second random stream for intensity: fract(random * 13.7)
    r2m = N(nt, 'ShaderNodeMath', -4.5, 0.6, operation='MULTIPLY',
            inputs={1: 13.73})
    L(nt, obj.outputs['Random'], r2m.inputs[0])
    r2 = N(nt, 'ShaderNodeMath', -3.7, 0.6, operation='FRACT')
    L(nt, r2m.outputs['Value'], r2.inputs[0])
    # intensity curve: many dim, few blazing
    ipow = N(nt, 'ShaderNodeMath', -2.9, 0.6, operation='POWER',
             inputs={1: 2.6})
    L(nt, r2.outputs['Value'], ipow.inputs[0])
    iscale = N(nt, 'ShaderNodeMapRange', -2.1, 0.6,
               inputs={'To Min': 0.6, 'To Max': 16.0})
    L(nt, ipow.outputs['Value'], iscale.inputs['Value'])
    gate = N(nt, 'ShaderNodeMath', -1.3, 1.0, operation='MULTIPLY')
    L(nt, lit.outputs['Value'], gate.inputs[0])
    L(nt, iscale.outputs['Result'], gate.inputs[1])
    # warm hue varying between ember and pale gold
    r3m = N(nt, 'ShaderNodeMath', -4.5, -0.4, operation='MULTIPLY',
            inputs={1: 7.31})
    L(nt, obj.outputs['Random'], r3m.inputs[0])
    r3 = N(nt, 'ShaderNodeMath', -3.7, -0.4, operation='FRACT')
    L(nt, r3m.outputs['Value'], r3.inputs[0])
    hue = ramp(nt, -2.9, -0.4, [
        (0.0, (1.0, 0.32, 0.06, 1)),
        (0.45, (1.0, 0.52, 0.16, 1)),
        (0.8, (1.0, 0.70, 0.32, 1)),
        (1.0, (0.95, 0.80, 0.48, 1))])
    L(nt, r3.outputs['Value'], hue.inputs['Fac'])
    # emission shader + dark glass base
    emis = N(nt, 'ShaderNodeEmission', 2, 1)
    L(nt, hue.outputs['Color'], emis.inputs['Color'])
    L(nt, gate.outputs['Value'], emis.inputs['Strength'])
    glass = N(nt, 'ShaderNodeBsdfPrincipled', 2, -1,
              inputs={'Base Color': (0.01, 0.012, 0.016, 1),
                      'Roughness': 0.08, 'Metallic': 0.4})
    mixs = N(nt, 'ShaderNodeMixShader', 5, 0)
    is_lit = N(nt, 'ShaderNodeMath', 0.5, 2.0, operation='GREATER_THAN',
               inputs={1: 0.01})
    L(nt, gate.outputs['Value'], is_lit.inputs[0])
    L(nt, is_lit.outputs['Value'], mixs.inputs['Fac'])
    L(nt, glass.outputs['BSDF'], mixs.inputs[1])
    L(nt, emis.outputs['Emission'], mixs.inputs[2])
    L(nt, mixs.outputs['Shader'], out.inputs['Surface'])
    return m


# ================================================================ Water
def build_water(name='Water'):
    m, nt = tree_of(name)
    out = N(nt, 'ShaderNodeOutputMaterial', 8, 0)
    bsdf = N(nt, 'ShaderNodeBsdfPrincipled', 5, 0,
             inputs={'Base Color': (0.28, 0.34, 0.36, 1),
                     'Roughness': 0.05, 'IOR': 1.333,
                     'Transmission Weight': 1.0})
    tc = N(nt, 'ShaderNodeTexCoord', -5, 0)
    # two scales of waves, anisotropic stretch
    map1 = N(nt, 'ShaderNodeMapping', -4, 1,
             inputs={'Scale': (1.0, 1.6, 1.0)})
    L(nt, tc.outputs['Object'], map1.inputs['Vector'])
    n1 = N(nt, 'ShaderNodeTexNoise', -3, 1,
           inputs={'Scale': 0.08, 'Detail': 6.0, 'Roughness': 0.55})
    L(nt, map1.outputs['Vector'], n1.inputs['Vector'])
    n2 = N(nt, 'ShaderNodeTexNoise', -3, -0.5,
           inputs={'Scale': 0.9, 'Detail': 5.0})
    L(nt, map1.outputs['Vector'], n2.inputs['Vector'])
    badd = N(nt, 'ShaderNodeMath', -1.8, 0.3, operation='MULTIPLY_ADD',
             inputs={1: 0.35})
    L(nt, n2.outputs['Fac'], badd.inputs[0])
    L(nt, n1.outputs['Fac'], badd.inputs[2])
    bump = N(nt, 'ShaderNodeBump', 2, 0.6, inputs={'Strength': 0.45,
                                                   'Distance': 0.04})
    L(nt, badd.outputs['Value'], bump.inputs['Height'])
    L(nt, bump.outputs['Normal'], bsdf.inputs['Normal'])
    L(nt, bsdf.outputs['BSDF'], out.inputs['Surface'])
    # deep absorption volume
    vol = N(nt, 'ShaderNodeVolumeAbsorption', 5, -2,
            inputs={'Color': (0.20, 0.33, 0.30, 1), 'Density': 0.35})
    L(nt, vol.outputs['Volume'], out.inputs['Volume'])
    return m


# ================================================================ Rock/Terrain
def build_rock(name='Rock'):
    m, nt = tree_of(name)
    out = N(nt, 'ShaderNodeOutputMaterial', 10, 0)
    bsdf = N(nt, 'ShaderNodeBsdfPrincipled', 8, 0,
             inputs={'Roughness': 0.94, 'Specular IOR Level': 0.15})
    tc = N(nt, 'ShaderNodeTexCoord', -7, 0)
    geo = N(nt, 'ShaderNodeNewGeometry', -7, -2)
    sep = N(nt, 'ShaderNodeSeparateXYZ', -6, 0.6)
    L(nt, tc.outputs['Object'], sep.inputs['Vector'])

    # --- strata bands on rock: warped sine of z
    warp = N(nt, 'ShaderNodeTexNoise', -6, 1.6, inputs={'Scale': 0.02,
                                                        'Detail': 3.0})
    L(nt, tc.outputs['Object'], warp.inputs['Vector'])
    zw = N(nt, 'ShaderNodeMath', -5.2, 1.2, operation='MULTIPLY_ADD',
           inputs={1: 34.0})
    L(nt, warp.outputs['Fac'], zw.inputs[0])
    zfreq = N(nt, 'ShaderNodeMath', -5.8, 0.9, operation='MULTIPLY', inputs={1: 0.55})
    L(nt, sep.outputs['Z'], zfreq.inputs[0])
    L(nt, zfreq.outputs['Value'], zw.inputs[2])
    zsin = N(nt, 'ShaderNodeMath', -4.4, 1.2, operation='MULTIPLY',
             inputs={1: 0.30})
    zs2 = N(nt, 'ShaderNodeMath', -4.8, 1.7, operation='SINE')
    L(nt, zw.outputs['Value'], zs2.inputs[0])
    L(nt, zs2.outputs['Value'], zsin.inputs[0])
    strata = N(nt, 'ShaderNodeMath', -3.6, 1.2, operation='ADD',
               inputs={1: 0.5})
    L(nt, zsin.outputs['Value'], strata.inputs[0])
    # fade banding out above the crag heights so mountains stay clean
    highz = N(nt, 'ShaderNodeMapRange', -3.6, 2.2,
              inputs={'From Min': 110.0, 'From Max': 200.0})
    L(nt, sep.outputs['Z'], highz.inputs['Value'])
    strata_mix = N(nt, 'ShaderNodeMix', -3.0, 1.7)
    strata_mix.data_type = 'FLOAT'
    strata_mix.inputs['B'].default_value = 0.5
    L(nt, highz.outputs['Result'], strata_mix.inputs['Factor'])
    L(nt, strata.outputs['Value'], strata_mix.inputs['A'])
    r_rock = ramp(nt, -2.8, 1.4, [
        (0.0, (0.085, 0.072, 0.060, 1)),
        (0.45, (0.135, 0.118, 0.098, 1)),
        (0.75, (0.170, 0.152, 0.128, 1)),
        (1.0, (0.105, 0.085, 0.068, 1))])
    L(nt, strata_mix.outputs['Result'], r_rock.inputs['Fac'])
    # mottle rock color
    n_rm = N(nt, 'ShaderNodeTexNoise', -2.8, 0.5, inputs={'Scale': 0.09,
                                                          'Detail': 6.0})
    L(nt, tc.outputs['Object'], n_rm.inputs['Vector'])
    m_rock = mix(nt, -1.8, 1.0, 'OVERLAY')
    m_rock.inputs['Factor'].default_value = 0.3
    L(nt, r_rock.outputs['Color'], m_rock.inputs['A'])
    L(nt, n_rm.outputs['Color'], m_rock.inputs['B'])

    # --- moor grass / heather on flat ground
    n_g1 = N(nt, 'ShaderNodeTexNoise', -2.8, -0.6, inputs={'Scale': 0.05,
                                                           'Detail': 5.0})
    L(nt, tc.outputs['Object'], n_g1.inputs['Vector'])
    r_grass = ramp(nt, -1.8, -0.6, [
        (0.25, (0.045, 0.066, 0.028, 1)),
        (0.5, (0.075, 0.088, 0.032, 1)),
        (0.7, (0.088, 0.068, 0.038, 1)),      # heather brown
        (0.9, (0.052, 0.048, 0.052, 1))])     # purple-grey heath
    L(nt, n_g1.outputs['Fac'], r_grass.inputs['Fac'])

    # slope mask: rock on steep, grass on flat (evaluated on true normal)
    nz = N(nt, 'ShaderNodeSeparateXYZ', -6, -2.8)
    L(nt, geo.outputs['Normal'], nz.inputs['Vector'])
    slope = N(nt, 'ShaderNodeMapRange', -5, -2.8,
              inputs={'From Min': 0.75, 'From Max': 0.92, 'To Min': 1.0,
                      'To Max': 0.0})
    L(nt, nz.outputs['Z'], slope.inputs['Value'])
    m_gr = mix(nt, 0, 0.4)
    L(nt, slope.outputs['Result'], m_gr.inputs['Factor'])
    L(nt, r_grass.outputs['Color'], m_gr.inputs['A'])
    L(nt, m_rock.outputs['Result'], m_gr.inputs['B'])

    # path: worn earth strip via attribute
    at_path = N(nt, 'ShaderNodeAttribute', -1, -1.8, attribute_name='path_w')
    m_path = mix(nt, 1.2, 0.2)
    m_path.inputs['B'].default_value = (0.115, 0.088, 0.055, 1)
    pmul = N(nt, 'ShaderNodeMath', 0.2, -1.2, operation='MULTIPLY',
             inputs={1: 0.85})
    L(nt, at_path.outputs['Fac'], pmul.inputs[0])
    L(nt, pmul.outputs['Value'], m_path.inputs['Factor'])
    L(nt, m_gr.outputs['Result'], m_path.inputs['A'])

    # forest floor darkening under trees
    at_f = N(nt, 'ShaderNodeAttribute', -1, -2.6, attribute_name='forest_w')
    m_ff = mix(nt, 2.2, 0.0, 'MULTIPLY')
    m_ff.inputs['B'].default_value = (0.45, 0.42, 0.35, 1)
    fmul = N(nt, 'ShaderNodeMath', 1.2, -2.2, operation='MULTIPLY',
             inputs={1: 0.7})
    L(nt, at_f.outputs['Fac'], fmul.inputs[0])
    L(nt, fmul.outputs['Value'], m_ff.inputs['Factor'])
    L(nt, m_path.outputs['Result'], m_ff.inputs['A'])

    # snow on high mountains
    zsnow = N(nt, 'ShaderNodeMapRange', 2.2, -1.6,
              inputs={'From Min': 520.0, 'From Max': 700.0, 'To Min': 0.0,
                      'To Max': 1.0})
    L(nt, sep.outputs['Z'], zsnow.inputs['Value'])
    n_sn = N(nt, 'ShaderNodeTexNoise', 1.6, -2.9, inputs={'Scale': 0.02,
                                                          'Detail': 4.0})
    L(nt, tc.outputs['Object'], n_sn.inputs['Vector'])
    snm = N(nt, 'ShaderNodeMath', 3.0, -1.9, operation='MULTIPLY_ADD',
            inputs={1: 0.5})
    L(nt, n_sn.outputs['Fac'], snm.inputs[0])
    L(nt, zsnow.outputs['Result'], snm.inputs[2])
    sn_clamp = N(nt, 'ShaderNodeMapRange', 3.8, -1.9,
                 inputs={'From Min': 0.55, 'From Max': 0.9})
    L(nt, snm.outputs['Value'], sn_clamp.inputs['Value'])
    m_snow = mix(nt, 4.6, 0.4)
    m_snow.inputs['B'].default_value = (0.55, 0.62, 0.72, 1)
    L(nt, sn_clamp.outputs['Result'], m_snow.inputs['Factor'])
    L(nt, m_ff.outputs['Result'], m_snow.inputs['A'])
    L(nt, m_snow.outputs['Result'], bsdf.inputs['Base Color'])

    # bump: rugged
    n_b1 = N(nt, 'ShaderNodeTexVoronoi', 4, 2.6, feature='F2',
             inputs={'Scale': 0.25})
    L(nt, tc.outputs['Object'], n_b1.inputs['Vector'])
    n_b2 = N(nt, 'ShaderNodeTexNoise', 4, 1.8, inputs={'Scale': 2.5,
                                                       'Detail': 7.0})
    L(nt, tc.outputs['Object'], n_b2.inputs['Vector'])
    bsum = N(nt, 'ShaderNodeMath', 5, 2.2, operation='MULTIPLY_ADD',
             inputs={1: 0.5})
    L(nt, n_b2.outputs['Fac'], bsum.inputs[0])
    L(nt, n_b1.outputs['Distance'], bsum.inputs[2])
    bump = N(nt, 'ShaderNodeBump', 6.5, 1.6, inputs={'Strength': 0.5,
                                                     'Distance': 1.2})
    L(nt, bsum.outputs['Value'], bump.inputs['Height'])
    L(nt, bump.outputs['Normal'], bsdf.inputs['Normal'])
    L(nt, bsdf.outputs['BSDF'], out.inputs['Surface'])
    return m


# ================================================================ Conifer
def build_conifer(name='Conifer'):
    m, nt = tree_of(name)
    out = N(nt, 'ShaderNodeOutputMaterial', 6, 0)
    bsdf = N(nt, 'ShaderNodeBsdfPrincipled', 4, 0,
             inputs={'Roughness': 0.85, 'Specular IOR Level': 0.15})
    tc = N(nt, 'ShaderNodeTexCoord', -3, 0)
    n1 = N(nt, 'ShaderNodeTexNoise', -2, 0.5, inputs={'Scale': 0.008,
                                                      'Detail': 3.0})
    L(nt, tc.outputs['Object'], n1.inputs['Vector'])
    r1 = ramp(nt, -1, 0.5, [
        (0.3, (0.022, 0.055, 0.028, 1)),
        (0.55, (0.030, 0.072, 0.033, 1)),
        (0.75, (0.045, 0.082, 0.030, 1)),
        (0.95, (0.024, 0.060, 0.045, 1))])
    L(nt, n1.outputs['Fac'], r1.inputs['Fac'])
    n2 = N(nt, 'ShaderNodeTexNoise', -2, -0.8, inputs={'Scale': 3.0,
                                                       'Detail': 5.0})
    L(nt, tc.outputs['Object'], n2.inputs['Vector'])
    m2 = mix(nt, 1, 0.2, 'MULTIPLY')
    m2.inputs['Factor'].default_value = 0.4
    L(nt, r1.outputs['Color'], m2.inputs['A'])
    L(nt, n2.outputs['Color'], m2.inputs['B'])
    L(nt, m2.outputs['Result'], bsdf.inputs['Base Color'])
    bump = N(nt, 'ShaderNodeBump', 2, -1.2, inputs={'Strength': 0.4,
                                                    'Distance': 0.3})
    L(nt, n2.outputs['Fac'], bump.inputs['Height'])
    L(nt, bump.outputs['Normal'], bsdf.inputs['Normal'])
    L(nt, bsdf.outputs['BSDF'], out.inputs['Surface'])
    return m


# ================================================================ small ones
def build_simple():
    # TrimStone: cleaner pale ashlar reusing wall builder with lighter hues
    build_wall('TrimStone',
               base_hues=[(0.34, 0.315, 0.272, 1), (0.30, 0.285, 0.252, 1),
                          (0.37, 0.335, 0.282, 1), (0.315, 0.30, 0.278, 1)],
               grime=0.35, moss=0.3)

    m, nt = tree_of('IronWork')
    out = N(nt, 'ShaderNodeOutputMaterial', 2, 0)
    b = N(nt, 'ShaderNodeBsdfPrincipled', 0, 0,
          inputs={'Base Color': (0.012, 0.012, 0.014, 1), 'Metallic': 0.85,
                  'Roughness': 0.45})
    L(nt, b.outputs['BSDF'], out.inputs['Surface'])

    m, nt = tree_of('Wood')
    out = N(nt, 'ShaderNodeOutputMaterial', 4, 0)
    b = N(nt, 'ShaderNodeBsdfPrincipled', 2, 0,
          inputs={'Roughness': 0.8})
    tc = N(nt, 'ShaderNodeTexCoord', -2, 0)
    mp = N(nt, 'ShaderNodeMapping', -1.2, 0, inputs={'Scale': (1, 1, 0.08)})
    L(nt, tc.outputs['Object'], mp.inputs['Vector'])
    n1 = N(nt, 'ShaderNodeTexNoise', -0.5, 0.5, inputs={'Scale': 3.0,
                                                        'Detail': 6.0})
    L(nt, mp.outputs['Vector'], n1.inputs['Vector'])
    r1 = ramp(nt, 0.5, 0.5, [(0.3, (0.062, 0.040, 0.024, 1)),
                             (0.7, (0.110, 0.072, 0.042, 1))])
    L(nt, n1.outputs['Fac'], r1.inputs['Fac'])
    L(nt, r1.outputs['Color'], b.inputs['Base Color'])
    bump = N(nt, 'ShaderNodeBump', 1, -1, inputs={'Strength': 0.3})
    L(nt, n1.outputs['Fac'], bump.inputs['Height'])
    L(nt, bump.outputs['Normal'], b.inputs['Normal'])
    L(nt, b.outputs['BSDF'], out.inputs['Surface'])

    # greenhouse glass: cool glass with faint interior warmth
    m, nt = tree_of('GreenhouseGlass')
    out = N(nt, 'ShaderNodeOutputMaterial', 4, 0)
    g = N(nt, 'ShaderNodeBsdfPrincipled', 2, 0,
          inputs={'Base Color': (0.60, 0.72, 0.66, 1), 'Roughness': 0.06,
                  'Transmission Weight': 1.0, 'IOR': 1.45})
    emis = N(nt, 'ShaderNodeEmission', 2, -1.4,
             inputs={'Color': (0.80, 0.80, 0.52, 1), 'Strength': 0.15})
    lw = N(nt, 'ShaderNodeLightPath', 0, -2)
    mixs = N(nt, 'ShaderNodeMixShader', 3.2, -0.5)
    fac = N(nt, 'ShaderNodeMath', 1, -2, operation='MULTIPLY',
            inputs={1: 0.2})
    L(nt, lw.outputs['Is Camera Ray'], fac.inputs[0])
    L(nt, fac.outputs['Value'], mixs.inputs['Fac'])
    L(nt, g.outputs['BSDF'], mixs.inputs[1])
    L(nt, emis.outputs['Emission'], mixs.inputs[2])
    L(nt, mixs.outputs['Shader'], out.inputs['Surface'])

    # clock dial: pale, faintly lit from behind at night
    m, nt = tree_of('ClockDial')
    out = N(nt, 'ShaderNodeOutputMaterial', 2, 0)
    b = N(nt, 'ShaderNodeBsdfPrincipled', 0, 0,
          inputs={'Base Color': (0.88, 0.82, 0.60, 1), 'Roughness': 0.4})
    b.inputs['Emission Color'].default_value = (1.0, 0.75, 0.38, 1)
    b.inputs['Emission Strength'].default_value = 0.7
    L(nt, b.outputs['BSDF'], out.inputs['Surface'])

    # lantern glow brighter
    m, nt = tree_of('LanternGlow')
    out = N(nt, 'ShaderNodeOutputMaterial', 2, 0)
    e = N(nt, 'ShaderNodeEmission', 0, 0,
          inputs={'Color': (1.0, 0.55, 0.18, 1), 'Strength': 300.0})
    L(nt, e.outputs['Emission'], out.inputs['Surface'])

    # lantern cage glass
    m, nt = tree_of('LanternGlass')
    out = N(nt, 'ShaderNodeOutputMaterial', 2, 0)
    b = N(nt, 'ShaderNodeBsdfPrincipled', 0, 0,
          inputs={'Base Color': (0.95, 0.82, 0.55, 1), 'Roughness': 0.12,
                  'Transmission Weight': 1.0, 'IOR': 1.4})
    L(nt, b.outputs['BSDF'], out.inputs['Surface'])

    # dark void (open arches)
    m, nt = tree_of('DarkVoid')
    out = N(nt, 'ShaderNodeOutputMaterial', 2, 0)
    b = N(nt, 'ShaderNodeBsdfDiffuse', 0, 0,
          inputs={'Color': (0.004, 0.004, 0.005, 1)})
    L(nt, b.outputs['BSDF'], out.inputs['Surface'])

    # bark
    m, nt = tree_of('Bark')
    out = N(nt, 'ShaderNodeOutputMaterial', 2, 0)
    b = N(nt, 'ShaderNodeBsdfPrincipled', 0, 0,
          inputs={'Base Color': (0.055, 0.038, 0.026, 1), 'Roughness': 0.95})
    L(nt, b.outputs['BSDF'], out.inputs['Surface'])

    # thatch
    m, nt = tree_of('Thatch')
    out = N(nt, 'ShaderNodeOutputMaterial', 3, 0)
    b = N(nt, 'ShaderNodeBsdfPrincipled', 1.5, 0, inputs={'Roughness': 0.95})
    tc = N(nt, 'ShaderNodeTexCoord', -1.5, 0)
    mp = N(nt, 'ShaderNodeMapping', -0.8, 0, inputs={'Scale': (1, 1, 6.0)})
    L(nt, tc.outputs['Object'], mp.inputs['Vector'])
    n1 = N(nt, 'ShaderNodeTexNoise', 0, 0.5, inputs={'Scale': 2.0,
                                                     'Detail': 6.0})
    L(nt, mp.outputs['Vector'], n1.inputs['Vector'])
    r1 = ramp(nt, 0.7, 0.5, [(0.3, (0.140, 0.090, 0.045, 1)),
                             (0.7, (0.075, 0.048, 0.028, 1))])
    L(nt, n1.outputs['Fac'], r1.inputs['Fac'])
    L(nt, r1.outputs['Color'], b.inputs['Base Color'])
    bmp = N(nt, 'ShaderNodeBump', 0.7, -1, inputs={'Strength': 0.5})
    L(nt, n1.outputs['Fac'], bmp.inputs['Height'])
    L(nt, bmp.outputs['Normal'], b.inputs['Normal'])
    L(nt, b.outputs['BSDF'], out.inputs['Surface'])

    # gold hoops
    m, nt = tree_of('GoldHoop')
    out = N(nt, 'ShaderNodeOutputMaterial', 2, 0)
    b = N(nt, 'ShaderNodeBsdfPrincipled', 0, 0,
          inputs={'Base Color': (0.62, 0.44, 0.10, 1), 'Metallic': 1.0,
                  'Roughness': 0.35})
    L(nt, b.outputs['BSDF'], out.inputs['Surface'])

    # banner cloth
    m, nt = tree_of('Banner')
    out = N(nt, 'ShaderNodeOutputMaterial', 2, 0)
    b = N(nt, 'ShaderNodeBsdfPrincipled', 0, 0,
          inputs={'Base Color': (0.30, 0.05, 0.05, 1), 'Roughness': 0.9})
    L(nt, b.outputs['BSDF'], out.inputs['Surface'])


build_wall('WallStone')
build_slate('RoofSlate')
build_copper('RoofCopper')
build_window_glass('WindowGlass')
build_water('Water')
build_rock('Rock')
build_conifer('Conifer')
build_simple()

# legacy blockout materials that may still be assigned somewhere -> restyle
for legacy, src in (('Stone', 'WallStone'), ('Roof', 'RoofSlate')):
    lm = bpy.data.materials.get(legacy)
    sm = bpy.data.materials.get(src)
    if lm and sm:
        # rebind every user of the legacy material to the real one
        for ob in bpy.data.objects:
            if ob.type != 'MESH':
                continue
            for slot in ob.material_slots:
                if slot.material == lm:
                    slot.material = sm
