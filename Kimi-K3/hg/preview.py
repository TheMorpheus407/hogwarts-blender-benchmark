import bpy, math
from mathutils import Vector
from math import pi

L = bpy.data.collections["Lights"]
CAM = bpy.data.collections["Cameras"]

def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

def add_cam(name, loc, target, lens=50):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    ob = bpy.data.objects.new(name, cd)
    CAM.objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    return ob

# hero camera: low across the lake, castle on crag
cam_hero = add_cam("Cam_Hero", (150, -430, 10), (-10, 0, 62), lens=52)
bpy.context.scene.camera = cam_hero

# moon key light: high NE, cool blue
sd = bpy.data.lights.new("MoonKey", 'SUN')
sd.energy = 2.2
sd.color = (0.55, 0.68, 0.95)
sd.angle = 0.05
so = bpy.data.objects.new("MoonKey", sd)
L.objects.link(so)
so.rotation_euler = (pi/3.2, 0, pi/5)

# faint cool fill from opposite
fd = bpy.data.lights.new("Fill", 'SUN')
fd.energy = 0.25
fd.color = (0.35, 0.42, 0.6)
fo = bpy.data.objects.new("Fill", fd)
L.objects.link(fo)
fo.rotation_euler = (pi/2.4, 0, -pi/1.4)

result = {"preview_setup": "ok"}
