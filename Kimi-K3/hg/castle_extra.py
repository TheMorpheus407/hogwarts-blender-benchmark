import bpy, math, random
from mathutils import Vector, Euler
from math import sin, cos, pi, hypot

C  = bpy.data.collections["Castle"]
CW = bpy.data.collections["Castle_Windows"]
B  = bpy.data.collections["Bridge"]
P  = bpy.data.collections["Props"]
T  = bpy.data.collections["Terrain"]

stone  = mat_stone()
stoned = mat_stone_dark()
slate  = mat_slate()
metal  = mat_metal()
wood   = mat_wood()
glassgh = mat_glass_greenhouse()

g_dark  = mat_glass_dark()
g_l1 = bpy.data.materials["GlassWarm1"]
g_l2 = bpy.data.materials["GlassWarm2"]
g_l3 = bpy.data.materials["GlassWarm3"]
g_l4 = bpy.data.materials["GlassWarm4"]
WINMATS = [g_dark, g_l1, g_l2, g_l3, g_l4]

ZB = 52.0

# ============================================================ GATEHOUSE
gh_x, gh_y = 95.0, -8.0
axis = math.atan2(20.0-(-8.0), 300.0-95.0)   # bridge heading
perp = axis + pi/2
for sgn in (-1, 1):
    tx = gh_x + 7.5*cos(perp)*sgn
    ty = gh_y + 7.5*sin(perp)*sgn
    tower(f"Gate_drum_{sgn}", tx, ty, ZB-4, 5.0, 24, C, stone, slate, spire_h=13, corbel=True)
# gate block + arch
ob = box_obj("Gatehouse_Block", (gh_x, gh_y, ZB+6), (16, 12, 20), C, stone)
ob.rotation_euler[2] = axis
arch_frame("Gate_ArchFrame", 5.5, 9.0, 6.0, 1.0, 3.0, C, stone,
           loc=(gh_x - 8.3*cos(axis), gh_y - 8.3*sin(axis), ZB+5), rot=Euler((0,0,axis),'XYZ'))
arch_panel("Gate_Dark", 5.5, 9.0, 6.0, 0.3, C, g_dark,
           loc=(gh_x - 8.3*cos(axis), gh_y - 8.3*sin(axis), ZB+5), rot=Euler((0,0,axis),'XYZ'))
cren = crenellations("Gate_cren", 14, (gh_x, gh_y, ZB+16), C, stone)
for sgn in (-1,1):
    gws = [((gh_x + sgn*3.2*cos(axis+pi/2) - 8.2*cos(axis), gh_y + sgn*3.2*sin(axis+pi/2) - 8.2*sin(axis), ZB+6),
            Euler((0,0,axis),'XYZ'), 1.0, 2.6, 1.6),
           ((gh_x + sgn*3.2*cos(axis+pi/2) - 8.2*cos(axis), gh_y + sgn*3.2*sin(axis+pi/2) - 8.2*sin(axis), ZB+11),
            Euler((0,0,axis),'XYZ'), 1.0, 2.6, 1.6)]
    add_window_panes(f"Gate_win_{sgn}", gws, CW, [g_l2, g_l3])
box_obj("Gate_string", (gh_x, gh_y, ZB+13), (16.6, 12.6, 0.7), C, stone).rotation_euler[2] = axis
cren.rotation_euler[2] = axis

# ============================================================ VIADUCT (built along +X local, then transformed)
VA = Vector((95.0, -8.0))
VB = Vector((300.0, 20.0))
vlen = (VB-VA).length
span = 20.0
n_spans = int(vlen/span)
deck_w = 7.0
deck_z = 56.0

verts, faces = [], []
def vbox(cx, cy, cz, dx, dy, dz):
    b = len(verts)
    verts.extend([(cx-dx/2,cy-dy/2,cz-dz/2),(cx+dx/2,cy-dy/2,cz-dz/2),(cx+dx/2,cy+dy/2,cz-dz/2),(cx-dx/2,cy+dy/2,cz-dz/2),
                  (cx-dx/2,cy-dy/2,cz+dz/2),(cx+dx/2,cy-dy/2,cz+dz/2),(cx+dx/2,cy+dy/2,cz+dz/2),(cx-dx/2,cy+dy/2,cz+dz/2)])
    faces.extend([(b,b+1,b+2,b+3),(b+4,b+7,b+6,b+5),(b,b+4,b+5,b+1),(b+1,b+5,b+6,b+2),(b+2,b+6,b+7,b+3),(b+3,b+7,b+4,b+0)])

# camber function
def deck_at(x):
    t = x/vlen
    return deck_z + 2.2*sin(pi*t)

# piers + arches per span
for i in range(n_spans+1):
    x = i*span
    wx, wy = VA.x + (VB-VA).normalized().x*x, VA.y + (VB-VA).normalized().y*x
    floor_z = terrain_h(wx, wy) - 1.5
    top_z = deck_at(x) - 9.0
    h = top_z - floor_z
    # pier (slightly battered: two stacked boxes)
    vbox(x, 0, floor_z + h*0.35, 5.2, deck_w+1.2, h*0.7)
    vbox(x, 0, floor_z + h*0.82, 4.2, deck_w+0.6, h*0.36+2)
    # cutwater on piers (both sides) - small prism
    b = len(verts)
    for sgn in (-1,1):
        y0 = sgn*(deck_w/2+0.6)
        z0 = floor_z; z1 = floor_z + h*0.5
        verts.extend([(x-2.6,y0,z0),(x+2.6,y0,z0),(x,y0+sgn*2.2,z0),
                      (x-2.6,y0,z1),(x+2.6,y0,z1),(x,y0+sgn*2.2,z1)])
        faces.extend([(b,b+1,b+2),(b+3,b+5,b+4),(b,b+3,b+4,b+1),(b+1,b+4,b+5,b+2),(b+2,b+5,b+3,b+0)])
        b = len(verts)

for i in range(n_spans):
    x0 = i*span
    xc = x0 + span/2
    zc = deck_at(xc) - 9.0     # arch springing center
    r_out, r_in = 10.0, 8.0
    nseg = 12
    b = len(verts)
    for k in range(nseg+1):
        a = pi - pi*k/nseg
        for (r, y) in [(r_out, -deck_w/2), (r_out, deck_w/2), (r_in, -deck_w/2), (r_in, deck_w/2)]:
            verts.append((xc + r*cos(a), y, zc + r*sin(a)))
    for k in range(nseg):
        q = b + k*4
        q2 = q + 4
        faces.append((q, q2, q2+1, q+1))       # outer band
        faces.append((q+2, q+3, q2+3, q2+2))   # inner band
        faces.append((q, q+2, q2+2, q2))       # side -y
        faces.append((q+1, q2+1, q2+3, q+3))   # side +y
    # spandrel fill: box above arch up to deck
    dz = deck_at(xc)
    vbox(xc, 0, (zc+10+dz)/2 - 0.6, span-5.0, deck_w-0.4, dz - (zc+10) + 1.2)

# deck slab + parapets + string course
vbox(vlen/2, 0, deck_z+1.0+0.9, vlen+10, deck_w+1.6, 1.8)
for sgn in (-1,1):
    vbox(vlen/2, sgn*(deck_w/2+0.4), deck_z+2.2, vlen+10, 0.8, 2.4)
    vbox(vlen/2, sgn*(deck_w/2+0.55), deck_z+0.4, vlen+10, 1.1, 0.5)   # string course ledge

vd_stone = bpy.data.materials.new("StoneViaduct"); vd_stone.use_nodes = True
_vn = vd_stone.node_tree; _pbs = _vn.nodes.get("Principled BSDF")
_pbs.inputs["Roughness"].default_value = 0.85
_tc = _vn.nodes.new("ShaderNodeTexCoord")
_no = _vn.nodes.new("ShaderNodeTexNoise"); _no.inputs["Scale"].default_value = 0.12; _no.inputs["Detail"].default_value = 4.0
_ra = _vn.nodes.new("ShaderNodeValToRGB")
_ra.color_ramp.elements[0].color = (0.20,0.175,0.145,1)
_ra.color_ramp.elements[1].color = (0.38,0.33,0.27,1)
_no2 = _vn.nodes.new("ShaderNodeTexNoise"); _no2.inputs["Scale"].default_value = 1.5; _no2.inputs["Detail"].default_value = 3.0
_bp = _vn.nodes.new("ShaderNodeBump"); _bp.inputs["Strength"].default_value = 0.5; _bp.inputs["Distance"].default_value = 0.25
_vn.links.new(_tc.outputs["Object"], _no.inputs["Vector"])
_vn.links.new(_tc.outputs["Object"], _no2.inputs["Vector"])
_vn.links.new(_no.outputs["Fac"], _ra.inputs["Fac"])
_vn.links.new(_ra.outputs["Color"], _pbs.inputs["Base Color"])
_vn.links.new(_no2.outputs["Fac"], _bp.inputs["Height"])
_vn.links.new(_bp.outputs["Normal"], _pbs.inputs["Normal"])
via = new_mesh_obj("Viaduct", verts, faces, B, vd_stone)
via.location = (VA.x, VA.y, 0)
via.rotation_euler[2] = axis

# merlons along parapet
mverts, mfaces = [], []
import math as _mm
for i in range(int(vlen/2.0)):
    x = 1.0 + i*2.0
    for sgn in (-1,1):
        y0 = sgn*(deck_w/2+0.4)
        b2 = len(mverts)
        hw, ht, hh = 0.55, 0.35, 0.9
        mverts.extend([(x-hw,y0-ht,0),(x+hw,y0-ht,0),(x+hw,y0+ht,0),(x-hw,y0+ht,0),
                       (x-hw,y0-ht,hh),(x+hw,y0-ht,hh),(x+hw,y0+ht,hh),(x-hw,y0+ht,hh)])
        mfaces.extend([(b2,b2+1,b2+2,b2+3),(b2+4,b2+7,b2+6,b2+5),(b2,b2+4,b2+5,b2+1),
                       (b2+1,b2+5,b2+6,b2+2),(b2+2,b2+6,b2+7,b2+3),(b2+3,b2+7,b2+4,b2+0)])
mer = new_mesh_obj("ViaMerlons", mverts, mfaces, B, vd_stone)
mer.location = (VA.x, VA.y, deck_z+3.4)
mer.rotation_euler[2] = axis

# lanterns along parapet (every 2 spans)
for i in range(0, n_spans+1):
    x = i*span
    for sgn in (-1,1):
        lx = VA.x + cos(axis)*x - sin(axis)*sgn*(deck_w/2+0.4)
        ly = VA.y + sin(axis)*x + cos(axis)*sgn*(deck_w/2+0.4)
        lantern_post(f"ViaLant_{i}_{sgn}", (lx, ly, deck_at(x)+2.4), B, h=2.6)

# ============================================================ BOATHOUSE + JETTY
bh_x, bh_y = 66.0, -112.0
box_obj("Boathouse_Base", (bh_x, bh_y, 3.0), (18, 13, 7.0), P, stoned)
# three arches facing lake (south)
for i in (-1, 0, 1):
    arch_frame(f"BH_arch_{i}", 3.6, 5.5, 3.6, 0.8, 1.6, P, stone,
               loc=(bh_x + i*5.5, bh_y-6.6, 0.4), rot=Euler((0,0,pi),'XYZ'))
    arch_panel(f"BH_dark_{i}", 3.6, 5.5, 3.6, 0.2, P, g_dark,
               loc=(bh_x + i*5.5, bh_y-6.7, 0.4), rot=Euler((0,0,pi),'XYZ'))
box_obj("Boathouse_Upper", (bh_x, bh_y, 9.0), (17, 12, 5.0), P, wood)
gable_roof("Boathouse_Roof", 17, 12, 6.5, (bh_x, bh_y, 11.5), P, slate, overhang=0.8, axis='X')
# small windows upper
specs = [((bh_x-4, bh_y-6.05, 8.2), Euler((0,0,pi),'XYZ'), 1.2, 1.8, 1.2),
         ((bh_x+3, bh_y-6.05, 8.2), Euler((0,0,pi),'XYZ'), 1.2, 1.8, 1.2)]
add_window_panes("BH_Windows", specs, CW, [g_l2, g_l3])
# jetty
box_obj("Jetty_deck", (bh_x+2, bh_y-14, 1.2), (4.0, 16, 0.5), P, wood)
import bpy as _b
_L = _b.data.collections["Lights"]
for _i, _ax in enumerate([bh_x-5.5, bh_x, bh_x+5.5]):
    _ld = _b.data.lights.new(f"BHA_{_i}", 'POINT')
    _ld.energy = 300; _ld.color = (1.0, 0.5, 0.2); _ld.shadow_soft_size = 0.6
    _ob = _b.data.objects.new(f"BHA_{_i}", _ld)
    _L.objects.link(_ob)
    _ob.location = (_ax, bh_y-7.2, 3.2)
for j in range(4):
    for sgn in (-1,1):
        cyl_obj(f"Jetty_post_{j}_{sgn}", (bh_x+2+sgn*1.8, bh_y-8-j*4, 0.2), 0.18, 2.4, P, wood, verts=8)
lantern_post("BH_Lantern", (bh_x+3.5, bh_y-20, 1.4), P, h=2.8)

# switchback stair up the south cliff
flights = [((62,-105,2.0),(40,-95,12.0)), ((40,-95,12.0),(56,-88,24.0)),
           ((56,-88,24.0),(34,-72,36.0)), ((34,-72,36.0),(32,-54,50.5))]
for i,(s,e) in enumerate(flights):
    stair_flight(f"CliffStair_{i}", s, e, 16, 2.4, P, stone)
    lantern_post(f"StairLant_{i}", e, P, h=2.6)
    sv, ev = Vector(s), Vector(e)
    mid = (sv+ev)/2
    run = (Vector((ev.x,ev.y,0)) - Vector((sv.x,sv.y,0))).length
    pitch = math.atan2(ev.z-sv.z, run)
    rw = box_obj(f"StairWall_{i}", (mid.x, mid.y, mid.z-2.8), (run+2, 3.2, 3.2), P, stoned)
    rw.rotation_euler[2] = math.atan2(ev.y-sv.y, ev.x-sv.x)
    rw.rotation_euler[1] = -pitch
# small landing shelters
for i,(s,e) in enumerate(flights):
    box_obj(f"StairLand_{i}", (e[0], e[1], e[2]+0.2), (3.2,3.2,0.4), P, stone)

# ============================================================ GREENHOUSES (north terrace)
for gi, gx in enumerate([-16, 2, 20]):
    gy = 72.0
    gz = 44.0
    box_obj(f"GH_base_{gi}", (gx, gy, gz+0.6), (15, 9, 1.2), P, stoned)
    box_obj(f"GH_glass_{gi}", (gx, gy, gz+3.4), (14.4, 8.4, 4.4), P, glassgh)
    gable_roof(f"GH_roof_{gi}", 14.4, 8.4, 3.2, (gx, gy, gz+5.6), P, glassgh, overhang=0.15, axis='X')
    # frame ribs
    for r in range(6):
        rx = gx - 6 + r*2.4
        box_obj(f"GH_rib_{gi}_{r}", (rx, gy, gz+3.4), (0.18, 8.5, 4.5), P, metal)

# ============================================================ CLOISTER courtyard
cl_x, cl_y = 12, -14
for side in range(4):
    a = side*pi/2
    L = 22 if side%2==0 else 16
    wx = cl_x + (11 if side==0 else -11 if side==2 else 0)
    wy = cl_y + (8 if side==1 else -8 if side==3 else 0)
    ob = box_obj(f"Cloister_{side}", (wx, wy, ZB+2.5), (L if side%2==1 else 0.0+ L, 2.0, 5.0), C, stone)
    ob.rotation_euler[2] = a
    specs = []
    for k in range(5):
        t = (k-2)*0.2*L*0.9
        px = wx + t*cos(a+pi/2)
        py = wy + t*sin(a+pi/2)
        specs.append(((px, py, ZB+0.6), Euler((0,0,a),'XYZ'), 1.4, 3.4, 2.2))
    add_window_panes(f"Cloister_win_{side}", specs, CW, [g_dark, g_l1, g_l2])

# ============================================================ OWLERY on west outcrop
tower("Owlery", -150, -70, 16, 4.0, 16, P, stone, slate, spire_h=9, corbel=True, verts_n=14)
specs = []
for row in range(2):
    for i in range(4):
        a = i/4*2*pi + row*0.4
        specs.append(((-150+(4.05)*cos(a), -70+(4.05)*sin(a), 20+row*6), Euler((0,0,a-pi/2),'XYZ'), 0.9, 1.6, 1.0))
add_window_panes("Owlery_Windows", specs, CW, [g_l1, g_l2, g_dark])

# ============================================================ GAMEKEEPER HUT (east forest edge)
hx, hy = 380, 60
hz = terrain_h(hx, hy)
box_obj("Hut_Body", (hx, hy, hz+1.6), (7.5, 5.5, 3.2), P, stone)
gable_roof("Hut_Roof", 7.5, 5.5, 3.0, (hx, hy, hz+3.2), P, wood, overhang=0.5, axis='X')
box_obj("Hut_Chimney", (hx+2.5, hy+1.5, hz+5.6), (1.0,1.0,3.4), P, stoned)
specs = [((hx-2.0, hy-2.8, hz+1.2), Euler((0,0,pi),'XYZ'), 1.1, 1.3, 0.9),
         ((hx+1.5, hy-2.8, hz+1.2), Euler((0,0,pi),'XYZ'), 1.1, 1.3, 0.9)]
add_window_panes("Hut_Windows", specs, CW, [g_l3, g_l2])

# ============================================================ WATER ROCKS (foreground interest)
for i in range(9):
    import random as _r
    _r.seed(500+i)
    wx = _r.uniform(-260, 320)
    wy = _r.uniform(-430, -140)
    if abs(wx) < 130 and wy > -200:
        continue
    build_crag_ok = None
    ob = cone_obj(f"WaterRock_{i}", (wx, wy, _r.uniform(-1.5, 0.5)), _r.uniform(2.5, 6.0), _r.uniform(0.5, 1.5), _r.uniform(2.0, 5.0), P, mat_rock(), verts=9)
    ob.rotation_euler[2] = _r.uniform(0, 6.28)

# terrace edge lanterns
for i, lx in enumerate(range(-50, 61, 22)):
    lantern_post(f"TerrLant_{i}", (lx, -55.0, ZB), P, h=2.8)

# rowboat with lantern on the lake
bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, location=(-62, -295, 0.4))
boat = bpy.context.active_object; boat.name = "Rowboat"; move_to_col(boat, P)
boat.scale = (3.2, 1.3, 0.75)
boat.data.materials.append(wood)
bpy.ops.mesh.primitive_cube_add(location=(-62, -295, 0.75))
seat = bpy.context.active_object; seat.name = "RowboatSeat"; move_to_col(seat, P)
seat.scale = (2.2, 0.9, 0.1); seat.data.materials.append(wood)
lantern_post("BoatLant", (-63.5, -295, 0.9), P, h=1.6)

# ============================================================ STANDING STONES
sc_x, sc_y = -330, 270
sz = terrain_h(sc_x, sc_y)
for i in range(9):
    a = i/9*2*pi
    r = 19 + random.uniform(-2, 2)
    sx, sy = sc_x + r*cos(a), sc_y + r*sin(a)
    ob = box_obj(f"Stone_{i}", (sx, sy, terrain_h(sx,sy)+1.6), (1.6,1.1,3.6+random.uniform(-0.6,0.9)), P, stoned, bevel=0.25)
    ob.rotation_euler = (random.uniform(-0.08,0.08), random.uniform(-0.08,0.08), a)

result = {"castle_extra": "built", "objects": len(bpy.data.objects)}
