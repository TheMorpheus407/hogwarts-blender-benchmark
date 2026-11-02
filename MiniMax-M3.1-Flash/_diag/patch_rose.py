"""Replace m_rose_glass in hg_mat.py with a leaded-panel mosaic version."""
import re

P = "/home/morpheus/Documents/Morpheus-Produktion/Benchmarks/Blender/MiniMax-M3.1-Flash/build/hg_mat.py"
s = open(P).read()

start = s.index("def m_rose_glass(")
end = s.index("def m_clock_face(")

NEW = '''def m_rose_glass(name='M_RoseGlass'):
    """Stained glass for the great rose window: a mosaic of leaded panels.

    The rose window used the ordinary window glass, and because every
    window is one object with one random value the whole seven metre disc
    came out as a single flat saturated orange decal pasted on the wall.
    A rose window is a patchwork of coloured panels, so this one is built
    from the polar coordinates of the opening.

    Four things have to be right for that to come out as a rose window and
    not as a test pattern:

    * The disc is built in the XZ plane -- every window profile in this
      library is an (x, z) polygon extruded through Y -- so the polar
      coordinates have to be taken from X and Z.  Reading Y instead meant
      the "angle" was measured across the thickness of the glass, and the
      whole window came out as vertical rainbow stripes.
    * The panel grid has to agree with the TRACERY.  The glass had twelve
      sectors while the stonework has eight principal spokes, so the
      colours ran across the stone instead of with it, and the window read
      as a pinwheel.  There are eight sectors here, phased so their edges
      land exactly on the spokes, and each is cut into three lights.
    * The panels have to be SMALL.  Sixteen concentric rings times eight
      sectors times three lights is nearly two hundred pieces of glass.
    * The colour has to be a property of the PANEL, not of the position
      inside it, and it has to be WEIGHTED.  A palette of eight evenly
      spaced primaries gave every eighth panel a different primary and
      the window came out as a colour wheel.  Medieval glass is mostly
      cobalt and ruby with a little amber and green, so the ramp is
      weighted towards the blues and the reds.
    """
    m, nt, out = newmat(name)
    tc = NN(nt, 'ShaderNodeTexCoord', (-2200, 0))
    sep = NN(nt, 'ShaderNodeSeparateXYZ', (-2020, 0))
    L(nt, tc.outputs['Generated'], 'Vector', sep, 'Vector')
    cx = mathn(nt, (-1840, 160), 'SUBTRACT', sep.outputs['X'], 0.5)
    cy = mathn(nt, (-1840, -40), 'SUBTRACT', sep.outputs['Z'], 0.5)
    x2 = mathn(nt, (-1660, 160), 'POWER', cx, 2.0)
    y2 = mathn(nt, (-1660, -40), 'POWER', cy, 2.0)
    ss = mathn(nt, (-1480, 60), 'ADD', x2, y2)
    rad = mathn(nt, (-1300, 60), 'SQRT', ss)
    ang = mathn(nt, (-1300, -220), 'ARCTAN2', cy, cx)
    # --- the panel grid ---------------------------------------------------
    # Eight sectors, phased so that their edges fall on the eight principal
    # spokes of the stone tracery (the spokes sit at 2*pi*i/8 + pi/8).
    ang01 = mathn(nt, (-1120, -220), 'MULTIPLY_ADD', ang, 0.15915494, -0.0625)
    sectf = mathn(nt, (-940, -220), 'MULTIPLY', ang01, 8.0)
    secti = mathn(nt, (-760, -360), 'FLOOR', sectf)
    sf = mathn(nt, (-760, -220), 'FRACT', sectf)
    # sixteen concentric rings
    ringf = mathn(nt, (-940, 60), 'MULTIPLY', rad, 16.0)
    ringi = mathn(nt, (-760, 60), 'FLOOR', ringf)
    rf = mathn(nt, (-760, 240), 'FRACT', ringf)
    # three lights inside every sector
    subf = mathn(nt, (-580, -220), 'MULTIPLY', sf, 3.0)
    subi = mathn(nt, (-400, -360), 'FLOOR', subf)
    subfr = mathn(nt, (-400, -220), 'FRACT', subf)
    # --- one identity per panel ------------------------------------------
    a1 = mathn(nt, (-220, -460), 'MULTIPLY', ringi, 24.0)
    a2 = mathn(nt, (-40, -460), 'MULTIPLY', secti, 3.0)
    a3 = mathn(nt, (140, -460), 'ADD', a1, a2)
    idx = mathn(nt, (320, -460), 'ADD', a3, subi)
    h1 = mathn(nt, (500, -460), 'MULTIPLY', idx, 12.9898)
    h2 = mathn(nt, (680, -460), 'SINE', h1)
    h3 = mathn(nt, (860, -460), 'MULTIPLY', h2, 43758.5453)
    h4 = mathn(nt, (1040, -460), 'FRACT', h3)
    # The middle of a rose window is a deep cool field, not a bag of
    # sweets: the inner rings are biased into the blue end of the palette.
    inner = maprange(nt, (320, -700), ringi, 1.0, 3.0, 0.0, 1.0)
    hscale = mathn(nt, (500, -700), 'MULTIPLY_ADD', inner, -0.78, 1.0)
    hcol = mathn(nt, (1220, -460), 'MULTIPLY', h4, hscale)
    glass = ramp(nt, (1400, -320),
                 [(0.00, (0.0180, 0.0330, 0.2000, 1)),
                  (0.14, (0.0260, 0.0520, 0.2900, 1)),
                  (0.30, (0.0420, 0.0760, 0.2600, 1)),
                  (0.41, (0.2600, 0.0240, 0.0300, 1)),
                  (0.53, (0.3300, 0.0700, 0.0350, 1)),
                  (0.67, (0.3000, 0.2700, 0.2000, 1)),
                  (0.81, (0.3200, 0.2100, 0.0500, 1)),
                  (0.91, (0.0300, 0.1100, 0.0550, 1)),
                  (1.00, (0.0250, 0.0900, 0.1150, 1))], interp='CONSTANT')
    L(nt, hcol, 'Value', glass, 'Factor')
    # --- the lead cames ----------------------------------------------------
    # Real stained glass is a mosaic held together by dark lead lines, and
    # without them the coloured pieces run into one another and the window
    # reads as a painted disc.  The distance to the nearest panel edge
    # darkens the glass to almost nothing.
    rf2 = mathn(nt, (-400, 320), 'SUBTRACT', 1.0, rf)
    edgeR = mathn(nt, (-220, 320), 'MINIMUM', rf, rf2)
    sf2 = mathn(nt, (-400, -60), 'SUBTRACT', 1.0, subfr)
    edgeS = mathn(nt, (-220, -60), 'MINIMUM', subfr, sf2)
    edge = mathn(nt, (1400, 200), 'MINIMUM', edgeR, edgeS)
    came = maprange(nt, (1580, 200), edge, 0.0, 0.13, 0.04, 1.0)
    # --- how much light each panel gets -----------------------------------
    # the light behind the window is strongest in the oculus and dies away
    # towards the outer ring
    fall = maprange(nt, (1400, 480), rad, 0.50, 0.06, 0.42, 1.0)
    # Not every panel is lit from behind.  The dark ones are what make a
    # rose window read as stained glass instead of a rainbow decal.  This
    # is a second hash of the same panel index, so the brightness belongs
    # to the panel rather than to a band crossing it.
    g1 = mathn(nt, (500, -880), 'MULTIPLY', idx, 78.233)
    g2 = mathn(nt, (680, -880), 'SINE', g1)
    g3 = mathn(nt, (860, -880), 'MULTIPLY', g2, 43758.5453)
    g4 = mathn(nt, (1040, -880), 'FRACT', g3)
    lit = mathn(nt, (1220, -880), 'MULTIPLY_ADD', g4, 0.85, 0.15)
    # old glass is never perfectly even
    gn = noise(nt, (1400, 720), 9.0, 8.0, 0.6, 0.4, tc.outputs['Generated'])
    gk = mathn(nt, (1580, 720), 'MULTIPLY_ADD', gn.outputs['Fac'], 0.55, 0.72)
    st = mathn(nt, (1760, 480), 'MULTIPLY', fall.outputs['Result'],
               gk.outputs['Value'])
    st = mathn(nt, (1940, 480), 'MULTIPLY', st, lit.outputs['Value'])
    st = mathn(nt, (2120, 480), 'MULTIPLY', st, came.outputs['Result'])
    bsdf = NN(nt, 'ShaderNodeBsdfPrincipled', (2300, 100))
    bsdf.inputs['Base Color'].default_value = (0.018, 0.020, 0.028, 1)
    bsdf.inputs['Roughness'].default_value = 0.18
    bsdf.inputs['IOR'].default_value = 1.52
    L(nt, glass, 'Color', bsdf, 'Emission Color')
    L(nt, st, 'Value', bsdf, 'Emission Strength')
    L(nt, bsdf, 'BSDF', out, 'Surface')
    return m


'''

s = s[:start] + NEW + s[end:]
open(P, "w").write(s)
print("m_rose_glass replaced")
