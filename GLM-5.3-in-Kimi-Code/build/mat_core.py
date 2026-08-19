# Build core surface materials (stone, slate, copper, rock, moor, water)
import bpy, math
exec(compile(open("/home/morpheus/Documents/Projects/Blender/GLM-5.3-in-Kimi-Code/build/mat_common.py").read(), "mat_common.py", "exec"))

# ================= STONE WALL =================
m, nt, bs = std_mat("M_StoneWall", (0.36,0.345,0.315), 0.86)
pos = geo_out(nt, "Position", (-1500, 0))
sep = mknode(nt, "ShaderNodeSeparateXYZ", (-1350, 600)); L(nt, pos, 0, sep, 0)
n1 = noise(nt, 0.045, 5, loc=(-1150, 250), vec=pos)
col_a = rgb(nt, (0.46,0.44,0.41), (-1150, 450))
col_b = rgb(nt, (0.27,0.26,0.245), (-1150, 350))
base = mixc(nt, col_a, col_b, mathn(nt, 'MULTIPLY', n1.outputs['Fac'], 0.8, loc=(-950,300)), loc=(-800, 380))
tint_attr = mknode(nt, "ShaderNodeAttribute", (-950, 150)); tint_attr.attribute_name = "tint"
tinted = mixc(nt, base, tint_attr.outputs['Color'], val(nt, 0.65, (-800, 140)), loc=(-650, 340))
nfine = noise(nt, 2.4, 4, loc=(-650, 80), vec=pos)
fine = mixc(nt, rgb(nt,(0.88,0.88,0.87),(-500,50)), rgb(nt,(1.10,1.08,1.04),(-500,0)), nfine.outputs['Fac'], loc=(-430, 30))
fine.node.blend_type = 'MULTIPLY'
col2 = mixc(nt, tinted, fine, val(nt, 0.30, (-420, 90)), loc=(-330, -20))
# dirt: stretched noise * AO
mapping = mknode(nt, "ShaderNodeMapping", (-1150, -200))
mapping.inputs['Scale'].default_value = (2.0, 2.0, 0.30)
texco = mknode(nt, "ShaderNodeTexCoord", (-1400, -200)); L(nt, texco, 0, mapping, 0)
ndirt = noise(nt, 1.0, 3, loc=(-1000, -200), vec=mapping.outputs[0])
ao = mknode(nt, "ShaderNodeAmbientOcclusion", (-1000, -400)); ao.inputs['Distance'].default_value = 1.5
dfac = mathn(nt, 'POWER', ndirt.outputs['Fac'], 1.6, loc=(-850,-190))
dfac = mathn(nt, 'MULTIPLY', dfac, mathn(nt, 'ADD', ao.outputs[0], 0.30), loc=(-750,-260))
col3 = mixc(nt, col2, rgb(nt, (0.15,0.14,0.125), (-720,-60)), mathn(nt, 'MULTIPLY', dfac, 0.55), loc=(-560, -40))
# moss: up-normal * noise * ao, biased low
nrm = mknode(nt, "ShaderNodeNormal", (-1150, 620))
nsep = mknode(nt, "ShaderNodeSeparateXYZ", (-1000, 620)); L(nt, nrm, 0, nsep, 0)
up = mathn(nt, 'SUBTRACT', nsep.outputs[2], 0.25, loc=(-900, 620))
up = clampn(nt, up)
nmos = noise(nt, 0.30, 4, loc=(-900, 460), vec=pos)
lowbias = mathn(nt, 'SUBTRACT', 24.0, sep.outputs[2], loc=(-900, 760))
lowbias = clampn(nt, lowbias, loc=(-850, 760))
mf = mathn(nt, 'MULTIPLY', up, nmos.outputs['Fac'], loc=(-750, 560))
mf = mathn(nt, 'MULTIPLY', mf, mathn(nt, 'MULTIPLY', ao.outputs[0], 1.3), loc=(-700, 460))
mf = mathn(nt, 'MULTIPLY', mf, lowbias, loc=(-620, 520))
final = mixc(nt, col3, rgb(nt, (0.075,0.115,0.05), (-560, 400)), mathn(nt, 'MULTIPLY', mf, 0.85, loc=(-540,460)), loc=(-380, 200))
pnt = geo_out(nt, "Pointiness", (-600, -500))
if pnt is not None:
    wear = mathn(nt, 'MULTIPLY', mathn(nt, 'MAXIMUM', pnt, 0.0, loc=(-500,-500)), 0.5)
    final = mixc(nt, final, rgb(nt, (0.52,0.51,0.49), (-400,-420)), wear, loc=(-250, -100))
L(nt, final, 0, bs, "Base Color")
bump = mknode(nt, "ShaderNodeBump", (200, -350)); bump.inputs['Strength'].default_value = 0.30
brick = mknode(nt, "ShaderNodeTexBrick", (-100, -520))
brick.inputs['Scale'].default_value = 2.4; L(nt, texco, 0, brick, 0)
nb = noise(nt, 1.0, 6, loc=(-60, -380), vec=pos)
bh = mathn(nt, 'ADD', mathn(nt, 'MULTIPLY', brick.outputs['Fac'], 0.30),
                       mathn(nt, 'MULTIPLY', nb.outputs['Fac'], 0.55), loc=(60, -400))
L(nt, bh, 0, bump, "Height"); L(nt, bump.outputs[0], 0, bs, "Normal")

# ================= SLATE ROOF =================
m, nt, bs = std_mat("M_Slate", (0.15,0.18,0.22), 0.45)
pos = geo_out(nt, "Position", (-1300, 0))
texco = mknode(nt, "ShaderNodeTexCoord", (-1250, 150))
brick = mknode(nt, "ShaderNodeTexBrick", (-900, 150))
brick.inputs['Scale'].default_value = 0.55
L(nt, texco, 0, brick, 0)
slate = mixc(nt, rgb(nt, (0.09,0.115,0.15), (-900, 400)), rgb(nt, (0.22,0.26,0.31), (-900, 320)), brick.outputs['Color'], loc=(-650, 250))
nsl = noise(nt, 0.09, 4, loc=(-650, 60), vec=pos)
slate2 = mixc(nt, slate, rgb(nt,(0.045,0.06,0.08),(-450,60)), mathn(nt, 'MULTIPLY', nsl.outputs['Fac'], 0.5), loc=(-420, 160))
nsl2 = noise(nt, 0.9, 3, loc=(-650, -120), vec=pos)
slate3 = mixc(nt, slate2, rgb(nt,(0.06,0.07,0.09),(-260,-120)), mathn(nt,'MULTIPLY', nsl2.outputs['Fac'], 0.25), loc=(-230, 40))
L(nt, slate3, 0, bs, "Base Color")
bump = mknode(nt, "ShaderNodeBump", (180, -250)); bump.inputs['Strength'].default_value = 0.09
L(nt, brick.outputs['Fac'], 0, bump, "Height"); L(nt, bump.outputs[0], 0, bs, "Normal")
setbs(bs, **{"Roughness": 0.40, "Specular IOR Level": 0.55})

# ================= COPPER (verdigris) =================
m, nt, bs = std_mat("M_Copper", (0.30,0.16,0.11), 0.42)
pos = geo_out(nt, "Position", (-1100, 0))
ncu = noise(nt, 0.10, 4, loc=(-850, 120), vec=pos)
pat = mixc(nt, rgb(nt, (0.25,0.12,0.08), (-850, 330)), rgb(nt, (0.20,0.44,0.37), (-850, 240)), mathn(nt,'MULTIPLY', ncu.outputs['Fac'], 1.15), loc=(-620, 220))
L(nt, pat, 0, bs, "Base Color")
setbs(bs, **{"Metallic": 0.9, "Roughness": 0.38})

# ================= ROCK CLIFF =================
m, nt, bs = std_mat("M_RockCliff", (0.155,0.145,0.135), 0.92)
pos = geo_out(nt, "Position", (-1500, 0))
sep = mknode(nt, "ShaderNodeSeparateXYZ", (-1400, 400)); L(nt, pos, 0, sep, 0)
nbig = noise(nt, 0.020, 5, loc=(-1200, 250), vec=pos)
strat = mathn(nt, 'ADD', mathn(nt, 'MULTIPLY', sep.outputs[2], 0.55),
                          mathn(nt, 'MULTIPLY', nbig.outputs['Fac'], 5.0), loc=(-1050, 300))
sine = mathn(nt, 'SINE', strat, loc=(-950, 300))
band = mathn(nt, 'MULTIPLY', mathn(nt, 'ADD', sine, 0.25), 0.5, loc=(-880, 300))
band = clampn(nt, band)
rc1 = mixc(nt, rgb(nt, (0.115,0.108,0.10), (-950, 500)), rgb(nt, (0.21,0.198,0.184), (-950, 420)), band, loc=(-750, 400))
n2 = noise(nt, 0.14, 5, loc=(-750, 220), vec=pos)
rc2 = mixc(nt, rc1, rgb(nt, (0.08,0.077,0.073), (-560, 220)), mathn(nt, 'MULTIPLY', n2.outputs['Fac'], 0.45), loc=(-550, 300))
ao = mknode(nt, "ShaderNodeAmbientOcclusion", (-750, -150)); ao.inputs['Distance'].default_value = 3.5
rc3 = mixc(nt, rc2, rgb(nt, (0.045,0.045,0.043), (-400,-100)), mathn(nt, 'MULTIPLY', ao.outputs[0], 0.5), loc=(-380, 80))
nmos = noise(nt, 0.28, 4, loc=(-380, 380), vec=pos)
lowbias = mathn(nt, 'SUBTRACT', 15.0, sep.outputs[2], loc=(-380, 500))
lowbias = clampn(nt, lowbias)
mf = mathn(nt, 'MULTIPLY', lowbias, nmos.outputs['Fac'], loc=(-260, 440))
mf = mathn(nt, 'MULTIPLY', mf, mathn(nt, 'MULTIPLY', ao.outputs[0], 1.2), loc=(-180, 380))
rc4 = mixc(nt, rc3, rgb(nt, (0.06,0.09,0.038), (-40, 380)), mathn(nt, 'MULTIPLY', mf, 0.8), loc=(0, 220))
L(nt, rc4, 0, bs, "Base Color")
bump = mknode(nt, "ShaderNodeBump", (180, -300)); bump.inputs['Strength'].default_value = 0.5
nb = noise(nt, 0.45, 7, loc=(0, -350), vec=pos)
L(nt, mathn(nt, 'ADD', mathn(nt, 'MULTIPLY', nb.outputs['Fac'], 0.55), mathn(nt, 'MULTIPLY', sine, 0.22)), 0, bump, "Height")
L(nt, bump.outputs[0], 0, bs, "Normal")

# ================= MOOR =================
m, nt, bs = std_mat("M_Moor", (0.05,0.065,0.033), 0.95)
pos = geo_out(nt, "Position", (-1300, 0))
nn2 = noise(nt, 0.016, 4, loc=(-1050, 350), vec=pos)
nn3 = noise(nt, 0.045, 4, loc=(-1050, 220), vec=pos)
g1 = mixc(nt, rgb(nt, (0.036,0.052,0.024), (-1050, 540)), rgb(nt, (0.08,0.05,0.058), (-1050, 460)), nn2.outputs['Fac'], loc=(-820, 460))
g2 = mixc(nt, g1, rgb(nt, (0.10,0.078,0.036), (-820, 350)), mathn(nt, 'MULTIPLY', nn3.outputs['Fac'], 0.7), loc=(-620, 380))
nrm = mknode(nt, "ShaderNodeNormal", (-1050, -100))
nsep = mknode(nt, "ShaderNodeSeparateXYZ", (-900, -100)); L(nt, nrm, 0, nsep, 0)
steep = mathn(nt, 'SUBTRACT', 1.0, nsep.outputs[2], loc=(-760, -60))
g3 = mixc(nt, g2, rgb(nt, (0.17,0.16,0.15), (-420, -40)), mathn(nt, 'MULTIPLY', mathn(nt, 'POWER', steep, 1.5), 0.85), loc=(-380, 160))
path_attr = mknode(nt, "ShaderNodeAttribute", (-420, 260)); path_attr.attribute_name = "path"
g4 = mixc(nt, g3, rgb(nt, (0.28,0.23,0.17), (-160, 280)), mathn(nt, 'MULTIPLY', path_attr.outputs['Fac'], 0.8), loc=(-40, 220))
L(nt, g4, 0, bs, "Base Color")
bump = mknode(nt, "ShaderNodeBump", (180, -250)); bump.inputs['Strength'].default_value = 0.25
L(nt, noise(nt, 0.35, 6, loc=(0, -300), vec=pos).outputs['Fac'], 0, bump, "Height")
L(nt, bump.outputs[0], 0, bs, "Normal")

# ================= WATER =================
m = new_mat("M_Water"); nt = m.node_tree
bs = nt.nodes.get("Principled BSDF"); bs.location = (300, 100)
nt.nodes["Material Output"].location = (900, 100)
pos = geo_out(nt, "Position", (-1400, 0))
wav1 = noise(nt, 0.09, 5, loc=(-1100, 200), roughness=0.35, distortion=2.0, vec=pos)
wav2 = noise(nt, 0.32, 4, loc=(-1100, 60), roughness=0.55, distortion=4.0, vec=pos)
rough = mathn(nt, 'ADD', mathn(nt, 'MULTIPLY', wav1.outputs['Fac'], 0.10), mathn(nt, 'MULTIPLY', wav2.outputs['Fac'], 0.05), loc=(-800, 120))
rough = mathn(nt, 'ADD', rough, 0.03)
setbs(bs, **{"Base Color": (0.004, 0.010, 0.014, 1.0), "Metallic": 0.0,
             "IOR": 1.33, "Specular IOR Level": 0.8})
L(nt, rough, 0, bs, "Roughness")
bump = mknode(nt, "ShaderNodeBump", (100, -150)); bump.inputs['Strength'].default_value = 0.04
L(nt, wav2.outputs['Fac'], 0, bump, "Height"); L(nt, bump.outputs[0], 0, bs, "Normal")
# shore blend attribute
shore_attr = mknode(nt, "ShaderNodeAttribute", (-800, -200)); shore_attr.attribute_name = "shore"
trans = mknode(nt, "ShaderNodeBsdfTransparent", (300, -250))
trans.inputs[0].default_value = (0.03, 0.06, 0.07, 1.0)
mixsh = mknode(nt, "ShaderNodeMixShader", (620, -50))
L(nt, shore_attr.outputs['Fac'], 0, mixsh, 0)
L(nt, bs.outputs[0], 0, mixsh, 2)
L(nt, trans.outputs[0], 0, mixsh, 1)
L(nt, mixsh.outputs[0], 0, nt.nodes["Material Output"], 0)
m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None

# assign
bpy.data.objects["Moor"].data.materials.clear()
bpy.data.objects["Moor"].data.materials.append(bpy.data.materials["M_Moor"])
bpy.data.objects["Castle_Rock"].data.materials.clear()
bpy.data.objects["Castle_Rock"].data.materials.append(bpy.data.materials["M_RockCliff"])
bpy.data.objects["Lake"].data.materials.clear()
bpy.data.objects["Lake"].data.materials.append(bpy.data.materials["M_Water"])

result = {"mats": [mm.name for mm in bpy.data.materials]}
