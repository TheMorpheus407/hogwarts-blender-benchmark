"""Boathouse at the waterline + switchback stair climbing the cove cliff,
with lanterns marking the path (key night-shot feature)."""
import bpy
import math
import hog
import hogkit as hk
from mathutils import Vector

hog.clear_coll('Boathouse')
hk.init()
M = hk.M

win_s = hk.window_template('lancet_s', 0.9, 2.4)
win_slit = hk.window_template('slit', 0.55, 1.6, frame_t=0.10, sill=False)

BX, BY = -27.0, -98.0
ROT = math.radians(18)

# ------------------------------------------------------------- boathouse
hog.box('BH_Platform', 'Boathouse', size=(18, 12, 1.6), loc=(BX, BY, -0.3),
        rot=ROT, mat=M['trim'])
hog.box('BH_Body', 'Boathouse', size=(13, 8.5, 5.2), loc=(BX, BY, 1.3),
        rot=ROT, mat=M['wall'])
hk.gable_roof('BH_Roof', 'Boathouse', 13, 8.5, 4.6, (BX, BY, 6.5), rot=ROT,
              overhang=0.6)
# arched water door on the lake-facing gable end (local -X toward lake/SW)
arch = hk.arch_outline(3.4, 2.4, seg=8)
pts = [(3.4 / 2, 0)] + [(x, z + 2.6) for (x, z) in arch] + [(-3.4 / 2, 0)]
hk.prism_xz('BH_Door', 'Boathouse', pts, 0.6,
            loc=(BX - 6.5 * math.cos(ROT), BY - 6.5 * math.sin(ROT), 1.1),
            rot=ROT + math.pi / 2,
            mat=hog.flat_mat('BoathouseInterior', (0.9, 0.45, 0.16), 0.9,
                             emit=0.02))
# side windows
hk.windows_on_rect(win_s, 'Windows', (BX, BY), 13, 8.5, ROT, 'S', [3.2], 3,
                   margin=2.0)
hk.windows_on_rect(win_s, 'Windows', (BX, BY), 13, 8.5, ROT, 'N', [3.2], 3,
                   margin=2.0)
# corner posts + lanterns at the door
hk.place_lantern('Boathouse', (BX - 7.6 * math.cos(ROT) + 2.2 * math.sin(ROT),
                               BY - 7.6 * math.sin(ROT) - 2.2 * math.cos(ROT),
                               1.4))
hk.place_lantern('Boathouse', (BX - 7.6 * math.cos(ROT) - 2.2 * math.sin(ROT),
                               BY - 7.6 * math.sin(ROT) + 2.2 * math.cos(ROT),
                               1.4))
# small wooden jetty
hog.box('BH_Jetty', 'Boathouse', size=(7, 2.4, 0.35),
        loc=(BX - 11 * math.cos(ROT), BY - 11 * math.sin(ROT), 0.15),
        rot=ROT, mat=M['wood'])

# ------------------------------------------------------------- stairs
def stair_flight(name, p0, p1, width=2.6, wall_h=1.1):
    """Solid stair prism from p0 to p1 (steps implied by sawtooth top),
    plus low parapet walls both sides."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    L = Vector((d.x, d.y)).length
    H = d.z
    ang = math.atan2(d.y, d.x)
    nsteps = max(3, int(H / 0.55))
    pts = [(0.0, 0.0)]
    for i in range(nsteps):
        t0 = i / nsteps
        t1 = (i + 1) / nsteps
        pts.append((L * t0, H * t1))
        pts.append((L * t1, H * t1))
    pts += [(L, -2.0), (0.0, -3.2)]
    ob = hk.prism_xz(name, 'Boathouse', pts, width, mat=M['trim'])
    ob.location = (p0.x, p0.y, p0.z)
    ob.rotation_euler = (0, 0, ang)
    # sloped parapet walls on both sides
    for s in (-1, 1):
        pw = hk.prism_xz(f'{name}_par{s}', 'Boathouse',
                         [(0, 0), (0, wall_h), (L, H + wall_h), (L, H - 0.6),
                          (0, -0.6)], 0.4, mat=M['wall'])
        pw.location = (p0.x - math.sin(ang) * s * (width / 2 + 0.2),
                       p0.y + math.cos(ang) * s * (width / 2 + 0.2), p0.z)
        pw.rotation_euler = (0, 0, ang)
    return ob


# switchback path: solve turn points ON the cove face at target heights.
# For each turn i we want height z_i; we march outward from the cove's
# inland center until the terrain surface drops to z_i.
CC = (-30.0, -58.0)          # fan center ON the plateau above the cove


def point_at_height(azimuth_deg, target_z):
    """March outward from CC until the terrain surface drops to target_z."""
    a = math.radians(azimuth_deg)
    dx, dy = math.cos(a), math.sin(a)
    lo, hi = 3.0, 70.0
    for _ in range(30):
        mid = (lo + hi) / 2
        gz = hog.ground_z(CC[0] + dx * mid, CC[1] + dy * mid)
        if gz is None or gz < target_z:
            hi = mid
        else:
            lo = mid
    r = (lo + hi) / 2
    return (CC[0] + dx * r, CC[1] + dy * r)


nturn = 8
pts3 = [(BX + 6.0, BY + 5.0, 1.3)]
for i in range(1, nturn):
    tz = 1.3 + (72.5 - 1.3) * (i / (nturn - 1)) ** 1.1
    az = 243.0 if i % 2 == 0 else 285.0        # alternate across the face
    x, y = point_at_height(az, tz + 2.5)
    pts3.append((x, y, tz))
pts3.append((-34.0, -56.0, 74.2))

for i in range(len(pts3) - 1):
    stair_flight(f'Stair_F{i}', pts3[i], pts3[i + 1])
    lx, ly, lz = pts3[i + 1]
    if i < len(pts3) - 2:
        hog.box(f'Stair_Land_{i}', 'Boathouse', size=(3.8, 3.8, 3.0),
                loc=(lx, ly, lz - 3.0), mat=M['trim'])
        hk.place_lantern('Boathouse', (lx, ly, lz))
hk.place_lantern('Boathouse', (BX + 8 * math.cos(ROT), BY + 8 * math.sin(ROT),
                               1.4))
