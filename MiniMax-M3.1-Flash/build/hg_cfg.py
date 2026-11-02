"""Hogwarts — shared world layout constants (metres, Z up, water at z=0)."""
import math

WATER_Z = 0.0
PLATEAU_Z = 60.0

# ---- the crag ----
# The top ellipse must enclose the whole castle footprint (the Great Hall's
# west wall reaches r=93); the eastern bulge is the promontory shoulder that
# carries the gate terrace out to the viaduct.
CRAG_TOP_RX = 106.0
CRAG_TOP_RY = 80.0
CRAG_EAST_BULGE = 0.42       # promontory shoulder reaching east toward the gorge
CRAG_BULGE_SIGMA = 0.85     # angular width of that shoulder (radians)
CRAG_BATTER = 14.0           # modest outward cornice below the rim

# ---- the gorge and the eastern highlands ----
GORGE_X0 = 158.0             # ravine floor starts (below the crag toe)
GORGE_X1 = 300.0             # ravine floor ends (east wall of the gorge)
GORGE_WALL_X = 324.0         # top of the sheer east wall of the gorge
GORGE_FLOOR_Z = 7.0
GORGE_Y0, GORGE_Y1 = -330.0, 285.0

# ---- great hall ----
GH_CX, GH_CY = -54.0, 0.0
GH_W, GH_L = 34.0, 112.0     # width (X), length (Y)
GH_WALL_H = 34.0
GH_RIDGE_H = 56.0

# ---- viaduct ----
VIA_Y = -46.0
VIA_X0, VIA_X1 = 150.0, 330.0
VIA_ARCHES = 11
VIA_SPAN = 11.0
VIA_PIER = 4.2
VIA_SPRING = 34.0          # impost line the arches spring from
VIA_RISE = 15.0            # height of the arch head above the impost
VIA_DECK_W = 7.4

# ---- boathouse / stair ----
BOAT_X, BOAT_Y = 72.0, -92.0

# ---- main towers ----
T_MAIN = (-2.0, 18.0)        # great spire
T_CLOCK = (28.0, -30.0)
T_EAST_A = (54.0, 24.0)
T_EAST_B = (66.0, 50.0)
T_EAST_C = (26.0, 58.0)
T_EAST_D = (4.0, 62.0)
T_GATE_A = (86.0, -58.0)
T_GATE_B = (86.0, -28.0)
T_OWLERY = (-172.0, 86.0)

# ---- paths (polylines over the landscape) ----
PATH_MAIN = [(760, 300), (560, 170), (430, 60), (372, -20), (330, -46),
             (130, -46), (92, -48), (52, -62), (30, -92)]
PATH_MOOR = [(-300, -240), (-180, -180), (-90, -130), (-40, -92)]
PATH_QUID = [(326, -46), (440, -150), (560, -250)]

# ---- greenshouse terrace ----
TERRACE_Z = 50.0
TERRACE_A0, TERRACE_A1 = 243.0, 272.0     # bearings the ledge wraps around
TERRACE_EMBED = 8.0        # how far the deck is keyed into the rock face
TERRACE_W = 14.0           # deck width out from the rock face
# (bearing_deg, length, depth) -- the glasshouses stand tangentially on the
# terrace, each one pushed clear of the rock bulge behind it.
GREENHOUSE = [(248.0, 13.5, 8.6), (258.0, 12.0, 8.2), (267.0, 10.0, 7.8)]


def cliff_r(a_deg, z):
    """Outer radius of the *displaced* cliff face at a bearing and height.

    The undisplaced profile is up to twenty metres inside the real rock, so
    anything that has to stand on the cliff has to be laid out against this.
    """
    import numpy as np
    import hg_land
    T = np.array([[np.radians(a_deg)]])
    Z = np.array([[float(z)]])
    return float(hg_land.crag_radius(T, Z)[0, 0])


def greenhouse_layout():
    """Where each glasshouse stands, given the shape of the cliff behind it.

    The rock face wanders by several metres from one bearing to the next, so
    a house laid out on a fixed circle hangs in mid-air at one end and is
    swallowed by the cliff at the other.  Each house is therefore pushed
    clear of the *largest* rock radius it covers, and turned so that its
    ridge runs along the cliff instead of cutting across it.
    """
    out = []
    for (a_deg, ln, dp) in GREENHOUSE:
        a = math.radians(a_deg)
        r0 = cliff_r(a_deg, TERRACE_Z)
        half = math.degrees((ln * 0.5 + 1.5) / max(20.0, r0))
        rmax = max(cliff_r(a_deg + s * half / 6.0, TERRACE_Z)
                   for s in (-6, -4, -2, 0, 2, 4, 6))
        r_in = rmax + 0.4
        r_c = r_in + dp * 0.5
        out.append({
            "bearing": a_deg, "angle": a, "length": ln, "depth": dp,
            "r_in": r_in, "r_c": r_c,
            "cx": math.cos(a) * r_c, "cy": math.sin(a) * r_c,
            "rot": a - math.pi * 0.5,
        })
    return out



def crag_rtop(th):
    """Top (plateau) radius of the crag at a given bearing."""
    ex = math.cos(th) / CRAG_TOP_RX
    ey = math.sin(th) / CRAG_TOP_RY
    e = 1.0 / math.sqrt(ex * ex + ey * ey)
    d = math.atan2(math.sin(th), math.cos(th))
    bulge = 1.0 + CRAG_EAST_BULGE * math.exp(-(d / CRAG_BULGE_SIGMA) ** 2)
    return e * bulge


def crag_face_r(a_deg, z):
    """Radius of the cliff face (no displacement) at a bearing and height."""
    u = max(0.0, min(1.0, (z + 26.0) / (PLATEAU_Z + 26.0)))
    rt = crag_rtop(math.radians(a_deg))
    rc = rt + CRAG_BATTER
    rbase = rc + 26.0
    if u < 0.05:
        return rbase + (rc - rbase) * (u / 0.05)
    if u < 0.955:
        return rc + 1.4 * ((u - 0.05) / 0.905)
    t = (u - 0.955) / 0.045
    s = t * t * (3.0 - 2.0 * t) if t < 1.0 else 1.0
    return rc + 1.4 - (CRAG_BATTER + 1.4) * s
