"""Head-local attachment resources. Geometry and UV identity stay independent of pose."""
import math,re
from functools import lru_cache
import numpy as np
import sculpt

PRESETS={
 'human':dict(shape='round',x=1.,y=-.35,z=0.,width=4.,height=5.,thickness=2.5,tip=.65,outward=0.,lean=0.,twist=0.),
 'cat':dict(shape='pointed',x=.65,y=.64,z=0.,width=5.,height=5.5,thickness=2.6,tip=0.,outward=12.,lean=0.,twist=0.),
 'long':dict(shape='round',x=.55,y=.70,z=0.,width=3.6,height=9.,thickness=2.2,tip=.35,outward=12.,lean=0.,twist=0.)}
LABELS={'human':'人耳','cat':'猫耳','long':'长耳'}
SPECS=(('x','左右位置',-1.8,1.8,.025),('y','上下位置',-1.5,1.5,.025),('z','前后位置',-1.5,1.5,.025),
 ('width','耳根宽度（px）',.5,12,.25),('height','耳朵长度（px）',.5,16,.25),('thickness','耳朵厚度（px）',.5,8,.25),
 ('tip','耳尖宽度',0,1,.025),('outward','向外张开',-90,90,1),('lean','前后倾斜',-90,90,1),('twist','耳朵扭转',-90,90,1))

def normalize(records):
 if not isinstance(records,list) or len(records)>32:raise ValueError('Invalid attachments (maximum 32)')
 result=[];seen=set()
 for source in records:
  if not isinstance(source,dict):raise ValueError('Invalid attachment')
  key=source.get('id','');preset=source.get('preset','cat')
  if not re.fullmatch(r'ear[1-9][0-9]{0,5}[LR]',key) or key in seen:raise ValueError('Invalid or duplicate attachment ID')
  if preset not in PRESETS or source.get('parent','head')!='head':raise ValueError('Invalid attachment preset or parent')
  item=dict(PRESETS[preset],id=key,parent='head',kind='ear',preset=preset,linked=True)
  if source.get('shape',item['shape']) not in ('round','pointed'):raise ValueError('Invalid ear shape')
  item['shape']=source.get('shape',item['shape'])
  if not isinstance(source.get('linked',True),bool):raise ValueError('Invalid attachment link')
  item['linked']=source.get('linked',True)
  for field,_,lo,hi,_ in SPECS:
   value=source.get(field,item[field])
   if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):raise ValueError('Invalid attachment number: '+field)
   item[field]=max(lo,min(hi,float(value)))
  seen.add(key);result.append(item)
 return result

def add_pair(model,preset):
 items=model.setdefault('attachments',[]);index=1
 while any(p['id'].startswith(f'ear{index}') and p['id'][:-1]==f'ear{index}' for p in items):index+=1
 if len(items)>30:raise ValueError('Maximum 32 attachments')
 pair=normalize([dict(PRESETS[preset],id=f'ear{index}{side}',preset=preset) for side in ('L','R')]);items.extend(pair)
 return pair[0]['id']

def record(model,key):return next(p for p in model.get('attachments',[]) if p['id']==key)
def name(key,model):
 from i18n import tr
 item=record(model,key)
 return f"{tr(LABELS[item['preset']])} {key[3:-1]} · {tr('左侧' if key.endswith('L') else '右侧')}"

def dimensions(item):return item['width'],item['height'],item['thickness']
def surface(item):return {k:item[k] for k in ('shape','width','height','thickness','tip')}

def frame(item,model,head,pose=None):
 if model.get('structure')=='plush' and pose is not None:
  import plush
  return plush.attachment_frame(item,model,pose)
 # Anchor on the sculpted head, then keep the ear rigid in the head frame.
 from core3d import rx,ry,rz
 sign=-1 if item['id'].endswith('L') else 1
 half=np.array((8.,7.5,7.5))*model['head']['size']
 local=np.array([[sign*item['x'],item['y'],item['z']]])*half
 anchor=sculpt.deform(local,(-half,half),model['head'])[0]
 origin,rotation=head
 return origin+rotation@anchor,rotation@rz(-sign*item['outward'])@rx(item['lean'])@ry(sign*item['twist'])

def mesh(item):
 return _mesh(tuple(item[k] for k in ('shape','width','height','thickness','tip')))

def taper_depth(local,item):
 """Keep the root's depth, closing the front/back surfaces at the tip.

 Apply after computing UV coordinates so existing painted texels keep their
 positions on the six face charts.
 """
 shaped=local.copy()
 shaped[:,2]*=np.clip(1-shaped[:,1]/item['height'],0,1)
 return shaped

@lru_cache(maxsize=128)
def _mesh(key):
 """Closed six-face mesh: rounded ears or a tapered triangular prism."""
 shape,w,h,d,tip=key;bounds=(np.array((-w/2,0.,-d/2)),np.array((w/2,h,d/2)))
 faces={'front':(0,1,2,1),'back':(0,1,2,-1),'right':(2,1,0,1),'left':(2,1,0,-1),'top':(0,2,1,1),'bottom':(0,2,1,-1)}
 result=[];steps=4 if shape=='round' else 2
 for face,(a,b,c,sign) in faces.items():
  vertices=[]
  for j in range(steps+1):
   for i in range(steps+1):
    q=np.zeros(3);q[a]=i/steps*2-1;q[b]=j/steps*2-1;q[c]=sign
    if shape=='round':q/=np.linalg.norm(q)
    t=(q[1]+1)/2
    q[0]*=(1-t)+t*tip if shape=='pointed' else 1-t*(1-tip)*.4
    vertices.append(np.array((q[0]*w/2,(q[1]+1)*h/2,q[2]*d/2)))
  for j in range(steps):
   for i in range(steps):
    k=j*(steps+1)+i
    for ids in ((k,k+1,k+steps+2),(k,k+steps+2,k+steps+1)):
     triangle=np.array([vertices[n] for n in ids]);normal=np.cross(triangle[1]-triangle[0],triangle[2]-triangle[0])
     if normal[c]*sign<0:triangle=triangle[::-1]
     result.append((face,triangle))
 return result,bounds
