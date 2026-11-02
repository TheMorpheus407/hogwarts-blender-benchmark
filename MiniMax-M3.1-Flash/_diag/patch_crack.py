"""Widen the painted joint network on the crag rock.

The geometry carries metre-scale fissures, but at the distances the cameras
see them they are a couple of pixels wide, and the dominant visual feature
of the cliff is the shader's own crack network -- which was only 0.63 m
wide and read as a thin drawn line rather than a fissure.  Widening the
crack ramps turns those lines into dark slots between blocks, which is
what makes a jointed crag read as jointed.
"""
import re

P = "/home/morpheus/Documents/Morpheus-Produktion/Benchmarks/Blender/MiniMax-M3.1-Flash/build/hg_mat.py"
s = open(P).read()

subs = [
 # primary joint network: 0.030 -> 0.11 (about 2.3 m of dark fissure)
 ("    vr = ramp(nt, (-1080, 600), [(0.0, (0, 0, 0, 1)), (0.030, (1, 1, 1, 1))])",
  "    vr = ramp(nt, (-1080, 600), [(0.0, (0, 0, 0, 1)), (0.105, (1, 1, 1, 1))])"),
 # secondary network: 0.022 -> 0.075
 ("    vr2 = ramp(nt, (-1080, 1260), [(0.0, (0, 0, 0, 1)), (0.022, (1, 1, 1, 1))])",
  "    vr2 = ramp(nt, (-1080, 1260), [(0.0, (0, 0, 0, 1)), (0.072, (1, 1, 1, 1))])"),
 # per-block tone: more separation between the blocks
 ("    cblk = maprange(nt, (-900, 1560), csep.outputs['X'], 0.10, 0.90, 0.78, 1.24)",
  "    cblk = maprange(nt, (-900, 1560), csep.outputs['X'], 0.10, 0.90, 0.70, 1.32)"),
 # the fissure itself is darker, so the crack reads as a slot
 ("    frac = mixrgb(nt, (-820, 500), 1.0, (0.082, 0.076, 0.068, 1), (0, 0, 0, 1))",
  "    frac = mixrgb(nt, (-820, 500), 1.0, (0.040, 0.037, 0.033, 1), (0, 0, 0, 1))"),
]
for a, b in subs:
    assert s.count(a) == 1, (a[:60], s.count(a))
    s = s.replace(a, b)
open(P, "w").write(s)
print("rock crack network widened")
