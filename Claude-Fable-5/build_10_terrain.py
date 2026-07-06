"""Terrain v3: crag promontory, gorge, east ridge, lake bed, moorland,
ridged-fractal mountains, lake. Emits vertex groups (cliff/forest/path)
and applies crag displacement so later scripts can ray-cast the real surface."""
import bpy
import math
import numpy as np
from mathutils import noise
import hog

hog.clear_coll('Terrain')

# ------------------------------------------------------------------ helpers
def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def fract_noise(xs, ys, scale, octaves, seed_z):
    out = np.empty(xs.shape[0])
    fn = noise.fractal
    for i in range(xs.shape[0]):
        out[i] = fn((xs[i] * scale, ys[i] * scale, seed_z), 1.0, 2.0, octaves)
    return out


def ridged_noise(xs, ys, scale, octaves, seed_z):
    """Ridged multifractal-ish: sharp crests."""
    out = np.zeros(xs.shape[0])
    amp, freq = 1.0, scale
    total = 0.0
    fn = noise.noise
    for o in range(octaves):
        layer = np.empty(xs.shape[0])
        for i in range(xs.shape[0]):
            layer[i] = fn((xs[i] * freq, ys[i] * freq, seed_z + o * 13.7))
        out += amp * (1.0 - np.abs(layer)) ** 2
        total += amp
        amp *= 0.52
        freq *= 2.05
    return out / total


def make_grid_object(name, xs2d, ys2d, zs2d, cname, mat):
    ny, nx = zs2d.shape
    nverts = nx * ny
    cos = np.empty((nverts, 3))
    cos[:, 0] = xs2d.ravel()
    cos[:, 1] = ys2d.ravel()
    cos[:, 2] = zs2d.ravel()
    me = bpy.data.meshes.new(name)
    me.vertices.add(nverts)
    me.vertices.foreach_set('co', cos.ravel())
    nfx, nfy = nx - 1, ny - 1
    nfaces = nfx * nfy
    ii, jj = np.meshgrid(np.arange(nfx), np.arange(nfy))
    v0 = (jj * nx + ii).ravel()
    idx = np.empty((nfaces, 4), dtype=np.int64)
    idx[:, 0] = v0
    idx[:, 1] = v0 + 1
    idx[:, 2] = v0 + nx + 1
    idx[:, 3] = v0 + nx
    me.loops.add(nfaces * 4)
    me.polygons.add(nfaces)
    me.polygons.foreach_set('loop_start',
                            (np.arange(nfaces) * 4).astype(np.int64).ravel())
    me.polygons.foreach_set('loop_total',
                            np.full(nfaces, 4, dtype=np.int64).ravel())
    me.loops.foreach_set('vertex_index', idx.ravel())
    me.update()
    me.validate()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    hog.coll(cname).objects.link(ob)
    me.materials.append(mat)
    return ob


def add_vgroup(ob, name, weights, levels=24):
    """Quantized weight assignment (fast)."""
    vg = ob.vertex_groups.new(name=name)
    w = np.clip(weights, 0.0, 1.0)
    q = np.round(w * levels).astype(np.int32)
    for lv in range(1, levels + 1):
        idx = np.nonzero(q == lv)[0]
        if len(idx):
            vg.add(idx.tolist(), lv / levels, 'REPLACE')
    return vg


# ------------------------------------------------------------------ main terrain
N = 460
SIZE = 1400.0
cx, cy = 0.0, 80.0
lin = np.linspace(-SIZE / 2, SIZE / 2, N)
X, Y = np.meshgrid(lin + cx, lin + cy)
xf, yf = X.ravel(), Y.ravel()

n_coarse = fract_noise(xf, yf, 0.008, 3, 3.3)
n_med = fract_noise(xf, yf, 0.03, 4, 7.7)
n_moor = fract_noise(xf, yf, 0.004, 4, 0.0)

base = 5.0 + 13.0 * n_moor
base += np.maximum(0.0, (yf - 300.0) * 0.06)
base += np.maximum(0.0, (np.abs(xf) - 480.0) * 0.05)

shore_y = -48.0 + 26.0 * np.sin(xf * 0.006 + 1.2)
lake_mask = smoothstep(shore_y, shore_y - 90.0, yf)
h = base * (1 - lake_mask) + (-9.0) * lake_mask

# --- promontory (castle crag) ---
PROM_RX, PROM_RY, PROM_CY = 118.0, 88.0, 14.0
pr = np.sqrt((xf / PROM_RX) ** 2 + ((yf - PROM_CY) / PROM_RY) ** 2)
pr_n = pr + 0.085 * n_coarse + 0.05 * n_med
cove = np.exp(-(((xf + 30.0) / 26.0) ** 2 + ((yf + 92.0) / 22.0) ** 2))
pr_n += 0.22 * cove
prom_mask = smoothstep(1.02, 0.82, pr_n)
prom_h = 75.0 * prom_mask ** 0.5
cliff_band = smoothstep(0.03, 0.25, prom_mask) * \
    (1 - smoothstep(0.85, 0.97, prom_mask))
ledges = np.abs(np.sin(prom_h * 0.22 + 2.5 * n_med)) * 7.0
prom_h -= ledges * cliff_band
prom_h += n_med * cliff_band * 10.0
h = np.maximum(h, prom_h)

# --- east ridge ---
er = np.sqrt(((xf - 215.0) / 72.0) ** 2 + ((yf - 5.0) / 92.0) ** 2)
er_n = er + 0.10 * n_coarse + 0.05 * n_med
er_mask = smoothstep(1.05, 0.72, er_n)
er_h = 54.0 * er_mask ** 0.55
er_band = smoothstep(0.05, 0.3, er_mask) * (1 - smoothstep(0.8, 0.95, er_mask))
er_h -= np.abs(np.sin(er_h * 0.25 + 2.0 * n_med)) * 3.5 * er_band
h = np.maximum(h, er_h)

# --- gorge (flooded inlet) ---
gorge_g = np.exp(-(((xf - 138.0) / 26.0) ** 2))
gorge_fade = 1.0 - smoothstep(40.0, 120.0, yf)
cut = smoothstep(0.22, 0.7, gorge_g) * gorge_fade
h = h * (1 - cut) + (-5.0) * cut

# --- plateau flatten ---
plateau = smoothstep(0.9, 0.985, prom_mask)
h = h * (1 - plateau) + 75.0 * plateau

# --- viaduct-gate shelf ---
shelf = np.exp(-(((xf - 100.0) / 16.0) ** 2 + ((yf + 6.0) / 14.0) ** 2))
shelf = smoothstep(0.3, 0.7, shelf)
h = h * (1 - shelf) + 58.0 * shelf

# --- greenhouse terrace ---
terr = np.exp(-(((xf - 52.0) / 26.0) ** 2 + ((yf + 72.0) / 18.0) ** 2))
terr = smoothstep(0.35, 0.75, terr)
h = h * (1 - terr) + 56.0 * terr

# --- worn paths: north gate -> NE forest; viaduct -> over east ridge ---
path_pts = [(-5.0, 66.0), (14.0, 96.0), (36.0, 140.0), (70.0, 190.0),
            (110.0, 248.0), (160.0, 310.0)]
path_pts2 = [(174.0, -4.0), (205.0, 30.0), (232.0, 110.0), (255.0, 230.0)]
path_d = np.full(xf.shape, 1e9)
for pts_list in (path_pts, path_pts2):
    for i in range(len(pts_list) - 1):
        (ax, ay), (bx, by) = pts_list[i], pts_list[i + 1]
        abx, aby = bx - ax, by - ay
        L2 = abx * abx + aby * aby
        t = np.clip(((xf - ax) * abx + (yf - ay) * aby) / L2, 0, 1)
        dx = xf - (ax + t * abx)
        dy = yf - (ay + t * aby)
        path_d = np.minimum(path_d, np.sqrt(dx * dx + dy * dy))
path_w = 1.0 - smoothstep(1.6, 4.5, path_d)
# gently smooth terrain along the path
h = h * (1 - 0.25 * path_w) + (h - 0.4) * 0.25 * path_w

# ------------------------------------------------------------ weights
slope_proxy = cliff_band + er_band + smoothstep(0.4, 0.75, cut)
forest_clump = fract_noise(xf, yf, 0.012, 3, 21.0)
forest_w = (smoothstep(1.5, 4.0, h) *                 # above waterline
            (1 - smoothstep(55.0, 85.0, h)) *         # thins at altitude
            (1 - slope_proxy) *
            (1 - smoothstep(0.5, 0.8, prom_mask)) *   # off the castle rock
            (1 - 0.8 * smoothstep(0.5, 0.85, er_mask)) *
            (1 - path_w) *
            np.clip(0.35 + 0.9 * forest_clump, 0, 1))
# clear a corridor along the viaduct approach and gorge rim
via_cx = smoothstep(85.0, 100.0, xf) * (1 - smoothstep(178.0, 195.0, xf))
via_cy = smoothstep(-26.0, -16.0, yf) * (1 - smoothstep(8.0, 18.0, yf))
forest_w = forest_w * (1 - via_cx * via_cy)
# moor grass gets the rest of the land
grass_w = smoothstep(0.8, 2.5, h) * (1 - slope_proxy * 0.7)

Z = h.reshape(N, N)
ter = make_grid_object('Terrain_Main', X, Y, Z, 'Terrain', hog.mat_rock())
add_vgroup(ter, 'cliff', slope_proxy)
add_vgroup(ter, 'forest', forest_w)
add_vgroup(ter, 'grass', grass_w)
# float attributes for the material pass
for aname, arr in (('path_w', path_w), ('cliff_w', slope_proxy),
                   ('forest_w', forest_w)):
    at = ter.data.attributes.new(name=aname, type='FLOAT', domain='POINT')
    at.data.foreach_set('value', arr.ravel())

# ---------------------------------------------------- crag displacement
# jagged voronoi facets + fine roughness, cliff-band only, then applied
tex1 = bpy.data.textures.get('CragVoro') or bpy.data.textures.new('CragVoro', 'VORONOI')
tex1.noise_scale = 26.0
tex1.distance_metric = 'DISTANCE_SQUARED'
tex2 = bpy.data.textures.get('CragFine') or bpy.data.textures.new('CragFine', 'CLOUDS')
tex2.noise_scale = 7.0
tex2.noise_depth = 3

md1 = ter.modifiers.new('CragVoro', 'DISPLACE')
md1.texture = tex1
md1.strength = 6.0
md1.mid_level = 0.5
md1.direction = 'NORMAL'
md1.vertex_group = 'cliff'
md2 = ter.modifiers.new('CragFine', 'DISPLACE')
md2.texture = tex2
md2.strength = 2.2
md2.mid_level = 0.5
md2.direction = 'NORMAL'
md2.vertex_group = 'cliff'
# apply so ray-casts and scatter see the final surface
bpy.context.view_layer.objects.active = ter
ter.select_set(True)
bpy.ops.object.modifier_apply(modifier='CragVoro')
bpy.ops.object.modifier_apply(modifier='CragFine')
ter.select_set(False)

# ------------------------------------------------------------------ mountains
def mountain_ridge(name, y_dist, width, amp, seed, x_span=4200.0,
                   nx=620, ny=80):
    lx = np.linspace(-x_span / 2, x_span / 2, nx)
    ly = np.linspace(-width / 2, width / 2, ny)
    MX, MY = np.meshgrid(lx, ly)
    xr, yr = MX.ravel(), MY.ravel()
    rid = ridged_noise(xr, yr + y_dist, 1.0 / 620.0, 5, seed)
    rid2 = fract_noise(xr, yr + y_dist, 1.0 / 90.0, 4, seed + 5)
    env = np.exp(-((yr / (width * 0.38)) ** 2))
    hgt = rid * amp * env * (0.55 + 0.45 * np.sin(xr / 700.0 + seed)) ** 0.5
    hgt += rid2 * amp * 0.07 * env
    MZ = hgt.reshape(ny, nx)
    ob = make_grid_object(name, MX, MY + y_dist, MZ, 'Terrain',
                          hog.mat_rock())
    return ob


mountain_ridge('Mountains_Near', 1000.0, 800.0, 420.0, 11.0)
mountain_ridge('Mountains_Mid', 1650.0, 1000.0, 640.0, 23.0)
mountain_ridge('Mountains_Far', 2500.0, 1300.0, 900.0, 5.0)
mountain_ridge('Hills_West', 430.0, 520.0, 240.0, 31.0, x_span=1700.0)
bpy.data.objects['Hills_West'].location.x = -950.0
mountain_ridge('Hills_East', 400.0, 520.0, 260.0, 17.0, x_span=1700.0)
bpy.data.objects['Hills_East'].location.x = 980.0

# ------------------------------------------------------------------ lake
# deep box so the water volume actually absorbs light with depth
lake = hog.box('Lake', 'Terrain', size=(6000, 6000, 14), loc=(0, -400, -6.65),
               base=False, mat=hog.mat_water())
