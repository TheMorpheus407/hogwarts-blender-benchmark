
import bpy, bmesh, math, os
from mathutils import Vector
from mathutils.noise import noise
ROOT='/home/morpheus/Documents/Projects/Benchmarks/Blender/GPT-6-Astra'
# Radial density falloff removes the visible boundary of each ellipsoidal fog bank.
m=bpy.data.materials['Low fog banks | silver vapour']
nt=m.node_tree;l=nt.links
v=nt.nodes.get('Principled Volume');source=v.inputs['Density'].links[0].from_socket
tc=next(n for n in nt.nodes if n.bl_idname=='ShaderNodeTexCoord')
sub=nt.nodes.new('ShaderNodeVectorMath');sub.operation='SUBTRACT';sub.inputs[1].default_value=(.5,.5,.5);l.new(tc.outputs['Generated'],sub.inputs[0])
mul=nt.nodes.new('ShaderNodeVectorMath');mul.operation='SCALE';mul.inputs['Scale'].default_value=2;l.new(sub.outputs[0],mul.inputs[0])
length=nt.nodes.new('ShaderNodeVectorMath');length.operation='LENGTH';l.new(mul.outputs[0],length.inputs[0])
falloff=nt.nodes.new('ShaderNodeMapRange');falloff.interpolation_type='SMOOTHERSTEP';falloff.clamp=True
falloff.inputs['From Min'].default_value=.22;falloff.inputs['From Max'].default_value=.98;falloff.inputs['To Min'].default_value=1;falloff.inputs['To Max'].default_value=0
l.new(length.outputs['Value'],falloff.inputs['Value'])
den=nt.nodes.new('ShaderNodeMath');den.operation='MULTIPLY';l.new(source,den.inputs[0]);l.new(falloff.outputs['Result'],den.inputs[1]);l.new(den.outputs[0],v.inputs['Density'])
# Replace the long triangle fan with compact concentric quads before displacement.
o=bpy.data.objects['Eastern crag | eroded gneiss']
bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table()
N=160
outer=[bm.verts[32*N+i] for i in range(N)]
center=bm.verts[33*N]
bmesh.ops.delete(bm,geom=list(center.link_faces),context='FACES_ONLY')
bm.verts.remove(center)
previous=outer
for ring in range(1,25):
 r=1-ring/25
 current=[]
 for i,ov in enumerate(outer):
  x=153+(ov.co.x-153)*r;y=18+(ov.co.y-18)*r
  z=46+(ov.co.z-46)*r**4+noise(Vector((x*.14,y*.14,13)))*.32*(1-r)
  current.append(bm.verts.new((x,y,z)))
 for i in range(N):
  f=bm.faces.new((previous[i],previous[(i+1)%N],current[(i+1)%N],current[i]));f.material_index=1
 previous=current
cent=bm.verts.new((153,18,46))
for i in range(N):
 f=bm.faces.new((previous[i],previous[(i+1)%N],cent));f.material_index=1
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
# Camera refinement keeps the whole boathouse and the spire finial within the detail shots.
c=bpy.data.objects['Cam_Detail_02'];c.data.lens=32.5;c.rotation_euler=(Vector((42,-82,10.4))-c.location).to_track_quat('-Z','Y').to_euler()
bpy.data.objects['Cam_Detail_01'].data.lens=47
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/hogwarts.blend')
