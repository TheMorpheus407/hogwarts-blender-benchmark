"""Compact shader-node builder: expression-style helpers that return output sockets."""
import bpy
import math

SOCK = bpy.types.NodeSocket


class NB:
    def __init__(self, mat, target='MATERIAL'):
        self.mat = mat
        if target == 'MATERIAL':
            mat.use_nodes = True
        else:
            mat.use_nodes = True
        self.nt = mat.node_tree
        self.nt.nodes.clear()
        self.nodes = self.nt.nodes
        self.links = self.nt.links
        self._x = 0
        self._y = 0

    # -------------------------------------------------------------- plumbing
    def _place(self, n):
        n.location = (self._x, self._y)
        self._y -= 190
        if self._y < -1600:
            self._y = 0
            self._x += 260

    def _in(self, node, key, val):
        if val is None:
            return
        sock = node.inputs[key]
        if isinstance(val, SOCK):
            self.links.new(val, sock)
        else:
            try:
                sock.default_value = val
            except TypeError:
                if isinstance(val, (int, float)):
                    sock.default_value = (val, val, val, 1.0) if len(sock.default_value) == 4 else (val, val, val)
                else:
                    raise

    def node(self, kind, **props):
        n = self.nodes.new(kind)
        for k, v in props.items():
            setattr(n, k, v)
        self._place(n)
        return n

    def out(self, node, key=0):
        return node.outputs[key]

    # -------------------------------------------------------------- inputs
    def geometry(self):
        return self.node('ShaderNodeNewGeometry')

    def texcoord(self):
        return self.node('ShaderNodeTexCoord')

    def attr(self, name, kind='GEOMETRY'):
        n = self.node('ShaderNodeAttribute', attribute_name=name, attribute_type=kind)
        return n

    def value(self, v):
        n = self.node('ShaderNodeValue')
        n.outputs[0].default_value = v
        return n.outputs[0]

    def rgb(self, c):
        n = self.node('ShaderNodeRGB')
        n.outputs[0].default_value = (*c[:3], 1.0)
        return n.outputs[0]

    def lightpath(self):
        return self.node('ShaderNodeLightPath')

    def objinfo(self):
        return self.node('ShaderNodeObjectInfo')

    # -------------------------------------------------------------- math
    def math(self, op, a, b=None, c=None, clamp=False):
        n = self.node('ShaderNodeMath', operation=op, use_clamp=clamp)
        self._in(n, 0, a)
        if b is not None:
            self._in(n, 1, b)
        if c is not None:
            self._in(n, 2, c)
        return n.outputs[0]

    def add(self, a, b):
        return self.math('ADD', a, b)

    def sub(self, a, b):
        return self.math('SUBTRACT', a, b)

    def mul(self, a, b):
        return self.math('MULTIPLY', a, b)

    def clamp01(self, a):
        return self.math('ADD', a, 0.0, clamp=True)

    def smooth(self, x, e0, e1):
        """smoothstep via map range (smoothstep interpolation)."""
        n = self.node('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP', clamp=True)
        self._in(n, 'Value', x)
        n.inputs['From Min'].default_value = e0
        n.inputs['From Max'].default_value = e1
        return n.outputs[0]

    def maprange(self, x, a0, a1, b0, b1, clamp=True):
        n = self.node('ShaderNodeMapRange', interpolation_type='LINEAR', clamp=clamp)
        self._in(n, 'Value', x)
        n.inputs['From Min'].default_value = a0
        n.inputs['From Max'].default_value = a1
        n.inputs['To Min'].default_value = b0
        n.inputs['To Max'].default_value = b1
        return n.outputs[0]

    def vmath(self, op, a, b=None, scale=None):
        n = self.node('ShaderNodeVectorMath', operation=op)
        self._in(n, 0, a)
        if b is not None:
            self._in(n, 1, b)
        if scale is not None:
            n.inputs['Scale'].default_value = scale if not isinstance(scale, SOCK) else 1.0
            if isinstance(scale, SOCK):
                self.links.new(scale, n.inputs['Scale'])
        return n

    def sepxyz(self, v):
        n = self.node('ShaderNodeSeparateXYZ')
        self._in(n, 0, v)
        return n

    def combxyz(self, x=0.0, y=0.0, z=0.0):
        n = self.node('ShaderNodeCombineXYZ')
        self._in(n, 0, x)
        self._in(n, 1, y)
        self._in(n, 2, z)
        return n.outputs[0]

    def mapping(self, vec, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), kind='POINT'):
        n = self.node('ShaderNodeMapping', vector_type=kind)
        self._in(n, 'Vector', vec)
        self._in(n, 'Location', loc)
        self._in(n, 'Rotation', rot)
        self._in(n, 'Scale', scale)
        return n.outputs[0]

    def mix(self, fac, a, b, blend='MIX', dtype='RGBA'):
        n = self.node('ShaderNodeMix', data_type=dtype, blend_type=blend, clamp_factor=True)
        self._in(n, 0, fac)
        if dtype == 'RGBA':
            ia, ib, io = 6, 7, 2
        elif dtype == 'FLOAT':
            ia, ib, io = 2, 3, 0
        else:
            ia, ib, io = 4, 5, 1
        if isinstance(a, tuple):
            a = (*a, 1.0) if (dtype == 'RGBA' and len(a) == 3) else a
        if isinstance(b, tuple):
            b = (*b, 1.0) if (dtype == 'RGBA' and len(b) == 3) else b
        self._in(n, ia, a)
        self._in(n, ib, b)
        return n.outputs[io]

    def ramp(self, fac, stops, interp='LINEAR'):
        n = self.node('ShaderNodeValToRGB')
        n.color_ramp.interpolation = interp
        els = n.color_ramp.elements
        # resize
        while len(els) < len(stops):
            els.new(0.5)
        while len(els) > len(stops):
            els.remove(els[-1])
        for e, (p, c) in zip(els, stops):
            e.position = p
            e.color = (*c[:3], c[3] if len(c) > 3 else 1.0)
        self._in(n, 'Fac', fac)
        return n.outputs['Color']

    def rgb2bw(self, c):
        n = self.node('ShaderNodeRGBToBW')
        self._in(n, 0, c)
        return n.outputs[0]

    def huesat(self, col, sat=1.0, val=1.0, hue=0.5, fac=1.0):
        n = self.node('ShaderNodeHueSaturation')
        self._in(n, 'Color', col)
        n.inputs['Saturation'].default_value = sat
        n.inputs['Value'].default_value = val
        n.inputs['Hue'].default_value = hue
        n.inputs['Fac'].default_value = fac
        return n.outputs[0]

    # -------------------------------------------------------------- textures
    def noise(self, vec, scale=5.0, detail=2.0, rough=0.5, dist=0.0, lac=2.0, out='Fac'):
        n = self.node('ShaderNodeTexNoise', noise_dimensions='3D')
        self._in(n, 'Vector', vec)
        self._in(n, 'Scale', scale)
        self._in(n, 'Detail', detail)
        self._in(n, 'Roughness', rough)
        self._in(n, 'Distortion', dist)
        self._in(n, 'Lacunarity', lac)
        return n.outputs[out]

    def voronoi(self, vec, scale=5.0, rand=1.0, feature='F1', out='Distance', smooth=0.0, metric='EUCLIDEAN'):
        n = self.node('ShaderNodeTexVoronoi', voronoi_dimensions='3D', feature=feature, distance=metric)
        self._in(n, 'Vector', vec)
        self._in(n, 'Scale', scale)
        self._in(n, 'Randomness', rand)
        if feature == 'SMOOTH_F1':
            self._in(n, 'Smoothness', smooth)
        return n.outputs[out]

    def brick(self, vec, w=0.6, h=0.3, mortar=0.02, msmooth=0.08, c1=(0.5, 0.5, 0.5), c2=(0.3, 0.3, 0.3),
              cm=(0.05, 0.05, 0.05), offset=0.5, bias=0.0, freq=2, squash=1.0):
        n = self.node('ShaderNodeTexBrick', offset=offset, offset_frequency=freq, squash=squash, squash_frequency=2)
        self._in(n, 'Vector', vec)
        n.inputs['Scale'].default_value = 1.0
        n.inputs['Brick Width'].default_value = w
        n.inputs['Row Height'].default_value = h
        n.inputs['Mortar Size'].default_value = mortar
        n.inputs['Mortar Smooth'].default_value = msmooth
        n.inputs['Bias'].default_value = bias
        self._in(n, 'Color1', (*c1[:3], 1.0))
        self._in(n, 'Color2', (*c2[:3], 1.0))
        self._in(n, 'Mortar', (*cm[:3], 1.0))
        return n

    def wave(self, vec, scale=5.0, dist=5.0, detail=2.0, wtype='BANDS', direction='X', profile='SIN', rings='Z'):
        n = self.node('ShaderNodeTexWave', wave_type=wtype, bands_direction=direction, rings_direction=rings, wave_profile=profile)
        self._in(n, 'Vector', vec)
        self._in(n, 'Scale', scale)
        self._in(n, 'Distortion', dist)
        self._in(n, 'Detail', detail)
        return n.outputs['Fac']

    def bump(self, height, strength=1.0, dist=0.05, normal=None, invert=False):
        n = self.node('ShaderNodeBump', invert=invert)
        self._in(n, 'Height', height)
        n.inputs['Strength'].default_value = strength
        n.inputs['Distance'].default_value = dist
        if normal is not None:
            self._in(n, 'Normal', normal)
        return n.outputs['Normal']

    def bevel(self, radius=0.05, samples=6):
        n = self.node('ShaderNodeBevel', samples=samples)
        n.inputs['Radius'].default_value = radius
        return n.outputs['Normal']

    def ao(self, dist=1.5, samples=8, inside=False, local=True, color=(1, 1, 1)):
        n = self.node('ShaderNodeAmbientOcclusion', samples=samples, inside=inside, only_local=local)
        n.inputs['Distance'].default_value = dist
        return n.outputs['AO']

    # -------------------------------------------------------------- shaders
    def principled(self, **kw):
        n = self.node('ShaderNodeBsdfPrincipled')
        for k, v in kw.items():
            key = k.replace('_', ' ')
            self._in(n, key, v)
        return n

    def emission(self, color, strength):
        n = self.node('ShaderNodeEmission')
        self._in(n, 'Color', color)
        self._in(n, 'Strength', strength)
        return n.outputs[0]

    def mixshader(self, fac, a, b):
        n = self.node('ShaderNodeMixShader')
        self._in(n, 0, fac)
        self.links.new(a, n.inputs[1])
        self.links.new(b, n.inputs[2])
        return n.outputs[0]

    def addshader(self, a, b):
        n = self.node('ShaderNodeAddShader')
        self.links.new(a, n.inputs[0])
        self.links.new(b, n.inputs[1])
        return n.outputs[0]

    def output(self, surface=None, volume=None, displacement=None, target='ALL'):
        n = self.node('ShaderNodeOutputMaterial', target=target)
        if surface is not None:
            self.links.new(surface, n.inputs['Surface'])
        if volume is not None:
            self.links.new(volume, n.inputs['Volume'])
        if displacement is not None:
            self.links.new(displacement, n.inputs['Displacement'])
        return n


def get_mat(name):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    return m
