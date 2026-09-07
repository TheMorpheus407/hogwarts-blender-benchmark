
# Make future boxes outward-facing at creation; recalc all new geometry before saving.
def fixnormals(o):
 if o.type=='MESH':
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 return o
# air mostly behind the castle, with restrained foreground scattering
AIR.node_tree.nodes.get('Principled Volume').inputs['Density'].default_value=.00028
bpy.data.objects['Blue atmospheric depth'].location=(0,760,310)
bpy.data.objects['Blue atmospheric depth'].scale.y=.66
BACKAIR=volume('Valley haze | background separation',.0013,(.44,.61,.74))
fixnormals(box('Haze behind the castle',(0,680,125),(2600,1100,250),BACKAIR,'FX'))
MIST.node_tree.nodes.get('Math.001').inputs[1].default_value=.008
# add concentrated low fog ribbons to the western lake and wooded ravine
FOGRIB=volume('Low fog banks | silver vapour',.027,(.55,.67,.72),True)
for i,(loc,sc) in enumerate([((-85,-42,4),(115,31,9)),((118,50,14),(140,44,20)),((-159,83,21),(160,61,25))]):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=loc)
 o=bpy.context.object;o.name='Low drifting fog bank %d'%i;o.scale=sc
 for c in list(o.users_collection):c.objects.unlink(o)
 COL['FX'].objects.link(o);o.data.materials.append(FOGRIB)
# give pine crowns substantial, irregular layered foliage and preserve the fine branches
for idx,(proto,h) in enumerate(PROTOS):
 rng=random.Random(760+idx);B=Batch('Temporary pine canopy','Nature')
 for tier in range(11):
  z=h*(.2+.068*tier);r=h*.235*(1-z/h)**.75;n=19;vs=[]
  angles=[2*pi*j/n for j in range(n)]
  rad=[rng.uniform(.7,1.2)*r for j in range(n)]
  for k in range(3):
   for j,a in enumerate(angles):
    fac=[1,.74,.05][k]
    xx=rad[j]*fac*cos(a);yy=rad[j]*fac*sin(a);zz=z+[rng.uniform(-.5,.03),.35,r*1.03][k]
    vs.append((xx,yy,zz))
  for j in range(n):
   for k in range(2):
    a=k*n+j;b=k*n+(j+1)%n
    B.geom([vs[a],vs[b],vs[b+n],vs[a+n]],[(0,1,2),(0,2,3)],NEEDLES[rng.randrange(4)])
 o=B.done();old=proto.data
 verts=[v.co[:] for v in old.vertices]+[v.co[:] for v in o.data.vertices];off=len(old.vertices)
 fs=[tuple(p.vertices) for p in old.polygons]+[tuple(off+i for i in p.vertices) for p in o.data.polygons]
 mats=list(old.materials);indices=[p.material_index for p in old.polygons]
 for p in o.data.polygons:
  ma=o.data.materials[p.material_index]
  if ma not in mats:mats.append(ma)
  indices.append(mats.index(ma))
 new=bpy.data.meshes.new('Pine %02d | dense layered foliage'%idx);new.from_pydata(verts,[],fs);new.update()
 for ma in mats:new.materials.append(ma)
 for p,mi in zip(new.polygons,indices):p.material_index=mi
 for ob in bpy.data.objects:
  if ob.type=='MESH' and ob.data==old:ob.data=new
 bpy.data.objects.remove(o,do_unlink=True)
 fixnormals(proto)
# thicker groves in the castle's middle-distance frame
rng=random.Random(4702);newtrees=0
for i in range(11400):
 x=rng.uniform(-330,365);y=rng.uniform(-45,380);z=groundheight(x,y)
 if z<2 or z>90 or (-115<x<127 and y<101):continue
 if 129<x<192 and -35<y<27:continue
 if any((x-p[0])**2+(y-p[1])**2<65 for p in path):continue
 if noise(Vector((x*.023,y*.023,3)))<-.37:continue
 proto,h=PROTOS[i%len(PROTOS)]
 o=bpy.data.objects.new('Dense grove pine %04d'%newtrees,proto.data);COL['Nature'].objects.link(o);o.location=(x,y,z-.3)
 sc=rng.uniform(.65,1.35);o.scale=(sc*1.1,sc*1.1,sc);o.rotation_euler.z=rng.uniform(0,2*pi);newtrees+=1
# Bedrock headland top grows into turf and has no empty table-like summit
o=bpy.data.objects['Eastern crag | eroded gneiss']
o.data.materials.append(GROUND)
for p in o.data.polygons:
 if p.center.z>43:p.material_index=1
B=Batch('Bridge headland | planted summit','Nature')
for i in range(130):
 x=rng.uniform(128,185);y=rng.uniform(-10,43)
 if ((x-153)/32)**2+((y-18)/38)**2>1:continue
 if abs(y+12)<7:continue
 proto,h=PROTOS[i%len(PROTOS)];o=bpy.data.objects.new('Headland pine %03d'%i,proto.data);COL['Nature'].objects.link(o);o.location=(x,y,46);sc=rng.uniform(.55,1);o.scale=(sc,sc,sc);o.rotation_euler.z=rng.uniform(0,6)
# join road at correct height, geometric cobbles on landing
for i in range(19):
 for j in range(8):
  B.cube((153+i*1.3,-16+j*1.05,48.4-i*.08),(1.24,1,.14),STONE)
B.done()
# A gate pavilion terminates the viaduct and hides the transition to the hill road.
for x in [148.6,158.5]:
 turret('Viaduct gatehouse octagonal tower',x,-10,46.3,2,10.5,9,ROOF,16)
B=Batch('Viaduct gatehouse | pointed entry','Viaduct')
for x in [150.5,156.5]:B.cube((x,-10,50.3),(1.1,4,8),STONE)
pts=archline(5,7);p0=Vector((153.5,-12.05,48.5))
B.path([p0+Vector((x,0,z)) for x,z in pts[2:]],.38,TRIM)
B.cube((153.5,-10,55.7),(7,4,1.6),STONE)
B.cube((153.5,-10,56.7),(8,4.8,.32),TRIM)
for x in [150.1,151.8,153.5,155.2,156.9]:B.cube((x,-12,57.3),(.8,.7,1),STONE)
lantern(B,150,-12.5,49,2.1,.36,True);lantern(B,157,-12.5,49,2.1,.36,True)
B.done()
# Blank defensive terrace faces receive a continuous blind Gothic arcade.
B=Batch('South terrace | carved blind arcade and buttress corbels')
for ii in range(5):
 x,y=poly[ii];nx,ny=poly[ii+1];d=Vector((nx-x,ny-y,0));le=d.length;ang=math.atan2(d.y,d.x)
 # polygon runs CCW around cliff; outward facade is right-hand side
 outward=Vector((sin(ang),-cos(ang),0))
 for j in range(int(le/3)):
  p=Vector((x,y,54.8))+d*((j+.5)/int(le/3))+outward*1.04
  window(B,p,1.7,3.5,ang,lit=3,tracery=True)
  q=p+outward*.1
  B.cube((q.x,q.y,53.4),(.5,.75,2),TRIM,ang)
B.done()
# Fine splintering around cliff buttresses, less repeated vertical columns.
B=Batch('Cliff | mica fracture plates and scree detail','Terrain')
for i in range(1250):
 a=rng.uniform(pi,2*pi);t=rng.uniform(.03,.96);rr=1.12-.18*t
 x=82*rr*cos(a);y=14+54*rr*sin(a);z=t*54
 shard(B,x,y,z,rng.uniform(.35,1.5),rng.uniform(.25,1.1),rng.uniform(.6,3.8),rng.uniform(.05,.7),5000+i)
B.done()
# More slate seams on long roofs to catch grazing light.
B=Batch('Roof slopes | raised slate lips')
for xx,yy,zz,L,W,H in [(58,33,91,44,24,15),(-12,40,81.5,74,17,12),(14,-23,71.5,40,12,9)]:
 for side in [-1,1]:
  for j in range(int(H/.47)):
   t=j/int(H/.47);y=yy+side*W/2*(1-t);z=zz+H*t+.035
   B.rod((xx-L/2,y,z),(xx+L/2,y,z),.026,ROOF,4)
B.done()
# lower blue key reveals fracture planes while warm pools ground the architecture
light('Lake bounce | cliff revelation','AREA',(-98,-153,71),(.31,.52,.7),155000,100,(0,-20,28))
light('Castle | warm hall bounce','AREA',(-50,-33,69),(1,.43,.16),11000,25,(-40,-19,79))
light('Boathouse | warm landing bounce','AREA',(43,-96,9),(1,.48,.20),1500,12,(42,-76,8))
light('Moon | forest edge silver','AREA',(-80,110,155),(.44,.64,.86),320000,150,(20,140,12))
bpy.data.objects['Dusk bounce on limestone'].data.energy=180000
bpy.data.objects['Moon directional'].data.energy=.45
s.view_settings.exposure=.55
# Moon's large-scale mineral seas and subtle crater speckle
nt=MOON.node_tree;l=nt.links;bs=nt.nodes.get('Principled BSDF');tc=nt.nodes.get('Texture Coordinate');no=nt.nodes.get('Noise Texture')
l.new(tc.outputs['Generated'],no.inputs[0]);no.inputs['Scale'].default_value=5;no.inputs['Detail'].default_value=3;no.inputs['Roughness'].default_value=.7
r=nt.nodes.get('Color Ramp');setramp(r,[(.24,(.12,.20,.26)),(.49,(.37,.49,.57)),(.64,(.7,.79,.82))]);bs.inputs['Emission Strength'].default_value=1.1
# seven working camera compositions
cam('Cam_Detail_01',(-20,-34,137),(-9,12,131),62)
cam('Cam_Detail_02',(75,-121,19),(40,-80,11),56)
cam('Cam_Detail_03',(-49,-64,80),(-42,-18,79),57)
o=bpy.data.objects['Cam_Boathouse'];o.location=(117,-206,13);o.data.lens=29;o.rotation_euler=(Vector((7,-4,76))-o.location).to_track_quat('-Z','Y').to_euler()
o=bpy.data.objects['Cam_Viaduct'];o.location=(130,-20,54.8);o.data.lens=26;o.rotation_euler=(Vector((12,7,94))-o.location).to_track_quat('-Z','Y').to_euler()
# Hero: include breathing room below the boathouse and across the reflective lake.
o=bpy.data.objects['Cam_Hero'];o.data.lens=40;o.location=(225,-419,113);o.rotation_euler=(Vector((18,1,65))-o.location).to_track_quat('-Z','Y').to_euler()
# repair normals on newly authored solids
for o in list(bpy.data.objects):
 if o.type=='MESH' and not (o.name.startswith('Highland pine') or o.name.startswith('Dense grove') or o.name.startswith('Headland pine')):fixnormals(o)
s.camera=bpy.data.objects['Cam_Hero'];s.cycles.samples=96
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/hogwarts.blend')
