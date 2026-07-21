import bpy, math, random
from mathutils import Vector, Matrix, noise
from math import sin, cos, pi

random.seed(1408)

WS = "/home/morpheus/Documents/Projects/Blender/Kimi-K3"

# ---------------------------------------------------------------- collections
def get_col(name, parent_name=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        if parent_name:
            bpy.data.collections[parent_name].children.link(c)
        else:
            bpy.context.scene.collection.children.link(c)
    return c

def move_to_col(obj, col):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)

# ---------------------------------------------------------------- node helpers
def _nt(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (800, 0)
    return nt, out

def _noise(nt, scale, detail, rough=0.65, loc=(0,0)):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    n.location = loc
    return n

def _ramp(nt, stops, loc=(0,0)):
    r = nt.nodes.new("ShaderNodeValToRGB")
    cr = r.color_ramp
    while len(cr.elements) > 2:
        cr.elements.remove(cr.elements[-1])
    cr.elements[0].position, cr.elements[0].color = stops[0]
    cr.elements[1].position, cr.elements[1].color = stops[-1]
    for pos, col in stops[1:-1]:
        e = cr.elements.new(pos)
        e.color = col
    r.location = loc
    return r

def _mix(nt, t, a, b, loc=(0,0)):
    m = nt.nodes.new("ShaderNodeMixRGB")
    m.blend_type = t
    m.inputs[1].default_value = a
    m.inputs[2].default_value = b
    m.location = loc
    return m

def _texcoord(nt, loc=(0,0)):
    t = nt.nodes.new("ShaderNodeTexCoord")
    t.location = loc
    return t

MATS = {}

def mat_stone():
    if "Stone" in MATS: return MATS["Stone"]
    m = bpy.data.materials.new("Stone"); MATS["Stone"] = m
    nt, out = _nt(m)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.location = (520, 60)
    bs.inputs["Roughness"].default_value = 0.82
    tc = _texcoord(nt, (-1200, 0))
    n1 = _noise(nt, 0.35, 3.0, loc=(-1000, 250))   # batch color patches
    n2 = _noise(nt, 4.0, 5.0, loc=(-1000, -50))    # mid variation
    n3 = _noise(nt, 45.0, 2.5, loc=(-1000, -350))  # fine grain
    r1 = _ramp(nt, [(0.2,(0.26,0.225,0.185,1)),(0.5,(0.37,0.32,0.26,1)),(0.8,(0.46,0.40,0.33,1))], (-720, 250))
    r2 = _ramp(nt, [(0.25,(0.75,0.73,0.70,1)),(0.75,(1.05,1.02,0.98,1))], (-720, -50))
    mixc = _mix(nt, 'MULTIPLY', (0,0,0,1), (0,0,0,1), (-420, 200))
    bump = nt.nodes.new("ShaderNodeBump"); bump.location = (280, -220)
    bump.inputs["Strength"].default_value = 0.45; bump.inputs["Distance"].default_value = 0.35
    nt.links.new(tc.outputs["Generated"], n1.inputs["Vector"])
    nt.links.new(tc.outputs["Generated"], n2.inputs["Vector"])
    nt.links.new(tc.outputs["Generated"], n3.inputs["Vector"])
    nt.links.new(n1.outputs["Fac"], r1.inputs["Fac"])
    nt.links.new(n2.outputs["Fac"], r2.inputs["Fac"])
    nt.links.new(r1.outputs["Color"], mixc.inputs[1])
    nt.links.new(r2.outputs["Color"], mixc.inputs[2])
    nt.links.new(mixc.outputs["Color"], bs.inputs["Base Color"])
    nt.links.new(n3.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(n2.outputs["Fac"], bump.inputs["Height"]) if False else None
    nt.links.new(bump.outputs["Normal"], bs.inputs["Normal"])
    nt.links.new(bs.outputs[0], out.inputs["Surface"])
    return m

def mat_stone_dark():
    if "StoneDark" in MATS: return MATS["StoneDark"]
    m = bpy.data.materials.new("StoneDark"); MATS["StoneDark"] = m
    nt, out = _nt(m)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.location = (520, 60)
    bs.inputs["Roughness"].default_value = 0.9
    tc = _texcoord(nt, (-1100, 0))
    n1 = _noise(nt, 0.6, 4.0, loc=(-950, 150))
    n3 = _noise(nt, 30.0, 3.0, loc=(-950, -200))
    r1 = _ramp(nt, [(0.25,(0.10,0.095,0.085,1)),(0.75,(0.21,0.19,0.165,1))], (-650, 150))
    bump = nt.nodes.new("ShaderNodeBump"); bump.location = (280, -200)
    bump.inputs["Strength"].default_value = 0.6; bump.inputs["Distance"].default_value = 0.4
    nt.links.new(tc.outputs["Generated"], n1.inputs["Vector"])
    nt.links.new(tc.outputs["Generated"], n3.inputs["Vector"])
    nt.links.new(n1.outputs["Fac"], r1.inputs["Fac"])
    nt.links.new(r1.outputs["Color"], bs.inputs["Base Color"])
    nt.links.new(n3.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bs.inputs["Normal"])
    nt.links.new(bs.outputs[0], out.inputs["Surface"])
    return m

def mat_slate():
    if "Slate" in MATS: return MATS["Slate"]
    m = bpy.data.materials.new("Slate"); MATS["Slate"] = m
    nt, out = _nt(m)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.location = (560, 60)
    bs.inputs["Roughness"].default_value = 0.55
    tc = _texcoord(nt, (-1300, 0))
    brick = nt.nodes.new("ShaderNodeTexBrick"); brick.location = (-1050, 120)
    brick.offset = 0.5; brick.offset_frequency = 2; brick.squash = 1.6; brick.squash_frequency = 2
    brick.inputs["Color1"].default_value = (0.055,0.068,0.09,1)
    brick.inputs["Color2"].default_value = (0.075,0.09,0.115,1)
    brick.inputs["Mortar"].default_value = (0.05,0.06,0.08,1)
    brick.inputs["Scale"].default_value = 45.0
    brick.inputs["Mortar Size"].default_value = 0.025
    brick.inputs["Bias"].default_value = 0.3
    nz = _noise(nt, 3.0, 4.0, loc=(-1050, -250))
    r = _ramp(nt, [(0.3,(0.7,0.75,0.85,1)),(0.7,(1.1,1.12,1.2,1))], (-650, -120))
    mul = _mix(nt, 'MULTIPLY', (0,0,0,1),(0,0,0,1), (-380, 120))
    bump = nt.nodes.new("ShaderNodeBump"); bump.location = (300, -200)
    bump.inputs["Strength"].default_value = 0.3; bump.inputs["Distance"].default_value = 0.1
    nt.links.new(tc.outputs["Generated"], brick.inputs["Vector"])
    nt.links.new(tc.outputs["Generated"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], r.inputs["Fac"])
    nt.links.new(brick.outputs["Color"], mul.inputs[1])
    nt.links.new(r.outputs["Color"], mul.inputs[2])
    nt.links.new(mul.outputs["Color"], bs.inputs["Base Color"])
    nt.links.new(brick.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bs.inputs["Normal"])
    nt.links.new(bs.outputs[0], out.inputs["Surface"])
    return m

def mat_verdigris():
    if "Verdigris" in MATS: return MATS["Verdigris"]
    m = bpy.data.materials.new("Verdigris"); MATS["Verdigris"] = m
    nt, out = _nt(m)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.location = (520, 60)
    bs.inputs["Roughness"].default_value = 0.45; bs.inputs["Metallic"].default_value = 0.35
    tc = _texcoord(nt, (-1000,0))
    n1 = _noise(nt, 2.5, 5.0, loc=(-850, 100))
    r1 = _ramp(nt, [(0.3,(0.05,0.16,0.14,1)),(0.6,(0.12,0.32,0.27,1)),(0.85,(0.20,0.42,0.34,1))], (-550, 100))
    bump = nt.nodes.new("ShaderNodeBump"); bump.location=(280,-200)
    bump.inputs["Strength"].default_value=0.3; bump.inputs["Distance"].default_value=0.2
    nt.links.new(tc.outputs["Generated"], n1.inputs["Vector"])
    nt.links.new(n1.outputs["Fac"], r1.inputs["Fac"])
    nt.links.new(r1.outputs["Color"], bs.inputs["Base Color"])
    nt.links.new(n1.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bs.inputs["Normal"])
    nt.links.new(bs.outputs[0], out.inputs["Surface"])
    return m

def mat_glass(name, warmth, strength):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); MATS[name] = m
    nt, out = _nt(m)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.location = (520, 60)
    bs.inputs["Roughness"].default_value = 0.3
    col = (1.0, 0.55*warmth + 0.12, 0.18*warmth + 0.02, 1.0)
    bs.inputs["Emission Color"].default_value = col
    bs.inputs["Emission Strength"].default_value = strength
    bs.inputs["Base Color"].default_value = (0.02,0.02,0.025,1)
    # mullion grid: wave X * wave Y mask dims emission at bars
    tc = _texcoord(nt, (-1300, 0))
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); sep.location = (-1100, 0)
    w1 = nt.nodes.new("ShaderNodeTexWave"); w1.wave_type='BANDS'; w1.bands_direction='X'; w1.location=(-1050, 200)
    w1.inputs["Scale"].default_value=9.0; w1.inputs["Distortion"].default_value=0.0; w1.inputs["Detail"].default_value=1.0
    w2 = nt.nodes.new("ShaderNodeTexWave"); w2.wave_type='BANDS'; w2.bands_direction='Y'; w2.location=(-1050, -100)
    w2.inputs["Scale"].default_value=14.0; w2.inputs["Distortion"].default_value=0.0
    r1 = _ramp(nt, [(0.06,(0,0,0,1)),(0.16,(1,1,1,1))], (-780, 200))
    r2 = _ramp(nt, [(0.05,(0,0,0,1)),(0.14,(1,1,1,1))], (-780, -100))
    mul = _mix(nt, 'MULTIPLY', (1,1,1,1),(1,1,1,1), (-520, 100))
    ms = nt.nodes.new("ShaderNodeMath"); ms.operation='MULTIPLY'; ms.location=(-250, 250)
    ms.inputs[1].default_value = strength
    nt.links.new(tc.outputs["Generated"], w1.inputs["Vector"])
    nt.links.new(tc.outputs["Generated"], w2.inputs["Vector"])
    nt.links.new(w1.outputs["Color"], r1.inputs["Fac"])
    nt.links.new(w2.outputs["Color"], r2.inputs["Fac"])
    nt.links.new(r1.outputs["Color"], mul.inputs[1])
    nt.links.new(r2.outputs["Color"], mul.inputs[2])
    nt.links.new(mul.outputs["Color"], ms.inputs[0])
    nt.links.new(ms.outputs[0], bs.inputs["Emission Strength"])
    nt.links.new(bs.outputs[0], out.inputs["Surface"])
    return m

def mat_glass_dark():
    if "GlassDark" in MATS: return MATS["GlassDark"]
    m = bpy.data.materials.new("GlassDark"); MATS["GlassDark"] = m
    nt, out = _nt(m)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.location=(520,60)
    bs.inputs["Roughness"].default_value = 0.12
    bs.inputs["Base Color"].default_value = (0.008,0.012,0.02,1)
    bs.inputs["Metallic"].default_value = 0.15
    tc=_texcoord(nt,(-1200,0))
    w1 = nt.nodes.new("ShaderNodeTexWave"); w1.wave_type='BANDS'; w1.bands_direction='X'; w1.location=(-1000,150)
    w1.inputs["Scale"].default_value=9.0
    w2 = nt.nodes.new("ShaderNodeTexWave"); w2.wave_type='BANDS'; w2.bands_direction='Y'; w2.location=(-1000,-100)
    w2.inputs["Scale"].default_value=14.0
    r1=_ramp(nt,[(0.07,(0.35,0.35,0.35,1)),(0.16,(0.02,0.02,0.02,1))],(-700,150))
    r2=_ramp(nt,[(0.06,(1,1,1,1)),(0.15,(0.02,0.02,0.02,1))],(-700,-100))
    mul=_mix(nt,'MULTIPLY',(0,0,0,1),(0,0,0,1),(-420,50))
    nt.links.new(tc.outputs["Generated"], w1.inputs["Vector"]); nt.links.new(tc.outputs["Generated"], w2.inputs["Vector"])
    nt.links.new(w1.outputs["Color"], r1.inputs["Fac"]); nt.links.new(w2.outputs["Color"], r2.inputs["Fac"])
    nt.links.new(r1.outputs["Color"], mul.inputs[1]); nt.links.new(r2.outputs["Color"], mul.inputs[2])
    nt.links.new(mul.outputs["Color"], bs.inputs["Base Color"])
    nt.links.new(bs.outputs[0], out.inputs["Surface"])
    return m

def mat_water():
    if "Water" in MATS: return MATS["Water"]
    m = bpy.data.materials.new("Water"); MATS["Water"] = m
    nt, out = _nt(m)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.location=(520,80)
    bs.inputs["Roughness"].default_value = 0.04
    bs.inputs["Base Color"].default_value = (0.004,0.010,0.016,1)
    bs.inputs["Metallic"].default_value = 0.0
    bs.inputs["Coat Weight"].default_value = 0.4
    bs.inputs["Coat Roughness"].default_value = 0.05
    tc=_texcoord(nt,(-1200,0))
    n1=_noise(nt, 1.2, 6.0, loc=(-1000,-100)); n1.noise_dimensions='4D'
    n1.inputs["W"].default_value=0.35
    n2=_noise(nt, 8.0, 3.0, loc=(-1000,-350))
    bump=nt.nodes.new("ShaderNodeBump"); bump.location=(250,-220)
    bump.inputs["Strength"].default_value=0.22; bump.inputs["Distance"].default_value=0.55
    nt.links.new(tc.outputs["Generated"], n1.inputs["Vector"]); nt.links.new(tc.outputs["Generated"], n2.inputs["Vector"])
    nt.links.new(n1.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bs.inputs["Normal"])
    nt.links.new(bs.outputs[0], out.inputs["Surface"])
    return m

def mat_rock():
    if "Rock" in MATS: return MATS["Rock"]
    m = bpy.data.materials.new("Rock"); MATS["Rock"] = m
    nt, out = _nt(m)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.location=(560,60)
    bs.inputs["Roughness"].default_value = 0.92
    tc=_texcoord(nt,(-1500,0))
    wave=nt.nodes.new("ShaderNodeTexWave"); wave.wave_type='BANDS'; wave.bands_direction='Z'; wave.location=(-1250,300)
    wave.inputs["Scale"].default_value=0.35; wave.inputs["Distortion"].default_value=3.5; wave.inputs["Detail"].default_value=5.0; wave.inputs["Detail Scale"].default_value=2.5
    n1=_noise(nt, 0.02, 5.0, loc=(-1250, 0))
    n2=_noise(nt, 0.5, 4.0, loc=(-1250, -280))
    n3=_noise(nt, 5.0, 3.0, loc=(-1250, -520))
    r1=_ramp(nt,[(0.2,(0.09,0.082,0.072,1)),(0.45,(0.17,0.155,0.135,1)),(0.7,(0.24,0.215,0.185,1)),(0.9,(0.14,0.13,0.11,1))],(-800,250))
    r2=_ramp(nt,[(0.3,(0.7,0.68,0.65,1)),(0.7,(1.15,1.12,1.08,1))],(-800,-30))
    mixm=_mix(nt,'MULTIPLY',(0,0,0,1),(0,0,0,1),(-480,150))
    mixb=_mix(nt,'MULTIPLY',(1,1,1,1),(1,1,1,1),(-480,-320))
    bump=nt.nodes.new("ShaderNodeBump"); bump.location=(300,-220)
    bump.inputs["Strength"].default_value=1.6; bump.inputs["Distance"].default_value=0.35
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], n2.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], n3.inputs["Vector"])
    nt.links.new(wave.outputs["Color"], r1.inputs["Fac"])
    nt.links.new(n1.outputs["Fac"], r2.inputs["Fac"])
    nt.links.new(r1.outputs["Color"], mixm.inputs[1])
    nt.links.new(r2.outputs["Color"], mixm.inputs[2])
    nt.links.new(mixm.outputs["Color"], bs.inputs["Base Color"])
    nt.links.new(n2.outputs["Fac"], mixb.inputs[1])
    nt.links.new(n3.outputs["Fac"], mixb.inputs[2])
    nt.links.new(mixb.outputs["Color"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bs.inputs["Normal"])
    nt.links.new(bs.outputs[0], out.inputs["Surface"])
    return m

def mat_ground():
    if "Ground" in MATS: return MATS["Ground"]
    m = bpy.data.materials.new("Ground"); MATS["Ground"] = m
    nt, out = _nt(m)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.location=(620,60)
    bs.inputs["Roughness"].default_value = 0.95
    tc=_texcoord(nt,(-1400,0))
    geo=nt.nodes.new("ShaderNodeNewGeometry"); geo.location=(-1400,-350)
    sep=nt.nodes.new("ShaderNodeSeparateXYZ"); sep.location=(-1200,-350)
    slope=_ramp(nt,[(0.55,(0,0,0,1)),(0.75,(1,1,1,1))],(-950,-350))  # rock on steep
    n1=_noise(nt, 0.5, 5.0, loc=(-1150, 150))
    n2=_noise(nt, 6.0, 4.0, loc=(-1150, -80))
    grass=_ramp(nt,[(0.3,(0.018,0.030,0.012,1)),(0.7,(0.045,0.06,0.02,1))],(-750,250))
    rockc=_ramp(nt,[(0.3,(0.06,0.055,0.05,1)),(0.7,(0.13,0.12,0.105,1))],(-750,-80))
    mixm=_mix(nt,'MIX',(0,0,0,1),(0,0,0,1),(-380,150))
    bump=nt.nodes.new("ShaderNodeBump"); bump.location=(350,-250)
    bump.inputs["Strength"].default_value=0.7; bump.inputs["Distance"].default_value=0.8
    nt.links.new(geo.outputs["Normal"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], slope.inputs["Fac"])
    nt.links.new(tc.outputs["Generated"], n1.inputs["Vector"])
    nt.links.new(tc.outputs["Generated"], n2.inputs["Vector"])
    nt.links.new(n1.outputs["Fac"], grass.inputs["Fac"])
    nt.links.new(n1.outputs["Fac"], rockc.inputs["Fac"])
    nt.links.new(slope.outputs["Color"], mixm.inputs[0])
    nt.links.new(grass.outputs["Color"], mixm.inputs[1])
    nt.links.new(rockc.outputs["Color"], mixm.inputs[2])
    nt.links.new(mixm.outputs["Color"], bs.inputs["Base Color"])
    nt.links.new(n2.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bs.inputs["Normal"])
    nt.links.new(bs.outputs[0], out.inputs["Surface"])
    return m

def mat_foliage():
    if "Foliage" in MATS: return MATS["Foliage"]
    m = bpy.data.materials.new("Foliage"); MATS["Foliage"] = m
    nt, out = _nt(m)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.location=(520,60)
    bs.inputs["Roughness"].default_value = 0.9
    tc=_texcoord(nt,(-900,0))
    n1=_noise(nt, 3.0, 4.0, loc=(-750,100))
    r1=_ramp(nt,[(0.25,(0.006,0.012,0.006,1)),(0.55,(0.014,0.028,0.012,1)),(0.8,(0.03,0.05,0.02,1))],(-450,100))
    nt.links.new(tc.outputs["Generated"], n1.inputs["Vector"])
    nt.links.new(n1.outputs["Fac"], r1.inputs["Fac"])
    nt.links.new(r1.outputs["Color"], bs.inputs["Base Color"])
    nt.links.new(bs.outputs[0], out.inputs["Surface"])
    return m

def mat_trunk():
    if "Trunk" in MATS: return MATS["Trunk"]
    m = bpy.data.materials.new("Trunk"); MATS["Trunk"] = m
    nt, out = _nt(m)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.location=(520,60)
    bs.inputs["Roughness"].default_value = 0.95
    bs.inputs["Base Color"].default_value = (0.02,0.014,0.01,1)
    nt.links.new(bs.outputs[0], out.inputs["Surface"])
    return m

def mat_wood():
    if "Wood" in MATS: return MATS["Wood"]
    m = bpy.data.materials.new("Wood"); MATS["Wood"] = m
    nt, out = _nt(m)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.location=(520,60)
    bs.inputs["Roughness"].default_value = 0.8
    tc=_texcoord(nt,(-1000,0))
    n1=_noise(nt, 4.0, 4.0, loc=(-850,100)); n1.inputs["Scale"].default_value=4.0
    wave=nt.nodes.new("ShaderNodeTexWave"); wave.wave_type='BANDS'; wave.bands_direction='Z'; wave.location=(-850,-150)
    wave.inputs["Scale"].default_value=6.0; wave.inputs["Distortion"].default_value=6.0; wave.inputs["Detail"].default_value=4.0
    r1=_ramp(nt,[(0.3,(0.05,0.032,0.02,1)),(0.7,(0.11,0.07,0.04,1))],(-550,100))
    bump=nt.nodes.new("ShaderNodeBump"); bump.location=(280,-200)
    bump.inputs["Strength"].default_value=0.4; bump.inputs["Distance"].default_value=0.15
    nt.links.new(tc.outputs["Generated"], n1.inputs["Vector"])
    nt.links.new(tc.outputs["Generated"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Color"], r1.inputs["Fac"])
    nt.links.new(r1.outputs["Color"], bs.inputs["Base Color"])
    nt.links.new(wave.outputs["Color"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bs.inputs["Normal"])
    nt.links.new(bs.outputs[0], out.inputs["Surface"])
    return m

def mat_metal():
    if "Metal" in MATS: return MATS["Metal"]
    m = bpy.data.materials.new("Metal"); MATS["Metal"] = m
    nt, out = _nt(m)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.location=(520,60)
    bs.inputs["Roughness"].default_value = 0.4
    bs.inputs["Metallic"].default_value = 0.85
    bs.inputs["Base Color"].default_value = (0.03,0.03,0.035,1)
    nt.links.new(bs.outputs[0], out.inputs["Surface"])
    return m

def mat_lantern():
    if "Lantern" in MATS: return MATS["Lantern"]
    m = bpy.data.materials.new("Lantern"); MATS["Lantern"] = m
    nt, out = _nt(m)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.location=(520,60)
    bs.inputs["Emission Color"].default_value = (1.0,0.38,0.09,1)
    bs.inputs["Emission Strength"].default_value = 5.0
    bs.inputs["Base Color"].default_value = (0.2,0.08,0.02,1)
    nt.links.new(bs.outputs[0], out.inputs["Surface"])
    return m

def mat_moon():
    if "Moon" in MATS: return MATS["Moon"]
    m = bpy.data.materials.new("Moon"); MATS["Moon"] = m
    nt, out = _nt(m)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.location=(520,60)
    tc=_texcoord(nt,(-900,0))
    n1=_noise(nt, 3.5, 6.0, loc=(-750,100))
    r1=_ramp(nt,[(0.35,(2.0,2.1,2.3,1)),(0.55,(1.1,1.2,1.35,1)),(0.75,(1.7,1.8,2.0,1))],(-450,100))
    bs.inputs["Emission Color"].default_value = (1.0,1.0,1.0,1)
    bs.inputs["Emission Strength"].default_value = 3.0
    bs.inputs["Roughness"].default_value=1.0
    nt.links.new(tc.outputs["Generated"], n1.inputs["Vector"])
    nt.links.new(n1.outputs["Fac"], r1.inputs["Fac"])
    nt.links.new(r1.outputs["Color"], bs.inputs["Emission Color"])
    nt.links.new(bs.outputs[0], out.inputs["Surface"])
    return m

def mat_glass_greenhouse():
    if "GlassGH" in MATS: return MATS["GlassGH"]
    m = bpy.data.materials.new("GlassGH"); MATS["GlassGH"] = m
    nt, out = _nt(m)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.location=(520,60)
    bs.inputs["Roughness"].default_value = 0.15
    bs.inputs["Base Color"].default_value = (0.05,0.07,0.05,1)
    bs.inputs["Emission Color"].default_value = (0.9,0.75,0.4,1)
    bs.inputs["Emission Strength"].default_value = 0.6
    nt.links.new(bs.outputs[0], out.inputs["Surface"])
    return m

# ---------------------------------------------------------------- mesh helpers
def new_mesh_obj(name, verts, faces, col, mat=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    if mat: me.materials.append(mat)
    return ob

def box_obj(name, loc, dims, col, mat=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    ob = bpy.context.active_object
    ob.name = name
    from mathutils import Matrix as _M
    ob.data.transform(_M.Diagonal((dims[0]/2, dims[1]/2, dims[2]/2, 1.0)))
    move_to_col(ob, col)
    if mat: ob.data.materials.append(mat)
    if bevel > 0:
        mod = ob.modifiers.new("Bevel","BEVEL"); mod.width=bevel; mod.segments=2
    return ob

def cyl_obj(name, loc, radius, depth, col, mat=None, verts=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc)
    ob = bpy.context.active_object; ob.name=name
    move_to_col(ob, col)
    if mat: ob.data.materials.append(mat)
    return ob

def cone_obj(name, loc, r1, r2, depth, col, mat=None, verts=24):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth, location=loc)
    ob = bpy.context.active_object; ob.name=name
    move_to_col(ob, col)
    if mat: ob.data.materials.append(mat)
    return ob

def shade_smooth(ob):
    if ob.type=='MESH':
        for p in ob.data.polygons: p.use_smooth=True

# ---------------------------------------------------------------- architecture pieces
def pointed_arch_face(w, h, spring, segments=8, center=(0,0)):
    """2D polygon points of a pointed (gothic) arch opening: width w, total height h,
    arch springs at height 'spring'. Returns list of (x,y) in local 2D."""
    pts = [(-w/2, 0.0), (-w/2, spring)]
    r = w  # gothic arch radius ~ width for 4-centered look; use two arcs
    # left arc from (-w/2, spring) to apex (0, h)
    for i in range(1, segments+1):
        t = i/segments
        ang = pi - (pi/2)*t
        x = -w/2 + (w/2)*(1-cos(ang*0.5)) * 2 * t  # approximate blend
        # simpler: quadratic bezier from (-w/2,spring) ctrl (-w/2, h) to (0,h)
    # use bezier approximation instead
    pts = [(-w/2, 0.0), (-w/2, spring)]
    for i in range(1, segments+1):
        t = i/segments
        x = (1-t)**2 * (-w/2) + 2*(1-t)*t * (-w/2) + t**2 * 0.0
        y = (1-t)**2 * spring + 2*(1-t)*t * h + t**2 * h
        pts.append((x, y))
    for i in range(1, segments+1):
        t = i/segments
        x = (1-t)**2 * 0.0 + 2*(1-t)*t * (w/2) + t**2 * (w/2)
        y = (1-t)**2 * h + 2*(1-t)*t * h + t**2 * spring
        pts.append((x, y))
    pts.append((w/2, 0.0))
    return pts

def arch_panel(name, w, h, spring, depth, col, mat, loc=(0,0,0), rot=(0,0,0), seg=6):
    """Solid extruded pointed-arch panel (used as glass/fill)."""
    pts2 = pointed_arch_face(w, h, spring, seg)
    verts = [(x, -depth/2, y) for (x,y) in pts2] + [(x, depth/2, y) for (x,y) in pts2]
    n = len(pts2)
    faces = []
    faces.append(tuple(range(n)))
    faces.append(tuple(range(n, 2*n))[::-1])
    for i in range(n):
        j = (i+1) % n
        faces.append((i, j, n+j, n+i))
    ob = new_mesh_obj(name, verts, faces, col, mat)
    ob.location = loc
    ob.rotation_euler = rot
    return ob

def arch_frame(name, w, h, spring, border, depth, col, mat, loc=(0,0,0), rot=(0,0,0), seg=6):
    """Stone frame: outer arch minus inner arch, extruded."""
    outer = pointed_arch_face(w+2*border, h+border, spring, seg)
    inner = pointed_arch_face(w, h, spring, seg)
    n = len(outer)
    verts = []
    for yoff in (-depth/2, depth/2):
        verts += [(x, yoff, y) for (x,y) in outer]
        verts += [(x, yoff, y) for (x,y) in inner]
    faces = []
    O0, I0, O1, I1 = 0, n, 2*n, 3*n
    for i in range(n):
        j=(i+1)%n
        faces.append((O0+i, O0+j, I0+j, I0+i))   # front ring
        faces.append((O1+j, O1+i, I1+i, I1+j))   # back ring
        faces.append((O0+j, O0+i, O1+i, O1+j))   # outer side
        faces.append((I0+i, I0+j, I1+j, I1+i))   # inner side
    ob = new_mesh_obj(name, verts, faces, col, mat)
    ob.location = loc; ob.rotation_euler = rot
    return ob

def gable_roof(name, length, width, height, loc, col, mat, overhang=0.6, axis='X'):
    """Steep gabled roof: prism. Axis X => ridge runs along X."""
    L, W, H = length/2+overhang, width/2+overhang, height
    verts = [(-L,-W,0),(L,-W,0),(L,W,0),(-L,W,0),(-L,0,H),(L,0,H)]
    faces = [(0,1,5,4),(3,4,5,2),(0,4,3),(1,2,5),(0,3,2,1)]
    ob = new_mesh_obj(name, verts, faces, col, mat)
    ob.location = loc
    if axis=='Y': ob.rotation_euler[2] = pi/2
    return ob

def crenellations(name, length, base_loc, col, mat, axis='X', merlon_w=1.1, gap=1.0, h=1.4, thick=0.5):
    """Row of merlons; base_loc is bottom center of the row."""
    step = merlon_w + gap
    count = max(1, int(length/step))
    verts, faces = [], []
    def add_box(cx, cz):
        nonlocal verts, faces
        b = len(verts)
        hw, ht = merlon_w/2, thick/2
        vs = [(cx-hw,-ht,cz),(cx+hw,-ht,cz),(cx+hw,ht,cz),(cx-hw,ht,cz),
              (cx-hw,-ht,cz+h),(cx+hw,-ht,cz+h),(cx+hw,ht,cz+h),(cx-hw,ht,cz+h)]
        verts += vs
        faces += [(b+0,b+1,b+2,b+3),(b+4,b+7,b+6,b+5),(b+0,b+4,b+5,b+1),
                  (b+1,b+5,b+6,b+2),(b+2,b+6,b+7,b+3),(b+3,b+7,b+4,b+0)]
    for i in range(count):
        cx = -length/2 + step/2 + i*step
        add_box(cx, 0)
    ob = new_mesh_obj(name, verts, faces, col, mat)
    ob.location = base_loc
    if axis=='Y': ob.rotation_euler[2] = pi/2
    return ob

def corbel_ring(name, r_base, r_top, h, loc, col, mat, verts_n=24):
    """Conical corbelled course (machicolation ring) flaring outward."""
    return cone_obj(name, (loc[0],loc[1],loc[2]+h/2), r_top, r_base, h, col, mat, verts=verts_n)

def tower(name, x, y, z_base, radius, h_wall, col, stone, slate,
          spire_h=None, spire_mat=None, corbel=True, cren=False, finial=True,
          windows=0, win_mats=None, win_rows=1, verts_n=20):
    """Cylindrical tower with corbelled crown + conical spire. Returns top z."""
    cyl_obj(name, (x,y,z_base+h_wall/2), radius, h_wall, col, stone, verts=verts_n)
    z_top = z_base + h_wall
    if corbel:
        corbel_ring(name+"_corbel", radius, radius*1.22, 1.6, (x,y,z_top), col, stone, verts_n)
        z_top += 1.6
    if cren:
        ring = crenellations(name+"_cren", 2*pi*radius*0.9, (0,0,0), col, stone,
                             merlon_w=0.9, gap=0.8, h=1.2, thick=0.45)
        # arrange merlons in a circle: rebuild as radial
        bpy.data.objects.remove(ring)
        verts, faces = [], []
        cnt = int(2*pi*radius/1.7)
        for i in range(cnt):
            a = i/cnt*2*pi
            cx, cy = x+radius*1.05*cos(a), y+radius*1.05*sin(a)
            b=len(verts); hw,ht,hh=0.45,0.25,1.2
            ca,sa=cos(a),sin(a)
            vs=[(-hw,-ht,0),(hw,-ht,0),(hw,ht,0),(-hw,ht,0),(-hw,-ht,hh),(hw,-ht,hh),(hw,ht,hh),(-hw,ht,hh)]
            for vx,vy,vz in vs:
                verts.append((cx+vx*ca-vy*sa, cy+vx*sa+vy*ca, z_top+vz))
            faces += [(b+0,b+1,b+2,b+3),(b+4,b+7,b+6,b+5),(b+0,b+4,b+5,b+1),
                      (b+1,b+5,b+6,b+2),(b+2,b+6,b+7,b+3),(b+3,b+7,b+4,b+0)]
        new_mesh_obj(name+"_cren", verts, faces, col, stone)
        z_top += 1.2
    if spire_h:
        sm = spire_mat or slate
        cone_obj(name+"_spire", (x,y,z_top+spire_h/2), radius*1.18, 0.02, spire_h, col, sm, verts=verts_n)
        if finial:
            cone_obj(name+"_finial", (x,y,z_top+spire_h+0.9), 0.12, 0.001, 1.8, col, mat_metal(), verts=8)
        z_top += spire_h
    return z_top

def add_window_panes(name, specs, col, mats, frame_mat=None):
    """specs: list of (loc, rot_euler_z_or_full, w, h, spring, arch?) glass panes merged into one mesh,
    randomly assigned lit/dark materials. Returns object."""
    verts, faces, fmats = [], [], []
    for spec in specs:
        loc, rot, w, h, spring = spec
        pts = pointed_arch_face(w, h, spring, 5)
        b = len(verts)
        M = Matrix.Translation(Vector(loc)) @ rot.to_matrix().to_4x4()
        for (px, py) in pts:
            v = M @ Vector((px, 0.0, py))
            verts.append(tuple(v))
        n = len(pts)
        faces.append(tuple(b+i for i in range(n)))
        wts = ([4,3,3,2,1,2] * 3)[:len(mats)]
        fmats.append(random.choices(range(len(mats)), weights=wts)[0])
    ob = new_mesh_obj(name, verts, faces, col, None)
    for mt in mats: ob.data.materials.append(mt)
    for i, poly in enumerate(ob.data.polygons):
        poly.material_index = fmats[i]
    return ob

def buttress(name, loc, h, col, stone, rot_z=0.0, depth=1.2, width=1.4, steps=3):
    """Stepped buttress: stack of shrinking boxes."""
    z = loc[2]
    for i in range(steps):
        frac = i/steps
        hh = h/steps
        dd = depth*(1-0.65*frac)
        ob = box_obj(f"{name}_{i}", (loc[0], loc[1], z+hh/2), (width, dd, hh), col, stone)
        ob.rotation_euler[2] = rot_z
        z += hh
    # small pinnacle
    ob = cone_obj(f"{name}_pin", (loc[0], loc[1], z+1.2), width*0.42, 0.02, 2.4, col, stone, verts=8)
    ob.rotation_euler[2] = rot_z

def stair_flight(name, start, end, steps, width, col, stone):
    """Straight stair flight from start to end (Vector)."""
    s, e = Vector(start), Vector(end)
    d = e - s
    run = Vector((d.x, d.y, 0)).length
    step_d = run/steps
    step_h = d.z/steps
    ang = math.atan2(d.y, d.x)
    for i in range(steps):
        t = (i+0.5)/steps
        p = s + d*t
        ob = box_obj(f"{name}_{i}", (p.x, p.y, p.z - step_h/2 + 0.05),
                     (step_d*1.05, width, max(step_h,0.12)), col, stone)
        ob.rotation_euler[2] = ang

def lantern_post(name, loc, col, h=3.2):
    metal = mat_metal(); lm = mat_lantern()
    cyl_obj(name+"_post", (loc[0],loc[1],loc[2]+h/2), 0.09, h, col, metal, verts=8)
    box_obj(name+"_cap", (loc[0],loc[1],loc[2]+h+0.42), (0.62,0.62,0.14), col, metal)
    cone_obj(name+"_roof", (loc[0],loc[1],loc[2]+h+0.72), 0.5, 0.02, 0.5, col, metal, verts=4)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, radius=0.26, location=(loc[0],loc[1],loc[2]+h+0.15))
    ob=bpy.context.active_object; ob.name=name+"_globe"; move_to_col(ob,col); ob.data.materials.append(lm)

result = {"kit": "loaded"}
