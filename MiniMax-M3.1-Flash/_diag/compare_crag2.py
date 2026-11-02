"""Exact old-vs-new crag radius comparison (fade applied), for the bias fix."""
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
th = np.linspace(0.0, 2 * np.pi, NTHETA, endpoint=False)
H = np.linspace(-26.0, C.PLATEAU_Z, NZ)
T, Z = np.meshgrid(th, H, indexing="ij")


def base_radius(T_, Z_):
    u = np.clip((Z_ + 26.0) / (C.PLATEAU_Z + 26.0), 0.0, 1.0)
    ex = np.cos(T_) / C.CRAG_TOP_RX
    ey = np.sin(T_) / C.CRAG_TOP_RY
    rt = 1.0 / np.sqrt(ex * ex + ey * ey)
    d_ang = np.arctan2(np.sin(T_), np.cos(T_))
    rt = rt * (1.0 + C.CRAG_EAST_BULGE * np.exp(-(d_ang / C.CRAG_BULGE_SIGMA) ** 2))
    rc = rt + C.CRAG_BATTER
    rbase = rc + 26.0
    R = np.where(u < 0.05, rbase + (rc - rbase) * (u / 0.05),
                 np.where(u < 0.955, rc + 1.4 * ((u - 0.05) / 0.905),
                          rc + 1.4 - (C.CRAG_BATTER + 1.4) *
                          N.smoothstep(0.0, 1.0, (u - 0.955) / 0.045)))
    return R


def fade_of(Z_):
    u = np.clip((Z_ + 26.0) / (C.PLATEAU_Z + 26.0), 0.0, 1.0)
    return 1.0 - 0.96 * N.smoothstep(0.93, 1.0, u)


# ---- reconstruct the OLD crag_disp exactly --------------------------------
def old_disp(T_, Z_):
    u = np.clip((Z_ + 26.0) / (C.PLATEAU_Z + 26.0), 0.0, 1.0)
    fade = 1.0 - 0.96 * N.smoothstep(0.93, 1.0, u)
    s = T_ * 120.0
    mega = 19.0 * N.vnoise(s / 52.0, 3.0, 3)
    lobes = 8.0 * N.vnoise(s / 18.5 + 11.0, 7.0, 3)
    cv = N.fbm(s / 34.0, Z_ / 30.0, 3, seed=53)
    cleft = -11.0 * np.clip(1.0 - np.abs(cv) * 2.6, 0.0, 1.0) ** 1.2
    cv2 = N.fbm(s / 16.0, Z_ / 15.0, 2, seed=71)
    cleft2 = -5.0 * np.clip(1.0 - np.abs(cv2) * 3.0, 0.0, 1.0) ** 1.4
    warp = 11.0 * N.vnoise(s / 30.0, 5.0, 21) + 5.0 * N.vnoise(s / 11.0, 9.0, 23)
    bed = 2.6 * N.fbm(s / 45.0, (Z_ + warp) / 9.0, 2, seed=31)
    lump = 3.0 * N.fbm(s / 12.0, Z_ / 9.0, 2, seed=17)
    frac = 2.2 * N.fbm(s / 13.0, Z_ / 11.0, 2, seed=91)
    fine = 0.35 * N.fbm(s / 10.0, Z_ / 8.0, 2, seed=31)
    arete = 1.0 * (N.ridged(s / 19.0, Z_ / 17.0, 2, seed=43) - 0.5)
    wd1, wd2, cellr = N.worley((s + 0.85 * Z_) / 10.0, Z_ / 9.0, 1.0, seed=131,
                                jitter=0.9)
    db = np.maximum((wd2 - wd1) * 0.5, 0.0)
    joint = -2.3 * (0.45 + 0.90 * cellr) * np.exp(-(db / 0.34) ** 2)
    d = mega + lobes + cleft + cleft2 + bed + lump + frac + fine + arete + joint + 8.0
    d = d * fade
    d = d + 3.6 * N.fbm(s / 12.0, Z_ / 8.0, 2, seed=63) * \
        N.smoothstep(0.900, 0.962, u) * (1.0 - 0.45 * N.smoothstep(0.988, 1.0, u))
    return d


RO = base_radius(T, Z) + old_disp(T, Z)
RN = LD.crag_radius(T, Z)
ds = 2 * math.pi * 190.0 / NTHETA
print("=== crag radius ===")
print(f"  OLD mean={RO.mean():.3f}  NEW mean={RN.mean():.3f}  "
      f"drift={RN.mean()-RO.mean():+.3f} m")
print(f"  OLD max={RO.max():.3f}  NEW max={RN.max():.3f}")
print(f"  rim OLD [{RO[-1,:].min():.2f} .. {RO[-1,:].max():.2f}]  "
      f"NEW [{RN[-1,:].min():.2f} .. {RN[-1,:].max():.2f}]")
print()
print(f"=== step between adjacent mesh columns (spacing {ds:.2f} m) ===")
for lbl, R in (("OLD", RO), ("NEW", RN)):
    d = np.abs(np.diff(R, axis=0))
    print(f"  {lbl}  p50={np.percentile(d,50):.3f} p90={np.percentile(d,90):.3f} "
          f"p99={np.percentile(d,99):.3f} max={d.max():.3f} "
          f">1.0m: {(d>1.0).sum()}")
print()
print("=== step between adjacent mesh rows ===")
for lbl, R in (("OLD", RO), ("NEW", RN)):
    d = np.abs(np.diff(R, axis=1))
    print(f"  {lbl}  p50={np.percentile(d,50):.3f} p90={np.percentile(d,90):.3f} "
          f"p99={np.percentile(d,99):.3f} max={d.max():.3f}")
print()
print(f"  bias correction to keep the mean radius: "
      f"{RO.mean()-RN.mean():+.3f} m  -> bias 8.0 -> {8.0 + RO.mean()-RN.mean():.2f}")
