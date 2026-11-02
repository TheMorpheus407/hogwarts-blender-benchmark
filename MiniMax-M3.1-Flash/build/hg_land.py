"""Hogwarts — landscape: terrain field, crag, plateau, lake, mountain ranges."""
import bpy, bmesh, math
import numpy as np
from mathutils import Vector
import hg_np as N
import hg_lib as L
import hg_cfg as C

TERRAIN_SPAN = 2400.0
TERRAIN_N = 520
WATER_SPAN = 3200.0
WATER_N = 340


def terrace(v, n=6.0, soft=0.45):
    """Quantise a height field into strata steps with soft risers."""
    f = v * n
    fl = np.floor(f)
    fr = f - fl
    s = np.clip((fr - (0.5 - soft * 0.5)) / max(soft, 1e-4), 0.0, 1.0)
    s = s * s * (3 - 2 * s)
    return (fl + s) / n


# ------------------------------------------------------------------ terrain field
def land_height(X, Y):
    """Height of the open landscape. Vectorised over numpy arrays."""
    # --- shoreline masks (noisy so the coast is never a clean line) ---
    e = N.smoothstep(C.GORGE_WALL_X, C.GORGE_WALL_X + 42.0,
                     X + 48 * N.fbm(X / 260.0, Y / 260.0, 4, seed=41))
    n = N.smoothstep(640, 940, Y + 90 * N.fbm(X / 320.0, Y / 320.0, 3, seed=7))
    w = N.smoothstep(-640, -940, X + 90 * N.fbm(X / 340.0, Y / 340.0, 3, seed=19))
    s = N.smoothstep(-720, -980, Y + 110 * N.fbm(X / 330.0, Y / 330.0, 3, seed=29))
    land = np.maximum(np.maximum(e, n), np.maximum(w, s))

    hills = (54.0
             + 76.0 * N.fbm(X / 330.0, Y / 330.0, 5, seed=3)
             + 48.0 * N.ridged(X / 620.0, Y / 620.0, 5, seed=9) ** 1.28
             + 13.0 * N.ridged(X / 145.0, Y / 145.0, 3, seed=23) ** 1.12)
    h = land * hills
    h += (1.0 - land) * (-17.0)                       # lake bed
    h += 6.0 * N.fbm(X / 90.0, Y / 90.0, 4, seed=55) * land

    # --- the crag stands proud: the ground falls away to a shoreline so the
    #     rock reads as a promontory rather than sitting in a bowl ---
    dc = np.hypot(X, Y * 1.06)
    moat = N.smoothstep(240.0, 120.0, dc)
    h = h * (1.0 - 0.88 * moat) + (-9.0) * (0.88 * moat)

    # --- the gorge: a rocky ravine between the crag and the eastern highlands ---
    rav = (N.smoothstep(C.GORGE_Y0, C.GORGE_Y0 + 150.0, Y)
           * (1.0 - N.smoothstep(C.GORGE_Y1 - 110.0, C.GORGE_Y1 + 60.0, Y)))
    ravband = (N.smoothstep(C.GORGE_X0, C.GORGE_X0 + 22.0, X)
               * (1.0 - N.smoothstep(C.GORGE_X1 - 26.0, C.GORGE_X1 + 6.0, X)))
    ravine = rav * ravband
    floor = C.GORGE_FLOOR_Z + 6.0 * N.fbm(X / 130.0, Y / 130.0, 4, seed=88)
    h = h * (1.0 - ravine) + floor * ravine

    # --- the castle's own shore: the bed shelves up towards the crag ---
    dc = np.hypot(X, Y * 1.06)
    shelf = N.smoothstep(430.0, 155.0, dc)
    h += shelf * 15.0

    # --- the boathouse inlet ---------------------------------------------
    # The boathouse has to stand *at the waterline*, but the shelf above
    # carried the ground five metres above the lake right up to its door:
    # the building was buried in a dry plateau and the water only began
    # fifty metres away.  Carve a rock inlet so the lake really laps the
    # boat door and both jetties stand in open water.
    #
    # A superellipse rather than a circle -- a round pond would read as a
    # pond.  Its north edge stops short of the moor path that lands on the
    # west bank, and its west edge stops short of the cliff foot, so the
    # inlet is a bay cut into the shore rather than a hole in the world.
    ex = np.abs(X - 80.0) / 46.0
    ey = np.abs(Y + 120.0) / 40.0
    db = (ex ** 3 + ey ** 3) ** (1.0 / 3.0)
    db *= 1.0 + 0.075 * N.fbm(X / 27.0, Y / 27.0, 3, seed=613)
    basin = N.smoothstep(1.12, 0.68, db)
    h = h * (1.0 - basin) + (-2.6) * basin
    return h


def land_mask(X, Y):
    """1 where the land is dry, 0 where it is water."""
    e = N.smoothstep(C.GORGE_WALL_X, C.GORGE_WALL_X + 42.0,
                     X + 48 * N.fbm(X / 260.0, Y / 260.0, 4, seed=41))
    n = N.smoothstep(640, 940, Y + 90 * N.fbm(X / 320.0, Y / 320.0, 3, seed=7))
    w = N.smoothstep(-640, -940, X + 90 * N.fbm(X / 340.0, Y / 340.0, 3, seed=19))
    s = N.smoothstep(-720, -980, Y + 110 * N.fbm(X / 330.0, Y / 330.0, 3, seed=29))
    return np.maximum(np.maximum(e, n), np.maximum(w, s))


def warp_grid(span, n, power=1.35):
    u = np.linspace(-1.0, 1.0, n + 1)
    x = span * np.sign(u) * np.abs(u) ** power
    return x


def terrain_z(X, Y):
    """Exact height of the *rendered* terrain surface at (X, Y).

    The terrain mesh is a warped grid, so sampling `land_height` directly
    gives a value that can differ from the visible surface by up to a metre.
    This reproduces the grid's parameterisation and interpolates the same
    quads, so scattered objects sit on the ground instead of hovering.
    """
    X = np.asarray(X, dtype=np.float64)
    Y = np.asarray(Y, dtype=np.float64)
    xs = warp_grid(TERRAIN_SPAN, TERRAIN_N, 1.35)
    ys = warp_grid(TERRAIN_SPAN, TERRAIN_N, 1.35)
    XG, YG = np.meshgrid(xs, ys, indexing='ij')
    ZG = land_height(XG, YG)
    p = 1.35
    n = TERRAIN_N
    ux = np.clip(np.sign(X) * (np.abs(X) / TERRAIN_SPAN) ** (1.0 / p), -1.0, 1.0)
    uy = np.clip(np.sign(Y) * (np.abs(Y) / TERRAIN_SPAN) ** (1.0 / p), -1.0, 1.0)
    tx = (ux + 1.0) * 0.5 * n
    ty = (uy + 1.0) * 0.5 * n
    ix = np.clip(np.floor(tx).astype(np.int64), 0, n - 1)
    iy = np.clip(np.floor(ty).astype(np.int64), 0, n - 1)
    fx = np.clip(tx - ix, 0.0, 1.0)
    fy = np.clip(ty - iy, 0.0, 1.0)
    z00 = ZG[ix, iy]
    z10 = ZG[ix + 1, iy]
    z01 = ZG[ix, iy + 1]
    z11 = ZG[ix + 1, iy + 1]
    return ((z00 * (1 - fx) + z10 * fx) * (1 - fy)
            + (z01 * (1 - fx) + z11 * fx) * fy)


def forest_density(X, Y, Z, slope):
    """0..1 density of conifer forest at each point.

    Shared by the terrain shader (which darkens the ground where the forest
    stands) and the tree scatter, so the mass and the individual trees agree.
    """
    d = 0.30 + 0.70 * (0.5 + 0.5 * N.fbm(X / 165.0, Y / 165.0, 4, seed=401))
    d = N.smoothstep(0.30, 0.66, d)                 # sharp stands + glades
    glade = 0.5 + 0.5 * N.fbm(X / 300.0, Y / 300.0, 3, seed=777)
    d *= N.smoothstep(0.22, 0.50, glade)
    d *= N.smoothstep(1.05, 0.30, slope)            # no trees on cliffs
    d *= N.smoothstep(0.35, 0.78, land_mask(X, Y))
    d *= N.smoothstep(-3.0, 5.0, Z)                 # not in the lake
    d *= N.smoothstep(210.0, 130.0, Z)              # thinning with altitude
    d *= N.smoothstep(0.18, 0.55, N.fbm(X / 420.0, Y / 420.0, 3, seed=555)
                      + 0.5)                        # valley belts
    d *= N.smoothstep(128.0, 235.0, np.hypot(X, Y))  # castle grounds
    # keep the approach road, the moor path and the viaduct clear
    d *= N.smoothstep(9.0, 20.0, N.dist_polyline(X, Y, C.PATH_MAIN))
    d *= N.smoothstep(7.0, 15.0, N.dist_polyline(X, Y, C.PATH_MOOR))
    d *= N.smoothstep(7.0, 15.0, N.dist_polyline(X, Y, C.PATH_QUID))
    d *= N.smoothstep(11.0, 24.0, np.abs(Y - C.VIA_Y))
    d *= N.smoothstep(10.0, 22.0, np.abs(X - C.BOAT_X))
    return np.clip(d, 0.0, 1.0)


def make_terrain(name, c, mats):
    xs = warp_grid(TERRAIN_SPAN, TERRAIN_N, 1.35)
    ys = warp_grid(TERRAIN_SPAN, TERRAIN_N, 1.35)
    X, Y = np.meshgrid(xs, ys, indexing='ij')
    Z = land_height(X, Y)
    gy, gx = np.gradient(Z, ys, xs)
    slope = np.sqrt(gx * gx + gy * gy)
    rocky = N.smoothstep(0.35, 1.25, slope)
    forest = forest_density(X, Y, Z, slope)

    mb = L.MB()
    attrs = []
    n = TERRAIN_N + 1
    for j in range(n):
        for i in range(n):
            mb.verts.append((float(xs[i]), float(ys[j]), float(Z[i, j])))
            attrs.append((float(forest[i, j]), float(rocky[i, j]), 0.0))
    for j in range(n - 1):
        for i in range(n - 1):
            a = j * n + i
            mb.faces.append((a, a + 1, a + n + 1, a + n))
            mb.mats.append(0)
    obj = mb.to_object(name, c, mats, fix_normals=False)
    L.write_color_attr(obj, "ground", attrs)
    obj.data.update()
    return obj


# ------------------------------------------------------------------ the crag
# Constant that puts the mean crag radius back where the terraces expect it.
BIAS = 8.82


def crag_disp(T, Z):
    """Radial displacement of the rock face (broadcasting arrays).

    The field is built in ARC-LENGTH / HEIGHT space, not in (cos T, sin T)
    space.  A field that only knows the bearing produces features that run
    the full height of the cliff, and the crag came out as a bundle of
    organ pipes -- smooth vertical tubes with an even 4-5 m pitch.  Working
    in metres of arc length instead lets the clefts wander, start, stop and
    merge, and lets every sector of the face carry its own bedding planes
    at its own heights.
    """
    u = np.clip((Z + 26.0) / (C.PLATEAU_Z + 26.0), 0.0, 1.0)
    # taper to nothing at the rim so the castle platform keeps a predictable
    # edge and the curtain walls / terraces can be placed against it
    fade = 1.0 - 0.96 * N.smoothstep(0.93, 1.0, u)
    s = T * 120.0                       # arc length along the cliff, metres

    # --- broad buttresses and re-entrant gullies (angular only) ---------
    mega = 19.0 * N.vnoise(s / 52.0, 3.0, 3)
    lobes = 8.0 * N.vnoise(s / 18.5 + 11.0, 7.0, 3)

    # --- vertical clefts that wander and die out part way up ------------
    # A ridged field in (arc, height): the crests of the ridge become the
    # lips of the clefts.  Because the field varies with height as well as
    # with bearing, a cleft can fade out half way up instead of running the
    # whole cliff like a rib.
    # NOTE on octaves: the crag mesh samples about every 1.7 m along the
    # cliff and every 0.7 m in height, so any octave finer than roughly
    # 5 m cannot be resolved.  An unresolved octave aliases into stair
    # steps, and the cliff came out looking like a stack of masonry blocks.
    cv = N.fbm(s / 34.0, Z / 30.0, 3, seed=53)
    cleft = -9.0 * np.clip(1.0 - np.abs(cv) * 2.6, 0.0, 1.0) ** 1.2
    cv2 = N.fbm(s / 16.0, Z / 15.0, 2, seed=71)
    cleft2 = -4.0 * np.clip(1.0 - np.abs(cv2) * 3.0, 0.0, 1.0) ** 1.4

    # --- bedding planes: a soft swell, NOT a stack of ledges ------------
    # The bedding height is warped by a slow field along the cliff, so the
    # shelves climb and dip around the face.  It is deliberately left
    # un-terraced: a quantised radial step lands on a near-vertical wall as
    # a crisp horizontal shelf, and a stack of those is exactly what makes
    # the crag read as a rubble wall instead of as rock.
    warp = 11.0 * N.vnoise(s / 30.0, 5.0, 21) + 5.0 * N.vnoise(s / 11.0, 9.0, 23)
    bed = 1.6 * N.fbm(s / 45.0, (Z + warp) / 9.0, 2, seed=31)

    # --- chunky broken rock ---------------------------------------------
    # Every wavelength here has to stay comfortably above the mesh spacing
    # (~1.4 m along the cliff, ~0.5 m in height).  A two-octave fbm at
    # s/12 puts its finest feature at 6 m, which the mesh resolves cleanly;
    # at s/7 it lands on 3.4 m and the cliff breaks into stair steps.
    # The amplitudes matter as much as the wavelengths: `lump` at 4.0 m over
    # a 6 m finest octave tilts the surface by more than 50 degrees between
    # neighbouring vertices, which is what pushed the shading past the
    # auto-smooth angle and broke the cliff into hard little facets.
    lump = 2.4 * N.fbm(s / 13.0, Z / 10.0, 2, seed=17)
    frac = 1.8 * N.fbm(s / 17.0, Z / 13.0, 2, seed=91)
    fine = 0.20 * N.fbm(s / 10.0, Z / 8.0, 2, seed=31)
    # --- arêtes ----------------------------------------------------------
    # Smooth fbm only ever makes pillows.  Ridged noise folds the surface
    # instead, and the fold line is a crease -- the difference between a
    # rounded mass and a crag broken along joint planes.  The amplitude is
    # kept low: the crease has to survive the mesh without tipping the
    # shading past the auto-smooth angle.
    arete = 4.2 * (N.ridged(s / 22.0, Z / 19.0, 2, seed=43) - 0.5)
    # a second, finer set of creases.  The fold lines of a ridged field are
    # what turns a smooth bulge into broken rock, but the amplitude has to
    # be big enough for the fold to tip the shading past the auto-smooth
    # angle -- at 1.3 m the creases were there but invisible, and the cliff
    # read as a loaf of melted wax.
    arete2 = 1.7 * (N.ridged(s / 11.0, Z / 9.5, 2, seed=59) - 0.5)
    # A third, finer set of creases for the close shots.  Six metres is
    # still four samples across on the crag mesh, so the folds survive as
    # folds; anything finer than that aliases into facets.
    arete3 = 0.85 * (N.ridged(s / 6.0, Z / 5.5, 2, seed=67) - 0.5)
    # --- jointed facets ---------------------------------------------------
    # The crag breaks along joint planes into flat slabs.  The cellular field
    # gives the joint NETWORK; the joint itself is a narrow trench traced
    # along the cell boundaries.
    # The lookup is sheared: an unsheared cell grid puts its boundaries on
    # near-horizontal lines, and a radial step along a horizontal line is a
    # LEDGE -- the cliff ends up as a stack of shelves.  Sheared, the same
    # step reads as an inclined joint plane.
    wd1, wd2, _cellr = N.worley((s + 0.85 * Z) / 10.0, Z / 9.0, 1.0, seed=131,
                                jitter=0.9)
    # Half the gap between the two nearest feature points is the distance to
    # the cell boundary.
    dbound = np.maximum((wd2 - wd1) * 0.5, 0.0)
    # The DEPTH of the trench has to vary smoothly.  Giving every cell its
    # own depth (a per-cell constant) put a hard radial step of up to two
    # metres along every cell boundary, and on a polar mesh a step of a
    # couple of metres breaks into a literal staircase -- the cliff came out
    # as a flight of stone steps.  The per-cell tone lives in the material's
    # joint network instead, where a step is a colour change and not a
    # displaced vertex.
    jdepth = 3.60 + 2.60 * N.fbm(s / 26.0, Z / 24.0, 3, seed=137)
    joint = -jdepth * np.exp(-(dbound / 0.40) ** 2)

    # --- second joint set --------------------------------------------------
    # A real crag breaks at two or three scales.  One network alone leaves
    # whole stretches of cliff unbroken, and the eye reads that as a smooth
    # pillow.  This set runs at a different angle and a finer pitch, so the
    # two networks cross and the face breaks into irregular blocks.  It is
    # sheared the other way, so the two sets are not parallel.
    wd3, wd4, _cellr2 = N.worley((s - 1.05 * Z) / 8.0, Z / 9.0, 1.0, seed=211,
                                 jitter=0.95)
    dbound2 = np.maximum((wd4 - wd3) * 0.5, 0.0)
    jdepth2 = 1.40 + 1.00 * N.fbm(s / 15.0, Z / 17.0, 3, seed=217)
    joint2 = -jdepth2 * np.exp(-(dbound2 / 0.42) ** 2)

    d = (mega + lobes + cleft + cleft2 + bed + lump + frac + fine
         + arete + arete2 + arete3 + joint + joint2 + BIAS)
    d = d * fade
    # The cornice: the last four metres of cliff turn over into the rim, and
    # the main displacement is faded out over exactly that band so the castle
    # platform keeps a predictable edge.  The side effect was a smooth grey
    # ramp 15 m wide running right around the castle, which read as a poured
    # concrete apron.  Broken rock has to survive up to the rim, so a
    # separate term carries it there.
    d = d + 3.6 * N.fbm(s / 12.0, Z / 8.0, 2, seed=63) * \
        N.smoothstep(0.900, 0.962, u) * (1.0 - 0.45 * N.smoothstep(0.988, 1.0, u))
    return d


def crag_radius(T, Z):
    """Outer radius of the rock at bearing T and height Z (numpy, broadcastable)."""
    u = np.clip((Z + 26.0) / (C.PLATEAU_Z + 26.0), 0.0, 1.0)
    ex = np.cos(T) / C.CRAG_TOP_RX
    ey = np.sin(T) / C.CRAG_TOP_RY
    rt = 1.0 / np.sqrt(ex * ex + ey * ey)
    d_ang = np.arctan2(np.sin(T), np.cos(T))
    rt = rt * (1.0 + C.CRAG_EAST_BULGE * np.exp(-(d_ang / C.CRAG_BULGE_SIGMA) ** 2))
    rc = rt + C.CRAG_BATTER
    rbase = rc + 26.0
    # Sheer wall from the talus up to the rim, with only a modest outward
    # cornice — a big overhang reads as a smooth mound from below.
    R = np.where(u < 0.05,
                 rbase + (rc - rbase) * (u / 0.05),
                 np.where(u < 0.955,
                          rc + 1.4 * ((u - 0.05) / 0.905),
                          rc + 1.4 - (C.CRAG_BATTER + 1.4) *
                          N.smoothstep(0.0, 1.0, (u - 0.955) / 0.045)))
    return R + crag_disp(T, Z)


def make_crag(name, c, mats, ntheta=960, nz=210):
    th = np.linspace(0.0, 2 * np.pi, ntheta, endpoint=False)
    H = np.linspace(-26.0, C.PLATEAU_Z, nz)
    T, Z = np.meshgrid(th, H, indexing='ij')
    R = crag_radius(T, Z)
    mb = L.MB()
    verts = np.stack([R * np.cos(T), R * np.sin(T), Z], axis=-1)
    for j in range(nz):
        for i in range(ntheta):
            mb.verts.append((float(verts[i, j, 0]), float(verts[i, j, 1]),
                             float(verts[i, j, 2])))
    for j in range(nz - 1):
        for i in range(ntheta):
            i2 = (i + 1) % ntheta
            mb.faces.append((j * ntheta + i, j * ntheta + i2,
                             (j + 1) * ntheta + i2, (j + 1) * ntheta + i))
            mb.mats.append(0)
    obj = mb.to_object(name, c, mats, fix_normals=False)
    # A generous auto-smooth angle: at 16 degrees almost every small step
    # in the displacement broke into its own facet and the crag read as a
    # pile of flat slabs.  The rock wants to read as one sculpted mass, with
    # the fracture structure carried by the material's joint network rather
    # than by the shading of the mesh.
    L.smooth(obj, 52)
    return obj


def make_plateau(name, c, mats, ntheta=256, nr=30):
    """Ground on top of the crag (castle platform); edge matches the rock rim."""
    th = np.linspace(0.0, 2 * np.pi, ntheta, endpoint=False)
    rt = crag_radius(th, np.full(ntheta, C.PLATEAU_Z))
    T, S = np.meshgrid(th, np.linspace(0.0, 1.0, nr), indexing='ij')
    RR = rt[:, None] * S
    X = RR * np.cos(T)
    Y = RR * np.sin(T)
    Z = C.PLATEAU_Z + 0.18 + 2.6 * N.fbm(X / 78.0, Y / 78.0, 4, seed=91) \
        + 1.1 * N.fbm(X / 26.0, Y / 26.0, 3, seed=47)
    Z -= 1.1 * S ** 10
    mb = L.MB()
    for j in range(nr):
        for i in range(ntheta):
            mb.verts.append((float(X[i, j]), float(Y[i, j]), float(Z[i, j])))
    for j in range(nr - 1):
        for i in range(ntheta):
            i2 = (i + 1) % ntheta
            mb.faces.append((j * ntheta + i, j * ntheta + i2,
                             (j + 1) * ntheta + i2, (j + 1) * ntheta + i))
            mb.mats.append(0)
    mb.verts.append((0.0, 0.0, float(C.PLATEAU_Z + 0.18)))
    ci = len(mb.verts) - 1
    for i in range(ntheta):
        mb.faces.append((ci, (i + 1) % ntheta, i))
        mb.mats.append(0)
    obj = mb.to_object(name, c, mats, fix_normals=False)
    L.smooth(obj, 40)
    return obj


# ------------------------------------------------------------------ lake
def make_water(name, c, mats):
    xs = warp_grid(WATER_SPAN, WATER_N, 1.25)
    ys = warp_grid(WATER_SPAN, WATER_N, 1.25)
    X, Y = np.meshgrid(xs, ys, indexing='ij')
    bed = land_height(X, Y)
    depth = np.clip(-bed, 0.0, 40.0)
    sw = 0.09 * np.sin(X * 0.021 + Y * 0.013) + 0.06 * np.sin(X * 0.041 - Y * 0.037)
    Z = C.WATER_Z + sw
    mb = L.MB()
    n = WATER_N + 1
    attrs = []
    for j in range(n):
        for i in range(n):
            mb.verts.append((float(xs[i]), float(ys[j]), float(Z[i, j])))
            attrs.append((float(depth[i, j] / 12.0), 0.0, 0.0))
    for j in range(n - 1):
        for i in range(n - 1):
            a = j * n + i
            mb.faces.append((a, a + 1, a + n + 1, a + n))
            mb.mats.append(0)
    obj = mb.to_object(name, c, mats, fix_normals=False)
    L.write_color_attr(obj, "depth", attrs)
    L.smooth(obj, 60)
    return obj


# ------------------------------------------------------------------ mountains
def make_mountains(name, c, mats, r0, r1, hmax, seed, ntheta=1000, nring=32):
    """A ring of jagged peaks forming one layer of the highland backdrop.

    The angular resolution is not a detail: the ridge crest is built from
    ridged noise at 5.4 cycles per radian, so the finest octave lands on
    5.4 * 2.07^4 = 99 cells around the whole ring.  Sampling that with 360
    segments -- one sample every 0.28 cells -- aliases the whole crest and
    the mountains come out as hard triangular cardboard tents.  The rule
    here is that no octave may be finer than about a quarter of the sample
    spacing, so the sample count is derived from the frequency, not chosen.
    """
    th = np.linspace(0.0, 2 * np.pi, ntheta, endpoint=False)
    rr = np.linspace(r0, r1, nring)
    T, R = np.meshgrid(th, rr, indexing='ij')
    # ridge crest: sharp, peaky profile around the ring
    crest = N.ridged(T * 5.4, np.zeros_like(T), 5, seed=seed)
    crest = np.clip(crest, 0.0, None) ** 1.18
    crest = 0.30 + 0.90 * crest
    # shoulders so the summits are not clean triangular tents
    crest = crest * (1.0 + 0.15 * (np.clip(
        N.ridged(T * 15.0, np.zeros_like(T), 3, seed=seed + 5),
        0.0, None) ** 1.5 - 0.42))
    # secondary spurs and gullies (2 octaves: the radial frequency of a third
    # octave would fall below two samples per cell and break into facets)
    spur = N.ridged(T * 17.0, R * 0.0035, 2, seed=seed + 7)
    spur = np.clip(spur, 0.0, None) ** 1.8
    # radial profile: climb out of the valley, crest, then fall behind.
    # The crest radius wanders with the bearing, otherwise the level sets are
    # perfect circular arcs and the near-horizontal facet at the top of the
    # profile becomes a dead-straight bright line across the sky.
    span = r1 - r0
    rw = N.fbm(T * 1.7, np.zeros_like(T), 3, seed=seed + 71) * span * 0.24
    Rq = R + rw
    prof = (N.smoothstep(r0, r0 + span * 0.40, Rq)
            * (1.0 - N.smoothstep(r1 - span * 0.34, r1, Rq)))
    H = hmax * crest * prof
    H += hmax * 0.30 * spur * prof
    H += hmax * 0.18 * N.fbm(T * 11.0, R * 0.0035, 2, seed=seed + 13) * prof
    X = R * np.cos(T)
    Y = R * np.sin(T)
    mb = L.MB()
    for j in range(nring):
        for i in range(ntheta):
            mb.verts.append((float(X[i, j]), float(Y[i, j]), float(H[i, j]) - 40.0))
    for j in range(nring - 1):
        for i in range(ntheta):
            i2 = (i + 1) % ntheta
            mb.faces.append((j * ntheta + i, j * ntheta + i2,
                             (j + 1) * ntheta + i2, (j + 1) * ntheta + i))
            mb.mats.append(0)
    obj = mb.to_object(name, c, mats, fix_normals=True)
    L.smooth(obj, 44)
    return obj


def make_massif(name, c, mats, ang0_deg, ang1_deg, r0, r1, hmax, seed,
                ntheta=760, nring=120, base_z=-90.0):
    """A single vast mountain mass standing close behind the castle.

    The distant ridge rings never read on the hero camera: at 4-7 km they
    subtend two or three degrees and sit at the same value as the sky, so the
    castle floats against empty sky.  Every reference image instead backs the
    castle with a *close, huge* hill whose crest passes behind the middle of
    the massing while the spires still clear it.

    This builds one sector of ridge geometry centred on a bearing: a series of
    summits with spurs and gullies, rising out of the moorland, with the
    sector's ends tapered to zero so the mass grows out of the terrain
    instead of ending on a cut edge.  The whole skirt sits below the land, so
    the only silhouette is the crest itself.

    Angles are standard mathematical bearings (0 deg = +X / east,
    90 deg = +Y / north).
    """
    a0 = math.radians(ang0_deg)
    a1 = math.radians(ang1_deg)
    th = np.linspace(a0, a1, ntheta)
    rr = np.linspace(r0, r1, nring)
    T, R = np.meshgrid(th, rr, indexing='ij')

    # --- summits along the arc: a handful of big massifs, not a uniform wall
    # Five octaves and a softer exponent: with four the ridged noise only
    # had sharp cusps, and the summits came out as clean triangular tents
    # with straight sides -- cardboard peaks.  The sample count has to keep
    # up: the finest octave of the crest lands on 3.3 * 2.07^4 = 61 cells
    # across the arc, so the arc needs several hundred samples before the
    # crest resolves into ridges instead of aliased facets.
    u = (th - a0) / max(1e-6, (a1 - a0))
    crest = N.ridged(u * 3.3, np.zeros_like(u), 5, seed=seed)
    crest = np.clip(crest, 0.0, None) ** 1.12
    crest = 0.46 + 0.84 * crest
    # shoulders: mid-scale ridging along the crest so each summit has
    # buttresses and saddles instead of a single clean apex
    shoulder = np.clip(N.ridged(u * 11.0, np.zeros_like(u), 3,
                                 seed=seed + 3), 0.0, None) ** 1.5
    crest = crest * (1.0 + 0.17 * (shoulder - 0.42))

    # --- radial profile: climb out of the moor, crest, then fall away behind
    # The crest radius has to wander with the bearing.  If it does not, the
    # height field stays separable -- crest(bearing) * profile(radius) --
    # and every level set is a circular arc.  Where the profile crosses its
    # maximum the surface turns horizontal over a whole ring at once, and a
    # 70 m wide flat facet seen edge-on reads as a dead-straight bright
    # plank floating in the sky.
    span = r1 - r0
    rshift = N.fbm(u * 5.0, np.zeros_like(u), 4, seed=seed + 41) * span * 0.17
    Rq = R + rshift[:, None]
    prof = (N.smoothstep(r0, r0 + span * 0.32, Rq)
            * (1.0 - N.smoothstep(r1 - span * 0.46, r1, Rq)))

    # --- taper the sector ends so the mass merges into the landscape
    edge = N.smoothstep(0.0, 0.24, u) * N.smoothstep(1.0, 0.76, u)

    H = hmax * crest[:, None] * prof * edge[:, None]
    # spurs and gullies raking down the flanks
    spur = np.clip(N.ridged(T * 11.0, R * 0.0045, 3, seed=seed + 7), 0.0, None) ** 1.75
    H += hmax * 0.24 * spur * prof * edge[:, None]
    # fine broken rock
    H += hmax * 0.11 * N.fbm(T * 8.0, R * 0.004, 3, seed=seed + 13) * prof * edge[:, None]
    # keep the summit ridge crisp -- erosion rounds everything else
    H *= (1.0 - 0.10 * N.fbm(T * 26.0, R * 0.004, 2, seed=seed + 29))

    X = R * np.cos(T)
    Y = R * np.sin(T)
    mb = L.MB()
    for j in range(nring):
        for i in range(ntheta):
            mb.verts.append((float(X[i, j]), float(Y[i, j]),
                             float(H[i, j] + base_z)))
    for j in range(nring - 1):
        for i in range(ntheta - 1):
            # wind counter-clockwise seen from above: (d/dtheta) x (d/dR)
            # points DOWN with this parameterisation, so the ring has to be
            # traversed the other way round or every face is back-facing.
            mb.faces.append((j * ntheta + i, (j + 1) * ntheta + i,
                             (j + 1) * ntheta + i + 1, j * ntheta + i + 1))
            mb.mats.append(0)
    obj = mb.to_object(name, c, mats, fix_normals=True)
    L.smooth(obj, 48)
    return obj
