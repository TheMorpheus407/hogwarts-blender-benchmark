
# Dense forest belts occupy valleys; the existing distant scatter thins into the hills.
n=0
while n<8000:
    side=-1 if rng.random()<.52 else 1
    x=rng.uniform(-475,-137) if side<0 else rng.uniform(144,486)
    y=rng.uniform(-90,445);z=terrain_h(x,y)
    if z<3.0 or distance_path(x,y)<7:continue
    if ((x-180)/48)**2+((y+94)/45)**2<1.0:continue
    valley=(noise(Vector((x*.017,y*.017,21)))+1)/2
    if rng.random()>.45+.50*valley:continue
    data,h=tree_meshes[rng.randrange(10)];o=bpy.data.objects.new('Forest • valley pine %04d'%n,data);C['Nature'].objects.link(o);o.location=(x,y,z-.12)
    size=rng.uniform(.73,1.25);o.scale=(size,size*rng.uniform(.86,1.05),size*rng.uniform(.88,1.22));o.rotation_euler.z=rng.random()*math.tau
    n+=1
# Give the dominant spire its clearly visible attendant turrets.
for ob in bpy.data.objects:
    if ob.name.startswith('Grand Tower • high attendant') and ob.type=='MESH':
        for v in ob.data.vertices:v.co.x-=2;v.co.y-=17
    if ob.name.startswith('Grand Tower • south attendant') and ob.type=='MESH':
        for v in ob.data.vertices:v.co.x+=2;v.co.y-=14
for cx,cy,zb,r,hh in [(-23,-2,117,3,22),(-3,-1,111,2.4,16)]:
    for lev in range(2):
        for k in range(7):
            aa=k*math.tau/7
            window('Grand Tower • attendant chamber',(cx+(r+.3)*math.cos(aa),cy+(r+.3)*math.sin(aa),zb+3+lev*7),.80,3,aa+math.pi/2,1)
turret('Grand Tower • high needle',-13,18.3,126,1.8,26,27)
for k in range(8):
    aa=k*math.tau/8;window('Grand Tower • high needle chamber',(-13+2.05*math.cos(aa),18.3+2.05*math.sin(aa),143),.7,3.7,aa+math.pi/2,1)
# Add architectural hoods to every roof dormer.
g=Geo()
for ob in list(bpy.data.objects):
    if '• spire dormer' not in ob.name:continue
    a=ob.rotation_euler.z;ca,sa=math.cos(a),math.sin(a);cx,cy,cz=ob.location
    vv=[(-.52,-.19,1.55),(.52,-.19,1.55),(0,-.19,2.27),(-.52,.70,1.55),(.52,.70,1.55),(0,.70,2.27)]
    v=[(cx+u*ca-dd*sa,cy+u*sa+dd*ca,cz+zz) for u,dd,zz in vv]
    g.add(v,[(0,3,5,2),(1,2,5,4),(0,2,1)],'roof')
g.create('Spire roofs • pointed slate dormer hoods')
# Procedural night sky: cobalt gradient, cloud veils, and small restrained stars.
scene=bpy.context.scene;world=scene.world;nt=world.node_tree;nt.nodes.clear()
out=node(nt,'ShaderNodeOutputWorld');bg=node(nt,'ShaderNodeBackground')
tc=node(nt,'ShaderNodeTexCoord');normal=tc.outputs['Normal']
sep=node(nt,'ShaderNodeSeparateXYZ');nt.links.new(normal,sep.inputs[0])
grad=ramp(nt,sep.outputs['Z'],[(0,(.038,.084,.142)),(.22,(.020,.044,.09)),(.72,(.006,.015,.038)),(1,(.003,.008,.024))])
cloud=noise_node(nt,vector_scale(nt,normal,(2.4,2.4,7)),2.0,5,.72);cloud.inputs['Distortion'].default_value=1.1
cloudr=ramp(nt,cloud.outputs['Fac'],[(.30,(.012,.025,.05)),(.58,(.06,.092,.145)),(.78,(.16,.205,.28))])
col=mixc(nt,.62,grad.outputs[0],cloudr.outputs[0])
stars=node(nt,'ShaderNodeTexVoronoi');stars.distance='EUCLIDEAN';stars.feature='F1';stars.inputs['Scale'].default_value=165;nt.links.new(normal,stars.inputs['Vector'])
star=ramp(nt,stars.outputs['Distance'],[(0,(.36,.49,.74)),(.025,(.27,.38,.57)),(.050,(0,0,0)),(1,(0,0,0))])
add=node(nt,'ShaderNodeMixRGB');add.blend_type='ADD';add.inputs[0].default_value=.75;nt.links.new(col,add.inputs[1]);nt.links.new(star.outputs[0],add.inputs[2]);nt.links.new(add.outputs[0],bg.inputs['Color'])
bg.inputs['Strength'].default_value=.55;nt.links.new(bg.outputs[0],out.inputs['Surface'])
# The moon is a procedural, cratered sphere; all of its shading is generated.
M['moon']=mat('Sky • silver cratered moon',(.59,.65,.71),.98)
nt,p,out,geo=shader_reset(M['moon']);pos=geo.outputs['Position']
n=noise_node(nt,pos,.38,5);col=ramp(nt,n.outputs['Fac'],[(.20,(.31,.36,.43)),(.43,(.62,.70,.80)),(.71,(.94,.98,1.0))])
nt.links.new(col.outputs[0],p.inputs['Base Color']);nt.links.new(col.outputs[0],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=1.9
vor=node(nt,'ShaderNodeTexVoronoi');vor.inputs['Scale'].default_value=.31;nt.links.new(pos,vor.inputs['Vector']);nt.links.new(bump_node(nt,vor.outputs['Distance'],.35,.55),p.inputs['Normal'])
bpy.ops.mesh.primitive_uv_sphere_add(segments=96,ring_count=64,radius=18.5,location=(-440,450,288))
moon=bpy.context.object;moon.name='Sky • the rising moon'
for c in list(moon.users_collection):c.objects.unlink(moon)
C['FX'].objects.link(moon);moon.data.materials.append(M['moon'])
for p in moon.data.polygons:p.use_smooth=True
# A very thin atmosphere separates mountain planes without concealing the architecture.
ma=bpy.data.materials.new('Atmosphere • Highland aerial perspective');ma.use_nodes=True;nt=ma.node_tree;nt.nodes.clear()
out=node(nt,'ShaderNodeOutputMaterial');sc=node(nt,'ShaderNodeVolumeScatter');sc.inputs['Color'].default_value=(.53,.65,.80,1);sc.inputs['Density'].default_value=.00017;sc.inputs['Anisotropy'].default_value=.45;nt.links.new(sc.outputs[0],out.inputs['Volume'])
box('Atmosphere • wide aerial haze',(0,250,220),(6500,4700,680),ma,group='FX')
# Height-limited, nonuniform lake mist, pooled in separate valley tongues.
fog=bpy.data.materials.new('Mist • drifting lake vapour');fog.use_nodes=True;nt=fog.node_tree;nt.nodes.clear()
out=node(nt,'ShaderNodeOutputMaterial');pv=node(nt,'ShaderNodeVolumePrincipled')
pv.inputs['Color'].default_value=(.52,.64,.77,1);pv.inputs['Anisotropy'].default_value=.35
texc=node(nt,'ShaderNodeTexCoord');obj=texc.outputs['Generated']
sep=node(nt,'ShaderNodeSeparateXYZ');nt.links.new(obj,sep.inputs[0])
fall=ramp(nt,sep.outputs['Z'],[(0,(.32,.32,.32)),(.22,(1,1,1)),(.62,(.32,.32,.32)),(1,(0,0,0))])
nn=noise_node(nt,vector_scale(nt,obj,(5.0,2.2,2.0)),2.3,4)
nr=ramp(nt,nn.outputs['Fac'],[(.31,(0,0,0)),(.56,(.34,.34,.34)),(.77,(1,1,1))])
density=mathn(nt,'MULTIPLY',fall.outputs[0],nr.outputs[0]);density=mathn(nt,'MULTIPLY',density.outputs[0],.012)
nt.links.new(density.outputs[0],pv.inputs['Density']);nt.links.new(pv.outputs[0],out.inputs['Volume'])
for name,loc,dim in [
    ('Lake • mist ribbon west',(-110,-67,6),(360,85,15)),
    ('Lake • mist ribbon east',(146,-49,5),(230,76,12)),
    ('Forest • low valley vapour',(-220,188,38),(270,175,23)),
    ('Forest • distant valley mist',(255,225,40),(340,170,25))]:
    box(name,loc,dim,fog,group='FX')
# Cool, directional moon light and warmer local pools establish the chosen mood.
sun=bpy.data.objects['Moon • silver directional key'];sun.data.energy=1.15;sun.data.color=(.58,.72,1);sun.data.angle=math.radians(2.0)
sun.rotation_euler=(Vector((0,0,55))-Vector((-300,-190,440))).to_track_quat('-Z','Y').to_euler()
bpy.data.objects['Sky • immense soft fill'].data.energy=92000
bpy.data.objects['Sky • immense soft fill'].data.color=(.47,.62,1)
bpy.data.objects['Rim • distant blue'].data.energy=155000
for i in range(6):
    light('Great Hall • candle spill %d'%i,(-77+i*11,-32,82),330,(1,.43,.15),5,target=(-77+i*11,-27.4,83))
light('Boathouse • reflected amber fill',(14,-111,6),190,(1,.43,.16),4,target=(14,-105.4,6))
scene.view_settings.exposure=.40;scene.view_settings.look='AgX - Medium High Contrast'
# Lower the hero to the lake, and keep all camera views physically plausible.
cam=bpy.data.objects['Cam_Hero'];cam.location=(255,-640,18);cam.data.lens=49;cam.rotation_euler=(Vector((12,5,61))-cam.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects['Cam_Boathouse'];cam.location=(70,-175,4.5);cam.data.lens=22;cam.rotation_euler=(Vector((1,-30,64))-cam.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects['Cam_Viaduct'];cam.location=(157,-81.12,58.8);cam.data.lens=24;cam.rotation_euler=(Vector((8,7,105))-cam.location).to_track_quat('-Z','Y').to_euler()
# Remove the glazed placeholder from the gate opening and fit a real iron portcullis.
gate=bpy.data.objects.get('Gatehouse • great pointed portal • mullioned glazing')
if gate:bpy.data.objects.remove(gate,do_unlink=True)
g=Geo();ga=math.atan2(-70,125)+math.pi/2;ca,sa=math.cos(ga),math.sin(ga)
for i in range(17):
    xx=-2.55+i*.31875;maxz=10.3-5.4*.8660254+math.sqrt(max(.1,5.4**2-(abs(xx)+2.7)**2))
    pts=[(55+xx*ca-dd*sa,-24+xx*sa+dd*ca,65+zz) for dd,zz in [(1.1,.1),(1.1,maxz-.12)]]
    g.tube(pts,.033,'bronze',6)
for zz in [1,2.5,4,5.5,7]:
    xxlim=2.5
    g.tube([(55-xxlim*ca-1.1*sa,-24-xxlim*sa+1.1*ca,65+zz),(55+xxlim*ca-1.1*sa,-24+xxlim*sa+1.1*ca,65+zz)],.035,'bronze',6)
g.create('Gatehouse • forged iron portcullis')
