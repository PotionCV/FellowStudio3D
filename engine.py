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
import motion_timing as MT
import hair
ROOT=Path(__file__).resolve().parent
RENDER_DEFAULTS=dict(parts=True,textures=True,gaps=True,outline=True,perfect=True)
LIMBS=('armL','armR','legL','legR')
COLORS={'armL':(232,180,105),'armR':(116,152,190),'legL':(138,180,128),'legR':(212,138,168),'head':(170,146,206),'torso':(216,118,90)}
LABELS={'body':'全身','arms':'双臂','legs':'双腿','armL':'左臂','armR':'右臂','legL':'左腿','legR':'右腿','torso':'腰 / 躯干','head':'头颈'}
LABELS['tail']='尾巴'
LABELS['hair']='头发'
POSES={'站立':'stand','下蹲':'crouch','举手':'cheer','伸手':'point','搬物':'carry','推东西':'push','敬礼':'salute','踢腿':'kick','挥拳':'punch','攀爬':'climb'}
ACTIONS={k:L.KINDS[k].label for k in ('stand',)+L.MENU}
ACTIONS['pose']=L.KINDS['pose'].label
PROJECT_NAMES=dict(stand='Idle',walk='Walk',run='Run',wave='Wave',raise_='Raise arms',stretch='Stretch',squat='Squat',bounce='Bounce',bow='Bow',shake='Shake head',nod='Nod')
PROJECT_NAMES['raise']=PROJECT_NAMES.pop('raise_')
PROJECT_NAMES.update(jump='Jump',thrust='Thrust',swing='Swing attack',kick='Kick',hit='Hit reaction',fall='Fall',getup='Get up',roll='Roll',climb='Climb',turn='Turn')
PROJECT_NAMES.update(twist='Waist twist',lift='Pick up')
PROJECT_NAMES.update(swim='Swim',hover='Hover')
PROJECT_NAMES['poseclip']='Pose animation'
PROJECT_NAMES['tail']='Tail motion'
PROJECT_NAMES['hair']='Hair motion'
POSE_CHANNELS=(*LIMBS,'tail',*hair.CHANNELS,'lean','rot','dx','dy','dz','body_pitch','body_axis','body_pivot','chest_yaw','pelvis_yaw','head','head_pitch','head_yaw','head_depth')

def channel_default(key):return [0.]*4 if key in LIMBS else [0.]*9 if key=='tail' or key in hair.CHANNELS else 0.

class PreviewCancelled(Exception):pass

def check_preview(cancel):
    if cancel is not None and cancel():raise PreviewCancelled()

def layer_targets(scope):
    if scope=='hair':return hair.CHANNELS
    upper=('armL','armR','lean','chest_yaw','head','head_pitch','head_yaw','head_depth')
    lower=('legL','legR','pelvis_yaw','dy')
    return upper if scope=='upper' else lower if scope=='lower' else ('head','head_pitch','head_yaw','head_depth') if scope=='head' else ('lean','rot','chest_yaw','pelvis_yaw','dy','dx','dz','body_pitch','body_axis','body_pivot') if scope=='torso' else targets(scope)

def mirror_pose(pose,model=None):
    result={}
    for key,value in pose.items():
        if key in LIMBS:
            result[key[:-1]+('L' if key.endswith('R') else 'R')]=[-value[0],-value[1],value[2],value[3]]
        elif key=='tail':result[key]=[v if i%3==0 else -v for i,v in enumerate(value)]
        elif key in hair.CHANNELS:
            target=key[:-1]+('L' if key.endswith('R') else 'R') if key.endswith(('L','R')) else key
            items=[p for p in (model or pose.get('_model') or {}).get('attachments',[]) if p.get('kind')=='hair' and p['section']!='cap']
            source=next((p for p in items if hair.channel(p)==key),None);other=hair.paired(items,source) if source else None
            if other is not None:target=hair.channel(other)
            result[target]=[v if i%3==0 else -v for i,v in enumerate(value)]
        else:result[key]=-value if key in ('dx','rot','body_axis','head','head_yaw','chest_yaw','pelvis_yaw','yaw') else value
    return result

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
    C=L.KINDS[kind];value=dict(kind=kind,params=C.defaults(),cycles=2 if kind=='run' else 1,mix=1.,retain=1.,enabled=True,scope='all',phase=0.,blend='add')
    if hasattr(C,'playback'):value.update(mode=C.playback,blend=C.blend,scope=C.scope,retain=0.)
    if getattr(C,'unilateral',False):value['side']='right'
    if kind=='raise':value['plane']='front'
    if kind=='lift':value.update(side='both',operation='pickup')
    if kind=='swim':value['style']='breast'
    if kind=='poseclip':
        from pose_animation import default_cards
        value.update(cards=default_cards(),ground=True)
    return value

def new_project(base='stand',name=None):
    preset=ROOT/'defaults'/f'{base}.json'
    if base in ('walk','run') and preset.exists():
        project=json.loads(preset.read_text(encoding='utf-8'))
        project['name']=name or PROJECT_NAMES[base]
        project['render']={**RENDER_DEFAULTS,**project.get('render',{})}
        return project
    result=dict(version=2,name=name or PROJECT_NAMES[base],seconds=1. if base in ('walk','run') else 2.,fps=12,
                base=entry(base),layers=[],controls={},physics={},render=dict(RENDER_DEFAULTS),yaw=0.,pitch=0.)
    if hasattr(L.KINDS[base],'playback'):result['playback']=L.KINDS[base].playback
    return result

def targets(scope):
    return LIMBS if scope=='body' else ('armL','armR') if scope=='arms' else ('legL','legR') if scope=='legs' else (scope,)

def samples(e,n,project=None):
    C=L.KINDS[e['kind']]; param=C.defaults();param.update(e.get('params',{}))
    if e['kind']=='hair':param['_channels']=hair.channels_for((project or {}).get('model')) or hair.CORE_CHANNELS
    if e['kind']=='kick':param['_style']=e.get('style','swing')
    if e['kind']=='swim':param['_style']=e.get('style','breast')
    if e['kind'] in ('swim','hover'):param['_float_pivot']=_roll_pivot(json.dumps(MD.normalize((project or {}).get('model')),sort_keys=True))
    if e['kind']=='raise':param['_plane']=e.get('plane','side')
    if e['kind']=='lift':
        param['_operation']=e.get('operation','pickup')
        param['_reach_factor']=C.reach_factor(param,(project or {}).get('model'),e.get('side','both'))
    if e['kind']=='pose':param['_pose']={k:copy.deepcopy(v) for k,v in e.get('pose',{}).items() if k in POSE_CHANNELS}
    if e['kind']=='poseclip':
        from pose_animation import normalize_cards
        param.update(_cards=normalize_cards(e.get('cards',[])),_loop=e.get('mode',MT.mode(project or {}))=='loop',_ground=e.get('ground',True))
    if e['kind']=='roll':param['_roll_pivot']=_roll_pivot(json.dumps(MD.normalize((project or {}).get('model')),sort_keys=True))
    result=[]
    for i in range(n):
        t=MT.sample_time(e,i,n,project)
        pose=C.at(t,param,0)
        if e['kind']=='pose' and e.get('ground'):pose['_ground']=True
        if e['kind']=='roll' and e.get('contact')=='air':pose['_ground']=False
        if e['kind']=='bounce' and param.get('high',0)>0 and .5-.5*math.cos(math.tau*t)>1e-6:pose['_ground']=False
        if e['kind'] in ('walk','run'):
            support=param.get('support',.5)
            if support!=.5:
                for limb,shift in (('legL',0),('legR',.5)):
                    u=(t+shift)%1;retimed=(u/support*.5 if u<support else .5+(u-support)/(1-support)*.5)-shift
                    pose[limb]=C.at(retimed%1,param,0)[limb]
            angle=math.radians(param.get('direction',0));stance=param.get('stance',1.)
            if angle or stance!=1:
                for limb in ('legL','legR'):
                    a,b,c,d=pose[limb];sign=-1 if limb.endswith('L') else 1
                    pose[limb]=[a+c*math.sin(angle)+sign*(stance-1)*12,b,c*math.cos(angle),d]
        if getattr(C,'unilateral',False):
            side=e.get('side','right')
            if side=='left':pose=mirror_pose(pose)
            elif side=='both':
                left=mirror_pose(C.at((t+.5)%1 if e.get('alternating') and e.get('mode')=='loop' else max(0.,2*t-1) if e.get('alternating') else t,param,0))
                if e.get('alternating') and e.get('mode')!='loop':pose=C.at(min(1.,2*t),param,0)
                for key,value in left.items():
                    if key in LIMBS:
                        if key not in pose or key.endswith('L'):pose[key]=value
                    elif key in pose and isinstance(value,(int,float)) and not isinstance(value,bool):pose[key]=(pose[key]+value)/2
                    else:pose.setdefault(key,value)
        if e['kind']=='wave':
            side=e.get('side',{'armL':'left','arms':'both'}.get(e.get('scope'),'right'))
            original=pose['armR'];pose={}
            if side in ('right','both'):pose['armR']=original
            if side in ('left','both'):
                other=C.at((t+(.5/max(1,param['times']) if side=='both' and e.get('alternating') else 0))%1,param,0)['armR']
                pose['armL']=[-other[0],-other[1],other[2],other[3]]
        result.append(pose)
    return result

def columns(seq,k):
    return np.array([p.get(k,channel_default(k)) for p in seq],dtype=float)

def flight_frames(seq,project):
    """Reserve flight height even when a pose layer precedes the jump layer."""
    count=len(seq);air=np.array([p.get('_ground') is False for p in seq])
    for entry in project.get('layers',[]):
        if entry['kind'] not in ('jump','bounce') or not entry.get('enabled',True) or entry.get('mix',1)<=0:continue
        if entry.get('scope','all')!='all' and 'dy' not in layer_targets(entry['scope']):continue
        for i,p in enumerate(samples(entry,count,project)):
            if p.get('_ground') is False and MT.layer_weight(entry,i,count,project)>1e-8:air[i]=True
    return air

def authored(project,cancel=None):
    check_preview(cancel)
    if isinstance(project.get('model'),dict) and 'face' in project['model']:project=dict(project,model={k:v for k,v in project['model'].items() if k!='face'})
    n=max(1,min(120,round(project.get('seconds',2)*project.get('fps',12))))
    if 'pose' in project: seq=[norm(project['pose']) for _ in range(n)]
    else:
        seq=[norm(F.POSES['stand']) for _ in range(n)]
        base={**project['base'],'mode':project.get('base_playback',MT.mode(project))}
        for p,b in zip(seq,samples(base,n,project)):p.update(b)
        seq=[norm(p) for p in seq]
    timed=any(any(k in e for k in ('start','end','span','fade')) for e in project.get('layers',[]) if e.get('enabled',True))
    range_reference={k:columns(seq,k).mean(axis=0) for k in LIMBS} if timed else None
    if 'model' in project:
        model=MD.normalize(project['model'])
        for pose in seq:pose['_model']=copy.deepcopy(model)
    controlled=False;flight=flight_frames(seq,project)
    for e in project.get('layers',[]):
        check_preview(cancel)
        if not e.get('enabled',True):continue
        if e['kind'] in ('thrust','swing'):
            if not e.get('mix',1) or not e.get('params',{}).get('reach',1):continue
            if not any(MT.layer_weight(e,i,n,project)>0 for i in range(n)):continue
            if not controlled:apply_controls(seq,project,range_reference);controlled=True
            apply_thrust(seq,e,project,cancel)
            continue
        w=float(e.get('mix',1)); retain=float(e.get('retain',1))
        ss=samples(e,n,project);keys=set().union(*(p.keys() for p in ss))
        weights=np.array([MT.layer_weight(e,i,n,project)*w for i in range(n)])
        scope=e.get('scope','all')
        if scope!='all':keys&=set(layer_targets(scope))
        keys.difference_update(('_ground','_feet_ground'))
        # Pose layers inherit an existing flight trajectory. Contact hints such
        # as a kick's supporting foot must not teleport an airborne character.
        forced_ground=e.get('contact','auto')=='ground'
        protected_height=flight|np.array([p.get('_ground') is False for p in seq]) if e['kind'] not in ('jump','bounce') and not forced_ground else np.zeros(n,dtype=bool)
        if scope in ('all','lower','legs'):
            for i,p in enumerate(seq):
                if weights[i]>1e-8 and '_ground' in ss[i]:
                    p['_ground']=True if forced_ground else bool(ss[i]['_ground']) and p.get('_ground',True)
                    if ss[i].get('_feet_ground'):p['_feet_ground']=True
                    else:p.pop('_feet_ground',None)
        for k in keys:
            old=columns(seq,k); add=columns(ss,k)
            weight=weights[:,None] if old.ndim>1 else weights
            if e.get('blend','posture' if e['kind'] in ('raise','wave') else 'add')=='posture':
                # Posture center and temporal motion are independent quantities.
                mean=old.mean(axis=0); am=add.mean(axis=0)
                val=(1-weight)*mean+weight*am+(old-mean)*(1-weight+weight*retain)+weight*(add-am)
            elif e.get('blend')=='replace':
                val=old*(1-weight)+(add+(old-old.mean(axis=0))*retain)*weight
            else:
                ref=np.array(R.spec4(F.POSES['stand'].get(k,(0,0)))) if k in LIMBS else 0.
                val=old+weight*(add-ref)
            if k=='dy':val[protected_height]=old[protected_height]
            for i,p in enumerate(seq):p[k]=val[i].tolist()
    if not controlled:apply_controls(seq,project,range_reference)
    if any(item.get('kind')=='tail' and item.get('wag') for item in (project.get('model') or {}).get('attachments',[])):
        for i,p in enumerate(seq):p['_motion_phase']=i/max(1,n if MT.mode(project)=='loop' else n-1)
    for p in seq:
        check_preview(cancel)
        p['yaw']=p.get('yaw',0)+project.get('yaw',0);p['pitch']=project.get('pitch',0)
        if p.get('_ground'):ground_pose(p)
        if project.get('camera_y'):p['_camera_y']=project['camera_y']
    if ('pose' not in project and project['base']['kind']=='stand'
            and project['base'].get('params',{}).get('breath',L.Stand.defaults()['breath'])>0
            and project.get('controls',{}).get('torso',{}).get('pin_feet',True)):
        # Derive reference feet from this exact pose/mix, with breathing removed.
        # This preserves a kick or jump's foot trajectory instead of grounding it.
        reference={k:copy.deepcopy(v) for k,v in project.items() if k not in ('assets3d','render')}
        reference['base'].setdefault('params',{})['breath']=0.
        for pose,rest in zip(seq,authored(reference,cancel)):
            check_preview(cancel)
            if pose.get('_ground') is False:continue
            pose['_foot_targets']={leg:[(yaw,R.chain(dict(rest,yaw=yaw,pitch=0,_camera_y=0),leg)[3]) for yaw in (45,135)] for leg in ('legL','legR')}
            pose['_breath_ik']=True
            pose['_breath_dy']=pose.get('dy',0)-rest.get('dy',0)
            lock_breath_feet(pose)
    return seq

def apply_thrust(seq,entry,project,cancel=None):
    C=L.KINDS[entry['kind']];params=C.defaults();params.update(entry.get('params',{}))
    side=entry.get('side','right');scope=entry.get('scope','all')
    allowed=None if scope=='all' else set(layer_targets(scope))
    means={arm:columns(seq,arm).mean(axis=0) for arm in ('armL','armR')}
    for i,pose in enumerate(seq):
        check_preview(cancel)
        weight=float(entry.get('mix',1))*MT.layer_weight(entry,i,len(seq),project)
        if weight<=0:continue
        t=MT.sample_time(entry,i,len(seq),project);drives=[]
        pinned={leg:[(yaw,R.chain(dict(pose,yaw=yaw,pitch=0),leg)[3]) for yaw in (45,135)] for leg in ('legL','legR')} if pose.get('_ground') is not False and (allowed is None or 'pelvis_yaw' in allowed) and project.get('controls',{}).get('torso',{}).get('pin_feet',True) else {}
        for current in (('left','right') if side=='both' else (side,)):
            phase=t
            if side=='both' and entry.get('alternating'):
                phase=(t+(.5 if current=='left' else 0))%1 if entry.get('mode')=='loop' else max(0.,2*t-1) if current=='left' else min(1.,2*t)
            arm='armL' if current=='left' else 'armR'
            goal,drive,extension=C.from_guard(phase,params,pose[arm],current)
            if allowed is None or arm in allowed:
                old=np.array(pose[arm]);target=np.array(goal)
                if entry.get('blend') in ('posture','replace'):target+=(old-means[arm])*float(entry.get('retain',0))*extension
                pose[arm]=(old+(target-old)*weight).tolist()
                strength=pose.setdefault('_thrust_strength',{})
                strength[arm]=max(strength.get(arm,0),min(1.,weight*extension))
            drives.append(drive)
        for key in drives[0]:
            if allowed is None or key in allowed:pose[key]=pose.get(key,0)+weight*sum(d[key] for d in drives)/len(drives)
        for leg,views in pinned.items():pose[leg]=R.solve_multi(dict(pose,_breath_ik=True),leg,views)

def apply_controls(seq,project,range_reference=None):
    for scope,c in sorted(project.get('controls',{}).items(),key=lambda item: (0 if item[0]=='body' else 1 if item[0] in ('arms','legs') else 2,item[0])):
        for k in targets(scope):
            if k=='hair':
                for channel in dict.fromkeys((*hair.channels_for(project.get('model')),*(k for k in hair.CHANNELS if any(k in p for p in seq) or any(name.startswith(k+'_') for name in c)))):
                    offset=np.array([c.get(channel+'_'+joint+'_'+axis,0.) for joint in ('root','middle','tip') for axis in ('pitch','yaw','roll')])
                    values=columns(seq,channel)*c.get('range',1)+offset
                    if c:
                        for pose,value in zip(seq,values):pose[channel]=value.tolist()
            elif k=='tail':
                names=('root','middle','tip');axes=('pitch','yaw','roll')
                offset=np.array([c.get(joint+'_'+axis,0.) for joint in names for axis in axes])
                values=columns(seq,'tail')*c.get('range',1)+offset
                if c:
                    for pose,value in zip(seq,values):pose['tail']=value.tolist()
            elif k in LIMBS:
                a=columns(seq,k); mean=range_reference[k] if range_reference is not None else a.mean(axis=0); a=mean+(a-mean)*c.get('range',1)
                sign=-1 if k.endswith('L') else 1
                adjustment=np.array([sign*c.get('raise',0),sign*c.get('bend',0),c.get('forward',0),c.get('fold',0)])+np.array(c.get('offset',[0,0,0,0]))
                a+=adjustment
                if range_reference is not None:range_reference[k]+=adjustment
                for i,p in enumerate(seq):p[k]=a[i].tolist()
            elif k in ('head','torso'):
                for p in seq:
                    if k=='head':p['head_pitch']+=c.get('nod',0);p['head']+=c.get('tilt',0);p['head_yaw']+=c.get('turn',0);p['head_depth']+=c.get('depth',0);p['head_follow_chest']=bool(c.get('follow_chest',True))
                    else:
                        pinned={leg:[(yaw,R.chain(dict(p,yaw=yaw,pitch=0),leg)[3]) for yaw in (45,135)] for leg in ('legL','legR')} if c.get('pin_feet',True) and p.get('_ground') is not False else {}
                        p['lean']+=c.get('lean',0);p['dy']+=c.get('height',0);p['dx']+=c.get('shift',0);p['rot']+=c.get('tilt',0);p['chest_yaw']+=c.get('turn',0);p['pelvis_yaw']+=c.get('hips_turn',0)
                        for leg,views in pinned.items():p[leg]=R.solve_multi(p,leg,views)

def lock_breath_feet(pose):
    for leg,views in pose.get('_foot_targets',{}).items():
        error=max(np.linalg.norm(np.array(R.chain(dict(pose,yaw=yaw,pitch=0,_camera_y=0),leg)[3])-target) for yaw,target in views)
        if error>.005:pose[leg]=R.solve_multi(dict(pose,_camera_y=0),leg,views)

def ground_pose(pose):
    import rounded_scene as S
    model=MD.normalize(pose.get('_model'));reference=_ground_level(json.dumps(model,sort_keys=True))
    bottom=S.ground_y(pose,('thighL','shinL','thighR','shinR') if pose.get('_feet_ground') else None)
    pose['dy']=pose.get('dy',0)+bottom-reference

@lru_cache(maxsize=64)
def _roll_pivot(model_key):
    import rounded_scene as S
    pose={'_model':json.loads(model_key),**norm(F.POSES['stand'])}
    j,triangles,_=S.pose_meshes(pose);vertices=np.concatenate([v for part,face,v,uv in triangles if not part.startswith('prop')])
    hip=np.mean([S.geometry(pose)[2][key][0] for key in ('legL','legR')],axis=0)
    return float((vertices[:,1].min()+vertices[:,1].max())/2-hip[1])

@lru_cache(maxsize=64)
def _ground_level(model_key):
    import rounded_scene as S
    return S.ground_y({'_model':json.loads(model_key),**norm(F.POSES['stand'])})

def _spring_track(target,roots,length,seconds,strength,bounce,periodic=True):
    """World-angle pendulum: spring torque + damping + acceleration of moving parent.
    Fixed integration step and periodic warm-up make random access/export deterministic.
    """
    count=len(target); dt=seconds/max(1,count if periodic else count-1)
    acc=(np.roll(roots,-1,axis=0)-2*roots+np.roll(roots,1,axis=0))/dt**2 if periodic else (np.gradient(np.gradient(roots,dt,axis=0),dt,axis=0) if count>2 else np.zeros_like(roots))
    freq=7.+15.*(1-strength); damp=2*freq*(.85-.55*bounce)
    x=float(target[0]);v=0.; out=np.empty(count)
    for cycle in range(40 if periodic else 1):
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

def physical(seq,project,cancel=None):
    check_preview(cancel)
    configs=dict(project.get('physics',{}))
    if any(item.get('kind')=='hair' for item in seq[0].get('_model',{}).get('attachments',[])) and 'hair' not in configs:configs['hair']=dict(hair.DEFAULT_PHYSICS)
    def amount(c):return max(c.get(k,0) for k in ('strength','upper','lower','root','middle','tip'))
    if not any(amount(c)>0 for c in configs.values()):return seq
    n=len(seq); seconds=project.get('seconds',2); sub=max(1,math.ceil(120*seconds/n));periodic=MT.mode(project)=='loop';count=n*sub if periodic else (n-1)*sub+1
    # Geometry is evaluated in two fixed anatomical planes, never in the preview camera.
    dense=[]
    for j in range(count):
        if j%16==0:check_preview(cancel)
        f=j/sub;i=int(f);u=f-i;p=copy.deepcopy(seq[i%n]);q=seq[(i+1)%n if periodic else min(i+1,n-1)]
        for k,v in p.items():
            if isinstance(v,(list,tuple)):p[k]=((1-u)*np.array(v)+u*np.array(q[k])).tolist()
            elif isinstance(v,(int,float)) and not isinstance(v,bool):p[k]=v*(1-u)+q[k]*u
        dense.append(p)
    for key,c in configs.items():
        check_preview(cancel)
        strength=amount(c); bounce=c.get('bounce',.4)
        if strength<=0:continue
        if key in LIMBS:
            upper_strength=c.get('upper',c.get('strength',0));lower_strength=c.get('lower',c.get('strength',0))
            for axis,yaw in ((0,0),(2,90)):
                check_preview(cancel)
                roots=[];parents=[];world_upper=[];world_lower=[]
                for p in dense:
                    check_preview(cancel)
                    view=dict(p,yaw=yaw,pitch=0)
                    chain=np.array(R.chain(view,key))
                    roots.append(chain[0] if periodic else chain[1]);parents.append(p.get('lean',0) if axis==2 and key.startswith('arm') else 0.)
                    if not periodic:
                        for values,vector in ((world_upper,chain[2]-chain[1]),(world_lower,chain[3]-chain[2])):
                            values.append(math.atan2(vector[0],vector[1]) if np.linalg.norm(vector)>1e-6 else (values[-1] if values else 0.))
                roots=np.array(roots);parents=np.array(parents)
                upper=np.array([p[key][axis] for p in dense])-parents if periodic else np.degrees(np.unwrap(world_upper))
                lower=upper+np.array([p[key][axis+1] for p in dense]) if periodic else np.degrees(np.unwrap(world_lower))
                lengths=R._rig(dense[0],key)[1]
                a=_spring_track(upper,roots,lengths[0],seconds,upper_strength,bounce,periodic)
                actual_upper=upper+(a-upper)*upper_strength
                elbow=roots+np.column_stack((np.sin(np.radians(actual_upper)), np.cos(np.radians(actual_upper)))) * lengths[0]
                b=_spring_track(lower,elbow,lengths[1],seconds,lower_strength,bounce,periodic)
                for j,p in enumerate(dense):
                    if periodic:
                        p[key][axis]=actual_upper[j]+parents[j]
                        p[key][axis+1]=lower[j]+(b[j]-lower[j])*lower_strength-actual_upper[j]
                    else:
                        p[key][axis]+=actual_upper[j]-upper[j]
                        p[key][axis+1]+=(b[j]-lower[j])*lower_strength-(actual_upper[j]-upper[j])
        elif key=='tail':
            import tails
            tails.physical(dense,c,seconds,periodic,_spring_track,lambda:check_preview(cancel))
        elif key=='hair':hair.physical(dense,c,seconds,periodic,_spring_track,lambda:check_preview(cancel))
        elif key=='head':
            roots=[]
            for p in dense:
                view=dict(p,yaw=90,pitch=0);roots.append(R.joints(view)['neck']['tip'])
            if periodic:target=np.array([p['head_pitch']+p['lean'] for p in dense])
            else:
                import rounded_scene as S
                axes=[S.geometry(p)[-1][1][:,1] for p in dense]
                target=np.degrees(np.unwrap([math.atan2(v[2],v[1]) for v in axes]))
            tracked=_spring_track(target,np.array(roots),7,seconds,strength,bounce,periodic)
            for j,p in enumerate(dense):p['head_pitch']+=(tracked[j]-target[j])*strength
    result=[dense[i*sub] for i in range(n)]
    for p,source in zip(result,seq):
        # The arm stiffens while the punch extends; ordinary softness resumes
        # on recovery instead of bending a completed straight strike back again.
        for arm,strength in source.get('_thrust_strength',{}).items():
            p[arm]=(np.array(p[arm])*(1-strength)+np.array(source[arm])*strength).tolist()
        original_dy=p.get('dy',0)
        if p.get('_ground'):ground_pose(p)
        if p.get('_breath_ik'):p['_breath_dy']+=p.get('dy',0)-original_dy
        lock_breath_feet(p)
    return result

@lru_cache(maxsize=6)
def _compiled(key):
    p=json.loads(key);return physical(authored(p),p)

def motion_project(project):
    motion={k:v for k,v in project.items() if k not in ('name','render','export_view','export_directions','auto_name_key','assets3d','camera_y')}
    if isinstance(motion.get('model'),dict) and 'face' in motion['model']:motion['model']={k:v for k,v in motion['model'].items() if k!='face'}
    return motion

def visible(seq,project,bundle=None):
    import rounded_scene,retro_animation
    seq=retro_animation.stylize(seq,project)
    bundle=bundle if bundle is not None else rounded_scene.assets(project)
    return [dict(pose,_assets3d=bundle,**({'_camera_y':project['camera_y']} if project.get('camera_y') else {})) for pose in seq]

def poses(project):
    motion=motion_project(project)
    seq=copy.deepcopy(_compiled(json.dumps(motion,sort_keys=True)))
    return visible(seq,project)

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
    for item in [p['base'],*p.get('layers',[])]:
        if item.get('kind')=='poseclip':
            from pose_animation import normalize_cards
            normalize_cards(item.get('cards',[]))
    return normalize_project_name(p)

def export_name(project,name=None):
    name=(name if name is not None else project.get('name','Animation')).strip()
    if not name or name in ('.','..') or re.search(r'[<>:"/\\|?*\x00-\x1f]',name) or name.endswith(('.', ' ')):
        raise ValueError('名称不能为空，或包含路径与文件名禁用字符')
    if name.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}:raise ValueError('请换一个导出名称')
    return name

def export(project,out=None,name=None,formats=None,create_folder=True,scale=1,directions=1,overwrite=False):
    if overwrite:
        from export_delivery import replace_export
        return replace_export(project,out,name,formats,create_folder,scale,directions,export)
    if isinstance(directions,bool) or not isinstance(directions,int) or directions not in (1,4,8):raise ValueError('方向数必须为1、4或8。')
    if directions!=1:
        import directional_export
        return directional_export.export(project,out,name,formats,create_folder,scale,directions)
    if 'export_directions' in project:project=dict(project,export_directions=1)
    if isinstance(scale,bool) or not isinstance(scale,int) or not 1<=scale<=8:raise ValueError('输出比例必须是 1 到 8 的整数')
    formats=set(('png','strip','gif','recipe') if formats is None else formats)
    if not formats or formats-{'png','strip','gif','recipe'}:raise ValueError('请选择至少一种有效的导出类型')
    import render_options as O
    width,height=(value*scale for value in O.size(project.get('render')))
    count=max(1,min(120,round(project.get('seconds',2)*project.get('fps',12))))
    if width*height*count*4>64*1024*1024 and formats-{'recipe'}:
        import directional_export
        return directional_export.export(project,out,name,formats,create_folder,scale,directions=1)
    parent=Path(out or ROOT/'out')
    requested=name
    name=export_name(project,name)
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
    if scale!=1:images=[im.resize((width,height),Image.Resampling.NEAREST) for im in images]
    if 'png' in formats:
        for i,im in enumerate(images):im.save(dest/f'{name}_{i:02d}.png')
    if 'strip' in formats:
        strip=Image.new('RGBA',(width*len(images),height))
        for i,im in enumerate(images):strip.paste(im,(i*width,0))
        strip.save(dest/f'{name}_strip.png')
    if 'gif' in formats:
        preview=[]
        for im in images:
            bg=Image.new('RGB',(width,height),(90,77,66));bg.paste(im,mask=im.getchannel('A'));preview.append(bg)
        preview[0].save(dest/f'{name}.gif',save_all=True,append_images=preview[1:],duration=round(1000/project.get('fps',12)),**({'loop':0} if MT.mode(project)=='loop' else {}))
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
def _spring_cached(target_bytes,roots_bytes,count,length,seconds,strength,bounce,periodic=True):
    target=np.frombuffer(target_bytes,dtype=np.float64);roots=np.frombuffer(roots_bytes,dtype=np.float64).reshape(count,2)
    return _spring_uncached(target,roots,length,seconds,strength,bounce,periodic)
def _spring_track(target,roots,length,seconds,strength,bounce,periodic=True):
    return _spring_cached(np.asarray(target,dtype=np.float64).tobytes(),np.asarray(roots,dtype=np.float64).tobytes(),len(target),length,seconds,strength,bounce,periodic).copy()
