
# The viaduct is solid masonry above true open arches.
for o in list(bpy.data.objects):
 if o.name.startswith('BLOCK'):bpy.data.objects.remove(o,do_unlink=True)
B=Batch('Grand Viaduct | voussoirs, true arches and tall cutwater piers','Viaduct')
start=65;span=10.8;count=8;yy=-12;deck=49;spring=36;rad=4.1;depth=8.5
for i in range(count):
 cx=start+span*(i+.5)
 # arch soffit and the masonry spandrel, triangulated curved inner edge
 for j in range(32):
  t1=j*pi/32;t2=(j+1)*pi/32
  x1=cx-rad*cos(t1);z1=spring+rad*sin(t1)
  x2=cx-rad*cos(t2);z2=spring+rad*sin(t2)
  for side in [-1,1]:
   y=yy+side*depth/2
   B.poly([(x1,y,z1),(x2,y,z2),(x2,y,deck),(x1,y,deck)],STONE)
   # lighter radial arch blocks with joints
   ta=t1+.012;tb=t2-.012;ro=rad+.66
   B.poly([(cx-rad*cos(ta),y+side*.1,spring+rad*sin(ta)),(cx-rad*cos(tb),y+side*.1,spring+rad*sin(tb)),(cx-ro*cos(tb),y+side*.1,spring+ro*sin(tb)),(cx-ro*cos(ta),y+side*.1,spring+ro*sin(ta))],TRIM)
  B.poly([(x1,yy-depth/2,z1),(x1,yy+depth/2,z1),(x2,yy+depth/2,z2),(x2,yy-depth/2,z2)],STONE)
 # space between arches from water to deck
for i in range(count+1):
 x=start+span*i
 B.cube((x,yy,23),(span-2*rad,depth,52),STONE)
 B.cube((x,yy,1.6),(4.5,11,3.5),ROCK)
 for side in [-1,1]:
  # triangular cutwaters
  vs=[(x-1.4,yy+side*4.1,0),(x+1.4,yy+side*4.1,0),(x,yy+side*6.2,0),
      (x-1.4,yy+side*4.1,26),(x+1.4,yy+side*4.1,26),(x,yy+side*6.2,22)]
  B.geom(vs,[(0,1,2),(0,3,4,1),(1,4,5,2),(2,5,3,0),(3,5,4)],STONE)
  B.cube((x,yy+side*4.25,44),(.65,.55,10),TRIM)
for z,h,w in [(48.8,.65,9.4),(49.6,.3,10),(50,.22,10.1)]:
 B.cube((start+span*count/2,yy,z),(span*count+3,w,h),TRIM)
# full-height parapet with open pointed arcade along its length
for side in [-1,1]:
 y=yy+side*4.5
 B.cube((start+span*count/2,y,50.35),(span*count+3,.55,.7),STONE)
 B.cube((start+span*count/2,y,52.4),(span*count+3,.85,.3),TRIM)
 for i in range(73):
  x=start-1+i*1.22
  B.cube((x,y,51.4),(.33,.6,1.8),STONE)
  # paired angled arch moulding above each small opening
  B.path([(x+.12,y,51.7),(x+.6,y,52.2),(x+1.07,y,51.7)],.12,TRIM)
B.done(.035)
# masonry road surface / individual paving slabs
B=Batch('Viaduct | worn flagstones','Viaduct')
for i in range(145):
 for j in range(7):
  B.cube((64+i*.61,-14.9+j*.92,49.95),(.58,.87,.08),STONE)
B.done()
LANTERN=material('Lantern | honey flame',(.9,.38,.075),.28)
bs=LANTERN.node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Color'].default_value=(1,.4,.09,1);bs.inputs['Emission Strength'].default_value=7
def lantern(B,x,y,z,post=2.2,size=.38,withlight=False):
 B.rod((x,y,z),(x,y,z+post),.06,IRON)
 for zz in [z+.06,z+post-.28]:
  B.rod((x,y,zz),(x,y,zz+.12),.14,IRON)
 B.cube((x,y,z+post),(size,size,size*1.6),LANTERN)
 for dx in [-size*.55,size*.55]:
  for dy in [-size*.55,size*.55]:
   B.rod((x+dx,y+dy,z+post-size*.8),(x+dx,y+dy,z+post+size*.8),.025,IRON,4)
 B.rod((x,y,z+post+size*.8),(x,y,z+post+size*1.7),size*.9,IRON,4,.04)
 B.cube((x,y,z+post-size*.83),(size*1.3,size*1.3,.09),IRON)
 if withlight:light('Lantern pool','POINT',(x,y,z+post),(1,.42,.105),38,.5)
B=Batch('Grand Viaduct | lantern procession','Viaduct')
for i in range(9):
 for side in [-1,1]:lantern(B,65+i*span,yy+side*4.5,52.5,1.1,.33,i%2==0)
B.done()
# Stepped castle terraces with continuous defensive circuit
poly=[(-76,-13),(-65,-34),(-20,-44),(14,-43),(46,-33),(73,-13),(76,20),(64,47),(25,61),(-30,59),(-67,35)]
mesh('Upper terrace | courtyard platform',[(x,y,59.8) for x,y in poly],[tuple(range(len(poly)))],STONE)
B=Batch('Outer ward | crenels, corbels and retaining walls')
for i,(x,y) in enumerate(poly):
 nx,ny=poly[(i+1)%len(poly)];a=Vector((x,y,0));b=Vector((nx,ny,0));d=b-a;length=d.length;angle=math.atan2(d.y,d.x);mid=(a+b)/2
 B.cube((mid.x,mid.y,56),(length,2,8),STONE,angle)
 B.cube((mid.x,mid.y,60.15),(length+1,2.5,.4),TRIM,angle)
 B.cube((mid.x,mid.y,61),(length,1.2,1.5),STONE,angle)
 B.cube((mid.x,mid.y,61.8),(length+1,1.45,.25),TRIM,angle)
 for j in range(int(length/1.8)):
  p=a+d*((j+.5)/int(length/1.8))
  B.cube((p.x,p.y,62.35),(.85,1.4,1.1),STONE,angle)
 for j in range(int(length/.9)):
  p=a+d*((j+.5)/int(length/.9))
  B.cube((p.x,p.y,59.15),(.32,2.3,.9),TRIM,angle)
B.done(.04)
# lower eastern terraces for greenhouses
for x,y,z,w,d in [(57,6,50,33,35),(63,28,44,28,35)]:
 box('Lower herbology terrace',(x,y,z-3),(w,d,6),STONE,bev=.45)
 B=Batch('Herbology terrace parapet')
 for yy in [y-d/2,y+d/2]:
  B.cube((x,yy,z+.6),(w+1,1,1.2),STONE)
  B.cube((x,yy,z+1.25),(w+1.5,1.3,.25),TRIM)
 B.done()
# Corner towers at the boundary, distinct roofs or battlements
turret('South cliff watchtower',-20,-42,50,3.2,12,7,COPPER)
turret('East curtain watchtower',74,18,44,3.3,21,12)
# Clock courtyard paving, fountain and colonnade
B=Batch('Upper courts | flagstones, fountain and benches')
for i in range(55):
 for j in range(21):
  x=-64+i*2.45;y=-38+j*4.5
  if random.random()>.11:B.cube((x,y,60.04),(2.38,4.42,.14),TRIM if random.random()<.12 else STONE)
B.rod((5,10,60),(5,10,60.4),4.2,STONE,32)
B.rod((5,10,60.4),(5,10,61.4),3.4,TRIM,32)
B.rod((5,10,61.4),(5,10,62.5),.5,TRIM,16)
B.rod((5,10,62.5),(5,10,62.8),1.5,TRIM,32)
for x,y in [(-5,-32),(7,-32),(22,16),(-22,12)]:
 B.cube((x,y,60.6),(3,1.1,.3),TRIM)
 for dx in [-1,1]:B.cube((x+dx,y,60.25),(.4,.9,.65),STONE)
B.done()
# flying buttresses above cloister passage, two-tier arches
B=Batch('Flying buttresses | south transept')
for x in [-5,1,7,13,19]:
 a=(x,-22,79);b=(x,-34,67)
 pts=[(x,-22-t*12,79-8*t-4*t*t) for t in [i/24 for i in range(25)]]
 B.path(pts,.38,STONE)
 pts2=[(x,-22-t*12,80.1-8*t-4*t*t) for t in [i/24 for i in range(25)]]
 for p,q,r,s0 in zip(pts,pts[1:],pts2,pts2[1:]):B.poly([p,q,s0,r],STONE)
 B.cube((x,-34,65),(.9,1.6,10),STONE)
 B.rod((x,-34,70),(x,-34,75),.44,TRIM,4,.01)
B.done()
# Lanterns on paths within the upper ward
B=Batch('Courtyard lanterns')
for x,y in [(-65,-30),(-53,-34),(-39,-37),(-24,-39),(-6,-36),(10,-36),(27,-32),(44,-26),(63,-19),(73,5),(-65,26),(-36,55),(12,56),(56,44)]:
 lantern(B,x,y,60,2.2,.38,True)
B.done()
# The boathouse: a stone undercroft and timber Gothic hall at lake level
bx,by=40,-79
crag('Boathouse shelf',bx,by,21,14,3.2,70)
box('Boathouse landing platform',(bx,by,2.1),(26,21,2.7),STONE,'Boathouse',.25)
box('Boathouse | stone hall',(bx,by,7.2),(20,13,10),STONE,'Boathouse',.15)
gable('Boathouse | steep slate gable',bx,by,12.2,22,16,11,ROOF,'Boathouse')
# two front boat openings read as deep arched recesses
B=Batch('Boathouse | carved portals, boarding and glazed gallery','Boathouse')
for dx in [-5,5]:
 window(B,(bx+dx,by-6.57,3),5.6,6.1,0,lit=3)
 # dark open portico, timber doors recessed inside
 for j in range(15):
  xx=bx+dx-2.6+j*.37
  B.cube((xx,by-6.71,5.2),(.33,.1,4.4),WOOD)
 for zz in [3.6,6]:
  B.cube((bx+dx,by-6.84,zz),(5.5,.15,.17),IRON)
 for sx in [-1,1]:
  for zz in [3.6,6]:
   B.cube((bx+dx+sx*2,by-6.97,zz),(.85,.09,.15),IRON)
for side in [-1,1]:
 for j in range(6):
  y=by-5+j*2
  window(B,(bx+side*10.07,y,8.6),1.35,2.8,pi/2 if side>0 else -pi/2,lit=j%3)
for x in [bx-10,bx,bx+10]:
 B.cube((x,by-6.75,7.5),(.65,.8,10.4),TRIM)
B.poly([(bx-10,by-8.05,12),(bx+10,by-8.05,12),(bx,by-8.05,23)],STONE)
window(B,(bx,by-8.1,13),3.4,6.4,lit=0)
for side in [-1,1]:
 B.path([(bx,by-8.15,23),(bx+side*10.7,by-8.15,12)],.21,TRIM)
 B.path([(bx+side*9.5,by-8.18,12.5),(bx+side*.4,by-8.18,12.5)],.12,WOOD)
 for j in range(1,5):
  x=bx+side*j*1.7;top=22-j*1.7
  B.cube((x,by-8.13,(top+12.5)/2),(.19,.24,top-12.5),WOOD)
# side buttresses and roof dormers
for side in [-1,1]:
 for j in range(5):
  y=by-5+j*2.6
  B.cube((bx+side*10.5,y,6),(1.3,.9,8.5),STONE)
  B.cube((bx+side*10.5,y,10.3),(1.6,1.2,.25),TRIM)
  if j%2==0:
   x=bx+side*6.8;z=15.6
   B.cube((x,y,z),(1.6,1.2,2),STONE)
   window(B,(x+side*.86,y,z-.7),.7,1.5,pi/2 if side>0 else -pi/2,lit=2,tracery=False)
B.done(.025)
turret('Boathouse bell lantern',bx,by+4,20,1.1,3,5,COPPER)
B=Batch('Boathouse | lamps and mooring wharf','Boathouse')
for dx in [-11.2,0,11.2]:
 lantern(B,bx+dx,by-9.4,3.5,2.1,.4,True)
# wooden dock to foreground
for i in range(46):
 B.cube((bx+14,by-8-i*.38,1.35),(4.2,.35,.24),WOOD)
for xx in [bx+12.2,bx+15.8]:
 for yy in [by-10,by-17,by-24]:
  B.rod((xx,yy,-2),(xx,yy,2.5),.19,WOOD,10)
  for z in [1.9,2.02,2.14]:B.rod((xx,yy,z),(xx,yy,z+.06),.23,WOOD,10)
B.done()
# handcrafted clinker rowing boats at the quay
def boat(name,x,y,rot):
 B=Batch(name,'Boathouse');vs=[];N=18
 for layer in range(5):
  t=layer/4
  for i in range(N):
   ph=i*2*pi/N
   xx=(.55+.35*t)*cos(ph)*(abs(sin(ph))*.35+.65);yy=2.5*sin(ph)
   zz=.25+layer*.16
   vs.append((xx*cos(rot)-yy*sin(rot)+x,xx*sin(rot)+yy*cos(rot)+y,zz))
 for j in range(4):
  for i in range(N):B.poly([vs[j*N+i],vs[j*N+(i+1)%N],vs[(j+1)*N+(i+1)%N],vs[(j+1)*N+i]],WOOD)
 B.path(vs[-N:]+[vs[-N]],.07,WOOD)
 for yy in [-1.1,0,1.1]:
  p=(x-yy*sin(rot),y+yy*cos(rot),.75)
  B.cube(p,(1.45,.25,.13),WOOD,rot)
 B.done()
boat('Rowing boat | north mooring',57,-92,-.13)
boat('Rowing boat | waiting by steps',49,-93,.5)
# long stair; every riser, coping stone and supporting wall modeled
stairpts=[(45,-69,3.5),(18,-59,20.5),(50,-42,37.5),(9,-41,59.8)]
B=Batch('Boathouse stair | 300 stone treads and switchback retaining walls','Boathouse')
for k,(a,b) in enumerate(zip(stairpts,stairpts[1:])):
 a,b=Vector(a),Vector(b);d=b-a;flat=Vector((d.x,d.y,0));le=flat.length;unit=flat/le;normal=Vector((-unit.y,unit.x,0));angle=math.atan2(d.y,d.x);steps=int((b.z-a.z)/.19)
 for j in range(steps):
  t=(j+.5)/steps;p=a+d*t
  B.cube((p.x,p.y,p.z-.15),(le/steps+.035,2.8,.35),STONE,angle)
 for side in [-1,1]:
  for j in range(steps):
   p=a+d*((j+.5)/steps)+normal*side*1.65
   # thick retaining wall underneath stair, all tied into cliff
   B.cube((p.x,p.y,p.z-2.7),(le/steps+.04,.55,7),STONE,angle)
   B.cube((p.x,p.y,p.z+1),(le/steps+.04,.75,.24),TRIM,angle)
  for t in [.05,.3,.55,.8]:
   p=a+d*t+normal*side*1.65
   lantern(B,p.x,p.y,p.z+1.15,1,.3,side<0)
 for p in [a,b]:B.cube((p.x,p.y,p.z-.2),(4,4,.5),TRIM,angle)
B.done(.02)
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/hogwarts.blend')
