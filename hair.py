"""Parametric hair sets, stable per-lock UVs and seven independent FK chains."""
import math,re
from functools import lru_cache
import numpy as np

STYLES={'short':'短碎发','bob':'波波头','long':'长直发','pony':'高马尾','twins':'双马尾'}
SECTIONS={'cap':'头发主体','bangL':'左刘海','bangR':'右刘海','sideL':'左中发束','sideR':'右中发束','back':'后发','ponyL':'左马尾','ponyR':'右马尾'}
ROLES={**SECTIONS,'lock':'自由发束'}

def role(item):return item.get('role',item['section'])

CORE_CHANNELS=tuple('hair_'+key for key in SECTIONS if key!='cap')
CHANNELS=CORE_CHANNELS+tuple('hair_extra'+str(i) for i in range(1,33))
DEFAULT_PHYSICS=dict(root=.05,middle=.3,tip=.55,bounce=.25)
SPECS=(('length','发束长度（px）',4,32,.5),('volume','头发蓬松（px）',.3,3,.1),
       ('bangs','刘海长度（px）',0,10,.5),('parting','分缝偏向',-1,1,.05),
       ('spread','发束张开（度）',0,50,1),('x','头发左右（px）',-6,6,.25),
       ('y','头发上下（px）',-6,6,.25),('z','头发前后（px）',-6,6,.25))

# Lock overrides are kept separately from whole-hairstyle parameters.
LOCK_SPECS=(('length','单束长度（px）',.5,48,.5),('width','单束宽度（px）',.5,24,.25),
 ('thickness','单束厚度（px）',.4,16,.2),('curl','单束弯曲（度）',-80,80,1),('tip','发梢饱满',0,1,.05),
 ('root_scale','发根宽度比例',.2,1.5,.05),('mid_scale','发中宽度比例',.2,1.5,.05),
 ('outward','发束侧倾（度）',-120,120,1),('lean','发束前后倾（度）',-90,90,1),
 ('yaw','发束转向（度）',-180,180,1),('twist','发片扭转（度）',-180,180,1),
 ('x','发束左右偏移（px）',-12,12,.25),('y','发束上下偏移（px）',-12,12,.25),('z','发束前后偏移（px）',-12,12,.25))
LOCK_DEFAULTS=dict(root_scale=1.,mid_scale=1.,tip=0.,lean=0.,yaw=0.,twist=0.)

def counterpart(section):return section[:-1]+('R' if section.endswith('L') else 'L') if section.endswith(('L','R')) else None

def lock_values(item,settings):
    override=settings.get('locks',{}).get(item['section'],{})
    return {key:override.get(key,0. if key in ('x','y','z') else item.get(key,LOCK_DEFAULTS.get(key,0.))) for key,*_ in LOCK_SPECS}

CAP_SPECS=(('width','发顶宽度（px）',3,48,.5),('length','发顶高度（px）',3,48,.5),('thickness','发顶厚度（px）',3,48,.5),
 ('front_cut','前额发际线',-.8,.8,.05),('back_cut','后侧覆盖',-.9,.8,.05),('crown_flat','顶部平缓',0,1,.05),('crown_width','顶部宽度比例',.5,1.5,.05),
 ('x','发顶左右（px）',-12,12,.25),('y','发顶上下（px）',-12,12,.25),('z','发顶前后（px）',-12,12,.25))
CAP_SHAPES={key:label for key,label in (('ellipsoid','圆润发顶'),('rounded_box','圆角发顶'),('box','方形发顶'),('cylinder','平顶发型'),('cone','尖顶发型'))}

def channel(item):return 'hair_extra'+re.match(r'hair(\d+)',item['id']).group(1) if item['section']=='lock' else 'hair_'+item['section']

def channels_for(model):return tuple(channel(p) for p in (model or {}).get('attachments',[]) if p.get('kind')=='hair' and p['section']!='cap')

def name(item):
    from i18n import tr
    label=tr(ROLES[role(item)])
    if item['section']=='lock' or item['section']=='cap' and item['id']!='hair1cap':label+=' '+re.match(r'hair(\d+)',item['id']).group(1)
    elif role(item)!=item['section']:label+=' · '+tr('部件')+str(tuple(SECTIONS).index(item['section'])+1)
    return label

def resolve(items,key):return next((p for p in items if p.get('id')==key),next((p for p in items if p.get('section')==key),None))

def partner(item):return item.get('mirror') or counterpart(item['section'])

def paired(items,item):
    other=resolve(items,partner(item))
    return other if other is not None and resolve(items,partner(other)) is item else None

def normalize_style(source):
    if not isinstance(source,dict):raise ValueError('Invalid hairstyle')
    style=source.get('style','short')
    if style not in STYLES:raise ValueError('Invalid hairstyle')
    defaults=dict(style=style,length={'short':7,'bob':12,'long':24,'pony':23,'twins':20}[style],volume=.8,bangs=4.,parting=0.,spread=25. if style=='twins' else 10.,x=0.,y=0.,z=0.)
    for key,_,lo,hi,_ in SPECS:
        value=source.get(key,defaults[key])
        if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value):raise ValueError('Invalid hair parameter: '+key)
        defaults[key]=float(np.clip(value,lo,hi))
    if 'locks' in source:
        locks=source['locks']
        if not isinstance(locks,dict):raise ValueError('Invalid hair locks')
        cleaned={}
        for section,values in locks.items():
            if section not in SECTIONS or section=='cap' or not isinstance(values,dict):raise ValueError('Invalid hair lock')
            record={}
            for key,_,lo,hi,_ in LOCK_SPECS:
                if key not in values:continue
                value=values[key]
                if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value):raise ValueError('Invalid hair lock parameter: '+key)
                record[key]=float(np.clip(value,lo,hi))
            if record:cleaned[section]=record
        if cleaned:defaults['locks']=cleaned
    if source.get('assembly'):
        if source['assembly'] is not True or not isinstance(source.get('pieces'),list) or len(source['pieces'])>32:raise ValueError('Invalid hair assembly')
        pieces=[normalize(p) for p in source['pieces']]
        if len({p['id'] for p in pieces})!=len(pieces):raise ValueError('Duplicate hair part')
        defaults.update(assembly=True,pieces=pieces);defaults.pop('locks',None)
    if 'cap' in source:
        override=source['cap']
        if not isinstance(override,dict):raise ValueError('Invalid hair cap')
        cap={}
        for key,_,lo,hi,_ in CAP_SPECS:
            if key not in override:continue
            value=override[key]
            if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value):raise ValueError('Invalid hair cap parameter')
            cap[key]=float(np.clip(value,lo,hi))
        if 'shape' in override:
            if override['shape'] not in CAP_SHAPES:raise ValueError('Invalid hair cap shape')
            cap['shape']=override['shape']
        if cap:defaults['cap']=cap
    return defaults

def normalize(source):
    if not isinstance(source,dict):raise ValueError('Invalid hair part')
    key=source.get('id','');section=source.get('section','')
    if not isinstance(key,str) or not (section in SECTIONS and key=='hair1'+section or section in ('cap','lock') and re.fullmatch(r'hair(?:[1-9]|[12][0-9]|3[0-2])'+section,key)) or source.get('parent','head')!='head':raise ValueError('Invalid hair part')
    result=dict(id=key,parent='head',kind='hair',section=section,shape=source.get('shape','lock'))
    if result['shape'] not in ('lock','ellipsoid','rounded_box','box','cylinder','cone','pyramid'):raise ValueError('Invalid hair shape')
    defaults=dict(width=4,length=8,thickness=2,curl=0,front_cut=.35,back_cut=-.5,x=0,y=0,z=0,outward=0,flex=1,crown_flat=0.,crown_width=1.,**LOCK_DEFAULTS)
    for key,lo,hi in (('width',.5,80),('length',.5,80),('thickness',.4,60),('curl',-80,80),('front_cut',-.8,.8),('back_cut',-.9,.8),('x',-50,50),('y',-40,50),('z',-40,40),('outward',-120,120),('flex',0,1),('root_scale',.2,1.5),('mid_scale',.2,1.5),('tip',0,1),('lean',-90,90),('yaw',-180,180),('twist',-180,180),('crown_flat',0,1),('crown_width',.5,1.5)):
        value=source.get(key,defaults[key])
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):raise ValueError('Invalid hair number: '+key)
        result[key]=float(np.clip(value,lo,hi))
    if 'role' in source:
        if source['role'] not in ROLES or (source['role']=='cap')!=(section=='cap'):raise ValueError('Invalid hair role')
        result['role']=source['role']
    if 'uv_mirror' in source:
        if not isinstance(source['uv_mirror'],bool):raise ValueError('Invalid hair UV mirror')
        result['uv_mirror']=source['uv_mirror']
    if 'mirror' in source:
        if not isinstance(source['mirror'],str) or not re.fullmatch(r'hair[1-9][0-9]?(?:cap|lock|bangL|bangR|sideL|sideR|back|ponyL|ponyR)',source['mirror']):raise ValueError('Invalid hair pair')
        result['mirror']=source['mirror']
    if source.get('profile'):
        import sculpt
        profile=source['profile']
        if not isinstance(profile,dict):raise ValueError('Invalid hair profile')
        result['profile']={k:float(profile[k]) for k in sculpt.DEFAULTS if k in profile and isinstance(profile[k],(float,int)) and not isinstance(profile[k],bool) and math.isfinite(profile[k])}
    return result

def records(model,settings):
    s=normalize_style(settings)
    if s.get('assembly'):return s['pieces']
    style=s['style'];v=s['volume']
    if model.get('structure')=='plush':
        b=model['body'];rx,ry,rz=b['upper_width']/2,b['height']*.2,b['depth']/2;shape='ellipsoid'
    else:rx,ry,rz=np.array((8,7.5,7.5))*model['head']['size'];shape=model['head']['shape']
    rx+=v;ry+=v;rz+=v;result=[]
    def add(section,**values):
        values={**dict(width=4,length=8,thickness=2,curl=-8,front_cut=.4-s['bangs']*.012,back_cut=-.25 if style=='short' else -.55,flex=.2 if style=='short' else .6 if style=='bob' else 1.),**values}
        if section=='cap':
            for key,value in s.get('cap',{}).items():
                values[key]=values.get(key,0.)+value if key in ('x','y','z') else value
        if section!='cap':
            for key,value in s.get('locks',{}).get(section,{}).items():
                values[key]=values.get(key,0.)+value if key in ('x','y','z') else value
        values.update(id='hair1'+section,section=section,parent='head',kind='hair')
        values['x']=values.get('x',0)+s['x'];values['y']=values.get('y',0)+s['y'];values['z']=values.get('z',0)+s['z'];result.append(normalize(values))
    add('cap',shape=shape,width=rx*2,length=ry*2,thickness=rz*2,flex=0,profile={k:model.get('head',{}).get(k,val) for k,val in __import__('sculpt').DEFAULTS.items()} if model.get('structure')!='plush' else {})
    if s['bangs']>0:
        for side,sign in (('L',-1),('R',1)):
            add('bang'+side,width=rx*.68*(1-sign*s['parting']*.35),length=max(.5,s['bangs']*(1+sign*s['parting']*.35)),thickness=2.,x=sign*rx*.32+s['parting']*rx*.18,y=ry*.73,z=rz*.87,outward=-sign*(8+s['parting']*10))
    if style in ('short','bob','long'):
        for side,sign in (('L',-1),('R',1)):
            add('side'+side,width=rx*.48,length=s['length']*(.6 if style=='short' else 1),thickness=3.,x=sign*rx*.86,y=ry*.3,z=0,outward=sign*s['spread']*.25)
    if style in ('bob','long'):
        add('back',width=rx*1.65,length=s['length'],thickness=3.,y=ry*.45,z=-rz*.82,curl=-5)
    elif style=='pony':
        add('back',width=rx*.7,length=s['length'],thickness=5.,y=ry*.9,z=-rz*.8,curl=35,outward=0)
    elif style=='twins':
        for side,sign in (('L',-1),('R',1)):
            add('pony'+side,width=rx*.62,length=s['length'],thickness=4.,x=sign*rx*.87,y=ry*.5,z=-rz*.4,curl=12,outward=sign*s['spread'])
    return result

def rebuild(model,settings):
    s=normalize_style(settings);others=[p for p in model.get('attachments',[]) if p.get('kind')!='hair'];items=records(model,s)
    if len(others)+len(items)>32:raise ValueError('Maximum 32 attachments')
    model['hairstyle']=s;model['attachments']=others+items

def dimensions(item):return item['width']*max(1.,item.get('root_scale',1.),item.get('mid_scale',1.)),item['length'],item['thickness']
def surface(item):return {k:item[k] for k in ('section','shape','width','length','thickness','curl','front_cut','back_cut','profile','root_scale','mid_scale','tip','crown_flat','crown_width') if k in item}
def proxy(item):return dict(shape='tube',width=item['width'],length=item['length'],thickness=item['thickness'],curl=item['curl'],tip=item.get('tip',0.))

def frame(item,model,head,pose):
    from core3d import rz,rx,ry
    anchor=np.array((item['x'],item['y'],item['z']))
    if model.get('structure')=='plush':
        import plush
        point=np.array((0.,model['body']['height']*.8,0.));origin,matrix=plush.local_frame(pose,point);u,_,vh=np.linalg.svd(matrix);rotation=u@vh;origin=origin+matrix@point
    else:origin,rotation=head
    return origin+rotation@anchor,rotation@rz(item.get('outward',0.))@ry(item.get('yaw',0.))@rx(item.get('lean',0.)) if item['section']=='cap' else rotation@rz(item['outward'])@ry(item.get('yaw',0.))@rx(180+item.get('lean',0.))@ry(item.get('twist',0.))

def mesh(item):
    if item['section']!='cap':
        import tails
        mesh,bounds=tails.mesh(proxy(item));root=item.get('root_scale',1.);middle=item.get('mid_scale',1.)
        if root==middle==1.:return mesh,bounds
        shaped=[]
        for face,points in mesh:
            points=points.copy();points[:,0]*=np.interp(points[:,1]/item['length'],[0,.5,1],[root,middle,1.]);shaped.append((face,points))
        lo,hi=bounds;lo=lo.copy();hi=hi.copy();lo[0]*=max(1.,root,middle);hi[0]*=max(1.,root,middle)
        return shaped,(lo,hi)
    triangles,bounds=_cap(tuple(item[k] for k in ('shape','width','length','thickness','front_cut','back_cut','crown_flat','crown_width')))
    if item.get('profile'):
        import sculpt
        triangles=[(face,sculpt.deform(points,bounds,item['profile'])) for face,points in triangles]
    if item.get('profile') or item.get('crown_width',1.)!=1.:
        vertices=np.concatenate([points for _,points in triangles]);bounds=(vertices.min(axis=0),vertices.max(axis=0))
    return triangles,bounds

@lru_cache(maxsize=64)
def _cap(key):
    shape,w,h,d,front,back,flat,top_width=key;radii=np.array((w,h,d))/2;inner=np.maximum(.1,radii-.45);rings=[];steps=5;sides=16
    for radius in (radii,inner):
        vertices=[]
        for j in range(steps+1):
            for i in range(sides):
                phi=i*math.tau/sides;cut=back+(front-back)*max(0,math.cos(phi))**2;theta=math.acos(cut)*j/steps
                q=np.array((math.sin(theta)*math.sin(phi),math.cos(theta),math.sin(theta)*math.cos(phi)))
                if shape=='rounded_box':q=q/max(1e-9,np.linalg.norm(q,ord=5))
                elif shape in ('box','cylinder','cone','pyramid'):
                    q=q/max(1e-9,np.max(np.abs(q)))
                    if shape in ('cylinder','cone'):q[[0,2]]/=max(1.,math.hypot(q[0],q[2]))
                    if shape in ('cone','pyramid'):q[[0,2]]*=(1-q[1])/2
                if q[1]>0:
                    q[[0,2]]*=1+(top_width-1)*q[1]
                    q[1]=q[1]*(1-flat)+min(1.,q[1]*2)*flat
                vertices.append(q*radius)
        rings.append(np.array(vertices))
    result=[]
    def triangle(points,outward):
        points=np.array(points);normal=np.cross(points[1]-points[0],points[2]-points[0])
        if np.linalg.norm(normal)<1e-9:return
        if normal@outward<0:points=points[::-1];normal=-normal
        axis=int(np.argmax(np.abs(normal)));face=(('right','left'),('top','bottom'),('front','back'))[axis][0 if normal[axis]>0 else 1];result.append((face,points))
    for layer,vertices in enumerate(rings):
        for j in range(steps):
            for i in range(sides):
                a=j*sides+i;b=j*sides+(i+1)%sides;c=(j+1)*sides+(i+1)%sides;e=(j+1)*sides+i
                for ids in ((a,b,c),(a,c,e)):
                    p=vertices[list(ids)];triangle(p,p.mean(axis=0)*(1 if layer==0 else -1))
    for i in range(sides):
        a=steps*sides+i;b=steps*sides+(i+1)%sides;p=[rings[0][a],rings[1][a],rings[1][b],rings[0][b]]
        for ids in ((0,1,2),(0,2,3)):triangle([p[n] for n in ids],np.array((0,-1,0)))
    return result,(-radii,radii)

def deform(raw,item,pose=None):
    if item['section']=='cap':return raw
    import tails
    return tails.skin(raw,proxy(item),pose.get(channel(item),[0.]*9) if pose is not None else [0.]*9)

def default_texture(layout):
    from PIL import Image,ImageDraw
    image=Image.new('RGBA',layout['size']);draw=ImageDraw.Draw(image)
    for face,(x,y,w,h) in layout['rects'].items():draw.rectangle((x,y,x+w-1,y+h-1),fill={'top':'#785447','bottom':'#49342f'}.get(face,'#62453b'))
    return image

def joints(item,model,head,pose):
    import tails
    origin,rotation=frame(item,model,head,pose);data=proxy(item);transforms,centers,_=tails.bone_transforms(data,pose.get(channel(item),[0.]*9))
    end=tails.deform(np.array([[0.,item['length'],0.]]),data)[0];offset,matrix=transforms[-1]
    return [origin+rotation@p for p in (*centers,offset+matrix@end)]

def physical(seq,config,seconds,periodic,spring,check):
    import rounded_scene as S,tails
    model=seq[0].get('_model',{});items=[p for p in model.get('attachments',[]) if p.get('kind')=='hair' and p['section']!='cap']
    heads=[S.geometry(p)[-1] for p in seq] if items else []
    for item in items:
        key=channel(item);data=proxy(item);check()
        for p in seq:p[key]=list(p.get(key,[0.]*9))
        frames=[frame(item,model,head,p) for p,head in zip(seq,heads)]
        for bone,name in enumerate(('root','middle','tip')):
            strength=float(np.clip(config.get(name,config.get('strength',0)),0,1))*item['flex']
            if strength<=0:continue
            roots=[];rotations=[]
            for p,(origin,rotation) in zip(seq,frames):
                _,centers,local=tails.bone_transforms(data,p[key]);roots.append(origin+rotation@centers[bone]);rotations.append(rotation@local[bone])
            roots=np.asarray(roots);r=np.asarray(rotations)
            targets=(np.arctan2(r[:,2,1],r[:,1,1]),np.arctan2(r[:,0,2],r[:,2,2]),np.arctan2(-r[:,0,1],r[:,1,1]))
            for axis,(angles,plane) in enumerate(zip(targets,(roots[:,[2,1]],roots[:,[0,2]],roots[:,[0,1]]*[-1,1]))):
                check();target=np.degrees(np.unwrap(angles));tracked=spring(target,plane,item['length']/3,seconds,strength,config.get('bounce',.25),periodic)
                for j,p in enumerate(seq):p[key][bone*3+axis]=float(np.clip(p[key][bone*3+axis]+(tracked[j]-target[j])*strength,-120,120))

class HairMotion:
    kind='hair';label='头发飘动';period=32;claims=CHANNELS;add=CHANNELS;playback='loop';blend='add';scope='all'
    params=tuple(dict(key=k,label=label,lo=lo,hi=hi,dflt=default,step=step) for k,label,lo,hi,default,step in (('sway','飘动幅度（度）',0,35,8,1),('lift','向后扬起（度）',-25,50,0,1),('follow','发梢跟随',0,1,.6,.05)))
    @classmethod
    def defaults(cls):return {p['key']:p['dflt'] for p in cls.params}
    @classmethod
    def touches(cls,key):return cls.claims
    @classmethod
    def at(cls,t,p,yaw):
        result={}
        for index,key in enumerate(p.get('_channels',CORE_CHANNELS)):
            values=[]
            for joint in range(3):
                phase=math.tau*(t%1-joint*p['follow']*.13-index*.035)
                values.extend((p['lift']/3+p['sway']*.25*math.cos(phase),p['sway']*(.25+.2*joint)*math.sin(phase),0.))
            result[key]=values
        return result
