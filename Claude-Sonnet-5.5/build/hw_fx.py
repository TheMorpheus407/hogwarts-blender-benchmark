"""Atmospheric volumes: world haze + low lake mist that pools in valleys."""
import bpy
import numpy as np
import math
from hw_nodes import NB, get_mat
import hw_scene as S


def clear_world_volume():
    w = bpy.context.scene.world
    nt = w.node_tree
    for n in list(nt.nodes):
        if n.name.startswith('HAZE'):
            nt.nodes.remove(n)


def build_haze_material(name='M_Haze', sigma0=0.85e-4, scale_h=1000.0, color=(0.36, 0.52, 0.78), aniso=0.42):
    nb = NB(get_mat(name))
    P = nb.geometry().outputs['Position']
    z = nb.sepxyz(P).outputs[2]
    tc = nb.texcoord().outputs['Generated']
    g = nb.sepxyz(tc)
    gx, gy = g.outputs[0], g.outputs[1]
    edge = nb.mul(nb.mul(nb.smooth(gx, 0.0, 0.14), nb.smooth(nb.sub(1.0, gx), 0.0, 0.14)),
                  nb.mul(nb.smooth(gy, 0.0, 0.14), nb.smooth(nb.sub(1.0, gy), 0.0, 0.14)))
    prof = nb.math('EXPONENT', nb.mul(nb.math('MAXIMUM', z, 0.0), -1.0 / scale_h))
    # slight large-scale patchiness so ridges do not fade uniformly
    n = nb.noise(nb.mapping(P, scale=(0.0007, 0.0007, 0.0014)), scale=1.0, detail=3, rough=0.5)
    dens = nb.mul(nb.mul(nb.mul(prof, edge), nb.add(0.7, nb.mul(n, 0.6))), sigma0)
    vs = nb.node('ShaderNodeVolumeScatter')
    vs.inputs['Color'].default_value = (*color, 1.0)
    vs.inputs['Anisotropy'].default_value = aniso
    nb._in(vs, 'Density', dens)
    nb.output(volume=vs.outputs[0])
    return nb.mat


def haze_object(name='FX_Haze', half=15000.0, z0=-20.0, z1=3200.0):
    coll = S.ensure_collection('FX')
    S.remove_object(name)
    mesh = bpy.data.meshes.new(name)
    V = np.array([[-half, -half, z0], [half, -half, z0], [half, half, z0], [-half, half, z0],
                  [-half, -half, z1], [half, -half, z1], [half, half, z1], [-half, half, z1]], np.float32)
    F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh.from_pydata(V.tolist(), [], F)
    mesh.update()
    mesh.materials.append(bpy.data.materials.get('M_Haze') or build_haze_material())
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    obj.visible_shadow = False
    obj.display_type = 'BOUNDS'
    return obj


def build_mist_material(name='M_Mist', base=0.030, height=12.0, top=70.0):
    """Ground mist: banks hugging the water and the low ground, wispy structure, thin right at the camera."""
    nb = NB(get_mat(name))
    geo = nb.geometry()
    P = geo.outputs['Position']
    sp_ = nb.sepxyz(P)
    x, y, z = sp_.outputs[0], sp_.outputs[1], sp_.outputs[2]
    tc = nb.texcoord().outputs['Generated']
    g = nb.sepxyz(tc)
    gx, gy, gz = g.outputs[0], g.outputs[1], g.outputs[2]
    edge = nb.mul(nb.mul(nb.smooth(gx, 0.0, 0.10), nb.smooth(nb.sub(1.0, gx), 0.0, 0.10)),
                  nb.mul(nb.smooth(gy, 0.0, 0.10), nb.smooth(nb.sub(1.0, gy), 0.0, 0.10)))
    # vertical profile: dense at the water, thinning upwards; the low ground (valleys, shore) sits inside the layer
    zc = nb.math('MAXIMUM', z, 0.0)
    vprof = nb.mul(nb.math('EXPONENT', nb.mul(zc, -1.0 / height)), 0.55)
    skim = nb.mul(nb.math('EXPONENT', nb.mul(zc, -1.0 / 2.6)), 0.95)        # dense sheet skimming the water
    pool = nb.mul(nb.smooth(z, 46.0, 4.0), 0.34)
    prof = nb.add(nb.add(vprof, skim), pool)
    # banks (large scale, stretched along the shore) + wisps (medium) + fine breakup, layer height wobbles too
    q1 = nb.combxyz(nb.mul(x, 0.0034), nb.mul(y, 0.0058), nb.mul(z, 0.020))
    banks = nb.noise(q1, scale=1.0, detail=4, rough=0.55)
    q2 = nb.combxyz(nb.mul(x, 0.011), nb.mul(y, 0.024), nb.mul(z, 0.05))
    wisps = nb.noise(q2, scale=1.0, detail=4, rough=0.55)
    q3 = nb.combxyz(nb.mul(x, 0.045), nb.mul(y, 0.075), nb.mul(z, 0.14))
    fine = nb.noise(q3, scale=1.0, detail=3, rough=0.5)
    shape = nb.add(nb.add(nb.mul(banks, 0.62), nb.mul(wisps, 0.30)), nb.mul(fine, 0.12))
    patch = nb.smooth(shape, 0.47, 0.70)
    rl = nb.lightpath().outputs['Ray Length']
    near = nb.smooth(rl, 90.0, 420.0)            # thin near the camera, builds up into the distance
    dens = nb.mul(nb.mul(nb.mul(nb.mul(prof, patch), edge), base), nb.add(0.10, nb.mul(near, 0.90)))
    vs = nb.node('ShaderNodeVolumeScatter')
    vs.inputs['Color'].default_value = (0.62, 0.76, 0.92, 1.0)
    vs.inputs['Anisotropy'].default_value = 0.35
    nb._in(vs, 'Density', dens)
    nb.output(volume=vs.outputs[0])
    return nb.mat


def mist_object(name='FX_LakeMist', center=(0.0, -700.0), size=(3800.0, 2800.0), z0=-6.0, z1=110.0):
    coll = S.ensure_collection('FX')
    S.remove_object(name)
    mesh = bpy.data.meshes.new(name)
    cx, cy = center
    hx, hy = size[0] / 2, size[1] / 2
    V = np.array([[cx - hx, cy - hy, z0], [cx + hx, cy - hy, z0], [cx + hx, cy + hy, z0], [cx - hx, cy + hy, z0],
                  [cx - hx, cy - hy, z1], [cx + hx, cy - hy, z1], [cx + hx, cy + hy, z1], [cx - hx, cy + hy, z1]], np.float32)
    F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh.from_pydata(V.tolist(), [], F)
    mesh.update()
    mesh.materials.append(bpy.data.materials.get('M_Mist') or build_mist_material())
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    obj.visible_shadow = False
    obj.display_type = 'BOUNDS'
    return obj


def volume_settings(step_rate=1.0, max_steps=1024, bounces=2):
    c = bpy.context.scene.cycles
    c.volume_step_rate = step_rate
    c.volume_preview_step_rate = 1.0
    c.volume_max_steps = max_steps
    c.volume_bounces = bounces


def gorge_mist_object(name='FX_GorgeMist', x0=110.0, x1=345.0, y0=-260.0, y1=330.0, z0=-8.0, z1=52.0):
    """Mist pooling in the east gorge under the viaduct."""
    coll = S.ensure_collection('FX')
    S.remove_object(name)
    mesh = bpy.data.meshes.new(name)
    V = np.array([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]], np.float32)
    F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh.from_pydata(V.tolist(), [], F)
    mesh.update()
    nb = NB(get_mat('M_GorgeMist'))
    P = nb.geometry().outputs['Position']
    sp_ = nb.sepxyz(P)
    x, y, z = sp_.outputs[0], sp_.outputs[1], sp_.outputs[2]
    tc = nb.texcoord().outputs['Generated']
    g = nb.sepxyz(tc)
    gx, gy, gz = g.outputs[0], g.outputs[1], g.outputs[2]
    edge = nb.mul(nb.mul(nb.smooth(gx, 0.0, 0.30), nb.smooth(nb.sub(1.0, gx), 0.0, 0.30)),
                  nb.mul(nb.smooth(gy, 0.0, 0.22), nb.smooth(nb.sub(1.0, gy), 0.0, 0.22)))
    vprof = nb.mul(nb.math('EXPONENT', nb.mul(nb.math('MAXIMUM', nb.sub(z, z0), 0.0), -1.0 / 13.0)), nb.smooth(nb.sub(1.0, gz), 0.0, 0.3))
    n1 = nb.noise(nb.combxyz(nb.mul(x, 0.008), nb.mul(y, 0.0055), nb.mul(z, 0.085)), scale=1.0, detail=4, rough=0.55)
    patch = nb.smooth(n1, 0.30, 0.78)
    rl = nb.lightpath().outputs['Ray Length']
    near = nb.smooth(rl, 120.0, 420.0)
    dens = nb.mul(nb.mul(nb.mul(nb.mul(vprof, patch), edge), 0.0032), nb.add(0.1, nb.mul(near, 0.9)))
    vs = nb.node('ShaderNodeVolumeScatter')
    vs.inputs['Color'].default_value = (0.36, 0.48, 0.66, 1.0)
    vs.inputs['Anisotropy'].default_value = 0.18
    nb._in(vs, 'Density', dens)
    nb.output(volume=vs.outputs[0])
    mesh.materials.append(nb.mat)
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    obj.visible_shadow = False
    obj.display_type = 'BOUNDS'
    return obj
