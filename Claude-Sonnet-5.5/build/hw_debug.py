"""Debug aids: back-face override material, scene statistics, orphan purge."""
import bpy
import numpy as np
from hw_nodes import NB, get_mat


def backface_material(name='M_DEBUG_Backface'):
    nb = NB(get_mat(name))
    geo = nb.geometry()
    bf = geo.outputs['Backfacing']
    red = nb.emission((1.0, 0.0, 0.0, 1.0), 6.0)
    gry = nb.emission((0.4, 0.4, 0.4, 1.0), 1.0)
    nb.output(nb.mixshader(bf, gry, red))
    return nb.mat


def set_override(on=True):
    vl = bpy.context.view_layer
    if on:
        vl.material_override = backface_material()
    else:
        vl.material_override = None
        m = bpy.data.materials.get('M_DEBUG_Backface')
        if m is not None:
            bpy.data.materials.remove(m)


def stats():
    out = {}
    tot_f = 0
    tot_o = 0
    for o in bpy.data.objects:
        if o.type == 'MESH':
            tot_o += 1
            tot_f += len(o.data.polygons)
    out['mesh_objects'] = tot_o
    out['mesh_faces'] = tot_f
    out['collections'] = [(c.name, len(c.objects)) for c in bpy.data.collections]
    out['orphans'] = dict(meshes=sum(1 for m in bpy.data.meshes if m.users == 0),
                          materials=sum(1 for m in bpy.data.materials if m.users == 0),
                          node_groups=sum(1 for n in bpy.data.node_groups if n.users == 0),
                          images=sum(1 for i in bpy.data.images if i.users == 0),
                          lights=sum(1 for l in bpy.data.lights if l.users == 0),
                          cameras=sum(1 for c in bpy.data.cameras if c.users == 0))
    return out


def count_windows():
    """Number of glass panes (quads/tris with glow attribute) and how many are lit."""
    n_all = 0
    n_lit = 0
    vals = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.name.startswith(('Castle_', 'Nature_Hut')):
            continue
        me = o.data
        att = me.attributes.get('glow')
        if att is None:
            continue
        a = np.zeros(len(att.data), dtype=np.float32)
        att.data.foreach_set('value', a) if False else att.data.foreach_get('value', a)
        m = a > -1
        n_all += int(m.sum())
        n_lit += int((a > 0.05).sum())
        vals.append(a[a > 0.05])
    v = np.concatenate(vals) if vals else np.zeros(1)
    return dict(glass_faces=n_all, lit_faces=n_lit, glow_mean=float(v.mean()), glow_std=float(v.std()),
                glow_min=float(v.min()), glow_max=float(v.max()))


def probe_backfaces(image_path, cam, n=300, seed=1, skip_prefix=('FX_',), detail=0):
    """Map red (back-face) pixels of a debug render back to scene objects via ray casts."""
    import numpy as np
    from mathutils import Vector
    img = bpy.data.images.load(image_path, check_existing=False)
    try:
        img.colorspace_settings.name = 'Non-Color'
        W, H = img.size
        px = np.empty(W * H * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
    finally:
        bpy.data.images.remove(img)
    px = px.reshape(H, W, 4)
    ys, xs = np.nonzero((px[..., 0] - px[..., 1]) > 0.15)
    total = int(len(xs))
    rng = np.random.default_rng(seed)
    if total > n:
        sel = rng.choice(total, n, replace=False)
        xs, ys = xs[sel], ys[sel]
    cd = cam.data
    sw = cd.sensor_width
    M = cam.matrix_world
    R3 = M.to_3x3()
    org = M.translation
    dg = bpy.context.evaluated_depsgraph_get()
    scn = bpy.context.scene
    groups = {}
    for x, y in zip(xs, ys):
        u = (x + 0.5) / W - 0.5
        v = ((y + 0.5) / H - 0.5) * (H / W)
        d = (R3 @ Vector(((u + cd.shift_x) * sw / cd.lens, (v + cd.shift_y) * sw / cd.lens, -1.0))).normalized()
        o = org.copy()
        for _ in range(8):
            hit, loc, nrm, idx, ob, mat = scn.ray_cast(dg, o, d)
            if not hit:
                break
            if ob.name.startswith(skip_prefix):
                o = loc + d * 1e-3
                continue
            key = ob.name
            g = groups.setdefault(key, dict(n=0, back=0, pts=[], idx=[], polys={}))
            g['n'] += 1
            if nrm.dot(d) > 0:
                g['back'] += 1
                g['pts'].append(tuple(round(c, 1) for c in loc))
                g['idx'].append(int(idx))
                me = ob.data
                if detail and idx not in g['polys'] and len(g['polys']) < detail and idx < len(me.polygons):
                    p = me.polygons[idx]
                    mi = p.material_index
                    g['polys'][int(idx)] = dict(
                        mat=me.materials[mi].name if mi < len(me.materials) else None,
                        n=[round(c, 2) for c in p.normal],
                        v=[[round(c, 1) for c in me.vertices[i].co] for i in p.vertices])
            break
    out = {}
    for k, g in groups.items():
        pts = np.array(g['pts']) if g['pts'] else np.zeros((0, 3))
        out[k] = dict(n=g['n'], back=g['back'],
                      lo=pts.min(0).round(1).tolist() if len(pts) else None,
                      hi=pts.max(0).round(1).tolist() if len(pts) else None,
                      sample=g['pts'][:4], faces=g['idx'][:4], polys=list(g['polys'].values()))
    return dict(red_pixels=total, sampled=int(len(xs)), objects=out)


def run_sweep(cams, prefix='dbg', res=(960, 540), samples=6, n_probe=250, hide=('FX_', 'Lake_Mist', 'Haze', 'Gorge'),
              out_dir=None):
    """Render back-face debug images for `cams` and map red pixels to objects.

    cams: {name: object_name | (loc, target, lens)}.  Returns a compact summary per camera.
    """
    import os
    import hw_scene as S
    import hw_render as R
    out_dir = out_dir or os.path.join(S.BASE, '_work')
    sc = bpy.context.scene
    old_cam = sc.camera
    hidden = []
    for o in bpy.data.objects:
        if o.name.startswith(hide) and not o.hide_render:
            o.hide_render = True
            hidden.append(o)
    R.configure(samples=samples, res=res)
    set_override(True)
    summary = {}
    try:
        for k, spec in cams.items():
            tmp = None
            if isinstance(spec, str):
                cam = bpy.data.objects[spec]
            else:
                loc, tgt, ln = spec
                cam = tmp = S.make_camera('Cam_Test_' + k, loc, tgt, lens=ln)
                bpy.context.view_layer.update()
            sc.camera = cam
            path = os.path.join(out_dir, '%s_%s.png' % (prefix, k))
            sc.render.filepath = path
            bpy.ops.render.render(write_still=True)
            r = probe_backfaces(path, cam, n=n_probe)
            objs = sorted(r['objects'].items(), key=lambda kv: -kv[1]['back'])
            summary[k] = dict(red=r['red_pixels'],
                              objs=[(o, v['n'], v['back'], v['lo'], v['hi']) for o, v in objs[:8] if v['back'] > 0])
            if tmp is not None:
                d = tmp.data
                bpy.data.objects.remove(tmp, do_unlink=True)
                bpy.data.cameras.remove(d)
    finally:
        set_override(False)
        for o in hidden:
            o.hide_render = False
        sc.camera = old_cam
    return summary


def inspect_pixels(cam, pixels, size=(960, 540), skip_prefix=('FX_',)):
    """Ray-cast through image pixels (x, y from the top-left, as displayed) and describe what is hit."""
    from mathutils import Vector
    W, H = size
    cd = cam.data
    sw = cd.sensor_width
    M = cam.matrix_world
    R3 = M.to_3x3()
    org = M.translation
    dg = bpy.context.evaluated_depsgraph_get()
    scn = bpy.context.scene
    res = []
    for x, y in pixels:
        u = (x + 0.5) / W - 0.5
        v = (((H - 1 - y) + 0.5) / H - 0.5) * (H / W)
        d = (R3 @ Vector(((u + cd.shift_x) * sw / cd.lens, (v + cd.shift_y) * sw / cd.lens, -1.0))).normalized()
        o = org.copy()
        for _ in range(8):
            hit, loc, nrm, idx, ob, mat = scn.ray_cast(dg, o, d)
            if not hit:
                res.append(dict(px=(x, y), hit=False))
                break
            if ob.name.startswith(skip_prefix):
                o = loc + d * 1e-3
                continue
            e = dict(px=(x, y), obj=ob.name, loc=[round(c, 2) for c in loc], dot=round(nrm.dot(d), 2))
            me = ob.data
            if hasattr(me, 'polygons') and idx < len(me.polygons):
                p = me.polygons[idx]
                mi = p.material_index
                e['mat'] = me.materials[mi].name if mi < len(me.materials) else None
                e['verts'] = [[round(c, 2) for c in me.vertices[i].co] for i in p.vertices]
                e['n'] = [round(c, 2) for c in p.normal]
            res.append(e)
            break
    return res
