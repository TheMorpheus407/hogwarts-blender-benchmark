"""Entry point executed through the Blender MCP:
    exec(open(RUN).read()); stage('terrain') ...
"""
import sys, importlib, time
ROOT = '/home/morpheus/Documents/Morpheus-Produktion/Benchmarks/Blender/Claude-Opus-5.5'
SCR = ROOT + '/scripts'
if SCR not in sys.path:
    sys.path.insert(0, SCR)

MODS = ['geo', 'arch', 'terrain', 'crag', 'materials', 'scene', 'castle', 'nature', 'env', 'cameras', 'props']


def reload_all():
    out = {}
    for m in MODS:
        try:
            if m in sys.modules:
                importlib.reload(sys.modules[m])
            else:
                importlib.import_module(m)
        except ModuleNotFoundError as e:
            out[m] = str(e)
    return out


def mod(name):
    return sys.modules[name]


def render(cam, name, pct=25, samples=32):
    import bpy
    sc = bpy.context.scene
    sc.camera = bpy.data.objects[cam]
    sc.render.resolution_percentage = pct
    sc.cycles.samples = samples
    sc.render.filepath = ROOT + '/wip/' + name + '.png'
    t = time.time()
    bpy.ops.render.render(write_still=True)
    return time.time() - t


def build_all(terrain_n=760, save=True):
    import bpy
    t0 = time.time()
    log = {}
    reload_all()
    sc = mod('scene')
    sc.clean_default()
    sc.setup_collections()
    mod('materials').build_all()
    mod('terrain').build(N=terrain_n)
    mod('crag').build()
    log['castle'] = mod('castle').build()
    log['forest'] = mod('nature').build_forest()
    log['props'] = mod('props').build()
    env = mod('env')
    env.world(1.0)
    env.moon_light()
    env.fill_light() if hasattr(env, 'fill_light') else None
    env.water_plane()
    env.mist(lake_density=0.0012, haze_density=0.00004)
    log['lights'] = env.lanterns(mod('castle').LANTERNS, mod('castle').GLOW_LIGHTS + mod('props').LIGHTS)
    mod('cameras').setup()
    sc.render_settings(final=False)
    purge()
    if save:
        bpy.ops.wm.save_as_mainfile(filepath=ROOT + '/hogwarts.blend')
    log['t'] = time.time() - t0
    return log


def _try_import(m):
    try:
        importlib.import_module(m)
        return True
    except ModuleNotFoundError:
        return False


def purge():
    import bpy
    for _ in range(3):
        bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)


def render_crop(cam, name, x0, x1, y0, y1, samples=256, pct=100):
    """render a border crop (fractions, y from bottom) at full resolution."""
    import bpy
    sc = bpy.context.scene
    r = sc.render
    r.use_border = True
    r.use_crop_to_border = True
    r.border_min_x, r.border_max_x, r.border_min_y, r.border_max_y = x0, x1, y0, y1
    try:
        return render(cam, name, pct, samples)
    finally:
        r.use_border = False
        r.use_crop_to_border = False


def render_async(cam, path, pct=100, samples=1024, final=True):
    """start a non-blocking render job that writes 'path' when done; poll with render_busy()."""
    import bpy
    sc = bpy.context.scene
    mod('scene').render_settings(final=final, pct=pct, samples=samples)
    sc.render.resolution_percentage = pct
    sc.cycles.samples = samples
    sc.camera = bpy.data.objects[cam]
    sc.render.filepath = path
    sc.render.use_border = False
    global _T0
    _T0 = time.time()
    return bpy.ops.render.render('INVOKE_DEFAULT', write_still=True)


def render_busy():
    import bpy
    return {'busy': bpy.app.is_job_running('RENDER'), 'elapsed': time.time() - _T0}
