"""World sky, moon, water surface, mist volumes, lantern lights."""
import bpy, math
from mathutils import Vector, Euler
import geo
from materials import NT

# moon direction (towards the moon): azimuth from +x counter-clockwise, elevation
MOON_AZ = math.radians(77.5)
MOON_EL = math.radians(22.5)
MOON_R = math.radians(1.25)   # cinematic, larger than life
# key moonlight is cheated ~30 deg further left than the visible disc so the crag and towers model
KEY_AZ = math.radians(107.0)
KEY_EL = math.radians(21.0)


def moon_dir():
    return Vector((math.cos(MOON_EL) * math.cos(MOON_AZ), math.cos(MOON_EL) * math.sin(MOON_AZ), math.sin(MOON_EL)))


class WT(NT):
    """NT helper bound to a world node tree."""

    def __init__(self, world):
        self.m = world
        world.use_nodes = True
        self.t = world.node_tree
        self.t.nodes.clear()
        self.x = 0
        self.out = self.n('ShaderNodeOutputWorld')


def world(strength=1.0):
    w = bpy.data.worlds.get('NightSky') or bpy.data.worlds.new('NightSky')
    bpy.context.scene.world = w
    t = WT(w)
    tc = t.n('ShaderNodeTexCoord')
    d = tc.outputs['Generated']
    md = moon_dir()
    sep = t.n('ShaderNodeSeparateXYZ', inp={'Vector': d})
    dz = sep.outputs[2]
    # --- gradient
    hz = t.maprange(dz, -0.02, 0.45, 0.0, 1.0)
    hz = t.math('POWER', hz, 0.55)
    sky = t.ramp(hz, [(0.0, (0.030, 0.052, 0.068)), (0.12, (0.020, 0.036, 0.055)), (0.5, (0.008, 0.016, 0.032)),
                      (1.0, (0.003, 0.006, 0.014))]).outputs[0]
    # --- moon terms
    dot = t.n('ShaderNodeVectorMath', operation='DOT_PRODUCT', inp={0: d, 1: md})
    m = t.math('MAXIMUM', dot.outputs['Value'], 0.0)
    halo_n = t.math('POWER', m, 900.0)
    halo_w = t.math('POWER', m, 40.0)
    halo_vw = t.math('POWER', m, 6.0)
    # --- clouds on a projected layer
    proj = t.n('ShaderNodeCombineXYZ')
    zc = t.math('MAXIMUM', dz, 0.035)
    t.l(t.math('DIVIDE', sep.outputs[0], zc), proj.inputs[0])
    t.l(t.math('DIVIDE', sep.outputs[1], zc), proj.inputs[1])
    proj.inputs[2].default_value = 0.3
    cn = t.noise(proj.outputs[0], 0.55, 7.0, 0.62, dist=0.35)
    cn2 = t.noise(proj.outputs[0], 2.2, 5.0, 0.6)
    wisp = t.maprange(t.math('ADD', cn.outputs['Fac'], t.math('MULTIPLY', cn2.outputs['Fac'], 0.25)), 0.52, 0.86, 0.0, 1.0)
    # large billowing banks with firmer edges
    big = t.noise(proj.outputs[0], 0.16, 6.0, 0.58, dist=0.6)
    bank = t.maprange(t.math('ADD', big.outputs['Fac'], t.math('MULTIPLY', cn2.outputs['Fac'], 0.18)), 0.5, 0.64, 0.0, 1.0)
    cden = t.math('MAXIMUM', t.math('MULTIPLY', wisp, 0.75), bank)
    # thin the clouds right around the moon so it shines through a gap, thicken low
    gap = t.maprange(halo_vw, 0.55, 0.95, 1.0, 0.35)
    cden = t.math('MULTIPLY', cden, gap)
    horiz = t.maprange(dz, 0.0, 0.08, 0.35, 1.0)
    cden = t.math('MULTIPLY', cden, horiz, clamp=True)
    # cloud shading: dark bodies, moon-silvered near the moon, faint bluish elsewhere
    edge = t.maprange(cn2.outputs['Fac'], 0.3, 0.7, 0.6, 1.2)
    lit = t.math('ADD', t.math('MULTIPLY', halo_w, 1.0), t.math('MULTIPLY', halo_vw, 0.18))
    lit = t.math('MULTIPLY', lit, edge)
    body = t.mix(t.maprange(cn2.outputs['Fac'], 0.35, 0.7, 0.0, 1.0), (0.022, 0.03, 0.045), (0.045, 0.056, 0.075))
    cloud_col = t.mix(t.math('MINIMUM', t.math('MULTIPLY', lit, edge), 1.0), body, (0.26, 0.34, 0.41))
    cloud_col = t.mix(t.maprange(lit, 0.8, 2.0, 0.0, 1.0), cloud_col, (0.62, 0.72, 0.8))
    # --- stars
    vor = t.n('ShaderNodeTexVoronoi', inp={'Vector': d, 'Scale': 420.0, 'Randomness': 1.0})
    star = t.maprange(vor.outputs['Distance'], 0.055, 0.0, 0.0, 1.0)
    star = t.math('POWER', star, 3.0)
    sb = t.maprange(t.n('ShaderNodeSeparateColor', inp={'Color': vor.outputs['Color']}).outputs[0], 0.72, 1.0, 0.0, 1.0)
    star = t.math('MULTIPLY', star, t.math('POWER', sb, 2.0))
    star = t.math('MULTIPLY', star, t.maprange(dz, 0.05, 0.35, 0.0, 1.0))
    star = t.math('MULTIPLY', star, t.math('SUBTRACT', 1.0, cden, clamp=True))
    star = t.math('MULTIPLY', star, t.maprange(halo_vw, 0.3, 0.8, 1.0, 0.0))
    star_c = t.mix(star, (0, 0, 0), (4.0, 4.2, 4.8))
    # --- moon disc with maria
    cosr = math.cos(MOON_R)
    disc = t.maprange(m, cosr - 0.0000045, cosr + 0.0000015, 0.0, 1.0)
    mar = t.noise(d, 110.0, 1.5, 0.5, dist=0.2)
    mar2 = t.noise(d, 600.0, 2.0, 0.5)
    mar_m = t.maprange(mar.outputs['Fac'], 0.45, 0.62, 1.0, 0.6)
    mar_m = t.math('MULTIPLY', mar_m, t.maprange(mar2.outputs['Fac'], 0.3, 0.7, 0.92, 1.05))
    limb = t.maprange(m, cosr, 1.0, 0.8, 1.0)
    moon_c = t.mix(t.math('MULTIPLY', t.math('MULTIPLY', disc, mar_m), limb), (0, 0, 0), (1.0, 0.97, 0.9))
    moon_c = t.mix(t.math('MULTIPLY', cden, 0.6), moon_c, (0, 0, 0))   # clouds veil the moon slightly
    # --- composite
    halo_c = t.mix(t.math('ADD', t.math('MULTIPLY', halo_n, 0.55), t.math('MULTIPLY', halo_w, 0.06)), (0, 0, 0), (0.55, 0.68, 0.8))
    col = t.mix(cden, sky, cloud_col)
    col = t.mix(1.0, col, halo_c, 'ADD')
    col = t.mix(1.0, col, star_c, 'ADD')
    sky_bg = t.n('ShaderNodeBackground', inp={'Color': col, 'Strength': strength})
    moon_bg = t.n('ShaderNodeBackground', inp={'Color': moon_c, 'Strength': 2.2})
    add = t.n('ShaderNodeAddShader')
    t.l(sky_bg.outputs[0], add.inputs[0])
    t.l(moon_bg.outputs[0], add.inputs[1])
    t.l(add.outputs[0], t.out.inputs['Surface'])
    return w


def moon_light(strength=1.2):
    coll = geo.get_coll('Lights')
    ob = bpy.data.objects.get('Moon_Key')
    if ob is None:
        ld = bpy.data.lights.new('Moon_Key', 'SUN')
        ob = bpy.data.objects.new('Moon_Key', ld)
        coll.objects.link(ob)
    ld = ob.data
    ld.energy = strength
    ld.color = (0.60, 0.72, 1.0)
    ld.angle = math.radians(1.0)
    d = Vector((math.cos(KEY_EL) * math.cos(KEY_AZ), math.cos(KEY_EL) * math.sin(KEY_AZ), math.sin(KEY_EL)))
    ob.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    ob.visible_glossy = False   # reflections come from the visible world moon disc
    return ob


def fill_light(strength=0.4):
    """soft cool fill standing in for moonlight bounced off the cloud deck behind the camera."""
    coll = geo.get_coll('Lights')
    ob = bpy.data.objects.get('Sky_Fill')
    if ob is None:
        ld = bpy.data.lights.new('Sky_Fill', 'SUN')
        ob = bpy.data.objects.new('Sky_Fill', ld)
        coll.objects.link(ob)
    ld = ob.data
    ld.energy = strength
    ld.color = (0.55, 0.68, 1.0)
    ld.angle = math.radians(25.0)
    ob.visible_glossy = False
    az, el = math.radians(245.0), math.radians(28.0)
    d = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
    ob.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    return ob


WAVES = [  # (amplitude m, wavelength m, direction deg)
    (0.070, 13.0, 100.0), (0.050, 8.3, 80.0), (0.035, 5.6, 115.0), (0.025, 4.1, 70.0),
    (0.018, 3.4, 95.0)]
WATER_C = (-30.0, -300.0)


def wave_h(x, y, fade):
    h = 0.0
    for i, (a, lam, d) in enumerate(WAVES):
        k = math.tau / lam
        dx, dy = math.cos(math.radians(d)), math.sin(math.radians(d))
        h += a * math.sin(k * (x * dx + y * dy) + i * 1.7)
    return h * fade


def water_plane(N=1300):
    """closed lake volume: a warped top grid (0.8 m cells near the cameras) with directional
    wave displacement, skirt and floor."""
    coll = geo.get_coll('Water')
    name = 'Lake_Surface'
    old = bpy.data.objects.get(name)
    if old:
        d = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if d.users == 0:
            bpy.data.meshes.remove(d)
    cx, cy = WATER_C
    a, b = N * 0.4, 9000.0 - N * 0.4
    us = [-1 + 2 * i / N for i in range(N + 1)]
    xs = [cx + a * u + b * u ** 3 for u in us]
    ys = [cy + a * u + b * u ** 3 for u in us]
    verts = []
    for y in ys:
        for x in xs:
            r = math.hypot(x - cx, y - cy)
            fade = 1.0 - geo.smoothstep(650.0, 1300.0, r)
            verts.append((x, y, wave_h(x, y, fade) if fade > 0 else 0.0))
    W = N + 1
    faces = []
    for j in range(N):
        for i in range(N):
            q = j * W + i
            faces.append((q, q + 1, q + W + 1, q + W))
    # skirt + floor
    border = [i for i in range(W)] + [j * W + N for j in range(1, W)] + \
             [N * W + i for i in range(N - 1, -1, -1)] + [j * W for j in range(N - 1, 0, -1)]
    base = len(verts)
    for k in border:
        x, y, _ = verts[k]
        verts.append((x, y, -45.0))
    nb = len(border)
    for i in range(nb):
        t0, t1 = border[i], border[(i + 1) % nb]
        faces.append((t1, t0, base + i, base + (i + 1) % nb))
    faces.append(tuple(base + i for i in reversed(range(nb))))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.materials.append(bpy.data.materials['Water'])
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return len(faces)


# ---------------------------------------------------------------- volumes
def _vol_box(name, x0, y0, z0, x1, y1, z1, mat):
    coll = geo.get_coll('FX')
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    mb = geo.MB(name)
    mb.box(x0, y0, z0, x1, y1, z1, mat)
    ob = mb.build(coll)
    ob.visible_shadow = True
    return ob


def mist(lake_density=0.0035, haze_density=0.00011):
    # low heterogeneous mist over the water, pooling in low ground
    t = NT('LakeMist')
    tc = t.n('ShaderNodeTexCoord')
    obj = tc.outputs['Object']
    sep = t.n('ShaderNodeSeparateXYZ', inp={'Vector': obj})
    z = sep.outputs[2]
    hfall = t.math('EXPONENT', t.math('MULTIPLY', t.math('MAXIMUM', z, 0.0), -1.0 / 5.0))
    # concentrate the bank around the promontory and along the far shores, clear near the hero camera
    vd = t.n('ShaderNodeVectorMath', operation='DISTANCE', inp={1: (0.0, -40.0, 0.0)})
    t.l(t.n('ShaderNodeCombineXYZ', inp={0: sep.outputs[0], 1: sep.outputs[1]}).outputs[0], vd.inputs[0])
    near = t.maprange(vd.outputs['Value'], 150.0, 330.0, 3.0, 0.08)
    far = t.maprange(vd.outputs['Value'], 900.0, 1600.0, 0.0, 0.7)
    hfall = t.math('MULTIPLY', hfall, t.math('ADD', near, far))
    n1 = t.noise(obj, 0.006, 4.0, 0.55, dist=0.6).outputs['Fac']
    n2 = t.noise(obj, 0.025, 3.0, 0.5).outputs['Fac']
    patch = t.maprange(t.math('ADD', n1, t.math('MULTIPLY', n2, 0.45)), 0.5, 0.9, 0.02, 1.0)
    dens = t.math('MULTIPLY', t.math('MULTIPLY', hfall, patch), lake_density)
    pv = t.n('ShaderNodeVolumePrincipled', inp={'Color': (0.75, 0.82, 0.9, 1), 'Anisotropy': 0.55})
    t.l(dens, pv.inputs['Density'])
    t.done(None, vol=pv.outputs[0]) if False else None
    t.l(pv.outputs[0], t.out.inputs['Volume'])
    _vol_box('FX_LakeMist', -2600, -2200, -1.0, 2600, 2400, 70.0, 'LakeMist')
    # aerial perspective haze (homogeneous, thins with altitude)
    t = NT('Haze')
    tc = t.n('ShaderNodeTexCoord')
    sep = t.n('ShaderNodeSeparateXYZ', inp={'Vector': tc.outputs['Object']})
    hf = t.math('EXPONENT', t.math('MULTIPLY', t.math('MAXIMUM', sep.outputs[2], 0.0), -1.0 / 650.0))
    dens = t.math('MULTIPLY', hf, haze_density)
    pv = t.n('ShaderNodeVolumePrincipled', inp={'Color': (0.6, 0.72, 0.9, 1), 'Anisotropy': 0.7})
    t.l(dens, pv.inputs['Density'])
    t.l(pv.outputs[0], t.out.inputs['Volume'])
    _vol_box('FX_Haze', -8500, -8300, -1.0, 8500, 8600, 1800.0, 'Haze')


# ---------------------------------------------------------------- lights
LANTERN_GAIN = 5.0


def lanterns(lantern_list, glow_list):
    coll = geo.get_coll('Lanterns', geo.get_coll('Lights'))
    for o in list(coll.objects):
        d = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if d.users == 0:
            bpy.data.lights.remove(d)
    for i, (x, y, z, p) in enumerate(lantern_list):
        ld = bpy.data.lights.new('LanternLight_%03d' % i, 'POINT')
        ld.energy = p * LANTERN_GAIN
        ld.color = (1.0, 0.58, 0.26)
        ld.shadow_soft_size = 0.12
        ob = bpy.data.objects.new('LanternLight_%03d' % i, ld)
        ob.location = (x, y, z)
        coll.objects.link(ob)
    for i, (x, y, z, p, c) in enumerate(glow_list):
        ld = bpy.data.lights.new('InteriorGlow_%02d' % i, 'POINT')
        ld.energy = p
        ld.color = c
        ld.shadow_soft_size = 1.0
        ob = bpy.data.objects.new('InteriorGlow_%02d' % i, ld)
        ob.location = (x, y, z)
        ob.visible_glossy = False
        ob.visible_transmission = False
        coll.objects.link(ob)
    return len(coll.objects)
