"""World (moonlit sky), key/fill lights, colour management."""
import bpy
import math
from mathutils import Vector
from hw_nodes import NB
import hw_scene as S

# moon position: azimuth measured from north (+Y) towards east (+X), elevation above horizon
MOON_AZ = 12.0
MOON_EL = 19.5
MOON_RADIUS_DEG = 1.10


def moon_vec(az=None, el=None):
    az = math.radians(MOON_AZ if az is None else az)
    el = math.radians(MOON_EL if el is None else el)
    return Vector((math.cos(el) * math.sin(az), math.cos(el) * math.cos(az), math.sin(el)))


def aim_light(obj, direction):
    """Point a sun lamp so that light travels along -direction (direction = towards the source)."""
    obj.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()


def build_world(sky_strength=1.0, cloud_cover=0.62, moon_strength=16.0, seed=3.0):
    w = bpy.data.worlds.get('World') or bpy.data.worlds.new('World')
    bpy.context.scene.world = w
    nb = NB(w)
    M = moon_vec()
    tc = nb.texcoord()
    V = tc.outputs['Generated']
    Vn = nb.vmath('NORMALIZE', V).outputs[0]
    z = nb.sepxyz(Vn).outputs[2]
    xv = nb.sepxyz(Vn).outputs[0]
    yv = nb.sepxyz(Vn).outputs[1]
    Mc = nb.rgb((0, 0, 0))
    mv = nb.combxyz(M.x, M.y, M.z)
    dot = nb.vmath('DOT_PRODUCT', Vn, mv).outputs[1]
    ang = nb.math('ARCCOSINE', nb.clamp01(dot) if False else nb.math('MINIMUM', nb.math('MAXIMUM', dot, -1.0), 1.0))
    # ------------------------------------------------ base gradient
    grad = nb.ramp(nb.math('MAXIMUM', z, 0.0), [(0.0, (0.032, 0.066, 0.086)), (0.07, (0.017, 0.040, 0.066)),
                                                (0.30, (0.0055, 0.0135, 0.036)), (1.0, (0.0015, 0.0035, 0.012))])
    below = nb.smooth(z, 0.0, -0.05)
    sky = nb.mix(below, grad, (0.006, 0.012, 0.018, 1.0))
    # glow around the moon (large, soft) also acts as ambient sky light
    a2 = nb.mul(ang, ang)
    halo1 = nb.math('EXPONENT', nb.mul(a2, -1.0 / (0.13 ** 2)))
    halo2 = nb.math('EXPONENT', nb.mul(a2, -1.0 / (0.42 ** 2)))
    halo3 = nb.math('EXPONENT', nb.mul(a2, -1.0 / (1.1 ** 2)))
    halo = nb.add(nb.add(nb.mul(halo1, 0.62), nb.mul(halo2, 0.09)), nb.mul(halo3, 0.012))
    halo_col = nb.mix(halo, (0, 0, 0, 1), (0.30, 0.55, 0.72, 1.0))
    sky = nb.mix(1.0, sky, halo_col, blend='ADD')
    # ------------------------------------------------ clouds (projected planes)
    den = nb.math('MAXIMUM', nb.add(z, 0.17), 0.06)
    cx = nb.math('DIVIDE', xv, den)
    cy = nb.math('DIVIDE', yv, den)
    cp = nb.combxyz(nb.mul(cx, 1.05), nb.mul(cy, 1.05), seed)
    warpn = nb.noise(cp, scale=0.9, detail=3, rough=0.5, out='Color')
    cpw = nb.vmath('ADD', cp, nb.vmath('SCALE', nb.vmath('SUBTRACT', warpn, (0.5, 0.5, 0.5)).outputs[0], scale=0.9).outputs[0]).outputs[0]
    c1 = nb.noise(cpw, scale=1.5, detail=6, rough=0.56)
    c2 = nb.noise(nb.mapping(cpw, scale=(0.35, 1.6, 1.0)), scale=2.5, detail=4, rough=0.5)
    cload = nb.add(nb.mul(c1, 0.78), nb.mul(c2, 0.30))
    lo = 0.60 - 0.22 * cloud_cover
    cov = nb.smooth(cload, lo, lo + 0.27)
    horizon_fade = nb.smooth(z, 0.0, 0.05)
    cov = nb.mul(cov, horizon_fade)
    thin = nb.mul(nb.mul(cov, nb.sub(1.0, cov)), 4.0)
    litdot = nb.math('POWER', nb.math('MAXIMUM', dot, 0.0), 5.0)
    lit_wide = nb.math('POWER', nb.math('MAXIMUM', dot, 0.0), 1.6)
    cloud_dark = (0.008, 0.016, 0.030, 1.0)
    cloud_mid = nb.mix(nb.smooth(c1, 0.4, 0.8), (0.010, 0.020, 0.036, 1.0), (0.020, 0.036, 0.058, 1.0))
    cloud_mid = nb.mix(nb.mul(nb.math('POWER', nb.math('MAXIMUM', dot, 0.0), 2.4), 0.60), cloud_mid, (0.085, 0.135, 0.19, 1.0))
    silver = (0.30, 0.44, 0.52, 1.0)
    glow_amt = nb.clamp01(nb.add(nb.mul(nb.mul(thin, nb.add(0.10, nb.mul(litdot, 2.4))), 1.5), nb.mul(lit_wide, 0.08)))
    ccol = nb.mix(glow_amt, cloud_mid, silver)
    # ------------------------------------------------ moon + stars (camera only)
    disc = nb.smooth(ang, math.radians(MOON_RADIUS_DEG) + 0.0018, math.radians(MOON_RADIUS_DEG) - 0.0006)
    tang = nb.vmath('SUBTRACT', Vn, nb.vmath('SCALE', mv, scale=dot).outputs[0]).outputs[0]
    maria = nb.smooth(nb.noise(nb.vmath('SCALE', tang, scale=42.0).outputs[0], scale=1.0, detail=5, rough=0.6), 0.42, 0.62)
    crat = nb.noise(nb.vmath('SCALE', tang, scale=260.0).outputs[0], scale=1.0, detail=3, rough=0.6)
    moon_tone = nb.sub(1.0, nb.add(nb.mul(maria, 0.26), nb.mul(crat, 0.10)))
    moon_base = nb.mix(nb.mul(maria, 0.7), (1.0, 0.96, 0.87, 1.0), (0.72, 0.75, 0.80, 1.0))
    moon_rgb = nb.vmath('SCALE', moon_base, scale=nb.mul(moon_tone, moon_strength)).outputs[0]
    sv = nb.vmath('SCALE', Vn, scale=1.0).outputs[0]
    star_v = nb.voronoi(sv, scale=130.0, rand=1.0, feature='F1', out='Distance')
    star_r = nb.rgb2bw(nb.voronoi(sv, scale=130.0, rand=1.0, feature='F1', out='Color'))
    star_on = nb.smooth(star_r, 0.90, 0.995)
    star_pt = nb.smooth(star_v, 0.06, 0.0)
    star = nb.mul(nb.mul(star_on, star_pt), nb.smooth(z, -0.01, 0.12))
    star_col = nb.mix(nb.noise(sv, scale=90.0, detail=1), (0.75, 0.85, 1.0, 1.0), (1.0, 0.92, 0.8, 1.0))
    trans = nb.sub(1.0, nb.clamp01(nb.mul(cov, 1.15)))
    starlight = nb.mul(nb.mul(star, nb.mul(trans, nb.sub(1.0, nb.clamp01(nb.mul(halo, 2.0))))), 420.0)
    stars_rgb = nb.vmath('SCALE', star_col, scale=starlight).outputs[0]
    moon_vis = nb.mul(disc, nb.add(0.10, nb.mul(trans, 0.90)))
    cam_sky = nb.mix(nb.clamp01(nb.mul(cov, 0.96)), sky, ccol)
    cam_sky = nb.mix(1.0, cam_sky, stars_rgb, blend='ADD')
    cam_sky = nb.mix(moon_vis, cam_sky, moon_rgb)
    # non-camera rays (lighting): same sky without the tiny bright details
    amb_sky = nb.mix(nb.clamp01(nb.mul(cov, 0.96)), sky, ccol)
    lp = nb.lightpath()
    is_cam = lp.outputs['Is Camera Ray']
    col = nb.mix(is_cam, amb_sky, cam_sky)
    bg = nb.node('ShaderNodeBackground')
    nb._in(bg, 'Color', col)
    bg.inputs['Strength'].default_value = sky_strength
    out = nb.node('ShaderNodeOutputWorld')
    nb.links.new(bg.outputs[0], out.inputs['Surface'])
    return w


def ensure_sun(name, strength, color, angle_deg, direction, coll='Lights'):
    o = bpy.data.objects.get(name)
    if o is None:
        l = bpy.data.lights.new(name, 'SUN')
        o = bpy.data.objects.new(name, l)
        S.ensure_collection(coll).objects.link(o)
    o.data.energy = strength
    o.data.color = color
    o.data.angle = math.radians(angle_deg)
    aim_light(o, direction)
    return o


def build_lights(key=2.4, fill=1.6):
    moon = moon_vec()
    ensure_sun('Moon_Key', key, (0.62, 0.74, 1.0), 3.1, moon)
    # cool sky fill raking in from the moon side (east-south-east, low): models the south faces and the crag
    fill_dir = moon_vec(az=110.0, el=27.0)
    ensure_sun('Sky_Fill', fill, (0.30, 0.44, 0.86), 24.0, fill_dir)


def set_color_management(exposure=0.4, look='AgX - Medium High Contrast', view='AgX'):
    sc = bpy.context.scene
    vs = sc.view_settings
    try:
        vs.view_transform = view
    except TypeError:
        vs.view_transform = 'Standard'
    try:
        vs.look = look
    except TypeError:
        pass
    vs.exposure = exposure
    vs.gamma = 1.0
    sc.display_settings.display_device = 'sRGB'
    return vs.view_transform
