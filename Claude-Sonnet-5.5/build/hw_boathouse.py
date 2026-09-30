"""Boathouse, jetty and rowing boats."""
import numpy as np
import math
from hw_geo import (Geo, boxes, beams, lathe, loft, sweep, prism, pyramid, poly_cap, xf, rotz, pointed_arch, round_arch,
                    offset_outline, frame_ring, wall_fill, reveal, triangulate_polygon)
from hw_geo import slab as G_slab
import hw_gothic as G
import hw_arch as A
import hw_walls as W
import hw_towers as TW

STONE = 'M_Stone'
DRESS = 'M_StoneDress'
TIMBER = 'M_Timber'
PLASTER = 'M_Plaster'
QUAY = 'M_Quay'
SLATE = 'M_Slate'
COPPER = 'M_Copper'


def timber_wall(g, x0, y0, x1, y1, za, zb, outward, rng, post=1.7, win=None, win_list=(), infill=PLASTER):
    """Timber-framed wall between plan points; `outward` = unit (ox, oy).  Adds posts/rails/braces + plaster."""
    d = np.array([x1 - x0, y1 - y0], float)
    L = np.linalg.norm(d)
    u = d / L
    o = np.array(outward, float)
    n = max(2, int(round(L / post)))
    ts = np.linspace(0, 1, n + 1)
    h = zb - za
    yaw = math.atan2(u[1], u[0])
    # plaster panel (single big quad slightly behind frame)
    p0 = np.array([x0, y0, za])
    P = np.array([[x0, y0, za], [x1, y1, za], [x1, y1, zb], [x0, y0, zb]])
    # orientation: E1 = u, E2 = up -> normal = u x up = right of u; ensure equals outward
    nrm = np.cross(np.array([u[0], u[1], 0]), np.array([0, 0, 1.0]))
    if nrm[0] * o[0] + nrm[1] * o[1] < 0:
        P = P[::-1]
    g.add(P[None], infill)
    # posts
    px = x0 + u[0] * ts * L + o[0] * 0.09
    py = y0 + u[1] * ts * L + o[1] * 0.09
    C = np.column_stack([px, py, np.full(len(ts), za)])
    boxes(g, C, [(0.24, 0.24, h)], yaw=yaw, m=TIMBER)
    # rails
    mid = np.array([x0 + u[0] * L / 2 + o[0] * 0.09, y0 + u[1] * L / 2 + o[1] * 0.09])
    for zr in (za, zb - 0.26, za + h * 0.42):
        boxes(g, [(mid[0], mid[1], zr)], [(L, 0.26, 0.26)], yaw=yaw, m=TIMBER)
    # braces (diagonals) in some panels
    for k in range(n):
        if rng.random() < 0.45:
            a = np.array([px[k], py[k], za + 0.26])
            b = np.array([px[k + 1], py[k + 1], za + h * 0.42])
            if rng.random() < 0.5:
                a, b = np.array([px[k + 1], py[k + 1], za + 0.26]), np.array([px[k], py[k], za + h * 0.42])
            beams(g, [a], [b], 0.16, 0.16, m=TIMBER)
    return dict(px=px, py=py)


def bargeboard(g, x, y, z_eave, half_span, pitch_deg, axis_yaw, rng, out=0.0):
    """Scalloped bargeboards along both rakes of a gable (gable faces -y locally, ridge at (x, y, ...))"""
    tp = math.tan(math.radians(pitch_deg))
    for sgn in (-1, 1):
        a = np.array([x + sgn * (half_span + 0.5), y, z_eave - 0.5 * tp])
        b = np.array([x, y, z_eave + half_span * tp + 0.1])
        beams(g, [a], [b], 0.5, 0.16, m=TIMBER, up=(0, 1, 0))
        # scallops
        n = 8
        for k in range(n):
            t = (k + 0.5) / n
            p = a + (b - a) * t
            boxes(g, [(p[0], p[1] - 0.02, p[2] - 0.55)], [(0.2, 0.14, 0.32)], m=TIMBER)


def rowboat(g, x, y, z, yaw, L=4.7, B=1.55, D=0.62, rng=None, lantern=False, color_m=TIMBER):
    n_st = 14
    t = np.linspace(0, 1, n_st)
    hb = B / 2.0 * np.sin(np.pi * np.clip(t, 0.0, 1.0)) ** 0.55 * (1.0 - 0.15 * t)
    dd = D * (0.55 + 0.45 * np.sin(np.pi * np.clip(t, 0.0, 1.0)) ** 0.5)
    lift = 0.25 * t ** 3 + 0.12 * (1 - t) ** 3          # sheer: bow higher
    xs = (t - 0.5) * L
    cs = np.linspace(-1, 1, 9)
    rings = []
    for i in range(n_st):
        yy = cs * hb[i]
        zz = -dd[i] * (1.0 - cs ** 2) ** 0.8 + lift[i] + 0.0
        zz = np.where(np.abs(cs) > 0.98, lift[i] + 0.0, zz + dd[i] * 0.0)
        rings.append(np.column_stack([np.full(9, xs[i]), yy, zz]))
    rings = np.stack(rings)
    for k in range(9):
        pass
    # hull exterior: rings along length (i), points across (j); orientation: across from -y to +y ; along +x
    outer = rings.copy()
    inner = rings.copy()
    inner[:, :, 1] *= 0.93
    inner[:, :, 2] += 0.07
    # transform to world
    def tf(R):
        c, s = math.cos(yaw), math.sin(yaw)
        X = R[..., 0] * c - R[..., 1] * s + x
        Y = R[..., 0] * s + R[..., 1] * c + y
        return np.stack([X, Y, R[..., 2] + z], axis=-1)
    Go = Geo('boat', [color_m])
    loft(Go, tf(outer), closed=False, m=color_m)
    loft(Go, tf(inner[:, ::-1]), closed=False, m=color_m, flip=True)
    g.merge(Go) if False else None
    for ch in Go.c4 + Go.c3:
        g.c4.append(ch) if ch['P'].shape[1] == 4 else g.c3.append(ch)
    # thwarts (seats)
    for xt in (-0.9, 0.0, 0.95):
        c, s = math.cos(yaw), math.sin(yaw)
        pos = (x + xt * c, y + xt * s, z + 0.02)
        boxes(g, [pos], [(0.34, B * 0.74, 0.05)], yaw=yaw, m=TIMBER)
    # gunwale rail
    for sd in (-1, 1):
        pts = []
        for i in range(2, n_st - 1):
            pts.append([xs[i], sd * hb[i] * 0.98, lift[i] + 0.03])
        pts = np.array(pts)
        c, s = math.cos(yaw), math.sin(yaw)
        P = np.column_stack([pts[:, 0] * c - pts[:, 1] * s + x, pts[:, 0] * s + pts[:, 1] * c + y, pts[:, 2] + z])
        beams(g, P[:-1], P[1:], 0.07, 0.06, m=TIMBER)
    # oars laid across
    if rng is not None and rng.random() < 0.7:
        c, s = math.cos(yaw), math.sin(yaw)
        a = np.array([x + 0.3 * c - 1.3 * s, y + 0.3 * s + 1.3 * c, z + 0.32])
        b = np.array([x + 0.1 * c + 1.5 * s, y + 0.1 * s - 1.5 * c, z + 0.38])
        beams(g, [a], [b], 0.06, 0.06, m=TIMBER)
    if lantern:
        post = W.lantern_post(1.4)
        c, s = math.cos(yaw), math.sin(yaw)
        g.add_geo(post, pos=(x + (L * 0.42) * c, y + (L * 0.42) * s, z + 0.1), scale=0.9)


def boathouse(g, cx, cy, z0, L=26.0, D=15.0, rng=None, found=10.0):
    rng = rng or np.random.default_rng(31)
    x0, x1 = cx - L / 2, cx + L / 2
    ys, yn = cy - D / 2, cy + D / 2
    plinth_h = 3.6
    # ---- stone quay / plinth
    boxes(g, [(cx, cy, z0 - found)], [(L + 2.0, D + 2.0, found + plinth_h)], m=QUAY, faces=(0, 1, 2, 3, 4))
    boxes(g, [(cx, cy, z0 + plinth_h)], [(L + 0.6, D + 0.6, 0.3)], m=DRESS)
    # quay wall batter towards the water (south) + steps
    for k in range(5):
        boxes(g, [(cx + 6.0, ys - 1.0 - k * 0.7, z0 - 0.45 * k - 0.4)], [(5.0, 0.7, 0.45 * (k + 1) + 0.4)], m=QUAY)
    # big boat doors (south face): frame
    O = round_arch(5.4, 2.6, n=10)
    O2 = offset_outline(O, 0.3)
    O3 = offset_outline(O, 0.6)
    doors = Geo('doors', [DRESS, TIMBER, 'M_GlassLit', 'M_Dark'])
    frame_ring(doors, O3, O2, -0.35, 0.3, DRESS, with_reveal=False)
    frame_ring(doors, O2, O, -0.55, 0.6, DRESS, y_inner_back=0.5)
    wall_fill(doors, O, 0.5, 'M_GlassLit', a={'glow': 0.85, 'hue': 0.08, 'seed': 0.3}, uv_center=(0, 0))
    for i in range(1, 7):
        xx = -2.7 + i * 5.4 / 7
        boxes(doors, [(xx, 0.0, 0.0)], [(0.14, 0.14, 5.2)], m=TIMBER)
    boxes(doors, [(0, 0.0, 1.9)], [(5.3, 0.16, 0.16)], m=TIMBER)
    boxes(doors, [(0, 0.0, 3.6)], [(5.3, 0.16, 0.16)], m=TIMBER)
    g.add_geo(doors, pos=(cx - 5.0, ys - 1.0, z0 + 0.15), outward=(0, -1))
    g.add_geo(doors, pos=(cx + 5.0, ys - 1.0, z0 + 0.15), outward=(0, -1))
    # plinth windows (small, lit)
    for xx in (cx - 11.0, cx, cx + 11.0):
        g.add_geo(G.window_rect(0.9, 1.1, 2, 2, molding=False), pos=(xx, ys - 1.0, z0 + 1.8), outward=(0, -1),
                  lit=(0.9, 0.12), rng=rng)
    # ---- timber upper storey
    za = z0 + plinth_h + 0.3
    zb = za + 4.6
    o_pad = 0.4
    xa, xb, ya, yb = x0 + 0.5, x1 - 0.5, ys + 0.5, yn - 0.5
    corners = [(xa, ya), (xb, ya), (xb, yb), (xa, yb)]
    outs = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    for k in range(4):
        p, q = corners[k], corners[(k + 1) % 4]
        timber_wall(g, p[0], p[1], q[0], q[1], za, zb, outs[k], rng)
    # jettied floor beam
    boxes(g, [(cx, cy, za - 0.35)], [(xb - xa + 0.5, yb - ya + 0.5, 0.35)], m=TIMBER, faces=(0, 1, 2, 3, 4, 5))
    # windows on the timber storey (mullioned rect, lit)
    for xx in (cx - 8.0, cx - 2.6, cx + 2.6, cx + 8.0):
        g.add_geo(G.window_rect(1.5, 1.7, 3, 2, molding=False, bar=0.05), pos=(xx, ya - 0.1, za + 1.4), outward=(0, -1),
                  lit=(rng.uniform(0.5, 1.0), rng.uniform(0.02, 0.3)), rng=rng)
    for yy in (cy - 2.0, cy + 2.0):
        g.add_geo(G.window_rect(1.4, 1.7, 2, 2, molding=False, bar=0.05), pos=(xa - 0.1, yy, za + 1.4), outward=(-1, 0),
                  lit=(0.8, 0.1), rng=rng)
        g.add_geo(G.window_rect(1.4, 1.7, 2, 2, molding=False, bar=0.05), pos=(xb + 0.1, yy, za + 1.4), outward=(1, 0),
                  lit=(0.6, 0.15), rng=rng)
    # ---- roof: main gable (ridge along x)
    pitch = 58.0
    z_eave = zb + 0.05
    rise = A.gable_roof(g, cx, cy, L + 0.4, D - 0.4, z_eave, pitch, axis='x', overhang=1.4, m_roof=SLATE, m_gable=TIMBER, thick=0.35)
    z_ridge = z_eave + rise
    # gable end timber infill
    for xe, ox in ((x0 + 0.5, -1), (x1 - 0.5, 1)):
        pass
    # ---- two front cross gables on the south slope
    tp = math.tan(math.radians(pitch))
    for xx in (cx - 6.5, cx + 6.5):
        gw = 6.4
        gd = 4.0
        y_face = ya - 0.05
        # gable wall (timber + plaster) rising from eaves
        wall_top = z_eave + 2.6
        timber_wall(g, xx - gw / 2, y_face, xx + gw / 2, y_face, z_eave - 0.05, wall_top, (0, -1), rng, post=1.6)
        # gable triangle
        tri_h = gw / 2 * tp * 0.95
        tri = np.array([[xx - gw / 2, y_face, wall_top], [xx + gw / 2, y_face, wall_top], [xx, y_face, wall_top + tri_h]])
        g.add(tri[None], PLASTER)
        # roof planes of the cross gable (from face back to main roof)
        depth = (wall_top + tri_h - z_eave) / tp * 0.7 + 1.0
        for sgn in (-1, 1):
            a = np.array([xx + sgn * (gw / 2 + 0.5), y_face - 0.7, wall_top - 0.5 * tp * 0.0])
            b = np.array([xx, y_face - 0.7, wall_top + tri_h + 0.1])
            c_ = np.array([xx, y_face + depth, wall_top + tri_h + 0.1])
            d_ = np.array([xx + sgn * (gw / 2 + 0.5), y_face + depth * 0.55, wall_top - 0.0])
            G_slab(g, np.stack([a, b, c_, d_]), 0.32, SLATE, hint=(sgn * 0.8, 0.0, 0.6), vertical=(1, 2))
        # bargeboards + finial
        bargeboard(g, xx, y_face - 0.72, wall_top - 0.1, gw / 2, math.degrees(math.atan(tri_h / (gw / 2))), 0.0, rng)
        g.add_geo(G.finial(2.4, 0.22, COPPER), pos=(xx, y_face - 0.6, wall_top + tri_h + 0.0))
        g.add_geo(G.window_lancet(0.9, 2.1, 1, molding=False), pos=(xx, y_face - 0.0, wall_top + 0.35), outward=(0, -1),
                  lit=(0.95, 0.1), rng=rng)
    # ---- central spire lantern on the ridge
    zl = z_ridge - 0.2
    seg = 8
    prof = [(1.55, zl), (1.55, zl + 2.4)]
    lathe(g, prof, (cx, cy, 0), segs=seg, m=TIMBER, smooth=False, yaw0=math.pi / 8)
    for k in range(seg):
        a = 2 * math.pi * k / seg
        g.add_geo(G.window_lancet(0.62, 1.7, 1, molding=False), pos=(cx + 1.45 * math.cos(a), cy + 1.45 * math.sin(a), zl + 0.45),
                  outward=(math.cos(a), math.sin(a)), lit=(0.9, 0.1), rng=rng)
    cp = np.array([(1.9, zl + 2.4), (1.3, zl + 3.4), (0.75, zl + 6.2), (0.2, zl + 9.4), (0.0, zl + 10.0)])
    lathe(g, cp, (cx, cy, 0), segs=seg, m=COPPER, smooth=False, yaw0=math.pi / 8, uv_v='slant')
    g.add_geo(G.finial(3.2, 0.3, COPPER), pos=(cx, cy, zl + 9.8))
    # eave brackets / hanging lanterns at the doors
    lw = W.lantern_wall()
    for xx in (cx - 7.6, cx - 2.4, cx + 2.4, cx + 7.6):
        g.add_geo(lw, pos=(xx, ys - 1.05, z0 + 4.4), outward=(0, -1))
    # chimney
    boxes(g, [(cx - 8.5, cy + 3.2, z_eave + 2.5)], [(1.4, 1.4, 5.0)], m=STONE)
    return dict(z_ridge=z_ridge, top=zl + 13.0)


def jetty(g, x, y_shore, z_deck=0.7, length=20.0, width=3.2, rng=None):
    """Wooden jetty extending south (-y) from y_shore."""
    rng = rng or np.random.default_rng(3)
    yc = y_shore - length / 2
    # deck planks: individual long boards
    nb = int(width / 0.24)
    for k in range(nb):
        xx = x - width / 2 + (k + 0.5) * width / nb
        boxes(g, [(xx, yc, z_deck)], [(width / nb - 0.02, length, 0.1)], m='M_Plank')
    # transverse beams underneath + posts
    ny = int(length / 2.2)
    for k in range(ny + 1):
        yy = y_shore - k * length / ny
        boxes(g, [(x, yy, z_deck - 0.3)], [(width + 0.4, 0.28, 0.3)], m=TIMBER)
        for sx in (-1, 1):
            prof = [(0.16, -4.0), (0.15, z_deck + 0.2), (0.17, z_deck + 0.9 if k % 2 == 0 else z_deck + 0.2), (0.0, z_deck + 0.95 if k % 2 == 0 else z_deck + 0.25)]
            lathe(g, prof, (x + sx * (width / 2 + 0.1), yy, 0), segs=8, m=TIMBER)
    # rope rails between tall posts
    for sx in (-1, 1):
        pts = np.array([[x + sx * (width / 2 + 0.1), y_shore - k * length / ny, z_deck + 0.8] for k in range(0, ny + 1, 2)])
        for a, b in zip(pts[:-1], pts[1:]):
            beams(g, [a], [b], 0.04, 0.04, m='M_Rope')
    # ladder at the end
    return dict(end_y=y_shore - length)
