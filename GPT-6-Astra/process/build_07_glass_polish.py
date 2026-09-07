
# Rich leaded glass: small irregular panes, restrained heraldic colors and connected tracery.
STAIN=[]
for i,(c,e) in enumerate([((.48,.235,.082),.6),((.75,.41,.16),.8),((.95,.61,.29),1.1),((.16,.23,.24),.25),((.34,.11,.055),.45),((.32,.36,.21),.5),((.84,.71,.46),1.25)]):
 m=material('Medieval crown glass | pane %d'%i,c,.24,.12)
 b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Emission Color'].default_value=(*c,1);b.inputs['Emission Strength'].default_value=e
 nt=m.node_tree;l=nt.links;tc=node(nt,'ShaderNodeTexCoord');no=node(nt,'ShaderNodeTexNoise');l.new(tc.outputs['Object'],no.inputs[0]);no.inputs['Scale'].default_value=16;no.inputs['Detail'].default_value=3
 bump=node(nt,'ShaderNodeBump');bump.inputs['Distance'].default_value=.012;bump.inputs['Strength'].default_value=.28;l.new(no.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],b.inputs['Normal'])
 STAIN.append(m)
B=Batch('Great Hall | stained crown glass, flowing tracery and heraldic medallions')
rng=random.Random(555)
for side in [-1,1]:
 yy=-8+side*11.05;normal=Vector((0,side,0))
 for bay in range(11):
  x=-62+bay*5;w=2.65;h=12.1;z0=73;spring=h-.866*w
  # substitute small panes over original emission, stopping short of the pointed head
  for row in range(23):
   z=z0+.18+row*.405
   for col in range(6):
    xx=x-w*.44+col*.39
    mi=rng.choices(range(7),[18,20,28,9,7,6,12])[0]
    B.poly([(xx,yy+side*.112,z),(xx+.375,yy+side*.112,z),(xx+.375,yy+side*.112,z+.389),(xx,yy+side*.112,z+.389)],STAIN[mi])
  # primary stone tracery forks continue the mullions into the curving arch head
  for sx in [-1,1]:
   x0=x+sx*w/6
   pts=[]
   for k in range(18):
    t=k/17;pts.append((x0+sx*.68*t*t,yy+side*.225,z0+spring-.03+t*1.18))
   B.path(pts,.065,TRIM)
   # twin lancet arches meet below the central trefoil
   pts=[(x+sx*.43+.41*cos(pi-k*pi/20),yy+side*.23,z0+spring-.14+.59*sin(k*pi/20)) for k in range(21)]
   B.path(pts,.055,TRIM)
  # quatrefoil heraldic boss halfway up one mullioned light
  cz=z0+5.1;rad=.39
  for k in range(4):
   ph=k*pi/2;cx=x+rad*.44*cos(ph);zz=cz+rad*.44*sin(ph)
   pts=[(cx+.22*cos(t*2*pi/20),yy+side*.24,zz+.22*sin(t*2*pi/20)) for t in range(21)]
   B.poly(pts,STAIN[4 if bay%2 else 3]);B.path(pts,.026,GOLD)
  # diamond lead ties laid over the upper and lower panes
  for row in range(11):
   z=z0+.4+row*.8
   for col in range(3):
    cx=x-.79+col*.79
    pts=[(cx-.37,yy+side*.16,z+.38),(cx,yy+side*.16,z+.73),(cx+.37,yy+side*.16,z+.38),(cx,yy+side*.16,z+.03)]
    B.path(pts,.012,IRON,4,True)
  # carved hood mould with jointed voussoirs and projecting spring blocks
  ol=archline(w+.64,h+.39)
  B.path([(x+xx,yy+side*.39,z0+zz) for xx,zz in ol[2:]],.10,TRIM,6)
  for j in range(4,len(ol),2):
   p=Vector((x+ol[j][0],yy+side*.42,z0+ol[j][1]))
   p2=Vector((x+ol[j-1][0],yy+side*.43,z0+ol[j-1][1]))
   tangent=(p-p2).normalized()
   B.rod(p-tangent*.035,p+tangent*.035,.11,STONE,6)
B.done()
# Replace the three-ring ornaments in the large windows with a continuous quatrefoil.
# Original rings are retained as carved foils, connected by the new flow of stone branches.
# Populate Gothic buttresses with crocket leaves, finials and small carved gargoyles.
B=Batch('Great Hall | crockets, fleurons and gargoyles')
for side in [-1,1]:
 y=-8+side*12.2
 for i in range(12):
  x=-64.5+i*5
  for z in [89.3,90,90.7,91.4]:
   r=.32*(93-z)/4
   for k in range(4):
    ph=k*pi/2
    p=(x+r*cos(ph),y+r*sin(ph),z)
    B.rod(p,(p[0]+.18*cos(ph),p[1]+.18*sin(ph),z+.19),.11,TRIM,5,.02)
  finial(B,x,y,92.7,.09,.9)
  # gargoyle water spout, projecting from the upper buttress, not floating
  B.cube((x,y+side*.3,85.8),(.4,.9,.42),STONE)
  B.rod((x,y+side*.4,85.9),(x,y+side*1.2,85.6),.18,STONE,7,.10)
  for sx in [-1,1]:
   B.poly([(x,y+side*.35,85.9),(x+sx*.46,y+side*.65,86.3),(x+sx*.28,y+side*.94,85.7)],TRIM)
B.done()
# A more weathered face: broad mineral staining, microscopic pits and softened chipped edges.
for mat in [STONE,TRIM]:
 nt=mat.node_tree;l=nt.links
 rain=nt.nodes.get('Rain paths under ledges');rain.inputs['Scale'].default_value=2.8
 batch_noise=nt.nodes.get('Quarry batch variation');batch_noise.inputs['Scale'].default_value=.23
 brick=nt.nodes.get('Quarried blocks | 1.2m x 0.48m')
 brick.inputs['Mortar Size'].default_value=.012
 # random block tones: weathered charcoal sandstone through pale grey-gold
 fac=1.35 if mat==TRIM else 1
 brick.inputs['Color1'].default_value=(.28*fac,.255*fac,.205*fac,1)
 brick.inputs['Color2'].default_value=(.12*fac,.143*fac,.134*fac,1)
# high-density rock displacements break large flat polygons with fine erosion
tx=bpy.data.textures.new('Schist fracture displacement | procedural',type='DISTORTED_NOISE');tx.noise_scale=1.8;tx.distortion=1.15
tx2=bpy.data.textures.new('Frost pitting displacement | procedural',type='CLOUDS');tx2.noise_scale=.28;tx2.noise_depth=2
for name,sub,strength in [
 ('Black Rock | folded schist core',2,.72),
 ('Black Rock | tilted buttress slabs and fallen scree',2,.44),
 ('Eastern crag | eroded gneiss',2,.6),
 ('Boathouse | lake-washed bedrock',2,.2)]:
 o=bpy.data.objects[name]
 md=o.modifiers.new('Subdivision for fracture relief','SUBSURF');md.subdivision_type='SIMPLE';md.levels=sub;md.render_levels=sub
 md=o.modifiers.new('Wind and frost fracture','DISPLACE');md.texture=tx;md.texture_coords='GLOBAL';md.strength=strength;md.mid_level=.5
 md=o.modifiers.new('Fine mineral relief','DISPLACE');md.texture=tx2;md.texture_coords='GLOBAL';md.strength=.11;md.mid_level=.5
# cloud contrast without excessive volume-light wash
AIR.node_tree.nodes.get('Principled Volume').inputs['Density'].default_value=.00013
BACKAIR.node_tree.nodes.get('Principled Volume').inputs['Density'].default_value=.0007
for o in COL['Lights'].objects:
 if hasattr(o.data,'volume_factor'):o.data.volume_factor=.35 if o.data.type=='AREA' else .7
s.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.38
bpy.data.objects['Castle | warm hall bounce'].data.energy=5500
bpy.data.objects['Lake bounce | cliff revelation'].data.energy=100000
# water ripples have a calm broad component and crisp specular ripples
bs=WATER.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.105;bs.inputs['Transmission Weight'].default_value=.38;bs.inputs['Metallic'].default_value=.22
# heroic water-level perspective, with ridge layering above both shores
o=bpy.data.objects['Cam_Hero'];o.location=(208,-431,62);o.data.lens=42;o.rotation_euler=(Vector((15,0,74))-o.location).to_track_quat('-Z','Y').to_euler()
o=bpy.data.objects['Cam_Boathouse'];o.location=(115,-227,12);o.data.lens=29;o.rotation_euler=(Vector((10,-4,69))-o.location).to_track_quat('-Z','Y').to_euler()
o=bpy.data.objects['Cam_Detail_03'];o.location=(-71,-66,82);o.data.lens=64;o.rotation_euler=(Vector((-50,-18,80))-o.location).to_track_quat('-Z','Y').to_euler()
# glancing stone ribs behind the clock tower, and copper gutters down the hall buttresses
B=Batch('Roof drainage | copper downpipes and rain hoppers')
for side in [-1,1]:
 for x in [-64.5,-49.5,-34.5,-19.5,-9.5]:
  y=-8+side*11.65
  B.rod((x,y,63),(x,y,87),.075,COPPER)
  B.cube((x,y,86.6),(.35,.32,.45),COPPER)
  for z in [65,70,75,80,85]:B.cube((x,y,z),(.26,.25,.12),IRON)
B.done()
for o in list(COL['Architecture_Detail'].objects):
 if o.type=='MESH':fixnormals(o)
s.camera=bpy.data.objects['Cam_Hero']
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/hogwarts.blend')
