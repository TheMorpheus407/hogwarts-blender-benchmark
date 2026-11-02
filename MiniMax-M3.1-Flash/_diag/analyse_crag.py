"""Offline analysis of the crag displacement field (no Blender needed).

Stubs out bpy/bmesh/mathutils so hg_land can be imported for its pure-numpy
geometry functions, then samples the crag on its real mesh grid and measures
where the radius jumps between neighbouring vertices.
"""
import sys, types, math
import numpy as np

BUILD = "/home/morpheus/Documents/Morpheus-Produktion/Benchmarks/Blender/MiniMax-M3.1-Flash/build"
sys.path.insert(0, BUILD)

# ---- stubs -----------------------------------------------------------------
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

NTHETA, NZ = 760, 175
th = np.linspace(0.0, 2 * np.pi, NTHETA, endpoint=False)
H = np.linspace(-26.0, C.PLATEAU_Z, NZ)
T, Z = np.meshgrid(th, H, indexing="ij")
S = T * 190.0                                   # arc length at the cliff radius

R = LD.crag_radius(T, Z)

# --- radial step between neighbouring columns (same height) ----------------
dR_ds = np.abs(np.diff(R, axis=0)) / (2 * math.pi * 190.0 / NTHETA)
print("=== radial jump between adjacent mesh columns (m) ===")
for p in (50, 90, 99, 99.9, 100):
    print(f"  p{p:<5} = {np.percentile(dR_ds, p):.3f}")
print(f"  max   = {dR_ds.max():.3f}")
big = np.argwhere(dR_ds > 1.0)
print(f"  columns with a >1.0 m radial jump: {len(big)}")

# --- radial jump between neighbouring rows (same bearing) ------------------
dR_dz = np.abs(np.diff(R, axis=1)) / ((C.PLATEAU_Z + 26.0) / NZ)
print()
print("=== radial jump between adjacent mesh rows (m) ===")
for p in (50, 90, 99, 99.9, 100):
    print(f"  p{p:<5} = {np.percentile(dR_dz, p):.3f}")
print(f"  max   = {dR_dz.max():.3f}")

# --- the joint term on its own ---------------------------------------------
def joint_field(T_, Z_, with_cellr=True):
    s = T_ * 190.0
    wd1, wd2, cellr = N.worley((s + 0.85 * Z_) / 10.0, Z_ / 9.0, 1.0, seed=131,
                                jitter=0.9)
    db = np.maximum((wd2 - wd1) * 0.5, 0.0)
    if with_cellr:
        return -2.3 * (0.45 + 0.90 * cellr) * np.exp(-(db / 0.34) ** 2)
    return -2.3 * np.exp(-(db / 0.34) ** 2)


J = joint_field(T, Z)
Jflat = joint_field(T, Z, with_cellr=False)
print()
print("=== joint term ===")
print(f"  with cellr : min={J.min():.3f} max={J.max():.3f}")
print(f"  without    : min={Jflat.min():.3f} max={Jflat.max():.3f}")
step = np.abs(np.diff(J, axis=0))
print(f"  max |dJ| between adjacent columns  (with cellr) = {step.max():.3f}")
stepf = np.abs(np.diff(Jflat, axis=0))
print(f"  max |dJ| between adjacent columns  (no cellr)   = {stepf.max():.3f}")

# --- worst offenders: where are they? --------------------------------------
n_big = (np.abs(np.diff(J, axis=0)) > 0.8).sum()
print(f"  column pairs with a >0.8 m joint jump: {n_big}")

# --- candidate fix: smooth modulation of the groove depth -------------------
def joint_fixed(T_, Z_):
    s = T_ * 190.0
    wd1, wd2, cellr = N.worley((s + 0.85 * Z_) / 10.0, Z_ / 9.0, 1.0, seed=131,
                                jitter=0.9)
    db = np.maximum((wd2 - wd1) * 0.5, 0.0)
    # depth modulated by a SMOOTH field of the same coordinates, not by the
    # per-cell constant -> the groove is continuous across every boundary
    depth = 1.5 + 1.1 * N.fbm(s / 26.0, Z_ / 24.0, 3, seed=131 + 7)
    return -depth * np.exp(-(db / 0.34) ** 2)


JF = joint_fixed(T, Z)
sf = np.abs(np.diff(JF, axis=0))
print()
print("=== candidate fix (smooth depth modulation) ===")
print(f"  min={JF.min():.3f} max={JF.max():.3f}")
print(f"  max |dJ| between adjacent columns = {sf.max():.3f}")
print(f"  column pairs with a >0.8 m jump  = {(sf > 0.8).sum()}")
