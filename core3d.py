"""World-space FK/IK, UV meshes and orthographic depth rasterization. No per-view pose edits."""
import copy,json,math,time
from pathlib import Path
from functools import lru_cache
import numpy as np
from PIL import Image
import uv_assets as U
VIEWS=((0.,0.),(90.,0.),(45.,0.),(45.,30.))
def rx(a):
 a=math.radians(a);c,s=math.cos(a),math.sin(a);return np.array(((1,0,0),(0,c,-s),(0,s,c)),float)
def ry(a):
 a=math.radians(a);c,s=math.cos(a),math.sin(a);return np.array(((c,0,s),(0,1,0),(-s,0,c)),float)
def rz(a):
 a=math.radians(a);c,s=math.cos(a),math.sin(a);return np.array(((c,-s,0),(s,c,0),(0,0,1)),float)
def new_project():
 return dict(type='FellowStudio3D',version=1,name='Character',model=copy.deepcopy(U.MODEL),textures=U.create_textures(U.MODEL),motion='idle',fps=12,seconds=1.,params=dict(stride=1.,swing=1.,bounce=1.,speed=1.,raiseL=0.,raiseR=0.,mix=1.,lean=0.,nod=0.,softUpper=0.,softLower=0.),render=dict(colors=True,outline=True,gaps=True,onepx=True))
def validate(p):
 if p.get('type')!='FellowStudio3D' or p.get('version')!=1:raise ValueError('Choose a FellowStudio3D project')
 for k,(lo,hi) in U.LIMITS.items():
  v=p['model'][k]
  if not isinstance(v,(int,float)) or not math.isfinite(v) or not lo<=v<=hi:raise ValueError('Invalid body parameter: '+k)
 if p['motion'] not in ('idle','walk','run','squat','jump'):raise ValueError('Invalid motion')
 if not 1<=p['fps']<=60 or not .1<=p['seconds']<=10:raise ValueError('Invalid duration')
 for k in new_project()['params']:
  v=p['params'][k]
  if not isinstance(v,(int,float)) or not math.isfinite(v) or abs(v)>360:raise ValueError('Invalid motion parameter')
 for key,point in p.get('targets',{}).items():
  if key not in ('armL','armR','legL','legR') or len(point)!=3 or any(not isinstance(v,(int,float)) or not math.isfinite(v) or abs(v)>1000 for v in point):raise ValueError('Invalid IK target')
 for part in U.PARTS:
  net=p['textures'][part]['layout'];w,h=net['size']
  if not (2<=w<=2048 and 2<=h<=2048):raise ValueError('Invalid texture size')
  for face in U.FACES:
   x,y,rw,rh=net['rects'][face]
   if min(x,y)<0 or min(rw,rh)<=0 or x+rw>w or y+rh>h:raise ValueError('Invalid UV region')
  if p['textures'][part].get('png') and U.texture_image(p,part).size!=(w,h):raise ValueError('Texture size does not match UV layout')
 return p
def save(p,path):
 path=Path(path);temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(path)
def load(path):return validate(json.loads(Path(path).read_text(encoding='utf-8')))
def normalize(v):return v/max(np.linalg.norm(v),1e-9)
def bone_rotation(start,end,reference=np.array((1.,0.,0.))):
 up=-normalize(end-start);right=reference-up*np.dot(reference,up)
 if np.linalg.norm(right)<1e-5:right=np.cross((0.,0.,1.),up)
 right=normalize(right);return np.column_stack((right,up,normalize(np.cross(right,up))))
def ik(root,target,l1,l2,pole=np.array((0.,0.,1.))):
 delta=target-root;distance=np.linalg.norm(delta);direction=normalize(delta);d=np.clip(distance,abs(l1-l2)+1e-5,l1+l2-1e-5)
 along=(l1*l1-l2*l2+d*d)/(2*d);side=pole-direction*np.dot(pole,direction)
 if np.linalg.norm(side)<1e-6:side=np.cross(direction,(1.,0.,0.))
 mid=root+direction*along+normalize(side)*math.sqrt(max(0,l1*l1-along*along))
 return mid,root+direction*d

def skeleton(p,phase):
 m=p['model'];a=p['params'];mode=p['motion'];t=phase%1;wave=math.sin(math.tau*t)
 follow=follow_offsets(p,t) if (a['softUpper'] or a['softLower']) and not p.get('_noPhysics') else {}
 leg1,leg2=m['legUpper'],m['legLower'];height=leg1+leg2-.8
 dy=0.;lean=a['lean']
 if mode in ('walk','run'):
  run=mode=='run';height-=1.1 if run else .5;dy=(.7 if run else .25)*a['bounce']*math.cos(2*math.tau*t);lean+=12 if run else 0
 elif mode=='squat':dy=-min(leg1+leg2-3,5)*(1-math.cos(math.tau*t))/2
 elif mode=='jump':dy=5*max(0,math.sin(math.tau*t))**.7-2*max(0,-math.sin(math.tau*t))
 else:dy=.2*(1-math.cos(math.tau*t))
 hips=np.array((0.,height+dy,0.));spine=rx(-lean);chest=hips+spine@np.array((0.,14*m['height'],0.))
 head=chest+spine@np.array((0.,1+m['headGap']+7*m['head'],0.));j={'hips':hips,'chest':chest,'head':head};bodies={}
 # Torso deforms in world coordinates; upper vertices follow the spine, lower
 # vertices retain the hip position. Every camera sees these same vertices.
 bodies['torso']=(hips,spine)
 bodies['head']=(head,spine@rx(-a['nod']))
 for side,sign in (('L',-1),('R',1)):
  shoulder=chest+spine@np.array((sign*(6*m['shoulder']+m['armWidth']*.35+m['armGap']),-.7,0.))
  swing=(38 if mode=='run' else 27)*a['swing']*wave*sign if mode in ('walk','run') else 0
  raised=a['raise'+side]*a['mix']
  inertia,lag=follow.get(side,(0.,0.))
  armrot=spine@rz(sign*(10+raised))@rx(-swing+inertia)
  elbow=shoulder+armrot@np.array((0.,-m['armUpper'],0.))
  fore=armrot@rx(-(55 if mode=='run' else 12)+lag)
  hand=elbow+fore@np.array((0.,-m['armLower'],0.))
  if 'arm'+side in p.get('targets',{}):
   elbow,hand=ik(shoulder,np.array(p['targets']['arm'+side]),m['armUpper'],m['armLower'],spine@np.array((0.,0.,1.)))
   armrot=bone_rotation(shoulder,elbow);fore=bone_rotation(elbow,hand)
  j['arm'+side]=(shoulder,elbow,hand);bodies['upperArm'+side]=(shoulder,armrot);bodies['lowerArm'+side]=(elbow,fore)
  hip=hips+np.array((sign*3.2*m['hip'],0.,0.));target=np.array((hip[0],0.,0.))
  if mode in ('walk','run'):
   u=(t+(0 if side=='L' else .5))%1;stance=.38 if mode=='run' else .62;stride=(5.2 if mode=='run' else 3.8)*a['stride']
   if u<stance:target[2]=stride*(1-2*u/stance)
   else:
    v=(u-stance)/(1-stance);target[2]=-stride+2*stride*v;target[1]=(4 if mode=='run' else 2.3)*math.sin(math.pi*v)
  elif mode=='jump':target[1]=max(0,dy);target[2]=1.5*max(0,dy)/5
  if 'leg'+side in p.get('targets',{}):target=np.array(p['targets']['leg'+side])
  knee,foot=ik(hip,target,leg1,leg2);j['leg'+side]=(hip,knee,foot)
  for key,start,end in (('thigh'+side,hip,knee),('shin'+side,knee,foot)):
   bodies[key]=(start,bone_rotation(start,end))
 return j,bodies

def spring_track(target,roots,length,seconds,strength):
    """Damped angular spring driven by world-space acceleration of the parent.
    Integrate fixed steps and warm up complete cycles for deterministic seeking.
    """
    if strength<=0:return np.zeros(len(target))
    count=len(target);dt=seconds/count;frequency=17-10*strength;damping=frequency*(1.8-.8*strength)
    accel=(np.roll(roots,-1,axis=0)-2*roots+np.roll(roots,1,axis=0))/(dt*dt)
    angles=np.unwrap(np.radians(target));out=np.empty(count);x=float(angles[0]);v=0.
    for cycle in range(24):
        start=(x,v)
        for i in range(count):
            # Y is up, Z is forward. Root motion supplies the inertial torque.
            inertia=-(accel[i,2]*math.cos(x)+accel[i,1]*math.sin(x))/max(length,1)
            force=frequency**2*(angles[i]-x)-damping*v+inertia*strength
            v=float(np.clip(v+dt*force,-20,20));x+=dt*v
            x=float(np.clip(x,angles[i]-1.1,angles[i]+1.1));out[i]=x
        if cycle>4 and abs(x-start[0])+abs(v-start[1])<1e-5:break
    return -np.degrees(out-angles)

@lru_cache(maxsize=24)
def _follow_tracks(key):
    p=json.loads(key);p['_noPhysics']=True;n=120;a=p['params'];m=p['model'];period=p['seconds']/max(.25,a['speed'])
    samples=[skeleton(p,i/n) for i in range(n)];result={}
    for side in ('L','R'):
        roots=np.array([j['arm'+side][0] for j,b in samples]);vectors=np.array([j['arm'+side][1]-j['arm'+side][0] for j,b in samples]);targets=np.degrees(np.arctan2(vectors[:,2],-vectors[:,1]))
        upper=spring_track(targets,roots,m['armUpper'],period,a['softUpper'])
        elbows=[];lower_targets=[]
        for i,(j,b) in enumerate(samples):
            rot=b['upperArm'+side][1]@rx(upper[i]);elbows.append(roots[i]+rot@np.array((0.,-m['armUpper'],0.)))
            fore=rot@rx(-(55 if p['motion']=='run' else 12));v=fore@np.array((0.,-1.,0.));lower_targets.append(math.degrees(math.atan2(v[2],-v[1])))
        lower=spring_track(lower_targets,np.array(elbows),m['armLower'],period,a['softLower']);result[side]=np.column_stack((upper,lower))
    return result

def follow_offsets(p,phase):
    key=json.dumps({k:p[k] for k in ('model','params','motion','seconds')},sort_keys=True);tracks=_follow_tracks(key);x=phase*120;i=int(x)%120;f=x-int(x)
    return {side:values[i]*(1-f)+values[(i+1)%120]*f for side,values in tracks.items()}

# Each face uses a consistent, externally documented drawing orientation.
# The subdivision rounds edges while retaining a rectangular, easy-to-paint UV net.
@lru_cache(maxsize=128)
def mesh_template(dims):
 half=np.array(dims,float)/2;bevel=min(half)*.32
 faces={'front':((0,0,1),(1,0,0),(0,1,0)),'back':((0,0,-1),(-1,0,0),(0,1,0)),
 'right':((1,0,0),(0,0,-1),(0,1,0)),'left':((-1,0,0),(0,0,1),(0,1,0)),
 'top':((0,1,0),(1,0,0),(0,0,-1)),'bottom':((0,-1,0),(1,0,0),(0,0,1))}
 result=[]
 for face,(n,u,v) in faces.items():
  n,u,v=map(lambda x:np.array(x,float),(n,u,v));verts=[];uv=[]
  for b in (-1.,0.,1.):
   for a in (-1.,0.,1.):
    raw=(n+u*a+v*b)*half;inner=np.clip(raw,-half+bevel,half-bevel);delta=raw-inner
    verts.append(inner+normalize(delta)*bevel);uv.append(((a+1)/2,(1-b)/2))
  for y in range(2):
   for x in range(2):
    i=y*3+x
    for tri in ((i,i+1,i+4),(i,i+4,i+3)):result.append((face,np.array([verts[k] for k in tri]),np.array([uv[k] for k in tri])))
 return result

def meshes(p,phase):
 j,bodies=skeleton(p,phase);m=p['model'];dims=U.dimensions(m);result=[]
 for part in U.PARTS:
  origin,rot=bodies[part];d=dims[part];net=p['textures'][part]['layout']
  for face,local,uv in mesh_template(tuple(d)):
   v=local.copy()
   if part=='torso':
    fraction=(v[:,1]/d[1]+.5);factors=np.interp(fraction,[0,.5,1],[m['hip'],m['waist'],m['shoulder']])/max(m['shoulder'],m['waist'],m['hip']);v[:,0]*=factors
    # lower center at hips, upper center at chest; spine is a local rotation.
    v[:,1]+=d[1]/2
   elif part not in ('head',):v[:,1]-=d[1]/2
   world=v@rot.T+origin
   x,y,w,h=net['rects'][face];coords=np.column_stack((x+uv[:,0]*max(0,w-1),y+uv[:,1]*max(0,h-1)))
   result.append((part,face,world,coords))
 return j,result

def project(points,yaw,pitch=0):
 camera=rx(pitch)@ry(yaw);q=np.asarray(points)@camera.T
 # Larger depth means closer to the viewer (front camera is at positive Z).
 return np.column_stack((31.5+q[:,0],55.5-q[:,1],q[:,2]))
def unproject(point,yaw,pitch=0):
 x,y,z=point;return (rx(pitch)@ry(yaw)).T@np.array((x-31.5,55.5-y,z))

def raster_reference(triangles,textures,cam,settings,selected=None,connections=None,pixel_shift=None):
 n=64;depth=np.full((n,n),-np.inf);owner=np.full((n,n),-1,np.int16);rgb=np.zeros((n,n,4),np.uint8)
 part_depth=np.full((len(U.PARTS),n,n),-np.inf) if settings['outline'] or settings['gaps'] else None
 for part,face,world,uv in triangles:
  q=project(world,*cam)
  if pixel_shift is not None:q[:,:2]+=pixel_shift
  x0=max(0,int(np.floor(q[:,0].min())));x1=min(n-1,int(np.ceil(q[:,0].max())));y0=max(0,int(np.floor(q[:,1].min())));y1=min(n-1,int(np.ceil(q[:,1].max())))
  if x0>x1 or y0>y1:continue
  a,b,c=q;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
  if abs(den)<1e-8:continue
  yy,xx=np.mgrid[y0:y1+1,x0:x1+1];x=xx;y=yy
  w0=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den;w1=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den;w2=1-w0-w1
  z=w0*a[2]+w1*b[2]+w2*c[2];region=depth[y0:y1+1,x0:x1+1];hit=(w0>=-1e-7)&(w1>=-1e-7)&(w2>=-1e-7)
  if not hit.any():continue
  tex=textures[part];coord=w0[...,None]*uv[0]+w1[...,None]*uv[1]+w2[...,None]*uv[2];ix=np.clip(np.floor(coord[...,0]+.5).astype(int),0,tex.shape[1]-1);iy=np.clip(np.floor(coord[...,1]+.5).astype(int),0,tex.shape[0]-1);color=tex[iy,ix].copy()
  if not settings.get('material_colors',settings['colors']):color[...,:3]=255
  hit &= color[...,3]>=128
  if part_depth is not None:
   layer=part_depth[U.PARTS.index(part),y0:y1+1,x0:x1+1];layer[hit]=np.maximum(layer[hit],z[hit])
  hit &= z>region+1e-6
  if not hit.any():continue
  region[hit]=z[hit];rgb[y0:y1+1,x0:x1+1][hit]=color[hit];owner[y0:y1+1,x0:x1+1][hit]=U.PARTS.index(part)
 return finish_raster(rgb,owner,depth,cam,settings,selected,connections,pixel_shift,part_depth)

def surface_depth_scale(layers):
 """Convert camera-depth separation to approximate surface-normal distance.
 Use one-sided slopes at silhouettes, never differences against empty pixels.
 """
 finite=np.isfinite(layers);slope2=np.zeros_like(layers)
 for axis in (1,2):
  before=np.roll(layers,1,axis);after=np.roll(layers,-1,axis)
  left=finite&np.isfinite(before);right=finite&np.isfinite(after)
  start=[slice(None)]*3;start[axis]=0;left[tuple(start)]=False
  end=[slice(None)]*3;end[axis]=-1;right[tuple(end)]=False
  dl=np.zeros_like(layers);dr=np.zeros_like(layers)
  np.subtract(layers,before,out=dl,where=left);np.subtract(after,layers,out=dr,where=right)
  slope=np.where(left&right,(dl+dr)*.5,np.where(left,dl,dr))
  slope2+=slope*slope
 return np.sqrt(1+slope2)

def finish_raster(rgb,owner,depth,cam,settings,selected=None,connections=None,pixel_shift=None,part_depth=None):
 n=64;mask=owner>=0;edges=np.zeros((n,n),bool);seams=np.zeros_like(edges)
 offsets=((-1,0),(1,0),(0,-1),(0,1)) if settings['onepx'] else tuple((x,y) for x in (-1,0,1) for y in (-1,0,1) if (x,y)!=(0,0))
 for dx,dy in offsets:
  shifted=np.roll(owner,(dy,dx),(0,1));valid=np.ones_like(mask)
  if dx<0:valid[:,-1]=False
  if dx>0:valid[:,0]=False
  if dy<0:valid[-1,:]=False
  if dy>0:valid[0,:]=False
  edges|=(~mask)&(shifted>=0)&valid
 # One-sided lines at occluding silhouettes; solid intersections stay joined.
 if settings['gaps'] or settings['outline']:
  yy,xx=np.indices((n,n))
  normal_scale=surface_depth_scale(part_depth) if part_depth is not None else None
  for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
   shifted=np.roll(owner,(dy,dx),(0,1));other=np.roll(depth,(dy,dx),(0,1));boundary=mask&(shifted>=0)&(owner!=shifted)
   if part_depth is not None:
    # Keep the hidden front surface of each part. If A continues behind B at
    # the adjacent sample, the visible surfaces cross: this is a solid join,
    # not a silhouette to outline. At a real occlusion A ends in projection
    # and B continues beneath A. Compare depths at the SAME pixel so a steep
    # background surface cannot steal the line or reverse the visual order.
    neighbor_layers=np.roll(part_depth,(dy,dx),(1,2))
    a_next=neighbor_layers[np.maximum(owner,0),yy,xx]
    b_here=part_depth[np.maximum(shifted,0),yy,xx]
    # A tiny positive depth is not enough to warrant a line at 64x64.
    # Allow .75 native units of contact tolerance, measured approximately
    # along the hidden surface normal, so grazing angles do not amplify it.
    scale=normal_scale[np.maximum(shifted,0),yy,xx]
    valid=boundary&~np.isfinite(a_next)&np.where(np.isfinite(b_here),depth>b_here+.75*scale,depth>other+.75)
   else:
    valid=boundary&(depth>other+.05)
   if dx>0:valid[:,0]=False
   if dx<0:valid[:,-1]=False
   if dy>0:valid[0,:]=False
   if dy<0:valid[-1,:]=False
   # Exempt only the corresponding parent/child pair around its real joint.
   # The capsule radius exceeds the old fixed 2.2 px protection disk.
   for first,second,point,radius in (() if part_depth is not None else connections or ()):
    sx,sy,_=project(np.array([point]),*cam)[0]
    if pixel_shift is not None:sx+=pixel_shift[0];sy+=pixel_shift[1]
    yy,xx=np.ogrid[:64,:64]
    joint=(xx-sx)**2+(yy-sy)**2<=radius**2
    pair=((owner==first)&(shifted==second))|((owner==second)&(shifted==first))
    valid &= ~(pair&joint)
   seams|=valid
  # The real raster uses surface coverage, never joint disks or part priority.
  # Pair-specific disks remain only for older callers lacking surface layers.
 if settings['outline']:
  color=(72,72,72,255) if settings['colors'] else (128,128,128,255)
  custom=settings.get('outline_color','auto')
  if isinstance(custom,str) and len(custom)==7 and custom.startswith('#'):
   try:color=tuple(int(custom[i:i+2],16) for i in (1,3,5))+(255,)
   except ValueError:pass
  rgb[edges|seams]=color
 else:rgb[seams]=0
 return rgb,owner

def render(p,phase=0,cam=(0,0)):
 joints,triangles=meshes(p,phase);tex={part:np.array(U.texture_image(p,part)) for part in U.PARTS}
 sockets=[point for k,chain in joints.items() if k.startswith(('arm','leg')) for point in chain[:2]]
 return raster(triangles,tex,cam,p['render'],sockets)[0]

def compile_preview(p):
 count=max(1,min(120,round(p['seconds']*p['fps'])));textures={part:np.array(U.texture_image(p,part)) for part in U.PARTS};frames={};joints=[]
 for i in range(count):
  j,triangles=meshes(p,i/count);joints.append(j);sockets=[point for k,chain in j.items() if k.startswith(('arm','leg')) for point in chain[:2]]
  for v,cam in enumerate(VIEWS):frames[v,i]=raster(triangles,textures,cam,p['render'],sockets)[0]
 return frames,joints

def export(p,directory,name,formats,view=0,folder=True):
 import re
 if not name or name in ('.','..') or re.search(r'[<>:"/\\|?*\x00-\x1f]',name) or name.endswith(('.', ' ')):raise ValueError('Invalid export name')
 if name.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}:raise ValueError('Invalid export name')
 if not formats or set(formats)-{'png','strip','gif','project'}:raise ValueError('Choose an export format')
 dest=Path(directory)/name if folder else Path(directory);count=min(120,max(1,round(p['seconds']*p['fps'])))
 names=([f'{name}_{i:02d}.png' for i in range(count)] if 'png' in formats else [])+([f'{name}_strip.png'] if 'strip' in formats else [])+([f'{name}.gif'] if 'gif' in formats else [])+([f'{name}.json'] if 'project' in formats else [])
 if folder and dest.exists():raise FileExistsError('Output folder already exists')
 if any((dest/file).exists() for file in names):raise FileExistsError('Output files already exist')
 dest.mkdir(parents=True,exist_ok=not folder)
 images=[Image.fromarray(render(p,i/count,VIEWS[view])) for i in range(count)] if set(formats)-{'project'} else []
 if 'png' in formats:
  for i,im in enumerate(images):im.save(dest/f'{name}_{i:02d}.png')
 if 'strip' in formats:
  im=Image.new('RGBA',(64*count,64))
  for i,frame in enumerate(images):im.paste(frame,(64*i,0))
  im.save(dest/f'{name}_strip.png')
 if 'gif' in formats:
  # GIF has one transparent palette entry, PNG remains the pixel-exact source.
  frames=[]
  for im in images:
   bg=Image.new('RGB',im.size,(90,77,66));bg.paste(im,mask=im.getchannel('A'));frames.append(bg.resize((256,256),Image.Resampling.NEAREST))
  frames[0].save(dest/f'{name}.gif',save_all=True,append_images=frames[1:],loop=0,duration=max(10,round(1000/(p['fps']*max(.25,p['params']['speed'])))))
 if 'project' in formats:save(p,dest/f'{name}.json')
 return dest

def raster(triangles,textures,cam,settings,selected=None,connections=None,stable_head=None,pixel_shift=None,protection=None,protection_context=None):
 """Batch triangle coverage and depth reduction on the 64x64 pixel grid.
 Only rasterize each triangle's bounding box; no Python loop per triangle.
 """
 n=64;depth=np.full((n,n),-np.inf);owner=np.full((n,n),-1,np.int16);rgb=np.zeros((n,n,4),np.uint8)
 if not triangles:return finish_raster(rgb,owner,depth,cam,settings,selected,connections)
 world=np.stack([t[2] for t in triangles]);uv=np.stack([t[3] for t in triangles]);parts=np.array([U.PARTS.index(t[0]) for t in triangles])
 q=project(world.reshape(-1,3),*cam).reshape(-1,3,3)
 if pixel_shift is not None:q[:,:,:2]+=pixel_shift
 head_shift=np.zeros(2)
 if stable_head is not None:
  center=project(np.array([stable_head]),*cam)[0]
  if pixel_shift is not None:center[:2]+=pixel_shift
  shift=np.array((np.floor(center[0])+.5-center[0],np.floor(center[1]+.5)-center[1]))
  head_shift=shift
  q[parts==U.PARTS.index('head'),:,:2]+=shift
 from pixel_protection import prepare,apply as apply_protection
 frames={}
 for part,data in (protection_context or {}).items():
  def project_frame(frame):
   origin,rotation=frame;points=project(np.array([origin,*[origin+rotation[:,axis] for axis in range(3)]]),*cam)
   if pixel_shift is not None:points[:,:2]+=pixel_shift
   if part=='head':points[:,:2]+=head_shift
   return {'origin':points[0],'matrix':(points[1:]-points[0]).T}
  frames[part]={**data,**project_frame(data['frame'])}
  if 'group_frames' in data:frames[part]['reference_frames']=[project_frame(f) for f in data['group_frames']]
 textures,patches=prepare(triangles,q,textures,protection,settings.get('material_colors',settings['colors']),frames)
 low=np.maximum(0,np.floor(q[:,:,:2].min(axis=1)).astype(int));high=np.minimum(n-1,np.ceil(q[:,:,:2].max(axis=1)).astype(int));wh=np.maximum(0,high-low+1);areas=wh[:,0]*wh[:,1]
 a,b,c=q[:,0],q[:,1],q[:,2];den=(b[:,1]-c[:,1])*(a[:,0]-c[:,0])+(c[:,0]-b[:,0])*(a[:,1]-c[:,1]);areas[np.abs(den)<1e-8]=0
 ids=np.repeat(np.arange(len(q)),areas);count=len(ids)
 if not count:return finish_raster(rgb,owner,depth,cam,settings,selected,connections)
 local=np.arange(count)-np.repeat(np.cumsum(areas)-areas,areas);x=low[ids,0]+local%wh[ids,0];y=low[ids,1]+local//wh[ids,0]
 aa,bb,cc=a[ids],b[ids],c[ids];d=den[ids]
 w0=((bb[:,1]-cc[:,1])*(x-cc[:,0])+(cc[:,0]-bb[:,0])*(y-cc[:,1]))/d;w1=((cc[:,1]-aa[:,1])*(x-cc[:,0])+(aa[:,0]-cc[:,0])*(y-cc[:,1]))/d;w2=1-w0-w1
 inside=(w0>=-1e-7)&(w1>=-1e-7)&(w2>=-1e-7);ids=ids[inside];x=x[inside];y=y[inside];w0=w0[inside];w1=w1[inside];w2=w2[inside]
 if not len(ids):return finish_raster(rgb,owner,depth,cam,settings,selected,connections)
 z=w0*a[ids,2]+w1*b[ids,2]+w2*c[ids,2];coords=w0[:,None]*uv[ids,0]+w1[:,None]*uv[ids,1]+w2[:,None]*uv[ids,2];sample_parts=parts[ids];color=np.zeros((len(ids),4),np.uint8)
 for p,part in enumerate(U.PARTS):
  mask=sample_parts==p
  if not mask.any():continue
  tex=textures[part];co=coords[mask];ix=np.clip(np.floor(co[:,0]+.5).astype(int),0,tex.shape[1]-1);iy=np.clip(np.floor(co[:,1]+.5).astype(int),0,tex.shape[0]-1);color[mask]=tex[iy,ix]
 if not settings.get('material_colors',settings['colors']):color[:,:3]=255
 opaque=color[:,3]>=128;pixel=(y*n+x)[opaque];z=z[opaque];color=color[opaque];sample_parts=sample_parts[opaque]
 part_depth=None
 if settings['outline'] or settings['gaps']:
  part_depth=np.full((len(U.PARTS),n,n),-np.inf)
  np.maximum.at(part_depth.ravel(),sample_parts*n*n+pixel,z)
 np.maximum.at(depth.ravel(),pixel,z)
 # Resolve ties in source triangle order, matching the scalar depth renderer.
 near=z>=depth.ravel()[pixel]-1e-6;entry=np.arange(len(z));winner=np.full(n*n,len(z),int);np.minimum.at(winner,pixel[near],entry[near]);filled=winner<len(z)
 chosen=winner[filled];rgb.reshape(-1,4)[filled]=color[chosen];owner.ravel()[filled]=sample_parts[chosen]
 apply_protection(rgb,owner,patches,U.PARTS)
 return finish_raster(rgb,owner,depth,cam,settings,selected,connections,pixel_shift,part_depth)

