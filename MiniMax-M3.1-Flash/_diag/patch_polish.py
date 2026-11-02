"""Final polish patch: readable masonry joints + a wider crag joint network.

1. MASONRY.  The course joints were 2.7 cm wide with 1.6 cm of bump relief.
   At the distance the viaduct camera sees (60-100 m) that is a four-pixel
   hairline of painted colour, so the biggest stone surface in the whole set
   read as a sheet of card.  Wider, crisper joints with real relief make
   the courses read at the same time as the close-up wall still looks like
   ashlar rather than rubber.

2. CRAG.  The painted joint network on the rock was 0.63 m wide -- about
   two pixels at the hero distance -- so the cliff's dominant feature was a
   thin drawn line.  Widening it turns those lines into dark slots between
   blocks, which is what makes a jointed crag read as jointed.
"""
import re

BUILD = "/home/morpheus/Documents/Morpheus-Produktion/Benchmarks/Blender/MiniMax-M3.1-Flash/build"

# ---------------------------------------------------------------- hg_mat.py
P = BUILD + "/hg_mat.py"
s = open(P).read()

subs = [
 # --- masonry: the cylindrical (tower) variant -------------------------
 ("        mj = masonry_mask(nt, mu, courses[0], courses[1], None, msize=0.016,\n                          msoft=0.055, loc=(-650, -300))",
  "        mj = masonry_mask(nt, mu, courses[0], courses[1], None, msize=0.024,\n                          msoft=0.038, loc=(-650, -300))"),
 # --- masonry: the triplanar variant ----------------------------------
 ("        mj = triplanar_masonry(nt, wobj, vtr.outputs['Vector'],\n                               courses[0], courses[1], msize=0.016,\n                               msoft=0.055, loc=(-650, -300))",
  "        mj = triplanar_masonry(nt, wobj, vtr.outputs['Vector'],\n                               courses[0], courses[1], msize=0.024,\n                               msoft=0.038, loc=(-650, -300))"),
 # --- per-block colour: the mortar band has to match the mask --------
 ("                                    msize=0.013, msoft=0.050, bias=0.06,\n                                    loc=(-650, 900))",
  "                                    msize=0.020, msoft=0.036, bias=0.06,\n                                    loc=(-650, 900))"),
 # --- bump: real relief in the joints --------------------------------
 ("    jointneg = mathn(nt, (180, -1100), 'MULTIPLY', mj, -0.85)",
  "    jointneg = mathn(nt, (180, -1100), 'MULTIPLY', mj, -1.15)"),
 ("    bump1.inputs['Strength'].default_value = 0.55\n    bump1.inputs['Distance'].default_value = 0.035",
  "    bump1.inputs['Strength'].default_value = 0.62\n    bump1.inputs['Distance'].default_value = 0.060"),
 # --- the crag's painted joint network -------------------------------
 ("    vr = ramp(nt, (-1080, 600), [(0.0, (0, 0, 0, 1)), (0.030, (1, 1, 1, 1))])",
  "    vr = ramp(nt, (-1080, 600), [(0.0, (0, 0, 0, 1)), (0.105, (1, 1, 1, 1))])"),
 ("    vr2 = ramp(nt, (-1080, 1260), [(0.0, (0, 0, 0, 1)), (0.022, (1, 1, 1, 1))])",
  "    vr2 = ramp(nt, (-1080, 1260), [(0.0, (0, 0, 0, 1)), (0.072, (1, 1, 1, 1))])"),
 ("    frac = mixrgb(nt, (-820, 500), 1.0, (0.082, 0.076, 0.068, 1), (0, 0, 0, 1))",
  "    frac = mixrgb(nt, (-820, 500), 1.0, (0.048, 0.044, 0.039, 1), (0, 0, 0, 1))"),
 ("    cblk = maprange(nt, (-900, 1560), csep.outputs['X'], 0.10, 0.90, 0.78, 1.24)",
  "    cblk = maprange(nt, (-900, 1560), csep.outputs['X'], 0.10, 0.90, 0.70, 1.32)"),
]
for a, b in subs:
    assert s.count(a) == 1, ("MISS", a[:70], s.count(a))
    s = s.replace(a, b)
open(P, "w").write(s)
print("hg_mat.py patched")

# --- rose window: a deeper, less primary medieval palette ---------------
s = open(P).read()
old = """    glass = ramp(nt, (1400, -320),
                 [(0.00, (0.0180, 0.0330, 0.2000, 1)),
                  (0.14, (0.0260, 0.0520, 0.2900, 1)),
                  (0.30, (0.0420, 0.0760, 0.2600, 1)),
                  (0.41, (0.2600, 0.0240, 0.0300, 1)),
                  (0.53, (0.3300, 0.0700, 0.0350, 1)),
                  (0.67, (0.3000, 0.2700, 0.2000, 1)),
                  (0.81, (0.3200, 0.2100, 0.0500, 1)),
                  (0.91, (0.0300, 0.1100, 0.0550, 1)),
                  (1.00, (0.0250, 0.0900, 0.1150, 1))], interp='CONSTANT')"""
new = """    glass = ramp(nt, (1400, -320),
                 [(0.00, (0.0140, 0.0260, 0.1700, 1)),
                  (0.18, (0.0200, 0.0420, 0.2450, 1)),
                  (0.36, (0.0320, 0.0600, 0.2150, 1)),
                  (0.46, (0.2300, 0.0220, 0.0280, 1)),
                  (0.60, (0.2700, 0.0580, 0.0300, 1)),
                  (0.68, (0.2000, 0.1780, 0.1320, 1)),
                  (0.80, (0.2450, 0.1620, 0.0420, 1)),
                  (0.89, (0.0260, 0.0880, 0.0440, 1)),
                  (0.95, (0.0220, 0.0720, 0.0940, 1)),
                  (1.00, (0.0220, 0.0720, 0.0940, 1))], interp='CONSTANT')"""
assert s.count(old) == 1
s = s.replace(old, new)
open(P, "w").write(s)
print("rose palette deepened")
