"""Castle rebuild root: clears Castle collections; remaining blockout parts.
Detailed parts:
  Great Hall            -> build_21_greathall.py
  Tower cluster + clock -> build_22_towercluster.py
  East keeps + gallery  -> build_24_eastkeeps.py
  Viaduct               -> build_25_viaduct.py
  Boathouse + stairs    -> build_26_boathouse.py
  Curtain walls + drums -> build_28_walls.py
"""
import bpy
import math
import hog

hog.clear_coll('Castle')
# greenhouses -> build_27_greenhouses.py
