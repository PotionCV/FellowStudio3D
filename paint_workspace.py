"""Local painting files with provenance checks and stable-save polling."""
import copy,json,hashlib
from pathlib import Path
import uv_assets as U

def painting_key(project):
 """Local preference key for artwork, independent of motion and model sizing.

 Use the project's original embedded PNGs, before model-to-UV adaptation. A
 resize can still reconnect and offer adaptation; another painted character
 does not inherit its predecessor's folder. No paths enter portable projects.
 """
 bundle=project.get('assets3d') or {}
 payload={part:resource.get('png') for part,resource in bundle.get('textures',{}).items() if resource.get('png')}
 return hashlib.sha256(json.dumps(payload,sort_keys=True).encode('utf-8')).hexdigest()

class PaintWorkspace:
 def __init__(self,folder):
  self.folder=Path(folder)
  self.manifest=json.loads((self.folder/'UV_Model.json').read_text(encoding='utf-8-sig'))
  if self.manifest.get('type')!='FellowStudio3D_UV':raise ValueError('Choose a FellowStudio3D painting folder')
  if self.manifest.get('mapping_version') not in (None,2):raise ValueError('Unsupported UV mapping version')
  self.seen={};self.pending={};self.attempts={};self.states={}
  for part in U.parts(self.manifest):self.seen[part]=self.stamp(part)
 def stamp(self,part):
  try:
   s=(self.folder/f'{part}.png').stat();return s.st_mtime_ns,s.st_size
  except OSError:return None
 def compatible(self,bundle,part):
  return part in self.manifest.get('textures',{}) and U.surface_record(self.manifest,part)==U.surface_record(bundle,part)
 def poll(self,bundle,force=False,skip=()):
  candidate=copy.deepcopy(bundle);changed=False;self.states={}
  for part in U.parts(bundle):
   if bundle['textures'][part].get('painting_override'):self.states[part]='embedded';continue
   if part in skip:self.states[part]='external';continue
   if part in bundle.get('shared_textures',{}):self.states[part]='shared';continue
   if not self.compatible(bundle,part):self.states[part]='mapping';continue
   stamp=self.stamp(part)
   if stamp is None:self.states[part]='missing';continue
   if stamp==self.seen.get(part) and not force:self.states[part]='ready';continue
   if self.pending.get(part)!=stamp and not force:
    self.pending[part]=stamp;self.attempts[part]=0;self.states[part]='waiting';continue
   if self.attempts.get(part,0)>=3 and not force:self.states[part]='invalid';continue
   try:
    U.import_texture(candidate,part,self.folder/f'{part}.png')
   except Exception:
    self.attempts[part]=self.attempts.get(part,0)+1;self.states[part]='invalid';continue
   self.seen[part]=stamp;self.pending.pop(part,None);self.attempts.pop(part,None)
   self.states[part]='updated'
   if not bundle['textures'][part].get('png') and U.texture_image(candidate,part).tobytes()==U.texture_image(bundle,part).tobytes():candidate['textures'][part]=copy.deepcopy(bundle['textures'][part])
   changed |= candidate['textures'][part]!=bundle['textures'][part]
  return U.apply_shared(candidate) if changed else None

def prepare(bundle,folder):
 folder=Path(folder)
 if (folder/'UV_Model.json').exists():
  workspace=PaintWorkspace(folder)
  if not all(workspace.compatible(bundle,p) for p in U.parts(bundle)):raise ValueError('This painting folder uses another model. Prepare a new folder for the current appearance.')
  return workspace
 U.export_pack(bundle,folder);return PaintWorkspace(folder)

def adapted_folder(bundle,old_folder,skip=()):
 old=Path(old_folder);workspace=PaintWorkspace(old)
 candidate=copy.deepcopy(bundle)
 source={'model':workspace.manifest['model'],'textures':{p:{'layout':r['layout'],'png':None,'name':'Default'} for p,r in workspace.manifest['textures'].items()}}
 from PIL import Image
 for part in U.parts(bundle):
  if part not in source['textures']:continue
  if part in skip or part in candidate.get('shared_textures',{}):continue
  U.import_texture(source,part,old/f'{part}.png')
  image=U.texture_image(source,part)
  if not candidate['textures'][part].get('png') and image.tobytes()==U.template(part,source['textures'][part]['layout']).tobytes():continue
  target=candidate['textures'][part];result=Image.new('RGBA',target['layout']['size'])
  for face,(x,y,w,h) in target['layout']['rects'].items():
   ox,oy,ow,oh=source['textures'][part]['layout']['rects'][face]
   result.paste(image.crop((ox,oy,ox+ow,oy+oh)).resize((w,h),Image.Resampling.NEAREST),(x,y))
  target.update(png=U.encode(result),name=f'{part}.png',provenance='adapted')
 U.apply_shared(candidate);index=2
 while (old.parent/(old.name+f'-v{index}')).exists():index+=1
 new=old.parent/(old.name+f'-v{index}');U.export_pack(candidate,new)
 return PaintWorkspace(new)

def project_copy(bundle,folder):
 """Prepare current project pixels without reading or overwriting older art."""
 target=Path(folder);chosen=target;index=2
 if target.exists() and any(target.iterdir()):
  while True:
   target=chosen.parent/(chosen.name+f'-project-v{index}')
   try:target.mkdir(exist_ok=False);break
   except FileExistsError:index+=1
 candidate=copy.deepcopy(bundle)
 for resource in candidate['textures'].values():resource.pop('painting_pending',None)
 U.export_pack(candidate,target)
 return PaintWorkspace(target)
