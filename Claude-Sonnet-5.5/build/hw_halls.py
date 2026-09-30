"""Hall / gallery / gatehouse generators (rectangular Gothic masses)."""
import numpy as np
import math
from hw_geo import (Geo, boxes, beams, lathe, loft, sweep, prism, pyramid, ngon, poly_cap, xf, rotz,
                    pointed_arch, offset_outline, wall_fill, frame_ring)
import hw_gothic as G
import hw_arch as A
import hw_towers as TW

STONE = 'M_Stone'
DRESS = 'M_StoneDress'
SLATE = 'M_Slate'
COPPER = 'M_Copper'
_PROTO = {}


def blind_arch(w=0.9, h=1.7):
    key = ('blind', round(w, 2), round(h, 2))

    def build():
        g = Geo('blind', [DRESS])
        O = pointed_arch(w, h - w * 0.95, w * 0.95, n=5)
        O2 = offset_outline(O, 0.14)
        frame_ring(g, O2, O, -0.16, 0.2, DRESS, y_inner_back=-0.02)
        wall_fill(g, O, -0.02, DRESS)
        return g
    return G.cached(key, build)


def chimney(g, x, y, z, w=2.0, h=9.0, pots=3, mat=STONE):
    boxes(g, [(x, y, z)], [(w, w * 0.9, h)], m=mat)
    boxes(g, [(x, y, z + h)], [(w + 0.5, w * 0.9 + 0.5, 0.45)], m=DRESS)
    boxes(g, [(x, y, z + h - 1.6)], [(w + 0.4, w * 0.9 + 0.4, 0.3)], m=DRESS)
    for k in range(pots):
        px = x + (k - (pots - 1) / 2.0) * (w / max(pots, 1)) * 0.9
        prof = [(0.32, 0.0), (0.30, 0.9), (0.40, 1.0), (0.40, 1.5), (0.30, 1.55), (0.0, 1.55)]
        lathe(g, prof, (px, y, z + h + 0.45), segs=8, m='M_Brick')


def cresting(g, x0, x1, y, z, spacing=2.4, h=0.9, rng=None):
    xs = np.arange(x0 + spacing / 2, x1, spacing)
    for xx in xs:
        base = np.array([[xx - 0.28, y - 0.14, z], [xx + 0.28, y - 0.14, z], [xx + 0.28, y + 0.14, z],
                         [xx - 0.28, y + 0.14, z]])
        pyramid(g, base, (xx, y, z + h * (0.85 + 0.3 * (rng.random() if rng else 0.5))), COPPER)


def flying_buttress(g, x, y_wall, out_sign, z_pier_top, z_wall, dist, w=1.1, th=0.8, mat=STONE, pin_h=6.0):
    """Pier at horizontal distance `dist` from a wall at y_wall (out_sign=+1 north side, -1 south) + arch."""
    yp = y_wall + out_sign * dist
    # pier
    boxes(g, [(x, yp, z_pier_top - 22.0)], [(w * 1.5, 2.0, 22.0)], m=mat, faces=(0, 1, 2, 3, 4))
    g.add_geo(G.pinnacle_free(pin_h, 1.2), pos=(x, yp, z_pier_top))
    # arch (quadratic bezier from pier to wall)
    P0 = np.array([x, yp - out_sign * 0.4, z_pier_top - 1.2])
    P1 = np.array([x, y_wall + out_sign * 0.2, z_wall])
    Pc = (P0 + P1) / 2 + np.array([0, 0, 3.0])
    ts = np.linspace(0, 1, 12)
    pts = ((1 - ts) ** 2)[:, None] * P0 + (2 * (1 - ts) * ts)[:, None] * Pc + (ts ** 2)[:, None] * P1
    tang = np.gradient(pts, axis=0)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    side = np.array([1.0, 0, 0])
    up = np.cross(side, tang)
    up /= np.linalg.norm(up, axis=1, keepdims=True)
    rings = []
    for k in range(len(pts)):
        c = pts[k]
        rr = np.array([c - side * w / 2 - up[k] * th / 2, c + side * w / 2 - up[k] * th / 2,
                       c + side * w / 2 + up[k] * th / 2, c - side * w / 2 + up[k] * th / 2])
        rings.append(rr)
    rings = np.stack(rings)
    # rings ordered along path; loft expects (k rings, n points)
    loft(g, rings, closed=True, m=mat, flip=(out_sign > 0))


def gothic_hall(g, cx, cy, L, D, z0, eaves, pitch, rng, bay_w=10.0, found=28.0, lit_p=0.6, south=True, north=True,
                ends=True, buttresses=True, dormers=True, chimneys=0, big=(2.5, 10.6), sill_z=10.2, low_win=True,
                frieze=True, corner_turrets=False, cresting_on=True, north_lit=0.35, flying=False, end_window=True,
                wall_mat=STONE, roof_mat=SLATE, dormer_every=1, low_z=4.4, rows=None):
    """Long hall with its ridge along X.  Faces the viewer on the south side.  Returns dict(ridge, z_eave)."""
    x0, x1 = cx - L / 2, cx + L / 2
    ys, yn = cy - D / 2, cy + D / 2
    z_wall = z0 + eaves + 0.6
    boxes(g, [(cx, cy, z0 - found)], [(L, D, found + eaves + 0.6)], m=wall_mat, faces=(0, 1, 2, 3, 4))
    # plinth
    for (yy, sgn) in ((ys, -1), (yn, 1)):
        boxes(g, [(cx, yy + sgn * 0.3, z0 - found)], [(L + 1.0, 0.9, found + 3.0)], m=wall_mat, faces=(0, 1, 2, 3, 4))
    # string courses around the footprint
    poly = np.array([[x0, ys], [x1, ys], [x1, yn], [x0, yn]])
    for zb in (3.0, sill_z - 0.9, eaves - 3.4):
        path = np.column_stack([poly, np.full(4, z0 + zb)])
        prof = np.array([[0.0, -0.3], [0.45, -0.3], [0.45, 0.12], [0.0, 0.45]])
        sweep(g, prof, path, closed=True, m=DRESS)
    nb = max(1, int(round(L / bay_w)))
    bw = L / nb
    bx = x0 + (np.arange(nb) + 0.5) * bw
    big_w, big_h = big
    for side_i, (yy, oy, do_side, lp) in enumerate(((ys, -1.0, south, lit_p), (yn, 1.0, north, north_lit))):
        if not do_side:
            continue
        # buttresses
        if buttresses:
            bxs = x0 + np.arange(nb + 1) * bw
            for k, xb in enumerate(bxs):
                if (k == 0 or k == nb) and corner_turrets:
                    continue
                pr = G.buttress(z0 - 4.0, z0 + eaves - 0.5, 1.7, 2.5, stages=3, pinnacle=True, pin_h=6.5)
                g.add_geo(pr, pos=(xb, yy, 0.0), outward=(0.0, oy))
        # windows per bay
        big_proto = G.window_lancet(big_w, big_h, 2)
        low_proto = G.window_lancet(1.2, 2.3, 1, molding=False)
        for xc in bx:
            if rows is None or 'big' in rows:
                g.add_geo(big_proto, pos=(xc, yy, z0 + sill_z), outward=(0, oy), lit=TW.pick_lit(rng, lp), rng=rng)
            if low_win:
                g.add_geo(low_proto, pos=(xc, yy, z0 + low_z), outward=(0, oy), lit=TW.pick_lit(rng, lp * 0.8), rng=rng)
        # blind arch frieze
        if frieze:
            ba = blind_arch(0.9, 1.9)
            n_f = int(L / 1.9)
            for k in range(n_f):
                xf_ = x0 + 1.4 + k * (L - 2.8) / max(n_f - 1, 1)
                g.add_geo(ba, pos=(xf_, yy, z0 + eaves - 3.0), outward=(0, oy))
        # corbel table
        nco = int(L / 1.5)
        xs_c = x0 + (np.arange(nco) + 0.5) * L / nco
        for i, (o, hh) in enumerate(((0.45, 0.32), (0.85, 0.32), (1.25, 0.34))):
            zc = z0 + eaves - 1.0 + i * 0.34 - 0.0
            C = np.column_stack([xs_c, np.full(nco, yy + oy * (o - 0.35) / 2.0), np.full(nco, zc)])
            boxes(g, C, [(0.62, o + 0.35, hh)], m=DRESS)
        # parapet base + merlons
        zp = z0 + eaves + 0.1
        boxes(g, [(cx, yy + oy * 0.62, zp)], [(L + 1.2, 0.9, 0.9)], m=wall_mat)
        nm = int(L / 2.2)
        xs_m = x0 + (np.arange(nm) + 0.5) * L / nm
        C = np.column_stack([xs_m, np.full(nm, yy + oy * 0.62), np.full(nm, zp + 0.9)])
        boxes(g, C, [(L / nm * 0.56, 0.9, 1.25)], m=wall_mat)
        boxes(g, C + np.array([0, 0, 1.25]), [(L / nm * 0.56 + 0.15, 1.05, 0.14)], m=DRESS)
    # end walls
    if ends:
        for xe, ox in ((x0, -1.0), (x1, 1.0)):
            if end_window:
                g.add_geo(G.window_lancet(3.6, 12.5, 3), pos=(xe, cy, z0 + 9.0), outward=(ox, 0), lit=TW.pick_lit(rng, lit_p), rng=rng)
                for dy in (-D * 0.32, D * 0.32):
                    g.add_geo(G.window_lancet(1.3, 3.4, 1), pos=(xe, cy + dy, z0 + 4.2), outward=(ox, 0), lit=TW.pick_lit(rng, lit_p * 0.7), rng=rng)
            for zb in (3.0,):
                pass
    # roof
    rise = A.gable_roof(g, cx, cy, L, D, z_wall, pitch, axis='x', overhang=0.15, m_roof=roof_mat, m_gable=wall_mat,
                        thick=0.5)
    z_ridge = z_wall + rise
    if cresting_on:
        cresting(g, x0 + 2, x1 - 2, cy, z_ridge + 0.05, 2.6, 1.0, rng)
        boxes(g, [(cx, cy, z_ridge - 0.05)], [(L + 0.6, 0.45, 0.5)], m=COPPER)
    # dormers on both slopes
    if dormers:
        tanp = math.tan(math.radians(pitch))
        nd = max(2, int(L / 9.0 / dormer_every))
        for k in range(nd):
            xd = x0 + (k + 0.5) * L / nd
            s = D / 2.0 * 0.42
            zd = z_wall + s * tanp
            pr = G.dormer(pitch)
            for (oy, yy) in ((-1.0, ys + s), (1.0, yn - s)):
                if oy > 0 and not north:
                    continue
                lp = lit_p if oy < 0 else north_lit
                g.add_geo(pr, pos=(xd, yy, zd), outward=(0, oy), lit=TW.pick_lit(rng, lp), rng=rng, scale=1.15)
    for k in range(chimneys):
        xc = x0 + (k + 0.6) * L / max(chimneys, 1)
        yc = cy + D * 0.17
        zc = z_wall + (D / 2 - D * 0.17) * math.tan(math.radians(pitch)) - 1.0
        chimney(g, xc, yc, zc, 2.0, 8.0 + 3 * rng.random(), 3)
    if flying and north:
        for xb in x0 + np.arange(1, nb) * bw:
            flying_buttress(g, xb, yn, 1.0, z0 + eaves - 4.0, z0 + eaves - 7.0, 5.2)
    return dict(ridge=z_ridge, z_wall=z_wall)


def arcade_gallery(g, x0, x1, y0, y1, z0, h, rng, found=28.0, lit_p=0.7, bay=3.6, open_h=7.6, wall_mat=STONE):
    """Low arcaded gallery block: pointed arcade windows on the south face, crenellated flat roof."""
    L = x1 - x0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    boxes(g, [(cx, cy, z0 - found)], [(L, y1 - y0, found + h)], m=wall_mat, faces=(0, 1, 2, 3, 4))
    nb = max(2, int(round(L / bay)))
    bw = L / nb
    proto = G.window_lancet(2.2, open_h, 1, rise_k=1.0, transoms=2)
    for k in range(nb):
        xc = x0 + (k + 0.5) * bw
        g.add_geo(proto, pos=(xc, y0, z0 + 3.4), outward=(0, -1), lit=TW.pick_lit(rng, lit_p), rng=rng)
        pr = G.buttress(z0 - 4.0, z0 + h - 0.5, 1.2, 1.6, stages=2, pinnacle=(k % 2 == 0), pin_h=4.0)
        g.add_geo(pr, pos=(x0 + k * bw, y0, 0.0), outward=(0, -1))
    g.add_geo(G.buttress(z0 - 4.0, z0 + h - 0.5, 1.2, 1.6, stages=2, pinnacle=True, pin_h=4.0), pos=(x1, y0, 0.0), outward=(0, -1))
    poly = np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
    for zb in (2.6, h - 2.4):
        path = np.column_stack([poly, np.full(4, z0 + zb)])
        sweep(g, np.array([[0.0, -0.3], [0.45, -0.3], [0.45, 0.12], [0.0, 0.45]]), path, closed=True, m=DRESS)
    # corbel + parapet
    nco = int(L / 1.5)
    xs_c = x0 + (np.arange(nco) + 0.5) * L / nco
    for i, (o, hh) in enumerate(((0.45, 0.32), (0.85, 0.32), (1.25, 0.34))):
        C = np.column_stack([xs_c, np.full(nco, y0 - (o - 0.35) / 2.0), np.full(nco, z0 + h - 1.0 + i * 0.34)])
        boxes(g, C, [(0.62, o + 0.35, hh)], m=DRESS)
    zp = z0 + h
    boxes(g, [(cx, y0 - 0.55, zp)], [(L + 1.2, 0.9, 0.9)], m=wall_mat)
    nm = int(L / 2.2)
    xs_m = x0 + (np.arange(nm) + 0.5) * L / nm
    C = np.column_stack([xs_m, np.full(nm, y0 - 0.55), np.full(nm, zp + 0.9)])
    boxes(g, C, [(L / nm * 0.56, 0.9, 1.25)], m=wall_mat)
    # low pitched lead roof (shed)
    A.gable_roof(g, cx, cy, L, y1 - y0, zp + 0.3, 12.0, axis='x', overhang=0.1, m_roof='M_Lead', m_gable=wall_mat, thick=0.3)


def gatehouse(g, cx, cy, sx, sy, z0, h, rng, found=30.0, lit_p=0.6, drum_r=5.6, portal_side='E'):
    x0, x1 = cx - sx / 2, cx + sx / 2
    y0, y1 = cy - sy / 2, cy + sy / 2
    boxes(g, [(cx, cy, z0 - found)], [(sx, sy, found + h)], m=STONE, faces=(0, 1, 2, 3, 4))
    poly = np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
    for zb in (4.0, 14.0, 24.0):
        path = np.column_stack([poly, np.full(4, z0 + zb)])
        sweep(g, np.array([[0.0, -0.3], [0.5, -0.3], [0.5, 0.15], [0.0, 0.5]]), path, closed=True, m=DRESS)
    # machicolated parapet
    zt = z0 + h
    for (a, b, ox, oy) in ((0, 1, 0, -1), (1, 2, 1, 0), (2, 3, 0, 1), (3, 0, -1, 0)):
        p0, p1 = poly[a], poly[b]
        Ln = float(np.linalg.norm(p1 - p0))
        u = (p1 - p0) / Ln
        yawv = math.atan2(u[1], u[0])
        n = int(Ln / 1.4)
        ts = (np.arange(n) + 0.5) / n
        for i, (o, hh) in enumerate(((0.55, 0.3), (1.0, 0.3), (1.5, 0.32))):
            C = np.column_stack([p0[0] + u[0] * ts * Ln + ox * (o - 0.35) / 2, p0[1] + u[1] * ts * Ln + oy * (o - 0.35) / 2,
                                 np.full(n, zt - 1.0 + i * 0.32)])
            boxes(g, C, [(0.6, o + 0.35, hh)], yaw=yawv, m=DRESS)
        mid = (p0 + p1) / 2 + np.array([ox, oy]) * 0.7
        boxes(g, [(mid[0], mid[1], zt)], [(Ln + 1.6, 0.95, 0.9)], yaw=yawv, m=STONE)
        nm = max(3, int(Ln / 2.2))
        ts2 = (np.arange(nm) + 0.5) / nm
        C = np.column_stack([p0[0] + u[0] * ts2 * Ln + ox * 0.7, p0[1] + u[1] * ts2 * Ln + oy * 0.7, np.full(nm, zt + 0.9)])
        boxes(g, C, [(Ln / nm * 0.55, 0.95, 1.3)], yaw=yawv, m=STONE)
    boxes(g, [(cx, cy, zt - 1.0)], [(sx + 2.0, sy + 2.0, 1.0)], m=DRESS)
    # flat roof slab cap
    boxes(g, [(cx, cy, zt)], [(sx - 0.2, sy - 0.2, 0.3)], m='M_Lead', faces=(4,))
    # drum towers at the two south corners
    rng2 = np.random.default_rng(rng.integers(1 << 30))
    for (dx, dy) in ((x0 + 1.0, y0 + 0.5), (x1 - 1.0, y0 + 0.5)):
        TW.round_tower(g, dx, dy, z0, drum_r, h + 4.0, 15.0, rng2, bands=(12.0, 24.0),
                       tiers=[(8.0, 6, G.window_lancet(0.9, 2.4, 1)), (18.0, 6, G.window_slit(0.3, 2.2)), (28.0, 6, G.window_lancet(0.8, 2.1, 1))],
                       top='corbel_cone', fin=4.0, lit_p=lit_p, segs=28, eave_out=1.3, cone_p=1.12)
    # portal (east face)
    ox, oy = (1.0, 0.0) if portal_side == 'E' else (0.0, -1.0)
    pw, ph = 5.6, 8.2
    O = pointed_arch(pw, ph - pw * 0.9, pw * 0.9, n=8)
    pg = Geo('portal', [DRESS, 'M_Iron', 'M_Dark'])
    O2 = offset_outline(O, 0.22)
    O3 = offset_outline(O, 0.55)
    frame_ring(pg, O3, O2, -0.35, 0.3, DRESS, with_reveal=False)
    frame_ring(pg, O2, O, -0.6, 0.6, DRESS, y_inner_back=0.6)
    wall_fill(pg, O, 0.6, 'M_Dark')
    # portcullis grid
    for i in range(1, 6):
        xx = -pw / 2 + i * pw / 6
        boxes(pg, [(xx, 0.35, 0.0)], [(0.1, 0.1, ph - 1.0)], m='M_Iron')
    for i in range(1, 5):
        boxes(pg, [(0, 0.35, i * (ph - 1.0) / 5)], [(pw - 0.2, 0.1, 0.1)], m='M_Iron')
    g.add_geo(pg, pos=((x1 if portal_side == 'E' else cx), (cy if portal_side == 'E' else y0), z0), outward=(ox, oy))
    # east face (portal side): lit windows flanking / above the portal + a grand central window
    if portal_side == 'E':
        g.add_geo(G.window_lancet(2.2, 7.0, 2), pos=(x1, cy, z0 + 15.5), outward=(1, 0), lit=(0.95, 0.12), rng=rng)
        for dy in (-6.8, 6.8):
            for zw in (12.0, 22.0, 30.0):
                g.add_geo(G.window_lancet(1.2, 3.4, 1), pos=(x1, cy + dy, z0 + zw), outward=(1, 0), lit=TW.pick_lit(rng, lit_p + 0.2), rng=rng)
        for dy in (-3.4, 3.4):
            g.add_geo(G.window_lancet(1.0, 3.0, 1), pos=(x1, cy + dy, z0 + 27.5), outward=(1, 0), lit=TW.pick_lit(rng, lit_p + 0.2), rng=rng)
        for zb in (0,):
            pass
    # windows on the other faces
    for (ox2, oy2, cxf, cyf, width) in ((0, -1, cx, y0, sx), (0, 1, cx, y1, sx), (-1, 0, x0, cy, sy)):
        for zw in (8.0, 18.0, 28.0):
            for off in (-width * 0.22, width * 0.22):
                tx, ty = -oy2, ox2
                g.add_geo(G.window_lancet(1.1, 3.2, 1), pos=(cxf + tx * off, cyf + ty * off, z0 + zw), outward=(ox2, oy2),
                          lit=TW.pick_lit(rng, lit_p), rng=rng)
    return dict(top=zt)
