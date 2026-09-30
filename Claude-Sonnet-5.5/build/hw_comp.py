"""Compositor: cinematic bloom on windows / moon, vignette, gentle colour grade (Blender 5.x node-group compositor)."""
import bpy


def _set_menu(sock, options):
    for o in options:
        try:
            sock.default_value = o
            return o
        except Exception:
            continue
    return None


def build(bloom=0.55, vignette=0.42, threshold=0.9, size=0.55):
    sc = bpy.context.scene
    old = bpy.data.node_groups.get('HW_Comp')
    if old is not None:
        bpy.data.node_groups.remove(old)
    ng = bpy.data.node_groups.new('HW_Comp', 'CompositorNodeTree')
    ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    nd, lk = ng.nodes, ng.links
    rl = nd.new('CompositorNodeRLayers')
    rl.location = (-900, 0)
    gl = nd.new('CompositorNodeGlare')
    gl.location = (-600, 100)
    used = _set_menu(gl.inputs['Type'], ['Bloom', 'Fog Glow', 'FOG_GLOW', 'BLOOM'])
    _set_menu(gl.inputs['Quality'], ['High', 'HIGH'])
    gl.inputs['Threshold'].default_value = threshold
    gl.inputs['Strength'].default_value = bloom
    gl.inputs['Size'].default_value = size
    gl.inputs['Smoothness'].default_value = 0.35
    lk.new(rl.outputs['Image'], gl.inputs['Image'])
    # vignette from image coordinates (smooth radial falloff, no hard edge)
    ic = nd.new('CompositorNodeImageCoordinates')
    ic.location = (-800, -300)
    lk.new(rl.outputs['Image'], ic.inputs['Image'])
    sub = nd.new('ShaderNodeVectorMath')
    sub.operation = 'SUBTRACT'
    sub.location = (-620, -300)
    lk.new(ic.outputs['Normalized'], sub.inputs[0])
    sub.inputs[1].default_value = (0.5, 0.5, 0.0)
    ln = nd.new('ShaderNodeVectorMath')
    ln.operation = 'LENGTH'
    ln.location = (-450, -300)
    lk.new(sub.outputs[0], ln.inputs[0])
    mr = nd.new('ShaderNodeMapRange')
    mr.interpolation_type = 'SMOOTHSTEP'
    mr.location = (-280, -300)
    mr.inputs['From Min'].default_value = 0.30
    mr.inputs['From Max'].default_value = 0.72
    lk.new(ln.outputs[1], mr.inputs['Value'])
    mixv = nd.new('ShaderNodeMix')
    mixv.data_type = 'RGBA'
    mixv.blend_type = 'MULTIPLY'
    mixv.location = (-150, 0)
    mixv.inputs[0].default_value = 1.0
    lk.new(gl.outputs[0], mixv.inputs[6])
    mv = nd.new('ShaderNodeMix')
    mv.data_type = 'RGBA'
    mv.location = (-120, -300)
    mv.inputs[6].default_value = (1.0, 1.0, 1.0, 1.0)
    mv.inputs[7].default_value = (1 - vignette, 1 - vignette, 1 - vignette * 0.85, 1.0)
    lk.new(mr.outputs[0], mv.inputs[0])
    lk.new(mv.outputs[2], mixv.inputs[7])
    # grade
    cb = nd.new('CompositorNodeColorBalance')
    cb.location = (100, 0)
    try:
        _set_menu(cb.inputs['Type'], ['Lift/Gamma/Gain', 'LIFT_GAMMA_GAIN'])
        cb.inputs['Factor'].default_value = 1.0
    except Exception:
        pass
    lk.new(mixv.outputs[2], cb.inputs['Image'])
    go = nd.new('NodeGroupOutput')
    go.location = (400, 0)
    lk.new(cb.outputs[0], go.inputs[0])
    sc.compositing_node_group = ng
    sc.render.use_compositing = True
    return dict(glare_type=used)


def disable():
    sc = bpy.context.scene
    sc.render.use_compositing = False
