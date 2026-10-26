"""Round, UV-mapped 3D bodies driven by the existing FellowStudio pose vocabulary."""
import copy,json,math
from functools import lru_cache
import numpy as np
from PIL import Image
import fellow as F,model_data as MD,uv_assets as U
import sculpt
import attachments as A
import plush as P
from core3d import rx,ry,rz,project,raster
PARTS=U.PARTS
U.COLORS['head']=(170,146,206)
ORIGIN=np.array((31.5,55.5))
def world(point):return np.array((point[0]-31.5,55.5-point[1],0.),float)
def root_rotation(pose):
 axis=pose.get('body_axis',0)
 return rz(-pose.get('rot',0))@ry(axis)@rx(pose.get('body_pitch',0))@ry(-axis)
def root_offset(pose):
 pivot=np.array((0.,pose.get('body_pivot',0.),0.))
 return np.array((pose.get('dx',0),-pose.get('dy',0),pose.get('dz',0)))+pivot-root_rotation(pose)@pivot
def direction(lat,sag):
 a,b=map(math.radians,(lat,sag));return np.array((math.sin(a)*math.cos(b),-math.cos(a)*math.cos(b),math.sin(b)))
def rotation_for(vector):
 up=-vector/max(np.linalg.norm(vector),1e-9);ref=np.array((1.,0.,0.));right=ref-up*np.dot(ref,up)
 if np.linalg.norm(right)<1e-5:right=np.cross((0.,0.,1.),up)
 right/=max(np.linalg.norm(right),1e-9);return np.column_stack((right,up,np.cross(right,up)))

def geometry(pose):
 key=json.dumps({k:v for k,v in pose.items() if k not in ('tail','_face_phase','_assets3d','_camera_y','_foot_targets','_breath_ik','_breath_dy','_thrust_strength','yaw','pitch','flip')},sort_keys=True,default=lambda v:v.tolist())
 return _geometry(key)

def limb_chain(pose,limb):
 # IK/physics query one chain hundreds of times. Other limbs, head rotation,
 # texture assets and the preview camera cannot affect this chain.
 keys=(limb,'_model','rot','body_pitch','body_axis','body_pivot','lean','dx','dy','dz','chest_yaw','pelvis_yaw','shoulder','pelvis','arm_scale','leg_scale','off_'+limb)
 key=json.dumps({k:pose[k] for k in keys if k in pose},sort_keys=True,default=lambda v:v.tolist())
 return _geometry(key,limb)

@lru_cache(maxsize=2048)
def _geometry(key,only=None):
 pose=json.loads(key);model=MD.normalize(pose.get('_model'))
 g=dict(F.model_geometry(pose))
 # The legacy sprite's hip pair is centered at 31.75, while the body/grid is
 # centered at 31.5. Remove only that inherited bias; retain user asymmetry.
 hip_bias=((F.HIP['L'][0]+F.HIP['R'][0])/2-F.BODY_X)*model['torso']['hip']
 if P.active(model):hip_bias=0
 g['hip']={side:(point[0]-hip_bias,point[1]) for side,point in g['hip'].items()}
 hips=g['hip'];pivot=world(tuple((hips['L'][i]+hips['R'][i])/2 for i in (0,1)))
 roll=root_rotation(pose);spine=rx(pose.get('lean',0));offset=root_offset(pose)
 chest=roll@spine@ry(pose.get('chest_yaw',0));pelvis=roll@ry(pose.get('pelvis_yaw',0))
 def upper(point):return chest@(world(point)-pivot)+pivot+offset
 sho_center=np.mean([world(g['sho'][s]) for s in ('L','R')],axis=0)
 hip_center=np.mean([world(g['hip'][s]) for s in ('L','R')],axis=0)
 chains={};parts={};j={}
 for side in ('L','R'):
  for kind in ('arm','leg'):
   if only is not None and kind+side!=only:continue
   key=kind+side;spec=tuple(pose.get(key,(0,0)))+(0,)*4;lat,bend,sag,sbend=spec[:4];limb=g['limbs'][key]
   anchor=world(g['sho' if kind=='arm' else 'hip'][side]);center=sho_center if kind=='arm' else hip_center
   anchor=rz(-pose.get('shoulder' if kind=='arm' else 'pelvis',0))@(anchor-center)+center
   off=F.sock(pose,'off_'+kind,side);anchor+=np.array((off[0],-off[1],0))
   transform=chest if kind=='arm' else pelvis;root=(transform@(anchor-pivot)+pivot+offset)
   scales=tuple(pose.get(kind+'_scale',(1,1)));lengths=tuple(limb['lengths'][i]*scales[i] for i in (0,1))
   v1=transform@direction(lat,sag);v2=transform@direction(lat+bend,sag+sbend);start=root+v1*limb['gap'];mid=start+v1*lengths[0];tip=mid+v2*lengths[1]
   chains[key]=(root,start,mid,tip);j[key]={'root':root,'mid':mid,'tip':tip}
   if only is not None:return chains[key]
   r0,r1=limb['radii'];rm=(r0+r1)/2
   first=('upperArm' if kind=='arm' else 'thigh')+side;second=('lowerArm' if kind=='arm' else 'shin')+side
   parts[first]=(start,transform@rotation_for(direction(lat,sag)),lengths[0],r0,rm);parts[second]=(mid,transform@rotation_for(direction(lat+bend,sag+sbend)),lengths[1],rm,r1)
 neck=upper((F.BODY_X,g['neck_y']))
 head_parent=chest if pose.get('head_follow_chest',True) else roll@spine
 linked=P.active(model) and model['body']['head_link']
 headrot=chest if linked else head_parent@ry(pose.get('head_yaw',0))@rx(pose.get('head_pitch',0))@rz(-pose.get('head',0))
 headcenter=neck+headrot@(world(g['head_c'])-world((F.BODY_X,g['neck_y'])))
 off=F.sock(pose,'off_head','');headcenter+=np.array((off[0],-off[1],0))
 headcenter+=chest@np.array((0.,0.,MD.normalize(pose.get('_model'))['head']['depth']+pose.get('head_depth',0)))
 for key,pos in (('waist',pivot+offset),('torso',upper(g['torso_c'])),('neck',neck),('head',headcenter)):j[key]={name:pos for name in ('root','mid','tip')}
 return g,j,chains,parts,(upper(g['torso_c']),chest),(headcenter,headrot)

def uv_tri(face,local,bounds,net):
 # Face bases match exported box-net orientation, while the surface is rounded.
 lo,hi=bounds;normalized=(local-lo)/np.maximum(hi-lo,1e-6)
 x,y,z=normalized.T
 a,b={'front':(x,1-y),'back':(1-x,1-y),'left':(z,1-y),'right':(1-z,1-y),'top':(x,z),'bottom':(x,1-z)}[face]
 ox,oy,w,h=net['rects'][face];return np.column_stack((ox+a*(w-1),oy+b*(h-1)))
def face_of(normal):
 # Equal-angle facets must choose the same chart on mirrored meshes. Tiny
 # trigonometric errors otherwise swap front/side charts on a cylinder.
 magnitude=np.abs(normal)/max(1e-12,np.max(np.abs(normal)))
 axis=int(np.argmax(np.round(magnitude,8)));return (('right','left'),('top','bottom'),('front','back'))[axis][0 if normal[axis]>=0 else 1]

def surface_rings(rings,segments=12,square=False):
 verts=[]
 for y,rx_,rz_ in rings:
  if square:
   verts.extend((rx_*x,y,rz_*z) for x,z in ((1,1),(-1,1),(-1,-1),(1,-1)))
  else:verts.extend((rx_*math.cos(math.tau*i/segments),y,rz_*math.sin(math.tau*i/segments)) for i in range(segments))
 verts=np.array(verts);triangles=[]
 for row in range(len(rings)-1):
  for i in range(segments):
   a=row*segments+i;b=row*segments+(i+1)%segments;c=b+segments;d=a+segments
   for ids in ((a,b,c),(a,c,d)):
    tri=verts[list(ids)];normal=np.cross(tri[1]-tri[0],tri[2]-tri[0]);radial=np.mean(tri,axis=0);radial[1]=0
    if np.dot(normal,radial)<0:tri=tri[[0,2,1]];normal=-normal
    if np.linalg.norm(normal)>1e-7:triangles.append((face_of(normal),tri))
 return triangles
@lru_cache(maxsize=256)
def capsule(length,r0,r1):
 # Hemispherical caps merge into the adjoining segment at the shared joint.
 rings=[]
 for theta in (0,math.pi/4,math.pi/2):rings.append((r0*math.cos(theta),r0*math.sin(theta),r0*math.sin(theta)))
 for theta in (math.pi/2,3*math.pi/4,math.pi):rings.append((-length+r1*math.cos(theta),r1*math.sin(theta),r1*math.sin(theta)))
 return surface_rings(rings,8), (np.array((-max(r0,r1),-length-r1,-max(r0,r1))),np.array((max(r0,r1),r0,max(r0,r1))))
@lru_cache(maxsize=256)
def limb_mesh(length,r0,r1,shape='capsule'):
 if shape=='capsule':return capsule(length,r0,r1)
 # Flat end caps overlap the joint center to keep bent segments connected.
 top=r0*.5;bottom=-length-r1*.5
 rings=((top,0,0),(top,r0,r0),(bottom,r1,r1),(bottom,0,0))
 return surface_rings(rings,4 if shape=='box' else 12,shape=='box'),(np.array((-max(r0,r1),bottom,-max(r0,r1))),np.array((max(r0,r1),top,max(r0,r1))))
@lru_cache(maxsize=64)
def head_mesh(size,shape='ellipsoid'):
 # Ellipsoid mapped from six cube faces: round outline, clear six-face UV net.
 half=np.array((8.,7.5,7.5))*size
 faces={'front':((0,0,1),(1,0,0),(0,1,0)),'back':((0,0,-1),(-1,0,0),(0,1,0)),'right':((1,0,0),(0,0,-1),(0,1,0)),'left':((-1,0,0),(0,0,1),(0,1,0)),'top':((0,1,0),(1,0,0),(0,0,-1)),'bottom':((0,-1,0),(1,0,0),(0,0,1))}
 triangles=[]
 for face,(n,u,v) in faces.items():
  n,u,v=map(np.array,(n,u,v));vertices=[];coords=[]
  for b in np.linspace(-1,1,7):
   for a in np.linspace(-1,1,7):
    q=(n+u*a+v*b).astype(float)
    if shape=='ellipsoid':q/=np.linalg.norm(q)
    elif shape=='rounded_box':q/=np.linalg.norm(q,ord=5)
    elif shape in ('cylinder','cone'):
     radius=max(1.,math.hypot(q[0],q[2]));q[[0,2]]/=radius
    if shape in ('cone','pyramid'):q[[0,2]]*=(1-q[1])/2
    vertices.append(q*half);coords.append(((a+1)/2,(1-b)/2))
  for y in range(6):
   for x in range(6):
    i=y*7+x
    for ids in ((i,i+1,i+8),(i,i+8,i+7)):triangles.append((face,np.array([vertices[k] for k in ids]),np.array([coords[k] for k in ids])))
 return triangles

def part_dimensions(model):
 pose={'_model':MD.normalize(model)};g=F.model_geometry(pose);dims={'head':tuple(np.array((16,15,15))*pose['_model']['head']['size']),'torso':(g['torso_mask'].shape[1],g['torso_mask'].shape[0]+pose['_model']['torso']['pelvis_depth'],7*pose['_model']['torso']['thickness'])}
 for side in ('L','R'):
  for kind in ('arm','leg'):
   limb=g['limbs'][kind+side];r0,r1=limb['radii'];rm=(r0+r1)/2
   for name,length,a,b in ((('upperArm' if kind=='arm' else 'thigh')+side,limb['lengths'][0],r0,rm),(('lowerArm' if kind=='arm' else 'shin')+side,limb['lengths'][1],rm,r1)):
    dims[name]=(max(a,b)*2,length+a+b,max(a,b)*2)
 dims={part:sculpt.dimensions(dim,pose['_model']['head' if part=='head' else 'torso' if part=='torso' else ('arm' if 'Arm' in part else 'leg')+part[-1]]) for part,dim in dims.items()}
 if P.active(pose['_model']):
  dims.pop('head');dims.pop('torso');dims['body']=P.dimensions(pose['_model'])
 dims.update({item['id']:A.dimensions(item) for item in pose['_model'].get('attachments',[])})
 return dims

def torso_rotation(pose,fraction):
 yaw=pose.get('pelvis_yaw',0)*(1-fraction)+pose.get('chest_yaw',0)*fraction
 return root_rotation(pose)@rx(pose.get('lean',0))@ry(yaw)

def torso_surface(local,g,pose):
 """Blend the chest turn into the pelvis instead of rotating a rigid torso."""
 center=world(g['torso_c']);pivot=world(np.mean(list(g['hip'].values()),axis=0));offset=root_offset(pose)
 height=g['torso_mask'].shape[0];fraction=np.clip((local[:,1]+height/2)/height,0,1)
 yaw=np.radians(pose.get('pelvis_yaw',0)*(1-fraction)+pose.get('chest_yaw',0)*fraction)
 rel=local+center-pivot;rotated=rel.copy()
 rotated[:,0]=rel[:,0]*np.cos(yaw)+rel[:,2]*np.sin(yaw);rotated[:,2]=-rel[:,0]*np.sin(yaw)+rel[:,2]*np.cos(yaw)
 return rotated@(root_rotation(pose)@rx(pose.get('lean',0))).T+pivot+offset
@lru_cache(maxsize=32)
def _assets(model_key,bundle_key):
 model=json.loads(model_key);bundle=json.loads(bundle_key);new={p:{'layout':U.layout(d),'png':None,'name':'Default'} for p,d in part_dimensions(model).items()}
 old=bundle.get('textures',{})
 for part in new:
  if part not in old:continue
  resource=old[part]
  if resource.get('painting_pending'):new[part]['painting_pending']=True
  if resource['layout']==new[part]['layout']:
   new[part]=resource
   if resource.get('png') and U.surface_record({'model':bundle.get('model',model),'textures':old},part)!=U.surface_record({'model':model,'textures':new},part):new[part]['provenance']='adapted'
   continue
  from pixel_protection import resize_groups
  new[part]['protected_groups']=resize_groups(resource,new[part]['layout'])
  if not resource.get('png'):continue
  source=U.decode(resource['png']);target=Image.new('RGBA',new[part]['layout']['size'])
  for face,(x,y,w,h) in new[part]['layout']['rects'].items():
   ox,oy,ow,oh=resource['layout']['rects'][face];target.paste(source.crop((ox,oy,ox+ow,oy+oh)).resize((w,h),Image.Resampling.NEAREST),(x,y))
  new[part].update(png=U.encode(target),name=resource.get('name','Painted'),provenance='adapted')
 result={'model':model,'textures':new}
 if bundle.get('shared_textures'):result['shared_textures']=bundle['shared_textures']
 elif not old:result['shared_textures']={p:p[:-1]+'L' for p in U.parts(result) if p.endswith('R') and p[:-1]+'L' in new}
 for p in U.parts(result):
  if p not in old and p.endswith('R') and p[:-1]+'L' in new:result.setdefault('shared_textures',{})[p]=p[:-1]+'L'
 return U.apply_shared(result)
def assets(project):return copy.deepcopy(_assets(json.dumps(MD.normalize(project.get('model')),sort_keys=True),json.dumps(project.get('assets3d',{}),sort_keys=True)))
def pose_meshes(pose):
 bundle=pose.get('_assets3d') or assets({'model':pose.get('_model')})
 key=json.dumps({k:v for k,v in pose.items() if k not in ('_face_phase','_assets3d','_camera_y','_foot_targets','_breath_ik','_breath_dy','_thrust_strength','yaw','pitch','flip')},sort_keys=True,default=lambda v:v.tolist())
 layouts=json.dumps({p:r['layout'] for p,r in bundle['textures'].items()},sort_keys=True)
 j,triangles=_mesh_cache(key,layouts)
 return j,triangles,bundle

@lru_cache(maxsize=64)
def _ground_clouds(model_key):
 """Keep only unique local vertices: contact queries need no UVs or triangles."""
 model=json.loads(model_key);pose={'_model':model}
 g,j,chains,limbs,torso,head=geometry(pose);triangles=pose_meshes(pose)[1]
 frames={part:(values[0],values[1]) for part,values in limbs.items()};frames['head']=head;frames.update({item['id']:A.frame(item,model,head,pose) for item in model.get('attachments',[])})
 result={}
 if P.active(model):frames['body']=(P.bottom(g),np.eye(3))
 for part,(origin,rot) in frames.items():
  if not any(p==part for p,f,v,uv in triangles):continue
  cloud=np.concatenate([v for p,f,v,uv in triangles if p==part])
  result[part]=np.unique(np.round((cloud-origin)@rot,10),axis=0)
 if P.active(model):return result
 body=[v for p,f,v,uv in triangles if p=='torso']
 # The closed pelvis is appended after the continuous torso in _mesh_cache.
 pelvis_count=(4 if model['torso']['shape']=='box' else 12)*6 if model['torso']['pelvis_depth']>0 else 0
 upper=body[:-pelvis_count] if pelvis_count else body
 result['torso']=np.unique(np.round(np.concatenate(upper)-world(g['torso_c']),10),axis=0)
 if pelvis_count:
  center=np.mean([chains['leg'+s][0] for s in ('L','R')],axis=0)
  result['pelvis']=np.unique(np.round(np.concatenate(body[-pelvis_count:])-center,10),axis=0)
 return result

def ground_y(pose,parts=None):
 model=MD.normalize(pose.get('_model'));clouds=_ground_clouds(json.dumps(model,sort_keys=True))
 g,j,chains,limbs,torso,head=geometry(pose);bottom=float('inf')
 for part,cloud in clouds.items():
  if parts is None and part.startswith(('tail','prop')):continue
  if parts is not None and part not in parts:continue
  if part.startswith('tail') and 'tail' in pose:
   item=A.record(model,part);net=U.layout(A.dimensions(item));triangles=attachment_triangles(item,model,head,pose,net)
   bottom=min(bottom,float(np.concatenate([t[2] for t in triangles])[:,1].min()));continue
  if part=='body':points=P.deform(cloud,pose,geometry=geometry(pose))
  elif part=='torso':points=torso_surface(cloud,g,pose)
  elif part=='pelvis':
   origin=np.mean([chains['leg'+s][0] for s in ('L','R')],axis=0)
   rot=root_rotation(pose)@ry(pose.get('pelvis_yaw',0))@rz(-pose.get('pelvis',0));points=cloud@rot.T+origin
  else:
   origin,rot=head if part=='head' else (A.frame(A.record(model,part),model,head,pose) if part not in PARTS else limbs[part][:2]);points=cloud@rot.T+origin
  bottom=min(bottom,float(points[:,1].min()))
 return bottom

@lru_cache(maxsize=256)
def _attachment_local(surface_key,layout_key,mirrored):
 item=json.loads(surface_key);net=json.loads(layout_key);mesh,bounds=A.mesh(item)
 faces=[];coords=[]
 for face,local in mesh:
  chart=local
  if mirrored:
   chart=local.copy();chart[:,0]*=-1;face={'left':'right','right':'left'}.get(face,face)
  faces.append(face);coords.append(uv_tri(face,chart,bounds,net))
 shaped=A.taper_depth(np.concatenate([local for face,local in mesh]),item).reshape(-1,3,3)
 return tuple(faces),shaped,np.array(coords),np.concatenate([local for face,local in mesh]).reshape(-1,3,3)

def attachment_triangles(item,model,head,pose,net):
 surface=dict(A.surface(item),kind=item.get('kind','ear'))
 faces,local,coords,raw=_attachment_local(json.dumps(surface,sort_keys=True),json.dumps(net,sort_keys=True),item['id'].endswith('R'))
 if item.get('kind')=='tail' and 'tail' in pose:
  import tails
  local=tails.skin(raw.reshape(-1,3),item,pose['tail']).reshape(-1,3,3)
 origin,rotation=A.frame(item,model,head,pose);worlds=local@rotation.T+origin
 return [(item['id'],face,world,uv) for face,world,uv in zip(faces,worlds,coords)]

@lru_cache(maxsize=64)
def _mesh_cache(key,layouts):
 pose=json.loads(key);bundle={'textures':{p:{'layout':layout} for p,layout in json.loads(layouts).items()}}
 g,j,chains,limbs,torso,head=geometry(pose);triangles=[];model=MD.normalize(pose.get('_model'))
 for part,(origin,rot,length,r0,r1) in limbs.items():
  section=('arm' if 'Arm' in part else 'leg')+part[-1]
  mesh,bounds=limb_mesh(length,r0,r1,model[section]['shape']);net=bundle['textures'][part]['layout']
  for face,local in mesh:
   chart=local
   # Paired limbs share a single anatomically mirrored chart convention.
   # Their world geometry and joint frames remain unchanged.
   if part.endswith('R'):
    chart=local.copy();chart[:,0]*=-1
    face={'left':'right','right':'left'}.get(face,face)
   chain_lengths=g['limbs'][section]['lengths'];offset=0 if part.startswith(('upper','thigh')) else chain_lengths[0]
   shaped=sculpt.deform(local,bounds,model[section],(-local[:,1]+offset)/sum(chain_lengths))
   triangles.append((part,face,shaped@rot.T+origin,uv_tri(face,chart,bounds,net)))
 if P.active(model):
  mesh,bounds=P.mesh(model);net=bundle['textures']['body']['layout']
  shaped=P.deform(np.concatenate([v for f,v in mesh]),pose,geometry=(g,j,chains,limbs,torso,head)).reshape(-1,3,3)
  for (face,local),deformed in zip(mesh,shaped):triangles.append(('body',face,deformed,uv_tri(face,local,bounds,net)))
  for item in model.get('attachments',[]):
   triangles.extend(attachment_triangles(item,model,head,pose,bundle['textures'][item['id']]['layout']))
  return j,triangles
 size=model['head']['size'];net=bundle['textures']['head']['layout'];origin,rot=head
 for face,local,uv in head_mesh(size,model['head']['shape']):
  x,y,w,h=net['rects'][face];coords=np.array((x,y))+uv*np.array((w-1,h-1));half=np.array((8.,7.5,7.5))*size;local=sculpt.deform(local,(-half,half),model['head']);triangles.append(('head',face,local@rot.T+origin,coords))
 for item in model.get('attachments',[]):
  triangles.extend(attachment_triangles(item,model,head,pose,bundle['textures'][item['id']]['layout']))
 mask=g['torso_mask'];h,w=mask.shape;ys=sorted(set((0,1,round(h*.2),round(h*.45),round(h*.7),h-2,h-1)));rings=[((h-1)/2-y,max(1,mask[y].sum()/2),3.5*(.75+.25*mask[y].sum()/max(mask.sum(axis=1)))) for y in ys]
 shape=model['torso']['shape'];pelvis_depth=model['torso']['pelvis_depth']
 if shape!='tapered':
  # Continuous body profile; shoulder/waist/hip sliders still affect each band.
  scale=max(model['torso'][k] for k in ('shoulder','waist','hip'))
  rings=[(y,w/2*np.interp((h/2-y)/h,[0,.5,1],[model['torso']['shoulder'],model['torso']['waist'],model['torso']['hip']])/scale,3.5) for y,_,_ in rings]
 thickness=model['torso']['thickness'];half_depth=3.5*thickness
 rings=[(y,x,z*thickness) for y,x,z in rings]
 rings=[(rings[0][0]+.4,0.,0.)]+rings+[(rings[-1][0]-.4,0.,0.)]
 net=bundle['textures']['torso']['layout'];origin,rot=torso;bounds=(np.array((-w/2,-h/2-pelvis_depth,-half_depth)),np.array((w/2,h/2,half_depth)))
 for face,local in surface_rings(rings,4 if shape=='box' else 12,shape=='box'):triangles.append(('torso',face,torso_surface(sculpt.deform(local,bounds,model['torso']),g,pose),uv_tri(face,local,bounds,net)))
 if pelvis_depth>0:
  # A real, closed pelvis joins the waist to the leg roots. It follows the
  # pelvis rotation, not the upper-body lean, and shares the torso material.
  hip_center=np.mean([chains['leg'+s][0] for s in ('L','R')],axis=0)
  hip_rot=root_rotation(pose)@ry(pose.get('pelvis_yaw',0))@rz(-pose.get('pelvis',0))
  width=max(3.,5.*model['torso']['hip']);bottom=-pelvis_depth
  pelvis_rings=((1.6,0.,0.),(1.6,width*.92,3.1*thickness),(0.,width,half_depth),(bottom,width*.72,2.8*thickness),(bottom,0.,0.))
  # Use the lower portion of the same UV chart, with no new texture card.
  for face,local in surface_rings(pelvis_rings,4 if shape=='box' else 12,shape=='box'):
   uvlocal=local.copy();uvlocal[:,1]+=-h/2
   shaped=sculpt.deform(uvlocal,bounds,model['torso']).copy();shaped[:,1]-=-h/2
   triangles.append(('torso',face,shaped@hip_rot.T+hip_center,uv_tri(face,uvlocal,bounds,net)))
 return j,triangles

@lru_cache(maxsize=64)
def _protection_references(model_key,layouts,groups_key):
 from pixel_protection import build_reference
 model=json.loads(model_key);groups=json.loads(groups_key)
 neutral={'_model':model};_,triangles=_mesh_cache(json.dumps(neutral,sort_keys=True),layouts)
 _,_,_,limbs,torso,head=geometry(neutral)
 frames={part:(values[0],values[1]) for part,values in limbs.items()}
 frames.update(torso=torso,head=head);frames.update({item['id']:A.frame(item,model,head,neutral) for item in model.get('attachments',[])})
 if P.active(model):frames['body']=(P.bottom(geometry(neutral)[0]),np.eye(3))
 result={}
 for part,items in groups.items():
  origin,rotation=frames[part]
  local=[(face,(world-origin)@rotation,uv) for p,face,world,uv in triangles if p==part]
  result[part]=[build_reference(local,group) for group in items]
 return result

def protection_context(pose,bundle):
 from pixel_protection import valid_groups
 groups={part:valid_groups(resource) for part,resource in bundle['textures'].items() if resource.get('protected_groups')}
 if not groups:return None
 layouts=json.dumps({p:r['layout'] for p,r in bundle['textures'].items()},sort_keys=True)
 refs=_protection_references(json.dumps(MD.normalize(pose.get('_model')),sort_keys=True),layouts,json.dumps(groups,sort_keys=True))
 _,_,_,limbs,torso,head=geometry(pose)
 frames={part:(values[0],values[1]) for part,values in limbs.items()};frames.update(torso=torso,head=head);model=MD.normalize(pose.get('_model'));frames.update({item['id']:A.frame(item,model,head,pose) for item in model.get('attachments',[])})
 if P.active(model):frames['body']=P.local_frame(pose,(0,model['body']['height']*.75,0))
 result={part:dict(references=items,frame=frames[part]) for part,items in refs.items()}
 for item in model.get('attachments',[]):
  if item.get('kind')=='tail' and item['id'] in result and 'tail' in pose:
   import tails
   result[item['id']]['group_frames']=[tails.group_frame(item,pose,r['anchor'] if r is not None else (0,0,0),frames[item['id']]) for r in refs[item['id']]]
 if 'body' in result:
  result['body']['group_frames']=[P.local_frame(pose,r['anchor'] if r is not None else (0,model['body']['height']*.75,0)) for r in refs['body']]
 if 'torso' in result:
  g=geometry(pose)[0];center=world(g['torso_c']);pivot=world(np.mean(list(g['hip'].values()),axis=0));offset=root_offset(pose)
  group_frames=[]
  for reference in refs['torso']:
   fraction=.5 if reference is None else np.clip((reference['anchor'][1]+g['torso_mask'].shape[0]/2)/g['torso_mask'].shape[0],0,1)
   rot=torso_rotation(pose,fraction);group_frames.append((rot@(center-pivot)+pivot+offset,rot))
  result['torso']['group_frames']=group_frames
 return result

def render(pose,settings=None,cam=(0,0)):
 j,triangles,bundle=pose_meshes(pose);yaw=pose.get('yaw',0)+cam[0];pitch=pose.get('pitch',0)+cam[1]
 # Backface rejection halves raster work without changing the depth test.
 view=np.array((math.sin(-math.radians(yaw))*math.cos(math.radians(pitch)),math.sin(math.radians(pitch)),math.cos(math.radians(yaw))*math.cos(math.radians(pitch))))
 worlds=np.stack([tri[2] for tri in triangles]);normal=np.cross(worlds[:,1]-worlds[:,0],worlds[:,2]-worlds[:,0]);visible=[triangles[i] for i in np.flatnonzero(normal@view>1e-8)]
 sockets=[chain[k] for name,chain in j.items() if name.startswith(('arm','leg')) for k in ('root','mid')]
 s={'parts':True,'textures':True,'outline':True,'gaps':True,'perfect':True,**(settings or {})}
 painted={part:resource for part,resource in bundle['textures'].items() if s['textures'] and resource.get('png')}
 textures={part:np.array(U.texture_image(bundle,part)) if part in painted else np.array([[(*U.color(part),255) if s['parts'] else (255,255,255,255)]],dtype=np.uint8) for part in U.parts(bundle)}
 names=U.parts(bundle);connections=[];g=F.model_geometry(pose)
 for kind in ('arm','leg'):
  for side in ('L','R'):
   first=('upperArm' if kind=='arm' else 'thigh')+side;second=('lowerArm' if kind=='arm' else 'shin')+side
   radius=sum(g['limbs'][kind+side]['radii'])/2+1
   connections.append((names.index(first),names.index(second),j[kind+side]['mid'],radius))
   if g['limbs'][kind+side]['bridge']:
    connections.append((names.index('body' if P.active(bundle['model']) else 'torso'),names.index(first),j[kind+side]['root'],g['limbs'][kind+side]['radii'][0]+.5))
 movement=np.array((pose.get('dx',0.),-pose.get('dy',0.)+pose.get('_breath_dy',0.),pose.get('dz',0.)))
 projected_move=project(np.array([movement,np.zeros(3)]),yaw,pitch)
 delta=projected_move[0,:2]-projected_move[1,:2]
 pixel_shift=np.floor(delta+.5)-delta+np.array((0.,math.floor(pose.get('_camera_y',0)+.5)))
 image=raster(visible,textures,(yaw,pitch),dict(colors=s['parts'] or bool(painted),material_colors=True,_parts=U.parts(bundle),_head_children=tuple(item['id'] for item in bundle['model'].get('attachments',[]) if item.get('parent','head')=='head'),outline=s['outline'],gaps=s['gaps'],onepx=True,outline_color=s.get('outline_color','auto')),sockets,connections,stable_head=None if P.active(bundle['model']) else j['head']['tip'],pixel_shift=pixel_shift,protection=painted,protection_context=protection_context(pose,bundle) if painted else None)[0]
 return image[:,::-1].copy() if pose.get('flip') else image
