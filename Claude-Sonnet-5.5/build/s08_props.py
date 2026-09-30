"""Stage 3b: props (covered bridge, owlery, hut + smoke, standing stones, foreground pines)."""
import bpy
import numpy as np
import math
import time
import importlib
import hw_layout as L
import hw_geo
import hw_gothic as G
import hw_towers as TW
import hw_walls as W
import hw_props as PR
import hw_trees as TR
import hw_scene as S
import hw_mats
import hw_fx
import s01_terrain as s1
for _m in (L, hw_geo, G, TW, W, PR, TR, S, hw_mats):
    importlib.reload(_m)
from hw_geo import Geo, boxes

Z0 = L.Z0


def finish(g, name, coll):
    g.consolidate()
    obj = g.to_object(bpy, coll, name)
    return obj, g.count()


def build_bridge(coll, seed=61):
    rng = np.random.default_rng(seed)
    g = Geo('Castle_CoveredBridge')
    b = L.BRIDGE
    PR.covered_bridge(g, b['A'], b['B'], s1.SAMPLER, rng)
    # small gate tower on the castle side
    TW.square_tower(g, -208.0, 9.0, Z0, 7.0, 7.0, 15.0, rng, bands=(6.0,), tiers=[(7.0, 1, G.window_lancet(0.9, 2.8, 1))],
                    hip=dict(pitch=50), lit_p=0.8, found=10.0, corner_pinnacles=True)
    return finish(g, 'Castle_CoveredBridge', coll)


def build_owlery(coll, seed=62):
    rng = np.random.default_rng(seed)
    g = Geo('Castle_Owlery')
    o = L.OWLERY
    z = float(s1.SAMPLER.z(o['x'], o['y']))
    PR.owlery(g, o['x'], o['y'], z, o['R'], o['shaft'], rng)
    return finish(g, 'Castle_Owlery', coll)


def build_hut(coll, seed=63):
    rng = np.random.default_rng(seed)
    g = Geo('Nature_Hut')
    h = L.HUT
    smp = s1.SAMPLER
    z = float(smp.z(h['x'], h['y']))
    top = PR.hut(g, h['x'], h['y'], z, h['yaw'], rng, smp)
    obj, cnt = finish(g, 'Nature_Hut', coll)
    # smoke volume box around the plume
    S.remove_object('FX_HutSmoke')
    fx = S.ensure_collection('FX')
    mesh = bpy.data.meshes.new('FX_HutSmoke')
    cx, cy, cz = top
    hx, hy, hz0, hz1 = 22.0, 22.0, cz - 1.0, cz + 38.0
    V = np.array([[cx - hx, cy - hy, hz0], [cx + hx, cy - hy, hz0], [cx + hx, cy + hy, hz0], [cx - hx, cy + hy, hz0],
                  [cx - hx, cy - hy, hz1], [cx + hx, cy - hy, hz1], [cx + hx, cy + hy, hz1], [cx - hx, cy + hy, hz1]], np.float32)
    F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh.from_pydata(V.tolist(), [], F)
    mesh.update()
    mat = PR.smoke_material('M_Smoke', x0=cx, y0=cy, z0=cz, wind=(0.9, 0.4))
    mesh.materials.append(mat)
    o = bpy.data.objects.new('FX_HutSmoke', mesh)
    fx.objects.link(o)
    o.visible_shadow = False
    o.display_type = 'BOUNDS'
    return obj, cnt


def build_stones(coll, seed=64):
    rng = np.random.default_rng(seed)
    g = Geo('Nature_StandingStones')
    st = L.STONES
    PR.standing_stones(g, st['x'], st['y'], s1.SAMPLER, rng)
    for m in ('M_RockChunk',):
        g.mid(m)
    return finish(g, 'Nature_StandingStones', coll)


def build_hero_pines(coll, seed=65):
    rng = np.random.default_rng(seed)
    g = Geo('Nature_HeroPines')
    protos = [TR.hero_pine(rng, height=hh, crown=cc, name='hp%d' % i, whorls=9, spray_len=1.9)
              for i, (hh, cc) in enumerate(((27.0, 7.5), (23.0, 6.8), (30.0, 8.0)))]
    smp = s1.SAMPLER
    for k, (x, y, sc) in enumerate(L.HERO_PINES):
        z = float(smp.z(x, y))
        g.add_geo(protos[k % 3], pos=(x, y, z - 0.6), yaw=rng.random() * 6.28, scale=sc)
    return finish(g, 'Nature_HeroPines', coll)


def build_owls(coll, seed=66):
    rng = np.random.default_rng(seed)
    g = Geo('Nature_Owls')
    protos = [PR.flying_owl(rng, phase=ph, span=1.0 + 0.12 * i) for i, ph in enumerate((0.1, 0.9, 1.7, 2.5, 3.3, 4.1, 5.0))]
    o = L.OWLERY
    z_o = float(s1.SAMPLER.z(o['x'], o['y']))
    n = 0
    for k in range(9):          # circling the owlery
        a = rng.random() * 2 * math.pi
        r = rng.uniform(16.0, 60.0)
        pos = (o['x'] + r * math.cos(a), o['y'] + r * math.sin(a), z_o + rng.uniform(22.0, 58.0))
        head = a + math.pi / 2 + rng.normal(0, 0.35)
        g.add_geo(protos[k % 7], pos=pos, yaw=head, scale=rng.uniform(1.6, 2.4))
        n += 1
    for k in range(7):          # a few across the castle towers and lake
        pos = (rng.uniform(-260.0, -120.0), rng.uniform(-60.0, 60.0), rng.uniform(96.0, 150.0))
        g.add_geo(protos[(k + 2) % 7], pos=pos, yaw=rng.uniform(0, 6.28), scale=rng.uniform(1.8, 2.6))
    return finish(g, 'Nature_Owls', coll)


BUILDERS = dict(bridge=build_bridge, owlery=build_owlery, hut=build_hut, stones=build_stones, pines=build_hero_pines, owls=build_owls)
NAMES = dict(bridge='Castle_CoveredBridge', owlery='Castle_Owlery', hut='Nature_Hut', stones='Nature_StandingStones', pines='Nature_HeroPines', owls='Nature_Owls')


def run(which=None):
    hw_mats.build_all_props()
    hw_mats.build_all_nature()
    cast = S.ensure_collection('Castle')
    nat = S.ensure_collection('Nature')
    out = {}
    for k in (which or BUILDERS.keys()):
        S.remove_object(NAMES[k])
        t0 = time.time()
        coll = cast if NAMES[k].startswith('Castle') else nat
        obj, cnt = BUILDERS[k](coll)
        out[k] = (cnt, round(time.time() - t0, 2))
    return out
