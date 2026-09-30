"""Local warm lights from the lamp registry (hw_walls.LAMP_REG)."""
import bpy
import math
import hw_scene as S
import hw_walls as W

CATS = {
    'stair': dict(energy=260.0, color=(1.0, 0.55, 0.20), radius=0.14),
    'viaduct': dict(energy=340.0, color=(1.0, 0.56, 0.22), radius=0.14),
    'boat': dict(energy=300.0, color=(1.0, 0.55, 0.20), radius=0.14),
    'terrace': dict(energy=260.0, color=(1.0, 0.56, 0.22), radius=0.14),
    'court': dict(energy=380.0, color=(1.0, 0.58, 0.24), radius=0.16),
    'interior': dict(energy=1200.0, color=(1.0, 0.86, 0.55), radius=0.5),
}


def build(reg=None, scale=1.0):
    reg = reg if reg is not None else W.LAMP_REG
    coll = S.ensure_collection('Lights')
    for o in list(coll.objects):
        if o.name.startswith('Lamp_'):
            d = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if d is not None and d.users == 0:
                bpy.data.lights.remove(d)
    n = 0
    for cat, pts in reg.items():
        p = CATS.get(cat, CATS['court'])
        for i, (x, y, z) in enumerate(pts):
            name = 'Lamp_%s_%03d' % (cat, i)
            ld = bpy.data.lights.new(name, 'POINT')
            ld.energy = p['energy'] * scale
            ld.color = p['color']
            ld.shadow_soft_size = p['radius']
            o = bpy.data.objects.new(name, ld)
            o.location = (x, y, z)
            coll.objects.link(o)
            n += 1
    return n
