"""Offline comparison of crag surface 'form' candidates.

The cliff still reads as rounded pillows.  The dominant shapes are
`mega` and `lobes`, which are ANGULAR-ONLY (their noise has a constant
second argument), so they carve vertical ribs.  Smooth noise makes those
ribs round; ridged noise folds them, which gives flat faces meeting at a
sharp arris.

Metrics on the real mesh grid:
  * flat%   -- fraction of the surface whose normal barely changes between
                neighbouring quads (a flat panel)
  * hard%   -- fraction whose normal changes by more than the 52 deg
                auto-smooth angle (a hard arris)
  * round%  -- fraction in between (a rounded form)
  * bias    -- the constant needed to keep the mean radius unchanged
"""
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

NTHETA, NZ = 960, 210
th = np.linspace(0.0, 2 * np.pi, NTHETA, endpoint=False)
H = np.linspace(-26.0, C.PLATEAU_Z, NZ)
T, Z = np.meshgrid(th, H, indexing="ij")
S = T * 120.0

u = np.clip((Z + 26.0) / (C.PLATEAU_Z + 26.0), 0.0, 1.0)
fade = 1.0 - 0.96 * N.smoothstep(0.93, 1.0, u)


def base_radius(T_, Z_):
    uu = np.clip((Z_ + 26.0) / (C.PLATEAU_Z + 26.0), 0.0, 1.0)
    ex = np.cos(T_) / C.CRAG_TOP_RX
    ey = np.sin(T_) / C.CRAG_TOP_RY
    rt = 1.0 / np.sqrt(ex * ex + ey * ey)
    d_ang = np.arctan2(np.sin(T_), np.cos(T_))
    rt = rt * (1.0 + C.CRAG_EAST_BULGE * np.exp(-(d_ang / C.CRAG_BULGE_SIGMA) ** 2))
    rc = rt + C.CRAG_BATTER
    rbase = rc + 26.0
    return np.where(uu < 0.05, rbase + (rc - rbase) * (uu / 0.05),
                    np.where(uu < 0.955, rc + 1.4 * ((uu - 0.05) / 0.905),
                             rc + 1.4 - (C.CRAG_BATTER + 1.4) *
                             N.smoothstep(0.0, 1.0, (uu - 0.955) / 0.045)))


def other_terms():
    mega_s = 19.0 * N.vnoise(S / 52.0, 3.0, 3)
    lobes_s = 8.0 * N.vnoise(S / 18.5 + 11.0, 7.0, 3)
    cv = N.fbm(S / 34.0, Z / 30.0, 3, seed=53)
    cleft = -9.0 * np.clip(1.0 - np.abs(cv) * 2.6, 0.0, 1.0) ** 1.2
    cv2 = N.fbm(S / 16.0, Z / 15.0, 2, seed=71)
    cleft2 = -4.0 * np.clip(1.0 - np.abs(cv2) * 3.0, 0.0, 1.0) ** 1.4
    warp = 11.0 * N.vnoise(S / 30.0, 5.0, 21) + 5.0 * N.vnoise(S / 11.0, 9.0, 23)
    bed = 1.6 * N.fbm(S / 45.0, (Z + warp) / 9.0, 2, seed=31)
    lump = 2.4 * N.fbm(S / 13.0, Z / 10.0, 2, seed=17)
    frac = 1.8 * N.fbm(S / 17.0, Z / 13.0, 2, seed=91)
    fine = 0.20 * N.fbm(S / 10.0, Z / 8.0, 2, seed=31)
    arete = 4.2 * (N.ridged(S / 22.0, Z / 19.0, 2, seed=43) - 0.5)
    arete2 = 1.7 * (N.ridged(S / 11.0, Z / 9.5, 2, seed=59) - 0.5)
    arete3 = 0.85 * (N.ridged(S / 6.0, Z / 5.5, 2, seed=67) - 0.5)
    wd1, wd2, _ = N.worley((S + 0.85 * Z) / 10.0, Z / 9.0, 1.0, seed=131,
                           jitter=0.9)
    db = np.maximum((wd2 - wd1) * 0.5, 0.0)
    jd = 3.60 + 2.60 * N.fbm(S / 26.0, Z / 24.0, 3, seed=137)
    joint = -jd * np.exp(-(db / 0.40) ** 2)
    wd3, wd4, _ = N.worley((S - 1.05 * Z) / 8.0, Z / 9.0, 1.0, seed=211,
                           jitter=0.95)
    db2 = np.maximum((wd4 - wd3) * 0.5, 0.0)
    jd2 = 1.40 + 1.00 * N.fbm(S / 15.0, Z / 17.0, 3, seed=217)
    joint2 = -jd2 * np.exp(-(db2 / 0.42) ** 2)
    return dict(cleft=cleft, cleft2=cleft2, bed=bed, lump=lump, frac=frac,
                fine=fine, arete=arete, arete2=arete2, arete3=arete3,
                joint=joint, joint2=joint2)


OTH = other_terms()


def evaluate(name, mega, lobes):
    d = (mega + lobes + sum(OTH.values())) * fade
    d = d + 3.6 * N.fbm(S / 12.0, Z / 8.0, 2, seed=63) * \
        N.smoothstep(0.900, 0.962, u) * (1.0 - 0.45 * N.smoothstep(0.988, 1.0, u))
    R = base_radius(T, Z) + d
    # quads -> normals
    P = np.stack([R * np.cos(T), R * np.sin(T), Z], axis=-1)
    a = P[1:, :-1, :] - P[:-1, :-1, :]
    b = P[:-1, 1:, :] - P[:-1, :-1, :]
    n = np.cross(a, b)
    ln = np.linalg.norm(n, axis=-1, keepdims=True)
    n = n / np.maximum(ln, 1e-12)
    # angle between neighbouring quads (along the height direction)
    dot = np.clip((n[:-1, :-1, :] * n[1:, :-1, :]).sum(axis=-1), -1, 1)
    ang = np.degrees(np.arccos(dot))
    # angle between neighbouring quads (along the bearing direction)
    dot2 = np.clip((n[:-1, :-1, :] * n[:-1, 1:, :]).sum(axis=-1), -1, 1)
    ang2 = np.degrees(np.arccos(dot2))
    allang = np.concatenate([ang.ravel(), ang2.ravel()])
    flat = np.mean(allang < 4.0) * 100
    hard = np.mean(allang > 52.0) * 100
    rnd = 100 - flat - hard
    print(f"{name:26s} flat={flat:5.1f}%  round={rnd:5.1f}%  hard={hard:5.1f}%  "
          f"meanR={R.mean():8.3f}  p99ang={np.percentile(allang,99):6.1f}  "
          f"maxang={allang.max():6.1f}")
    return R.mean()


print("=== crag surface form candidates ===")
print("(flat = planar panels, round = pillows, hard = sharp arrises)")

m0 = 19.0 * N.vnoise(S / 52.0, 3.0, 3)
l0 = 8.0 * N.vnoise(S / 18.5 + 11.0, 7.0, 3)
evaluate("CURRENT (smooth ribs)", m0, l0)

for am, al, tag in ((15.0, 7.0, "ridged 15/7"), (19.0, 9.0, "ridged 19/9"),
                    (24.0, 11.0, "ridged 24/11")):
    m = am * (N.ridged(S / 52.0, 3.0, 3) * 2.0 - 1.0)
    l = al * (N.ridged(S / 18.5 + 11.0, 7.0, 3) * 2.0 - 1.0)
    evaluate(tag, m, l)

# ridged ribs + narrower, sharper clefts
m = 19.0 * (N.ridged(S / 52.0, 3.0, 3) * 2.0 - 1.0)
l = 9.0 * (N.ridged(S / 18.5 + 11.0, 7.0, 3) * 2.0 - 1.0)
cv = N.fbm(S / 34.0, Z / 30.0, 3, seed=53)
c_sharp = -9.0 * np.clip(1.0 - np.abs(cv) * 4.2, 0.0, 1.0) ** 0.85
saved = OTH["cleft"]
OTH["cleft"] = c_sharp
evaluate("ridged + sharp clefts", m, l)
OTH["cleft"] = saved

# --- how much crease amplitude does it take to read as faceted rock? ------
print()
print("=== crease (arete) amplitude sweep ===")
for amp, amp2, amp3 in ((4.2, 1.7, 0.85), (6.5, 2.6, 1.2), (8.5, 3.4, 1.5),
                         (10.5, 4.2, 1.8)):
    OTH["arete"] = amp * (N.ridged(S / 22.0, Z / 19.0, 2, seed=43) - 0.5)
    OTH["arete2"] = amp2 * (N.ridged(S / 11.0, Z / 9.5, 2, seed=59) - 0.5)
    OTH["arete3"] = amp3 * (N.ridged(S / 6.0, Z / 5.5, 2, seed=67) - 0.5)
    m = 19.0 * (N.ridged(S / 52.0, 3.0, 3) * 2.0 - 1.0)
    l = 9.0 * (N.ridged(S / 18.5 + 11.0, 7.0, 3) * 2.0 - 1.0)
    evaluate(f"crease {amp}/{amp2}/{amp3}", m, l)
