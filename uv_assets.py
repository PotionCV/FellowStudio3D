"""UV nets and portable embedded textures for FellowStudio3D."""
import base64,copy,io,json,math,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,PngImagePlugin
PARTS=('head','torso','upperArmL','lowerArmL','upperArmR','lowerArmR','thighL','shinL','thighR','shinR')
COLORS={'head':(173,151,209),'torso':(216,118,90),'upperArmL':(232,180,105),'lowerArmL':(232,180,105),'upperArmR':(116,152,190),'lowerArmR':(116,152,190),'thighL':(138,180,128),'shinL':(138,180,128),'thighR':(212,138,168),'shinR':(212,138,168)}
MODEL=dict(shoulder=1.,waist=1.,hip=1.,height=1.,head=1.,headGap=0.,armUpper=6.,armLower=6.,legUpper=7.,legLower=7.,armWidth=5.,legWidth=5.,armGap=0.)
LIMITS=dict(shoulder=(.65,1.6),waist=(.5,1.5),hip=(.65,1.5),height=(.7,1.3),head=(.65,1.5),headGap=(-4,6),armUpper=(3,10),armLower=(3,10),legUpper=(3,10),legLower=(3,10),armWidth=(3,7),legWidth=(3,7),armGap=(0,4))
FACES=('front','right','back','left','top','bottom')
GLYPHS={'F':('111','100','110','100','100'),'R':('110','101','110','101','101'),'B':('110','101','110','101','110'),'L':('100','100','100','100','111'),'T':('111','010','010','010','010'),'D':('110','101','101','101','110')}
def dimensions(model):
 m={**MODEL,**model}
 return {'head':(15*m['head'],14*m['head'],14*m['head']),'torso':(12*max(m['shoulder'],m['waist'],m['hip']),14*m['height'],7),
 **{part:(m['armWidth'],m['armUpper' if part.startswith('upper') else 'armLower'],m['armWidth']) for part in PARTS if 'Arm' in part},
 **{part:(m['legWidth'],m['legUpper' if part.startswith('thigh') else 'legLower'],m['legWidth']) for part in PARTS if part.startswith(('thigh','shin'))}}
def layout(dims):
 w,h,d=[max(2,math.ceil(v)) for v in dims];p=2
 # Cross net: top/bottom attach to front, four side faces form a strip.
 rects={'front':(p+d,p+d,w,h),'left':(p,p+d,d,h),'right':(p+d+w,p+d,d,h),'back':(p+d+w+d,p+d,w,h),'top':(p+d,p,w,d),'bottom':(p+d,p+d+h,w,d)}
 size=(2**math.ceil(math.log2(2*p+2*(w+d))),2**math.ceil(math.log2(2*p+h+2*d)))
 return dict(size=list(size),rects={face:list(rect) for face,rect in rects.items()})
def template(part,net,guide=False):
 im=Image.new('RGBA',net['size']);draw=ImageDraw.Draw(im)
 for face,(x,y,w,h) in net['rects'].items():
  draw.rectangle((x,y,x+w-1,y+h-1),fill=COLORS[part]+(255,))
  if guide:
   draw.rectangle((x,y,x+w-1,y+h-1),outline=(52,45,40,255))
   letter='D' if face=='bottom' else face[:1].upper();gx=x+(w-3)//2;gy=y+(h-5)//2
   for row,bits in enumerate(GLYPHS[letter]):
    for col,bit in enumerate(bits):
     if bit=='1' and x<=gx+col<x+w and y<=gy+row<y+h:draw.point((gx+col,gy+row),fill='white')
 return im

def encode(im):
 out=io.BytesIO();im.save(out,format='PNG');return base64.b64encode(out.getvalue()).decode('ascii')
def decode(text):
 if len(text)>12_000_000:raise ValueError('Texture data too large')
 with Image.open(io.BytesIO(base64.b64decode(text,validate=True))) as im:
  if max(im.size)>2048:raise ValueError('Maximum texture size is 2048 px')
  return im.convert('RGBA')
def texture_image(project,part):
 resource=project['textures'][part]
 return decode(resource['png']) if resource.get('png') else template(part,resource['layout'])
def create_textures(model):return {part:{'layout':layout(dims),'png':None,'name':'Default'} for part,dims in dimensions(model).items()}
def surface_record(project,part):
 model=project.get('model',{})
 if isinstance(model.get('head'),dict):
  import model_data as M
  model=M.normalize(model)
  if part=='head':geometry={k:model['head'][k] for k in ('shape','size')}
  elif part=='torso':
   geometry=dict(model['torso'])
   # Keep metadata exported before this parameter compatible at legacy depth.
   if geometry['thickness']==1.:geometry.pop('thickness')
  else:
   limb=('arm' if 'Arm' in part else 'leg')+part[-1];data=model[limb]
   segment='upper' if part.startswith(('upper','thigh')) else 'lower'
   geometry={k:data[k] for k in ('shape','thickness',segment)}
 else:geometry=model
 return {'layout':project['textures'][part]['layout'],'geometry':geometry,'mapping':2}

def texture_signature(project,part):
 return hashlib.sha256(json.dumps(surface_record(project,part),sort_keys=True,separators=(',',':')).encode()).hexdigest()

def painting_info(project,part,guide=False):
 return {'type':'FellowStudio3D_Texture','part':part,'guide':guide,'surface':surface_record(project,part)}

def save_painting(project,part,path,guide=False):
 info=PngImagePlugin.PngInfo();info.add_text('FellowStudio3D',json.dumps(painting_info(project,part,guide)))
 image=template(part,project['textures'][part]['layout'],True) if guide else texture_image(project,part)
 image.save(path,format='PNG',pnginfo=info)

def texture_match(project,part,path):
 """PNG size is necessary, not proof of UV/shape provenance."""
 path=Path(path)
 with Image.open(path) as image:
  if image.format!='PNG':return 'format'
  if image.size!=tuple(project['textures'][part]['layout']['size']):return 'size'
  raw=image.info.get('FellowStudio3D');record=json.loads(raw) if raw else None
 if path.stem.endswith('_Guide') or record and record.get('guide'):return 'guide'
 if record is None and (path.parent/'UV_Model.json').is_file():
  manifest=json.loads((path.parent/'UV_Model.json').read_text(encoding='utf-8-sig'))
  if manifest.get('type')=='FellowStudio3D_UV' and part in manifest.get('textures',{}):
   if manifest.get('mapping_version') not in (None,2):return 'mapping'
   if 'mapping_version' not in manifest:
    return 'unknown' if surface_record(manifest,part)==surface_record(project,part) else 'mapping'
   record={'part':part,'surface':surface_record(manifest,part)}
 if record is None:return 'unknown'
 other=record.get('part','')
 if other!=part and not (part.endswith(('L','R')) and other[:-1]==part[:-1]):return 'part'
 return 'matched' if record.get('surface')==surface_record(project,part) else 'mapping'

def import_texture(project,part,path,check=True):
 match='unknown'
 if check:
  match=texture_match(project,part,path)
  if match not in ('matched','unknown'):
   raise ValueError({'format':'Use a PNG image','size':'PNG size does not match. Prepare painting files for this model.',
    'guide':'Choose the painting PNG, not the guide image.','part':'This texture belongs to another body part.',
    'mapping':'This texture uses another model surface or UV layout. Adapt the painting files first.'}[match])
 with Image.open(path) as source:
  if source.format!='PNG':raise ValueError('Use a PNG image')
  expected=tuple(project['textures'][part]['layout']['size'])
  if source.size!=expected:raise ValueError(f'Expected {expected[0]} x {expected[1]} px; got {source.width} x {source.height}. Export the template for this model first.')
  image=source.convert('RGBA')
 # Alpha is intentionally preserved; holes reveal the next surface in depth.
 resource=project['textures'][part];resource['png']=encode(image);resource['name']=Path(path).name;resource['provenance']=match

def repack(project):
 """Fit existing painted faces to new physical dimensions, preserving face identity."""
 old=copy.deepcopy(project['textures']);new=create_textures(project['model'])
 for part in PARTS:
  from pixel_protection import resize_groups
  new[part]['protected_groups']=resize_groups(old[part],new[part]['layout'])
  if not old[part].get('png'):continue
  source=decode(old[part]['png']);target=Image.new('RGBA',new[part]['layout']['size'])
  for face,(x,y,w,h) in new[part]['layout']['rects'].items():
   ox,oy,ow,oh=old[part]['layout']['rects'][face]
   patch=source.crop((ox,oy,ox+ow,oy+oh)).resize((w,h),Image.Resampling.NEAREST);target.paste(patch,(x,y))
  new[part].update(png=encode(target),name=old[part]['name'])
 project['textures']=new

def export_pack(project,folder):
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
 names=[f'{p}{suffix}.png' for p in PARTS for suffix in ('','_Guide')]+['UV_Model.json','READ_ME.txt']
 if any((folder/name).exists() for name in names):raise FileExistsError('UV files already exist here. Choose an empty folder.')
 for part in PARTS:
  save_painting(project,part,folder/f'{part}.png');save_painting(project,part,folder/f'{part}_Guide.png',True)
 (folder/'UV_Model.json').write_text(json.dumps({'type':'FellowStudio3D_UV','mapping_version':2,'model':project['model'],'shared_textures':project.get('shared_textures',{}),'textures':{p:{'layout':r['layout'],'protected_groups':r.get('protected_groups',[])} for p,r in project['textures'].items()}},indent=2),encoding='utf-8')
 (folder/'READ_ME.txt').write_text('Paint the PART.png files, preserving canvas size and face positions. PART_Guide.png is a separate guide: F=front, B=back, L=left, R=right, T=top, D=bottom (down). Left/right on the sheet refer to character sides. Keep UV_Model.json next to the images. Import the folder or drop one PART.png onto its matching card. Avoid smoothing/resizing. Alpha is supported.\n',encoding='utf-8')
 return folder

def import_pack(project,folder):
 folder=Path(folder);manifest=json.loads((folder/'UV_Model.json').read_text(encoding='utf-8'))
 if manifest.get('type')!='FellowStudio3D_UV':raise ValueError('This folder is not a FellowStudio3D UV pack')
 if manifest.get('mapping_version') not in (None,2):raise ValueError('Unsupported UV mapping version')
 candidate=copy.deepcopy(project)
 # Never silently reinterpret old UVs using a newly generated net.
 if any(surface_record(manifest,p)!=surface_record(project,p) for p in PARTS):raise ValueError('This UV pack belongs to different model surfaces. Restore the matching appearance or adapt the painting files first.')
 for part in PARTS:
  if manifest['textures'][part]['layout']!=json.loads(json.dumps(project['textures'][part]['layout'])):raise ValueError('UV layout does not match this project')
  import_texture(candidate,part,folder/f'{part}.png')
  from pixel_protection import valid_groups
  resource=candidate['textures'][part]
  resource['protected_groups']=valid_groups({**resource,'protected_groups':manifest['textures'][part].get('protected_groups',[])})
 if 'shared_textures' in manifest:candidate['shared_textures']=copy.deepcopy(manifest['shared_textures'])
 apply_shared(candidate)
 project['textures']=candidate['textures']
 if candidate.get('shared_textures'):project['shared_textures']=candidate['shared_textures']
 else:project.pop('shared_textures',None)

def apply_shared(project):
 """Link only anatomical counterparts; never recolor unpainted defaults."""
 links=project.get('shared_textures',{})
 if not isinstance(links,dict):raise ValueError('Invalid texture sharing links')
 valid={target:source for target,source in links.items() if target.endswith('R') and source==target[:-1]+'L' and target in PARTS}
 from pixel_protection import resize_groups
 for target,source in valid.items():
  a=project['textures'][source];b=project['textures'][target]
  b['protected_groups']=resize_groups(a,b['layout'])
  if a.get('provenance'):b['provenance']=a['provenance']
  if not a.get('png'):b.update(png=None,name='Default');b.pop('provenance',None);continue
  if a['layout']==b['layout']:b.update(png=a['png'],name=a.get('name','Painted'));continue
  image=texture_image(project,source);result=Image.new('RGBA',b['layout']['size'])
  for face,(x,y,w,h) in b['layout']['rects'].items():
   ox,oy,ow,oh=a['layout']['rects'][face];result.paste(image.crop((ox,oy,ox+ow,oy+oh)).resize((w,h),Image.Resampling.NEAREST),(x,y))
  b.update(png=encode(result),name=a.get('name','Painted'))
 if valid:project['shared_textures']=valid
 else:project.pop('shared_textures',None)
 return project
