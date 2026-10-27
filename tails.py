"""Closed, curved tail attachments with deterministic clip-synchronous wagging."""
import math,re
import attachment_binding as B
from functools import lru_cache
import numpy as np

PRESETS={
 'long_tail':dict(shape='tube',length=17.,width=3.,thickness=3.,curl=75.,lean=-75.,wag=18.,cycles=1.,x=0.,y=2.,z=0.,outward=0.),
 'fluffy_tail':dict(shape='brush',length=16.,width=7.,thickness=6.,curl=40.,lean=-70.,wag=12.,cycles=1.,x=0.,y=2.,z=0.,outward=0.),
 'zigzag_tail':dict(shape='zigzag',length=24.,width=18.,thickness=1.5,curl=0.,lean=-12.,wag=0.,cycles=1.,x=8.,y=0.,z=-1.,outward=0.),
 'bob_tail':dict(shape='bob',length=5.,width=5.,thickness=5.,curl=0.,lean=-90.,wag=0.,cycles=1.,x=0.,y=2.,z=0.,outward=0.)}
LABELS={'long_tail':'长尾','fluffy_tail':'蓬松尾','bob_tail':'短圆尾','zigzag_tail':'折线尾'}
SPECS=(('length','尾巴长度（px）',3,26,.5),('width','尾巴粗细（px）',.5,24,.25),
 ('curl','尾巴弯曲（度）',-150,150,1),('tip','尾尖粗细',0,1,.05),('wag','摆尾幅度（度）',-60,60,1),
 ('thickness','尾巴厚度（px）',.5,12,.25),('lean','尾巴抬起（度）',-160,60,1),
 ('x','尾根左右（px）',-24,24,.25),('y','尾根上下（px）',-24,24,.25),('z','尾根前后（px）',-24,24,.25),
 ('outward','尾巴朝向（度）',-90,90,1),('cycles','每轮摆尾次数',1,4,1))

def normalize(source):
 key=source.get('id','');preset=source.get('preset','long_tail')
 if not isinstance(key,str) or not re.fullmatch(r'tail[1-9][0-9]{0,5}',key):raise ValueError('Invalid tail ID')
 parent=B.validate(source.get('parent','pelvis'))
 if preset not in PRESETS:raise ValueError('Invalid tail preset')
 item=dict(PRESETS[preset],tip=0.,id=key,parent=parent,kind='tail',preset=preset)
 if parent!='pelvis':item.update(x=0.,y=0.,z=0.)
 if source.get('shape',item['shape']) not in ('tube','brush','bob','zigzag'):raise ValueError('Invalid tail shape')
 item['shape']=source.get('shape',item['shape'])
 for field,_,lo,hi,_ in SPECS:
  value=source.get(field,item[field])
  if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):raise ValueError('Invalid tail number: '+field)
  item[field]=max(lo,min(hi,float(value)))
 item['cycles']=float(round(item['cycles']))
 return item

def add(model,preset='long_tail'):
 items=model.setdefault('attachments',[])
 if len(items)>=32:raise ValueError('Maximum 32 attachments')
 index=1
 while any(p['id']==f'tail{index}' for p in items):index+=1
 item=normalize(dict(id=f'tail{index}',preset=preset));item['wag']=0.;items.append(item);return item['id']

def dimensions(item):return item['width'],item['length'],item['thickness']
def surface(item):return {**{k:item[k] for k in ('shape','length','width','thickness','curl')},'tip':item.get('tip',0.)}

def frame(item,model,pose):
 import rounded_scene as S
 from core3d import rx,ry,rz
 phase=(pose.get('_motion_phase',0.)*item['cycles']%1.)*math.tau
 swing=item['outward']+(item['wag']*math.sin(phase) if 'tail' not in pose else 0.)
 if item['parent']!='pelvis':
  origin,rotation=B.frame(item['parent'],model,pose)
  return origin+rotation@np.array((item['x'],item['y'],item['z'])),rotation@ry(swing)@rx(item['lean'])
 if model.get('structure')=='plush':
  import plush as P
  b=model['body'];t=.22+item['y']/b['height'];depth=P.profile(b,float(np.clip(t,0,1)))[1]
  anchor=np.array((item['x'],b['height']*.22+item['y'],-depth+item['z']+.6))
  origin,matrix=P.local_frame(pose,anchor);u,_,vh=np.linalg.svd(matrix)
  return origin+matrix@anchor,u@vh@ry(swing)@rx(item['lean'])
 _,j,_,_,_,_=S.geometry(pose)
 rotation=S.root_rotation(pose)@ry(pose.get('pelvis_yaw',0))@rz(-pose.get('pelvis',0))
 anchor=np.array((item['x'],item['y'],-3.5*model['torso']['thickness']+item['z']+.6))
 return j['waist']['tip']+rotation@anchor,rotation@ry(swing)@rx(item['lean'])

def deform(local,item):
 """Bend after UV projection; moving/rotating the tail never repacks its atlas."""
 points=local.copy();length=item['length'];angle=math.radians(item['curl'])
 # Keep the bend radius wider than the cross section at extreme proportions.
 angle=float(np.clip(angle,-1.8*length/item['thickness'],1.8*length/item['thickness']))
 if abs(angle)<1e-8:return points
 a=angle*local[:,1]/length;radius=length/angle;z=local[:,2]
 points[:,1]=(radius-z)*np.sin(a)
 points[:,2]=radius*(1-np.cos(a))+z*np.cos(a)
 return points

def mesh(item):return _mesh((*tuple(item[k] for k in ('shape','length','width','thickness')),item.get('tip',0.)))

def bone_transforms(item,angles):
 """Three FK joints with pitch/yaw/roll, relative to the curved bind pose."""
 from core3d import rx,ry,rz
 values=np.asarray(angles,dtype=float).reshape(3,3)
 if not np.isfinite(values).all():raise ValueError('Invalid tail joint angles')
 values=np.clip(values,-150,150);length=item['length'];curl=math.radians(item['curl'])
 curl=float(np.clip(curl,-1.8*length/item['thickness'],1.8*length/item['thickness']))
 centers=deform(np.array([[0.,i*length/3,0.] for i in range(3)]),item)
 rest=[rx(math.degrees(curl*i/3)) for i in range(3)];origins=[];rotations=[];transforms=[]
 for i,(pitch,yaw,roll) in enumerate(values):
  delta=ry(yaw)@rx(pitch)@rz(roll)
  if i==0:origin=centers[0];rotation=rest[0]@delta
  else:
   origin=origins[i-1]+rotations[i-1]@rest[i-1].T@(centers[i]-centers[i-1])
   rotation=rotations[i-1]@rest[i-1].T@rest[i]@delta
  origins.append(origin);rotations.append(rotation)
  matrix=rotation@rest[i].T;transforms.append((origin-matrix@centers[i],matrix))
 return transforms,origins,rotations

def skin(raw,item,angles):
 """Shared surface vertices use the same continuous linear skin weights."""
 rest=deform(raw,item)
 if not np.any(angles):return rest
 transforms,_,_=bone_transforms(item,angles)
 position=np.clip(raw[:,1]/item['length']*3,0,2);lower=np.floor(position).astype(int);fraction=position-lower
 result=np.zeros_like(rest)
 for i,(offset,matrix) in enumerate(transforms):
  weights=np.where(lower==i,1-fraction,0)+np.where(np.minimum(lower+1,2)==i,fraction,0)
  result+=(rest@matrix.T+offset)*weights[:,None]
 return result

def joints(item,model,pose):
 origin,rotation=frame(item,model,pose);transforms,centers,_=bone_transforms(item,pose.get('tail',[0.]*9))
 end=deform(np.array([[0.,item['length'],0.]]),item)[0];offset,matrix=transforms[-1]
 return [origin+rotation@point for point in (*centers,offset+matrix@end)]

def physical(seq,config,seconds,periodic,spring,check):
 """Solve parent-driven inertia in world space, from root to tip.

 Uses the same fixed-rate spring solver as limbs; no viewport or wall clock state.
 Multiple tails share one animation channel, with the first tail as the reference rig.
 """
 model=seq[0].get('_model',{});items=[p for p in model.get('attachments',[]) if p.get('kind')=='tail']
 if not items:return
 item=items[0]
 for p in seq:
  if 'tail' not in p:
   # Preserve older whole-tail wag before enabling the new joint channel.
   from core3d import rx,ry
   swing=item['wag']*math.sin(math.tau*(p.get('_motion_phase',0)*item['cycles']%1))
   matrix=rx(-item['lean'])@ry(swing)@rx(item['lean'])
   p['tail']=[math.degrees(math.asin(float(np.clip(-matrix[1,2],-1,1)))),math.degrees(math.atan2(matrix[0,2],matrix[2,2])),math.degrees(math.atan2(matrix[1,0],matrix[1,1]))]+[0.]*6
  else:p['tail']=list(p['tail'])
 frames=[frame(item,model,p) for p in seq]
 for bone,name in enumerate(('root','middle','tip')):
  strength=float(np.clip(config.get(name,config.get('strength',0)),0,1))
  if strength<=0:continue
  check();roots=[];rotations=[]
  for p,(origin,rotation) in zip(seq,frames):
   _,centers,local=bone_transforms(item,p['tail']);roots.append(origin+rotation@centers[bone]);rotations.append(rotation@local[bone])
  roots=np.asarray(roots);rotations=np.asarray(rotations)
  # Project the world orientation into the three anatomical planes. Unwrapping
  # keeps a crossing of +/-180 degrees from becoming an artificial impulse.
  targets=(np.arctan2(rotations[:,2,1],rotations[:,1,1]),
           np.arctan2(rotations[:,0,2],rotations[:,2,2]),
           np.arctan2(-rotations[:,0,1],rotations[:,1,1]))
  planes=(roots[:,[2,1]],roots[:,[0,2]],roots[:,[0,1]]*[-1,1])
  for axis,(angles,plane) in enumerate(zip(targets,planes)):
   check();target=np.degrees(np.unwrap(angles));tracked=spring(target,plane,item['length']/3,seconds,strength,config.get('bounce',.4),periodic)
   for j,p in enumerate(seq):p['tail'][bone*3+axis]=float(np.clip(p['tail'][bone*3+axis]+(tracked[j]-target[j])*strength,-150,150))

def group_frame(item,pose,anchor,world_frame):
 transforms,_,_=bone_transforms(item,pose.get('tail',[0.]*9))
 anchor=np.asarray(anchor);angle=float(np.clip(math.radians(item['curl']),-1.8*item['length']/item['thickness'],1.8*item['length']/item['thickness']))
 if abs(angle)<1e-8:t=anchor[1]/item['length']
 else:
  radius=item['length']/angle;sign=1 if radius>0 else -1
  t=math.atan2(anchor[1]*sign,(radius-anchor[2])*sign)/angle
 position=float(np.clip(t*3,0,2));index=int(position);weight=position-index;other=min(index+1,2)
 matrix=(1-weight)*transforms[index][1]+weight*transforms[other][1]
 point=(1-weight)*(transforms[index][0]+transforms[index][1]@anchor)+weight*(transforms[other][0]+transforms[other][1]@anchor)
 u,_,vh=np.linalg.svd(matrix);matrix=u@vh;offset=point-matrix@anchor;origin,rotation=world_frame
 return origin+rotation@offset,rotation@matrix

@lru_cache(maxsize=128)
def _mesh(key):
 from rounded_scene import surface_rings
 shape,length,width,depth,tip=key
 if shape=='zigzag':return zigzag_mesh(length,width,depth)
 rings=[];samples=np.linspace(0,1,13)
 cap=1-min(.3,max(.025,min(width,depth)*tip/(2*length)))
 if tip>0 and shape!='bob':samples=np.unique(np.r_[samples,np.linspace(cap,1,5)])
 for t in samples:
  if shape=='bob':radius=math.sqrt(max(0.,1-(2*t-1)**2))
  elif shape=='brush':radius=math.sin(math.pi*t)**.65
  else:radius=min(1.,t/.06)*(1-t)**.45
  if tip>0 and shape!='bob':
   base=(math.sin(math.pi*min(t,cap))**.65 if shape=='brush' else min(1.,t/.06)*(1-min(t,cap))**.45)
   radius=(1-tip)*base+tip*min(1.,t/.06)
   if t>cap:radius*=math.sqrt(max(0.,1-((t-cap)/(1-cap))**2))
  if t==0 or t==1:radius=0.
  rings.append((float(t*length),float(radius*width/2),float(radius*depth/2)))
 return surface_rings(rings,12),(np.array((-width/2,0.,-depth/2)),np.array((width/2,length,depth/2)))


@lru_cache(maxsize=64)
def zigzag_mesh(length,width,depth):
 """A closed extruded polygon; shared points retain continuous FK weights."""
 from hand_props import triangulate
 points=np.array([(-.50,0),(-.28,.04),(-.38,.16),(-.10,.22),(-.25,.38),(0,.50),(-.13,.62),(.45,1.),(.50,.67),(.12,.45),(.26,.30),(-.02,.15),(.08,.06),(-.38,0.)],float)
 if np.sum(points[:,0]*np.roll(points[:,1],-1)-np.roll(points[:,0],-1)*points[:,1])<0:points=points[::-1]
 points*=np.array((width,length));result=[]
 for ids in triangulate(points):
  front=np.array([(points[k,0],points[k,1],depth/2) for k in ids]);back=front[::-1].copy();back[:,2]=-depth/2
  result.extend((('front',front),('back',back)))
 for a,b in zip(points,np.roll(points,-1,axis=0)):
  normal=np.array((b[1]-a[1],a[0]-b[0]));axis=int(np.argmax(abs(normal)));face=(('right','left'),('top','bottom'))[axis][0 if normal[axis]>0 else 1]
  quad=np.array([(a[0],a[1],-depth/2),(b[0],b[1],-depth/2),(b[0],b[1],depth/2),(a[0],a[1],depth/2)])
  result.extend((face,quad[list(ids)]) for ids in ((0,1,2),(0,2,3)))
 return result,(np.array((-width/2,0.,-depth/2)),np.array((width/2,length,depth/2)))
