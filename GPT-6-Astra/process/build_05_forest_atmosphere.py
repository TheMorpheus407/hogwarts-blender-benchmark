
# Widen the open lake basin; retain a narrow east headland connected to the bridge.
def groundheight(x,y):
 east=(x-(141+max(0,-y-12)*1.15))*.42
 west=(-x-(145+max(0,-y)*.8))*.30
 north=(y-104)*.34
 edge=max(east,west,north)
 hill=(11*sin(x*.019+y*.009)+8*sin(y*.025-x*.008)+6*noise(Vector((x*.013,y*.013,5))))
 z=min(92,edge)+hill
 influence=math.exp(-((x-169)/29)**2-((y+4)/34)**2)
 return z*(1-influence)+46*influence
o=bpy.data.objects['Highland shore | peat moor and conifer valleys']
for v in o.data.vertices:v.co.z=groundheight(v.co.x,v.co.y)
# extend the carriage road across the headland with its terrain conformance corrected
o=bpy.data.objects['Old carriage road | worn moorland approach']
for v in o.data.vertices:
 if v.co.x>176:v.co.z=groundheight(v.co.x,v.co.y)+.25
# remove the deliberately broad paving outside the enclosing walls
o=bpy.data.objects['Upper courts | flagstones, fountain and benches']
# face-based removal keeps paved courtyards within the defensive circuit
import bmesh
bm=bmesh.new();bm.from_mesh(o.data)
remove=[]
for f in bm.faces:
 c=f.calc_center_median()
 if ((c.x>52 and c.y<-20) or (c.x>70) or c.y>58 or c.y<-40):remove.append(f)
bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(o.data);bm.free()
# Pine shader and handcrafted branch meshes, instanced to keep the scene efficient
BARK=material('Scots pine | silver brown bark',(.09,.073,.045))
rough_shader(BARK,(.025,.019,.01),(.21,.16,.095),2,4,.06)
NEEDLES=[]
for i,c in enumerate([(.018,.051,.038),(.024,.075,.052),(.036,.089,.059),(.051,.106,.062)]):
 m=material('Pine needles %d'%i,c,.82)
 rough_shader(m,tuple(v*.48 for v in c),tuple(v*1.65 for v in c),4,2,.018)
 NEEDLES.append(m)
def pineprototype(seed):
 rng=random.Random(seed);B=Batch('Pine species %02d | branch mesh'%seed,'Nature');h=rng.uniform(10,15);r=h*.017
 B.rod((0,0,0),(.12,-.07,h),r,BARK,10,.025)
 for tier in range(13):
  z=h*(.16+.061*tier);length=h*.23*(1-z/h)**.67
  branches=rng.randint(6,9)
  for j in range(branches):
   ph=2*pi*j/branches+tier*2.37+rng.uniform(-.25,.25);le=length*rng.uniform(.68,1.13)
   end=Vector((le*cos(ph),le*sin(ph),z+rng.uniform(-.6,.25)))
   root=Vector((0,0,z+.2))
   B.rod(root,end,.048*(1-z/h)+.012,BARK,5,.008)
   # lateral sprays produce layered feathery silhouettes rather than smooth cones
   for k in range(6):
    t=.15+k*.14;p=root.lerp(end,t);spray=le*.26*(1-t)+.12
    for side in [-1,1]:
     d=Vector((cos(ph+side*.8),sin(ph+side*.8),.22))*spray
     tip=p+d
     B.rod(p,tip,.06,NEEDLES[rng.randrange(4)],5,.003)
     # irregular dense needles collected into angular branchlets
     for m in range(3):
      q=p.lerp(tip,m/3);rr=spray*.22*(1-m*.2);top=q+Vector((0,0,rr*2.7))
      for v in range(4):
       aa=v*pi/2+ph
       B.poly([q+Vector((rr*cos(aa),rr*sin(aa),-.04)),q+Vector((rr*cos(aa+pi/2),rr*sin(aa+pi/2),-.04)),top],NEEDLES[rng.randrange(4)])
 B.rod((0,0,h*.83),(0,0,h+.3),.34,NEEDLES[1],7,.002)
 o=B.done();o.hide_render=True;o.hide_set(True)
 return o,h
PROTOS=[pineprototype(90+i) for i in range(12)]
# instance terrain forest according to elevation, water line, exposure, and roads
rng=random.Random(984)
trees=0
for i in range(7300):
 x=rng.uniform(-450,470);y=rng.uniform(-120,490)
 z=groundheight(x,y)
 if z<2 or z>96:continue
 if (-106<x<121 and y<99):continue
 # castle approach clearing and road corridor
 if 131<x<187 and -31<y<26:continue
 if any((x-p[0])**2+(y-p[1])**2<50 for p in path):continue
 dens=.68 if z<65 else .35
 if noise(Vector((x*.025,y*.025,16)))<-.28:dens*=.3
 if rng.random()>dens:continue
 proto,hh=PROTOS[rng.randrange(len(PROTOS))]
 o=bpy.data.objects.new('Highland pine %04d'%trees,proto.data);COL['Nature'].objects.link(o)
 o.location=(x,y,z-.35);scale=rng.uniform(.5,1.32)*(1-.003*max(0,z-40));o.scale=(scale*rng.uniform(.83,1.08),scale*rng.uniform(.83,1.08),scale)
 o.rotation_euler=(rng.uniform(-.04,.04),rng.uniform(-.035,.035),rng.random()*2*pi);trees+=1
# a few windswept trees rooted in crevices below the castle
for i in range(53):
 a=rng.uniform(0,2*pi);x=87*cos(a);y=14+59*sin(a)
 if y<-40 and x>0:continue
 proto,hh=PROTOS[i%len(PROTOS)];o=bpy.data.objects.new('Crag pine %02d'%i,proto.data);COL['Nature'].objects.link(o);o.location=(x,y,rng.uniform(2,9));sc=rng.uniform(.28,.6);o.scale=(sc,sc,sc);o.rotation_euler.z=rng.uniform(0,6)
# outlying moor boulders
B=Batch('Moorland | granite exposures','Terrain')
for i in range(330):
 x=rng.uniform(-350,380);y=rng.uniform(-60,330);z=groundheight(x,y)
 if z<1 or (-110<x<125 and y<100):continue
 shard(B,x,y,z-1,rng.uniform(.7,3),rng.uniform(.6,2),rng.uniform(1,4),rng.uniform(0,6),3000+i)
B.done()
# distant owlery, visibly separated from the main compound
ox,oy=-123,117;oz=groundheight(ox,oy)
cliff('Owlery knoll',ox,oy,14,12,oz+5,27)
turret('The Owlery',ox,oy,oz+3,4,19,12,ROOF)
B=Batch('Owlery | perch brackets and landing arches')
for i in range(8):
 ph=i*pi/4
 window(B,(ox+4.1*cos(ph),oy+4.1*sin(ph),oz+16),1.1,3.7,ph+pi/2,lit=3)
 B.rod((ox+3.8*cos(ph),oy+3.8*sin(ph),oz+15.6),(ox+5.8*cos(ph),oy+5.8*sin(ph),oz+15.6),.1,WOOD)
B.done()
# A small keeper's cottage at the forest edge
hx,hy=206,69;hz=groundheight(hx,hy)
cone('Keeper cottage | octagonal stone walls',(hx,hy,hz+2.1),4,4,4.2,STONE,n=8)
cone('Keeper cottage | pitched slate roof',(hx,hy,hz+6),5,.3,4,ROOF,n=8)
box('Keeper cottage | chimney',(hx+2,hy+1,hz+6.5),(1,1,6),STONE,bev=.08)
B=Batch('Keeper cottage | warm windows')
for ph in [pi,pi*1.5,0]:
 window(B,(hx+4.03*cos(ph),hy+4.03*sin(ph),hz+1),1.1,2,ph+pi/2,lit=0)
lantern(B,hx,hy-5,hz,.9,.25,True);B.done()
# Volumes use smooth height falloff and noise for thin, patchy lake mist.
def volume(name,density,color,low=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;nt.nodes.clear();l=nt.links
 out=node(nt,'ShaderNodeOutputMaterial');v=node(nt,'ShaderNodeVolumePrincipled');v.inputs['Color'].default_value=(*color,1);v.inputs['Anisotropy'].default_value=.28;l.new(v.outputs['Volume'],out.inputs['Volume'])
 if low:
  tc=node(nt,'ShaderNodeTexCoord');sep=node(nt,'ShaderNodeSeparateXYZ');l.new(tc.outputs['Generated'],sep.inputs[0])
  rr=setramp(node(nt,'ShaderNodeValToRGB'),[(0,(0,0,0)),(.18,(.7,.7,.7)),(.45,(.8,.8,.8)),(1,(0,0,0))]);l.new(sep.outputs['Z'],rr.inputs[0])
  mp=node(nt,'ShaderNodeVectorMath');mp.operation='MULTIPLY';mp.inputs[1].default_value=(.021,.029,.13);l.new(tc.outputs['Object'],mp.inputs[0])
  no=node(nt,'ShaderNodeTexNoise');l.new(mp.outputs[0],no.inputs[0]);no.inputs['Scale'].default_value=1;no.inputs['Detail'].default_value=3
  mul=node(nt,'ShaderNodeMath');mul.operation='MULTIPLY';l.new(no.outputs['Fac'],mul.inputs[0]);l.new(rr.outputs[0],mul.inputs[1])
  mul2=node(nt,'ShaderNodeMath');mul2.operation='MULTIPLY';mul2.inputs[1].default_value=density;l.new(mul.outputs[0],mul2.inputs[0]);l.new(mul2.outputs[0],v.inputs['Density'])
 else:v.inputs['Density'].default_value=density
 return m
MIST=volume('Lake mist | drifting ground fog',.012,(.46,.63,.72),True)
box('Mist over the Black Lake',(0,100,6),(1800,1900,20),MIST,'FX')
AIR=volume('Highland air | aerial perspective',.0009,(.40,.55,.72))
box('Blue atmospheric depth',(0,550,310),(3200,2700,630),AIR,'FX')
# chimney smoke
SMOKE=volume('Cottage chimney smoke',.075,(.34,.4,.43),True)
bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=12,location=(hx+2,hy+1,hz+13))
o=bpy.context.object;o.name='Cottage | drifting chimney smoke';o.scale=(1.4,1.3,5)
for c in list(o.users_collection):c.objects.unlink(o)
COL['FX'].objects.link(o);o.data.materials.append(SMOKE)
# more directional procedural clouds
nt=s.world.node_tree;n=nt.nodes;l=nt.links
tc=next(x for x in n if x.bl_idname=='ShaderNodeTexCoord');no=next(x for x in n if x.bl_idname=='ShaderNodeTexNoise')
mp=node(nt,'ShaderNodeVectorMath');mp.operation='MULTIPLY';mp.inputs[1].default_value=(1,1,3.6);l.new(tc.outputs['Normal'],mp.inputs[0]);l.new(mp.outputs[0],no.inputs[0]);no.inputs['Scale'].default_value=3.4;no.inputs['Detail'].default_value=6
r=next(x for x in n if x.bl_idname=='ShaderNodeValToRGB')
setramp(r,[(.26,(.012,.025,.051)),(.55,(.046,.089,.14)),(.76,(.16,.235,.32))])
# The moon is procedural, with a cratered mineral shader, never a texture.
MOON=material('Moon | basalt seas and crater dust',(.6,.69,.73))
nt,bs,tc,no=rough_shader(MOON,(.24,.34,.41),(.72,.84,.88),5,5,.015)
l=nt.links;l.new(bs.inputs['Base Color'].links[0].from_socket,bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=2.2
hero=bpy.data.objects['Cam_Hero'];bpy.context.view_layer.update();rot=hero.matrix_world.to_3x3();direction=(rot@Vector((.245,.148,-1))).normalized()
moonloc=hero.location+direction*1800
bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,radius=22,location=moonloc)
o=bpy.context.object;o.name='Moon above the eastern Highlands'
for c in list(o.users_collection):c.objects.unlink(o)
COL['FX'].objects.link(o);o.data.materials.append(MOON)
for p in o.data.polygons:p.use_smooth=True
# sky stars are restrained and sparse in blue hour
STAR=material('Stars | pale ice',(.5,.62,.85))
bs=STAR.node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Color'].default_value=(.6,.75,1,1);bs.inputs['Emission Strength'].default_value=3
B=Batch('Stars in breaks between cloud','FX')
for i in range(90):
 dx=rng.uniform(-.7,.7);dy=rng.uniform(.04,.48)
 dire=(rot@Vector((dx,dy,-1))).normalized();p=hero.location+dire*2300
 rr=rng.uniform(.055,.21)
 B.rod(p,p+dire*.05,rr,STAR,5)
B.done()
# final camera starting points
o=bpy.data.objects['Cam_Aerial'];o.location=(253,-280,258);o.data.lens=37;o.rotation_euler=(Vector((24,8,67))-o.location).to_track_quat('-Z','Y').to_euler()
s.camera=hero;s.cycles.samples=96
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/hogwarts.blend')
