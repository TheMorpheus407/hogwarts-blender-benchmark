import bpy
# wipe generated data for clean rebuild
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob)
for me in list(bpy.data.meshes):
    bpy.data.meshes.remove(me)
for ma in list(bpy.data.materials):
    bpy.data.materials.remove(ma)
for li in list(bpy.data.lights):
    bpy.data.lights.remove(li)
for ca in list(bpy.data.cameras):
    bpy.data.cameras.remove(ca)
result = {"reset": "ok"}
