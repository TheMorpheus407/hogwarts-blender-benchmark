# Thin the mist veil so moonlight/windows read; final pass
import bpy

scn = bpy.context.scene
scn.view_settings.exposure = 0.55

def tune_mist(name, dens_old, dens_new, col):
    m = bpy.data.materials.get(name)
    if not m: return None
    nt = m.node_tree
    hit = None
    for n in nt.nodes:
        if n.type == 'MATH' and n.operation == 'MULTIPLY' and abs(n.inputs[1].default_value - dens_old) < 1e-4:
            n.inputs[1].default_value = dens_new
            hit = dens_new
    for n in nt.nodes:
        if n.type == 'RGB':
            n.outputs[0].default_value = (*col, 1.0)
    return hit

r1 = tune_mist("Mist_Lake", 0.0045, 0.0026, (0.42, 0.52, 0.72))
r2 = tune_mist("Mist_Gorge", 0.0055, 0.0032, (0.45, 0.55, 0.75))
r3 = tune_mist("Mist_Moor_N", 0.0035, 0.0020, (0.42, 0.52, 0.72))
r4 = tune_mist("Mist_W", 0.0040, 0.0024, (0.42, 0.52, 0.72))

gm = bpy.data.materials["M_WindowGlass"]
for n in gm.node_tree.nodes:
    if n.type == 'MATH' and n.operation == 'MULTIPLY' and abs(n.inputs[1].default_value - 14.0) < 0.1:
        n.inputs[1].default_value = 18.0

bpy.ops.wm.save_as_mainfile(filepath="/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/hogwarts.blend")
result = {"mists": (r1, r2, r3, r4)}
