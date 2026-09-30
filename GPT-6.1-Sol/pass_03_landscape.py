
# Fractured promontory: front face follows the stair height, while the plateau supports the campus.
for name in ['Castle crag • primary promontory','Moorland • northern slopes']:
    if bpy.data.objects.get(name):bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
verts=[];faces=[];n=144;nz=31
for j in range(nz):
    t=j/(nz-1);zz=-5+70*t
    for i in range(n):
        a=math.tau*i/n;cs=math.cos(a);sn=math.sin(a)
        angfract=.025*math.sin(a*19+.8)+.035*math.sin(a*11-1.3)
        localfract=.015*noise(Vector((cs*13,sn*13,t*9)))
        rr=1+angfract+localfract
        rx=111-4*t
        ry=(112-34*t**1.4) if sn<0 else (88-13*t)
        xx=-7+rx*math.copysign(abs(cs)**.84,cs)*rr+2.5*t
        yy=20+ry*sn*rr
        z=zz+(.6*math.sin(a*13+t*6)+.35*noise(Vector((a*8,t*8,7))))*math.sin(t*math.pi)
        verts.append((xx,yy,z))
verts.append((-4.5,20,65));center=len(verts)-1
for j in range(nz-1):
    for i in range(n):
        k=j*n+i;q=j*n+(i+1)%n
        faces.append((k,q,q+n,k+n))
for i in range(n):faces.append(((nz-1)*n+i,(nz-1)*n+(i+1)%n,center))
mesh('Castle crag • fractured schist bedrock',verts,faces,'rock','Terrain',True)
def crag_block(name,loc,size,seed,angle=0):
    rnd=random.Random(seed);nn=rnd.choice([5,6,7]);v=[];hh=size[2]
    angular=[math.tau*i/nn+rnd.uniform(-.10,.10) for i in range(nn)]
    scales=[rnd.uniform(.65,.95),rnd.uniform(.88,1.08),rnd.uniform(.67,.90)]
    for j,(z,scale) in enumerate(zip([-hh/2,0,hh/2],scales)):
        for a in angular:
            x=math.cos(a)*size[0]/2*scale+rnd.uniform(-.25,.25)+z*.18
            y=math.sin(a)*size[1]/2*scale+rnd.uniform(-.3,.3)
            zz=z+rnd.uniform(-1,1)*(0 if j==0 else 1)
            v.append((x,y,zz))
    f=[tuple(reversed(range(nn))),tuple(range(2*nn,3*nn))]
    for j in range(2):
        for i in range(nn):f.append((j*nn+i,j*nn+(i+1)%nn,(j+1)*nn+(i+1)%nn,(j+1)*nn+i))
    o=mesh(name,v,f,'rock','Terrain');o.location=loc;o.rotation_euler.z=angle
    return o
for i in range(43):
    a=math.pi+math.pi*(i+.25)/43
    z=rng.uniform(12,45);t=z/65
    x=-7+(111-4*t)*math.copysign(abs(math.cos(a))**.84,math.cos(a))
    y=20+(112-34*t**1.4)*math.sin(a)
    size=(rng.uniform(7,17),rng.uniform(6,13),rng.uniform(17,34))
    crag_block('Crag • tilted fracture slab %02d'%i,(x,y+1,z),size,1000+i,a*.08)
for i in range(18):
    a=math.tau*i/18;z=rng.uniform(53,57);t=z/65
    x=-7+(111-4*t)*math.copysign(abs(math.cos(a))**.84,math.cos(a));y=20+((112-34*t**1.4) if math.sin(a)<0 else 88-13*t)*math.sin(a)
    crag_block('Crag • crown ledge %02d'%i,(x,y,z),(rng.uniform(10,19),rng.uniform(8,14),rng.uniform(8,17)),2000+i,a)
# Sculpt the stair into the same geology. Move each flight to its rock contour.
old_pts=[(23,-101,2.1),(32,-79,11),(-19,-66,27),(23,-51,43),(-18,-39,58),(-12,-33,65)]
new_pts=[(23,-101,2.1),(32,-91,11),(-19,-84,27),(23,-75,43),(-18,-66,58),(-12,-33,65)]
for ob in list(bpy.data.objects):
    if ob.name.startswith('Boathouse stair •') or ob.name.startswith('Cliff stair •'):
        if ob.type=='MESH':
            for v in ob.data.vertices:
                # Select the flight by its height interval and interpolate the shift.
                zz=v.co.z
                k=min(4,max(0,next((k for k in range(5) if zz<=old_pts[k+1][2]+.25),4)))
                t=max(0,min(1,(zz-old_pts[k][2])/(old_pts[k+1][2]-old_pts[k][2])))
                dy=(new_pts[k][1]-old_pts[k][1])*(1-t)+(new_pts[k+1][1]-old_pts[k+1][1])*t
                v.co.y+=dy
            ob.data.update()
        elif ob.type=='LIGHT':
            zz=ob.location.z-1.4
            k=min(4,max(0,next((k for k in range(5) if zz<=old_pts[k+1][2]),4)))
            t=max(0,min(1,(zz-old_pts[k][2])/(old_pts[k+1][2]-old_pts[k][2])))
            ob.location.y+=(new_pts[k][1]-old_pts[k][1])*(1-t)+(new_pts[k+1][1]-old_pts[k+1][1])*t
# Wider moor terrain, with a genuine open lake in front of the promontory.
def terrain_h(x,y):
    a=45*math.exp(-(((x-260)/195)**2+((y-85)/265)**2))
    b=38*math.exp(-(((x+245)/190)**2+((y-130)/310)**2))
    c=47*math.exp(-(((x-315)/125)**2+((y+215)/140)**2))
    back=40/(1+math.exp(-(y-170)/65))
    f=fractal(Vector((x*.006,y*.006,2)),1.0,2.05,5)
    h=a+b+c+back+11*f+4*math.sin(x*.017+y*.013)
    h-=72*math.exp(-((x-5)/145)**4-((y+48)/155)**4)
    h-=32/(1+math.exp((y+165)/35))
    return h
terrain('Moorland • heather slopes and inlet',-1100,1300,-480,1250,260,210,terrain_h)
# Blend the east viaduct landing into the rolling shore.
east=bpy.data.objects.get('East gate outcrop')
if east:
    for v in east.data.vertices:
        if v.co.z>10:
            t=(v.co.z-10)/43
            v.co.x=180+(v.co.x-180)*(1.30-.30*t)
            v.co.y=-94+(v.co.y+94)*(1.30-.30*t)
# Wind-eroded stones at the shoreline and on the moor.
for i in range(90):
    a=rng.uniform(math.pi,math.tau)
    x=-7+125*math.copysign(abs(math.cos(a))**.84,math.cos(a))
    y=20+115*math.sin(a)
    z=rng.uniform(-.3,1.0);scale=rng.uniform(1.3,6.0)
    crag_block('Shore • broken schist boulder %03d'%i,(x,y,z),(scale*1.8,scale,scale*.85),3000+i,rng.random()*math.tau)
# Paths are continuous ribbons conforming to the terrain, joining the viaduct landing.
M['path']=mat('Paths • wet ochre gravel',(.13,.105,.072),.9)
path_pts=[(180,-94),(209,-65),(223,-26),(251,1),(259,45),(290,71),(336,82),(360,137),(404,190),(469,216)]
v=[];f=[]
for k in range(len(path_pts)-1):
    p,q=Vector(path_pts[k]),Vector(path_pts[k+1]);d=q-p;perp=Vector((-d.y,d.x)).normalized()
    for j in range(10):
        t=j/10;c=p+d*t
        for side in [-1,1]:
            xy=c+perp*(2.35*side);z=terrain_h(xy.x,xy.y)+.065
            # A short stone ramp drops from the gate crag to the winding moor track.
            if k==0:z=max(z,54-(54-terrain_h(q.x,q.y))*t)
            v.append((xy.x,xy.y,z))
for i in range(len(v)//2-1):f.append((2*i,2*i+1,2*i+3,2*i+2))
mesh('Moor • winding carriage road',v,f,'path','Terrain')
# Conifer prototypes: broken branch tiers and individual needle fans.
M['bark']=mat('Forest • Scots pine bark',(.087,.052,.034),.92)
needle_mats=[]
for i,col in enumerate([(.020,.060,.045),(.032,.083,.055),(.038,.10,.067),(.052,.117,.073),(.069,.132,.083)]):
    ma=mat('Forest • needles tone '+str(i),col,.83);needle_mats.append(ma)
tree_meshes=[]
for variant in range(10):
    rnd=random.Random(8000+variant);g=Geo();height=rnd.uniform(10.5,17.5);baseR=height*rnd.uniform(.16,.20)
    g.tube([(0,0,0),(.05,0,height*.75),(.12,0,height)],height*.018,'bark',8)
    for lev in range(13):
        t=.17+lev*.061;zz=height*t;rad=baseR*(1-t)**.80
        arms=rnd.choice([6,7,8])
        for j in range(arms):
            a=j*math.tau/arms+lev*.82+rnd.uniform(-.12,.12);length=rad*rnd.uniform(.75,1.12)
            # Bowed branches, followed by serrated horizontal needle fans.
            endpoint=(length*math.cos(a),length*math.sin(a),zz-height*.026)
            g.tube([(0,0,zz),(endpoint[0]*.58,endpoint[1]*.58,zz+.04),endpoint],.022,'bark',5)
            for fidx in range(4):
                ft=.24+fidx*.19;cx=endpoint[0]*ft;cy=endpoint[1]*ft;cz=zz-height*.021*ft
                span=length*(.33-.20*ft);fw=length*.22
                # A pair of bent serrated needle fronds on each branch.
                for side in [-1,1]:
                    perp=Vector((-math.sin(a),math.cos(a),0))
                    forward=Vector((math.cos(a),math.sin(a),0))
                    root=Vector((cx,cy,cz));tip=root+perp*span*side+forward*fw
                    v=[tuple(root),tuple(root+forward*.24),tuple(tip+Vector((0,0,.10))),tuple(tip-forward*.19),tuple(root+Vector((0,0,-.12)))]
                    g.add(v,[(0,1,2),(0,2,3),(0,3,4),(0,4,1)],needle_mats[rnd.randrange(5)])
    g.tube([(.1,0,height*.78),(.1,0,height)],.025,needle_mats[2],6)
    o=g.create('Conifer • prototype %02d'%variant,'Nature');tree_meshes.append((o.data,height))
    bpy.data.objects.remove(o,do_unlink=True)
def distance_path(x,y):
    pt=Vector((x,y));best=100000
    for p,q in zip(path_pts[:-1],path_pts[1:]):
        p,q=Vector(p),Vector(q);d=q-p;t=max(0,min(1,(pt-p).dot(d)/d.dot(d)))
        best=min(best,(pt-(p+d*t)).length)
    return best
count=0;attempts=0
while count<4300 and attempts<30000:
    attempts+=1;x=rng.uniform(-750,900);y=rng.uniform(-280,810);z=terrain_h(x,y)
    if z<2.5 or z>125:continue
    if ((x+5)/149)**2+((y-18)/110)**2<1.25:continue
    if ((x-180)/47)**2+((y+94)/41)**2<1:continue
    if distance_path(x,y)<7:continue
    cluster=(noise(Vector((x*.014,y*.014,6)))+1)/2
    if rng.random()>.26+.71*cluster:continue
    data,baseh=tree_meshes[rng.randrange(10)]
    o=bpy.data.objects.new('Forest • conifer %04d'%count,data);C['Nature'].objects.link(o);o.location=(x,y,z-.2)
    size=rng.uniform(.65,1.35)*(1-min(.28,max(0,(z-65)/200)))
    o.scale=(size*rng.uniform(.87,1.08),size*rng.uniform(.87,1.08),size*rng.uniform(.90,1.14));o.rotation_euler.z=rng.random()*math.tau
    count+=1
# Forest edge on both sides of the crag, with low wind-pruned trees.
for i in range(55):
    a=rng.uniform(.0,math.pi);rr=rng.uniform(.79,.99)
    x=-7+107*math.copysign(abs(math.cos(a))**.84,math.cos(a))*rr;y=20+73*math.sin(a)*rr
    if -87<x<90 and -26<y<77:continue
    data,h=tree_meshes[rng.randrange(10)]
    o=bpy.data.objects.new('Castle grounds • wind-pruned pine %02d'%i,data);C['Nature'].objects.link(o);o.location=(x,y,64.5);o.scale=(.45,.45,.52);o.rotation_euler.z=rng.random()*math.tau
# Physical water surface: long swell geometry plus fine shader ripples in the material pass.
old=bpy.data.objects.get('Black Lake • wave surface')
if old:bpy.data.objects.remove(old,do_unlink=True)
def water_h(x,y):
    return .05*math.sin(x*.23+y*.15)+.022*math.sin(x*.51-y*.41)+.012*math.sin(y*.83+x*.37)
terrain('Black Lake • displaced wave surface',-3000,3000,-3000,2300,350,310,water_h,'water')
# Reframe the elevated view to include the complete skyline, bridge and water.
cam=bpy.data.objects['Cam_Aerial'];cam.location=(358,-392,318);cam.data.lens=41
cam.rotation_euler=(Vector((18,8,69))-cam.location).to_track_quat('-Z','Y').to_euler()
