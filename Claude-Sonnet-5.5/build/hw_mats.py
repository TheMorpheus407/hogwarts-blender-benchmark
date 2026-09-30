"""Procedural materials for the castle (all shader nodes, no image textures)."""
import bpy
import math
from hw_nodes import NB, get_mat


def _dot(nb, a, b):
    n = nb.vmath('DOT_PRODUCT', a, b)
    return n.outputs[1]


# --------------------------------------------------------------------------------------
# stone family
# --------------------------------------------------------------------------------------

def build_stone(name='M_Stone', pal=((0.44, 0.39, 0.31), (0.36, 0.35, 0.33)), block=(0.62, 0.34), block2=(0.40, 0.21),
                batch_scale=0.10, dirt=1.0, moss=1.0, wear=1.0, bump=1.0, rough=0.84, mortar_col=(0.19, 0.18, 0.165),
                warm=(1.10, 1.0, 0.86), cool=(0.88, 0.95, 1.04), tint=0.55, ashlar_mix=0.35, bevel_r=0.07,
                dark_base=1.0):
    nb = NB(get_mat(name))
    geo = nb.geometry()
    P = geo.outputs['Position']
    N = geo.outputs['Normal']
    uv = nb.texcoord().outputs['UV']
    # regional "quarry batch" variation
    vor = nb.voronoi(P, scale=batch_scale, out='Color')
    batch = nb.rgb2bw(vor)
    low = nb.noise(P, scale=0.03, detail=3, rough=0.6)
    # masonry courses on UV with a slight wobble
    wob = nb.noise(P, scale=2.1, detail=1, rough=0.5, out='Color')
    wob_v = nb.vmath('SUBTRACT', wob, (0.5, 0.5, 0.5)).outputs[0]
    uvw = nb.vmath('ADD', uv, nb.vmath('SCALE', wob_v, scale=0.045).outputs[0]).outputs[0]
    brA = nb.brick(uvw, block[0], block[1], 0.013, 0.16, c1=pal[0], c2=pal[1], cm=mortar_col)
    brB = nb.brick(uvw, block2[0], block2[1], 0.013, 0.16, c1=pal[1], c2=pal[0], cm=mortar_col, offset=0.45)
    rubble = nb.smooth(nb.noise(P, scale=0.05, detail=2, rough=0.5), 0.55, 0.62)
    rubble = nb.mul(rubble, 1.0 - ashlar_mix + 0.0) if False else rubble
    col = nb.mix(rubble, brA.outputs['Color'], brB.outputs['Color'])
    fac = nb.sub(1.0, nb.mix(rubble, brA.outputs['Fac'], brB.outputs['Fac'], dtype='FLOAT'))   # Brick Fac = 1 on MORTAR -> invert
    randb = nb.rgb2bw(brA.outputs['Color'])
    # batch tint
    tint_col = nb.mix(batch, warm, cool)
    col = nb.mix(tint, col, nb.mix(1.0, col, tint_col, blend='MULTIPLY'))
    col = nb.mix(nb.smooth(low, 0.35, 0.65), col, nb.mix(1.0, col, (0.86, 0.9, 0.92, 1.0), blend='MULTIPLY'))
    # dirt: streaks running down from ledges + crevice darkening
    sp = nb.mapping(P, scale=(0.75, 0.75, 0.10))
    streak = nb.smooth(nb.noise(sp, scale=1.0, detail=3, rough=0.6), 0.50, 0.80)
    ao = nb.ao(dist=1.7, samples=6)
    crev = nb.sub(1.0, ao)
    up = nb.smooth(N[2] if False else nb.sepxyz(N).outputs[2], 0.2, 0.9)
    dirt_m = nb.clamp01(nb.add(nb.mul(streak, 0.42 * dirt), nb.mul(crev, 0.85 * dirt)))
    col = nb.mix(nb.mul(dirt_m, 0.75), col, (0.03, 0.028, 0.026, 1.0))
    # moss: lower / wetter surfaces, up-facing ledges, cavities
    z = nb.sepxyz(P).outputs[2]
    wet_h = nb.smooth(z, 95.0, 40.0)
    mossn = nb.smooth(nb.noise(P, scale=3.3, detail=5, rough=0.6), 0.5, 0.68)
    moss_m = nb.mul(mossn, nb.clamp01(nb.mul(wet_h, nb.add(0.22, nb.add(nb.mul(up, 0.75), nb.mul(crev, 0.55))))))
    moss_m = nb.mul(moss_m, moss)
    moss_col = nb.mix(nb.noise(P, scale=14, detail=3), (0.045, 0.085, 0.03, 1.0), (0.08, 0.11, 0.035, 1.0))
    col = nb.mix(moss_m, col, moss_col)
    # edge wear (bevel)
    bev = nb.bevel(bevel_r, 5)
    edge = nb.smooth(nb.sub(1.0, _dot(nb, bev, N)), 0.0, 0.22)
    col = nb.mix(nb.mul(edge, 0.55 * wear), col, nb.mix(1.0, col, (1.7, 1.65, 1.55, 1.0), blend='MULTIPLY'))
    col = nb.mix(1.0, col, (dark_base, dark_base, dark_base, 1.0), blend='MULTIPLY')
    # relief
    fine = nb.noise(P, scale=24, detail=6, rough=0.55)
    mid = nb.noise(P, scale=6.5, detail=3, rough=0.5)
    h = nb.add(nb.add(nb.mul(fac, 0.62), nb.mul(randb, 0.26)), nb.add(nb.mul(fine, 0.32), nb.mul(mid, 0.18)))
    nrm = nb.bump(h, strength=1.0 * bump, dist=0.06, normal=bev)
    rgh = nb.add(rough, nb.sub(nb.mul(fine, 0.14), 0.05))
    rgh = nb.mix(moss_m, rgh, 0.95, dtype='FLOAT')
    bsdf = nb.principled(Base_Color=col, Roughness=rgh, Normal=nrm, Specular_IOR_Level=0.3)
    nb.output(bsdf.outputs[0])
    return nb.mat


# --------------------------------------------------------------------------------------
# slate roof
# --------------------------------------------------------------------------------------

def build_slate(name='M_Slate', tile=(0.30, 0.24)):
    nb = NB(get_mat(name))
    geo = nb.geometry()
    P = geo.outputs['Position']
    N = geo.outputs['Normal']
    uv = nb.texcoord().outputs['UV']
    wob = nb.noise(P, scale=1.4, detail=1, rough=0.5, out='Color')
    wob_v = nb.vmath('SUBTRACT', wob, (0.5, 0.5, 0.5)).outputs[0]
    uvw = nb.vmath('ADD', uv, nb.vmath('SCALE', wob_v, scale=0.012).outputs[0]).outputs[0]
    br = nb.brick(uvw, tile[0], tile[1], 0.012, 0.25, c1=(0.0, 0.0, 0.0), c2=(1.0, 1.0, 1.0), cm=(0.0, 0.0, 0.0), offset=0.5)
    r = nb.rgb2bw(br.outputs['Color'])          # per-tile random 0..1 (mortar = 0)
    fac = nb.sub(1.0, br.outputs['Fac'])         # Brick Fac = 1 on MORTAR -> invert (1 on tile)
    v = nb.sepxyz(uvw).outputs[1]
    f = nb.math('FRACT', nb.math('DIVIDE', v, tile[1]))
    # tile relief: bottom edge proud, sloping back under the next course
    tile_h = nb.add(nb.mul(nb.sub(1.0, f), 0.85), 0.15)
    tile_h = nb.mul(tile_h, fac)
    tilt = nb.mul(nb.sub(r, 0.5), 0.35)
    fine = nb.noise(P, scale=38, detail=5, rough=0.55)
    hgt = nb.add(nb.add(tile_h, tilt), nb.mul(fine, 0.35))
    # colour: blue-grey slate with green/violet tile variation
    dark = nb.mix(r, (0.040, 0.050, 0.072, 1.0), (0.085, 0.098, 0.128, 1.0))
    grn = nb.mix(nb.smooth(nb.noise(P, scale=0.11, detail=2), 0.5, 0.7), dark, (0.045, 0.062, 0.06, 1.0))
    # lichen / moss speckle
    lich = nb.smooth(nb.noise(P, scale=5.2, detail=6, rough=0.62), 0.63, 0.74)
    lich_c = nb.mix(nb.noise(P, scale=21, detail=2), (0.11, 0.12, 0.075, 1.0), (0.17, 0.17, 0.11, 1.0))
    col = nb.mix(nb.mul(lich, 0.75), grn, lich_c)
    # rain streaks down the slope + edge chips
    sp = nb.mapping(uvw, scale=(2.2, 0.14, 1.0))
    stk = nb.smooth(nb.noise(sp, scale=1.0, detail=3), 0.55, 0.78)
    col = nb.mix(nb.mul(stk, 0.35), col, (0.14, 0.15, 0.17, 1.0))
    edge_l = nb.smooth(nb.sub(1.0, f), 0.9, 1.0)
    col = nb.mix(nb.mul(edge_l, 0.4), col, (0.16, 0.17, 0.2, 1.0))
    # per-tile brightness (some tiles lighter / newer) and darker lower edge of every course
    tile_v = nb.add(0.72, nb.mul(nb.math('POWER', r, 1.3), 0.75))
    col = nb.mix(1.0, col, tile_v, blend='MULTIPLY')
    band = nb.smooth(f, 0.0, 0.22)                                 # 0 at the course line, 1 higher up
    horiz = nb.mul(nb.sub(1.0, band), nb.smooth(f, 0.0, 0.02))     # shadow tucked under the tile above
    vert = nb.mul(nb.sub(1.0, fac), band)                          # vertical joints only
    col = nb.mix(nb.mul(vert, 0.55), col, nb.mix(1.0, col, (0.30, 0.30, 0.32, 1.0), blend='MULTIPLY'))
    col = nb.mix(nb.mul(horiz, 0.85), col, nb.mix(1.0, col, (0.32, 0.32, 0.34, 1.0), blend='MULTIPLY'))
    nrm = nb.bump(hgt, strength=1.5, dist=0.06)
    rgh = nb.add(0.40, nb.mul(nb.sub(fine, 0.5), 0.4))
    rgh = nb.mix(lich, rgh, 0.85, dtype='FLOAT')
    bsdf = nb.principled(Base_Color=col, Roughness=nb.add(rgh, 0.10), Normal=nrm, Specular_IOR_Level=0.30)
    nb.output(bsdf.outputs[0])
    return nb.mat


# --------------------------------------------------------------------------------------
# copper with verdigris
# --------------------------------------------------------------------------------------

def build_copper(name='M_Copper'):
    nb = NB(get_mat(name))
    geo = nb.geometry()
    P = geo.outputs['Position']
    uv = nb.texcoord().outputs['UV']
    u = nb.sepxyz(uv).outputs[0]
    z = nb.sepxyz(P).outputs[2]
    fu = nb.math('FRACT', nb.math('DIVIDE', u, 0.62))
    seam = nb.add(nb.smooth(fu, 0.94, 1.0), nb.smooth(fu, 0.06, 0.0))
    n1 = nb.noise(P, scale=2.6, detail=6, rough=0.6)
    n2 = nb.noise(nb.mapping(P, scale=(1.0, 1.0, 0.25)), scale=4.0, detail=4)
    pat = nb.smooth(nb.add(nb.mul(n1, 0.7), nb.mul(n2, 0.5)), 0.42, 0.62)
    patina = nb.mix(nb.noise(P, scale=9, detail=4), (0.06, 0.34, 0.27, 1.0), (0.10, 0.46, 0.38, 1.0))
    copper = (0.52, 0.20, 0.09, 1.0)
    col = nb.mix(pat, copper, patina)
    col = nb.mix(nb.mul(seam, 0.6), col, (0.12, 0.30, 0.24, 1.0))
    h = nb.add(nb.mul(seam, 0.5), nb.mul(n1, 0.25))
    nrm = nb.bump(h, strength=0.9, dist=0.03)
    metal = nb.sub(1.0, pat)
    rgh = nb.mix(pat, 0.34, 0.62, dtype='FLOAT')
    bsdf = nb.principled(Base_Color=col, Metallic=metal, Roughness=rgh, Normal=nrm)
    nb.output(bsdf.outputs[0])
    return nb.mat


# --------------------------------------------------------------------------------------
# windows / glow
# --------------------------------------------------------------------------------------

def build_glass_lit(name='M_GlassLit', strength=7.5):
    nb = NB(get_mat(name))
    geo = nb.geometry()
    P = geo.outputs['Position']
    uv = nb.texcoord().outputs['UV']
    glow = nb.attr('glow').outputs['Fac']
    hue = nb.attr('hue').outputs['Fac']
    seed = nb.attr('seed').outputs['Fac']
    # colour temperature
    warm = nb.ramp(hue, [(0.0, (1.0, 0.33, 0.07)), (0.30, (1.0, 0.52, 0.16)), (0.55, (1.0, 0.72, 0.36)),
                         (0.80, (0.82, 0.86, 1.0)), (1.0, (0.62, 0.74, 1.0))])
    # leaded diamond lattice in window space (u = x, v = height above sill)
    ruv = nb.mapping(uv, rot=(0, 0, math.radians(45)), scale=(1.0, 1.0, 1.0))
    diam = nb.brick(ruv, 0.30, 0.30, 0.028, 0.03, c1=(0.55, 0.55, 0.55), c2=(1.0, 1.0, 1.0), cm=(0.0, 0.0, 0.0), offset=0.0)
    lead = nb.sub(1.0, diam.outputs['Fac'])      # 1 on the glass, 0 on the lead came
    pane_r = nb.rgb2bw(diam.outputs['Color'])
    # "room" variation: gradient + curtain / furniture blotches, per window seed
    vcoord = nb.sepxyz(uv).outputs[1]
    grad = nb.maprange(vcoord, 0.0, 9.0, 0.55, 1.15)
    seedv = nb.combxyz(nb.mul(seed, 37.0), nb.mul(seed, 91.0), nb.mul(seed, 13.0))
    blot = nb.noise(nb.vmath('ADD', nb.mapping(uv, scale=(0.7, 0.7, 0.7)), seedv).outputs[0], scale=1.0, detail=3, rough=0.6)
    blot_m = nb.smooth(blot, 0.45, 0.7)
    room = nb.mul(nb.sub(1.0, nb.mul(blot_m, 0.6)), grad)
    flick = nb.add(0.8, nb.mul(nb.math('SINE', nb.mul(seed, 40.0)), 0.2))
    inten = nb.mul(nb.mul(nb.mul(glow, strength), nb.mul(room, nb.add(0.65, nb.mul(pane_r, 0.5)))), nb.mul(lead, flick))
    emis_col = nb.mix(nb.smooth(inten, 0.0, 25.0), warm, nb.mix(1.0, warm, (1.0, 0.85, 0.6, 1.0), blend='MULTIPLY'))
    bsdf = nb.principled(Base_Color=(0.006, 0.008, 0.012, 1.0), Roughness=0.05, Specular_IOR_Level=0.8, IOR=1.5,
                         Emission_Color=emis_col, Emission_Strength=inten)
    nb.output(bsdf.outputs[0])
    return nb.mat


def build_clockface(name='M_ClockFace'):
    nb = NB(get_mat(name))
    geo = nb.geometry()
    P = geo.outputs['Position']
    n = nb.noise(P, scale=12, detail=4)
    col = nb.mix(n, (0.86, 0.80, 0.62, 1.0), (0.96, 0.9, 0.72, 1.0))
    bsdf = nb.principled(Base_Color=col, Roughness=0.4, Emission_Color=(1.0, 0.82, 0.5, 1.0), Emission_Strength=nb.mul(nb.add(0.7, n), 5.0))
    nb.output(bsdf.outputs[0])
    return nb.mat


def build_lantern_glass(name='M_LanternGlass'):
    nb = NB(get_mat(name))
    geo = nb.geometry()
    P = geo.outputs['Position']
    seed = nb.attr('seed').outputs['Fac']
    hue = nb.attr('hue').outputs['Fac']
    fl = nb.add(0.75, nb.mul(nb.math('SINE', nb.mul(seed, 60.0)), 0.25))
    n = nb.noise(P, scale=40, detail=2)
    col = nb.ramp(hue, [(0.0, (1.0, 0.34, 0.08)), (0.15, (1.0, 0.55, 0.18)), (1.0, (1.0, 0.75, 0.4))])
    bsdf = nb.principled(Base_Color=(0.02, 0.012, 0.006, 1.0), Roughness=0.2, Emission_Color=col,
                         Emission_Strength=nb.mul(fl, nb.add(16.0, nb.mul(n, 8.0))))
    nb.output(bsdf.outputs[0])
    return nb.mat


# --------------------------------------------------------------------------------------
# metals, wood, plaster and small stuff
# --------------------------------------------------------------------------------------

def build_iron(name='M_Iron'):
    nb = NB(get_mat(name))
    P = nb.geometry().outputs['Position']
    n = nb.noise(P, scale=18, detail=5)
    col = nb.mix(n, (0.025, 0.026, 0.03, 1.0), (0.06, 0.05, 0.045, 1.0))
    nrm = nb.bump(n, strength=0.3, dist=0.01)
    bsdf = nb.principled(Base_Color=col, Metallic=0.85, Roughness=nb.add(0.42, nb.mul(n, 0.2)), Normal=nrm)
    nb.output(bsdf.outputs[0])
    return nb.mat


def build_lead(name='M_Lead'):
    nb = NB(get_mat(name))
    P = nb.geometry().outputs['Position']
    n = nb.noise(P, scale=6, detail=6)
    seam = nb.smooth(nb.math('FRACT', nb.mul(nb.sepxyz(nb.texcoord().outputs['UV']).outputs[0], 0.7)), 0.94, 1.0)
    col = nb.mix(n, (0.10, 0.11, 0.125, 1.0), (0.18, 0.19, 0.2, 1.0))
    nrm = nb.bump(nb.add(seam, nb.mul(n, 0.3)), strength=0.6, dist=0.03)
    bsdf = nb.principled(Base_Color=col, Metallic=0.7, Roughness=nb.add(0.5, nb.mul(n, 0.2)), Normal=nrm)
    nb.output(bsdf.outputs[0])
    return nb.mat


def build_timber(name='M_Timber', axis='Z'):
    """Weathered timber; the grain (growth rings seen from outside) runs along `axis`: Z for posts / studs, Y for planks."""
    nb = NB(get_mat(name))
    P = nb.geometry().outputs['Position']
    stretch = {'Z': (1.0, 1.0, 0.06), 'Y': (1.0, 0.06, 1.0), 'X': (0.06, 1.0, 1.0)}[axis]
    wob = nb.vmath('SCALE', nb.noise(nb.mapping(P, scale=stretch), scale=2.2, detail=3, out='Color'), scale=0.35).outputs[0]
    coords = nb.vmath('ADD', P, wob).outputs[0]
    grain = nb.wave(coords, scale=7.0, dist=2.2, detail=3, wtype='RINGS', rings=axis, profile='SAW')
    streak = nb.noise(nb.mapping(P, scale=tuple(0.04 if a == axis else 1.0 for a in 'XYZ')), scale=55.0, detail=4, rough=0.6)
    pore = nb.smooth(nb.noise(nb.mapping(P, scale=tuple(0.03 if a == axis else 1.0 for a in 'XYZ')), scale=140.0, detail=2), 0.62, 0.8)
    col = nb.mix(nb.add(nb.mul(grain, 0.55), nb.mul(streak, 0.45)), (0.026, 0.015, 0.009, 1.0), (0.082, 0.047, 0.026, 1.0))
    col = nb.mix(nb.mul(pore, 0.5), col, (0.015, 0.009, 0.006, 1.0))
    nrm = nb.bump(nb.add(nb.mul(grain, 0.4), nb.mul(streak, 0.6)), strength=0.35, dist=0.012)
    bsdf = nb.principled(Base_Color=col, Roughness=nb.add(0.66, nb.mul(streak, 0.2)), Normal=nrm, Specular_IOR_Level=0.3)
    nb.output(bsdf.outputs[0])
    return nb.mat


def build_plaster(name='M_Plaster'):
    nb = NB(get_mat(name))
    P = nb.geometry().outputs['Position']
    n = nb.noise(P, scale=2.5, detail=6)
    stain = nb.smooth(nb.noise(nb.mapping(P, scale=(1.5, 1.5, 0.2)), scale=2.0, detail=4), 0.5, 0.75)
    col = nb.mix(n, (0.30, 0.28, 0.24, 1.0), (0.40, 0.38, 0.33, 1.0))
    col = nb.mix(nb.mul(stain, 0.6), col, (0.09, 0.085, 0.07, 1.0))
    nrm = nb.bump(nb.noise(P, scale=25, detail=5), strength=0.5, dist=0.02)
    bsdf = nb.principled(Base_Color=col, Roughness=0.88, Normal=nrm)
    nb.output(bsdf.outputs[0])
    return nb.mat


def build_brick(name='M_Brick'):
    nb = NB(get_mat(name))
    P = nb.geometry().outputs['Position']
    n = nb.noise(P, scale=20, detail=4)
    col = nb.mix(n, (0.20, 0.07, 0.04, 1.0), (0.30, 0.11, 0.06, 1.0))
    bsdf = nb.principled(Base_Color=col, Roughness=0.88, Normal=nb.bump(n, strength=0.5, dist=0.02))
    nb.output(bsdf.outputs[0])
    return nb.mat


def build_dark(name='M_Dark'):
    nb = NB(get_mat(name))
    bsdf = nb.principled(Base_Color=(0.003, 0.003, 0.004, 1.0), Roughness=0.7)
    nb.output(bsdf.outputs[0])
    return nb.mat


def build_rope(name='M_Rope'):
    nb = NB(get_mat(name))
    P = nb.geometry().outputs['Position']
    n = nb.noise(P, scale=60, detail=3)
    bsdf = nb.principled(Base_Color=nb.mix(n, (0.10, 0.075, 0.045, 1.0), (0.18, 0.14, 0.09, 1.0)), Roughness=0.9)
    nb.output(bsdf.outputs[0])
    return nb.mat


def build_cobble(name='M_Cobble'):
    nb = NB(get_mat(name))
    geo = nb.geometry()
    P = geo.outputs['Position']
    # flat-ish pavers: voronoi cells on world XY (paving seen from above)
    pxy = nb.mapping(P, scale=(1.0, 1.0, 0.0))
    cells = nb.voronoi(pxy, scale=4.4, rand=0.8, feature='F1', out='Distance')
    cellc = nb.rgb2bw(nb.voronoi(pxy, scale=4.4, rand=0.8, feature='F1', out='Color'))
    edge = nb.voronoi(pxy, scale=4.4, rand=0.8, feature='DISTANCE_TO_EDGE', out='Distance')
    gap = nb.smooth(edge, 0.025, 0.10)
    col = nb.mix(cellc, (0.16, 0.15, 0.14, 1.0), (0.26, 0.245, 0.23, 1.0))
    wet = nb.smooth(nb.noise(P, scale=0.5, detail=3), 0.45, 0.7)
    col = nb.mix(nb.sub(1.0, gap), col, (0.03, 0.028, 0.025, 1.0))
    h = nb.add(nb.mul(gap, 0.7), nb.mul(cells, 0.3))
    nrm = nb.bump(h, strength=0.9, dist=0.05)
    bsdf = nb.principled(Base_Color=col, Roughness=nb.mix(wet, 0.75, 0.32, dtype='FLOAT'), Normal=nrm)
    nb.output(bsdf.outputs[0])
    return nb.mat


def build_all_castle():
    build_stone('M_Stone')
    build_stone('M_StoneDress', pal=((0.50, 0.46, 0.38), (0.43, 0.42, 0.39)), block=(0.50, 0.30), block2=(0.34, 0.20),
                dirt=0.65, moss=0.5, wear=0.7, rough=0.78, tint=0.45)
    build_stone('M_Quay', pal=((0.34, 0.33, 0.29), (0.27, 0.29, 0.27)), block=(0.95, 0.52), block2=(0.66, 0.38),
                dirt=1.5, moss=2.2, wear=1.0, rough=0.9, tint=0.6, dark_base=0.9)
    build_slate('M_Slate')
    build_copper('M_Copper')
    build_glass_lit('M_GlassLit')
    build_clockface('M_ClockFace')
    build_lantern_glass('M_LanternGlass')
    build_iron('M_Iron')
    build_lead('M_Lead')
    build_timber('M_Timber')
    build_timber('M_Plank', axis='Y')
    build_plaster('M_Plaster')
    build_brick('M_Brick')
    build_dark('M_Dark')
    build_dark('M_ClockMark')
    build_rope('M_Rope')
    build_cobble('M_Cobble')


# --------------------------------------------------------------------------------------
# terrain: rock / moor / shore / path / plateau paving in one shader
# --------------------------------------------------------------------------------------


def _rock_block(nb, P, x, y, z, Nz, up, wet_h, wetz, strength=1.0, base_normal=None):
    """Shared rock shading. Returns (colour, roughness, normal)."""
    zt = nb.add(z, nb.add(nb.mul(x, 0.21), nb.mul(y, 0.05)))
    bandn = nb.noise(nb.combxyz(nb.mul(x, 0.05), nb.mul(y, 0.05), nb.mul(zt, 0.45)), scale=1.0, detail=6, rough=0.55)
    bandf = nb.noise(nb.combxyz(nb.mul(x, 0.22), nb.mul(y, 0.22), nb.mul(zt, 1.9)), scale=1.0, detail=4, rough=0.5)
    bigp = nb.noise(P, scale=0.045, detail=3)
    rockA = nb.mix(bandn, (0.170, 0.155, 0.130, 1.0), (0.300, 0.245, 0.178, 1.0))
    rockA = nb.mix(nb.smooth(bandf, 0.55, 0.78), rockA, (0.105, 0.105, 0.112, 1.0))
    rockB = nb.mix(nb.smooth(bigp, 0.4, 0.62), rockA, (0.140, 0.150, 0.162, 1.0))
    # weathering patches + rain streaks running down the face
    patch = nb.smooth(nb.noise(P, scale=0.32, detail=4, rough=0.55), 0.42, 0.68)
    rockB = nb.mix(nb.mul(patch, 0.32), rockB, nb.mix(1.0, rockB, (0.62, 0.66, 0.70, 1.0), blend='MULTIPLY'))
    streak = nb.smooth(nb.noise(nb.combxyz(nb.mul(x, 1.3), nb.mul(y, 1.3), nb.mul(z, 0.11)), scale=1.0, detail=4, rough=0.6), 0.52, 0.74)
    rockB = nb.mix(nb.mul(streak, 0.42), rockB, nb.mix(1.0, rockB, (0.45, 0.5, 0.52, 1.0), blend='MULTIPLY'))
    # jointing: straight-edged fracture blocks (Voronoi cells stretched along the bedding), cracks visible in patches only
    cell_p = nb.mapping(nb.vmath('ADD', P, nb.vmath('SCALE', nb.noise(P, scale=0.05, detail=2, out='Color'), scale=0.9).outputs[0]).outputs[0],
                        scale=(0.30, 0.30, 0.12))
    cell_e = nb.voronoi(cell_p, scale=1.0, rand=1.0, feature='DISTANCE_TO_EDGE', out='Distance')
    cell_v = nb.rgb2bw(nb.voronoi(cell_p, scale=1.0, rand=1.0, feature='F1', out='Color'))
    vis = nb.smooth(nb.noise(P, scale=0.10, detail=2), 0.44, 0.58)
    joint = nb.mul(nb.sub(1.0, nb.smooth(cell_e, 0.0, 0.040)), vis)
    block_tone = nb.add(0.86, nb.mul(cell_v, 0.28))
    big = nb.noise(P, scale=0.20, detail=6, rough=0.55)
    mid = nb.noise(P, scale=0.85, detail=5, rough=0.55)
    fine = nb.noise(P, scale=4.5, detail=4, rough=0.5)
    sbed = nb.math('SINE', nb.add(nb.mul(zt, 2 * math.pi / 3.3), nb.mul(nb.add(big, nb.mul(mid, 0.6)), 14.0)))
    bedl = nb.mul(nb.smooth(nb.math('ABSOLUTE', sbed), 0.93, 1.0), nb.smooth(nb.noise(P, scale=0.15, detail=2), 0.35, 0.65))
    rockB = nb.mix(1.0, rockB, block_tone, blend='MULTIPLY')
    crack_col = nb.mix(1.0, rockB, (0.42, 0.42, 0.45, 1.0), blend='MULTIPLY')
    rockC = nb.mix(nb.clamp01(nb.add(nb.mul(joint, 0.72), nb.mul(bedl, 0.20))), rockB, crack_col)
    mossn = nb.smooth(nb.noise(P, scale=1.5, detail=5, rough=0.6), 0.34, 0.54)
    moss = nb.mul(nb.mul(up, mossn), nb.add(0.85, nb.mul(wet_h, 0.15)))
    moss_col = nb.mix(nb.noise(P, scale=8.0, detail=3), (0.030, 0.055, 0.018, 1.0), (0.058, 0.085, 0.028, 1.0))
    rock = nb.mix(moss, rockC, moss_col)
    lich = nb.smooth(nb.noise(P, scale=3.8, detail=6, rough=0.62), 0.68, 0.76)
    rock = nb.mix(nb.mul(lich, 0.30), rock, (0.28, 0.21, 0.07, 1.0))
    rock = nb.mix(nb.mul(wetz, 0.7), rock, nb.mix(1.0, rock, (0.35, 0.4, 0.4, 1.0), blend='MULTIPLY'))
    algae = nb.mul(nb.smooth(z, 1.6, 0.4), nb.smooth(z, -1.5, -0.3))
    rock = nb.mix(nb.mul(algae, 0.85), rock, (0.010, 0.030, 0.020, 1.0))
    blocky = nb.mul(nb.math('SNAP', nb.mul(big, 5.0), 1.0), 0.20)
    h = nb.add(nb.add(nb.mul(big, 0.75), nb.mul(mid, 0.30)),
               nb.add(nb.add(nb.mul(fine, 0.05), nb.mul(blocky, 0.28)),
                      nb.sub(0.0, nb.add(nb.mul(bedl, 0.24), nb.mul(joint, 0.16)))))
    nrm = nb.bump(h, strength=1.05 * strength, dist=0.5, normal=base_normal)
    rgh = nb.mix(wetz, nb.mix(moss, 0.86, 0.95, dtype='FLOAT'), 0.38, dtype='FLOAT')
    rock = nb.mix(1.0, rock, (0.58, 0.58, 0.58, 1.0), blend='MULTIPLY')
    return rock, rgh, nrm


def build_ground(name='M_Ground'):
    nb = NB(get_mat(name))
    geo = nb.geometry()
    P = geo.outputs['Position']
    N = geo.outputs['Normal']
    sp_ = nb.sepxyz(P)
    x, y, z = sp_.outputs[0], sp_.outputs[1], sp_.outputs[2]
    Nz = nb.sepxyz(N).outputs[2]
    amount = nb.attr('amount').outputs['Fac']
    inside = nb.attr('inside').outputs['Fac']
    pathm = nb.attr('path').outputs['Fac']
    forest = nb.attr('forest').outputs['Fac']
    # ------------------------------------------------------------ masks
    steep = nb.smooth(nb.sub(1.0, Nz), 0.40, 0.62)
    brk = nb.noise(P, scale=0.045, detail=4, rough=0.6)
    band_brk = nb.noise(nb.combxyz(nb.mul(x, 0.10), nb.mul(y, 0.10), nb.mul(z, 0.42)), scale=1.0, detail=5, rough=0.6)
    fine_brk = nb.noise(P, scale=0.32, detail=6, rough=0.6)
    rock_base = nb.math('MAXIMUM', nb.sub(nb.mul(amount, 1.05), 0.16), steep)
    rock_gate = nb.smooth(nb.math('MAXIMUM', amount, steep), 0.10, 0.45)         # gentle grassy slopes never break into bare rock
    rock_nz = nb.add(nb.mul(nb.sub(brk, 0.5), 0.5), nb.add(nb.mul(nb.sub(band_brk, 0.5), 0.34), nb.mul(nb.sub(fine_brk, 0.5), 0.26)))
    rock_m = nb.smooth(nb.add(rock_base, nb.mul(rock_nz, rock_gate)), 0.44, 0.56)
    up = nb.smooth(Nz, 0.5, 0.86)
    wet_h = nb.smooth(z, 60.0, 4.0)
    # ------------------------------------------------------------ rock
    wetz = nb.smooth(z, 3.2, 0.1)
    g1 = nb.noise(nb.combxyz(nb.mul(x, 0.011), nb.mul(y, 0.011), nb.mul(z, 0.017)), scale=1.0, detail=6, rough=0.58)
    g2 = nb.noise(nb.combxyz(nb.mul(x, 0.036), nb.mul(y, 0.036), nb.mul(z, 0.05)), scale=1.0, detail=4, rough=0.55)
    mh = nb.add(nb.mul(g1, 0.72), nb.mul(g2, 0.28))
    nrm_b = nb.bump(mh, strength=3.4, dist=20.0)
    mfac = nb.mul(nb.smooth(z, 45.0, 240.0), nb.sub(1.0, nb.smooth(inside, 0.2, 0.6)))
    nrm_base = nb.mix(mfac, N, nrm_b, dtype='VECTOR')
    rock, rgh_rock, nrm_rock = _rock_block(nb, P, x, y, z, Nz, up, wet_h, wetz, base_normal=nrm_base)
    rock = nb.mix(1.0, rock, nb.mix(mfac, (1, 1, 1, 1), (0.66, 0.70, 0.76, 1.0)), blend='MULTIPLY')
    # ------------------------------------------------------------ moor / grass / heather
    n_low = nb.noise(P, scale=0.018, detail=3, rough=0.55)
    n_mid = nb.noise(P, scale=0.11, detail=4, rough=0.5)
    n_fine = nb.noise(P, scale=5.0, detail=5, rough=0.55)
    grass = nb.mix(n_mid, (0.024, 0.036, 0.015, 1.0), (0.050, 0.060, 0.026, 1.0))
    heath = nb.mix(n_fine, (0.044, 0.034, 0.026, 1.0), (0.074, 0.052, 0.038, 1.0))
    moor = nb.mix(nb.smooth(n_low, 0.45, 0.60), grass, heath)
    dead = nb.smooth(nb.noise(P, scale=0.32, detail=4), 0.56, 0.70)
    moor = nb.mix(nb.mul(dead, 0.4), moor, (0.11, 0.095, 0.056, 1.0))
    moor = nb.mix(nb.mul(forest, 0.65), moor, (0.020, 0.024, 0.014, 1.0))
    h_moor = nb.add(nb.add(nb.mul(nb.noise(P, scale=22.0, detail=6, rough=0.6), 0.5), nb.mul(nb.noise(P, scale=2.2, detail=4), 0.4)),
                    nb.add(nb.mul(nb.noise(P, scale=14.0, detail=3), 0.22), nb.mul(nb.noise(P, scale=70.0, detail=2), 0.16)))
    nrm_moor = nb.bump(h_moor, strength=1.6, dist=0.10, normal=nrm_base)
    speck = nb.smooth(nb.noise(P, scale=38.0, detail=2), 0.55, 0.75)
    moor = nb.mix(nb.mul(speck, 0.35), moor, (0.11, 0.10, 0.05, 1.0))
    # ------------------------------------------------------------ shore / pebbles
    pebv = nb.voronoi(P, scale=9.0, rand=1.0, feature='F1', out='Distance')
    pebc = nb.rgb2bw(nb.voronoi(P, scale=9.0, rand=1.0, feature='F1', out='Color'))
    beach_m = nb.mul(nb.smooth(z, 3.4, 0.6), nb.smooth(Nz, 0.45, 0.85))
    beach = nb.mix(pebc, (0.026, 0.026, 0.024, 1.0), (0.064, 0.058, 0.048, 1.0))
    b_mid = nb.noise(P, scale=0.35, detail=5, rough=0.6)
    b_big = nb.noise(P, scale=0.06, detail=4, rough=0.55)
    beach = nb.mix(nb.smooth(b_mid, 0.42, 0.66), beach, (0.028, 0.032, 0.022, 1.0))                  # mud / moss / dead grass patches
    beach = nb.mix(nb.mul(nb.smooth(b_big, 0.50, 0.72), 0.55), beach, (0.040, 0.036, 0.030, 1.0))
    nrm_beach = nb.bump(nb.add(nb.mul(nb.sub(1.0, nb.smooth(pebv, 0.0, 0.5)), 0.5),
                               nb.add(nb.mul(b_mid, 0.9), nb.mul(nb.noise(P, scale=2.4, detail=4), 0.6))), strength=1.6, dist=0.08)
    under = nb.smooth(z, 0.0, -3.0)
    beach = nb.mix(nb.mul(under, 0.7), beach, (0.010, 0.020, 0.018, 1.0))
    # ------------------------------------------------------------ path
    pdirt = nb.mix(nb.noise(P, scale=14.0, detail=4), (0.075, 0.056, 0.038, 1.0), (0.115, 0.088, 0.060, 1.0))
    # ------------------------------------------------------------ plateau paving
    pv_edge = nb.voronoi(nb.mapping(P, scale=(0.55, 0.55, 0.0)), scale=1.0, rand=0.8, feature='DISTANCE_TO_EDGE', out='Distance')
    pv_gap = nb.smooth(pv_edge, 0.0, 0.06)
    pv_c = nb.rgb2bw(nb.voronoi(nb.mapping(P, scale=(0.55, 0.55, 0.0)), scale=1.0, rand=0.8, feature='F1', out='Color'))
    pav = nb.mix(pv_c, (0.075, 0.072, 0.066, 1.0), (0.130, 0.124, 0.113, 1.0))
    pav = nb.mix(nb.sub(1.0, pv_gap), pav, (0.03, 0.045, 0.02, 1.0))
    nrm_pav = nb.bump(nb.add(nb.mul(pv_gap, 0.7), nb.mul(nb.noise(P, scale=12, detail=4), 0.2)), strength=0.9, dist=0.05)
    # ------------------------------------------------------------ high-altitude frost
    snow_m = nb.mul(nb.smooth(nb.add(z, nb.mul(nb.sub(nb.noise(P, scale=0.004, detail=4), 0.5), 260.0)), 860.0, 1050.0), nb.smooth(Nz, 0.5, 0.85))
    # ------------------------------------------------------------ combine
    col = nb.mix(beach_m, moor, beach)
    col = nb.mix(rock_m, col, rock)
    col = nb.mix(1.0, col, nb.mix(nb.smooth(z, 80.0, 700.0), (1, 1, 1, 1), (0.62, 0.66, 0.70, 1.0)), blend='MULTIPLY')
    col = nb.mix(nb.mul(snow_m, 0.8), col, (0.16, 0.19, 0.26, 1.0))
    col = nb.mix(nb.smooth(pathm, 0.3, 0.7), col, pdirt)
    col = nb.mix(nb.smooth(inside, 0.4, 0.7), col, pav)
    nrm = nb.mix(beach_m, nrm_moor, nrm_beach, dtype='VECTOR')
    nrm = nb.mix(rock_m, nrm, nrm_rock, dtype='VECTOR')
    nrm = nb.mix(nb.smooth(inside, 0.4, 0.7), nrm, nrm_pav, dtype='VECTOR')
    rgh = nb.mix(rock_m, nb.mix(beach_m, 0.92, 0.82, dtype='FLOAT'), rgh_rock, dtype='FLOAT')
    rgh = nb.mix(nb.smooth(inside, 0.4, 0.7), rgh, 0.72, dtype='FLOAT')
    spec = nb.mix(rock_m, nb.mix(beach_m, 0.05, 0.07, dtype='FLOAT'), 0.2, dtype='FLOAT')
    bsdf = nb.principled(Base_Color=col, Roughness=rgh, Normal=nrm, Specular_IOR_Level=spec)
    nb.output(bsdf.outputs[0])
    return nb.mat


# --------------------------------------------------------------------------------------
# water
# --------------------------------------------------------------------------------------

def build_water(name='M_Water'):
    nb = NB(get_mat(name))
    geo = nb.geometry()
    P = geo.outputs['Position']
    sp_ = nb.sepxyz(P)
    x, y = sp_.outputs[0], sp_.outputs[1]
    # anisotropic ripples: long along X, short along Y (calm loch, wind from the west)
    q1 = nb.combxyz(nb.mul(x, 0.55), nb.mul(y, 2.2), 0.0)
    q2 = nb.combxyz(nb.mul(x, 1.7), nb.mul(y, 5.5), 3.0)
    q3 = nb.combxyz(nb.mul(x, 0.09), nb.mul(y, 0.30), 7.0)
    r1 = nb.noise(q1, scale=0.55, detail=3, rough=0.5)
    r2 = nb.noise(q2, scale=1.4, detail=2, rough=0.5)
    r3 = nb.noise(q3, scale=1.0, detail=2, rough=0.5)
    hgt = nb.add(nb.add(nb.mul(r1, 0.6), nb.mul(r2, 0.25)), nb.mul(r3, 1.4))
    nrm = nb.bump(hgt, strength=0.85, dist=0.06)
    rgh = nb.add(0.035, nb.mul(nb.sub(r2, 0.5), 0.03))
    bsdf = nb.principled(Base_Color=(0.02, 0.05, 0.06, 1.0), Roughness=rgh, IOR=1.333, Transmission_Weight=1.0, Normal=nrm,
                         Specular_IOR_Level=0.5)
    # volume: dark peaty loch, red absorbed first
    va = nb.node('ShaderNodeVolumeAbsorption')
    va.inputs['Color'].default_value = (0.055, 0.30, 0.34, 1.0)
    va.inputs['Density'].default_value = 0.42
    vsc = nb.node('ShaderNodeVolumeScatter')
    vsc.inputs['Color'].default_value = (0.10, 0.30, 0.36, 1.0)
    vsc.inputs['Density'].default_value = 0.020
    vsc.inputs['Anisotropy'].default_value = 0.3
    vsum = nb.addshader(va.outputs[0], vsc.outputs[0])
    nb.output(surface=bsdf.outputs[0], volume=vsum)
    return nb.mat


def build_all_landscape():
    build_ground('M_Ground')
    build_water('M_Water')


# --------------------------------------------------------------------------------------
# vegetation + boulders
# --------------------------------------------------------------------------------------

def build_conifer(name='M_Conifer'):
    nb = NB(get_mat(name))
    geo = nb.geometry()
    P = geo.outputs['Position']
    tip = nb.attr('tip').outputs['Fac']
    ri = nb.objinfo().outputs['Random']
    base = nb.mix(ri, (0.008, 0.020, 0.013, 1.0), (0.015, 0.030, 0.014, 1.0))
    cl = nb.noise(P, scale=1.3, detail=4, rough=0.55)
    base = nb.mix(nb.smooth(cl, 0.4, 0.7), base, (0.005, 0.014, 0.010, 1.0))
    tipn = nb.mul(tip, nb.add(0.35, nb.mul(nb.noise(P, scale=1.1, detail=3), 0.9)))
    col = nb.mix(nb.mul(tipn, 0.40), base, (0.018, 0.036, 0.020, 1.0))
    ndl = nb.noise(P, scale=16.0, detail=5, rough=0.6)
    nrm = nb.bump(ndl, strength=0.8, dist=0.06)
    bsdf = nb.principled(Base_Color=col, Roughness=nb.add(0.78, nb.mul(ndl, 0.15)), Normal=nrm, Specular_IOR_Level=0.08)
    nb.output(bsdf.outputs[0])
    return nb.mat


def build_bark(name='M_Bark'):
    nb = NB(get_mat(name))
    P = nb.geometry().outputs['Position']
    g = nb.noise(nb.mapping(P, scale=(3.0, 3.0, 0.35)), scale=6.0, detail=6, rough=0.6)
    col = nb.mix(g, (0.020, 0.012, 0.008, 1.0), (0.060, 0.038, 0.024, 1.0))
    nrm = nb.bump(g, strength=1.5, dist=0.08)
    bsdf = nb.principled(Base_Color=col, Roughness=0.88, Normal=nrm)
    nb.output(bsdf.outputs[0])
    return nb.mat


def build_rockchunk(name='M_RockChunk'):
    nb = NB(get_mat(name))
    geo = nb.geometry()
    P = geo.outputs['Position']
    N = geo.outputs['Normal']
    sp_ = nb.sepxyz(P)
    x, y, z = sp_.outputs[0], sp_.outputs[1], sp_.outputs[2]
    Nz = nb.sepxyz(N).outputs[2]
    up = nb.smooth(Nz, 0.5, 0.86)
    wet_h = nb.smooth(z, 60.0, 4.0)
    wetz = nb.smooth(z, 3.2, 0.1)
    rock, rgh, nrm = _rock_block(nb, P, x, y, z, Nz, up, wet_h, wetz, strength=1.2)
    bsdf = nb.principled(Base_Color=rock, Roughness=rgh, Normal=nrm, Specular_IOR_Level=0.2)
    nb.output(bsdf.outputs[0])
    return nb.mat


def build_reed(name='M_Reed'):
    nb = NB(get_mat(name))
    P = nb.geometry().outputs['Position']
    tip = nb.attr('tip').outputs['Fac']
    ri = nb.objinfo().outputs['Random']
    base = nb.mix(ri, (0.020, 0.034, 0.012, 1.0), (0.046, 0.052, 0.018, 1.0))
    col = nb.mix(nb.mul(tip, 0.85), base, (0.13, 0.11, 0.045, 1.0))
    n = nb.noise(P, scale=6.0, detail=2)
    bsdf = nb.principled(Base_Color=col, Roughness=nb.add(0.55, nb.mul(n, 0.2)), Specular_IOR_Level=0.25)
    nb.output(bsdf.outputs[0])
    return nb.mat


def build_all_nature():
    build_reed('M_Reed')
    build_conifer('M_Conifer')
    build_bark('M_Bark')
    build_rockchunk('M_RockChunk')


# --------------------------------------------------------------------------------------
# glasshouse materials
# --------------------------------------------------------------------------------------

def build_glass(name='M_Glass'):
    nb = NB(get_mat(name))
    P = nb.geometry().outputs['Position']
    fr = nb.node('ShaderNodeFresnel')
    fr.inputs['IOR'].default_value = 1.45
    tr = nb.node('ShaderNodeBsdfTransparent')
    nb._in(tr, 'Color', (0.86, 0.95, 0.90, 1.0))
    dirt = nb.smooth(nb.noise(P, scale=2.2, detail=5), 0.45, 0.8)
    gl = nb.node('ShaderNodeBsdfGlossy')
    nb._in(gl, 'Color', (0.88, 0.94, 1.0, 1.0))
    nb._in(gl, 'Roughness', nb.add(0.02, nb.mul(dirt, 0.25)))
    f2 = nb.clamp01(nb.add(nb.mul(fr.outputs[0], 1.3), nb.mul(dirt, 0.08)))
    nb.output(nb.mixshader(f2, tr.outputs[0], gl.outputs[0]))
    return nb.mat


def build_ironpaint(name='M_IronPaint'):
    nb = NB(get_mat(name))
    P = nb.geometry().outputs['Position']
    n = nb.noise(P, scale=14, detail=5)
    chip = nb.smooth(nb.noise(P, scale=6, detail=6), 0.62, 0.72)
    col = nb.mix(n, (0.028, 0.050, 0.048, 1.0), (0.05, 0.075, 0.07, 1.0))
    col = nb.mix(chip, col, (0.09, 0.05, 0.03, 1.0))
    bsdf = nb.principled(Base_Color=col, Metallic=nb.mix(chip, 0.25, 0.8, dtype='FLOAT'), Roughness=nb.add(0.42, nb.mul(n, 0.25)),
                         Normal=nb.bump(n, strength=0.3, dist=0.01))
    nb.output(bsdf.outputs[0])
    return nb.mat


def build_foliage(name='M_Foliage'):
    nb = NB(get_mat(name))
    P = nb.geometry().outputs['Position']
    n = nb.noise(P, scale=4.0, detail=5)
    col = nb.mix(n, (0.03, 0.10, 0.03, 1.0), (0.06, 0.16, 0.05, 1.0))
    bsdf = nb.principled(Base_Color=col, Roughness=0.6, Normal=nb.bump(n, strength=0.6, dist=0.05),
                         Emission_Color=(0.55, 0.85, 0.30, 1.0), Emission_Strength=nb.mul(nb.add(0.25, n), 0.14))
    nb.output(bsdf.outputs[0])
    return nb.mat


def build_all_glasshouse():
    build_glass('M_Glass')
    build_ironpaint('M_IronPaint')
    build_foliage('M_Foliage')


# --------------------------------------------------------------------------------------
# props: thatch, feathers, owl eyes
# --------------------------------------------------------------------------------------

def build_thatch(name='M_Thatch'):
    nb = NB(get_mat(name))
    geo = nb.geometry()
    P = geo.outputs['Position']
    uv = nb.texcoord().outputs['UV']
    st = nb.mapping(uv, scale=(9.0, 0.9, 1.0))
    straw = nb.noise(st, scale=1.0, detail=6, rough=0.6)
    fine = nb.noise(P, scale=20.0, detail=5)
    col = nb.mix(straw, (0.10, 0.075, 0.04, 1.0), (0.24, 0.18, 0.09, 1.0))
    col = nb.mix(nb.smooth(nb.noise(P, scale=0.7, detail=4), 0.55, 0.75), col, (0.04, 0.05, 0.03, 1.0))
    nrm = nb.bump(nb.add(nb.mul(straw, 0.8), nb.mul(fine, 0.4)), strength=1.4, dist=0.09)
    bsdf = nb.principled(Base_Color=col, Roughness=0.92, Normal=nrm)
    nb.output(bsdf.outputs[0])
    return nb.mat


def build_feather(name='M_Feather'):
    nb = NB(get_mat(name))
    P = nb.geometry().outputs['Position']
    n = nb.noise(P, scale=30.0, detail=5)
    col = nb.mix(n, (0.05, 0.04, 0.03, 1.0), (0.16, 0.12, 0.08, 1.0))
    bsdf = nb.principled(Base_Color=col, Roughness=0.9, Normal=nb.bump(n, strength=0.5, dist=0.01))
    nb.output(bsdf.outputs[0])
    return nb.mat


def build_owleye(name='M_OwlEye'):
    nb = NB(get_mat(name))
    bsdf = nb.principled(Base_Color=(0.3, 0.2, 0.02, 1.0), Roughness=0.2, Emission_Color=(1.0, 0.7, 0.1, 1.0), Emission_Strength=6.0)
    nb.output(bsdf.outputs[0])
    return nb.mat


def build_all_props():
    build_thatch('M_Thatch')
    build_feather('M_Feather')
    build_owleye('M_OwlEye')
