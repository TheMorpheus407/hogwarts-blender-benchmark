"""Compare the OLD crag joint term with the NEW one on the real mesh grid."""
import sys, types, math
import numpy as np

BUILD = "/home/morpheus/Documents/Morpheus-Produktion/Benchmarks/Blender/MiniMax-M3.1-Flash/build"
sys.path.insert(0, BUILD)

bpy = types.ModuleType("bpy")
bmesh = types.ModuleType("bmesh")


class _V:
    def __init__(self, *a, **k):
        self.x = self.y = self.z = 0.0


mathutils = types.ModuleType("mathutils")
mathutils.Vector = _V
mathutils.Matrix = _V
mathutils.Euler = _V
mu_geom = types.ModuleType("mathutils.geometry")
mu_geom.tessellate_polygon = lambda *a, **k: []
mathutils.geometry = mu_geom
mu_noise = types.ModuleType("mathutils.noise")
mu_noise.noise = lambda *a, **k: 0.0
mu_noise.turbulence = lambda *a, **k: 0.0
mathutils.noise = mu_noise
sys.modules.update({"bpy": bpy, "bmesh": bmesh, "mathutils": mathutils,
                    "mathutils.geometry": mu_geom, "mathutils.noise": mu_noise})

import hg_np as N            # noqa: E402
import hg_cfg as C           # noqa: E402
import hg_land as LD         # noqa: E402

NTHETA, NZ = LD.make_crag.__defaults__[0], LD.make_crag.__defaults__[1]
print(f"crag mesh: {NTHETA} x {NZ} = {NTHETA*NZ} verts")


def grid(ntheta, nz):
    th = np.linspace(0.0, 2 * np.pi, ntheta, endpoint=False)
    H = np.linspace(-26.0, C.PLATEAU_Z, nz)
    T, Z = np.meshgrid(th, H, indexing="ij")
    return T, Z


T, Z = grid(NTHETA, NZ)
S = T * 120.0


def old_joint(T_, Z_):
    s = T_ * 120.0
    wd1, wd2, cellr = N.worley((s + 0.85 * Z_) / 10.0, Z_ / 9.0, 1.0, seed=131,
                                jitter=0.9)
    db = np.maximum((wd2 - wd1) * 0.5, 0.0)
    return -2.3 * (0.45 + 0.90 * cellr) * np.exp(-(db / 0.34) ** 2)


def new_joint(T_, Z_):
    s = T_ * 120.0
    wd1, wd2, _ = N.worley((s + 0.85 * Z_) / 10.0, Z_ / 9.0, 1.0, seed=131,
                           jitter=0.9)
    db = np.maximum((wd2 - wd1) * 0.5, 0.0)
    jd = 1.85 + 1.45 * N.fbm(s / 26.0, Z_ / 24.0, 3, seed=137)
    j1 = -jd * np.exp(-(db / 0.40) ** 2)
    wd3, wd4, _ = N.worley((s - 1.05 * Z_) / 8.0, Z_ / 9.0, 1.0, seed=211,
                           jitter=0.95)
    db2 = np.maximum((wd4 - wd3) * 0.5, 0.0)
    jd2 = 0.75 + 0.60 * N.fbm(s / 15.0, Z_ / 17.0, 3, seed=217)
    j2 = -jd2 * np.exp(-(db2 / 0.42) ** 2)
    return j1 + j2


JO, JN = old_joint(T, Z), new_joint(T, Z)
print()
print("=== joint term statistics ===")
print(f"  OLD  mean={JO.mean():+.3f} min={JO.min():+.3f} max={JO.max():+.3f}")
print(f"  NEW  mean={JN.mean():+.3f} min={JN.min():+.3f} max={JN.max():+.3f}")
print(f"  mean shift = {JN.mean()-JO.mean():+.3f} m")
print(f"  max |dJ| between adjacent columns  OLD={np.abs(np.diff(JO,axis=0)).max():.3f}"
      f"  NEW={np.abs(np.diff(JN,axis=0)).max():.3f}")
print(f"  column pairs > 0.8 m jump        OLD={(np.abs(np.diff(JO,axis=0))>0.8).sum()}"
      f"  NEW={(np.abs(np.diff(JN,axis=0))>0.8).sum()}")

# the whole crag radius, old vs new (bias kept as-is)
def radius_with(joint):
    u = np.clip((Z + 26.0) / (C.PLATEAU_Z + 26.0), 0.0, 1.0)
    ex = np.cos(T) / C.CRAG_TOP_RX
    ey = np.sin(T) / C.CRAG_TOP_RY
    rt = 1.0 / np.sqrt(ex * ex + ey * ey)
    d_ang = np.arctan2(np.sin(T), np.cos(T))
    rt = rt * (1.0 + C.CRAG_EAST_BULGE * np.exp(-(d_ang / C.CRAG_BULGE_SIGMA) ** 2))
    rc = rt + C.CRAG_BATTER
    rbase = rc + 26.0
    R = np.where(u < 0.05, rbase + (rc - rbase) * (u / 0.05),
                 np.where(u < 0.955, rc + 1.4 * ((u - 0.05) / 0.905),
                          rc + 1.4 - (C.CRAG_BATTER + 1.4) *
                          N.smoothstep(0.0, 1.0, (u - 0.955) / 0.045)))
    return R + LD.crag_disp(T, Z) - joint + joint   # same for both


RO = radius_with(JO)
RN = LD.crag_radius(T, Z)
print()
print("=== crag radius, old vs new (same bias) ===")
print(f"  OLD mean={RO.mean():.3f}  NEW mean={RN.mean():.3f}"
      f"  drift={RN.mean()-RO.mean():+.3f} m")
print(f"  OLD max={RO.max():.3f}  NEW max={RN.max():.3f}")

dR = np.abs(np.diff(RN, axis=0))
ds = 2 * math.pi * 190.0 / NTHETA
print()
print("=== NEW: radial change between adjacent mesh columns ===")
for p in (50, 90, 99, 99.9, 100):
    print(f"  p{p:<5} = {np.percentile(dR, p):.3f} m   (sample spacing {ds:.2f} m)")
print(f"  columns with a >1.0 m step: {(dR>1.0).sum()}")

# silhouette continuity of the whole rim
rim = RN[-1, :]
print()
print(f"  rim radius: min={rim.min():.2f} max={rim.max():.2f} "
      f"(old min={RO[-1,:].min():.2f} max={RO[-1,:].max():.2f})")
