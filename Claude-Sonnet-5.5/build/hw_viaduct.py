"""Many-arched stone viaduct."""
import numpy as np
import math
from hw_geo import Geo, boxes, beams, lathe, loft, sweep, prism, pyramid, poly_cap, triangulate_polygon
import hw_walls as W
import hw_gothic as G

STONE = 'M_Stone'
DRESS = 'M_StoneDress'


def _quads_between(g, A, B, m, flip=False):
    """Loft between two (n,3) polylines, quads (A_j, A_j+1, B_j+1, B_j)."""
    P = np.stack([A[:-1], A[1:], B[1:], B[:-1]], axis=1)
    if flip:
        P = P[:, ::-1]
    g.add(P, m)


def elevation_polygon(g, poly2, y, m, facing=-1):
    """Fill a simple x-z polygon at depth y.  facing=-1: normal -y (front seen from the south)."""
    tri = triangulate_polygon(np.asarray(poly2))
    T = np.array(tri)
    P3 = np.column_stack([poly2[:, 0], np.full(len(poly2), y), poly2[:, 1]])
    P = P3[T]
    if facing > 0:
        P = P[:, ::-1]
    g.add(P, m)


def build_viaduct(g, smp, x0, n, y, deck_z, width=7.4, pitch=26.0, pier_w=4.2, water_z=0.0, rng=None):
    rng = rng or np.random.default_rng(5)
    hw = width / 2.0
    r_in = (pitch - pier_w) / 2.0
    r_out = r_in + 1.15
    z_s = deck_z - 1.7 - r_out - 0.35          # springing line
    xs = x0 + pier_w / 2 + np.arange(n + 1) * pitch
    info = dict(piers=[], z_s=z_s)
    for i, xc in enumerate(xs):
        # base height from terrain
        sx = np.array([xc - pier_w, xc, xc + pier_w])
        zz = np.min([smp.z(sx[a], y + b) for a in range(3) for b in (-hw, 0.0, hw)])
        zb = float(min(zz, water_z + 1.0) - 3.0) if zz < 8 else float(zz - 3.0)
        zb = min(zb, z_s - 10.0)
        info['piers'].append((float(xc), zb))
        # rings (x half width w/2, y half hw) from bottom to top with batter and setback
        def rect_ring(dx, dy, z):
            return np.array([[xc - pier_w / 2 - dx, y - hw - dy, z], [xc + pier_w / 2 + dx, y - hw - dy, z],
                             [xc + pier_w / 2 + dx, y + hw + dy, z], [xc - pier_w / 2 - dx, y + hw + dy, z]])
        H = z_s - zb
        z_mid = zb + H * 0.5
        rings = [rect_ring(1.6, 1.0, zb), rect_ring(0.9, 0.5, zb + H * 0.25), rect_ring(0.55, 0.3, z_mid),
                 rect_ring(0.3, 0.15, z_s - H * 0.18), rect_ring(0.0, 0.0, z_s - 1.0)]
        loft(g, np.stack(rings), closed=True, m=STONE, uv_v='z')
        # setback string courses
        for zc_, out in ((z_mid, 0.35), (z_s - H * 0.18, 0.30)):
            path = rect_ring(0.3 if out < 0.32 else 0.55, 0.15 if out < 0.32 else 0.3, zc_)[:, :2]
            path = np.column_stack([path, np.full(4, zc_)])
            sweep(g, np.array([[0.0, -0.3], [out, -0.3], [out, 0.05], [0.0, 0.3]]), path, closed=True, m=DRESS)
        # impost block
        boxes(g, [(xc, y, z_s - 0.9)], [(pier_w + 0.7, width + 0.5, 0.9)], m=DRESS)
        # cutwaters if in water
        if zb < water_z + 4.0:
            zt = water_z + 6.0
            poly = np.array([[xc - pier_w / 2 - 0.3, y - hw - 0.3], [xc, y - hw - 3.3], [xc + pier_w / 2 + 0.3, y - hw - 0.3],
                             [xc + pier_w / 2 + 0.3, y + hw + 0.3], [xc, y + hw + 3.3], [xc - pier_w / 2 - 0.3, y + hw + 0.3]])
            # order must be CCW from above: reorder
            cx_, cy_ = poly.mean(axis=0)
            ang = np.arctan2(poly[:, 1] - cy_, poly[:, 0] - cx_)
            poly = poly[np.argsort(ang)]
            r0 = np.column_stack([poly, np.full(len(poly), zb)])
            r1 = np.column_stack([poly, np.full(len(poly), zt)])
            loft(g, np.stack([r0, r1]), closed=True, m=STONE, uv_v='z')
            # sloped cap
            cap = np.column_stack([cx_ + (poly[:, 0] - cx_) * 0.55, cy_ + (poly[:, 1] - cy_) * 0.55, np.full(len(poly), zt + 0.9)])
            loft(g, np.stack([r1, cap]), closed=True, m=DRESS)
            poly_cap(g, cap, DRESS, up=True)
    # arches + spandrels per span
    for i in range(n):
        xc = 0.5 * (xs[i] + xs[i + 1])
        th = np.linspace(math.pi, 0.0, 25)
        intr = np.column_stack([xc + r_in * np.cos(th), np.full(25, y), z_s + r_in * np.sin(th)])
        extr = np.column_stack([xc + r_out * np.cos(th), np.full(25, y), z_s + r_out * np.sin(th)])
        # soffit (intrados): loft front->back, normal pointing down/inward
        for yy_a, yy_b in ((y - hw, y + hw),):
            A = intr.copy()
            A[:, 1] = yy_a
            B = intr.copy()
            B[:, 1] = yy_b
            # quads (A_j, A_j+1, B_j+1, B_j): E1 along arc (left->right), E2 = +y ; normal = E1 x E2
            # arc runs from angle pi (left) to 0 (right): E1 ~ +x at crown; x cross y = +z (up) -> flip to face down
            _quads_between(g, A, B, DRESS, flip=True)
        # voussoir ring faces (front & back) with alternating relief
        nv = 24
        thv = np.linspace(math.pi, 0.0, nv + 1)
        for k in range(nv):
            rr = 0.05 if k % 2 == 0 else 0.0
            a0, a1 = thv[k], thv[k + 1]
            ri0, ri1 = r_in, r_in
            ro0, ro1 = r_out + rr, r_out + rr
            for yy, fc in ((y - hw - 0.06, -1), (y + hw + 0.06, 1)):
                q = np.array([[xc + r_in * math.cos(a0), yy, z_s + r_in * math.sin(a0)],
                              [xc + r_in * math.cos(a1), yy, z_s + r_in * math.sin(a1)],
                              [xc + ro1 * math.cos(a1), yy, z_s + ro1 * math.sin(a1)],
                              [xc + ro0 * math.cos(a0), yy, z_s + ro0 * math.sin(a0)]])
                # arc runs from left to right; (q0,q1) = along arc, (q0->q3) = outward radial.
                # front (y-side): viewer at -y looking +y sees x to the right: normal = E1 x E2 with E1 ~ +x tangent, E2 radial (up at crown)
                # x cross z = -y  -> faces -y for the front; back needs flipping
                g.add(q[None] if fc < 0 else q[None, ::-1], DRESS)
        # spandrel polygon between pier centre lines, front and back
        xl, xr = xs[i], xs[i + 1]
        pts = [(xl, z_s - 0.9), (xc - r_out, z_s - 0.9), (xc - r_out, z_s)]
        thp = np.linspace(math.pi, 0.0, 22)[1:-1]
        pts += [(xc + r_out * math.cos(t), z_s + r_out * math.sin(t)) for t in thp]
        pts += [(xc + r_out, z_s), (xc + r_out, z_s - 0.9), (xr, z_s - 0.9), (xr, deck_z), (xl, deck_z)]
        poly = np.array(pts)
        area = 0.5 * np.sum(poly[:, 0] * np.roll(poly[:, 1], -1) - np.roll(poly[:, 0], -1) * poly[:, 1])
        if area < 0:
            poly = poly[::-1]
        # (viewer at -y: x right, z up, CCW polygon faces -y)
        elevation_polygon(g, poly, y - hw, STONE, facing=-1)
        elevation_polygon(g, poly, y + hw, STONE, facing=+1)
        # inner skins (the masonry has a thickness: looking through an arch you see proper faces, not the back of the skin)
        elevation_polygon(g, poly, y - hw + 0.5, STONE, facing=+1)
        elevation_polygon(g, poly, y + hw - 0.5, STONE, facing=-1)
    # deck, string course under it, parapets
    xa, xb = xs[0] - pier_w / 2, xs[-1] + pier_w / 2
    # string course below deck edge
    for sd in (-1, 1):
        boxes(g, [((xa + xb) / 2, y + sd * (hw + 0.1), deck_z - 1.3)], [(xb - xa + 0.2, 0.55, 0.5)], m=DRESS)
    # deck slab top (cobbles)
    g.add(np.array([[[xa, y - hw, deck_z], [xb, y - hw, deck_z], [xb, y + hw, deck_z], [xa, y + hw, deck_z]]]), 'M_Cobble')
    # deck underside is closed by the spandrel tops (thin) ; parapet walls
    for sd in (-1, 1):
        yc = y + sd * (hw - 0.3)
        boxes(g, [((xa + xb) / 2, yc, deck_z)], [(xb - xa, 0.65, 1.1)], m=STONE)
        boxes(g, [((xa + xb) / 2, yc, deck_z + 1.1)], [(xb - xa + 0.1, 0.9, 0.16)], m=DRESS)
        # pilasters every half pitch + lantern posts over piers
        px = np.arange(xa + 3.0, xb - 2.0, pitch / 2)
        boxes(g, np.column_stack([px, np.full(len(px), yc), np.full(len(px), deck_z)]), [(0.9, 1.0, 1.6)], m=STONE)
        boxes(g, np.column_stack([px, np.full(len(px), yc), np.full(len(px), deck_z + 1.6)]), [(1.1, 1.2, 0.18)], m=DRESS)
    # lantern posts every pitch on the parapet (over each pier)
    post = W.lantern_post(2.6)
    for sd in (-1, 1):
        yc = y + sd * (hw - 0.3)
        for ii, xp in enumerate(xs):
            g.add_geo(post, pos=(xp, yc, deck_z + 1.78))
            if ii % 2 == (0 if sd < 0 else 1):
                W.reg('viaduct', xp, yc, deck_z + 1.78 + 2.35)
    return info
