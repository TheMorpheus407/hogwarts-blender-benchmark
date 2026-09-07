"""Master layout of the castle — the single source of truth for positions (metres).

X = east, Y = north, Z = up, lake surface at Z = 0.  The plateau under the
tower cluster is at ~76 m, under the Great Hall ~70 m.
"""
import math

# --------------------------------------------------------------------------- towers
# Each tower: kind in {round, square, oct}, centre, radius / half-size, base z,
# top of masonry, roof kind, roof apex.  No two towers share the same recipe.
TOWERS = [
    # The Grand Tower — the huge conical round tower at the Great Hall's east end
    dict(name="T_Grand", kind="round", cx=-36, cy=-30, r=11.0, z0=66, z_top=122, roof="cone", z_apex=156,
         segs=64, machicolation=True, corbels=True, bands=(84, 98, 112), turrets=1, win_rows=(78, 88, 98, 108), copper=False),
    # Central spire tower — the tallest
    dict(name="T_Spire", kind="square", cx=48, cy=12, r=8.0, z0=74, z_top=130, roof="spire", z_apex=186,
         corner_turrets=True, ct_r=2.3, ct_top=138, ct_apex=152, bands=(92, 110), win_rows=(84, 96, 108, 120), copper=True),
    # Tall thin pinnacle beside the spire
    dict(name="T_Pinnacle", kind="round", cx=38, cy=26, r=3.6, z0=74, z_top=142, roof="cone", z_apex=166,
         segs=32, bands=(100, 120, 134), win_rows=(90, 104, 118, 130), copper=False),
    # Astronomy tower — round, tall, with a crown of small turrets
    dict(name="T_Astronomy", kind="round", cx=22, cy=44, r=6.8, z0=72, z_top=126, roof="cone", z_apex=150,
         segs=48, crown=True, bands=(90, 106), win_rows=(82, 94, 106, 116), copper=True),
    # Clock tower — square with a pyramid roof and lantern
    dict(name="T_Clock", kind="square", cx=84, cy=-30, r=6.8, z0=72, z_top=116, roof="pyramid", z_apex=134,
         clock=True, clock_z=104, lantern=True, bands=(86, 96), win_rows=(80, 90), copper=False),
    # North-east octagonal tower
    dict(name="T_NorthEast", kind="oct", cx=98, cy=36, r=8.2, z0=72, z_top=106, roof="cone", z_apex=122,
         bands=(84, 96), win_rows=(80, 90, 100), copper=False),
    # Gryffindor tower — big round tower on the east flank, bell roof
    dict(name="T_Gryffindor", kind="round", cx=120, cy=6, r=8.8, z0=68, z_top=108, roof="bell", z_apex=126,
         segs=56, machicolation=True, bands=(80, 92), win_rows=(78, 88, 98), copper=True),
    # Small stair turret on the long gallery
    dict(name="T_Stair", kind="round", cx=-22, cy=-40, r=2.8, z0=70, z_top=98, roof="cone", z_apex=108,
         segs=24, bands=(86,), win_rows=(80, 88), copper=False),
    # South-west bastion tower under the Great Hall terrace
    dict(name="T_Bastion", kind="round", cx=-98, cy=-58, r=5.0, z0=44, z_top=64, roof="flat", z_apex=72,
         segs=36, machicolation=True, bands=(64,), win_rows=(), copper=False),
    # West tower at the hall's west end (shorter, square, pyramid)
    dict(name="T_West", kind="round", cx=-106, cy=-36, r=5.5, z0=62, z_top=96, roof="cone", z_apex=114,
         segs=40, bands=(76, 88), win_rows=(72, 82, 90), copper=False),
    # Ravenclaw tower — slender round tower behind the spire, copper cap
    dict(name="T_Ravenclaw", kind="round", cx=74, cy=36, r=6.2, z0=74, z_top=134, roof="cone", z_apex=160,
         segs=44, machicolation=True, bands=(92, 108, 122), win_rows=(84, 98, 112, 126), copper=True),
    # Gatehouse drum towers (viaduct head) — pair, but different heights
    dict(name="T_GateN", kind="round", cx=124, cy=-30, r=4.6, z0=62, z_top=86, roof="cone", z_apex=97,
         segs=32, machicolation=True, bands=(74,), win_rows=(70, 78), copper=False),
    dict(name="T_GateS", kind="round", cx=108, cy=-52, r=4.2, z0=60, z_top=82, roof="cone", z_apex=92,
         segs=32, machicolation=True, bands=(72,), win_rows=(68, 76), copper=False),
    # Owlery-like small tower on the north-west outcrop
    dict(name="T_Chapel", kind="oct", cx=-66, cy=30, r=5.2, z0=70, z_top=96, roof="cone", z_apex=112,
         bands=(82,), win_rows=(78, 88), copper=False),
]

# --------------------------------------------------------------------------- halls / ranges
# Rectangular blocks with gable roofs: x0,x1,y0,y1, floor z, wall height, ridge above eave, roof axis
GREAT_HALL = dict(name="GreatHall", x0=-104, x1=-46, y0=-46, y1=-26, z0=70, wall_h=21, ridge_h=14, axis='x',
                  bays=8, buttress=True, turret_r=2.1, turret_h=6, turret_cone=8)

RANGES = [
    # long gallery between the Grand Tower and the cluster (south front)
    dict(name="R_LongGallery", x0=-25, x1=34, y0=-38, y1=-22, z0=70, wall_h=19, ridge_h=8, axis='x', bays=7, buttress=True),
    # kitchen annex north of the Great Hall
    dict(name="R_Kitchens", x0=-92, x1=-62, y0=-26, y1=-4, z0=70, wall_h=12, ridge_h=7, axis='y', bays=3),
    # chapel-like block with a great south window, between gallery and clock tower
    dict(name="R_Chapel", x0=34, x1=74, y0=-44, y1=-22, z0=72, wall_h=22, ridge_h=10, axis='x', bays=5, buttress=True, big_window=True, flying=True),
    # lower east range: clock tower -> gatehouse
    dict(name="R_East", x0=91, x1=128, y0=-36, y1=-12, z0=68, wall_h=15, ridge_h=7, axis='x', bays=4),
    # north range with the north gate
    dict(name="R_North", x0=-34, x1=34, y0=48, y1=62, z0=66, wall_h=16, ridge_h=7, axis='x', bays=8),
    # west cloister range closing the courtyard
    dict(name="R_WestCloister", x0=-46, x1=-36, y0=-4, y1=46, z0=70, wall_h=9, ridge_h=4, axis='y', bays=6, arcade="E"),
    # east range along the courtyard, under the spire tower
    dict(name="R_EastCloister", x0=56, x1=66, y0=22, y1=48, z0=74, wall_h=9, ridge_h=4, axis='y', bays=3, arcade="W"),
    # infirmary range NE
    dict(name="R_Infirmary", x0=70, x1=106, y0=46, y1=60, z0=70, wall_h=13, ridge_h=6, axis='x', bays=4),
    # library block west of the spire
    dict(name="R_Library", x0=-4, x1=38, y0=-18, y1=-4, z0=72, wall_h=15, ridge_h=7, axis='x', bays=5),
]

# --------------------------------------------------------------------------- curtain walls
# polyline of (x, y); wall top = local ground + h; crenellated; towers at marked vertices
CURTAIN = dict(name="Curtain", h=7.5, thick=2.2, pts=[
    (-40, -44), (-30, -54), (14, -60), (60, -62), (96, -60), (118, -50),
    (134, -30), (138, -4), (134, 26), (122, 52), (98, 68), (60, 78), (20, 82), (-20, 80),
    (-56, 72), (-86, 56), (-104, 34), (-112, 6), (-116, -22), (-110, -38)])

# terrace retaining walls (polylines, open)
TERRACE_WALLS = [
    dict(name="Wall_Bastion", h=4.0, thick=1.6, pts=[(12, -64), (30, -69), (55, -71), (80, -69), (94, -63)]),
    dict(name="Wall_HallBastion", h=3.0, thick=2.4, pts=[(-112, -44), (-100, -52), (-80, -54), (-58, -53), (-44, -50)]),
    dict(name="Wall_Greenhouse", h=3.0, thick=1.2, pts=[(96, 40), (110, 34), (132, 34), (156, 44), (162, 60)]),
]

GATEHOUSE = dict(name="Gatehouse", cx=116, cy=-41, w=13.0, d=9.0, rot_deg=-30.0, z0=62.5, wall_h=17.0)

# --------------------------------------------------------------------------- viaduct
VIADUCT = dict(name="Viaduct", p0=(118, -44), p1=(258, -128), z_deck=62.5, width=7.5, n_arches=11,
               pier_w=3.2, arch="pointed", parapet_h=1.1, lantern_every=2)

# --------------------------------------------------------------------------- boathouse + stair
BOATHOUSE = dict(name="Boathouse", cx=60, cy=-97, w=11, d=17, rot_deg=-30, z0=-0.4, wall_h=5.5, ridge_h=6.5)
BOAT_STAIR = dict(name="BoatStair", width=3.0,
                  flights=[(66, -88, 0.6), (78, -84, 8.5), (50, -80, 18.0), (74, -76, 27.5), (48, -72, 37.0), (70, -68, 46.5), (52, -63, 55.5), (50, -60, 58.0)])

# --------------------------------------------------------------------------- greenhouses
GREENHOUSES = [
    dict(name="Greenhouse_1", cx=118, cy=54, w=9, d=22, rot_deg=15, z0=57, wall_h=2.2, ridge_h=3.2),
    dict(name="Greenhouse_2", cx=134, cy=52, w=9, d=22, rot_deg=15, z0=57, wall_h=2.2, ridge_h=3.2),
    dict(name="Greenhouse_3", cx=150, cy=58, w=7, d=16, rot_deg=15, z0=57, wall_h=2.0, ridge_h=2.8),
]

# --------------------------------------------------------------------------- extras
QUIDDITCH = dict(cx=330, cy=215, rx=58, ry=32, rot_deg=22, z=40.0)
HUT = dict(cx=392, cy=118, r=4.6)
STONE_CIRCLE = dict(cx=-330, cy=250, r=9)
OWLERY = dict(cx=-96, cy=62, r=3.4)
COVERED_BRIDGE = dict(p0=(2, 84), p1=(10, 158), z0=63.0, z1=52.0, width=3.4)

# --------------------------------------------------------------------------- cameras
CAMERAS = {
    "Cam_Hero":      dict(loc=(-168, -458, 6),   target=(18, -12, 82), lens=42),
    "Cam_Aerial":    dict(loc=(700, -430, 300),  target=(30, 10, 118), lens=32),
    "Cam_Boathouse": dict(loc=(92, -142, 2.5),  target=(54, -86, 30), lens=20),
    "Cam_Viaduct":   dict(loc=(212, -100, 64.8), target=(62, 4, 96),   lens=35),
    "Cam_West":      dict(loc=(-640, -260, 14),  target=(-10, -12, 70), lens=35),
    "Cam_Top":       dict(loc=(20, 0, 900),      target=(20, 0, 0),    lens=50, ortho=1000),
}
