
import bpy, os, time, json, hashlib, struct
ROOT='/home/morpheus/Documents/Morpheus-Produktion/Benchmarks/Blender/GPT-6.1-Sol'
DELIVERY=[
('Cam_Hero','hero.png'),
('Cam_Aerial','angle_aerial.png'),
('Cam_Boathouse','angle_boathouse.png'),
('Cam_Viaduct','angle_viaduct.png'),
('Cam_Detail_Turret','detail_01.png'),
('Cam_Detail_Boathouse','detail_02.png'),
('Cam_Detail_Stone','detail_03.png')]
def final_settings():
    s=bpy.context.scene
    s.render.engine='CYCLES';s.cycles.device='GPU';s.cycles.samples=1024
    s.cycles.use_adaptive_sampling=False;s.cycles.use_denoising=True;s.cycles.denoiser='OPTIX'
    s.render.resolution_x=3840;s.render.resolution_y=2160;s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.color_depth='16'
    s.render.use_persistent_data=True
    return s
def start_delivery(index):
    if bpy.app.is_job_running('RENDER'):raise RuntimeError('A render is already running')
    s=final_settings();cam,name=DELIVERY[index];s.camera=bpy.data.objects[cam];s.render.filepath=os.path.join(ROOT,name)
    state={'scene_revision':'gilding-enamel-connected-lead-v1','index':index,'camera':cam,'file':name,'started':time.time(),'settings':{'engine':s.render.engine,'samples':s.cycles.samples,'adaptive_sampling':s.cycles.use_adaptive_sampling,'denoising':s.cycles.use_denoising,'width':s.render.resolution_x,'height':s.render.resolution_y,'percentage':s.render.resolution_percentage,'color_depth':s.render.image_settings.color_depth}}
    bpy.app.driver_namespace['HG_RENDER']=state
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'hogwarts.blend'),compress=True)
    op=bpy.ops.render.render('INVOKE_DEFAULT',write_still=True)
    return {'started':name,'camera':cam,'operation':list(op),'settings':state['settings']}
def delivery_status():
    state=bpy.app.driver_namespace.get('HG_RENDER')
    if not state:return {'running':False,'state':None}
    return {**state,'running':bpy.app.is_job_running('RENDER'),'elapsed_seconds':round(time.time()-state['started'],1),'exists':os.path.isfile(os.path.join(ROOT,state['file']))}
def finish_delivery():
    if bpy.app.is_job_running('RENDER'):raise RuntimeError('Render is not complete')
    state=bpy.app.driver_namespace['HG_RENDER'];path=os.path.join(ROOT,state['file'])
    if os.path.getmtime(path)<state['started']-2:raise RuntimeError('The output predates this render: '+path)
    with open(path,'rb') as f:head=f.read(29)
    if head[:8]!=b'\x89PNG\r\n\x1a\n':raise RuntimeError('Invalid PNG: '+path)
    dims=struct.unpack('>II',head[16:24])
    if dims!=(3840,2160):raise RuntimeError('Wrong image size: '+str(dims))
    if head[24]!=16 or head[25]!=2:raise RuntimeError('Expected 16-bit RGB PNG')
    with open(path,'rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    rec={**state,'completed':time.time(),'elapsed_seconds':round(time.time()-state['started'],1),'bytes':os.path.getsize(path),'sha256':digest,'verified_png_dimensions':list(dims)}
    manifestpath=os.path.join(ROOT,'render_manifest.json')
    data=json.load(open(manifestpath)) if os.path.exists(manifestpath) else {'build_brief':'SPEC.md','blender_version':bpy.app.version_string,'scene':'hogwarts.blend','mood':'Moonlit Highland blue hour','procedural_only':True,'renders':{}}
    data['renders'][state['file']]=rec
    with open(manifestpath,'w') as f:json.dump(data,f,indent=2)
    return rec


def queue_tick():
    q=bpy.app.driver_namespace.get('HG_QUEUE')
    if not q or not q['active']:return None
    if bpy.app.is_job_running('RENDER'):return 2.0
    try:
        rec=finish_delivery();q['completed'].append(rec['file'])
        index=rec['index']+1
        if index>=len(DELIVERY):
            q['active']=False;q['current']=None;q['finished']=time.time()
            return None
        start_delivery(index);q['current']=DELIVERY[index][1]
        return 2.0
    except Exception as exc:
        q['active']=False;q['error']=str(exc)
        return None

def start_queue():
    q=bpy.app.driver_namespace.get('HG_QUEUE')
    if q and q.get('active'):raise RuntimeError('Delivery queue is already active')
    if bpy.app.is_job_running('RENDER'):raise RuntimeError('Render already active')
    q={'active':True,'current':DELIVERY[0][1],'completed':[],'error':None,'started':time.time()}
    bpy.app.driver_namespace['HG_QUEUE']=q
    first=start_delivery(0)
    bpy.app.timers.register(queue_tick,first_interval=2.0)
    return {'queue':q,'first_render':first}

def queue_status():
    q=bpy.app.driver_namespace.get('HG_QUEUE',{})
    state=bpy.app.driver_namespace.get('HG_RENDER',{})
    return {**q,'render_running':bpy.app.is_job_running('RENDER'),'current_elapsed_seconds':round(time.time()-state.get('started',time.time()),1)}
