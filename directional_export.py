"""Bounded-memory directional atlases and engine-neutral frame metadata."""
import json,math,shutil,tempfile
from pathlib import Path
from PIL import Image

MAX_ATLAS_EDGE=4096

def page_layout(count,scale,directions,native=(64,64)):
 width,height=(v*scale for v in native);columns=max(1,MAX_ATLAS_EDGE//width);rows=max(1,MAX_ATLAS_EDGE//height)
 return [dict(first_frame=first,frame_count=min(columns,count-first),first_direction=row,direction_count=min(rows,directions-row),size=[width*min(columns,count-first),height*min(rows,directions-row)]) for row in range(0,directions,rows) for first in range(0,count,columns)]

def export(project,out=None,name=None,formats=None,create_folder=True,scale=1,directions=8):
 import engine as E
 if isinstance(directions,bool) or not isinstance(directions,int) or directions not in (1,4,8):raise ValueError('方向数必须为1、4或8。')
 if isinstance(scale,bool) or not isinstance(scale,int) or not 1<=scale<=8:raise ValueError('输出比例必须是 1 到 8 的整数')
 formats=set(('png','strip','gif','recipe') if formats is None else formats)
 if not formats or formats-{'png','strip','gif','recipe'}:raise ValueError('请选择至少一种有效的导出类型')
 import render_options as O
 count=max(1,min(120,round(project.get('seconds',2)*project.get('fps',12))))
 native_size=O.size(project.get('render'));width,height=(v*scale for v in native_size)
 if 'gif' in formats and width*height*count>64*1024*1024:raise ValueError('GIF尺寸与帧数过大，请降低输出倍率或帧数；PNG支持分页输出。')
 requested=name;name=E.export_name(project,name);parent=Path(out or E.ROOT/'out')
 parent.mkdir(parents=True,exist_ok=True);created_folder=False
 if create_folder:
  if requested is None:dest=Path(tempfile.mkdtemp(prefix=name+'_',dir=parent));created_folder=True
  else:
   dest=parent/name
   if dest.exists():raise FileExistsError('同名文件夹已存在，请更换名称或目录')
 else:dest=parent
 views=[dict(id=f'd{angle:03}',yaw=angle,pitch=0) for angle in range(0,360,360//directions)]
 if directions==1:views=[dict(id='d000',yaw=project.get('export_view',{}).get('yaw',0),pitch=project.get('export_view',{}).get('pitch',0))]
 pages=page_layout(count,scale,directions,native_size) if 'strip' in formats else []
 for i,page in enumerate(pages):page['file']=f'{name}_atlas'+(f'_{i:02}' if len(pages)>1 else '')+'.png'
 recipe='recipe.json' if create_folder else name+'.json';metadata=name+'_atlas.json'
 files=[page['file'] for page in pages]
 if 'png' in formats:files += [f'{name}_{view["id"]}_{i:02}.png' for view in views for i in range(count)]
 if 'gif' in formats:files += [f'{name}_{view["id"]}.gif' for view in views]
 if 'recipe' in formats:files.append(recipe)
 files.append(metadata)
 try:
  if any((dest/file).exists() for file in files):raise FileExistsError('同名文件已存在，请更换名称或目录')
  seq=E.poses(project) if formats-{'recipe'} else []
  fps=project.get('fps',12);duration=1000/fps
  data=dict(type='FellowStudioDirectionalAtlas',version=1,name=name,fps=fps,
            playback=E.MT.mode(project),frame_count=count,scale=scale,native_cell=list(native_size),cell=[width,height],
            pivot=[native_size[0]/2*scale,(native_size[1]-8+math.floor(project.get('camera_y',0)+.5))*scale],
            character_yaw=project.get('yaw',0),camera_pitch=views[0]['pitch'],pages=pages,directions=[])
  for row,view in enumerate(views):
   frames=[]
   for i in range(count):
    page=next((p for p in pages if p['first_frame']<=i<p['first_frame']+p['frame_count'] and p['first_direction']<=row<p['first_direction']+p['direction_count']),None)
    image=page['file'] if page else (f'{name}_{view["id"]}_{i:02}.png' if 'png' in formats else None)
    rect=[(i-page['first_frame'])*width,(row-page['first_direction'])*height,width,height] if page else ([0,0,width,height] if image else None)
    frame=dict(index=i,duration_ms=duration,image=image,rect=rect)
    if 'png' in formats:frame['png']=f'{name}_{view["id"]}_{i:02}.png'
    frames.append(frame)
   data['directions'].append(dict(view,row=row,frames=frames))
  with tempfile.TemporaryDirectory(prefix='.fellow-export-',dir=parent) as temp:
   stage=Path(temp);native=stage/'native';native.mkdir()
   # Work one page at a time: at 8x, an eight-row page is at most 64 MiB RGBA.
   batches=pages or [dict(first_frame=0,frame_count=count)]
   for page in batches:
    atlas=Image.new('RGBA',page['size']) if pages else None
    for row,view in enumerate(views):
     if pages and not page['first_direction']<=row<page['first_direction']+page['direction_count']:continue
     for i in range(page['first_frame'],page['first_frame']+page['frame_count']):
      if not seq:continue
      image=Image.fromarray(E.rgba(seq[i],project.get('render'),(view['yaw'],view['pitch'])))
      if 'gif' in formats:image.save(native/f'{view["id"]}_{i:02}.png')
      if scale!=1:image=image.resize((width,height),Image.Resampling.NEAREST)
      if 'png' in formats:image.save(stage/f'{name}_{view["id"]}_{i:02}.png')
      if atlas is not None:atlas.paste(image,((i-page['first_frame'])*width,(row-page['first_direction'])*height))
    if atlas is not None:atlas.save(stage/page['file']);atlas.close()
   if 'gif' in formats:
    # Process each view separately rather than retaining eight scaled clips.
    for view in views:
     preview=[]
     for i in range(count):
      with Image.open(native/f'{view["id"]}_{i:02}.png') as source:image=source.convert('RGBA')
      bg=Image.new('RGB',native_size,(90,77,66));bg.paste(image,mask=image.getchannel('A'))
      frame=bg.quantize(colors=256)
      if scale!=1:frame=frame.resize((width,height),Image.Resampling.NEAREST)
      preview.append(frame);image.close();bg.close()
     preview[0].save(stage/f'{name}_{view["id"]}.gif',save_all=True,append_images=preview[1:],duration=round(duration),**({'loop':0} if E.MT.mode(project)=='loop' else {}))
     for image in preview:image.close()
   if 'recipe' in formats:E.save(dict(project,name=name,export_directions=directions),stage/recipe)
   (stage/metadata).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
   if create_folder and not created_folder:dest.mkdir(exist_ok=False);created_folder=True
   published=[]
   try:
    for file in files:
     target=dest/file
     # Exclusive creation also catches a file appearing after the preflight.
     with target.open('xb') as output:
      published.append(target)
      with (stage/file).open('rb') as source:shutil.copyfileobj(source,output)
   except Exception:
    for target in published:target.unlink(missing_ok=True)
    raise
  return dest
 except Exception:
  if created_folder and dest.is_dir():
   try:dest.rmdir()
   except OSError:pass
  raise
