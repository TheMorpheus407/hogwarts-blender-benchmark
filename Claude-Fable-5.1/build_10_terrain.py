"""Pass 1 — terrain: crag, gorge, east spur, mainland, mountains, lake.

Height field is computed in numpy for full control; meshes are built with
foreach_set for speed.  Two terrain meshes (near, fine / far, coarse) and two
lake meshes.  Vertex attributes drive the shaders and the forest scatter.
"""
import bpy, os, sys, importlib, math, time
import numpy as np
FOLDER = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else bpy.path.abspath("//")
if FOLDER not in sys.path:
    sys.path.insert(0, FOLDER)
import hog_lib as H; importlib.reload(H)
import hog_layout as LAY; importlib.reload(LAY)
from hog_lib import fbm, ridged, smoothstep, smax, smin, sd_superellipse, sd_polyline

t_start = time.time()

# ------------------------------------------------------------------ layout constants
NEAR_X = (-696.0, 696.0)
NEAR_Y = (-804.0, 600.0)
NEAR_STEP = 2.0
FAR_HALF = 5400.0
FAR_STEP = 12.0
LAKE_Z = 0.0

# Shoreline of the mainland: land is north/east of this poly-line (y > shore(x)), with bends east.
SHORE_PTS = [(-6000, 420), (-2600, 380), (-1500, 300), (-900, 210), (-500, 150), (-260, 128),
             (-120, 112), (60, 96), (170, 74), (230, 64), (330, 70), (430, 40), (520, -60),
             (600, -220), (680, -420), (760, -700), (860, -1100), (1000, -1800), (1300, -3200), (1600, -6000)]

# --- terraces cut into the crag (cx, cy, ax, ay, rot_deg, z, exponent)
TERRACES = [
    # bastion terrace below the tower cluster, where the boathouse stair arrives
    (52, -61, 42, 9, -6, 58.0, 2.6),
    # greenhouse terrace, east-north-east
    (128, 56, 34, 22, 15, 57.0, 2.4),
    # lower court north of the cluster (saddle side)
    (20, 92, 60, 26, 0, 60.0, 2.4),
    # main courtyard (paved)
    (10, 22, 47, 24, 0, 72.0, 3.0),
    # gamekeeper's hut pad
    (392, 118, 14, 12, 0, 30.0, 2.4),
    # Quidditch pitch: flat oval on the mainland slope north-east
    (330, 215, 82, 52, 22, 40.0, 2.3),
]

# --- worn paths (polylines) : (points, width)
PATHS = [
    # from the northern saddle up to the north gate
    ([(-40, 520), (-70, 400), (-30, 300), (10, 220), (-10, 160), (0, 120), (10, 96)], 4.0),
    # east spur road to the viaduct head, continuing east along the shore to the pitch
    ([(258, -128), (300, -110), (350, -70), (430, 10), (520, 60), (640, 120), (760, 160)], 4.0),
    # gamekeeper track: from the north gate area east along the ridge to the forest
    ([(20, 118), (90, 128), (150, 130), (220, 150), (300, 190), (380, 250)], 3.0),
    # boathouse cove lane along the shore to the west
    ([(-80, -110), (-160, -90), (-260, -60), (-380, -40)], 3.0),
]

# ------------------------------------------------------------------ height field
def shore_y(x):
    xs = np.array([p[0] for p in SHORE_PTS], dtype=np.float64)
    ys = np.array([p[1] for p in SHORE_PTS], dtype=np.float64)
    return np.interp(x, xs, ys)

def height_field(X, Y, detail=True):
    """Return (Z, masks) for arrays X, Y (metres)."""
    x = X.astype(np.float64); y = Y.astype(np.float64)
    R = np.sqrt(x * x + y * y)

    # ---- 1. mainland / lake basin ------------------------------------------------
    land = (y - shore_y(x)) + 25.0 * fbm(x, y, octaves=4, scale=420.0, seed=3)
    # profile: lake bed at -45, shore at 0, moor rising inland
    z_main = np.where(land < 0,
                      -46.0 * smoothstep(0.0, 260.0, -land) - 0.0,
                      0.0)
    inland = np.clip(land, 0, None)
    z_main = z_main + 34.0 * smoothstep(0.0, 260.0, inland) + 0.06 * inland
    # rolling moor
    z_main += (14.0 * fbm(x, y, octaves=6, scale=260.0, seed=11) + 3.0 * fbm(x, y, octaves=5, scale=60.0, seed=12)) * smoothstep(-40.0, 60.0, land)
    # the neck: a ridge running north from the crag so the north gate road is plausible
    neck = np.exp(-((x + 0.0) / 130.0) ** 2) * smoothstep(40.0, 130.0, y) * smoothstep(520.0, 220.0, y)
    z_main += 38.0 * neck
    # a knoll north of the castle (far end of the covered bridge)
    z_main += 26.0 * np.exp(-(((x - 12.0) / 34.0) ** 2 + ((y - 178.0) / 26.0) ** 2))
    # a valley running NNE from behind the castle (mist pools here)
    valley = np.exp(-((x - 0.55 * (y - 200.0) - 260.0) / 220.0) ** 2) * smoothstep(150.0, 500.0, y)
    z_main -= 26.0 * valley
    # keep the lake bed gently uneven
    z_main += 3.0 * fbm(x, y, octaves=4, scale=120.0, seed=5) * (land < 0)

    # ---- 2. mountains (beyond ~1 km) ---------------------------------------------
    mt_mask = smoothstep(950.0, 2600.0, R)
    # open the lake to the south-west: mountains lower there
    az = np.arctan2(y, x)
    sw = np.exp(-((az - math.radians(-125)) / 0.9) ** 2)
    mt_mask *= (1.0 - 0.75 * sw)
    rid = ridged(x, y, octaves=8, scale=1700.0, seed=21, sharp=0.7)
    big = 0.5 + 0.5 * fbm(x, y, octaves=3, scale=2600.0, seed=22)
    z_mtn = (100.0 + 640.0 * rid * (0.55 + 0.45 * big)) * mt_mask
    z_mtn += 60.0 * fbm(x, y, octaves=6, scale=400.0, seed=23) * mt_mask
    z_mtn += (55.0 * ridged(x, y, octaves=5, scale=260.0, seed=24, sharp=0.5) - 20.0) * mt_mask
    z_mtn += (16.0 * ridged(x, y, octaves=4, scale=70.0, seed=25, sharp=0.4) - 6.0) * mt_mask
    # nearer foothills north (behind the castle) so ridges layer up
    hill_mask = smoothstep(350.0, 1100.0, R) * smoothstep(-0.3, 0.5, y / (R + 1.0))
    z_hill = (50.0 + 150.0 * ridged(x, y, octaves=5, scale=650.0, seed=31, sharp=0.4)) * hill_mask
    z = smax(z_main, z_main + z_mtn * 0.0 + z_hill * 0.0, 5.0)  # placeholder to keep dtype
    z = z_main + z_mtn + z_hill

    # ---- 3. castle crag ------------------------------------------------------------
    def promontory(d_raw, top, seed, prof_t, prof_z, rib_amp=(11.0, 4.0), rib_scale=(85.0, 22.0)):
        """Cliffed promontory from a signed outline distance (<0 inside).
        Returns (z, t, steep) where t = depth inside the outline (m)."""
        # warp the outline so the cliff breaks into vertical ribs / buttresses
        d = d_raw + rib_amp[0] * fbm(x, y, octaves=3, scale=rib_scale[0], seed=seed) \
                  + rib_amp[1] * fbm(x, y, octaves=4, scale=rib_scale[1], seed=seed + 1) \
                  + 2.0 * fbm(x, y, octaves=3, scale=7.0, seed=seed + 2)
        t = -d
        zc = np.interp(t, prof_t, prof_z)
        # steepness of the profile at t (for strata weighting)
        dz = (np.interp(t + 0.5, prof_t, prof_z) - np.interp(t - 0.5, prof_t, prof_z))
        steep = smoothstep(0.75, 1.9, dz)
        # blend the plateau top in above the cliff lip
        zc = zc + (top - prof_z[-1]) * smoothstep(prof_t[-3], prof_t[-1], t)
        return zc, t, steep

    # main promontory, elongated E-W, pointing SSW into the lake
    d_crag = sd_superellipse(x, y, 8.0, 6.0, 150.0, 106.0, n=2.9, rot=math.radians(-6))
    top = 66.0
    top = top + 10.0 * np.exp(-(((x - 60) / 70.0) ** 2 + ((y - 10) / 55.0) ** 2))
    top = top + 4.0 * np.exp(-(((x + 70) / 60.0) ** 2 + ((y + 12) / 40.0) ** 2))
    top = top - 8.0 * smoothstep(40.0, 110.0, y)
    top = top + 1.5 * fbm(x, y, octaves=4, scale=40.0, seed=42)
    # profile: talus apron from the lake bed, then a steep slope, then a near-vertical cliff, then the lip
    PT = [-14.0, 0.0, 10.0, 20.0, 27.0, 35.0, 40.0, 48.0]
    PZ = [-42.0, -28.0, -4.0, 18.0, 36.0, 60.0, 68.0, 72.0]
    z_crag, t_crag, steep_crag = promontory(d_crag, top, 41, PT, PZ, rib_amp=(16.0, 7.0), rib_scale=(110.0, 20.0))
    z = smax(z, z_crag, 5.0)

    # secondary promontory east of the gorge: viaduct landing (lower, more rounded)
    d_spur = sd_superellipse(x, y, 305.0, -118.0, 94.0, 68.0, n=2.6, rot=math.radians(28))
    top_s = 60.0 - 6.0 * smoothstep(0.0, 80.0, -(y + 118.0)) + 1.2 * fbm(x, y, octaves=4, scale=35.0, seed=44)
    PTs = [-14.0, 0.0, 10.0, 20.0, 28.0, 36.0, 44.0]
    PZs = [-38.0, -26.0, -6.0, 14.0, 34.0, 54.0, 60.0]
    z_spur, t_spur, steep_spur = promontory(d_spur, top_s, 43, PTs, PZs, rib_amp=(9.0, 3.5), rib_scale=(70.0, 20.0))
    z = smax(z, z_spur, 5.0)

    # a low rocky islet / skerries near the hero foreground for depth
    for (ix, iy, ir, ih, sd) in ((-330, -420, 26, 3.5, 51), (-410, -470, 14, 2.0, 52), (240, -520, 20, 2.5, 53)):
        d_i = sd_superellipse(x, y, ix, iy, ir, ir * 0.7, n=2.2, rot=0.6) + 4.0 * fbm(x, y, octaves=3, scale=20.0, seed=sd)
        z_i = -30.0 + (ih + 30.0) * smoothstep(-1.0, 22.0, -d_i) ** 0.9
        z = smax(z, z_i, 4.0)

    # ---- 4. rock detail & strata on steep ground ----------------------------------
    rock_zone = np.clip(smoothstep(-40.0, 8.0, t_crag) + smoothstep(-40.0, 8.0, t_spur), 0, 1)
    steep = np.clip(steep_crag * smoothstep(-6.0, 4.0, t_crag) + steep_spur * smoothstep(-6.0, 4.0, t_spur), 0, 1)
    fine_grid = (X[0, 1] - X[0, 0]) < 0.6
    if detail:
        # (a) rock relief first: ribs, boulders, ledgy noise
        z += (2.6 * ridged(x, y, octaves=5, scale=24.0, seed=62, sharp=0.5) - 1.3) * steep * rock_zone
        z += 0.7 * fbm(x, y, octaves=5, scale=8.0, seed=63) * rock_zone
        z += (0.9 * ridged(x, y, octaves=4, scale=5.0, seed=65, sharp=0.4) - 0.45) * steep * rock_zone
        if fine_grid:
            z += (1.1 * ridged(x, y, octaves=4, scale=3.2, seed=67, sharp=0.6) - 0.55) * steep * rock_zone
        # (b) stair corridor: carve a shelf so the flights sit on rock
        fl_ = LAY.BOAT_STAIR["flights"]
        cut_all = np.full_like(z, 1e9)
        near_all = np.zeros_like(z)
        for (xa, ya, za), (xb, yb, zb) in zip(fl_[:-1], fl_[1:]):
            bax, bay = xb - xa, yb - ya
            hh = np.clip(((x - xa) * bax + (y - ya) * bay) / (bax * bax + bay * bay + 1e-9), 0.0, 1.0)
            dd = np.sqrt((x - xa - bax * hh) ** 2 + (y - ya - bay * hh) ** 2)
            zi = za + (zb - za) * hh
            cut = zi - 0.45 + 0.75 * np.clip(dd - 1.8, 0.0, None)
            cut_all = np.minimum(cut_all, cut)
            near_all = np.maximum(near_all, smoothstep(6.5, 3.0, dd))
        z = z + (np.minimum(z, cut_all) - z) * near_all
        # (c) strata: step the height on steep rock, warped so the ledges wander; beds dip slightly
        step = 6.0
        warp = 2.2 * fbm(x, y, octaves=4, scale=34.0, seed=61) + 0.05 * x
        hs = (z + warp) / step
        fl = np.floor(hs); fr = hs - fl
        shaped = fl + smoothstep(0.36, 0.64, fr)
        z_terr = shaped * step - warp
        z = z + (z_terr - z) * steep * 0.9
        # (d) keep the stair treads clear of the stepped rock
        z = np.minimum(z, cut_all + (1.0 - near_all) * 1e6)
        # (e) small post-noise so the treads of the ledges are not dead flat
        z += 0.25 * fbm(x, y, octaves=3, scale=2.2, seed=66) * rock_zone
        if fine_grid:
            z += 0.18 * fbm(x, y, octaves=3, scale=1.0, seed=68) * rock_zone
    # gentle micro-relief everywhere on land (also on the far mesh so the seam matches)
    z += 0.35 * fbm(x, y, octaves=4, scale=14.0, seed=64) * smoothstep(-2.0, 2.0, z)

    # ---- 5. terraces (cut & fill) ---------------------------------------------------
    for (cx, cy, ax, ay, rot, tz, ex) in TERRACES:
        d_t = sd_superellipse(x, y, cx, cy, ax, ay, n=ex, rot=math.radians(rot))
        m = smoothstep(-3.0, 3.0, -d_t)
        z = z + (tz - z) * m

    # ---- 6. paths ------------------------------------------------------------------
    path_mask = np.zeros_like(z)
    for pts, w in PATHS:
        d = sd_polyline(x, y, pts)
        path_mask = np.maximum(path_mask, smoothstep(w, w * 0.35, d))
    # the paths are worn into the ground: slight groove & smoothing (box blur)
    if detail and z.shape[0] > 8 and (X[0, 1] - X[0, 0]) < 4.0:
        k = 3
        zp = np.pad(z, k, mode='edge')
        cs = np.cumsum(np.cumsum(zp, axis=0), axis=1)
        n = 2 * k + 1
        blur = (cs[n:, n:] - cs[:-n, n:] - cs[n:, :-n] + cs[:-n, :-n]) / (n * n)
        blur = np.pad(blur, ((0, z.shape[0] - blur.shape[0]), (0, z.shape[1] - blur.shape[1])), mode='edge')
        z = z + (blur - 0.25 - z) * path_mask

    # ---- masks for shading / scatter ------------------------------------------------
    gz_y, gz_x = np.gradient(z, Y[:, 0], X[0, :])
    slope = np.sqrt(gz_x ** 2 + gz_y ** 2)
    masks = {
        "slope": slope,
        "rock": np.clip(rock_zone * smoothstep(0.4, 1.2, slope) + smoothstep(1.0, 2.2, slope) + steep, 0, 1),
        "path": path_mask,
        "wet": smoothstep(6.0, 0.5, z),
        "crag": rock_zone,
        # talus / scree: rocky ground low on the crag where boulders collect
        "scree": np.clip(rock_zone * smoothstep(28.0, 2.0, z) * smoothstep(0.0, 1.5, z) * smoothstep(2.6, 0.5, slope), 0, 1),
    }
    # forest density: on land, moderate slopes, below ~420 m, thinner near the castle
    dist_castle = np.sqrt((x - 40.0) ** 2 + (y - 10.0) ** 2)
    forest = smoothstep(1.5, 4.0, z) * smoothstep(1.6, 0.6, slope) * smoothstep(520.0, 150.0, z)
    forest *= smoothstep(150.0, 330.0, dist_castle)             # castle grounds are cleared
    forest *= smoothstep(150.0, 330.0, np.sqrt((x - 305.0) ** 2 + (y + 118.0) ** 2)) * 0.6 + 0.4  # spur mostly open
    forest *= 0.45 + 0.55 * smoothstep(-0.2, 0.5, fbm(x, y, octaves=4, scale=220.0, seed=71))  # clumps
    forest *= 1.0 - path_mask
    dqx, dqy = x - 330.0, y - 215.0
    cq, sq = math.cos(math.radians(22)), math.sin(math.radians(22))
    qx, qy = cq * dqx + sq * dqy, -sq * dqx + cq * dqy
    forest *= smoothstep(1.0, 1.35, np.sqrt((qx / 82.0) ** 2 + (qy / 52.0) ** 2))  # Quidditch clearing
    forest *= 1.0 - smoothstep(30.0, 12.0, np.sqrt((x - 392.0) ** 2 + (y - 118.0) ** 2) - 10.0)  # hut clearing
    forest *= 1.0 - smoothstep(40.0, 14.0, np.sqrt((x + 330.0) ** 2 + (y - 250.0) ** 2))         # stone circle
    forest *= 1.0 - smoothstep(60.0, 20.0, np.sqrt((x - 10.0) ** 2 + (y - 150.0) ** 2))          # bridge line
    masks["forest"] = np.clip(forest, 0, 1)
    return z, masks


def make_grid_mesh(name, X, Y, Z, keep=None, attrs=None, coll="Terrain", mat=None):
    """Fast quad grid mesh from 2D arrays (shape [ny, nx])."""
    ny, nx = Z.shape
    me = bpy.data.meshes.new(name)
    verts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1).astype(np.float32)
    me.vertices.add(verts.shape[0])
    me.vertices.foreach_set("co", verts.ravel())
    I, J = np.meshgrid(np.arange(nx - 1), np.arange(ny - 1))
    v0 = (J * nx + I).ravel()
    quads = np.stack([v0, v0 + 1, v0 + nx + 1, v0 + nx], axis=1)
    if keep is not None:
        quads = quads[keep.ravel()]
    nf = quads.shape[0]
    me.loops.add(nf * 4)
    me.polygons.add(nf)
    me.loops.foreach_set("vertex_index", quads.ravel().astype(np.int32))
    me.polygons.foreach_set("loop_start", (np.arange(nf) * 4).astype(np.int32))
    try:
        me.polygons.foreach_set("loop_total", np.full(nf, 4, dtype=np.int32))
    except Exception:
        pass
    me.update(calc_edges=True)
    me.validate()
    if attrs:
        for k, arr in attrs.items():
            a = me.attributes.new(k, 'FLOAT', 'POINT')
            a.data.foreach_set("value", arr.ravel().astype(np.float32))
    me.shade_smooth()
    obj = bpy.data.objects.new(name, me)
    H.link_obj(obj, coll)
    if mat:
        H.set_material(obj, mat)
    return obj

# ------------------------------------------------------------------ build
for n in ("Terrain", "Water"):
    H.clear_collection(n)

mat_rock = H.ensure_material("M_Terrain", (0.32, 0.30, 0.26, 1))
mat_far = H.ensure_material("M_TerrainFar", (0.30, 0.31, 0.28, 1))
mat_water = H.ensure_material("M_Water", (0.02, 0.05, 0.07, 1))

# --- near terrain
xs = np.arange(NEAR_X[0], NEAR_X[1] + 1e-6, NEAR_STEP)
ys = np.arange(NEAR_Y[0], NEAR_Y[1] + 1e-6, NEAR_STEP)
X, Y = np.meshgrid(xs, ys)
Z, M = height_field(X, Y, detail=True)
CRAG_X = (-210.0, 336.0)
CRAG_Y = (-204.0, 132.0)
CRAG_STEP = 0.75
inside_c = (X > CRAG_X[0] + 1) & (X < CRAG_X[1] - 1) & (Y > CRAG_Y[0] + 1) & (Y < CRAG_Y[1] - 1)
Zn = Z - 3.0 * inside_c
near = make_grid_mesh("Terrain_Near", X, Y, Zn, attrs=M, mat=mat_rock)
near["hog_step"] = NEAR_STEP

# --- crag: high-resolution mesh so the strata and ribs resolve on the near-vertical faces
xc = np.arange(CRAG_X[0], CRAG_X[1] + 1e-6, CRAG_STEP)
yc = np.arange(CRAG_Y[0], CRAG_Y[1] + 1e-6, CRAG_STEP)
XC, YC = np.meshgrid(xc, yc)
ZC, MC = height_field(XC, YC, detail=True)
HI_X = (16.0, 112.0)
HI_Y = (-142.0, -44.0)
inside_h = (XC > HI_X[0] + 0.5) & (XC < HI_X[1] - 0.5) & (YC > HI_Y[0] + 0.5) & (YC < HI_Y[1] - 0.5)
ZC = ZC - 3.0 * inside_h
crag = make_grid_mesh("Terrain_Crag", XC, YC, ZC, attrs=MC, mat=mat_rock)
crag["hog_step"] = CRAG_STEP

# --- boathouse cliff: finest tier (0.4 m) where Cam_Boathouse and Cam_Detail_02 look
xh = np.arange(HI_X[0], HI_X[1] + 1e-6, 0.3)
yh = np.arange(HI_Y[0], HI_Y[1] + 1e-6, 0.3)
XH, YH = np.meshgrid(xh, yh)
ZH, MH = height_field(XH, YH, detail=True)
craghi = make_grid_mesh("Terrain_CragHi", XH, YH, ZH, attrs=MH, mat=mat_rock)
craghi["hog_step"] = 0.3

# --- far terrain (hole under the near mesh, minus one cell of overlap)
xf = np.arange(-FAR_HALF, FAR_HALF + 1e-6, FAR_STEP)
yf = np.arange(-FAR_HALF, FAR_HALF + 1e-6, FAR_STEP)
XF, YF = np.meshgrid(xf, yf)
ZF, MF = height_field(XF, YF, detail=True)
cx = 0.5 * (XF[:-1, :-1] + XF[1:, 1:]); cy = 0.5 * (YF[:-1, :-1] + YF[1:, 1:])
inside_v = (XF > NEAR_X[0] + 1) & (XF < NEAR_X[1] - 1) & (YF > NEAR_Y[0] + 1) & (YF < NEAR_Y[1] - 1)
ZF = ZF - 3.0 * inside_v
RF = np.sqrt(XF ** 2 + YF ** 2)
MF["forest"] = MF["forest"] * smoothstep(3200.0, 1400.0, RF)
far = make_grid_mesh("Terrain_Far", XF, YF, ZF, keep=None,
                     attrs={"slope": MF["slope"], "rock": MF["rock"], "forest": MF["forest"], "wet": MF["wet"], "path": MF["path"]},
                     mat=mat_far)

# --- lake near: gentle static swell + shader ripples (2 m grid)
xl = np.arange(NEAR_X[0], NEAR_X[1] + 1e-6, 2.0)
yl = np.arange(NEAR_Y[0], NEAR_Y[1] + 1e-6, 2.0)
XL, YL = np.meshgrid(xl, yl)
wave = np.zeros_like(XL)
for (a, kx, ky, ph) in ((0.06, 0.055, 0.020, 0.3), (0.045, -0.031, 0.062, 1.9), (0.03, 0.09, -0.07, 4.1), (0.02, 0.15, 0.12, 0.7)):
    wave += a * np.sin(kx * XL + ky * YL + ph)
wave += 0.05 * fbm(XL, YL, octaves=4, scale=22.0, seed=81)
riml = np.minimum.reduce([XL - NEAR_X[0], NEAR_X[1] - XL, YL - NEAR_Y[0], NEAR_Y[1] - YL])
wave = wave * smoothstep(0.0, 30.0, riml)
lake_near = make_grid_mesh("Lake_Near", XL, YL, LAKE_Z + wave, coll="Water", mat=mat_water)

# --- lake far: a flat frame (4 trapezoids) around the near box — no subdivision needed
def frame_mesh(name, outer, inner, z, coll, mat):
    (ox0, ox1, oy0, oy1) = outer; (ix0, ix1, iy0, iy1) = inner
    verts = [(ox0, oy0, z), (ox1, oy0, z), (ox1, oy1, z), (ox0, oy1, z),
             (ix0, iy0, z), (ix1, iy0, z), (ix1, iy1, z), (ix0, iy1, z)]
    faces = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return H.new_mesh_obj(name, verts, faces, coll, mat=mat)
lake_far = frame_mesh("Lake_Far", (-9000.0, 9000.0, -9000.0, 9000.0), (NEAR_X[0], NEAR_X[1], NEAR_Y[0], NEAR_Y[1]), LAKE_Z, "Water", mat_water)

H.purge_orphans()
result = {
    "craghi_verts": len(craghi.data.vertices),
    "crag_verts": len(crag.data.vertices),
    "near_verts": len(near.data.vertices), "far_verts": len(far.data.vertices),
    "lake_near_verts": len(lake_near.data.vertices),
    "z_range_near": [float(Z.min()), float(Z.max())], "z_range_far": [float(ZF.min()), float(ZF.max())],
    "secs": round(time.time() - t_start, 1),
}
