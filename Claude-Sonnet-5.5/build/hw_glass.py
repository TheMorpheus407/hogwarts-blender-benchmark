"""Greenhouses: glass + iron frame structures with lit plants inside."""
import numpy as np
import math
from hw_geo import Geo, boxes, beams, lathe, loft, sweep, pyramid, poly_cap, rotz, triangulate_polygon
import hw_gothic as G
import hw_towers as TW
import hw_walls as W

GLASS = 'M_Glass'
FRAME = 'M_IronPaint'
STONE = 'M_Stone'
DRESS = 'M_StoneDress'
PLANT = 'M_Foliage'


def plant_cluster(g, x, y, z, rng, size=1.0, n=5):
    for k in range(n):
        a = rng.random() * 2 * math.pi
        r = rng.random() * 0.9 * size
        h = (0.9 + 1.6 * rng.random()) * size
        rr = (0.45 + 0.5 * rng.random()) * size
        prof = [(0.05, 0.0), (rr * 0.6, h * 0.25), (rr, h * 0.55), (rr * 0.7, h * 0.85), (0.0, h)]
        lathe(g, prof, (x + r * math.cos(a), y + r * math.sin(a), z), segs=7, m=PLANT, uv_v='z')
    # planter box under
    boxes(g, [(x, y, z - 0.02)], [(1.6 * size + 0.6, 1.2 * size + 0.6, 0.35)], m='M_Stone')


def arch_section(w, h_wall, rise, n=15):
    """Cross-section polyline (x,z): left base -> wall top -> elliptical arch -> right wall top -> right base."""
    a = w / 2.0
    th = np.linspace(math.pi, 0.0, n)
    arc = np.column_stack([a * np.cos(th), h_wall + rise * np.sin(th)])
    pts = np.vstack([[[-a, 0.0]], arc, [[a, 0.0]]])
    return pts


def barrel_house(g, cx, cy, z0, L, W_, h_wall, rise, rng, yaw=0.0, n_ribs=None, plants=True):
    """Barrel-vaulted conservatory along local Y (length L), width W_, centred at (cx,cy)."""
    sec = arch_section(W_, h_wall, rise)
    n_ribs = n_ribs or max(3, int(L / 2.6))
    ys = np.linspace(-L / 2, L / 2, n_ribs + 1)
    rings = []
    for yy in ys:
        rings.append(np.column_stack([sec[:, 0], np.full(len(sec), yy), sec[:, 1] + 0.9]))   # +0.9 sits on the plinth
    rings = np.stack(rings)
    # glass: loft with rings along Y; cross-section = axis 1  -> transpose so that axis0 = along y? loft: axis0 rings, axis1 points
    # we need E1 along the cross-section (left->right) and E2 along +y : rings ordered along y with points across -> exactly (k=n_ribs+1, n=len(sec))
    Gt = Geo('gh_tmp', [GLASS, FRAME, STONE, PLANT])
    loft(Gt, rings, closed=False, m=GLASS, flip=False)
    # ribs
    for k in range(len(ys)):
        pts = rings[k]
        c = pts[:-1] + np.array([0, 0, 0.0])
        offs = np.zeros_like(pts)
        offs[:, 0] = np.sign(pts[:, 0]) * 0.0
        beams(Gt, pts[:-1], pts[1:], 0.11, 0.13, m=FRAME)
    # purlins along Y
    for j in range(0, len(sec), 2):
        a = rings[0, j].copy()
        b = rings[-1, j].copy()
        beams(Gt, [a], [b], 0.07, 0.07, m=FRAME)
    # plinth (stone) and end walls (glass arches with bars)
    boxes(Gt, [(0, 0, -6.0)], [(W_ + 0.8, L + 0.8, 6.9)], m=STONE, faces=(0, 1, 2, 3))
    boxes(Gt, [(0, 0, 0.9)], [(W_ + 1.0, L + 1.0, 0.16)], m=DRESS, faces=(4,))
    for ysgn, yy in ((-1, -L / 2), (1, L / 2)):
        sec3 = np.column_stack([sec[:, 0], np.full(len(sec), yy), sec[:, 1] + 0.9])
        # end glass: fan from the base line
        top_poly = sec3[::-1]                      # CCW in (x, z)
        poly2 = np.column_stack([top_poly[:, 0], top_poly[:, 2]])
        idx = np.array(triangulate_polygon(poly2), dtype=int)
        F = top_poly[idx]
        n0 = np.cross(F[0, 1] - F[0, 0], F[0, 2] - F[0, 0])
        if (n0[1] * ysgn) < 0:
            F = F[:, ::-1]
        Gt.add(F, GLASS)
        # vertical mullions on the end wall
        for xx in np.linspace(-W_ / 2, W_ / 2, 7):
            zt = h_wall + rise * math.sqrt(max(0.0, 1 - (2 * xx / W_) ** 2))
            beams(Gt, [(xx, yy, 0.9)], [(xx, yy, zt + 0.9)], 0.07, 0.09, m=FRAME)
        beams(Gt, [(-W_ / 2, yy, 0.9 + h_wall * 0.5)], [(W_ / 2, yy, 0.9 + h_wall * 0.5)], 0.07, 0.09, m=FRAME)
    # ridge cap
    beams(Gt, [(0, -L / 2, h_wall + rise + 0.95)], [(0, L / 2, h_wall + rise + 0.95)], 0.22, 0.2, m=FRAME)
    # plants inside
    if plants:
        for k in range(int(L / 3.6)):
            for side in (-1, 1):
                plant_cluster(Gt, side * W_ * 0.28, -L / 2 + 1.8 + k * 3.6, 1.05, rng, 1.0, 4)
        boxes(Gt, [(0, 0, 1.0)], [(1.4, L - 2, 0.02)], m='M_Cobble', faces=(4,))
    g.add_geo(Gt, pos=(cx, cy, z0), yaw=yaw)


def dome_house(g, cx, cy, z0, R, h_wall, dome_h, rng, n_mer=14):
    Gt = Geo('dome_tmp', [GLASS, FRAME, STONE, PLANT])
    # plinth
    lathe(Gt, [(R + 0.7, -8.0), (R + 0.7, 0.9), (R + 0.3, 1.05)], (0, 0, 0), segs=28, m=STONE)
    # glass walls
    lathe(Gt, [(R, 0.9), (R, 0.9 + h_wall)], (0, 0, 0), segs=n_mer * 2, m=GLASS, smooth=False, yaw0=0.0)
    # dome (elliptical)
    ph = np.linspace(0.0, math.pi / 2, 10)
    prof = np.column_stack([R * np.cos(ph), 0.9 + h_wall + dome_h * np.sin(ph)])
    lathe(Gt, prof, (0, 0, 0), segs=n_mer * 2, m=GLASS, smooth=False)
    # meridian ribs + wall mullions
    for k in range(n_mer * 2):
        a = 2 * math.pi * k / (n_mer * 2)
        pts = [np.array([(R + 0.03) * math.cos(a), (R + 0.03) * math.sin(a), 0.9]),
               np.array([(R + 0.03) * math.cos(a), (R + 0.03) * math.sin(a), 0.9 + h_wall])]
        for p_ in prof[1:]:
            pts.append(np.array([(p_[0] + 0.05) * math.cos(a), (p_[0] + 0.05) * math.sin(a), p_[1] + 0.03]))
        pts = np.array(pts)
        beams(Gt, pts[:-1], pts[1:], 0.09, 0.11, m=FRAME)
    # latitude rings
    for zr, rr in [(0.9 + h_wall, R + 0.05)] + [(p_[1] + 0.03, p_[0] + 0.05) for p_ in prof[2:8:2]]:
        lathe(Gt, [(rr, zr - 0.06), (rr + 0.06, zr - 0.06), (rr + 0.06, zr + 0.06), (rr, zr + 0.06)], (0, 0, 0), segs=n_mer * 2, m=FRAME, smooth=False)
    # cap + finial
    lathe(Gt, [(0.6, 0.9 + h_wall + dome_h - 0.2), (0.35, 0.9 + h_wall + dome_h + 0.6), (0.0, 0.9 + h_wall + dome_h + 0.9)],
          (0, 0, 0), segs=10, m=FRAME)
    Gt.add_geo(G.finial(2.6, 0.24, 'M_Copper'), pos=(0, 0, 0.9 + h_wall + dome_h + 0.5))
    # plants and centre palm
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        plant_cluster(Gt, 0.55 * R * math.cos(a), 0.55 * R * math.sin(a), 1.0, rng, 0.9, 3)
    prof = [(0.25, 0.0), (0.2, 3.5), (0.9, 5.6), (1.6, 6.2), (0.8, 7.0), (0.0, 7.6)]
    lathe(Gt, prof, (0, 0, 1.0), segs=8, m=PLANT)
    g.add_geo(Gt, pos=(cx, cy, z0))


def lean_to(g, cx, cy, z0, L, D, h_front, h_back, rng, yaw=0.0):
    """Shed-roof glasshouse: front (south, -y local) low, back wall (north) high, ridge along x."""
    Gt = Geo('lean_tmp', [GLASS, FRAME, STONE, PLANT])
    xs = np.linspace(-L / 2, L / 2, max(3, int(L / 1.9)) + 1)
    zf, zb = h_front + 0.9, h_back + 0.9
    # roof glass
    roof = np.array([[[-L / 2, -D / 2, zf], [L / 2, -D / 2, zf], [L / 2, D / 2, zb], [-L / 2, D / 2, zb]]])
    Gt.add(roof, GLASS)
    # front glass wall
    Gt.add(np.array([[[-L / 2, -D / 2, 0.9], [L / 2, -D / 2, 0.9], [L / 2, -D / 2, zf], [-L / 2, -D / 2, zf]]]), GLASS)
    # side glass triangles/quads
    for sx in (-1, 1):
        q = np.array([[sx * L / 2, -D / 2, 0.9], [sx * L / 2, D / 2, 0.9], [sx * L / 2, D / 2, zb], [sx * L / 2, -D / 2, zf]])
        if sx < 0:
            q = q[::-1]
        Gt.add(q[None], GLASS)
    for xx in xs:
        beams(Gt, [(xx, -D / 2, 0.9)], [(xx, -D / 2, zf)], 0.08, 0.1, m=FRAME)
        beams(Gt, [(xx, -D / 2, zf)], [(xx, D / 2, zb)], 0.08, 0.12, m=FRAME)
    for zz in np.linspace(0.9, zf, 3):
        beams(Gt, [(-L / 2, -D / 2, zz)], [(L / 2, -D / 2, zz)], 0.06, 0.07, m=FRAME)
    for t in (0.33, 0.66):
        beams(Gt, [(-L / 2, -D / 2 + D * t, zf + (zb - zf) * t)], [(L / 2, -D / 2 + D * t, zf + (zb - zf) * t)], 0.07, 0.09, m=FRAME)
    boxes(Gt, [(0, 0, -6.0)], [(L + 0.8, D + 0.8, 6.9)], m=STONE, faces=(0, 1, 2, 3))
    boxes(Gt, [(0, 0, 0.9)], [(L + 1.0, D + 1.0, 0.14)], m=DRESS, faces=(4,))
    for k in range(int(L / 3.2)):
        plant_cluster(Gt, -L / 2 + 1.6 + k * 3.2, 0.0, 1.05, rng, 0.9, 3)
    g.add_geo(Gt, pos=(cx, cy, z0), yaw=yaw)
