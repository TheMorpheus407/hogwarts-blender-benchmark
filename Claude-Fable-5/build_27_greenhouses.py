"""Greenhouses: stone plinth, iron lattice frame, glass gable volumes,
terrace retaining wall. Victorian-gothic glasshouses."""
import bpy
import bmesh
import math
import hog
import hogkit as hk

hog.clear_coll('Greenhouses')
hk.init()
M = hk.M

GLASS = hog.flat_mat('GreenhouseGlass', (0.42, 0.55, 0.55), 0.08)
IRON = hog.flat_mat('IronWork', (0.02, 0.02, 0.025), 0.6)


def greenhouse(name, cx, cy, z, sx, sy, wall_h, roof_h, rot):
    # stone plinth
    hog.box(f'{name}_Plinth', 'Greenhouses', size=(sx + 0.6, sy + 0.6, 0.9),
            loc=(cx, cy, z), rot=rot, mat=M['trim'])
    zb = z + 0.9
    # glass volume (gable shape, glass on all faces)
    hog.gable(f'{name}_Glass', 'Greenhouses', sx, sy, wall_h, roof_h,
              loc=(cx, cy, zb), rot=rot, mats=[GLASS, GLASS])
    # iron frame lattice as one mesh
    bm = bmesh.new()
    t = 0.09

    def bar(x0, y0, z0, x1, y1, z1):
        vs = bmesh.ops.create_cube(bm, size=1.0)['verts']
        dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
        L = math.sqrt(dx * dx + dy * dy + dz * dz)
        bmesh.ops.scale(bm, vec=(t, t, L + t), verts=vs)
        # align +Z to the bar direction
        from mathutils import Vector
        q = Vector((dx, dy, dz)).to_track_quat('Z', 'X')
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=q.to_matrix(), verts=vs)
        bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2,
                                     (z0 + z1) / 2), verts=vs)

    hx, hy = sx / 2, sy / 2
    n_v = int(sx / 1.3)
    for i in range(n_v + 1):
        x = -hx + sx * i / n_v
        bar(x, -hy, 0, x, -hy, wall_h)
        bar(x, hy, 0, x, hy, wall_h)
        bar(x, -hy, wall_h, x, 0, wall_h + roof_h)   # rafters
        bar(x, hy, wall_h, x, 0, wall_h + roof_h)
    for sgn in (-1, 1):
        bar(-hx, sgn * hy, wall_h, hx, sgn * hy, wall_h)      # eaves
        bar(sgn * hx, -hy, 0, sgn * hx, -hy, wall_h)
        bar(sgn * hx, hy, 0, sgn * hx, hy, wall_h)
        bar(sgn * hx, -hy, wall_h, sgn * hx, 0, wall_h + roof_h)
        bar(sgn * hx, hy, wall_h, sgn * hx, 0, wall_h + roof_h)
        bar(sgn * hx, -hy, wall_h * 0.55, sgn * hx, hy, wall_h * 0.55)
    bar(-hx, 0, wall_h + roof_h, hx, 0, wall_h + roof_h)      # ridge
    # horizontal rails long sides
    for zz in (wall_h * 0.5,):
        bar(-hx, -hy, zz, hx, -hy, zz)
        bar(-hx, hy, zz, hx, hy, zz)
    ob = hog.obj_from_bm(bm, f'{name}_Frame', 'Greenhouses', IRON)
    ob.location = (cx, cy, zb)
    ob.rotation_euler = (0, 0, rot)
    # finials on ridge ends
    for sgn in (-1, 1):
        c, s = math.cos(rot), math.sin(rot)
        fx = cx + sgn * hx * c
        fy = cy + sgn * hx * s
        hk.pinnacle(f'{name}_Fin_{sgn}', 'Greenhouses',
                    (fx, fy, zb + wall_h + roof_h), r=0.18, h=1.2)


TZ = 55.4
greenhouse('GH1', 44, -76, TZ, 15, 8.5, 3.4, 2.6, 0.20)
greenhouse('GH2', 59, -73, TZ, 13, 8.0, 3.2, 2.4, -0.12)
greenhouse('GH3', 51, -63, TZ, 11, 7.0, 3.0, 2.2, 0.05)
# small connecting stone garden walls + lanterns
hog.box('GH_GardenWall1', 'Greenhouses', size=(16, 0.8, 1.4),
        loc=(51, -70, TZ), rot=0.35, mat=M['wall'])
hk.place_lantern('Greenhouses', (46, -69, TZ + 0.1))
hk.place_lantern('Greenhouses', (57, -68, TZ + 0.1))
# terrace retaining wall along the south edge of the shelf
hog.box('GH_Terrace_Wall', 'Greenhouses', size=(42, 2.2, 9),
        loc=(51, -82, TZ - 8.2), rot=0.06, mat=M['wall'])
hk.crenel_strip('GH_Terrace_Cren', 'Greenhouses', 42, base_h=0.9,
                merlon_h=0.5, t=0.4, loc=(51, -82.9, TZ + 0.8), rot=0.06)
