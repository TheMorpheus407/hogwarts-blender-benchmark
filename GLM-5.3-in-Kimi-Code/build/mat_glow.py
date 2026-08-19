# Window glass, lantern glow, clock face materials
import bpy
exec(compile(open("/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/build/mat_common.py").read(), "mat_common.py", "exec"))

# ============ WINDOW GLASS (emissive w/ per-vertex glow+warm) ============
m = new_mat("M_WindowGlass"); nt = m.node_tree
bs = nt.nodes.get("Principled BSDF"); bs.location = (400, 100)
nt.nodes["Material Output"].location = (700, 100)
glow_a = mknode(nt, "ShaderNodeAttribute", (-600, 300)); glow_a.attribute_name = "glow"
warm_a = mknode(nt, "ShaderNodeAttribute", (-600, 0)); warm_a.attribute_name = "warm"
g = glow_a.outputs['Fac']
wfac = clampn(nt, warm_a.outputs['Fac'], 0.0, 1.0, loc=(-420, 0))
warm_col = mixc(nt, rgb(nt, (1.0, 0.62, 0.28), (-400, -60)), rgb(nt, (1.0, 0.85, 0.62), (-400, -140)), wfac, loc=(-240, -80))
dark_col = rgb(nt, (0.01, 0.015, 0.02), (-240, 160))
gcol = mixc(nt, dark_col, warm_col, clampn(nt, mathn(nt, 'MULTIPLY', g, 1.0, loc=(-400, 300)), 0.0, 1.0, loc=(-260, 300)), loc=(-100, 100))
L(nt, gcol, 0, bs, "Base Color")
strength = mathn(nt, 'MULTIPLY', g, 7.0, loc=(-100, 300))
L(nt, strength, 0, bs, "Emission Strength")
L(nt, warm_col, 0, bs, "Emission Color")
setbs(bs, **{"Roughness": 0.04, "Metallic": 0.0, "IOR": 1.5,
             "Specular IOR Level": 0.6, "Transmission Weight": 0.0})

# ============ LANTERN GLASS ============
m = new_mat("M_LanternGlass"); nt = m.node_tree
bs = nt.nodes.get("Principled BSDF"); bs.location = (400, 100)
nt.nodes["Material Output"].location = (700, 100)
glow_a = mknode(nt, "ShaderNodeAttribute", (-400, 200)); glow_a.attribute_name = "glow"
L(nt, rgb(nt, (1.0, 0.55, 0.22), (0, 0)), 0, bs, "Emission Color")
L(nt, mathn(nt, 'MULTIPLY', glow_a.outputs['Fac'], 16.0, loc=(-100, 200)), 0, bs, "Emission Strength")
setbs(bs, **{"Base Color": (0.2, 0.1, 0.04, 1.0), "Roughness": 0.1})

# ============ CLOCK FACE ============
m = new_mat("M_ClockFace"); nt = m.node_tree
bs = nt.nodes.get("Principled BSDF"); bs.location = (400, 100)
nt.nodes["Material Output"].location = (700, 100)
setbs(bs, **{"Base Color": (0.82, 0.79, 0.72, 1.0), "Roughness": 0.5})
L(nt, rgb(nt, (0.55, 0.53, 0.48), (0,0)), 0, bs, "Emission Color")
mknode(nt, "ShaderNodeValue", (-100, 200)).outputs[0].default_value = 0.20
valnode = [n for n in nt.nodes if n.type == 'VALUE'][0]
L(nt, valnode.outputs[0], 0, bs, "Emission Strength")

# assign material slots
wins = bpy.data.objects["Windows"]
wins.data.materials.clear()
wins.data.materials.append(bpy.data.materials["M_WindowGlass"])
wins.data.materials.append(bpy.data.materials["M_StoneWall"])

lans = bpy.data.objects["Lanterns"]
lans.data.materials.clear()
lans.data.materials.append(bpy.data.materials["M_LanternGlass"])
lans.data.materials.append(bpy.data.materials["M_StoneWall"])

clk = bpy.data.objects["ClockFaces"]
clk.data.materials.clear()
clk.data.materials.append(bpy.data.materials["M_ClockFace"])
clk.data.materials.append(bpy.data.materials["M_StoneWall"])
clk.data.materials.append(bpy.data.materials["M_Copper"])

result = {"ok": True}
