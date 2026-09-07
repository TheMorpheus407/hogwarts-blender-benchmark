import bpy, math, random, os, json, time
from mathutils import Vector, Matrix
from mathutils.noise import noise_vector, noise, fractal, turbulence
from math import sin, cos, pi, sqrt
ROOT='/home/morpheus/Documents/Projects/Benchmarks/Blender/GPT-6-Astra'
random.seed(817)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
 if c.name != 'Collection': bpy.data.collections.remove(c)
base=bpy.data.collections.get('Collection') or bpy.data.collections.new('Collection'); base.name='Castle'
COL={}
for n in ['Castle','Terrain','Nature','Lights','FX','Cameras','Architecture_Detail','Boathouse','Viaduct','Greenhouses']:
 c=bpy.data.collections.get(n) or bpy.data.collections.new(n)
 if c.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(c)
 COL[n]=c
def mesh(name,vs,fs,mat,col='Castle',smooth=False):
 m=bpy.data.meshes.new(name); m.from_pydata(vs,[],fs); m.update()
 o=bpy.data.objects.new(name,m); COL[col].objects.link(o)
 if mat: m.materials.append(mat)
 if smooth:
  for p in m.polygons:p.use_smooth=True
 return o
def bevel(o,w=.1,seg=2):
 mod=o.modifiers.new('Soft weathered arrises','BEVEL');mod.width=w;mod.segments=seg
 return o
def box(name,loc,sc,mat,col='Castle',bev=0):
 x,y,z=[s/2 for s in sc]
 vs=[(-x,-y,-z),(-x,-y,z),(-x,y,-z),(-x,y,z),(x,-y,-z),(x,-y,z),(x,y,-z),(x,y,z)]
 o=mesh(name,vs,[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],mat,col)
 o.location=loc
 if bev:bevel(o,bev)
 return o
def cone(name,loc,r1,r2,depth,mat,col='Castle',n=48):
 vs=[(r*cos(2*pi*i/n),r*sin(2*pi*i/n),z) for z,r in [(-depth/2,r1),(depth/2,r2)] for i in range(n)]
 fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]
 fs += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 o=mesh(name,vs,fs,mat,col);o.location=loc
 for p in o.data.polygons[2:]:p.use_smooth=True
 return o
def beam(name,a,b,width,mat,col='Castle',n=8):
 a,b=Vector(a),Vector(b);o=cone(name,(a+b)*.5,width,width,(b-a).length,mat,col,n)
 o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def curve(name,pts,r,mat,col='Castle',cyclic=False):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=1;c.bevel_depth=r;c.resolution_u=12;c.bevel_resolution=2
 p=c.splines.new('POLY');p.points.add(len(pts)-1)
 for q,v in zip(p.points,pts):q.co=(*v,1)
 p.use_cyclic_u=cyclic
 o=bpy.data.objects.new(name,c);COL[col].objects.link(o);c.materials.append(mat);return o
def material(name,color,rough=.7,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
 return m
STONE=material('Limestone | warm ashlar, wet seams',(0.36,.32,.255))
TRIM=material('Carved pale sandstone',(.48,.445,.36))
ROOF=material('Blue slate | hand split',(.075,.115,.15),.48)
COPPER=material('Patinated copper',(.09,.22,.20),.4,.6)
ROCK=material('Highland schist | stratified',(.15,.175,.17))
GROUND=material('Peat, heather and moss',(.055,.09,.07))
WATER=material('Black Lake | deep glacial water',(.012,.047,.055),.18,.15)
DARK=material('Recessed shadow',(.012,.017,.021),.8)
IRON=material('Black wrought iron',(.025,.035,.04),.36,.65)
WOOD=material('Rain dark oak',(.105,.055,.024),.62)
GOLD=material('Aged brass',(.48,.26,.075),.32,.72)
GLASS=[]
for i,(col,strength) in enumerate([((.9,.34,.075),3.2),((1,.57,.2),2.6),((.65,.25,.07),1.5),((.15,.19,.18),.05),((.33,.26,.12),.3),((1,.72,.38),4.5)]):
 m=material('Window glass %02d'%i,col,.22,.15);b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Emission Color'].default_value=(*col,1);b.inputs['Emission Strength'].default_value=strength;GLASS.append(m)
def gable(name,x,y,z,w,d,h,mat,col='Castle'):
 vs=[(x-w/2,y-d/2,z),(x+w/2,y-d/2,z),(x,y-d/2,z+h),(x-w/2,y+d/2,z),(x+w/2,y+d/2,z),(x,y+d/2,z+h)]
 return mesh(name,vs,[(0,2,1),(3,4,5),(0,3,5,2),(2,5,4,1),(0,1,4,3)],mat,col)
def hall_roof(name,x,y,z,length,width,h,mat):
 o=gable(name,0,0,z,width,length,h,mat)
 # long ridge along X
 o.rotation_euler[2]=pi/2;o.location.x=x;o.location.y=y
 return o
def cam(name,loc,target,lens):
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);COL['Cameras'].objects.link(o)
 o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=10000
 return o
def light(name,typ,loc,color,power,size=1,target=None):
 d=bpy.data.lights.new(name,typ);d.energy=power;d.color=color
 if typ=='AREA':d.shape='DISK';d.size=size
 if typ=='POINT':d.shadow_soft_size=size
 o=bpy.data.objects.new(name,d);COL['Lights'].objects.link(o);o.location=loc
 if target:o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
 return o
def crag(name,cx,cy,rx,ry,h,seed):
 rng=random.Random(seed);N=180;L=26;vs=[]
 jitter=[rng.uniform(-1,1) for i in range(N)]
 for j in range(L):
  t=j/(L-1);z=-4+t*(h+4)
  scale=1.16-.2*t+.032*sin(t*30)+.027*sin(t*91)
  for i in range(N):
   a=2*pi*i/N
   irregular=1+.048*sin(5*a)+.04*sin(11*a+1)+.025*sin(a*23)+.024*jitter[i]
   x=cx+rx*scale*irregular*cos(a)+2.3*sin(t*11+a*4)
   y=cy+ry*scale*irregular*sin(a)
   zz=z+sin(a*9+2*t)*2.4+sin(a*19-t*11)*.8
   vs.append((x,y,zz))
 fs=[]
 for j in range(L-1):
  for i in range(N):
   a=j*N+i;b=j*N+(i+1)%N;c=b+N;d=a+N
   if (i+j)%2:fs.extend([(a,b,d),(b,c,d)])
   else:fs.extend([(a,b,c),(a,c,d)])
 vs.append((cx,cy,h-.5));center=len(vs)-1
 for i in range(N):fs.append(((L-1)*N+i,(L-1)*N+(i+1)%N,center))
 return mesh(name,vs,fs,ROCK,'Terrain')
crag('The Black Rock | primary promontory',0,14,83,55,60,11)
crag('Eastern bridge abutment',145,16,36,50,47,23)
box('Upper castle foundation',(0,14,59),(126,72,6),STONE,bev=.8)
box('Great Hall masonry',(-37,-8,75),(56,22,27),STONE,bev=.16)
hall_roof('Great Hall steep slate roof',-37,-8,88.5,59,25,18,ROOF)
tower_specs=[
 ('Grand Staircase Tower',-8,13,61,10.3,61,38),
 ('Astronomy Tower',33,27,61,8,55,33),
 ('Ravenclaw Tower',66,27,60,6,36,24),
 ('Library Tower',-53,28,60,6.2,32,21),
 ('West Gate Tower',-66,-21,59,3.7,17,8),
 ('East Gate Tower',64,-10,54,4.5,26,16),
 ('Bell Tower',10,40,61,5.2,33,23),
 ('Owl turret',-34,40,62,3.8,28,18)]
for name,x,y,z,r,h,sp in tower_specs:
 cone(name+' shaft',(x,y,z+h/2),r,r*.96,h,STONE)
 cone(name+' roof',(x,y,z+h+sp/2),r*1.15,.05,sp,COPPER if name=='Bell Tower' else ROOF)
box('Clock Tower masonry',(35,0,82),(17,18,43),STONE,bev=.2)
gable('Clock Tower gabled roof',35,0,103.5,19,21,19,ROOF)
box('East residential wing',(58,33,76),(41,21,30),STONE,bev=.2)
hall_roof('East wing roof',58,33,91,44,24,15,ROOF)
box('North cloister wing',(-12,40,71),(71,15,21),STONE,bev=.15)
hall_roof('North cloister roof',-12,40,81.5,74,17,12,ROOF)
box('South gallery',(14,-23,65),(39,11,13),STONE,bev=.15)
hall_roof('South gallery roof',14,-23,71.5,40,12,9,ROOF)
# temporary bridge is replaced in the architecture pass
box('BLOCK Bridge deck',(108,-12,48),(90,9,3),STONE)
for x in range(66,154,10):box('BLOCK Bridge pier',(x,-12,21),(3.5,8,52),STONE)
# lake has real shallow waves
N=180;vs=[];fs=[]
for j in range(N+1):
 y=-900+j*1800/N
 for i in range(N+1):
  x=-900+i*1800/N;z=.07*sin(x*.15+y*.22)+.055*sin(y*.4-x*.06)
  vs.append((x,y,z))
for j in range(N):
 for i in range(N):
  a=j*(N+1)+i;fs.append((a,a+1,a+N+2,a+N+1))
mesh('The Black Lake',vs,fs,WATER,'Terrain',True)
def ridge(name,y,base,height,seed):
 rng=random.Random(seed);vs=[];fs=[];nx=180;ny=30
 peaks=[(rng.uniform(-1050,1050),rng.uniform(85,220),rng.uniform(.4,1)) for _ in range(13)]
 for j in range(ny+1):
  v=j/ny;yy=y+v*340
  for i in range(nx+1):
   x=-1700+i*3400/nx
   elev=sum(amp*math.exp(-((x-pos)/wid)**2) for pos,wid,amp in peaks)
   z=base+height*elev*sin(v*pi)**.7+noise(Vector((x*.008,yy*.009,seed)))*height*.18
   vs.append((x,yy,z))
 for j in range(ny):
  for i in range(nx):
   a=j*(nx+1)+i;fs.extend([(a,a+1,a+nx+2),(a,a+nx+2,a+nx+1)])
 return mesh(name,vs,fs,GROUND,'Terrain',True)
ridge('Near western Highland',260,1,110,41)
ridge('Middle Highland ridge',620,18,130,62)
ridge('Far Highland ridge',1000,35,170,7)
# moonlit blue hour lighting
world=bpy.data.worlds.new('Blue hour | procedural cloud sky');bpy.context.scene.world=world;world.use_nodes=True
n=world.node_tree.nodes;l=world.node_tree.links;n.clear()
out=n.new('ShaderNodeOutputWorld');bg=n.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.32
tc=n.new('ShaderNodeTexCoord');no=n.new('ShaderNodeTexNoise');no.inputs['Scale'].default_value=2.8;no.inputs['Detail'].default_value=5;no.inputs['Roughness'].default_value=.7
l.new(tc.outputs['Normal'],no.inputs['Vector'])
r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.28;r.color_ramp.elements[0].color=(.014,.025,.06,1);r.color_ramp.elements[1].position=.72;r.color_ramp.elements[1].color=(.17,.27,.4,1)
l.new(no.outputs['Fac'],r.inputs[0]);l.new(r.outputs[0],bg.inputs['Color']);l.new(bg.outputs[0],out.inputs[0])
light('Moon | cool silver key','AREA',(-100,-80,270),(.57,.72,1),2200000,180,(0,0,60))
light('Last blue light | east rim','AREA',(160,130,180),(.32,.55,1),2600000,150,(0,0,80))
light('Dusk bounce on limestone','AREA',(-100,-180,95),(1,.74,.47),550000,130,(0,0,65))
sun=light('Moon directional','SUN',(0,0,200),(.56,.7,1),1.3,target=(60,80,0));sun.data.angle=.08
cam('Cam_Hero',(222,-384,126),(15,5,75),50)
cam('Cam_Aerial',(225,-245,235),(15,5,56),48)
cam('Cam_Boathouse',(125,-178,18),(15,-1,72),38)
cam('Cam_Viaduct',(141,-18,55),(14,1,88),26)
s=bpy.context.scene;s.camera=bpy.data.objects['Cam_Hero'];s.render.engine='CYCLES'
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX'
for d in p.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=48;s.cycles.use_denoising=True;s.cycles.use_adaptive_sampling=True
s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100
s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.4
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.color_depth='8'
s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
s.render.film_transparent=False;s.world.color=(.04,.08,.15)
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/hogwarts.blend')
