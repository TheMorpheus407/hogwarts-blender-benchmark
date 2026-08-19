# node-graph helper kit (runs inside Blender via MCP)
import bpy, math
from mathutils import Vector

def L(nt, a, ao, b, bi):
    asock = a.outputs[ao] if hasattr(a, 'outputs') and not hasattr(a, 'default_value') else a
    bsock = b.inputs[bi] if hasattr(b, 'inputs') and not hasattr(b, 'default_value') else b
    nt.links.new(asock, bsock)

def mknode(nt, ntype, loc=(0,0), **kw):
    n = nt.nodes.new(ntype)
    n.location = loc
    for k, v in kw.items():
        try: setattr(n, k, v)
        except Exception: pass
    return n

def rgb(nt, c, loc):
    n = mknode(nt, "ShaderNodeRGB", loc)
    n.outputs[0].default_value = (*c, 1.0)
    return n.outputs[0]

def val(nt, v, loc):
    n = mknode(nt, "ShaderNodeValue", loc)
    n.outputs[0].default_value = v
    return n.outputs[0]

def texco(nt, loc=(-1400, 0)):
    return mknode(nt, "ShaderNodeTexCoord", loc)

def geo_out(nt, name, loc):
    g = mknode(nt, "ShaderNodeNewGeometry", loc)
    for o in g.outputs:
        if o.name == name: return o
    return None

CLAMP_OP = 'MINIMUM'
def clampn(nt, v, lo=0.0, hi=1.0, loc=(0,0)):
    v2 = mathn(nt, 'MAXIMUM', v, lo, loc=loc)
    return mathn(nt, 'MINIMUM', v2, hi, loc=(loc[0]+80, loc[1]))

def mathn(nt, op, *vals, loc=(0,0)):
    m = mknode(nt, "ShaderNodeMath", loc)
    m.operation = op
    ins = [m.inputs[i] for i in range(len(vals))]
    for sock, v in zip(ins, vals):
        if isinstance(v, (int, float)): sock.default_value = v
        else: nt.links.new(v, sock)
    return m.outputs[0]

def mixc(nt, a, b, fac, loc=(0,0), blend='MIX'):
    m = mknode(nt, "ShaderNodeMixRGB", loc)
    m.blend_type = blend
    nt.links.new(a, m.inputs['Color1'])
    nt.links.new(b, m.inputs['Color2'])
    nt.links.new(fac, m.inputs['Fac'])
    return m.outputs[0]

def noise(nt, scale, detail=4, loc=(0,0), roughness=0.5, distortion=0.0, vec=None):
    n = mknode(nt, "ShaderNodeTexNoise", loc)
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    try:
        n.inputs['Roughness'].default_value = roughness
        n.inputs['Distortion'].default_value = distortion
    except Exception: pass
    if vec is not None:
        vsock = vec.outputs[0] if hasattr(vec, 'outputs') else vec
        nt.links.new(vsock, n.inputs[0])
    return n

def wave(nt, scale, distortion=0.0, detail=2, loc=(0,0), vec=None):
    n = mknode(nt, "ShaderNodeTexWave", loc)
    n.inputs['Scale'].default_value = scale
    n.inputs['Distortion'].default_value = distortion
    n.inputs['Detail'].default_value = detail
    if vec is not None: nt.links.new(vec, n.inputs[0])
    return n

def voronoi(nt, scale, loc=(0,0), vec=None):
    n = mknode(nt, "ShaderNodeTexVoronoi", loc)
    n.inputs['Scale'].default_value = scale
    if vec is not None: nt.links.new(vec, n.inputs[0])
    return n

def setbs(bs, **kw):
    for k, v in kw.items():
        if k in bs.inputs:
            try: bs.inputs[k].default_value = v
            except Exception: pass

def new_mat(name):
    m = bpy.data.materials.get(name)
    if m: bpy.data.materials.remove(m, do_unlink=True)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m

def std_mat(name, color, rough=0.9):
    m = new_mat(name)
    nt = m.node_tree
    bs = nt.nodes.get("Principled BSDF")
    bs.location = (500, 0)
    nt.nodes["Material Output"].location = (800, 0)
    setbs(bs, **{"Base Color": (*color,1.0), "Roughness": rough, "Metallic": 0.0,
                 "Specular IOR Level": 0.35})
    return m, nt, bs
