
# Lower the lake-washed shelf below the working apron and build proper launch slipways.
bpy.data.objects['Boathouse | lake-washed bedrock'].scale.z=.40
B=Batch('Boathouse | twin launch slipways','Boathouse')
for x in [35,45]:
 a=Vector((x,-88.7,3.42));b=Vector((x,-102,.22))
 # masonry wedge rises continuously from the lake
 vs=[(x-2.7,-88.7,3.42),(x+2.7,-88.7,3.42),(x+2.7,-102,.22),(x-2.7,-102,.22),(x-2.7,-88.7,-1),(x+2.7,-88.7,-1),(x+2.7,-102,-1),(x-2.7,-102,-1)]
 B.geom(vs,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],STONE)
 for j in range(30):
  t=j/29;p=a.lerp(b,t)
  B.cube((p.x,p.y,p.z+.045),(5.3,.17,.07),WOOD)
 for sx in [-1.8,1.8]:
  B.rod((x+sx,-88.7,3.56),(x+sx,-102,.35),.09,WOOD)
B.done();fixnormals(bpy.data.objects['Boathouse | twin launch slipways'])
# An arriving rowing boat provides a restrained human scale cue across the lake.
boat('Arrival | rowing boat on the Black Lake',-4,-116,.48)
B=Batch('Arrival | cloaked passengers, oars and bow lantern','Boathouse')
for xx,yy in [(-4.2,-116.5),(-3.8,-115.4),(-4.8,-117.1)]:
 B.rod((xx,yy,.67),(xx,yy,1.64),.26,IRON,9,.13)
 B.rod((xx,yy,1.54),(xx,yy,1.85),.17,IRON,9,.1)
B.rod((-4.6,-116,.9),(-7.3,-115.8,.28),.038,WOOD)
B.rod((-3.4,-116,.9),(-1,-117.3,.24),.038,WOOD)
B.cube((-7.15,-115.8,.29),(.65,.19,.04),WOOD,.1)
B.cube((-1.1,-117.23,.26),(.65,.19,.04),WOOD,-.4)
lantern(B,-3.3,-114.3,.55,.55,.19,True)
B.done()
o=bpy.data.objects['Cam_Detail_02'];o.data.lens=43;o.rotation_euler=(Vector((42,-82,10))-o.location).to_track_quat('-Z','Y').to_euler()
# No timeline camera binding may override an explicit render camera.
for marker in s.timeline_markers:marker.camera=None
s.camera=bpy.data.objects['Cam_Hero']
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/hogwarts.blend')
