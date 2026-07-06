"""Hogwarts build helper library. Reloaded into Blender as module 'hog'."""
import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Euler

FOLDER = '/home/morpheus/Documents/Projects/Blender/Claude-Fable-5'


# ---------------------------------------------------------------- collections
def coll(name):
    return bpy.data.collections[name]


def clear_coll(name, recursive=True):
    c = bpy.data.collections.get(name)
    if not c:
        return
    colls = [c]
    if recursive:
        stack = list(c.children)
        while stack:
            k = stack.pop()
            colls.append(k)
            stack.extend(k.children)
    for cc in colls:
        for ob in list(cc.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
    purge()


def purge():
    for blk in (bpy.data.meshes, bpy.data.curves, bpy.data.lights,
                bpy.data.cameras, bpy.data.materials, bpy.data.node_groups):
        for b in list(blk):
            if b.users == 0 and not b.use_fake_user:
                blk.remove(b)


# ---------------------------------------------------------------- mesh basics
def obj_from_bm(bm, name, cname, mats=None, smooth_angle=None):
    """Create object from bmesh. mats: material or list of materials."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll(cname).objects.link(ob)
    if mats:
        if not isinstance(mats, (list, tuple)):
            mats = [mats]
        for m in mats:
            me.materials.append(m)
    if smooth_angle is not None:
        for p in me.polygons:
            p.use_smooth = True
        me.set_sharp_from_angle(angle=smooth_angle)
    return ob


def box(name, cname, size=(1, 1, 1), loc=(0, 0, 0), rot=0.0, mat=None,
        base=True):
    """Axis box. If base, loc is the bottom-center."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    ob = obj_from_bm(bm, name, cname, mat)
    z = loc[2] + (size[2] / 2 if base else 0)
    ob.location = (loc[0], loc[1], z)
    ob.rotation_euler = (0, 0, rot)
    return ob


def cyl(name, cname, r=1.0, h=1.0, loc=(0, 0, 0), segs=24, mat=None,
        r2=None, smooth=True, rot=(0, 0, 0)):
    """Cylinder/cone, loc is bottom-center. r2=0 gives a cone."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs,
                          radius1=r, radius2=r if r2 is None else r2,
                          depth=h)
    if smooth:
        for f in bm.faces:
            if abs(f.normal.z) < 0.99:
                f.smooth = True
    ob = obj_from_bm(bm, name, cname, mat)
    ob.location = (loc[0], loc[1], loc[2] + h / 2)
    ob.rotation_euler = rot
    return ob


def gable(name, cname, sx, sy, wall_h, roof_h, loc=(0, 0, 0), rot=0.0,
          mats=None, roof_overhang=0.0):
    """Rectangular hall with gabled roof, ridge along local X.
    mats: [wall_mat, roof_mat]. loc is bottom-center of footprint."""
    hx, hy = sx / 2.0, sy / 2.0
    oh = roof_overhang
    vs = [(-hx, -hy, 0), (hx, -hy, 0), (hx, hy, 0), (-hx, hy, 0),
          (-hx, -hy, wall_h), (hx, -hy, wall_h),
          (hx, hy, wall_h), (-hx, hy, wall_h),
          (-hx, 0, wall_h + roof_h), (hx, 0, wall_h + roof_h)]
    faces = [(0, 3, 2, 1),          # bottom
             (0, 1, 5, 4),          # wall -Y
             (2, 3, 7, 6),          # wall +Y
             (1, 2, 6, 9, 5),       # gable +X
             (3, 0, 4, 8, 7),       # gable -X
             (4, 5, 9, 8),          # roof -Y
             (6, 7, 8, 9)]          # roof +Y
    bm = bmesh.new()
    bvs = [bm.verts.new(v) for v in vs]
    bm.verts.ensure_lookup_table()
    for i, f in enumerate(faces):
        fc = bm.faces.new([bvs[j] for j in f])
        fc.material_index = 1 if i >= 5 else 0
    ob = obj_from_bm(bm, name, cname, mats)
    ob.location = loc
    ob.rotation_euler = (0, 0, rot)
    return ob


def look_at(ob, target):
    d = Vector(target) - Vector(ob.location)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def camera(name, loc, target, lens=50, clip_end=8000):
    cam = bpy.data.objects.get(name)
    if cam is None:
        cd = bpy.data.cameras.new(name)
        cam = bpy.data.objects.new(name, cd)
        coll('Cameras').objects.link(cam)
    cam.data.lens = lens
    cam.data.clip_start = 0.5
    cam.data.clip_end = clip_end
    cam.location = loc
    look_at(cam, target)
    return cam


# ---------------------------------------------------------------- materials
def flat_mat(name, rgb, rough=0.8, emit=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_fake_user = True
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    if emit > 0:
        b.inputs['Emission Color'].default_value = (*rgb, 1)
        b.inputs['Emission Strength'].default_value = emit
    return m


def mat_stone():
    return flat_mat('Stone', (0.50, 0.46, 0.40), 0.9)


def mat_roof():
    return flat_mat('Roof', (0.10, 0.12, 0.15), 0.7)


def mat_rock():
    return flat_mat('Rock', (0.30, 0.27, 0.23), 0.95)


def mat_water():
    return flat_mat('Water', (0.01, 0.03, 0.05), 0.05)


# ---------------------------------------------------------------- terrain
def ground_z(x, y, obj_name='Terrain_Main', z_from=600.0):
    """Ray-cast straight down onto a terrain object; returns hit z or None."""
    ob = bpy.data.objects.get(obj_name)
    if ob is None:
        return None
    ok, loc, nrm, idx = ob.ray_cast((x, y, z_from), (0, 0, -1))
    return loc.z if ok else None


# ---------------------------------------------------------------- rendering
def quickrender(path, pct=25, samples=48, camera=None):
    s = bpy.context.scene
    if camera:
        s.camera = bpy.data.objects[camera]
    old_pct = s.render.resolution_percentage
    old_smp = s.cycles.samples
    old_fp = s.render.filepath
    s.render.resolution_percentage = pct
    s.cycles.samples = samples
    s.render.filepath = path
    try:
        bpy.ops.render.render(write_still=True)
    finally:
        s.render.resolution_percentage = old_pct
        s.cycles.samples = old_smp
        s.render.filepath = old_fp


def save():
    bpy.ops.wm.save_mainfile()
