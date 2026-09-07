
class Batch:
 def __init__(self,name,col='Architecture_Detail'):
  self.name=name;self.col=col;self.v=[];self.f=[];self.mi=[];self.mats=[]
 def idx(self,m):
  if m not in self.mats:self.mats.append(m)
  return self.mats.index(m)
 def poly(self,pts,m):
  a=len(self.v);self.v.extend([tuple(p) for p in pts]);self.f.append(tuple(range(a,a+len(pts))));self.mi.append(self.idx(m))
 def geom(self,vs,fs,m):
  a=len(self.v);self.v.extend([tuple(p) for p in vs]);self.f.extend([tuple(a+i for i in f) for f in fs]);self.mi.extend([self.idx(m)]*len(fs))
 def cube(self,c,sz,m,angle=0):
  x,y,z=[v/2 for v in sz];vs=[]
  for a,b,d in [(-x,-y,-z),(-x,-y,z),(-x,y,-z),(-x,y,z),(x,-y,-z),(x,-y,z),(x,y,-z),(x,y,z)]:
   vs.append((c[0]+a*cos(angle)-b*sin(angle),c[1]+a*sin(angle)+b*cos(angle),c[2]+d))
  self.geom(vs,[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],m)
 def rod(self,a,b,r,m,n=8,r2=None):
  a,b=Vector(a),Vector(b);delta=b-a
  if delta.length<.0001:return
  q=delta.to_track_quat('Z','Y');vs=[]
  for z,rr in [(0,r),(delta.length,r if r2 is None else r2)]:
   for i in range(n):vs.append(a+q@Vector((rr*cos(2*pi*i/n),rr*sin(2*pi*i/n),z)))
  fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
  self.geom(vs,fs,m)
 def path(self,pts,r,m,n=6,closed=False):
  for a,b in zip(pts,pts[1:]):self.rod(a,b,r,m,n)
  if closed:self.rod(pts[-1],pts[0],r,m,n)
 def done(self,bev=0):
  o=mesh(self.name,self.v,self.f,None,self.col)
  for m in self.mats:o.data.materials.append(m)
  for p,i in zip(o.data.polygons,self.mi):p.material_index=i
  if bev:bevel(o,bev,2)
  return o
def archline(w,h,steps=12):
 spring=h-sqrt(3)*w/2
 pts=[(-w/2,0),(w/2,0),(w/2,spring)]
 for i in range(1,steps+1):
  t=i/steps*pi/3
  pts.append((-w/2+w*cos(t),spring+w*sin(t)))
 for i in range(1,steps+1):
  t=2*pi/3+i/steps*pi/3
  pts.append((w/2+w*cos(t),spring+w*sin(t)))
 return pts
def window(B,loc,w,h,a=0,lit=None,tracery=True):
 u=Vector((cos(a),sin(a),0));n=Vector((sin(a),-cos(a),0));origin=Vector(loc)
 def P(x,z,d):return origin+u*x+Vector((0,0,z))+n*d
 outline=archline(w,h);out=archline(w+.5,h+.28)
 # dark embrasure and recessed stained glass
 B.poly([P(x,z,.028) for x,z in out],DARK)
 mat=GLASS[random.choices(range(6),[23,20,18,24,10,5])[0]] if lit is None else GLASS[lit]
 B.poly([P(x*.92,z*.98+.04,.09) for x,z in outline],mat)
 # deeply carved ring in two moulded orders
 for j in range(len(out)):
  k=(j+1)%len(out)
  B.poly([P(*out[j],.28),P(*out[k],.28),P(*outline[k],.25),P(*outline[j],.25)],TRIM)
  B.poly([P(*outline[j],.25),P(*outline[k],.25),P(*outline[k],.1),P(*outline[j],.1)],STONE)
 B.path([P(x,z,.32) for x,z in out],.055,STONE,6,True)
 # sill
 mid=origin+n*.31+Vector((0,0,-.08))
 B.cube(mid,(w+.8,.65,.22),TRIM,a)
 spring=h-.866*w
 if tracery:
  for xx in [-w/6,w/6] if w>1.8 else [0]:
   top=spring+.15
   B.rod(P(xx,.08,.18),P(xx,top,.18),.045 if w<2 else .07,TRIM)
  B.rod(P(-w*.47,h*.38,.17),P(w*.47,h*.38,.17),.045,IRON)
  if h>4:B.rod(P(-w*.47,h*.68,.17),P(w*.47,h*.68,.17),.045,IRON)
  # trefoil / circular tracery in the arch head
  rr=w*.20;cz=spring+w*.27
  for k in range(3):
   cx=sin(k*2*pi/3)*rr*.63;zz=cz+cos(k*2*pi/3)*rr*.63
   pts=[P(cx+rr*.66*cos(t*2*pi/20),zz+rr*.66*sin(t*2*pi/20),.20) for t in range(21)]
   B.path(pts,.045,TRIM)
  # lead cames
  for xx in [-w*.34,0,w*.34]:
   B.rod(P(xx,.1,.13),P(xx,spring,.13),.015,IRON,4)
  for zz in [i*.62 for i in range(1,int(spring/.62)+1)]:
   B.rod(P(-w*.45,zz,.14),P(w*.45,zz,.14),.013,IRON,4)
 return mat
def finial(B,x,y,z,r=.23,h=2):
 B.rod((x,y,z),(x,y,z+h),r,IRON,8,.025)
 B.rod((x-.48,y,z+h*.64),(x+.48,y,z+h*.64),r*.3,GOLD,6)
 for zz,rr in [(z+.2,r*1.8),(z+h*.5,r*1.2)]:
  B.rod((x,y,zz-.06),(x,y,zz+.06),rr,GOLD,12)
def tiered_spire(name,x,y,z,r,h,material=ROOF):
 B=Batch(name)
 # slightly flared eaves and visible slate courses on a gently concave spire
 bands=max(16,int(h/.75))
 for i in range(bands):
  t=i/bands;t2=(i+1)/bands
  r1=r*(1-t)**1.08+.09;r2=r*(1-t2)**1.08+.055
  B.rod((x,y,z+h*t),(x,y,z+h*t2+.025),r1,material,48,r2)
 finial(B,x,y,z+h,.18,2.5)
 return B.done()
def turret(name,x,y,z,r,h,sp,roofmat=ROOF,sides=32):
 cone(name+' stone shaft',(x,y,z+h/2),r,r*.95,h,STONE,n=sides)
 B=Batch(name+' carved masonry')
 for zz,rr,hh in [(z+.6,r*1.08,.7),(z+h*.44,r*1.02,.27),(z+h-1,r*1.08,.65),(z+h,r*1.17,.45)]:
  B.rod((x,y,zz-hh/2),(x,y,zz+hh/2),rr,TRIM,32)
 for az in range(0,360,45):
  ph=math.radians(az)
  for zz in [z+h*.32,z+h*.66]:
   window(B,(x+(r+.01)*cos(ph),y+(r+.01)*sin(ph),zz),max(.55,r*.35),min(3.5,h*.18),ph+pi/2,tracery=r>1.5)
 for i in range(18):
  ph=2*pi*i/18
  B.cube((x+r*1.02*cos(ph),y+r*1.02*sin(ph),z+h-1.6),(.3,.55,.9),TRIM,ph)
 B.done()
 tiered_spire(name+' slate cap',x,y,z+h+.3,r*1.22,sp,roofmat)
# remove smooth provisional roofs
for name,x,y,z,r,h,sp in tower_specs:
 ob=bpy.data.objects.get(name+' roof')
 if ob:bpy.data.objects.remove(ob,do_unlink=True)
 tiered_spire(name+' coursed roof',x,y,z+h,r*1.15,sp,COPPER if name=='Bell Tower' else ROOF)
# great hall buttresses, sculptural pinnacles, facade bays
B=Batch('Great Hall | lancets, tracery and buttress orders')
for side in [-1,1]:
 yy=-8+side*11.05;a=0 if side==-1 else pi
 for i in range(11):
  xx=-62+5*i
  window(B,(xx,yy,65),2.55,6.2,a)
  window(B,(xx,yy,73),2.65,12.1,a,lit=(i%3),tracery=True)
 for i in range(12):
  xx=-64.5+i*5
  for zz,dep,ww,hh in [(65,2.5,1.25,8),(74,2,1.1,10),(82,1.5,.8,8),(87,.95,.65,3)]:
   B.cube((xx,yy+side*dep*.45,zz),(ww,dep,hh),STONE)
   B.cube((xx,yy+side*dep*.45,zz+hh/2),(ww+.25,dep+.28,.28),TRIM)
  B.rod((xx,yy+side*.5,89),(xx,yy+side*.5,93),.44,TRIM,4,.01)
 for zz in [62.3,71.9,86.5,88.2]:
  B.cube((-37,yy,zz),(57,.7,.36),TRIM)
 # corbel table
 for i in range(94):
  xx=-64.8+i*.6
  B.cube((xx,yy+side*.21,62.5),(.3,.65,.6),TRIM)
# end windows, rose above paired lancets
for xx,a in [(-65.04,-pi/2),(-8.96,pi/2)]:
 for yy in [-14,-8,-2]:
  window(B,(xx,yy,66),3.35,17,a,lit=1)
 # triangular gable stone screen in front roof
 pts=[(xx,-19,88.4),(xx,3,88.4),(xx,-8,106.5)]
 B.poly(pts,STONE)
 center=Vector((xx,-8,94));U=Vector((0,1,0));N=Vector((-1 if xx<-20 else 1,0,0))
 pts=[center+U*(3.2*cos(t*2*pi/48))+Vector((0,0,3.2*sin(t*2*pi/48)))+N*.1 for t in range(49)]
 B.poly(pts,GLASS[2]);B.path(pts,.25,TRIM)
 for k in range(12):
  ph=k*2*pi/12;B.rod(center+N*.25,center+N*.25+U*(3.1*cos(ph))+Vector((0,0,3.1*sin(ph))),.075,TRIM)
B.done()
for x in [-65,-9]:
 for y in [-19,3]:turret('Great Hall corner fleche',x,y,84,1.03,17,10)
# hall rooftop fleche and dormer casements
turret('Great Hall ridge fleche',-35,-8,103,1.45,6,15,COPPER,16)
B=Batch('Great Hall | dormers, gutters and slate seams')
for side in [-1,1]:
 for i in range(10):
  x=-61+i*5.2;y=-8+side*7.7;z=95.2
  B.cube((x,y,z),(1.45,1.4,2.6),STONE)
  # window in outward face of dormer
  window(B,(x,y+side*.73,z-.85),.8,1.7,0 if side<0 else pi,lit=3,tracery=False)
  gable('Hall dormer stone pediment',x,y,z+1.3,1.8,1.8,1.7,ROOF)
 B.path([(-66,-8+side*12.6,88.7),(-8,-8+side*12.6,88.7)],.13,IRON)
# tiled slopes with seams every 70 cm / staggered slate edges
for side in [-1,1]:
 for j in range(27):
  t=j/27;y=-8+side*(12.5*(1-t));z=88.5+18*t+.045
  B.path([(-66.5,y,z),(-7.5,y,z)],.035,ROOF,4)
B.done()
# main tower detailed belts, windows and machicolations
for name,x,y,z,r,h,sp in tower_specs:
 B=Batch(name+' | windows, string courses, machicolations')
 levels=list(range(6,int(h)-3,6))
 for li,zz in enumerate(levels):
  for j in range(14 if r>7 else 10):
   count=14 if r>7 else 10;ph=2*pi*(j+.18*(li%2))/count
   window(B,(x+(r*(1-.04*(zz/h))+.025)*cos(ph),y+(r*(1-.04*(zz/h))+.025)*sin(ph),z+zz),1.05 if r>7 else .9,3.2 if r>7 else 2.65,ph+pi/2)
 for dz in [1,h*.37,h*.7,h-3,h-.25]:
  rr=r*(1-.04*dz/h)+.25
  B.rod((x,y,z+dz),(x,y,z+dz+.35),rr,TRIM,64)
 for j in range(int(r*7)):
  ph=2*pi*j/int(r*7);rr=r*.99
  B.cube((x+rr*cos(ph),y+rr*sin(ph),z+h-1.6),(.42,.85,1.6),STONE,ph+pi/2)
 # roof dormers at two heights
 if r>5:
  for row in range(3 if r>9 else 2):
   dz=4+row*7;rr=r*1.15*(1-dz/sp)**1.08
   for j in range(12):
    ph=j*2*pi/12
    # outward-facing stone dormer tiny gabled canopy
    px=x+(rr+.05)*cos(ph);py=y+(rr+.05)*sin(ph)
    window(B,(px,py,z+h+dz),.62,1.55,ph+pi/2,lit=random.choice([0,2,3,3,4]),tracery=False)
    B.rod((px,py,z+h+dz+1.7),(px-.7*cos(ph),py-.7*sin(ph),z+h+dz+2.6),.48,ROOF,4,.03)
 B.done()
# high attached stair turrets, asymmetrical tower cluster
turret('Grand Staircase hanging turret',-14.5,14.5,117,1.85,22,13)
cone('Hanging turret corbel trumpet',(-14.5,14.5,114.5),.45,1.95,5,STONE)
for i,(x,y,z,r,h,sp) in enumerate([(26,26,94,2.5,32,20),(37,32,100,2.4,30,22),(37,21,86,2.1,24,20),(28,34,82,2.8,27,18),(44,28,77,2,27,17)]):
 turret('Astronomy attendant %02d'%i,x,y,z,r,h,sp)
# clock tower corner lancets and sharp pinnacles
B=Batch('Clock Tower | Gothic masonry and astronomical clock')
for a,loc in [(0,(35,-9.04,0)),(pi,(35,9.04,0)),(pi/2,(43.54,0,0)),(-pi/2,(26.46,0,0))]:
 ux,uy=cos(a),sin(a)
 for zz in [65,73,81,89]:
  for dx in [-5,0,5]:window(B,(loc[0]+ux*dx,loc[1]+uy*dx,zz),1.45,4,a)
 for zz in [62,71,79,87,95,103]:
  B.cube((loc[0],loc[1],zz),(17.8,.55,.3),TRIM,a)
# Clock dark brass dial in front of steep gable stonework
B.poly([(25.9,-10.54,103),(44.1,-10.54,103),(35,-10.54,122)],STONE)
cx,cy,cz=35,-10.7,107.5
pts=[(cx+3.7*cos(i*2*pi/96),cy,cz+3.7*sin(i*2*pi/96)) for i in range(96)]
B.poly(pts,DARK)
for rr,th in [(3.8,.19),(3.45,.06),(2.84,.055)]:
 B.path([(cx+rr*cos(i*2*pi/96),cy-.08,cz+rr*sin(i*2*pi/96)) for i in range(97)],th,GOLD)
for i in range(60):
 ph=2*pi*i/60;rr=3.12 if i%5==0 else 3.3
 B.rod((cx+rr*sin(ph),cy-.12,cz+rr*cos(ph)),(cx+3.42*sin(ph),cy-.12,cz+3.42*cos(ph)),.052 if i%5==0 else .026,GOLD)
for ph,len_ in [(.4,2.2),(2.4,2.9)]:
 B.rod((cx,cy-.18,cz),(cx+len_*sin(ph),cy-.18,cz+len_*cos(ph)),.095,GOLD)
# Roman numerals are actual text geometry, factory builtin font
for i,t in enumerate(['XII','I','II','III','IV','V','VI','VII','VIII','IX','X','XI']):
 ph=i*2*pi/12;d=bpy.data.curves.new('Clock numeral '+t,'FONT');d.body=t;d.align_x='CENTER';d.align_y='CENTER';d.size=.47;d.extrude=.008
 o=bpy.data.objects.new('Astronomical clock | '+t,d);COL['Architecture_Detail'].objects.link(o);o.location=(cx+3.02*sin(ph),cy-.16,cz+3.02*cos(ph));o.rotation_euler=(pi/2,0,0);d.materials.append(GOLD)
B.done()
for x in [26.5,43.5]:
 for y in [-8,8]:turret('Clock Tower corner pinnacle',x,y,96,1.15,13+(2 if y>0 else 0),12)
# all residential and cloister facade casements
B=Batch('Residential ranges | 240 leaded lancets')
for xx,yy,L,W,z,h in [(58,33,41,21,61,30),(-12,40,71,15,60.5,21),(14,-23,39,11,58.5,13)]:
 for side in [-1,1]:
  for zz in range(int(z+3),int(z+h-2),6):
   for dx in range(-int(L/2)+3,int(L/2)-1,4):
    window(B,(xx+dx,yy+side*(W/2+.035),zz),1.55,3.7,0 if side<0 else pi)
  for zz in [z+1,z+8,z+h-1]:
   B.cube((xx,yy+side*W/2,zz),(L+1,.55,.36),TRIM)
  for dx in range(-int(L/2),int(L/2)+1,5):
   B.cube((xx+dx,yy+side*(W/2+.25),z+h/2),(.65,1,h),STONE)
 for side in [-1,1]:
  for zz in range(int(z+3),int(z+h-2),6):
   for dy in [-W*.27,0,W*.27]:window(B,(xx+side*(L/2+.04),yy+dy,zz),1.8,4,pi/2 if side>0 else -pi/2)
B.done()
# Camera and mass corrections
s=bpy.context.scene
s.camera=bpy.data.objects['Cam_Hero'];s.camera.data.lens=43
s.camera.location=(222,-384,116);s.camera.rotation_euler=(Vector((20,6,73))-s.camera.location).to_track_quat('-Z','Y').to_euler()
for n in ['Near western Highland','Middle Highland ridge','Far Highland ridge']:
 o=bpy.data.objects[n]
 for v in o.data.vertices:v.co.z*=.52
# adjust base exposures now windows can be judged
for n in ['Moon | cool silver key','Last blue light | east rim','Dusk bounce on limestone']:
 bpy.data.objects[n].data.energy*=.18
bpy.data.objects['Moon directional'].data.energy=.7
s.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.24
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/hogwarts.blend')
