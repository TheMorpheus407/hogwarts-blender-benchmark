# Final light rebalance: deeper night, windows/lanterns pop
import bpy
import bpy as _b

scn = bpy.context.scene
scn.view_settings.exposure = 0.62

# moon key light: dimmer
bpy.data.objects["MoonSun"].data.energy = 2.1

# window glass emission back up
gm = bpy.data.materials["M_WindowGlass"]
for n in gm.node_tree.nodes:
    if n.type == 'MATH' and n.operation == 'MULTIPLY' and abs(n.inputs[1].default_value - 7.0) < 0.1:
        n.inputs[1].default_value = 14.0
# lantern glass
lm = bpy.data.materials["M_LanternGlass"]
for n in lm.node_tree.nodes:
    if n.type == 'MATH' and n.operation == 'MULTIPLY' and abs(n.inputs[1].default_value - 16.0) < 0.1:
        n.inputs[1].default_value = 24.0
# clock face softly luminous
cm = bpy.data.materials["M_ClockFace"]
for n in cm.node_tree.nodes:
    if n.type == 'VALUE':
        n.outputs[0].default_value = 0.4

# fill light dimmer
f = bpy.data.objects.get("Fill_West")
if f: f.data.energy = 0.25

bpy.ops.wm.save_as_mainfile(filepath="/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/hogwarts.blend")
result = {"ok": True, "exposure": scn.view_settings.exposure}
