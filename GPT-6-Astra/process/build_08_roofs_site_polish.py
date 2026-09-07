from mathutils.noise import noise

# Individually laid slate shingles on the hero spires and the boathouse.
SLATES=[]
for i,f in enumerate([.72,.9,1.08,1.23]):
 m=material('Split slate | individual tile %d'%i,(.043*f,.07*f,.09*f),.49,.08)
 rough_shader(m,(.026*f,.045*f,.061*f),(.067*f,.097*f,.12*f),8,3,.014,.08)
 m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.5
 SLATES.append(m)
def tile(B,pts,normal,mat):
 normal=Vector(normal)*.035;vs=[Vector(p) for p in pts];vs+= [p-normal for p in vs]
 B.geom(vs,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],mat)
rng=random.Random(824)
for name,x,y,z,r,h,sp in tower_specs:
 if r<5:continue
 B=Batch(name+' | individually laid slate')
 r*=1.15;base=z+h;rows=int(sp/.43)
 for row in range(rows):
  t=row/rows;t2=min(1,(row+1.13)/rows)
  rlo=r*(1-t)**1.08+.14;rhi=r*(1-t2)**1.08+.10
  count=max(9,int(2*pi*rlo/.57))
  for j in range(count):
   a1=2*pi*(j+.5*(row%2))/count+.003;a2=2*pi*(j+1+.5*(row%2))/count-.003
   extra=rng.uniform(-.009,.017)
   pts=[(x+(rlo+extra)*cos(a1),y+(rlo+extra)*sin(a1),base+sp*t),(x+(rlo+extra)*cos(a2),y+(rlo+extra)*sin(a2),base+sp*t),(x+rhi*cos(a2),y+rhi*sin(a2),base+sp*t2),(x+rhi*cos(a1),y+rhi*sin(a1),base+sp*t2)]
   tile(B,pts,(cos((a1+a2)/2),sin((a1+a2)/2),r/sp),SLATES[rng.choices(range(4),[1,4,4,1])[0]])
 B.done()
# flat gabled slopes: rows of real, thin, overlapping stone tiles
def roof_tiles(name,x,y,z,L,W,H,longx=True):
 B=Batch(name)
 rows=int(sqrt((W/2)**2+H**2)/.58);cols=int(L/.57)
 for side in [-1,1]:
  for row in range(rows):
   t=row/rows;t2=min(1,(row+1.13)/rows)
   for col in range(cols):
    q1=-L/2+(col+.5*(row%2))*L/cols;q2=min(L/2,q1+L/cols-.015)
    if q1>=L/2:continue
    r1=W/2*(1-t);r2=W/2*(1-t2)
    if longx:
     pts=[(x+q1,y+side*r1,z+H*t+.085),(x+q2,y+side*r1,z+H*t+.085),(x+q2,y+side*r2,z+H*t2+.075),(x+q1,y+side*r2,z+H*t2+.075)]
     normal=(0,side*H,W/2)
    else:
     pts=[(x+side*r1,y+q1,z+H*t+.085),(x+side*r1,y+q2,z+H*t+.085),(x+side*r2,y+q2,z+H*t2+.075),(x+side*r2,y+q1,z+H*t2+.075)]
     normal=(side*H,0,W/2)
    tile(B,pts,Vector(normal).normalized(),SLATES[rng.choices(range(4),[1,4,4,1])[0]])
 B.done()
roof_tiles('Great Hall | overlapping roof slates',-37,-8,88.5,59,25,18)
roof_tiles('Boathouse | overlapping roof slates',40,-79,12.2,16,22,11,False)
# stone gables in the east wing instead of exposed triangular roof ends
for name in ['East wing roof','North cloister roof','South gallery roof']:
 o=bpy.data.objects[name];o.data.materials.append(STONE)
 for p in o.data.polygons[:2]:p.material_index=1
B=Batch('East range | traceried gables, chimneys and dormers')
for side in [-1,1]:
 x=58+side*22
 window(B,(x+side*.05,33,94),3.5,8,pi/2 if side>0 else -pi/2,lit=2)
 B.path([(x,21,91),(x,33,106),(x,45,91)],.22,TRIM)
for i in range(7):
 x=40+i*5.5
 for side in [-1,1]:
  y=33+side*7.7;z=96.2
  B.cube((x,y,z),(1.6,1.4,2.8),STONE)
  window(B,(x,y+side*.74,z-.9),.9,2,0 if side<0 else pi,lit=3 if i%3 else 2)
  gable('East wing dormer canopy',x,y,z+1.4,1.9,1.8,1.8,ROOF)
 if i%2==0:
  B.cube((x,35,106),(1.25,1,4),STONE)
  B.cube((x,35,108.1),(1.7,1.45,.35),TRIM)
  for dx in [-.35,.35]:B.rod((x+dx,35,108.2),(x+dx,35,109),.19,STONE,10)
B.done()
# herbology must be visible on its own ledge, below and outside the main rock.
for o in list(COL['Greenhouses'].objects):o.location+=Vector((36,12,-7))
cliff('Herbology | projecting lower crag',97,34,24,28,42,97)
fixnormals(box('Herbology | lower terrace foundation',(98,33,41.5),(35,35,4),STONE,bev=.4))
B=Batch('Herbology | lower terrace balustrade')
for yy in [15.5,50.5]:
 B.cube((98,yy,44),(35,1.1,1.3),STONE)
 B.cube((98,yy,44.8),(36,1.4,.25),TRIM)
 for x in range(81,117,2):B.cube((x,yy,45.3),(.8,1.2,.9),STONE)
B.done()
# Remove disconnected paving outside the actual enclosing polygon.
def insidepoly(x,y,p):
 inside=False
 j=len(p)-1
 for i in range(len(p)):
  xi,yi=p[i];xj,yj=p[j]
  if ((yi>y)!=(yj>y)) and x<(xj-xi)*(y-yi)/(yj-yi)+xi:inside=not inside
  j=i
 return inside
o=bpy.data.objects['Upper courts | flagstones, fountain and benches'];bm=bmesh.new();bm.from_mesh(o.data)
remove=[f for f in bm.faces if not insidepoly(f.calc_center_median().x,f.calc_center_median().y,poly)]
bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(o.data);bm.free()
# Clear stray talus from the boathouse's working apron.
o=bpy.data.objects['Black Rock | tilted buttress slabs and fallen scree'];bm=bmesh.new();bm.from_mesh(o.data)
seen=set();remove=[]
for v in bm.verts:
 if v in seen:continue
 stack=[v];comp=[];seen.add(v)
 while stack:
  cur=stack.pop();comp.append(cur)
  for e in cur.link_edges:
   w=e.other_vert(cur)
   if w not in seen:seen.add(w);stack.append(w)
 xs=[v.co.x for v in comp];ys=[v.co.y for v in comp];zs=[v.co.z for v in comp]
 if max(xs)>27 and min(xs)<66 and min(ys)<-81 and max(ys)>-98 and max(zs)>2.7:remove.extend(comp)
bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(o.data);bm.free()
# An ascending approach connects the level viaduct deck to the upper castle gate.
B=Batch('Viaduct | ascending gate stair and landing','Viaduct')
a=Vector((85,-12,50.03));b=Vector((61,-20,60.05));d=b-a;ang=math.atan2(d.y,d.x);le=Vector((d.x,d.y,0)).length;side=Vector((-d.y,d.x,0)).normalized();steps=53
for i in range(steps):
 p=a+d*((i+.5)/steps)
 B.cube((p.x,p.y,p.z-.24),(le/steps+.015,4,.48),STONE,ang)
 for sg in [-1,1]:
  q=p+side*2.3*sg
  B.cube((q.x,q.y,q.z-.45),(le/steps+.02,.7,2.9),STONE,ang)
  B.cube((q.x,q.y,q.z+1.1),(le/steps+.02,.95,.23),TRIM,ang)
for t in [.12,.43,.76]:
 p=a+d*t+side*2.3;lantern(B,p.x,p.y,p.z+1.25,1,.28,True)
B.cube((61,-20,59.7),(7,7,.7),STONE)
B.done()
# quiet structural ironwork and mooring hardware are visible at close range
B=Batch('Boathouse | weathered mooring hardware','Boathouse')
for x,y in [(28,-88),(51,-88),(54,-101)]:
 for zz in [1.9,2.1]:
  B.path([(x+.26*cos(t*2*pi/24),y+.26*sin(t*2*pi/24),zz) for t in range(25)],.035,IRON)
 B.rod((x,y,1.5),(x,y,2.4),.13,WOOD)
B.done()
# final composition corrections for full subjects in supporting views
o=bpy.data.objects['Cam_Detail_01'];o.location=(-54,-78,144);o.data.lens=58;o.rotation_euler=(Vector((-8,13,139))-o.location).to_track_quat('-Z','Y').to_euler()
o=bpy.data.objects['Cam_Detail_02'];o.location=(82,-141,24);o.data.lens=48;o.rotation_euler=(Vector((42,-80,10))-o.location).to_track_quat('-Z','Y').to_euler()
o=bpy.data.objects['Cam_Aerial'];o.location=(278,-252,265);o.data.lens=34;o.rotation_euler=(Vector((22,10,59))-o.location).to_track_quat('-Z','Y').to_euler()
o=bpy.data.objects['Cam_Viaduct'];o.location=(128,-12,51.8);o.data.lens=24;o.rotation_euler=(Vector((28,3,84))-o.location).to_track_quat('-Z','Y').to_euler()
# Use a subtle photographic lens glow.
ng=bpy.data.node_groups.new('Hogwarts | final lens response','CompositorNodeTree')
ng.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
rl=ng.nodes.new('CompositorNodeRLayers');gl=ng.nodes.new('CompositorNodeGlare');gl.inputs['Type'].default_value='Fog Glow';gl.inputs['Quality'].default_value='High'
out=ng.nodes.new('NodeGroupOutput');ng.links.new(rl.outputs['Image'],gl.inputs['Image']);ng.links.new(gl.outputs['Image'],out.inputs['Image'])
s.compositing_node_group=ng
# adjustable through modern Blender glare socket interface
for inp in gl.inputs:
 if inp.name=='Threshold':inp.default_value=1.4
 if inp.name=='Strength':inp.default_value=.16
 if inp.name=='Size':inp.default_value=.45
for o in list(COL['Architecture_Detail'].objects)+list(COL['Viaduct'].objects)+list(COL['Greenhouses'].objects):
 if o.type=='MESH':fixnormals(o)
s.camera=bpy.data.objects['Cam_Hero']
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/hogwarts.blend')
