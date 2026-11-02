"""Verify the seven delivered 4K frames."""
import os
import numpy as np
from PIL import Image

ROOT = "/home/morpheus/Documents/Morpheus-Produktion/Benchmarks/Blender/MiniMax-M3.1-Flash"
SHOTS = ["hero.png", "angle_aerial.png", "angle_boathouse.png",
         "angle_viaduct.png", "detail_01.png", "detail_02.png", "detail_03.png"]

ok = True
print(f"{'file':22s} {'size':>12s} {'mode':>12s} {'max':>6s} {'p50':>6s} "
      f"{'p99':>6s} {'clip%':>7s} {'warm px':>9s}")
for name in SHOTS:
    p = os.path.join(ROOT, name)
    if not os.path.exists(p):
        print(f"{name:22s}  MISSING")
        ok = False
        continue
    im = Image.open(p)
    w, h = im.size
    a = np.asarray(im.convert("RGB")).astype(np.float32) / 255.0
    lum = a.mean(axis=2)
    clip = np.mean((a >= 1.0) | (a <= 0.0)) * 100
    warm = int(((a[:, :, 0] > 0.35) & (a[:, :, 0] > a[:, :, 1] * 1.30)).sum())
    bad = (w, h) != (3840, 2160)
    if bad:
        ok = False
    print(f"{name:22s} {str((w,h)):>12s} {im.mode:>12s} {lum.max():6.3f} "
          f"{np.percentile(lum,50):6.3f} {np.percentile(lum,99):6.3f} "
          f"{clip:7.3f} {warm:9d}" + ("   <-- WRONG SIZE" if bad else ""))

blend = os.path.join(ROOT, "hogwarts.blend")
print()
print(f"hogwarts.blend  {os.path.getsize(blend)/1e6:.1f} MB  "
      f"mtime {os.path.getmtime(blend):.0f}")
print("ALL FRAMES OK" if ok else "PROBLEMS FOUND")
