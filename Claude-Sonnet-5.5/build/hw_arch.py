"""Architecture primitives built on hw_geo (roofs, tower shells, spires)."""
import numpy as np
import math
from hw_geo import (Geo, boxes, lathe, loft, sweep, prism, pyramid, ngon, rect_poly, poly_cap, beams, xf, rotz,
                    pointed_arch, round_arch, circle_outline, offset_outline, wall_strip, wall_fill, reveal,
                    outer_side, frame_ring)


def gable_roof(g, cx, cy, L, D, z_eave, pitch_deg, axis='x', overhang=1.2, m_roof='M_Slate', m_gable='M_Stone',
               thick=0.45, gables=True, ridge_extra=0.0):
    """Gable roof.  L along the ridge axis, D across.  Returns ridge height above z_eave."""
    tanp = math.tan(math.radians(pitch_deg))
    half = D / 2.0
    rise = half * tanp + ridge_extra
    ov = overhang
    a0, a1 = -(L / 2.0 + ov), (L / 2.0 + ov)
    zr = z_eave + rise
    ze_o = z_eave - ov * tanp
    # local frame: ridge along local x, across = local y  (south slope at -y)
    ys = -(half + ov)
    yn = half + ov
    top_s = np.array([[a0, ys, ze_o], [a1, ys, ze_o], [a1, 0, zr], [a0, 0, zr]])
    top_n = np.array([[a1, yn, ze_o], [a0, yn, ze_o], [a0, 0, zr], [a1, 0, zr]])
    # underside (thickness): the eave edge is the top edge shifted along -normal; at the ridge both undersides
    # meet on the centre plane, `thick / cos(pitch)` below the ridge (trimmed, so nothing pokes through the top)
    cp_ = math.cos(math.radians(pitch_deg))
    ns = np.array([0, -math.sin(math.radians(pitch_deg)), cp_])
    nn = np.array([0, math.sin(math.radians(pitch_deg)), cp_])
    zr_u = zr - thick / cp_

    def under(quad, n):
        e0, e1 = quad[0] - n * thick, quad[1] - n * thick
        r1 = np.array([quad[2][0], 0.0, zr_u])
        r0 = np.array([quad[3][0], 0.0, zr_u])
        return np.array([r0, r1, e1, e0])

    faces = [top_s, top_n, under(top_s, ns), under(top_n, nn)]
    # eave fascia (south / north) and verge boards
    for quad, n, sgn in ((top_s, ns, -1), (top_n, nn, 1)):
        p0, p1 = quad[0], quad[1]
        f = np.array([p1, p0, p0 - n * thick, p1 - n * thick])
        faces.append(f)
    # verge boards at both ends
    for x_end, sgn in ((a0, -1), (a1, 1)):
        for quad, n in ((top_s, ns), (top_n, nn)):
            pts = [q for q in quad if abs(q[0] - x_end) < 1e-6]
            if len(pts) == 2:
                q0, q1 = pts
                lo, hi = (q0, q1) if q0[2] < q1[2] else (q1, q0)
                f = np.array([lo, hi, np.array([x_end, 0.0, zr_u]), lo - n * thick])
                # orient outward (normal along sgn * x)
                nrm = np.cross(f[1] - f[0], f[3] - f[0])
                if nrm[0] * sgn < 0:
                    f = f[::-1]
                faces.append(f)
    P = np.stack(faces)
    if axis == 'y':
        P = rotz(P, math.pi / 2.0)
    g.add(xf(P, (cx, cy, 0)), m_roof)
    if gables:
        gh = half
        for x_end, sgn in ((-L / 2.0, -1), (L / 2.0, 1)):
            tri = np.array([[x_end, -gh, z_eave], [x_end, gh, z_eave], [x_end, 0, zr]])
            if sgn < 0:
                tri = tri[[1, 0, 2]]
            T = tri[None]
            if axis == 'y':
                T = rotz(T, math.pi / 2.0)
            g.add(xf(T, (cx, cy, 0)), m_gable)
    return rise


def concave_cone_profile(R, H, n=14, p=1.18, r_top=0.0):
    """Radius profile of a slightly concave spire, bottom -> top (r, z)."""
    t = np.linspace(0.0, 1.0, n)
    r = r_top + (R - r_top) * (1.0 - t) ** p
    return np.column_stack([r, H * t])


def round_tower_blockout(g, x, y, z0, R, shaft, cone, fin=4.0, gallery=0.0, m_wall='M_Stone', m_roof='M_Slate',
                         found=26.0, segs=40):
    prof = [(R + 1.6, -found), (R + 1.6, -1.5), (R + 0.4, 0.5), (R, 2.0), (R, shaft)]
    if gallery > 0:
        prof += [(R + 1.5, shaft), (R + 1.5, shaft + gallery)]
        rc = R + 1.6
        zc = shaft + gallery
    else:
        prof += [(R + 0.7, shaft), (R + 0.7, shaft + 0.8)]
        rc = R + 0.9
        zc = shaft + 0.8
    lathe(g, prof, (x, y, z0), segs=segs, m=m_wall)
    cp = concave_cone_profile(rc, cone, 16, 1.18, 0.25)
    cp[:, 1] += zc
    lathe(g, cp, (x, y, z0), segs=segs, m=m_roof, uv_v='slant')
    # finial
    fp = [(0.35, 0.0), (0.22, fin * 0.7), (0.5, fin * 0.72), (0.3, fin * 0.86), (0.0, fin)]
    fp = np.array(fp)
    fp[:, 1] += zc + cone - 0.2
    lathe(g, fp, (x, y, z0), segs=10, m='M_Copper')


def square_tower_blockout(g, x, y, z0, s, shaft, spire, fin=5.0, m_wall='M_Stone', m_roof='M_Slate', found=26.0,
                          yaw=0.0):
    boxes(g, [(x, y, z0 - found)], [(s, s, shaft + found)], yaw=yaw, m=m_wall, faces=(0, 1, 2, 3, 4))
    # cornice
    boxes(g, [(x, y, z0 + shaft)], [(s + 1.6, s + 1.6, 1.0)], yaw=yaw, m=m_wall)
    base = ngon(x, y, (s + 1.6) / math.sqrt(2.0), 4, math.pi / 4 + yaw)
    base3 = np.column_stack([base, np.full(4, z0 + shaft + 1.0)])
    pyramid(g, base3, (x, y, z0 + shaft + 1.0 + spire), m_roof)
    fp = np.array([(0.35, 0.0), (0.22, fin * 0.7), (0.5, fin * 0.72), (0.3, fin * 0.86), (0.0, fin)])
    fp[:, 1] += z0 + shaft + 1.0 + spire - 0.2
    lathe(g, fp, (x, y, 0), segs=10, m='M_Copper')


def hall_blockout(g, cx, cy, L, D, z0, eaves, pitch, axis='x', found=26.0, m_wall='M_Stone', m_roof='M_Slate'):
    sx, sy = (L, D) if axis == 'x' else (D, L)
    boxes(g, [(cx, cy, z0 - found)], [(sx, sy, eaves + found)], m=m_wall, faces=(0, 1, 2, 3, 4))
    rise = gable_roof(g, cx, cy, L, D, z0 + eaves, pitch, axis=axis, overhang=1.4, m_roof=m_roof, m_gable=m_wall)
    return rise
