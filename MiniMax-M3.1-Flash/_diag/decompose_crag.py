"""Decompose the crag surface: which term makes the visible horizontal 'loaves'?"""
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

# a fixed height, and the bearing range the hero camera sees on the crag
Z0 = 20.0
th = np.linspace(np.pi * 0.55, np.pi * 1.35, 960)
s = th * 120.0

TERMS = {}


def add(k, v):
    TERMS[k] = v


mega = 19.0 * N.vnoise(s / 52.0, 3.0, 3)
lobes = 8.0 * N.vnoise(s / 18.5 + 11.0, 7.0, 3)
cv = N.fbm(s / 34.0, Z0 / 30.0, 3, seed=53)
cleft = -11.0 * np.clip(1.0 - np.abs(cv) * 2.6, 0.0, 1.0) ** 1.2
cv2 = N.fbm(s / 16.0, Z0 / 15.0, 2, seed=71)
cleft2 = -5.0 * np.clip(1.0 - np.abs(cv2) * 3.0, 0.0, 1.0) ** 1.4
warp = 11.0 * N.vnoise(s / 30.0, 5.0, 21) + 5.0 * N.vnoise(s / 11.0, 9.0, 23)
bed = 2.6 * N.fbm(s / 45.0, (Z0 + warp) / 9.0, 2, seed=31)
lump = 3.0 * N.fbm(s / 12.0, Z0 / 9.0, 2, seed=17)
frac = 2.2 * N.fbm(s / 13.0, Z0 / 11.0, 2, seed=91)
fine = 0.35 * N.fbm(s / 10.0, Z0 / 8.0, 2, seed=31)
arete = 1.0 * (N.ridged(s / 19.0, Z0 / 17.0, 2, seed=43) - 0.5)
wd1, wd2, cellr = N.worley((s + 0.85 * Z0) / 10.0, Z0 / 9.0, 1.0, seed=131,
                            jitter=0.9)
db = np.maximum((wd2 - wd1) * 0.5, 0.0)
joint = -2.3 * (0.45 + 0.90 * cellr) * np.exp(-(db / 0.34) ** 2)

for k, v in (("mega", mega), ("lobes", lobes), ("cleft", cleft),
             ("cleft2", cleft2), ("bed", bed), ("lump", lump),
             ("frac", frac), ("fine", fine), ("arete", arete),
             ("joint", joint)):
    add(k, v)

ds = 2 * math.pi * 190.0 / 960
print(f"=== amplitude of each term along one height line (Z={Z0}) ===")
print(f"{'term':8s} {'std':>7s} {'max-min':>9s} {'mean wavelength (m)':>21s}")
for k, v in TERMS.items():
    sd = v.std()
    # dominant wavelength from the FFT of the profile
    x = v - v.mean()
    f = np.abs(np.fft.rfft(x))
    if f[1:].sum() > 0:
        kk = np.argmax(f[1:]) + 1
        lam = (len(x) * ds) / kk
    else:
        lam = float('nan')
    print(f"{k:8s} {sd:7.3f} {v.max()-v.min():9.3f} {lam:21.1f}")

tot = sum(TERMS.values())
print()
print(f"total   {tot.std():7.3f} {tot.max()-tot.min():9.3f}")

# what does the profile look like?  print a coarse ascii of the total
print()
print("=== total profile (each char = one 10 m segment) ===")
n = len(tot)
seg = n // 90
prof = tot[:seg * 90].reshape(90, seg).mean(axis=1)
lo, hi = prof.min(), prof.max()
for row in range(22):
    line = ""
    for v in prof:
        t = (v - lo) / max(hi - lo, 1e-6)
        line += " .:-=+*#%@"[min(int(t * 10), 9)]
    print(f"  {hi - (hi-lo)*row/22:7.1f} |{line}|")
