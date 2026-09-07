"""Pass 3 — nature: procedural conifers scattered with geometry nodes."""
import bpy, bmesh, os, sys, importlib, math, random
from mathutils import Vector
FOLDER = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else bpy.path.abspath("//")
if FOLDER not in sys.path:
    sys.path.insert(0, FOLDER)
import hog_lib as H; importlib.reload(H)
from hog_lib import NB

H.clear_collection("Nature")
lib = H.coll("TreeLib", "Nature")

# --------------------------------------------------------------------------- conifer mesh
def make_conifer(name, height, r_base, layers, seed, droop=0.35, lean=0.0):
    rng = random.Random(seed)
    bm = bmesh.new()
    # trunk
    H.bm_cylinder(bm, r_base * 0.09, -0.5, height * 0.92, 8, r_top=r_base * 0.03)
    trunk_faces = set(f.index for f in bm.faces)
    n_tf = len(bm.faces)
    segs = 12
    for i in range(layers):
        t = i / max(1, layers - 1)
        z = height * (0.14 + 0.80 * t)
        r = r_base * (1.0 - 0.9 * t) ** 0.85 + 0.12
        h = r * (1.25 + 0.5 * t) + 0.6
        ring = []
        for k in range(segs):
            a = 2 * math.pi * k / segs + rng.random() * 0.25
            rr = r * (0.75 + 0.5 * rng.random())
            ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z - droop * rr * (0.6 + 0.8 * rng.random()))))
        apex = bm.verts.new((rng.uniform(-0.1, 0.1) * r, rng.uniform(-0.1, 0.1) * r, z + h))
        for k in range(segs):
            bm.faces.new((ring[k], ring[(k + 1) % segs], apex))
        # underside (dark) — cap
        bm.faces.new(list(reversed(ring)))
    # leader
    H.bm_cone(bm, r_base * 0.12 + 0.1, height * 0.90, height, 6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    me.materials.append(bpy.data.materials.get("M_Trunk") or H.ensure_material("M_Trunk", (0.1, 0.07, 0.05, 1)))
    me.materials.append(bpy.data.materials.get("M_Conifer") or H.ensure_material("M_Conifer", (0.05, 0.09, 0.04, 1)))
    for p in me.polygons:
        p.material_index = 0 if p.index < n_tf else 1
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    H.link_obj(ob, lib)
    ob.location = (-9000, -9000 + 40 * len(lib.objects), 0)
    if lean:
        ob.rotation_euler = (math.radians(lean), 0, 0)
    return ob

trees = [
    make_conifer("Tree_Spruce_A", 21.0, 3.4, 9, 1),
    make_conifer("Tree_Spruce_B", 17.0, 2.9, 8, 2),
    make_conifer("Tree_Fir_C", 14.0, 3.1, 7, 3, droop=0.5),
    make_conifer("Tree_Pine_D", 24.0, 3.0, 7, 4, droop=0.25),
    make_conifer("Tree_Young_E", 9.0, 2.0, 6, 5),
]

# --------------------------------------------------------------------------- geometry nodes scatter
def scatter_group(name="GN_ForestScatter"):
    ng = bpy.data.node_groups.get(name)
    if ng:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    iface = ng.interface
    iface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    s_d = iface.new_socket("Density", in_out='INPUT', socket_type='NodeSocketFloat'); s_d.default_value = 0.03
    s_s = iface.new_socket("Seed", in_out='INPUT', socket_type='NodeSocketInt'); s_s.default_value = 1
    s_c = iface.new_socket("Trees", in_out='INPUT', socket_type='NodeSocketCollection')
    s_sc = iface.new_socket("Scale", in_out='INPUT', socket_type='NodeSocketFloat'); s_sc.default_value = 1.0
    iface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nodes = ng.nodes; links = ng.links
    gi = nodes.new("NodeGroupInput"); go = nodes.new("NodeGroupOutput")
    attr = nodes.new("GeometryNodeInputNamedAttribute"); attr.data_type = 'FLOAT'; attr.inputs["Name"].default_value = "forest"
    # density = forest^1.5 * Density
    pw = nodes.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.inputs[1].default_value = 1.4
    links.new(attr.outputs["Attribute"], pw.inputs[0])
    dens = nodes.new("ShaderNodeMath"); dens.operation = 'MULTIPLY'
    links.new(pw.outputs[0], dens.inputs[0]); links.new(gi.outputs["Density"], dens.inputs[1])
    dist = nodes.new("GeometryNodeDistributePointsOnFaces"); dist.distribute_method = 'RANDOM'
    links.new(gi.outputs["Geometry"], dist.inputs["Mesh"])
    links.new(dens.outputs[0], dist.inputs["Density"])
    links.new(gi.outputs["Seed"], dist.inputs["Seed"])
    ci = nodes.new("GeometryNodeCollectionInfo"); ci.transform_space = 'ORIGINAL'
    ci.inputs["Separate Children"].default_value = True; ci.inputs["Reset Children"].default_value = True
    links.new(gi.outputs["Trees"], ci.inputs["Collection"])
    iop = nodes.new("GeometryNodeInstanceOnPoints")
    links.new(dist.outputs["Points"], iop.inputs["Points"])
    links.new(ci.outputs["Instances"], iop.inputs["Instance"])
    iop.inputs["Pick Instance"].default_value = True
    idn = nodes.new("GeometryNodeInputID")
    rnd_i = nodes.new("FunctionNodeRandomValue"); rnd_i.data_type = 'INT'
    rnd_i.inputs["Min"].default_value = 0; rnd_i.inputs["Max"].default_value = 4
    links.new(idn.outputs[0], rnd_i.inputs["ID"]); links.new(gi.outputs["Seed"], rnd_i.inputs["Seed"])
    links.new(rnd_i.outputs["Value"], iop.inputs["Instance Index"])
    rnd_r = nodes.new("FunctionNodeRandomValue"); rnd_r.data_type = 'FLOAT'
    rnd_r.inputs["Min"].default_value = 0.0; rnd_r.inputs["Max"].default_value = 6.2832
    links.new(idn.outputs[0], rnd_r.inputs["ID"])
    seed2 = nodes.new("ShaderNodeMath"); seed2.operation = 'ADD'; seed2.inputs[1].default_value = 7
    links.new(gi.outputs["Seed"], seed2.inputs[0]); links.new(seed2.outputs[0], rnd_r.inputs["Seed"])
    rot = nodes.new("ShaderNodeCombineXYZ")
    links.new(rnd_r.outputs[1], rot.inputs["Z"])
    links.new(rot.outputs[0], iop.inputs["Rotation"])
    rnd_s = nodes.new("FunctionNodeRandomValue"); rnd_s.data_type = 'FLOAT'
    rnd_s.inputs["Min"].default_value = 0.7; rnd_s.inputs["Max"].default_value = 1.35
    links.new(idn.outputs[0], rnd_s.inputs["ID"])
    seed3 = nodes.new("ShaderNodeMath"); seed3.operation = 'ADD'; seed3.inputs[1].default_value = 13
    links.new(gi.outputs["Seed"], seed3.inputs[0]); links.new(seed3.outputs[0], rnd_s.inputs["Seed"])
    # smaller trees where the forest thins (attribute low)
    edge = nodes.new("ShaderNodeMath"); edge.operation = 'MULTIPLY_ADD'; edge.inputs[1].default_value = 0.45; edge.inputs[2].default_value = 0.6
    links.new(attr.outputs["Attribute"], edge.inputs[0])
    sc1 = nodes.new("ShaderNodeMath"); sc1.operation = 'MULTIPLY'
    links.new(rnd_s.outputs[1], sc1.inputs[0]); links.new(edge.outputs[0], sc1.inputs[1])
    sc2 = nodes.new("ShaderNodeMath"); sc2.operation = 'MULTIPLY'
    links.new(sc1.outputs[0], sc2.inputs[0]); links.new(gi.outputs["Scale"], sc2.inputs[1])
    scv = nodes.new("ShaderNodeCombineXYZ")
    for k in ("X", "Y", "Z"):
        links.new(sc2.outputs[0], scv.inputs[k])
    links.new(scv.outputs[0], iop.inputs["Scale"])
    join = nodes.new("GeometryNodeJoinGeometry")
    links.new(iop.outputs["Instances"], join.inputs[0])
    links.new(gi.outputs["Geometry"], join.inputs[0])
    links.new(join.outputs[0], go.inputs["Geometry"])
    return ng

ng = scatter_group()
counts = {}
for (obj_name, density, seed, scale) in (("Terrain_CragHi", 0.028, 4, 1.0), ("Terrain_Crag", 0.028, 1, 1.0), ("Terrain_Near", 0.028, 2, 1.0), ("Terrain_Far", 0.0045, 3, 1.6)):
    ob = bpy.data.objects.get(obj_name)
    if ob is None:
        continue
    for md in list(ob.modifiers):
        if md.type == 'NODES':
            ob.modifiers.remove(md)
    md = ob.modifiers.new("ForestScatter", 'NODES')
    md.node_group = ng
    md["Socket_1"] = density
    md["Socket_2"] = seed
    md["Socket_3"] = lib
    md["Socket_4"] = scale
    counts[obj_name] = density

# --------------------------------------------------------------------------- boulders / scree
rocklib = H.coll("RockLib", "Nature")
def make_boulder(name, r, seed):
    rng = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=r)
    for v in bm.verts:
        n = v.co.normalized()
        f = 1.0 + 0.28 * (rng.random() - 0.5) + 0.18 * math.sin(3.1 * v.co.x / r + seed) * math.cos(2.3 * v.co.y / r) + 0.12 * math.sin(4.7 * v.co.z / r + 1.3 * seed)
        v.co = n * r * f
        v.co.z *= 0.72
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    me.materials.append(bpy.data.materials.get("M_Terrain") or H.ensure_material("M_Terrain", (0.3, 0.3, 0.3, 1)))
    for pp in me.polygons:
        pp.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    H.link_obj(ob, rocklib)
    ob.location = (-9000, -8000 + 20 * len(rocklib.objects), 0)
    return ob
boulders = [make_boulder("Rock_A", 1.4, 11), make_boulder("Rock_B", 0.9, 12), make_boulder("Rock_C", 2.2, 13), make_boulder("Rock_D", 0.6, 14), make_boulder("Rock_E", 1.1, 15)]

def scree_group(name="GN_ScreeScatter"):
    ng = bpy.data.node_groups.get(name)
    if ng:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    iface = ng.interface
    iface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    s_d = iface.new_socket("Density", in_out='INPUT', socket_type='NodeSocketFloat'); s_d.default_value = 0.05
    s_s = iface.new_socket("Seed", in_out='INPUT', socket_type='NodeSocketInt'); s_s.default_value = 1
    s_c = iface.new_socket("Rocks", in_out='INPUT', socket_type='NodeSocketCollection')
    iface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nodes = ng.nodes; links = ng.links
    gi = nodes.new("NodeGroupInput"); go = nodes.new("NodeGroupOutput")
    attr = nodes.new("GeometryNodeInputNamedAttribute"); attr.data_type = 'FLOAT'; attr.inputs["Name"].default_value = "scree"
    dens = nodes.new("ShaderNodeMath"); dens.operation = 'MULTIPLY'
    links.new(attr.outputs["Attribute"], dens.inputs[0]); links.new(gi.outputs["Density"], dens.inputs[1])
    dist = nodes.new("GeometryNodeDistributePointsOnFaces"); dist.distribute_method = 'RANDOM'
    links.new(gi.outputs["Geometry"], dist.inputs["Mesh"]); links.new(dens.outputs[0], dist.inputs["Density"]); links.new(gi.outputs["Seed"], dist.inputs["Seed"])
    ci = nodes.new("GeometryNodeCollectionInfo"); ci.transform_space = 'ORIGINAL'
    ci.inputs["Separate Children"].default_value = True; ci.inputs["Reset Children"].default_value = True
    links.new(gi.outputs["Rocks"], ci.inputs["Collection"])
    iop = nodes.new("GeometryNodeInstanceOnPoints")
    links.new(dist.outputs["Points"], iop.inputs["Points"]); links.new(ci.outputs["Instances"], iop.inputs["Instance"])
    iop.inputs["Pick Instance"].default_value = True
    idn = nodes.new("GeometryNodeInputID")
    ri = nodes.new("FunctionNodeRandomValue"); ri.data_type = 'INT'; ri.inputs["Min"].default_value = 0; ri.inputs["Max"].default_value = 4
    links.new(idn.outputs[0], ri.inputs["ID"]); links.new(gi.outputs["Seed"], ri.inputs["Seed"]); links.new(ri.outputs["Value"], iop.inputs["Instance Index"])
    rr = nodes.new("FunctionNodeRandomValue"); rr.data_type = 'FLOAT_VECTOR'
    rr.inputs["Min"].default_value = (-0.4, -0.4, 0.0); rr.inputs["Max"].default_value = (0.4, 0.4, 6.283)
    links.new(idn.outputs[0], rr.inputs["ID"]); links.new(gi.outputs["Seed"], rr.inputs["Seed"]); links.new(rr.outputs["Value"], iop.inputs["Rotation"])
    rs = nodes.new("FunctionNodeRandomValue"); rs.data_type = 'FLOAT'; rs.inputs["Min"].default_value = 0.5; rs.inputs["Max"].default_value = 1.6
    sd = nodes.new("ShaderNodeMath"); sd.operation = 'ADD'; sd.inputs[1].default_value = 5
    links.new(gi.outputs["Seed"], sd.inputs[0]); links.new(idn.outputs[0], rs.inputs["ID"]); links.new(sd.outputs[0], rs.inputs["Seed"])
    sv = nodes.new("ShaderNodeCombineXYZ")
    for k in ("X", "Y", "Z"):
        links.new(rs.outputs[1], sv.inputs[k])
    links.new(sv.outputs[0], iop.inputs["Scale"])
    join = nodes.new("GeometryNodeJoinGeometry")
    links.new(iop.outputs["Instances"], join.inputs[0]); links.new(gi.outputs["Geometry"], join.inputs[0])
    links.new(join.outputs[0], go.inputs["Geometry"])
    return ng
sg = scree_group()
for (obj_name, density, seed) in (("Terrain_CragHi", 0.09, 21), ("Terrain_Crag", 0.09, 22), ("Terrain_Near", 0.03, 23)):
    ob = bpy.data.objects.get(obj_name)
    if ob is None:
        continue
    md = ob.modifiers.new("ScreeScatter", 'NODES')
    md.node_group = sg
    md["Socket_1"] = density
    md["Socket_2"] = seed
    md["Socket_3"] = rocklib

# hide the library from render/view (instances still render)
vl = bpy.context.view_layer
def find_lc(lc, name):
    if lc.collection.name == name:
        return lc
    for c in lc.children:
        r = find_lc(c, name)
        if r:
            return r
for cname in ("TreeLib", "RockLib"):
    lc = find_lc(vl.layer_collection, cname)
    if lc:
        lc.exclude = True
result = {"trees": [t.name for t in trees], "scatter": counts}
