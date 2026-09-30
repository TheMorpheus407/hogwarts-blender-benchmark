"""Face-soup geometry kit.

Conventions
-----------
* Metres, Z up.  Faces are quads / triangles with counter-clockwise winding seen from outside.
* Prototypes (windows etc.) are authored on a SOUTH-facing wall: wall plane y = 0, outward = -y,
  screen-right = +x, up = +z, the building interior is +y.  `Geo.add_geo(..., outward=(ox,oy))` turns it.
* Lathe / sweep profiles are (offset, height) polylines traversed with the solid on the LEFT
  (i.e. counter-clockwise for closed profiles, bottom -> top for walls).
"""
import numpy as np
import math

F32 = np.float32
UPV = np.array([0.0, 0.0, 1.0])
WIN_STATS = {'total': 0, 'lit': 0}
ATTRS = ('glow', 'hue', 'seed')


def _arr(x):
    return np.asarray(x, dtype=np.float64)


def rotz(P, ang):
    P = _arr(P)
    ang = _arr(ang)
    c = np.cos(ang)
    s = np.sin(ang)
    while c.ndim < P.ndim - 1:
        c = c[..., None]
        s = s[..., None]
    x = P[..., 0] * c - P[..., 1] * s
    y = P[..., 0] * s + P[..., 1] * c
    return np.stack([x, y, P[..., 2]], axis=-1)


def xf(P, pos=(0, 0, 0), yaw=0.0, scale=1.0):
    P = _arr(P) * scale
    if np.any(np.asarray(yaw) != 0):
        P = rotz(P, yaw)
    return P + _arr(pos)


def yaw_for_outward(ox, oy):
    """Yaw that turns a south-facing prototype so that it faces (ox, oy)."""
    return math.atan2(ox, -oy)


def normalize(v, eps=1e-12):
    v = _arr(v)
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), eps)


def frame_quad(c, r, u, hw, hh):
    """Quad(s) centred at c spanned by unit axes r,u.  CCW seen from the side r x u points to."""
    c = _arr(c)
    r = _arr(r)
    u = _arr(u)
    hw = _arr(hw)[..., None]
    hh = _arr(hh)[..., None]
    A = r * hw
    B = u * hh
    return np.stack([c - A - B, c + A - B, c + A + B, c - A + B], axis=-2)


# --------------------------------------------------------------------------------------
# polygon triangulation (ear clipping, small n)
# --------------------------------------------------------------------------------------

def triangulate_polygon(pts2):
    """pts2: (n,2) CCW polygon -> list of (i,j,k) index triples."""
    pts2 = _arr(pts2)
    n = len(pts2)
    idx = list(range(n))
    tris = []
    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1
        ear = False
        for a in range(len(idx)):
            i0, i1, i2 = idx[a - 1], idx[a], idx[(a + 1) % len(idx)]
            p0, p1, p2 = pts2[i0], pts2[i1], pts2[i2]
            cross = (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0])
            if cross <= 1e-12:
                continue
            ok = True
            for k in idx:
                if k in (i0, i1, i2):
                    continue
                q = pts2[k]
                d1 = (p1[0] - p0[0]) * (q[1] - p0[1]) - (p1[1] - p0[1]) * (q[0] - p0[0])
                d2 = (p2[0] - p1[0]) * (q[1] - p1[1]) - (p2[1] - p1[1]) * (q[0] - p1[0])
                d3 = (p0[0] - p2[0]) * (q[1] - p2[1]) - (p0[1] - p2[1]) * (q[0] - p2[0])
                if d1 >= -1e-12 and d2 >= -1e-12 and d3 >= -1e-12:
                    ok = False
                    break
            if ok:
                tris.append((i0, i1, i2))
                idx.pop(a)
                ear = True
                break
        if not ear:
            break
    if len(idx) == 3:
        tris.append((idx[0], idx[1], idx[2]))
    return tris


class Geo:
    """Accumulates faces; `to_object` turns them into one Blender mesh object."""

    def __init__(self, name, mats=None):
        self.name = name
        self.mats = list(mats or [])
        self.c4 = []
        self.c3 = []

    # ------------------------------------------------------------------ materials
    def mid(self, m):
        if isinstance(m, str):
            if m not in self.mats:
                self.mats.append(m)
            return self.mats.index(m)
        return int(m)

    # ------------------------------------------------------------------ raw add
    def add(self, P, m=0, uv=None, n=None, a=None):
        """P: (N,4,3) quads or (N,3,3) tris (any leading shape is flattened)."""
        P = _arr(P)
        k = P.shape[-2]
        P = P.reshape(-1, k, 3)
        N = P.shape[0]
        if N == 0:
            return
        if isinstance(m, str):
            m = self.mid(m)
        m = np.broadcast_to(np.asarray(m, dtype=np.int32), (N,)).copy()
        ch = {'P': P.astype(F32), 'm': m, 'UV': None, 'N': None, 'a': {}}
        if uv is not None:
            ch['UV'] = _arr(uv).reshape(N, k, 2).astype(F32)
        if n is not None:
            ch['N'] = _arr(n).reshape(N, k, 3).astype(F32)
        if a:
            for key, val in a.items():
                ch['a'][key] = np.broadcast_to(np.asarray(val, dtype=F32), (N,)).copy()
        (self.c4 if k == 4 else self.c3).append(ch)

    def add_quads(self, P, m=0, uv=None, n=None, a=None, eps=1e-6):
        """Quads that may contain degenerate (collapsed) edges: split into tris where needed."""
        P = _arr(P).reshape(-1, 4, 3)
        if isinstance(m, str):
            m = self.mid(m)
        N = len(P)
        marr = np.broadcast_to(np.asarray(m, dtype=np.int32), (N,))
        uvv = None if uv is None else _arr(uv).reshape(N, 4, 2)
        nn = None if n is None else _arr(n).reshape(N, 4, 3)
        aa = {}
        if a:
            for key, val in a.items():
                aa[key] = np.broadcast_to(np.asarray(val, dtype=F32), (N,))
        dAB = np.linalg.norm(P[:, 0] - P[:, 1], axis=1) < eps
        dBC = np.linalg.norm(P[:, 1] - P[:, 2], axis=1) < eps
        dCD = np.linalg.norm(P[:, 2] - P[:, 3], axis=1) < eps
        dDA = np.linalg.norm(P[:, 3] - P[:, 0], axis=1) < eps
        deg = dAB | dBC | dCD | dDA
        ok = ~deg
        if ok.any():
            self.add(P[ok], marr[ok], None if uvv is None else uvv[ok], None if nn is None else nn[ok],
                     {k: v[ok] for k, v in aa.items()})
        # degenerate ones -> triangles
        for mask, idx in ((dAB & ~dCD & ~dBC & ~dDA, (0, 2, 3)), (dCD & ~dAB & ~dBC & ~dDA, (0, 1, 2)),
                          (dBC & ~dAB & ~dCD & ~dDA, (0, 1, 3)), (dDA & ~dAB & ~dCD & ~dBC, (0, 1, 2))):
            if mask.any():
                self.add(P[mask][:, idx], marr[mask], None if uvv is None else uvv[mask][:, idx],
                         None if nn is None else nn[mask][:, idx], {k: v[mask] for k, v in aa.items()})

    def add_geo(self, other, pos=(0, 0, 0), yaw=0.0, scale=1.0, outward=None, attrs=None, lit=None,
                rng=None, glass_mat='M_GlassLit'):
        """Instance another Geo (a prototype).  `outward=(ox,oy)` overrides yaw for south-facing prototypes.

        Glass chunks whose glow == -1 are replaced by per-pane random values from `lit` = (base, hue) or None (dark).
        """
        if outward is not None:
            yaw = yaw_for_outward(outward[0], outward[1])
        remap = {i: self.mid(name) for i, name in enumerate(other.mats)}
        lut = np.zeros(max(len(other.mats), 1), dtype=np.int32)
        for i, j in remap.items():
            lut[i] = j
        rng = rng or np.random.default_rng()
        if any(('glow' in ch['a'] and np.all(ch['a']['glow'] < -0.5)) for ch in other.c4 + other.c3):
            WIN_STATS['total'] += 1
            if lit is not None:
                WIN_STATS['lit'] += 1
        for src, dst in ((other.c4, self.c4), (other.c3, self.c3)):
            for ch in src:
                P = xf(ch['P'], pos, yaw, scale).astype(F32)
                N = None
                if ch['N'] is not None:
                    N = rotz(ch['N'], yaw).astype(F32) if yaw != 0 else ch['N']
                a = dict(ch['a'])
                pane = a.pop('pane', None)
                if 'glow' in a and np.all(a['glow'] < -0.5):
                    cnt = len(ch['P'])
                    if pane is None:
                        pane = np.zeros(cnt, dtype=F32)
                    up, inv = np.unique(pane, return_inverse=True)
                    if lit is None:
                        gl = np.zeros(cnt, dtype=F32)
                        hu = np.zeros(cnt, dtype=F32)
                    else:
                        base, hue = lit
                        gl = (base * (0.55 + 0.45 * rng.random(len(up))))[inv].astype(F32)
                        hu = np.clip(hue + 0.06 * (rng.random(len(up)) - 0.5), 0, 1)[inv].astype(F32)
                    a['glow'] = gl
                    a['hue'] = hu
                    a['seed'] = rng.random(len(up))[inv].astype(F32)
                if attrs:
                    for key, val in attrs.items():
                        a[key] = np.broadcast_to(np.asarray(val, dtype=F32), (len(ch['P']),)).copy()
                dst.append({'P': P, 'm': lut[ch['m']].astype(np.int32), 'UV': ch['UV'], 'N': N, 'a': a})


    def consolidate(self):
        """Merge chunks that share material / attribute signature (keeps 'pane' ids)."""
        for attr in ('c4', 'c3'):
            chunks = getattr(self, attr)
            if len(chunks) <= 1:
                continue
            groups = {}
            for ch in chunks:
                for mi in np.unique(ch['m']):
                    pass
                sig = (ch['UV'] is not None, ch['N'] is not None, tuple(sorted(ch['a'].keys())))
                groups.setdefault(sig, []).append(ch)
            out = []
            for sig, lst in groups.items():
                P = np.concatenate([c['P'] for c in lst])
                m = np.concatenate([c['m'] for c in lst])
                UV = np.concatenate([c['UV'] for c in lst]) if sig[0] else None
                N = np.concatenate([c['N'] for c in lst]) if sig[1] else None
                a = {k: np.concatenate([c['a'][k] for c in lst]) for k in sig[2]}
                out.append({'P': P, 'm': m, 'UV': UV, 'N': N, 'a': a})
            setattr(self, attr, out)
        return self

    def merge(self, other):
        self.add_geo(other)

    def count(self):
        return sum(len(c['P']) for c in self.c4), sum(len(c['P']) for c in self.c3)

    def bounds(self):
        allp = [c['P'].reshape(-1, 3) for c in self.c4 + self.c3]
        if not allp:
            return None
        A = np.concatenate(allp)
        return A.min(0), A.max(0)

    # ------------------------------------------------------------------ build
    def _concat(self, chunks, k):
        if not chunks:
            return (np.zeros((0, k, 3), F32), np.zeros((0,), np.int32), np.zeros((0, k, 2), F32),
                    np.zeros((0, k, 3), F32), np.zeros((0,), bool), np.zeros((0,), bool), {})
        P = np.concatenate([c['P'] for c in chunks])
        m = np.concatenate([c['m'] for c in chunks])
        UVs, Ns, hasUV, hasN = [], [], [], []
        atts = {}
        for c in chunks:
            n = len(c['P'])
            UVs.append(c['UV'] if c['UV'] is not None else np.zeros((n, k, 2), F32))
            hasUV.append(np.full(n, c['UV'] is not None))
            Ns.append(c['N'] if c['N'] is not None else np.zeros((n, k, 3), F32))
            hasN.append(np.full(n, c['N'] is not None))
            for key in c['a']:
                atts.setdefault(key, None)
        outatt = {key: [] for key in atts}
        for c in chunks:
            n = len(c['P'])
            for key in outatt:
                outatt[key].append(c['a'].get(key, np.zeros(n, F32)))
        outatt = {k2: np.concatenate(v) for k2, v in outatt.items()}
        return P, m, np.concatenate(UVs), np.concatenate(Ns), np.concatenate(hasUV), np.concatenate(hasN), outatt

    def to_object(self, bpy, coll, name=None, smooth_default=False):
        name = name or self.name
        P4, m4, uv4, n4, hu4, hn4, a4 = self._concat(self.c4, 4)
        P3, m3, uv3, n3, hu3, hn3, a3 = self._concat(self.c3, 3)
        nq, nt = len(P4), len(P3)
        V = np.concatenate([P4.reshape(-1, 3), P3.reshape(-1, 3)]).astype(F32)
        nl = nq * 4 + nt * 3
        nf = nq + nt
        # face normals (flat) + auto UV
        fn4 = np.cross(P4[:, 2] - P4[:, 0], P4[:, 3] - P4[:, 1]) if nq else np.zeros((0, 3), F32)
        fn3 = np.cross(P3[:, 1] - P3[:, 0], P3[:, 2] - P3[:, 0]) if nt else np.zeros((0, 3), F32)
        fn4 = fn4 / np.maximum(np.linalg.norm(fn4, axis=1, keepdims=True), 1e-12)
        fn3 = fn3 / np.maximum(np.linalg.norm(fn3, axis=1, keepdims=True), 1e-12)

        def auto_uv(P, fn):
            """Wall: (along-wall, z).  Slope: (along-eave, up-slope).  Flat: (x, y)."""
            if len(P) == 0:
                return np.zeros((0, P.shape[1], 2), F32)
            nz = fn[:, 2]
            up = np.array([0, 0, 1.0])
            vdir = up[None, :] - nz[:, None] * fn
            ln = np.linalg.norm(vdir, axis=1, keepdims=True)
            flat = (np.abs(nz) > 0.985)[:, None]
            vdir = np.where(ln > 1e-6, vdir / np.maximum(ln, 1e-9), np.array([0, 1.0, 0]))
            right = np.cross(vdir, fn)
            u = np.einsum('nkc,nc->nk', P, right)
            v = np.einsum('nkc,nc->nk', P, vdir)
            u = np.where(flat, P[..., 0], u)
            v = np.where(flat, P[..., 1], v)
            return np.stack([u, v], axis=-1).astype(F32)

        if nq:
            au = auto_uv(P4, fn4)
            uv4 = np.where(hu4[:, None, None], uv4, au)
        if nt:
            au = auto_uv(P3, fn3)
            uv3 = np.where(hu3[:, None, None], uv3, au)
        mesh = bpy.data.meshes.new(name)
        mesh.vertices.add(len(V))
        mesh.vertices.foreach_set('co', V.ravel())
        mesh.loops.add(nl)
        mesh.loops.foreach_set('vertex_index', np.arange(nl, dtype=np.int32))
        mesh.polygons.add(nf)
        starts = np.concatenate([np.arange(nq, dtype=np.int32) * 4, nq * 4 + np.arange(nt, dtype=np.int32) * 3])
        totals = np.concatenate([np.full(nq, 4, np.int32), np.full(nt, 3, np.int32)])
        mesh.polygons.foreach_set('loop_start', starts)
        mesh.polygons.foreach_set('loop_total', totals)
        mesh.update(calc_edges=True)
        # materials
        for mn in self.mats:
            mat = bpy.data.materials.get(mn)
            if mat is None:
                mat = bpy.data.materials.new(mn)
            mesh.materials.append(mat)
        mesh.polygons.foreach_set('material_index', np.concatenate([m4, m3]).astype(np.int32))
        # UVs
        uvl = mesh.uv_layers.new(name='UVMap')
        uvl.data.foreach_set('uv', np.concatenate([uv4.reshape(-1, 2), uv3.reshape(-1, 2)]).ravel())
        # face attributes
        names = set(a4) | set(a3)
        for key in names:
            arr = np.concatenate([a4.get(key, np.zeros(nq, F32)), a3.get(key, np.zeros(nt, F32))]).astype(F32)
            att = mesh.attributes.new(key, 'FLOAT', 'FACE')
            att.data.foreach_set('value', arr)
        # custom split normals where provided
        anyN = (nq and hn4.any()) or (nt and hn3.any())
        if anyN:
            Nq = np.where(hn4[:, None, None], n4, fn4[:, None, :]) if nq else np.zeros((0, 4, 3), F32)
            Nt = np.where(hn3[:, None, None], n3, fn3[:, None, :]) if nt else np.zeros((0, 3, 3), F32)
            NL = np.concatenate([Nq.reshape(-1, 3), Nt.reshape(-1, 3)]).astype(F32)
            ln = np.linalg.norm(NL, axis=1, keepdims=True)
            NL = NL / np.maximum(ln, 1e-9)
            mesh.normals_split_custom_set(NL)
        obj = bpy.data.objects.new(name, mesh)
        coll.objects.link(obj)
        return obj


# --------------------------------------------------------------------------------------
# oriented boxes
# --------------------------------------------------------------------------------------

def slab(g, quad, thick, m=0, hint=None, vertical=(), vdir=(0.0, 0.0, 1.0), edges=(1, 1, 1, 1), m_under=None, a=None):
    """Closed thin slab.  `quad` (4,3) is the top face, CCW seen from outside (flipped to face `hint` when given).

    The underside is the top shifted by `thick` against the normal; vertices listed in `vertical` (ridge edge of a
    roof plane) are shifted along `vdir` instead so two planes meeting at a ridge stay flush.  Side strips are
    added for every edge whose flag is set (edge i runs from vertex i to i+1).
    """
    Q = np.array(quad, dtype=float).reshape(4, 3)
    n = np.cross(Q[1] - Q[0], Q[3] - Q[0])
    n /= (np.linalg.norm(n) + 1e-12)
    vert = tuple(vertical)
    ed = tuple(edges)
    if hint is not None and float(np.dot(n, np.asarray(hint, float))) < 0:
        Q = Q[::-1].copy()
        n = -n
        vert = tuple(3 - i for i in vert)
        ed = tuple(ed[(2 - i) % 4] for i in range(4))          # edge i of the flipped quad = old edge 2 - i
    U = Q - n * thick
    if vert:
        vd = np.asarray(vdir, float)
        vd /= np.linalg.norm(vd)
        k = abs(float(np.dot(n, vd)))
        for i in vert:
            U[i] = Q[i] - vd * (thick / max(k, 1e-3))
    g.add(Q[None], m, a=a)
    g.add(U[::-1][None], m if m_under is None else m_under, a=a)
    for i in range(4):
        if not ed[i]:
            continue
        j = (i + 1) % 4
        g.add(np.array([Q[j], Q[i], U[i], U[j]])[None], m, a=a)


def obox(g, C, axes, S, m=0, faces=(0, 1, 2, 3, 4, 5), a=None, base=True):
    """Generic oriented boxes.  C (n,3) centre of the base (base=True) or the box centre,
    axes (n,3,3) rows = local x,y,z unit axes (right-handed), S (n,3) full sizes."""
    C = _arr(C).reshape(-1, 3)
    S = _arr(S).reshape(-1, 3)
    axes = _arr(axes)
    n = max(len(C), len(S), 1 if axes.ndim == 2 else len(axes))
    C = np.broadcast_to(C, (n, 3))
    S = np.broadcast_to(S, (n, 3))
    if axes.ndim == 2:
        axes = np.broadcast_to(axes, (n, 3, 3))
    H = S / 2.0
    cen = C + (axes[:, 2, :] * H[:, 2:3] if base else 0.0)
    ma = m
    for fi in faces:
        i, s = fi // 2, (1.0 if fi % 2 == 0 else -1.0)
        nn = axes[:, i, :] * s
        uu = axes[:, (i + 2) % 3, :]
        rr = np.cross(uu, nn)
        hw = H[:, (i + 1) % 3]
        hh = H[:, (i + 2) % 3]
        c = cen + nn * H[:, i:i + 1]
        g.add(frame_quad(c, rr, uu, hw, hh), ma, a=a)


def yaw_axes(yaw, n=1):
    yaw = np.broadcast_to(_arr(yaw), (n,)).copy()
    c, s = np.cos(yaw), np.sin(yaw)
    A = np.zeros((n, 3, 3))
    A[:, 0, 0] = c
    A[:, 0, 1] = s
    A[:, 1, 0] = -s
    A[:, 1, 1] = c
    A[:, 2, 2] = 1.0
    return A


def boxes(g, C, S, yaw=0.0, m=0, faces=(0, 1, 2, 3, 4, 5), a=None):
    """Batch of yaw-rotated boxes; C is the centre of the BASE (x,y,z0), S=(sx,sy,sz)."""
    C = _arr(C).reshape(-1, 3)
    S = _arr(S).reshape(-1, 3)
    n = max(len(C), len(S), np.size(yaw))
    A = yaw_axes(yaw, n)
    obox(g, np.broadcast_to(C, (n, 3)), A, np.broadcast_to(S, (n, 3)), m, faces, a, base=True)


def beams(g, P0, P1, w, h, m=0, up=(0, 0, 1), faces=(0, 1, 2, 3, 4, 5), a=None):
    """Rectangular beams between point pairs.  Local x = width axis, y = along the beam, z = height axis."""
    P0 = _arr(P0).reshape(-1, 3)
    P1 = _arr(P1).reshape(-1, 3)
    n = max(len(P0), len(P1))
    P0 = np.broadcast_to(P0, (n, 3))
    P1 = np.broadcast_to(P1, (n, 3))
    d = P1 - P0
    L = np.linalg.norm(d, axis=1)
    ax = d / np.maximum(L[:, None], 1e-9)
    upv = np.broadcast_to(_arr(up), (n, 3)).copy()
    par = np.abs(np.einsum('nc,nc->n', ax, upv)) > 0.98
    upv[par] = np.array([1.0, 0, 0])
    xa = np.cross(ax, upv)
    xa = xa / np.maximum(np.linalg.norm(xa, axis=1, keepdims=True), 1e-9)
    za = np.cross(xa, ax)
    A = np.stack([xa, ax, za], axis=1)  # x,y,z right-handed? x × y = z  -> xa × ax = -(ax × xa) ... fix sign
    # ensure right-handed
    hand = np.einsum('nc,nc->n', np.cross(A[:, 0], A[:, 1]), A[:, 2])
    A[hand < 0, 2] *= -1
    S = np.stack([np.broadcast_to(_arr(w), (n,)), L, np.broadcast_to(_arr(h), (n,))], axis=1)
    obox(g, (P0 + P1) / 2.0, A, S, m, faces, a, base=False)


# --------------------------------------------------------------------------------------
# rings / lofts / lathe / sweep
# --------------------------------------------------------------------------------------

def loft(g, rings, closed=True, m=0, smooth=False, uv_v='z', a=None, uv_u_scale=1.0, flip=False,
         crease_deg=None):
    """rings (k,n,3): k rings (bottom->top) of n points (CCW from above).  Returns nothing."""
    R = _arr(rings)
    k, n = R.shape[:2]
    if flip:
        R = R[::-1]
    ja = np.arange(n if closed else n - 1)
    jb = (ja + 1) % n
    A = R[:-1][:, ja]
    B = R[:-1][:, jb]
    Cc = R[1:][:, jb]
    D = R[1:][:, ja]
    P = np.stack([A, B, Cc, D], axis=2)  # (k-1, nseg, 4, 3)
    # UV
    seg = np.linalg.norm(R[:, jb] - R[:, ja], axis=2)  # (k, nseg)
    U = np.concatenate([np.zeros((k, 1)), np.cumsum(seg, axis=1)], axis=1) * uv_u_scale  # (k, nseg+1)
    if uv_v == 'z':
        Vv = R[:, :, 2]
        Vj = np.concatenate([Vv[:, ja], Vv[:, jb][:, -1:]], axis=1)
    else:
        dz = np.linalg.norm(np.diff(R, axis=0), axis=2)
        Vv = np.concatenate([np.zeros((1, n)), np.cumsum(dz, axis=0)], axis=0)
        Vj = np.concatenate([Vv[:, ja], Vv[:, jb][:, -1:]], axis=1)
    uvA = np.stack([U[:-1, :-1], Vj[:-1, :-1]], axis=-1)
    uvB = np.stack([U[:-1, 1:], Vj[:-1, 1:]], axis=-1)
    uvC = np.stack([U[1:, 1:], Vj[1:, 1:]], axis=-1)
    uvD = np.stack([U[1:, :-1], Vj[1:, :-1]], axis=-1)
    UV = np.stack([uvA, uvB, uvC, uvD], axis=2)
    Nn = None
    if smooth:
        # vertex normals on the grid
        if closed:
            dj = np.roll(R, -1, axis=1) - np.roll(R, 1, axis=1)
        else:
            dj = np.gradient(R, axis=1)
        di = np.gradient(R, axis=0) if k > 1 else np.zeros_like(R)
        VN = np.cross(dj, di)
        ln = np.linalg.norm(VN, axis=2, keepdims=True)
        VN = np.where(ln > 1e-9, VN / np.maximum(ln, 1e-9), np.array([0, 0, 1.0]))
        Nn = np.stack([VN[:-1][:, ja], VN[:-1][:, jb], VN[1:][:, jb], VN[1:][:, ja]], axis=2)
    g.add_quads(P.reshape(-1, 4, 3), m, uv=UV.reshape(-1, 4, 2),
                n=None if Nn is None else Nn.reshape(-1, 4, 3), a=a)


def ring_uv_circ(r, quant=1.2):
    """Circumference quantised so that stone / slate patterns close around a round tower."""
    C = 2.0 * math.pi * r
    return max(quant, round(C / quant) * quant)


def lathe(g, profile, pos=(0, 0, 0), segs=32, m=0, smooth=True, uvr=None, yaw0=0.0, mats=None, scale=1.0,
          uv_v='z', crease_deg=38.0, a=None, quant=1.2):
    """Surface of revolution.  profile: (k,2) of (r,z) bottom->top, solid on the left."""
    prof = _arr(profile) * scale
    k = len(prof)
    pos = _arr(pos)
    S = int(segs)
    th = yaw0 + 2.0 * math.pi * np.arange(S + 1) / S
    cth, sth = np.cos(th), np.sin(th)
    rmax = float(np.max(prof[:, 0])) if uvr is None else uvr * scale
    Cq = ring_uv_circ(max(rmax, 0.3), quant)
    # profile normals
    d = np.diff(prof, axis=0)
    seg_len = np.linalg.norm(d, axis=1)
    sn = np.stack([d[:, 1], -d[:, 0]], axis=1)
    sn = sn / np.maximum(np.linalg.norm(sn, axis=1, keepdims=True), 1e-12)  # (k-1, 2): (nr, nz)
    cum = np.concatenate([[0.0], np.cumsum(seg_len)])
    marr = None
    if mats is not None:
        marr = [g.mid(x) for x in mats]
    for i in range(k - 1):
        r0, z0 = prof[i]
        r1, z1 = prof[i + 1]
        if seg_len[i] < 1e-9:
            continue
        # corner normals (smooth across nearly-straight profile joints)
        n0 = sn[i].copy()
        n1 = sn[i].copy()
        if smooth:
            cosc = math.cos(math.radians(crease_deg))
            if i > 0 and float(np.dot(sn[i - 1], sn[i])) > cosc:
                n0 = sn[i - 1] + sn[i]
                n0 = n0 / max(np.linalg.norm(n0), 1e-9)
            if i < k - 2 and float(np.dot(sn[i + 1], sn[i])) > cosc:
                n1 = sn[i + 1] + sn[i]
                n1 = n1 / max(np.linalg.norm(n1), 1e-9)
        j = np.arange(S)
        A = np.stack([pos[0] + r0 * cth[j], pos[1] + r0 * sth[j], np.full(S, pos[2] + z0)], axis=1)
        B = np.stack([pos[0] + r0 * cth[j + 1], pos[1] + r0 * sth[j + 1], np.full(S, pos[2] + z0)], axis=1)
        Cc = np.stack([pos[0] + r1 * cth[j + 1], pos[1] + r1 * sth[j + 1], np.full(S, pos[2] + z1)], axis=1)
        D = np.stack([pos[0] + r1 * cth[j], pos[1] + r1 * sth[j], np.full(S, pos[2] + z1)], axis=1)
        P = np.stack([A, B, Cc, D], axis=1)
        # uv
        u0 = j / S * Cq
        u1 = (j + 1) / S * Cq
        flat_seg = abs(z1 - z0) < 0.08 * abs(r1 - r0)
        if flat_seg:
            UV = np.stack([P[..., 0], P[..., 1]], axis=-1)
        else:
            if uv_v == 'z':
                va, vb = pos[2] + z0, pos[2] + z1
            else:
                va, vb = cum[i], cum[i + 1]
            UV = np.stack([np.stack([u0, np.full(S, va)], 1), np.stack([u1, np.full(S, va)], 1),
                           np.stack([u1, np.full(S, vb)], 1), np.stack([u0, np.full(S, vb)], 1)], axis=1)
        Nn = None
        if smooth:
            def nrm(nn, jj):
                return np.stack([nn[0] * cth[jj], nn[0] * sth[jj], np.full(len(jj), nn[1])], axis=1)
            Nn = np.stack([nrm(n0, j), nrm(n0, j + 1), nrm(n1, j + 1), nrm(n1, j)], axis=1)
        mm = m if marr is None else marr[i]
        g.add_quads(P, mm, uv=UV, n=Nn, a=a)


def sweep(g, profile, path, closed=True, m=0, side=1.0, smooth=False, a=None, mitre=True, z_add=0.0):
    """Sweep a closed (d,h) profile along a horizontal path (n,3).  d = offset to the RIGHT of travel
    (outward for a CCW loop), h = up.  Profile must be CCW in (d,h)."""
    prof = _arr(profile)
    path = _arr(path).copy()
    n = len(path)
    if closed:
        tan = np.roll(path, -1, axis=0) - path
    else:
        tan = np.gradient(path, axis=0)
    tan[:, 2] = 0
    tan = normalize(tan)
    nrm = np.stack([tan[:, 1], -tan[:, 0], np.zeros(n)], axis=1) * side
    if closed:
        prev_n = np.roll(nrm, 1, axis=0)
        # segment normals: nrm[i] belongs to segment i->i+1 ; vertex i uses seg i-1 and seg i
        mit = (prev_n + nrm) / np.maximum(1.0 + np.einsum('nc,nc->n', prev_n, nrm), 0.15)[:, None]
    else:
        seg_t = normalize(np.diff(path, axis=0) * np.array([1, 1, 0]))
        seg_n = np.stack([seg_t[:, 1], -seg_t[:, 0], np.zeros(len(seg_t))], axis=1) * side
        mit = np.zeros((n, 3))
        mit[0] = seg_n[0]
        mit[-1] = seg_n[-1]
        if n > 2:
            mit[1:-1] = (seg_n[:-1] + seg_n[1:]) / np.maximum(1.0 + np.einsum('nc,nc->n', seg_n[:-1], seg_n[1:]),
                                                                0.15)[:, None]
        nrm = mit
    if not mitre:
        mit = nrm
    rings = []
    for d, h in prof:
        rings.append(path + mit * d + np.array([0, 0, h + z_add]))
    rings.append(rings[0])
    loft(g, np.stack(rings, axis=0), closed=closed, m=m, smooth=smooth, uv_v='z', a=a)


def poly_cap(g, pts3, m=0, up=True, a=None):
    """Triangulated cap for a planar (near-horizontal) polygon given CCW from above."""
    pts3 = _arr(pts3)
    tri = triangulate_polygon(pts3[:, :2])
    if not tri:
        return
    T = np.array(tri)
    P = pts3[T]  # (t,3,3)
    if not up:
        P = P[:, ::-1]
    g.add(P, m, a=a)


def prism(g, poly, z0, z1, m=0, top=True, bottom=False, m_top=None, a=None, uv_v='z'):
    """Extrude a CCW polygon (n,2) between z0 and z1."""
    poly = _arr(poly)
    n = len(poly)
    r0 = np.column_stack([poly, np.full(n, z0)])
    r1 = np.column_stack([poly, np.full(n, z1)])
    loft(g, np.stack([r0, r1]), closed=True, m=m, uv_v=uv_v, a=a)
    if top:
        poly_cap(g, r1, m if m_top is None else m_top, up=True, a=a)
    if bottom:
        poly_cap(g, r0, m, up=False, a=a)


def ngon(cx, cy, r, n, yaw0=0.0):
    t = yaw0 + 2 * math.pi * np.arange(n) / n
    return np.column_stack([cx + r * np.cos(t), cy + r * np.sin(t)])


def rect_poly(cx, cy, sx, sy, yaw=0.0):
    p = np.array([[-sx / 2, -sy / 2], [sx / 2, -sy / 2], [sx / 2, sy / 2], [-sx / 2, sy / 2]])
    c, s = math.cos(yaw), math.sin(yaw)
    x = p[:, 0] * c - p[:, 1] * s + cx
    y = p[:, 0] * s + p[:, 1] * c + cy
    return np.column_stack([x, y])


def pyramid(g, base3, apex, m=0, a=None):
    """Pyramid faces from a CCW (from above) base ring to an apex point."""
    base3 = _arr(base3)
    n = len(base3)
    ap = np.broadcast_to(_arr(apex), (n, 3))
    P = np.stack([base3, np.roll(base3, -1, axis=0), ap], axis=1)
    g.add(P, m, a=a)


# --------------------------------------------------------------------------------------
# arches / outlines (x,z in the wall plane, viewer looking +y: x right, z up)
# --------------------------------------------------------------------------------------

def pointed_arch(w, h_spring, rise, n=9, y_bottom=0.0, cx=0.0):
    """CCW outline (as seen from outside, x right / z up) of a pointed arch opening of width w.
    Vertical jambs from y_bottom to the springing line h_spring, then two circular arcs meeting
    at the apex `rise` above the springing line."""
    a = w / 2.0
    R = (rise * rise + a * a) / (2.0 * a)
    phi_a = math.acos(-(R - a) / R)
    ph = np.linspace(math.pi, phi_a, n)
    xl = -a + R + R * np.cos(ph)      # left arc: springing (-a) -> apex (0)
    zl = h_spring + R * np.sin(ph)
    xr = -xl                          # right arc: springing (+a) -> apex (0)
    pts = [(a, y_bottom)]
    pts += list(zip(xr, zl))
    pts += list(zip(xl[::-1][1:], zl[::-1][1:]))
    pts += [(-a, y_bottom)]
    P = np.array(pts, dtype=np.float64)
    P[:, 0] += cx
    return P


def round_arch(w, h_spring, n=12, y_bottom=0.0, cx=0.0):
    a = w / 2.0
    t = np.linspace(0, math.pi, n)
    pts = [(a, y_bottom)]
    pts += [(a * math.cos(tt), h_spring + a * math.sin(tt)) for tt in t]
    pts += [(-a, y_bottom)]
    P = np.array(pts, dtype=np.float64)
    P[:, 0] += cx
    return P


def circle_outline(r, n=16, cx=0.0, cz=0.0):
    t = 2 * math.pi * np.arange(n) / n
    return np.column_stack([cx + r * np.cos(t), cz + r * np.sin(t)])


def rect_outline(w, h, cx=0.0, z0=0.0):
    return np.array([[cx + w / 2, z0], [cx + w / 2, z0 + h], [cx - w / 2, z0 + h], [cx - w / 2, z0]], dtype=np.float64)


def offset_outline(P, d):
    """Offset a CCW closed outline outward by d (mitred)."""
    P = _arr(P)
    n = len(P)
    t = np.roll(P, -1, axis=0) - P
    t = t / np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-12)
    nr = np.stack([t[:, 1], -t[:, 0]], axis=1)  # outward for CCW
    pn = np.roll(nr, 1, axis=0)
    mit = (pn + nr) / np.maximum(1.0 + np.einsum('nc,nc->n', pn, nr), 0.2)[:, None]
    return P + mit * d


def wall_strip(g, outer, inner, y, m=0, a=None, uvz=None):
    """Front-facing strip between two CCW outlines in the wall plane at depth y (face normal -y)."""
    outer = _arr(outer)
    inner = _arr(inner)
    n = len(outer)
    j2 = (np.arange(n) + 1) % n
    A = np.column_stack([outer[:, 0], np.full(n, y), outer[:, 1]])
    B = np.column_stack([outer[j2, 0], np.full(n, y), outer[j2, 1]])
    Cc = np.column_stack([inner[j2, 0], np.full(n, y), inner[j2, 1]])
    D = np.column_stack([inner[:, 0], np.full(n, y), inner[:, 1]])
    g.add_quads(np.stack([A, B, Cc, D], axis=1), m, a=a)


def wall_fill(g, outline, y, m=0, a=None, uv_scale=1.0, uv_offset=(0.0, 0.0), uv_center=None):
    """Front-facing filled polygon (glass pane).  UV = (x, z) metres relative to `uv_center` (default: centroid)."""
    outline = _arr(outline)
    tri = triangulate_polygon(outline)
    if not tri:
        return
    T = np.array(tri)
    P3 = np.column_stack([outline[:, 0], np.full(len(outline), y), outline[:, 1]])
    P = P3[T]
    # winding: CCW seen from -y viewer (x right, z up) -> normal -y  ✓
    c = outline.mean(axis=0) if uv_center is None else np.asarray(uv_center, dtype=np.float64)
    UV = np.stack([(outline[T][..., 0] - c[0]) * uv_scale + uv_offset[0],
                   (outline[T][..., 1] - c[1]) * uv_scale + uv_offset[1]], axis=-1)
    g.add(P, m, uv=UV, a=a)


def reveal(g, inner, y_front, y_back, m=0, a=None):
    """Inner side walls of an opening (faces point into the opening)."""
    inner = _arr(inner)
    n = len(inner)
    j2 = (np.arange(n) + 1) % n
    A = np.column_stack([inner[:, 0], np.full(n, y_front), inner[:, 1]])
    B = np.column_stack([inner[j2, 0], np.full(n, y_front), inner[j2, 1]])
    Cc = np.column_stack([inner[j2, 0], np.full(n, y_back), inner[j2, 1]])
    D = np.column_stack([inner[:, 0], np.full(n, y_back), inner[:, 1]])
    g.add_quads(np.stack([A, B, Cc, D], axis=1), m, a=a)


def outer_side(g, outer, y_front, y_back, m=0, a=None):
    """Outward-facing side walls of a projecting frame."""
    outer = _arr(outer)
    n = len(outer)
    j2 = (np.arange(n) + 1) % n
    A = np.column_stack([outer[:, 0], np.full(n, y_back), outer[:, 1]])
    B = np.column_stack([outer[j2, 0], np.full(n, y_back), outer[j2, 1]])
    Cc = np.column_stack([outer[j2, 0], np.full(n, y_front), outer[j2, 1]])
    D = np.column_stack([outer[:, 0], np.full(n, y_front), outer[:, 1]])
    g.add_quads(np.stack([A, B, Cc, D], axis=1), m, a=a)


def frame_ring(g, outer, inner, y_front, y_back, m=0, a=None, y_inner_back=None, with_reveal=True):
    """Projecting frame: front strip + reveal + outer sides."""
    wall_strip(g, outer, inner, y_front, m, a)
    if with_reveal:
        reveal(g, inner, y_front, y_inner_back if y_inner_back is not None else y_back, m, a)
    outer_side(g, outer, y_front, y_back, m, a)
