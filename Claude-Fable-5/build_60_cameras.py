"""Cameras. (Scene lighting lives in build_50_lights.py.)"""
import bpy
import hog

hog.camera('Cam_Hero', (-85, -490, 45), (0, 0, 85), lens=47)
hog.camera('Cam_Aerial', (-260, -420, 260), (10, 20, 80), lens=50)
hog.camera('Cam_Boathouse', (-98, -166, 12), (-26, -90, 26), lens=33)
hog.camera('Cam_Viaduct', (172, -13, 60.5), (94, -4, 76), lens=30)
# detail close-up cameras (material/geometry proof shots)
hog.camera('Cam_Detail1', (-102, -72, 82), (-55, -18, 98), lens=45)
hog.camera('Cam_Detail2', (-62, -38, 168), (-6, 26, 158), lens=55)
hog.camera('Cam_Detail3', (-50, -121, 3.2), (-26.5, -96, 6.5), lens=45)
bpy.context.scene.camera = bpy.data.objects['Cam_Hero']
