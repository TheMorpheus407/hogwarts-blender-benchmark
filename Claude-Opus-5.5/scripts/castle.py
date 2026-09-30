"""Hogwarts castle layout. Plateau (Crag_Main top) at z=55.
x = east, y = north; the lake and the hero camera lie to the south."""
import bpy, math, random
from mathutils import Vector, Matrix
import geo, arch, terrain, crag
from geo import MB, mat_loc, TAU
from arch import (ST, TR, SL, CU, GL, MT, WD, window, window_glow, hall_block, round_tower, square_tower,
                  gable_roof, cone_roof, pyramid_roof, crenellate, machicolated_parapet, string_course,
                  buttress, pinnacle, finial_spike, circle, offset_poly, edge_frame, poly_edges, rz_for,
                  windows_on_edge, flying_buttress, door)

TOP = 55.0
DZ = crag.DZ
LANTERNS = []      # (x, y, z, power)
GLOW_LIGHTS = []   # interior fill lights (x, y, z, power, colour)


def lantern(mb, x, y, z, post=True, bracket_dir=None, power=25.0, hang=False):
    """iron lantern on a post (or wall bracket); records a light position."""
    if post:
        # turned cast-iron post: plinth, fluted shaft, collar and a scrolled bracket head
        mb.lathe([(0.17, z), (0.17, z + 0.12), (0.12, z + 0.2), (0.1, z + 0.45), (0.13, z + 0.55), (0.065, z + 0.7),
                  (0.05, z + 2.0), (0.085, z + 2.08), (0.05, z + 2.16), (0.13, z + 2.26), (0.13, z + 2.3)], 10, MT,
                 mat_loc((x, y, 0)))
        lz = z + 2.3
    else:
        lz = z
    s = 0.2
    mb.box(x - s - 0.03, y - s - 0.03, lz, x + s + 0.03, y + s + 0.03, lz + 0.06, MT)
    mb.box(x - s, y - s, lz + 0.06, x + s, y + s, lz + 0.52, 'Lantern')
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(x + sx * s - 0.025, y + sy * s - 0.025, lz + 0.06, x + sx * s + 0.025, y + sy * s + 0.025, lz + 0.55, MT)
    mb.lathe([(s + 0.08, lz + 0.52), (s + 0.08, lz + 0.58), (0.04, lz + 0.85), (0.0, lz + 0.95)], 4, MT,
             mat_loc((x, y, 0), math.pi / 4))
    LANTERNS.append((x, y, lz + 0.3 + mb.zoff, power))


def plinth(mb, poly, z0, z1, out=1.2):
    """battered masonry base under an edge building, foot buried in the rock."""
    top = offset_poly(poly, 0.35)
    bot = offset_poly(poly, out)
    mb.loft([[(x, y, z0) for x, y in bot], [(x, y, z1 - 0.8) for x, y in top], [(x, y, z1) for x, y in top]], ST)
    string_course(mb, poly, z1 - 0.1, out=0.5, hgt=0.45)


def rect(cx, cy, L, W, rz=0.0):
    M = mat_loc((cx, cy, 0), rz)
    return [tuple((M @ Vector((px, py, 0)))[:2]) for px, py in
            [(-L / 2, -W / 2), (L / 2, -W / 2), (L / 2, W / 2), (-L / 2, W / 2)]]


# ================================================================== GREAT HALL
def great_hall(mb):
    arch.RNG.seed(11)
    cx, cy, L, W = -95.0, -50.0, 60.0, 20.0
    z0, z1 = 58.0, 76.0
    poly = rect(cx, cy, L, W)
    mb.rnd = 0.62
    plinth(mb, poly, 36.0, z0)
    mb.prism(poly, z0 - 0.5, z1, ST)
    # undercroft windows in the plinth
    for p0, p1 in list(poly_edges(poly))[0:1]:
        windows_on_edge(mb, p0, p1, 49.0, 1.0, 1.8, 5.0, 'round', lit=0.45, level=0.6, margin=2.5,
                        depth=0.8)
    # the tall lancet windows in bays with stepped buttresses
    bays = 11
    for ei, (p0, p1) in enumerate(poly_edges(poly)):
        if ei % 2 == 0:  # long sides
            Le = math.dist(p0, p1)
            for k in range(bays):
                t = (k + 0.5) / bays
                M, _ = edge_frame(p0, p1, t, 61.0)
                window(mb, M, 2.3, 11.5, 'pointed', depth=0.55, frame=0.3, glow=window_glow(0.97, 1.15),
                       mullion=2, sharp=1.25)
            for k in range(bays + 1):
                t = k / bays
                Mb, _ = edge_frame(p0, p1, t, 0)
                buttress(mb, Mb, 40.0, z1 + 0.2, 1.4, 2.6, 4, pin=True)
    # west end: great traceried window; east end joins the link block
    p0, p1 = poly[3], poly[0]
    M, _ = edge_frame(p0, p1, 0.5, 62.0)
    window(mb, M, 6.0, 13.5, 'pointed', depth=0.7, frame=0.5, glow=window_glow(1.0, 1.4), mullion=4, sharp=1.1)
    for t in (0.18, 0.82):
        M, _ = edge_frame(p0, p1, t, 63.0)
        window(mb, M, 1.4, 8.0, 'pointed', depth=0.4, frame=0.25, glow=window_glow(0.8, 1.0))
    string_course(mb, poly, 60.2, out=0.25, hgt=0.4)
    string_course(mb, poly, z1 - 0.3, out=0.35, hgt=0.45)
    machicolated_parapet(mb, poly, z1, over=0.5) if False else crenellate(mb, offset_poly(poly, 0.3), z1 + 0.15,
                                                                         True, thick=0.5, low=0.9, merlon=0.75)
    # steep slate roof with pointed dormers
    gable_roof(mb, cx, cy, L, W, z1 + 0.3, 16.5, 0.0, over=0.2, dormers=7, dormer_lit=0.4)
    # the four corner turrets
    for i, (px, py) in enumerate(poly):
        ox = 1.6 if px > cx else -1.6
        oy = 1.6 if py > cy else -1.6
        h = [89.0, 87.5, 90.0, 88.5][i]
        round_tower(mb, px + ox * 0.5, py + oy * 0.5, 2.4, 44.0, h, n=16, roof='cone', roof_h=11.0 + i,
                    crown='eave', win_levels=[66.0, 74.0, h - 5.0], lit=0.35, win_w=0.6, win_h=1.8, bands=True,
                    flare=0.45, bell=0.16)
    # ridge fleche (small spire at the middle of the roof)
    fx, fy = cx + 6, cy
    rz_ = z1 + 0.3 + 16.5
    mb.lathe([(1.4, rz_ - 2.5), (1.4, rz_ + 3.0)], 8, ST, mat_loc((fx, fy, 0)))
    for k in range(8):
        a = TAU * (k + 0.5) / 8
        M = mat_loc((fx + 1.35 * math.cos(a), fy + 1.35 * math.sin(a), rz_ - 0.3), rz_for(a))
        window(mb, M, 0.5, 2.4, 'pointed', depth=0.1, frame=0.08, glow=0.0, mullion=0, sill=False, hood=False)
    cone_roof(mb, fx, fy, rz_ + 3.0, 1.4, 9.0, 8, SL, flare=0.4, bell=0.0)
    return poly


# ================================================================== BIG CONE TOWER
def cone_tower(mb):
    arch.RNG.seed(21)
    x, y, r = -46.0, -48.0, 12.5
    mb.rnd = 0.4
    plinth(mb, circle(x, y, r, 36, math.pi / 36), 30.0, 52.0, out=1.8)
    top = round_tower(mb, x, y, r, 51.5, 110.0, n=36, roof='cone', roof_h=50.0, crown='mach', lit=0.55,
                      level=1.0, win_w=1.2, win_h=3.0, win_every=2, bell=0.06,
                      win_levels=[56, 63, 70, 77, 84, 91, 98])
    # cone dormers (lucarnes) in two rings
    for ring, (t, cnt) in enumerate(((0.16, 11), (0.4, 8))):
        z = 110.3 + 50.0 * t
        rr = (r + 0.45 + 0.35 * 0.3) * (1 - t) + 0.2
        for k in range(cnt):
            a = TAU * (k + 0.5 * ring) / cnt + 0.2
            M = mat_loc((x + rr * math.cos(a), y + rr * math.sin(a), z), rz_for(a))
            arch.dormer(mb, M, 1.2, 1.9, 0.45)
    # attached stair turret
    round_tower(mb, x + 9.0, y - 9.5, 3.2, 38.0, 118.0, n=16, roof='cone', roof_h=14.0, crown='mach',
                lit=0.4, win_w=0.5, win_h=1.4, win_every=3, bell=0.12)
    return top


# ================================================================== GALLERY WING
def gallery(mb):
    arch.RNG.seed(31)
    mb.rnd = 0.55
    # link between hall and cone tower
    hall_block(mb, -61.0, -45.0, 8.0, 16.0, 55.0, 80.0, roof_h=7.0, lit=0.5, win_w=1.0, win_h=2.4, bay=4.0)
    # long arcaded gallery (like the studio model's middle range)
    cx, cy, L, W = -12.0, -50.0, 34.0, 13.0
    poly = rect(cx, cy, L, W)
    plinth(mb, poly, 38.0, 56.0)
    mb.prism(poly, 55.5, 70.0, ST)
    p0, p1 = poly[0], poly[1]
    for k in range(9):
        M, _ = edge_frame(p0, p1, (k + 0.5) / 9, 57.5)
        window(mb, M, 2.0, 6.0, 'pointed', depth=0.5, frame=0.28, glow=window_glow(0.8, 1.1), mullion=1,
               sharp=1.0)
    for k in range(9):
        M, _ = edge_frame(p0, p1, (k + 0.5) / 9, 65.0)
        window(mb, M, 1.1, 2.6, 'pointed', depth=0.3, frame=0.2, glow=window_glow(0.5, 0.9))
    for k in range(10):
        Mb, _ = edge_frame(p0, p1, k / 9, 0)
        if 0 < k < 9:
            buttress(mb, Mb, 42.0, 70.0, 0.9, 1.6, 3, pin=True)
    for p0_, p1_ in list(poly_edges(poly))[2:3]:
        windows_on_edge(mb, p0_, p1_, 58.0, 1.1, 3.0, 4.2, lit=0.5)
        windows_on_edge(mb, p0_, p1_, 64.5, 1.0, 2.5, 4.2, lit=0.5)
    string_course(mb, poly, 63.6, out=0.2, hgt=0.3)
    string_course(mb, poly, 69.7, out=0.35, hgt=0.4)
    crenellate(mb, offset_poly(poly, 0.25), 70.2, True, thick=0.5, low=0.9, merlon=0.7)
    gable_roof(mb, cx, cy, L, W, 70.3, 9.5, 0.0, over=0.2, dormers=5, dormer_lit=0.3)
    # small round front tower down on the rock ledge
    round_tower(mb, -31.0, -78.0, 5.6, 25.0, 68.0, n=20, roof='cone', roof_h=17.0, crown='mach', lit=0.45,
                win_w=0.8, win_h=2.0, bell=0.1)
    # linking curtain from the front tower to the gallery plinth
    crenellate(mb, [(-27, -74), (-18, -58)], 55.2, closed=False, thick=0.8, low=1.1)
    mb.seg_box((-27, -74), (-18, -58), 25.0, 55.3, 3.0, ST)


# ================================================================== CENTRAL CLUSTER
def central(mb):
    arch.RNG.seed(41)
    mb.rnd = 0.3
    # connecting ranges (roofs at varied heights)
    hall_block(mb, 42.0, -47.0, 36.0, 15.0, 52.0, 86.0, roof_h=11.0, lit=0.55, level=1.0, win_w=1.1, win_h=2.6,
               bay=4.2, buttress_d=1.4, dormers=4)
    plinth(mb, rect(42.0, -47.0, 36.0, 15.0), 38.0, 53.0)
    hall_block(mb, 48.0, -6.0, 30.0, 18.0, 55.0, 90.0, roof_h=12.0, lit=0.5, win_w=1.1, win_h=2.6, bay=4.5,
               dormers=3)
    hall_block(mb, 84.0, -20.0, 18.0, 30.0, 55.0, 84.0, roof_h=10.0, lit=0.5, win_w=1.0, win_h=2.4, bay=4.2,
               hip=True)
    hall_block(mb, 14.0, -28.0, 16.0, 30.0, 55.0, 82.0, roof_h=10.0, lit=0.5, win_w=1.0, win_h=2.4, bay=4.2,
               rz=0.0, hip=False, dormers=2)
    # --- the main tower: square shaft, octagonal belfry, great spire (tallest element)
    mx, my = 47.0, -26.0
    square_tower(mb, mx, my, 15.0, 15.0, 55.0, 121.0, roof=None, lit=0.55, level=1.1, win_w=1.3, win_h=3.2,
                 corner_turrets=True, crown='mach')
    oc = circle(mx, my, 6.6, 8, math.pi / 8)
    mb.prism(oc, 121.0, 139.0, ST)
    for k in range(8):
        a = TAU * k / 8
        rr = 6.6 * math.cos(math.pi / 8)
        M = mat_loc((mx + rr * math.cos(a), my + rr * math.sin(a), 124.0), rz_for(a))
        window(mb, M, 2.0, 10.0, 'pointed', depth=0.4, frame=0.28, glow=window_glow(0.5, 0.8), mullion=1,
               sharp=1.3)
    string_course(mb, oc, 138.6, out=0.35, hgt=0.4)
    for px, py in oc:
        pinnacle(mb, px, py, 139.0, 0.8, 6.5)
    crenellate(mb, offset_poly(oc, 0.1), 139.0, True, thick=0.45, low=0.8, merlon=0.6, mw=0.7, gap=0.55)
    pyramid_roof(mb, offset_poly(oc, -0.35), 139.2, 50.0, over=0.1, mat=SL, bell=0.04)
    # spire lucarnes
    for k in range(8):
        a = TAU * (k + 0.5) / 8
        rr = 5.3
        M = mat_loc((mx + rr * math.cos(a), my + rr * math.sin(a), 146.0), rz_for(a))
        arch.dormer(mb, M, 1.0, 1.9, 0.4)
    # --- attendant towers, no two alike
    round_tower(mb, 22.0, -52.0, 6.2, 44.0, 104.0, n=24, roof='cone', roof_h=24.0, crown='mach', lit=0.5,
                win_w=0.9, win_h=2.2, bell=0.1)
    square_tower(mb, 70.0, -50.0, 9.5, 9.5, 44.0, 108.0, roof='pyramid', roof_h=27.0, lit=0.45, win_w=1.0,
                 win_h=2.4, corner_turrets=True)
    round_tower(mb, 28.0, -4.0, 4.3, 55.0, 124.0, n=20, roof='cone', roof_h=19.0, roof_mat=CU, crown='eave',
                lit=0.45, win_w=0.8, win_h=2.0, win_every=2, bell=0.18, flare=0.7)
    # octagonal tower with needle spire
    oc2 = circle(74.0, -4.0, 5.2, 8, math.pi / 8)
    mb.prism(oc2, 55.0, 117.0, ST)
    for lev in range(9):
        z = 59.0 + lev * 6.5
        for k in range(8):
            if (k + lev) % 2:
                continue
            a = TAU * k / 8
            rr = 5.2 * math.cos(math.pi / 8)
            M = mat_loc((74.0 + rr * math.cos(a), -4.0 + rr * math.sin(a), z), rz_for(a))
            window(mb, M, 0.9, 2.3, 'pointed', depth=0.25, frame=0.16, glow=window_glow(0.45))
    machicolated_parapet(mb, oc2, 117.0, over=0.6)
    pyramid_roof(mb, offset_poly(oc2, -0.3), 117.3, 29.0, over=0.05, mat=SL, bell=0.02)
    round_tower(mb, 91.0, -40.0, 3.6, 42.0, 100.0, n=16, roof='cone', roof_h=15.0, crown='mach', lit=0.4,
                win_w=0.7, win_h=1.8, bell=0.14)
    round_tower(mb, 56.0, -61.0, 3.0, 40.0, 92.0, n=16, roof='cone', roof_h=13.0, roof_mat=CU, crown='eave',
                lit=0.4, win_w=0.6, win_h=1.6, bell=0.2, flare=0.6)
    square_tower(mb, 30.0, -34.0, 8.0, 8.0, 55.0, 113.0, roof='spire8', roof_h=30.0, lit=0.45, win_w=0.9,
                 win_h=2.2, crown='mach')
    round_tower(mb, 64.0, 12.0, 5.0, 55.0, 110.0, n=20, roof='cone', roof_h=21.0, crown='mach', lit=0.45,
                win_w=0.8, win_h=2.0, bell=0.08)
    # flying buttresses from the front range to its pier turrets
    for px in (34.0, 50.0):
        pier = (px, -60.5)
        mb.box(px - 0.8, -61.3, 44.0, px + 0.8, -59.7, 80.0, ST)
        pinnacle(mb, px, -60.5, 80.0, 1.0, 6.0)
        flying_buttress(mb, (px, -55.2), pier, 82.0, 78.0, 0.7)


# ================================================================== EAST RANGE, CLOCK TOWER, COURTYARD
def clock_face(mb, M, R=2.6, hour=10, minute=8):
    """readable clock: dial disc, roman numerals built from strokes, hands. Local -y out."""
    dial = 'ClockFace'
    n = 40
    ring = [(R * math.cos(TAU * i / n), -0.28, R * math.sin(TAU * i / n)) for i in range(n)]
    arch.face_toward(mb, ring, (0, -1, 0), dial, M)
    # stone surround ring
    outer = [((R + 0.55) * math.cos(TAU * i / n), (R + 0.55) * math.sin(TAU * i / n)) for i in range(n)]
    inner = [(R * math.cos(TAU * i / n), R * math.sin(TAU * i / n)) for i in range(n)]
    for i in range(n):
        j = (i + 1) % n
        arch.face_toward(mb, [(outer[i][0], -0.45, outer[i][1]), (outer[j][0], -0.45, outer[j][1]),
                              (inner[j][0], -0.45, inner[j][1]), (inner[i][0], -0.45, inner[i][1])],
                         (0, -1, 0), TR, M)
        arch.face_toward(mb, [(inner[i][0], -0.45, inner[i][1]), (inner[j][0], -0.45, inner[j][1]),
                              (inner[j][0], -0.28, inner[j][1]), (inner[i][0], -0.28, inner[i][1])],
                         (-(inner[i][0]), 0, -(inner[i][1])), TR, M)
        arch.face_toward(mb, [(outer[i][0], 0.1, outer[i][1]), (outer[j][0], 0.1, outer[j][1]),
                              (outer[j][0], -0.45, outer[j][1]), (outer[i][0], -0.45, outer[i][1])],
                         (outer[i][0], 0, outer[i][1]), TR, M)
    # numerals
    romans = ['XII', 'I', 'II', 'III', 'IIII', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI']
    gh = R * 0.2
    sw = gh * 0.13
    for h, txt in enumerate(romans):
        ang = math.pi / 2 - TAU * h / 12
        cxr = R * 0.76
        cx, cz = cxr * math.cos(ang), cxr * math.sin(ang)
        # glyph baseline faces the centre: glyph 'up' = outward direction
        up = (math.cos(ang), math.sin(ang))
        rt = (up[1], -up[0])
        cw = gh * 0.42
        total = sum(cw if c == 'I' else gh * 0.62 for c in txt)
        pos = -total / 2
        for ch in txt:
            wch = cw if ch == 'I' else gh * 0.62
            mid = pos + wch / 2
            strokes = []
            if ch == 'I':
                strokes = [((0, -gh / 2), (0, gh / 2))]
            elif ch == 'V':
                strokes = [((-wch * 0.4, gh / 2), (0, -gh / 2)), ((wch * 0.4, gh / 2), (0, -gh / 2))]
            elif ch == 'X':
                strokes = [((-wch * 0.4, gh / 2), (wch * 0.4, -gh / 2)), ((wch * 0.4, gh / 2), (-wch * 0.4, -gh / 2))]
            for (a0, b0), (a1, b1) in strokes:
                # glyph local (u along rt, v along up)
                p0 = (cx + rt[0] * (mid + a0) + up[0] * b0, cz + rt[1] * (mid + a0) + up[1] * b0)
                p1 = (cx + rt[0] * (mid + a1) + up[0] * b1, cz + rt[1] * (mid + a1) + up[1] * b1)
                L = math.dist(p0, p1)
                an = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
                m = M @ Matrix.Translation(((p0[0] + p1[0]) / 2, -0.3, (p0[1] + p1[1]) / 2)) @ Matrix.Rotation(-an, 4, 'Y')
                mb.box(-L / 2, -0.05, -sw / 2, L / 2, 0.0, sw / 2, MT, m)
            pos += wch + gh * 0.08
    # minute ticks
    for k in range(60):
        if k % 5 == 0:
            continue
        ang = math.pi / 2 - TAU * k / 60
        p = (R * 0.93 * math.cos(ang), R * 0.93 * math.sin(ang))
        m = M @ Matrix.Translation((p[0], -0.3, p[1])) @ Matrix.Rotation(-ang, 4, 'Y')
        mb.box(-0.06, -0.04, -0.025, 0.06, 0.0, 0.025, MT, m)
    # hands
    ha = math.pi / 2 - TAU * ((hour % 12) + minute / 60) / 12
    ma = math.pi / 2 - TAU * minute / 60
    for ang, ln, wd in ((ha, R * 0.5, 0.16), (ma, R * 0.78, 0.1)):
        m = M @ Matrix.Rotation(-ang, 4, 'Y')
        mb.box(-0.3, -0.42, -wd / 2, ln, -0.33, wd / 2, MT, m)
        tip = M @ Matrix.Translation((ln * math.cos(ang), -0.375, ln * math.sin(ang))) @ Matrix.Rotation(-ang, 4, 'Y')
        mb.add([(0, -0.045, -wd), (0, -0.045, wd), (wd * 2.2, -0.045, 0), (0, 0.045, -wd), (0, 0.045, wd), (wd * 2.2, 0.045, 0)],
               [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)], MT, tip)
    mb.lathe([(0.22, -0.46), (0.22, -0.3)], 12, MT, M @ Matrix.Rotation(math.pi / 2, 4, 'X'))


def east_range(mb):
    arch.RNG.seed(51)
    mb.rnd = 0.7
    hall_block(mb, 116.0, -8.0, 34.0, 16.0, 55.0, 79.0, roof_h=11.0, lit=0.55, win_w=1.1, win_h=2.6, bay=4.3,
               rz=math.radians(28), dormers=4)
    hall_block(mb, 104.0, 30.0, 14.0, 34.0, 55.0, 76.0, roof_h=9.0, lit=0.5, win_w=1.0, win_h=2.4, bay=4.2,
               hip=True)
    # clock tower at the viaduct gate
    x, y = 140.0, 30.0
    top = square_tower(mb, x, y, 11.0, 11.0, 50.0, 104.0, roof='pyramid', roof_h=27.0, lit=0.5,
                       win_w=1.0, win_h=2.4, levels=[58.0, 66.0, 74.0, 82.0], crown='mach', corner_turrets=True)
    for k, (phi) in enumerate((-math.pi / 2, 0.0, math.pi / 2)):
        ox, oy = math.cos(phi), math.sin(phi)
        M = mat_loc((x + ox * 5.5, y + oy * 5.5, 95.0), rz_for(phi))
        clock_face(mb, M, 2.7, 10, 9)
        # gothic frame: flanking colonnettes with pinnacles, pointed hood over the dial
        for sx in (-1, 1):
            mb.box(sx * 3.75 - 0.22, -0.55, -4.2, sx * 3.75 + 0.22, 0.1, 2.2, TR, M)
            p = M @ Vector((sx * 3.75, -0.33, 2.2))
            pinnacle(mb, p.x, p.y, p.z, 0.5, 4.8, rz_for(phi))
        hood = [(3.55 * math.cos(a_), 3.55 * math.sin(a_)) for a_ in [math.pi * k / 16 for k in range(17)]]
        hood = [(x, z * 1.25 if z > 0 else z) for x, z in hood]
        arch.bar_poly(mb, M, hood, 0.24, 0.05, -0.62, TR)
        finial_spike(mb, 0, 0, 4.25, 1.4, M=M @ Matrix.Translation((0, -0.35, 0)))
        # tracery panel beneath the dial
        for k in range(4):
            Mw = M @ Matrix.Translation((-2.4 + k * 1.6, 0.0, -7.8))
            window(mb, Mw, 0.8, 3.0, 'pointed', depth=0.18, frame=0.12, glow=window_glow(0.5, 0.9), mullion=0)
        mb.box(-3.9, -0.45, -4.6, 3.9, 0.1, -4.2, TR, M)
    # gatehouse where the viaduct enters (arched passage)
    hall_block(mb, 152.0, 42.0, 10.0, 12.0, 52.0, 68.0, roof_h=6.0, lit=0.5, win_w=0.9, win_h=2.0, bay=3.5,
               hip=True, parapet=True)
    for sx in (-1, 1):
        round_tower(mb, 157.0, 42.0 + sx * 6.8, 2.4, 44.0, 74.0, n=14, roof='cone', roof_h=9.0, crown='mach',
                    lit=0.4, win_w=0.5, win_h=1.4, bell=0.1)
    # courtyard ranges north of the gate
    hall_block(mb, 118.0, 72.0, 36.0, 13.0, 55.0, 74.0, roof_h=8.0, lit=0.45, win_w=1.0, win_h=2.4, bay=4.0,
               rz=math.radians(-18))


# ================================================================== NORTH RANGES (aerial filler)
def north(mb):
    arch.RNG.seed(61)
    mb.rnd = 0.8
    hall_block(mb, -95.0, -24.0, 52.0, 16.0, 55.0, 74.0, roof_h=10.0, lit=0.5, win_w=1.0, win_h=2.4, bay=4.0,
               dormers=4)
    hall_block(mb, -40.0, 10.0, 60.0, 15.0, 55.0, 78.0, roof_h=10.0, lit=0.5, win_w=1.0, win_h=2.4, bay=4.2,
               dormers=5)
    hall_block(mb, 10.0, 60.0, 50.0, 14.0, 55.0, 75.0, roof_h=9.0, lit=0.45, win_w=1.0, win_h=2.4, bay=4.0,
               rz=math.radians(12), dormers=3)
    hall_block(mb, -95.0, 55.0, 14.0, 44.0, 55.0, 72.0, roof_h=9.0, lit=0.45, win_w=1.0, win_h=2.4, bay=4.0)
    hall_block(mb, 70.0, 40.0, 24.0, 14.0, 55.0, 80.0, roof_h=9.0, lit=0.45, win_w=1.0, win_h=2.4, bay=4.0,
               rz=math.radians(70))
    round_tower(mb, -118.0, 70.0, 7.0, 50.0, 98.0, n=24, roof='cone', roof_h=24.0, crown='mach', lit=0.45,
                win_w=0.9, win_h=2.2, bell=0.1)
    square_tower(mb, -10.0, 92.0, 10.0, 10.0, 52.0, 106.0, roof='pyramid', roof_h=24.0, lit=0.45,
                 win_w=1.0, win_h=2.4, corner_turrets=False)
    round_tower(mb, -60.0, 40.0, 5.0, 55.0, 102.0, n=20, roof='cone', roof_h=20.0, roof_mat=CU, crown='eave',
                lit=0.45, win_w=0.8, win_h=2.0, flare=0.7, bell=0.16)
    round_tower(mb, 40.0, 100.0, 4.0, 50.0, 90.0, n=16, roof='cone', roof_h=15.0, crown='mach', lit=0.4,
                win_w=0.7, win_h=1.8)
    # north gatehouse (path to the grounds)
    hall_block(mb, 44.0, 122.0, 12.0, 10.0, 48.0, 66.0, roof_h=5.0, lit=0.4, win_w=0.9, win_h=2.0, bay=3.5, hip=True)
    for sx in (-1, 1):
        round_tower(mb, 44.0 + sx * 6.5, 126.0, 2.6, 40.0, 72.0, n=14, roof='cone', roof_h=9.5, crown='mach',
                    lit=0.35, win_w=0.5, win_h=1.4)


# ================================================================== WEST TERRACE, OWLERY
def west(mb):
    arch.RNG.seed(71)
    mb.rnd = 0.2
    # bastion round tower on the west ledge
    round_tower(mb, -163.0, -62.0, 6.5, 28.0, 64.0, n=24, roof='cone', roof_h=18.0, crown='mach', lit=0.4,
                win_w=0.8, win_h=2.0, bell=0.1)
    # terrace walls following the ledge rim
    pts = []
    for k in range(18):
        a = -0.2 + k * 0.22
        pts.append(crag.rim_point('Crag_West', -152 + 50 * math.cos(a), -52 + 50 * math.sin(a), 2.5))
    pts = [p for p in pts if p[1] < -30]
    crenellate(mb, pts, 41.0, closed=False, thick=0.8, low=1.1)
    for a, b in zip(pts[:-1], pts[1:]):
        mb.seg_box(a, b, 30.0, 41.2, 1.2, ST)
    # stair from ledge up to the hall plinth
    for k in range(24):
        z = 41.0 + k * 0.6
        mb.box(-138.0 + k * 0.5, -68.0, 38.0, -137.3 + k * 0.5, -64.5, z, ST)
    # owlery on its pinnacle
    ox, oy = -222.0, 58.0
    round_tower(mb, ox, oy, 4.6, 64.0, 82.0, n=16, roof=None, crown='eave', lit=0.0,
                win_levels=[], bands=False)
    for k in range(16):
        if k % 2:
            continue
        a = TAU * (k + 0.5) / 16 + math.pi / 16
        rr = 4.6 * math.cos(math.pi / 16)
        M = mat_loc((ox + rr * math.cos(a), oy + rr * math.sin(a), 72.0), rz_for(a))
        window(mb, M, 1.0, 2.6, 'round', depth=0.3, frame=0.15, glow=0.0, mullion=0)
        M = mat_loc((ox + rr * math.cos(a), oy + rr * math.sin(a), 77.5), rz_for(a))
        window(mb, M, 0.6, 1.2, 'round', depth=0.2, frame=0.12, glow=window_glow(0.25, 0.3), mullion=0)
    cone_roof(mb, ox, oy, 82.0, 4.6, 12.0, 16, SL, flare=1.1, bell=0.2)
    # the owlery stair from its rock down to the path
    for k in range(30):
        a = 2.3 + k * 0.11
        z = 64.0 - k * 0.55
        rr = 9.5 + k * 0.12
        mb.boxc((ox + rr * math.cos(a), oy + rr * math.sin(a), z - 6.0), (1.6, 2.4, 6.0), ST, rz=a)


# ================================================================== CURTAIN WALLS ALONG THE RIM
def curtain(mb):
    arch.RNG.seed(81)
    mb.rnd = 0.45
    # stretches of rim not covered by buildings: sample the rim, keep chosen spans
    spans = [((-150, 10), (-146, 46)), ((-146, 46), (-124, 82)), ((-84, 104), (-20, 122)),
             ((104, 106), (146, 84)), ((146, 84), (160, 52)), ((98, -50), (118, -34)), ((118, -34), (136, -14)),
             ((136, -14), (156, 18)), ((-146, -30), (-150, 10)), ((80, -58), (98, -50))]
    for a, b in spans:
        a2 = crag.rim_point('Crag_Main', *a, 3.0)
        b2 = crag.rim_point('Crag_Main', *b, 3.0)
        L = math.dist(a2, b2)
        segs = max(1, int(L / 8))
        pts = [(geo.lerp(a2[0], b2[0], k / segs), geo.lerp(a2[1], b2[1], k / segs)) for k in range(segs + 1)]
        for p, q in zip(pts[:-1], pts[1:]):
            mb.seg_box(p, q, 44.0, 60.0, 2.2, ST)
        crenellate(mb, pts, 60.0, closed=False, thick=0.7, low=1.0)
        arch.corbel_row(mb, pts, 60.0, closed=False, depth=0.5, spacing=1.5)
        # bartizan at the end of each span
        round_tower(mb, b2[0], b2[1], 2.0, 57.0, 64.0, n=12, roof='cone', roof_h=6.0, crown='eave',
                    win_levels=[59.5], lit=0.2, win_w=0.4, win_h=1.1, bands=False, flare=0.4, corbel=True)


# ================================================================== PAVING
def paving(mb):
    """plateau terraces: masonry retaining walls (exposed where the rock top drops) topped by paving."""
    for rim, zt, zb, ins in ((crag.MAIN_RIM, TOP + 0.55, 36.0, 2.0),
                             (crag.BLOBS[1]['rim'], 31.55, 16.0, 2.0),
                             (crag.BLOBS[2]['rim'], 41.55, 26.0, 2.0)):
        ring = offset_poly(rim, -ins)
        mb.prism(ring, zb, zt - 0.02, ST, cap_top=False)
        mb.add([(x, y, zt) for x, y in ring], [tuple(range(len(ring)))], 'Paving')
        string_course(mb, ring, zt - 0.5, out=0.3, hgt=0.4)


# ================================================================== VIADUCT
def viaduct(mb, lm):
    arch.RNG.seed(91)
    mb.rnd = 0.5
    x0, x1, y = 158.0, terrain.VIADUCT_X1, terrain.VIADUCT_Y
    deck = 53.0
    wdt = 7.0
    n = 12
    span = (x1 - x0) / n
    pw = 4.6
    hw = wdt / 2
    # piers
    for k in range(n + 1):
        px = x0 + k * span
        g = min(terrain.height(px, y), terrain.height(px, y - hw), terrain.height(px, y + hw)) - DZ
        g = min(g, 30.0 if k == 0 else g)
        zb = g - 3.0
        # footing with cutwaters
        mb.box(px - pw / 2 - 0.8, y - hw - 1.2, zb, px + pw / 2 + 0.8, y + hw + 1.2, max(g + 3.0, 1.5 - DZ), ST)
        for sy in (-1, 1):
            mb.add([(px - pw / 2 - 0.8, y + sy * (hw + 1.2), zb), (px + pw / 2 + 0.8, y + sy * (hw + 1.2), zb),
                    (px, y + sy * (hw + 4.0), zb), (px - pw / 2 - 0.8, y + sy * (hw + 1.2), max(g + 3.0, 1.5 - DZ)),
                    (px + pw / 2 + 0.8, y + sy * (hw + 1.2), max(g + 3.0, 1.5 - DZ)), (px, y + sy * (hw + 1.2), max(g + 5.5, 4.0 - DZ))],
                   [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)] if sy < 0 else
                   [(2, 1, 0), (4, 5, 3), (1, 4, 3, 0), (2, 5, 4, 1), (0, 3, 5, 2)], ST)
        # tapered shaft
        mb.loft([[(px - pw / 2 - 0.4, y - hw - 0.5, zb), (px + pw / 2 + 0.4, y - hw - 0.5, zb),
                  (px + pw / 2 + 0.4, y + hw + 0.5, zb), (px - pw / 2 - 0.4, y + hw + 0.5, zb)],
                 [(px - pw / 2, y - hw, deck - 1.0), (px + pw / 2, y - hw, deck - 1.0),
                  (px + pw / 2, y + hw, deck - 1.0), (px - pw / 2, y + hw, deck - 1.0)]], ST)
        # stepped buttresses on both faces of each pier
        for sy in (-1, 1):
            yb = y + sy * hw
            for k2, (d_, zt) in enumerate(((1.6, g + (deck - g) * 0.35), (1.1, g + (deck - g) * 0.7), (0.55, deck + 1.6))):
                z0_ = g if k2 == 0 else g + (deck - g) * (0.35 if k2 == 1 else 0.7)
                y0_, y1_ = (yb - d_, yb) if sy < 0 else (yb, yb + d_)
                mb.box(px - 0.9, y0_, z0_, px + 0.9, y1_, zt, TR if k2 == 2 else ST)
    # arches (upper tier springing at deck-12; lower tier where tall)
    def arch_span(xa, xb, zs, rise, top, pointed=True):
        segs = 10
        w = xb - xa
        pts = []
        for i in range(segs + 1):
            t = i / segs
            xx = xa + w * t
            if pointed:
                # two-centred arch
                u = abs(t - 0.5) * 2
                zz = zs + rise * math.sqrt(max(0, 1 - u ** 1.6))
            else:
                zz = zs + rise * math.sin(math.pi * t)
            pts.append((xx, zz))
        for sy in (-1, 1):
            yy = y + sy * hw
            for i in range(segs):
                (xa_, za_), (xb_, zb_) = pts[i], pts[i + 1]
                arch.face_toward(mb, [(xa_, yy, za_), (xb_, yy, zb_), (xb_, yy, top), (xa_, yy, top)], (0, sy, 0), ST)
        for i in range(segs):
            (xa_, za_), (xb_, zb_) = pts[i], pts[i + 1]
            arch.face_toward(mb, [(xa_, y - hw, za_), (xb_, y - hw, zb_), (xb_, y + hw, zb_), (xa_, y + hw, za_)],
                             (0, 0, -1), TR)
            # voussoir ring on both faces
            for sy in (-1, 1):
                yy = y + sy * (hw + 0.12)
                arch.face_toward(mb, [(xa_, yy, za_), (xb_, yy, zb_), (xb_, yy, zb_ + 0.9), (xa_, yy, za_ + 0.9)],
                                 (0, sy, 0), TR)
    for k in range(n):
        xa = x0 + k * span + pw / 2
        xb = x0 + (k + 1) * span - pw / 2
        arch_span(xa, xb, deck - 13.0, 6.5, deck - 1.0)
        gmid = min(terrain.height(x0 + (k + 0.5) * span, y), terrain.height(x0 + k * span, y),
                   terrain.height(x0 + (k + 1) * span, y)) - DZ
        if deck - 13.0 - gmid > 26:
            zs2 = max(gmid + 4, 3.0 - DZ) + (deck - 13.0 - gmid) * 0.45
            arch_span(xa, xb, zs2, 5.0, zs2 + 7.0)
            # string course across at the lower tier crown
    # deck, cornice and parapets
    mb.box(x0 - 2, y - hw - 0.3, deck - 1.2, x1 + 2, y + hw + 0.3, deck, TR)
    mb.box(x0 - 2, y - hw - 0.6, deck - 1.6, x1 + 2, y + hw + 0.6, deck - 1.1, TR)
    for sy in (-1, 1):
        yy = y + sy * (hw - 0.2)
        # pierced parapet: posts + rail, small pointed openings
        mb.box(x0 - 2, yy - 0.25, deck, x1 + 2, yy + 0.25, deck + 0.35, ST)
        mb.box(x0 - 2, yy - 0.3, deck + 1.05, x1 + 2, yy + 0.3, deck + 1.3, TR)
        # gothic arcaded balustrade: colonnettes carrying little pointed arches
        pitch = 0.95
        cnt = int((x1 - x0 + 4) / pitch)
        Mr = Matrix.Translation((0, yy, 0))
        for k in range(cnt + 1):
            xx = x0 - 2 + k * pitch
            mb.box(xx - 0.09, yy - 0.16, deck + 0.35, xx + 0.09, yy + 0.16, deck + 1.05, ST)
            if k < cnt:
                xa_, xb_ = xx + 0.09, xx + pitch - 0.09
                wv = xb_ - xa_
                arc = [(xa_ + wv / 2 + x, deck + 0.6 + z) for x, z in geo.pointed_arch(wv, 0.3, 3, 0.55)[1:]]
                arc = [(xb_, deck + 0.6)] + arc[1:] + [(xa_, deck + 0.6)]
                arch.bar_poly(mb, Mr, arc, 0.07, 0.13, -0.13, TR)
                # trefoil-ish spandrel disc
                mb.box(xx + pitch / 2 - 0.05, yy - 0.12, deck + 0.98, xx + pitch / 2 + 0.05, yy + 0.12, deck + 1.05, TR)
    # lanterns over each pier (both sides, alternating)
    for k in range(n + 1):
        px = x0 + k * span
        for sy in (-1, 1):
            yy = y + sy * (hw - 0.2)
            mb.box(px - 0.45, yy - 0.45, deck, px + 0.45, yy + 0.45, deck + 1.6, TR)
            lantern(lm, px, yy, deck + 1.6, post=True, power=35.0)
    # paving on deck
    mb.box(x0 - 2, y - hw + 0.4, deck - 0.05, x1 + 2, y + hw - 0.4, deck + 0.02, 'Paving')
    # east abutment and gate on the rock outcrop
    g = 80.0 - DZ - 3.0
    mb.box(x1 - 1, y - hw - 1.5, g - 6, x1 + 10, y + hw + 1.5, deck, ST)
    crenellate(mb, [(x1 + 10, y - hw - 1.5), (x1 - 1, y - hw - 1.5)], deck, closed=False, thick=0.6, low=1.0)
    crenellate(mb, [(x1 - 1, y + hw + 1.5), (x1 + 10, y + hw + 1.5)], deck, closed=False, thick=0.6, low=1.0)
    for sy in (-1, 1):
        round_tower(mb, x1 + 4.0, y + sy * (hw + 2.6), 2.3, g - 4, deck + 12.0, n=14, roof='cone', roof_h=8.5,
                    crown='mach', lit=0.3, win_w=0.5, win_h=1.4, bell=0.1)
    # castle end ramp from deck to courtyard level
    mb.box(x0 - 8, y - hw, 45.0, x0 - 1, y + hw, deck, ST)


# ================================================================== BOATHOUSE & STAIR
def shore_y(x, y_start=-90.0):
    y = y_start
    while y > -400:
        if terrain.height(x, y) < -0.3:
            return y
        y -= 0.5
    return y


def rock_face_y(x0, x1, z, bl_name=None):
    """southernmost rock surface y within [x0,x1] at height z, over all rock bodies."""
    ymin = 1e9
    for bl in crag.BLOBS:
        if bl_name and bl['name'] != bl_name:
            continue
        if z > bl['top'] + 0.5 or z < bl['bot']:
            continue
        c = bl['c']
        rim = bl['rim']
        for i in range(120):
            a = -math.pi + i * (math.pi / 119)
            r = crag.ray_poly(c, a, rim)
            x = c[0] + math.cos(a) * r
            yv = c[1] + math.sin(a) * r
            o = crag.radial_offset(bl, a, z, r, x, yv)
            rr = max(r + o, 2.0)
            px, py = c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr
            if x0 - 1.5 <= px <= x1 + 1.5:
                ymin = min(ymin, py)
    return ymin


MOORED = []   # (x, y, yaw) of boats tied up at the jetty


def boathouse(mb, lm):
    arch.RNG.seed(101)
    mb.rnd = 0.9
    MOORED.clear()
    bx = 6.0
    sy = min(shore_y(bx), min(rock_face_y(bx - 12, bx + 12, z) for z in (0.5, 3.0, 6.0, 10.0, 14.0)) - 1.0)
    L, W = 18.0, 14.0   # deep hall; its tall gable faces the lake
    by = sy - L / 2 + 3.0
    # quay / stone base
    mb.box(bx - W / 2 - 4, by - L / 2 - 2.5, -4.0, bx + W / 2 + 5, by + L / 2 + 6, 1.2, ST)
    string_course(mb, rect(bx + 0.5, by + 1.75, W + 9, L + 8.5), 0.9, out=0.2, hgt=0.3)
    poly = rect(bx, by, W, L)
    # stone ground storey with the water gate
    mb.prism(poly, 1.2, 7.0, ST)
    string_course(mb, poly, 6.8, out=0.25, hgt=0.35)
    # jettied timber upper storey
    up = offset_poly(poly, 0.45)
    mb.prism(up, 7.1, 12.0, 'Plaster')
    for p0, p1 in poly_edges(offset_poly(poly, 0.5)):
        Le = math.dist(p0, p1)
        cnt = max(2, int(Le / 1.5))
        for k in range(cnt + 1):
            M, _ = edge_frame(p0, p1, k / cnt, 0)
            mb.box(-0.13, -0.12, 7.1, 0.13, 0.06, 12.0, 'Beam', M)
        for zz in (7.15, 9.4, 11.95):
            M, _ = edge_frame(p0, p1, 0.5, 0)
            mb.box(-Le / 2 - 0.1, -0.15, zz - 0.12, Le / 2 + 0.1, 0.06, zz + 0.12, 'Beam', M)
        # diagonal braces
        for k in range(cnt):
            if k % 2:
                continue
            M, _ = edge_frame(p0, p1, (k + 0.5) / cnt, 0)
            dl = math.hypot(Le / cnt, 2.2)
            ang = math.atan2(2.2, Le / cnt) * (1 if k % 4 == 0 else -1)
            mb.box(-dl / 2, -0.1, -0.09, dl / 2, 0.05, 0.09, 'Beam', M @ Matrix.Translation((0, 0, 8.3)) @ Matrix.Rotation(-ang, 4, 'Y'))
    # joist ends under the jetty
    for p0, p1 in poly_edges(poly):
        Le = math.dist(p0, p1)
        for k in range(int(Le / 0.9)):
            M, _ = edge_frame(p0, p1, (k + 0.5) / int(Le / 0.9), 0)
            mb.box(-0.1, -0.5, 6.85, 0.1, 0.05, 7.1, 'Beam', M)
    # windows: side lights and a tall gable window over the lake
    for ei, (p0, p1) in enumerate(poly_edges(up)):
        if ei in (1, 3):
            windows_on_edge(mb, p0, p1, 7.9, 0.9, 2.4, 2.4, 'pointed', lit=0.9, level=1.3, margin=1.3,
                            depth=0.2, frame=0.14)
            windows_on_edge(mb, poly[ei], poly[(ei + 1) % 4], 3.0, 0.7, 1.6, 3.4, 'round', lit=0.6, level=0.9,
                            margin=2.0, depth=0.3, frame=0.15)
    p0, p1 = up[0], up[1]
    for t in (0.22, 0.78):
        M, _ = edge_frame(p0, p1, t, 7.9)
        window(mb, M, 1.0, 2.6, 'pointed', depth=0.2, frame=0.14, glow=window_glow(1.0, 1.3), mullion=0)
    # the great water gate (warm interior visible through it)
    M, _ = edge_frame(poly[0], poly[1], 0.5, 0.2)
    arch.door(mb, M, 6.4, 6.2, glow=0.35)
    for sx in (-1, 1):
        Ml, _ = edge_frame(poly[0], poly[1], 0.5 + sx * 0.36, 4.6)
        p = Ml @ Vector((0, -0.55, 0))
        mb.box(p.x - 0.05, p.y - 0.3, p.z - 0.05, p.x + 0.05, p.y + 0.5, p.z + 0.05, MT)
        lantern(lm, p.x, p.y - 0.3, p.z - 0.6, post=False, power=14)
    # gable wall to the lake in the roof space: tall lancet
    M, _ = edge_frame(up[0], up[1], 0.5, 12.4)
    window(mb, M, 1.6, 5.0, 'pointed', depth=0.25, frame=0.2, glow=window_glow(1.0, 1.5), mullion=1, sharp=1.2)
    # steep roof, dormers, ridge fleche
    gable_roof(mb, bx, by, L + 1.0, W + 0.9, 12.0, 11.5, math.pi / 2, over=1.0, dormers=3, dormer_lit=0.7)
    fx, fy = bx, by + 1.0
    rzt = 12.0 + 11.5
    mb.box(fx - 0.9, fy - 0.9, rzt - 3.0, fx + 0.9, fy + 0.9, rzt + 2.2, 'Plaster')
    for k in range(4):
        a = k * math.pi / 2
        M = mat_loc((fx + 0.9 * math.cos(a), fy + 0.9 * math.sin(a), rzt + 0.1), rz_for(a))
        window(mb, M, 0.55, 1.5, 'pointed', depth=0.08, frame=0.08, glow=0.8, mullion=0, sill=False, hood=False)
    pyramid_roof(mb, [(fx - 1.0, fy - 1.0), (fx + 1.0, fy - 1.0), (fx + 1.0, fy + 1.0), (fx - 1.0, fy + 1.0)],
                 rzt + 2.2, 6.5, over=0.25, mat=SL)
    # jetty (timber) running out into the lake beside the gate, with moored boats
    jx = bx + W / 2 + 3.2
    y_end = by - L / 2 - 26.0
    for k in range(14):
        yy = by - L / 2 + 1 - k * 2.0
        for sx in (-1, 1):
            mb.box(jx + sx * 1.1 - 0.13, yy - 0.13, -4, jx + sx * 1.1 + 0.13, yy + 0.13, 1.5, 'Beam')
    mb.box(jx - 1.4, y_end, 0.95, jx + 1.4, by - L / 2 + 2, 1.18, WD)
    for sx in (-1, 1):
        mb.box(jx + sx * 1.3 - 0.05, y_end, 1.18, jx + sx * 1.3 + 0.05, by - L / 2 + 2, 1.28, 'Beam')
    lantern(lm, jx + 1.1, y_end + 0.5, 1.18, post=True, power=16)
    lantern(lm, jx - 1.1, y_end + 13.0, 1.18, post=True, power=12)
    for k, (dx, dy, yaw) in enumerate(((3.0, -6.0, 1.52), (3.1, -13.0, 1.63), (-3.0, -17.0, 1.58), (3.2, -20.5, 1.5))):
        MOORED.append((jx + dx, by - L / 2 + dy, yaw))
    GLOW_LIGHTS.append((bx, by - L / 2 + 1.5, 3.0, 40.0, (1.0, 0.55, 0.25)))
    return bx, by, L, W, sy


def ext_y(mb, poly, y0, y1, mat):
    """extrude an x-z polygon (list of (x,z)) between y0 and y1 (y0 < y1)."""
    n = len(poly)
    front = [(x, y0, z) for x, z in poly]
    back = [(x, y1, z) for x, z in poly]
    arch.face_toward(mb, front, (0, -1, 0), mat)
    arch.face_toward(mb, back, (0, 1, 0), mat)
    cx = sum(p[0] for p in poly) / n
    cz = sum(p[1] for p in poly) / n
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        arch.face_toward(mb, [(a[0], y0, a[1]), (b[0], y0, b[1]), (b[0], y1, b[1]), (a[0], y1, a[1])],
                         ((a[0] + b[0]) / 2 - cx, 0, (a[1] + b[1]) / 2 - cz), mat)


def stair_run(mb, lm, xa, za, xb, zb, wd=3.0, seg=3.0, lantern_every=4):
    """one long straight flight climbing from (xa,za) to (xb,zb) along the cliff contour."""
    n = max(2, int(abs(xb - xa) / seg))
    xs = [geo.lerp(xa, xb, i / n) for i in range(n + 1)]
    zs = [geo.lerp(za, zb, i / n) for i in range(n + 1)]
    # face position per segment, then smoothed so the flight reads as one line
    ys = []
    for i in range(n):
        x0_, x1_ = min(xs[i], xs[i + 1]), max(xs[i], xs[i + 1])
        zlo, zhi = min(zs[i], zs[i + 1]), max(zs[i], zs[i + 1])
        yf = min(rock_face_y(x0_, x1_, zz) for zz in (zlo - 4.0, zlo - 1.0, zhi + 1.0, zhi + 3.0))
        ys.append(yf - 0.6 - wd)
    sm = []
    for i in range(n):
        w = ys[max(0, i - 2):i + 3]
        sm.append(min(w))
    for i in range(n):
        x0_, x1_ = xs[i], xs[i + 1]
        z0_, z1_ = zs[i], zs[i + 1]
        y0 = sm[i]
        y1 = y0 + wd
        lo, hi = (x0_, x1_) if x0_ < x1_ else (x1_, x0_)
        zl, zh = (z0_, z1_) if x0_ < x1_ else (z1_, z0_)
        base = min(z0_, z1_) - 3.2
        ext_y(mb, [(lo, base), (hi, base), (hi, zh - 0.2), (lo, zl - 0.2)], y0 - 0.5, y1 + 0.6, ST)
        # arched soffit band under the flight
        ext_y(mb, [(lo, base - 0.5), (hi, base - 0.5), (hi, base), (lo, base)], y0 - 0.6, y1 + 0.6, TR)
        # treads
        steps = max(1, int(round(abs(z1_ - z0_) / 0.18)))
        for k in range(steps):
            t0, t1 = k / steps, (k + 1) / steps
            xa_, xb_ = geo.lerp(x0_, x1_, t0), geo.lerp(x0_, x1_, t1)
            zt = geo.lerp(z0_, z1_, t1 if z1_ > z0_ else t0)
            mb.box(min(xa_, xb_), y0, zt - 0.22, max(xa_, xb_), y1, zt, 'Paving')
        # parapet + coping on the open side, higher wall on the rock side
        for (ya, yb_, hgt) in ((y0 - 0.5, y0 - 0.02, 1.05), (y1 + 0.02, y1 + 0.55, 1.6)):
            ext_y(mb, [(lo, zl - 0.3), (hi, zh - 0.3), (hi, zh + hgt), (lo, zl + hgt)], ya, yb_, ST)
            ext_y(mb, [(lo, zl + hgt), (hi, zh + hgt), (hi, zh + hgt + 0.18), (lo, zl + hgt + 0.18)],
                  ya - 0.08, yb_ + 0.08, TR)
        if i % lantern_every == 2:
            lantern(lm, (lo + hi) / 2, y0 - 0.26, (zl + zh) / 2 + 1.23, post=False, power=18.0)
        if i % 3 == 0:
            # buttress pier dropping into the rock below
            pz = (zl + zh) / 2
            mb.box(lo - 0.2, y0 - 1.1, pz - 26.0, lo + 1.0, y1 + 0.4, pz - 0.4, ST)
            mb.box(lo - 0.35, y0 - 1.25, pz - 3.8, lo + 1.15, y1 + 0.5, pz - 3.4, TR)
    return sm


def boat_stair(mb, lm, bx, by, L):
    """two long diagonal flights (a '<' on the cliff) from the quay to the terrace gate."""
    arch.RNG.seed(111)
    mb.rnd = 0.35
    xq = bx + 12.0
    xt = bx + 78.0
    zmid = 44.0
    ztop = TOP + DZ + 0.4
    y1 = stair_run(mb, lm, xq, 1.2, xt, zmid)
    y2 = stair_run(mb, lm, xt + 3.0, zmid, bx + 8.0, ztop)
    # landing at the turn: a small square stair-turret with a pyramid cap
    yl = min(y1[-1], y2[0])
    yh = max(y1[-1], y2[0]) + 4.0
    cx_, cy_ = xt + 2.5, (yl + yh) / 2
    wx, wy = 7.5, yh - yl + 1.0
    mb.box(cx_ - wx / 2, cy_ - wy / 2, zmid - 16.0, cx_ + wx / 2, cy_ + wy / 2, zmid - 0.2, ST)
    string_course(mb, rect(cx_, cy_, wx, wy), zmid - 0.6, out=0.25, hgt=0.35)
    mb.box(cx_ - wx / 2 + 0.3, cy_ - wy / 2 + 0.3, zmid - 0.22, cx_ + wx / 2 - 0.3, cy_ + wy / 2 - 0.3, zmid, 'Paving')
    for sx in (-1, 1):
        mb.box(cx_ + sx * (wx / 2 - 0.5) - 0.5, cy_ - wy / 2, zmid, cx_ + sx * (wx / 2 - 0.5) + 0.5, cy_ - wy / 2 + 1.0, zmid + 3.2, ST)
    pyramid_roof(mb, rect(cx_, cy_ + 0.5, wx, wy - 1.0), zmid + 3.2, 5.5, over=0.35, mat=SL)
    M, _ = edge_frame((cx_ - wx / 2, cy_ - wy / 2), (cx_ + wx / 2, cy_ - wy / 2), 0.5, zmid - 9.0)
    window(mb, M, 0.7, 2.0, 'pointed', depth=0.2, frame=0.14, glow=window_glow(1.0, 0.8), mullion=0)
    lantern(lm, cx_, cy_ - wy / 2 + 0.5, zmid + 2.2, post=False, power=22.0)
    # quay landing
    mb.box(bx + 4.0, y1[0] - 0.5, -3.0, xq + 0.5, y1[0] + 3.0, 1.2, ST)
    return y1, y2


def cliff_path(mb, lm):
    """lantern-lit path cut across the west face: from the west terrace down to a landing stage."""
    arch.RNG.seed(131)
    mb.rnd = 0.6
    ys = stair_run(mb, lm, -150.0, 41.0 + DZ - 0.5, -92.0, 36.0, wd=2.2, lantern_every=3)
    ys2 = stair_run(mb, lm, -89.0, 36.0, -40.0, 1.3, wd=2.2, lantern_every=3)
    yl = min(ys[-1], ys2[0])
    mb.box(-93.0, yl - 0.5, 30.0, -88.0, yl + 4.0, 35.8, ST)
    mb.box(-93.0, yl, 35.78, -88.0, yl + 3.0, 36.0, 'Paving')
    lantern(lm, -90.5, yl - 0.2, 36.0, post=True, power=18.0)
    # small landing stage at the foot
    y0 = ys2[-1]
    mb.box(-44.0, y0 - 6.0, -3.0, -34.0, y0 + 2.0, 1.2, ST)
    lantern(lm, -35.0, y0 - 5.5, 1.2, post=True, power=18.0)


# ================================================================== GREENHOUSES
def greenhouses(mb, gm, lm):
    arch.RNG.seed(121)
    mb.rnd = 0.15
    z = 31.6
    specs = [(128.0, -52.0, 24.0, 9.0, 0.35), (160.0, -58.0, 20.0, 8.0, 0.2), (150.0, -28.0, 26.0, 9.0, 0.28)]
    for (cx, cy, L, W, rz) in specs:
        M = mat_loc((cx, cy, 0), rz)
        # dwarf brick wall
        mb.box(-L / 2, -W / 2, z - 0.3, L / 2, W / 2, z + 0.9, ST, M)
        # glass envelope: walls + pitched roof
        hwall = 3.2
        ridge = 6.6
        gv = [(-L / 2 + 0.1, -W / 2 + 0.1, z + 0.9), (L / 2 - 0.1, -W / 2 + 0.1, z + 0.9),
              (L / 2 - 0.1, W / 2 - 0.1, z + 0.9), (-L / 2 + 0.1, W / 2 - 0.1, z + 0.9),
              (-L / 2 + 0.1, -W / 2 + 0.1, z + hwall), (L / 2 - 0.1, -W / 2 + 0.1, z + hwall),
              (L / 2 - 0.1, W / 2 - 0.1, z + hwall), (-L / 2 + 0.1, W / 2 - 0.1, z + hwall),
              (-L / 2 + 0.1, 0, z + ridge), (L / 2 - 0.1, 0, z + ridge)]
        gf = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 9, 8), (6, 7, 8, 9),
              (5, 6, 9), (7, 4, 8)]
        gm.add(gv, gf, 'GreenhouseGlass', M)
        # iron glazing bars
        cnt = int(L / 0.9)
        for k in range(cnt + 1):
            x = -L / 2 + 0.1 + (L - 0.2) * k / cnt
            for sy in (-1, 1):
                mb.box(x - 0.04, sy * (W / 2 - 0.1) - 0.04, z + 0.9, x + 0.04, sy * (W / 2 - 0.1) + 0.04, z + hwall, 'Frame', M)
                # rafter
                a = Vector((x, sy * (W / 2 - 0.1), z + hwall))
                b = Vector((x, 0, z + ridge))
                ln = (b - a).length
                ang = math.atan2(b.z - a.z, -sy * (b.y - a.y) if sy < 0 else (a.y - b.y))
                mr = M @ Matrix.Translation((a + b) / 2) @ Matrix.Rotation(math.atan2(b.z - a.z, abs(b.y - a.y)) * (-sy), 4, 'X')
                mb.box(-0.04, -ln / 2, -0.04, 0.04, ln / 2, 0.04, 'Frame', mr)
        for zz in (z + 0.9, z + 2.0, z + hwall):
            for sy in (-1, 1):
                mb.box(-L / 2, sy * (W / 2 - 0.1) - 0.05, zz - 0.04, L / 2, sy * (W / 2 - 0.1) + 0.05, zz + 0.04, 'Frame', M)
        mb.box(-L / 2, -0.08, z + ridge - 0.05, L / 2, 0.08, z + ridge + 0.25, 'Frame', M)
        # ends
        for sx in (-1, 1):
            for k in range(7):
                yy = -W / 2 + W * k / 6
                top = z + hwall + (ridge - hwall) * (1 - abs(yy) / (W / 2))
                mb.box(sx * (L / 2 - 0.1) - 0.04, yy - 0.04, z + 0.9, sx * (L / 2 - 0.1) + 0.04, yy + 0.04, top, 'Frame', M)
        # plants inside: benches with clumps
        rnd = random.Random(int(cx * 7))
        for k in range(int(L / 1.4)):
            for sy in (-1, 1):
                px = -L / 2 + 1.0 + k * 1.4 + rnd.uniform(-0.3, 0.3)
                py = sy * (W / 4) + rnd.uniform(-0.6, 0.6)
                h = rnd.uniform(0.6, 2.4)
                mb.lathe([(0.0, z + 0.9), (rnd.uniform(0.4, 0.8), z + 0.9 + h * 0.3), (rnd.uniform(0.3, 0.6), z + 0.9 + h * 0.8),
                          (0.0, z + 0.9 + h)], 7, 'Plant', M @ mat_loc((px, py, 0)))
        GLOW_LIGHTS.append((*(M @ Vector((0, 0, z + 4.0)))[:2], z + 4.0 + mb.zoff, 180.0, (1.0, 0.72, 0.42)))
    # terrace parapet along the east ledge rim
    pts = []
    for k in range(26):
        a = -2.6 + k * 0.2
        pts.append(crag.rim_point('Crag_East', 150 + 70 * math.cos(a), -40 + 50 * math.sin(a), 2.0))
    crenellate(mb, pts, 31.0, closed=False, thick=0.6, low=1.0, merlon=0.0 if False else 0.6)
    for a, b in zip(pts[:-1], pts[1:]):
        mb.seg_box(a, b, 22.0, 31.3, 1.0, ST)
    for p in pts[::5]:
        lantern(lm, p[0], p[1], 32.0, post=True, power=18.0)
    # kitchen garden: clipped hedges along the parapet, yews, raised beds
    import nature
    hed = []
    for k in range(40):
        a_ = -2.7 + k * 0.13
        hed.append(crag.rim_point('Crag_East', 146 + 70 * math.cos(a_), -40 + 50 * math.sin(a_), 5.0))
    for p, q in zip(hed[:-1], hed[1:]):
        mb.seg_box(p, q, z - 0.2, z + 1.0, 0.9, 'Shrub')
    rnd = random.Random(77)
    for k in range(9):
        a_ = -2.5 + k * 0.62
        px, py = crag.rim_point('Crag_East', 146 + 70 * math.cos(a_), -40 + 50 * math.sin(a_), 8.0)
        nature.conifer(mb, rnd.uniform(5.5, 8.0), rnd.uniform(1.4, 2.0), 6, 100 + k, 'spruce') if False else None
        mt = mat_loc((px, py, z - 0.2))
        tm = MB('tmp')
        nature.conifer2(tm, rnd.uniform(5.5, 8.0), rnd.uniform(1.3, 1.9), 100 + k, 'spruce')
        base_ = len(mb.v)
        for v in tm.v:
            q = mt @ Vector(v)
            mb.v.append((q.x, q.y, q.z + mb.zoff))
        for f_, m_ in zip(tm.f, tm.fm):
            mb.f.append(tuple(base_ + i for i in f_))
            mb.fm.append(mb.mi(tm.mats[m_]))
            mb.fg.append(0.0)
            mb.fr.append(rnd.random())
    for (bx_, by_) in ((122.0, -30.0), (135.0, -70.0), (170.0, -44.0)):
        mb.box(bx_ - 3.0, by_ - 1.2, z - 0.2, bx_ + 3.0, by_ + 1.2, z + 0.5, ST)
        mb.box(bx_ - 2.8, by_ - 1.0, z + 0.5, bx_ + 2.8, by_ + 1.0, z + 0.62, 'Soil')
    # stair from the terrace up to the main level
    for k in range(40):
        zz = 31.5 + k * 0.6
        mb.box(108.0 + k * 0.0 - 1.8, -40.0 + k * 0.5, 28.0, 108.0 + 1.8, -39.4 + k * 0.5, zz, ST)


# ================================================================== COURTYARD LANTERNS & INTERIOR FILLS
def courtyard_lights(lm):
    for (x, y) in [(-60, -20), (-20, -20), (20, 30), (60, 70), (100, 50), (125, 40), (-40, 60), (-100, 30),
                   (0, 110), (90, 0), (-130, -10), (-10, -64), (8, -64)]:
        lantern(lm, x, y, TOP + 0.55, post=True, power=28.0)


# ================================================================== BUILD
def build():
    LANTERNS.clear()
    GLOW_LIGHTS.clear()
    geo.clear_coll('Castle')
    coll = geo.get_coll('Castle')
    stats = {}
    lm = MB('Castle_Lanterns')
    lm.zoff = DZ
    lo = MB('Castle_LanternsLow')
    for name, fn in [('Castle_GreatHall', great_hall), ('Castle_ConeTower', cone_tower),
                     ('Castle_Gallery', gallery), ('Castle_CentralTowers', central),
                     ('Castle_EastRange', east_range), ('Castle_NorthRanges', north),
                     ('Castle_WestTerrace', west), ('Castle_CurtainWalls', curtain),
                     ('Castle_Paving', paving)]:
        mb = MB(name)
        mb.zoff = DZ
        fn(mb)
        mb.build(coll, smooth_angle=40)
        stats[name] = len(mb.f)
    mb = MB('Castle_Viaduct')
    mb.zoff = DZ
    viaduct(mb, lm)
    mb.build(coll, smooth_angle=40)
    stats['Castle_Viaduct'] = len(mb.f)
    mb = MB('Castle_Boathouse')
    bx, by, L, W, sy = boathouse(mb, lo)
    mb.build(coll, smooth_angle=40)
    mb = MB('Castle_BoathouseStair')
    boat_stair(mb, lo, bx, by, L)
    mb.build(coll, smooth_angle=40)
    mb = MB('Castle_Greenhouses')
    mb.zoff = DZ
    gm = MB('Castle_GreenhouseGlass')
    gm.zoff = DZ
    greenhouses(mb, gm, lm)
    mb.build(coll, smooth_angle=40)
    gm.build(coll)
    courtyard_lights(lm)
    for m_ in (lm, lo):
        ob = m_.build(coll, smooth_angle=40)
        if ob:
            ob.visible_shadow = False  # the lantern lights sit inside the cages
    stats['lanterns'] = len(LANTERNS)
    return stats
