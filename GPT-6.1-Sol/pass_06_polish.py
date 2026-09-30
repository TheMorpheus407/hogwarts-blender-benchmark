
# Unite the geological masses, then erode them at several real-world scales.
# Direct mesh copies avoid evaluated-dependency-graph conversion.
members=[o for o in C['Terrain'].objects if o.name=='Castle crag • fractured schist bedrock' or o.name.startswith('Crag • tilted fracture slab') or o.name.startswith('Crag • crown ledge')]
g=Geo()
for o in members:
    verts=[tuple(o.matrix_world @ v.co) for v in o.data.vertices]
    faces=[tuple(p.vertices) for p in o.data.polygons]
    if o.name=='Castle crag • fractured schist bedrock':faces.append(tuple(reversed(range(144))))
    g.add(verts,faces,'rock')
crag=g.create('Castle crag • unified eroded Highland schist','Terrain',True)
for o in members:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT');crag.select_set(True);bpy.context.view_layer.objects.active=crag
mod=crag.modifiers.new('Geological union • one metre voxels','REMESH');mod.mode='VOXEL';mod.voxel_size=.92;mod.adaptivity=.0;mod.use_smooth_shade=True
bpy.ops.object.modifier_apply(modifier=mod.name)
vg=crag.vertex_groups.new(name='Weathering • pinned beneath castle foundations')
for v in crag.data.vertices:
    zz=v.co.z
    weight=max(0,min(1,(63-zz)/8))
    vg.add([v.index],weight,'REPLACE')
for name,scale,strength,depth in [('Major fractured bedding',4.1,3.7,2),('Secondary rock erosion',1.45,1.55,3),('Fine weathered corners',.38,.33,2)]:
    tex=bpy.data.textures.new('Crag • '+name,type='CLOUDS');tex.noise_scale=scale;tex.noise_depth=depth
    m=crag.modifiers.new(name,'DISPLACE');m.texture=tex;m.texture_coords='GLOBAL';m.strength=strength;m.mid_level=.5;m.vertex_group=vg.name
for p in crag.data.polygons:p.use_smooth=True
# Geological foliation is broad, broken, and diagonally folded rather than close parallel bands.
nt=M['rock'].node_tree
wave=nt.nodes.get('Metamorphic schist foliation')
wave.inputs['Scale'].default_value=.52;wave.inputs['Distortion'].default_value=11;wave.inputs['Detail Scale'].default_value=3.1
# New cracks cross the strata and are much less regular.
for n in nt.nodes:
    if n.type=='TEX_VORONOI' and n.label=='Mineral fracture network':n.inputs['Scale'].default_value=1.10
# Roughen and vegetate the far landing rock.
ob=bpy.data.objects['East gate outcrop'];bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
rem=ob.modifiers.new('Landing rock • dense weathering surface','REMESH');rem.mode='VOXEL';rem.voxel_size=.9;rem.use_smooth_shade=True
# Close the lower boundary for remeshing.
import bmesh
bm=bmesh.new();bm.from_mesh(ob.data)
edges=[e for e in bm.edges if e.is_boundary]
if edges:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
bm.to_mesh(ob.data);bm.free()
bpy.ops.object.modifier_apply(modifier=rem.name)
vg2=ob.vertex_groups.new(name='Pinned bridge landing')
for v in ob.data.vertices:vg2.add([v.index],max(0,min(1,(52-v.co.z)/6)),'REPLACE')
tex=bpy.data.textures.new('Landing • eroded stone',type='CLOUDS');tex.noise_scale=2.4;tex.noise_depth=3
mod=ob.modifiers.new('Landing • natural rock erosion','DISPLACE');mod.texture=tex;mod.texture_coords='GLOBAL';mod.strength=2.5;mod.vertex_group=vg2.name
for p in ob.data.polygons:p.use_smooth=True
# The access ramp has continuous ground beneath it, merging the landing into the moor.
base_h=terrain_h
def terrain_h(x,y):
    p=Vector((180,-94));q=Vector((222,-37));d=q-p;pt=Vector((x,y));t=max(0,min(1,(pt-p).dot(d)/d.dot(d)));dist=(pt-(p+d*t)).length
    old=base_h(x,y);target=53+(base_h(q.x,q.y)-53)*t
    weight=math.exp(-(dist/24)**2)
    return old+max(0,target-old)*weight
ob=bpy.data.objects['Moorland • heather slopes and inlet']
for v in ob.data.vertices:
    x,y,z=v.co;v.co.z=terrain_h(x,y)
ob.data.update()
for o in C['Nature'].objects:
    if o.name.startswith('Forest •') and 130<o.location.x<255 and -135<o.location.y<20:o.location.z=terrain_h(o.location.x,o.location.y)-.12
# Procedural ground cover softens the eastern landing terrace.
v=[];f=[];n=90
for r,zz in [(0,53.15),(.78,53.08)]:
    if r==0:
        v.append((180,-94,zz));continue
    for i in range(n):
        a=i*math.tau/n;rr=1+.07*math.sin(a*5)+.04*math.cos(a*11)
        v.append((180+31*r*math.cos(a)*rr,-94+30*r*math.sin(a)*rr,zz+.20*math.sin(a*4)))
for i in range(n):f.append((0,i+1,(i+1)%n+1))
mesh('Viaduct landing • lichen and heather cap',v,f,'ground','Terrain')
# Reduce repeating streaks in the water: combine directional ripples with crossed capillary noise.
nt=M['water'].node_tree
for n in nt.nodes:
    if n.type=='TEX_WAVE':
        n.inputs['Distortion'].default_value=14;n.inputs['Scale'].default_value=.43;n.inputs['Detail Scale'].default_value=2.7
    if n.type=='BUMP':n.inputs['Strength'].default_value*=.77
# Softer cloud veils preserve the large-scale sky gradient.
nt=bpy.context.scene.world.node_tree
for n in nt.nodes:
    if n.type=='TEX_NOISE':
        n.inputs['Distortion'].default_value=.15;n.inputs['Detail'].default_value=7;n.inputs['Roughness'].default_value=.58
# Stone-supported landings complete the stair at its turns.
for k,p in enumerate(new_pts[1:-1]):
    x,y,z=p
    crag_block('Cliff stair • natural buttress at turn %d'%k,(x,y+3,z-7),(8,11,15),6500+k,.18)


# Shape the plateau into two architectural levels and expose the greenhouse terrace.
crag=bpy.data.objects['Castle crag • unified eroded Highland schist']
for v in crag.data.vertices:
    x,y,z=v.co
    if z>49:
        topweight=max(0,min(1,(z-49)/16))
        frontdrop=7*max(0,min(1,(-y-35)/22))
        greenhousedrop=14*math.exp(-((x-80)/24)**4-((y-54)/22)**4)
        v.co.z-=max(frontdrop,greenhousedrop)*topweight
crag.data.update()
# Lower lake-side terrace: limestone court, corbelled defensive wall, arched niches.
g=Geo()
g.box((-4,-46.4,61.9),(127,10.0,.7),'stone')
g.box((-4,-51.7,59.2),(127,1.8,6.0),'stone')
g.box((-4,-51.7,63.1),(128,1.4,1.9),'stone')
g.box((-4,-51.7,64.2),(128,1.95,.28),'trim')
for i in range(54):
    xx=-66.5+i*2.35
    g.box((xx,-51.7,64.78),(1.12,1.52,1.02),'stone')
    g.box((xx,-52.12,61.15),(.60,1.32,.82),'trim')
for xx in [-65,57]:
    g.box((xx,-46.4,63.1),(1.5,11.0,2.2),'stone')
g.create('Lower terrace • stepped lake fortifications')
for i in range(35):
    xx=-64+i*3.55
    window('Lower terrace • arched undercroft light',(xx,-52.76,58.75),1.15,2.70,0,2)
for i in range(8):
    xx=-60+i*16.4
    lantern('Lower terrace • courtyard lantern',xx,-49.6,62.3,.72,True)
# Connect the greenhouse walk and support the staircase tower above it.
cyl('East staircase tower • terrace foundation',71,44,55.8,4.72,5.25,'stone',n=48)
g=Geo()
for i in range(48):
    x=57.0+i*.255;z=65-(i+1)*9/48
    g.box((x,39.1,z-.10),(.28,3.3,.20),'trim')
g.create('Conservatory terrace • descending stone steps')
beam('Conservatory terrace • handrail',(57,37.7,66),(69.25,37.7,57),.09,'bronze')
# Genuine, metre-scale flags are used on horizontal stone surfaces.
M['paving']=mat('Stone • worn limestone flagstones',(.22,.20,.145),.82)
nt,p,out,geo=shader_reset(M['paving']);pos=geo.outputs['Position']
tc=node(nt,'ShaderNodeTexCoord');vec=tc.outputs['Object']
brick=node(nt,'ShaderNodeTexBrick','Uneven laid flagstones');nt.links.new(vec,brick.inputs['Vector'])
brick.inputs['Scale'].default_value=1;brick.inputs['Brick Width'].default_value=1.35;brick.inputs['Row Height'].default_value=.77
brick.inputs['Mortar Size'].default_value=.018;brick.inputs['Mortar Smooth'].default_value=.006
brick.inputs['Color1'].default_value=(.22,.207,.167,1);brick.inputs['Color2'].default_value=(.135,.149,.139,1);brick.inputs['Mortar'].default_value=(.035,.042,.036,1)
macro=noise_node(nt,pos,.35,5);var=ramp(nt,macro.outputs[0],[(.15,(.10,.109,.089)),(.78,(.32,.30,.205))])
col=mixc(nt,.28,brick.outputs['Color'],var.outputs[0]);nt.links.new(col,p.inputs['Base Color'])
p.inputs['Roughness'].default_value=.81
normal=bump_node(nt,brick.outputs['Fac'],.43,.038)
normal=bump_node(nt,noise_node(nt,pos,29,4).outputs[0],.52,.014,normal)
bv=node(nt,'ShaderNodeBevel','Worn flagstone corners');bv.inputs['Radius'].default_value=.030;bv.samples=3;nt.links.new(normal,bv.inputs['Normal']);nt.links.new(bv.outputs['Normal'],p.inputs['Normal'])
# Horizontal faces receive paving; walls retain their vertical sandstone courses.
for me in list(bpy.data.meshes):
    slots=[i for i,ma in enumerate(me.materials) if ma in [M['stone'],M['trim']]]
    if not slots:continue
    tops=[poly for poly in me.polygons if poly.material_index in slots and poly.normal.z>.72 and poly.area>.13]
    if not tops:continue
    me.materials.append(M['paving']);idx=len(me.materials)-1
    for poly in tops:poly.material_index=idx
road=bpy.data.objects['Grand viaduct • sloping stone carriageway'];road.data.materials.clear();road.data.materials.append(M['paving'])
# Shader bevels round visible masonry edges and preserve detailed erosion normal maps.
for ma in [M['stone'],M['trim']]:
    nt=ma.node_tree;p=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
    normal_link=p.inputs['Normal'].links[0].from_socket if p.inputs['Normal'].is_linked else None
    bv=node(nt,'ShaderNodeBevel','Weathered sandstone corners');bv.samples=3;bv.inputs['Radius'].default_value=.027
    if normal_link:nt.links.new(normal_link,bv.inputs['Normal'])
    nt.links.new(bv.outputs['Normal'],p.inputs['Normal'])
# Put the attendant turret crowns back on their moved towers.
for ob in bpy.data.objects:
    if ob.name.startswith('Attendant spire • stone crown') and ob.type=='MESH':
        c=sum((v.co for v in ob.data.vertices),Vector())/len(ob.data.vertices)
        if math.hypot(c.x+21,c.y-15)<2.4:
            for v in ob.data.vertices:v.co.x-=2;v.co.y-=17
        elif math.hypot(c.x+5,c.y-13)<2.4:
            for v in ob.data.vertices:v.co.x+=2;v.co.y-=14
# Conservatory foliage is lit warmly without overexposing the glass roof.
for ob in C['Lights'].objects:
    if ob.name.startswith('Greenhouse'):ob.data.energy=240
# Courtyard furnishings provide familiar human-scale cues.
g=Geo()
for x,y in [(-3,-23),(8,-23),(16,-20),(-7,-8)]:
    g.box((x,y,65.8),(3.0,.52,.16),'wood')
    for dx in [-1.08,1.08]:g.box((x+dx,y,65.4),(.22,.43,.76),'stone')
g.create('Upper courtyard • oak benches on stone legs')
# A stepped fountain at the centre of the quiet quad.
cyl('Upper courtyard • fountain pedestal',1,-13,65.75,2.3,.40,'trim',n=48)
ring('Upper courtyard • fountain basin',1,-13,66.1,2.15,.27,.61,'stone',n=64)
cyl('Upper courtyard • fountain column',1,-13,66.2,.38,2.2,'trim',n=16,r2=.27)
cyl('Upper courtyard • bronze fountain bowl',1,-13,68.15,1.0,.35,'bronze',n=32,r2=.5)
# Small garden rectangles soften the cloister edges without obscuring architecture.
for x,y in [(-7,-25),(9,-25),(8,-2)]:
    box('Upper courtyard • garden edging',(x,y,65.85),(5.5,2.6,.28),'trim',.04)
    box('Upper courtyard • moss garden',(x,y,66.02),(5.0,2.1,.14),'ground')
# Richer lantern amber remains readable at all camera distances.
p=M['lantern'].node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.28,.035,1);p.inputs['Emission Strength'].default_value=5.5;p.inputs['Base Color'].default_value=(.28,.085,.012,1)
# Introduce irregular chips into the surviving natural stair supports.
for ob in C['Terrain'].objects:
    if not ob.name.startswith('Cliff stair • natural buttress'):continue
    sub=ob.modifiers.new('Natural buttress facets','SUBSURF');sub.subdivision_type='SIMPLE';sub.levels=2;sub.render_levels=2
    tex=bpy.data.textures.get('Landing • eroded stone')
    mod=ob.modifiers.new('Fractured stair outcrop','DISPLACE');mod.texture=tex;mod.texture_coords='GLOBAL';mod.strength=.72
# Dedicated detail cameras examine geometry and procedural materials.
camera('Cam_Detail_Stone',(-68,-58,89),(-57,-27.8,86),58)
camera('Cam_Detail_Turret',(92,-36,134),(63,8,123),57)
camera('Cam_Detail_Boathouse',(48,-142,10),(13,-99,8.6),52)


# Sandstone close views now show pits, gritty inclusions and real recessed mortar joints.
for ma in [M['stone'],M['trim']]:
    nt=ma.node_tree;p=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
    geo=next(n for n in nt.nodes if n.type=='NEW_GEOMETRY');pos=geo.outputs['Position']
    old=p.inputs['Base Color'].links[0].from_socket
    mott=noise_node(nt,pos,8.5,5,.79)
    grit=ramp(nt,mott.outputs['Fac'],[(.23,(.47,.46,.42)),(.52,(.88,.90,.85)),(.78,(1.34,1.26,1.13))])
    mul=node(nt,'ShaderNodeMixRGB','Mineral grains and pitted weathering');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=.76;nt.links.new(old,mul.inputs[1]);nt.links.new(grit.outputs[0],mul.inputs[2]);nt.links.new(mul.outputs[0],p.inputs['Base Color'])
    bevel=nt.nodes.get('Weathered sandstone corners')
    oldnormal=bevel.inputs['Normal'].links[0].from_socket
    roughstone=noise_node(nt,pos,14.2,5,.82)
    b=bump_node(nt,roughstone.outputs['Fac'],.77,.026,oldnormal);nt.links.new(b,bevel.inputs['Normal'])
    for n in nt.nodes:
        if n.type=='BUMP' and n.inputs['Height'].is_linked and n.inputs['Height'].links[0].from_node.type=='TEX_BRICK':n.invert=True
# Assign physically varied room warmth in an inspectable, deterministic way.
nt=M['window'].node_tree;p=nt.nodes.get('Principled BSDF')
info=next(n for n in nt.nodes if n.type=='OBJECT_INFO')
for link in list(p.inputs['Emission Color'].links):nt.links.remove(link)
nt.links.new(info.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=2.6;p.inputs['Roughness'].default_value=.13
rr=random.Random(17128)
for ob in bpy.context.scene.objects:
    if not ob.get('architectural_element'):continue
    r=rr.random()
    if r<.32:color=(.0015,.004,.007,1)
    elif r<.42:color=(.046,.032,.016,1)
    else:
        strength=rr.uniform(.30,1.10);warm=rr.uniform(.25,.55)
        color=(strength,strength*warm,strength*rr.uniform(.035,.16),1)
    ob.color=color
    if ob.name.startswith('Great Hall') and 'clerestory' in ob.name and -64<ob.location.x<-47 and ob.location.y<-20:
        ob.color=(rr.uniform(.6,.9),rr.uniform(.25,.40),rr.uniform(.060,.10),1)
# Wavy old glass subtly distorts reflections.
geo=node(nt,'ShaderNodeNewGeometry');n=noise_node(nt,geo.outputs['Position'],3.2,3);nt.links.new(bump_node(nt,n.outputs[0],.38,.009),p.inputs['Normal'])
# Continuous diagonal lead cames replace the isolated diamond motifs.
for (w,h,style),me in list(window_templates.items()):
    if style<2 or not me.users:continue
    g=Geo();g.v=[tuple(v.co) for v in me.vertices];g.mats=list(me.materials)
    for poly in me.polygons:
        if me.materials[poly.material_index]==M['bronze']:continue
        g.f.append(tuple(poly.vertices));g.mi.append(poly.material_index)
    spring=h-w*.8660254
    for col in range(style):
        left=-w/2+.14+col*(w-.28)/style;right=-w/2+.14+(col+1)*(w-.28)/style
        width=right-left-.05;left+=.025;slope=1.28
        for sign in [-1,1]:
            for j in range(-3,int(spring/.52)+5):
                z0=.18+j*.52;lo=0;hi=width
                za,zb=.22,spring-.12
                if sign>0:lo=max(lo,(za-z0)/slope);hi=min(hi,(zb-z0)/slope)
                else:lo=max(lo,(z0-zb)/slope);hi=min(hi,(z0-za)/slope)
                if hi-lo>.015:
                    g.tube([(left+lo,.067,z0+sign*slope*lo),(left+hi,.067,z0+sign*slope*hi)],.0085,'bronze',4)
    used=sorted({i for face in g.f for i in face});mapping={idx:new for new,idx in enumerate(used)}
    verts=[g.v[i] for i in used];faces=[tuple(mapping[i] for i in face) for face in g.f]
    me.clear_geometry();me.from_pydata(verts,[],faces);me.materials.clear()
    for ma in g.mats:me.materials.append(ma)
    for poly,idx in zip(me.polygons,g.mi):poly.material_index=idx
    me.update()
# Close composition includes the complete Gothic arch rather than cropping its tracery.
cam=bpy.data.objects['Cam_Detail_Stone'];cam.location=(-72,-73,90);cam.data.lens=55
cam.rotation_euler=(Vector((-55,-27.8,85.5))-cam.location).to_track_quat('-Z','Y').to_euler()


# Room lighting has gentle spatial falloff and blurred interior variation.
nt=M['window'].node_tree;p=nt.nodes.get('Principled BSDF')
info=next(n for n in nt.nodes if n.type=='OBJECT_INFO')
tc=node(nt,'ShaderNodeTexCoord');gen=tc.outputs['Generated']
n=noise_node(nt,vector_scale(nt,gen,(2.7,.7,1.5)),2.2,3,.56)
fac=ramp(nt,n.outputs['Fac'],[(.20,(.20,.20,.20)),(.50,(.64,.64,.64)),(.79,(1,1,1))])
sep=node(nt,'ShaderNodeSeparateXYZ');nt.links.new(gen,sep.inputs[0])
height=node(nt,'ShaderNodeMapRange');nt.links.new(sep.outputs['Z'],height.inputs['Value']);height.inputs['To Min'].default_value=1.1;height.inputs['To Max'].default_value=.58
mul=node(nt,'ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1
nt.links.new(info.outputs['Color'],mul.inputs[1]);nt.links.new(fac.outputs[0],mul.inputs[2])
mul2=node(nt,'ShaderNodeMixRGB');mul2.blend_type='MULTIPLY';mul2.inputs[0].default_value=1;nt.links.new(mul.outputs[0],mul2.inputs[1]);nt.links.new(height.outputs[0],mul2.inputs[2]);nt.links.new(mul2.outputs[0],p.inputs['Emission Color'])
# The main mullions stop at the springing of their lancets, leaving the trefoil head clear.
for (w,h,style),me in window_templates.items():
    if style<2 or not me.users:continue
    oldtop=h-w*.34;newtop=h-w*.8660254+.03*(w-.22)/style
    for v in me.vertices:
        if abs(v.co.z-oldtop)<.0001 and -.116<v.co.y<.076:
            for k in range(1,style):
                xx=-w/2+w*k/style
                if abs(abs(v.co.x-xx)-.045)<.0001:v.co.z=newtop
    me.update()
# Vary the four Hall turrets and the smaller paired towers.
for ob in bpy.data.objects:
    if ob.type!='MESH':continue
    if ob.name.startswith('Great Hall • corner turret'):
        c=sum((v.co for v in ob.data.vertices),Vector())/len(ob.data.vertices)
        cx=-83 if c.x<-50 else -17;cy=-28 if c.y<-15 else -2
        index=(0 if cx==-83 else 2)+(0 if cy==-28 else 1)
        sr,sh,sroof=[(1.0,1.0,1.0),(.88,1.04,1.10),(1.07,.94,.88),(.94,1.12,1.03)][index]
        for v in ob.data.vertices:
            v.co.x=cx+(v.co.x-cx)*sr;v.co.y=cy+(v.co.y-cy)*sr
            v.co.z=88+(v.co.z-88)*sh if v.co.z<=108 else 88+20*sh+(v.co.z-108)*sroof
    elif ob.name.startswith('Gatehouse • flanking needle'):
        c=sum((v.co for v in ob.data.vertices),Vector())/len(ob.data.vertices)
        if c.x<55:
            for v in ob.data.vertices:
                v.co.x=c.x+(v.co.x-c.x)*.88;v.co.y=c.y+(v.co.y-c.y)*.88
                v.co.z=65+(v.co.z-65)*1.05 if v.co.z<=80 else 80.75+(v.co.z-80)*1.20
    elif ob.name.startswith('Boathouse • gable turret'):
        c=sum((v.co for v in ob.data.vertices),Vector())/len(ob.data.vertices)
        if c.x>14:
            for v in ob.data.vertices:
                v.co.x=c.x+(v.co.x-c.x)*.86;v.co.y=c.y+(v.co.y-c.y)*.86
                v.co.z=8+(v.co.z-8)*1.12 if v.co.z<=14.5 else 15.28+(v.co.z-14.5)*.88
            if 'spire' in ob.name:
                ob.data.materials.clear();ob.data.materials.append(M['roof'])
# Let the grass cover the entire irregular bridge landing rather than isolated triangular patches.
rock=bpy.data.objects['East gate outcrop']
for v in rock.data.vertices:
    if v.co.z>52.9:v.co.z=52.9
rock.data.update()
# An old moon's dark maria and bright cratered highlands are generated from scratch.
nt=M['moon'].node_tree;p=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');geo=next(n for n in nt.nodes if n.type=='NEW_GEOMETRY')
old=p.inputs['Emission Color'].links[0].from_socket
n=noise_node(nt,geo.outputs['Position'],.071,4,.61)
maria=ramp(nt,n.outputs['Fac'],[(.28,(.38,.45,.55)),(.52,(.76,.82,.90)),(.70,(1,1,1))])
mul=node(nt,'ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=.74;nt.links.new(old,mul.inputs[1]);nt.links.new(maria.outputs[0],mul.inputs[2]);nt.links.new(mul.outputs[0],p.inputs['Emission Color']);nt.links.new(mul.outputs[0],p.inputs['Base Color']);p.inputs['Emission Strength'].default_value=1.7
# A small gamekeeper's cottage adds a human-scale warm point at the forest edge.
hx,hy=-159,89;hz=terrain_h(hx,hy)+.55
for o in list(C['Nature'].objects):
    if o.name.startswith('Forest •') and math.hypot(o.location.x-hx,o.location.y-hy)<10:bpy.data.objects.remove(o,do_unlink=True)
box('Gamekeeper • rubble foundation',(hx,hy,hz-.7),(8.8,7.0,1.5),'stone',.11)
box('Gamekeeper • cottage',(hx,hy,hz+1.7),(7.8,6.1,3.4),'stone',.10)
gable('Gamekeeper • high slate roof',hx,hy,hz+3.4,8.9,7.1,3.3)
slate_gable('Gamekeeper cottage',hx,hy,hz+3.4,8.9,7.1,3.3)
for x in [hx-2.2,hx+2.2]:window('Gamekeeper • front candle window',(x,hy-3.39,hz+.8),1.05,1.8,0,2).color=(.83,.31,.05,1)
door=box('Gamekeeper • oak door',(hx,hy-3.10,hz+1.03),(1.30,.18,2.06),'wood',.035)
cyl('Gamekeeper • stone chimney',hx+2.4,hy+1,hz+3.2,.63,4.6,'stone',n=8)
cyl('Gamekeeper • chimney pot',hx+2.4,hy+1,hz+7.8,.34,.60,'bronze',n=16)
lantern('Gamekeeper • porch lamp',hx+.92,hy-3.48,hz,.68,True)
smoke=bpy.data.materials.new('Gamekeeper • soft chimney smoke');smoke.use_nodes=True;nt=smoke.node_tree;nt.nodes.clear()
out=node(nt,'ShaderNodeOutputMaterial');vol=node(nt,'ShaderNodeVolumePrincipled');vol.inputs['Color'].default_value=(.35,.42,.47,1);vol.inputs['Anisotropy'].default_value=.15
tc=node(nt,'ShaderNodeTexCoord');gn=tc.outputs['Generated'];noiseN=noise_node(nt,gn,4.1,3)
sep=node(nt,'ShaderNodeSeparateXYZ');nt.links.new(gn,sep.inputs[0]);fade=mathn(nt,'SUBTRACT',1,sep.outputs['Z']);den=mathn(nt,'MULTIPLY',fade.outputs[0],noiseN.outputs['Fac']);den=mathn(nt,'MULTIPLY',den.outputs[0],.18);nt.links.new(den.outputs[0],vol.inputs['Density']);nt.links.new(vol.outputs[0],out.inputs['Volume'])
for i in range(6):
    # Small overlapping vapour wisps, leaning with the wind.
    box('Gamekeeper • drifting smoke %d'%i,(hx+2.4+i*.48,hy+1+i*.22,hz+8.7+i*.83),(1.25+i*.24,1.0+i*.22,1.7),smoke,group='FX')
# Slight optical halation around the moon, lanterns and inhabited windows.
scene=bpy.context.scene;nt=scene.compositing_node_group;nt.nodes.clear()
if not nt.interface.items_tree:nt.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
rl=nt.nodes.new('CompositorNodeRLayers');rl.location=(-350,0)
gl=nt.nodes.new('CompositorNodeGlare');gl.inputs['Type'].default_value='Fog Glow';gl.inputs['Quality'].default_value='High';gl.inputs['Threshold'].default_value=1.2;gl.inputs['Smoothness'].default_value=.28;gl.inputs['Strength'].default_value=.085;gl.inputs['Size'].default_value=.23;gl.location=(-100,0)
out=nt.nodes.new('NodeGroupOutput');out.location=(180,0)
nt.links.new(rl.outputs['Image'],gl.inputs['Image']);nt.links.new(gl.outputs['Image'],out.inputs['Image'])
# All close views retain architectural edges and complete arches.
cam=bpy.data.objects['Cam_Detail_Stone'];cam.location=(-44,-83,91);cam.data.lens=61
cam.rotation_euler=(Vector((-55,-27.8,85.7))-cam.location).to_track_quat('-Z','Y').to_euler()


# Rebuild the stair on its final cliff contour with rigid, upright lamps and level treads.
for ob in list(bpy.data.objects):
    if ob.name.startswith('Boathouse stair •') or ob.name.startswith('Cliff stair • lantern'):
        bpy.data.objects.remove(ob,do_unlink=True)
stair=Geo();coping=Geo()
for k,(p,q) in enumerate(zip(new_pts[:-1],new_pts[1:])):
    p,q=Vector(p),Vector(q);vec=q-p;horizontal=math.hypot(vec.x,vec.y);ux,uy=vec.x/horizontal,vec.y/horizontal
    nx,ny=-uy,ux;width=3.25;steps=max(8,int((q.z-p.z)/.19));rise=(q.z-p.z)/steps;run=horizontal/steps
    for j in range(steps):
        t=(j+.5)/steps;cx=p.x+vec.x*t;cy=p.y+vec.y*t;zz=p.z+rise*(j+1);half=run*.52
        corners=[(cx-ux*half-nx*width/2,cy-uy*half-ny*width/2,zz-.30),(cx+ux*half-nx*width/2,cy+uy*half-ny*width/2,zz-.30),(cx+ux*half+nx*width/2,cy+uy*half+ny*width/2,zz-.30),(cx-ux*half+nx*width/2,cy-uy*half+ny*width/2,zz-.30)]
        v=corners+[(x,y,zz) for x,y,_ in corners]
        stair.add(v,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'trim')
        stair.add(v,[(4,5,6,7)],'paving')
    v=[(p.x-nx*width/2,p.y-ny*width/2,p.z-5),(p.x+nx*width/2,p.y+ny*width/2,p.z-5),(q.x+nx*width/2,q.y+ny*width/2,q.z-5),(q.x-nx*width/2,q.y-ny*width/2,q.z-5),
       (p.x-nx*width/2,p.y-ny*width/2,p.z),(p.x+nx*width/2,p.y+ny*width/2,p.z),(q.x+nx*width/2,q.y+ny*width/2,q.z),(q.x-nx*width/2,q.y-ny*width/2,q.z)]
    stair.add(v,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],'stone')
    for side in [-1,1]:
        pp=p+Vector((nx*side*(width/2+.12),ny*side*(width/2+.12),0));qq=q+Vector((nx*side*(width/2+.12),ny*side*(width/2+.12),0))
        vv=[]
        for endpoint in [pp,qq]:vv += [tuple(endpoint+Vector((nx*s*.30,ny*s*.30,z))) for z in [0,1.05] for s in [-1,1]]
        stair.add(vv,[(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5),(0,2,3,1),(4,5,7,6)],'stone')
        coping.tube([pp+Vector((0,0,1.1)),qq+Vector((0,0,1.1))],.14,'trim',8)
    for t in [0,.33,.67]:
        pos=p+vec*t+Vector((nx*(width/2+.12),ny*(width/2+.12),1.08))
        lantern('Cliff stair • lantern %d %.2f'%(k,t),*pos,.72,k%2==0)
    if k<4:stair.box(tuple(q-Vector((0,0,.20))),(5.5,5.3,.4),'paving')
stair.create('Boathouse stair • level treads and anchored switchbacks')
coping.create('Boathouse stair • carved limestone coping')
# Exposed roots and loose chips at the waterline have procedural bark as well.
nt,p,out,geo=shader_reset(M['bark']);pos=geo.outputs['Position'];p.inputs['Roughness'].default_value=.94
n=noise_node(nt,vector_scale(nt,pos,(4.0,4.0,.20)),3.2,4)
col=ramp(nt,n.outputs[0],[(.25,(.035,.022,.015)),(.72,(.145,.074,.037))]);nt.links.new(col.outputs[0],p.inputs['Base Color']);nt.links.new(bump_node(nt,n.outputs[0],.5,.034),p.inputs['Normal'])
# Group the campus by architectural function while retaining the six main scene collections.
subnames=['Great Hall','Towers','Clock Tower','Viaduct and Gate','Boathouse and Stair','Greenhouses','Courts and Wings']
subs={}
for name in subnames:
    c=bpy.data.collections.new(name);C['Castle'].children.link(c);subs[name]=c
for ob in list(C['Castle'].objects):
    name=ob.name
    if name.startswith('Great Hall'):key='Great Hall'
    elif name.startswith('Clock') or 'clock' in name:key='Clock Tower'
    elif name.startswith('Grand viaduct') or name.startswith('Gatehouse'):key='Viaduct and Gate'
    elif name.startswith('Boathouse') or name.startswith('Cliff stair') or name.startswith('Black Lake • moored') or name=='Black Lake • launch boat':key='Boathouse and Stair'
    elif name.startswith('Greenhouse') or name.startswith('Conservatory'):key='Greenhouses'
    elif any(n in name for n in ['Tower','tower','turret','sentinel','needle','Attendant']):key='Towers'
    else:key='Courts and Wings'
    subs[key].objects.link(ob);C['Castle'].objects.unlink(ob)
# A compact record stays embedded in the .blend and records the required render contract.
scene=bpy.context.scene
scene['Build brief']='SPEC.md • Hogwarts — Full Environment Build'
scene['Reference files']='Hogwarts.jpg; Hogwarts2.jpg; Hogwarts3.jpg; Hogwarts4.jpg • visual study only'
scene['Mood']='Moonlit Highland blue hour, warm candlelight and drifting lake mist'
scene['Provenance']='All meshes and shader nodes constructed procedurally through the connected blender-official MCP. No imported assets or image textures.'
scene['Final render contract']='Cycles • 3840 × 2160 • 100% • 1024 samples • denoised'
bpy.data.orphans_purge(do_recursive=True)


# The clock dial sits fully in front of its stone gable.
for ob in bpy.data.objects:
    if ob.name.startswith('South clock'):ob.location.y-=.42
# Mist and smoke disappear smoothly at their volume boundaries.
for ma in [fog,smoke]:
    nt=ma.node_tree;vol=next(n for n in nt.nodes if n.type=='PRINCIPLED_VOLUME')
    old=vol.inputs['Density'].links[0].from_socket
    tc=next(n for n in nt.nodes if n.type=='TEX_COORD')
    sep=node(nt,'ShaderNodeSeparateXYZ');nt.links.new(tc.outputs['Generated'],sep.inputs[0])
    masks=[]
    for channel in ['X','Y']:
        complement=mathn(nt,'SUBTRACT',1,sep.outputs[channel])
        fac=mathn(nt,'MULTIPLY',sep.outputs[channel],complement.outputs[0]);fac=mathn(nt,'MULTIPLY',fac.outputs[0],4)
        masks.append(fac.outputs[0])
    fac=mathn(nt,'MULTIPLY',*masks);fac=mathn(nt,'SQRT',fac.outputs[0]);den=mathn(nt,'MULTIPLY',old,fac.outputs[0]);nt.links.new(den.outputs[0],vol.inputs['Density'])
# Freeze the chosen cliff-weathering values into the procedural source record.
for m in bpy.data.objects['Castle crag • unified eroded Highland schist'].modifiers:
    if m.name=='Major fractured bedding':m.strength=2.25
    if m.name=='Secondary rock erosion':m.strength=.86
# Focus the roof detail on the stonework, slate courses and clock.
cam=bpy.data.objects['Cam_Detail_Turret'];cam.data.dof.use_dof=True;cam.data.dof.focus_distance=(cam.location-Vector((63,8,123))).length;cam.data.dof.aperture_fstop=1.2
# Scene audit: all visible meshes are assigned procedural materials, with valid coordinates.
bad=[]
for o in bpy.context.scene.objects:
    if o.type=='MESH' and not o.data.materials:bad.append(o.name)
    if any(not math.isfinite(c) for c in o.location):bad.append(o.name+' nonfinite position')
if bad:raise RuntimeError('Scene audit failed: '+str(bad))
scene=bpy.context.scene;scene.camera=bpy.data.objects['Cam_Hero']
scene.render.image_settings.color_depth='16';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.compression=25
scene.cycles.use_denoising=True;scene.cycles.denoiser='OPTIX'


# The north aisle has genuinely curved flying arches, with carved stone coping.
for ob in list(bpy.data.objects):
    if ob.name.startswith('Great Hall • flying buttress') and ('coping' in ob.name or ob.name=='Great Hall • flying buttress' or ob.name.rsplit('.',1)[0]=='Great Hall • flying buttress'):
        bpy.data.objects.remove(ob,do_unlink=True)
for i in range(8):
    xx=-79+i*8.3
    upper=[(-1+8*t/20,91-9*t/20-1.9*math.sin(math.pi*t/20)) for t in range(21)]
    lower=[(y,z-.72) for y,z in reversed(upper)]
    g=Geo();g.poly(upper+lower,-.34,.34,'stone')
    strip=[(y,z+.13) for y,z in upper]+[(y,z+.37) for y,z in reversed(upper)]
    g.poly(strip,-.43,.43,'trim')
    o=g.create('Great Hall • arched flying buttress %02d'%i);o.location=(xx,0,0);o.rotation_euler.z=math.pi/2
    sub=bpy.data.collections['Great Hall'];sub.objects.link(o);C['Castle'].objects.unlink(o)
# A softer light separates the roof stonework from the distant forest in the detail view.
bpy.data.objects['Cam_Detail_Boathouse'].data.dof.use_dof=True
cam=bpy.data.objects['Cam_Detail_Boathouse'];cam.data.dof.focus_distance=(cam.location-Vector((13,-99,8.6))).length;cam.data.dof.aperture_fstop=4.0


# Carve the boathouse's occupied volume out of the cliff so rock cannot intrude into its launch bays.
crag=bpy.data.objects['Castle crag • unified eroded Highland schist']
cutter=box('Geology • boathouse rock excavation',(14,-98.5,11.0),(29,23,27),'dark',group='Terrain')
cutter.hide_render=True;cutter.display_type='WIRE';cutter.hide_set(True)
mod=crag.modifiers.new('Boathouse • excavated rock chamber','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
for ob in list(C['Terrain'].objects):
    if ob.name.startswith('Shore • broken schist boulder') and -.5<ob.location.x<28.5 and -111<ob.location.y<-86:
        bpy.data.objects.remove(ob,do_unlink=True)
# Dock steps match the difference in level between the wooden jetty and stone apron.
g=Geo()
for i in range(5):
    zz=.83+.87*(i+1)/5
    g.box((14,-110.4+i*.35,zz-.10),(3.4,.38,.20),'wood')
o=g.create('Boathouse • five dock access steps')
sub=bpy.data.collections['Boathouse and Stair'];sub.objects.link(o);C['Castle'].objects.unlink(o)
for xx in [12.7,15.3]:
    o=beam('Boathouse • dock stair oak stringer',(xx,-110.7,.67),(xx,-108.8,1.60),.15,'wood')
    sub.objects.link(o);C['Castle'].objects.unlink(o)


# Final forest quality pass: each tree is a branch skeleton with thousands of needle tufts.
# There are no solid cone skirts or image cutouts.
def foliage_tuft(g,centre,axis,length,radius,ma,rnd):
    axis=Vector(axis).normalized()
    u=axis.cross(Vector((0,0,1)))
    if u.length<.01:u=axis.cross(Vector((0,1,0)))
    u.normalize();v=axis.cross(u).normalized();centre=Vector(centre);nn=7;verts=[]
    for ri,(dist,rr) in enumerate([(-length*.5,radius*.20),(0,radius),(length*.5,radius*.06)]):
        for j in range(nn):
            a=j*math.tau/nn
            r=rr*rnd.uniform(.82,1.17)
            verts.append(tuple(centre+axis*dist+u*(r*math.cos(a))+v*(r*.62*math.sin(a))))
    faces=[tuple(reversed(range(nn))),tuple(range(2*nn,3*nn))]
    for ri in range(2):
        for j in range(nn):faces.append((ri*nn+j,ri*nn+(j+1)%nn,(ri+1)*nn+(j+1)%nn,(ri+1)*nn+j))
    g.add(verts,faces,ma)
    # Real geometric needles feather the outline of each tuft.
    for i in range(4):
        a=rnd.random()*math.tau;perp=u*math.cos(a)+v*math.sin(a);p=centre+axis*rnd.uniform(-length*.35,length*.35)+perp*radius*.63
        direction=(perp*.8+axis*.6).normalized();side=direction.cross(axis).normalized()
        tip=p+direction*rnd.uniform(.065,.13)
        g.add([tuple(p-side*.006),tuple(tip),tuple(p+side*.006)],[(0,1,2)],ma)
for variant in range(10):
    me=bpy.data.meshes.get('Conifer • prototype %02d · mesh'%variant)
    if not me:continue
    rnd=random.Random(33410+variant);height=tree_meshes[variant][1]
    g=Geo();trunklean=Vector((rnd.uniform(-.30,.30),rnd.uniform(-.22,.22),0))
    # A tapered trunk with slightly irregular bark rings.
    nn=10;v=[]
    for j in range(10):
        t=j/9;centre=trunklean*t;rad=height*.021*(1-t*.95)
        for i in range(nn):
            a=i*math.tau/nn;r=rad*rnd.uniform(.87,1.1)
            v.append((centre.x+r*math.cos(a),centre.y+r*math.sin(a),height*t))
    f=[tuple(reversed(range(nn))),tuple(range(9*nn,10*nn))]
    for j in range(9):
        for i in range(nn):f.append((j*nn+i,j*nn+(i+1)%nn,(j+1)*nn+(i+1)%nn,(j+1)*nn+i))
    g.add(v,f,'bark')
    levels=17
    for lev in range(levels):
        t=.14+lev*.048;z=height*t+rnd.uniform(-.16,.16);rad=height*.237*(1-t)**.89
        arms=5+(lev+variant)%3
        for arm in range(arms):
            a=arm*math.tau/arms+lev*1.31+rnd.uniform(-.20,.20)
            direction=Vector((math.cos(a),math.sin(a),0))
            perp=Vector((-math.sin(a),math.cos(a),0))
            root=Vector((trunklean.x*t,trunklean.y*t,z))
            reach=rad*rnd.uniform(.80,1.15)
            bend=root+direction*(reach*.48)+Vector((0,0,-height*.014))
            tip=root+direction*reach+Vector((0,0,-height*rnd.uniform(.010,.027)))
            g.tube([root,bend,tip],max(.009,height*.004*(1-t)),'bark',5)
            for j in range(6):
                ft=.14+j*.135;origin=root.lerp(tip,ft)
                for side in [-1,1]:
                    twiglen=reach*(.43*(1-ft)+.095)*rnd.uniform(.8,1.18)
                    twigdir=(direction*.54+perp*.84*side+Vector((0,0,rnd.uniform(-.14,.20)))).normalized()
                    endpoint=origin+twigdir*twiglen
                    g.tube([origin,endpoint],.008,'bark',4)
                    centre=origin+twigdir*(twiglen*.60)
                    leaflen=twiglen*1.10+.09;radius=max(.055,height*.012*(1-ft*.40)*(1-t*.23))
                    foliage_tuft(g,centre,twigdir,leaflen,radius,needle_mats[rnd.randrange(5)],rnd)
            foliage_tuft(g,tip-direction*.08,direction,.32,max(.055,height*.01*(1-t*.5)),needle_mats[(lev+arm+variant)%5],rnd)
    foliage_tuft(g,trunklean+Vector((0,0,height*.98)),Vector((0,0,1)),height*.11,.10,needle_mats[2],rnd)
    me.clear_geometry();me.from_pydata(g.v,[],g.f);me.materials.clear()
    for ma in g.mats:me.materials.append(ma)
    for poly,idx in zip(me.polygons,g.mi):poly.material_index=idx;poly.use_smooth=True
    me.update()
# Store the final instance count and procedural mesh detail in the scene.
bpy.context.scene['Forest design']='Ten unique conifer meshes with tapered trunks, irregular branches, opaque needle tufts and individual geometric needles; over twelve thousand varied instances.'

# Final forest quality pass: each tree is a branch skeleton with thousands of needle tufts.
# There are no solid cone skirts or image cutouts.
def foliage_tuft(g,centre,axis,length,radius,ma,rnd):
    axis=Vector(axis).normalized()
    u=axis.cross(Vector((0,0,1)))
    if u.length<.01:u=axis.cross(Vector((0,1,0)))
    u.normalize();v=axis.cross(u).normalized();centre=Vector(centre);nn=7;verts=[]
    for ri,(dist,rr) in enumerate([(-length*.5,radius*.20),(0,radius),(length*.5,radius*.06)]):
        for j in range(nn):
            a=j*math.tau/nn
            r=rr*rnd.uniform(.82,1.17)
            verts.append(tuple(centre+axis*dist+u*(r*math.cos(a))+v*(r*.80*math.sin(a))))
    faces=[tuple(reversed(range(nn))),tuple(range(2*nn,3*nn))]
    for ri in range(2):
        for j in range(nn):faces.append((ri*nn+j,ri*nn+(j+1)%nn,(ri+1)*nn+(j+1)%nn,(ri+1)*nn+j))
    g.add(verts,faces,ma)
    # Real geometric needles feather the outline of each tuft.
    for i in range(4):
        a=rnd.random()*math.tau;perp=u*math.cos(a)+v*math.sin(a);p=centre+axis*rnd.uniform(-length*.35,length*.35)+perp*radius*.63
        direction=(perp*.8+axis*.6).normalized();side=direction.cross(axis).normalized()
        tip=p+direction*rnd.uniform(.065,.13)
        g.add([tuple(p-side*.006),tuple(tip),tuple(p+side*.006)],[(0,1,2)],ma)
for variant in range(10):
    me=bpy.data.meshes.get('Conifer • prototype %02d · mesh'%variant)
    if not me:continue
    rnd=random.Random(33410+variant);height=tree_meshes[variant][1]
    g=Geo();trunklean=Vector((rnd.uniform(-.30,.30),rnd.uniform(-.22,.22),0))
    # A tapered trunk with slightly irregular bark rings.
    nn=10;v=[]
    for j in range(10):
        t=j/9;centre=trunklean*t;rad=height*.021*(1-t*.95)
        for i in range(nn):
            a=i*math.tau/nn;r=rad*rnd.uniform(.87,1.1)
            v.append((centre.x+r*math.cos(a),centre.y+r*math.sin(a),height*t))
    f=[tuple(reversed(range(nn))),tuple(range(9*nn,10*nn))]
    for j in range(9):
        for i in range(nn):f.append((j*nn+i,j*nn+(i+1)%nn,(j+1)*nn+(i+1)%nn,(j+1)*nn+i))
    g.add(v,f,'bark')
    levels=17
    for lev in range(levels):
        t=.14+lev*.048;z=height*t+rnd.uniform(-.16,.16);rad=height*.237*(1-t)**.89
        arms=5+(lev+variant)%3
        for arm in range(arms):
            a=arm*math.tau/arms+lev*1.31+rnd.uniform(-.20,.20)
            direction=Vector((math.cos(a),math.sin(a),0))
            perp=Vector((-math.sin(a),math.cos(a),0))
            root=Vector((trunklean.x*t,trunklean.y*t,z))
            reach=rad*rnd.uniform(.80,1.15)
            bend=root+direction*(reach*.48)+Vector((0,0,-height*.014))
            tip=root+direction*reach+Vector((0,0,-height*rnd.uniform(.010,.027)))
            g.tube([root,bend,tip],max(.009,height*.004*(1-t)),'bark',5)
            for j in range(6):
                ft=.14+j*.135;origin=root.lerp(tip,ft)
                for side in [-1,1]:
                    twiglen=reach*(.43*(1-ft)+.095)*rnd.uniform(.8,1.18)
                    twigdir=(direction*.54+perp*.84*side+Vector((0,0,rnd.uniform(-.14,.20)))).normalized()
                    endpoint=origin+twigdir*twiglen
                    g.tube([origin,endpoint],.008,'bark',4)
                    centre=origin+twigdir*(twiglen*.60)
                    leaflen=twiglen*1.10+.09;radius=max(.055,height*.018*(1-ft*.40)*(1-t*.23))
                    foliage_tuft(g,centre,twigdir,leaflen,radius,needle_mats[rnd.randrange(5)],rnd)
            foliage_tuft(g,tip-direction*.08,direction,.32,max(.08,height*.015*(1-t*.5)),needle_mats[(lev+arm+variant)%5],rnd)
    foliage_tuft(g,trunklean+Vector((0,0,height*.98)),Vector((0,0,1)),height*.11,.10,needle_mats[2],rnd)
    me.clear_geometry();me.from_pydata(g.v,[],g.f);me.materials.clear()
    for ma in g.mats:me.materials.append(ma)
    for poly,idx in zip(me.polygons,g.mi):poly.material_index=idx;poly.use_smooth=True
    me.update()
# Store the final instance count and procedural mesh detail in the scene.
bpy.context.scene['Forest design']='Ten unique conifer meshes with tapered trunks, irregular branches, opaque needle tufts and individual geometric needles; over twelve thousand varied instances.'



import ast, re
# Close-up refinement: aged gilding, enamel dial and leaded dormer glass.
nt,p,out,geo=shader_reset(M['gold']);pos=geo.outputs['Position']
wear=noise_node(nt,pos,8.5,5,.67)
col=ramp(nt,wear.outputs['Fac'],[(.20,(.16,.067,.015)),(.44,(.48,.26,.050)),(.68,(.74,.46,.095)),(.86,(.84,.57,.16))])
nt.links.new(col.outputs[0],p.inputs['Base Color']);nt.links.new(col.outputs[0],p.inputs['Emission Color'])
p.inputs['Emission Strength'].default_value=.28;p.inputs['Metallic'].default_value=.87
rough=node(nt,'ShaderNodeMapRange','Uneven polished gilding');nt.links.new(wear.outputs['Fac'],rough.inputs['Value'])
rough.inputs['To Min'].default_value=.48;rough.inputs['To Max'].default_value=.22;nt.links.new(rough.outputs[0],p.inputs['Roughness'])
grain=noise_node(nt,vector_scale(nt,pos,(1.0,.5,3.2)),210,2,.6)
normal=bump_node(nt,grain.outputs['Fac'],.24,.00065)
bevel=node(nt,'ShaderNodeBevel','Worn raised edges');bevel.inputs['Radius'].default_value=.009;bevel.samples=4
nt.links.new(normal,bevel.inputs['Normal']);nt.links.new(bevel.outputs['Normal'],p.inputs['Normal'])
M['clock_enamel']=mat('Clock • weathered blue-black enamel',(.008,.012,.019),.38,.24)
nt,p,out,geo=shader_reset(M['clock_enamel']);pos=geo.outputs['Position']
w=noise_node(nt,pos,2.2,4,.62)
c=ramp(nt,w.outputs['Fac'],[(.15,(.004,.007,.011)),(.55,(.008,.013,.021)),(.86,(.016,.020,.024))])
nt.links.new(c.outputs[0],p.inputs['Base Color']);p.inputs['Roughness'].default_value=.40;p.inputs['Metallic'].default_value=.25;p.inputs['Coat Weight'].default_value=.17
nt.links.new(bump_node(nt,noise_node(nt,pos,175,2).outputs['Fac'],.2,.00022),p.inputs['Normal'])
for ob in bpy.context.scene.objects:
    if 'clock mechanism' in ob.name and ob.type=='MESH':
        for i,ma in enumerate(ob.data.materials):
            if ma==M['dark']:ob.data.materials[i]=M['clock_enamel']
lead_templates=0
for me in list(bpy.data.meshes):
    if not me.users or 'Window • prototype (' not in me.name:continue
    match=re.search(r'prototype (\([^\)]+\))',me.name)
    if not match:continue
    w,h,style=ast.literal_eval(match.group(1))
    if style!=1 or me.get('leaded_dormer_refined'):continue
    g=Geo();g.v=[tuple(v.co) for v in me.vertices];g.mats=list(me.materials)
    for poly in me.polygons:g.f.append(tuple(poly.vertices));g.mi.append(poly.material_index)
    poly=[(x,z+.035) for x,z in gothic(w-.29,h-.225,20)]
    slope=1.5;spacing=.29 if w<1.2 else .38
    for sign in [-1,1]:
        for j in range(-int(w/spacing)-3,int(h/spacing)+int(w/spacing)+4):
            intercept=j*spacing;cross=[]
            for k,(x1,z1) in enumerate(poly):
                x2,z2=poly[(k+1)%len(poly)];den=(z2-z1)-sign*slope*(x2-x1)
                if abs(den)<1e-10:continue
                t=(sign*slope*x1+intercept-z1)/den
                if -.000001<=t<=1.000001:cross.append(x1+t*(x2-x1))
            cross=sorted(set(round(x,7) for x in cross))
            if len(cross)>=2 and cross[-1]-cross[0]>.02:
                a,b=cross[0]+.003,cross[-1]-.003
                g.tube([(a,.060,sign*slope*a+intercept),(b,.060,sign*slope*b+intercept)],.0055 if w<1.2 else .008,'bronze',6)
    g.tube([(0,.058,.04),(0,.058,h-.20)],.009 if w<1.2 else .014,'bronze',6)
    me.clear_geometry();me.from_pydata(g.v,[],g.f);me.materials.clear()
    for ma in g.mats:me.materials.append(ma)
    for p,idx in zip(me.polygons,g.mi):p.material_index=idx
    me['leaded_dormer_refined']=True;me.update();lead_templates+=1
# Slightly denser pooling mist from the preceding forest pass.
for n in fog.node_tree.nodes:
    if n.type=='MATH' and n.operation=='MULTIPLY' and abs(n.inputs[1].default_value-.012)<1e-6:n.inputs[1].default_value=.025



# Connect the large-window lead network to the full arched glass perimeter.
lead_templates_large=0
for me in list(bpy.data.meshes):
    if not me.users or 'Window • prototype (' not in me.name:continue
    match=re.search(r'prototype (\([^\)]+\))',me.name)
    if not match:continue
    w,h,style=ast.literal_eval(match.group(1))
    if style<2 or me.get('full_arch_lead_network'):continue
    g=Geo();g.v=[tuple(v.co) for v in me.vertices];g.mats=list(me.materials)
    for face in me.polygons:
        if me.materials[face.material_index]==M['bronze']:continue
        g.f.append(tuple(face.vertices));g.mi.append(face.material_index)
    profile=gothic(w-.24,h-.16,32);slope=1.28;spacing=.52
    for sign in [-1,1]:
        for j in range(-int(w/spacing)-3,int(h/spacing)+int(w/spacing)+4):
            intercept=j*spacing;cross=[]
            for k,(x1,z1) in enumerate(profile):
                x2,z2=profile[(k+1)%len(profile)];den=(z2-z1)-sign*slope*(x2-x1)
                if abs(den)<1e-10:continue
                t=(sign*slope*x1+intercept-z1)/den
                if -.000001<=t<=1.000001:cross.append(x1+t*(x2-x1))
            cross=sorted(set(round(x,7) for x in cross))
            if len(cross)>=2 and cross[-1]-cross[0]>.015:
                a,b=cross[0],cross[-1]
                g.tube([(a,.067,sign*slope*a+intercept),(b,.067,sign*slope*b+intercept)],.0085,'bronze',6)
    used=sorted({idx for face in g.f for idx in face});index={old:new for new,old in enumerate(used)}
    verts=[g.v[i] for i in used];faces=[tuple(index[i] for i in face) for face in g.f]
    me.clear_geometry();me.from_pydata(verts,[],faces);me.materials.clear()
    for ma in g.mats:me.materials.append(ma)
    for face,idx in zip(me.polygons,g.mi):face.material_index=idx
    me['full_arch_lead_network']=True;me.update();lead_templates_large+=1
