"""Shared helpers for the procedural Hogwarts build.

Everything here is pure bpy / bmesh / numpy — no external assets.
Import from build scripts with:

    import hog_lib as H; importlib.reload(H)
"""
import bpy, bmesh, math, os, random, time
from mathutils import Vector, Matrix, Euler
import numpy as np

FOLDER = os.path.dirname(os.path.abspath(__file__))
WIP = os.path.join(FOLDER, "wip")
BLEND = os.path.join(FOLDER, "hogwarts.blend")

# ---------------------------------------------------------------- collections
def coll(name, parent=None):
    """Get or create a collection and link it under *parent* (scene root if None)."""
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
    par = parent if parent is not None else bpy.context.scene.collection
    if isinstance(par, str):
        par = coll(par)
    if c.name not in par.children and c is not par:
        # avoid double-linking under a different parent
        for other in bpy.data.collections:
            if c.name in other.children and other is not par:
                other.children.unlink(c)
        if c.name in bpy.context.scene.collection.children and par is not bpy.context.scene.collection:
            bpy.context.scene.collection.children.unlink(c)
        par.children.link(c)
    return c

def clear_collection(name, remove_data=True):
    c = bpy.data.collections.get(name)
    if c is None:
        return
    for ch in list(c.children):
        clear_collection(ch.name, remove_data)
    for o in list(c.objects):
        data = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if remove_data and data is not None and data.users == 0:
            try:
                if isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)
                elif isinstance(data, bpy.types.Curve):
                    bpy.data.curves.remove(data)
                elif isinstance(data, bpy.types.Light):
                    bpy.data.lights.remove(data)
                elif isinstance(data, bpy.types.Camera):
                    bpy.data.cameras.remove(data)
            except Exception:
                pass

def purge_orphans():
    for _ in range(3):
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

# ---------------------------------------------------------------- objects
def link_obj(obj, c):
    if isinstance(c, str):
        c = coll(c)
    for uc in list(obj.users_collection):
        uc.objects.unlink(obj)
    c.objects.link(obj)
    return obj

def new_mesh_obj(name, verts, faces, c, edges=(), smooth=False, mat=None, recalc=True):
    """Create a mesh object from python data; normals recalculated outward."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], list(edges), [tuple(f) for f in faces])
    me.update()
    if recalc and faces:
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me); bm.free()
    if smooth:
        me.shade_smooth()
    obj = bpy.data.objects.new(name, me)
    link_obj(obj, c)
    if mat is not None:
        set_material(obj, mat)
    return obj

def obj_from_bmesh(name, bm, c, smooth=False, mat=None, recalc=True, free=True):
    me = bpy.data.meshes.new(name)
    if recalc:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    if free:
        bm.free()
    me.update()
    if smooth:
        me.shade_smooth()
    obj = bpy.data.objects.new(name, me)
    link_obj(obj, c)
    if mat is not None:
        set_material(obj, mat)
    return obj

def set_material(obj, mat, slot=0):
    if isinstance(mat, str):
        mat = bpy.data.materials.get(mat) or ensure_material(mat)
    me = obj.data
    if me is None:
        return
    while len(me.materials) <= slot:
        me.materials.append(None)
    me.materials[slot] = mat

def ensure_material(name, color=(0.5, 0.5, 0.5, 1.0)):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = color
        m.diffuse_color = color
    return m

def smooth_by_angle(obj, angle_deg=35.0):
    me = obj.data
    me.shade_smooth()
    # Blender 4.1+: sharp edges by angle
    try:
        bpy.ops.object.select_all(action='DESELECT')
    except Exception:
        pass
    try:
        with bpy.context.temp_override(object=obj, selected_objects=[obj], active_object=obj):
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle_deg))
    except Exception:
        # fallback: mark sharp edges manually
        bm = bmesh.new(); bm.from_mesh(me)
        th = math.radians(angle_deg)
        for e in bm.edges:
            if len(e.link_faces) == 2:
                a = e.link_faces[0].normal.angle(e.link_faces[1].normal, 0.0)
                e.smooth = a < th
        bm.to_mesh(me); bm.free()

# ---------------------------------------------------------------- bmesh primitives
def bm_new():
    return bmesh.new()

def bm_box(bm, size, center=(0, 0, 0), rot_z=0.0):
    """Axis-aligned box (size = (sx, sy, sz)) centred at *center* (z = bottom+sz/2)."""
    sx, sy, sz = size
    m = Matrix.Translation(Vector(center)) @ Matrix.Rotation(rot_z, 4, 'Z') @ Matrix.Diagonal((sx, sy, sz, 1.0))
    r = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, matrix=m, verts=r['verts'])
    return r['verts']

def bm_box_zrange(bm, x0, x1, y0, y1, z0, z1, rot_z=0.0, pivot=None):
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    verts = bm_box(bm, (x1 - x0, y1 - y0, z1 - z0), (cx, cy, cz))
    if rot_z:
        p = Vector(pivot) if pivot is not None else Vector((cx, cy, cz))
        m = Matrix.Translation(p) @ Matrix.Rotation(rot_z, 4, 'Z') @ Matrix.Translation(-p)
        bmesh.ops.transform(bm, matrix=m, verts=verts)
    return verts

def bm_cylinder(bm, r, z0, z1, segs=32, center=(0, 0), r_top=None, cap_bottom=True, cap_top=True, rot=0.0):
    """Cylinder / truncated cone between z0 and z1."""
    r_top = r if r_top is None else r_top
    res = bmesh.ops.create_cone(bm, cap_ends=False, cap_tris=False, segments=segs,
                                radius1=r, radius2=r_top, depth=(z1 - z0))
    verts = res['verts']
    m = Matrix.Translation(Vector((center[0], center[1], (z0 + z1) / 2))) @ Matrix.Rotation(rot, 4, 'Z')
    bmesh.ops.transform(bm, matrix=m, verts=verts)
    # caps
    if cap_bottom or cap_top:
        bot = [v for v in verts if abs(v.co.z - z0) < 1e-5]
        top = [v for v in verts if abs(v.co.z - z1) < 1e-5]
        if cap_bottom and len(bot) >= 3 and r > 1e-6:
            bm.faces.new(bot)
        if cap_top and len(top) >= 3 and r_top > 1e-6:
            bm.faces.new(top)
    return verts

def bm_cone(bm, r, z0, z1, segs=32, center=(0, 0), cap=True, rot=0.0):
    """Pointed cone: base radius r at z0, apex at z1."""
    res = bmesh.ops.create_cone(bm, cap_ends=False, cap_tris=False, segments=segs,
                                radius1=r, radius2=0.0, depth=(z1 - z0))
    verts = res['verts']
    m = Matrix.Translation(Vector((center[0], center[1], (z0 + z1) / 2))) @ Matrix.Rotation(rot, 4, 'Z')
    bmesh.ops.transform(bm, matrix=m, verts=verts)
    if cap:
        bot = [v for v in verts if abs(v.co.z - z0) < 1e-5]
        if len(bot) >= 3:
            bm.faces.new(bot)
    return verts

def bm_prism(bm, poly2d, z0, z1, cap_bottom=True, cap_top=True):
    """Extrude a 2D polygon (list of (x,y)) between z0 and z1; orientation is auto-corrected to CCW."""
    area = 0.0
    for (ax, ay), (bx, by) in zip(poly2d, poly2d[1:] + poly2d[:1]):
        area += ax * by - bx * ay
    if area < 0:
        poly2d = list(reversed(poly2d))
    n = len(poly2d)
    vb = [bm.verts.new((x, y, z0)) for x, y in poly2d]
    vt = [bm.verts.new((x, y, z1)) for x, y in poly2d]
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append(bm.faces.new((vb[i], vb[j], vt[j], vt[i])))
    if cap_bottom:
        faces.append(bm.faces.new(list(reversed(vb))))
    if cap_top:
        faces.append(bm.faces.new(vt))
    return vb + vt, faces

def bm_gable_roof(bm, x0, x1, y0, y1, z_eave, z_ridge, axis='x', overhang=0.0, thickness=0.0):
    """Simple gable roof prism. Ridge runs along *axis*."""
    if axis == 'x':
        xa, xb = x0 - overhang, x1 + overhang
        ya, yb = y0 - overhang, y1 + overhang
        ym = (y0 + y1) / 2
        v = [bm.verts.new(p) for p in (
            (xa, ya, z_eave), (xb, ya, z_eave), (xb, yb, z_eave), (xa, yb, z_eave),
            (xa, ym, z_ridge), (xb, ym, z_ridge))]
        faces = [bm.faces.new((v[0], v[1], v[5], v[4])),   # south slope
                 bm.faces.new((v[2], v[3], v[4], v[5])),   # north slope
                 bm.faces.new((v[0], v[4], v[3])),         # west gable
                 bm.faces.new((v[1], v[2], v[5])),         # east gable
                 bm.faces.new((v[3], v[2], v[1], v[0]))]   # underside
    else:
        xa, xb = x0 - overhang, x1 + overhang
        ya, yb = y0 - overhang, y1 + overhang
        xm = (x0 + x1) / 2
        v = [bm.verts.new(p) for p in (
            (xa, ya, z_eave), (xb, ya, z_eave), (xb, yb, z_eave), (xa, yb, z_eave),
            (xm, ya, z_ridge), (xm, yb, z_ridge))]
        faces = [bm.faces.new((v[1], v[2], v[5], v[4])),
                 bm.faces.new((v[3], v[0], v[4], v[5])),
                 bm.faces.new((v[0], v[1], v[4])),
                 bm.faces.new((v[2], v[3], v[5])),
                 bm.faces.new((v[3], v[2], v[1], v[0]))]
    return v, faces

def bm_transform(bm, verts, matrix):
    bmesh.ops.transform(bm, matrix=matrix, verts=verts)

def bm_merge_from(bm_dst, obj):
    """Append an object's mesh (with its world transform) into bm_dst."""
    tmp = bmesh.new(); tmp.from_mesh(obj.data)
    tmp.transform(obj.matrix_world)
    me = bpy.data.meshes.new("_tmp_merge")
    tmp.to_mesh(me); tmp.free()
    bm_dst.from_mesh(me)
    bpy.data.meshes.remove(me)

def finish_bmesh(bm, name, c, mat=None, smooth=False, auto_smooth_deg=None, recalc=True, weld=1e-4):
    if weld:
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=weld)
    obj = obj_from_bmesh(name, bm, c, smooth=smooth, mat=mat, recalc=recalc)
    if auto_smooth_deg is not None:
        smooth_by_angle(obj, auto_smooth_deg)
    return obj

# ---------------------------------------------------------------- 2D helpers
def circle_pts(cx, cy, r, n, phase=0.0):
    return [(cx + r * math.cos(phase + 2 * math.pi * i / n), cy + r * math.sin(phase + 2 * math.pi * i / n)) for i in range(n)]

def rect_pts(x0, x1, y0, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

def rot2(x, y, ang):
    c, s = math.cos(ang), math.sin(ang)
    return (c * x - s * y, s * x + c * y)

# ---------------------------------------------------------------- scene / render
def save(path=BLEND):
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True, copy=False)
    return path

def set_render(res=(3840, 2160), samples=1024, pct=100, denoise=True):
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    scn.render.resolution_x, scn.render.resolution_y = res
    scn.render.resolution_percentage = pct
    scn.cycles.samples = samples
    scn.cycles.use_denoising = denoise

def render_async(path, cam=None, res=(1280, 720), samples=64, denoise=True, pct=100, marker=True):
    """Kick a blocking render off a timer so the MCP call returns immediately.
    Poll for `<path>.done` (or `<path>.err`) from outside."""
    scn = bpy.context.scene
    if cam is not None:
        scn.camera = bpy.data.objects[cam] if isinstance(cam, str) else cam
    set_render(res, samples, pct, denoise)
    scn.render.image_settings.file_format = 'PNG'
    scn.render.image_settings.color_mode = 'RGB'
    scn.render.filepath = path
    for ext in (".done", ".err"):
        try:
            os.remove(path + ext)
        except FileNotFoundError:
            pass
    def _do():
        t0 = time.time()
        try:
            bpy.ops.render.render(write_still=True)
            with open(path + ".done", "w") as f:
                f.write("%.1f s\n" % (time.time() - t0))
        except Exception as e:
            with open(path + ".err", "w") as f:
                f.write(repr(e))
        return None
    bpy.app.timers.register(_do, first_interval=0.05)
    return path

# ---------------------------------------------------------------- noise (numpy)
def _hash2(ix, iy, seed):
    n = (ix * 374761393 + iy * 668265263 + seed * 1442695041) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    n = n ^ (n >> 16)
    return n

def value_noise(x, y, seed=0):
    """Smooth value noise in [-1,1] on a unit lattice (numpy arrays)."""
    x0 = np.floor(x).astype(np.int64); y0 = np.floor(y).astype(np.int64)
    fx = x - x0; fy = y - y0
    u = fx * fx * (3 - 2 * fx); v = fy * fy * (3 - 2 * fy)
    def h(ix, iy):
        return (_hash2(ix, iy, seed) & 0xFFFF) / 65535.0 * 2.0 - 1.0
    a = h(x0, y0); b = h(x0 + 1, y0); c = h(x0, y0 + 1); d = h(x0 + 1, y0 + 1)
    return (a * (1 - u) + b * u) * (1 - v) + (c * (1 - u) + d * u) * v

def fbm(x, y, octaves=6, lacunarity=2.0, gain=0.5, seed=0, scale=1.0):
    """Fractal Brownian motion, roughly in [-1,1]."""
    out = np.zeros_like(x, dtype=np.float64)
    amp = 1.0; fr = 1.0 / scale; norm = 0.0
    for i in range(octaves):
        out += amp * value_noise(x * fr + 17.1 * i, y * fr - 9.3 * i, seed + i * 101)
        norm += amp
        amp *= gain; fr *= lacunarity
    return out / norm

def ridged(x, y, octaves=6, lacunarity=2.0, gain=0.5, seed=0, scale=1.0, sharp=1.0):
    """Ridged multifractal in [0,1] (1 = ridge crest)."""
    out = np.zeros_like(x, dtype=np.float64)
    amp = 1.0; fr = 1.0 / scale; norm = 0.0; w = 1.0
    for i in range(octaves):
        n = 1.0 - np.abs(value_noise(x * fr + 3.7 * i, y * fr + 5.1 * i, seed + i * 77))
        n = n ** (1.0 + sharp)
        out += amp * n * w
        w = np.clip(n, 0, 1)
        norm += amp
        amp *= gain; fr *= lacunarity
    return out / norm

def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)

def smax(a, b, k):
    """Smooth maximum (polynomial)."""
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * h + a * (1 - h) + k * h * (1 - h)

def smin(a, b, k):
    return -smax(-a, -b, k)

def sd_superellipse(x, y, cx, cy, ax, ay, n=2.5, rot=0.0):
    """Signed-ish distance field (<0 inside) for a rotated superellipse, in metres (approx)."""
    dx, dy = x - cx, y - cy
    c, s = math.cos(-rot), math.sin(-rot)
    rx = c * dx - s * dy; ry = s * dx + c * dy
    r = (np.abs(rx / ax) ** n + np.abs(ry / ay) ** n) ** (1.0 / n)
    # scale to approximate metres using the local semi-axis
    ang = np.arctan2(ry / ay, rx / ax)
    local = np.sqrt((ax * np.cos(ang)) ** 2 + (ay * np.sin(ang)) ** 2)
    return (r - 1.0) * local

def sd_segment(px, py, ax, ay, bx, by):
    pax, pay = px - ax, py - ay
    bax, bay = bx - ax, by - ay
    h = np.clip((pax * bax + pay * bay) / (bax * bax + bay * bay + 1e-9), 0.0, 1.0)
    return np.sqrt((pax - bax * h) ** 2 + (pay - bay * h) ** 2)

def sd_polyline(px, py, pts):
    d = np.full_like(px, 1e9, dtype=np.float64)
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        d = np.minimum(d, sd_segment(px, py, ax, ay, bx, by))
    return d

# ---------------------------------------------------------------- misc
def rng(seed):
    return random.Random(seed)

def lerp(a, b, t):
    return a + (b - a) * t

def clamp(x, a, b):
    return max(a, min(b, x))

def render_batch(jobs, samples=64, res=(1280, 720), denoise=True, pct=100):
    """Queue several renders: jobs = [(path, cam_name), ...] (optionally 4-tuples with res, samples).
    Runs sequentially off a timer; writes <path>.done / .err markers and a batch marker."""
    scn = bpy.context.scene
    done_marker = jobs[0][0] + ".batch"
    try:
        os.remove(done_marker)
    except FileNotFoundError:
        pass
    def _do():
        log = []
        for job in jobs:
            path, cam = job[0], job[1]
            r = job[2] if len(job) > 2 else res
            s = job[3] if len(job) > 3 else samples
            t0 = time.time()
            try:
                scn.camera = bpy.data.objects[cam]
                set_render(r, s, pct, denoise)
                scn.render.image_settings.file_format = 'PNG'
                scn.render.filepath = path
                bpy.ops.render.render(write_still=True)
                log.append("%s %.1fs" % (os.path.basename(path), time.time() - t0))
            except Exception as e:
                log.append("%s ERR %r" % (os.path.basename(path), e))
        with open(done_marker, "w") as f:
            f.write("\n".join(log) + "\n")
        return None
    bpy.app.timers.register(_do, first_interval=0.05)
    return done_marker

# ---------------------------------------------------------------- node graph helper
class NB:
    """Tiny node-graph DSL.  nb.n("ShaderNodeTexNoise", Scale=4.0, _noise_dimensions='3D')
    Keyword args starting with '_' set node properties; others set input sockets
    (a NodeSocket value creates a link).  Returns the node."""
    def __init__(self, tree, clear=True):
        self.t = tree
        if clear:
            tree.nodes.clear()
        self._x = 0
    def n(self, typ, label=None, **kw):
        node = self.t.nodes.new(typ)
        node.location = (self._x, 0); self._x += 200
        if label:
            node.label = label; node.name = label
        for k, v in kw.items():
            if k.startswith("_"):
                setattr(node, k[1:], v)
        for k, v in kw.items():
            if k.startswith("_"):
                continue
            key = k.replace("__", " ")
            sock = None
            if key.isdigit():
                sock = node.inputs[int(key)]
            else:
                import re as _re
                mm = _re.match(r"^(.*)_(\d+)$", key)
                base, idx = (mm.group(1), int(mm.group(2))) if mm else (key, 0)
                cands = [s for s in node.inputs if s.name == base and s.enabled]
                if not cands:
                    cands = [s for s in node.inputs if s.name == base]
                if idx < len(cands):
                    sock = cands[idx]
            if sock is None:
                raise KeyError(f"{typ}: no input {key!r}; have {[s.name for s in node.inputs]}")
            if isinstance(v, bpy.types.NodeSocket):
                self.t.links.new(v, sock)
            else:
                if hasattr(sock, "default_value"):
                    try:
                        sock.default_value = v
                    except Exception:
                        sock.default_value = (v, v, v, 1.0) if isinstance(v, (int, float)) else v
        return node
    def link(self, a, b):
        self.t.links.new(a, b)
    def o(self, node, name):
        for s in node.outputs:
            if s.name == name and s.enabled:
                return s
        return node.outputs[name]

def new_material(name):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m
