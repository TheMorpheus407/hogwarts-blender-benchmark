import bpy, bmesh, math, random
import numpy as np
from mathutils import Vector, Matrix, noise as mnoise
import importlib
import hogwarts_lib as HL
importlib.reload(HL)

WS = HL.WS
MATS = {}

def fbm_np(x, y, seed=0.0, octaves=4, lac=2.03, gain=0.5):
    out = np.zeros_like(x)
    amp = 1.0
    f = 1.0
    for i in range(octaves):
        p = seed * 17.13 + i * 101.7
        out += amp * (np.sin(x * f * 0.9 + p) * np.cos(y * f * 1.07 + p * 1.3)
                      + 0.5 * np.sin((x * 1.7 + y * 1.3) * f + p * 2.1)) / 1.5
        amp *= gain
        f *= lac
    return out

def new_mat(name):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    return m, nt

def _mix(nt, fac, a, b):
    n = nt.nodes.new('ShaderNodeMix')
    n.data_type = 'RGBA'
    if isinstance(fac, (int, float)):
        n.inputs[0].default_value = fac
    else:
        nt.links.new(fac, n.inputs[0])
    for sock, val in ((6, a), (7, b)):
        if isinstance(val, (int, float, tuple)):
            n.inputs[sock].default_value = val
        else:
            nt.links.new(val, n.inputs[sock])
    return n.outputs[2]

def _ramp(nt, fac, stops):
    n = nt.nodes.new('ShaderNodeValToRGB')
    for i, (pos, col) in enumerate(stops):
        if i < 2:
            e = n.color_ramp.elements[i]
        else:
            e = n.color_ramp.elements.new(pos)
        e.position = pos
        e.color = col
    nt.links.new(fac, n.inputs[0])
    return n.outputs[0]

def ensure_materials():
    m, nt = new_mat('M_Stone')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    map1 = nt.nodes.new('ShaderNodeMapping')
    nt.links.new(geo.outputs['Position'], map1.inputs[0])
    batch = nt.nodes.new('ShaderNodeTexNoise')
    batch.inputs['Scale'].default_value = 0.02
    batch.inputs['Detail'].default_value = 2
    nt.links.new(map1.outputs[0], batch.inputs['Vector'])
    col_batch = _ramp(nt, batch.outputs['Fac'], [
        (0.3, (0.07, 0.06, 0.05, 1)), (0.45, (0.10, 0.09, 0.07, 1)),
        (0.6, (0.06, 0.06, 0.055, 1)), (0.75, (0.12, 0.10, 0.08, 1))])
    grain = nt.nodes.new('ShaderNodeTexNoise')
    grain.inputs['Scale'].default_value = 3.5
    grain.inputs['Detail'].default_value = 8
    nt.links.new(map1.outputs[0], grain.inputs['Vector'])
    col_grain = _mix(nt, grain.outputs['Fac'], col_batch, (0.08, 0.075, 0.07, 1))
    streak_map = nt.nodes.new('ShaderNodeMapping')
    streak_map.inputs['Scale'].default_value = (3.0, 3.0, 0.15)
    nt.links.new(geo.outputs['Position'], streak_map.inputs[0])
    streak = nt.nodes.new('ShaderNodeTexNoise')
    streak.inputs['Scale'].default_value = 1.2
    streak.inputs['Detail'].default_value = 4
    nt.links.new(streak_map.outputs[0], streak.inputs['Vector'])
    streak_r = nt.nodes.new('ShaderNodeMath')
    streak_r.operation = 'GREATER_THAN'
    streak_r.inputs[1].default_value = 0.72
    nt.links.new(streak.outputs['Fac'], streak_r.inputs[0])
    col_streak = _mix(nt, streak_r.outputs[0], col_grain, (0.065, 0.06, 0.052, 1))
    pt = nt.nodes.new('ShaderNodeValToRGB')
    pt.color_ramp.elements[0].position = 0.42
    pt.color_ramp.elements[1].position = 0.62
    nt.links.new(geo.outputs['Pointiness'], pt.inputs[0])
    col_wear = _mix(nt, pt.outputs[0], (0.04, 0.038, 0.035, 1), col_streak)
    hfall = nt.nodes.new('ShaderNodeMath')
    hfall.operation = 'LESS_THAN'
    hfall.inputs[1].default_value = 22.0
    nt.links.new(sep.outputs['Z'], hfall.inputs[0])
    mossn = nt.nodes.new('ShaderNodeTexNoise')
    mossn.inputs['Scale'].default_value = 0.35
    mossn.inputs['Detail'].default_value = 6
    nt.links.new(map1.outputs[0], mossn.inputs['Vector'])
    mossm = nt.nodes.new('ShaderNodeMath')
    mossm.operation = 'MULTIPLY'
    nt.links.new(hfall.outputs[0], mossm.inputs[0])
    mossr = nt.nodes.new('ShaderNodeMath')
    mossr.operation = 'GREATER_THAN'
    mossr.inputs[1].default_value = 0.55
    nt.links.new(mossn.outputs['Fac'], mossr.inputs[0])
    nt.links.new(mossr.outputs[0], mossm.inputs[1])
    col_moss = _mix(nt, mossm.outputs[0], col_wear, (0.045, 0.09, 0.035, 1))
    sepN = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Normal'], sepN.inputs[0])
    slope_lo = nt.nodes.new('ShaderNodeMath')
    slope_lo.operation = 'GREATER_THAN'
    slope_lo.inputs[1].default_value = 0.18
    nt.links.new(sepN.outputs['Z'], slope_lo.inputs[0])
    slope_hi = nt.nodes.new('ShaderNodeMath')
    slope_hi.operation = 'LESS_THAN'
    slope_hi.inputs[1].default_value = 0.88
    nt.links.new(sepN.outputs['Z'], slope_hi.inputs[0])
    slope_m = nt.nodes.new('ShaderNodeMath')
    slope_m.operation = 'MULTIPLY'
    nt.links.new(slope_lo.outputs[0], slope_m.inputs[0])
    nt.links.new(slope_hi.outputs[0], slope_m.inputs[1])
    slate_col = _slate_nodes(nt, map1)
    col_final = _mix(nt, slope_m.outputs[0], col_moss, slate_col)
    nt.links.new(col_final, bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.85
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.35
    nt.links.new(grain.outputs['Fac'], bump.inputs['Height'])
    bump2 = nt.nodes.new('ShaderNodeBump')
    bump2.inputs['Strength'].default_value = 0.25
    nt.links.new(bump.outputs[0], bump2.inputs['Normal'])
    vor = nt.nodes.new('ShaderNodeTexVoronoi')
    vor.inputs['Scale'].default_value = 9.0
    nt.links.new(map1.outputs[0], vor.inputs['Vector'])
    nt.links.new(vor.outputs['Distance'], bump2.inputs['Height'])
    nt.links.new(bump2.outputs[0], bsdf.inputs['Normal'])
    MATS['stone'] = m

    m, nt = new_mat('M_StoneCopper')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Roughness'].default_value = 0.7
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    sepN = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Normal'], sepN.inputs[0])
    sn = nt.nodes.new('ShaderNodeTexNoise')
    sn.inputs['Scale'].default_value = 2.0
    stonec = _ramp(nt, sn.outputs['Fac'], [(0.3, (0.14, 0.12, 0.09, 1)), (0.7, (0.22, 0.19, 0.15, 1))])
    slope_lo = nt.nodes.new('ShaderNodeMath')
    slope_lo.operation = 'GREATER_THAN'
    slope_lo.inputs[1].default_value = 0.18
    nt.links.new(sepN.outputs['Z'], slope_lo.inputs[0])
    slope_hi = nt.nodes.new('ShaderNodeMath')
    slope_hi.operation = 'LESS_THAN'
    slope_hi.inputs[1].default_value = 0.88
    nt.links.new(sepN.outputs['Z'], slope_hi.inputs[0])
    slope_m = nt.nodes.new('ShaderNodeMath')
    slope_m.operation = 'MULTIPLY'
    nt.links.new(slope_lo.outputs[0], slope_m.inputs[0])
    nt.links.new(slope_hi.outputs[0], slope_m.inputs[1])
    cn = nt.nodes.new('ShaderNodeTexNoise')
    cn.inputs['Scale'].default_value = 3.0
    copc = _ramp(nt, cn.outputs['Fac'], [(0.3, (0.04, 0.22, 0.18, 1)), (0.7, (0.09, 0.38, 0.3, 1))])
    colf = _mix(nt, slope_m.outputs[0], stonec, copc)
    nt.links.new(colf, b.inputs['Base Color'])
    nt.links.new(b.outputs[0], out.inputs[0])
    MATS['stonecopper'] = m

    m, nt = new_mat('M_GlassGlow')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    attr = nt.nodes.new('ShaderNodeAttribute')
    attr.attribute_name = 'wr'
    lit = nt.nodes.new('ShaderNodeMath')
    lit.operation = 'GREATER_THAN'
    lit.inputs[1].default_value = 0.0
    nt.links.new(attr.outputs['Fac'], lit.inputs[0])
    emis = nt.nodes.new('ShaderNodeEmission')
    colr = _ramp(nt, attr.outputs['Fac'], [
        (0.0, (1.0, 0.28, 0.05, 1)), (0.5, (1.0, 0.45, 0.12, 1)), (1.0, (1.0, 0.65, 0.28, 1))])
    nt.links.new(colr, emis.inputs['Color'])
    strn = nt.nodes.new('ShaderNodeMapRange')
    strn.inputs['From Min'].default_value = 0.0
    strn.inputs['From Max'].default_value = 1.0
    strn.inputs['To Min'].default_value = 3.5
    strn.inputs['To Max'].default_value = 12.0
    nt.links.new(attr.outputs['Fac'], strn.inputs['Value'])
    nt.links.new(strn.outputs[0], emis.inputs['Strength'])
    dark = nt.nodes.new('ShaderNodeBsdfPrincipled')
    dark.inputs['Base Color'].default_value = (0.01, 0.012, 0.02, 1)
    dark.inputs['Roughness'].default_value = 0.2
    mixsh = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lit.outputs[0], mixsh.inputs[0])
    nt.links.new(dark.outputs[0], mixsh.inputs[1])
    nt.links.new(emis.outputs[0], mixsh.inputs[2])
    nt.links.new(mixsh.outputs[0], out.inputs[0])
    MATS['glass'] = m

    m, nt = new_mat('M_GHGlass')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = (0.06, 0.10, 0.09, 1)
    b.inputs['Roughness'].default_value = 0.2
    b.inputs['Transmission Weight'].default_value = 0.5
    b.inputs['Emission Color'].default_value = (1.0, 0.6, 0.25, 1)
    b.inputs['Emission Strength'].default_value = 0.02
    nt.links.new(b.outputs[0], out.inputs[0])
    MATS['ghglass'] = m

    m, nt = new_mat('M_Water')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = (0.012, 0.03, 0.035, 1)
    b.inputs['Roughness'].default_value = 0.03
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['IOR'].default_value = 1.33
    tc = nt.nodes.new('ShaderNodeTexCoord')
    w1 = nt.nodes.new('ShaderNodeTexNoise')
    w1.inputs['Scale'].default_value = 0.15
    w1.inputs['Detail'].default_value = 6
    nt.links.new(tc.outputs['Object'], w1.inputs['Vector'])
    w2 = nt.nodes.new('ShaderNodeTexNoise')
    w2.inputs['Scale'].default_value = 1.4
    w2.inputs['Detail'].default_value = 8
    nt.links.new(tc.outputs['Object'], w2.inputs['Vector'])
    bmp = nt.nodes.new('ShaderNodeBump')
    bmp.inputs['Strength'].default_value = 0.06
    nt.links.new(w1.outputs['Fac'], bmp.inputs['Height'])
    bmp2 = nt.nodes.new('ShaderNodeBump')
    bmp2.inputs['Strength'].default_value = 0.03
    nt.links.new(bmp.outputs[0], bmp2.inputs['Normal'])
    nt.links.new(w2.outputs['Fac'], bmp2.inputs['Height'])
    nt.links.new(bmp2.outputs[0], b.inputs['Normal'])
    nt.links.new(b.outputs[0], out.inputs[0])
    MATS['water'] = m

    m, nt = new_mat('M_Ground')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Roughness'].default_value = 0.9
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    sepN = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Normal'], sepN.inputs[0])
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    gn = nt.nodes.new('ShaderNodeTexNoise')
    gn.inputs['Scale'].default_value = 0.08
    gn.inputs['Detail'].default_value = 8
    grass_col = _ramp(nt, gn.outputs['Fac'], [
        (0.25, (0.012, 0.022, 0.008, 1)), (0.5, (0.02, 0.035, 0.012, 1)), (0.75, (0.04, 0.045, 0.02, 1))])
    rockn = nt.nodes.new('ShaderNodeTexNoise')
    rockn.inputs['Scale'].default_value = 1.0
    rockn.inputs['Detail'].default_value = 10
    rock_col = _ramp(nt, rockn.outputs['Fac'], [
        (0.3, (0.05, 0.048, 0.045, 1)), (0.6, (0.10, 0.095, 0.09, 1)), (0.8, (0.16, 0.15, 0.135, 1))])
    strata = nt.nodes.new('ShaderNodeMath')
    strata.operation = 'MULTIPLY_ADD'
    nt.links.new(sep.outputs['Z'], strata.inputs[0])
    strata.inputs[1].default_value = 0.7
    nt.links.new(rockn.outputs['Fac'], strata.inputs[2])
    sins = nt.nodes.new('ShaderNodeMath')
    sins.operation = 'SINE'
    nt.links.new(strata.outputs[0], sins.inputs[0])
    rock_col2 = _mix(nt, sins.outputs[0], rock_col, (0.07, 0.065, 0.06, 1))
    slope_r = nt.nodes.new('ShaderNodeMath')
    slope_r.operation = 'LESS_THAN'
    slope_r.inputs[1].default_value = 0.72
    nt.links.new(sepN.outputs['Z'], slope_r.inputs[0])
    rockmask = slope_r
    col1 = _mix(nt, rockmask.outputs[0], grass_col, rock_col2)
    pattr = nt.nodes.new('ShaderNodeAttribute')
    pattr.attribute_name = 'path'
    col2 = _mix(nt, pattr.outputs['Fac'], col1, (0.10, 0.085, 0.065, 1))
    shore_r = nt.nodes.new('ShaderNodeMapRange')
    shore_r.inputs['From Min'].default_value = 0.4
    shore_r.inputs['From Max'].default_value = 5.0
    shore_r.inputs['To Min'].default_value = 1.0
    shore_r.inputs['To Max'].default_value = 0.0
    nt.links.new(sep.outputs['Z'], shore_r.inputs['Value'])
    col3 = _mix(nt, shore_r.outputs[0], col2, (0.02, 0.022, 0.022, 1))
    nt.links.new(col3, b.inputs['Base Color'])
    bmp = nt.nodes.new('ShaderNodeBump')
    bmp.inputs['Strength'].default_value = 0.5
    nt.links.new(rockn.outputs['Fac'], bmp.inputs['Height'])
    bmpb = nt.nodes.new('ShaderNodeBump')
    bmpb.inputs['Strength'].default_value = 0.7
    lrock = nt.nodes.new('ShaderNodeTexNoise')
    lrock.inputs['Scale'].default_value = 0.10
    lrock.inputs['Detail'].default_value = 6
    nt.links.new(lrock.outputs['Fac'], bmpb.inputs['Height'])
    nt.links.new(bmpb.outputs[0], bmp.inputs['Normal'])
    nt.links.new(bmp.outputs[0], b.inputs['Normal'])
    nt.links.new(b.outputs[0], out.inputs[0])
    MATS['ground'] = m

    m, nt = new_mat('M_Mountain')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Roughness'].default_value = 0.95
    cam = nt.nodes.new('ShaderNodeCameraData')
    haze = nt.nodes.new('ShaderNodeMapRange')
    haze.inputs['From Min'].default_value = 150.0
    haze.inputs['From Max'].default_value = 1800.0
    haze.inputs['To Min'].default_value = 0.0
    haze.inputs['To Max'].default_value = 0.95
    nt.links.new(cam.outputs['View Z Depth'], haze.inputs['Value'])
    base = _ramp(nt, haze.outputs[0], [(0.0, (0.02, 0.03, 0.035, 1)), (1.0, (0.02, 0.05, 0.07, 1))])
    nt.links.new(base, b.inputs['Base Color'])
    nt.links.new(b.outputs[0], out.inputs[0])
    MATS['mountain'] = m

    m, nt = new_mat('M_Tree')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Roughness'].default_value = 0.8
    oi = nt.nodes.new('ShaderNodeObjectInfo')
    tr = _ramp(nt, oi.outputs['Random'], [
        (0.0, (0.015, 0.035, 0.015, 1)), (0.5, (0.02, 0.05, 0.02, 1)), (1.0, (0.035, 0.06, 0.025, 1))])
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(oi.outputs['Location'], sep.inputs[0])
    nt.links.new(tr, b.inputs['Base Color'])
    nt.links.new(b.outputs[0], out.inputs[0])
    MATS['tree'] = m

    m, nt = new_mat('M_Wood')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Roughness'].default_value = 0.8
    wn = nt.nodes.new('ShaderNodeTexNoise')
    wn.inputs['Scale'].default_value = 8.0
    wc = _ramp(nt, wn.outputs['Fac'], [(0.3, (0.06, 0.035, 0.02, 1)), (0.7, (0.10, 0.06, 0.03, 1))])
    nt.links.new(wc, b.inputs['Base Color'])
    nt.links.new(b.outputs[0], out.inputs[0])
    MATS['wood'] = m

    m, nt = new_mat('M_SlateRoof')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Roughness'].default_value = 0.5
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sl = _slate_nodes(nt, None, tc)
    nt.links.new(sl, b.inputs['Base Color'])
    nt.links.new(b.outputs[0], out.inputs[0])
    MATS['slate'] = m

    m, nt = new_mat('M_Copper')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Roughness'].default_value = 0.45
    b.inputs['Metallic'].default_value = 0.4
    cn = nt.nodes.new('ShaderNodeTexNoise')
    cn.inputs['Scale'].default_value = 2.0
    cc = _ramp(nt, cn.outputs['Fac'], [(0.3, (0.05, 0.25, 0.2, 1)), (0.7, (0.1, 0.4, 0.32, 1))])
    nt.links.new(cc, b.inputs['Base Color'])
    nt.links.new(b.outputs[0], out.inputs[0])
    MATS['copper'] = m

    m, nt = new_mat('M_LanternGlow')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    e = nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = (1.0, 0.55, 0.18, 1)
    e.inputs['Strength'].default_value = 18.0
    nt.links.new(e.outputs[0], out.inputs[0])
    MATS['lanternglow'] = m

    m, nt = new_mat('M_Iron')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1)
    b.inputs['Metallic'].default_value = 0.6
    b.inputs['Roughness'].default_value = 0.5
    nt.links.new(b.outputs[0], out.inputs[0])
    MATS['iron'] = m

    m, nt = new_mat('M_Clockface')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    e = nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = (1.0, 0.8, 0.5, 1)
    e.inputs['Strength'].default_value = 3.0
    nt.links.new(e.outputs[0], out.inputs[0])
    MATS['clockface'] = m

    m, nt = new_mat('M_Clockhand')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = (0.01, 0.01, 0.01, 1)
    nt.links.new(b.outputs[0], out.inputs[0])
    MATS['clockhand'] = m

    m, nt = new_mat('M_Mist')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    pv = nt.nodes.new('ShaderNodeVolumePrincipled')
    pv.inputs['Color'].default_value = (0.35, 0.45, 0.55, 1)
    pv.inputs['Anisotropy'].default_value = 0.4
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    hf = nt.nodes.new('ShaderNodeMapRange')
    hf.inputs['From Min'].default_value = -1.0
    hf.inputs['From Max'].default_value = 1.0
    hf.inputs['To Min'].default_value = 1.0
    hf.inputs['To Max'].default_value = 0.0
    nt.links.new(sep.outputs['Z'], hf.inputs['Value'])
    hfp = nt.nodes.new('ShaderNodeMath')
    hfp.operation = 'POWER'
    hfp.inputs[1].default_value = 2.5
    nt.links.new(hf.outputs[0], hfp.inputs[0])
    mn = nt.nodes.new('ShaderNodeTexNoise')
    mn.inputs['Scale'].default_value = 2.5
    mn.inputs['Detail'].default_value = 4
    nt.links.new(tc.outputs['Object'], mn.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 0.35
    mr.inputs['From Max'].default_value = 0.75
    nt.links.new(mn.outputs['Fac'], mr.inputs['Value'])
    dm = nt.nodes.new('ShaderNodeMath')
    dm.operation = 'MULTIPLY'
    nt.links.new(hfp.outputs[0], dm.inputs[0])
    nt.links.new(mr.outputs[0], dm.inputs[1])
    ds = nt.nodes.new('ShaderNodeMath')
    ds.operation = 'MULTIPLY'
    ds.inputs[1].default_value = 0.008
    nt.links.new(dm.outputs[0], ds.inputs[0])
    nt.links.new(ds.outputs[0], pv.inputs['Density'])
    nt.links.new(pv.outputs[0], out.inputs['Volume'])
    MATS['mist'] = m

    m, nt = new_mat('M_Smoke')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    pv = nt.nodes.new('ShaderNodeVolumePrincipled')
    pv.inputs['Color'].default_value = (0.5, 0.5, 0.5, 1)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    hf = nt.nodes.new('ShaderNodeMapRange')
    hf.inputs['From Min'].default_value = -1.0
    hf.inputs['From Max'].default_value = 1.0
    hf.inputs['To Min'].default_value = 0.5
    hf.inputs['To Max'].default_value = 0.0
    nt.links.new(sep.outputs['Z'], hf.inputs['Value'])
    mn = nt.nodes.new('ShaderNodeTexNoise')
    mn.inputs['Scale'].default_value = 3.0
    nt.links.new(tc.outputs['Object'], mn.inputs['Vector'])
    dm = nt.nodes.new('ShaderNodeMath')
    dm.operation = 'MULTIPLY'
    nt.links.new(hf.outputs[0], dm.inputs[0])
    nt.links.new(mn.outputs['Fac'], dm.inputs[1])
    ds = nt.nodes.new('ShaderNodeMath')
    ds.operation = 'MULTIPLY'
    ds.inputs[1].default_value = 0.6
    nt.links.new(dm.outputs[0], ds.inputs[0])
    nt.links.new(ds.outputs[0], pv.inputs['Density'])
    nt.links.new(pv.outputs[0], out.inputs['Volume'])
    MATS['smoke'] = m

    m, nt = new_mat('M_Moon')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    e = nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = (0.9, 0.95, 1.0, 1)
    e.inputs['Strength'].default_value = 40.0
    nt.links.new(e.outputs[0], out.inputs[0])
    MATS['moon'] = m

    return MATS

def _slate_nodes(nt, mapn, tc=None):
    src = mapn
    if src is None:
        src = tc
    wave = nt.nodes.new('ShaderNodeTexWave')
    wave.inputs['Scale'].default_value = 0.8
    wave.inputs['Distortion'].default_value = 3.0
    if src is not None:
        nt.links.new(src.outputs[0] if hasattr(src, 'outputs') else src, wave.inputs['Vector'])
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Scale'].default_value = 0.7
    br.inputs['Color1'].default_value = (0.02, 0.03, 0.05, 1)
    br.inputs['Color2'].default_value = (0.035, 0.05, 0.075, 1)
    br.inputs['Mortar'].default_value = (0.015, 0.02, 0.03, 1)
    br.inputs['Mortar Size'].default_value = 0.02
    if src is not None:
        nt.links.new(src.outputs[0], br.inputs['Vector'])
    nn = nt.nodes.new('ShaderNodeTexNoise')
    nn.inputs['Scale'].default_value = 0.15
    if src is not None:
        nt.links.new(src.outputs[0], nn.inputs['Vector'])
    mixn = nt.nodes.new('ShaderNodeMix')
    mixn.data_type = 'RGBA'
    mixn.inputs[0].default_value = 0.4
    nt.links.new(br.outputs['Color'], mixn.inputs[6])
    mixn.inputs[7].default_value = (0.05, 0.06, 0.08, 1)
    nt.links.new(nn.outputs['Fac'], mixn.inputs[0])
    return mixn.outputs[2]

TERR = {}
PLAT = 42.0
MOON_DIR = Vector((0.34, 0.86, 0.38)).normalized()
SPUR_A = (-34.0, -48.0)
SPUR_B = (-64.0, -100.0)

def terrain_h(X, Y):
    ang = np.arctan2(Y, X)
    an = 0.16 * np.sin(ang * 3 + 1.7) + 0.10 * np.sin(ang * 5 + 0.4) + 0.06 * np.sin(ang * 8 + 2.9)
    rn = np.sqrt(X ** 2 + Y ** 2) * (1 + an)
    t = np.clip((rn - 62) / 38, 0, 1)
    sm = t * t * (3 - 2 * t)
    n1 = fbm_np(X * 0.02, Y * 0.02, 1.0, 4)
    u = np.clip((t - 0.45) / 0.35, 0, 1)
    base = 42 * (1 - u) ** 1.1
    terr = np.floor(base / 5.0) * 5.0
    ledge = base - terr
    ridge = 1 - np.abs(fbm_np(X * 0.02, Y * 0.02, 4.0, 4))
    cliff = terr + ledge * (0.35 + 0.65 * ridge)
    rock = fbm_np(X * 0.04, Y * 0.04, 9.0, 5)
    cliff = cliff + rock * 10.0 * u * (1 - u)
    rock2 = fbm_np(X * 0.22, Y * 0.22, 11.0, 4)
    cliff = cliff + rock2 * 6.0 * u * (1 - u) * 2.0
    rock3 = fbm_np(X * 0.5, Y * 0.5, 13.0, 3)
    cliff = cliff + rock3 * 1.2 * u * (1 - u) * 2.0
    cliff = cliff + np.sin(base * 0.9 + n1 * 3) * 0.8 * (u > 0) * (u < 1)
    n2 = fbm_np(X * 0.008, Y * 0.008, 2.0, 4)
    n3 = fbm_np(X * 0.03, Y * 0.03, 3.0, 3)
    moor = 2.2 + 3.0 * n2 + 1.0 * n3 + 14 * np.clip((rn - 160) / 250, 0, 1) ** 1.6 * (0.6 + 0.4 * n2)
    h = cliff + moor * u
    h = h + 0.4 * n3 * (rn < 82)
    lake = np.clip((-Y - 70) / 40, 0, 1) * np.clip((rn - 95) / 15, 0, 1)
    lake = lake * lake * (3 - 2 * lake)
    h = h + (-3.5 - h) * lake
    inlet = np.exp(-((Y + 35) / 28) ** 2) * np.clip((X - 55) / 25, 0, 1)
    h = h + (-4.0 - h) * np.clip(inlet, 0, 1) * 0.9
    d2 = np.sqrt((X - 132) ** 2 + (Y + 42) ** 2)
    h = h + 30 * np.exp(-(d2 / 30) ** 2)
    d3 = np.sqrt((X + 60) ** 2 + (Y + 92) ** 2)
    h = np.maximum(h, 2.0 * np.exp(-(d3 / 14) ** 2) + 0.3)
    d4 = np.sqrt((X + 95) ** 2 + (Y + 45) ** 2)
    h = h + 12 * np.exp(-(d4 / 11) ** 2)
    d5 = np.sqrt((X - 120) ** 2 + (Y + 230) ** 2)
    h = h + 7 * np.exp(-(d5 / 45) ** 2)
    ax, ay = SPUR_A
    bx, by = SPUR_B
    abx, aby = bx - ax, by - ay
    L2 = abx * abx + aby * aby
    s = np.clip(((X - ax) * abx + (Y - ay) * aby) / L2, 0, 1)
    dx = X - (ax + s * abx)
    dy = Y - (ay + s * aby)
    dsp = np.sqrt(dx * dx + dy * dy)
    spur_h = (40 * (1 - s) + 1.5 * s) - dsp * 1.1
    spur_h = np.maximum(spur_h, 0) * np.exp(-(dsp / 14) ** 2)
    h = np.maximum(h, spur_h)
    cm = (t > 0.03) & (t < 0.97)
    n1c = fbm_np(X * 0.015, Y * 0.015, 5.0, 3)
    h = h + np.sin(h * 0.8 + n1 * 4) * (0.25 + 0.5 * (n1c > 0)) * cm
    return h, rn, t

PATH_SEGS = [((-40, -62), (-30, -52)), ((-30, -52), (-38, -44)), ((-38, -44), (-26, -34)),
             ((-26, -34), (-30, -24)), ((-30, -24), (-16, -14)), ((-16, -14), (0, -6)),
             ((0, -6), (20, -8)), ((20, -8), (45, -8)), ((45, -8), (74, -8)),
             ((0, -6), (-20, 2)), ((-20, 2), (-45, 4))]

def path_mask(X, Y):
    dmin = np.full_like(X, 1e9)
    for (a, b) in PATH_SEGS:
        ax, ay = a
        bx, by = b
        abx, aby = bx - ax, by - ay
        L2 = abx * abx + aby * aby
        tt = np.clip(((X - ax) * abx + (Y - ay) * aby) / L2, 0, 1)
        dx = X - (ax + tt * abx)
        dy = Y - (ay + tt * aby)
        dmin = np.minimum(dmin, np.sqrt(dx * dx + dy * dy))
    return np.clip(1 - dmin / 2.0, 0, 1)

def build_terrain():
    nx, ny = 760, 680
    xs = np.linspace(-450, 450, nx)
    ys = np.linspace(-450, 350, ny)
    X, Y = np.meshgrid(xs, ys)
    H, rn, t = terrain_h(X, Y)
    pm = path_mask(X, Y)
    gy, gx = np.gradient(H)
    slope = np.sqrt(gx ** 2 + gy ** 2)
    me = bpy.data.meshes.new('Terrain')
    verts = np.stack([X, Y, H], axis=-1).reshape(-1, 3)
    me.vertices.add(len(verts))
    me.vertices.foreach_set('co', verts.ravel())
    faces = []
    idx = np.arange(ny * nx).reshape(ny, nx)
    for j in range(ny - 1):
        for i in range(nx - 1):
            faces.append((idx[j, i], idx[j, i + 1], idx[j + 1, i + 1], idx[j + 1, i]))
    me.loops.add(len(faces) * 4)
    me.polygons.add(len(faces))
    me.loops.foreach_set('vertex_index', np.array(faces).ravel())
    me.polygons.foreach_set('loop_start', np.arange(len(faces)) * 4)
    me.polygons.foreach_set('loop_total', np.full(len(faces), 4))
    me.update()
    me.validate()
    if len(me.polygons) and me.polygons[0].normal.z < 0:
        me.flip_normals()
    at = me.attributes.new('path', 'FLOAT', 'POINT')
    at.data.foreach_set('value', pm.ravel())
    ob = bpy.data.objects.new('Terrain', me)
    HL.get_coll('Terrain').objects.link(ob)
    d5 = np.sqrt((X - 120) ** 2 + (Y + 230) ** 2)
    d3 = np.sqrt((X + 60) ** 2 + (Y + 92) ** 2)
    forest = ((H > 1.0) & (H < 24) & (slope < 0.8) & (pm < 0.3) &
              ((rn > 100) | (d5 < 70)) & (d3 > 18)).astype(np.float32)
    vg = ob.vertex_groups.new(name='forest')
    flat = forest.ravel()
    nz_ids = np.nonzero(flat)[0]
    vg.add(list(map(int, nz_ids)), 1.0, 'REPLACE')
    TERR['xs'] = xs
    TERR['ys'] = ys
    TERR['H'] = H
    return ob

def ground(x, y):
    xs, ys, H = TERR['xs'], TERR['ys'], TERR['H']
    fx = np.clip((x - xs[0]) / (xs[-1] - xs[0]) * (len(xs) - 1), 0, len(xs) - 1.001)
    fy = np.clip((y - ys[0]) / (ys[-1] - ys[0]) * (len(ys) - 1), 0, len(ys) - 1.001)
    i = int(fx)
    j = int(fy)
    tx = fx - i
    ty = fy - j
    h00 = H[j, i]
    h10 = H[j, min(i + 1, len(xs) - 1)]
    h01 = H[min(j + 1, len(ys) - 1), i]
    h11 = H[min(j + 1, len(ys) - 1), min(i + 1, len(xs) - 1)]
    return h00 * (1 - tx) * (1 - ty) + h10 * tx * (1 - ty) + h01 * (1 - tx) * ty + h11 * tx * ty

def build_water():
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=3000)
    ob = HL.new_obj('Water', bm, 'Terrain')
    ob.location = (0, 0, 0.35)
    return ob

def build_mountains():
    for (y0, amp, seed) in ((1600, 200, 7.3), (2400, 420, 13.7), (3400, 700, 29.1)):
        bm = bmesh.new()
        nx, ny = 120, 14
        grid = {}
        for j in range(ny):
            for i in range(nx):
                u = i / (nx - 1)
                v = j / (ny - 1)
                x = -1900 + 3800 * u
                y = y0 + 500 * v
                n = mnoise.noise(Vector((x * 0.0008, y * 0.0008, seed)))
                n2 = mnoise.noise(Vector((x * 0.003, y * 0.003, seed * 2)))
                r = max(0.0, 0.5 + 0.45 * n + 0.35 * n2) ** 1.6
                w = math.sin(math.pi * v) ** 0.6 * math.sin(math.pi * u) ** 0.3
                grid[(i, j)] = bm.verts.new(Vector((x, y, amp * r * w)))
        for j in range(ny - 1):
            for i in range(nx - 1):
                bm.faces.new((grid[(i, j)], grid[(i + 1, j)], grid[(i + 1, j + 1)], grid[(i, j + 1)]))
        HL.new_obj('Mountain_%d' % seed, bm, 'Terrain')

def make_tree(name, h, rng):
    bm = bmesh.new()
    HL.bm_cyl(bm, 0.25, h * 0.3, seg=6, z0=0)
    tiers = 4
    for i in range(tiers):
        z = h * 0.18 + (h * 0.82) * i / tiers
        r = (h * 0.22) * (1 - i / (tiers + 0.5)) * rng.uniform(0.9, 1.1)
        HL.bm_cone(bm, r, h * 0.38, seg=8, z0=z)
    ob = HL.new_obj(name, bm, 'TreeAssets')
    ob.data.materials.append(MATS['tree'])
    return ob

def build_forest():
    tc = HL.get_coll('TreeAssets')
    rng = random.Random(42)
    for i, h in enumerate((9, 12, 15)):
        make_tree('Conifer_%d' % i, h, rng)
    tob = bpy.data.objects.get('Terrain')
    ps_mod = tob.modifiers.new('forest', 'PARTICLE_SYSTEM')
    psys = tob.particle_systems[-1]
    st = psys.settings
    st.type = 'HAIR'
    st.count = 14000
    st.hair_length = 1.0
    st.use_advanced_hair = True
    st.render_type = 'COLLECTION'
    st.instance_collection = tc
    st.use_rotation_instance = False
    st.particle_size = 1.25
    st.size_random = 0.45
    st.use_rotations = True
    st.rotation_mode = 'GLOB_Z'
    st.rotation_factor_random = 0.08
    st.phase_factor_random = 2.0
    psys.vertex_group_density = 'forest'
    sc = bpy.context.scene
    if tc.name in [c.name for c in sc.collection.children]:
        sc.collection.children.unlink(tc)

def build_sky():
    w = bpy.data.worlds.get('World') or bpy.data.worlds.new('World')
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    nt.links.new(bg.outputs[0], out.inputs[0])
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    dz = nt.nodes.new('ShaderNodeMath')
    dz.operation = 'MAXIMUM'
    dz.inputs[1].default_value = 0.0
    nt.links.new(sep.outputs['Z'], dz.inputs[0])
    hgt = nt.nodes.new('ShaderNodeMath')
    hgt.operation = 'POWER'
    hgt.inputs[1].default_value = 0.55
    nt.links.new(dz.outputs[0], hgt.inputs[0])
    skycol = _mix(nt, hgt.outputs[0], (0.016, 0.042, 0.06, 1), (0.0015, 0.004, 0.010, 1))
    stn = nt.nodes.new('ShaderNodeTexNoise')
    stn.inputs['Scale'].default_value = 420.0
    stn.inputs['Detail'].default_value = 2.0
    nt.links.new(tc.outputs['Generated'], stn.inputs['Vector'])
    sthr = nt.nodes.new('ShaderNodeMath')
    sthr.operation = 'GREATER_THAN'
    sthr.inputs[1].default_value = 0.78
    nt.links.new(stn.outputs['Fac'], sthr.inputs[0])
    stmul = nt.nodes.new('ShaderNodeMath')
    stmul.operation = 'MULTIPLY'
    stmul.inputs[1].default_value = 0.25
    nt.links.new(sthr.outputs[0], stmul.inputs[0])
    nt.links.new(sep.outputs['Z'], stmul.inputs[1])
    col_star = nt.nodes.new('ShaderNodeMix')
    col_star.data_type = 'RGBA'
    col_star.blend_type = 'ADD'
    col_star.inputs[0].default_value = 1.0
    nt.links.new(skycol, col_star.inputs[6])
    stcol = nt.nodes.new('ShaderNodeCombineColor')
    nt.links.new(stmul.outputs[0], stcol.inputs[0])
    nt.links.new(stmul.outputs[0], stcol.inputs[1])
    nt.links.new(stmul.outputs[0], stcol.inputs[2])
    nt.links.new(stcol.outputs[0], col_star.inputs[7])
    dot = nt.nodes.new('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    nt.links.new(tc.outputs['Generated'], dot.inputs[0])
    dot.inputs[1].default_value = MOON_DIR
    halo1 = nt.nodes.new('ShaderNodeMath')
    halo1.operation = 'POWER'
    halo1.inputs[1].default_value = 900.0
    dm = nt.nodes.new('ShaderNodeMath')
    dm.operation = 'MAXIMUM'
    dm.inputs[1].default_value = 0.0
    nt.links.new(dot.outputs['Value'], dm.inputs[0])
    nt.links.new(dm.outputs[0], halo1.inputs[0])
    h1m = nt.nodes.new('ShaderNodeMath')
    h1m.operation = 'MULTIPLY'
    h1m.inputs[1].default_value = 2.5
    nt.links.new(halo1.outputs[0], h1m.inputs[0])
    halo2 = nt.nodes.new('ShaderNodeMath')
    halo2.operation = 'POWER'
    halo2.inputs[1].default_value = 8.0
    nt.links.new(dm.outputs[0], halo2.inputs[0])
    h2m = nt.nodes.new('ShaderNodeMath')
    h2m.operation = 'MULTIPLY'
    h2m.inputs[1].default_value = 0.08
    nt.links.new(halo2.outputs[0], h2m.inputs[0])
    hsum = nt.nodes.new('ShaderNodeMath')
    hsum.operation = 'ADD'
    nt.links.new(h1m.outputs[0], hsum.inputs[0])
    nt.links.new(h2m.outputs[0], hsum.inputs[1])
    hcol = nt.nodes.new('ShaderNodeCombineColor')
    for i in range(3):
        nt.links.new(hsum.outputs[0], hcol.inputs[i])
    col_moon = nt.nodes.new('ShaderNodeMix')
    col_moon.data_type = 'RGBA'
    col_moon.blend_type = 'ADD'
    col_moon.inputs[0].default_value = 1.0
    nt.links.new(col_star.outputs[2], col_moon.inputs[6])
    nt.links.new(hcol.outputs[0], col_moon.inputs[7])
    nt.links.new(col_moon.outputs[2], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 1.0

def build_moon():
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=32, radius=80)
    ob = HL.new_obj('Moon', bm, 'FX')
    ob['mat'] = 'moon'
    ob.location = MOON_DIR * 2600
    d = (MOON_DIR * -1.0)
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    ob.visible_shadow = False
    return ob

def build_clouds():
    m, nt = new_mat('M_Cloud')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    cn = nt.nodes.new('ShaderNodeTexNoise')
    cn.inputs['Scale'].default_value = 0.0016
    cn.inputs['Detail'].default_value = 8.0
    cn.inputs['Roughness'].default_value = 0.62
    nt.links.new(tc.outputs['Object'], cn.inputs['Vector'])
    al = nt.nodes.new('ShaderNodeValToRGB')
    al.color_ramp.elements[0].position = 0.44
    al.color_ramp.elements[1].position = 0.62
    nt.links.new(cn.outputs['Fac'], al.inputs[0])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (0.045, 0.075, 0.10, 1)
    em.inputs['Strength'].default_value = 0.8
    mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(al.outputs[0], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs[0])
    MATS['cloud'] = m
    for (z, sc) in ((520, 2600), (760, 3200)):
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=sc)
        ob = HL.new_obj('Clouds_%d' % z, bm, 'FX')
        ob.location = (0, 600, z)
        ob['mat'] = 'cloud'
        ob.visible_shadow = False

def build_mist():
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    ob = HL.new_obj('Mist', bm, 'FX')
    ob.scale = (500, 550, 6)
    ob.location = (0, -150, 6)
    ob['mat'] = 'mist'
    ob.visible_shadow = False

def build_lights():
    old = bpy.data.objects.get('Moonlight')
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    sd = bpy.data.lights.new('Moonlight', 'SUN')
    sd.energy = 2.0
    sd.color = (0.62, 0.75, 1.0)
    sd.angle = math.radians(2.0)
    ob = bpy.data.objects.new('Moonlight', sd)
    HL.get_coll('Lights').objects.link(ob)
    d = MOON_DIR * -1.0
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    oldf = bpy.data.objects.get('FillLight')
    if oldf:
        bpy.data.objects.remove(oldf, do_unlink=True)
    fd = bpy.data.lights.new('FillLight', 'SUN')
    fd.energy = 1.1
    fd.color = (0.5, 0.65, 0.9)
    fd.angle = math.radians(15.0)
    fo = bpy.data.objects.new('FillLight', fd)
    HL.get_coll('Lights').objects.link(fo)
    fdir = Vector((0.55, 0.25, -0.8)).normalized()
    fo.rotation_mode = 'QUATERNION'
    fo.rotation_quaternion = fdir.to_track_quat('-Z', 'Y')

def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = d.to_track_quat('-Z', 'Y')

def build_cameras():
    cams = [
        ('Cam_Hero', (26, -225, 16), (-8, -5, 55), 32),
        ('Cam_Aerial', (260, -260, 150), (0, 10, 45), 40),
        ('Cam_Boathouse', (-118, -148, 4), (-58, -92, 26), 28),
        ('Cam_Viaduct', (168, -120, 18), (95, -20, 42), 35),
    ]
    for (n, loc, tgt, mm) in cams:
        cd = bpy.data.cameras.new(n)
        cd.lens = mm
        cd.clip_end = 8000
        ob = bpy.data.objects.new(n, cd)
        HL.get_coll('Cameras').objects.link(ob)
        ob.location = loc
        look_at(ob, tgt)

COPPER = {'T_MainAtt1', 'T_East3'}

def assign_materials():
    for coll in ('Castle', 'Lights', 'Terrain', 'Nature', 'FX'):
        c = bpy.data.collections.get(coll)
        if not c:
            continue
        for ob in c.objects:
            if ob.type != 'MESH':
                continue
            me = ob.data
            tag = ob.get('mat')
            if tag == 'lantern':
                me.materials.clear()
                me.materials.append(MATS['iron'])
                me.materials.append(MATS['lanternglow'])
                zmin = min((ob.matrix_world @ v.co).z for v in me.vertices)
                for p in me.polygons:
                    z = (ob.matrix_world @ p.center).z
                    p.material_index = 1 if (zmin + 2.62) < z < (zmin + 2.96) else 0
                continue
            if tag and tag in MATS:
                me.materials.clear()
                me.materials.append(MATS[tag])
                continue
            if ob.name.endswith('_glass'):
                me.materials.clear()
                me.materials.append(MATS['glass'])
                continue
            if coll == 'Castle':
                me.materials.clear()
                base = ob.name.split('.')[0]
                key = [k for k in COPPER if base.startswith(k)]
                me.materials.append(MATS['stonecopper'] if key else MATS['stone'])
                continue
            if ob.name == 'Terrain':
                me.materials.clear()
                me.materials.append(MATS['ground'])
            elif ob.name == 'Water':
                me.materials.clear()
                me.materials.append(MATS['water'])
            elif ob.name.startswith('Mountain'):
                me.materials.clear()
                me.materials.append(MATS['mountain'])
            elif ob.name.startswith('Conifer'):
                me.materials.clear()
                me.materials.append(MATS['tree'])

def setup_render(final=False):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 1024 if final else 64
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.01 if final else 0.05
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    sc.cycles.volume_step_rate = 1.0
    sc.cycles.volume_max_steps = 256
    sc.cycles.volume_bounces = 1
    sc.cycles.transparent_max_bounces = 16
    sc.render.resolution_x = 3840
    sc.render.resolution_y = 2160
    sc.render.resolution_percentage = 100 if final else 33
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.view_settings.exposure = 1.0
    sc.render.image_settings.file_format = 'PNG'

def clean_default():
    for n in ('Cube', 'Light', 'Camera'):
        ob = bpy.data.objects.get(n)
        if ob:
            bpy.data.objects.remove(ob, do_unlink=True)

def build_castle():
    HL.clear_coll('Castle')
    lc = bpy.data.collections.get('Lights')
    if lc:
        for ob in list(lc.objects):
            if ob.name.startswith('Lantern'):
                bpy.data.objects.remove(ob, do_unlink=True)
    rng = random.Random(9)
    P = 41.5
    HL.build_hall('Hall', (-52, 10), 0, 54, 13, 18, base_z=P)
    HL.build_tower('T_Main', (-4, 10), 8.5, 46, cap='cone', base_z=P, roof_h=34, cols=6, rows=5, seg=24)
    HL.build_tower('T_Att1', (-16, 22), 5, 36, cap='cone', base_z=P, cols=4, rows=4)
    HL.build_tower('T_MainAtt1', (8, 24), 4.5, 32, cap='cone', base_z=P, cols=4, rows=3)
    HL.build_tower('T_Att2', (10, 0), 5.5, 34, cap='spire', base_z=P, cols=4, rows=4)
    HL.build_tower('T_Att3', (-18, -2), 4, 26, cap='crenel', base_z=P, cols=3, rows=3)
    HL.build_clock('ClockTower', (24, -8), 9, 40, base_z=P)
    HL.build_tower('T_East1', (40, 10), 6, 40, cap='cone', base_z=P, cols=5, rows=4)
    HL.build_tower('T_East2', (52, 20), 5, 32, cap='spire', base_z=P, cols=4, rows=3)
    HL.build_tower('T_East3', (60, 6), 4, 27, cap='cone', base_z=P, cols=3, rows=3)
    HL.build_tower('T_East4', (48, -2), 4.5, 30, cap='cone', base_z=P, cols=4, rows=3)
    HL.build_tower('T_East5', (68, 14), 3.5, 22, cap='crenel', base_z=P, cols=3, rows=2)
    HL.build_tower('T_East6', (36, 24), 4, 30, cap='cone', base_z=P, cols=3, rows=3)
    HL.build_tower('T_Court1', (14, -16), 3, 20, cap='cone', base_z=P, cols=3, rows=2)
    HL.build_tower('T_Court2', (58, -10), 3, 18, cap='crenel', base_z=P, cols=3, rows=2)
    ring = [(-80, 20), (-80, -10), (-62, -32), (-30, -44), (5, -48), (40, -42),
            (66, -30), (80, -8), (80, 20), (-80, 20)]
    for i in range(len(ring) - 1):
        HL.build_wall('RingWall_%d' % i, ring[i], ring[i + 1], 5.5, t=1.4, z0=P - 1.5)
    terr = [((-20, -100), (30, -106)), ((30, -106), (70, -90)), ((-60, -96), (-20, -100))]
    for i, (a, b) in enumerate(terr):
        g = min(ground(a[0], a[1]), ground(b[0], b[1]))
        HL.build_wall('TerraceWall_%d' % i, a, b, 10, t=1.6, z0=g - 3)
    g = ground(66, -64)
    bm = bmesh.new()
    HL.bm_box(bm, 24, 16, 3, mat=HL.M4((66, -64, g - 1)))
    HL.new_obj('GHTerrace', bm, 'Castle')
    HL.build_greenhouse('GH1', (60, -64, g + 2), 7, 12, 3.2, rot_z=math.radians(90))
    HL.build_greenhouse('GH2', (70, -64, g + 2), 6, 10, 2.8, rot_z=math.radians(90))
    sb = []
    av = Vector((SPUR_A[0], SPUR_A[1], 0))
    bv = Vector((SPUR_B[0], SPUR_B[1], 0))
    ab = bv - av
    perp = Vector((-ab.y, ab.x, 0)).normalized()
    for i, s in enumerate((1.0, 0.82, 0.64, 0.46, 0.28, 0.1, 0.0)):
        off = 0.0 if i in (0, 6) else (5.0 if i % 2 else -5.0)
        p = av + ab * s + perp * off
        sb.append((p.x, p.y))
    zs = [1.5]
    for (x, y) in sb[1:-1]:
        zs.append(max(ground(x, y) + 0.5, zs[-1] + 2))
    zs.append(PLAT)
    for i in range(len(sb) - 1):
        HL.build_stair('Stair_%d' % i, sb[i], sb[i + 1], zs[i], zs[i + 1])
    for i in range(1, len(sb) - 1):
        bml = bmesh.new()
        HL.bm_box(bml, 3.4, 3.4, 1.0, mat=HL.M4((sb[i][0], sb[i][1], zs[i] - 1.0)))
        HL.new_obj('Landing_%d' % i, bml, 'Castle')
        HL.build_lantern('Lantern_S%d' % i, (sb[i][0] + 1.2, sb[i][1] + 1.2), zs[i])
    HL.build_viduct('Viaduct', (76, -10), (132, -42), 36, arch_n=7, width=5.5)
    HL.build_tower('T_Gate', (76, -10), 4, 16, cap='crenel', base_z=30, cols=3, rows=2)
    vdir = Vector((132 - 76, -42 + 10, 0)).normalized()
    vlen = (Vector((132, -42, 0)) - Vector((76, -10, 0))).length
    for i in range(1, 6):
        d = vlen * i / 6
        p = Vector((76, -10, 0)) + vdir * d
        HL.build_lantern('Lantern_V%d' % i, (p.x, p.y - 2.4), 36.5)
    for i, (x, y) in enumerate(((0, -8), (20, -12), (45, -10), (-30, 0), (-70, 4))):
        HL.build_lantern('Lantern_C%d' % i, (x, y), P)
    bh_g = ground(SPUR_B[0], SPUR_B[1])
    bxs, bys = SPUR_B
    bms = bmesh.new()
    HL.bm_box(bms, 11, 9, 4, mat=HL.M4((bxs, bys, bh_g - 1.5)))
    HL.new_obj('Boathouse_Base', bms, 'Castle')
    bmw = bmesh.new()
    HL.bm_box(bmw, 8, 6.5, 4.5, mat=HL.M4((bxs, bys, bh_g + 2.5)))
    obw = HL.new_obj('Boathouse_Wood', bmw, 'Castle')
    obw['mat'] = 'wood'
    bmr = bmesh.new()
    prof = [(-4.6, 0), (4.6, 0), (4.6, 0.3), (0, 3.6), (-4.6, 0.3)]
    vs = [bmr.verts.new(Vector((x, -3.8, z))) for (x, z) in prof]
    vs2 = [bmr.verts.new(Vector((x, 3.8, z))) for (x, z) in prof]
    n = len(vs)
    for i in range(n):
        j = (i + 1) % n
        bmr.faces.new((vs[i], vs[j], vs2[j], vs2[i]))
    bmr.faces.new(vs)
    bmr.faces.new(list(reversed(vs2)))
    bmesh.ops.transform(bmr, matrix=HL.M4((bxs, bys, bh_g + 7.0)), verts=bmr.verts[:])
    obr = HL.new_obj('Boathouse_Roof', bmr, 'Castle')
    obr['mat'] = 'slate'
    bmt = bmesh.new()
    HL.bm_cyl(bmt, 0.8, 2.2, seg=8, mat=HL.M4((bxs, bys, bh_g + 10.2)))
    HL.bm_cone(bmt, 1.1, 2.4, seg=8, mat=HL.M4((bxs, bys, bh_g + 12.2)))
    HL.finial(bmt, bh_g + 14.4, mat=HL.M4((bxs, bys, 0)))
    obt = HL.new_obj('Boathouse_Turret', bmt, 'Castle')
    obt['mat'] = 'slate'
    bmj = bmesh.new()
    HL.bm_box(bmj, 3, 16, 0.35, mat=HL.M4((bxs - 2, bys - 12, 0.9)))
    for k in range(4):
        HL.bm_cyl(bmj, 0.15, 2.2, seg=6, mat=HL.M4((bxs - 3.3 + (k % 2) * 2.6, bys - 6 - (k // 2) * 8, -1.0)))
    obj = HL.new_obj('Jetty', bmj, 'Castle')
    obj['mat'] = 'wood'
    HL.build_lantern('Lantern_J0', (bxs - 3.5, bys - 17), 1.4)
    HL.build_lantern('Lantern_J1', (bxs + 4, bys - 6), bh_g + 0.5)
    og = ground(-95, -45)
    HL.build_tower('Owlery', (-95, -45), 2.2, 8, cap='cone', base_z=og - 1, cols=3, rows=2, win_w=0.5, win_h=1.0)
    hg = ground(-140, -140)
    bmh = bmesh.new()
    HL.bm_cyl(bmh, 3.2, 3.2, seg=12, mat=HL.M4((-140, -140, hg - 0.5)))
    HL.bm_cone(bmh, 3.9, 3.4, seg=12, mat=HL.M4((-140, -140, hg + 2.7)))
    HL.bm_cyl(bmh, 0.5, 4.5, seg=8, mat=HL.M4((-138.5, -141, hg)))
    obh = HL.new_obj('Hut', bmh, 'Castle')
    sm = bmesh.new()
    bmesh.ops.create_cube(sm, size=2.0)
    obsm = HL.new_obj('HutSmoke', sm, 'FX')
    obsm.scale = (1.2, 1.2, 5)
    obsm.location = (-138.5, -141, hg + 8)
    obsm['mat'] = 'smoke'
    obsm.visible_shadow = False

def build_all():
    clean_default()
    for cn in ('Castle', 'Terrain', 'Nature', 'Lights', 'FX', 'Cameras', 'TreeAssets'):
        HL.get_coll(cn)
    for cn in ('Terrain', 'FX', 'Cameras', 'TreeAssets', 'Nature'):
        HL.clear_coll(cn)
    ensure_materials()
    build_terrain()
    build_water()
    build_mountains()
    build_forest()
    build_sky()
    build_moon()
    build_clouds()
    build_mist()
    build_lights()
    build_castle()
    build_cameras()
    assign_materials()
    setup_render(False)

def render_check(cam_name, path, res_pct=25, samples=48):
    sc = bpy.context.scene
    cam = bpy.data.objects.get(cam_name)
    sc.camera = cam
    sc.render.resolution_percentage = res_pct
    sc.cycles.samples = samples
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path
