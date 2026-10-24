"""Recipe composition, shared pose/IK geometry and deterministic secondary dynamics."""
from pathlib import Path
from functools import lru_cache
import copy, json, math, re, tempfile
import numpy as np
from PIL import Image
import fellow as F
import rig as R
import layers as L
import model_data as MD
ROOT=Path(__file__).resolve().parent
RENDER_DEFAULTS=dict(parts=True,gaps=True,outline=True,perfect=True)
LIMBS=('armL','armR','legL','legR')
COLORS={'armL':(232,180,105),'armR':(116,152,190),'legL':(138,180,128),'legR':(212,138,168),'head':(170,146,206),'torso':(216,118,90)}
LABELS={'body':'全身','arms':'双臂','legs':'双腿','armL':'左臂','armR':'右臂','legL':'左腿','legR':'右腿','torso':'腰 / 躯干','head':'头颈'}
POSES={'站立':'stand','下蹲':'crouch','举手':'cheer','伸手':'point','搬物':'carry','推东西':'push','敬礼':'salute','踢腿':'kick','挥拳':'punch','攀爬':'climb'}
ACTIONS={k:L.KINDS[k].label for k in ('stand',)+L.MENU}
PROJECT_NAMES=dict(stand='Idle',walk='Walk',run='Run',wave='Wave',raise_='Raise arms',stretch='Stretch',squat='Squat',bounce='Bounce',bow='Bow',shake='Shake head',nod='Nod')
PROJECT_NAMES['raise']=PROJECT_NAMES.pop('raise_')

def automatic_name(key):
    import i18n
    return i18n.CATALOG.get(key,{}).get('en',key)

def normalize_project_name(project):
    key=project.get('auto_name_key')
    if key:
        import i18n
        known={key,*i18n.CATALOG.get(key,{}).values()}
        if project.get('name') in known:project['name']=automatic_name(key)
    return project

def norm(p):
    d=dict(lean=0.,rot=0.,dx=0.,dy=0.,head=0.,head_pitch=0.,head_yaw=0.,head_depth=0.,head_follow_chest=True,chest_yaw=0.,pelvis_yaw=0.,yaw=0.,pitch=0.)
    d.update(copy.deepcopy(p))
    for k in LIMBS:d[k]=list(R.spec4(d.get(k,(0,0))))
    return d

def entry(kind):
    return dict(kind=kind,params=L.KINDS[kind].defaults(),cycles=2 if kind=='run' else 1,mix=1.,retain=1.,enabled=True,scope='all',phase=0.)

def new_project(base='stand',name=None):
    preset=ROOT/'defaults'/f'{base}.json'
    if base in ('walk','run') and preset.exists():
        project=json.loads(preset.read_text(encoding='utf-8'))
        project['name']=name or PROJECT_NAMES[base]
        project['render']={**RENDER_DEFAULTS,**project.get('render',{})}
        return project
    return dict(version=2,name=name or PROJECT_NAMES[base],seconds=1. if base in ('walk','run') else 2.,fps=12,
                base=entry(base),layers=[],controls={},physics={},render=dict(RENDER_DEFAULTS),yaw=0.,pitch=0.)

def targets(scope):
    return LIMBS if scope=='body' else ('armL','armR') if scope=='arms' else ('legL','legR') if scope=='legs' else (scope,)

def samples(e,n):
    C=L.KINDS[e['kind']]; param=C.defaults();param.update(e.get('params',{}))
    return [C.at((i/n*e.get('cycles',1)+e.get('phase',0))%1,param,0) for i in range(n)]

def columns(seq,k):
    return np.array([p.get(k,[0.]*4 if k in LIMBS else 0.) for p in seq],dtype=float)

def authored(project):
    n=max(1,min(120,round(project.get('seconds',2)*project.get('fps',12))))
    if 'pose' in project: seq=[norm(project['pose']) for _ in range(n)]
    else:
        seq=[norm(F.POSES['stand']) for _ in range(n)]
        for p,b in zip(seq,samples(project['base'],n)):p.update(b)
        seq=[norm(p) for p in seq]
    for e in project.get('layers',[]):
        if not e.get('enabled',True):continue
        w=float(e.get('mix',1)); retain=float(e.get('retain',1))
        ss=samples(e,n);keys=set().union(*(p.keys() for p in ss))
        scope=e.get('scope','all')
        if scope!='all':keys&=set(targets(scope))
        for k in keys:
            old=columns(seq,k); add=columns(ss,k)
            if e['kind'] in ('raise','wave'):
                # Posture center and temporal motion are independent quantities.
                mean=old.mean(axis=0); am=add.mean(axis=0)
                val=(1-w)*mean+w*am+(old-mean)*(1-w+w*retain)+w*(add-am)
            else:
                ref=np.array(R.spec4(F.POSES['stand'].get(k,(0,0)))) if k in LIMBS else 0.
                val=old+w*(add-ref)
            for i,p in enumerate(seq):p[k]=val[i].tolist()
    if 'model' in project:
        model=MD.normalize(project['model'])
        for pose in seq:pose['_model']=copy.deepcopy(model)
    for scope,c in sorted(project.get('controls',{}).items(),key=lambda item: (0 if item[0]=='body' else 1 if item[0] in ('arms','legs') else 2,item[0])):
        for k in targets(scope):
            if k in LIMBS:
                a=columns(seq,k); mean=a.mean(axis=0); a=mean+(a-mean)*c.get('range',1)
                sign=-1 if k.endswith('L') else 1
                a+=np.array([sign*c.get('raise',0),sign*c.get('bend',0),c.get('forward',0),c.get('fold',0)])
                a+=np.array(c.get('offset',[0,0,0,0]))
                for i,p in enumerate(seq):p[k]=a[i].tolist()
            elif k in ('head','torso'):
                for p in seq:
                    if k=='head':p['head_pitch']+=c.get('nod',0);p['head']+=c.get('tilt',0);p['head_yaw']+=c.get('turn',0);p['head_depth']+=c.get('depth',0);p['head_follow_chest']=bool(c.get('follow_chest',True))
                    else:
                        pinned={leg:[(yaw,R.chain(dict(p,yaw=yaw,pitch=0),leg)[3]) for yaw in (45,135)] for leg in ('legL','legR')} if c.get('pin_feet',True) else {}
                        p['lean']+=c.get('lean',0);p['dy']+=c.get('height',0);p['dx']+=c.get('shift',0);p['rot']+=c.get('tilt',0);p['chest_yaw']+=c.get('turn',0);p['pelvis_yaw']+=c.get('hips_turn',0)
                        for leg,views in pinned.items():p[leg]=R.solve_multi(p,leg,views)
    for p in seq:
        p['yaw']=p.get('yaw',0)+project.get('yaw',0);p['pitch']=project.get('pitch',0)
    return seq

def _spring_track(target,roots,length,seconds,strength,bounce):
    """World-angle pendulum: spring torque + damping + acceleration of moving parent.
    Fixed integration step and periodic warm-up make random access/export deterministic.
    """
    count=len(target); dt=seconds/count
    acc=(np.roll(roots,-1,axis=0)-2*roots+np.roll(roots,1,axis=0))/dt**2
    freq=7.+15.*(1-strength); damp=2*freq*(.85-.55*bounce)
    x=float(target[0]);v=0.; out=np.empty(count)
    for cycle in range(40):
        start=(x,v)
        for j in range(count):
            theta=math.radians(x)
            inertia=-(acc[j,0]*math.cos(theta)-acc[j,1]*math.sin(theta))/max(1,length)*180/math.pi
            force=freq*freq*(target[j]-x)-damp*v+inertia*strength
            v+=dt*force;x+=dt*v
            x=max(float(target[j])-75,min(float(target[j])+75,x));v=max(-1000.,min(1000.,v))
            out[j]=x
        if cycle>3 and abs(x-start[0])+abs(v-start[1])<.001:break
    return out

def physical(seq,project):
    configs=project.get('physics',{})
    if not any(max(c.get('strength',0),c.get('upper',0),c.get('lower',0))>0 for c in configs.values()):return seq
    n=len(seq); seconds=project.get('seconds',2); sub=max(1,math.ceil(120*seconds/n));count=n*sub
    # Geometry is evaluated in two fixed anatomical planes, never in the preview camera.
    dense=[]
    for j in range(count):
        f=j/sub;i=int(f);u=f-i;p=copy.deepcopy(seq[i%n]);q=seq[(i+1)%n]
        for k,v in p.items():
            if isinstance(v,(list,tuple)):p[k]=((1-u)*np.array(v)+u*np.array(q[k])).tolist()
            elif isinstance(v,(int,float)) and not isinstance(v,bool):p[k]=v*(1-u)+q[k]*u
        dense.append(p)
    for key,c in configs.items():
        strength=max(c.get('strength',0),c.get('upper',0),c.get('lower',0)); bounce=c.get('bounce',.4)
        if strength<=0:continue
        if key in LIMBS:
            upper_strength=c.get('upper',c.get('strength',0));lower_strength=c.get('lower',c.get('strength',0))
            for axis,yaw in ((0,0),(2,90)):
                roots=[];parents=[]
                for p in dense:
                    view=dict(p,yaw=yaw,pitch=0)
                    roots.append(R.chain(view,key)[0]);parents.append(p.get('lean',0) if axis==2 and key.startswith('arm') else 0.)
                roots=np.array(roots);parents=np.array(parents)
                upper=np.array([p[key][axis] for p in dense])-parents
                lower=upper+np.array([p[key][axis+1] for p in dense])
                lengths=R._rig(dense[0],key)[1]
                a=_spring_track(upper,roots,lengths[0],seconds,upper_strength,bounce)
                actual_upper=upper+(a-upper)*upper_strength
                elbow=roots+np.column_stack((np.sin(np.radians(actual_upper)), np.cos(np.radians(actual_upper)))) * lengths[0]
                b=_spring_track(lower,elbow,lengths[1],seconds,lower_strength,bounce)
                for j,p in enumerate(dense):
                    p[key][axis]=actual_upper[j]+parents[j]
                    p[key][axis+1]=lower[j]+(b[j]-lower[j])*lower_strength-actual_upper[j]
        elif key=='head':
            roots=[]
            for p in dense:
                view=dict(p,yaw=90,pitch=0);roots.append(R.joints(view)['neck']['tip'])
            target=np.array([p['head_pitch']+p['lean'] for p in dense])
            tracked=_spring_track(target,np.array(roots),7,seconds,strength,bounce)
            for j,p in enumerate(dense):p['head_pitch']+=(tracked[j]-target[j])*strength
    return [dense[i*sub] for i in range(n)]

@lru_cache(maxsize=6)
def _compiled(key):
    p=json.loads(key);return physical(authored(p),p)

def poses(project):
    motion={k:v for k,v in project.items() if k not in ('name','render','export_view','auto_name_key','assets3d')}
    seq=copy.deepcopy(_compiled(json.dumps(motion,sort_keys=True)))
    import rounded_scene
    bundle=rounded_scene.assets(project)
    for pose in seq:pose['_assets3d']=bundle
    return seq

OUTLINE_COLOR=(128,128,128,255)
PART_OUTLINE_COLOR=(72,72,72,255)
def outer_ring(silhouette,perfect=False):
    # Flood exterior background with vectorized 4-neighbor propagation.
    padded=np.pad(silhouette.astype(np.uint8),1)
    background=padded==0;outside=np.zeros_like(background)
    outside[[0,-1],:]=True;outside[:,[0,-1]]=True
    while True:
        grown=outside.copy();grown[1:,:]|=outside[:-1,:];grown[:-1,:]|=outside[1:,:]
        grown[:,1:]|=outside[:,:-1];grown[:,:-1]|=outside[:,1:];grown &= background
        if np.array_equal(grown,outside):break
        outside=grown
    exterior=outside[1:-1,1:-1]
    expanded=np.zeros_like(padded,dtype=bool)
    for y in (-1,0,1):
        for x in (-1,0,1):
            if perfect and abs(x)+abs(y)>1:continue
            expanded[1:-1,1:-1] |= padded[1+y:padded.shape[0]-1+y,1+x:padded.shape[1]-1+x]>0
    return expanded[1:-1,1:-1] & exterior

def rgba(pose,settings=None,cam=(0,0)):
    settings={**RENDER_DEFAULTS,**(settings or {})};p=dict(pose,yaw=pose.get('yaw',0)+cam[0],pitch=pose.get('pitch',0)+cam[1])
    old=F.NO_CARVE;old_perfect=F.PIXEL_PERFECT
    try:
        F.PIXEL_PERFECT=settings.get('perfect',False)
        F.NO_CARVE=not settings.get('gaps',True);mask=F.render(p);parts=dict(F.LAST_PARTS);silhouette=F.LAST_SILHOUETTE.copy()
    finally:F.NO_CARVE=old;F.PIXEL_PERFECT=old_perfect
    a=np.zeros((64,64,4),np.uint8);a[mask]=(255,255,255,255)
    if settings.get('parts',False):
        for group in reversed(F.layer_order(p,F.yaw_of(p),F.pitch_of(p))):
            for k in group:
                m=parts[k][:,::-1] if p.get('flip') else parts[k];a[m]=COLORS[k]+(255,)
    if settings.get('outline',True):
        if p.get('flip'):silhouette=silhouette[:,::-1]
        # Carved overlap pixels become opaque separation lines when outlining.
        # Natural background holes are excluded because they are outside the raw silhouette.
        lines=outer_ring(silhouette,perfect=settings.get('perfect',False)) | (silhouette & ~mask)
        a[lines]=PART_OUTLINE_COLOR if settings.get('parts',False) else OUTLINE_COLOR
    return a

def save(project,path):
    path=Path(path);temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(project,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(path)

def load(path):
    p=json.loads(Path(path).read_text(encoding='utf-8'))
    if p.get('version')!=2 or 'base' not in p:raise ValueError('请选择新版动作工坊的配方；旧版文件保留在原工具中。')
    if p['base']['kind'] not in L.KINDS:raise ValueError('未知基础动作')
    return normalize_project_name(p)

def export(project,out=None,name=None,formats=None,create_folder=True,scale=1):
    if isinstance(scale,bool) or not isinstance(scale,int) or not 1<=scale<=8:raise ValueError('输出比例必须是 1 到 8 的整数')
    formats=set(('png','strip','gif','recipe') if formats is None else formats)
    if not formats or formats-{'png','strip','gif','recipe'}:raise ValueError('请选择至少一种有效的导出类型')
    parent=Path(out or ROOT/'out')
    requested=name
    name=(name if name is not None else project.get('name','Animation')).strip()
    if not name or name in ('.','..') or re.search(r'[<>:"/\\|?*\x00-\x1f]',name) or name.endswith(('.', ' ')):
        raise ValueError('名称不能为空，或包含路径与文件名禁用字符')
    if name.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}:raise ValueError('请换一个导出名称')
    parent.mkdir(parents=True,exist_ok=True)
    dest=(parent/name if requested is not None else Path(tempfile.mkdtemp(prefix=name+'_',dir=parent))) if create_folder else parent
    if create_folder and requested is not None:dest.mkdir(exist_ok=False)
    seq=poses(project) if formats-{'recipe'} else []
    recipe_file='recipe.json' if create_folder else f'{name}.json'
    if not create_folder:
        targets=([f'{name}_{i:02d}.png' for i in range(len(seq))] if 'png' in formats else [])
        targets+=([f'{name}_strip.png'] if 'strip' in formats else [])
        targets+=([f'{name}.gif'] if 'gif' in formats else [])
        targets+=([recipe_file] if 'recipe' in formats else [])
        if any((dest/file).exists() for file in targets):raise FileExistsError('同名文件已存在，请更换名称或目录')
    view=project.get('export_view',{});cam=(view.get('yaw',0),view.get('pitch',0))
    images=[Image.fromarray(rgba(p,project.get('render'),cam)) for p in seq]
    size=64*scale
    if scale!=1:images=[im.resize((size,size),Image.Resampling.NEAREST) for im in images]
    if 'png' in formats:
        for i,im in enumerate(images):im.save(dest/f'{name}_{i:02d}.png')
    if 'strip' in formats:
        strip=Image.new('RGBA',(size*len(images),size))
        for i,im in enumerate(images):strip.paste(im,(i*size,0))
        strip.save(dest/f'{name}_strip.png')
    if 'gif' in formats:
        preview=[]
        for im in images:
            bg=Image.new('RGB',(size,size),(90,77,66));bg.paste(im,mask=im.getchannel('A'));preview.append(bg)
        preview[0].save(dest/f'{name}.gif',save_all=True,append_images=preview[1:],duration=round(1000/project.get('fps',12)),loop=0)
    if 'recipe' in formats:save(dict(project,name=name),dest/recipe_file)
    return dest

# Preserve the mature motion composition and tuned recipes; only replace the
# image formation stage. All four views observe the same three-dimensional pose.
def rgba(pose,settings=None,cam=(0,0)):
    import rounded_scene
    return rounded_scene.render(pose,settings,cam)

# Cache deterministic spring solves independently per body part. Editing one arm
# leaves the other limbs' targets and parent trajectories reusable.
_spring_uncached=_spring_track
@lru_cache(maxsize=128)
def _spring_cached(target_bytes,roots_bytes,count,length,seconds,strength,bounce):
    target=np.frombuffer(target_bytes,dtype=np.float64);roots=np.frombuffer(roots_bytes,dtype=np.float64).reshape(count,2)
    return _spring_uncached(target,roots,length,seconds,strength,bounce)
def _spring_track(target,roots,length,seconds,strength,bounce):
    return _spring_cached(np.asarray(target,dtype=np.float64).tobytes(),np.asarray(roots,dtype=np.float64).tobytes(),len(target),length,seconds,strength,bounce).copy()
