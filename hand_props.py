"""Closed, paintable hand props attached to a continuous anatomical wrist frame."""
import math,re
import attachment_binding as B
from functools import lru_cache
import numpy as np

LEGACY_PRESETS={'sword':dict(length=18.,width=6.,thickness=1.5,pitch=150.),
         'staff':dict(length=25.,width=5.,thickness=2.,pitch=0.),
         'shield':dict(length=13.,width=10.,thickness=2.,pitch=0.)}
PRESETS={'box':dict(length=8.,width=6.,thickness=4.,pitch=0.),
 'cylinder':dict(length=12.,width=4.,thickness=4.,pitch=0.),
 'sphere':dict(length=8.,width=8.,thickness=8.,pitch=0.),
 'cone':dict(length=10.,width=6.,thickness=6.,pitch=0.)}
LABELS={'box':'长方体','cylinder':'圆柱体','sphere':'球体','cone':'圆锥体'}
SPECS=(('length','道具长度（px）',4,32,.5),('width','道具宽度（px）',1,18,.25),
 ('pitch','握持俯仰（度）',-180,180,1),('thickness','道具厚度（px）',.5,8,.25),
 ('yaw','握持转向（度）',-180,180,1),('roll','握持侧倾（度）',-180,180,1),
 ('x','握点左右（px）',-24,24,.25),('y','握点上下（px）',-24,24,.25),('z','握点前后（px）',-24,24,.25))

def normalize(source):
 key=source.get('id','');preset=source.get('preset','box');parent=source.get('parent','armR')
 if not isinstance(key,str) or not re.fullmatch(r'prop[1-9][0-9]{0,5}',key):raise ValueError('Invalid hand prop ID')
 presets={**LEGACY_PRESETS,**PRESETS}
 B.validate(parent)
 if preset not in presets:raise ValueError('Invalid prop preset')
 item=dict(yaw=0.,roll=0.,x=0.,y=0.,z=0.,**presets[preset],id=key,parent=parent,kind='prop',preset=preset,shape=preset)
 if source.get('shape',preset)!=preset:raise ValueError('Invalid hand prop shape')
 for field,_,lo,hi,_ in SPECS:
  value=source.get(field,item[field])
  if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):raise ValueError('Invalid hand prop number: '+field)
  item[field]=max(lo,min(hi,float(value)))
 return item

def add(model,preset='box',parent='armR'):
 items=model.setdefault('attachments',[])
 if len(items)>=32:raise ValueError('Maximum 32 attachments')
 index=1
 while any(p['id']==f'prop{index}' for p in items):index+=1
 item=normalize(dict(id=f'prop{index}',preset=preset,parent=parent));items.append(item);return item['id']

def dimensions(item):return item['width'],item['length'],item['thickness']
def surface(item):return {key:item[key] for key in ('shape','length','width','thickness')}

def frame(item,model,pose):
 from core3d import rx,ry,rz
 origin,rotation=B.frame(item['parent'],model,pose)
 origin=origin+rotation@np.array((item['x'],item['y'],item['z']))
 return origin,rotation@ry(item['yaw'])@rx(item['pitch'])@rz(item['roll'])

def polygon(shape,w,h):
 if shape=='box':points=[(-.5,-.5),(.5,-.5),(.5,.5),(-.5,.5)]
 elif shape=='sword':
  points=[(-.13,-.14),(.13,-.14),(.13,.02),(.5,.02),(.5,.1),(.23,.1),(.23,.7),(0,.86),(-.23,.7),(-.23,.1),(-.5,.1),(-.5,.02),(-.13,.02)]
 elif shape=='staff':
  points=[(-.1,-.5),(.1,-.5),(.1,.27),(.5,.38),(0,.5),(-.5,.38),(-.1,.27)]
 else:points=[(0,-.5),(.42,-.25),(.5,.3),(.38,.5),(-.38,.5),(-.5,.3),(-.42,-.25)]
 return np.array([(x*w,y*h) for x,y in points])

def triangulate(points):
 """Ear clipping for the small simple, counterclockwise silhouette polygons."""
 def cross(a,b,c):return float((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
 remaining=list(range(len(points)));triangles=[]
 while len(remaining)>3:
  for at,b in enumerate(remaining):
   a,c=remaining[at-1],remaining[(at+1)%len(remaining)]
   if cross(points[a],points[b],points[c])<=1e-9:continue
   if any(all(cross(points[x],points[y],points[k])>=-1e-9 for x,y in ((a,b),(b,c),(c,a))) for k in remaining if k not in (a,b,c)):continue
   triangles.append((a,b,c));remaining.pop(at);break
  else:raise ValueError('Invalid prop polygon')
 triangles.append(tuple(remaining));return triangles

def mesh(item):return _mesh(tuple(item[key] for key in ('shape','length','width','thickness')))

@lru_cache(maxsize=128)
def _mesh(key):
 shape,h,w,d=key
 if shape in ('cylinder','sphere','cone'):
  from rounded_scene import surface_rings
  if shape=='cylinder':rings=[(-h/2,0.,0.),(-h/2,w/2,d/2),(h/2,w/2,d/2),(h/2,0.,0.)]
  elif shape=='cone':rings=[(-h/2,0.,0.),(-h/2,w/2,d/2),(h/2,0.,0.)]
  else:rings=[(float((t-.5)*h),float((math.sin(math.pi*t) if 0<t<1 else 0.)*w/2),float((math.sin(math.pi*t) if 0<t<1 else 0.)*d/2)) for t in np.linspace(0,1,13)]
  return surface_rings(rings,16),(np.array((-w/2,-h/2,-d/2)),np.array((w/2,h/2,d/2)))
 points=polygon(shape,w,h);result=[]
 for indices in triangulate(points):
  front=np.array([(points[k,0],points[k,1],d/2) for k in indices])
  back=front[::-1].copy();back[:,2]=-d/2
  result.extend((('front',front),('back',back)))
 for a,b in zip(points,np.roll(points,-1,axis=0)):
  normal=np.array((b[1]-a[1],a[0]-b[0]));axis=int(np.argmax(abs(normal)))
  face=(('right','left'),('top','bottom'))[axis][0 if normal[axis]>0 else 1]
  quad=np.array([(a[0],a[1],-d/2),(b[0],b[1],-d/2),(b[0],b[1],d/2),(a[0],a[1],d/2)])
  result.extend((face,quad[list(ids)]) for ids in ((0,1,2),(0,2,3)))
 bounds=(np.array((points[:,0].min(),points[:,1].min(),-d/2)),np.array((points[:,0].max(),points[:,1].max(),d/2)))
 return result,bounds
