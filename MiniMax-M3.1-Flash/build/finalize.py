"""Post-render housekeeping: purge orphan data and save the deliverable .blend.

The SPEC asks for clean scene organisation and no orphan data.  The build
leaves behind the boolean-cutter meshes, the window template meshes whose
objects were re-materialled, and the old image datablocks; none of them
affect the render, but they should not ship in the file.
"""
import bpy

ROOT = "/home/morpheus/Documents/Morpheus-Produktion/Benchmarks/Blender/MiniMax-M3.1-Flash"

report = {}
for _ in range(4):
    n = 0
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images,
                 bpy.data.lights, bpy.data.cameras, bpy.data.curves,
                 bpy.data.node_groups, bpy.data.textures, bpy.data.collections):
        for db in list(coll):
            if db.users == 0 and not db.use_fake_user:
                try:
                    coll.remove(db)
                    n += 1
                except Exception:
                    pass
    report["removed_round"] = n
    if n == 0:
        break

scn = bpy.context.scene
scn.camera = bpy.data.objects["Cam_Hero"]
bpy.ops.wm.save_as_mainfile(filepath=ROOT + "/hogwarts.blend")

report["objects"] = len(bpy.data.objects)
report["meshes"] = len(bpy.data.meshes)
report["materials"] = len(bpy.data.materials)
report["images"] = len(bpy.data.images)
report["orphan_meshes"] = sum(1 for m in bpy.data.meshes if m.users == 0)
report["orphan_materials"] = sum(1 for m in bpy.data.materials if m.users == 0)
report["collections"] = {c.name: len(c.objects) for c in bpy.data.collections}
report["saved"] = True
result = report
