"""Gothic architectural vocabulary built on geo.MB.

Local frame convention for wall-mounted elements: x along the wall, z up,
outward normal = -y. rz for an outward direction phi is phi + pi/2.
"""
import math, random
from mathutils import Vector, Matrix
import geo
from geo import MB, mat_loc, TAU

ST = 'Stone'
TR = 'StoneTrim'
SL = 'Slate'
CU = 'Copper'
GL = 'Glass'
MT = 'Iron'
WD = 'Wood'

RNG = random.Random(7)
DETAIL = 1


def newell(pts):
    n = Vector((0, 0, 0))
    k = len(pts)
    for i in range(k):
        a = pts[i]
        b = pts[(i + 1) % k]
        n.x += (a[1] - b[1]) * (a[2] + b[2])
        n.y += (a[2] - b[2]) * (a[0] + b[0])
        n.z += (a[0] - b[0]) * (a[1] + b[1])
    return n


def face_toward(mb, pts, want, mat, M=None, glow=None):
    """add polygon pts (local), flipped so its normal points along 'want' (local)."""
    n = newell(pts)
    if n.dot(Vector(want)) < 0:
        pts = list(reversed(pts))
    mb.add(pts, [tuple(range(len(pts)))], mat, M, glow=glow)


def rz_for(phi):
    return phi + math.pi / 2


# ------------------------------------------------------------------ glow model
def window_glow(lit_p=0.55, level=1.0):
    """random inhabited-window emission. 0 = dark pane."""
    r = RNG.random()
    if r > lit_p:
        return 0.0
    g = math.exp(RNG.gauss(0.0, 0.75)) * level
    if RNG.random() < 0.18:
        g *= 0.15  # candle-dim rooms
    return max(0.02, min(g, 2.6))


def floor_lit(lit):
    """occupancy of one storey: some floors dark, some busy."""
    r = RNG.random()
    if r < 0.35:
        return lit * 0.15
    if r < 0.7:
        return lit * 0.8
    return min(0.95, lit * 1.6)


# ------------------------------------------------------------------ windows
def window(mb, M, w, h, kind='pointed', depth=0.32, frame=0.22, glow=0.0, mullion=None,
           sill=True, hood=True, sharp=1.0, trim=TR):
    """Window at local origin (bottom-centre on wall face y=0), projecting surround."""
    if kind == 'pointed':
        inner = geo.pointed_arch(w, h, 5 if DETAIL else 3, sharp)
    elif kind == 'round':
        inner = geo.round_arch(w, h, 7 if DETAIL else 4)
    else:
        inner = geo.rect_outline(w, h)
    outer = geo.offset_outline(inner, frame)
    n = len(inner)
    yg = -0.03
    yd = -depth
    # glass pane
    pane = [(x, yg, z) for x, z in inner]
    face_toward(mb, pane, (0, -1, 0), GL, M, glow=glow)
    cx = sum(p[0] for p in inner) / n
    cz = sum(p[1] for p in inner) / n
    for i in range(n):
        a, b = inner[i], inner[(i + 1) % n]
        oa, ob = outer[i], outer[(i + 1) % n]
        # reveal (faces the opening centre)
        mx, mz = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        face_toward(mb, [(a[0], yg, a[1]), (b[0], yg, b[1]), (b[0], yd, b[1]), (a[0], yd, a[1])],
                    (cx - mx, 0, cz - mz), trim, M)
        # front ring
        face_toward(mb, [(oa[0], yd, oa[1]), (ob[0], yd, ob[1]), (b[0], yd, b[1]), (a[0], yd, a[1])],
                    (0, -1, 0), trim, M)
        # outer side of surround
        omx, omz = (oa[0] + ob[0]) / 2, (oa[1] + ob[1]) / 2
        face_toward(mb, [(oa[0], 0.05, oa[1]), (ob[0], 0.05, ob[1]), (ob[0], yd, ob[1]), (oa[0], yd, oa[1])],
                    (omx - cx, 0, omz - cz), trim, M)
    if not DETAIL:
        return
    # mullions / transom / tracery (stone bars inside the reveal)
    if mullion is None:
        mullion = 1 if w > 0.9 else 0
        if w > 2.2:
            mullion = 2
    bw = 0.07 + 0.025 * w
    yb0, yb1 = yg - 0.001, yg - 0.12
    if kind == 'pointed':
        rad = w * sharp
        c = rad - w / 2
        ah = math.sqrt(max(rad * rad - c * c, 0.0))
        spring = max(h - ah, 0.0)
    elif kind == 'round':
        spring = h - w / 2
    else:
        spring = h
    if mullion > 0 and kind == 'pointed':
        k = mullion + 1
        wl = w / k
        sub_s = spring - 0.05 * w
        for i in range(mullion):
            x = -w / 2 + wl * (i + 1)
            mb.box(x - bw / 2, yb1, 0, x + bw / 2, yb0, sub_s + 0.02, trim, M)
        # sub-arches over each light
        for i in range(k):
            xc = -w / 2 + wl * (i + 0.5)
            sa = geo.pointed_arch(wl, wl * 0.9, 4, 1.0)
            pts = [(xc + x, sub_s + z) for x, z in sa if z > 1e-6]
            pts = [(xc + wl / 2, sub_s)] + pts + [(xc - wl / 2, sub_s)]
            bar_poly(mb, M, pts, bw * 0.8, yb0, yb1, trim)
        # oculus in the head
        head = h - sub_s
        orad = min(w * 0.23, head * 0.3)
        oz = sub_s + wl * 0.9 + (head - wl * 0.9) * 0.48
        if orad > 0.12 and oz + orad < h - 0.05:
            ring = [(orad * math.cos(TAU * j / 12), oz + orad * math.sin(TAU * j / 12)) for j in range(13)]
            bar_poly(mb, M, ring, bw * 0.7, yb0, yb1, trim)
            # trefoil cusps
            for j in range(3):
                a = math.pi / 2 + TAU * j / 3
                cx_, cz_ = 0.45 * orad * math.cos(a), oz + 0.45 * orad * math.sin(a)
                cr = 0.36 * orad
                cusp = [(cx_ + cr * math.cos(TAU * q / 8), cz_ + cr * math.sin(TAU * q / 8)) for q in range(9)]
                bar_poly(mb, M, cusp, bw * 0.45, yb0, yb1, trim)
    else:
        for i in range(mullion):
            x = -w / 2 + w * (i + 1) / (mullion + 1)
            mb.box(x - bw / 2, yb1, 0, x + bw / 2, yb0, spring + 0.25 * w, trim, M)
    if h > 2.2 * w and kind != 'rect':
        tz = spring * 0.5
        mb.box(-w / 2, yb1, tz - bw / 2, w / 2, yb0, tz + bw / 2, trim, M)
    if sill:
        mb.box(-w / 2 - frame - 0.08, yd - 0.1, -0.22, w / 2 + frame + 0.08, 0.05, 0.0, trim, M)
    if hood and kind != 'rect':
        # label / hood mould following the arch top
        hood_pts = geo.offset_outline(inner, frame + 0.12)
        top_idx = [i for i, p in enumerate(inner) if p[1] > h - (w * 0.9)]
        for i in top_idx:
            j = (i + 1) % n
            if j not in top_idx and not (inner[j][1] > h - w * 0.9):
                continue
            a, b = hood_pts[i], hood_pts[j]
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if L < 1e-4:
                continue
            ang = math.atan2(b[1] - a[1], b[0] - a[0])
            m = M @ Matrix.Translation(((a[0] + b[0]) / 2, 0, (a[1] + b[1]) / 2)) @ Matrix.Rotation(-ang, 4, 'Y')
            mb.box(-L / 2 - 0.02, yd - 0.08, -0.07, L / 2 + 0.02, 0.05, 0.07, trim, m)


def bar_poly(mb, M, pts, bw, y0, y1, mat):
    """square-section stone bar along a polyline (x,z) in the wall frame."""
    for (xa, za), (xb, zb) in zip(pts[:-1], pts[1:]):
        L = math.hypot(xb - xa, zb - za)
        if L < 1e-4:
            continue
        ang = math.atan2(zb - za, xb - xa)
        m = M @ Matrix.Translation(((xa + xb) / 2, 0, (za + zb) / 2)) @ Matrix.Rotation(-ang, 4, 'Y')
        mb.box(-L / 2 - bw * 0.3, y1, -bw / 2, L / 2 + bw * 0.3, y0, bw / 2, mat, m)


def door(mb, M, w, h, glow=0.0):
    inner = geo.pointed_arch(w, h, 5)
    outer = geo.offset_outline(inner, 0.45)
    n = len(inner)
    face_toward(mb, [(x, -0.02, z) for x, z in inner], (0, -1, 0), WD if glow <= 0 else 'Interior', M,
                glow=glow)
    cx = 0.0
    cz = h / 2
    for i in range(n):
        a, b = inner[i], inner[(i + 1) % n]
        oa, ob = outer[i], outer[(i + 1) % n]
        mx, mz = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        face_toward(mb, [(a[0], -0.02, a[1]), (b[0], -0.02, b[1]), (b[0], -0.6, b[1]), (a[0], -0.6, a[1])],
                    (cx - mx, 0, cz - mz), TR, M)
        face_toward(mb, [(oa[0], -0.6, oa[1]), (ob[0], -0.6, ob[1]), (b[0], -0.6, b[1]), (a[0], -0.6, a[1])],
                    (0, -1, 0), TR, M)
        omx, omz = (oa[0] + ob[0]) / 2, (oa[1] + ob[1]) / 2
        face_toward(mb, [(oa[0], 0.05, oa[1]), (ob[0], 0.05, ob[1]), (ob[0], -0.6, ob[1]), (oa[0], -0.6, oa[1])],
                    (omx - cx, 0, omz - cz), TR, M)


# ------------------------------------------------------------------ walls on a polygon
def poly_edges(poly):
    n = len(poly)
    for i in range(n):
        yield poly[i], poly[(i + 1) % n]


def edge_frame(p0, p1, t, z=0.0, out=0.0):
    """matrix at parameter t along edge p0->p1 on the wall face; outward is right-hand."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    ox, oy = dy / L, -dx / L
    x = p0[0] + dx * t + ox * out
    y = p0[1] + dy * t + oy * out
    phi = math.atan2(oy, ox)
    return mat_loc((x, y, z), rz_for(phi)), L


def windows_on_edge(mb, p0, p1, z, w, h, spacing, kind='pointed', lit=0.55, level=1.0,
                    margin=None, depth=0.3, frame=0.2, sharp=1.0, skip=None):
    L = math.dist(p0, p1)
    margin = spacing * 0.6 if margin is None else margin
    avail = L - 2 * margin
    if avail < w:
        return 0
    cnt = max(1, int(avail / spacing) + 1)
    cnt_ok = 0
    for k in range(cnt):
        t = (margin + (avail * (k + 0.5) / cnt)) / L
        if skip and skip(k, cnt):
            continue
        M, _ = edge_frame(p0, p1, t, z)
        window(mb, M, w, h, kind, depth=depth, frame=frame, glow=window_glow(lit, level), sharp=sharp)
        cnt_ok += 1
    return cnt_ok


def string_course(mb, poly, z, out=0.18, hgt=0.35, mat=TR):
    """projecting moulding band around a closed polygon (CCW)."""
    ring = offset_poly(poly, out)
    mb.loft([[(x, y, z) for x, y in ring], [(x, y, z + hgt) for x, y in ring],
             [(x, y, z + hgt + 0.12) for x, y in offset_poly(poly, out * 0.3)]], mat)


def offset_poly(poly, d):
    """outward offset of a CCW polygon (miter)."""
    n = len(poly)
    res = []
    for i in range(n):
        p0 = Vector(poly[i - 1])
        p1 = Vector(poly[i])
        p2 = Vector(poly[(i + 1) % n])
        e0 = (p1 - p0).normalized()
        e1 = (p2 - p1).normalized()
        n0 = Vector((e0.y, -e0.x))
        n1 = Vector((e1.y, -e1.x))
        m = n0 + n1
        if m.length < 1e-6:
            m = n0
        m.normalize()
        cs = max(m.dot(n0), 0.3)
        q = p1 + m * (d / cs)
        res.append((q.x, q.y))
    return res


def crenellate(mb, pts, z, closed=True, thick=0.55, low=1.0, merlon=0.85, mw=0.9, gap=0.7,
               mat=ST, out=0.0):
    """parapet wall with merlons along a polyline (wall centred 'out' outward of the line)."""
    n = len(pts)
    segs = n if closed else n - 1
    for i in range(segs):
        p0, p1 = pts[i], pts[(i + 1) % n]
        L = math.dist(p0, p1)
        if L < 0.05:
            continue
        mb.seg_box(p0, p1, z, z + low, thick, mat, off=-out)
        if not DETAIL:
            continue
        per = mw + gap
        cnt = int((L + gap) / per)
        if cnt < 1:
            continue
        slack = (L - (cnt * per - gap)) / 2
        dx, dy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
        nx, ny = dy, -dx
        for k in range(cnt):
            s0 = slack + k * per
            a = (p0[0] + dx * s0 - nx * out, p0[1] + dy * s0 - ny * out)
            b = (p0[0] + dx * (s0 + mw) - nx * out, p0[1] + dy * (s0 + mw) - ny * out)
            mb.seg_box(a, b, z + low, z + low + merlon, thick, mat)


def corbel_row(mb, pts, z, closed=True, depth=0.7, spacing=1.4, size=0.4, mat=TR):
    """machicolation corbels below an overhanging parapet (outward = right-hand)."""
    n = len(pts)
    segs = n if closed else n - 1
    for i in range(segs):
        p0, p1 = pts[i], pts[(i + 1) % n]
        L = math.dist(p0, p1)
        cnt = int(L / spacing)
        for k in range(cnt):
            t = (k + 0.5) / cnt
            M, _ = edge_frame(p0, p1, t, z)
            mb.box(-size / 2, -depth, -0.5, size / 2, 0.1, 0.0, mat, M)
            mb.box(-size / 2, -depth * 0.55, -1.0, size / 2, 0.1, -0.5, mat, M)
            mb.box(-size / 2, -depth * 0.25, -1.4, size / 2, 0.1, -1.0, mat, M)


def machicolated_parapet(mb, poly, z, over=0.7, mat=ST):
    """corbels + overhanging crenellated parapet on a closed CCW polygon at height z."""
    if DETAIL:
        corbel_row(mb, poly, z, depth=over + 0.05)
    ring = offset_poly(poly, over)
    # slab
    mb.loft([[(x, y, z) for x, y in poly], [(x, y, z) for x, y in ring],
             [(x, y, z + 0.3) for x, y in ring]], TR, cap_bot=False, cap_top=False)
    crenellate(mb, offset_poly(poly, over - 0.28), z + 0.3, True, thick=0.55)


# ------------------------------------------------------------------ roofs
def cone_roof(mb, x, y, z, r, h, n=24, mat=SL, flare=0.9, bell=0.12, finial=True, M=None):
    prof = [(r + flare, z - 0.1), (r + flare, z + 0.15), (r + flare * 0.35, z + 0.9)]
    steps = 8
    for i in range(1, steps + 1):
        t = i / steps
        rr = (r + flare * 0.3) * (1 - t) * (1 + bell * math.sin(t * math.pi) * -1)
        prof.append((max(rr, 0.0), z + 0.9 + (h - 0.9) * t))
    prof[-1] = (0.0, z + h)
    m = mat_loc((x, y, 0))
    if M is not None:
        m = M @ m
    mb.lathe(prof, n, mat, m)
    if finial:
        finial_spike(mb, x, y, z + h - 0.4, h * 0.05 + 1.2, M=M)


def finial_spike(mb, x, y, z, h, M=None, mat=MT):
    s = h / 3.0
    prof = [(0.12 * s, z), (0.2 * s, z + 0.35 * s), (0.28 * s, z + 0.6 * s), (0.1 * s, z + 0.9 * s),
            (0.14 * s, z + 1.2 * s), (0.05 * s, z + 1.3 * s), (0.0, z + h)]
    m = mat_loc((x, y, 0))
    if M is not None:
        m = M @ m
    mb.lathe(prof, 8, mat, m)


def pyramid_roof(mb, poly, z, h, over=0.5, mat=SL, finial=True, bell=0.1):
    ring = offset_poly(poly, over)
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    rings = [[(x, y, z - 0.1) for x, y in ring], [(x, y, z + 0.2) for x, y in ring]]
    steps = 5
    for i in range(1, steps):
        t = i / steps
        k = (1 - t) * (1 - bell * math.sin(t * math.pi))
        rings.append([(cx + (x - cx) * k, cy + (y - cy) * k, z + 0.2 + (h - 0.2) * t) for x, y in ring])
    rings.append([(cx, cy, z + h)])
    mb.loft(rings, mat)
    if finial:
        finial_spike(mb, cx, cy, z + h - 0.3, 1.5 + h * 0.06)


def gable_roof(mb, cx, cy, L, W, z, h, rz=0.0, over=0.5, mat=SL, gable_mat=ST, gables=True,
               dormers=0, dormer_lit=0.35, crest=True, hip=False):
    """Roof ridge along local x. L,W = footprint of the walls below."""
    M = mat_loc((cx, cy, 0), rz)
    hx, hy = L / 2 + over * 0.6, W / 2 + over
    th = 0.35
    if hip:
        rings = [[(-hx, -hy, z), (hx, -hy, z), (hx, hy, z), (-hx, hy, z)]]
        inset = min(W / 2 * 0.9, L / 2 - 0.5)
        mb.add([(-hx, -hy, z), (hx, -hy, z), (hx, hy, z), (-hx, hy, z),
                (-hx + inset, 0, z + h), (hx - inset, 0, z + h)],
               [(0, 1, 5, 4), (2, 3, 4, 5), (1, 2, 5), (3, 0, 4), (3, 2, 1, 0)], mat, M)
    else:
        # slab roof with thickness at the eaves
        v = [(-hx, -hy, z), (hx, -hy, z), (hx, 0, z + h), (-hx, 0, z + h),
             (-hx, hy, z), (hx, hy, z),
             (-hx, -hy, z - th), (hx, -hy, z - th), (-hx, hy, z - th), (hx, hy, z - th)]
        f = [(0, 1, 2, 3), (3, 2, 5, 4), (6, 7, 1, 0), (4, 5, 9, 8), (6, 0, 3, 4, 8), (7, 9, 5, 2, 1),
             (8, 9, 7, 6)]
        mb.add(v, f, mat, M)
        if gables:
            gx = L / 2
            for sx in (-1, 1):
                x0 = sx * gx
                x1 = sx * (gx - 0.6)
                gv = [(x0, -W / 2, z - 0.4), (x0, W / 2, z - 0.4), (x0, 0, z + h * (W / 2) / hy + 0.4),
                      (x1, -W / 2, z - 0.4), (x1, W / 2, z - 0.4), (x1, 0, z + h * (W / 2) / hy + 0.4)]
                if sx > 0:
                    gf = [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
                else:
                    gf = [(2, 1, 0), (3, 4, 5), (1, 4, 3, 0), (2, 5, 4, 1), (0, 3, 5, 2)]
                mb.add(gv, gf, gable_mat, M)
    if crest and DETAIL:
        # ridge cresting: small iron spikes
        cnt = int(L / 2.5)
        for k in range(cnt):
            x = -L / 2 + L * (k + 0.5) / cnt
            mb.box(x - 0.05, -0.05, z + h, x + 0.05, 0.05, z + h + 0.7, MT, M)
        mb.box(-L / 2, -0.12, z + h - 0.1, L / 2, 0.12, z + h + 0.12, MT, M)
    if dormers and DETAIL:
        slope = h / hy
        for k in range(dormers):
            x = -L / 2 + L * (k + 0.5) / dormers
            for side in (-1, 1):
                yb = side * (hy - 1.6)
                zb = z + (hy - abs(yb)) * slope
                dm = M @ mat_loc((x, yb, zb), 0 if side < 0 else math.pi)
                dormer(mb, dm, 1.6, 2.4, dormer_lit)


def dormer(mb, M, w, h, lit):
    """small gabled dormer; local -y faces down-slope."""
    d = 2.2
    mb.box(-w / 2, -0.2, -0.6, w / 2, d, h, ST, M)
    rv = [(-w / 2 - 0.25, -0.3, h - 0.05), (w / 2 + 0.25, -0.3, h - 0.05), (0, -0.3, h + w * 0.9),
          (-w / 2 - 0.25, d, h - 0.05), (w / 2 + 0.25, d, h - 0.05), (0, d, h + w * 0.9)]
    mb.add(rv, [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)], SL, M)
    wm = M @ Matrix.Translation((0, -0.2, 0.3))
    window(mb, wm, w * 0.55, h * 0.75, 'pointed', depth=0.12, frame=0.12, glow=window_glow(lit),
           mullion=0, sill=False, hood=False)
    finial_spike(mb, 0, -0.3, h + w * 0.85, 0.9, M=M)


# ------------------------------------------------------------------ buttresses & pinnacles
def pinnacle(mb, x, y, z, s=0.8, h=4.0, rz=0.0, mat=TR):
    M = mat_loc((x, y, 0), rz)
    sh = h * 0.38
    mb.box(-s / 2, -s / 2, z, s / 2, s / 2, z + sh, mat, M)
    if DETAIL:
        mb.box(-s / 2 - 0.08, -s / 2 - 0.08, z + sh, s / 2 + 0.08, s / 2 + 0.08, z + sh + 0.15, mat, M)
    rings = [[(-s / 2, -s / 2, z + sh + 0.15), (s / 2, -s / 2, z + sh + 0.15), (s / 2, s / 2, z + sh + 0.15),
              (-s / 2, s / 2, z + sh + 0.15)], [(0, 0, z + h)]]
    mb.loft(rings, mat, M)
    if DETAIL:
        # crockets as small spurs on the spirelet
        for t in (0.35, 0.65):
            zz = z + sh + 0.15 + (h - sh - 0.15) * t
            ss = s / 2 * (1 - t) + 0.12
            for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                mb.box(sx * ss - 0.07, sy * ss - 0.07, zz, sx * ss + 0.07, sy * ss + 0.07, zz + 0.3, mat, M)


def buttress(mb, M, z0, z1, w=1.2, d=2.2, steps=3, pin=True):
    """stepped buttress on wall face (local frame). Weathered set-offs."""
    hseg = (z1 - z0) / steps
    for k in range(steps):
        dd = d * (1 - k / steps * 0.62)
        za, zb = z0 + k * hseg, z0 + (k + 1) * hseg
        mb.box(-w / 2, -dd, za, w / 2, 0.2, zb - 0.45, ST, M)
        # sloped set-off
        dn = d * (1 - (k + 1) / steps * 0.62) if k < steps - 1 else 0.3
        v = [(-w / 2, -dd, zb - 0.45), (w / 2, -dd, zb - 0.45), (w / 2, 0.2, zb - 0.45), (-w / 2, 0.2, zb - 0.45),
             (-w / 2, -dn, zb), (w / 2, -dn, zb), (w / 2, 0.2, zb), (-w / 2, 0.2, zb)]
        mb.add(v, [(3, 2, 1, 0), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)], TR, M)
    if pin:
        p = M @ Vector((0, -0.4, z1))
        rz = math.atan2(M[1][0], M[0][0])
        pinnacle(mb, p.x, p.y, z1, 0.75, 4.2, rz)


def flying_buttress(mb, p_wall, p_pier, z_wall, z_pier_top, width=0.6, mat=ST):
    """arched strut from a pier top down to a wall head (quarter arch underside)."""
    dx, dy = p_wall[0] - p_pier[0], p_wall[1] - p_pier[1]
    L = math.hypot(dx, dy)
    a = math.atan2(dy, dx)
    M = mat_loc((p_pier[0], p_pier[1], 0), a)
    seg = 8
    top = []
    bot = []
    for i in range(seg + 1):
        t = i / seg
        x = L * t
        zt = geo.lerp(z_pier_top, z_wall, t) + 0.6
        zb = geo.lerp(z_pier_top - 2.0, z_wall - 5.5, t) + math.sin(t * math.pi) * -1.5 + (1 - t) * 0.0
        zb = min(zb, zt - 0.8)
        # quarter-ellipse soffit
        zb = z_pier_top - 1.2 - (1 - math.cos(t * math.pi / 2)) * 0 - (z_pier_top - z_wall + 4.0) * (1 - math.sqrt(max(0, 1 - t * t)))
        zb = min(zb, zt - 0.8)
        top.append((x, zt))
        bot.append((x, zb))
    hw = width / 2
    for i in range(seg):
        (x0, t0), (x1, t1) = top[i], top[i + 1]
        (_, b0), (_, b1) = bot[i], bot[i + 1]
        v = [(x0, -hw, b0), (x1, -hw, b1), (x1, -hw, t1), (x0, -hw, t0),
             (x0, hw, b0), (x1, hw, b1), (x1, hw, t1), (x0, hw, t0)]
        mb.add(v, [(0, 1, 2, 3), (5, 4, 7, 6), (3, 2, 6, 7), (4, 5, 1, 0)], mat, M)


# ------------------------------------------------------------------ towers
def circle(cx, cy, r, n, phase=0.0):
    return [(cx + r * math.cos(phase + TAU * i / n), cy + r * math.sin(phase + TAU * i / n)) for i in range(n)]


def round_tower(mb, x, y, r, z0, z1, n=24, roof='cone', roof_h=None, roof_mat=SL, win_levels=None,
                lit=0.5, level=1.0, crown='mach', taper=0.0, win_w=0.9, win_h=2.2, bands=True,
                win_phase=0.0, win_every=2, finial=True, bell=0.12, flare=0.9, corbel=False):
    """Round tower (n-gon). crown: 'mach' machicolated crenellation, 'eave' plain eave, 'none'."""
    phase = math.pi / n
    rt = r * (1 - taper)
    if corbel and DETAIL:
        # corbelled base: moulded ogee cone ending in a small boss
        prof = [(0.0, z0 - r * 1.9), (0.22, z0 - r * 1.85), (0.3, z0 - r * 1.6)]
        for k in range(1, 9):
            t_ = k / 8
            prof.append((0.3 + (r - 0.3) * (math.sin(t_ * math.pi / 2) ** 1.4), z0 - r * 1.6 * (1 - t_)))
        prof.append((r + 0.12, z0 - 0.05))
        prof.append((r + 0.12, z0 + 0.25))
        prof.append((r, z0 + 0.3))
        mb.lathe(prof, n, TR, mat_loc((x, y, 0)), phase=phase, cap_bot=False, cap_top=False)
    body = [[(x + r * math.cos(phase + TAU * i / n), y + r * math.sin(phase + TAU * i / n), z0) for i in range(n)],
            [(x + rt * math.cos(phase + TAU * i / n), y + rt * math.sin(phase + TAU * i / n), z1) for i in range(n)]]
    mb.loft(body, ST)
    # windows on alternate facets per level
    if win_levels is None:
        H = z1 - z0
        nl = max(1, int((H - 4) / 5.5))
        win_levels = [z0 + 3.0 + i * (H - 6) / max(nl, 1) for i in range(nl)]
    for li, wz in enumerate(win_levels):
        fl = floor_lit(lit)
        t = (wz - z0) / max(z1 - z0, 1e-3)
        rr = geo.lerp(r, rt, t) * math.cos(math.pi / n)
        for i in range(n):
            if (i + li) % win_every:
                continue
            phi = TAU * (i + 0.5) / n + phase + win_phase * 0
            phi = phase + TAU * i / n + math.pi / n
            M = mat_loc((x + rr * math.cos(phi), y + rr * math.sin(phi), wz), rz_for(phi))
            ww = min(win_w, 2 * rr * math.tan(math.pi / n) - 0.6)
            if ww < 0.4:
                continue
            window(mb, M, ww, win_h, 'pointed', depth=0.25, frame=0.16, glow=window_glow(fl, level))
    if bands and DETAIL:
        for li, wz in enumerate(win_levels[1:], 1):
            zb = wz - 1.1
            t = (zb - z0) / max(z1 - z0, 1e-3)
            string_course(mb, circle(x, y, geo.lerp(r, rt, t), n, phase), zb, out=0.14, hgt=0.28)
    top = z1
    if crown == 'mach':
        machicolated_parapet(mb, circle(x, y, rt, n, phase), z1, over=0.65)
        top = z1 + 0.3
    elif crown == 'eave':
        string_course(mb, circle(x, y, rt, n, phase), z1 - 0.6, out=0.25, hgt=0.4)
    if roof == 'cone':
        rh = roof_h if roof_h is not None else rt * 3.2
        rr = rt + (0.45 if crown == 'mach' else 0.0)
        cone_roof(mb, x, y, top, rr, rh, max(n, 16), roof_mat, flare=flare if crown != 'mach' else 0.35,
                  bell=bell, finial=finial)
        return top + rh
    return top


def square_tower(mb, x, y, w, d, z0, z1, rz=0.0, roof='pyramid', roof_h=None, roof_mat=SL, lit=0.5,
                 level=1.0, win_w=1.1, win_h=2.6, levels=None, crown='mach', corner_turrets=False,
                 buttresses=False, bands=True):
    M = mat_loc((x, y, 0), rz)
    loc = [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]
    poly = [tuple((M @ Vector((px, py, 0)))[:2]) for px, py in loc]
    mb.prism(poly, z0, z1, ST)
    H = z1 - z0
    if levels is None:
        nl = max(1, int((H - 4) / 6.0))
        levels = [z0 + 3.5 + i * (H - 7) / max(nl, 1) for i in range(nl)]
    for p0, p1 in poly_edges(poly):
        L = math.dist(p0, p1)
        sp = max(win_w * 2.4, L / max(1, int(L / (win_w * 2.6))))
        for wz in levels:
            windows_on_edge(mb, p0, p1, wz, win_w, win_h, sp, lit=floor_lit(lit), level=level, margin=1.2)
        if buttresses and DETAIL:
            for t in (0.0, 1.0):
                pass
    if bands and DETAIL:
        for wz in levels[1:]:
            string_course(mb, poly, wz - 1.2, out=0.15, hgt=0.3)
    top = z1
    if crown == 'mach':
        machicolated_parapet(mb, poly, z1, over=0.7)
        top = z1 + 0.3
    if corner_turrets:
        for px, py in poly:
            round_tower(mb, px, py, 1.6, z1 - 7, z1 + 3.5, n=12, roof='cone', roof_h=6.5, crown='eave',
                        win_levels=[z1 - 2], lit=0.3, bands=False, win_w=0.5, win_h=1.3, flare=0.35, corbel=True)
    if roof == 'pyramid':
        rh = roof_h if roof_h is not None else max(w, d) * 1.6
        inner = offset_poly(poly, -0.3) if crown == 'mach' else poly
        pyramid_roof(mb, inner, top, rh, over=0.4 if crown != 'mach' else 0.05, mat=roof_mat)
        return top + rh
    if roof == 'spire8':
        rh = roof_h if roof_h is not None else max(w, d) * 3.0
        rr = min(w, d) / 2 * 0.95
        oct_ = circle(x, y, rr, 8, math.pi / 8 + rz)
        pyramid_roof(mb, oct_, top, rh, over=0.2, mat=roof_mat, bell=0.05)
        return top + rh
    return top


def hall_block(mb, cx, cy, L, W, z0, z1, rz=0.0, roof_h=None, lit=0.5, level=1.0, win_w=1.2,
               win_h=2.8, levels=None, bay=4.5, buttress_d=0.0, parapet=True, dormers=0,
               roof_mat=SL, win_kind='pointed', gables=True, hip=False, end_windows=True, bands=True,
               roof=True, win_sharp=1.0):
    """Rectangular wing with windows, optional buttresses, parapet and gabled roof."""
    M = mat_loc((cx, cy, 0), rz)
    loc = [(-L / 2, -W / 2), (L / 2, -W / 2), (L / 2, W / 2), (-L / 2, W / 2)]
    poly = [tuple((M @ Vector((px, py, 0)))[:2]) for px, py in loc]
    mb.prism(poly, z0, z1, ST)
    H = z1 - z0
    if levels is None:
        nl = max(1, int((H - 3) / 5.0))
        levels = [z0 + 2.8 + i * (H - 5.5) / max(nl, 1) for i in range(nl)]
    for ei, (p0, p1) in enumerate(poly_edges(poly)):
        Le = math.dist(p0, p1)
        if ei % 2 == 1 and not end_windows:
            continue
        nb = max(1, round(Le / bay))
        sp = Le / nb
        for wz in levels:
            windows_on_edge(mb, p0, p1, wz, win_w, win_h, sp, win_kind, floor_lit(lit), level,
                            margin=sp * 0.5 - 0.01, sharp=win_sharp)
        if buttress_d > 0 and DETAIL and ei % 2 == 0:
            for k in range(nb + 1):
                t = k / nb
                if 0 < k < nb:
                    Mb, _ = edge_frame(p0, p1, t, 0)
                    buttress(mb, Mb, z0, z1 - 0.5, 1.1, buttress_d, 3, pin=parapet)
    if bands and DETAIL:
        for wz in levels[1:]:
            string_course(mb, poly, wz - 1.0, out=0.14, hgt=0.3)
    if parapet:
        string_course(mb, poly, z1 - 0.2, out=0.3, hgt=0.35)
        crenellate(mb, offset_poly(poly, 0.05), z1 + 0.15, True, thick=0.45, low=0.8, merlon=0.7) if DETAIL else None
    if roof:
        rh = roof_h if roof_h is not None else W * 0.75
        gable_roof(mb, cx, cy, L, W, z1 + (0.3 if parapet else 0), rh, rz, over=0.1 if parapet else 0.6,
                   mat=roof_mat, dormers=dormers, gables=gables, hip=hip)
    return poly
