"""Window units, lattice walls with punched openings, and gothic detail pieces.

Window units are built once per (type, w, h) and instanced with linked mesh
data.  Each instance carries its glow in object color:  R = emission strength
(0 = dark room), G = warmth (0 cold-yellow .. 1 deep orange).
"""
import bpy, bmesh, math, random, importlib
from mathutils import Vector, Matrix
import hog_lib as H
importlib.reload(H)
from hog_lib import bm_box, bm_box_zrange, bm_cylinder, bm_cone, bm_prism

MAT_STONE = "M_Stone"
MAT_TRIM = "M_StoneTrim"
MAT_GLASS = "M_Glass"
MAT_LEAD = "M_Lead"
MAT_SLATE = "M_Slate"

_unit_cache = {}
_rng = random.Random(7)

# --------------------------------------------------------------------------- arch loop
def arch_loop(w, h, style="lancet", n_arc=9):
    """Closed 2D loop (x, z) of the window opening, CCW, starting bottom-left.
    style: lancet (two-centre pointed), round, rect."""
    pts = []
    if style == "rect":
        return [(-w / 2, 0.0), (w / 2, 0.0), (w / 2, h), (-w / 2, h)]
    if style == "round":
        r = w / 2
        zs = h - r
        pts = [(-w / 2, 0.0), (w / 2, 0.0), (w / 2, zs)]
        for k in range(1, 2 * n_arc):
            a = math.pi * k / (2 * n_arc)
            pts.append((r * math.cos(a), zs + r * math.sin(a)))
        pts.append((-w / 2, zs))
        return pts
    # lancet
    r = w * (1.15 if w < 1.6 else 1.0)
    cxr = w / 2 - r            # centre of the right-hand arc (on the left)
    rise = math.sqrt(r * r - (r - w / 2) ** 2)
    zs = h - rise
    if zs < 0.3 * h:
        zs = 0.3 * h; rise = h - zs
    th_apex = math.atan2(rise, -cxr)
    pts = [(-w / 2, 0.0), (w / 2, 0.0), (w / 2, zs)]
    for k in range(1, n_arc):
        a = th_apex * k / n_arc
        pts.append((cxr + r * math.cos(a), zs + r * math.sin(a)))
    pts.append((0.0, zs + rise))
    for k in range(n_arc - 1, 0, -1):
        a = th_apex * k / n_arc
        pts.append((-(cxr + r * math.cos(a)), zs + r * math.sin(a)))
    pts.append((-w / 2, zs))
    return pts

def _ray_rect(cx, cz, ang, x0, x1, z0, z1):
    dx, dz = math.cos(ang), math.sin(ang)
    best = 1e9
    if abs(dx) > 1e-9:
        for xx in (x0, x1):
            t = (xx - cx) / dx
            if t > 0:
                zz = cz + dz * t
                if z0 - 1e-6 <= zz <= z1 + 1e-6:
                    best = min(best, t)
    if abs(dz) > 1e-9:
        for zz in (z0, z1):
            t = (zz - cz) / dz
            if t > 0:
                xx = cx + dx * t
                if x0 - 1e-6 <= xx <= x1 + 1e-6:
                    best = min(best, t)
    return (cx + dx * best, cz + dz * best)

def _resample_by_angle(loop, cx, cz, n):
    """Resample a star-shaped loop at n equally spaced angles around (cx, cz)."""
    out = []
    m = len(loop)
    for k in range(n):
        ang = -math.pi + 2 * math.pi * (k + 0.5) / n
        dx, dz = math.cos(ang), math.sin(ang)
        best = None
        for i in range(m):
            (ax, az), (bx, bz) = loop[i], loop[(i + 1) % m]
            ex, ez = bx - ax, bz - az
            den = dx * ez - dz * ex
            if abs(den) < 1e-12:
                continue
            t = ((ax - cx) * ez - (az - cz) * ex) / den
            u = ((ax - cx) * dz - (az - cz) * dx) / den
            if t > 0 and -1e-6 <= u <= 1 + 1e-6:
                if best is None or t < best[0]:
                    best = (t, (ax + ex * u, az + ez * u))
        out.append(best[1] if best else (cx, cz))
    return out

# --------------------------------------------------------------------------- window unit mesh
def build_window_unit(kind, w, h, lights=1, transom=True, glass=True, depth=0.45, proud=0.07, tracery=True, plate_w=None):
    """Return a mesh: window unit in local coords (X along wall, +Y outward, Z up; sill at z=0)."""
    key = (kind, round(w, 2), round(h, 2), lights, transom, glass, tracery, plate_w)
    if key in _unit_cache and _unit_cache[key].users >= 0 and _unit_cache[key].name in bpy.data.meshes:
        return _unit_cache[key]
    style = {"lancet": "lancet", "twin": "lancet", "great": "lancet", "rect": "rect", "slit": "rect", "round": "round"}[kind]
    bm = bmesh.new()
    loop = arch_loop(w, h, style)
    jamb = 0.32 if w > 0.6 else 0.18
    if plate_w is not None:
        jamb = max(jamb, (plate_w - w) / 2 + 0.05)
    sill_d = 0.30
    head = 0.42 if style != "rect" else 0.30
    X0, X1, Z0, Z1 = -w / 2 - jamb, w / 2 + jamb, -sill_d, h + head
    cx, cz = 0.0, h * 0.5
    n = max(24, 4 * len(loop))
    inner = _resample_by_angle(loop, cx, cz, n)
    outer = [_ray_rect(cx, cz, -math.pi + 2 * math.pi * (k + 0.5) / n, X0, X1, Z0, Z1) for k in range(n)]
    # front plate (proud of the wall) : ring between outer rect and arch opening
    vin_f = [bm.verts.new((x, proud, z)) for x, z in inner]
    vout_f = [bm.verts.new((x, proud, z)) for x, z in outer]
    vout_b = [bm.verts.new((x, 0.0, z)) for x, z in outer]
    vin_b = [bm.verts.new((x, -depth, z)) for x, z in inner]
    faces = []
    for k in range(n):
        k2 = (k + 1) % n
        faces.append(bm.faces.new((vout_f[k], vout_f[k2], vin_f[k2], vin_f[k])))   # plate front
        faces.append(bm.faces.new((vout_b[k], vout_b[k2], vout_f[k2], vout_f[k])))  # plate rim
        faces.append(bm.faces.new((vin_f[k], vin_f[k2], vin_b[k2], vin_b[k])))      # reveal
    stone_faces = list(faces)
    # glass pane (n-gon) at the back of the reveal
    glass_faces = []
    if glass:
        gf = bm.faces.new(list(reversed(vin_b)))
        glass_faces.append(gf)
    # sill: a projecting block below the opening
    sv = bm_box(bm, (w + 2 * jamb + 0.16, 0.22, 0.16), (0.0, proud + 0.02, -sill_d + 0.08))
    # hood mould: thin band following the outer top (approximate with a box for rect, arc for arches)
    trim_faces = []
    if style != "rect" and w > 0.7:
        r_h = w / 2 + jamb + 0.08
        # simple arc band across the head
        band = []
        m = 10
        for k in range(m + 1):
            a = math.pi * k / m
            band.append((r_h * math.cos(a), h - w / 2 * 0.15 + (w / 2 + jamb - 0.05) * math.sin(a) * (1.0 if style == 'round' else 1.12)))
        prev = None
        for (bx, bz) in band:
            if prev is not None:
                # quad strip of a 0.12 thick band, 0.06 proud
                p0 = prev; p1 = (bx, bz)
                dx, dz = p1[0] - p0[0], p1[1] - p0[1]
                L = math.hypot(dx, dz) or 1.0
                nx, nz = -dz / L * 0.12, dx / L * 0.12
                q = [bm.verts.new((p0[0], proud + 0.05, p0[1])), bm.verts.new((p1[0], proud + 0.05, p1[1])),
                     bm.verts.new((p1[0] + nx, proud + 0.05, p1[1] + nz)), bm.verts.new((p0[0] + nx, proud + 0.05, p0[1] + nz))]
                trim_faces.append(bm.faces.new(q))
                q2 = [bm.verts.new((p0[0], proud, p0[1])), bm.verts.new((p1[0], proud, p1[1])),
                      bm.verts.new((p1[0], proud + 0.05, p1[1])), bm.verts.new((p0[0], proud + 0.05, p0[1]))]
                trim_faces.append(bm.faces.new(q2))
            prev = (bx, bz)
    # tracery bars (lead/stone) just in front of the glass
    bar = 0.09
    yb = -depth + 0.10
    if tracery and glass and kind != "slit":
        if lights >= 2:
            for i in range(1, lights):
                xm = -w / 2 + w * i / lights
                bm_box(bm, (bar, bar, h * 0.62), (xm, yb, h * 0.31))
            if style == "lancet":
                # Y-tracery: from each mullion top, two bars up into the arch
                for i in range(1, lights):
                    xm = -w / 2 + w * i / lights
                    for sgn in (-1, 1):
                        ang = math.radians(28) * sgn
                        L = h * 0.30
                        bx = xm + math.sin(ang) * L / 2; bz = h * 0.62 + math.cos(ang) * L / 2
                        vs = bm_box(bm, (bar, bar, L), (bx, yb, bz))
                        mrot = Matrix.Translation(Vector((bx, yb, bz))) @ Matrix.Rotation(-ang, 4, 'Y') @ Matrix.Translation(Vector((-bx, -yb, -bz)))
                        bmesh.ops.transform(bm, matrix=mrot, verts=vs)
        if transom and h > 1.6:
            zt = h * (0.55 if lights >= 2 else 0.5)
            bm_box(bm, (w, bar, bar), (0.0, yb, zt))
            if h > 5.0:
                bm_box(bm, (w, bar, bar), (0.0, yb, h * 0.28))
        # leaded-light lattice: thin vertical & horizontal ribs
        if w > 0.6:
            nv = max(1, int(w / 0.42))
            for i in range(1, nv):
                xm = -w / 2 + w * i / nv
                bm_box(bm, (0.03, 0.03, h * 0.98), (xm, yb - 0.03, h * 0.49))
            nh = max(1, int(h / 0.45))
            for i in range(1, nh):
                zm = h * i / nh
                bm_box(bm, (w, 0.03, 0.03), (0.0, yb - 0.03, zm))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    me = bpy.data.meshes.new(f"WinUnit_{kind}_{w:.2f}x{h:.2f}_{lights}")
    # materials: 0 stone trim, 1 glass, 2 lead bars
    for f in bm.faces:
        f.material_index = 0
    for f in glass_faces:
        f.material_index = 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # flip glass to face outward (+Y)
    for f in glass_faces:
        if f.normal.y < 0:
            f.normal_flip()
    bm.to_mesh(me); bm.free()
    me.materials.append(bpy.data.materials.get(MAT_TRIM) or H.ensure_material(MAT_TRIM, (0.6, 0.56, 0.5, 1)))
    me.materials.append(bpy.data.materials.get(MAT_GLASS) or H.ensure_material(MAT_GLASS, (0.9, 0.7, 0.4, 1)))
    # bars share the trim material (index 0) except we tint via a third slot for lead
    me.materials.append(bpy.data.materials.get(MAT_LEAD) or H.ensure_material(MAT_LEAD, (0.3, 0.3, 0.33, 1)))
    # assign bar faces (all faces with |y| near yb) to lead
    for p in me.polygons:
        c = me.vertices[p.vertices[0]].co
        if abs(c.y - (-depth + 0.10)) < 0.08 or abs(c.y - (-depth + 0.07)) < 0.05:
            p.material_index = 2
    _unit_cache[key] = me
    return me

def place_window(me, pos, normal, coll, glow, warmth, name="Win", scale=1.0):
    """Instance a window unit mesh at world pos (sill centre) facing *normal* (2D)."""
    ob = bpy.data.objects.new(name, me)
    H.link_obj(ob, coll)
    ang = math.atan2(normal[1], normal[0]) - math.pi / 2   # local +Y -> normal
    ob.matrix_world = Matrix.Translation(Vector(pos)) @ Matrix.Rotation(ang, 4, 'Z') @ Matrix.Scale(scale, 4)
    ob.color = (glow, warmth, 0.0, 1.0)
    return ob

def glow_pick(rng, lit_prob=0.55):
    """Return (glow, warmth) for a window: most dark or dim, some bright."""
    if rng.random() > lit_prob:
        return (0.0, rng.random())
    u = rng.random()
    if u < 0.45:
        g = 0.25 + 0.3 * rng.random()
    elif u < 0.85:
        g = 0.55 + 0.35 * rng.random()
    else:
        g = 1.0 + 0.6 * rng.random()
    return (g, rng.random())

# --------------------------------------------------------------------------- lattice faces
def _partition_face(bm, origin, udir, vdir, Lu, v0, v1, holes, flip=False):
    """Quad-partitioned planar face. origin: 3D point at (u=0, v=v0) ... vdir is Z usually.
    holes: list of (u0, u1, v0, v1) in face coords (u along udir, v absolute along vdir)."""
    us = {0.0, Lu}; vs = {v0, v1}
    for (a, b, c, d) in holes:
        us.update((max(0.0, a), min(Lu, b))); vs.update((max(v0, c), min(v1, d)))
    us = sorted(us); vs = sorted(vs)
    ox, oy, oz = origin
    ux, uy, uz = udir
    wx, wy, wz = vdir
    grid = {}
    def V(u, v):
        key = (round(u, 5), round(v, 5))
        if key not in grid:
            grid[key] = bm.verts.new((ox + ux * u + wx * (v - v0), oy + uy * u + wy * (v - v0), oz + uz * u + wz * (v - v0)))
        return grid[key]
    faces = []
    for i in range(len(us) - 1):
        for j in range(len(vs) - 1):
            cu = (us[i] + us[i + 1]) / 2; cv = (vs[j] + vs[j + 1]) / 2
            if any(a <= cu <= b and c <= cv <= d for (a, b, c, d) in holes):
                continue
            q = (V(us[i], vs[j]), V(us[i + 1], vs[j]), V(us[i + 1], vs[j + 1]), V(us[i], vs[j + 1]))
            if flip:
                q = tuple(reversed(q))
            try:
                faces.append(bm.faces.new(q))
            except ValueError:
                pass
    return faces

def wall_box_with_windows(bm, x0, x1, y0, y1, zb, zt, windows):
    """Closed box; each side face may carry rectangular holes.
    windows: list of dicts {side: 'S'|'N'|'E'|'W', s: along-face pos from the face start (CCW seen from above),
             z: sill z, w: hole width, h: hole height}.
    Returns the list of (pos3d, normal2d, w, h, dict) for window placement."""
    placements = []
    sides = {
        'S': ((x0, y0, zb), (1, 0, 0), x1 - x0, (0, -1)),
        'E': ((x1, y0, zb), (0, 1, 0), y1 - y0, (1, 0)),
        'N': ((x1, y1, zb), (-1, 0, 0), x1 - x0, (0, 1)),
        'W': ((x0, y1, zb), (0, -1, 0), y1 - y0, (-1, 0)),
    }
    for side, (origin, udir, Lu, nrm) in sides.items():
        holes = []
        for wdef in windows:
            if wdef["side"] != side:
                continue
            u0 = wdef["s"] - wdef["w"] / 2; u1 = wdef["s"] + wdef["w"] / 2
            if u0 < 0.05 or u1 > Lu - 0.05 or wdef["z"] < zb + 0.05 or wdef["z"] + wdef["h"] > zt - 0.05:
                continue
            holes.append((u0, u1, wdef["z"], wdef["z"] + wdef["h"]))
            pos = (origin[0] + udir[0] * wdef["s"], origin[1] + udir[1] * wdef["s"], wdef["z"])
            placements.append((pos, nrm, wdef))
        _partition_face(bm, origin, udir, (0, 0, 1), Lu, zb, zt, holes)
    # top & bottom
    vb = [bm.verts.new(p) for p in ((x0, y0, zb), (x1, y0, zb), (x1, y1, zb), (x0, y1, zb))]
    vt = [bm.verts.new(p) for p in ((x0, y0, zt), (x1, y0, zt), (x1, y1, zt), (x0, y1, zt))]
    bm.faces.new(list(reversed(vb)))
    bm.faces.new(vt)
    return placements

def cylinder_with_windows(bm, cx, cy, r, zb, zt, segs, windows, cap_top=True, cap_bottom=True, phase=0.0):
    """Cylinder side as a lattice; windows = list of dicts {seg: start segment, n: segments, z, h}.
    Returns placements (pos, normal2d, wdef)."""
    zs = {zb, zt}
    for w in windows:
        zs.update((w["z"], w["z"] + w["h"]))
    zs = sorted(zs)
    rings = []
    for z in zs:
        rings.append([bm.verts.new((cx + r * math.cos(phase + 2 * math.pi * k / segs), cy + r * math.sin(phase + 2 * math.pi * k / segs), z)) for k in range(segs)])
    holes = set()
    placements = []
    for w in windows:
        for k in range(w["seg"], w["seg"] + w["n"]):
            for j in range(len(zs) - 1):
                if zs[j] >= w["z"] - 1e-6 and zs[j + 1] <= w["z"] + w["h"] + 1e-6:
                    holes.add((k % segs, j))
        a = phase + 2 * math.pi * (w["seg"] + w["n"] / 2) / segs
        # chord mid-point (slightly inside the circle)
        rc = r * math.cos(math.pi * w["n"] / segs)
        placements.append(((cx + rc * math.cos(a), cy + rc * math.sin(a), w["z"]), (math.cos(a), math.sin(a)), w))
    for j in range(len(zs) - 1):
        for k in range(segs):
            if (k, j) in holes:
                continue
            k2 = (k + 1) % segs
            bm.faces.new((rings[j][k], rings[j][k2], rings[j + 1][k2], rings[j + 1][k]))
    if cap_bottom:
        bm.faces.new(list(reversed(rings[0])))
    if cap_top:
        bm.faces.new(rings[-1])
    return placements

# --------------------------------------------------------------------------- gothic pieces
def corbel_ring(bm, cx, cy, r, z, n, size=0.45, depth=0.55, phase=0.0):
    """Ring of corbel blocks projecting from a round wall (machicolation supports)."""
    for i in range(n):
        a = phase + 2 * math.pi * i / n
        px, py = cx + (r + depth / 2 - 0.05) * math.cos(a), cy + (r + depth / 2 - 0.05) * math.sin(a)
        vs = bm_box(bm, (depth, size, size * 1.3), (px, py, z))
        m = Matrix.Translation(Vector((px, py, z))) @ Matrix.Rotation(a, 4, 'Z') @ Matrix.Translation(Vector((-px, -py, -z)))
        bmesh.ops.transform(bm, matrix=m, verts=vs)

def corbel_line(bm, p0, p1, z, nrm, pitch=1.1, size=0.4, depth=0.5):
    x0, y0 = p0; x1, y1 = p1
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    n = max(1, int(L / pitch))
    for i in range(n):
        s = (i + 0.5) * L / n
        px, py = x0 + ux * s + nrm[0] * depth / 2, y0 + uy * s + nrm[1] * depth / 2
        vs = bm_box(bm, (size, depth, size * 1.2), (px, py, z))
        ang = math.atan2(uy, ux)
        m = Matrix.Translation(Vector((px, py, z))) @ Matrix.Rotation(ang, 4, 'Z') @ Matrix.Translation(Vector((-px, -py, -z)))
        bmesh.ops.transform(bm, matrix=m, verts=vs)

def pinnacle(bm, x, y, z0, base=0.7, h=3.2):
    """Octagonal pinnacle with a tapering spirelet and finial."""
    pts = H.circle_pts(x, y, base / 2, 8, phase=math.pi / 8)
    bm_prism(bm, pts, z0, z0 + h * 0.4)
    bm_prism(bm, H.circle_pts(x, y, base / 2 + 0.08, 8, phase=math.pi / 8), z0 + h * 0.4, z0 + h * 0.46)
    bm_cone(bm, base / 2 + 0.02, z0 + h * 0.46, z0 + h, 8, center=(x, y))
    bm_cylinder(bm, 0.05, z0 + h - 0.2, z0 + h + 0.5, 6, center=(x, y))
    bm_cylinder(bm, 0.14, z0 + h + 0.25, z0 + h + 0.4, 6, center=(x, y), r_top=0.02)

def buttress(bm, x, y, nrm, zb, z_top, w=1.3, d0=1.8, steps=3, cap=True):
    """Stepped buttress projecting along nrm from the wall plane at (x, y)."""
    nx, ny = nrm
    ang = math.atan2(ny, nx)
    for i in range(steps):
        t0 = zb if i == 0 else z_top - (z_top - zb) * (1.0 - i / steps) * 0.9
        depth = d0 * (1.0 - 0.28 * i)
        z1 = z_top if i == steps - 1 else z_top - (z_top - zb) * (1.0 - (i + 1) / steps) * 0.9
        px, py = x + nx * (depth / 2 - 0.15), y + ny * (depth / 2 - 0.15)
        vs = bm_box(bm, (w - 0.1 * i, depth, z1 - t0), (px, py, (t0 + z1) / 2))
        m = Matrix.Translation(Vector((px, py, 0))) @ Matrix.Rotation(ang - math.pi / 2, 4, 'Z') @ Matrix.Translation(Vector((-px, -py, 0)))
        bmesh.ops.transform(bm, matrix=m, verts=vs)
        # sloped weathering (a wedge) at each step top
        if i < steps - 1:
            wz = z1
            wd = depth - d0 * (1.0 - 0.28 * (i + 1))
            px2, py2 = x + nx * (depth - wd / 2 - 0.15), y + ny * (depth - wd / 2 - 0.15)
            vs = bm_box(bm, (w - 0.1 * i, wd, 0.5), (px2, py2, wz + 0.25))
            m = Matrix.Translation(Vector((px2, py2, 0))) @ Matrix.Rotation(ang - math.pi / 2, 4, 'Z') @ Matrix.Translation(Vector((-px2, -py2, 0)))
            bmesh.ops.transform(bm, matrix=m, verts=vs)
    if cap:
        pinnacle(bm, x + nx * (d0 * (1.0 - 0.28 * (steps - 1)) / 2 - 0.15), y + ny * (d0 * (1.0 - 0.28 * (steps - 1)) / 2 - 0.15), z_top, base=w * 0.7, h=2.6 + 0.6 * w)

def flying_buttress(bm, x, y, nrm, zb, z_pier_top, z_wall, reach=5.0, w=1.0):
    """Outer pier at *reach* from the wall plus a sloping strut (with a pointed arch underneath)
    landing on the wall at z_wall.  nrm points away from the wall."""
    nx, ny = nrm
    px, py = x + nx * reach, y + ny * reach
    # pier with pinnacle
    bm_box(bm, (w, w, z_pier_top - zb), (px, py, (zb + z_pier_top) / 2))
    pinnacle(bm, px, py, z_pier_top, base=w * 0.8, h=3.0)
    # strut: box from the pier top to the wall, tilted
    ax, ay, az = px - nx * w * 0.3, py - ny * w * 0.3, z_pier_top - 0.3
    bx, by, bz = x + nx * 0.3, y + ny * 0.3, z_wall
    L = math.sqrt((bx - ax) ** 2 + (by - ay) ** 2 + (bz - az) ** 2)
    mx, my, mz = (ax + bx) / 2, (ay + by) / 2, (az + bz) / 2
    vs = bm_box(bm, (L, w * 0.7, 0.9), (mx, my, mz))
    d = Vector((bx - ax, by - ay, bz - az)).normalized()
    rot = d.to_track_quat('X', 'Z').to_matrix().to_4x4()
    m = Matrix.Translation(Vector((mx, my, mz))) @ rot @ Matrix.Translation(Vector((-mx, -my, -mz)))
    bmesh.ops.transform(bm, matrix=m, verts=vs)
    # arch under the strut: a quarter arc of small blocks from the pier to the wall
    n = 6
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n
        a0, a1 = math.pi / 2 * t0, math.pi / 2 * t1
        r = reach - w * 0.6
        p0 = (px - nx * (r - r * math.cos(a0)) - nx * w * 0.3, py - ny * (r - r * math.cos(a0)) - ny * w * 0.3, z_pier_top - 0.6 - (r * 0.8) * (1 - math.sin(a0)))
        p1 = (px - nx * (r - r * math.cos(a1)) - nx * w * 0.3, py - ny * (r - r * math.cos(a1)) - ny * w * 0.3, z_pier_top - 0.6 - (r * 0.8) * (1 - math.sin(a1)))
        seg = math.dist(p0, p1)
        cxk, cyk, czk = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, (p0[2] + p1[2]) / 2
        vs = bm_box(bm, (seg + 0.05, w * 0.6, 0.5), (cxk, cyk, czk))
        d = Vector((p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])).normalized()
        rot = d.to_track_quat('X', 'Z').to_matrix().to_4x4()
        m = Matrix.Translation(Vector((cxk, cyk, czk))) @ rot @ Matrix.Translation(Vector((-cxk, -cyk, -czk)))
        bmesh.ops.transform(bm, matrix=m, verts=vs)

def string_course_box(bm, x0, x1, y0, y1, z, proud=0.22, h=0.32):
    bm_box_zrange(bm, x0 - proud, x1 + proud, y0 - proud, y1 + proud, z, z + h)

def dormer(bm, x, y, z_base, nrm, w=1.6, h=2.2, depth=1.6):
    """Small gabled dormer (lucarne) sitting on a roof slope, facing nrm."""
    nx, ny = nrm
    ang = math.atan2(ny, nx) + math.pi / 2
    def T(vs):
        m = Matrix.Translation(Vector((x, y, z_base))) @ Matrix.Rotation(ang, 4, 'Z') @ Matrix.Translation(Vector((-x, -y, -z_base)))
        bmesh.ops.transform(bm, matrix=m, verts=vs)
    # body: box from inside the roof out to the face
    vs = bm_box(bm, (w, depth, h), (x, y - depth / 2 + 0.1, z_base + h / 2))
    T(vs)
    # gable roof on top
    vb = [bm.verts.new(p) for p in ((x - w / 2 - 0.15, y - depth + 0.1, z_base + h), (x + w / 2 + 0.15, y - depth + 0.1, z_base + h),
                                    (x + w / 2 + 0.15, y + 0.25, z_base + h), (x - w / 2 - 0.15, y + 0.25, z_base + h))]
    ra = bm.verts.new((x, y - depth + 0.1, z_base + h + w * 0.7)); rb = bm.verts.new((x, y + 0.25, z_base + h + w * 0.7))
    fs = [bm.faces.new((vb[0], vb[1], ra)), bm.faces.new((vb[1], vb[2], rb, ra)), bm.faces.new((vb[2], vb[3], rb)), bm.faces.new((vb[3], vb[0], ra, rb))]
    T(vb + [ra, rb])
    return (x + nx * (depth - 0.1) * 0.0, y, z_base)   # window centre computed by caller

def lantern_mesh(bm, x, y, z, size=0.42):
    """Open-frame hanging lantern: four corner rods, a pyramidal cap and a base plate.
    The emissive glass block and the point light are added by the light pass at (x, y, z)."""
    h = size * 1.3
    for sx in (-1, 1):
        for sy in (-1, 1):
            bm_box(bm, (0.035, 0.035, h), (x + sx * size * 0.5, y + sy * size * 0.5, z))
    bm_box(bm, (size + 0.08, size + 0.08, 0.05), (x, y, z - h / 2))
    bm_box(bm, (size + 0.08, size + 0.08, 0.05), (x, y, z + h / 2))
    bm_cone(bm, size * 0.85, z + h / 2 + 0.03, z + h / 2 + 0.28, 4, center=(x, y))
    bm_cylinder(bm, 0.03, z + h / 2 + 0.25, z + h / 2 + 0.55, 6, center=(x, y))
    bm_cylinder(bm, 0.08, z + h / 2 + 0.5, z + h / 2 + 0.6, 6, center=(x, y))
