"""PASS 5 — night sky, moonlight, lanterns, mist, cameras.

Mood: moonlit night.  The moon sits *behind* the castle as seen from the hero
camera, so the architecture reads as a dark silhouette rim-lit against a teal
halo — the Hogwarts2.jpg composition.  Warm window/lantern glow is the only
warm light in frame.

NOTE: the world deliberately carries **no volume shader**.  A constant-density
world volume integrates along an effectively infinite ray and extinguishes the
background entirely (verified: sky radiance 0.0007 -> 0.53 with it removed).
Atmosphere is instead carried by bounded, height-graded volume boxes.
"""
import bpy, math, importlib, sys, os
import numpy as np
from mathutils import Vector, Matrix

BUILD = "/home/morpheus/Documents/Morpheus-Produktion/Benchmarks/Blender/MiniMax-M3.1-Flash/build"
if BUILD not in sys.path:
    sys.path.insert(0, BUILD)

import hg_lib, hg_np, hg_mat, hg_cfg, hg_land, hg_castle
for m in (hg_lib, hg_np, hg_mat, hg_cfg, hg_land, hg_castle):
    importlib.reload(m)
import hg_lib as L
import hg_mat as M
import hg_cfg as C

MOON_DIR = Vector((-0.46, 0.46, 0.76)).normalized()   # from the scene towards the moon
FILL_DIR = Vector((0.627, -0.440, 0.643)).normalized()  # soft sky fill from camera side
RAKE_DIR = Vector((0.92, 0.10, 0.38)).normalized()    # low side rake from the east
BOUNCE_DIR = Vector((0.854, -0.495, 0.139)).normalized()  # moonlight bounced off the lake
# A second, much lower rake out of the west-south-west.  It travels almost
# parallel to the crag's south face, so every ridge and hollow on the cliff
# gets a lit edge and a shadowed side.  Lit frontally by the sky fill, the
# same rock reads as one smooth, melted mass.
CRAG_RAKE_DIR = Vector((-0.87, -0.44, 0.21)).normalized()
SUN_STRENGTH = 3.30      # moonlight key/rim (the moon is behind the castle)
FILL_STRENGTH = 1.85     # broad cool sky bounce so the shadow side still reads
RAKE_STRENGTH = 0.55     # low side rake that separates the east-facing planes
BOUNCE_STRENGTH = 1.05   # lake bounce that models the crag's camera-facing face
CRAG_RAKE_STRENGTH = 0.68
WORLD_STRENGTH = 1.0     # sky radiance is authored directly in the shader
EXPOSURE = 0.0


def cliff_r(a_deg, z):
    """Radius of the *displaced* cliff face at a bearing and height."""
    T = np.array([[math.radians(a_deg)]])
    Z = np.array([[float(z)]])
    return float(hg_land.crag_radius(T, Z)[0, 0])


def set_moon_from_cam(cam, yaw=8.5, pitch=7.5):
    """Aim the moon `yaw` deg right of the camera centre and `pitch` deg up.

    Keeps the moon in the hero frame no matter how the camera is re-aimed.
    """
    global MOON_DIR
    bpy.context.view_layer.update()
    m = cam.matrix_world.to_3x3()
    right = (m @ Vector((1.0, 0.0, 0.0))).normalized()
    up = (m @ Vector((0.0, 1.0, 0.0))).normalized()
    fwd = (m @ Vector((0.0, 0.0, -1.0))).normalized()
    a, e = math.radians(yaw), math.radians(pitch)
    MOON_DIR = (fwd + right * math.tan(a) + up * math.tan(e)).normalized()
    return MOON_DIR


def build_world():
    """Procedural moonlit night sky: gradient, teal halo, stars, moon, clouds."""
    w = bpy.data.worlds.get("HogwartsSky")
    if w is None:
        w = bpy.data.worlds.new("HogwartsSky")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = M.NN(nt, 'ShaderNodeOutputWorld', (1700, 0))
    bg = M.NN(nt, 'ShaderNodeBackground', (1500, 0))
    bg.inputs['Strength'].default_value = WORLD_STRENGTH
    M.L(nt, bg, 'Background', out, 'Surface')

    # ---------- sky direction ----------
    # NOTE: in a world shader `Incoming` points back *towards* the camera, i.e.
    # it is the negated view direction.  Negate it so Z is up and the dot
    # product with MOON_DIR peaks at the moon.
    geo = M.NN(nt, 'ShaderNodeNewGeometry', (-2000, 0))
    vnorm = M.NN(nt, 'ShaderNodeVectorMath', (-1800, 0), operation='NORMALIZE')
    M.L(nt, geo, 'Incoming', vnorm, 'Vector')
    flip = M.NN(nt, 'ShaderNodeVectorMath', (-1700, 0), operation='SCALE')
    M.L(nt, vnorm.outputs['Vector'], flip, 'Vector')
    flip.inputs['Scale'].default_value = -1.0
    dirv = flip.outputs['Vector']
    sep = M.sepxyz(nt, (-1500, 0), dirv)

    # ---------- moon proximity ----------
    dot = M.NN(nt, 'ShaderNodeVectorMath', (-1600, 560), operation='DOT_PRODUCT')
    M.L(nt, dirv, 'Vector', dot, 0)
    dot.inputs[1].default_value = tuple(MOON_DIR)
    md = dot.outputs['Value']
    # wide atmospheric halo (teal), tight inner glow
    halo_wide = M.maprange(nt, (-1400, 700), md, 0.22, 1.0, 0.0, 1.0)
    halo_wide = M.mathn(nt, (-1200, 700), 'POWER', halo_wide, 1.70)
    halo_tight = M.maprange(nt, (-1400, 520), md, 0.84, 1.0, 0.0, 1.0)
    halo_tight = M.mathn(nt, (-1200, 520), 'POWER', halo_tight, 1.70)
    # the bloom collar hugging the disc itself -- without it the moon is a
    # flat cut-out pasted on the sky
    halo_bloom = M.maprange(nt, (-1400, 640), md, 0.9860, 1.0, 0.0, 1.0)
    halo_bloom = M.mathn(nt, (-1200, 640), 'POWER', halo_bloom, 1.25)
    # the moon disc itself -- a wide, soft limb, otherwise it reads as a
    # hard white circle pasted onto the sky
    disc = M.maprange(nt, (-1400, 360), md, 0.99930, 0.99988, 0.0, 1.0)

    # ---------- base vertical gradient ----------
    elev = M.maprange(nt, (-1400, 0), sep.outputs['Z'], -0.32, 0.90, 0.0, 1.0)
    sky = M.ramp(nt, (-1200, 0), [(0.00, (0.0264, 0.0564, 0.0880, 1)),
                                  (0.26, (0.0404, 0.0946, 0.1452, 1)),
                                  (0.42, (0.0220, 0.0528, 0.0946, 1)),
                                  (0.70, (0.0096, 0.0238, 0.0594, 1)),
                                  (1.00, (0.0036, 0.0096, 0.0308, 1))])
    M.L(nt, elev, 'Result', sky, 'Factor')

    # Teal halo added over the gradient.  NOTE: the density float must be
    # MULTIPLIED into the tint -- linking a float straight into Color2
    # replaces the tint with neutral grey and washes the colour out.
    halo_col = M.mixrgb(nt, (-1000, 700), 1.0, (0.0900, 0.2500, 0.2800, 1),
                        (1.0, 1.0, 1.0, 1))
    halo_col.blend_type = 'MULTIPLY'
    M.L(nt, halo_wide, 'Value', halo_col, 'Color2')
    sky_halo = M.mixrgb(nt, (-800, 300), 1.0, (0, 0, 0, 1), (0, 0, 0, 1))
    sky_halo.blend_type = 'ADD'
    M.L(nt, sky, 'Color', sky_halo, 'Color1')
    M.L(nt, halo_col, 'Color', sky_halo, 'Color2')
    halo2_col = M.mixrgb(nt, (-800, 120), 1.0, (0.2600, 0.5600, 0.6000, 1),
                         (1.0, 1.0, 1.0, 1))
    halo2_col.blend_type = 'MULTIPLY'
    M.L(nt, halo_tight, 'Value', halo2_col, 'Color2')
    sky_halo2 = M.mixrgb(nt, (-600, 200), 1.0, (0, 0, 0, 1), (0, 0, 0, 1))
    sky_halo2.blend_type = 'ADD'
    M.L(nt, sky_halo, 'Color', sky_halo2, 'Color1')
    M.L(nt, halo2_col, 'Color', sky_halo2, 'Color2')
    # bloom collar: a bright ring of scattered light around the disc
    bloom_col = M.mixrgb(nt, (-600, 420), 1.0, (0.5200, 0.6200, 0.6800, 1),
                         (1.0, 1.0, 1.0, 1))
    bloom_col.blend_type = 'MULTIPLY'
    M.L(nt, halo_bloom, 'Value', bloom_col, 'Color2')
    sky_bloom = M.mixrgb(nt, (-400, 400), 1.0, (0, 0, 0, 1), (0, 0, 0, 1))
    sky_bloom.blend_type = 'ADD'
    M.L(nt, sky_halo2, 'Color', sky_bloom, 'Color1')
    M.L(nt, bloom_col, 'Color', sky_bloom, 'Color2')

    # ---------- stars ----------
    smap = M.mapping(nt, (-1600, -460), dirv, scale=(190.0, 190.0, 190.0))
    sv = M.voronoi(nt, (-1400, -460), 1.0, 1.0, 'F1', smap.outputs['Vector'])
    sdist = M.ramp(nt, (-1200, -460), [(0.0, (1, 1, 1, 1)), (0.09, (0, 0, 0, 1))])
    M.L(nt, sv, 'Distance', sdist, 'Factor')
    srand = M.NN(nt, 'ShaderNodeSeparateXYZ', (-1400, -700))
    M.L(nt, sv, 'Color', srand, 'Vector')
    sbr = M.maprange(nt, (-1200, -700), srand.outputs['X'], 0.0, 1.0, 0.0, 1.0)
    sbr2 = M.mathn(nt, (-1000, -700), 'MULTIPLY', sbr, 3.4)
    stars = M.mathn(nt, (-800, -560), 'MULTIPLY', sdist.outputs['Color'], sbr2)
    hz = M.maprange(nt, (-1000, -340), sep.outputs['Z'], -0.02, 0.18, 0.0, 1.0)
    stars = M.mathn(nt, (-600, -460), 'MULTIPLY', stars, hz)
    moonprox = M.maprange(nt, (-1000, 300), md, 0.9880, 0.99990, 1.0, 0.0)
    stars = M.mathn(nt, (-420, -460), 'MULTIPLY', stars, moonprox)
    starpow = M.mathn(nt, (-240, -460), 'POWER', stars, 0.50)
    starcol = M.mixrgb(nt, (-60, -460), 1.0, (0.26, 0.30, 0.40, 1), (1.0, 1.0, 1.0, 1))
    starcol.blend_type = 'MULTIPLY'
    M.L(nt, starpow, 'Value', starcol, 'Color2')

    # ---------- cloud deck ----------
    cmap = M.mapping(nt, (-1600, -980), dirv, scale=(2.6, 2.6, 7.0))
    cn = M.noise(nt, (-1400, -980), 1.9, 8.0, 0.62, 0.45, cmap.outputs['Vector'])
    # A single smooth noise thresholded hard gives folded-paper shapes, not
    # cloud: the edges come out as hard creases with a bright rim.  A second,
    # finer field breaks the outline up, and the ramp is kept wide so the
    # density fades in rather than stopping dead.
    cn2 = M.noise(nt, (-1400, -1150), 8.0, 6.0, 0.55, 0.30, cmap.outputs['Vector'])
    csum = M.mathn(nt, (-1300, -1040), 'ADD', cn.outputs['Fac'], cn2.outputs['Fac'])
    cnf = M.mathn(nt, (-1300, -930), 'MULTIPLY', csum.outputs['Value'], 0.66)
    cr = M.ramp(nt, (-1200, -980), [(0.34, (0, 0, 0, 1)), (0.86, (1, 1, 1, 1))])
    M.L(nt, cnf, 'Value', cr, 'Factor')
    cband = M.maprange(nt, (-1200, -1180), sep.outputs['Z'], -0.05, 0.10, 0.0, 1.0)
    ctop = M.maprange(nt, (-1200, -1280), sep.outputs['Z'], 0.92, 0.35, 0.0, 1.0)
    clouds = M.mathn(nt, (-1000, -1040), 'MULTIPLY', cr.outputs['Color'], cband)
    clouds = M.mathn(nt, (-820, -1040), 'MULTIPLY', clouds, ctop)
    # clouds pick up the moon: teal near it, near-black away from it
    lit_amt = M.maprange(nt, (-1000, -1240), md, 0.30, 0.98, 0.0, 1.0)
    cloud_col = M.mixrgb(nt, (-640, -1080), 0.5, (0.0030, 0.0060, 0.0120, 1),
                         (0.0320, 0.0720, 0.0800, 1))
    M.L(nt, lit_amt, 'Result', cloud_col, 'Factor')
    cloud_layer = M.mixrgb(nt, (-400, -900), 0.5, (0, 0, 0, 1), (0, 0, 0, 1))
    M.L(nt, sky_bloom, 'Color', cloud_layer, 'Color1')
    M.L(nt, cloud_col, 'Color', cloud_layer, 'Color2')
    M.L(nt, clouds, 'Value', cloud_layer, 'Factor')
    # silver lining on the cloud edge nearest the moon
    cspec = M.mathn(nt, (-820, -1320), 'MULTIPLY', cr.outputs['Color'], halo_tight)
    cspec = M.mathn(nt, (-640, -1320), 'MULTIPLY', cspec, 0.30)
    edge = M.mixrgb(nt, (-220, -1200), 1.0, (0.0400, 0.0950, 0.1050, 1), (1.0, 1.0, 1.0, 1))
    edge.blend_type = 'MULTIPLY'
    M.L(nt, cspec, 'Value', edge, 'Color2')
    with_edge = M.mixrgb(nt, (0, -900), 1.0, (0, 0, 0, 1), (0, 0, 0, 1))
    with_edge.blend_type = 'ADD'
    M.L(nt, cloud_layer, 'Color', with_edge, 'Color1')
    M.L(nt, edge, 'Color', with_edge, 'Color2')

    # ---------- stars sit on top of the cloud deck ----------
    sky_star = M.mixrgb(nt, (200, -300), 1.0, (0, 0, 0, 1), (0, 0, 0, 1))
    sky_star.blend_type = 'ADD'
    M.L(nt, with_edge, 'Color', sky_star, 'Color1')
    M.L(nt, starcol, 'Color', sky_star, 'Color2')

    # ---------- the moon ----------
    mm = M.mapping(nt, (-1400, -140), dirv, scale=(22.0, 22.0, 22.0))
    mtex = M.voronoi(nt, (-1200, -140), 1.0, 1.0, 'F1', mm.outputs['Vector'])
    mtexr = M.ramp(nt, (-1000, -140), [(0.0, (0.55, 0.57, 0.64, 1)),
                                       (0.55, (1.0, 0.99, 0.96, 1))])
    M.L(nt, mtex, 'Distance', mtexr, 'Factor')
    # mottled surface, then masked by the disc so it only exists on the moon
    mottled = M.mixrgb(nt, (-700, -140), 1.0, (3.1, 3.1, 3.05, 1), (1, 1, 1, 1))
    mottled.blend_type = 'MULTIPLY'
    M.L(nt, mtexr, 'Color', mottled, 'Color2')
    moondisc = M.mixrgb(nt, (400, -100), 1.0, (1, 1, 1, 1), (1, 1, 1, 1))
    moondisc.blend_type = 'MULTIPLY'
    M.L(nt, mottled, 'Color', moondisc, 'Color1')
    M.L(nt, disc, 'Result', moondisc, 'Color2')
    moonfinal = M.mixrgb(nt, (600, -100), 1.0, (0, 0, 0, 1), (0, 0, 0, 1))
    moonfinal.blend_type = 'ADD'
    M.L(nt, sky_star, 'Color', moonfinal, 'Color1')
    M.L(nt, moondisc, 'Color', moonfinal, 'Color2')
    M.L(nt, moonfinal, 'Color', bg, 'Color')
    return w


def build_lights():
    c = L.coll("Lights")
    for o in list(c.objects):
        bpy.data.objects.remove(o, do_unlink=True)

    # --- moonlight (key, backlights the castle from the hero camera) ---
    d = bpy.data.lights.new("Moonlight", 'SUN')
    d.energy = SUN_STRENGTH
    d.angle = math.radians(0.72)
    d.color = (0.62, 0.74, 1.0)
    sun = bpy.data.objects.new("Moonlight", d)
    c.objects.link(sun)
    sun.location = tuple(MOON_DIR * 900)
    sun.rotation_euler = (-MOON_DIR).to_track_quat('-Z', 'Y').to_euler()

    # --- soft sky fill so the shadow side still reads ---
    fd = bpy.data.lights.new("SkyFill", 'SUN')
    fd.energy = FILL_STRENGTH
    fd.angle = math.radians(42.0)
    fd.color = (0.34, 0.52, 0.92)
    fill = bpy.data.objects.new("SkyFill", fd)
    c.objects.link(fill)
    fill.location = tuple(FILL_DIR * 900)
    fill.rotation_euler = (-FILL_DIR).to_track_quat('-Z', 'Y').to_euler()

    # --- low rake from the east: separates the east-facing planes from the
    #     south faces so the massing reads instead of flattening out ---
    rd = bpy.data.lights.new("SideRake", 'SUN')
    rd.energy = RAKE_STRENGTH
    rd.angle = math.radians(24.0)
    rd.color = (0.44, 0.60, 0.90)
    rake = bpy.data.objects.new("SideRake", rd)
    c.objects.link(rake)
    rake.location = tuple(RAKE_DIR * 900)
    rake.rotation_euler = (-RAKE_DIR).to_track_quat('-Z', 'Y').to_euler()

    # --- grazing rake across the crag's south-west face --------------------
    # Almost parallel to the cliff, so the rock is modelled by its own
    # relief instead of by a flat frontal wash.
    gd = bpy.data.lights.new("CragRake", 'SUN')
    gd.energy = CRAG_RAKE_STRENGTH
    gd.angle = math.radians(9.0)
    gd.color = (0.44, 0.60, 0.92)
    grake = bpy.data.objects.new("CragRake", gd)
    c.objects.link(grake)
    grake.location = tuple(CRAG_RAKE_DIR * 900)
    grake.rotation_euler = (-CRAG_RAKE_DIR).to_track_quat('-Z', 'Y').to_euler()

    # --- moonlight bounced off the lake: a very low, cool light from the
    #     camera side.  The moon itself is behind the castle, so without this
    #     the whole crag face turned into a featureless black slab. ---
    bd = bpy.data.lights.new("LakeBounce", 'SUN')
    bd.energy = BOUNCE_STRENGTH
    bd.angle = math.radians(30.0)
    bd.color = (0.38, 0.55, 0.86)
    bounce = bpy.data.objects.new("LakeBounce", bd)
    c.objects.link(bounce)
    bounce.location = tuple(BOUNCE_DIR * 900)
    bounce.rotation_euler = (-BOUNCE_DIR).to_track_quat('-Z', 'Y').to_euler()

    # --- warm window/lantern fill lights (a few real lamps, rest is emissive) ---
    lamp_specs = []
    # viaduct parapet lamps
    x0 = C.VIA_X0
    for i in range(C.VIA_ARCHES + 1):
        x = x0 - C.VIA_PIER * .5 + i * (C.VIA_SPAN + C.VIA_PIER)
        lamp_specs.append((x, C.VIA_Y - 2.8, C.PLATEAU_Z + 5.6, 190.0))
        lamp_specs.append((x, C.VIA_Y + 2.8, C.PLATEAU_Z + 5.6, 190.0))
    # boathouse + stair + courtyards
    lamp_specs.append((C.BOAT_X, C.BOAT_Y - 9.0, 7.0, 210.0))
    # The boathouse floods the cliff it is built into.  Without this the
    # south-east wall behind the boat house is a dead black slab; with it
    # the rock carries a warm pool at its foot that fades up into the cold
    # moonlight, which is what gives the cliff its depth.
    lamp_specs.append((C.BOAT_X - 1.0, C.BOAT_Y - 11.0, 11.0, 1150.0))
    # the lantern at the head of the boathouse jetty: it lights the moored
    # boat and lays a warm streak across the black water in the foreground
    lamp_specs.append((C.BOAT_X + 2.6, C.BOAT_Y - 21.4, 6.0, 430.0))
    # the rowboat's own bow lantern
    lamp_specs.append((C.BOAT_X + 4.9, C.BOAT_Y - 16.7, 1.35, 80.0))
    # the jetty lantern: a warm anchor in the hero foreground
    lamp_specs.append((C.BOAT_X - 15.0, C.BOAT_Y - 36.0, 4.8, 280.0))
    lamp_specs.append((C.BOAT_X - 12.0, C.BOAT_Y + 12.0, 26.0, 180.0))
    lamp_specs.append((58.0, -30.0, C.PLATEAU_Z + 3.0, 220.0))
    lamp_specs.append((-20.0, -40.0, C.PLATEAU_Z + 3.0, 220.0))
    lamp_specs.append((30.0, 30.0, C.PLATEAU_Z + 4.0, 180.0))
    # warm light that models the architecture: wall sconces, gate lanterns,
    # courtyard braziers.  Without these the castle is a flat silhouette.
    lamp_specs.append((-40.0, -53.0, C.PLATEAU_Z + 12.0, 900.0))   # hall S wall, E end
    lamp_specs.append((-67.0, -53.0, C.PLATEAU_Z + 12.0, 900.0))   # hall S wall, W end
    lamp_specs.append((-29.0, -34.0, C.PLATEAU_Z + 13.0, 1050.0))   # hall E wall
    lamp_specs.append((-29.0, 30.0, C.PLATEAU_Z + 13.0, 1050.0))
    lamp_specs.append((-29.0, 58.0, C.PLATEAU_Z + 13.0, 900.0))
    lamp_specs.append((C.GH_CX, C.GH_CY + 58.0, C.PLATEAU_Z + 15.0, 950.0))
    lamp_specs.append((86.0, -44.0, C.PLATEAU_Z + 4.0, 520.0))      # gatehouse
    lamp_specs.append((86.0, -32.0, C.PLATEAU_Z + 4.0, 520.0))
    lamp_specs.append((8.0, 34.0, C.PLATEAU_Z + 4.0, 620.0))        # courtyard
    lamp_specs.append((34.0, 6.0, C.PLATEAU_Z + 4.0, 620.0))
    lamp_specs.append((26.0, -34.0, C.PLATEAU_Z + 4.0, 620.0))      # clock base
    lamp_specs.append((54.0, 22.0, C.PLATEAU_Z + 3.0, 520.0))       # east tower
    # a lamp inside each glasshouse -- the Potmorec end is always warm
    for g in C.greenhouse_layout():
        lamp_specs.append((g["cx"], g["cy"], C.TERRACE_Z + 2.6, 150.0))
    lamp_specs.append((C.BOAT_X - 22.0, C.BOAT_Y + 4.0, 16.0, 420.0))  # cliff stair
    # a lamp on the switchback stair itself, wherever the crag put it
    for (a_deg, zz, en) in ((-46.5, 9.0, 520.0), (-44.5, 30.0, 520.0),
                            (-42.0, 50.0, 460.0)):
        r = cliff_r(a_deg, zz) + 3.2
        a = math.radians(a_deg)
        lamp_specs.append((r * math.cos(a), r * math.sin(a), zz + 3.0, en))
    for i, (lx, ly, lz, en) in enumerate(lamp_specs):
        dd = bpy.data.lights.new("Lamp_%02d" % i, 'POINT')
        dd.energy = en
        dd.color = (1.0, 0.50, 0.18)
        # A point light's radius is ALSO the size of its specular highlight,
        # so a 1.6 m "soft" lamp reflected in the lake came out as a 1.6 m
        # cream-coloured disc floating on the water.  Keep the radius small;
        # the shadows stay soft because the moonlight, fill and rake are SUN
        # lamps carrying their own angular sizes.
        dd.shadow_soft_size = 0.35 if en < 300.0 else (1.1 if en > 1000.0 else 0.6)
        o = bpy.data.objects.new("Lamp_%02d" % i, dd)
        c.objects.link(o)
        o.location = (lx, ly, lz)


def build_mist():
    """Bounded, height-graded mist over the lake, the gorge and the upper air.

    Every box carries a radial density falloff so the volume reaches zero
    density before its side wall — otherwise camera rays that stop hitting
    the wall leave a hard horizontal seam across the sky.
    """
    c = L.coll("FX")
    for o in list(c.objects):
        bpy.data.objects.remove(o, do_unlink=True)

    mist_lake = M.m_mist('M_Mist', col=(0.085, 0.130, 0.175), density=0.00055,
                         z_top=19.0, z_peak=2.5, z_bot=-8.0, floor=0.30,
                         nscale=0.010, rough=0.62,
                         r_in=820.0, r_out=1260.0, r_cx=0.0, r_cy=0.0)
    mist_gorge = M.m_mist('M_MistGorge', col=(0.080, 0.115, 0.155), density=0.00040,
                          z_top=44.0, z_peak=14.0, z_bot=6.0, floor=0.25,
                          nscale=0.016, rough=0.55,
                          r_in=300.0, r_out=390.0, r_cx=240.0, r_cy=-20.0)
    mist_air = M.m_mist('M_MistAir', col=(0.070, 0.110, 0.150), density=0.00010,
                        z_top=230.0, z_peak=45.0, z_bot=40.0, floor=0.0,
                        nscale=0.006, rough=0.5,
                        r_in=1900.0, r_out=2500.0, r_cx=0.0, r_cy=0.0)

    def box(name, x0, x1, y0, y1, z0, z1, mat):
        mb = L.MB()
        mb.add(*L.p_box_minmax(x0, y0, z0, x1, y1, z1), mat=0)
        o = mb.to_object(name, c, [mat], fix_normals=False)
        o.visible_shadow = False
        return o

    box("Mist_Lake", -1320, 1320, -1320, 1320, -8.0, 20.0, mist_lake)
    box("Mist_Gorge", 100.0, 400.0, -420.0, 380.0, 2.0, 26.0, mist_gorge)
    box("Mist_Air", -2600, 2600, -2600, 2600, 40.0, 240.0, mist_air)


def build_cameras():
    c = L.coll("Cameras")
    for o in list(c.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    cams = []
    # HERO — low over the lake to the south-east.  A 35 mm lens on a wide
    # arc is what makes the composition work: at 44 mm the castle's
    # silhouette alone ate two thirds of the frame width and left no sky for
    # the backdrop massif or the moon.  The aim point is pushed to
    # screen-right of the castle so the massing sits left of centre, the
    # backdrop hill fills the left third and the moon has clear sky on the
    # right — the Hogwarts2.jpg composition.
    cams.append(L.place_cam("Cam_Hero", c, target=(12.0, 6.0, 68.0), dist=400.0,
                            azim=20.0, z=14.0, lens=42.0))
    # AERIAL — elevated three-quarter over the gorge, ridges on the horizon.
    cams.append(L.place_cam("Cam_Aerial", c, target=(6.0, 4.0, 92.0), dist=600.0,
                            azim=39.0, z=158.0, lens=42.0))
    # BOATHOUSE -- out on the water south-east of the boathouse at eye
    # level over the open inlet: the lit hull house left of centre with its
    # great tracery door, the switchback stair and the cliff mass above it,
    # the viaduct's lantern line receding on the right, the jetty running
    # out of the bottom of the frame.
    cams.append(L.place_cam("Cam_Boathouse", c, target=(72.0, -100.0, 10.0),
                            dist=30.5, azim=-31.6, z=3.0, lens=24.0))
    # VIADUCT — from the gorge floor beneath the arcade, arches receding east.
    cams.append(L.place_cam("Cam_Viaduct", c, target=(205.0, -46.0, 46.0),
                            dist=118.0, azim=33.0, z=12.0, lens=35.0))
    # DETAIL 1 — the Great Hall's north-east corner: rose window, stepped
    # buttresses, pinnacles and corner turret, raked by the moon.
    # DETAIL 1 -- the Great Hall's south wall: rose window, lancet bays,
    # stepped buttresses and a corner turret, washed by warm sconces.
    cams.append(L.place_cam("Cam_Detail_Wall", c, target=(-54.0, -56.0, 71.0),
                            dist=44.0, azim=25.0, z=C.PLATEAU_Z + 13.0,
                            lens=48.0))
    # DETAIL 2 -- the boathouse at the waterline: the lit boat door in the
    # middle of the frame with its heavy glazing bars, the moored rowing
    # boat in the near foreground with its bow lantern and the lantern's
    # reflection in the black water.  The first framing was a wide shot
    # that gave a third of the frame to a blank stretch of the boathouse's
    # east wall; this one is tighter and lower, and drops the lens a stop
    # to keep the water and the reflection in the bottom of the frame.
    cams.append(L.place_cam("Cam_Detail_Boathouse", c,
                            target=(74.0, -103.0, 3.2),
                            dist=23.0, azim=25.4, z=2.6, lens=31.0))
    # DETAIL 3 -- the clock tower: the readable dial, the belfry openings
    # and the spire against the moonlit sky.  The SOUTH dial is hemmed in by
    # the east range's roof and by the Great Hall, so the shot is taken from
    # the north, where the moon rakes the dial face almost square on.
    cams.append(L.place_cam("Cam_Detail_Turret", c,
                            target=(C.T_CLOCK[0], C.T_CLOCK[1] + 9.85, 81.0),
                            dist=62.0, azim=170.0, z=86.0, lens=78.0))
    bpy.context.scene.camera = cams[0]
    return cams


def main():
    build_cameras()
    set_moon_from_cam(bpy.context.scene.camera, yaw=14.0, pitch=8.0)
    print("moon dir:", tuple(round(v, 3) for v in MOON_DIR))
    build_world()
    build_lights()
    build_mist()
    scn = bpy.context.scene
    scn.view_settings.view_transform = 'AgX'
    for want in ('AgX - Punchy', 'Punchy', 'AgX - Medium High Contrast',
                 'Medium High Contrast'):
        try:
            scn.view_settings.look = want
            break
        except Exception:
            continue
    print("view look:", scn.view_settings.look)
    scn.view_settings.exposure = EXPOSURE
    scn.cycles.max_bounces = 12
    scn.cycles.diffuse_bounces = 4
    scn.cycles.glossy_bounces = 6
    scn.cycles.transmission_bounces = 8
    scn.cycles.volume_bounces = 2
    scn.cycles.transparent_max_bounces = 12
    scn.cycles.caustics_reflective = False
    scn.cycles.caustics_refractive = False
    scn.cycles.use_adaptive_sampling = True
    scn.cycles.adaptive_threshold = 0.006
    scn.cycles.sample_clamp_indirect = 8.0
    scn.render.film_transparent = False
    print("lighting done")


if __name__ == "__main__":
    main()
