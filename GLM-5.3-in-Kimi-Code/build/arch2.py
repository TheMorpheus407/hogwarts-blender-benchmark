# Architecture builders, part 2 — runs in Blender, uses lib.py functions
import bpy, bmesh, math, json, random
from mathutils import Vector, Matrix

_lib = {}
exec(compile(bpy.data.texts['lib'].as_string(), "lib.py", "exec"), _lib)
ring = _lib['ring']; band_faces = _lib['band_faces']; cap_faces = _lib['cap_faces']
crenel_ring = _lib['crenel_ring']; cone_roof = _lib['cone_roof']; build_tower = _lib['build_tower']
new_obj = _lib['new_obj']; finish = _lib['finish']; ensure_fcol = _lib['ensure_fcol']; paint = _lib['paint']
fbm2 = _lib['fbm2']

WINREG = {"windows": [], "lanterns": []}

def save_reg():
    t = bpy.data.texts.get("winreg") or bpy.data.texts.new("winreg")
    t.from_string(json.dumps(WINREG))

def load_reg():
    t = bpy.data.texts.get("winreg")
    if t:
        WINREG.clear(); WINREG.update(json.loads(t.as_string()))

def reg_win(p, n, up, w, h, glow, warm, mull, kind):
    WINREG["windows"].append(dict(p=[p.x,p.y,p.z], n=[n.x,n.y,n.z], up=[up.x,up.y,up.z],
                                  w=w, h=h, glow=round(glow,3), warm=round(warm,3),
                                  mull=mull, kind=kind))

def reg_lantern(p, glow):
    WINREG["lanterns"].append(dict(p=[p.x,p.y,p.z], glow=round(glow,3)))

# ---------- straight wall with crenellation ----------
def wall_segment(bm, x0, y0, x1, y1, z0, h, thick=2.0, mat=0, crenel=True,
                 walk=True, tint=None, tlay=None, batter=0.12, sides_seg=6):
    dx, dy = x1-x0, y1-y0
    ln = math.hypot(dx, dy)
    ux, uy = dx/ln, dy/ln          # along
    nx, ny = -uy, ux               # normal (left of dir)
    def pt(t, off, z):
        return bm.verts.new((x0 + ux*t + nx*off, y0 + uy*t + ny*off, z))
    fs = []
    n = max(2, int(ln/6))
    ts = [ln*i/n for i in range(n+1)]
    # battered faces: outer (off -thick..-thick+batter), inner vertical
    for i in range(n):
        t0, t1 = ts[i], ts[i+1]
        wobble = 1.0 + 0.25*(fbm2(t0*0.11, x0*0.07, 3, 1, 91.1)-0.5)
        th = thick*wobble
        a = pt(t0, -th, z0);             b = pt(t1, -th, z0)
        c = pt(t1, -th+batter, z0+h);    d = pt(t0, -th+batter, z0+h)
        fs.append(bm.faces.new((a,b,c,d)))
        e = pt(t0, 0.0, z0);             f = pt(t1, 0.0, z0)
        g = pt(t1, 0.0, z0+h);           h_ = pt(t0, 0.0, z0+h)
        fs.append(bm.faces.new((f,e,h_,g)))
    # top walk + crenels along outer edge
    for i in range(n):
        t0, t1 = ts[i], ts[i+1]
        wobble = 1.0 + 0.25*(fbm2(t0*0.11, x0*0.07, 3, 1, 91.1)-0.5)
        th = thick*wobble
        a = pt(t0, -th+batter, z0+h); b = pt(t1, -th+batter, z0+h)
        c = pt(t1, 0.0, z0+h); d = pt(t0, 0.0, z0+h)
        f = bm.faces.new((a,b,c,d)); fs.append(f)
    if crenel:
        step = 2.2
        t = 0.6
        while t < ln - 0.6:
            m_w = min(1.0, ln - 0.6 - t)
            a0 = pt(t, -thick*1.02+batter, z0+h); b0 = pt(t+m_w*0.55, -thick*1.02+batter, z0+h)
            c0 = pt(t+m_w*0.55, -thick*0.55, z0+h); d0 = pt(t, -thick*0.55, z0+h)
            a1 = pt(t, -thick*1.02+batter, z0+h+1.0); b1 = pt(t+m_w*0.55, -thick*1.02+batter, z0+h+1.0)
            c1 = pt(t+m_w*0.55, -thick*0.55, z0+h+1.0); d1 = pt(t, -thick*0.55, z0+h+1.0)
            try:
                fs.append(bm.faces.new((a0,b0,b1,a1)))
                fs.append(bm.faces.new((d0,c0,c1,d1)))
                fs.append(bm.faces.new((a1,b1,c1,d1)))
            except ValueError: pass
            t += step
    for f in fs: f.material_index = mat
    if tint is not None and tlay is not None: paint(bm, tlay, fs, tint)
    return fs

# ---------- buttress ----------
def buttress(bm, x, y, ang, z0, z1, w=1.3, proj=1.8, steps=3, mat=0, tint=None, tlay=None):
    fs = []
    ca, sa = math.cos(ang), math.sin(ang)
    def q(px, py, z):
        return bm.verts.new((x + ca*px - sa*py, y + sa*px + ca*py, z))
    n = steps
    for i in range(n):
        f0 = 0.4 + proj*(1 - i/n)
        f1 = 0.4 + proj*(1 - (i+1)/n)
        zb0 = z0 + (z1-z0)*i/n; zb1 = z0 + (z1-z0)*(i+1)/n
        # outer face
        a=q(-w/2,-f0,zb0); b=q(w/2,-f0,zb0); c=q(w/2,-f1,zb1); d=q(-w/2,-f1,zb1)
        fs.append(bm.faces.new((a,b,c,d)))
        # sides
        e=q(w/2,0.2,zb0); g=q(w/2,0.2,zb1)
        fs.append(bm.faces.new((b,e,g,c)))
        e2=q(-w/2,0.2,zb0); g2=q(-w/2,0.2,zb1)
        fs.append(bm.faces.new((a,d,g2,e2)))
        # slope top of this stage
        fs.append(bm.faces.new((d,c,g,g2)) if i == 0 else bm.faces.new((d,c,g,g2)))
    # cap slope
    f_top = 0.4
    a=q(-w/2,-f_top,z1); b=q(w/2,-f_top,z1); c=q(w/2,0.2,z1); d=q(-w/2,0.2,z1)
    fs.append(bm.faces.new((a,b,c,d)))
    for f in fs: f.material_index = mat
    if tint is not None and tlay is not None: paint(bm, tlay, fs, tint)
    return fs

# ---------- gable roof (ridge along direction dir) ----------
def gable_roof(bm, cx, cy, z0, sx, sy, ridge_h, rot_z, mat=1, overhang=0.8,
               dormers=0, tint=None, tlay=None, base_tint=None):
    fs = []
    ca, sa = math.cos(rot_z), math.sin(rot_z)
    def P(px, py, z):
        return bm.verts.new((cx + ca*px - sa*py, cy + sa*px + ca*py, z))
    ox = sx/2 + overhang; oy = sy/2 + overhang
    # two slopes
    for s in (-1, 1):
        a = P(-ox, s*oy, z0); b = P(ox, s*oy, z0)
        c = P(ox, s*0.28, z0+ridge_h); d = P(-ox, s*0.28, z0+ridge_h)
        f = bm.faces.new((a,b,c,d)); f.smooth = False
        fs.append(f)
    # gable ends (stone)
    for s in (-1, 1):
        a = P(s*ox, -oy, z0); b = P(s*ox, oy, z0)
        c = P(s*ox, oy*0.94, z0+ridge_h*0.94); d = P(s*ox, -oy*0.94, z0+ridge_h*0.94)
        e = P(s*ox, 0.28, z0+ridge_h); g = P(s*ox, -0.28, z0+ridge_h)
        fs.append(bm.faces.new((a,b,c,g))); fs.append(bm.faces.new((a,g,e,d)))
    # ridge
    r1 = P(-ox, 0.28, z0+ridge_h); r2 = P(ox, 0.28, z0+ridge_h)
    r3 = P(ox, -0.28, z0+ridge_h); r4 = P(-ox, -0.28, z0+ridge_h)
    fs.append(bm.faces.new((r1,r2,r3,r4)))
    for f in fs: f.material_index = mat
    if tint is not None and tlay is not None: paint(bm, tlay, fs, tint)
    return fs

# ---------- pointed-arch hall with bays, buttresses, clerestory ----------
def great_hall(bm, cx, cy, rot_z, z0, L, W, H, mat=0, roof_mat=1, tint=None, tlay=None):
    ca, sa = math.cos(rot_z), math.sin(rot_z)
    def P(px, py, z):
        return Vector((cx + ca*px - sa*py, cy + sa*px + sa*py, z))
    def Pv(px, py, z):
        v = P(px, py, z); return bm.verts.new(v)
    fs = []
    bays = max(4, int(L/10))
    # walls: two long sides + ends
    for s in (-1, 1):
        y0 = s*W/2
        for i in range(bays):
            x0 = -L/2 + L*i/bays; x1 = -L/2 + L*(i+1)/bays
            a = Pv(x0, y0, z0); b = Pv(x1, y0, z0)
            c = Pv(x1, y0+s*0.1, z0+H); d = Pv(x0, y0+s*0.1, z0+H)
            f = bm.faces.new((a,b,c,d)); fs.append(f)
        # end gable walls
    for s in (-1, 1):
        x0 = s*L/2
        a = Pv(x0, -W/2, z0); b = Pv(x0, W/2, z0)
        c = Pv(x0, W/2, z0+H); d = Pv(x0, -W/2, z0+H)
        fs.append(bm.faces.new((a,b,c,d)))
    # buttresses + window registration along both sides
    nbut = bays + 1
    for i in range(nbut):
        bx = -L/2 + L*i/bays
        for s in (-1, 1):
            v = P(bx, s*(W/2+0.9), 0)
            ang = rot_z - s*math.pi/2
            buttress(bm, v.x, v.y, ang, z0, z0+H*0.94, w=1.4, proj=1.9, steps=3,
                     mat=mat, tint=tint, tlay=tlay)
    for i in range(bays):
        bx = -L/2 + L*(i+0.5)/bays
        for s in (-1, 1):
            v = P(bx, s*(W/2+0.12), z0+3.2)
            nrm = P(0, s*(W/2+1), 0) - P(0, s*(W/2-1), 0)
            nrm = Vector((nrm.x, nrm.y, 0)).normalized()
            upv = Vector((0,0,1))
            glow = random.choice([0,0,0.3,0.55,0.8,1.0,1.2])
            reg_win(v, nrm, upv, 2.1, 5.2, glow, random.uniform(0.75,1.0), 2, "arch")
    # clerestory row (upper)
    for i in range(bays*2):
        bx = -L/2 + L*(i+0.5)/(bays*2)
        for s in (-1, 1):
            v = P(bx, s*(W/2+0.06), z0+H*0.62)
            nrm = Vector((ca*(-s*0) - sa*s, sa*0 + ca*s, 0))
            nrm = Vector((-sa*s, ca*s, 0))
            glow = random.choice([0,0.25,0.5,0.9,1.1])
            reg_win(v, nrm, Vector((0,0,1)), 0.9, 2.2, glow, random.uniform(0.8,1.0), 1, "lancet")
    # roof
    gable_roof(bm, cx, cy, z0+H, L, W, W*0.62, rot_z, mat=roof_mat, tint=tint, tlay=tlay)
    for f in fs: f.material_index = mat
    if tint is not None and tlay is not None: paint(bm, tlay, fs, tint)
    return fs

# ---------- corner turret (cylindrical with cone) ----------
def corner_turret(bm, cx, cy, z0, z1, r, sides=10, roof_h=0, mat=0, roof_mat=2,
                  tint=None, tlay=None, finial=True, glow_bias=0.5):
    fs = build_tower(bm, cx, cy, z0, z1, r, sides=sides, stages=2, strings=1,
                     parapet="cone" if roof_h > 0 else "crenel",
                     roof_h=roof_h, roof_mat=roof_mat, finial=finial,
                     tint=tint, tlay=tlay, mat=mat)
    # tiny windows
    for i in range(2):
        az = random.uniform(0, 2*math.pi)
        p = Vector((cx + (r+0.1)*math.cos(az), cy + (r+0.1)*math.sin(az), z0 + (z1-z0)*(0.35+0.3*i)))
        nrm = Vector((math.cos(az), math.sin(az), 0))
        glow = random.choice([0, 0.5*glow_bias, glow_bias, 1.1*glow_bias])
        reg_win(p, nrm, Vector((0,0,1)), 0.7, 1.6, glow, random.uniform(0.75,1.0), 1, "lancet")
    return fs
