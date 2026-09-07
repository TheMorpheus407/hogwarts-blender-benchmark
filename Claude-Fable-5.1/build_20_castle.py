"""Pass 2 — castle: towers, halls, ranges, walls, viaduct, boathouse, greenhouses.

Reads hog_layout.LAYOUT; detail level from hog_kit.DETAIL.
"""
import bpy, os, sys, importlib, time
FOLDER = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else bpy.path.abspath("//")
if FOLDER not in sys.path:
    sys.path.insert(0, FOLDER)
import hog_lib as H; importlib.reload(H)
import hog_layout as L; importlib.reload(L)
import hog_kit as K; importlib.reload(K)

t0 = time.time()
K.DETAIL = globals().get("DETAIL", 0)
K.reset_ground_cache()

for c in ("GreatHall", "TowerCluster", "Towers", "Walls", "Viaduct", "Boathouse", "Greenhouses", "Windows", "Details"):
    H.clear_collection(c)
    H.coll(c, "Castle")

count = 0
for t in L.TOWERS:
    count += len(K.build_tower(t, coll="Towers"))
count += len(K.build_great_hall(L.GREAT_HALL, coll="GreatHall"))
for rg in L.RANGES:
    count += len(K.build_range(rg, coll="Walls"))
count += len(K.build_wall_polyline(L.CURTAIN, coll="Walls", closed=True))
for w in L.TERRACE_WALLS:
    count += len(K.build_wall_polyline(w, coll="Walls", towers=False))
count += len(K.build_viaduct(L.VIADUCT, coll="Viaduct"))
count += len(K.build_gatehouse(L.GATEHOUSE, coll="Walls"))
count += len(K.build_boathouse(L.BOATHOUSE, coll="Boathouse"))
count += len(K.build_stair(L.BOAT_STAIR, coll="Boathouse"))
for g in L.GREENHOUSES:
    count += len(K.build_greenhouse(g, coll="Greenhouses"))

# lantern anchor points for the light pass
lan = []
for src in (L.VIADUCT.get("_lanterns", []), L.BOAT_STAIR.get("_lanterns", []), L.BOATHOUSE.get("_lanterns", []), L.GATEHOUSE.get("_lanterns", [])):
    lan.extend([list(p) for p in src])
bpy.context.scene["hog_lanterns"] = [c for p in lan for c in p]

H.purge_orphans()
result = {"objects": count, "lanterns": len(lan), "secs": round(time.time() - t0, 1)}
