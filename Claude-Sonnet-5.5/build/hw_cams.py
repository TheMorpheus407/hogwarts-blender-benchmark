"""Camera rig: the four deliverable cameras + three detail cameras."""
import bpy
import hw_scene as S

RIG = {
    'Cam_Hero': dict(loc=(-30.0, -520.0, 3.2), target=(-30.0, 0.0, 3.2), lens=32.0, shift=(0.0, 0.16)),
    'Cam_Aerial': dict(loc=(-372.0, -366.0, 156.0), target=(-10.0, 20.0, 84.0), lens=28.0, shift=(0.0, 0.05)),
    'Cam_Boathouse': dict(loc=(-14.0, -166.0, 2.0), target=(-50.0, -98.0, 24.0), lens=24.0, shift=(0.0, 0.0)),
    'Cam_Viaduct': dict(loc=(302.0, -1.5, 57.0), target=(40.0, -2.0, 78.0), lens=28.0, shift=(0.0, 0.0)),
    'Cam_Detail_01': dict(loc=(-62.0, -34.0, 108.0), target=(-96.0, 8.0, 150.0), lens=45.0, shift=(0.0, 0.0)),
    'Cam_Detail_02': dict(loc=(-24.0, -128.0, 3.0), target=(-48.0, -100.0, 7.5), lens=36.0, shift=(0.0, 0.0)),
    'Cam_Detail_03': dict(loc=(-150.0, -29.0, 58.0), target=(-158.0, -21.0, 70.0), lens=24.0, shift=(0.0, 0.0)),
}


def build():
    for name, r in RIG.items():
        S.make_camera(name, r['loc'], r['target'], lens=r['lens'], shift=r['shift'])
    bpy.context.scene.camera = bpy.data.objects['Cam_Hero']


def remove_test_cameras():
    for o in list(bpy.data.objects):
        if o.type == 'CAMERA' and o.name.startswith('Cam_Test'):
            d = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if d.users == 0:
                bpy.data.cameras.remove(d)
    for o in list(bpy.data.objects):
        if o.type == 'CAMERA' and o.name == 'Cam_TestP':
            d = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if d.users == 0:
                bpy.data.cameras.remove(d)
