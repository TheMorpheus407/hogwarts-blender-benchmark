# Windows/lanterns: keep them in AgX's color-preserving range so they glow ORANGE
import bpy
gm = bpy.data.materials["M_WindowGlass"]
for n in gm.node_tree.nodes:
    if n.type == 'MATH' and n.operation == 'MULTIPLY' and abs(n.inputs[1].default_value - 18.0) < 0.1:
        n.inputs[1].default_value = 5.0
# deepen emission color slightly
bs = [n for n in gm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
for l in gm.node_tree.links:
    pass
for n in gm.node_tree.nodes:
    if n.type == 'RGB':
        c = n.outputs[0].default_value
        # the two warm mix colors of window material: make them more saturated
        if abs(c[0] - 1.0) < 0.01 and abs(c[1] - 0.62) < 0.02:
            n.outputs[0].default_value = (1.0, 0.45, 0.16, 1.0)
        elif abs(c[0] - 1.0) < 0.01 and abs(c[1] - 0.85) < 0.02:
            n.outputs[0].default_value = (1.0, 0.72, 0.42, 1.0)

lm = bpy.data.materials["M_LanternGlass"]
for n in lm.node_tree.nodes:
    if n.type == 'MATH' and n.operation == 'MULTIPLY' and abs(n.inputs[1].default_value - 24.0) < 0.1:
        n.inputs[1].default_value = 9.0
for n in lm.node_tree.nodes:
    if n.type == 'RGB' and abs(n.outputs[0].default_value[0] - 1.0) < 0.01 and n.outputs[0].default_value[1] < 0.7:
        n.outputs[0].default_value = (1.0, 0.42, 0.14, 1.0)

bpy.ops.wm.save_as_mainfile(filepath="/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/hogwarts.blend")
result = {"ok": True}
