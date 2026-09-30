"""Scene helpers: collections, cameras, render setup, cleanup."""
import bpy
import math
import os
from mathutils import Vector

BASE = '/home/morpheus/Documents/Morpheus-Produktion/Benchmarks/Blender/Claude-Sonnet-5.5'
WORK = BASE + '/_work'
COLLECTIONS = ['Castle', 'Terrain', 'Nature', 'Lights', 'FX', 'Cameras']


def ensure_collection(name, parent=None):
    """Return collection `name`; with `parent` it is (re)linked below that collection."""
    c = bpy.data.collections.get(name)
    par = parent or bpy.context.scene.collection
    if c is None:
        c = bpy.data.collections.new(name)
        par.children.link(c)
    elif parent is not None:
        for p in [bpy.context.scene.collection] + list(bpy.data.collections):
            if p is not par and name in p.children:
                p.children.unlink(c)
        if name not in par.children:
            par.children.link(c)
    return c


def _find_layer(lc, name):
    if lc.name == name:
        return lc
    for ch in lc.children:
        r = _find_layer(ch, name)
        if r is not None:
            return r
    return None


def exclude_collection(name, on=True):
    """Exclude / include a (possibly nested) collection in the active view layer."""
    lc = _find_layer(bpy.context.view_layer.layer_collection, name)
    if lc is not None:
        lc.exclude = on
    return lc


def clear_collection(name):
    """Remove all objects (and their mesh data) from a collection."""
    c = bpy.data.collections.get(name)
    if c is None:
        return
    for o in list(c.objects):
        data = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if data is not None and getattr(data, 'users', 1) == 0:
            if isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
            elif isinstance(data, bpy.types.Curve):
                bpy.data.curves.remove(data)
            elif isinstance(data, bpy.types.Light):
                bpy.data.lights.remove(data)
            elif isinstance(data, bpy.types.Camera):
                bpy.data.cameras.remove(data)


def remove_object(name):
    o = bpy.data.objects.get(name)
    if o is None:
        return
    data = o.data
    bpy.data.objects.remove(o, do_unlink=True)
    if data is not None and getattr(data, 'users', 1) == 0 and isinstance(data, bpy.types.Mesh):
        bpy.data.meshes.remove(data)


def purge_orphans():
    for _ in range(3):
        bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)


def fresh_scene():
    """Remove the factory objects and make the standard collection layout."""
    sc = bpy.context.scene
    for o in list(bpy.data.objects):
        if o.name in ('Cube', 'Light', 'Camera'):
            bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections):
        if c.name == 'Collection' and not c.objects:
            bpy.data.collections.remove(c)
    for name in COLLECTIONS:
        ensure_collection(name)
    ensure_collection('Water', parent=bpy.data.collections['Terrain'])
    purge_orphans()
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0
    sc.unit_settings.length_unit = 'METERS'


def ensure_material(name, color=(0.5, 0.5, 0.5), rough=0.6, emission=None, strength=1.0):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    if not any(n.type == 'BSDF_PRINCIPLED' for n in nt.nodes):
        nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
        nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    bsdf = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = rough
    if emission is not None:
        bsdf.inputs['Emission Color'].default_value = (*emission, 1.0)
        bsdf.inputs['Emission Strength'].default_value = strength
    return m


def make_camera(name, loc, target, lens=35.0, sensor=36.0, clip=(0.3, 40000.0), coll='Cameras', roll=0.0,
                shift=(0.0, 0.0)):
    cam = bpy.data.cameras.get(name)
    obj = bpy.data.objects.get(name)
    if cam is None:
        cam = bpy.data.cameras.new(name)
    if obj is None:
        obj = bpy.data.objects.new(name, cam)
        ensure_collection(coll).objects.link(obj)
    cam.lens = lens
    cam.sensor_width = sensor
    cam.sensor_fit = 'HORIZONTAL'
    cam.clip_start, cam.clip_end = clip
    cam.shift_x, cam.shift_y = shift
    obj.location = loc
    d = Vector(target) - Vector(loc)
    q = d.to_track_quat('-Z', 'Y')
    e = q.to_euler()
    obj.rotation_euler = e
    if roll:
        obj.rotation_euler.rotate_axis('Z', math.radians(roll))
    return obj


def cycles_setup(samples=64, res=(1280, 720), pct=100, denoise=True, adaptive=True, device='GPU',
                 denoiser='OPENIMAGEDENOISE'):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    cp = bpy.context.preferences.addons['cycles'].preferences
    cp.compute_device_type = 'OPTIX'
    cp.refresh_devices()
    for d in cp.devices:
        d.use = (d.type == 'OPTIX')
    sc.cycles.device = device
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = adaptive
    sc.cycles.use_denoising = denoise
    sc.cycles.denoiser = denoiser
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = pct
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_depth = '16' if pct == 100 and res[0] >= 3840 else '8'
    sc.render.image_settings.color_mode = 'RGB'
    bpy.context.preferences.view.render_display_type = 'NONE'


def render_to(path, cam_name=None):
    sc = bpy.context.scene
    if cam_name:
        sc.camera = bpy.data.objects[cam_name]
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path
