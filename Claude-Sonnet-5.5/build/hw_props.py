"""Props: covered timber bridge + trestles, owlery, gamekeeper's hut, smoke, standing stones."""
import numpy as np
import math
from hw_geo import (Geo, boxes, beams, lathe, loft, sweep, pyramid, poly_cap, rotz, pointed_arch, offset_outline,
                    frame_ring, wall_fill, triangulate_polygon, slab)
import hw_gothic as G
import hw_towers as TW
import hw_walls as W
import hw_arch as A
import hw_trees as TR

TIMBER = 'M_Timber'
STONE = 'M_Stone'
DRESS = 'M_StoneDress'
SLATE = 'M_Slate'


class Frame3:
    """Bridge frame: origin A, along-axis (with slope), lateral (horizontal) and up (perpendicular)."""

    def __init__(self, A_, B_):
        self.A = np.asarray(A_, float)
        d = np.asarray(B_, float) - self.A
        self.L = float(np.linalg.norm(d))
        self.et = d / self.L
        h = np.array([d[0], d[1], 0.0])
        h /= np.linalg.norm(h)
        self.es = np.array([-h[1], h[0], 0.0])           # left of travel
        self.eh = np.cross(self.et, self.es)              # up-ish
        if self.eh[2] < 0:
            self.eh = -self.eh
        self.yaw = math.atan2(h[1], h[0])

    def p(self, t, s, h):
        return self.A + self.et * t + self.es * s + self.eh * h


def covered_bridge(g, A_, B_, smp, rng, width=4.2, bent_t=(0.30, 0.62), post_every=2.3):
    F = Frame3(A_, B_)
    L = F.L
    hw = width / 2.0
    wall_h = 4.3
    # ---------- deck
    n_pl = int(L / 0.25)
    # deck as a solid slab (top planks via uv pattern in material) + underside stringers
    P = np.array([[F.p(0, -hw, 0), F.p(L, -hw, 0), F.p(L, hw, 0), F.p(0, hw, 0)]])
    g.add(P, TIMBER)
    for s in (-hw + 0.3, 0.0, hw - 0.3):
        beams(g, [F.p(0, s, -0.5)], [F.p(L, s, -0.5)], 0.45, 0.85, m=TIMBER, up=tuple(F.eh))
    ts = np.arange(0.0, L + 0.1, 2.3)
    for t in ts:
        beams(g, [F.p(t, -hw - 0.25, -0.2)], [F.p(t, hw + 0.25, -0.2)], 0.35, 0.45, m=TIMBER, up=tuple(F.eh))
    # ---------- side trusses and cladding
    npost = int(L / post_every) + 1
    tp = np.linspace(0.0, L, npost)
    for sd in (-1, 1):
        s = sd * (hw + 0.1)
        # bottom / top chords
        beams(g, [F.p(0, s, 0.1)], [F.p(L, s, 0.1)], 0.30, 0.36, m=TIMBER, up=tuple(F.eh))
        beams(g, [F.p(0, s, wall_h)], [F.p(L, s, wall_h)], 0.30, 0.36, m=TIMBER, up=tuple(F.eh))
        beams(g, [F.p(0, s, 1.35)], [F.p(L, s, 1.35)], 0.22, 0.24, m=TIMBER, up=tuple(F.eh))
        beams(g, [F.p(0, s, 3.4)], [F.p(L, s, 3.4)], 0.2, 0.22, m=TIMBER, up=tuple(F.eh))
        for k, t in enumerate(tp):
            beams(g, [F.p(t, s, 0.1)], [F.p(t, s, wall_h)], 0.34, 0.34, m=TIMBER, up=tuple(F.eh))
            if k < npost - 1:
                t2 = tp[k + 1]
                if k % 2 == 0:
                    beams(g, [F.p(t, s, 0.1)], [F.p(t2, s, wall_h)], 0.2, 0.22, m=TIMBER, up=tuple(F.eh))
                else:
                    beams(g, [F.p(t2, s, 0.1)], [F.p(t, s, wall_h)], 0.2, 0.22, m=TIMBER, up=tuple(F.eh))
        # lower solid siding (vertical boards)
        Pq = np.array([[F.p(0, s, 0.1), F.p(L, s, 0.1), F.p(L, s, 1.35), F.p(0, s, 1.35)]])
        if sd > 0:
            Pq = Pq[:, ::-1]
        g.add(Pq, TIMBER)
        # upper cladding strip under the roof
        Pq = np.array([[F.p(0, s, 3.4), F.p(L, s, 3.4), F.p(L, s, wall_h), F.p(0, s, wall_h)]])
        if sd > 0:
            Pq = Pq[:, ::-1]
        g.add(Pq, TIMBER)
    # cross ties at the top
    for t in tp[::2]:
        beams(g, [F.p(t, -hw - 0.1, wall_h)], [F.p(t, hw + 0.1, wall_h)], 0.3, 0.3, m=TIMBER, up=tuple(F.eh))
    # ---------- roof (gable, slate): two closed slabs (top, underside, eave fascia, end caps) meeting at the ridge
    ov = 0.95
    pitch = math.radians(38.0)
    rise = (hw + ov) * math.tan(pitch)
    up_ = tuple(F.eh)
    ridge0, ridge1 = F.p(-1.0, 0.0, wall_h + rise), F.p(L + 1.0, 0.0, wall_h + rise)
    for sd in (-1, 1):
        e0, e1 = F.p(-1.0, sd * (hw + ov), wall_h - 0.05), F.p(L + 1.0, sd * (hw + ov), wall_h - 0.05)
        hint = tuple(sd * 0.6 * F.es + 0.8 * F.eh)
        slab(g, np.stack([e0, e1, ridge1, ridge0]), 0.32, SLATE, hint=hint, vertical=(2, 3), vdir=up_, m_under=TIMBER)
    # ridge cap
    beams(g, [F.p(-1.0, 0, wall_h + rise + 0.05)], [F.p(L + 1.0, 0, wall_h + rise + 0.05)], 0.32, 0.26, m=TIMBER, up=tuple(F.eh))
    # rafters visible at the eaves
    for t in np.arange(0.0, L + 0.1, 1.15):
        for sd in (-1, 1):
            beams(g, [F.p(t, sd * (hw + 0.1), wall_h - 0.1)], [F.p(t, sd * (hw + ov), wall_h - 0.05 - ov * math.tan(pitch) * 0.0 - 0.15)], 0.16, 0.2, m=TIMBER, up=tuple(F.eh))
    # ---------- lanterns inside (registered lamps) + glowing floor spill
    post = W.lantern_wall()
    for t in np.arange(3.0, L - 2.0, 6.5):
        W.reg('bridge', *(F.p(t, 0.0, wall_h - 0.9)))
    # ---------- trestle bents
    for tb in bent_t:
        t = tb * L
        top = F.p(t, 0, -0.9)
        for sd in (-1, 1):
            s = sd * (hw - 0.2)
            base_xy = F.p(t, s * 1.55, 0)[:2]
            zf = float(smp.z(base_xy[0], base_xy[1]))
            zf = min(zf, top[2] - 6.0)
            pt_top = F.p(t, s, -0.9)
            pt_bot = np.array([base_xy[0], base_xy[1], zf])
            beams(g, [pt_bot + np.array([0, 0, 0.9])], [pt_top], 0.75, 0.75, m=TIMBER)
            boxes(g, [(base_xy[0], base_xy[1], zf - 2.5)], [(2.6, 2.6, 3.4)], yaw=F.yaw, m=STONE)
        # cross bracing (X) at levels
        zt_ = top[2]
        zb_ = min(float(smp.z(*F.p(t, 0, 0)[:2])), zt_ - 8.0)
        n_lv = max(2, int((zt_ - zb_) / 7.0))
        zs = np.linspace(zb_ + 2.0, zt_ - 1.0, n_lv + 1)
        for a, b in zip(zs[:-1], zs[1:]):
            for sgn in (1, -1):
                pa = np.array([*F.p(t, -sgn * (hw + 0.6), 0)[:2], a])
                pb = np.array([*F.p(t, sgn * (hw + 0.6), 0)[:2], b])
                beams(g, [pa], [pb], 0.36, 0.36, m=TIMBER)
            beams(g, [np.array([*F.p(t, -(hw + 0.6), 0)[:2], b])], [np.array([*F.p(t, (hw + 0.6), 0)[:2], b])], 0.5, 0.5, m=TIMBER)
        # legs in the along-direction (bracing between the two bents is left open)
    return F


def owlery(g, x, y, z0, R, shaft, rng, found=10.0):
    info = TW.round_tower(g, x, y, z0, R, shaft, 0.1, rng, bands=(8.0, 17.0), top='plain', segs=28, fin=0.0,
                          tiers=[(3.0, 5, G.window_slit(0.3, 2.0)), (11.0, 5, G.window_lancet(0.8, 2.6, 1)), (20.0, 4, G.window_slit(0.3, 2.0))],
                          lit_p=0.5, found=found, flare=1.6)
    # open belfry drum: piers between 8 big arches
    zb = z0 + shaft + 0.8
    Hh = 6.4
    n = 8
    for k in range(n):
        a = 2 * math.pi * (k + 0.5) / n
        boxes(g, [(x + (R - 0.3) * math.cos(a), y + (R - 0.3) * math.sin(a), zb)], [(1.5, 1.7, Hh)], yaw=a, m=STONE)
        pos = (x + (R - 0.3) * math.cos(a + math.pi / n), y + (R - 0.3) * math.sin(a + math.pi / n), zb)
    for k in range(n):
        a = 2 * math.pi * k / n
        g.add_geo(G.window_lancet(3.0, Hh - 0.4, 1, molding=False, sill=False, rise_k=1.0),
                  pos=(x + (R - 0.6) * math.cos(a), y + (R - 0.6) * math.sin(a), zb + 0.2),
                  outward=(math.cos(a), math.sin(a)), lit=(0.28 + 0.2 * rng.random(), 0.03), rng=rng)
    # interior: dark floor disc + floor slab
    lathe(g, [(R + 0.6, zb - 0.6), (R + 0.6, zb), (0.0, zb)], (x, y, 0), segs=n * 2, m=DRESS)
    # cornice + conical roof
    lathe(g, [(R + 1.2, zb + Hh), (R + 1.6, zb + Hh + 0.9)], (x, y, 0), segs=n * 2, m=DRESS) if False else None
    rc = R + 1.5
    prof = [(R - 0.5, zb + Hh - 0.2), (rc, zb + Hh - 0.2), (rc + 0.3, zb + Hh + 0.5)]
    lathe(g, prof, (x, y, 0), segs=n * 4, m=DRESS)
    cone = TW.cone_profile(rc + 0.3, 17.0, 16, 1.22, 0.2)
    cone[:, 1] += zb + Hh + 0.5
    lathe(g, cone, (x, y, 0), segs=n * 4, m=SLATE, uv_v='slant')
    g.add_geo(G.finial(4.5, 0.4, 'M_Copper'), pos=(x, y, zb + Hh + 0.5 + 17.0 - 0.4))
    # perches: beams sticking out below the arches with a few owls
    for k in range(n):
        a = 2 * math.pi * k / n
        px, py = x + (R + 0.3) * math.cos(a), y + (R + 0.3) * math.sin(a)
        p0 = np.array([px, py, zb - 0.4])
        p1 = np.array([px + 2.6 * math.cos(a), py + 2.6 * math.sin(a), zb - 0.5])
        beams(g, [p0], [p1], 0.16, 0.16, m=TIMBER)
        if rng.random() < 0.55:
            owl(g, p1[0] - 0.4 * math.cos(a), p1[1] - 0.4 * math.sin(a), p1[2] + 0.1, a + math.pi, rng)
    return dict(top=zb + Hh + 0.5 + 17.0 + 4.5)


def owl(g, x, y, z, yaw, rng, s=1.0):
    body = [(0.05, 0.0), (0.22 * s, 0.10 * s), (0.28 * s, 0.32 * s), (0.20 * s, 0.55 * s), (0.0, 0.62 * s)]
    lathe(g, body, (x, y, z), segs=8, m='M_Feather')
    head = [(0.02, 0.58 * s), (0.20 * s, 0.63 * s), (0.20 * s, 0.78 * s), (0.0, 0.84 * s)]
    lathe(g, head, (x, y, z), segs=8, m='M_Feather')
    for sd in (-1, 1):
        ex = x + 0.10 * s * math.cos(yaw) * 1.0 + sd * 0.09 * s * math.cos(yaw + math.pi / 2) + 0.14 * s * math.cos(yaw)
        ey = y + 0.10 * s * math.sin(yaw) * 1.0 + sd * 0.09 * s * math.sin(yaw + math.pi / 2) + 0.14 * s * math.sin(yaw)
        boxes(g, [(ex, ey, z + 0.68 * s)], [(0.05 * s, 0.05 * s, 0.05 * s)], yaw=yaw, m='M_OwlEye')


def hut(g, x, y, z, yaw, rng, smp):
    """Gamekeeper's hut: rubble walls, thatch roof, chimney, door, lit window, woodpile, fence."""
    c, s = math.cos(yaw), math.sin(yaw)
    def loc(u, v, h=0.0):
        return (x + u * c - v * s, y + u * s + v * c, z + h)
    L_, D_ = 7.0, 5.2
    hw_ = 2.7
    boxes(g, [loc(0, 0, -1.5)], [(L_, D_, hw_ + 1.5)], yaw=yaw, m=STONE, faces=(0, 1, 2, 3, 4))
    # thatch roof: gable, ridge along local u
    G_ = Geo('hutroof', ['M_Thatch', STONE])
    A.gable_roof(G_, 0.0, 0.0, L_, D_, hw_, 52.0, axis='x', overhang=0.55, m_roof='M_Thatch', m_gable=STONE, thick=0.55)
    g.add_geo(G_, pos=(x, y, z), yaw=yaw)
    # chimney at the +u gable
    boxes(g, [loc(L_ / 2 - 0.5, 0.0, 0.0)], [(1.5, 1.7, hw_ + 6.4)], yaw=yaw, m=STONE)
    boxes(g, [loc(L_ / 2 - 0.5, 0.0, hw_ + 6.4)], [(1.9, 2.1, 0.35)], yaw=yaw, m=DRESS)
    top = loc(L_ / 2 - 0.5, 0.0, hw_ + 6.75)
    # door + window on the front (local -v)
    door = Geo('door', [TIMBER, DRESS, 'M_Dark'])
    O = pointed_arch(1.15, 1.25, 0.6, n=5)
    frame_ring(door, offset_outline(O, 0.14), O, -0.2, 0.3, DRESS, y_inner_back=-0.05)
    wall_fill(door, O, -0.05, TIMBER)
    g.add_geo(door, pos=loc(-1.2, -D_ / 2), yaw=yaw, outward=None) if False else None
    g.add_geo(door, pos=loc(-1.2, -D_ / 2), yaw=yaw)
    g.add_geo(G.window_rect(1.0, 0.9, 2, 2, molding=False), pos=loc(1.4, -D_ / 2, 1.0), yaw=yaw, lit=(0.9, 0.08), rng=rng)
    g.add_geo(G.window_rect(0.8, 0.8, 2, 2, molding=False), pos=loc(L_ / 2, 0.0, 1.0), yaw=yaw + math.pi / 2, lit=(0.55, 0.05), rng=rng)
    # woodpile
    for row in range(3):
        for k in range(5 - row):
            px, py, pz = loc(-2.2 + k * 0.42 + row * 0.21, D_ / 2 + 1.0, 0.25 + row * 0.38)
            beams(g, [(px, py, pz)], [(px + 1.8 * (-s), py + 1.8 * c, pz)], 0.34, 0.34, m=TIMBER)
    # fence
    for k in range(9):
        u0 = -5.0 + k * 1.4
        px, py, pz = loc(u0, -D_ / 2 - 3.5)
        pz = float(smp.z(px, py))
        boxes(g, [(px, py, pz - 0.2)], [(0.14, 0.14, 1.35)], yaw=yaw, m=TIMBER)
        if k < 8:
            qx, qy, qz = loc(u0 + 1.4, -D_ / 2 - 3.5)
            qz = float(smp.z(qx, qy))
            for hh in (0.55, 1.0):
                beams(g, [(px, py, pz + hh)], [(qx, qy, qz + hh)], 0.09, 0.08, m=TIMBER)
    W.reg('court', *loc(-1.2, -D_ / 2 - 0.8, 2.2))
    return top


def smoke_material(name='M_Smoke', x0=0.0, y0=0.0, z0=0.0, wind=(1.0, 0.35)):
    from hw_nodes import NB, get_mat
    nb = NB(get_mat(name))
    P = nb.geometry().outputs['Position']
    sp_ = nb.sepxyz(P)
    px, py, pz = sp_.outputs[0], sp_.outputs[1], sp_.outputs[2]
    h = nb.math('MAXIMUM', nb.sub(pz, z0), 0.0)
    hp = nb.math('POWER', nb.add(h, 0.5), 1.35)
    ax = nb.add(x0, nb.mul(hp, wind[0] * 0.55))
    ay = nb.add(y0, nb.mul(hp, wind[1] * 0.55))
    dx = nb.sub(px, ax)
    dy = nb.sub(py, ay)
    r = nb.math('SQRT', nb.add(nb.mul(dx, dx), nb.mul(dy, dy)))
    rad = nb.add(0.45, nb.mul(h, 0.16))
    rad_n = nb.math('DIVIDE', r, rad)
    prof = nb.smooth(nb.sub(1.0, rad_n), 0.0, 0.85)
    n1 = nb.noise(nb.combxyz(nb.mul(px, 0.42), nb.mul(py, 0.42), nb.mul(pz, 0.28)), scale=1.0, detail=5, rough=0.6)
    fade = nb.mul(nb.smooth(h, 0.0, 1.5), nb.smooth(nb.sub(1.0, nb.math('DIVIDE', h, 34.0)), 0.0, 0.7))
    dens = nb.mul(nb.mul(prof, nb.smooth(n1, 0.28, 0.75)), nb.mul(fade, 0.55))
    vs = nb.node('ShaderNodeVolumeScatter')
    vs.inputs['Color'].default_value = (0.72, 0.78, 0.86, 1.0)
    vs.inputs['Anisotropy'].default_value = 0.35
    nb._in(vs, 'Density', dens)
    nb.output(volume=vs.outputs[0])
    return nb.mat


def standing_stones(g, cx, cy, smp, rng, R=12.5, n=11):
    protos = [TR.standing_stone(rng, h=rng.uniform(2.6, 4.3), w=rng.uniform(1.0, 1.7), name='ss%d' % i, seed=i * 3 + 1) for i in range(5)]
    for k in range(n):
        a = 2 * math.pi * k / n + rng.normal(0, 0.05)
        px, py = cx + R * math.cos(a), cy + R * math.sin(a)
        pz = float(smp.z(px, py))
        g.add_geo(protos[k % 5], pos=(px, py, pz - 0.5), yaw=a + rng.normal(0, 0.3), scale=1.0)
    # altar stone + a fallen one
    g.add_geo(TR.boulder(rng, 2.6, 'altar', flat=0.55, seed=91), pos=(cx, cy, float(smp.z(cx, cy)) - 0.4))
    g.add_geo(TR.standing_stone(rng, h=2.0, w=1.3, name='fallen', seed=77), pos=(cx + R * 1.35, cy - 3, float(smp.z(cx + R * 1.35, cy - 3)) - 0.2), yaw=1.0)


def flying_owl(rng, phase=0.3, span=1.05):
    """Owl in flight, heading +x, origin at the body centre."""
    g = Geo('owl_fly', ['M_Feather'])
    # body: loft along x
    n = 9
    ts = np.linspace(0, 1, n)
    rings = []
    for t in ts:
        r = 0.115 * (math.sin(math.pi * min(max(t, 0.02), 0.98)) ** 0.55) + 0.01
        x = (t - 0.45) * 0.44
        ang = np.linspace(0, 2 * math.pi, 8, endpoint=False)
        rings.append(np.column_stack([np.full(8, x), r * np.cos(ang), r * 0.9 * np.sin(ang)]))
    R = np.stack(rings)
    # ring order (x rising) with CCW cross-section seen from +x : ang increases y->z ; check orientation by flipping if needed
    loft(g, R[::-1], closed=True, m='M_Feather', smooth=True)
    # head bump
    lathe(g, [(0.02, 0.0), (0.10, 0.06), (0.11, 0.14), (0.06, 0.2), (0.0, 0.22)], (0.20, 0.0, -0.11), segs=8, m='M_Feather')
    # wings: 3 spanwise sections with a flap dihedral
    for sd in (-1, 1):
        pts_l = []
        pts_t = []
        yy = 0.0
        zz = 0.0
        for k in range(5):
            s = k / 4.0
            dih = math.sin(phase + s * 0.9) * 0.9 + 0.15
            yy += sd * (span / 2 / 4) * math.cos(dih)
            zz += (span / 2 / 4) * math.sin(dih)
            chord = 0.30 * (1.0 - 0.55 * s * s) + 0.04
            pts_l.append([0.06 - 0.02 * s, yy, zz])
            pts_t.append([0.06 - 0.02 * s - chord, yy, zz - 0.02 * s])
        pl, pt = np.array(pts_l), np.array(pts_t)
        for k in range(4):
            q = np.array([pt[k], pt[k + 1], pl[k + 1], pl[k]])
            slab(g, q, 0.012, 'M_Feather', hint=(0.0, 0.0, 1.0))
    # tail
    tail = np.array([[-0.22, -0.05, 0.0], [-0.22, 0.05, 0.0], [-0.42, 0.075, 0.0], [-0.42, -0.075, 0.0]])
    slab(g, tail, 0.012, 'M_Feather', hint=(0.0, 0.0, 1.0))
    return g
