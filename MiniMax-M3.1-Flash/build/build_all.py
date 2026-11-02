"""Full rebuild: landscape -> castle -> (optional) preview render."""
import bpy, os, sys, time, traceback

BUILD = "/home/morpheus/Documents/Morpheus-Produktion/Benchmarks/Blender/MiniMax-M3.1-Flash/build"
ROOT = os.path.dirname(BUILD)
if BUILD not in sys.path:
    sys.path.insert(0, BUILD)

RENDER = globals().get('RENDER', True)
RES = globals().get('RES', (1600, 900))
SAMPLES = globals().get('SAMPLES', 48)
OUT = globals().get('OUT', os.path.join(ROOT, "_preview_castle.png"))


def run(script, extra=None):
    ns = {"__file__": os.path.join(BUILD, script), "__name__": "__main__"}
    if extra:
        ns.update(extra)
    exec(compile(open(os.path.join(BUILD, script)).read(), script, "exec"), ns)


def audit_shader_graphs():
    """Fail loudly on cyclic node graphs.

    A self-referencing link (node output -> its own input) makes Cycles
    evaluate the socket as zero, which silently turns a whole material black.
    This has to be a hard error, never a rendering artefact.
    """
    problems = []
    trees = [("MAT " + m.name, m.node_tree) for m in bpy.data.materials
             if m.use_nodes and m.node_tree]
    trees += [("WORLD " + w.name, w.node_tree) for w in bpy.data.worlds
              if w.use_nodes and w.node_tree]
    for label, nt in trees:
        adj = {}
        for l in nt.links:
            if l.from_node is l.to_node:
                problems.append("%s: self-loop on %s (%s -> %s)"
                                % (label, l.from_node.name,
                                   l.from_socket.name, l.to_socket.name))
                continue
            adj.setdefault(l.from_node.name, set()).add(l.to_node.name)
        color, stack = {}, []

        def dfs(n):
            color[n] = 1
            stack.append(n)
            for m in adj.get(n, ()):
                if color.get(m, 0) == 0:
                    dfs(m)
                elif color.get(m) == 1:
                    problems.append("%s: cycle %s" % (label, stack[stack.index(m):] + [m]))
            color[n] = 2
            stack.pop()

        for n in list(adj.keys()):
            if color.get(n, 0) == 0:
                dfs(n)
    if problems:
        raise RuntimeError("cyclic shader graph(s):\n  " + "\n  ".join(problems))
    return True


t0 = time.time()
try:
    run("p1_blockout.py", {"RENDER_PREVIEW": False})
    run("p2_castle.py")
    run("p4_landscape.py")
    run("p5_props.py")
    run("p3_light.py")
    audit_shader_graphs()
    ok = True
    err = None
except Exception:
    ok = False
    err = traceback.format_exc()[-3000:]

if ok and RENDER:
    scn = bpy.context.scene
    scn.render.resolution_x, scn.render.resolution_y = RES
    scn.cycles.samples = SAMPLES
    scn.render.filepath = OUT
    bpy.ops.render.render(write_still=True)

if not ok:
    raise RuntimeError("build failed: " + str(err))
result = {"ok": ok, "error": err, "elapsed": round(time.time() - t0, 1),
          "objects": len(bpy.data.objects),
          "faces": sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')}
