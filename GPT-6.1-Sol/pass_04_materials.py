
# Fill the conifer crowns with irregular, overlapping branch masses.
for variant in range(10):
    me=bpy.data.meshes.get('Conifer • prototype %02d · mesh'%variant)
    if not me:continue
    rnd=random.Random(9400+variant);height=tree_meshes[variant][1]
    g=Geo();g.v=[tuple(v.co) for v in me.vertices];g.f=[tuple(p.vertices) for p in me.polygons];g.mi=[p.material_index for p in me.polygons];g.mats=list(me.materials)
    baseR=height*(.18+variant%3*.012)
    for lev in range(13):
        t=.12+lev*.063;zz=height*t;rad=baseR*(1-t)**.85;nn=22
        v=[]
        for ringi in range(3):
            rr=rad*[1.0,.75,.10][ringi];rz=zz+[0,height*.05,height*.15][ringi]
            for j in range(nn):
                aa=j*math.tau/nn+lev*.61
                rrj=rr*(.80+rnd.random()*.29)*(1+.09*(j%2))
                v.append((rrj*math.cos(aa),rrj*math.sin(aa),rz+rnd.uniform(-.14,.14)))
        f=[]
        for ri in range(2):
            for j in range(nn):f.append((ri*nn+j,ri*nn+(j+1)%nn,(ri+1)*nn+(j+1)%nn,(ri+1)*nn+j))
        f.append(tuple(range(2*nn,3*nn)))
        g.add(v,f,needle_mats[(lev+variant)%5])
    me.clear_geometry();me.from_pydata(g.v,[],g.f);me.materials.clear()
    for ma in g.mats:me.materials.append(ma)
    for p,i in zip(me.polygons,g.mi):p.material_index=i;p.use_smooth=True
    me.update()
# Node helpers keep every material procedural and scaled in metres.
def shader_reset(ma):
    nt=ma.node_tree;nt.nodes.clear()
    p=nt.nodes.new('ShaderNodeBsdfPrincipled');out=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(p.outputs['BSDF'],out.inputs['Surface'])
    geo=nt.nodes.new('ShaderNodeNewGeometry');geo.location=(-1100,0)
    return nt,p,out,geo
def node(nt,typ,name=None):
    o=nt.nodes.new(typ)
    if name:o.label=name;o.name=name
    return o
def noise_node(nt,vec,scale,detail=4,rough=.7):
    n=node(nt,'ShaderNodeTexNoise');n.inputs['Scale'].default_value=scale;n.inputs['Detail'].default_value=detail;n.inputs['Roughness'].default_value=rough
    nt.links.new(vec,n.inputs['Vector']);return n
def ramp(nt,fac,colors):
    r=node(nt,'ShaderNodeValToRGB')
    es=r.color_ramp.elements
    es.remove(es[1])
    for i,(pos,col) in enumerate(colors):
        e=es[0] if i==0 else es.new(pos);e.position=pos;e.color=(*col,1)
    nt.links.new(fac,r.inputs['Fac']);return r
def mathn(nt,op,a=None,b=None):
    n=node(nt,'ShaderNodeMath');n.operation=op
    for i,v in enumerate([a,b]):
        if v is None:continue
        if isinstance(v,(int,float)):n.inputs[i].default_value=v
        else:nt.links.new(v,n.inputs[i])
    return n
def vector_scale(nt,vec,scale):
    n=node(nt,'ShaderNodeVectorMath');n.operation='MULTIPLY';nt.links.new(vec,n.inputs[0]);n.inputs[1].default_value=scale
    return n.outputs[0]
def mixc(nt,fac,c0,c1):
    m=node(nt,'ShaderNodeMixRGB');m.blend_type='MIX'
    nt.links.new(fac,m.inputs[0]) if not isinstance(fac,(float,int)) else setattr(m.inputs[0],'default_value',fac)
    for idx,c in [(1,c0),(2,c1)]:
        if isinstance(c,tuple):m.inputs[idx].default_value=(*c,1)
        else:nt.links.new(c,m.inputs[idx])
    return m.outputs[0]
def bump_node(nt,height,strength,distance,normal=None):
    b=node(nt,'ShaderNodeBump');b.inputs['Strength'].default_value=strength;b.inputs['Distance'].default_value=distance;nt.links.new(height,b.inputs['Height'])
    if normal:nt.links.new(normal,b.inputs['Normal'])
    return b.outputs['Normal']
def stone_shader(ma,light=False):
    nt,p,out,geo=shader_reset(ma);pos=geo.outputs['Position'];p.inputs['Roughness'].default_value=.83
    sep=node(nt,'ShaderNodeSeparateXYZ');nt.links.new(pos,sep.inputs[0])
    tangent=mathn(nt,'ADD',sep.outputs['X'],mathn(nt,'MULTIPLY',sep.outputs['Y'],.83).outputs[0])
    comb=node(nt,'ShaderNodeCombineXYZ');nt.links.new(tangent.outputs[0],comb.inputs['X']);nt.links.new(sep.outputs['Z'],comb.inputs['Y'])
    brick=node(nt,'ShaderNodeTexBrick','Hand-cut sandstone courses');nt.links.new(comb.outputs[0],brick.inputs['Vector'])
    brick.inputs['Scale'].default_value=1
    brick.inputs['Brick Width'].default_value=.96;brick.inputs['Row Height'].default_value=.43
    brick.inputs['Mortar Size'].default_value=.018;brick.inputs['Mortar Smooth'].default_value=.008
    c1=(.38,.31,.215) if light else (.28,.225,.155);c2=(.24,.225,.178) if light else (.17,.16,.127)
    brick.inputs['Color1'].default_value=(*c1,1);brick.inputs['Color2'].default_value=(*c2,1);brick.inputs['Mortar'].default_value=(.068,.068,.055,1)
    macro=noise_node(nt,pos,.16,5)
    quarry=ramp(nt,macro.outputs['Fac'],[(.20,(.13,.115,.09)),(.47,(.30,.25,.17)),(.76,(.45,.36,.245))])
    col=mixc(nt,.35,brick.outputs['Color'],quarry.outputs['Color'])
    streak_vec=vector_scale(nt,pos,(.46,.46,.022))
    streak=noise_node(nt,streak_vec,3.2,5)
    sr=ramp(nt,streak.outputs['Fac'],[(.29,(0,0,0)),(.63,(.12,.12,.12)),(.78,(.46,.46,.46))])
    col=mixc(nt,sr.outputs[0],col,(.072,.068,.049))
    # Humidity and moss gather around the lower, wet stone.
    height=node(nt,'ShaderNodeMapRange');nt.links.new(sep.outputs['Z'],height.inputs['Value'])
    height.inputs['From Min'].default_value=25;height.inputs['From Max'].default_value=78;height.inputs['To Min'].default_value=.58;height.inputs['To Max'].default_value=0;height.clamp=True
    mossnoise=noise_node(nt,pos,1.15,4)
    moss=ramp(nt,mossnoise.outputs['Fac'],[(.43,(0,0,0)),(.59,(.18,.18,.18)),(.77,(1,1,1))])
    mf=mathn(nt,'MULTIPLY',height.outputs[0],moss.outputs[0])
    col=mixc(nt,mf.outputs[0],col,(.063,.090,.042))
    # Curvature gently lightens weathered corners; fine erosion survives close views.
    wear=ramp(nt,geo.outputs['Pointiness'],[(.40,(0,0,0)),(.53,(.10,.10,.10)),(.65,(.37,.37,.37))])
    col=mixc(nt,wear.outputs[0],col,(.43,.365,.257))
    nt.links.new(col,p.inputs['Base Color'])
    mort=bump_node(nt,brick.outputs['Fac'],.45,.035)
    fine=noise_node(nt,pos,34,4,.78)
    fineb=bump_node(nt,fine.outputs['Fac'],.42,.018,mort)
    nt.links.new(fineb,p.inputs['Normal'])
    rough=mathn(nt,'MULTIPLY_ADD',macro.outputs['Fac'],.17);rough.inputs[2].default_value=.69;nt.links.new(rough.outputs[0],p.inputs['Roughness'])
stone_shader(M['stone'])
stone_shader(M['trim'],True)
# Schist: warped diagonal strata, mineral bands, cracks and damp lichen.
nt,p,out,geo=shader_reset(M['rock']);pos=geo.outputs['Position']
p.inputs['Roughness'].default_value=.91
macro=noise_node(nt,pos,.29,6,.74)
base=ramp(nt,macro.outputs['Fac'],[(.19,(.045,.054,.055)),(.44,(.11,.132,.132)),(.62,(.19,.202,.18)),(.82,(.32,.309,.24))])
mapn=node(nt,'ShaderNodeVectorMath');mapn.operation='MULTIPLY';nt.links.new(pos,mapn.inputs[0]);mapn.inputs[1].default_value=(.10,.11,.73)
wave=node(nt,'ShaderNodeTexWave','Metamorphic schist foliation');wave.wave_type='BANDS';wave.bands_direction='DIAGONAL';wave.inputs['Scale'].default_value=2.3;wave.inputs['Distortion'].default_value=4.6;wave.inputs['Detail'].default_value=5;wave.inputs['Detail Scale'].default_value=1.9;nt.links.new(mapn.outputs[0],wave.inputs['Vector'])
layer=ramp(nt,wave.outputs['Fac'],[(.05,(.032,.045,.046)),(.39,(.13,.15,.139)),(.72,(.24,.247,.204)),(.97,(.095,.12,.115))])
col=mixc(nt,.28,base.outputs[0],layer.outputs[0])
fine=noise_node(nt,pos,8.5,5,.76)
vor=node(nt,'ShaderNodeTexVoronoi','Mineral fracture network');vor.feature='DISTANCE_TO_EDGE';vor.inputs['Scale'].default_value=.84;nt.links.new(pos,vor.inputs['Vector'])
cracks=ramp(nt,vor.outputs['Distance'],[(.0,(.47,.47,.47)),(.013,(.30,.30,.30)),(.044,(0,0,0))])
col=mixc(nt,cracks.outputs[0],col,(.021,.035,.031))
sep=node(nt,'ShaderNodeSeparateXYZ');nt.links.new(pos,sep.inputs[0])
hm=node(nt,'ShaderNodeMapRange');nt.links.new(sep.outputs['Z'],hm.inputs['Value']);hm.inputs['From Min'].default_value=0;hm.inputs['From Max'].default_value=54;hm.inputs['To Min'].default_value=.50;hm.inputs['To Max'].default_value=.05
moss=mathn(nt,'MULTIPLY',hm.outputs[0],ramp(nt,macro.outputs['Fac'],[(.37,(0,0,0)),(.64,(1,1,1))]).outputs[0])
col=mixc(nt,moss.outputs[0],col,(.07,.095,.053));nt.links.new(col,p.inputs['Base Color'])
b0=bump_node(nt,wave.outputs['Fac'],.28,.12)
b1=bump_node(nt,fine.outputs['Fac'],.65,.09,b0)
b2=bump_node(nt,vor.outputs['Distance'],.30,.05,b1);nt.links.new(b2,p.inputs['Normal'])
# Add subtle geometric erosion to the major exposed slabs.
tex=bpy.data.textures.new('Crag • procedural fracture erosion',type='CLOUDS');tex.noise_scale=2.1;tex.noise_depth=2
for ob in C['Terrain'].objects:
    if ob.name.startswith('Crag • tilted fracture slab') or ob.name.startswith('Crag • crown ledge'):
        sub=ob.modifiers.new('Subdivided fracture surface','SUBSURF');sub.subdivision_type='SIMPLE';sub.levels=2;sub.render_levels=2
        disp=ob.modifiers.new('Schist micro-erosion','DISPLACE');disp.texture=tex;disp.strength=.45;disp.mid_level=.50;disp.texture_coords='GLOBAL'
# Blue slate flakes with tile-scale mineral variation and subtle moss.
for ma in [M['roof'],*slate_mats]:
    color=tuple(ma.diffuse_color[:3]);nt,p,out,geo=shader_reset(ma);pos=geo.outputs['Position'];p.inputs['Roughness'].default_value=.63
    n=noise_node(nt,pos,12,3);col=ramp(nt,n.outputs['Fac'],[(.2,tuple(c*.65 for c in color)),(.52,color),(.79,tuple(c*1.26 for c in color))])
    n2=noise_node(nt,pos,63,3);normal=bump_node(nt,n2.outputs['Fac'],.40,.007)
    nt.links.new(col.outputs[0],p.inputs['Base Color']);nt.links.new(normal,p.inputs['Normal'])
# Verdigris copper: exposed metal peeks through the weathered oxide.
nt,p,out,geo=shader_reset(M['copper']);pos=geo.outputs['Position']
n=noise_node(nt,pos,1.3,6);pat=ramp(nt,n.outputs['Fac'],[(.20,(.045,.026,.014)),(.42,(.062,.098,.075)),(.60,(.105,.245,.199)),(.81,(.19,.31,.245))])
nt.links.new(pat.outputs[0],p.inputs['Base Color']);nt.links.new(mathn(nt,'SUBTRACT',.92,mathn(nt,'MULTIPLY',n.outputs[0],.55).outputs[0]).outputs[0],p.inputs['Metallic'])
p.inputs['Roughness'].default_value=.46;nt.links.new(bump_node(nt,noise_node(nt,pos,31,3).outputs[0],.36,.01),p.inputs['Normal'])
# Aged oak and bronze.
nt,p,out,geo=shader_reset(M['wood']);pos=geo.outputs['Position']
grain=noise_node(nt,vector_scale(nt,pos,(.24,7.0,7.0)),3.1,4)
col=ramp(nt,grain.outputs[0],[(.18,(.020,.012,.007)),(.48,(.095,.046,.018)),(.78,(.21,.121,.054))])
nt.links.new(col.outputs[0],p.inputs['Base Color']);p.inputs['Roughness'].default_value=.79;nt.links.new(bump_node(nt,grain.outputs[0],.51,.025),p.inputs['Normal'])
nt,p,out,geo=shader_reset(M['bronze']);pos=geo.outputs['Position'];p.inputs['Metallic'].default_value=.78;p.inputs['Roughness'].default_value=.41
pat=noise_node(nt,pos,5.2,4);cc=ramp(nt,pat.outputs[0],[(.2,(.025,.024,.017)),(.5,(.095,.071,.029)),(.8,(.045,.104,.079))]);nt.links.new(cc.outputs[0],p.inputs['Base Color'])
nt.links.new(bump_node(nt,noise_node(nt,pos,40,2).outputs[0],.3,.006),p.inputs['Normal'])
# Moorland mixes peat, heather, lichen and exposed rock.
nt,p,out,geo=shader_reset(M['ground']);pos=geo.outputs['Position'];p.inputs['Roughness'].default_value=.98
macro=noise_node(nt,pos,.045,5);col=ramp(nt,macro.outputs[0],[(.20,(.028,.041,.025)),(.40,(.063,.09,.038)),(.62,(.10,.119,.057)),(.77,(.13,.094,.072))])
patch=noise_node(nt,pos,.30,5);rm=ramp(nt,patch.outputs[0],[(.57,(0,0,0)),(.77,(.65,.65,.65))])
color=mixc(nt,rm.outputs[0],col.outputs[0],(.13,.14,.109));nt.links.new(color,p.inputs['Base Color'])
nt.links.new(bump_node(nt,noise_node(nt,pos,11,3).outputs[0],.60,.075),p.inputs['Normal'])
# Path gravel and slate chips.
nt,p,out,geo=shader_reset(M['path']);pos=geo.outputs['Position'];p.inputs['Roughness'].default_value=.85
n=noise_node(nt,pos,9,3);cc=ramp(nt,n.outputs[0],[(.2,(.07,.056,.036)),(.8,(.21,.175,.112))]);nt.links.new(cc.outputs[0],p.inputs['Base Color']);nt.links.new(bump_node(nt,n.outputs[0],.68,.055),p.inputs['Normal'])
# Needle color varies by tree as well as along every crown.
for ma in needle_mats:
    base=tuple(ma.diffuse_color[:3]);nt,p,out,geo=shader_reset(ma);pos=geo.outputs['Position'];p.inputs['Roughness'].default_value=.82
    n=noise_node(nt,pos,8.2,2);col=ramp(nt,n.outputs[0],[(.22,tuple(c*.62 for c in base)),(.78,tuple(c*1.45 for c in base))])
    info=node(nt,'ShaderNodeObjectInfo');var=ramp(nt,info.outputs['Random'],[(0,(.69,.73,.66)),(1,(1.2,1.13,.84))])
    mul=node(nt,'ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=.65;nt.links.new(col.outputs[0],mul.inputs[1]);nt.links.new(var.outputs[0],mul.inputs[2]);nt.links.new(mul.outputs[0],p.inputs['Base Color'])
    p.inputs['Subsurface Weight'].default_value=.045
    nt.links.new(bump_node(nt,n.outputs[0],.2,.004),p.inputs['Normal'])
# Fresnel water, small ripples, and real near-shore absorption.
nt,p,out,geo=shader_reset(M['water']);pos=geo.outputs['Position'];p.inputs['Base Color'].default_value=(.016,.031,.039,1);p.inputs['Roughness'].default_value=.035;p.inputs['Transmission Weight'].default_value=.98;p.inputs['IOR'].default_value=1.333
wave=node(nt,'ShaderNodeTexWave');wave.wave_type='BANDS';wave.bands_direction='X';wave.inputs['Scale'].default_value=.72;wave.inputs['Distortion'].default_value=7;wave.inputs['Detail'].default_value=4;wave.inputs['Detail Scale'].default_value=1.8;nt.links.new(vector_scale(nt,pos,(.58,1.0,.4)),wave.inputs['Vector'])
n=noise_node(nt,pos,2.9,3);normal=bump_node(nt,wave.outputs['Fac'],.32,.11);normal=bump_node(nt,n.outputs['Fac'],.24,.026,normal);nt.links.new(normal,p.inputs['Normal'])
depth=bpy.data.materials.new('Lake • blue-green absorption');depth.use_nodes=True;nd=depth.node_tree;nd.nodes.clear()
out=nd.nodes.new('ShaderNodeOutputMaterial');ab=nd.nodes.new('ShaderNodeVolumeAbsorption');ab.inputs['Color'].default_value=(.14,.38,.39,1);ab.inputs['Density'].default_value=.08;nd.links.new(ab.outputs[0],out.inputs['Volume'])
box('Black Lake • deep absorption volume',(0,-350,-40),(6000,5300,80),depth,group='FX')
# Reduce the daytime-like base reflection from unlit panes.
p=M['window'].node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.029,.018,.01,1);p.inputs['Emission Strength'].default_value=2.4
