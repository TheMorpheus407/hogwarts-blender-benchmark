"""Tower generators: round towers / turrets, square towers with spires."""
import numpy as np
import math
from hw_geo import (Geo, boxes, beams, lathe, loft, sweep, prism, pyramid, ngon, poly_cap, xf, rotz)
import hw_gothic as G
import hw_arch as A

STONE = 'M_Stone'
DRESS = 'M_StoneDress'
SLATE = 'M_Slate'
COPPER = 'M_Copper'


# --------------------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------------------

def pick_lit(rng, p, cool_p=0.05):
    """None (dark) or (intensity, hue)."""
    if rng.random() > p:
        return None
    base = 0.30 + 0.70 * rng.random() ** 0.8
    if rng.random() < cool_p:
        hue = 0.85 + 0.15 * rng.random()
    else:
        hue = 0.02 + 0.55 * rng.random() ** 1.3
    return (base, hue)


def corbel_ring(g, x, y, z_top, R, n, m=STONE, out=(0.5, 1.0, 1.5), h=0.9, width=0.8, embed=0.35):
    th = 2 * math.pi * (np.arange(n) + 0.5) / n
    for i, o in enumerate(out):
        zb = z_top - h * (len(out) - i)
        rc = R + (o - embed) / 2.0
        C = np.column_stack([x + rc * np.cos(th), y + rc * np.sin(th), np.full(n, zb)])
        boxes(g, C, [(o + embed, width, h)], yaw=th, m=m)


def merlon_ring(g, x, y, z, Rp, n, m=STONE, h=1.35, t=0.85, fill=0.55):
    th = 2 * math.pi * (np.arange(n) + 0.5) / n
    bw = 2 * math.pi * Rp / n * fill
    rc = Rp - t / 2.0
    C = np.column_stack([x + rc * np.cos(th), y + rc * np.sin(th), np.full(n, z)])
    boxes(g, C, [(t, bw, h)], yaw=th, m=m)
    # caps
    boxes(g, C + np.array([0, 0, h]), [(t + 0.16, bw + 0.16, 0.16)], yaw=th, m=m)


def ring_wall(g, x, y, z, Rp, t, h, m=STONE, segs=48):
    prof = [(Rp - t, z), (Rp, z), (Rp, z + h), (Rp - t, z + h)]
    lathe(g, prof, (x, y, 0), segs=segs, m=m)


def cone_profile(rc, H, n=16, p=1.16, r_top=0.25):
    t = np.linspace(0.0, 1.0, n)
    r = r_top + (rc - r_top) * (1.0 - t) ** p
    return np.column_stack([r, H * t])


def cone_pitch(rc, H, t, p=1.16, r_top=0.25):
    drdt = -p * (rc - r_top) * (1.0 - t) ** (p - 1.0)
    return math.degrees(math.atan2(H, abs(drdt)))


def cone_radius(rc, t, p=1.16, r_top=0.25):
    return r_top + (rc - r_top) * (1.0 - t) ** p


def window_tier(g, x, y, z0, R, z_off, n, proto, rng, lit_p, jitter=0.25, skip_p=0.0, phase=None, hue_bias=None):
    ph = rng.random() * 2 * math.pi if phase is None else phase
    for k in range(n):
        if rng.random() < skip_p:
            continue
        th = ph + 2 * math.pi * k / n + (rng.random() - 0.5) * jitter * 2 * math.pi / n
        pos = (x + (R - 0.02) * math.cos(th), y + (R - 0.02) * math.sin(th), z0 + z_off)
        g.add_geo(proto, pos=pos, outward=(math.cos(th), math.sin(th)), lit=pick_lit(rng, lit_p), rng=rng)


def string_course_profile(R, zb, out=0.5, h=0.45):
    return [(R, zb - 0.3), (R + out, zb - 0.3), (R + out, zb + h - 0.3), (R, zb + h + 0.05)]


# --------------------------------------------------------------------------------------
# round tower
# --------------------------------------------------------------------------------------

def round_tower(g, x, y, z0, R, shaft, cone, rng, bands=(), tiers=(), top='corbel_cone', cone_p=1.16,
                cone_top=0.25, cone_mat=SLATE, dormers=(), ribs=0, fin=6.0, fin_mat=COPPER, lit_p=0.55,
                segs=40, found=24.0, flare=2.4, gal_h=0.55, corbels=True, dormer_scale=1.0, wall_mat=STONE,
                band_out=0.5, eave_out=1.9, crenel_h=1.35, cone_base_z=None, ribs_mat=None, foot_z=None,
                smooth=True, yaw0=0.0):
    """Round tower whose base sits at z0 (foundation continues `found` below)."""
    # ---- shaft profile
    if found > 0:
        prof = [(R + flare, -found), (R + flare * 0.55, -found * 0.5), (R + 0.9, -3.5), (R + 0.45, 0.0), (R, 3.2)]
    else:
        prof = [(R, 0.0)]
    for zb in sorted(bands):
        prof += string_course_profile(R, zb, band_out)
    prof += [(R, shaft)]
    lathe(g, prof, (x, y, z0), segs=segs, m=wall_mat, smooth=smooth, yaw0=yaw0)
    zc = shaft
    rc = R
    if top in ('corbel_cone', 'crenel_cone'):
        ncorb = max(8, int(round(2 * math.pi * R / 1.5)))
        if corbels:
            corbel_ring(g, x, y, z0 + shaft, R, ncorb, m=DRESS, out=(0.55, 1.05, eave_out * 0.8))
        slab = [(R, shaft), (R + eave_out, shaft), (R + eave_out, shaft + 0.55), (R + eave_out - 0.35, shaft + 0.72)]
        lathe(g, slab, (x, y, z0), segs=segs, m=DRESS, smooth=smooth, yaw0=yaw0)
        zc = shaft + 0.72
        rc = R + eave_out - 0.35
        if top == 'crenel_cone':
            ring_wall(g, x, y, z0 + zc - 0.1, R + eave_out - 0.1, 0.85, 1.2, m=wall_mat, segs=segs)
            nm = max(8, int(round(2 * math.pi * (R + eave_out) / 2.1)))
            merlon_ring(g, x, y, z0 + zc + 1.1, R + eave_out - 0.1, nm, m=wall_mat, h=crenel_h)
            Rd = R - 0.4
            lathe(g, [(Rd, zc - 0.05), (Rd, zc + 3.0)], (x, y, z0), segs=segs, m=wall_mat, smooth=smooth, yaw0=yaw0)
            zc = zc + 3.0
            rc = Rd + 0.75
    else:
        cor = [(R, shaft - 0.3), (R + 0.9, shaft - 0.3), (R + 0.9, shaft + 0.35), (R + 0.35, shaft + 0.75)]
        lathe(g, cor, (x, y, z0), segs=segs, m=DRESS, smooth=smooth, yaw0=yaw0)
        zc = shaft + 0.75
        rc = R + 0.35
    # ---- cone
    cp = cone_profile(rc, cone, 18, cone_p, cone_top)
    cp[:, 1] += zc
    lathe(g, cp, (x, y, z0), segs=segs, m=cone_mat, uv_v='slant', crease_deg=50, smooth=smooth, yaw0=yaw0)
    # ---- ribs (hip rolls)
    if ribs:
        for k in range(ribs):
            th = 2 * math.pi * k / ribs + 0.3
            pts = []
            for t in np.linspace(0.02, 0.97, 14):
                rr = cone_radius(rc, t, cone_p, cone_top) + 0.10
                pts.append((x + rr * math.cos(th), y + rr * math.sin(th), z0 + zc + cone * t))
            pts = np.array(pts)
            beams(g, pts[:-1], pts[1:], 0.26, 0.26, m=ribs_mat or cone_mat)
    # ---- dormers on the cone
    for (t, n, scale) in dormers:
        r_t = cone_radius(rc, t, cone_p, cone_top)
        ph = cone_pitch(rc, cone, t, cone_p, cone_top)
        proto = G.dormer(min(ph, 80.0))
        off = rng.random() * 2 * math.pi
        for k in range(n):
            th = off + 2 * math.pi * k / n
            pos = (x + (r_t - 0.05) * math.cos(th), y + (r_t - 0.05) * math.sin(th), z0 + zc + cone * t)
            g.add_geo(proto, pos=pos, outward=(math.cos(th), math.sin(th)), scale=scale * dormer_scale,
                      lit=pick_lit(rng, lit_p), rng=rng)
    # ---- finial
    if fin > 0:
        g.add_geo(G.finial(fin, 0.42 if fin > 3 else 0.28, fin_mat), pos=(x, y, z0 + zc + cone - 0.35))
    # ---- windows
    for tr in tiers:
        z_off, n, proto = tr[0], tr[1], tr[2]
        skip_p = tr[3] if len(tr) > 3 else 0.0
        window_tier(g, x, y, z0, R, z_off, n, proto, rng, lit_p, skip_p=skip_p)
    return dict(top=z0 + zc + cone + fin)


# --------------------------------------------------------------------------------------
# bracket (corbelled) turret: starts in mid-air on an inverted-cone corbel
# --------------------------------------------------------------------------------------

def bracket_turret(g, x, y, z_base, R, shaft, cone, rng, lit_p=0.5, cone_mat=SLATE, fin=3.5, segs=20, corbel_h=7.0):
    prof = [(0.6, z_base - corbel_h), (R * 0.5, z_base - corbel_h * 0.7), (R * 0.8, z_base - corbel_h * 0.35),
            (R + 0.35, z_base - 0.5), (R + 0.35, z_base)]
    # underside is a steep inverted cone -> profile bottom->top, solid on the left
    lathe(g, prof, (x, y, 0), segs=segs, m=DRESS)
    return round_tower(g, x, y, z_base, R, shaft, cone, rng, bands=(shaft * 0.5,), tiers=(),
                       top='plain', cone_mat=cone_mat, fin=fin, lit_p=lit_p, segs=segs, found=0.0, flare=0.0,
                       band_out=0.3)


# --------------------------------------------------------------------------------------
# square tower with a spire
# --------------------------------------------------------------------------------------

def spire_square(g, x, y, z_base, half, H, rng, sides=4, p=1.12, lucarnes=((0.32, 1.0),), crockets=True,
                 mat=SLATE, fin=6.0, lit_p=0.4, yaw=0.0, skirt=0.9):
    """Pyramidal spire (4 or 8 sided) whose eaves sit at z_base; `half` = half base width."""
    rc = half * math.sqrt(2.0) if sides == 4 else half / math.cos(math.pi / sides)
    prof = cone_profile(rc + skirt * 0.5, H, 14, p, 0.18)
    prof[:, 1] += z_base
    lathe(g, prof, (x, y, 0), segs=sides, m=mat, smooth=False, yaw0=math.pi / sides + yaw, uv_v='slant')
    # crockets along the edges
    if crockets:
        for k in range(sides):
            th = math.pi / sides + yaw + 2 * math.pi * k / sides
            ts = np.linspace(0.12, 0.86, 9)
            for t in ts:
                rr = cone_radius(rc + skirt * 0.5, t, p, 0.18) + 0.05
                z = z_base + H * t
                sc = 1.0 - 0.6 * t
                boxes(g, [(x + rr * math.cos(th), y + rr * math.sin(th), z)], [(0.5 * sc + 0.15, 0.32 * sc + 0.12, 0.62 * sc + 0.2)],
                      yaw=th, m=DRESS)
    # lucarnes
    for (t, sc) in lucarnes:
        rr = cone_radius(rc + skirt * 0.5, t, p, 0.18)
        # distance to a face centre (spire face is flat): apothem
        ap = rr * math.cos(math.pi / sides)
        pitch = math.degrees(math.atan2(H, (rc + skirt * 0.5) * p * math.cos(math.pi / sides) * (1 - t) ** (p - 1)))
        proto = G.dormer(min(pitch, 80.0))
        for k in range(sides):
            th = 2 * math.pi * k / sides + yaw
            pos = (x + (ap - 0.05) * math.cos(th), y + (ap - 0.05) * math.sin(th), z_base + H * t)
            g.add_geo(proto, pos=pos, outward=(math.cos(th), math.sin(th)), scale=sc, lit=pick_lit(rng, lit_p), rng=rng)
    if fin > 0:
        g.add_geo(G.finial(fin, 0.4, COPPER), pos=(x, y, z_base + H - 0.3))


def square_tower(g, x, y, z0, sx, sy, shaft, rng, bands=(), tiers=(), found=24.0, batter=1.6, wall_mat=STONE,
                 lit_p=0.5, parapet=True, corner_pinnacles=True, clock=None, spire=None, hip=None,
                 faces=('S', 'E', 'N', 'W')):
    """Square tower.  tiers: (z_off, n_per_face, proto, skip_p).  clock: dict(z=, r=)."""
    hx, hy = sx / 2.0, sy / 2.0

    def off(d):
        return np.array([[x - hx - d, y - hy - d], [x + hx + d, y - hy - d], [x + hx + d, y + hy + d],
                         [x - hx - d, y + hy + d]])
    poly = off(0.0)

    def ring(d, z):
        return np.column_stack([off(d), np.full(4, z)])
    loft(g, np.stack([ring(batter + 1.6, z0 - found), ring(batter + 0.8, z0 - found * 0.5), ring(batter * 0.75, z0 - 4.0),
                      ring(0.35, z0), ring(0.0, z0 + 3.5), ring(0.0, z0 + shaft)]), closed=True, m=wall_mat)
    # string courses as sweeps of a small profile
    for zb in bands:
        path = np.column_stack([poly, np.full(4, z0 + zb)])
        prof = np.array([[0.0, -0.3], [0.5, -0.3], [0.5, 0.15], [0.0, 0.5]])
        sweep(g, prof, path, closed=True, m=DRESS)
    # cornice + parapet
    zt = z0 + shaft
    path = np.column_stack([poly, np.full(4, zt)])
    prof = np.array([[0.0, -0.9], [0.55, -0.9], [0.55, -0.45], [1.0, -0.45], [1.0, 0.25], [0.0, 0.25]])
    sweep(g, prof, path, closed=True, m=DRESS)
    top_z = zt + 0.25
    if parapet:
        for (ia, ib) in ((0, 1), (1, 2), (2, 3), (3, 0)):
            p0, p1 = poly[ia], poly[ib]
            d = p1 - p0
            Ln = float(np.linalg.norm(d))
            u = d / Ln
            outward = np.array([u[1], -u[0]])
            n = max(3, int(Ln / 2.0))
            ts = (np.arange(n) + 0.5) / n
            C = np.column_stack([p0[0] + u[0] * ts * Ln + outward[0] * 0.55, p0[1] + u[1] * ts * Ln + outward[1] * 0.55,
                                 np.full(n, top_z + 0.8)])
            yawv = math.atan2(u[1], u[0])
            boxes(g, C, [(Ln / n * 0.55, 0.9, 1.3)], yaw=yawv, m=wall_mat)
            mid = (p0 + p1) / 2.0 + outward * 0.55
            boxes(g, [(mid[0], mid[1], top_z)], [(Ln + 1.6, 0.9, 0.8)], yaw=yawv, m=wall_mat)
        top_z += 0.8
    # corner pinnacles / turrets
    if corner_pinnacles:
        for (cx_, cy_) in poly:
            dx = math.copysign(0.45, cx_ - x)
            dy = math.copysign(0.45, cy_ - y)
            g.add_geo(G.pinnacle_free(6.5 + 0.02 * shaft, 1.3), pos=(cx_ + dx, cy_ + dy, zt - 0.5), scale=1.0)
    # windows on faces
    face_defs = {'S': ((x, y - hy), (0.0, -1.0), sx), 'N': ((x, y + hy), (0.0, 1.0), sx),
                 'E': ((x + hx, y), (1.0, 0.0), sy), 'W': ((x - hx, y), (-1.0, 0.0), sy)}
    for fc in faces:
        (cx_, cy_), (ox, oy), width = face_defs[fc]
        tx, ty = -oy, ox   # tangent (right-hand when seen from outside is (oy,-ox) ... use symmetric)
        for tr in tiers:
            z_off, n, proto = tr[0], tr[1], tr[2]
            skip_p = tr[3] if len(tr) > 3 else 0.0
            for k in range(n):
                if rng.random() < skip_p:
                    continue
                off = ((k + 0.5) / n - 0.5) * (width - 3.0)
                pos = (cx_ + tx * off + ox * 0.0, cy_ + ty * off, z0 + z_off)
                g.add_geo(proto, pos=pos, outward=(ox, oy), lit=pick_lit(rng, lit_p), rng=rng)
    if clock is not None:
        for fc in clock.get('faces', ('S',)):
            (cx_, cy_), (ox, oy), width = face_defs[fc]
            g.add_geo(G.clock_face(clock['r']), pos=(cx_, cy_, z0 + clock['z']), outward=(ox, oy))
    top = top_z
    if spire is not None:
        spire_square(g, x, y, top_z - 0.2, hx + 0.9, spire['H'], rng, sides=spire.get('sides', 4),
                     lucarnes=spire.get('lucarnes', ((0.30, 1.0),)), fin=spire.get('fin', 6.0),
                     lit_p=lit_p, mat=spire.get('mat', SLATE), p=spire.get('p', 1.12))
        top = top_z + spire['H'] + spire.get('fin', 6.0)
    elif hip is not None:
        A.gable_roof(g, x, y, sx + 1.0, sy + 1.0, top_z, hip.get('pitch', 55), axis='x', overhang=0.6, m_roof=SLATE,
                     m_gable=wall_mat)
    return dict(top=top)
