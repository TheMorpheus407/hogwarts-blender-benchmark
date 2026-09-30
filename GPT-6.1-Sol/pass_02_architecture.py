
for o in list(bpy.data.objects):
    if o.name.startswith('Great Hall • test bay') or o.name=='Great Hall • blockout':bpy.data.objects.remove(o,do_unlink=True)
g=Geo()
g.box((-50,-15,66.5),(68,25,3),'stone')
g.box((-50,-15,80),(65,23,.55),'dark')
g.box((-50,-15,94.4),(65,23,.4),'wood')
for sy in [-1,1]:
    yy=-15+sy*12.5;ang=0 if sy<0 else math.pi
    for i in range(12):
        xx=-81.1667+i*5.6667
        gothic_wall_cell('Great Hall • '+('south' if sy<0 else 'north')+' bay %02d lower'%i,(xx,yy,68),5.6667,12,3.05,9.5,1.0,ang)
        gothic_wall_cell('Great Hall • '+('south' if sy<0 else 'north')+' bay %02d clerestory'%i,(xx,yy,80),5.6667,15,3.05,12.4,1.0,ang)
    for z in [68,80,94.4]:g.box((-50,yy+sy*.18,z),(69,1.9,.42),'trim')
    for i in range(13):
        xx=-84+i*5.6667
        for z,hh,dep in [(68,8,4.4),(76,9,3.5),(85,10.3,2.5)]:
            g.box((xx,yy+sy*(dep/2-.25),z+hh/2),(1.23,dep,hh),'stone')
            g.box((xx,yy+sy*(dep/2-.25),z+hh),(1.5,dep+.22,.35),'trim')
        pinnacle('Great Hall • pinnacle %02d %d'%(i,sy),xx,yy+sy*1.5,95.5,7.4,.48)
        for dd in [0,1]:g.box((xx+.55*dd,yy+sy*.50,66.8),(.45,1.2,1.2),'trim')
g.create('Great Hall • buttresses, bands and carved corbels')
for xx,ang in [(-84,-math.pi/2),(-16,math.pi/2)]:
    box('Great Hall • gable masonry',(xx,-15,82),(1.5,25,26),'stone',.06)
    v=[(xx-.75,-27.5,95),(xx-.75,-2.5,95),(xx-.75,-15,116),(xx+.75,-27.5,95),(xx+.75,-2.5,95),(xx+.75,-15,116)]
    mesh('Great Hall • gable pediment',v,[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)],'stone')
    for yy in [-23,-15,-7]:window('Great Hall • end lancet',(xx+(.80 if xx>-50 else -.80),yy,72),2.65,16,ang,3)
    # Round rose composed of direct mesh tracery, oriented toward the gable.
    ro=Geo()
    prof=[(3*math.cos(i*math.tau/64),3*math.sin(i*math.tau/64)) for i in range(64)]
    ro.poly(prof,-.05,.10,'window')
    for rr,th in [(3.14,.16),(2.85,.065),(1.0,.065)]:
        ro.tube([(rr*math.cos(i*math.tau/64),-.16,rr*math.sin(i*math.tau/64)) for i in range(64)],th,'trim',8,True)
    for i in range(12):
        a=i*math.tau/12
        ro.tube([(math.cos(a),-.14,math.sin(a)),(math.cos(a)*2.85,-.14,math.sin(a)*2.85)],.055,'trim',6)
        cc=(math.cos(a)*1.96,math.sin(a)*1.96)
        ro.tube([(cc[0]+.47*math.cos(t*math.tau/24),-.15,cc[1]+.47*math.sin(t*math.tau/24)) for t in range(24)],.048,'trim',6,True)
    ob=ro.create('Great Hall • wheel rose tracery');ob.location=(xx+(.82 if xx>-50 else -.82),-15,101);ob.rotation_euler.z=ang
beam('Great Hall • lead ridge',(-85,-15,117.15),(-15,-15,117.15),.27,'bronze')
for i in range(10):
    xx=-79+i*6.2
    for sy in [-1,1]:
        yy=-15+sy*6.6;zz=95+22*(1-6.6/13.5)
        box('Great Hall • stone dormer',(xx,yy,zz+.85),(1.55,1.1,2.1),'stone')
        gable('Great Hall • dormer slate',xx,yy,zz+1.9,1.75,1.55,1.6)
        window('Great Hall • dormer lancet',(xx,yy+sy*.57,zz+.2),.75,1.4,0 if sy<0 else math.pi,1)
for i in range(8):
    xx=-79+i*8.3
    beam('Great Hall • flying buttress',(xx,-1,91),(xx,7,82),.65,'stone')
    beam('Great Hall • flying buttress coping',(xx,-1,92),(xx,7,83),.23,'trim')
    box('Great Hall • flying buttress pier',(xx,7,76),(1.5,1.9,14),'stone',.06)
    pinnacle('Great Hall • flying buttress finial',xx,7,83,6,.35)


if bpy.data.objects.get('Upper courtyard • foundation'):
    bpy.data.objects.remove(bpy.data.objects['Upper courtyard • foundation'],do_unlink=True)
g=Geo()
g.box((0,6,64.9),(110,72,1.6),'stone')
for sy in [-1,1]:
    yy=6+sy*36
    g.box((1,yy,61.5),(110,2.5,8),'stone')
    g.box((1,yy,67.5),(110,1.25,2.3),'stone')
    g.box((1,yy,68.8),(111,1.8,.30),'trim')
    for i in range(47):
        xx=-52+i*2.30
        g.box((xx,yy,69.4),(1.16,1.5,1.0),'stone')
        g.box((xx,yy+sy*.3,64.7),(.65,1.35,.9),'trim')
g.create('Courtyards • retaining walls, crenels and machicolations')
for i in range(16):
    xx=-12+i*4.32
    gothic_wall_cell('Lake gallery • bay %02d'%i,(xx,-35,64.1),4.32,9.5,2.70,6.5,1.0,0,.9)
g=Geo();g.box((20,-33.6,74),(73,4.1,.8),'stone')
for i in range(35):g.box((-15+i*2.1,-35,75),(.95,1.15,1.1),'trim')
g.create('Lake gallery • paved battlement walk')
turret('South court watchtower',-71,-44,54,4.6,26,13,'copper')
turret('Southeast sentinel',62,-33,51,5.2,27,18)
turret('Ravenclaw needle',18,24,91,2.3,23,31)
turret('East staircase tower',71,44,61,4.6,29,19,'copper')
turret('Northwest octagonal library tower',-56,56,65,5.4,27,23,n=8)
turret('North cloister lantern',-29,69,65,3.5,23,16,'copper',n=8)
for prefix,x,y,L,W,zbase,hh in [
    ('Transfiguration wing',39,-2,40,22,64,28),
    ('Library wing',-23,41,64,18,65,28),
    ('East library',27,58,58,17,65,22)]:
    g=Geo()
    for sy in [-1,1]:
        yy=y+sy*W/2
        for i in range(int(L/5)):
            xx=x-L/2+2.5+i*5
            for level in range(2):
                window(prefix+' • carved lancet',(xx,yy+sy*.32,zbase+3+level*10),2.2,7.4,0 if sy<0 else math.pi,2)
            for j in range(3):
                g.box((xx+2.5,yy+sy*.8,zbase+5+j*8),(1.0,2.0-j*.45,10-j*.5),'stone')
            pinnacle(prefix+' • ridge pinnacle',xx+2.5,yy+sy*.35,zbase+hh,4.8,.3)
        for z in [zbase+1,zbase+12,zbase+hh-.5]:g.box((x,yy+sy*.2,z),(L+1,1.25,.3),'trim')
    for sx in [-1,1]:
        for yy in [y-W*.28,y+W*.28]:
            window(prefix+' • end window',(x+sx*(L/2+.32),yy,zbase+6),2.4,10,math.pi/2 if sx>0 else -math.pi/2,2)
    g.create(prefix+' • carved bands and buttresses')
towers=[
('Grand Tower',-13,8,65,12,62,48),
('Astronomy Tower',64,8,63,7,50,36),
('North library tower',1,51,65,7,39,25),
('West cloister turret',-76,25,65,4.7,24,19),
('South court watchtower',-71,-44,54,4.6,26,13),
('Southeast sentinel',62,-33,51,5.2,27,18),
('East staircase tower',71,44,61,4.6,29,19),
('Northwest octagonal library tower',-56,56,65,5.4,27,23),
('North cloister lantern',-29,69,65,3.5,23,16),
('Ravenclaw needle',18,24,91,2.3,23,31),
('Clock tower • northeast turret',51,40,96,3.6,34,31),
('Clock tower • southwest turret',31,18,91,3.3,30,29)]
for ti,(name,x,y,zb,r,hh,rh) in enumerate(towers):
    floors=max(2,int(hh/8.7));count=max(7,int(r*1.10))
    for lev in range(floors):
        zz=zb+3+lev*(hh-7)/floors
        for i in range(count):
            aa=i*math.tau/count+(ti%4)*.12
            ww=1.15 if r>4 else .73;wh=4.2 if r>9 else 3.8 if r>4 else 2.5
            window(name+' • room %02d.%02d'%(lev,i),(x+(r+.36)*math.cos(aa),y+(r+.36)*math.sin(aa),zz),ww,wh,aa+math.pi/2,1 if r<4 else 2)
    for zz in [zb+2.0,zb+hh*.50,zb+hh-3.8]:ring(name+' • sandstone string course',x,y,zz,r+.25,.31,.36,'trim',n=64)
    ring(name+' • projecting machicolation crown',x,y,zb+hh-2,r+.63,.5,1.1,'stone',n=64)
    gg=Geo();nc=int(r*5)
    for i in range(nc):
        aa=i*math.tau/nc;cx=x+(r+.30)*math.cos(aa);cy=y+(r+.30)*math.sin(aa)
        gg.box((cx,cy,zb+hh-2.9),(.39,.39,1.15),'trim')
    gg.create(name+' • sculpted corbel row')
    if r>6:
        for lev in range(3 if r>10 else 2):
            zz=zb+hh+6+lev*9;rr=(r+.65)*(1-(zz-(zb+hh))/rh);n=max(5,int(rr*2.2))
            for i in range(n):
                aa=i*math.tau/n+(lev%2)*.12
                window(name+' • spire dormer',(x+(rr+.28)*math.cos(aa),y+(rr+.28)*math.sin(aa),zz),.78,1.6,aa+math.pi/2,1)
gg=Geo()
for sy in [-1,1]:
    yy=30+sy*11.5
    for xx in [33,41,49]:
        window('Clock Tower • choir lancet',(xx,yy+sy*.34,71),2.8,11,0 if sy<0 else math.pi,3)
        window('Clock Tower • upper lancet',(xx,yy+sy*.34,86),2.35,9.5,0 if sy<0 else math.pi,2)
    for xx in [30.5,36.3,45.7,51.5]:
        gg.box((xx,yy+sy*.8,89),(1.0,2.6,46),'stone')
        pinnacle('Clock Tower • crocketed pinnacle',xx,yy+sy*.6,114,7,.4)
    for z in [69,84,99,113]:gg.box((41,yy+sy*.10,z),(23,1.4,.45),'trim')
gg.create('Clock Tower • stepped Gothic buttresses')
M['gold']=mat('Clock • gilded bronze',(.62,.40,.095),.27,.78)
p=M['gold'].node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(.5,.24,.04,1);p.inputs['Emission Strength'].default_value=.35
def clock_dial(name,loc,angle):
    g=Geo()
    prof=[(4.5*math.cos(i*math.tau/96),4.5*math.sin(i*math.tau/96)) for i in range(96)]
    g.poly(prof,-.10,.12,'dark')
    for rr,tt in [(4.82,.17),(4.5,.055),(4.12,.030),(3.61,.035)]:
        g.tube([(rr*math.cos(i*math.tau/96),-.22,rr*math.sin(i*math.tau/96)) for i in range(96)],tt,'gold',8,True)
    for i in range(60):
        a=i*math.tau/60;rr=4.04;ll=.24 if i%5==0 else .11
        g.tube([(rr*math.sin(a),-.25,rr*math.cos(a)),((rr-ll)*math.sin(a),-.25,(rr-ll)*math.cos(a))],.046 if i%5==0 else .026,'gold',6)
    for a,ll,ww in [(math.radians(60),3.48,.14),(-math.radians(60),2.45,.20)]:
        g.tube([(0,-.31,0),(ll*math.sin(a),-.31,ll*math.cos(a))],ww/2,'gold',8)
    g.tube([(0,-.34,-.04),(0,-.34,.04)],.20,'gold',16)
    ob=g.create(name+' • clock mechanism');ob.location=loc;ob.rotation_euler.z=angle
    ca,sa=math.cos(angle),math.sin(angle);romans=['XII','I','II','III','IV','V','VI','VII','VIII','IX','X','XI']
    for i,roman in enumerate(romans):
        a=i*math.tau/12;xx=3.36*math.sin(a);zz=3.36*math.cos(a)
        cu=bpy.data.curves.new(name+' • numeral '+roman,'FONT');cu.body=roman;cu.size=.68;cu.align_x='CENTER';cu.align_y='CENTER';cu.extrude=.012;cu.bevel_depth=.003
        o=bpy.data.objects.new(name+' • Roman '+roman,cu);C['Castle'].objects.link(o);cu.materials.append(M['gold'])
        o.location=(loc[0]+xx*ca+.30*sa,loc[1]+xx*sa-.30*ca,loc[2]+zz);o.rotation_euler=(math.pi/2,0,angle)
clock_dial('South clock',(41,18.05,105),0)
clock_dial('East clock',(52.95,30,105),math.pi/2)
for x,y,z in [(-21,15,139),(-5,13,127),(18,24,114)]:
    for i in range(5):
        aa=math.tau*i/5;pinnacle('Attendant spire • stone crown',x+1.9*math.cos(aa),y+1.9*math.sin(aa),z-1,3.8,.22)
for o in bpy.data.objects:
    if o.name.startswith('Great Hall • end lancet'):o.location.x+=.2 if o.location.x>-50 else -.2


# Grand viaduct: twelve structural arches with wedge-shaped voussoirs.
start=Vector((55,-24));end=Vector((180,-94));d=end-start;length=d.length
a=math.atan2(d.y,d.x);ca,sa=math.cos(a),math.sin(a)
N=12;bay=length/N;opening=bay-2.05;r=opening/2
def deckz(u):return 65-11*u/length
g=Geo();wedges=Geo()
for i in range(N):
    u=(i+.5)*bay;top=deckz(u)-.9;spring=top-r-.8
    upper=[(u+r*math.cos(t*math.pi/24),spring+r*math.sin(t*math.pi/24)) for t in range(25)]
    profile=upper+[(u-bay/2,spring),(u-bay/2,deckz(u-bay/2)-.4),(u+bay/2,deckz(u+bay/2)-.4),(u+bay/2,spring)]
    g.poly(profile,-3.45,3.45,'stone')
    for sy in [-1,1]:
        for j in range(22):
            aa=j*math.pi/22+.009;bb=(j+1)*math.pi/22-.009
            prof=[(u+r*math.cos(aa),spring+r*math.sin(aa)),(u+r*math.cos(bb),spring+r*math.sin(bb)),(u+(r+.58)*math.cos(bb),spring+(r+.58)*math.sin(bb)),(u+(r+.58)*math.cos(aa),spring+(r+.58)*math.sin(aa))]
            dd=sy*3.51
            wedges.poly(prof,dd-.16,dd+.16,'trim' if j%4 else 'stone')
for i in range(N+1):
    u=i*bay;zz=deckz(u)-r-1.4
    ww=2.10;wb=3.3;dep=7.0;bottom=1.0
    v=[(u-wb/2,-dep/2,bottom),(u+wb/2,-dep/2,bottom),(u+wb/2,dep/2,bottom),(u-wb/2,dep/2,bottom),
       (u-ww/2,-3.45,zz),(u+ww/2,-3.45,zz),(u+ww/2,3.45,zz),(u-ww/2,3.45,zz)]
    g.add(v,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],'stone')
    g.box((u,0,1.3),(4.6,8.5,2.0),'rock')
    for z in [4,17,32,zz-.4]:g.box((u,0,z),(2.7,7.4,.4),'trim')
    # Pointed cutwaters break up the tall piers.
    for sy in [-1,1]:
        cut=[(u-.95,sy*3.3,2),(u+.95,sy*3.3,2),(u,sy*5.0,2),(u-.60,sy*3.3,20),(u+.60,sy*3.3,20),(u,sy*4.3,20)]
        g.add(cut,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],'stone')
for sy in [-1,1]:
    for i in range(N):
        u=(i+.5)*bay
        # Sloping parapets formed from extruded profiles.
        profile=[(i*bay,deckz(i*bay)),((i+1)*bay,deckz((i+1)*bay)),((i+1)*bay,deckz((i+1)*bay)+1.55),(i*bay,deckz(i*bay)+1.55)]
        dd=sy*3.65;g.poly(profile,dd-.38,dd+.38,'stone')
        cap=[(x,z+1.55) for x,z in [(i*bay,deckz(i*bay)),((i+1)*bay,deckz((i+1)*bay))]]
        g.poly([(cap[0][0],cap[0][1]),(cap[1][0],cap[1][1]),(cap[1][0],cap[1][1]+.22),(cap[0][0],cap[0][1]+.22)],dd-.52,dd+.52,'trim')
for name,gg in [('Grand viaduct • piers, vaults and parapets',g),('Grand viaduct • carved radial voussoirs',wedges)]:
    ob=gg.create(name);ob.location=(start.x,start.y,0);ob.rotation_euler.z=a
road=Geo();road.poly([(0,63.85),(length,52.85),(length,54),(0,65)],-3.45,3.45,'stone')
ob=road.create('Grand viaduct • sloping stone carriageway');ob.location=(start.x,start.y,0);ob.rotation_euler.z=a
for i in range(N+1):
    u=i*bay
    for sy in [-1,1]:
        xx=start.x+u*ca-sy*3.62*sa;yy=start.y+u*sa+sy*3.62*ca
        lantern('Viaduct • lantern %02d %d'%(i,sy),xx,yy,deckz(u)+1.72,.78,i%2==0)
gothic_wall_cell('Gatehouse • great pointed portal',(55,-24,65),12,13,5.4,10.3,0,a+math.pi/2,2.8)
for offset in [-5.1,5.1]:
    xx=55-offset*sa;yy=-24+offset*ca
    turret('Gatehouse • flanking needle',xx,yy,65,1.5,15,10)
    lantern('Gatehouse • amber sconce',xx+ca*1.9,yy+sa*1.9,68,.90)
# Clock face lifted into the stone gable for skyline readability.
for yy in [18.4,41.6]:
    v=[(30,yy-.65,114),(52,yy-.65,114),(41,yy-.65,139),(30,yy+.65,114),(52,yy+.65,114),(41,yy+.65,139)]
    mesh('Clock Tower • pointed sandstone gable',v,[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)],'stone')
for o in bpy.data.objects:
    if o.name.startswith('South clock'):o.location.z+=20
# Longer switchback stair from the waterline to the lake gallery.
stair_pts=[(23,-101,2.1),(32,-79,11),(-19,-66,27),(23,-51,43),(-18,-39,58),(-12,-33,65)]
stair=Geo();coping=Geo()
for k,(p,q) in enumerate(zip(stair_pts[:-1],stair_pts[1:])):
    p,q=Vector(p),Vector(q);vec=q-p;horizontal=math.hypot(vec.x,vec.y);ux,uy=vec.x/horizontal,vec.y/horizontal
    nx,ny=-uy,ux;width=3.25;steps=max(8,int((q.z-p.z)/.19));rise=(q.z-p.z)/steps;run=horizontal/steps
    for j in range(steps):
        t=(j+.5)/steps;cx=p.x+vec.x*t;cy=p.y+vec.y*t;zz=p.z+rise*(j+1)
        # Steps are actual horizontal treads with a continuous supporting masonry web.
        half=run*.51
        corners=[(cx-ux*half-nx*width/2,cy-uy*half-ny*width/2,zz-.30),(cx+ux*half-nx*width/2,cy+uy*half-ny*width/2,zz-.30),(cx+ux*half+nx*width/2,cy+uy*half+ny*width/2,zz-.30),(cx-ux*half+nx*width/2,cy-uy*half+ny*width/2,zz-.30)]
        v=corners+[(x,y,zz) for x,y,_ in corners];stair.add(v,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],'trim')
    # Thick wall beneath stairs, cut to the slope and embedded into the cliff.
    v=[(p.x-nx*width/2,p.y-ny*width/2,p.z-4),(p.x+nx*width/2,p.y+ny*width/2,p.z-4),(q.x+nx*width/2,q.y+ny*width/2,q.z-4),(q.x-nx*width/2,q.y-ny*width/2,q.z-4),
       (p.x-nx*width/2,p.y-ny*width/2,p.z),(p.x+nx*width/2,p.y+ny*width/2,p.z),(q.x+nx*width/2,q.y+ny*width/2,q.z),(q.x-nx*width/2,q.y-ny*width/2,q.z)]
    stair.add(v,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],'stone')
    for side in [-1,1]:
        pp=p+Vector((nx*side*(width/2+.12),ny*side*(width/2+.12),0))
        qq=q+Vector((nx*side*(width/2+.12),ny*side*(width/2+.12),0))
        # Continuous knee-high masonry parapet with coping.
        widthrail=.33
        vv=[]
        for endpoint in [pp,qq]:
            vv += [tuple(endpoint+Vector((nx*s*widthrail,ny*s*widthrail,z))) for z in [0,1.05] for s in [-1,1]]
        stair.add(vv,[(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5),(0,2,3,1),(4,5,7,6)],'stone')
        coping.tube([pp+Vector((0,0,1.1)),qq+Vector((0,0,1.1))],.15,'trim',8)
    for t in [0,.33,.67]:
        pos=p+vec*t+Vector((nx*(width/2+.12),ny*(width/2+.12),1.08))
        lantern('Cliff stair • lantern %d %.2f'%(k,t),*pos,.72,k%2==0)
    if k<len(stair_pts)-2:
        stair.box(tuple(q-Vector((0,0,.20))),(5.5,5.3,.4),'trim')
stair.create('Boathouse stair • 330 carved stone treads and retaining walls')
coping.create('Boathouse stair • continuous worn coping')
# The boathouse has three real open launch portals.
bpy.data.objects.remove(bpy.data.objects['Boathouse • blockout'],do_unlink=True)
for i in range(3):
    xx=14-22/2+(i+.5)*22/3
    # Arch spandrel and jambs, kept open rather than glazed.
    g=Geo();w=5.8;h=8.4;bottom=.10;spring=h-w*.8660254+bottom
    profile=[(x,z+bottom) for x,z in gothic(w,h)[2:]]+[(-22/6,spring),(-22/6,9),(22/6,9),(22/6,spring)]
    g.poly(profile,0,1.35,'stone')
    for x in [-(22/3+w)/4,(22/3+w)/4]:g.box((x,.65,spring/2),((22/3-w)/2,1.3,spring),'stone')
    g.tube([(x,-.16,z+.1) for x,z in gothic(w+.15,h+.12)],.20,'trim',8)
    o=g.create('Boathouse • launch arch '+str(i+1));o.location=(xx,-105.5,2)
    # Dark oak rafters and a warm interior lamp.
    beam('Boathouse • oak header',(xx-3,-103.8,10.4),(xx+3,-103.8,10.4),.35,'wood')
    light('Boathouse • interior amber '+str(i),(xx,-99,8.5),120,(1,.45,.17),.8,'POINT')
g=Geo()
g.box((14,-89.15,6.5),(22,1.5,9),'stone')
g.box((2.25,-97,6.5),(1.5,17,9),'stone')
g.box((25.75,-97,6.5),(1.5,17,9),'stone')
g.box((14,-106.4,1),(26,4.8,1.4),'stone')
g.box((14,-89,1.5),(26,3.5,2.4),'stone')
g.create('Boathouse • buttressed walls and waterline apron')
for xx,aa in [(1.44,-math.pi/2),(26.56,math.pi/2)]:
    for yy in [-101,-95,-90]:
        window('Boathouse • amber side lancet',(xx,yy,4),1.4,4.0,aa,2)
for xx in [2.8,25.2]:
    turret('Boathouse • gable turret',xx,-96.7,8,1.0,6.5,6.0,'copper',n=16)
for yy in [-105.8,-88.2]:
    for xx in [2.4,9.6,17.1,25.3]:
        box('Boathouse • battered buttress',(xx,yy,5.5),(1.3,2.5,7),'stone',.06)
        box('Boathouse • limestone buttress cap',(xx,yy,9),(1.55,2.85,.35),'trim',.03)
# Stone and timber jetty.
jetty=Geo();jetty.box((14,-119.5,.60),(3.5,24,.32),'wood')
for i in range(55):jetty.box((14,-108+i*(-23/54),.83),(3.6,.35,.11),'wood')
for yy in [-108,-113,-118,-123,-130]:
    for xx in [12.3,15.7]:
        jetty.tube([(xx,yy,-2),(xx,yy,1.25)],.14,'wood',10)
        jetty.box((xx,yy,1.35),(.42,.42,.13),'wood')
jetty.create('Boathouse • plank landing and oak pilings')
for xx,yy in [(12.2,-110),(15.8,-126),(2.7,-106),(26,-106)]:
    lantern('Boathouse • waterside lantern',xx,yy,1.05,.70,True)
def boat(name,x,y,angle):
    gg=Geo();L=4.9;W=1.55
    # Open clinker hull, curved in plan and rising at bow and stern.
    v=[]
    for j in range(5):
        t=j/4;zz=-.24+t*.67;wscale=.22+.78*math.sin(t*math.pi/2)
        for i in range(28):
            a=i*math.tau/28
            xx=L/2*math.cos(a);yy=W/2*math.sin(a)*wscale
            v.append((xx,yy,zz+.28*abs(math.cos(a))**5))
    f=[]
    for j in range(4):
        for i in range(28):f.append((j*28+i,j*28+(i+1)%28,(j+1)*28+(i+1)%28,(j+1)*28+i))
    gg.add(v,f,'wood')
    for j in range(5):
        pts=[(L/2*math.cos(i*math.tau/28),W/2*math.sin(i*math.tau/28)*(.22+.78*math.sin(j/4*math.pi/2)),-.24+j/4*.67+.28*abs(math.cos(i*math.tau/28))**5) for i in range(28)]
        gg.tube(pts,.025,'bronze',5,True)
    for xx in [-1.0,0,1]:gg.box((xx,0,.22),(.24,1.20,.09),'wood')
    gg.tube([(-1.65,-.48,.40),(1.1,.60,.44)],.045,'wood',8)
    ob=gg.create(name);ob.location=(x,y,.30);ob.rotation_euler.z=angle
boat('Black Lake • moored rowing boat 1',8,-112,.15)
boat('Black Lake • moored rowing boat 2',21,-110,-.13)
boat('Black Lake • launch boat',14,-99,math.pi/2)
# Recess the central shore into a lake inlet.
oldh=terrain_h
def terrain_h(x,y):
    base=oldh(x,y)
    mouth=60*math.exp(-((x-4)/140)**4-((y+57)/143)**4)
    fore=45/(1+math.exp((y+105)/25))
    return base-mouth-fore
ob=bpy.data.objects['Moorland • northern slopes']
for v in ob.data.vertices:
    x,y,z=v.co;v.co.z=terrain_h(x,y)
ob.data.update()


# Lower east terrace: three framed glass conservatories and growing beds.
M['greenhouse_glass']=mat('Glass • conservatory green reflection',(.12,.23,.20),.12)
p=M['greenhouse_glass'].node_tree.nodes.get('Principled BSDF');p.inputs['Transmission Weight'].default_value=.90;p.inputs['IOR'].default_value=1.46
M['leaves']=mat('Vegetation • garden leaves',(.07,.14,.048),.72)
box('Conservatory terrace • retaining foundation',(79,53,53),(35,24,6),'stone',.12)
box('Conservatory terrace • flagstone walk',(79,53,56.1),(36,25,.40),'trim',.03)
rock_radial('Conservatory terrace • lower outcrop',76,50,31,27,51,141)
for i in range(3):
    x=68+i*10.2;y=53;L=18.0;W=7.8;zb=56.35;wallh=3.5;rise=3.2
    g=Geo();fr=Geo()
    # Ridge runs along Y; glazed walls and pitched panes are separate panels.
    for sy in [-1,1]:
        yy=y+sy*L/2
        g.add([(x-W/2,yy,zb),(x+W/2,yy,zb),(x+W/2,yy,zb+wallh),(x,yy,zb+wallh+rise),(x-W/2,yy,zb+wallh)],[(0,1,2,3,4)],'greenhouse_glass')
        fr.tube([(x-W/2,yy,zb),(x-W/2,yy,zb+wallh),(x,yy,zb+wallh+rise),(x+W/2,yy,zb+wallh),(x+W/2,yy,zb)],.085,'bronze',8)
        for xx in [x-W/4,x,x+W/4]:fr.tube([(xx,yy,zb),(xx,yy,zb+wallh+rise*(1-abs(xx-x)/(W/2)))],.054,'bronze',6)
    for side in [-1,1]:
        xx=x+side*W/2
        g.add([(xx,y-L/2,zb),(xx,y+L/2,zb),(xx,y+L/2,zb+wallh),(xx,y-L/2,zb+wallh)],[(0,1,2,3)],'greenhouse_glass')
        g.add([(xx,y-L/2,zb+wallh),(xx,y+L/2,zb+wallh),(x,y+L/2,zb+wallh+rise),(x,y-L/2,zb+wallh+rise)],[(0,1,2,3)],'greenhouse_glass')
        for j in range(10):
            yy=y-L/2+j*L/9
            fr.tube([(xx,yy,zb),(xx,yy,zb+wallh),(x,yy,zb+wallh+rise)],.075,'bronze',8)
        for z in [zb+.3,zb+1.8,zb+wallh]:fr.tube([(xx,y-L/2,z),(xx,y+L/2,z)],.065,'bronze',6)
        for fraction in [.33,.66]:
            xx2=x+side*W/2*fraction;zz=zb+wallh+rise*(1-fraction)
            fr.tube([(xx2,y-L/2,zz),(xx2,y+L/2,zz)],.062,'bronze',6)
    fr.tube([(x,y-L/2,zb+wallh+rise),(x,y+L/2,zb+wallh+rise)],.11,'bronze',8)
    g.create('Greenhouse %d • transparent panes'%(i+1));fr.create('Greenhouse %d • complete iron frame'%(i+1))
    bed=Geo()
    for j in range(2):
        xx=x+(-1 if j==0 else 1)*2
        bed.box((xx,y,zb+.35),(2.6,14,.65),'wood')
        for k in range(35):
            px=xx+rng.uniform(-1,1);py=y+rng.uniform(-6.5,6.5);hz=rng.uniform(.30,.85)
            bed.tube([(px,py,zb+.65),(px+.1,py,zb+.65+hz)],.025,'wood',5)
            for q in range(4):
                aa=rng.random()*math.tau
                bed.add([(px,py,zb+.65+hz*.65),(px+.38*math.cos(aa),py+.38*math.sin(aa),zb+.65+hz*.92),(px+.19*math.cos(aa+.6),py+.19*math.sin(aa+.6),zb+.65+hz*.65)],[(0,1,2)],'leaves')
    bed.create('Greenhouse %d • inhabited potting beds'%(i+1))
    light('Greenhouse %d • soft amber interior'%(i+1),(x,y,zb+2),180,(1,.60,.28),2,'POINT')
for x,y in [(61,41),(93,41),(62,64),(94,64)]:lantern('Conservatory terrace • lantern',x,y,56.4,.8)
# Slate is modeled as individually staggered courses, then shaded procedurally.
slate_mats=[]
for i in range(7):
    tone=.82+i*.045
    ma=mat('Slate • course tone %02d'%i,(.048*tone,.071*tone,.090*tone),.63)
    slate_mats.append(ma)
def slate_gable(name,x,y,z,L,W,rise):
    g=Geo();slant=math.hypot(W/2,rise);rows=int(slant/.62);columns=int(L/.56)
    for sy in [-1,1]:
        for j in range(rows):
            t0=j/rows;t1=(j+1)/rows+.012;offset=(j%2)*.5
            for i in range(columns+1):
                x0=x-L/2+(i-offset)*L/columns+.012;x1=min(x+L/2,x0+L/columns-.024)
                x0=max(x-L/2,x0)
                if x1<=x0:continue
                y0=y+sy*W/2*(1-t0);y1=y+sy*W/2*(1-min(.999,t1))
                z0=z+rise*t0+.045;z1=z+rise*min(.999,t1)+.060
                v=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z1),(x0,y1,z1)]
                g.add(v,[(0,1,2,3)],slate_mats[rng.randrange(len(slate_mats))])
    return g.create(name+' • staggered slate tiles')
for params in [
    ('Great Hall',-50,-15,95,70,27,22),
    ('Library',-23,41,93,66,20,15),
    ('Transfiguration',39,-2,92,42,24,18),
    ('East library',27,58,87,60,19,14),
    ('Clock saddle',41,30,114,24,25,26),
    ('Boathouse',14,-97,11,24,19,11)]:
    slate_gable(*params)
def slate_cone(name,x,y,z,r,h):
    g=Geo();rows=max(5,int(h/.72))
    for j in range(rows):
        t0=j/rows;t1=min(.999,(j+1)/rows+.008)
        rr=r*(1-t0);rr1=r*(1-t1);n=max(6,int(math.tau*rr/.62))
        for i in range(n):
            offset=(j%2)*.5;a=(i+offset)*math.tau/n+.002;b=(i+1+offset)*math.tau/n-.002
            v=[(x+(rr+.048)*math.cos(a),y+(rr+.048)*math.sin(a),z+h*t0+.020),
               (x+(rr+.048)*math.cos(b),y+(rr+.048)*math.sin(b),z+h*t0+.020),
               (x+(rr1+.060)*math.cos(b),y+(rr1+.060)*math.sin(b),z+h*t1+.018),
               (x+(rr1+.060)*math.cos(a),y+(rr1+.060)*math.sin(a),z+h*t1+.018)]
            g.add(v,[(0,1,2,3)],slate_mats[rng.randrange(len(slate_mats))])
    return g.create(name+' • circular slate courses')
for name,x,y,zb,r,hh,rh in towers:
    roofob=bpy.data.objects.get(name+' • spire')
    if roofob and roofob.data.materials[0] != M['copper']:slate_cone(name,x,y,zb+hh,r+.65,rh)
# Needle finials have crossbars, spheres and weather vanes.
for name,x,y,zb,r,hh,rh in towers:
    z=zb+hh+rh
    beam(name+' • finial crossbar',(x-.38,y,z+.82),(x+.38,y,z+.82),.06,'bronze')
    cyl(name+' • gold finial collar',x,y,z+.22,.17,.25,'gold',n=16,r2=.06)
