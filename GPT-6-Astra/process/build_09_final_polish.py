
# Restrained final grading and per-view framing adjustments.
o=bpy.data.objects['Cam_Detail_01'];o.data.lens=49;o.rotation_euler=(Vector((-8,13,142))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.data.objects['Moon above the eastern Highlands'].location.z+=145
for i in [3,4]:
 bs=GLASS[i].node_tree.nodes.get('Principled BSDF')
 bs.inputs['Base Color'].default_value=(.009,.024,.027,1) if i==3 else (.047,.033,.017,1)
 bs.inputs['Roughness'].default_value=.18;bs.inputs['Metallic'].default_value=.03
 bs.inputs['Specular IOR Level'].default_value=.32
bs=GREENGLASS.node_tree.nodes.get('Principled BSDF')
bs.inputs['Transmission Weight'].default_value=.96;bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.1;bs.inputs['Base Color'].default_value=(.6,.74,.66,1);bs.inputs['Emission Strength'].default_value=0
# the major distant ridges rise above the near wooded slopes
for name,f in [('Middle Highland ridge',1.55),('Far Highland ridge',1.75)]:
 o=bpy.data.objects[name]
 for v in o.data.vertices:v.co.z*=f
 for p in o.data.polygons:p.use_smooth=True
 m=material(name+' | distant exposed stone',(.055,.077,.096))
 rough_shader(m,(.028,.044,.059),(.13,.145,.15),.021,5,.2)
 o.data.materials.clear();o.data.materials.append(m)
# Footpath and steps between the herbology ledge and castle's east terrace.
B=Batch('Herbology | garden access stair and lamps','Greenhouses')
a=Vector((81,41,59.5));b=Vector((90,48,43.6));d=b-a;ang=math.atan2(d.y,d.x);steps=83;le=Vector((d.x,d.y,0)).length
for i in range(steps):
 p=a+d*((i+.5)/steps);B.cube((p.x,p.y,p.z-.13),(le/steps+.025,2.4,.3),STONE,ang)
for t in [.1,.4,.7,.95]:
 p=a+d*t;lantern(B,p.x,p.y+1.4,p.z,1.2,.25,True)
B.done()
# subtle glass panes in the boathouse's main lancet
B=Batch('Boathouse | patterned crown-glass lancet','Boathouse')
for row in range(9):
 for col in range(5):
  x=40-1.4+col*.56;z=13.15+row*.42
  B.poly([(x,-87.217,z),(x+.54,-87.217,z),(x+.54,-87.217,z+.405),(x,-87.217,z+.405)],STAIN[(row+col*3)%7])
B.done()
# catalog the shot list in the scene for easy navigation after opening.
shots=[('Cam_Hero','hero.png'),('Cam_Aerial','angle_aerial.png'),('Cam_Boathouse','angle_boathouse.png'),('Cam_Viaduct','angle_viaduct.png'),('Cam_Detail_01','detail_01.png'),('Cam_Detail_02','detail_02.png'),('Cam_Detail_03','detail_03.png')]
for i,(n,f) in enumerate(shots):
 marker=s.timeline_markers.new(n,frame=1+i*10);marker.camera=None
 bpy.data.objects[n]['Output file']=f
s['Project']='Hogwarts | The Black Lake at blue hour'
s['Creation']='Entirely procedural geometry and shaders. No imported assets or image textures.'
s['Reference use']='Four local JPG references studied visually; none loaded as scene textures.'
s['Render delivery']='Cycles / 3840 x 2160 / 1024 samples / denoised'
for o in list(COL['Greenhouses'].objects)+list(COL['Boathouse'].objects):
 if o.type=='MESH':fixnormals(o)
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/hogwarts.blend')
