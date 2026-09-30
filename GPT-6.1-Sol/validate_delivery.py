
import bpy, math, json, hashlib, struct
from pathlib import Path
ROOT=Path('/home/morpheus/Documents/Morpheus-Produktion/Benchmarks/Blender/GPT-6.1-Sol')
REVISION='gilding-enamel-connected-lead-v1'
EXPECTED={'hero.png':'Cam_Hero','angle_aerial.png':'Cam_Aerial','angle_boathouse.png':'Cam_Boathouse','angle_viaduct.png':'Cam_Viaduct','detail_01.png':'Cam_Detail_Turret','detail_02.png':'Cam_Detail_Boathouse','detail_03.png':'Cam_Detail_Stone'}
def scene_audit():
    s=bpy.context.scene;meshes=[m for m in bpy.data.meshes if m.users]
    invalid_meshes=[m.name for m in meshes if any(not all(math.isfinite(c) for c in v.co) for v in m.vertices)]
    invalid_transforms=[o.name for o in s.objects if any(not math.isfinite(c) for row in o.matrix_world for c in row)]
    missing_meshes=set()
    for me in meshes:
        used={p.material_index for p in me.polygons}
        if not me.materials or any(i>=len(me.materials) or me.materials[i] is None for i in used):missing_meshes.add(me.name)
    missing=[o.name for o in s.objects if o.type=='MESH' and not o.hide_render and o.data.name in missing_meshes]
    groups=[bpy.data.objects,bpy.data.meshes,bpy.data.materials,bpy.data.curves,bpy.data.textures,bpy.data.collections,bpy.data.cameras,bpy.data.lights,bpy.data.worlds,bpy.data.node_groups,bpy.data.texts]
    orphans=[x.name for ids in groups for x in ids if x.users==0]
    node_trees=[m.node_tree for m in bpy.data.materials if m.use_nodes]+[w.node_tree for w in bpy.data.worlds if w.use_nodes]+list(bpy.data.node_groups)
    report={'scene':s.name,'scene_revision':s.get('delivery_revision'),'blender':bpy.app.version_string,'units':s.unit_settings.system,'metres_per_unit':s.unit_settings.scale_length,'objects':len(s.objects),'unique_meshes':len(meshes),'unique_mesh_vertices':sum(len(m.vertices) for m in meshes),'unique_mesh_polygons':sum(len(m.polygons) for m in meshes),'window_objects':sum(o.get('architectural_element')=='arched mullioned window' for o in s.objects),'forest_instances':sum(o.name.startswith('Forest •') for o in s.objects),'root_collections':[c.name for c in s.collection.children],'cameras':sorted(o.name for o in s.objects if o.type=='CAMERA'),'linked_libraries':len(bpy.data.libraries),'image_texture_nodes':sum(n.type=='TEX_IMAGE' for nt in node_trees for n in nt.nodes),'external_image_paths':[i.filepath for i in bpy.data.images if i.filepath],'visible_meshes_without_materials':missing,'nonfinite_object_transforms':invalid_transforms,'nonfinite_mesh_coordinates':invalid_meshes,'orphan_datablocks':orphans}
    assert not any([invalid_meshes,invalid_transforms,missing,orphans,report['linked_libraries'],report['image_texture_nodes'],report['external_image_paths']]),report
    assert set(EXPECTED.values()).issubset(report['cameras'])
    assert report['units']=='METRIC' and report['metres_per_unit']==1.0
    return report

def verify_renders():
    manifest=json.loads((ROOT/'render_manifest.json').read_text());proof=[]
    for name,cam in EXPECTED.items():
        rec=manifest['renders'][name];path=ROOT/name;header=path.read_bytes()[:29]
        assert header[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',header[16:24])==(3840,2160)
        assert header[24:26]==bytes([16,2])
        assert rec['camera']==cam and rec['scene_revision']==REVISION
        settings=rec['settings']
        assert settings['engine']=='CYCLES' and settings['samples']==1024 and settings['denoising'] and not settings['adaptive_sampling']
        assert settings['width']==3840 and settings['height']==2160 and settings['percentage']==100
        with path.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
        assert digest==rec['sha256'] and path.stat().st_size==rec['bytes']
        assert path.stat().st_mtime>=rec['started']-2
        proof.append({'file':name,'camera':cam,'dimensions':[3840,2160],'bit_depth':16,'samples':1024,'denoised':True,'bytes':rec['bytes'],'sha256':digest})
    return proof
