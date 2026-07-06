"""The grand viaduct: pointed-arch bays on tall piers, parapet, lanterns."""
import bpy
import math
import hog
import hogkit as hk

hog.clear_coll('Viaduct')
hk.init()
M = hk.M

X0, X1 = 100.0, 170.0     # span
YC = -6.0                 # centerline
W = 7.5                   # width
BED = -8.0                # pier footing
SPRING = 26.0             # arch springing
RISE = 13.0               # arch rise above springing
SPAN_TOP = 52.0           # spandrel top
DECK = 55.5               # deck walking level

nbays = 5
bw = (X1 - X0) / nbays    # 14.0
aw = bw * 0.60            # arch opening 8.4

# ------------------------------------------------------------- arcade wall
arch = hk.arch_outline(aw, RISE, seg=10)
for b in range(nbays):
    bx = X0 + b * bw
    x_l = bx + (bw - aw) / 2
    x_r = bx + bw - (bw - aw) / 2
    cx = bx + bw / 2
    pts = [(bx, BED), (bx, SPAN_TOP), (bx + bw, SPAN_TOP), (bx + bw, BED),
           (x_r, BED), (x_r, SPRING)]
    pts += [(cx + px, SPRING + pz) for (px, pz) in arch[1:-1]]
    pts += [(x_l, SPRING), (x_l, BED)]
    hk.prism_xz(f'Via_Bay_{b}', 'Viaduct', pts, W, loc=(0, YC, 0),
                mat=M['wall'])
    # pier pilasters on both outer faces
    for sy in (-1, 1):
        hog.box(f'Via_Pil_{b}_{sy}', 'Viaduct', size=(2.6, 1.0, SPRING - BED),
                loc=(bx, YC + sy * (W / 2 + 0.4), BED), mat=M['wall'])
# final pier at east end
hog.box('Via_Pier_End', 'Viaduct', size=(3.5, W, SPAN_TOP - BED),
        loc=(X1, YC, BED), mat=M['wall'])
for sy in (-1, 1):
    hog.box(f'Via_Pil_end_{sy}', 'Viaduct', size=(2.6, 1.0, SPRING - BED),
            loc=(X1, YC + sy * (W / 2 + 0.4), BED), mat=M['wall'])

# corbel table under deck edge
for sy in (-1, 1):
    n = int((X1 - X0) / 1.6)
    for i in range(n):
        hog.box(f'Via_Corb_{sy}_{i}', 'Viaduct', size=(0.5, 0.5, 0.7),
                loc=(X0 + 0.8 + i * 1.6, YC + sy * (W / 2 + 0.15),
                     SPAN_TOP - 0.7), mat=M['trim'])

# ------------------------------------------------------------------- deck
hog.box('Via_Deck', 'Viaduct', size=(X1 - X0 + 6, W + 1.6, DECK - SPAN_TOP),
        loc=((X0 + X1) / 2, YC, SPAN_TOP), mat=M['trim'])
for sy in (-1, 1):
    hk.crenel_strip(f'Via_Parapet_{sy}', 'Viaduct', X1 - X0 + 6,
                    base_h=1.3, merlon_h=0.6, t=0.4,
                    loc=((X0 + X1) / 2, YC + sy * (W / 2 + 0.5), DECK))
# lanterns along both parapets at pier positions
for b in range(nbays + 1):
    bx = X0 + b * bw
    for sy in (-1, 1):
        hk.place_lantern('Viaduct', (bx, YC + sy * (W / 2 + 0.45), DECK + 1.3))
