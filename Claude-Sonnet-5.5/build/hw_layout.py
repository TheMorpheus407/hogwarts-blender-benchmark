"""Design constants: everything that positions things in the world (metres, Z up, +X east, +Y north)."""
import numpy as np

Z0 = 54.0          # castle plateau height above the lake
WATER_Z = 0.0

# ----------------------------------------------------------------------------- lake
# (cx, cy, rx, ry)   elliptical blobs, smooth-unioned, domain-warped in the terrain module
LAKE_BLOBS = [
    (10.0, -900.0, 540.0, 830.0),     # main lake, tip at y ~ -70 in front of the crag
    (-395.0, -95.0, 215.0, 205.0),    # west bay wrapping the promontory
    (222.0, 60.0, 105.0, 300.0),      # east inlet / gorge under the viaduct
    (-40.0, -1500.0, 900.0, 500.0),   # widen the southern (camera) end
]
# small land bumps inside the lake: (cx, cy, rx, ry, height)
LAND_BUMPS = [
    (20.0, -428.0, 42.0, 26.0, 10.0),     # foreground promontory (right of hero frame) for the big pines
    (-56.0, -436.0, 20.0, 12.0, 4.5),     # small rocky islet (left foreground, inside the hero frame)
    (-262.0, -395.0, 34.0, 26.0, 7.0),    # further islet
]

# ----------------------------------------------------------------------------- platforms / crag
# polygon = top edge of the rock (plan view, CCW).  z = flat top.  W = width of the cliff+talus skirt
PLATFORMS = [
    dict(name='plateau', z=Z0, W=62.0, p=1.55, seed=61, poly=[
        (-216, 8), (-214, -22), (-200, -32), (-160, -33), (-125, -34), (-104, -38), (-92, -44), (-70, -48),
        (-46, -44), (-34, -38), (-12, -34), (14, -34), (40, -32), (66, -28), (90, -24), (108, -20), (118, -8),
        (122, 10), (120, 32), (112, 54), (92, 72), (44, 84), (-24, 88), (-96, 84), (-160, 80), (-200, 66),
        (-214, 40)]),
    dict(name='terrace_se', z=38.0, W=48.0, p=1.55, seed=62, spur=0.5, poly=[
        (2, -58), (30, -74), (66, -82), (100, -72), (114, -50), (104, -38), (62, -44), (28, -50)]),
    dict(name='outcrop_west', z=62.0, W=46.0, p=1.55, seed=63, poly=[
        (-312, 22), (-298, 0), (-276, -4), (-266, 18), (-278, 40), (-302, 44)]),
    dict(name='west_spur', z=60.0, W=40.0, p=1.55, seed=66, poly=[
        (-322, 34), (-296, 46), (-284, 100), (-300, 170), (-350, 170), (-356, 80)]),
    dict(name='boat_shelf', z=3.2, W=14.0, p=2.0, seed=64, poly=[
        (-74, -110), (-22, -112), (-18, -90), (-70, -86)]),
    dict(name='abutment_east', z=Z0, W=40.0, p=1.9, seed=65, poly=[
        (322, -26), (372, -26), (376, 26), (322, 26)]),
]

# ----------------------------------------------------------------------------- viaduct
VIADUCT = dict(x0=103.0, x1=337.0, y=0.0, deck=Z0, n=9, width=7.0)

# ----------------------------------------------------------------------------- castle massing
# All heights are ABOVE the base level of the structure (base z comes from the terrain / platform).
CASTLE = dict(
    hall=dict(cx=-160.0, cy=-8.0, L=90.0, D=26.0, eaves=25.0, pitch=54.0, base=Z0),
    grand=dict(x=-96.0, y=8.0, R=20.0, shaft=72.0, gallery=4.0, cone=56.0, fin=9.0, base=Z0),
    library=dict(cx=-56.0, cy=0.0, L=52.0, D=28.0, eaves=27.0, pitch=46.0, base=Z0),
    gallery=dict(x0=-84.0, x1=-34.0, y0=-24.0, y1=-14.0, h=15.0, base=Z0),
    clock=dict(x=-18.0, y=6.0, s=14.0, shaft=54.0, belfry=13.0, spire=30.0, fin=5.0, base=Z0),
    spire=dict(x=26.0, y=20.0, s=12.5, shaft=72.0, spire=40.0, fin=6.0, base=Z0),
    roundb=dict(x=50.0, y=-2.0, R=8.8, shaft=48.0, cone=30.0, fin=4.0, base=Z0),
    octc=dict(x=44.0, y=40.0, R=6.4, shaft=58.0, cone=26.0, fin=4.0, base=Z0),
    roundd=dict(x=4.0, y=38.0, R=7.4, shaft=42.0, cone=27.0, fin=4.0, base=Z0),
    righthall=dict(cx=28.0, cy=-8.0, L=46.0, D=22.0, eaves=27.0, pitch=50.0, base=Z0),
    gatehouse=dict(cx=94.0, cy=0.0, sx=24.0, sy=22.0, h=36.0, base=Z0),
    northrange=dict(cx=-70.0, cy=64.0, L=96.0, D=22.0, eaves=22.0, pitch=48.0, base=Z0),
)
# attendant turrets: (x, y, R, base_dz, shaft, cone, kind)  base_dz = start above plateau
TURRETS = [
    # attendants of the Grand Tower (tangent to its shaft): x, y, R, base_dz, shaft, cone, kind
    (-118.0, 10.0, 4.2, 0.0, 74.0, 26.0, 'plain'),
    (-107.0, 27.0, 3.4, 0.0, 84.0, 24.0, 'plain'),
    (-75.7, 15.1, 3.0, 44.0, 44.0, 22.0, 'bracket'),
    (-92.3, -14.2, 3.8, 0.0, 58.0, 20.0, 'plain'),
    (-79.7, 22.0, 2.3, 0.0, 92.0, 24.0, 'plain'),
    (-78.0, -7.0, 3.2, 0.0, 68.0, 22.0, 'plain'),
    (-113.6, -6.1, 3.0, 0.0, 52.0, 18.0, 'plain'),
    # Great Hall corner turrets
    (-206.0, -20.0, 2.9, 0.0, 40.0, 18.0, 'corner'),
    (-114.0, -20.0, 2.9, 0.0, 40.0, 18.0, 'corner'),
    (-206.0, 4.0, 2.9, 0.0, 40.0, 18.0, 'corner'),
    (-114.0, 4.0, 2.9, 0.0, 40.0, 18.0, 'corner'),
]
# extra towers of the right cluster: kind, x, y, R_or_s, shaft, roof, style
CLUSTER_R = [
    ('round', 14.0, -15.0, 4.8, 46.0, 26.0, 'slate'),
    ('round', -4.0, 27.0, 5.6, 62.0, 30.0, 'slate'),
    ('square', 61.0, 16.0, 9.0, 58.0, 34.0, 'slate'),
    ('round', 72.0, 26.0, 4.2, 40.0, 24.0, 'copper'),
    ('round', 18.4, 12.4, 2.3, 76.0, 28.0, 'slate'),
    ('round', 33.6, 12.4, 2.3, 84.0, 30.0, 'slate'),
    ('round', 18.4, 27.6, 2.3, 70.0, 26.0, 'copper'),
    ('round', 33.6, 27.6, 2.3, 80.0, 30.0, 'slate'),
    ('round', 40.0, 27.0, 1.8, 90.0, 26.0, 'slate'),
    ('round', 8.0, 14.0, 2.0, 60.0, 22.0, 'slate'),
]
BOATHOUSE = dict(cx=-48.0, cy=-98.0, L=26.0, D=15.0, base=3.2)

# ----------------------------------------------------------------------------- boathouse stair
# flights: (x_start, z_start, x_end, z_end); y follows the cliff contour (see hw_terrain.plan_flight)
STAIR = dict(width=3.6, flights=[(-44.0, 3.4, -92.0, 16.5), (-92.0, 16.5, -46.0, 29.5), (-46.0, 29.5, -92.0, 42.5),
                                 (-92.0, 42.5, -56.0, Z0)], y_lo=-105.0, y_hi=-20.0)

# ----------------------------------------------------------------------------- paths (plan polylines, smoothed later)
PATHS = dict(
    main=[(1500, 420), (1250, 350), (1050, 300), (900, 230), (780, 170), (690, 140), (610, 96), (540, 70), (470, 50),
          (410, 30), (372, 14), (346, 2)],
    north_gate=[(-60, 400), (-40, 300), (-10, 220), (10, 160), (40, 118), (70, 92), (96, 60), (110, 30), (116, 6)],
    shore=[(-330, -430), (-300, -360), (-270, -300), (-230, -250), (-190, -210), (-150, -170), (-110, -135), (-78, -108)],
)

# ----------------------------------------------------------------------------- props / clearings
OWLERY = dict(x=-283.0, y=14.0, R=6.4, shaft=26.0)
BRIDGE = dict(A=(-213.0, 9.0, 54.7), B=(-259.0, 12.0, 62.3))
HUT = dict(x=392.0, y=52.0, yaw=0.55)
STONES = dict(x=566.0, y=122.0)
HERO_PINES = [(12.0, -426.0, 1.00), (26.0, -420.0, 1.25), (35.0, -431.0, 0.85), (17.0, -437.0, 0.7), (-57.0, -436.0, 0.62), (-65.0, -439.0, 0.42)]
CLEARINGS = [(392.0, 52.0, 34.0), (566.0, 122.0, 36.0), (-283.0, 14.0, 26.0), (20.0, -428.0, 22.0), (-56.0, -436.0, 20.0), (-48.0, -100.0, 48.0), (60.0, -62.0, 40.0)]
