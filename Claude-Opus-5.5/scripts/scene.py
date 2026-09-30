"""Render settings, cameras, collections."""
import bpy, math
from mathutils import Vector
import geo

COLLS = ['Castle', 'Terrain', 'Water', 'Nature', 'Lights', 'FX', 'Cameras']


def setup_collections():
    for c in COLLS:
        geo.get_coll(c)


def clean_default():
    for n in ('Cube', 'Light', 'Camera'):
        o = bpy.data.objects.get(n)
        if o:
            d = o.data
            bpy.data.objects.remove(o, do_unlink=True)
    for blk in (bpy.data.meshes, bpy.data.lights, bpy.data.cameras):
        for d in list(blk):
            if d.users == 0:
                blk.remove(d)


def render_settings(final=False, pct=25, samples=64):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    cy.device = 'GPU'
    sc.render.resolution_x = 3840
    sc.render.resolution_y = 2160
    sc.render.resolution_percentage = 100 if final else pct
    cy.samples = 1024 if final else samples
    cy.use_adaptive_sampling = not final   # finals: the full 1024 samples on every pixel
    cy.adaptive_threshold = 0.03
    cy.use_denoising = True
    cy.denoiser = 'OPTIX'
    cy.max_bounces = 8
    cy.diffuse_bounces = 3
    cy.glossy_bounces = 4
    cy.transmission_bounces = 8
    cy.volume_bounces = 1
    cy.transparent_max_bounces = 12
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.blur_glossy = 0.5
    cy.sample_clamp_indirect = 8.0
    cy.volume_step_rate = 1.0
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_depth = '16' if final else '8'
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.view_settings.exposure = 1.2
    sc.view_settings.gamma = 1.0
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0


def add_camera(name, loc, target, lens=35.0, shift_y=0.0, shift_x=0.0, fstop=None, focus=None, roll=0.0):
    coll = geo.get_coll('Cameras')
    ob = bpy.data.objects.get(name)
    if ob is None:
        cam = bpy.data.cameras.new(name)
        ob = bpy.data.objects.new(name, cam)
        coll.objects.link(ob)
    cam = ob.data
    cam.lens = lens
    cam.sensor_width = 36.0
    cam.clip_start = 0.5
    cam.clip_end = 30000.0
    cam.shift_y = shift_y
    cam.shift_x = shift_x
    ob.location = Vector(loc)
    d = Vector(target) - Vector(loc)
    rot = d.to_track_quat('-Z', 'Y').to_euler()
    rot.rotate_axis('Z', math.radians(roll))
    ob.rotation_euler = rot
    if fstop:
        cam.dof.use_dof = True
        cam.dof.aperture_fstop = fstop
        cam.dof.focus_distance = focus if focus else d.length
    else:
        cam.dof.use_dof = False
    return ob


def set_cam(name):
    bpy.context.scene.camera = bpy.data.objects[name]
