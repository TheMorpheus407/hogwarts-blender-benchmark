"""Final render setup: compositor glare (fog glow), denoiser, 4K settings."""
import bpy

scene = bpy.context.scene

# ---------------------------------------------------------------- compositor
nt = None
if hasattr(scene, 'compositing_node_group'):
    ng = scene.compositing_node_group
    if ng is None:
        ng = bpy.data.node_groups.new('Compositing', 'CompositorNodeTree')
        scene.compositing_node_group = ng
    nt = ng
elif hasattr(scene, 'node_tree'):
    scene.use_nodes = True
    nt = scene.node_tree

if nt is not None:
    nt.nodes.clear()
    rl = nt.nodes.new('CompositorNodeRLayers')
    src_sock = rl.outputs['Image']
    if hasattr(scene, 'compositing_node_group') and \
            scene.compositing_node_group == nt:
        # group-style compositor (Blender 5): output socket on the group
        try:
            if not any(getattr(s, 'in_out', '') == 'OUTPUT'
                       for s in nt.interface.items_tree):
                nt.interface.new_socket('Image', in_out='OUTPUT',
                                        socket_type='NodeSocketColor')
        except Exception:
            pass
        n_out = nt.nodes.new('NodeGroupOutput')
        dst_sock = n_out.inputs[0]
    else:
        comp = nt.nodes.new('CompositorNodeComposite')
        dst_sock = comp.inputs['Image']

    glare = nt.nodes.new('CompositorNodeGlare')
    # Blender 5: options are menu/value input sockets
    for tval in ('FOG_GLOW', 'Fog Glow', 'BLOOM', 'Bloom'):
        try:
            glare.inputs['Type'].default_value = tval
            break
        except Exception:
            continue
    for qval in ('HIGH', 'High'):
        try:
            glare.inputs['Quality'].default_value = qval
            break
        except Exception:
            continue
    for iname, val in (('Threshold', 1.6), ('Smoothness', 0.15),
                       ('Strength', 0.32), ('Saturation', 1.0),
                       ('Size', 0.6)):
        try:
            glare.inputs[iname].default_value = val
        except Exception:
            pass
    nt.links.new(src_sock, glare.inputs['Image'])
    nt.links.new(glare.outputs['Image'], dst_sock)
    scene.render.use_compositing = True

# ---------------------------------------------------------------- render cfg
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = 1024
scene.cycles.use_denoising = True
try:
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    scene.cycles.denoising_use_gpu = True
except Exception:
    pass
scene.render.resolution_x = 3840
scene.render.resolution_y = 2160
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_depth = '16'
scene.render.image_settings.compression = 50
