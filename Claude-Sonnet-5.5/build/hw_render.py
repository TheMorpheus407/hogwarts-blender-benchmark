"""Final-quality render configuration + asynchronous rendering of the deliverables."""
import bpy
import math
import os
import time
import hw_scene as S

BASE = S.BASE

# per-camera composition tuning (exposure in stops, depth of field)
FILL_DEFAULT = (110.0, 27.0)          # azimuth (from north, towards east), elevation of the cool sky-fill sun

SHOTS = {
    'Cam_Hero': dict(file='hero.png', exposure=0.35, dof=None),
    'Cam_Aerial': dict(file='angle_aerial.png', exposure=1.15, dof=None),
    'Cam_Boathouse': dict(file='angle_boathouse.png', exposure=0.65, dof=dict(focus=(-48.0, -100.0, 8.0), fstop=6.3)),
    'Cam_Viaduct': dict(file='angle_viaduct.png', exposure=0.55, dof=dict(focus=(60.0, -2.0, 60.0), fstop=9.0), fill=(40.0, 24.0)),
    'Cam_Detail_01': dict(file='detail_01.png', exposure=0.9, dof=dict(focus=(-96.0, 8.0, 150.0), fstop=4.0)),
    'Cam_Detail_02': dict(file='detail_02.png', exposure=0.75, dof=dict(focus=(-48.0, -106.0, 6.0), fstop=3.2)),
    'Cam_Detail_03': dict(file='detail_03.png', exposure=0.75, dof=dict(focus=(-158.0, -21.0, 66.0), fstop=3.5)),
}


def configure(samples=1024, res=(3840, 2160), pct=100, denoise=True, adaptive=True, threshold=0.004, min_samples=96):
    sc = bpy.context.scene
    S.cycles_setup(samples=samples, res=res, pct=pct, denoise=denoise, adaptive=adaptive, denoiser='OPENIMAGEDENOISE')
    c = sc.cycles
    c.adaptive_threshold = threshold
    c.adaptive_min_samples = min_samples
    c.use_light_tree = True
    # ray-marched (biased) volumes: same converged image as delta tracking here, but ~20x faster on the mist volumes
    c.volume_biased = True
    c.use_volume_guiding = False
    c.volume_step_rate = 0.75
    c.volume_max_steps = 1024
    c.max_bounces = 12
    c.diffuse_bounces = 4
    c.glossy_bounces = 6
    c.transmission_bounces = 8
    c.volume_bounces = 2
    c.transparent_max_bounces = 10
    c.sample_clamp_direct = 0.0
    c.sample_clamp_indirect = 8.0
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.blur_glossy = 0.5
    c.film_exposure = 1.0
    try:
        c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
        c.denoising_prefilter = 'ACCURATE'
        c.denoising_quality = 'HIGH'
        c.denoising_use_gpu = True
    except Exception:
        pass
    sc.render.film_transparent = False
    sc.render.filter_size = 1.3
    sc.render.dither_intensity = 1.0
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.image_settings.color_depth = '8'
    sc.render.image_settings.compression = 15
    sc.render.use_persistent_data = False
    return dict(samples=c.samples, res=(sc.render.resolution_x, sc.render.resolution_y), pct=sc.render.resolution_percentage,
                denoise=c.use_denoising, denoiser=c.denoiser)


def apply_shot(cam_name):
    sc = bpy.context.scene
    shot = SHOTS[cam_name]
    cam = bpy.data.objects[cam_name]
    sc.camera = cam
    sc.view_settings.exposure = shot['exposure']
    fill = bpy.data.objects.get('Sky_Fill')
    if fill is not None:
        import hw_atmo
        az, el = shot.get('fill', FILL_DEFAULT)
        hw_atmo.aim_light(fill, hw_atmo.moon_vec(az=az, el=el))
    d = shot.get('dof')
    if d is None:
        cam.data.dof.use_dof = False
    else:
        cam.data.dof.use_dof = True
        from mathutils import Vector
        dist = (Vector(d['focus']) - cam.location).length
        cam.data.dof.focus_distance = dist
        cam.data.dof.aperture_fstop = d['fstop']
    return shot


def render_still(cam_name, out_dir=BASE, filename=None, write=True):
    shot = apply_shot(cam_name)
    path = os.path.join(out_dir, filename or shot['file'])
    bpy.context.scene.render.filepath = path
    t0 = time.time()
    bpy.ops.render.render(write_still=write)
    return path, round(time.time() - t0, 1)


# ---------------------------------------------------------------------------------------------------------
# unattended chain of final renders (timer driven, one job at a time)
# ---------------------------------------------------------------------------------------------------------
ORDER = ['Cam_Hero', 'Cam_Aerial', 'Cam_Boathouse', 'Cam_Viaduct', 'Cam_Detail_01', 'Cam_Detail_02', 'Cam_Detail_03']
CHAIN = dict(queue=[], done=[], running=None, out_dir=BASE, active=False)


def _chain_tick():
    if bpy.app.is_job_running('RENDER'):
        return 20.0
    r = CHAIN['running']
    if r is not None:
        ok = os.path.exists(r['path']) and os.path.getmtime(r['path']) >= r['t0']
        CHAIN['done'].append(dict(cam=r['cam'], file=os.path.basename(r['path']), ok=bool(ok),
                                  minutes=round((time.time() - r['t0']) / 60.0, 1)))
        CHAIN['running'] = None
    if not CHAIN['queue']:
        CHAIN['active'] = False
        return None
    cam = CHAIN['queue'].pop(0)
    shot = apply_shot(cam)
    path = os.path.join(CHAIN['out_dir'], shot['file'])
    bpy.context.scene.render.filepath = path
    CHAIN['running'] = dict(cam=cam, path=path, t0=time.time())
    try:
        bpy.ops.render.render('INVOKE_DEFAULT', write_still=True)
    except Exception as e:                      # keep the chain alive; the failure shows up in `done`
        CHAIN['done'].append(dict(cam=cam, file=shot['file'], ok=False, error=str(e)[:200]))
        CHAIN['running'] = None
    return 20.0


def chain_start(cams=None, out_dir=BASE, **cfg):
    """Configure the final settings and render `cams` one after another without any further interaction."""
    info = configure(**cfg)
    CHAIN.update(queue=list(cams or ORDER), done=[], running=None, out_dir=out_dir, active=True)
    bpy.app.timers.register(_chain_tick, first_interval=2.0)
    return info


def chain_status():
    r = CHAIN['running']
    return dict(active=CHAIN['active'], job=bool(bpy.app.is_job_running('RENDER')),
                running=None if r is None else dict(cam=r['cam'], minutes=round((time.time() - r['t0']) / 60.0, 1)),
                queue=list(CHAIN['queue']), done=list(CHAIN['done']))
