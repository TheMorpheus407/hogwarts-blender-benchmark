"""Pass 4 — procedural materials (all shader nodes, no textures)."""
import bpy, os, sys, importlib, math
FOLDER = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else bpy.path.abspath("//")
if FOLDER not in sys.path:
    sys.path.insert(0, FOLDER)
import hog_lib as H; importlib.reload(H)
from hog_lib import NB, new_material

def _out(nb, shader, volume=None, displacement=None):
    out = nb.n("ShaderNodeOutputMaterial")
    nb.link(shader, out.inputs["Surface"])
    if volume is not None:
        nb.link(volume, out.inputs["Volume"])
    if displacement is not None:
        nb.link(displacement, out.inputs["Displacement"])
    return out

# --------------------------------------------------------------------------- stone
def mat_stone(name="M_Stone", base=(0.40, 0.36, 0.30), trim=False, moss_amount=1.0, batch_scale=0.06):
    m = new_material(name); nb = NB(m.node_tree)
    tc = nb.n("ShaderNodeTexCoord")
    geo = nb.n("ShaderNodeNewGeometry")
    # --- quarry-batch colour variation: big voronoi cells in world space
    vor = nb.n("ShaderNodeTexVoronoi", Vector=tc.outputs["Object"], Scale=batch_scale, _feature='F1', _distance='EUCLIDEAN', Randomness=1.0)
    batch = nb.n("ShaderNodeValToRGB", Factor=vor.outputs["Color"])
    cr = batch.color_ramp; cr.elements[0].color = (0.80, 0.79, 0.76, 1); cr.elements[1].color = (1.14, 1.10, 1.05, 1)
    # per-object random shift so no two towers are identical
    oi = nb.n("ShaderNodeObjectInfo")
    objv = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=oi.outputs["Random"], Value_1=0.16, Value_2=0.92)
    # --- ashlar courses
    if trim:
        bw, bh = 1.0, 0.55
    else:
        bw, bh = 1.6, 0.62
    mapping = nb.n("ShaderNodeMapping", Vector=tc.outputs["Object"], Rotation=(0.0, 0.0, 0.0))
    # bricks are laid in the XZ plane for walls facing Y and YZ for walls facing X: mix both via normal
    # (cheap triplanar: choose the horizontal axis by |N.x| vs |N.y|)
    sep = nb.n("ShaderNodeSeparateXYZ", Vector=mapping.outputs["Vector"])
    nrm = nb.n("ShaderNodeSeparateXYZ", Vector=geo.outputs["Normal"])
    absx = nb.n("ShaderNodeMath", _operation='ABSOLUTE', Value=nrm.outputs["X"])
    absy = nb.n("ShaderNodeMath", _operation='ABSOLUTE', Value=nrm.outputs["Y"])
    usex = nb.n("ShaderNodeMath", _operation='GREATER_THAN', Value=absx.outputs[0], Value_1=absy.outputs[0])
    hcoord = nb.n("ShaderNodeMix", _data_type='FLOAT', Factor=usex.outputs[0], A=sep.outputs["X"], B=sep.outputs["Y"])
    bvec = nb.n("ShaderNodeCombineXYZ", X=hcoord.outputs["Result"], Y=sep.outputs["Z"], Z=0.0)
    brickA = nb.n("ShaderNodeTexBrick", Vector=bvec.outputs[0], Scale=1.0, Color1=(0.76, 0.78, 0.80, 1), Color2=(1.18, 1.13, 1.05, 1),
                  Mortar=(0.62, 0.58, 0.53, 1), Mortar__Size=0.014 if not trim else 0.006, Mortar__Smooth=0.6, Bias=0.0, Brick__Width=bw, Row__Height=bh)
    brickA.offset = 0.5; brickA.squash = 1.0
    brickB = nb.n("ShaderNodeTexBrick", Vector=bvec.outputs[0], Scale=1.0, Color1=(0.78, 0.79, 0.79, 1), Color2=(1.16, 1.12, 1.05, 1),
                  Mortar=(0.62, 0.58, 0.53, 1), Mortar__Size=0.014 if not trim else 0.006, Mortar__Smooth=0.6, Bias=0.0, Brick__Width=bw * 1.55, Row__Height=bh)
    brickB.offset = 0.33; brickB.squash = 1.0
    bondn = nb.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=0.22, Detail=2.0)
    bondm = nb.n("ShaderNodeMath", _operation='GREATER_THAN', Value=bondn.outputs["Factor"], Value_1=0.5)
    brick_col = nb.n("ShaderNodeMix", _data_type='RGBA', Factor=bondm.outputs[0], A=brickA.outputs["Color"], B=brickB.outputs["Color"])
    brick_fac = nb.n("ShaderNodeMix", _data_type='FLOAT', Factor=bondm.outputs[0], A=brickA.outputs["Factor"], B=brickB.outputs["Factor"])
    class _B: pass
    brick = _B(); brick.outputs = {"Color": nb.o(brick_col, "Result"), "Factor": nb.o(brick_fac, "Result")}
    # --- surface grime / weathering noise (fine and coarse)
    n_fine = nb.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=9.0, Detail=6.0, Roughness=0.62)
    n_coarse = nb.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=0.35, Detail=4.0, Roughness=0.5)
    grime = nb.n("ShaderNodeValToRGB", Factor=n_coarse.outputs["Factor"])
    grime.color_ramp.elements[0].position = 0.35; grime.color_ramp.elements[0].color = (0.48, 0.47, 0.46, 1)
    grime.color_ramp.elements[1].position = 0.65; grime.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1)
    # --- dirt streaking under ledges: AO (crevices/overhangs) × vertically stretched noise
    ao = nb.n("ShaderNodeAmbientOcclusion", Distance=1.6, _samples=4, _only_local=True)
    ao_inv = nb.n("ShaderNodeMath", _operation='SUBTRACT', Value=1.0, Value_1=ao.outputs["AO"])
    smap = nb.n("ShaderNodeMapping", Vector=tc.outputs["Object"], Scale=(6.0, 6.0, 0.35))
    streak_n = nb.n("ShaderNodeTexNoise", Vector=smap.outputs["Vector"], Scale=1.0, Detail=3.0, Roughness=0.6)
    streak = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=streak_n.outputs["Factor"], Value_1=ao_inv.outputs[0])
    streak2 = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=streak.outputs[0], Value_1=2.2, _use_clamp=True)
    # --- moss: upward-ish faces, low on the building, crevices, noise
    up = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=nrm.outputs["Z"], Value_1=0.9, Value_2=0.35, _use_clamp=True)
    wpos = nb.n("ShaderNodeSeparateXYZ", Vector=geo.outputs["Position"])
    low = nb.n("ShaderNodeMapRange", Value=wpos.outputs["Z"], From__Min=95.0, From__Max=45.0, To__Min=0.15, To__Max=1.0)
    mossn = nb.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=1.6, Detail=5.0, Roughness=0.6)
    mossr = nb.n("ShaderNodeValToRGB", Factor=mossn.outputs["Factor"])
    mossr.color_ramp.elements[0].position = 0.48; mossr.color_ramp.elements[1].position = 0.66
    m1 = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=up.outputs[0], Value_1=low.outputs["Result"])
    m2 = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=m1.outputs[0], Value_1=mossr.outputs["Color"])
    aoc = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=ao_inv.outputs[0], Value_1=0.6, Value_2=0.7)
    moss = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=m2.outputs[0], Value_1=aoc.outputs[0])
    mossf = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=moss.outputs[0], Value_1=moss_amount, _use_clamp=True)
    # --- assemble colour
    col0 = nb.n("ShaderNodeMix", _data_type='RGBA', Factor=1.0, A=(0, 0, 0, 1), B=base + (1,))
    colb = nb.n("ShaderNodeVectorMath", _operation='MULTIPLY', Vector=nb.o(col0, "Result"), Vector_1=batch.outputs["Color"])
    colo = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=colb.outputs[0], Scale=objv.outputs[0])
    colbr = nb.n("ShaderNodeVectorMath", _operation='MULTIPLY', Vector=colo.outputs[0], Vector_1=brick.outputs["Color"])
    colg = nb.n("ShaderNodeVectorMath", _operation='MULTIPLY', Vector=colbr.outputs[0], Vector_1=grime.outputs["Color"])
    fine_v = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=n_fine.outputs["Factor"], Value_1=0.3, Value_2=0.85)
    colf = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=colg.outputs[0], Scale=fine_v.outputs[0])
    col_streak = nb.n("ShaderNodeMix", _data_type='RGBA', Factor=streak2.outputs[0], A=colf.outputs[0], B=(0.10, 0.09, 0.08, 1))
    col_moss = nb.n("ShaderNodeMix", _data_type='RGBA', Factor=mossf.outputs[0], A=nb.o(col_streak, "Result"), B=(0.12, 0.17, 0.05, 1))
    # --- normal: bevel for edge wear + bump from mortar and fine noise
    bevel = nb.n("ShaderNodeBevel", Radius=0.05, _samples=4)
    bumpn = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=n_fine.outputs["Factor"], Value_1=0.4, Value_2=brick.outputs["Factor"])
    bump = nb.n("ShaderNodeBump", Strength=0.35 if not trim else 0.2, Distance=0.03, Height=bumpn.outputs[0], Normal=bevel.outputs["Normal"])
    rough = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=mossf.outputs[0], Value_1=0.15, Value_2=0.78)
    bsdf = nb.n("ShaderNodeBsdfPrincipled", Base__Color=nb.o(col_moss, "Result"), Roughness=rough.outputs[0], Normal=bump.outputs["Normal"])
    bsdf.inputs["Specular IOR Level"].default_value = 0.35
    _out(nb, bsdf.outputs[0])
    return m

# --------------------------------------------------------------------------- slate / copper / lead / wood
def mat_slate(name="M_Slate", cone=False):
    m = new_material(name); nb = NB(m.node_tree)
    tc = nb.n("ShaderNodeTexCoord"); geo = nb.n("ShaderNodeNewGeometry")
    sep = nb.n("ShaderNodeSeparateXYZ", Vector=tc.outputs["Object"])
    if cone:
        # round roofs: object origin sits on the axis -> arc-length coordinate = angle * local radius
        ang = nb.n("ShaderNodeMath", _operation='ARCTAN2', Value=sep.outputs["Y"], Value_1=sep.outputs["X"])
        rad = nb.n("ShaderNodeVectorMath", _operation='LENGTH', Vector=nb.n("ShaderNodeCombineXYZ", X=sep.outputs["X"], Y=sep.outputs["Y"], Z=0.0).outputs[0])
        hc = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=ang.outputs[0], Value_1=rad.outputs["Value"])
        vec = nb.n("ShaderNodeCombineXYZ", X=hc.outputs[0], Y=sep.outputs["Z"], Z=0.0)
    else:
        # planar roofs: horizontal coordinate = position projected on the surface's horizontal tangent
        # (exact metric tile size on any slope/orientation); rows follow z
        tang = nb.n("ShaderNodeVectorMath", _operation='CROSS_PRODUCT', Vector=geo.outputs["True Normal"], Vector_1=(0.0, 0.0, 1.0))
        tangn = nb.n("ShaderNodeVectorMath", _operation='NORMALIZE', Vector=tang.outputs[0])
        hcm = nb.n("ShaderNodeVectorMath", _operation='DOT_PRODUCT', Vector=tc.outputs["Object"], Vector_1=tangn.outputs[0])
        vec = nb.n("ShaderNodeCombineXYZ", X=hcm.outputs["Value"], Y=sep.outputs["Z"], Z=0.0)
    brick = nb.n("ShaderNodeTexBrick", Vector=vec.outputs[0], Scale=1.0, Color1=(0.13, 0.15, 0.19, 1), Color2=(0.30, 0.32, 0.36, 1),
                 Mortar=(0.05, 0.06, 0.07, 1), Mortar__Size=0.014, Mortar__Smooth=0.15, Bias=0.0, Brick__Width=0.30, Row__Height=0.19)
    brick.offset = 0.5
    n1 = nb.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=1.1, Detail=5.0, Roughness=0.55)
    lich = nb.n("ShaderNodeValToRGB", Factor=n1.outputs["Factor"])
    lich.color_ramp.elements[0].position = 0.55; lich.color_ramp.elements[0].color = (1, 1, 1, 1)
    lich.color_ramp.elements[1].position = 0.75; lich.color_ramp.elements[1].color = (1.8, 1.75, 1.5, 1)
    n2 = nb.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=14.0, Detail=4.0)
    fine = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=n2.outputs["Factor"], Value_1=0.35, Value_2=0.82)
    c1 = nb.n("ShaderNodeVectorMath", _operation='MULTIPLY', Vector=brick.outputs["Color"], Vector_1=lich.outputs["Color"])
    c2 = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=c1.outputs[0], Scale=fine.outputs[0])
    oi = nb.n("ShaderNodeObjectInfo")
    objv = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=oi.outputs["Random"], Value_1=0.25, Value_2=0.88)
    c3 = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=c2.outputs[0], Scale=objv.outputs[0])
    bh = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=n2.outputs["Factor"], Value_1=0.25, Value_2=brick.outputs["Factor"])
    bump = nb.n("ShaderNodeBump", Strength=0.5, Distance=0.02, Height=bh.outputs[0])
    tile = nb.n("ShaderNodeSeparateColor", Color=brick.outputs["Color"])
    rough0 = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=n1.outputs["Factor"], Value_1=0.25, Value_2=0.30)
    rough = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=tile.outputs["Red"], Value_1=0.9, Value_2=rough0.outputs[0], _use_clamp=True)
    bsdf = nb.n("ShaderNodeBsdfPrincipled", Base__Color=c3.outputs[0], Roughness=rough.outputs[0], Normal=bump.outputs["Normal"])
    bsdf.inputs["Specular IOR Level"].default_value = 0.6
    _out(nb, bsdf.outputs[0])
    return m

def mat_copper(name="M_Copper"):
    m = new_material(name); nb = NB(m.node_tree)
    tc = nb.n("ShaderNodeTexCoord")
    n1 = nb.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=0.9, Detail=6.0, Roughness=0.6)
    n2 = nb.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=6.0, Detail=5.0)
    smap = nb.n("ShaderNodeMapping", Vector=tc.outputs["Object"], Scale=(4.0, 4.0, 0.4))
    st = nb.n("ShaderNodeTexNoise", Vector=smap.outputs["Vector"], Scale=1.0, Detail=3.0)
    ramp = nb.n("ShaderNodeValToRGB", Factor=n1.outputs["Factor"])
    ramp.color_ramp.elements[0].position = 0.3; ramp.color_ramp.elements[0].color = (0.045, 0.12, 0.11, 1)
    ramp.color_ramp.elements[1].position = 0.7; ramp.color_ramp.elements[1].color = (0.11, 0.25, 0.22, 1)
    # bare copper showing through on edges (bevel-normal difference) and along streaks
    # bare copper shows along weathering streaks (no bevel: sharp spire ridges must not rim-light)
    stf = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=st.outputs["Factor"], Value_1=1.2, Value_2=-0.55, _use_clamp=True)
    bare = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=stf.outputs[0], Value_1=1.0, _use_clamp=True)
    col = nb.n("ShaderNodeMix", _data_type='RGBA', Factor=bare.outputs[0], A=ramp.outputs["Color"], B=(0.32, 0.17, 0.10, 1))
    fine = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=n2.outputs["Factor"], Value_1=0.3, Value_2=0.85)
    colf = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=nb.o(col, "Result"), Scale=fine.outputs[0])
    bump = nb.n("ShaderNodeBump", Strength=0.25, Distance=0.02, Height=n2.outputs["Factor"])
    metal = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=bare.outputs[0], Value_1=0.15, Value_2=0.8)
    rough = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=bare.outputs[0], Value_1=-0.1, Value_2=0.62)
    bsdf = nb.n("ShaderNodeBsdfPrincipled", Base__Color=colf.outputs[0], Metallic=metal.outputs[0], Roughness=rough.outputs[0], Normal=bump.outputs["Normal"])
    _out(nb, bsdf.outputs[0])
    return m

def mat_lead(name="M_Lead"):
    m = new_material(name); nb = NB(m.node_tree)
    tc = nb.n("ShaderNodeTexCoord")
    n = nb.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=5.0, Detail=4.0)
    v = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=n.outputs["Factor"], Value_1=0.3, Value_2=0.8)
    col = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=(0.20, 0.21, 0.24), Scale=v.outputs[0])
    bump = nb.n("ShaderNodeBump", Strength=0.2, Distance=0.01, Height=n.outputs["Factor"])
    bsdf = nb.n("ShaderNodeBsdfPrincipled", Base__Color=col.outputs[0], Metallic=0.7, Roughness=0.5, Normal=bump.outputs["Normal"])
    _out(nb, bsdf.outputs[0])
    return m

def mat_wood(name="M_Wood"):
    m = new_material(name); nb = NB(m.node_tree)
    tc = nb.n("ShaderNodeTexCoord")
    mp = nb.n("ShaderNodeMapping", Vector=tc.outputs["Object"], Scale=(1.0, 12.0, 12.0))
    w = nb.n("ShaderNodeTexWave", Vector=mp.outputs["Vector"], Scale=0.6, Distortion=3.0, Detail=3.0, _wave_type='BANDS', _bands_direction='X')
    n = nb.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=3.0, Detail=4.0)
    ramp = nb.n("ShaderNodeValToRGB", Factor=w.outputs["Factor"])
    ramp.color_ramp.elements[0].color = (0.12, 0.08, 0.05, 1); ramp.color_ramp.elements[1].color = (0.28, 0.19, 0.11, 1)
    v = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=n.outputs["Factor"], Value_1=0.4, Value_2=0.75)
    col = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=ramp.outputs["Color"], Scale=v.outputs[0])
    bump = nb.n("ShaderNodeBump", Strength=0.3, Distance=0.01, Height=w.outputs["Factor"])
    bsdf = nb.n("ShaderNodeBsdfPrincipled", Base__Color=col.outputs[0], Roughness=0.7, Normal=bump.outputs["Normal"])
    _out(nb, bsdf.outputs[0])
    return m

def mat_cobble(name="M_Cobble"):
    m = new_material(name); nb = NB(m.node_tree)
    geo = nb.n("ShaderNodeNewGeometry")
    vor = nb.n("ShaderNodeTexVoronoi", Vector=geo.outputs["Position"], Scale=2.6, _feature='DISTANCE_TO_EDGE', Randomness=0.85)
    vc = nb.n("ShaderNodeTexVoronoi", Vector=geo.outputs["Position"], Scale=2.6, _feature='F1', Randomness=0.85)
    joint = nb.n("ShaderNodeMapRange", Value=vor.outputs["Distance"], From__Min=0.0, From__Max=0.06, To__Min=0.0, To__Max=1.0)
    n = nb.n("ShaderNodeTexNoise", Vector=geo.outputs["Position"], Scale=8.0, Detail=4.0)
    cellv = nb.n("ShaderNodeValToRGB", Factor=vc.outputs["Color"])
    cellv.color_ramp.elements[0].color = (0.30, 0.28, 0.25, 1); cellv.color_ramp.elements[1].color = (0.46, 0.43, 0.38, 1)
    fine = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=n.outputs["Factor"], Value_1=0.35, Value_2=0.8)
    c1 = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=cellv.outputs["Color"], Scale=fine.outputs[0])
    col = nb.n("ShaderNodeMix", _data_type='RGBA', Factor=joint.outputs["Result"], A=(0.08, 0.075, 0.07, 1), B=c1.outputs[0])
    bh = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=n.outputs["Factor"], Value_1=0.25, Value_2=joint.outputs["Result"])
    bump = nb.n("ShaderNodeBump", Strength=0.6, Distance=0.04, Height=bh.outputs[0])
    bsdf = nb.n("ShaderNodeBsdfPrincipled", Base__Color=nb.o(col, "Result"), Roughness=0.7, Normal=bump.outputs["Normal"])
    _out(nb, bsdf.outputs[0])
    return m

# --------------------------------------------------------------------------- glass
def mat_glass(name="M_Glass", glow_scale=2.8):
    m = new_material(name); nb = NB(m.node_tree)
    oi = nb.n("ShaderNodeObjectInfo")
    sep = nb.n("ShaderNodeSeparateColor", Color=oi.outputs["Color"])
    tc = nb.n("ShaderNodeTexCoord")
    # interior variation across the pane (curtains / rooms)
    n = nb.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=0.9, Detail=2.0)
    nv = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=n.outputs["Factor"], Value_1=0.7, Value_2=0.55)
    gs = nb.n("ShaderNodeValue", "GlowScale"); gs.outputs[0].default_value = glow_scale
    s1 = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=sep.outputs["Red"], Value_1=gs.outputs[0])
    strength = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=s1.outputs[0], Value_1=nv.outputs[0])
    warm = nb.n("ShaderNodeMix", _data_type='RGBA', Factor=sep.outputs["Green"], A=(1.0, 0.64, 0.32, 1), B=(1.0, 0.44, 0.15, 1))
    em = nb.n("ShaderNodeEmission", Color=nb.o(warm, "Result"), Strength=strength.outputs[0])
    # dark reflective pane when unlit
    fres = nb.n("ShaderNodeFresnel", IOR=1.5)
    gl = nb.n("ShaderNodeBsdfGlossy", Color=(0.9, 0.9, 0.95, 1), Roughness=0.08)
    dark = nb.n("ShaderNodeBsdfDiffuse", Color=(0.02, 0.025, 0.03, 1))
    pane = nb.n("ShaderNodeMixShader", Factor=fres.outputs[0], **{"1": dark.outputs[0], "2": gl.outputs[0]})
    lit = nb.n("ShaderNodeMath", _operation='GREATER_THAN', Value=sep.outputs["Red"], Value_1=0.02)
    mix = nb.n("ShaderNodeMixShader", Factor=lit.outputs[0], **{"1": pane.outputs[0], "2": em.outputs[0]})
    _out(nb, mix.outputs[0])
    return m

def mat_clockface(name="M_ClockFace"):
    m = new_material(name); nb = NB(m.node_tree)
    em = nb.n("ShaderNodeEmission", Color=(1.0, 0.85, 0.6, 1), Strength=0.12)
    df = nb.n("ShaderNodeBsdfDiffuse", Color=(0.8, 0.72, 0.55, 1))
    mix = nb.n("ShaderNodeAddShader", **{"0": df.outputs[0], "1": em.outputs[0]})
    _out(nb, mix.outputs[0])
    return m

def mat_greenhouse_glass(name="M_GreenhouseGlass"):
    m = new_material(name); nb = NB(m.node_tree)
    fres = nb.n("ShaderNodeFresnel", IOR=1.5)
    gl = nb.n("ShaderNodeBsdfGlossy", Color=(1, 1, 1, 1), Roughness=0.05)
    tr = nb.n("ShaderNodeBsdfTransparent", Color=(0.55, 0.7, 0.6, 1))
    em = nb.n("ShaderNodeEmission", Color=(0.55, 0.9, 0.5, 1), Strength=0.03)
    inner = nb.n("ShaderNodeAddShader", **{"0": tr.outputs[0], "1": em.outputs[0]})
    mix = nb.n("ShaderNodeMixShader", Factor=fres.outputs[0], **{"1": inner.outputs[0], "2": gl.outputs[0]})
    _out(nb, mix.outputs[0])
    try:
        m.blend_method = 'BLEND'
    except Exception:
        pass
    return m

# --------------------------------------------------------------------------- terrain
def mat_terrain(name="M_Terrain", far=False):
    m = new_material(name); nb = NB(m.node_tree)
    tc = nb.n("ShaderNodeTexCoord"); geo = nb.n("ShaderNodeNewGeometry")
    pos = nb.n("ShaderNodeSeparateXYZ", Vector=geo.outputs["Position"])
    nrm = nb.n("ShaderNodeSeparateXYZ", Vector=geo.outputs["Normal"])
    a_rock = nb.n("ShaderNodeAttribute", _attribute_name="rock")
    a_path = nb.n("ShaderNodeAttribute", _attribute_name="path")
    a_wet = nb.n("ShaderNodeAttribute", _attribute_name="wet")
    a_forest = nb.n("ShaderNodeAttribute", _attribute_name="forest")
    # --- rock: horizontal bedding (two frequencies, warped), sparse vertical joints, granular surface
    warp = nb.n("ShaderNodeTexNoise", Vector=geo.outputs["Position"], Scale=0.05, Detail=3.0)
    wz = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=warp.outputs["Factor"], Value_1=6.0, Value_2=pos.outputs["Z"])
    band = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=wz.outputs[0], Value_1=0.22)
    bandf = nb.n("ShaderNodeMath", _operation='FRACT', Value=band.outputs[0])
    bandr = nb.n("ShaderNodeValToRGB", Factor=bandf.outputs[0])
    bandr.color_ramp.elements[0].color = (0.17, 0.155, 0.14, 1); bandr.color_ramp.elements[0].position = 0.0
    e = bandr.color_ramp.elements.new(0.45); e.color = (0.25, 0.225, 0.19, 1)
    e = bandr.color_ramp.elements.new(0.9); e.color = (0.21, 0.195, 0.17, 1)
    bandr.color_ramp.elements[-1].color = (0.12, 0.11, 0.10, 1)
    band2 = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=wz.outputs[0], Value_1=1.1)
    band2f = nb.n("ShaderNodeMath", _operation='FRACT', Value=band2.outputs[0])
    band2v = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=band2f.outputs[0], Value_1=0.14, Value_2=0.9)
    # vertical joints: tall thin voronoi cells -> edges run mostly vertically
    jmap = nb.n("ShaderNodeMapping", Vector=geo.outputs["Position"], Scale=(0.16, 0.16, 0.03))
    jv = nb.n("ShaderNodeTexVoronoi", Vector=jmap.outputs["Vector"], Scale=1.0, _feature='DISTANCE_TO_EDGE', Randomness=1.0)
    joint = nb.n("ShaderNodeMapRange", Value=jv.outputs["Distance"], From__Min=0.0, From__Max=0.05, To__Min=0.62, To__Max=1.0)
    # granular surface + slight per-block tone
    rn = nb.n("ShaderNodeTexNoise", Vector=geo.outputs["Position"], Scale=2.8, Detail=6.0, Roughness=0.6)
    rv = nb.n("ShaderNodeTexVoronoi", Vector=jmap.outputs["Vector"], Scale=1.0, _feature='F1')
    rvr = nb.n("ShaderNodeValToRGB", Factor=rv.outputs["Color"])
    rvr.color_ramp.elements[0].color = (0.9, 0.9, 0.9, 1); rvr.color_ramp.elements[1].color = (1.08, 1.06, 1.04, 1)
    rfine = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=rn.outputs["Factor"], Value_1=0.45, Value_2=0.75)
    rock1 = nb.n("ShaderNodeVectorMath", _operation='MULTIPLY', Vector=bandr.outputs["Color"], Vector_1=rvr.outputs["Color"])
    rock2 = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=rock1.outputs[0], Scale=rfine.outputs[0])
    rock3 = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=rock2.outputs[0], Scale=joint.outputs["Result"])
    rock4 = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=rock3.outputs[0], Scale=band2v.outputs[0])
    if not far:
        aor = nb.n("ShaderNodeAmbientOcclusion", Distance=4.0, _samples=4, _only_local=True)
        aov = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=aor.outputs["AO"], Value_1=0.55, Value_2=0.45)
        rock = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=rock4.outputs[0], Scale=aov.outputs[0])
    else:
        rock = rock4
    # lichen / moss on rock: upward faces low down and near water
    mossn = nb.n("ShaderNodeTexNoise", Vector=geo.outputs["Position"], Scale=0.25, Detail=5.0)
    mossr = nb.n("ShaderNodeValToRGB", Factor=mossn.outputs["Factor"])
    mossr.color_ramp.elements[0].position = 0.45; mossr.color_ramp.elements[1].position = 0.62
    upf = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=nrm.outputs["Z"], Value_1=1.2, Value_2=-0.2, _use_clamp=True)
    mossf = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=mossr.outputs["Color"], Value_1=upf.outputs[0])
    rock_m = nb.n("ShaderNodeMix", _data_type='RGBA', Factor=mossf.outputs[0], A=rock.outputs[0], B=(0.10, 0.15, 0.05, 1))
    # --- moor / grass: heather greens & browns
    gn = nb.n("ShaderNodeTexNoise", Vector=geo.outputs["Position"], Scale=0.08, Detail=5.0, Roughness=0.6)
    gr = nb.n("ShaderNodeValToRGB", Factor=gn.outputs["Factor"])
    gr.color_ramp.elements[0].position = 0.35; gr.color_ramp.elements[0].color = (0.065, 0.09, 0.035, 1)
    gr.color_ramp.elements[1].position = 0.7; gr.color_ramp.elements[1].color = (0.20, 0.17, 0.08, 1)
    e = gr.color_ramp.elements.new(0.52); e.color = (0.10, 0.13, 0.045, 1)
    gfine = nb.n("ShaderNodeTexNoise", Vector=geo.outputs["Position"], Scale=2.5, Detail=5.0)
    gfv = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=gfine.outputs["Factor"], Value_1=0.5, Value_2=0.7)
    grass = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=gr.outputs["Color"], Scale=gfv.outputs[0])
    # high altitude: grey scree and faint snow
    high = nb.n("ShaderNodeMapRange", Value=pos.outputs["Z"], From__Min=260.0, From__Max=520.0, To__Min=0.0, To__Max=1.0)
    scree = nb.n("ShaderNodeMix", _data_type='RGBA', Factor=high.outputs["Result"], A=grass.outputs[0], B=(0.22, 0.215, 0.20, 1))
    snowh = nb.n("ShaderNodeMapRange", Value=pos.outputs["Z"], From__Min=850.0, From__Max=1250.0, To__Min=0.0, To__Max=1.0)
    snowf = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=snowh.outputs["Result"], Value_1=upf.outputs[0])
    ground = nb.n("ShaderNodeMix", _data_type='RGBA', Factor=snowf.outputs[0], A=nb.o(scree, "Result"), B=(0.75, 0.78, 0.85, 1))
    # --- mix rock vs ground by attribute + local slope
    slope = nb.n("ShaderNodeMapRange", Value=nrm.outputs["Z"], From__Min=0.72, From__Max=0.5, To__Min=0.0, To__Max=1.0)
    rockf0 = nb.n("ShaderNodeMath", _operation='MAXIMUM', Value=a_rock.outputs["Factor"], Value_1=slope.outputs["Result"])
    rockn = nb.n("ShaderNodeTexNoise", Vector=geo.outputs["Position"], Scale=0.12, Detail=4.0)
    rockf1 = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=rockn.outputs["Factor"], Value_1=0.5, Value_2=rockf0.outputs[0])
    rockf = nb.n("ShaderNodeMath", _operation='SUBTRACT', Value=rockf1.outputs[0], Value_1=0.25, _use_clamp=True)
    rockf2 = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=rockf.outputs[0], Value_1=1.6, _use_clamp=True)
    base = nb.n("ShaderNodeMix", _data_type='RGBA', Factor=rockf2.outputs[0], A=nb.o(ground, "Result"), B=nb.o(rock_m, "Result"))
    # --- path dirt
    pathc = nb.n("ShaderNodeMix", _data_type='RGBA', Factor=a_path.outputs["Factor"], A=nb.o(base, "Result"), B=(0.30, 0.26, 0.20, 1))
    # --- wet darkening near the water line
    wetf = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=a_wet.outputs["Factor"], Value_1=0.55)
    wet = nb.n("ShaderNodeMix", _data_type='RGBA', Factor=wetf.outputs[0], A=nb.o(pathc, "Result"), B=(0.05, 0.05, 0.05, 1))
    # --- forest floor darkening under trees (attribute)
    ff = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=a_forest.outputs["Factor"], Value_1=0.5)
    col = nb.n("ShaderNodeMix", _data_type='RGBA', Factor=ff.outputs[0], A=nb.o(wet, "Result"), B=(0.06, 0.07, 0.04, 1))
    # --- bump: strata ledges + rock noise + fine grass noise
    bh1 = nb.n("ShaderNodeMath", _operation='MULTIPLY', Value=bandf.outputs[0], Value_1=rockf2.outputs[0])
    bh2 = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=rn.outputs["Factor"], Value_1=0.5, Value_2=bh1.outputs[0])
    bh2b = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=joint.outputs["Result"], Value_1=0.5, Value_2=bh2.outputs[0])
    bh3 = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=band2f.outputs[0], Value_1=0.3, Value_2=bh2b.outputs[0])
    bh = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=gfine.outputs["Factor"], Value_1=0.15, Value_2=bh3.outputs[0])
    if far:
        # mid-scale ruggedness for the mountains (features of 25-120 m)
        mn1 = nb.n("ShaderNodeTexNoise", Vector=geo.outputs["Position"], Scale=0.009, Detail=5.0, Roughness=0.65)
        mn2 = nb.n("ShaderNodeTexVoronoi", Vector=geo.outputs["Position"], Scale=0.03, _feature='DISTANCE_TO_EDGE')
        mh = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=mn2.outputs["Distance"], Value_1=1.5, Value_2=mn1.outputs["Factor"])
        bh = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=mh.outputs[0], Value_1=2.0, Value_2=bh.outputs[0])
    bump = nb.n("ShaderNodeBump", Strength=0.5 if far else 0.6, Distance=2.5 if far else 0.35, Height=bh.outputs[0])
    rough = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=wetf.outputs[0], Value_1=-0.5, Value_2=0.9)
    bsdf = nb.n("ShaderNodeBsdfPrincipled", Base__Color=nb.o(col, "Result"), Roughness=rough.outputs[0], Normal=bump.outputs["Normal"])
    bsdf.inputs["Specular IOR Level"].default_value = 0.3
    _out(nb, bsdf.outputs[0])
    return m

# --------------------------------------------------------------------------- water
def mat_water(name="M_Water"):
    m = new_material(name); nb = NB(m.node_tree)
    geo = nb.n("ShaderNodeNewGeometry")
    # ripples: two distorted noises + a directional wave for wind streaks
    mp1 = nb.n("ShaderNodeMapping", Vector=geo.outputs["Position"], Scale=(1.0, 1.4, 1.0))
    n1 = nb.n("ShaderNodeTexNoise", Vector=mp1.outputs["Vector"], Scale=0.45, Detail=6.0, Roughness=0.55, Distortion=0.4)
    n2 = nb.n("ShaderNodeTexNoise", Vector=geo.outputs["Position"], Scale=2.2, Detail=4.0, Roughness=0.5)
    mp2 = nb.n("ShaderNodeMapping", Vector=geo.outputs["Position"], Rotation=(0, 0, 0.5))
    wv = nb.n("ShaderNodeTexWave", Vector=mp2.outputs["Vector"], Scale=0.08, Distortion=6.0, Detail=3.0, Detail__Scale=2.0, _wave_type='BANDS')
    h1 = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=n2.outputs["Factor"], Value_1=0.35, Value_2=n1.outputs["Factor"])
    h = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=wv.outputs["Factor"], Value_1=0.25, Value_2=h1.outputs[0])
    bump = nb.n("ShaderNodeBump", Strength=0.35, Distance=0.05, Height=h.outputs[0])
    bsdf = nb.n("ShaderNodeBsdfPrincipled", Base__Color=(0.010, 0.020, 0.025, 1), Roughness=0.07, IOR=1.333, Normal=bump.outputs["Normal"])
    bsdf.inputs["Transmission Weight"].default_value = 1.0
    bsdf.inputs["Specular IOR Level"].default_value = 0.5
    vol = nb.n("ShaderNodeVolumeAbsorption", Color=(0.12, 0.22, 0.20, 1), Density=0.35)
    _out(nb, bsdf.outputs[0], volume=vol.outputs[0])
    return m

# --------------------------------------------------------------------------- vegetation
def mat_conifer(name="M_Conifer"):
    m = new_material(name); nb = NB(m.node_tree)
    oi = nb.n("ShaderNodeObjectInfo")
    tc = nb.n("ShaderNodeTexCoord")
    n = nb.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=3.0, Detail=4.0)
    ramp = nb.n("ShaderNodeValToRGB", Factor=oi.outputs["Random"])
    ramp.color_ramp.elements[0].color = (0.020, 0.042, 0.018, 1); ramp.color_ramp.elements[1].color = (0.040, 0.062, 0.022, 1)
    v = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=n.outputs["Factor"], Value_1=0.6, Value_2=0.6)
    col = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=ramp.outputs["Color"], Scale=v.outputs[0])
    bump = nb.n("ShaderNodeBump", Strength=0.6, Distance=0.1, Height=n.outputs["Factor"])
    bsdf = nb.n("ShaderNodeBsdfPrincipled", Base__Color=col.outputs[0], Roughness=0.85, Normal=bump.outputs["Normal"])
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    tl = nb.n("ShaderNodeBsdfTranslucent", Color=(0.07, 0.12, 0.04, 1))
    mix = nb.n("ShaderNodeMixShader", Factor=0.18, **{"1": bsdf.outputs[0], "2": tl.outputs[0]})
    _out(nb, mix.outputs[0])
    return m

def mat_trunk(name="M_Trunk"):
    m = new_material(name); nb = NB(m.node_tree)
    tc = nb.n("ShaderNodeTexCoord")
    n = nb.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=6.0, Detail=4.0)
    v = nb.n("ShaderNodeMath", _operation='MULTIPLY_ADD', Value=n.outputs["Factor"], Value_1=0.5, Value_2=0.6)
    col = nb.n("ShaderNodeVectorMath", _operation='SCALE', Vector=(0.10, 0.07, 0.05), Scale=v.outputs[0])
    bsdf = nb.n("ShaderNodeBsdfPrincipled", Base__Color=col.outputs[0], Roughness=0.9)
    _out(nb, bsdf.outputs[0])
    return m

def mat_lantern_glass(name="M_LanternGlass"):
    m = new_material(name); nb = NB(m.node_tree)
    em = nb.n("ShaderNodeEmission", Color=(1.0, 0.62, 0.28, 1), Strength=40.0)
    _out(nb, em.outputs[0])
    return m

# --------------------------------------------------------------------------- build all
mat_stone("M_Stone")
mat_stone("M_StoneTrim", base=(0.50, 0.46, 0.40), trim=True, moss_amount=0.4)
mat_slate("M_Slate")
mat_slate("M_SlateCone", cone=True)
mat_copper("M_Copper")
mat_lead("M_Lead")
mat_wood("M_Wood")
mat_glass("M_Glass")
mat_clockface("M_ClockFace")
mat_greenhouse_glass("M_GreenhouseGlass")
mat_terrain("M_Terrain")
mat_terrain("M_TerrainFar", far=True)
mat_water("M_Water")
mat_conifer("M_Conifer")
mat_trunk("M_Trunk")
mat_lantern_glass("M_LanternGlass")
mat_cobble("M_Cobble")
result = {"materials": sorted(m.name for m in bpy.data.materials)}
