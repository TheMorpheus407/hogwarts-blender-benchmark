
def node(nt,typ,name=None):
 o=nt.nodes.new(typ)
 if name:o.label=name;o.name=name
 return o
def setramp(n,stops):
 r=n.color_ramp
 while len(r.elements)>2:r.elements.remove(r.elements[-1])
 for i,(p,c) in enumerate(stops):
  e=r.elements[i] if i<2 else r.elements.new(p);e.position=p;e.color=(*c,1)
 return n
def stone_shader(mat,lightness=1):
 nt=mat.node_tree;n=nt.nodes;l=nt.links;n.clear()
 out=node(nt,'ShaderNodeOutputMaterial');bs=node(nt,'ShaderNodeBsdfPrincipled');l.new(bs.outputs[0],out.inputs['Surface']);bs.inputs['Roughness'].default_value=.82
 g=node(nt,'ShaderNodeNewGeometry');p=g.outputs['Position'];sep=node(nt,'ShaderNodeSeparateXYZ');l.new(p,sep.inputs[0])
 add=node(nt,'ShaderNodeMath');add.operation='ADD';l.new(sep.outputs['X'],add.inputs[0]);l.new(sep.outputs['Y'],add.inputs[1])
 co=node(nt,'ShaderNodeCombineXYZ');l.new(add.outputs[0],co.inputs['X']);l.new(sep.outputs['Z'],co.inputs['Y'])
 brick=node(nt,'ShaderNodeTexBrick','Quarried blocks | 1.2m x 0.48m');l.new(co.outputs[0],brick.inputs['Vector'])
 brick.inputs['Scale'].default_value=1;brick.inputs['Brick Width'].default_value=1.25;brick.inputs['Row Height'].default_value=.52;brick.inputs['Mortar Size'].default_value=.017;brick.inputs['Mortar Smooth'].default_value=.01
 brick.inputs['Color1'].default_value=(.30*lightness,.27*lightness,.218*lightness,1);brick.inputs['Color2'].default_value=(.18*lightness,.18*lightness,.156*lightness,1);brick.inputs['Mortar'].default_value=(.072,.078,.07,1)
 coarse=node(nt,'ShaderNodeTexNoise','Quarry batch variation');l.new(p,coarse.inputs[0]);coarse.inputs['Scale'].default_value=.11;coarse.inputs['Detail'].default_value=4;coarse.inputs['Roughness'].default_value=.8
 ramp=setramp(node(nt,'ShaderNodeValToRGB'),[(.2,(.33,.37,.34)),(.8,(.95,.89,.76))]);l.new(coarse.outputs['Fac'],ramp.inputs[0])
 mix=node(nt,'ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.72;l.new(brick.outputs['Color'],mix.inputs[1]);l.new(ramp.outputs[0],mix.inputs[2])
 # thin vertical rain streaks
 mp=node(nt,'ShaderNodeVectorMath');mp.operation='MULTIPLY';mp.inputs[1].default_value=(3.5,3.5,.16);l.new(p,mp.inputs[0])
 rain=node(nt,'ShaderNodeTexNoise','Rain paths under ledges');l.new(mp.outputs[0],rain.inputs[0]);rain.inputs['Scale'].default_value=1.5;rain.inputs['Detail'].default_value=3
 rr=setramp(node(nt,'ShaderNodeValToRGB'),[(.3,(.34,.32,.23)),(.56,(.88,.91,.84))]);l.new(rain.outputs['Fac'],rr.inputs[0])
 m2=node(nt,'ShaderNodeMixRGB');m2.blend_type='MULTIPLY';m2.inputs[0].default_value=.38;l.new(mix.outputs[0],m2.inputs[1]);l.new(rr.outputs[0],m2.inputs[2])
 # damp moss is strongest under the castle's lower wards
 less=node(nt,'ShaderNodeMapRange');l.new(sep.outputs['Z'],less.inputs['Value']);less.inputs['From Min'].default_value=8;less.inputs['From Max'].default_value=72;less.inputs['To Min'].default_value=.65;less.inputs['To Max'].default_value=0
 mossfac=node(nt,'ShaderNodeMath');mossfac.operation='MULTIPLY';l.new(less.outputs[0],mossfac.inputs[0]);l.new(coarse.outputs['Fac'],mossfac.inputs[1])
 mm=node(nt,'ShaderNodeMixRGB');l.new(mossfac.outputs[0],mm.inputs[0]);l.new(m2.outputs[0],mm.inputs[1]);mm.inputs[2].default_value=(.048,.085,.046,1)
 l.new(mm.outputs[0],bs.inputs['Base Color'])
 fine=node(nt,'ShaderNodeTexNoise','Stone micro-pitting');l.new(p,fine.inputs[0]);fine.inputs['Scale'].default_value=18;fine.inputs['Detail'].default_value=4
 bump=node(nt,'ShaderNodeBump');bump.inputs['Strength'].default_value=.5;bump.inputs['Distance'].default_value=.09;l.new(fine.outputs['Fac'],bump.inputs['Height'])
 b2=node(nt,'ShaderNodeBump');b2.invert=True;b2.inputs['Strength'].default_value=.65;b2.inputs['Distance'].default_value=.06;l.new(brick.outputs['Fac'],b2.inputs['Height']);l.new(bump.outputs[0],b2.inputs['Normal'])
 bev=node(nt,'ShaderNodeBevel');bev.inputs['Radius'].default_value=.045;bev.samples=3;l.new(bev.outputs[0],bump.inputs['Normal'])
 l.new(b2.outputs[0],bs.inputs['Normal'])
stone_shader(STONE)
stone_shader(TRIM,1.4)
def rough_shader(mat,c1,c2,scale,detail,bumpdist,metal=0):
 nt=mat.node_tree;n=nt.nodes;l=nt.links;n.clear();out=node(nt,'ShaderNodeOutputMaterial');bs=node(nt,'ShaderNodeBsdfPrincipled')
 l.new(bs.outputs[0],out.inputs[0]);bs.inputs['Roughness'].default_value=.76;bs.inputs['Metallic'].default_value=metal
 tex=node(nt,'ShaderNodeTexCoord');noi=node(nt,'ShaderNodeTexNoise');l.new(tex.outputs['Object'],noi.inputs[0]);noi.inputs['Scale'].default_value=scale;noi.inputs['Detail'].default_value=detail;noi.inputs['Roughness'].default_value=.76
 r=setramp(node(nt,'ShaderNodeValToRGB'),[(.23,c1),(.8,c2)]);l.new(noi.outputs['Fac'],r.inputs[0]);l.new(r.outputs[0],bs.inputs['Base Color'])
 f=node(nt,'ShaderNodeTexNoise');l.new(tex.outputs['Object'],f.inputs[0]);f.inputs['Scale'].default_value=scale*15;f.inputs['Detail'].default_value=3
 b=node(nt,'ShaderNodeBump');b.inputs['Strength'].default_value=.6;b.inputs['Distance'].default_value=bumpdist;l.new(f.outputs['Fac'],b.inputs['Height']);l.new(b.outputs[0],bs.inputs['Normal'])
 return nt,bs,tex,noi
nt,bs,tc,no=rough_shader(ROOF,(.018,.032,.043),(.09,.135,.155),2,4,.045,.12)
bs.inputs['Roughness'].default_value=.48
# slate tile mortar combined with noise
l=nt.links;sep=node(nt,'ShaderNodeSeparateXYZ');l.new(tc.outputs['Object'],sep.inputs[0]);co=node(nt,'ShaderNodeCombineXYZ');l.new(sep.outputs['X'],co.inputs['X']);l.new(sep.outputs['Z'],co.inputs['Y'])
brick=node(nt,'ShaderNodeTexBrick','Individual split slates');l.new(co.outputs[0],brick.inputs[0]);brick.inputs['Scale'].default_value=1;brick.inputs['Brick Width'].default_value=.52;brick.inputs['Row Height'].default_value=.35;brick.inputs['Mortar Size'].default_value=.009
brick.inputs['Color1'].default_value=(.09,.14,.18,1);brick.inputs['Color2'].default_value=(.027,.05,.068,1);brick.inputs['Mortar'].default_value=(.012,.02,.023,1)
mix=node(nt,'ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.45;l.new(bs.inputs['Base Color'].links[0].from_socket,mix.inputs[1]);l.new(brick.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],bs.inputs['Base Color'])
b=node(nt,'ShaderNodeBump');b.invert=True;b.inputs['Distance'].default_value=.025;b.inputs['Strength'].default_value=.5;l.new(brick.outputs['Fac'],b.inputs['Height']);l.new(bs.inputs['Normal'].links[0].from_socket,b.inputs['Normal']);l.new(b.outputs[0],bs.inputs['Normal'])
rough_shader(COPPER,(.015,.055,.05),(.12,.29,.25),3,4,.025,.65)
nt,bs,tc,no=rough_shader(ROCK,(.032,.048,.052),(.23,.25,.225),.25,6,.24)
l=nt.links
mapping=node(nt,'ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(.45,.5,4);l.new(tc.outputs['Object'],mapping.inputs[0])
layer=node(nt,'ShaderNodeTexNoise','Mica bedding and mineral seams');l.new(mapping.outputs[0],layer.inputs[0]);layer.inputs['Scale'].default_value=1.3;layer.inputs['Detail'].default_value=5;layer.inputs['Roughness'].default_value=.8
r=setramp(node(nt,'ShaderNodeValToRGB'),[(.25,(.035,.05,.047)),(.48,(.105,.128,.126)),(.65,(.25,.25,.22)),(.8,(.11,.14,.128))]);l.new(layer.outputs['Fac'],r.inputs[0])
mix=node(nt,'ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.55;l.new(bs.inputs['Base Color'].links[0].from_socket,mix.inputs[1]);l.new(r.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],bs.inputs['Base Color'])
bs.inputs['Roughness'].default_value=.77
b=node(nt,'ShaderNodeBump');b.inputs['Distance'].default_value=.45;b.inputs['Strength'].default_value=.65;l.new(layer.outputs['Fac'],b.inputs['Height']);l.new(bs.inputs['Normal'].links[0].from_socket,b.inputs['Normal']);l.new(b.outputs[0],bs.inputs['Normal'])
rough_shader(GROUND,(.025,.04,.026),(.16,.16,.077),.45,5,.12)
nt,bs,tc,no=rough_shader(WOOD,(.035,.014,.006),(.22,.13,.063),1.8,3,.035)
v=node(nt,'ShaderNodeVectorMath');v.operation='MULTIPLY';v.inputs[1].default_value=(4,4,.13);nt.links.new(tc.outputs['Object'],v.inputs[0]);nt.links.new(v.outputs[0],no.inputs[0])
# physically transmissive and multi-scale rippled water
nt=WATER.node_tree;nt.nodes.clear();l=nt.links;out=node(nt,'ShaderNodeOutputMaterial');bs=node(nt,'ShaderNodeBsdfPrincipled');l.new(bs.outputs[0],out.inputs['Surface'])
bs.inputs['Base Color'].default_value=(.018,.047,.055,1);bs.inputs['Roughness'].default_value=.17;bs.inputs['IOR'].default_value=1.333;bs.inputs['Transmission Weight'].default_value=.65;bs.inputs['Metallic'].default_value=.1
tc=node(nt,'ShaderNodeTexCoord');mp=node(nt,'ShaderNodeVectorMath');mp.operation='MULTIPLY';mp.inputs[1].default_value=(.4,1.8,1);l.new(tc.outputs['Object'],mp.inputs[0])
no=node(nt,'ShaderNodeTexNoise');l.new(mp.outputs[0],no.inputs[0]);no.inputs['Scale'].default_value=1.8;no.inputs['Detail'].default_value=3;no.inputs['Roughness'].default_value=.55
b=node(nt,'ShaderNodeBump');b.inputs['Strength'].default_value=.3;b.inputs['Distance'].default_value=.10;l.new(no.outputs['Fac'],b.inputs['Height'])
no2=node(nt,'ShaderNodeTexNoise');l.new(mp.outputs[0],no2.inputs[0]);no2.inputs['Scale'].default_value=.18;no2.inputs['Detail'].default_value=2
b2=node(nt,'ShaderNodeBump');b2.inputs['Strength'].default_value=.35;b2.inputs['Distance'].default_value=.22;l.new(no2.outputs['Fac'],b2.inputs['Height']);l.new(b.outputs[0],b2.inputs['Normal']);l.new(b2.outputs[0],bs.inputs['Normal'])
# floor below the lake enables true nearshore transparency
box('Lake bed',(0,0,-18),(2000,2000,2),ROCK,'Terrain')
# non-uniform light intensities, leaded stained glass remains warm
for i,m in enumerate(GLASS):
 bs=m.node_tree.nodes.get('Principled BSDF')
 bs.inputs['Emission Strength'].default_value=[1.8,2.4,.65,0,.12,3.8][i]
 bs.inputs['Roughness'].default_value=.32
 nt=m.node_tree;l=nt.links;tc=node(nt,'ShaderNodeTexCoord');noi=node(nt,'ShaderNodeTexNoise');l.new(tc.outputs['Object'],noi.inputs[0]);noi.inputs['Scale'].default_value=5;noi.inputs['Detail'].default_value=2
 b=node(nt,'ShaderNodeBump');b.inputs['Distance'].default_value=.008;b.inputs['Strength'].default_value=.18;l.new(noi.outputs['Fac'],b.inputs['Height']);l.new(b.outputs[0],bs.inputs['Normal'])
# Replace the provisional stacked rock with disrupted schist bedding
for name in ['The Black Rock | primary promontory','Eastern bridge abutment','Boathouse shelf']:
 o=bpy.data.objects.get(name)
 if o:bpy.data.objects.remove(o,do_unlink=True)
def cliff(name,cx,cy,rx,ry,h,seed):
 rng=random.Random(seed);N=160;L=33;vs=[];fs=[]
 for j in range(L):
  t=j/(L-1)
  for i in range(N):
   a=2*pi*i/N
   p=Vector((cos(a)*3,sin(a)*3,t*4+seed))
   nv=noise(p);n2=noise(p*3)
   scale=1.12-.19*t+.065*nv+.03*n2+.055*sin(5*a)+.018*sin(17*a)
   x=cx+rx*scale*cos(a)+4.5*t;y=cy+ry*scale*sin(a)+2*t
   z=-3+t*(h+3)+2.2*sin(a*6+.6)+n2*1.2
   if j==L-1:z=h-1+1.1*sin(a*5)
   vs.append((x,y,z))
 for j in range(L-1):
  for i in range(N):
   a=j*N+i;b=j*N+(i+1)%N
   fs.extend([(a,b,b+N),(a,b+N,a+N)])
 vs.append((cx,cy,h-1));c=len(vs)-1
 for i in range(N):fs.append(((L-1)*N+i,(L-1)*N+(i+1)%N,c))
 return mesh(name,vs,fs,ROCK,'Terrain')
cliff('Black Rock | folded schist core',0,14,82,54,59,11)
# bridge abutment tied into highland shore instead of a separate pillar
cliff('Eastern crag | eroded gneiss',153,18,39,46,47,9)
cliff('Boathouse | lake-washed bedrock',40,-79,21,15,3.1,41)
def shard(B,x,y,z,w,d,h,angle,seed):
 rng=random.Random(seed);N=7;L=4;vs=[]
 radial=[rng.uniform(.72,1.2) for _ in range(N)]
 for j in range(L):
  t=j/(L-1);fac=[.68,1,.92,.35][j]
  for i in range(N):
   a=2*pi*i/N;xx=w*cos(a)*fac*radial[i];yy=d*sin(a)*fac*radial[i]
   zz=t*h+(rng.random()-.5)*h*.14
   xx+=t*h*.18
   vs.append((x+xx*cos(angle)-yy*sin(angle),y+xx*sin(angle)+yy*cos(angle),z+zz))
 fs=[tuple(reversed(range(N))),tuple(range((L-1)*N,L*N))]
 for j in range(L-1):
  for i in range(N):
   a=j*N+i;b=j*N+(i+1)%N
   fs.append((a,b,b+N,a+N))
 B.geom(vs,fs,ROCK)
B=Batch('Black Rock | tilted buttress slabs and fallen scree','Terrain')
for i in range(230):
 a=random.random()*2*pi;r=random.uniform(.92,1.13)
 x=82*r*cos(a);y=14+54*r*sin(a)
 h=random.uniform(8,37);z=random.uniform(-2,49-h)
 shard(B,x,y,z,random.uniform(2,7),random.uniform(2,5),h,.32+random.uniform(-.22,.22),i+17)
# talus apron, broken boulders and stair-supported south slope
for i in range(250):
 a=random.uniform(pi,2*pi);rr=random.uniform(.88,1.3)
 x=86*rr*cos(a);y=14+59*rr*sin(a)
 shard(B,x,y,-2,random.uniform(1,5),random.uniform(1,4),random.uniform(3,11),random.random()*6,i+360)
for i in range(55):
 x=random.uniform(6,57);y=random.uniform(-73,-43)
 z=max(0,(-y-44)*-.66+22)
 shard(B,x,y,-1,random.uniform(3,8),random.uniform(4,9),z+random.uniform(3,9),.3,i+910)
B.done()
# Moorland promontories surrounding the inlet, with a traversable east approach
def groundheight(x,y):
 # shoreline: x>130 or x<-110 or y>90; shore drops into lake naturally
 east=(x-122)*.5
 west=(-x-113)*.29
 north=(y-72)*.26
 edge=max(east,west,north)
 hill=14*sin(x*.019+y*.009)+10*sin(y*.025-x*.008)+8*noise(Vector((x*.013,y*.013,5)))
 return min(100,edge)+hill
def landmesh():
 N=240;vs=[];fs=[]
 for j in range(N+1):
  y=-215+j*790/N
  for i in range(N+1):
   x=-590+i*1210/N
   z=groundheight(x,y)
   # carve deep water into main basin
   if -115<x<118 and y<85:z=min(z,-7)
   # blend bridge landing to a road-height headland
   influence=math.exp(-((x-163)/32)**2-((y+7)/40)**2)
   z=z*(1-influence)+46*influence
   vs.append((x,y,z))
 for j in range(N):
  for i in range(N):
   a=j*(N+1)+i;fs.extend([(a,a+1,a+N+2),(a,a+N+2,a+N+1)])
 return mesh('Highland shore | peat moor and conifer valleys',vs,fs,GROUND,'Terrain',True)
landmesh()
# roughen distant ridges into realistic ridgelines
for name in ['Near western Highland','Middle Highland ridge','Far Highland ridge']:
 o=bpy.data.objects[name]
 for v in o.data.vertices:
  x,y,z=v.co
  if z>3:v.co.z+=noise(Vector((x*.025,y*.019,7)))*11+noise(Vector((x*.071,y*.04,6)))*3
# lush turf pockets on the rock crown; broad material mask stays on terrain
B=Batch('Crag | sheltered moss shelves','Nature')
for i in range(100):
 a=random.random()*2*pi
 x=76*cos(a);y=14+48*sin(a);z=57+random.uniform(-3,0)
 shard(B,x,y,z,random.uniform(1,4),random.uniform(1,3),random.uniform(.4,1.5),.4,i+2000)
o=B.done();o.data.materials.clear();o.data.materials.append(GROUND)
# windswept path from bridge landing through forest
B=Batch('Old carriage road | worn moorland approach','Terrain')
path=[(152,-12,49),(174,0,47),(188,29,0),(213,57,0),(226,94,0),(251,130,0),(292,158,0),(338,163,0)]
for i in range(2,len(path)):
 x,y,z=path[i];path[i]=(x,y,groundheight(x,y)+.2)
for a,b in zip(path,path[1:]):
 a,b=Vector(a),Vector(b);d=b-a;n=Vector((-d.y,d.x,0)).normalized()*2.3
 B.poly([a-n,a+n,b+n,b-n],STONE)
B.done()
# glass conservatories on a planted lower eastern terrace
GREENGLASS=material('Greenhouse | rippled horticultural glass',(.10,.22,.22),.16,.15)
b=GREENGLASS.node_tree.nodes.get('Principled BSDF');b.inputs['Transmission Weight'].default_value=.65;b.inputs['IOR'].default_value=1.47
b.inputs['Emission Color'].default_value=(.13,.24,.18,1);b.inputs['Emission Strength'].default_value=.17
LEAF=material('Herbology foliage',(.045,.13,.048),.75)
for ix,x in enumerate([52,62,72]):
 y=21;z=50.1
 box('Greenhouse stone plinth',(x,y,z+.3),(7.6,19,.6),STONE,'Greenhouses',.06)
 B=Batch('Herbology glasshouse %d | cast iron ribs'%ix,'Greenhouses')
 # transparent pitched volume
 vs=[(x-3.5,y-9,z+.6),(x+3.5,y-9,z+.6),(x+3.5,y-9,z+4),(x,y-9,z+6.4),(x-3.5,y-9,z+4),
     (x-3.5,y+9,z+.6),(x+3.5,y+9,z+.6),(x+3.5,y+9,z+4),(x,y+9,z+6.4),(x-3.5,y+9,z+4)]
 B.geom(vs,[(0,1,2,3,4),(9,8,7,6,5)]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)],GREENGLASS)
 for j in range(13):
  yy=y-9+j*1.5
  pts=[(x-3.5,yy,z+.6),(x-3.5,yy,z+4),(x,yy,z+6.4),(x+3.5,yy,z+4),(x+3.5,yy,z+.6)]
  B.path(pts,.055,COPPER)
 for dx,dz in [(-3.5,2.2),(-3.5,4),(-1.75,5.2),(0,6.4),(1.75,5.2),(3.5,4),(3.5,2.2)]:
  B.rod((x+dx,y-9,z+dz),(x+dx,y+9,z+dz),.05,COPPER)
 for yy in [y-9,y+9]:
  for dx in [-2,-1,0,1,2]:B.rod((x+dx,yy,z+.6),(x+dx,yy,z+4.7),.045,COPPER)
 for j in range(25):
  px=x+random.uniform(-2.7,2.7);py=y+random.uniform(-8,8)
  B.rod((px,py,z+.7),(px,py,z+random.uniform(1,2.7)),.5,LEAF,7,.07)
 B.done()
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/hogwarts.blend')
