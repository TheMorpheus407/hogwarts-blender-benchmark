"""Landscape heightfield: lake basin, castle promontory, eastern gorge, grounds,
moorland hills and the highland mountain ring. Warped grid: ~2 m cells near the
castle, growing to ~80 m at the 9 km edge."""
import bpy, math
from mathutils import Vector, noise
import geo

SEED = Vector((13.1, 71.7, 3.3))


def _n(x, y, s, z=0.0):
    return noise.noise(Vector((x / s, y / s, z)) + SEED)


def fbm(x, y, s, oct=5, z=0.0):
    return noise.fractal(Vector((x / s, y / s, z)) + SEED, 0.55, 2.0, oct)


def ridged(x, y, s, oct=6):
    return noise.ridged_multi_fractal(Vector((x / s, y / s, 0.37)) + SEED, 0.9, 2.1, oct, 1.0, 2.0)


def ell(x, y, cx, cy, rx, ry):
    return (math.sqrt(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2) - 1.0) * min(rx, ry)


def rbox(x, y, cx, cy, hx, hy, r=20.0):
    dx = abs(x - cx) - hx + r
    dy = abs(y - cy) - hy + r
    o = math.hypot(max(dx, 0), max(dy, 0))
    return o + min(max(dx, dy), 0) - r


# ---------------------------------------------------------------- key places
VIADUCT_Y = 42.0
VIADUCT_X0 = 168.0
VIADUCT_X1 = 338.0
EAST_HILL = (400.0, 50.0)
HUT = (-120.0, 430.0)
PITCH = (-620.0, 520.0)
STONES = (420.0, 60.0)

PATHS = [
    # from the viaduct's east end through the stone circle and away east/north-east
    [(338, 42), (372, 50), (410, 64), (455, 90), (520, 120), (600, 170), (700, 240), (820, 300)],
    # north gate down to the grounds, Hagrid's hut and the forest edge
    [(40, 128), (45, 170), (30, 220), (0, 280), (-40, 340), (-90, 400), (-118, 422)],
    # branch to the Quidditch pitch
    [(0, 280), (-120, 300), (-260, 350), (-400, 420), (-520, 480), (-590, 505)],
    # lakeside path west
    [(-90, 400), (-200, 420), (-330, 440), (-460, 430)],
]


def seg_dist(px, py, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def path_dist(x, y):
    d = 1e9
    for pl in PATHS:
        for a, b in zip(pl[:-1], pl[1:]):
            # cheap reject
            if min(a[0], b[0]) - 30 < x < max(a[0], b[0]) + 30 and min(a[1], b[1]) - 30 < y < max(a[1], b[1]) + 30:
                d = min(d, seg_dist(x, y, a, b))
    return d


def lake_sdf(x, y):
    wob = fbm(x, y, 260.0, 4) * 45.0 + _n(x, y, 60.0) * 10.0
    d_main = ell(x, y, 0, -1000, 2400, 1080)
    d_west = ell(x, y, -360, 90, 250, 340)
    d_inlet = rbox(x, y, 268, 80, 42, 330, 30)
    lake = min(d_main, d_west, d_inlet) + wob
    # promontory keeps its land (crag sits on it)
    prom = ell(x, y, 0, 75, 190, 105)
    prom = min(prom, rbox(x, y, 40, 250, 170, 140, 40), ell(x, y, 420, 90, 120, 110))
    prom += _n(x, y, 80.0) * 8.0
    # the gorge must stay open where the viaduct crosses
    return max(lake, -prom) if d_inlet > 5 else lake


def height(x, y):
    d = lake_sdf(x, y)
    if d < 0:
        w = -d
        h = -0.6 - 0.18 * w - 6.0 * geo.smoothstep(15, 120, w)
        h += fbm(x, y, 40.0, 3) * 1.5
        return max(h, -38.0)
    # ---- land
    shore = 0.8 + 9.0 * geo.smoothstep(0, 45, d) + 0.03 * min(d, 600)
    hills = (fbm(x, y, 650.0, 4) * 0.5 + 0.5) * 70.0 * geo.smoothstep(20, 320, d)
    moor = fbm(x, y, 90.0, 3, 1.3) * 2.5 * geo.smoothstep(0, 60, d)
    h = shore + hills + moor
    # mountains ring
    r = math.hypot(x * 0.85, (y + 700) * 1.0)
    mm = geo.smoothstep(1900, 4200, r)
    if mm > 0:
        rid = ridged(x, y, 1500.0, 6)
        h += mm * (rid * 260.0 + 60.0) + mm * mm * 200.0 * (fbm(x, y, 2600, 3) + 0.5)
    # the great hill behind the castle (right of centre from the lake)
    bx, by = x - 700, y - 3400
    h += 380.0 * math.exp(-(bx * bx) / (2 * 900.0 ** 2) - (by * by) / (2 * 650.0 ** 2))
    bx, by = x + 2300, y - 2000
    h += 300.0 * math.exp(-(bx * bx + by * by) / (2 * 800.0 ** 2))
    # east hill where the viaduct lands (stone circle on top)
    ex, ey = x - EAST_HILL[0], y - EAST_HILL[1]
    g = math.exp(-(ex * ex + ey * ey) / (2 * 120.0 ** 2))
    h = geo.lerp(h, 70.0 + fbm(x, y, 30.0, 2) * 3.0, g * geo.smoothstep(0, 140, d) ** 0.7)
    # promontory core under the crag, and the grounds north of the castle
    pc = ell(x, y, 0, 60, 170, 95)
    if pc < 60:
        h = geo.lerp(h, 40.0 + fbm(x, y, 50, 3) * 4.0, geo.smoothstep(60, -20, pc) * geo.smoothstep(0, 30, d))
    gd = rbox(x, y, 20, 300, 230, 170, 60)
    if gd < 120:
        gh = 52.0 - (y - 130) * 0.06 + fbm(x, y, 150, 4) * 7.0
        h = geo.lerp(h, gh, geo.smoothstep(120, 0, gd) * geo.smoothstep(0, 40, d))
    # Quidditch pitch: level oval
    qx, qy = (x - PITCH[0]) / 95.0, (y - PITCH[1]) / 60.0
    qd = math.sqrt(qx * qx + qy * qy)
    if qd < 2.2:
        h = geo.lerp(h, 24.0, geo.smoothstep(2.2, 1.15, qd))
    # paths worn into the ground
    pd = path_dist(x, y)
    if pd < 8:
        h -= 0.35 * geo.smoothstep(8, 1.5, pd)
    return h


def warp(u, a=620.0, b=8400.0):
    return u * a + b * u * u * u


def build(N=760, coll=None):
    coll = coll or geo.get_coll('Terrain')
    verts = []
    us = [-1 + 2 * i / N for i in range(N + 1)]
    xs = [warp(u) for u in us]
    ys = [warp(u) + 150.0 for u in us]
    pmask = []
    fmask = []
    for y in ys:
        for x in xs:
            h = height(x, y)
            verts.append((x, y, h))
            pd = path_dist(x, y)
            pmask.append(geo.smoothstep(6.0, 1.0, pd + _n(x, y, 3.0) * 1.2))
    faces = []
    W = N + 1
    for j in range(N):
        for i in range(N):
            a = j * W + i
            faces.append((a, a + 1, a + W + 1, a + W))
    me = bpy.data.meshes.new('Terrain')
    me.from_pydata(verts, [], faces)
    at = me.attributes.new('path', 'FLOAT', 'POINT')
    at.data.foreach_set('value', pmask)
    me.polygons.foreach_set('use_smooth', [True] * len(faces))
    me.materials.append(bpy.data.materials.get('Ground') or bpy.data.materials.new('Ground'))
    me.update()
    old = bpy.data.objects.get('Terrain')
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    ob = bpy.data.objects.new('Terrain', me)
    coll.objects.link(ob)
    return ob
