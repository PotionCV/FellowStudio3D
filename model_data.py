"""Portable parametric model resources. Units are source sprite pixels or ratios."""
import copy,json,math
from pathlib import Path
DEFAULT={'version':1,'torso':{'height':1.,'shoulder':1.,'waist':1.,'hip':1.},'head':{'size':1.,'gap':0.}}
for key in ('armL','armR','legL','legR'):
    DEFAULT[key]={'upper':5.8,'lower':5.8,'thickness':1.,'spread':0.,'vertical':0.,'gap':0.,'connected':True}
SHAPES={'head':('ellipsoid','cylinder','rounded_box','box'),
        'torso':('tapered','barrel','box'),
        **{key:('capsule','cylinder','box') for key in ('armL','armR','legL','legR')}}
SHAPE_LABELS={'ellipsoid':'椭圆头','cylinder':'圆柱形','rounded_box':'圆角方形','box':'方形',
              'tapered':'收腰躯干','barrel':'筒形躯干','capsule':'胶囊形'}
for part,shapes in SHAPES.items():DEFAULT[part]['shape']=shapes[0]
DEFAULT['torso']['pelvis_depth']=2.5
DEFAULT['torso']['thickness']=1.15
DEFAULT['head']['depth']=0.
LIMITS={'height':(.65,1.35),'shoulder':(.65,1.6),'waist':(.4,1.5),'hip':(.65,1.5),'size':(.6,1.6),'gap':(-6,6),'upper':(2,12),'lower':(2,12),'thickness':(.5,1.6),'spread':(-6,6),'vertical':(-4,4),'pelvis_depth':(0,5),'depth':(-8,8)}
def normalize(value=None):
    result=copy.deepcopy(DEFAULT)
    if value is None:return result
    if not isinstance(value,dict):raise ValueError('Invalid model resource')
    # Resources made before torso thickness retain their original geometry/UVs.
    if 'torso' in value and isinstance(value['torso'],dict) and 'thickness' not in value['torso']:
        result['torso']['thickness']=1.
    for part in ('torso','head','armL','armR','legL','legR'):
        source=value.get(part,{})
        if not isinstance(source,dict):raise ValueError('Invalid model section: '+part)
        for key,default in result[part].items():
            if key not in source:continue
            v=source[key]
            if key=='shape':
                if v not in SHAPES[part]:raise ValueError('Invalid model shape: '+str(v))
                result[part][key]=v
            elif key=='connected':
                if not isinstance(v,bool):raise ValueError('Invalid connection mode')
                result[part][key]=v
            else:
                if not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v):raise ValueError('Invalid model number: '+key)
                lo,hi=(.5,2.) if part=='torso' and key=='thickness' else ((-6,6) if part=='head' and key=='gap' else LIMITS[key])
                result[part][key]=max(lo,min(hi,float(v)))
    return result

def save(model,path,assets=None):
    resource={'type':'FellowStudioModel','version':2,'model':normalize(model)}
    if assets is not None:
        import rounded_scene as S
        resource['assets3d']=S.assets({'model':resource['model'],'assets3d':assets})
    path=Path(path);tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(resource,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(path)
def load_resource(path):
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data,dict) or data.get('type')!='FellowStudioModel':raise ValueError('Please choose a model preset')
    result={'model':normalize(data.get('model'))}
    if 'assets3d' in data:
        import rounded_scene as S,uv_assets as U
        if not isinstance(data['assets3d'],dict):raise ValueError('Invalid model textures')
        result['assets3d']=S.assets({'model':result['model'],'assets3d':data['assets3d']})
        for part in U.PARTS:U.texture_image(result['assets3d'],part).load()
    return result

def load(path):return load_resource(path)['model']
