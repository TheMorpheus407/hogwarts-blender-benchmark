
import bpy, math, random, os
from mathutils import Vector, Matrix
from mathutils.noise import noise, fractal
ROOT='/home/morpheus/Documents/Morpheus-Produktion/Benchmarks/Blender/GPT-6.1-Sol'
rng=random.Random(74119)
C={}
for name in ['Castle','Terrain','Nature','Lights','FX','Cameras']:
    c=bpy.data.collections.get(name) or bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c) if c.name not in bpy.context.scene.collection.children else None
    C[name]=c
def mat(name,col,rough=.7,metal=0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name); m.diffuse_color=(*col,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*col,1)
    p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
    return m
M={}
M['stone']=mat('Stone • weathered Highland sandstone',(.28,.245,.193))
M['trim']=mat('Stone • pale cut limestone',(.38,.35,.278))
M['roof']=mat('Roof • midnight blue Welsh slate',(.047,.071,.09),.36)
M['copper']=mat('Roof • aged verdigris copper',(.074,.17,.16),.43,.68)
M['rock']=mat('Crag • ancient stratified schist',(.13,.155,.155),.9)
M['ground']=mat('Moor • heather and damp grass',(.069,.105,.074),.95)
M['water']=mat('Lake • black water',(.016,.042,.063),.075)
M['dark']=mat('Recess • deep unlit interior',(.005,.009,.012),.65)
M['bronze']=mat('Metal • aged black bronze',(.075,.053,.024),.32,.76)
M['wood']=mat('Timber • damp old oak',(.09,.05,.026),.8)
def mesh(name,verts,faces,ma='stone',group='Castle',smooth=False):
    me=bpy.data.meshes.new(name+' · mesh'); me.from_pydata(verts,[],faces); me.update()
    ob=bpy.data.objects.new(name,me); C[group].objects.link(ob)
    if ma: me.materials.append(M[ma] if isinstance(ma,str) else ma)
    if smooth:
        for p in me.polygons:p.use_smooth=True
    return ob
def box(name,loc,dim,ma='stone',bevel=0,group='Castle'):
    x,y,z=[d/2 for d in dim]
    v=[(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
    f=[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]
    o=mesh(name,v,f,ma,group); o.location=loc
    if bevel:
        mod=o.modifiers.new('Soft weathered edges','BEVEL');mod.width=bevel;mod.segments=2
    return o
def cyl(name,x,y,z,r,h,ma='stone',n=48,r2=None,smooth=True,group='Castle'):
    if r2 is None:r2=r
    verts=[]
    for zz,rr in [(z,r),(z+h,r2)]:
        verts += [(x+rr*math.cos(2*math.pi*i/n),y+rr*math.sin(2*math.pi*i/n),zz) for i in range(n)]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,verts,faces,ma,group,smooth)
def ring(name,x,y,z,r,thick,h,ma='trim',n=64):
    verts=[]
    for zz,rr in [(z,r),(z,r-thick),(z+h,r),(z+h,r-thick)]:
        verts += [(x+rr*math.cos(2*math.pi*i/n),y+rr*math.sin(2*math.pi*i/n),zz) for i in range(n)]
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces += [(i,j,j+2*n,i+2*n),(i+n,i+3*n,j+3*n,j+n),(i+2*n,j+2*n,j+3*n,i+3*n),(j,i,i+n,j+n)]
    return mesh(name,verts,faces,ma,smooth=True)
def beam(name,a,b,width,ma='trim',group='Castle'):
    a,b=Vector(a),Vector(b);d=b-a
    o=box(name,(a+b)/2,(width,width,d.length),ma,group=group)
    o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    return o
def curve(name,pts,radius=.1,ma='trim',group='Castle',cyclic=False):
    cu=bpy.data.curves.new(name+' · curve','CURVE');cu.dimensions='3D';cu.resolution_u=1
    sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
    for p,v in zip(sp.points,pts):p.co=(*v,1)
    sp.use_cyclic_u=cyclic;cu.bevel_depth=radius;cu.resolution_u=1;cu.bevel_resolution=2
    o=bpy.data.objects.new(name,cu);C[group].objects.link(o);cu.materials.append(M[ma] if isinstance(ma,str) else ma)
    return o
def gable(name,x,y,z,L,W,rise,ma='roof'):
    v=[(x-L/2,y-W/2,z),(x+L/2,y-W/2,z),(x+L/2,y+W/2,z),(x-L/2,y+W/2,z),(x-L/2,y,z+rise),(x+L/2,y,z+rise)]
    return mesh(name,v,[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4),(0,3,2,1)],ma)
def turret(name,x,y,z,r,h,roof,ma='roof',n=48):
    body=cyl(name+' • shaft',x,y,z,r,h)
    cyl(name+' • eaves',x,y,z+h-.8,r+.45,1.3,'trim')
    cyl(name+' • spire',x,y,z+h,r+.65,roof,ma,n=n,r2=.05)
    cyl(name+' • finial',x,y,z+h+roof-.1,.10,2.4,'bronze',n=12,r2=.02)
    return body
def light(name,loc,energy,color,size=1,typ='AREA',target=None):
    data=bpy.data.lights.new(name,typ);data.energy=energy;data.color=color
    if typ=='AREA':data.shape='DISK';data.size=size
    elif typ=='POINT':data.shadow_soft_size=size
    ob=bpy.data.objects.new(name,data);C['Lights'].objects.link(ob);ob.location=loc
    if target:ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    return ob
def camera(name,loc,target,lens=45):
    d=bpy.data.cameras.new(name);d.lens=lens;d.clip_end=12000
    ob=bpy.data.objects.new(name,d);C['Cameras'].objects.link(ob);ob.location=loc
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    return ob
def rock_radial(name,cx,cy,rx,ry,height,seed=1):
    rnd=random.Random(seed);n=128;rings=20;verts=[]
    phase=rnd.random()*6.2
    for j in range(rings):
        t=j/(rings-1);z=-5+t*(height+5)
        for i in range(n):
            a=2*math.pi*i/n
            rr=1.18-.24*t + .08*math.sin(a*5+phase)+.045*math.cos(a*11-phase)
            rr+=.03*noise(Vector((math.cos(a)*8,math.sin(a)*8,t*17)))
            x=cx+rx*rr*math.cos(a)+6*math.sin(t*4+phase)
            y=cy+ry*rr*math.sin(a)+3*math.sin(t*6)
            zz=z+2.5*math.sin(a*5+phase)+1.1*noise(Vector((x*.09,y*.09,t*8)))
            if j==rings-1:zz=height+.7*math.sin(a*5)
            verts.append((x,y,zz))
    verts.append((cx,cy,height));center=len(verts)-1;faces=[]
    for j in range(rings-1):
        for i in range(n):
            q=j*n+i;u=j*n+(i+1)%n
            if (i+j)%2:faces += [(q,u,u+n),(q,u+n,q+n)]
            else:faces += [(q,u,q+n),(u,u+n,q+n)]
    for i in range(n):faces.append(((rings-1)*n+i,(rings-1)*n+(i+1)%n,center))
    return mesh(name,verts,faces,'rock','Terrain')
def terrain_h(x,y):
    a=math.exp(-(((x-230)/190)**2+((y-75)/260)**2))
    b=math.exp(-(((x+190)/150)**2+((y-120)/280)**2))
    base=35*a+32*b+30/(1+math.exp(-(y-135)/50))
    f=fractal(Vector((x*.007,y*.007,2)),1.0,2.1,5)
    return max(-12,base+15*f+6*math.sin(x*.012+y*.018))
def terrain(name,x0,x1,y0,y1,nx,ny,func,ma='ground'):
    v=[]
    for j in range(ny+1):
        y=y0+(y1-y0)*j/ny
        for i in range(nx+1):
            x=x0+(x1-x0)*i/nx;v.append((x,y,func(x,y)))
    f=[]
    for j in range(ny):
        for i in range(nx):
            k=j*(nx+1)+i;f += [(k,k+1,k+nx+2),(k,k+nx+2,k+nx+1)]
    return mesh(name,v,f,ma,'Terrain',True)


# Gothic construction library: local facade coordinates are X / depth / Z.
def gothic(w,h,steps=12):
    spring=h-w*.8660254
    pts=[(-w/2,0),(w/2,0),(w/2,spring)]
    for i in range(1,steps+1):
        t=i/steps; a=t*math.pi/3
        pts.append((-w/2+w*math.cos(a),spring+w*math.sin(a)))
    for i in range(1,steps+1):
        t=i/steps;a=math.pi/3+(2*math.pi/3)*0
        # Mirror the right arc across the apex, travelling to left shoulder.
        aa=(1-t)*math.pi/3
        pts.append((w/2-w*math.cos(aa),spring+w*math.sin(aa)))
    return pts
def extrude_profile(name,profile,d0,d1,ma='stone'):
    n=len(profile);v=[(x,d0,z) for x,z in profile]+[(x,d1,z) for x,z in profile]
    f=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    f += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,v,f,ma)
def arch_ring(name,w,h,width,depth=.30,ma='trim'):
    a=gothic(w,h);b=gothic(w+2*width,h+width)
    n=len(a);v=[]
    for y,prof in [(-depth,a),(-depth,b),(0,a),(0,b)]:
        v += [(x,y,z-width if prof is b else z) for x,z in prof]
    f=[]
    for i in range(n):
        j=(i+1)%n
        f += [(i,j,j+n,i+n),(i+n,j+n,j+3*n,i+3*n),(i+2*n,j+2*n,j,i),(i+3*n,j+3*n,j+2*n,i+2*n)]
    return mesh(name,v,f,ma)
def merge_objects(name,objects,group='Castle'):
    verts=[];faces=[];inds=[];materials=[]
    dg=bpy.context.evaluated_depsgraph_get()
    for o in objects:
        eo=o.evaluated_get(dg);me=eo.to_mesh();start=len(verts)
        verts += [tuple(o.matrix_world @ v.co) for v in me.vertices]
        faces += [tuple(start+i for i in p.vertices) for p in me.polygons]
        slots=[]
        for ma in me.materials:
            if ma not in materials:materials.append(ma)
            slots.append(materials.index(ma))
        inds += [slots[p.material_index] if slots else 0 for p in me.polygons]
        eo.to_mesh_clear()
    ob=mesh(name,verts,faces,None,group)
    for ma in materials:ob.data.materials.append(ma)
    for p,i in zip(ob.data.polygons,inds):p.material_index=i
    for o in objects:bpy.data.objects.remove(o,do_unlink=True)
    return ob
def emit_windows():
    m=mat('Glass • candlelight varied by room',(.52,.23,.058),.22)
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    info=n.new('ShaderNodeObjectInfo')
    ramp=n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    for pos,col in [(0,(.002,.003,.006,1)),(.22,(.009,.018,.022,1)),(.29,(.27,.11,.028,1)),(.48,(.78,.31,.065,1)),(.70,(1,.49,.15,1)),(.89,(1,.69,.31,1))]:
        e=ramp.color_ramp.elements[0] if pos==0 else ramp.color_ramp.elements.new(pos);e.position=pos;e.color=col
    ramp.color_ramp.interpolation='CONSTANT'
    l.new(info.outputs['Random'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Emission Color'])
    p.inputs['Emission Strength'].default_value=3.2
    p.inputs['Metallic'].default_value=.06;p.inputs['Transmission Weight'].default_value=.08
    M['window']=m
    M['lantern']=mat('Glass • lantern amber',(.7,.30,.075),.15)
    p=M['lantern'].node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.38,.065,1);p.inputs['Emission Strength'].default_value=8
emit_windows()
window_templates={}
def window_template(w,h,style=2):
    key=(round(w,2),round(h,2),style)
    if key in window_templates:return window_templates[key]
    before=set(bpy.data.objects)
    extrude_profile('Window • dark reveal',gothic(w,h),.24,.32,'dark')
    extrude_profile('Window • warm panes',gothic(w-.27,h-.19),.17,.19,'window')
    arch_ring('Window • outer limestone archivolt',w,h,.19,.24)
    arch_ring('Window • fine inner bead',w-.16,h-.06,.055,.14)
    box('Window • projecting drip sill',(0,-.18,-.1),(w+.7,.80,.25),'trim',.025)
    for s in [-1,1]:
        box('Window • jamb shaft',(s*(w/2+.07),-.26,(h-w*.866)/2),(.13,.13,h-w*.866),'trim',.02)
        cyl('Window • column capital',s*(w/2+.07),-.26,h-w*.866-.16,.12,.2,'trim',n=12)
    spring=h-w*.866
    if style>=2:
        for k in range(1,style):
            xx=-w/2+w*k/style
            box('Window • mullion',(xx,-.09,(h-.8)/2),(.10,.16,h-.8),'trim')
        if h>4:
            for z in [h*.30,h*.62]:
                box('Window • transom',(0,-.09,z),(w-.28,.15,.10),'trim')
        # Curved stone tracery and leaded diamonds.
        for k in range(style):
            xx=-w/2+w*(k+.5)/style;sw=(w-.35)/style
            pts=[(u+xx,-.105,z+spring-sw*.56) for u,z in gothic(sw,sw*1.5)]
            curve('Window • lancet tracery',pts,.048,'trim')
        for level in range(max(2,int(spring/.85))):
            zz=.45+level*.8
            for col in range(style):
                xx=-w/2+w*(col+.5)/style
                curve('Window • leaded diamond',[(xx-.23,.12,zz),(xx,.12,zz+.35),(xx+.23,.12,zz),(xx,.12,zz-.35)],.013,'bronze',cyclic=True)
        cz=h-w*.60;rr=w*.15
        for k in range(3):
            a=2*math.pi*k/3+math.pi/2
            pts=[(rr*.6*math.cos(a)+rr*.65*math.cos(t*2*math.pi/24),-.12,cz+rr*.6*math.sin(a)+rr*.65*math.sin(t*2*math.pi/24)) for t in range(24)]
            curve('Window • trefoil tracery',pts,.039,'trim',cyclic=True)
    objs=[o for o in bpy.data.objects if o not in before]
    ob=merge_objects('Gothic window • prototype '+str(key),objs)
    window_templates[key]=ob.data
    bpy.data.objects.remove(ob,do_unlink=True)
    return window_templates[key]
def window(name,loc,w,h,angle=0,style=2):
    data=window_template(w,h,style)
    o=bpy.data.objects.new(name,data);C['Castle'].objects.link(o)
    o.location=loc;o.rotation_euler.z=angle;o['architectural_element']='arched mullioned window'
    return o
def localize(ob,loc,angle):
    ob.location=loc;ob.rotation_euler.z=angle
    return ob
def gothic_wall_cell(name,loc,bay,wall_h,w,h,bottom,angle=0,thickness=1.3):
    # Build a genuinely open arched wall bay from an extruded outline.
    profile=gothic(w,h)
    upper=profile[2:]
    # Right shoulder across apex down to left shoulder, then around outside.
    poly=[(x,z+bottom) for x,z in upper]
    spring=h-w*.866+bottom
    poly += [(-bay/2,spring),(-bay/2,wall_h),(bay/2,wall_h),(bay/2,spring)]
    localize(extrude_profile(name+' • pointed spandrel',poly,0,thickness,'stone'),loc,angle)
    for xx in [-(bay+w)/4,(bay+w)/4]:
        localize(box(name+' • jamb masonry',(xx,thickness/2,(spring+bottom)/2),((bay-w)/2,thickness,spring-bottom),'stone'),loc,angle)
        # Compensate transforms: box has world coords before localization.
    # Use vertices for bottom wall so its origin can carry local coordinates.
    o=box(name+' • lower masonry',(0,thickness/2,bottom/2),(bay,thickness,bottom),'stone')
    o.data.transform(o.matrix_world);o.location=(0,0,0);localize(o,loc,angle)
    # Jamb origins similarly need their local offsets retained.
    for o in list(bpy.data.objects):
        if o.name.startswith(name+' • jamb masonry'):
            # They have already been localized, restore the intended local geometry offset.
            xx=-(bay+w)/4 if 'masonry.001' not in o.name else (bay+w)/4
    # Explicit properly transformed side columns.
    # Old columns are removed and recreated below.
    for o in list(bpy.data.objects):
        if o.name.startswith(name+' • jamb masonry'):bpy.data.objects.remove(o,do_unlink=True)
    for k,xx in enumerate([-(bay+w)/4,(bay+w)/4]):
        o=box(name+' • solid side '+str(k),(xx,thickness/2,(spring+bottom)/2),((bay-w)/2,thickness,spring-bottom),'stone')
        o.data.transform(o.matrix_world);o.location=(0,0,0);localize(o,loc,angle)
    window(name+' • tracery',(loc[0]-bottom*0,loc[1],loc[2]+bottom),w,h,angle,3 if w>2.8 else 2)
def pinnacle(name,x,y,z,h=6,r=.40):
    cyl(name+' • stem',x,y,z,r,h*.42,'trim',n=8)
    cyl(name+' • pointed cap',x,y,z+h*.42,r*1.45,h*.58,'roof',n=8,r2=.04)
    cyl(name+' • finial',x,y,z+h,.035,.55,'bronze',n=8,r2=.01)
def lantern(name,x,y,z,scale=1,lit=True):
    cyl(name+' • base',x,y,z,.22*scale,.15*scale,'bronze',n=12)
    cyl(name+' • stem',x,y,z+.15*scale,.055*scale,1.5*scale,'bronze',n=12)
    zz=z+1.65*scale
    box(name+' • amber glass',(x,y,zz+.29*scale),(.34*scale,.34*scale,.55*scale),'lantern')
    cyl(name+' • cap',x,y,zz+.58*scale,.31*scale,.22*scale,'bronze',n=4,r2=.04)
    for sx in [-1,1]:
        for sy in [-1,1]:
            box(name+' • cage',(x+sx*.18*scale,y+sy*.18*scale,zz+.3*scale),(.035*scale,.035*scale,.61*scale),'bronze')
    if lit:light(name+' • pool',(x,y,zz+.2*scale),85*scale*scale,(1,.43,.14),.3,'POINT')


class Geo:
    def __init__(self):self.v=[];self.f=[];self.mi=[];self.mats=[]
    def add(self,v,f,ma='stone'):
        if isinstance(ma,str):ma=M[ma]
        if ma not in self.mats:self.mats.append(ma)
        idx=self.mats.index(ma);off=len(self.v)
        self.v.extend([tuple(p) for p in v]);self.f.extend([tuple(off+i for i in face) for face in f]);self.mi.extend([idx]*len(f))
    def box(self,loc,dim,ma='stone'):
        x,y,z=[d/2 for d in dim];cx,cy,cz=loc
        v=[(cx+u,cy+w,cz+t) for u,w,t in [(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]]
        self.add(v,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],ma)
    def poly(self,profile,d0,d1,ma='stone'):
        n=len(profile);v=[(x,d0,z) for x,z in profile]+[(x,d1,z) for x,z in profile]
        f=[tuple(reversed(range(n))),tuple(range(n,2*n))]
        f += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        self.add(v,f,ma)
    def tube(self,pts,r=.06,ma='trim',n=6,cyclic=False):
        pts=[Vector(p) for p in pts]
        if cyclic:pts.append(pts[0])
        v=[];f=[]
        for i,p in enumerate(pts):
            tangent=pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]
            if tangent.length<.0001:tangent=Vector((0,0,1))
            tangent.normalize()
            u=tangent.cross(Vector((0,1,0)))
            if u.length<.01:u=tangent.cross(Vector((1,0,0)))
            u.normalize();w=tangent.cross(u).normalized()
            for j in range(n):v.append(tuple(p+r*(u*math.cos(math.tau*j/n)+w*math.sin(math.tau*j/n))))
        for i in range(len(pts)-1):
            for j in range(n):f.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
        f += [tuple(reversed(range(n))),tuple(range((len(pts)-1)*n,len(pts)*n))]
        self.add(v,f,ma)
    def create(self,name,group='Castle',smooth=False):
        o=mesh(name,self.v,self.f,None,group,smooth)
        for ma in self.mats:o.data.materials.append(ma)
        for p,i in zip(o.data.polygons,self.mi):p.material_index=i
        return o
def window_template(w,h,style=2):
    key=(round(w,3),round(h,3),style)
    if key in window_templates:return window_templates[key]
    g=Geo()
    g.poly(gothic(w,h),.20,.22,'dark')
    g.poly(gothic(w-.24,h-.16),.105,.12,'window')
    # Two solid carved moldings follow the pointed arch.
    for ww,hh,r,dep in [(w+.26,h+.10,.115,-.08),(w-.10,h-.04,.046,-.15)]:
        pts=[(x,dep,z) for x,z in gothic(ww,hh)]
        g.tube(pts,r,'trim',8,True)
    spring=h-w*.8660254
    g.box((0,-.08,-.13),(w+.7,.85,.24),'trim')
    for s in [-1,1]:
        g.box((s*(w/2+.13),.05,spring/2),(.27,.50,spring),'trim')
        g.box((s*(w/2+.13),-.02,spring-.1),(.42,.58,.25),'trim')
    if style>=2:
        for k in range(1,style):
            xx=-w/2+w*k/style
            g.box((xx,-.02,(h-w*.34)/2),(.09,.19,h-w*.34),'trim')
        for zz in ([h*.30,h*.60] if h>5 else [h*.45]):
            g.box((0,-.02,zz),(w-.20,.19,.085),'trim')
        for k in range(style):
            xx=-w/2+w*(k+.5)/style;sw=(w-.22)/style
            pts=[(u+xx,-.025,z+spring-sw*.65) for u,z in gothic(sw,sw*1.55)]
            g.tube(pts,.038,'trim',6,True)
        rr=w*.125;cz=h-w*.47
        for k in range(3):
            aa=k*math.tau/3+math.pi/2
            pts=[(rr*.60*math.cos(aa)+rr*.68*math.cos(t*math.tau/18),-.06,cz+rr*.60*math.sin(aa)+rr*.68*math.sin(t*math.tau/18)) for t in range(18)]
            g.tube(pts,.034,'trim',6,True)
        for level in range(max(2,int(spring/.70))):
            zz=.42+level*.70
            for col in range(style):
                xx=-w/2+w*(col+.5)/style
                pts=[(xx-.19,.08,zz),(xx,.08,zz+.30),(xx+.19,.08,zz),(xx,.08,zz-.30)]
                g.tube(pts,.012,'bronze',4,True)
    o=g.create('Window • prototype '+str(key))
    window_templates[key]=o.data
    bpy.data.objects.remove(o,do_unlink=True)
    return window_templates[key]
def gothic_wall_cell(name,loc,bay,wall_h,w,h,bottom,angle=0,thickness=1.3):
    g=Geo();spring=h-w*.8660254+bottom
    upper=gothic(w,h)[2:]
    profile=[(x,z+bottom) for x,z in upper]
    profile += [(-bay/2,spring),(-bay/2,wall_h),(bay/2,wall_h),(bay/2,spring)]
    g.poly(profile,0,thickness,'stone')
    for xx in [-(bay+w)/4,(bay+w)/4]:
        g.box((xx,thickness/2,spring/2),((bay-w)/2,thickness,spring),'stone')
    g.box((0,thickness/2,bottom/2),(bay,thickness,bottom),'stone')
    o=g.create(name+' • open arched masonry');o.location=loc;o.rotation_euler.z=angle
    ca,sa=math.cos(angle),math.sin(angle)
    window(name+' • mullioned glazing',(loc[0],loc[1],loc[2]+bottom),w,h,angle,3 if w>2.8 else 2)
    return o
