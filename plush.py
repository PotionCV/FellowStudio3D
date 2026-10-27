"""Continuous bag-shaped bodies using the existing limb and motion vocabulary."""
import math
from functools import lru_cache
import numpy as np

DEFAULT=dict(height=38.,upper_width=25.,belly_width=28.,bottom_width=21.,depth=19.,head_link=True,flex=.65)
SPECS=(('height','整体高度（px）',24,46,.5),('upper_width','上部宽度（px）',12,38,.5),
 ('belly_width','肚子宽度（px）',12,40,.5),('bottom_width','底部宽度（px）',8,36,.5),('depth','主体厚度（px）',8,32,.5))

def active(model):return model.get('structure')=='plush'

def normalize(source):
 if not isinstance(source,dict):raise ValueError('Invalid plush body')
 result=dict(DEFAULT)
 for key,_,lo,hi,_ in (*SPECS,('flex','',0,1,.05)):
  v=source.get(key,result[key])
  if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):raise ValueError('Invalid plush parameter: '+key)
  result[key]=float(np.clip(v,lo,hi))
 if not isinstance(source.get('head_link',True),bool):raise ValueError('Invalid head/body link')
 result['head_link']=source.get('head_link',True)
 profile_name=source.get('profile','bag')
 if profile_name not in ('bag','rounded'):raise ValueError('Invalid plush profile')
 if profile_name!='bag':result['profile']=profile_name
 return result

def profile(body,t):
 """Closed rounded ends with no neck indentation. Fractions run bottom to top."""
 xs=(0,.04,.13,.38,.62,.82,.94,.985,1)
 widths=(0,body['bottom_width']*.36,body['bottom_width']*.5,body['belly_width']*.5,
         (body['belly_width']+body['upper_width'])*.25,body['upper_width']*.5,body['upper_width']*.44,body['upper_width']*.25,0)
 depths=(0,.65,.92,1,1,.98,.86,.48,0)
 if body.get('profile')=='rounded':
  xs=(0,.04,.13,.34,.53,.65,.80,.92,.98,1.)
  widths=(0,body['bottom_width']*.36,body['bottom_width']*.5,body['belly_width']*.5,body['belly_width']*.47,body['upper_width']*.43,body['upper_width']*.5,body['upper_width']*.43,body['upper_width']*.24,0)
  depths=(0,.50,.77,1.,.88,.79,1.,.89,.50,0)
 return np.interp(t,xs,widths),body['depth']/2*np.interp(t,xs,depths)

def rig(model,g):
 """Place sockets on the continuous body and keep short legs on the base floor."""
 body=model['body'];result=dict(g);legreach=max(sum(v['lengths'])+v['gap']+v['radii'][1] for k,v in g['limbs'].items() if k.startswith('leg'))
 hip_y=55.5-legreach;bottom_y=hip_y+2.;shoulder_y=bottom_y-body['height']*.58
 result['sho']={};result['hip']={}
 for side,sign in (('L',-1),('R',1)):
  arm=model['arm'+side];leg=model['leg'+side]
  result['sho'][side]=(31.5+sign*(profile(body,.58)[0]+arm['spread']),shoulder_y+arm['vertical'])
  result['hip'][side]=(31.5+sign*(body['bottom_width']*.26+leg['spread']),hip_y+leg['vertical'])
 result.update(torso_c=(31.5,bottom_y-body['height']*.45),head_c=(31.5,bottom_y-body['height']*.78),neck_y=bottom_y-body['height']*.60,body_bottom=bottom_y,body_params=body)
 return result

def dimensions(model):
 b=model['body'];return max(b[k] for k in ('upper_width','belly_width','bottom_width')),b['height'],b['depth']

def bottom(g):return np.array((0.,55.5-g['body_bottom'],0.))

def mesh(model):return _mesh(tuple(model['body'][k] for k in ('height','upper_width','belly_width','bottom_width','depth'))+(model['body'].get('profile','bag'),))

@lru_cache(maxsize=128)
def _mesh(key):
 from rounded_scene import surface_rings
 height,upper,belly,base,depth,profile_name=key;body=dict(height=height,upper_width=upper,belly_width=belly,bottom_width=base,depth=depth,profile=profile_name)
 rings=[]
 # Extra intermediate rings distribute bending rather than creating a hinge.
 extra=[.04,.13,.38,.62,.82,.94,.985]+([.34,.53,.65,.80,.92,.98] if profile_name=='rounded' else [])
 for t in sorted(set(np.linspace(0,1,21).tolist()+extra)):
  w,d=profile(body,t);rings.append((t*height,w,d))
 triangles=[]
 for _,points in surface_rings(rings,16):
  # A bag has a broad face, including its cheeks. Keep the front/back charts
  # over 135 degrees instead of switching charts at the first 45-degree normal.
  center=points.mean(axis=0);rw,rd=profile(body,center[1]/height)
  angle=math.atan2(center[2]/max(rd,1e-9),center[0]/max(rw,1e-9))
  sine=math.sin(angle)
  face=('front' if sine>math.sin(math.pi/8) else 'back' if sine<-math.sin(math.pi/8) else 'right' if center[0]>=0 else 'left')
  if center[1]/height>=.985:face='top'
  elif center[1]/height<=.02:face='bottom'
  triangles.append((face,points))
 width=max(upper,belly,base)
 return triangles,(np.array((-width/2,0.,-depth/2)),np.array((width/2,height,depth/2)))

def smooth(t,lo,hi):
 v=np.clip((t-lo)/(hi-lo),0,1);return v*v*(3-2*v)

def deform(local,pose,g=None,geometry=None):
 from rounded_scene import geometry as geo,world,root_rotation,root_offset,rx,ry
 if geometry is None:geometry=geo(pose)
 if g is None:g=geometry[0]
 body=g['body_params'];points=np.asarray(local)+bottom(g)
 pivot=world(np.mean(list(g['hip'].values()),axis=0));offset=root_offset(pose);root=root_rotation(pose)
 chest=root@rx(pose.get('lean',0))@ry(pose.get('chest_yaw',0));pelvis=root@ry(pose.get('pelvis_yaw',0))
 lower=(points-pivot)@pelvis.T+pivot+offset;middle=(points-pivot)@chest.T+pivot+offset
 t=np.asarray(local)[:,1]/body['height'];weight=smooth(t,.08,.58)[:,None]
 shaped=lower*(1-weight)+middle*weight
 if not body['head_link']:
  origin,rot=geometry[-1];rest=world(g['head_c']);upper=(points-rest)@rot.T+origin
  weight=smooth(t,.50,.80)[:,None]*body['flex'];shaped=shaped*(1-weight)+upper*weight
 return shaped

def local_frame(pose,anchor):
 """Affine surface frame at a protected motif or accessory root."""
 anchor=np.asarray(anchor,float);points=np.array([anchor,*[anchor+np.eye(3)[i]*.01 for i in range(3)]])
 world=deform(points,pose);matrix=(world[1:]-world[0]).T/.01
 return world[0]-matrix@anchor,matrix

def attachment_frame(item,model,pose):
 from rounded_scene import rx,ry,rz
 b=model['body'];sign=-1 if item['id'].endswith('L') else 1
 anchor=np.array((sign*item['x']*b['upper_width']/2,b['height']*(.78+item['y']*.2),item['z']*b['depth']/2))
 origin,matrix=local_frame(pose,anchor)
 # Keep attachments rigid even when the parent body stretches during bending.
 u,_,vh=np.linalg.svd(matrix);rotation=u@vh
 return origin+matrix@anchor,rotation@rz(-sign*item['outward'])@rx(item['lean'])@ry(sign*item['twist'])
