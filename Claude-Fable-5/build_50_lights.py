"""Light + atmosphere: moonlit night sky (stars, cloud wisps, moon halo),
moon disc + matching cool sun key, warm interior fill points, lake mist."""
import bpy
import math
import hog

hog.clear_coll('Lights')
hog.clear_coll('FX')

D = 200


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


# ---------------------------------------------------------------- moon geo
AZ = math.radians(-6.0)      # west of north
EL = math.radians(17.5)
DIST = 3600.0
mx = DIST * math.cos(EL) * math.sin(AZ)
my = DIST * math.cos(EL) * math.cos(AZ)
mz = DIST * math.sin(EL)

moon_mat = bpy.data.materials.get('MoonGlow')
if moon_mat is None:
    moon_mat = bpy.data.materials.new('MoonGlow')
    moon_mat.use_fake_user = True
moon_mat.use_nodes = True
nt = moon_mat.node_tree
nt.nodes.clear()
out = N(nt, 'ShaderNodeOutputMaterial', 4, 0)
tc = N(nt, 'ShaderNodeTexCoord', -2, 0)
n1 = N(nt, 'ShaderNodeTexNoise', -1, 0, inputs={'Scale': 3.0, 'Detail': 5.0})
L(nt, tc.outputs['Generated'], n1.inputs['Vector'])
maria = ramp(nt, 0, 0, [(0.35, (0.78, 0.82, 0.90, 1)),
                        (0.55, (1.0, 1.0, 0.98, 1)),
                        (0.75, (0.82, 0.86, 0.94, 1))])
L(nt, n1.outputs['Fac'], maria.inputs['Fac'])
emis = N(nt, 'ShaderNodeEmission', 2, 0, inputs={'Strength': 22.0})
L(nt, maria.outputs['Color'], emis.inputs['Color'])
L(nt, emis.outputs['Emission'], out.inputs['Surface'])

moon = hog.cyl('Moon', 'Lights', r=52.0, h=1.0, loc=(mx, my, mz), segs=48,
               mat=moon_mat)
moon.rotation_euler = (math.pi / 2 + EL, 0, -AZ)
moon.visible_shadow = False

# ---------------------------------------------------------------- moon key
ld = bpy.data.lights.new('MoonSun', 'SUN')
ld.energy = 2.6
ld.color = (0.70, 0.82, 1.0)
ld.angle = math.radians(0.8)
sun = bpy.data.objects.new('MoonSun', ld)
hog.coll('Lights').objects.link(sun)
sun.rotation_euler = (math.pi / 2 - EL, 0, math.pi - AZ)
# rim kicker from the north-west, faint, separates towers from sky
ld2 = bpy.data.lights.new('RimFill', 'SUN')
ld2.energy = 1.3
ld2.color = (0.45, 0.60, 0.95)
ld2.angle = math.radians(4.0)
rim = bpy.data.objects.new('RimFill', ld2)
hog.coll('Lights').objects.link(rim)
rim.rotation_euler = (math.radians(65), 0, math.radians(-140))
# soft sky-bounce fill from the south so camera-facing walls aren't void
ld3 = bpy.data.lights.new('SkyBounce', 'SUN')
ld3.energy = 1.2
ld3.color = (0.35, 0.48, 0.72)
ld3.angle = math.radians(12.0)
skyb = bpy.data.objects.new('SkyBounce', ld3)
hog.coll('Lights').objects.link(skyb)
skyb.rotation_euler = (math.radians(38), 0, math.radians(178))

# ---------------------------------------------------------------- world sky
w = bpy.context.scene.world
nt = w.node_tree
nt.nodes.clear()
wout = N(nt, 'ShaderNodeOutputWorld', 8, 0)
bg = N(nt, 'ShaderNodeBackground', 6, 0, inputs={'Strength': 1.0})
tc = N(nt, 'ShaderNodeTexCoord', -8, 0)
sep = N(nt, 'ShaderNodeSeparateXYZ', -7, 0)
L(nt, tc.outputs['Generated'], sep.inputs['Vector'])

# vertical gradient
grad = ramp(nt, -5.5, 1.5, [
    (0.44, (0.022, 0.037, 0.062, 1)),     # horizon band
    (0.52, (0.013, 0.024, 0.046, 1)),
    (0.65, (0.006, 0.012, 0.028, 1)),
    (1.0, (0.002, 0.005, 0.014, 1))])     # zenith
zmap = N(nt, 'ShaderNodeMapRange', -6.3, 1.5,
         inputs={'From Min': -0.05, 'From Max': 1.0})
L(nt, sep.outputs['Z'], zmap.inputs['Value'])
L(nt, zmap.outputs['Result'], grad.inputs['Fac'])

# stars: voronoi points, faded at horizon
vor = N(nt, 'ShaderNodeTexVoronoi', -6, -1, inputs={'Scale': 140.0})
vor.feature = 'F1'
L(nt, tc.outputs['Generated'], vor.inputs['Vector'])
star_m = N(nt, 'ShaderNodeMath', -5, -1, operation='LESS_THAN',
           inputs={1: 0.015})
L(nt, vor.outputs['Distance'], star_m.inputs[0])
# per-star brightness via voronoi color
star_b = N(nt, 'ShaderNodeMath', -4.2, -1.3, operation='POWER',
           inputs={1: 3.0})
sepc = N(nt, 'ShaderNodeSeparateColor', -5, -1.9)
L(nt, vor.outputs['Color'], sepc.inputs['Color'])
L(nt, sepc.outputs['Red'], star_b.inputs[0])
star = N(nt, 'ShaderNodeMath', -3.4, -1, operation='MULTIPLY')
L(nt, star_m.outputs['Value'], star.inputs[0])
L(nt, star_b.outputs['Value'], star.inputs[1])
horiz = N(nt, 'ShaderNodeMapRange', -4.2, -0.3,
          inputs={'From Min': 0.05, 'From Max': 0.35})
L(nt, sep.outputs['Z'], horiz.inputs['Value'])
star2 = N(nt, 'ShaderNodeMath', -2.6, -0.7, operation='MULTIPLY')
L(nt, star.outputs['Value'], star2.inputs[0])
L(nt, horiz.outputs['Result'], star2.inputs[1])

# cloud wisps: stretched noise bands, hide stars where cloudy
mapc = N(nt, 'ShaderNodeMapping', -6.5, -3.2, inputs={'Scale': (2.2, 2.2, 5.5)})
L(nt, tc.outputs['Generated'], mapc.inputs['Vector'])
ncl = N(nt, 'ShaderNodeTexNoise', -5.5, -3.2,
        inputs={'Scale': 1.6, 'Detail': 7.0, 'Roughness': 0.62,
                'Distortion': 0.8})
L(nt, mapc.outputs['Vector'], ncl.inputs['Vector'])
cl_r = ramp(nt, -4.5, -3.2, [(0.48, (0, 0, 0, 1)), (0.75, (1, 1, 1, 1))])
L(nt, ncl.outputs['Fac'], cl_r.inputs['Fac'])
# clouds only in a band above horizon
cl_band = N(nt, 'ShaderNodeMapRange', -5.5, -4.2,
            inputs={'From Min': 0.08, 'From Max': 0.25})
L(nt, sep.outputs['Z'], cl_band.inputs['Value'])
cl_band2 = N(nt, 'ShaderNodeMapRange', -4.5, -4.6, interpolation_type='SMOOTHSTEP',
             inputs={'From Min': 0.75, 'From Max': 0.35, 'To Min': 0.0,
                     'To Max': 1.0})
L(nt, sep.outputs['Z'], cl_band2.inputs['Value'])
clm = N(nt, 'ShaderNodeMath', -3.5, -3.6, operation='MULTIPLY')
L(nt, cl_r.outputs['Color'], clm.inputs[0])
L(nt, cl_band.outputs['Result'], clm.inputs[1])
clm2 = N(nt, 'ShaderNodeMath', -2.8, -3.8, operation='MULTIPLY')
L(nt, clm.outputs['Value'], clm2.inputs[0])
L(nt, cl_band2.outputs['Result'], clm2.inputs[1])

# moon halo: glow around moon direction
mdir = (math.cos(EL) * math.sin(AZ), math.cos(EL) * math.cos(AZ),
        math.sin(EL))
dot = N(nt, 'ShaderNodeVectorMath', -6, -5.4, operation='DOT_PRODUCT')
dot.inputs[1].default_value = mdir
L(nt, tc.outputs['Generated'], dot.inputs[0])
halo_p = N(nt, 'ShaderNodeMath', -5, -5.4, operation='POWER',
           inputs={1: 90.0})
halo_c = N(nt, 'ShaderNodeMath', -5.5, -5.0, operation='MAXIMUM',
           inputs={1: 0.0})
L(nt, dot.outputs['Value'], halo_c.inputs[0])
L(nt, halo_c.outputs['Value'], halo_p.inputs[0])
halo_s = N(nt, 'ShaderNodeMath', -4.2, -5.4, operation='MULTIPLY',
           inputs={1: 1.1})
L(nt, halo_p.outputs['Value'], halo_s.inputs[0])
# wide soft halo
halo2_p = N(nt, 'ShaderNodeMath', -5, -6.1, operation='POWER',
            inputs={1: 8.0})
L(nt, halo_c.outputs['Value'], halo2_p.inputs[0])
halo2_s = N(nt, 'ShaderNodeMath', -4.2, -6.1, operation='MULTIPLY',
            inputs={1: 0.16})
L(nt, halo2_p.outputs['Value'], halo2_s.inputs[0])
halo_add = N(nt, 'ShaderNodeMath', -3.4, -5.7, operation='ADD')
L(nt, halo_s.outputs['Value'], halo_add.inputs[0])
L(nt, halo2_s.outputs['Value'], halo_add.inputs[1])

# compose: gradient + stars*(1-clouds) + clouds_color + halo
star_vis = N(nt, 'ShaderNodeMath', -2.0, -1.6, operation='SUBTRACT',
             inputs={0: 1.0})
L(nt, clm2.outputs['Value'], star_vis.inputs[1])
star3 = N(nt, 'ShaderNodeMath', -1.4, -1.2, operation='MULTIPLY',
          inputs={1: 16.0})
L(nt, star2.outputs['Value'], star3.inputs[0])
star4 = N(nt, 'ShaderNodeMath', -0.8, -1.4, operation='MULTIPLY')
L(nt, star3.outputs['Value'], star4.inputs[0])
L(nt, star_vis.outputs['Value'], star4.inputs[1])

mix1 = N(nt, 'ShaderNodeMix', 0, 0.6, data_type='RGBA')
mix1.blend_type = 'MIX'
cl_col = ramp(nt, -1.6, -2.6, [(0.0, (0.045, 0.065, 0.095, 1)),
                               (1.0, (0.10, 0.13, 0.17, 1))])
L(nt, halo_add.outputs['Value'], cl_col.inputs['Fac'])
L(nt, clm2.outputs['Value'], mix1.inputs['Factor'])
L(nt, grad.outputs['Color'], mix1.inputs['A'])
L(nt, cl_col.outputs['Color'], mix1.inputs['B'])

addst = N(nt, 'ShaderNodeMix', 1.5, 0.3, data_type='RGBA', blend_type='ADD')
addst.inputs['Factor'].default_value = 1.0
stcol = N(nt, 'ShaderNodeCombineColor', 0.4, -1.2)
for i, v in enumerate((0.85, 0.92, 1.0)):
    stcol.inputs[i].default_value = v
stmul = N(nt, 'ShaderNodeVectorMath', 0.9, -0.9, operation='SCALE')
L(nt, stcol.outputs['Color'], stmul.inputs[0])
L(nt, star4.outputs['Value'], stmul.inputs['Scale'])
L(nt, mix1.outputs['Result'], addst.inputs['A'])
L(nt, stmul.outputs['Vector'], addst.inputs['B'])

addhalo = N(nt, 'ShaderNodeMix', 3, 0.15, data_type='RGBA', blend_type='ADD')
addhalo.inputs['Factor'].default_value = 1.0
halocol = N(nt, 'ShaderNodeCombineColor', 1.8, -0.9)
for i, v in enumerate((0.55, 0.68, 0.95)):
    halocol.inputs[i].default_value = v
halomul = N(nt, 'ShaderNodeVectorMath', 2.4, -0.8, operation='SCALE')
L(nt, halocol.outputs['Color'], halomul.inputs[0])
L(nt, halo_add.outputs['Value'], halomul.inputs['Scale'])
L(nt, addst.outputs['Result'], addhalo.inputs['A'])
L(nt, halomul.outputs['Vector'], addhalo.inputs['B'])

L(nt, addhalo.outputs['Result'], bg.inputs['Color'])
L(nt, bg.outputs['Background'], wout.inputs['Surface'])

# ---------------------------------------------------------------- mist
def mist_material(name, z0, z1, density, aniso=0.5):
    """Volume scatter whose density falls off with WORLD z from z0 to z1."""
    mm = bpy.data.materials.get(name)
    if mm is None:
        mm = bpy.data.materials.new(name)
        mm.use_fake_user = True
    mm.use_nodes = True
    nt = mm.node_tree
    nt.nodes.clear()
    out = N(nt, 'ShaderNodeOutputMaterial', 6, 0)
    geo = N(nt, 'ShaderNodeNewGeometry', -6, 0)
    nno = N(nt, 'ShaderNodeTexNoise', -4, 0.5,
            inputs={'Scale': 0.010, 'Detail': 5.0, 'Distortion': 0.6})
    L(nt, geo.outputs['Position'], nno.inputs['Vector'])
    nr = ramp(nt, -3, 0.5, [(0.46, (0, 0, 0, 1)), (0.78, (1, 1, 1, 1))])
    L(nt, nno.outputs['Fac'], nr.inputs['Fac'])
    sep = N(nt, 'ShaderNodeSeparateXYZ', -4, -1)
    L(nt, geo.outputs['Position'], sep.inputs['Vector'])
    zfall = N(nt, 'ShaderNodeMapRange', -3, -1,
              inputs={'From Min': z0, 'From Max': z1, 'To Min': 1.0,
                      'To Max': 0.0})
    L(nt, sep.outputs['Z'], zfall.inputs['Value'])
    dmul = N(nt, 'ShaderNodeMath', -1.5, 0, operation='MULTIPLY')
    L(nt, nr.outputs['Color'], dmul.inputs[0])
    L(nt, zfall.outputs['Result'], dmul.inputs[1])
    dscale = N(nt, 'ShaderNodeMath', -0.5, 0, operation='MULTIPLY',
               inputs={1: density})
    L(nt, dmul.outputs['Value'], dscale.inputs[0])
    vol = N(nt, 'ShaderNodeVolumeScatter', 2, 0,
            inputs={'Color': (0.65, 0.75, 0.9, 1), 'Anisotropy': aniso})
    L(nt, dscale.outputs['Value'], vol.inputs['Density'])
    L(nt, vol.outputs['Volume'], out.inputs['Volume'])
    return mm


lake_mist = mist_material('LakeMist', 0.3, 7.0, 0.014)
veil_mist = mist_material('HighVeil', 30.0, 50.0, 0.0008, aniso=0.3)

mist = hog.box('Mist_Lake', 'FX', size=(1500, 1100, 9), loc=(-30, -280, -0.5),
               base=True, mat=lake_mist)
mist.visible_shadow = False
mist2 = hog.box('Mist_Gorge', 'FX', size=(260, 420, 9), loc=(150, 60, -2),
                base=True, mat=lake_mist)
mist2.visible_shadow = False
mist3 = hog.box('Mist_Veil', 'FX', size=(800, 560, 26), loc=(0, -80, 29),
                base=True, mat=veil_mist)
mist3.visible_shadow = False

# ------------------------------------------------- warm interior points
def warm_point(name, loc, energy=120.0, size=0.6,
               color=(1.0, 0.62, 0.28)):
    ld = bpy.data.lights.new(name, 'POINT')
    ld.energy = energy
    ld.color = color
    ld.shadow_soft_size = size
    ob = bpy.data.objects.new(name, ld)
    hog.coll('Lights').objects.link(ob)
    ob.location = loc
    return ob


warm_point('P_Boathouse', (-27, -98, 4.2), 340)
warm_point('P_Gatehouse', (103.5, -6, 61.5), 200)
warm_point('P_GH1', (44, -76, 58.5), 12, color=(0.9, 0.85, 0.55))
warm_point('P_GH2', (59, -73, 58.5), 9, color=(0.9, 0.85, 0.55))
warm_point('P_Hut', (-195, -55, 4.5), 130)
warm_point('P_CourtW', (-62, 30, 78), 150)
warm_point('P_CourtE', (30, 20, 80), 120)
warm_point('P_GreatHallInt', (-58, -16, 95), 400, size=2.0)

# ---------------------------------------------------------------- exposure
scene = bpy.context.scene
scene.view_settings.exposure = 0.85
scene.view_settings.look = 'AgX - Base Contrast'
scene.cycles.volume_step_rate = 1.0
scene.cycles.volume_max_steps = 256
