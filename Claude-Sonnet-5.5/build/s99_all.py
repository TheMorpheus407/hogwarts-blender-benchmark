"""Master build: rebuilds the whole scene deterministically.  run(quality='preview'|'final')."""
import sys
import importlib
import time
import bpy
import numpy as np

LIB = ['hw_noise', 'hw_geo', 'hw_arch', 'hw_gothic', 'hw_towers', 'hw_halls', 'hw_layout', 'hw_terrain', 'hw_walls',
       'hw_viaduct', 'hw_boathouse', 'hw_glass', 'hw_trees', 'hw_props', 'hw_nature', 'hw_nodes', 'hw_mats', 'hw_atmo',
       'hw_fx', 'hw_lights', 'hw_scene', 'hw_cams', 'hw_comp']
STAGES = ['s01_terrain', 's03_castle', 's04_lower', 's05_extras', 's07_terrace', 's08_props', 's06_nature']


def reload_all():
    for m in LIB + STAGES:
        if m in sys.modules:
            importlib.reload(sys.modules[m])
        else:
            importlib.import_module(m)
    import hw_gothic
    hw_gothic._CACHE.clear()


def run(quality='preview', skip=(), save=True):
    reload_all()
    import hw_scene as S
    import hw_mats
    import hw_atmo
    import hw_fx
    import hw_lights
    import hw_walls
    import s01_terrain as s1
    import s03_castle as c3
    import s04_lower as s4
    import s05_extras as s5
    import s07_terrace as s7
    import s08_props as s8
    import s06_nature as s6
    out = {}
    t0 = time.time()
    S.fresh_scene()
    hw_walls.LAMP_REG.clear()
    # materials first (objects bind by name)
    if 'mats' not in skip:
        hw_mats.build_all_castle()
        hw_mats.build_all_landscape()
        hw_mats.build_all_nature()
        hw_mats.build_all_glasshouse()
        hw_mats.build_all_props()
    out['t_mats'] = round(time.time() - t0, 1)
    out['terrain'] = s1.run(quality)
    out['t_terrain'] = round(time.time() - t0, 1)
    S.clear_collection('Castle')
    out['castle'] = c3.run(clear=False)
    out['lower'] = s4.run()
    out['extras'] = s5.run()
    out['terrace'] = s7.run()
    out['props'] = s8.run()
    out['t_castle'] = round(time.time() - t0, 1)
    out['nature'] = s6.run(max_points=(140000 if quality == 'final' else 60000))
    out['rocks'] = s6.run_rocks()
    out['shore'] = s6.run_shore()
    hw_atmo.build_world()
    hw_atmo.build_lights()
    hw_atmo.set_color_management()
    hw_fx.clear_world_volume()
    hw_fx.build_haze_material()
    hw_fx.haze_object()
    hw_fx.build_mist_material()
    hw_fx.mist_object()
    hw_fx.gorge_mist_object()
    hw_fx.volume_settings()
    out['lamps'] = hw_lights.build()
    import hw_cams, hw_comp
    hw_cams.remove_test_cameras()
    hw_cams.build()
    hw_comp.build()
    import hw_geo
    out['windows'] = dict(hw_geo.WIN_STATS)
    out['t'] = round(time.time() - t0, 1)
    if save:
        import os
        path = S.BASE + '/hogwarts.blend'
        bpy.ops.wm.save_as_mainfile(filepath=path, compress=False)
        out['saved_mb'] = round(os.path.getsize(path) / 1e6, 1)
    return out
