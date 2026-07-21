import bpy
from mathutils import Vector

CAM = bpy.data.collections["Cameras"]

def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

def add_cam(name, loc, target, lens=50):
    old = bpy.data.objects.get(name)
    if old: bpy.data.objects.remove(old)
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_end = 12000
    cd.clip_start = 0.3
    cd.dof.use_dof = False
    ob = bpy.data.objects.new(name, cd)
    CAM.objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    return ob

cam_hero = add_cam("Cam_Hero", (185, -455, 9), (-20, 5, 68), lens=55)
add_cam("Cam_Aerial", (370, -390, 285), (40, 0, 55), lens=50)
add_cam("Cam_Boathouse", (98, -198, 4), (50, -88, 32), lens=27)
add_cam("Cam_Viaduct", (165, 6, 63), (80, -5, 72), lens=38)
add_cam("Cam_Detail1", (140, 20, 82), (99, -13, 74), lens=55)
add_cam("Cam_Detail2", (98, -148, 4), (64, -112, 7), lens=34)
add_cam("Cam_Detail3", (2, -46, 104), (36, 14, 100), lens=52)
bpy.context.scene.camera = cam_hero
result = {"cameras": "ok"}
