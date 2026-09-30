"""Gothic detail prototypes.  All authored on a SOUTH-facing wall: wall plane y=0, outward = -y,
screen-right = +x, up = +z, interior = +y.  Instance with Geo.add_geo(proto, pos, outward=(ox,oy))."""
import numpy as np
import math
from hw_geo import (Geo, boxes, beams, lathe, loft, sweep, prism, pyramid, ngon, poly_cap, xf, rotz,
                    pointed_arch, round_arch, circle_outline, rect_outline, offset_outline, wall_strip, wall_fill,
                    reveal, outer_side, frame_ring, triangulate_polygon)

STONE = 'M_StoneDress'
WALL = 'M_Stone'
GLASS = 'M_GlassLit'
IRON = 'M_Iron'
FACE = 'M_ClockFace'
MARK = 'M_ClockMark'
SLATE = 'M_Slate'
_CACHE = {}


_PANE_ID = [0]


def cached(key, fn):
    if key not in _CACHE:
        _CACHE[key] = fn().consolidate()
    return _CACHE[key]


def _pane(g, outline, cx=0.0, y=-0.05):
    _PANE_ID[0] += 1
    wall_fill(g, outline, y, GLASS, a={'glow': -1.0, 'pane': _PANE_ID[0]}, uv_center=(cx, 0.0))


def _bars(g, P, bar, y_front=-0.30, y_back=-0.05):
    frame_ring(g, offset_outline(P, bar), P, y_front, y_back, STONE, with_reveal=True)


# --------------------------------------------------------------------------------------
# windows
# --------------------------------------------------------------------------------------

def window_lancet(w=2.4, h=9.5, lights=2, rise_k=0.95, transoms=0, oculus=True, bar=0.07, mullion=0.18,
                  molding=True, n_arc=7, sill=True):
    key = ('lancet', round(w, 2), round(h, 2), lights, round(rise_k, 2), transoms, oculus, molding, n_arc, sill)

    def build():
        g = Geo('win_lancet', [STONE, GLASS])
        rise = w * rise_k
        hs = max(h - rise, 0.3)
        O = pointed_arch(w, hs, rise, n=n_arc)
        O2 = offset_outline(O, 0.17)
        O3 = offset_outline(O, 0.38)
        if molding:
            frame_ring(g, O3, O2, -0.22, 0.28, STONE, with_reveal=False)
        frame_ring(g, O2, O, -0.40, 0.28, STONE, y_inner_back=-0.05)
        if sill:
            boxes(g, [(0, -0.30, -0.66)], [(w + 1.15, 0.72, 0.26)], m=STONE, faces=(0, 1, 3, 4, 2))
        if lights == 1:
            _pane(g, O)
            for i in range(transoms):
                zt = h * (i + 1) / (transoms + 1) * 0.86
                boxes(g, [(0, -0.155, zt)], [(w, 0.21, 0.07)], m=STONE)
        else:
            nlt = lights
            pw = (w - (nlt - 1) * mullion - nlt * 2 * bar) / nlt
            hs_sub = hs - 0.25
            rise_sub = 0.95 * pw
            zsub_top = hs_sub + rise_sub
            xs = [-w / 2 + bar + pw / 2 + i * (pw + 2 * bar + mullion) for i in range(nlt)]
            for xc in xs:
                P = pointed_arch(pw, hs_sub, rise_sub, n=6, cx=xc)
                _pane(g, P)
                _bars(g, P, bar)
            for i in range(nlt - 1):
                xm = (xs[i] + xs[i + 1]) / 2
                boxes(g, [(xm, -0.175, 0.0)], [(mullion, 0.25, zsub_top - 0.35)], m=STONE)
            if oculus:
                ro = 0.30 * (w / 2.0) * (1.0 if nlt == 2 else 1.25)
                zc = zsub_top + 0.18 + ro
                if zc + ro < h - 0.3:
                    C = circle_outline(ro, 14, 0.0, zc)
                    _pane(g, C)
                    _bars(g, C, bar)
            for i in range(transoms):
                zt = hs_sub * (i + 1) / (transoms + 1)
                boxes(g, [(0, -0.155, zt)], [(w, 0.21, 0.06)], m=STONE)
        return g
    return cached(key, build)


def window_rect(w=1.6, h=2.2, cols=2, rows=3, molding=True, bar=0.06, arch=False):
    key = ('rect', round(w, 2), round(h, 2), cols, rows, molding, arch)

    def build():
        g = Geo('win_rect', [STONE, GLASS])
        if arch:
            O = round_arch(w, h - w / 2, n=8)
        else:
            O = rect_outline(w, h)
        O2 = offset_outline(O, 0.14)
        O3 = offset_outline(O, 0.3)
        if molding:
            frame_ring(g, O3, O2, -0.18, 0.28, STONE, with_reveal=False)
        frame_ring(g, O2, O, -0.32, 0.28, STONE, y_inner_back=-0.05)
        boxes(g, [(0, -0.24, -0.5)], [(w + 0.9, 0.55, 0.2)], m=STONE, faces=(0, 1, 3, 4, 2))
        # panes: grid of cells (pointed cap handled by full-width top pane when arch)
        cw = (w - (cols - 1) * bar) / cols
        rh_ = ((h - (w / 2 if arch else 0)) - (rows - 1) * bar) / rows
        for r in range(rows):
            for c in range(cols):
                x0 = -w / 2 + c * (cw + bar)
                z0 = r * (rh_ + bar)
                cell = rect_outline(cw, rh_, x0 + cw / 2, z0)
                _pane(g, cell)
        for c in range(1, cols):
            boxes(g, [(-w / 2 + c * (cw + bar) - bar / 2, -0.12, 0)], [(bar, 0.14, h - (w / 2 if arch else 0))], m=STONE)
        for r in range(1, rows):
            boxes(g, [(0, -0.12, r * (rh_ + bar) - bar / 2)], [(w, 0.14, bar)], m=STONE)
        if arch:
            cap = round_arch(w, h - w / 2, n=8)
            top = np.array([p for p in cap if p[1] >= h - w / 2 - 1e-6])
            top = np.vstack([[[w / 2, h - w / 2]], top[1:-1] if len(top) > 2 else top, [[-w / 2, h - w / 2]]])
            if len(top) >= 3:
                _pane(g, top)
        return g
    return cached(key, build)


def window_slit(w=0.30, h=2.0):
    key = ('slit', round(w, 2), round(h, 2))

    def build():
        g = Geo('win_slit', [STONE, GLASS])
        O = pointed_arch(w, h - w * 0.9, w * 0.9, n=4)
        O2 = offset_outline(O, 0.16)
        frame_ring(g, O2, O, -0.22, 0.28, STONE, y_inner_back=-0.05)
        _pane(g, O)
        return g
    return cached(key, build)


def window_round(r=0.9, spokes=6, bar=0.06):
    key = ('round', round(r, 2), spokes)

    def build():
        g = Geo('win_round', [STONE, GLASS])
        C = circle_outline(r, 20, 0.0, r)
        C2 = offset_outline(C, 0.16)
        C3 = offset_outline(C, 0.34)
        frame_ring(g, C3, C2, -0.2, 0.28, STONE, with_reveal=False)
        frame_ring(g, C2, C, -0.36, 0.28, STONE, y_inner_back=-0.05)
        # wedge panes
        n = spokes
        for i in range(n):
            a0 = 2 * math.pi * i / n + bar / r
            a1 = 2 * math.pi * (i + 1) / n - bar / r
            arc = [(0.0, r)] + [((r - 0.02) * math.cos(a), r + (r - 0.02) * math.sin(a)) for a in np.linspace(a0, a1, 4)]
            P = np.array(arc)
            # CCW check
            area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
            if area < 0:
                P = P[::-1]
            _PANE_ID[0] += 1
            wall_fill(g, P, -0.05, GLASS, a={'glow': -1.0, 'pane': _PANE_ID[0]}, uv_center=(0.0, 0.0))
        for i in range(n):
            a = 2 * math.pi * i / n
            beams(g, [(0.0, -0.12, r)], [((r - 0.02) * math.cos(a), -0.12, r + (r - 0.02) * math.sin(a))], bar, 0.12, m=STONE)
        return g
    return cached(key, build)


def clock_face(r=3.4):
    key = ('clock', round(r, 2))

    def build():
        g = Geo('clock', [STONE, FACE, MARK])
        C = circle_outline(r, 40, 0.0, r)
        C2 = offset_outline(C, 0.55)
        C3 = offset_outline(C, 0.95)
        frame_ring(g, C3, C2, -0.45, 0.35, STONE, with_reveal=False)
        frame_ring(g, C2, C, -0.80, 0.35, STONE, y_inner_back=-0.25)
        wall_fill(g, C, -0.25, FACE, a={'glow': 1.0, 'hue': 0.22, 'seed': 0.5}, uv_center=(0.0, r))
        # hour marks
        for i in range(12):
            a = math.pi / 2 - 2 * math.pi * i / 12
            big = (i % 3 == 0)
            r0, r1 = (0.80 if big else 0.86) * r, 0.94 * r
            p0 = (r0 * math.cos(a), -0.32, r + r0 * math.sin(a))
            p1 = (r1 * math.cos(a), -0.32, r + r1 * math.sin(a))
            beams(g, [p0], [p1], 0.20 if big else 0.10, 0.10, m=MARK, up=(0, -1, 0))
        # hands (10:10)
        for ang_deg, ln, wd in ((150.0, 0.66 * r, 0.24), (30.0, 0.84 * r, 0.16)):
            a = math.radians(ang_deg)
            p1 = (ln * math.cos(a), -0.36, r + ln * math.sin(a))
            beams(g, [(0.0, -0.36, r)], [p1], wd, 0.10, m=MARK, up=(0, -1, 0))
        boxes(g, [(0, -0.38, r - 0.15)], [(0.34, 0.14, 0.3)], m=MARK)
        return g
    return cached(key, build)


def dormer(pitch_deg=54.0, w=1.7, hf=1.9, rise_g=1.05, win_h=1.55, win_w=0.85, embed=1.2):
    """Gabled dormer.  Origin = centre of the front-wall foot on the roof surface; the roof rises toward +y."""
    key = ('dormer', round(pitch_deg, 1), round(w, 2), round(hf, 2), round(rise_g, 2), round(win_h, 2))

    def build():
        g = Geo('dormer', [STONE, SLATE, GLASS])
        tp = math.tan(math.radians(min(pitch_deg, 84.0)))
        hz = hf + rise_g
        De = hf / tp
        Dr = hz / tp
        wl = w / 2.0
        # front wall (stone) with window in it: wall as quad below gable, gable triangle
        z_bot = -embed * tp * 0.5
        g.add(np.array([[[-wl, 0, z_bot], [wl, 0, z_bot], [wl, 0, hf], [-wl, 0, hf]]]), STONE)
        g.add(np.array([[[-wl, 0, hf], [wl, 0, hf], [0, 0, hz]]]), STONE)
        # cheeks
        for sgn in (-1, 1):
            xw = sgn * wl
            tri = np.array([[xw, 0, 0.0], [xw, De + 0.02, hf], [xw, 0, hf]])
            if sgn < 0:
                tri = tri[[0, 2, 1]]
            g.add(tri[None], STONE)
        # roof planes: slate slab with an underside (trimmed at the ridge) and front / eave fascia
        for sgn in (-1, 1):
            ov = 0.22
            t = 0.10
            xo = sgn * (wl + ov)
            T = np.array([[xo, -0.30, hf - 0.14], [xo, De, hf - 0.14], [0, Dr, hz], [0, -0.30, hz + 0.14]])
            n0 = np.cross(T[1] - T[0], T[3] - T[0])
            n0 /= np.linalg.norm(n0)
            n_out = n0 if sgn > 0 else -n0                    # outward / up normal of the top face
            dz = t / abs(n_out[2])
            U = T.copy()
            U[0] -= n_out * t
            U[1] -= n_out * t
            U[2] -= np.array([0.0, 0.0, dz])
            U[3] -= np.array([0.0, 0.0, dz])
            top = T if sgn > 0 else T[::-1]
            under = U[::-1] if sgn > 0 else U
            g.add(top[None], SLATE)
            g.add(under[None], SLATE)
            for a_, b_, want in ((0, 3, (0, -1, 0)), (0, 1, (sgn, 0, 0))):
                F = np.array([T[a_], T[b_], U[b_], U[a_]])
                nf = np.cross(F[1] - F[0], F[3] - F[0])
                if np.dot(nf, want) < 0:
                    F = F[::-1]
                g.add(F[None], SLATE)
        # window
        P = pointed_arch(win_w, hf - 0.55 - win_w * 0.9, win_w * 0.9, n=5, y_bottom=0.0)
        P[:, 1] += 0.32
        Po = offset_outline(P, 0.14)
        frame_ring(g, Po, P, -0.22, 0.20, STONE, y_inner_back=-0.05)
        _PANE_ID[0] += 1
        wall_fill(g, P, -0.05, GLASS, a={'glow': -1.0, 'pane': _PANE_ID[0]}, uv_center=(0.0, 0.0))
        # finial on gable
        boxes(g, [(0, -0.1, hz + 0.05)], [(0.12, 0.12, 0.7)], m=STONE)
        return g
    return cached(key, build)


# --------------------------------------------------------------------------------------
# buttresses / pinnacles / finials
# --------------------------------------------------------------------------------------

def _rect_ring(cx, y_front, y_back, w, z):
    """Rectangle ring (CCW from above) for a buttress stage: x in [-w/2,w/2], y from y_front (outer, -y) to y_back."""
    return np.array([[cx - w / 2, y_front, z], [cx + w / 2, y_front, z], [cx + w / 2, y_back, z], [cx - w / 2, y_back, z]])


def buttress(z_bottom, z_top, w0=1.7, p0=2.6, stages=3, pinnacle=True, pin_h=6.0):
    """Stepped buttress on a south wall: stage boxes + sloped weathering frusta + optional pinnacle."""
    key = ('butt', round(z_bottom, 1), round(z_top, 1), round(w0, 2), round(p0, 2), stages, pinnacle, round(pin_h, 1))

    def build():
        g = Geo('buttress', [STONE, WALL])
        H = z_top - z_bottom
        cuts = np.linspace(0.0, 1.0, stages + 1) ** 0.85
        z_edges = z_bottom + cuts * H
        w = w0
        p = p0
        emb = 0.6
        for k in range(stages):
            za, zb = z_edges[k], z_edges[k + 1]
            last = (k == stages - 1)
            wn = w * 0.82
            pn = p * 0.70
            slope_h = 0.9 if not last else 0.0
            # shaft
            r0 = _rect_ring(0, -p, emb, w, za)
            r1 = _rect_ring(0, -p, emb, w, zb - slope_h)
            loft(g, np.stack([r0, r1]), closed=True, m=STONE, uv_v='z')
            if not last:
                r2 = _rect_ring(0, -pn, emb, wn, zb)
                loft(g, np.stack([r1, r2]), closed=True, m=STONE, uv_v='z')
            else:
                # top: sloped cap (weathering) toward the wall
                r_top = _rect_ring(0, -p * 0.55, emb, w * 0.72, zb + 0.55)
                loft(g, np.stack([r1, r_top]), closed=True, m=STONE, uv_v='z')
                poly_cap(g, r_top, STONE, up=True)
            w, p = wn, pn
        if pinnacle:
            zt = z_top + 0.55
            pw = w0 * 0.55
            base = np.array([[-pw / 2, -pw / 2 - 0.1, zt], [pw / 2, -pw / 2 - 0.1, zt], [pw / 2, pw / 2 - 0.1, zt],
                             [-pw / 2, pw / 2 - 0.1, zt]])
            top = base.copy()
            top[:, 2] += pin_h * 0.45
            loft(g, np.stack([base, top]), closed=True, m=STONE)
            sq = np.array([[-pw / 2 - 0.12, -pw / 2 - 0.22, top[0, 2]], [pw / 2 + 0.12, -pw / 2 - 0.22, top[0, 2]],
                           [pw / 2 + 0.12, pw / 2 + 0.02, top[0, 2]], [-pw / 2 - 0.12, pw / 2 + 0.02, top[0, 2]]])
            sq2 = sq.copy()
            sq2[:, 2] += 0.25
            loft(g, np.stack([sq, sq2]), closed=True, m=STONE)
            ring = sq2
            apex = np.array([0.0, -0.1, top[0, 2] + 0.25 + pin_h * 0.55])
            pyramid(g, ring, apex, STONE)
            # crocket ball
            fp = np.array([(0.13, 0.0), (0.1, 0.25), (0.22, 0.4), (0.0, 0.7)])
            fp[:, 1] += apex[2] - 0.2
            lathe(g, fp, (0.0, -0.1, 0.0), segs=8, m=STONE)
        return g
    return cached(key, build)


def pinnacle_free(h=5.0, w=0.9, m=STONE):
    """Free-standing square pinnacle (origin at base centre)."""
    key = ('pin', round(h, 1), round(w, 2))

    def build():
        g = Geo('pinnacle', [STONE])
        base = np.array([[-w / 2, -w / 2, 0.0], [w / 2, -w / 2, 0.0], [w / 2, w / 2, 0.0], [-w / 2, w / 2, 0.0]])
        top = base.copy()
        top[:, 2] += h * 0.4
        loft(g, np.stack([base, top]), closed=True, m=STONE)
        sq = np.array([[-w / 2 - 0.1, -w / 2 - 0.1, top[0, 2]], [w / 2 + 0.1, -w / 2 - 0.1, top[0, 2]],
                       [w / 2 + 0.1, w / 2 + 0.1, top[0, 2]], [-w / 2 - 0.1, w / 2 + 0.1, top[0, 2]]])
        sq2 = sq.copy()
        sq2[:, 2] += 0.2
        loft(g, np.stack([sq, sq2]), closed=True, m=STONE)
        pyramid(g, sq2, np.array([0.0, 0.0, top[0, 2] + 0.2 + h * 0.6]), STONE)
        # crockets: tiny hooks up the four edges
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            for t in (0.3, 0.55, 0.78):
                r = (w / 2 + 0.1) * (1 - t) * 1.35
                z = top[0, 2] + 0.2 + h * 0.6 * t
                boxes(g, [(r * math.cos(a), r * math.sin(a), z)], [(0.16, 0.16, 0.2)], yaw=a, m=STONE)
        fp = np.array([(0.10, 0.0), (0.08, 0.2), (0.16, 0.32), (0.0, 0.6)])
        fp[:, 1] += top[0, 2] + 0.2 + h * 0.6 - 0.15
        lathe(g, fp, (0, 0, 0), segs=8, m=STONE)
        return g
    return cached(key, build)


def finial(h=4.0, ball=0.32, m='M_Copper'):
    key = ('fin', round(h, 1), round(ball, 2))

    def build():
        g = Geo('finial', [m])
        prof = [(ball * 1.1, 0.0), (ball * 0.55, h * 0.12), (ball * 0.55, h * 0.30), (ball, h * 0.36),
                (ball * 1.15, h * 0.46), (ball * 0.6, h * 0.58), (ball * 0.16, h * 0.78), (0.0, h)]
        lathe(g, prof, (0, 0, 0), segs=10, m=m)
        return g
    return cached(key, build)
